"""Shared configuration for the yt-transcript and yt-notes skills.

Both skills read the SAME user config file so transcripts and notes always land
under one root folder.

Resolution order (later wins; empty values never override):
  1. Built-in defaults (notes root = ~/YouTubeNotes)
  2. Skill config: config.json inside the yt-transcript skill folder, then one
     inside this skill's own folder. This is the file to edit on claude.ai,
     where it is the only config that persists; yt-notes reads yt-transcript's
     copy, so there is one file to edit.
  3. User config file: ~/.yt-notes/config.json (or $YT_NOTES_CONFIG), the file
     to edit on your own computer. Values still equal to the built-in defaults
     are ignored, so an untouched file never overrides the skill config.
  4. Environment variables: YT_NOTES_ROOT, TRANSCRIPTAPI_KEY, SUPADATA_API_KEY

On a local machine the user config file is created with defaults on first run
so it is easy to edit. In a cloud sandbox (claude.ai) it is not created,
because it would be lost when the session ends.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

DEFAULTS = {
    # Where everything is stored on this device. Edit to point at your
    # Google-Drive-synced folder, e.g.
    # "~/Library/CloudStorage/GoogleDrive-you@gmail.com/My Drive/Vault/YouTube Notes"
    "notes_root": "~/YouTubeNotes",
    # Folder path inside "My Drive" used when running in claude.ai (web, mobile,
    # desktop chat), where files are uploaded with the Google Drive connector.
    # Should be the Drive-side twin of notes_root.
    "drive_root": "YouTubeNotes",
    # How yt-notes writes notes: "html" (default) = a rich single-page note with
    # tabs, illustrations and animations, plus a small markdown card for
    # Obsidian search; "markdown" = an Obsidian markdown note with HTML-snippet illustrations.
    "note_format": "html",
    # Optional: absolute path of the Obsidian vault that contains notes_root.
    # Usually not needed: it is found automatically by looking for a .obsidian
    # folder above notes_root.
    "obsidian_vault_root": "",
    # Most videos yt-notes combines into one note.
    "max_videos": 5,
    # Preferred transcript languages, in order.
    "languages": ["en"],
    # Order of transcript sources to try.
    "tiers": ["ytdlp", "transcriptapi", "supadata"],
    # Extra yt-dlp arguments. If YouTube says "Sign in to confirm you're not a
    # bot", use your browser's cookies: ["--cookies-from-browser", "chrome"]
    "ytdlp_args": [],
    # API keys (environment variables take precedence).
    "transcriptapi_key": "",
    "supadata_key": "",
    # Max time to wait for a Supadata AI transcription job.
    "supadata_poll_timeout_seconds": 1800,
}

SECRET_KEYS = {"transcriptapi_key", "supadata_key"}
SOURCES_DIRNAME = "_sources"


def user_config_path() -> Path:
    return Path(os.environ.get("YT_NOTES_CONFIG", "~/.yt-notes/config.json")).expanduser()


def _merge(base: dict, extra: dict, skip_defaults: bool = False) -> bool:
    """Merge non-empty values into base. Returns True if anything was applied."""
    applied = False
    for k, v in extra.items():
        if k.startswith("_"):
            continue
        if v in ("", None, [], {}):
            continue
        if skip_defaults and k in DEFAULTS and v == DEFAULTS[k]:
            continue
        base[k] = v
        applied = True
    return applied


def skill_config_paths(skill_dir: Path) -> list[Path]:
    """Skill-bundled config files, lowest priority first.

    yt-transcript's config.json is the shared one; a config.json in this
    skill's own folder (if any) is applied after it.
    """
    paths = []
    shared = skill_dir.parent / "yt-transcript" / "config.json"
    own = skill_dir / "config.json"
    for p in (shared, own):
        if p.exists() and p.resolve() not in [q.resolve() for q in paths]:
            paths.append(p)
    return paths


def _read_json(p: Path) -> dict:
    try:
        with p.open(encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception as e:  # malformed config should not kill the run
        print(f"WARNING: could not read config {p}: {e}", file=sys.stderr)
        return {}


def environment() -> str:
    """'cloud-sandbox' for claude.ai-style sandboxes (ephemeral disk), else 'local'."""
    if os.environ.get("YT_NOTES_ENV"):
        return os.environ["YT_NOTES_ENV"]
    if sys.platform.startswith("linux") and (
        os.path.isdir("/mnt/user-data") or os.path.isdir("/mnt/skills")
    ):
        return "cloud-sandbox"
    return "local"


def load(skill_dir: Path, root_override: str | None = None) -> dict:
    cfg = dict(DEFAULTS)
    cfg["_created_config"] = False
    cfg["_settings_from"] = []
    env = environment()

    for p in skill_config_paths(skill_dir):
        if _merge(cfg, _read_json(p)):
            cfg["_settings_from"].append(str(p))
    cfg["_skill_config"] = skill_dir.parent / "yt-transcript" / "config.json"

    ucp = user_config_path()
    if ucp.exists():
        if _merge(cfg, _read_json(ucp), skip_defaults=True):
            cfg["_settings_from"].append(str(ucp))
    elif env != "cloud-sandbox":
        try:
            ucp.parent.mkdir(parents=True, exist_ok=True)
            starter = {k: v for k, v in DEFAULTS.items()}
            starter["_help"] = (
                "Edit notes_root to change where transcripts and notes are saved. "
                "Keys may also be set via TRANSCRIPTAPI_KEY / SUPADATA_API_KEY env vars."
            )
            with ucp.open("w", encoding="utf-8") as f:
                json.dump(starter, f, indent=2)
            cfg["_created_config"] = True
        except OSError:
            pass

    env_map = {
        "YT_NOTES_ROOT": "notes_root",
        "TRANSCRIPTAPI_KEY": "transcriptapi_key",
        "SUPADATA_API_KEY": "supadata_key",
    }
    for var, key in env_map.items():
        if os.environ.get(var):
            cfg[key] = os.environ[var]

    if root_override:
        cfg["notes_root"] = root_override

    root = Path(os.path.expandvars(str(cfg["notes_root"]))).expanduser()
    cfg["_root"] = root
    cfg["_sources"] = root / SOURCES_DIRNAME
    cfg["_config_path"] = ucp
    cfg["_env"] = env
    if isinstance(cfg.get("languages"), str):
        cfg["languages"] = [s.strip() for s in cfg["languages"].split(",") if s.strip()]
    if isinstance(cfg.get("tiers"), str):
        cfg["tiers"] = [s.strip() for s in cfg["tiers"].split(",") if s.strip()]
    return cfg


def location_banner(cfg: dict) -> str:
    lines = [
        "=" * 60,
        "📁 YOUTUBE NOTES LOCATION",
        f"  Notes root  : {cfg['_root']}",
        f"  Transcripts : {cfg['_sources']}",
        f"  Environment : {cfg['_env']}",
    ]
    if cfg["_env"] == "cloud-sandbox":
        lines += [
            f"  Drive folder: My Drive/{cfg['drive_root']}  (this disk is temporary; results are saved there)",
            f"  Settings    : {cfg['_skill_config']}",
            "                (to change drive_root on claude.ai, edit config.json in the yt-transcript skill)",
        ]
    else:
        lines.append(f"  Config file : {cfg['_config_path']}  (edit \"notes_root\" to change)")
    if cfg.get("_settings_from"):
        lines.append("  Loaded from : " + ", ".join(cfg["_settings_from"]))
    if cfg.get("_created_config"):
        lines.append("  (Config file was just created with defaults.)")
    lines.append("=" * 60)
    return "\n".join(lines)


_BAD_CHARS = re.compile(r'[\\/:*?"<>|#^\[\]{}\x00-\x1f]')


def safe_name(text: str, max_len: int = 80) -> str:
    """Filesystem- and Obsidian-wikilink-safe name that stays human readable.

    Words are separated by underscores, never spaces:
    "Consistent Hashing - Explained!" -> "Consistent_Hashing_Explained!"
    """
    text = _BAD_CHARS.sub(" ", text or "")
    text = re.sub(r"\s+[-–—]+\s+", " ", text)   # " - " separators become a single break
    text = re.sub(r"[\s_]+", "_", text).strip("._- ")
    if len(text) > max_len:
        cut = text[:max_len].rsplit("_", 1)[0]
        text = cut if len(cut) > max_len * 0.6 else text[:max_len]
        text = text.strip("._-")
    return text or "Untitled"


def find_vault_root(start: Path, explicit: str = "") -> Path | None:
    """The Obsidian vault containing `start`: explicit setting, else the nearest
    folder (start or above) that has a .obsidian directory."""
    if explicit:
        p = Path(os.path.expandvars(explicit)).expanduser()
        return p if p.exists() else None
    try:
        cur = start.expanduser().resolve()
    except OSError:
        return None
    for d in [cur, *cur.parents]:
        if (d / ".obsidian").is_dir():
            return d
    return None


def display_name(name: str) -> str:
    """Folder/file name back to readable text for index pages: "System_Design" -> "System Design"."""
    return name.replace("_", " ")


def fmt_ts(seconds: float | int | None) -> str:
    if seconds is None:
        return ""
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"
