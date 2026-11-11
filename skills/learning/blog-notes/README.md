# blog-notes

Paste one or more blog post links, ask for notes, and get distilled, Obsidian-ready study notes saved by topic, next to your yt-notes video notes.

## What It Does

Fetches each post's full text, author, date and images, picks out the ideas that matter, and writes a markdown note per concept.

- **Markdown first:** `##` sections and `###` subsections, inline HTML-snippet illustrations, important code kept verbatim. Boilerplate sections (FAQs, newsletter boxes, author bio, related posts, comments) are skipped.
- **HTML only where it helps:** a concept that moves (a request flow, an algorithm) gets a small step-through **explainer** page linked from the note. Most notes have none. Ask "as HTML" for a full yt-notes-style tabbed page instead.
- **Several posts:** posts on the **same concept** become one combined note (shared ideas once, unique ones tagged `P2`, a coverage table, disagreements called out). Posts on **different concepts** become separate notes in the same topic, linked to each other. The grouping is announced in one line before writing.
- **Modes:** `quick` (TL;DR plus a "worth a deep read?" verdict), `distilled` (default), `deep` (full reasoning, edge cases and code). Add **critique** to any of them for claims vs. evidence, assumptions, gaps, and whether the post is outdated.
- **Faithful:** paywalled or JavaScript-only pages are detected and skipped (you can paste the text instead); notes are never written from a teaser or a title.

Saved as `<Topic>/<Note_Title>/<Note_Title>.md` (plus any `<Note_Title>__<Concept>.html` explainers), with the article kept under `_sources/` and the topic indexes rebuilt. If a note with the same title already exists from another source (e.g. a video note), the new one becomes `<Title> (<site>)` and both are linked.

Works together with:

| Skill | Does |
|---|---|
| [yt-notes](../yt-notes/) | **Required.** Template, visuals guide, note checker and topic index |
| [yt-transcript](../yt-transcript/) | Holds the shared `config.json` used on claude.ai |
| [gdrive-save](../../google-drive/gdrive-save/) | Saves files to Google Drive (used on web/mobile) |

## Platform

**Claude Code**, **Cursor** and **claude.ai** (web, mobile, desktop chat).

## Setup

### Local: Claude Code / Cursor (Mac)

```bash
./install.sh learning                          # yt-transcript, yt-notes, blog-notes, lecture-distiller
pip install trafilatura                        # optional: better extraction on messy pages
```

Ask: *"Make notes from https://example.com/blog/how-does-prompt-caching-work and https://example.com/blog/how-does-semantic-caching-work"*. Files are saved to `~/Notes` (or your `notes_root`).

### Web / mobile: claude.ai

1. Zip and upload `yt-transcript`, `yt-notes`, `blog-notes` and `gdrive-save`: **Customize → Skills → + → Upload a skill**.
2. **Customize → Connectors**: connect **Google Drive** (required) and **Supadata** (reads pages when the sandbox can't; no key needed).
3. Ask the same way. Notes are saved to `My Drive/Notes`.

## Configure

Settings are shared with yt-notes: `~/.yt-notes/config.json` on your computer, or `config.json` in the yt-transcript skill on claude.ai. blog-notes adds:

| Setting | Default | What it does |
|---|---|---|
| `blog_note_format` | `markdown` | `markdown` (note + optional explainers) or `html` (yt-notes-style page + card) |
| `blog_mode` | `distilled` | `quick`, `distilled` or `deep` |
| `max_posts` | `5` | Most posts combined into one note |
| `max_combined_words` | `40000` | Word budget for one combined note |
| `article_tiers` | `["local", "supadata"]` | `local` is free; `supadata` costs 1 credit per page and runs only if local fails (key: `SUPADATA_API_KEY` or `supadata_key`) |
| `max_explainers` | `2` | Most HTML explainer pages per note |

## Trigger Phrases

- "make notes from this blog post / these articles"
- "summarize this post so I can revise it later"
- "deep notes on this engineering blog, I'll implement it"
- "quick notes on these 4 links from my reading list"
- "break down this Medium article and critique it"

YouTube links go to [yt-notes](../yt-notes/); transcript files you already have go to [lecture-distiller](../lecture-distiller/).

## Development

```bash
python3 -m unittest discover -s skills/learning/blog-notes/tests -v
python3 -m unittest discover -s skills/learning/yt-notes/tests -v
```
