#!/usr/bin/env python3
"""Fetch blog posts and save each one as a "source package" for blog-notes.

  fetch_article.py --where                       # print the save location
  fetch_article.py <url> [<url> ...]             # fetch (reuses saved packages)
      [--force] [--tiers local,supadata] [--root PATH] [--no-images]
  fetch_article.py --from-file <file.md|.html> --url <url> [--title "Title"] [--trust]
      # save scraped text (e.g. from the Supadata connector), or with --trust text the
      # user pasted / a page they saved themselves (paywalls, blocked sites)

Package: <notes_root>/_sources/<Post_Title>_<urlhash>/
  meta.json               title, author, site, dates, url, word counts, fetch method, warnings, images
  article_<urlhash>.md    the article as markdown (readable in Obsidian)
  images/                 the article's images (at most 20 and 5 MB)

Tiers: "local" (free: download + extract here) then "supadata" (1 credit:
Supadata web scrape API, key in SUPADATA_API_KEY or config "supadata_key").

Output ends with a JSON block between "=== RESULT JSON ===" and "=== END RESULT ===".
Exit codes: 0 at least one post saved (see each post's status: ok, cached,
truncated, failed) | 2 all failed | 3 all failed and a Supadata key is needed |
4 all failed because the network is blocked | 5 bad input (not a web URL, or a
YouTube link, which belongs to yt-notes).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import socket
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlunparse

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import article_extract as X  # noqa: E402
import ytn_config as C  # noqa: E402

USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
SUPADATA_SCRAPE = "https://api.supadata.ai/v1/web/scrape"
MAX_IMAGES = 20
MAX_IMAGE_BYTES = 5 * 1024 * 1024
TRACKING = re.compile(r"^(utm_.*|ref|ref_src|source|fbclid|gclid|mc_cid|mc_eid|igshid|si)$", re.I)


class NetworkError(Exception):
    """The request never reached the server (DNS, refused, sandbox egress block)."""


class TierError(Exception):
    """This tier could not get the article (HTTP error, not HTML, empty...)."""


class CredentialsMissing(Exception):
    """A paid tier is configured but its API key isn't set."""


