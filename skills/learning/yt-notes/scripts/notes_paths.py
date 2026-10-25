#!/usr/bin/env python3
"""Paths, naming and index pages for yt-notes.

  notes_paths.py where
      Print the save location banner + existing topics.
  notes_paths.py prepare --source <source_dir> --topic "System Design" --title "Consistent Hashing"
      Create the note folder and print the file names/links to use (JSON).
      If a note for the same video already exists anywhere, it is reported so
      it can be regenerated in place instead of duplicated.
  notes_paths.py index [--topic "System Design" | --all]
      Rebuild _index.md for a topic (and the root _index.md).

Layout:
  <root>/_index.md                            all topics
  <root>/<Topic>/_index.md                    notes in a topic
  <root>/<Topic>/<Title>/<Title>.md           the note
  <root>/<Topic>/<Title>/<Title>_interactive.html   (optional)
  <root>/_sources/<Video_Title>_<id>/         transcript package (yt-transcript)

Folder and file names use underscores instead of spaces (e.g. System_Design/
Consistent_Hashing/Consistent_Hashing.md). Titles inside the notes keep spaces.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
import ytn_config as C  # noqa: E402

SKIP_DIRS = {C.SOURCES_DIRNAME, ".obsidian", ".trash"}


def topics(root: Path) -> list[str]:
    if not root.exists():
        return []
    out = []
    for d in sorted(root.iterdir()):
        if d.is_dir() and d.name not in SKIP_DIRS and not d.name.startswith("."):
            out.append(d.name)
    return out


def frontmatter(md: Path) -> dict:
    try:
        text = md.read_text(encoding="utf-8")
    except OSError:
        return {}
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not mm:
            continue
        k, v = mm.group(1), mm.group(2).strip()
        if v.startswith('"') and v.endswith('"'):
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                v = v.strip('"')
        elif v.startswith("[") and v.endswith("]"):
            v = [x.strip().strip('"\'') for x in v[1:-1].split(",") if x.strip()]
        fm[k] = v
    return fm


def note_files(root: Path):
    """Yield (topic, note_md_path) for every note under root."""
    for t in topics(root):
        tdir = root / t
        for md in tdir.rglob("*.md"):
            if md.name == "_index.md" or any(p in SKIP_DIRS for p in md.parts):
                continue
            if md.stem == md.parent.name:  # <Title>/<Title>.md
                yield t, md


def find_note_for_video(root: Path, vid: str):
    for t, md in note_files(root):
        if frontmatter(md).get("video_id") == vid:
            return t, md
    return None


def cmd_where(cfg):
    print(C.location_banner(cfg))
    ts = topics(cfg["_root"])
    print("Existing topics: " + (", ".join(ts) if ts else "(none yet)"))
    return {"notes_root": str(cfg["_root"]), "environment": cfg["_env"], "drive_root": cfg["drive_root"],
            "config_path": str(cfg["_config_path"]), "topics": ts}


def cmd_prepare(cfg, args):
    src = Path(args.source).expanduser()
    meta_path = src / "meta.json"
    if not meta_path.exists():
        sys.exit(f"ERROR: {meta_path} not found - fetch the transcript first (yt-transcript).")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    vid = meta.get("video_id")
    root = cfg["_root"]
    topic_parts = [C.safe_name(p, 60) for p in re.split(r"[/\\]", args.topic) if p.strip()]
    title = C.safe_name(args.title, 90)

    existing = find_note_for_video(root, vid) if vid else None
    if existing and not args.new_location:
        e_topic, e_md = existing
        note_dir, title = e_md.parent, e_md.stem
        topic_rel = str(e_md.parent.parent.relative_to(root))
    else:
        note_dir = root.joinpath(*topic_parts) / title
        topic_rel = "/".join(topic_parts)
    note_dir.mkdir(parents=True, exist_ok=True)

    note_md = note_dir / f"{title}.md"
    html = note_dir / f"{title}_interactive.html"
    transcript_md = next(iter(sorted(src.glob("transcript_*.md")) + sorted(src.glob("transcript - *.md"))), None)
    vault = cfg.get("obsidian_vault_root") or ""
    embed_path = None
    if vault:
        vp = Path(os.path.expandvars(vault)).expanduser()
        try:
            embed_path = html.resolve().relative_to(vp.resolve()).as_posix()
        except ValueError:
            embed_path = None
    drive_dir = "/".join([cfg["drive_root"].strip("/"), topic_rel, note_dir.name])
    out = {
        "note_dir": str(note_dir),
        "note_file": str(note_md),
        "note_exists": note_md.exists(),
        "regenerating_existing_note": bool(existing),
        "interactive_file": str(html),
        "interactive_wikilink": f"[[{html.name}|▶ Open the interactive walkthrough]]",
        "interactive_embed_block": (f"```html-embed\nfile: {embed_path}\n```" if embed_path else None),
        "transcript_wikilink": f"[[{transcript_md.stem}|Full transcript]]" if transcript_md else None,
        "source_dir": str(src),
        "topic": topic_rel,
        "drive_dir": drive_dir,
        "today": date.today().isoformat(),
        "video_id": vid,
        "existing_topics": topics(root),
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return out


def rebuild_topic_index(root: Path, topic: str):
    tdir = root / topic
    rows = []
    for t, md in note_files(root):
        if t != topic:
            continue
        fm = frontmatter(md)
        rel = md.relative_to(tdir).with_suffix("").as_posix()
        rows.append({
            # "\|" because a bare pipe inside a table cell would split the column
            "link": f"[[{rel}\\|{fm.get('title') or C.display_name(md.stem)}]]",
            "summary": (fm.get("summary") or "").replace("|", "/"),
            "channel": (fm.get("channel") or "").replace("|", "/"),
            "created": fm.get("created") or "",
            "status": fm.get("status") or "",
        })
    rows.sort(key=lambda r: r["created"], reverse=True)
    lines = ["---", f"title: {json.dumps(C.display_name(topic) + ' - index')}", "type: yt-notes-index", "---", "",
             f"# {C.display_name(topic)}", "", f"{len(rows)} note(s). This page is rebuilt automatically; don't edit it.", "",
             "| Note | Summary | Channel | Added | Status |", "|---|---|---|---|---|"]
    lines += [f"| {r['link']} | {r['summary']} | {r['channel']} | {r['created']} | {r['status']} |" for r in rows]
    (tdir / "_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(rows)


def rebuild_root_index(root: Path):
    lines = ["---", 'title: "YouTube Notes - index"', "type: yt-notes-index", "---", "",
             "# YouTube Notes", "", "This page is rebuilt automatically; don't edit it.", ""]
    for t in topics(root):
        n = sum(1 for tt, _ in note_files(root) if tt == t)
        if n:
            lines.append(f"- [[{t}/_index|{C.display_name(t)}]] ({n})")
    root.mkdir(parents=True, exist_ok=True)
    (root / "_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def cmd_index(cfg, args):
    root = cfg["_root"]
    done = {}
    targets = topics(root) if args.all or not args.topic else [args.topic.split("/")[0]]
    for t in targets:
        if (root / t).is_dir():
            done[t] = rebuild_topic_index(root, t)
    rebuild_root_index(root)
    print(json.dumps({"rebuilt": done, "root_index": str(root / "_index.md")}, indent=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="override notes root for this run")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("where")
    p = sub.add_parser("prepare")
    p.add_argument("--source", required=True)
    p.add_argument("--topic", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--new-location", action="store_true",
                   help="create a new note even if one exists for this video")
    i = sub.add_parser("index")
    i.add_argument("--topic")
    i.add_argument("--all", action="store_true")
    args = ap.parse_args()
    cfg = C.load(SKILL_DIR, root_override=args.root)
    if args.cmd == "where":
        print(json.dumps(cmd_where(cfg), indent=2))
    elif args.cmd == "prepare":
        print(C.location_banner(cfg), file=sys.stderr)
        cmd_prepare(cfg, args)
    elif args.cmd == "index":
        cmd_index(cfg, args)


if __name__ == "__main__":
    main()
