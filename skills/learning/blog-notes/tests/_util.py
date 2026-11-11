"""Test helpers: import the skill's scripts and point config at temp folders."""
from __future__ import annotations

import os
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
LEARNING = SKILL.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(SKILL / "scripts"))


def isolate_config(tmp: Path, root: Path | None = None):
    """Point the shared config at a temp file and (optionally) a temp notes root."""
    os.environ["YT_NOTES_CONFIG"] = str(tmp / "config.json")
    os.environ["YT_NOTES_ENV"] = "local"
    if root is not None:
        os.environ["YT_NOTES_ROOT"] = str(root)
    else:
        os.environ.pop("YT_NOTES_ROOT", None)
    os.environ.pop("SUPADATA_API_KEY", None)
