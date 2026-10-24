#!/usr/bin/env python3
"""Quality checks for a generated note (run before saving to Drive / reporting).

  check_note.py <note.md> [--html <interactive.html>]

Checks:
  * YAML frontmatter exists and has the required keys
  * every ```mermaid block renders (uses `mmdc` if installed; otherwise only
    static checks), and avoids diagram types Obsidian can't draw yet
  * no leftover template placeholders ({{...}} / TODO)
  * interactive HTML (optional): loads without JS errors (uses Playwright if
    installed) and doesn't depend on external scripts
Exit code 1 when a hard error is found; warnings don't fail.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REQUIRED = ["title", "video_url", "video_id", "topic", "tags", "created", "summary"]
# Newer Mermaid diagram types that Obsidian's bundled Mermaid may not support.
RISKY = ["block-beta", "architecture-beta", "packet-beta", "kanban", "radar-beta", "treemap", "venn"]


def check_frontmatter(text, errors, warnings):
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        errors.append("missing YAML frontmatter at top of note")
        return
    keys = set(re.findall(r"^([A-Za-z_][\w-]*):", m.group(1), re.M))
    missing = [k for k in REQUIRED if k not in keys]
    if missing:
        errors.append(f"frontmatter missing keys: {', '.join(missing)}")


def mermaid_blocks(text):
    return [(m.start(), m.group(1)) for m in re.finditer(r"```mermaid\n(.*?)```", text, re.S)]


def check_mermaid(text, errors, warnings):
    blocks = mermaid_blocks(text)
    if not blocks:
        warnings.append("no Mermaid diagrams: deep notes usually need at least one")
    mmdc = shutil.which("mmdc")
    if not mmdc:
        warnings.append("mmdc not installed: Mermaid syntax not rendered-checked "
                        "(optional: npm i -g @mermaid-js/mermaid-cli)")
    for i, (pos, code) in enumerate(blocks, 1):
        line = text[:pos].count("\n") + 1
        first = code.strip().splitlines()[0] if code.strip() else ""
        for r in RISKY:
            if first.startswith(r):
                errors.append(f"diagram #{i} (line {line}) uses '{r}', which Obsidian may not render; use flowchart instead")
        if re.search(r"\bclick\s+\w+", code):
            warnings.append(f"diagram #{i} (line {line}) uses 'click', which Obsidian ignores")
        if mmdc:
            with tempfile.TemporaryDirectory() as td:
                src, out = Path(td) / "d.mmd", Path(td) / "d.svg"
                src.write_text(code, encoding="utf-8")
                p = subprocess.run([mmdc, "-q", "-i", str(src), "-o", str(out)], capture_output=True, text=True,
                                   timeout=120)
                if p.returncode != 0 or not out.exists():
                    msg = (p.stderr or p.stdout).strip().splitlines()
                    msg = next((l for l in msg if "rror" in l), msg[0] if msg else "render failed")
                    errors.append(f"diagram #{i} (line {line}, '{first[:40]}') does not render: {msg[:240]}")
    return len(blocks)


def check_html(path: Path, errors, warnings):
    html = path.read_text(encoding="utf-8")
    ext = re.findall(r"<script[^>]+src=[\"'](https?://[^\"']+)", html)
    if ext:
        warnings.append(f"interactive HTML loads external scripts ({', '.join(ext[:3])}); it won't work offline in Obsidian")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        warnings.append("playwright not installed: interactive HTML not test-loaded")
        return
    problems = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.on("pageerror", lambda e: problems.append(f"JS error: {e}"))
        pg.on("console", lambda m: problems.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        pg.goto(path.resolve().as_uri())
        pg.wait_for_timeout(800)
        # click through controls if the template's buttons exist
        for sel in ["#next", "#next", "#prev", "#play"]:
            if pg.query_selector(sel):
                pg.click(sel)
                pg.wait_for_timeout(150)
        b.close()
    errors.extend(f"interactive HTML: {x}" for x in problems)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("note")
    ap.add_argument("--html")
    a = ap.parse_args()
    note = Path(a.note)
    text = note.read_text(encoding="utf-8")
    errors, warnings = [], []
    check_frontmatter(text, errors, warnings)
    n = check_mermaid(text, errors, warnings)
    if re.search(r"\{\{[^}]+\}\}|\bTODO\b|\bTBD\b", text):
        errors.append("leftover placeholder ({{...}}, TODO or TBD) in note")
    if a.html:
        hp = Path(a.html)
        if hp.exists():
            check_html(hp, errors, warnings)
        else:
            errors.append(f"interactive file not found: {hp}")
    words = len(re.sub(r"```.*?```", "", text, flags=re.S).split())
    print(f"note: {note.name} | ~{words} words | {n} mermaid diagram(s)")
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print("RESULT: " + ("FAIL - fix the errors above" if errors else "OK"))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
