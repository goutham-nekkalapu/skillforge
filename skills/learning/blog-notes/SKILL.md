---
name: blog-notes
description: Turn one or more blog posts or web articles into distilled study notes saved by topic in the user's notes folder (next to their yt-notes video notes), for learning and interview prep. Fetches the full article text first and refuses to write notes from a paywall teaser. Notes are markdown by default with ## and ### structure; a small HTML explainer page is added only for a concept that moves (a request flow, an algorithm) and needs a step-through. Several posts on the same concept become one combined note; posts on different concepts become separate, linked notes. Modes - quick, distilled (default), deep - plus an optional critique. Use this whenever the user shares blog, Medium, Substack, engineering-blog or article URLs and asks for notes, study notes, a summary to keep, a breakdown, "notes I can refer to later", or to "learn from these posts", even without saying "notes"; also to regenerate a blog note, add a post to one, or make it deeper. YouTube links go to yt-notes; transcript files the user already has go to lecture-distiller.
---

# blog-notes

Make notes that let the user understand and revise a topic weeks later without rereading the post. They live in the same notes folder as yt-notes' video notes, so a topic folder can hold both:

```
<notes_root>/                               default ~/Notes (settings: ~/.yt-notes/config.json,
  _index.md                                 or the yt-transcript skill's config.json on claude.ai)
  <Topic>/_index.md
  <Topic>/<Note_Title>/<Note_Title>.md      the note (markdown, the default)
  <Topic>/<Note_Title>/<Note_Title>__<Concept>.html   optional explainer page(s)
  _sources/<Post_Title>_<hash>/             the saved article: meta.json, article_<hash>.md, images/
```

Folder and file names use underscores; pass normal titles with spaces to the scripts and they convert them. Titles inside notes keep their spaces.

This skill needs **yt-notes** installed next to it: it reuses yt-notes' HTML template, visuals guide, checker and index. Paths below use `<skill_dir>` for this skill's folder and `<yt_notes>` for `<skill_dir>/../yt-notes`.

## How the user likes these notes

The default comes from a prompt the user wrote that gave them notes they liked: *markdown, one note per concept, skip the FAQ section, use headings and subsections*. So:

- **Markdown first.** `##` sections with `###` subsections, so the note has a navigable outline. Static pictures go inline as small HTML snippets.
- **HTML only where it earns its place.** An explainer page for a concept that *moves* (several steps where state changes) or needs a toggle. A static picture never qualifies. Usually zero per note, at most `max_explainers` (default 2).
- **Overrides:** "as HTML"/"full HTML" gives yt-notes' tabbed page plus card (`--format html`); "no HTML" means no explainers.

## Step 1: Say where notes will be saved (every run)

```bash
python3 <skill_dir>/scripts/notes_paths.py where
```

