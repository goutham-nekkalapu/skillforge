#!/usr/bin/env python3
"""Paths, naming and index pages for blog-notes (shares the notes folder with yt-notes).

  notes_paths.py where
      Print the save-location banner and the existing topics (JSON).
  notes_paths.py prepare --source <package_dir> [--source ...] --topic "LLM Engineering" --title "Prompt Caching"
                         [--format markdown|html] [--mode quick|distilled|deep] [--critique] [--new-location]
      Create the note folder and print the file names and links to use (JSON).
      Repeat --source (up to max_posts) for one note combining several posts.
      A note that already covers the same post(s) is reused, so it's regenerated in place.
      A different note with the same title (e.g. a video note) is never overwritten:
      the new note becomes "<Title> (<site>)".
  notes_paths.py index [--topic "LLM Engineering" | --all]
      Rebuild the topic and root _index.md (yt-notes' index code, so both kinds of notes are listed).

Needs the yt-notes skill installed next to this one (skills/learning/yt-notes).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
import ytn_config as C  # noqa: E402
from fetch_article import normalize_url  # noqa: E402

YT_NOTES_SCRIPT = SKILL_DIR.parent / "yt-notes" / "scripts" / "notes_paths.py"
_YT = None


class NeedsYtNotes(Exception):
    pass


def yt():
    """yt-notes' notes_paths module (topics, note_files, frontmatter, cmd_index)."""
    global _YT
    if _YT is None:
        if not YT_NOTES_SCRIPT.exists():
            raise NeedsYtNotes(f"blog-notes needs the yt-notes skill installed next to it (looked for {YT_NOTES_SCRIPT}). "
                               "Install it with: npx skillforge install learning/yt-notes")
        spec = importlib.util.spec_from_file_location("yt_notes_paths", YT_NOTES_SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _YT = mod
    return _YT


def note_urls(fm: dict) -> tuple[set, bool]:
    """Normalised post URLs a note covers, and whether it is a combined note."""
    urls = fm.get("source_urls")
    if isinstance(urls, list) and urls:
        return {normalize_url(u) for u in urls}, True
    if fm.get("source_url"):
        return {normalize_url(fm["source_url"])}, False
    return set(), False


def find_existing_note(root: Path, urls: list[str]):
    """(topic, md, previous urls) of the note covering these posts, or None. Same rule as yt-notes:
    one post -> its single-post note; several -> a combined note whose posts are a subset or superset."""
    want = {normalize_url(u) for u in urls}
    for t, md in yt().note_files(root):
        fm = yt().frontmatter(md)
        have, combined = note_urls(fm)
        if not have:
            continue
        if len(want) == 1 and not combined and have == want:
            return t, md, fm
        if len(want) > 1 and combined and (have <= want or want <= have):
            return t, md, fm
    return None


def load_posts(sources: list[str]) -> list[dict]:
    posts = []
    for s in sources:
        src = Path(s).expanduser()
        meta_path = src / "meta.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"{meta_path} not found - fetch the post first (fetch_article.py)")
        m = json.loads(meta_path.read_text(encoding="utf-8"))
        h = m.get("hash") or src.name.rsplit("_", 1)[-1]
        posts.append({
            "tag": f"P{len(posts) + 1}",
            "title": m.get("title"),
            "author": m.get("author"),
            "site": m.get("site"),
            "url": m.get("url"),
            "published": m.get("published"),
            "word_count": int(m.get("word_count") or 0),
            "source_dir": str(src),
            "source_wikilink": f"[[article_{h}|Saved article]]",
        })
    return posts


def cmd_where(cfg) -> dict:
    print(C.location_banner(cfg), file=sys.stderr)
    return {"notes_root": str(cfg["_root"]), "sources": str(cfg["_sources"]), "environment": cfg["_env"],
            "drive_root": cfg["drive_root"], "existing_topics": yt().topics(cfg["_root"]),
            "blog_note_format": cfg.get("blog_note_format"), "blog_mode": cfg.get("blog_mode")}


def cmd_prepare(cfg, a) -> dict:
    sources = list(dict.fromkeys(a.source))
    posts = load_posts(sources)
    max_posts = int(cfg.get("max_posts") or 5)
    max_words = int(cfg.get("max_combined_words") or 40000)
    total = sum(p["word_count"] for p in posts)
    combined = len(posts) > 1
    if len(posts) > max_posts:
        raise ValueError(f"{len(posts)} posts given; one combined note takes at most {max_posts} (setting max_posts). "
                         "Split them by subtopic, or make one note per post plus a short hub note linking them.")
    if combined and total > max_words:
        raise ValueError(f"these {len(posts)} posts have {total} words; one combined note takes at most {max_words} "
                         "(setting max_combined_words). Split them by subtopic, or make one note per post plus a hub note.")

    root: Path = cfg["_root"]
    urls = [p["url"] for p in posts]
    found = None if a.new_location else find_existing_note(root, urls)
    renamed = None
    if found:
        _, md, fm = found
        note_dir, title_safe = md.parent, md.stem
        topic_rel = md.parent.parent.relative_to(root).as_posix()
        title = fm.get("title") or C.display_name(title_safe)
        previous = fm.get("source_urls") if isinstance(fm.get("source_urls"), list) else (
            [fm["source_url"]] if fm.get("source_url") else [])
    else:
        topic_parts = [C.safe_name(p, 60) for p in re.split(r"[/\\]", a.topic) if p.strip()]
        topic_rel = "/".join(topic_parts)
        title = a.title
        base = root.joinpath(*topic_parts)
        if (base / C.safe_name(title, 90) / f"{C.safe_name(title, 90)}.md").exists():
            renamed = a.title
            site = posts[0]["site"] or "blog"
            title = f"{a.title} ({site})"
            n = 2
            while (base / C.safe_name(title, 90) / f"{C.safe_name(title, 90)}.md").exists():
                title = f"{a.title} ({site}) {n}"
                n += 1
        title_safe = C.safe_name(title, 90)
        note_dir = base / title_safe
        previous = []
    note_dir.mkdir(parents=True, exist_ok=True)

    fmt = (a.format or cfg.get("blog_note_format") or "markdown").lower()
    mode = (a.mode or cfg.get("blog_mode") or "distilled").lower()
    md_file = note_dir / f"{title_safe}.md"
    page = note_dir / f"{title_safe}.html"
    vault = C.find_vault_root(root, cfg.get("obsidian_vault_root") or "")
    embed_dir = None
    if vault:
        try:
            embed_dir = note_dir.resolve().relative_to(vault.resolve()).as_posix()
        except ValueError:
            embed_dir = None
    prev_norm = {normalize_url(u) for u in previous}
    return {
        "format": fmt,
        "mode": mode,
        "critique": bool(a.critique),
        "title": title,
        "note_dir": str(note_dir),
        "note_file": str(page if fmt == "html" else md_file),
        "card_file": str(md_file) if fmt == "html" else None,
        "note_exists": (page if fmt == "html" else md_file).exists(),
        "regenerating_existing_note": bool(found),
        "renamed_for_collision": renamed,
        "explainer_prefix": str(note_dir / f"{title_safe}__"),
        "embed_dir": embed_dir,
        "posts": posts,
        "combined": combined,
        "total_words": total,
        "previous_posts": previous,
        "added_posts": [u for u in urls if previous and normalize_url(u) not in prev_norm],
        "topic": topic_rel,
        "drive_dir": "/".join([cfg["drive_root"].strip("/"), topic_rel, note_dir.name]),
        "drive_files": [p.name for p in ((page, md_file) if fmt == "html" else (md_file,))],
        "today": date.today().isoformat(),
        "max_posts": max_posts,
        "max_combined_words": max_words,
        "max_explainers": int(cfg.get("max_explainers") or 2),
        "existing_topics": yt().topics(root),
    }


def cmd_index(cfg, a) -> None:
    topic = "/".join(C.safe_name(p, 60) for p in re.split(r"[/\\]", a.topic) if p.strip()) if a.topic else None
    yt().cmd_index(cfg, argparse.Namespace(topic=topic, all=a.all or not topic))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="override notes root for this run")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("where")
    p = sub.add_parser("prepare")
    p.add_argument("--source", required=True, action="append", help="source package folder; repeat to combine posts")
    p.add_argument("--topic", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--format", choices=["markdown", "html"], help="override blog_note_format for this note")
    p.add_argument("--mode", choices=["quick", "distilled", "deep"], help="override blog_mode for this note")
    p.add_argument("--critique", action="store_true", help="the note gets a Critique section")
    p.add_argument("--new-location", action="store_true", help="make a new note even if one exists for these posts")
    i = sub.add_parser("index")
    i.add_argument("--topic")
    i.add_argument("--all", action="store_true")
    a = ap.parse_args(argv)
    cfg = C.load(SKILL_DIR, root_override=a.root)
    try:
        if a.cmd == "where":
            print(json.dumps(cmd_where(cfg), indent=2, ensure_ascii=False))
        elif a.cmd == "prepare":
            print(C.location_banner(cfg), file=sys.stderr)
            print(json.dumps(cmd_prepare(cfg, a), indent=2, ensure_ascii=False))
        elif a.cmd == "index":
            cmd_index(cfg, a)
    except (NeedsYtNotes, ValueError, FileNotFoundError) as e:
        print(f"ERROR: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
