# blog-notes: design

Date: 2026-11-11 · Branch: `feature/blog-notes` · Location: `skills/learning/blog-notes/`

## Intent

`yt-notes` turns YouTube videos into study notes. The user also learns from blog posts and wants the same thing for them: give one or more blog URLs, get distilled notes saved by topic in the same notes folder, ready for revision and interview prep weeks later.

The user's own prompt that produced notes they liked is the reference point for the default behaviour:

> create notes for prompt caching, semantic caching using these respective links in markdown format. keep them in separate markdown files each of their own. ignore the FAQs section of these pages. try to use headings (subsections) in the notes

So the default is **markdown**, **one note per concept**, **boilerplate sections skipped**, **clear `##`/`###` structure**.

## Goals

1. Accept 1..N blog post URLs, fetch the full article text reliably, and save it as a source package (like `yt-transcript` does for videos).
2. Decide automatically which posts belong in one note (same concept) and which get their own notes, announce the grouping in one line, and proceed.
3. Write distilled markdown notes; add a small HTML explainer page only for concepts that need motion or interaction.
4. Offer depth modes (`quick`, `distilled`, `deep`) plus an optional `critique` add-on.
5. Live alongside yt-notes: same notes root, same topic folders, same indexes, same Obsidian conventions, so video notes and blog notes on a topic sit together.

## Non-goals (v1)

- Mixing videos and blog posts in one combined note (planned later; keep the source package shape compatible).
- PDFs, arXiv papers, Twitter/X threads, newsletters behind login, documentation sites crawled as a whole.
- Interview questions or flashcards (same as yt-notes: the user builds those across notes).

## Anti-goals (a failure even if it "works")

- Notes written from a paywall teaser, the title, or a summary instead of the full article.
- Notes that paraphrase the post section by section in the author's order instead of restructuring around the ideas.
- Two different concepts glued into one note under an umbrella title ("LLM Caching" for prompt caching + semantic caching).
- Silently dropping a URL that failed to fetch.

## Behaviour

### 1. Where notes go (every run)

Same as yt-notes Step 1: print the save-location banner and tell the user in one line. Shared config: `~/.yt-notes/config.json` locally, the yt-transcript skill's `config.json` on claude.ai. New keys (defaults shown), added to the `DEFAULTS` of every copy of `ytn_config.py`:

| Key | Default | Meaning |
|---|---|---|
| `blog_note_format` | `"markdown"` | Separate from yt-notes' `note_format` so yt-notes stays HTML-first |
| `blog_mode` | `"distilled"` | Default depth mode |
| `max_posts` | `5` | Most posts combined into one note |
| `max_combined_words` | `40000` | Word budget for one combined note |
| `article_tiers` | `["local", "supadata"]` | Fetch order (see below) |
| `max_explainers` | `2` | Most HTML explainers per markdown note |

### 2. Fetching: the source package

A script `scripts/fetch_article.py <url> [<url>...]` produces, per post:

```
<notes_root>/_sources/<Post_Title>_<urlhash>/
  meta.json      url, canonical_url, title, author, site, published, updated,
                 word_count, fetch_method, warnings[], images[] (src, alt, local file)
  article_<urlhash>.md   clean article markdown, readable in Obsidian (headings, code blocks, images)
  images/        downloaded article images (capped: 20 images, 5 MB total)
```

`<urlhash>` = first 10 hex chars of SHA-1 of the canonical URL. An existing package for the same URL is reused (status `cached`); `--force` re-fetches. Output ends with a `=== RESULT JSON ===` block and exit codes mirroring yt-transcript (0 ok, 2 failed, 3 credentials needed, 4 network blocked, 5 bad input) so the skill text can follow the same pattern.

Fetch tiers, tried in `article_tiers` order:

| Tier | Cost | How |
|---|---|---|
| `local` | free | Download HTML with urllib, extract main content with **trafilatura** if installed (`pip install trafilatura`), else a built-in stdlib fallback (HTMLParser: take `<article>`/`<main>`, drop nav/header/footer/aside/script/style, convert headings, paragraphs, lists, `<pre>`, tables, images to markdown). Reads author/date/title from JSON-LD, OpenGraph and `<meta>` tags |
| `supadata` | 1 credit | Supadata web scrape API (`supadata_key`, already in config) returns markdown |