# ------------------------------------------------------------------ urls
def normalize_url(url: str) -> str:
    p = urlparse(url.strip())
    query = urlencode([(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not TRACKING.match(k)])
    path = p.path or "/"
    if len(path) > 1:
        path = path.rstrip("/")
    return urlunparse((p.scheme.lower(), p.netloc.lower(), path, "", query, ""))


def url_hash(url: str) -> str:
    return hashlib.sha1(normalize_url(url).encode("utf-8")).hexdigest()[:10]


def is_youtube(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return host.endswith("youtube.com") or host.endswith("youtu.be") or host.endswith("youtube-nocookie.com")


def is_web_url(url: str) -> bool:
    p = urlparse(url)
    return p.scheme in ("http", "https") and bool(p.netloc)


# ------------------------------------------------------------------ http
def http_get(url: str, headers: dict | None = None, timeout: int = 20):
    """GET a URL -> (status, content_type, body). Raises NetworkError if the server can't be reached."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", "") if e.headers else "", e.read() if e.fp else b""
    except (urllib.error.URLError, socket.timeout, ConnectionError, OSError) as e:
        raise NetworkError(str(getattr(e, "reason", e))) from e


# ------------------------------------------------------------------ cache
def find_cached(sources: Path, url: str) -> Path | None:
    if not sources.is_dir():
        return None
    h = url_hash(url)
    for d in sources.iterdir():
        if d.is_dir() and d.name.endswith("_" + h) and (d / "meta.json").exists():
            return d
    for m in sources.glob("*/meta.json"):
        try:
            if h in json.loads(m.read_text(encoding="utf-8")).get("url_hashes", []):
                return m.parent
        except (ValueError, OSError):
            continue
    return None


# ------------------------------------------------------------------ tiers
def tier_local(url: str, cfg: dict) -> dict:
    status, ctype, body = http_get(url, {"Accept": "text/html,application/xhtml+xml"})
    if status != 200:
        raise TierError(f"local: HTTP {status}" + (" (the site blocks automated requests)" if status in (401, 403, 429) else ""))
    if ctype and "html" not in ctype.lower() and "xml" not in ctype.lower():
        raise TierError(f"local: not an HTML page ({ctype})")
    return X.extract(X.decode_html(body, ctype), url)


def _md_title(md: str) -> str | None:
    m = re.search(r"^#\s+(.+)$", md or "", re.M)
    return m.group(1).strip() if m else None


def _strip_title(md: str, title: str) -> str:
    """Drop a leading '# Title' line (the package writes its own)."""
    lines = (md or "").lstrip().splitlines()
    if lines and lines[0].startswith("# ") and lines[0][2:].strip().lower() == (title or "").strip().lower():
        lines = lines[1:]
    return "\n".join(lines).strip()


def article_from_markdown(md: str, url: str, title: str | None = None) -> dict:
    title = title or _md_title(md) or url
    body = _strip_title(md, title)
    host = urlparse(url).netloc.lower()
    images = []
    for alt, src in re.findall(r"!\[([^\]]*)\]\(([^)\s]+)", body):
        if src.startswith("http") and not any(i["src"] == src for i in images):
            images.append({"src": src, "alt": alt})
    words = len(re.findall(r"\w+", re.sub(r"```.*?```", " ", body, flags=re.S)))
    return {"title": title, "author": None, "site": host[4:] if host.startswith("www.") else host,
            "published": None, "updated": None, "canonical_url": url, "markdown": body,
            "images": images, "word_count": words, "page_word_count": 0}


def tier_supadata(url: str, cfg: dict) -> dict:
    key = cfg.get("supadata_key")
    if not key:
        raise CredentialsMissing("supadata")
    status, _, body = http_get(f"{SUPADATA_SCRAPE}?url={quote(url, safe='')}", {"x-api-key": key, "Accept": "application/json"}, timeout=60)
    if status in (401, 403):
        raise TierError("supadata: the API key was rejected")
    if status != 200:
        raise TierError(f"supadata: HTTP {status}: {body[:200].decode('utf-8', 'replace')}")
    try:
        data = json.loads(body)
    except ValueError as e:
        raise TierError(f"supadata: bad response ({e})") from e
    content = data.get("content") or ""
    if not content.strip():
        raise TierError("supadata: returned no content")
    return article_from_markdown(content, url, data.get("name") or None)


TIERS = {"local": tier_local, "supadata": tier_supadata}


# ------------------------------------------------------------------ package
def _image_name(i: int, src: str, ctype: str) -> str:
    base = Path(urlparse(src).path).name or f"image{i}"
    stem, ext = Path(base).stem, Path(base).suffix.lower()
    if not ext or len(ext) > 5:
        ext = mimetypes.guess_extension((ctype or "").split(";")[0].strip()) or ".img"
    return f"{i:02d}_{C.safe_name(stem, 40)}{ext}"


def download_images(images: list[dict], dest: Path, warnings: list[str]) -> None:
    total, saved = 0, 0
    for img in images:
        if saved >= MAX_IMAGES:
            warnings.append(f"only the first {MAX_IMAGES} images were saved")
            break
        src = img["src"]
        try:
            status, ctype, body = http_get(src, {"Accept": "image/*"})
        except NetworkError as e:
            warnings.append(f"image not saved ({src}): {e}")
            continue
        if status != 200 or (ctype and not ctype.lower().startswith("image/")):
            warnings.append(f"image not saved ({src}): HTTP {status} {ctype}".strip())
            continue
        if total + len(body) > MAX_IMAGE_BYTES:
            warnings.append(f"image not saved ({src}): over the {MAX_IMAGE_BYTES // (1024 * 1024)} MB image budget")
            continue
        dest.mkdir(parents=True, exist_ok=True)
        name = _image_name(saved + 1, src, ctype)
        (dest / name).write_bytes(body)
        img["file"] = f"images/{name}"
        total += len(body)
        saved += 1


def write_package(sources: Path, article: dict, url: str, fetch_method: str, warnings: list[str],
                  fetch_images: bool = True, truncated: bool = False) -> Path:
    canonical = article.get("canonical_url") or url
    h = url_hash(canonical)
    folder = sources / f"{C.safe_name(article['title'], 80)}_{h}"
    old = find_cached(sources, url) or find_cached(sources, canonical)
    if old and old != folder:  # re-fetch of a post whose title changed: keep one folder
        folder = old
    folder.mkdir(parents=True, exist_ok=True)

    images = [dict(i) for i in article.get("images", [])]
    if fetch_images and images:
        download_images(images, folder / "images", warnings)
    md = article["markdown"]
    for img in images:
        if img.get("file"):
            md = md.replace(f"]({img['src']})", f"]({img['file']})")

    hashes = sorted({h, url_hash(url)})
    meta = {k: article.get(k) for k in ("title", "author", "site", "published", "updated", "canonical_url",
                                        "word_count", "page_word_count")}
    meta.update({"url": url, "url_hashes": hashes, "truncated": truncated, "hash": h, "fetch_method": fetch_method,
                 "warnings": warnings, "fetched": date.today().isoformat(),
                 "article_file": f"article_{h}.md", "images": images})
    (folder / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    fm = {"title": article["title"], "source_url": url, "author": article.get("author") or "",
          "site": article.get("site") or "", "published": article.get("published") or "", "fetch_method": fetch_method}
    lines = ["---"] + [f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in fm.items()] + ["---", "",
                                                                                              f"# {article['title']}", ""]
    if warnings:
        lines += ["> [!warning] Fetch warnings", *[f"> - {w}" for w in warnings], ""]
    (folder / f"article_{h}.md").write_text("\n".join(lines) + md.strip() + "\n", encoding="utf-8")
    return folder


# ------------------------------------------------------------------ fetching one post
def fetch_one(url: str, cfg: dict, tiers: list[str], force: bool, fetch_images: bool, log: list[str]) -> dict:
    sources: Path = cfg["_sources"]
    result = {"url": url, "status": "failed", "source_dir": None, "title": None, "word_count": 0,
              "fetch_method": None, "warnings": [], "error": None, "credits": 0}
    if not force:
        cached = find_cached(sources, url)
        if cached:
            meta = json.loads((cached / "meta.json").read_text(encoding="utf-8"))
            truncated = meta.get("truncated")
            if truncated is None:  # packages saved before the flag existed
                truncated = bool(meta.get("warnings")) and meta.get("fetch_method") != "user-provided"
            result.update(status="truncated" if truncated else "cached", source_dir=str(cached), title=meta.get("title"),
                          word_count=meta.get("word_count", 0), fetch_method=meta.get("fetch_method"),
                          warnings=meta.get("warnings", []))
            log.append(f"{url}: reusing saved package {cached.name}")
            return result

    best, kinds = None, []
    for tier in tiers:
        fn = TIERS.get(tier)
        if not fn:
            log.append(f"{url}: unknown tier {tier!r} skipped")
            continue
        try:
            art = fn(url, cfg)
        except CredentialsMissing:
            kinds.append("credentials")
            log.append(f"{url}: {tier}: skipped, no API key set")
            continue
        except NetworkError as e:
            kinds.append("network")
            log.append(f"{url}: {tier}: network error: {e}")
            continue
        except TierError as e:
            kinds.append("failed")
            log.append(f"{url}: {e}")
            continue
        if tier == "supadata":
            result["credits"] += 1
        warns = X.paywall_warnings(art["markdown"], art["word_count"], art.get("page_word_count", 0))
        log.append(f"{url}: {tier}: {art['word_count']} words" + (f" ({'; '.join(warns)})" if warns else ""))
        if best is None or (not warns and best[2]) or (bool(warns) == bool(best[2]) and art["word_count"] > best[0]["word_count"]):
            best = (art, tier, warns)
        if not warns:
            break

    if best is None:
        if "credentials" in kinds:
            result["error"] = "credentials"
        elif kinds and all(k == "network" for k in kinds):
            result["error"] = "network"
        else:
            result["error"] = "failed"
        return result

    art, tier, warns = best
    truncated = bool(warns)
    warns = list(warns)
    folder = write_package(sources, art, url, tier, warns, fetch_images, truncated)
    result.update(status="truncated" if truncated else "ok",
                  source_dir=str(folder), title=art["title"], word_count=art["word_count"], fetch_method=tier,
                  warnings=warns)
    return result


# ------------------------------------------------------------------ main
CREDENTIALS_MSG = """=== CREDENTIALS NEEDED ===
The page couldn't be read directly, and the fallback (Supadata web scrape, 1 credit per page) needs an API key.
  Key name : SUPADATA_API_KEY  (or "supadata_key" in ~/.yt-notes/config.json)
  Sign up  : https://dash.supadata.ai
  Get key  : https://dash.supadata.ai/organizations/api-key
On claude.ai, use the Supadata connector instead (no key needed here).
Or paste the article text and save it with --from-file.
=== END CREDENTIALS ==="""


def emit(result: dict) -> None:
    print("=== RESULT JSON ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=== END RESULT ===")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fetch blog posts into source packages for blog-notes.")
    ap.add_argument("urls", nargs="*")
    ap.add_argument("--where", action="store_true", help="print where packages are saved and exit")
    ap.add_argument("--force", action="store_true", help="re-fetch even if a package exists")
    ap.add_argument("--tiers", help="comma list, e.g. local,supadata")
    ap.add_argument("--root", help="notes root for this run")
    ap.add_argument("--no-images", action="store_true", help="don't download the article's images")
    ap.add_argument("--from-file", help="markdown or HTML file with the article (pasted or saved by the user)")
    ap.add_argument("--url", help="the post's URL, with --from-file")
    ap.add_argument("--title", help="the post's title, with --from-file")
    ap.add_argument("--trust", action="store_true",
                    help="with --from-file: the user pasted or saved the full article, so don't mark it truncated")
    a = ap.parse_args(argv)

    cfg = C.load(SKILL_DIR, a.root)
    if a.where:
        print(C.location_banner(cfg))
        return 0

    if a.from_file:
        if not a.url or not is_web_url(a.url):
            print("ERROR: --from-file needs --url <the post's http(s) URL>")
            return 5
        raw = Path(a.from_file).expanduser().read_bytes()
        if raw.lstrip(b"\xef\xbb\xbf \t\r\n").startswith(b"<"):
            art = X.extract(X.decode_html(raw, None), a.url)
            if a.title:
                art["title"] = a.title
        else:
            art = article_from_markdown(raw.decode("utf-8", errors="replace").lstrip("\ufeff"), a.url, a.title)
        warns = X.paywall_warnings(art["markdown"], art["word_count"], art.get("page_word_count", 0))
        truncated = bool(warns) and not a.trust
        method = "user-provided" if a.trust else "from-file"
        folder = write_package(cfg["_sources"], art, a.url, method, warns, not a.no_images, truncated)
        emit({"posts": [{"url": a.url, "status": "truncated" if truncated else "ok", "source_dir": str(folder), "title": art["title"],
                         "word_count": art["word_count"], "fetch_method": method, "warnings": warns,
                         "error": None}], "credits_used": 0})
        return 0

    if not a.urls:
        ap.print_usage()
        return 5
    bad = [u for u in a.urls if not is_web_url(u)]
    yt = [u for u in a.urls if is_web_url(u) and is_youtube(u)]
    if bad or yt:
        for u in bad:
            print(f"ERROR: not a web page URL: {u}")
        for u in yt:
            print(f"ERROR: {u} is a YouTube link; use the yt-notes skill for videos.")
        return 5

    urls, seen = [], set()
    for u in a.urls:
        n = normalize_url(u)
        if n not in seen:
            seen.add(n)
            urls.append(u)
    tiers = [t.strip() for t in a.tiers.split(",")] if a.tiers else list(cfg.get("article_tiers") or ["local"])

    print(C.location_banner(cfg))
    log: list[str] = []
    posts = [fetch_one(u, cfg, tiers, a.force, not a.no_images, log) for u in urls]
    for line in log:
        print("  " + line)
    credits = sum(p.pop("credits", 0) for p in posts)
    if any(p["error"] == "credentials" for p in posts):
        print(CREDENTIALS_MSG)
    emit({"posts": posts, "credits_used": credits})

    if any(p["status"] != "failed" for p in posts):
        return 0
    errors = {p["error"] for p in posts}
    if errors == {"credentials"}:
        return 3
    if errors == {"network"}:
        return 4
    return 2


if __name__ == "__main__":
    sys.exit(main())
