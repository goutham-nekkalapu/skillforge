#!/usr/bin/env python3
"""Fetch everything about a YouTube video (metadata, description, chapters,
transcript) and save it as a reusable "source package" on disk.

Tiers, tried in order (configurable):
  1. ytdlp          - local yt-dlp. Free. Metadata + chapters + YouTube captions.
  2. transcriptapi  - transcriptapi.com. YouTube captions (manual or auto) when
                      yt-dlp is blocked. Cannot transcribe caption-less videos.
  3. supadata       - api.supadata.ai, mode=auto: existing captions, otherwise
                      AI speech-to-text (2 credits / minute).

Usage:
  fetch.py --where                     # print the save location and exit
  fetch.py <youtube-url-or-id>         # fetch and save (uses cache if present)
  fetch.py <url> --force               # ignore cache, fetch again
  fetch.py <url> --tiers supadata      # force a specific tier
  fetch.py --ingest data.json          # save data gathered via MCP connectors

Exit codes: 0 ok | 2 failed | 3 credentials needed | 4 network blocked
(use connector path) | 5 bad input.
The final machine-readable result is printed between
"=== RESULT JSON ===" and "=== END RESULT ===".
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
import ytn_config as C  # noqa: E402

UA = "yt-notes-skill/1.0"


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------
class TierError(Exception):
    """This tier failed; try the next one."""


class NoCaptions(TierError):
    """The video has no captions on YouTube (only AI transcription can help)."""


class CredError(TierError):
    """Credentials missing or rejected."""


class NetworkError(TierError):
    """Could not reach the service (offline, firewall, sandbox allowlist)."""


class FatalVideoError(Exception):
    """Video is private / deleted / unavailable: no tier can help."""


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def extract_video_id(s: str) -> str | None:
    s = (s or "").strip()
    if _ID_RE.match(s):
        return s
    try:
        u = urllib.parse.urlparse(s if "://" in s else "https://" + s)
    except ValueError:
        return None
    host = (u.hostname or "").lower()
    path = u.path or ""
    if host.endswith("youtu.be"):
        cand = path.strip("/").split("/")[0]
        return cand if _ID_RE.match(cand) else None
    if "youtube" in host:
        q = urllib.parse.parse_qs(u.query)
        if q.get("v") and _ID_RE.match(q["v"][0]):
            return q["v"][0]
        m = re.match(r"^/(?:shorts|embed|live|v|e)/([A-Za-z0-9_-]{11})", path)
        if m:
            return m.group(1)
    return None


def watch_url(vid: str) -> str:
    return f"https://www.youtube.com/watch?v={vid}"


def http(method, url, headers=None, params=None, timeout=120):
    """Return (status, headers_dict, parsed_json_or_text). Raises NetworkError."""
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status, hdrs, raw = r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        status, hdrs, raw = e.code, dict(e.headers or {}), e.read() or b""
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise NetworkError(f"cannot reach {urllib.parse.urlparse(url).hostname}: {e}")
    text = raw.decode("utf-8", "replace")
    try:
        body = json.loads(text) if text else {}
    except json.JSONDecodeError:
        body = text
    return status, {k.lower(): v for k, v in hdrs.items()}, body


def looks_like_proxy_block(status, body) -> bool:
    return status in (403, 407) and not isinstance(body, dict)


def norm_date(s) -> str | None:
    if not s:
        return None
    s = str(s)
    if re.fullmatch(r"\d{8}", s):
        return f"{s[:4]}-{s[4:6]}-{s[6:]}"
    m = re.match(r"(\d{4}-\d{2}-\d{2})", s)
    return m.group(1) if m else s


_TS = r"(?:\d{1,2}:)?\d{1,2}:\d{2}"


def ts_to_seconds(ts: str) -> int:
    parts = [int(p) for p in ts.split(":")]
    sec = 0
    for p in parts:
        sec = sec * 60 + p
    return sec


def chapters_from_description(desc: str) -> list[dict]:
    """Parse 'MM:SS Title' / 'Title - MM:SS' lines from a description."""
    out = []
    for line in (desc or "").splitlines():
        line = line.strip()
        m = re.match(rf"^[\(\[]?({_TS})[\)\]]?\s*[-–—|:.)]*\s*(.+)$", line)
        if m:
            out.append({"start": ts_to_seconds(m.group(1)), "title": m.group(2).strip()})
            continue
        m = re.match(rf"^(.+?)\s*[-–—|:]?\s*[\(\[]?({_TS})[\)\]]?$", line)
        if m and len(m.group(1)) < 120:
            out.append({"start": ts_to_seconds(m.group(2)), "title": m.group(1).strip(" -–—|:")})
    # de-dupe, sort, require at least 2 entries to count as chapters
    seen, chapters = set(), []
    for c in sorted(out, key=lambda c: c["start"]):
        if c["start"] not in seen and c["title"]:
            seen.add(c["start"])
            chapters.append(c)
    return chapters if len(chapters) >= 2 else []


def links_from_description(desc: str) -> list[str]:
    links = re.findall(r"https?://[^\s<>\"')\]]+", desc or "")
    seen, out = set(), []
    for l in links:
        l = l.rstrip(".,;")
        if l not in seen:
            seen.add(l)
            out.append(l)
    return out


def clean_segments(segs: list[dict]) -> list[dict]:
    out = []
    for s in segs:
        t = re.sub(r"\s+", " ", str(s.get("text", "")).replace("\n", " ")).strip()
        if not t or (out and out[-1]["text"] == t):
            continue
        out.append({"start": round(float(s.get("start", 0) or 0), 2), "text": t})
    return out


# --------------------------------------------------------------------------
# Tier 1: yt-dlp
# --------------------------------------------------------------------------
def ytdlp_cmd() -> list[str] | None:
    exe = shutil.which("yt-dlp")
    if exe:
        return [exe]
    try:
        import yt_dlp  # noqa: F401

        return [sys.executable, "-m", "yt_dlp"]
    except ImportError:
        return None


def pick_track(info: dict, prefs: list[str]):
    """Return (code, kind) where kind in manual|auto|auto-translated, or None."""
    manual = {k: v for k, v in (info.get("subtitles") or {}).items() if k != "live_chat"}
    auto = info.get("automatic_captions") or {}
    orig = info.get("language")
    if not orig:
        origs = [k[:-5] for k in auto if k.endswith("-orig")]
        orig = origs[0] if origs else None

    def find(d, lang):
        if lang in d:
            return lang
        for k in d:
            if k.split("-")[0] == lang and not k.endswith("-orig"):
                return k
        return None

    for lang in prefs:
        k = find(manual, lang)
        if k:
            return k, "manual"
    if orig:
        k = find(manual, orig)
        if k:
            return k, "manual"
        for k in (f"{orig}-orig", orig):
            if k in auto:
                return k, "auto"
    for lang in prefs:
        k = find(auto, lang)
        if k:
            return k, ("auto" if (orig and lang == orig.split("-")[0]) else "auto-translated")
    if manual:
        return next(iter(manual)), "manual"
    for k in auto:
        if k.endswith("-orig"):
            return k, "auto"
    return None


def parse_json3(text: str) -> list[dict]:
    data = json.loads(text)
    segs = []
    for ev in data.get("events", []):
        if not ev.get("segs"):
            continue
        t = "".join(s.get("utf8", "") for s in ev["segs"])
        if t.strip():
            segs.append({"start": ev.get("tStartMs", 0) / 1000.0, "text": t})
    return segs


def parse_vtt(text: str) -> list[dict]:
    segs, last_line = [], None
    blocks = re.split(r"\n\s*\n", text.replace("\r", ""))
    for b in blocks:
        lines = b.strip().split("\n")
        tline = next((l for l in lines if "-->" in l), None)
        if not tline:
            continue
        start = tline.split("-->")[0].strip()
        h_m_s = start.replace(",", ".").split(":")
        try:
            sec = sum(float(x) * 60 ** i for i, x in enumerate(reversed(h_m_s)))
        except ValueError:
            continue
        for l in lines[lines.index(tline) + 1 :]:
            l = re.sub(r"<[^>]+>", "", l).strip()
            if l and l != last_line:
                segs.append({"start": sec, "text": l})
                last_line = l
    return segs


def meta_from_ytdlp(info: dict, vid: str) -> dict:
    desc = info.get("description") or ""
    chapters = [
        {"start": int(c.get("start_time") or 0), "title": c.get("title", "").strip()}
        for c in (info.get("chapters") or [])
    ]
    chapter_source = "youtube" if chapters else None
    if not chapters:
        chapters = chapters_from_description(desc)
        chapter_source = "description" if chapters else None
    return {
        "video_id": vid,
        "url": watch_url(vid),
        "title": info.get("title"),
        "channel": info.get("channel") or info.get("uploader"),
        "channel_url": info.get("channel_url") or info.get("uploader_url"),
        "upload_date": norm_date(info.get("upload_date")),
        "duration_seconds": info.get("duration"),
        "language": info.get("language"),
        "tags": info.get("tags") or [],
        "categories": info.get("categories") or [],
        "thumbnail": info.get("thumbnail"),
        "view_count": info.get("view_count"),
        "description": desc,
        "description_links": links_from_description(desc),
        "chapters": chapters,
        "chapter_source": chapter_source,
        "meta_source": "ytdlp",
    }


def tier_ytdlp(vid: str, cfg: dict, log: list):
    """Returns (meta, segments_or_None, tinfo_or_None). Raises TierError."""
    cmd = ytdlp_cmd()
    if not cmd:
        raise TierError("yt-dlp is not installed (pip install -U yt-dlp, or brew install yt-dlp)")
    extra = cfg.get("ytdlp_args") or []
    if isinstance(extra, str):
        extra = extra.split()
    cmd = cmd + [str(a) for a in extra]
    with tempfile.TemporaryDirectory() as td:
        try:
            p = subprocess.run(
                cmd + ["-J", "--skip-download", "--no-playlist", "--no-warnings", watch_url(vid)],
                capture_output=True, text=True, timeout=180,
            )
        except subprocess.TimeoutExpired:
            raise TierError("yt-dlp timed out reading video info")
        if p.returncode != 0 or not p.stdout.strip():
            err = (p.stderr or "").strip().splitlines()
            msg = err[-1] if err else "unknown error"
            low = msg.lower()
            if any(x in low for x in ("private video", "video unavailable", "has been removed", "does not exist")):
                raise FatalVideoError(f"yt-dlp: {msg}")
            if "not a bot" in low or "sign in" in low:
                raise TierError("yt-dlp: YouTube asked for a bot check (common on cloud/VPN IPs). "
                                "On your own computer, set \"ytdlp_args\": [\"--cookies-from-browser\", \"chrome\"] "
                                "in the config to fix this for free.")
            raise TierError(f"yt-dlp could not read the video: {msg[:300]}")
        info = json.loads(p.stdout)
        meta = meta_from_ytdlp(info, vid)
        track = pick_track(info, cfg.get("languages") or ["en"])
        if not track:
            meta["_no_captions"] = True
            log.append("ytdlp: metadata OK, but the video has no captions on YouTube")
            return meta, None, None
        code, kind = track
        info_path = Path(td) / "info.json"
        info_path.write_text(p.stdout, encoding="utf-8")
        flag = "--write-subs" if kind == "manual" else "--write-auto-subs"
        try:
            p2 = subprocess.run(
                cmd + ["--skip-download", "--no-warnings", "--load-info-json", str(info_path), flag,
                       "--sub-langs", code, "--sub-format", "json3/vtt/best",
                       "-o", str(Path(td) / "sub.%(ext)s")],
                capture_output=True, text=True, timeout=180,
            )
        except subprocess.TimeoutExpired:
            raise_partial(meta, "yt-dlp timed out downloading captions", log)
        files = [f for f in glob.glob(str(Path(td) / "sub.*")) if not f.endswith("info.json")]
        if not files:
            err = (p2.stderr or "").strip().splitlines()
            raise_partial(meta, f"yt-dlp found captions ({code}) but could not download them: "
                          f"{err[-1] if err else 'no file written'}", log)
        f = files[0]
        raw = Path(f).read_text(encoding="utf-8", errors="replace")
        segs = parse_json3(raw) if f.endswith(".json3") else parse_vtt(raw)
        segs = clean_segments(segs)
        if not segs:
            raise_partial(meta, "yt-dlp caption file was empty", log)
        lang = code.replace("-orig", "")
        return meta, segs, {"method": "ytdlp", "kind": kind, "language": lang, "credits_used": 0}


class PartialMeta(TierError):
    def __init__(self, msg, meta):
        super().__init__(msg)
        self.meta = meta


def raise_partial(meta, msg, log):
    raise PartialMeta(msg, meta)


# --------------------------------------------------------------------------
# Tier 2: TranscriptAPI (captions only)
# --------------------------------------------------------------------------
TAPI = "https://transcriptapi.com/api/v2"


def tapi_get(path, key, params, retries=3):
    for attempt in range(retries + 1):
        status, hdrs, body = http("GET", TAPI + path, {"Authorization": f"Bearer {key}"}, params)
        if status in (408, 429, 503) and attempt < retries:
            wait = float(hdrs.get("retry-after", 2 ** attempt))
            time.sleep(min(wait, 30))
            continue
        return status, hdrs, body
    return status, hdrs, body


def tier_transcriptapi(vid: str, cfg: dict, need_meta: bool, log: list):
    key = cfg.get("transcriptapi_key")
    if not key:
        raise CredError("TRANSCRIPTAPI_KEY is not set")
    params = {"video_url": vid, "format": "json", "include_timestamp": "true", "send_metadata": "true"}
    langs = cfg.get("languages") or []
    if langs:
        params["language"] = ",".join(langs)
    status, _, body = tapi_get("/youtube/transcript", key, params)
    if status == 404 and isinstance(body, dict) and body.get("code") == "no_transcript_for_requested_languages":
        params.pop("language", None)
        status, _, body = tapi_get("/youtube/transcript", key, params)
    if looks_like_proxy_block(status, body):
        raise NetworkError(f"transcriptapi.com blocked by network (HTTP {status})")
    if status == 401:
        raise CredError("TranscriptAPI rejected the key (401). Check TRANSCRIPTAPI_KEY.")
    if status == 402:
        detail = body.get("detail") if isinstance(body, dict) else body
        msg = detail.get("message") if isinstance(detail, dict) else detail
        raise TierError(f"TranscriptAPI: payment required - {msg}")
    if status == 404:
        code = body.get("code") if isinstance(body, dict) else None
        if code == "video_unavailable":
            raise FatalVideoError("TranscriptAPI: video unavailable (private, deleted or not playable)")
        raise NoCaptions("TranscriptAPI: video has no captions on YouTube")
    if status != 200 or not isinstance(body, dict):
        raise TierError(f"TranscriptAPI HTTP {status}: {str(body)[:200]}")

    segs = clean_segments(body.get("transcript") or [])
    lang = str(body.get("language") or "")
    kind = "auto" if lang.startswith("asr") else "manual"
    lang = lang.replace("asr-", "").replace("asr", "") or None
    credits = 1
    meta = None
    if need_meta:
        md = body.get("metadata") or {}
        meta = {
            "video_id": vid, "url": watch_url(vid), "title": md.get("title"),
            "channel": md.get("author_name"), "channel_url": md.get("author_url"),
            "thumbnail": md.get("thumbnail_url"), "duration_seconds": body.get("length_seconds"),
            "description": "", "description_links": [], "chapters": [], "chapter_source": None,
            "tags": [], "meta_source": "transcriptapi",
        }
        s2, _, m2 = tapi_get("/youtube/video/metadata", key, {"video_url": vid, "include": "details"})
        if s2 == 200 and isinstance(m2, dict):
            credits += 1
            desc = m2.get("description") or ""
            det = m2.get("details") or {}
            links = [l.get("url") for l in (m2.get("descriptionLinks") or []) if l.get("url")]
            meta.update({
                "title": m2.get("title") or meta["title"],
                "channel": (m2.get("channel") or {}).get("name") or meta["channel"],
                "upload_date": norm_date(m2.get("publishDate")),
                "description": desc,
                "description_links": links or links_from_description(desc),
                "tags": det.get("tags") or [],
                "categories": [det["category"]] if det.get("category") else [],
                "duration_seconds": det.get("lengthSeconds") or meta["duration_seconds"],
                "view_count": m2.get("viewCountText"),
            })
            ch = chapters_from_description(desc)
            meta["chapters"], meta["chapter_source"] = ch, ("description" if ch else None)
        else:
            log.append(f"transcriptapi: metadata call failed (HTTP {s2}); description unavailable")
    if not segs:
        raise TierError("TranscriptAPI returned an empty transcript")
    return meta, segs, {"method": "transcriptapi", "kind": kind, "language": lang, "credits_used": credits}


# --------------------------------------------------------------------------
# Tier 3: Supadata (captions or AI transcription)
# --------------------------------------------------------------------------
SUPA = "https://api.supadata.ai/v1"


def supa_get(path, key, params=None):
    return http("GET", SUPA + path, {"x-api-key": key}, params, timeout=180)


def supa_err(status, body):
    if isinstance(body, dict):
        return f"{body.get('error', '')}: {body.get('message', '')} {body.get('details', '')}".strip()
    return str(body)[:200]


def tier_supadata(vid: str, cfg: dict, need_meta: bool, log: list):
    key = cfg.get("supadata_key")
    if not key:
        raise CredError("SUPADATA_API_KEY is not set")
    params = {"url": watch_url(vid), "mode": "auto", "text": "false"}
    langs = cfg.get("languages") or []
    if langs:
        params["lang"] = langs[0]
    status, hdrs, body = supa_get("/transcript", key, params)
    if looks_like_proxy_block(status, body):
        raise NetworkError(f"api.supadata.ai blocked by network (HTTP {status})")
    if status == 401:
        raise CredError("Supadata rejected the key (401). Check SUPADATA_API_KEY.")
    if status in (403, 404):
        raise FatalVideoError(f"Supadata: video not accessible ({supa_err(status, body)})")
    billed = hdrs.get("x-billable-requests")
    ai = False
    if status == 202 and isinstance(body, dict) and body.get("jobId"):
        ai = True
        job = body["jobId"]
        print(f"[supadata] AI transcription job {job} started (estimated credits: {billed}). Polling...",
              flush=True)
        deadline = time.time() + int(cfg.get("supadata_poll_timeout_seconds") or 1800)
        while True:
            time.sleep(3)
            s2, _, b2 = supa_get(f"/transcript/{job}", key)
            st = b2.get("status") if isinstance(b2, dict) else None
            if s2 == 200 and st == "completed":
                body = b2.get("result") if isinstance(b2.get("result"), dict) else b2
                break
            if st == "failed" or s2 >= 400:
                raise TierError(f"Supadata job failed: {b2.get('error') if isinstance(b2, dict) else b2}")
            if time.time() > deadline:
                raise TierError(f"Supadata job {job} still running after timeout; re-run later")
    elif status == 206:
        raise TierError("Supadata: transcript unavailable for this video")
    elif status != 200:
        raise TierError(f"Supadata HTTP {status}: {supa_err(status, body)}")

    content = body.get("content") if isinstance(body, dict) else None
    if isinstance(content, str):
        segs = [{"start": 0, "text": content}]
    else:
        segs = [{"start": (c.get("offset") or 0) / 1000.0, "text": c.get("text", "")} for c in (content or [])]
    segs = clean_segments(segs)
    if not segs:
        raise TierError("Supadata returned no speech for this video")
    try:
        if billed is not None and float(billed) > 1:
            ai = True
    except ValueError:
        pass
    kind = "ai-generated" if ai else "captions-or-ai"
    meta = None
    if need_meta:
        s3, _, m = supa_get("/youtube/video", key, {"id": vid})
        if s3 == 200 and isinstance(m, dict):
            desc = m.get("description") or ""
            ch = chapters_from_description(desc)
            meta = {
                "video_id": vid, "url": watch_url(vid), "title": m.get("title"),
                "channel": (m.get("channel") or {}).get("name"),
                "channel_url": f"https://www.youtube.com/channel/{(m.get('channel') or {}).get('id')}"
                if (m.get("channel") or {}).get("id") else None,
                "upload_date": norm_date(m.get("uploadDate")), "duration_seconds": m.get("duration"),
                "tags": m.get("tags") or [], "thumbnail": m.get("thumbnail"),
                "view_count": m.get("viewCount"), "description": desc,
                "description_links": links_from_description(desc), "chapters": ch,
                "chapter_source": "description" if ch else None, "meta_source": "supadata",
            }
        else:
            log.append(f"supadata: metadata call failed (HTTP {s3})")
    return meta, segs, {
        "method": "supadata", "kind": kind, "language": (body or {}).get("lang"),
        "credits_used": billed,
    }


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------
CRED_HELP = {
    "transcriptapi": (
        "TranscriptAPI (YouTube captions when yt-dlp is blocked)",
        "TRANSCRIPTAPI_KEY", "transcriptapi_key", "https://transcriptapi.com/signup",
    ),
    "supadata": (
        "Supadata (AI transcription for videos without captions)",
        "SUPADATA_API_KEY", "supadata_key", "https://dash.supadata.ai",
    ),
}


def creds_block(missing: list[str], cfg: dict) -> str:
    lines = ["", "=== CREDENTIALS NEEDED ==="]
    for name in missing:
        title, env, ckey, url = CRED_HELP[name]
        lines += [
            f"* {title}: key not set or invalid.",
            f"    Get a key : {url}",
            f"    Set it    : export {env}=\"...\"   (e.g. in ~/.zshrc)",
            f"           or : add \"{ckey}\": \"...\" to {cfg['_config_path']}",
        ]
    lines.append("Ask the user to set the key(s), then run this command again.")
    lines.append("=== END CREDENTIALS NEEDED ===")
    return "\n".join(lines)


def merge_meta(base, extra):
    if not base:
        return extra
    if extra:
        for k, v in extra.items():
            if base.get(k) in (None, "", [], {}) and v not in (None, "", [], {}):
                base[k] = v
    return base


def run_tiers(vid: str, cfg: dict, tiers: list[str]):
    log, missing, net_fail = [], [], []
    meta = segs = tinfo = None
    no_captions = False
    for tier in tiers:
        if segs:
            break
        if tier == "transcriptapi" and no_captions:
            log.append("transcriptapi: skipped (video has no YouTube captions; it can only fetch captions)")
            continue
        try:
            if tier == "ytdlp":
                print("[tier 1/3] yt-dlp ...", flush=True)
                m, s, t = tier_ytdlp(vid, cfg, log)
                meta = merge_meta(meta, m)
                if m and m.get("_no_captions"):
                    no_captions = True
                if s:
                    segs, tinfo = s, t
            elif tier == "transcriptapi":
                print("[tier 2/3] TranscriptAPI ...", flush=True)
                m, s, t = tier_transcriptapi(vid, cfg, need_meta=meta is None, log=log)
                meta, segs, tinfo = merge_meta(meta, m), s, t
            elif tier == "supadata":
                print("[tier 3/3] Supadata (captions, else AI transcription) ...", flush=True)
                m, s, t = tier_supadata(vid, cfg, need_meta=meta is None, log=log)
                meta, segs, tinfo = merge_meta(meta, m), s, t
            else:
                log.append(f"unknown tier '{tier}' ignored")
        except PartialMeta as e:
            meta = merge_meta(meta, e.meta)
            log.append(f"{tier}: {e}")
        except NoCaptions as e:
            no_captions = True
            log.append(f"{tier}: {e}")
        except CredError as e:
            missing.append(tier)
            log.append(f"{tier}: {e}")
            print(f"  ! {tier}: {e}", flush=True)
        except NetworkError as e:
            net_fail.append(tier)
            log.append(f"{tier}: {e}")
        except TierError as e:
            log.append(f"{tier}: {e}")
    return meta, segs, tinfo, log, missing, net_fail


def group_paragraphs(segs, chapters):
    """Yield (chapter_title_or_None, chapter_start, [(start, text)...]) groups."""
    bounds = sorted(chapters or [], key=lambda c: c["start"])
    groups = []
    ci = -1
    cur = {"title": None, "start": 0, "paras": []}
    para, para_start, para_len = [], None, 0
    def flush_para():
        nonlocal para, para_start, para_len
        if para:
            cur["paras"].append((para_start, " ".join(para)))
        para, para_start, para_len = [], None, 0
    for s in segs:
        while ci + 1 < len(bounds) and s["start"] >= bounds[ci + 1]["start"]:
            flush_para()
            if cur["paras"] or cur["title"]:
                groups.append(cur)
            ci += 1
            cur = {"title": bounds[ci]["title"], "start": bounds[ci]["start"], "paras": []}
        if para_start is None:
            para_start = s["start"]
        para.append(s["text"])
        para_len += len(s["text"])
        if para_len > 700 or (s["start"] - para_start > 60 and para_len > 250):
            flush_para()
    flush_para()
    groups.append(cur)
    return groups


def yq(v):
    return json.dumps(v, ensure_ascii=False) if v not in (None, "") else '""'


def render_transcript_md(meta, segs, tinfo):
    vid = meta["video_id"]
    title = meta.get("title") or vid
    dur = C.fmt_ts(meta.get("duration_seconds")) if meta.get("duration_seconds") else ""
    fm = [
        "---",
        "type: yt-transcript",
        f"video_id: {yq(vid)}",
        f"title: {yq(title)}",
        f"channel: {yq(meta.get('channel'))}",
        f"url: {yq(meta.get('url'))}",
        f"upload_date: {yq(meta.get('upload_date'))}",
        f"duration: {yq(dur)}",
        f"language: {yq(tinfo.get('language'))}",
        f"transcript_method: {yq(tinfo.get('method'))}",
        f"transcript_kind: {yq(tinfo.get('kind'))}",
        f"fetched: {yq(tinfo.get('fetched_at'))}",
        "tags: [yt-transcript]",
        "---",
        "",
        f"# {title}",
        "",
    ]
    ch = f"[{meta.get('channel')}]({meta.get('channel_url')})" if meta.get("channel_url") else (meta.get("channel") or "?")
    fm.append(f"**Video:** {meta.get('url')} · **Channel:** {ch} · **Published:** {meta.get('upload_date') or '?'}"
              f" · **Duration:** {dur or '?'}")
    fm.append(f"**Transcript source:** {tinfo.get('method')} ({tinfo.get('kind')}, {tinfo.get('language') or '?'})")
    if tinfo.get("kind") in ("auto", "auto-translated", "ai-generated", "captions-or-ai"):
        fm.append("> Machine-generated transcript: technical terms and names may be misheard.")
    fm.append("")
    if meta.get("description"):
        fm += ["## Description", ""] + [f"> {l}" if l.strip() else ">" for l in meta["description"].splitlines()] + [""]
    if meta.get("description_links"):
        fm += ["## Links in description", ""] + [f"- {l}" for l in meta["description_links"]] + [""]
    if meta.get("chapters"):
        fm += [f"## Chapters ({meta.get('chapter_source')})", ""]
        fm += [f"- {C.fmt_ts(c['start'])} {c['title']}" for c in meta["chapters"]] + [""]
    fm += ["## Transcript", ""]
    for g in group_paragraphs(segs, meta.get("chapters")):
        if g["title"]:
            fm += [f"### {g['title']} ({C.fmt_ts(g['start'])})", ""]
        for start, text in g["paras"]:
            fm += [f"**[{C.fmt_ts(start)}]** {text}", ""]
    return "\n".join(fm)


def find_cached(cfg, vid):
    src = cfg["_sources"]
    if not src.exists():
        return None
    for d in src.iterdir():
        # "<Title>_<id>" (current) or "<Title> - <id>" (older versions)
        if d.is_dir() and (d.name.endswith(f"_{vid}") or d.name.endswith(f" - {vid}")) \
                and (d / "meta.json").exists():
            return d
    return None


def transcript_md_name(folder: Path, vid: str) -> str:
    """Name of the transcript markdown in a package (handles the older "transcript - <id>.md")."""
    for name in (f"transcript_{vid}.md", f"transcript - {vid}.md"):
        if (folder / name).exists():
            return name
    return f"transcript_{vid}.md"


def write_package(cfg, meta, segs, tinfo, log):
    vid = meta["video_id"]
    old = find_cached(cfg, vid)
    folder = cfg["_sources"] / f"{C.safe_name(meta.get('title') or vid)}_{vid}"
    if old and old != folder:
        shutil.rmtree(old, ignore_errors=True)
    folder.mkdir(parents=True, exist_ok=True)
    tinfo["fetched_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    tinfo["segment_count"] = len(segs)
    clean_meta = {k: v for k, v in meta.items() if not k.startswith("_")}
    record = {**clean_meta, "transcript": tinfo, "fetch_log": log}
    (folder / "meta.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    (folder / "transcript.json").write_text(json.dumps(segs, ensure_ascii=False), encoding="utf-8")
    md_name = f"transcript_{vid}.md"
    legacy = folder / f"transcript - {vid}.md"
    if legacy.exists():
        legacy.unlink()
    (folder / md_name).write_text(render_transcript_md(clean_meta, segs, tinfo), encoding="utf-8")
    return folder, md_name


def result_summary(cfg, folder, md_name, meta, tinfo, log, warnings, cached=False):
    words = 0
    try:
        words = sum(len(s["text"].split()) for s in json.loads((folder / "transcript.json").read_text()))
    except Exception:
        pass
    return {
        "status": "cached" if cached else "ok",
        "video_id": meta.get("video_id"),
        "title": meta.get("title"),
        "channel": meta.get("channel"),
        "duration": C.fmt_ts(meta.get("duration_seconds")) if meta.get("duration_seconds") else None,
        "chapters": len(meta.get("chapters") or []),
        "transcript_method": tinfo.get("method"),
        "transcript_kind": tinfo.get("kind"),
        "language": tinfo.get("language"),
        "transcript_words": words,
        "credits_used": tinfo.get("credits_used"),
        "notes_root": str(cfg["_root"]),
        "drive_root": cfg["drive_root"],
        "environment": cfg["_env"],
        "source_dir": str(folder),
        "files": {
            "meta": str(folder / "meta.json"),
            "transcript_md": str(folder / md_name),
            "transcript_json": str(folder / "transcript.json"),
        },
        "warnings": warnings,
        "log": log,
    }


def emit(result, code=0):
    print("\n=== RESULT JSON ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=== END RESULT ===")
    return code


def do_ingest(path: str, cfg):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    vid = data.get("video_id") or extract_video_id(data.get("url", ""))
    if not vid:
        print("ERROR: ingest file needs video_id or url", file=sys.stderr)
        return None
    m = data.get("meta") or {}
    desc = m.get("description") or ""
    chapters = m.get("chapters") or chapters_from_description(desc)
    meta = {
        "video_id": vid, "url": watch_url(vid), "title": m.get("title"), "channel": m.get("channel"),
        "channel_url": m.get("channel_url"), "upload_date": norm_date(m.get("upload_date")),
        "duration_seconds": m.get("duration_seconds"), "language": data.get("language"),
        "tags": m.get("tags") or [], "thumbnail": m.get("thumbnail"), "description": desc,
        "description_links": m.get("description_links") or links_from_description(desc),
        "chapters": chapters, "chapter_source": m.get("chapter_source") or ("description" if chapters else None),
        "meta_source": data.get("method", "connector"),
    }
    if data.get("segments"):
        segs = clean_segments(data["segments"])
    else:
        segs = clean_segments([{"start": 0, "text": data.get("text", "")}])
    tinfo = {"method": data.get("method", "connector"), "kind": data.get("kind", "unknown"),
             "language": data.get("language"), "credits_used": data.get("credits_used")}
    return meta, segs, tinfo


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", nargs="?", help="YouTube URL or 11-char video ID")
    ap.add_argument("--where", action="store_true", help="print save location and exit")
    ap.add_argument("--force", action="store_true", help="re-fetch even if cached")
    ap.add_argument("--root", help="override notes root for this run")
    ap.add_argument("--tiers", help="comma list, e.g. ytdlp,supadata")
    ap.add_argument("--ingest", help="JSON file with data gathered via MCP connectors")
    args = ap.parse_args()

    cfg = C.load(SKILL_DIR, root_override=args.root)
    print(C.location_banner(cfg), flush=True)
    if args.where:
        return emit({"status": "where", "notes_root": str(cfg["_root"]), "sources_dir": str(cfg["_sources"]),
                     "config_path": str(cfg["_config_path"]), "environment": cfg["_env"],
                     "drive_root": cfg["drive_root"],
                     "keys_configured": {"transcriptapi": bool(cfg.get("transcriptapi_key")),
                                         "supadata": bool(cfg.get("supadata_key"))}})

    if args.ingest:
        got = do_ingest(args.ingest, cfg)
        if not got:
            return 5
        meta, segs, tinfo = got
        if not segs:
            print("ERROR: ingest file has no transcript text", file=sys.stderr)
            return 5
        folder, md = write_package(cfg, meta, segs, tinfo, ["ingested from connector data"])
        print(f"\nSaved to: {folder}")
        return emit(result_summary(cfg, folder, md, meta, tinfo, ["ingested from connector data"], []))

    vid = extract_video_id(args.url or "")
    if not vid:
        print(f"ERROR: could not find a YouTube video ID in: {args.url!r}", file=sys.stderr)
        return 5

    cached = find_cached(cfg, vid)
    if cached and not args.force:
        rec = json.loads((cached / "meta.json").read_text(encoding="utf-8"))
        md = transcript_md_name(cached, vid)
        print(f"\nAlready fetched earlier - reusing: {cached}  (use --force to re-fetch)")
        return emit(result_summary(cfg, cached, md, rec, rec.get("transcript", {}), rec.get("fetch_log", []),
                                   [], cached=True))

    tiers = [t.strip() for t in args.tiers.split(",")] if args.tiers else list(cfg.get("tiers") or [])
    try:
        meta, segs, tinfo, log, missing, net_fail = run_tiers(vid, cfg, tiers)
    except FatalVideoError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return emit({"status": "video_unavailable", "video_id": vid, "error": str(e)}, 2)

    if not segs:
        print("\nCould not get a transcript. Attempts:")
        for l in log:
            print(f"  - {l}")
        api_tiers = [t for t in tiers if t != "ytdlp"]
        if missing:
            print(creds_block(missing, cfg))
            return emit({"status": "credentials_needed", "video_id": vid, "missing": missing, "log": log}, 3)
        if api_tiers and set(net_fail) >= set(api_tiers):
            print("\nThe transcript APIs are unreachable from this environment. Use the connector path "
                  "(TranscriptAPI / Supadata MCP connector) and --ingest, as described in SKILL.md.")
            return emit({"status": "network_blocked", "video_id": vid, "log": log}, 4)
        return emit({"status": "failed", "video_id": vid, "log": log}, 2)

    if not meta:
        meta = {"video_id": vid, "url": watch_url(vid), "title": vid, "chapters": []}
    meta.setdefault("video_id", vid)
    meta.setdefault("url", watch_url(vid))
    warnings = []
    for t in missing:
        warnings.append(f"{CRED_HELP[t][0]} key is not set - that fallback was skipped. "
                        f"Set {CRED_HELP[t][1]} to enable it.")
    if tinfo.get("kind") in ("auto-translated",):
        warnings.append("Transcript is YouTube's machine translation of auto-captions; quality may be low.")
    folder, md = write_package(cfg, meta, segs, tinfo, log)
    print(f"\nSaved to: {folder}")
    return emit(result_summary(cfg, folder, md, meta, tinfo, log, warnings))


if __name__ == "__main__":
    sys.exit(main())