Agent-side fallbacks, described in the skill text, not the script:
- **claude.ai / blocked network:** the Supadata connector's `supadata_scrape` tool, then save the result into a package with `fetch_article.py --from-file <md> --url <url>`.
- **Everything failed / paywalled:** ask the user to paste the article or save the page; ingest with `--from-file`.
- **WebFetch is not a valid source** for the article body: it returns a model's summary, not the verbatim text. It may be used only to read metadata.

YouTube URLs are rejected with exit 5 and a message pointing to yt-notes.

**Truncation / paywall detection** (adds a `warnings[]` entry; the skill stops for that post unless the user says to continue): article under ~300 words, or text containing paywall markers ("subscribe to continue", "members only", "sign in to read", "this post is for paid subscribers", etc.), or extracted words < 25% of visible page words. The rule from yt-notes holds: never write a note from a fragment.

The package keeps the article faithful and complete; skipping boilerplate happens when writing the note, not when saving the source.

**Partial failures in a multi-post run:** write the notes for every post that fetched fully; never pause the whole run. Posts that failed or were truncated are listed in the report with the reason and the `--from-file` / paste route. Grouping is decided from the posts that fetched; if a missing post leaves a gap (e.g. Part 2 of a series), the combined note says so in a callout and the report says it can be added later ("add this post to my X note").

### 3. Grouping posts into notes

After fetching **all** posts (fetching is free/cheap, so judge from content, not titles):

**Test:** can one note title name *the concept itself* and honestly cover every post in the group? A title that only works because it is broad ("LLM Caching") means split.

| Posts | Result |
|---|---|
| Several explanations of the same concept | One combined note |
| A series (Part 1/2/3) | One combined note |
| Related but different concepts (prompt caching + semantic caching) | Separate notes, same topic folder, linked to each other |
| Unrelated | Separate notes, each in its own topic |
| Mixed (3 on A, 2 on B) | One note per group |

The skill states the grouping in one line ("3 notes: Prompt Caching (P1, P3), Semantic Caching (P2), Postgres Vacuum (P4)") and proceeds without waiting. User overrides always win: "combine them" / "keep them separate". If the user asked for one note but the posts are clearly different concepts, that is the one case where the skill asks before writing.