Tell the user in one line where notes go (the banner's notes root). In a `cloud-sandbox` environment, say they'll be saved to the Drive folder instead, because that disk is temporary. Keep `existing_topics`; you'll reuse topic names.

## Step 2: Fetch every post

```bash
python3 <skill_dir>/scripts/fetch_article.py "<url1>" "<url2>" ...
```

Read the block between `=== RESULT JSON ===` and `=== END RESULT ===`. Each post has a `status`:

| status | Meaning | What to do |
|---|---|---|
| `ok` / `cached` | Full article saved (or reused) | Use `source_dir` |
| `truncated` | Saved, but it looks cut off (paywall text, under ~300 words, or a JavaScript-only page). `warnings` say why | Don't write a note from it. Skip it, tell the user why, and offer the paste route below. If they say the post really is that short, continue |
| `failed` | Nothing usable | Skip it and report why |

The run never stops for one bad post: write notes for the posts that fetched, and list the skipped ones in the report. Never write a note from the title, a teaser, or your own knowledge of the topic; the user relies on these notes reflecting what the article actually says.

Exit codes: `0` at least one post saved · `3` a Supadata key is needed (show the `=== CREDENTIALS NEEDED ===` block and stop) · `4` the network is blocked (typical on claude.ai, see below) · `5` bad input: a YouTube link (hand it to yt-notes) or not a URL.

**Fallbacks**
- **claude.ai / blocked network:** call the Supadata connector's `supadata_scrape` tool for each URL, save its markdown to a file, then `fetch_article.py --from-file <file.md> --url <url> [--title "..."]` to make the package.
- **Paywalled or blocked everywhere:** ask the user to paste the article (or save the page as HTML) and use `--from-file`.
- **Don't use WebFetch for the article body.** It returns a model's summary, not the text, so notes built on it wouldn't be faithful. It's fine for checking a title or date.

`fetch_article.py` reuses saved packages (so regenerating costs nothing); `--force` re-fetches. The `local` tier is free; `supadata` costs 1 credit per page and runs only if local fails.

## Step 3: Read everything

For each post, read `meta.json` and the whole `article_<hash>.md`. Look at the images in `images/` too: blog diagrams often carry the main point. Long posts (over ~8k words): read in parts and keep a running outline of ideas, examples, numbers, code and claims. You read everything so you can choose well, not so everything goes into the note.

## Step 4: Group posts into notes

Read `references/grouping.md`. In short: posts share a note only when one title can name **the concept itself** and honestly cover all of them. A title that only works because it's broad ("LLM Caching" for a prompt caching post and a semantic caching post) means separate notes, in the same topic folder, linked to each other. A series (Part 1/2/3) is one note.

Announce the grouping in one line and carry on without waiting, e.g. *"2 notes: Prompt Caching (P1), Semantic Caching (P2), both in LLM Engineering."* The user's word wins: "combine them" or "keep them separate". The one time to ask first: the user asked for one note but the posts are clearly different concepts.

## Step 5: Plan each note

Decide briefly:
- **Title**: the concept, not the post's headline ("Prompt Caching", not "How does Prompt Caching work?"). The post title goes in `aliases`.
- **Topic**: broad and reusable ("LLM Engineering", "System Design"). Reuse an existing topic whenever one fits.
- **Mode**: what the user asked for, else the `blog_mode` setting (default `distilled`). "quick notes" → `quick`; "detailed / deep / I'll implement this" → `deep`; "analyze / critique / is this right" → add `--critique`.
- **What stays**: keep / compress / leave out, as in `references/note-structure.md`. Restructure around the ideas; don't follow the post's heading order section by section.
- **Explainers**: which concept (if any) moves enough to need one (`references/explainers.md`).

## Step 6: Prepare the folder

```bash
python3 <skill_dir>/scripts/notes_paths.py prepare --source "<source_dir>" [--source ...] --topic "<Topic>" --title "<Title>" [--mode quick|distilled|deep] [--critique] [--format markdown|html]
```

It prints JSON with `note_file`, `title`, `posts` (each with its `tag` P1…, `source_wikilink`), `explainer_prefix`, `embed_dir`, `drive_dir`, `drive_files`, `today` and the limits. Use the returned `title`: if a different note (say a video note) already has that title in the topic, it returns `"<Title> (<site>)"` and sets `renamed_for_collision`. In that case link the two notes to each other in their Related lines. If the post(s) already have a note, it returns that note (`regenerating_existing_note: true`) and you overwrite it in place.

More than `max_posts` (5) posts, or over `max_combined_words` (40,000) in total, is too much for one combined note. It exits with a message: offer to split by subtopic, or make one note per post plus a short hub note linking them, and ask which.

In a cloud sandbox, first search Drive for an existing note on the same URL (`fullText contains '<url>'` and `title contains '.md'`) and reuse its topic and title.

## Step 7: Write the note

Read `references/note-structure.md` (sections, modes, frontmatter) and `<yt_notes>/references/visuals.md` (picking and drawing visuals) now.

**Markdown (default):** write `note_file`: frontmatter, then `##` sections with `###` subsections, inline HTML snippets for visuals, code that carries the idea verbatim. Skip the post's boilerplate (FAQs, newsletter boxes, author bio, related posts, comments, table of contents) unless the user asks for it.

**Explainers:** build each from `references/explainers.md` and save it as `<explainer_prefix><Concept>.html`. Link it where the concept is explained, and list it in the note's `explainers` frontmatter.

**HTML format** (`--format html`): follow yt-notes' HTML format exactly (`<yt_notes>/references/html-notes.md`, template `<yt_notes>/assets/note-template.html`), with the blog frontmatter on the card.

**Combined notes:** tag points from one post with `(P2)`, add a Coverage table and a Sources section, and add a "Posts differ" callout where they disagree (`references/note-structure.md`).

## Step 8: Check

```bash
python3 <yt_notes>/scripts/check_note.py "<note_file>"
python3 <yt_notes>/scripts/check_note.py "<explainer.html>" --explainer     # each explainer
```

For HTML format pass `--card <card_file>` instead. Fix every `ERROR` and re-run until `RESULT: OK`. A warning that Playwright isn't installed is fine.

## Step 9: Update the indexes

```bash
python3 <skill_dir>/scripts/notes_paths.py index --topic "<Topic>"
```

Skip this in a cloud sandbox (the local copy doesn't have the user's other notes).

## Step 10: Save to Google Drive (cloud sandbox only)

On claude.ai the disk is temporary. Use the **gdrive-save** skill to save `drive_files` plus any explainers to `drive_dir`, conflict rule `replace`, and each post's `meta.json` and `article_<hash>.md` to `<drive_root>/_sources/<folder>/` (skip `images/`). Without gdrive-save, use the Google Drive connector directly as yt-notes Step 9 describes. Never say notes are saved when they only exist in the sandbox.

On the user's computer the files are already in `notes_root`; if that's inside their Google Drive folder, Drive syncs them.

## Step 11: Report

Short:
- The grouping used, and each note's path (and Drive path), noting any that replaced an earlier version or were renamed for a title collision.
- Mode and format, one line on what's inside, and any explainers.
- Skipped posts and why (truncated, failed), with the paste option.
- Fetch warnings worth knowing and Supadata credits spent.

## Other requests

- **"Make this deeper / quicker"**: re-run `prepare` with the new `--mode`; it finds the note and you rewrite it in place.
- **"Add this post to my X note"**: fetch it, then `prepare` with the note's existing posts plus the new one (`previous_posts` lists them); merge it in with the next tag.
- **"Move this note to topic X"**: move the folder, then `index --all`.
