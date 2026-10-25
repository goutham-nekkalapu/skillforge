"""Shared configuration for the yt-transcript and yt-notes skills.

Both skills read the SAME user config file so transcripts and notes always land
under one root folder.

Resolution order (later wins, empty values never override):
  1. Built-in defaults (notes root = ~/YouTubeNotes)
  2. config.json bundled inside the skill folder (handy for claude.ai uploads)
  3. User config file: ~/.yt-notes/config.json  (or $YT_NOTES_CONFIG)
  4. Environment variables: YT_NOTES_ROOT, TRANSCRIPTAPI_KEY, SUPADATA_API_KEY

The user config file is created with defaults on first run so it is easy to edit.
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
    # Optional: absolute path of the Obsidian vault that contains notes_root.
    # When set, notes get an inline `html-embed` block for interactive files.
    "obsidian_vault_root": "",
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


def _merge(base: dict, extra: dict) -> None:
    for k, v in extra.items():
        if k.startswith("_"):
            continue
        if v in ("", None, [], {}):
            continue
        base[k] = v


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

    bundled = skill_dir / "config.json"
    if bundled.exists():
        _merge(cfg, _read_json(bundled))

    ucp = user_config_path()
    if ucp.exists():
        _merge(cfg, _read_json(ucp))
    else:
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
    for env, key in env_map.items():
        if os.environ.get(env):
            cfg[key] = os.environ[env]

    if root_override:
        cfg["notes_root"] = root_override

    root = Path(os.path.expandvars(str(cfg["notes_root"]))).expanduser()
    cfg["_root"] = root
    cfg["_sources"] = root / SOURCES_DIRNAME
    cfg["_config_path"] = ucp
    cfg["_env"] = environment()
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
        f"  Config file : {cfg['_config_path']}  (edit \"notes_root\" to change)",
        f"  Environment : {cfg['_env']}",
    ]
    if cfg["_env"] == "cloud-sandbox":
        lines.append(
            f"  NOTE: this disk is temporary. Copy results to Google Drive folder "
            f"'{cfg['drive_root']}' (My Drive) with the Drive connector."
        )
    if cfg.get("_created_config"):
        lines.append("  (Config file was just created with defaults.)")
    lines.append("=" * 60)
    return "\n".join(lines)


_BAD_CHARS = re.compile(r'[\\/:*?"<>|#^\[\]{}\x00-\x1f]')


def safe_name(text: str, max_len: int = 80) -> str:
    """Filesystem- and Obsidian-wikilink-safe name that stays human readable."""
    text = _BAD_CHARS.sub(" ", text or "")
    text = re.sub(r"\s+", " ", text).strip(" .-_")
    if len(text) > max_len:
        cut = text[:max_len].rsplit(" ", 1)[0]
        text = cut if len(cut) > max_len * 0.6 else text[:max_len]
    return text or "Untitled"


def fmt_ts(seconds: float | int | None) -> str:
    if seconds is None:
        return ""
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"