Limits apply **only to combined notes**: more than `max_posts` posts or more than `max_combined_words` words → suggest splitting by subtopic, or one note per post plus a short hub note linking them; ask which. Separate notes have no count limit (they're written one at a time).

### 4. Modes

Depth is chosen per request ("quick notes on these", "deep notes"); format is separate.

| Mode | Output | Use |
|---|---|---|
| `quick` | Short markdown note: TL;DR, why it matters, one inline visual, "Worth a deep read?" verdict with a reason. No explainers | Triaging a reading list |
| `distilled` (default) | Full markdown note: 3–7 key ideas, inline visuals, explainers where earned | Most posts |
| `deep` | Like distilled, but keeps the full reasoning chain, edge cases, numbers, and important code verbatim | Engineering posts the user will work from |
| `+ critique` (add-on to any mode) | An extra `## Critique` section: claims vs. evidence, hidden assumptions, what's missing, is it outdated (given the publish date) | Opinionated posts, "analyze this" requests |

`quick` is a full note in the normal place, not just a card, so it shows up in indexes and can later be regenerated as `distilled`/`deep` in place.

### 5. Format: markdown first, HTML only where it earns its place

- **Markdown (default):** `<Topic>/<Note_Title>/<Note_Title>.md` with frontmatter, `##` sections, `###` subsections. Static visuals inline as small HTML snippets, same rules as yt-notes `references/visuals.md` (no hand-drawn SVG, no Mermaid unless asked).
- **HTML explainer:** for a concept that *moves* (several steps where state changes: a request path through a cache, an algorithm, a rebalance) or needs interaction (before/after toggle). Static pictures never qualify. File: `<Note_Title>/<Note_Title>__<Concept>.html`, built from yt-notes' `assets/note-template.html` with a single panel (no tab bar needed when there's one panel) using the stepper/compare/graph components. Placed in the markdown right where the concept is explained: an `html-embed` block when an Obsidian vault is detected (as yt-notes' `page_embed_block`), plus a plain `[[...html|Step through it]]` link. At most `max_explainers` per note; usually zero.
- **Overrides:** "no HTML" → never create explainers; "full HTML" / "as HTML" → yt-notes-style tabbed page + markdown card, exactly as yt-notes' HTML format.

### 6. What goes into a note

Follows yt-notes `references/note-structure.md` (distil: keep / compress / leave out; intuition then precision; faithful with "Added context"/"Correction" callouts; no timestamps/questions/flashcards), with blog-specific rules:

- **Restructure, don't paraphrase.** Plan the note around ideas, not the post's heading order.
- **Skip boilerplate sections by default:** FAQs, newsletter/subscribe blocks, author bio, "related posts", comments, sponsor/ads, table of contents. User can name more ("ignore the benchmarks section").
- **Code:** keep code that carries the idea, verbatim, with language tags; drop setup/boilerplate code.
- **Images:** read downloaded diagrams to understand them; rebuild the important ones as inline HTML components (or an explainer if it moves); list original image URLs in the Source section. Do not embed downloaded images in the note (v1).
- **Staleness:** show `published` (and `updated`) prominently; if the post is old for a fast-moving field, add a short "May be outdated" callout naming what to check.
- **Opinions:** attribute opinions to the author ("the author argues…").
- Sections (markdown `##`): Overview (TL;DR + why it matters + big-picture visual), Key ideas (each a `###`), Walkthrough / Compare only if present, Takeaways, Critique (if requested), Source.

Combined notes: same as yt-notes "Combining several videos" with tags `P1…P5` instead of `V1…V5` (order given), a Coverage grid (markdown table, ideas × posts, `●` full / `◐` part / `–` none), "Posts differ" callouts, and a Sources section.

### 7. Frontmatter

```yaml
title: "Prompt Caching"
aliases: ["Prompt Caching", "How does prompt caching work?"]
summary: "..."
topic: "LLM Engineering"
tags: [llm, caching]
status: new
format: markdown            # or html
mode: distilled             # quick | distilled | deep
critique: false
source_type: blog
source_url: "https://..."   # combined: source_urls: [...]
author: "..."               # combined: authors: [...]
site: "outcomeschool.com"   # combined: sites: [...]
published: "2025-03-02"
source: "[[article_<urlhash>|Saved article]]"
explainers: ["Prompt_Caching__Cache_Lookup.html"]
created: "2026-11-11"
```

`check_note.py` must accept these keys (the blog key set instead of the video key set when `source_type: blog`).

### 8. Regenerating, duplicates, indexes

- `scripts/notes_paths.py prepare --source <pkg>... --topic --title [--format] [--mode]` mirrors yt-notes' prepare, keyed on `source_url(s)` instead of video ids: an existing note for the same URL(s) is regenerated in place (same subset/superset rule for combined notes). Prints JSON with `note_file`, `explainer_dir`, `embed` helper, `posts` (tag, title, author, site, url, `source_wikilink`), `existing_topics`, `today`, limits.
- Indexes: the topic and root `_index.md` must list video and blog notes together. yt-notes' `rebuild_topic_index` already picks up any `<Title>/<Title>.md`; change its "Channel" column to "Source" and show `site` (or "N posts") for blog notes. blog-notes' `index` command does not reimplement this: it imports yt-notes' `notes_paths.py` from `<skill_dir>/../yt-notes/scripts` at runtime and calls its `index` logic (blog-notes already requires yt-notes). The root index is retitled "Notes" (see below) but keeps `type: yt-notes-index`.
- **Title collision with a note from another source** (e.g. a video note "Prompt Caching" already exists in the topic): never overwrite it. See "Title collisions" below.
- "Add this post to my X note", "regenerate as deep", "move to topic Y" work like the yt-notes equivalents.

### 9. claude.ai (cloud sandbox)

Same as yt-notes Step 9: save the note, explainers and the source package (`meta.json`, `article_<urlhash>.md`; skip `images/`) to Drive via gdrive-save with conflict rule `replace`; never claim saved when only in the sandbox. Network is usually blocked there, so fetching goes through the Supadata connector + `--from-file`.

### 10. Report

Short: where each note was saved (and whether it replaced one), the grouping used, mode/format, explainers created, any fetch warnings (truncation, Supadata credits), any post skipped and why.

## Structure (decided)

```
skills/learning/blog-notes/
  SKILL.md
  README.md
  references/
    note-structure.md     blog-specific structure, modes, critique, frontmatter
    grouping.md           the same-concept test with worked examples
    explainers.md         when an explainer earns its place + how to build one
  scripts/
    fetch_article.py      source package
    notes_paths.py        where / prepare / index for blog notes
    ytn_config.py         copy of the shared config module (same pattern as yt-notes/yt-transcript)
  examples/sample-output/ one distilled markdown note with one explainer, one quick note
  tests/                  unittest: extractor on saved HTML fixtures, paywall detection, grouping-independent script logic
```

Reuse from yt-notes rather than copying: `assets/note-template.html`, `references/visuals.md`, `references/html-notes.md`, `scripts/check_note.py`, via `<skill_dir>/../yt-notes/...`. blog-notes therefore requires yt-notes installed (and yt-transcript, which holds the claude.ai config); README and learning README say so, as yt-notes already does for yt-transcript.

Repo updates: root README catalog row, `skills/learning/README.md` table + "which skill" guidance (YouTube link → yt-notes; blog URL → blog-notes; files you have → lecture-distiller), yt-notes `check_note.py` and index tweak, `ytn_config.py` new defaults in all copies.

The SKILL.md description must trigger on blog/article URLs with "notes", "summarize this post", "break down this article", "learn from these posts", and explicitly hand YouTube links to yt-notes. Use the skill-creator skill to draft and test the description.

## Left to the builder

- Exact paywall marker list and thresholds.
- The stdlib extractor's internals and how much markdown fidelity it reaches (fixtures decide).
- Exact wording of SKILL.md and references, following yt-notes' style.
- Whether `check_note.py` changes are a flag or auto-detection from frontmatter.

## Title collisions (decided with the user)

When a blog note's title matches an existing note from a different source in the same topic, never overwrite it: create `<Title> (<site>)`, e.g. `Prompt Caching (outcomeschool.com)`, alongside it, and link the two notes to each other in their Related lines.

## Rename the notes root to "Notes" (decided with the user)

Notes from any skill are just notes, so the shared default folder changes from `YouTubeNotes` to `Notes`:
- `ytn_config.py` (all copies): `notes_root` default `~/Notes`, `drive_root` default `Notes`.
- `skills/learning/yt-transcript/config.json`: `drive_root` → `Notes`.
- Root `_index.md` title "YouTube Notes" → "Notes" (the `type: yt-notes-index` key stays so existing queries keep working). This replaces the earlier call to keep the old title.
- Every mention in yt-notes / yt-transcript SKILL.md, README.md, `notes_paths.py` docstrings and `examples/sample-output/_index.md`.
- Existing users keep working without surprises: a user config that explicitly sets `notes_root` still wins. The READMEs get a short "moving from YouTubeNotes" note: rename the folder (local or Drive), then update `notes_root` / `drive_root` in the config.

## Calls made by Claude (not explicitly agreed by the user)

- Separate config key `blog_note_format` so yt-notes keeps its HTML default.
- `quick` writes a real note (not just a card) so it can be upgraded in place.
- Explainer file naming `<Note>__<Concept>.html`, cap of 2 per note.
- Supadata as the only paid tier; WebFetch excluded as a body source.
- Depending on yt-notes for template/checker instead of copying them.
- Grouping is announced and proceeds without waiting (user: "sure").
- Partial fetch failures don't stop the run; the report lists skipped posts.
- Index code is imported from yt-notes at runtime.
- Saved article file is `article_<urlhash>.md` (unique wikilink target, like `transcript_<id>.md`).
