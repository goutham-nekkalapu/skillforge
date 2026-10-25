---
name: yt-notes
description: Turn a YouTube video into distilled, highly visual study notes saved to the user's notes folder, organised by topic so they can be revisited for learning and interview prep. By default each note is a rich single-page HTML file with tabs, hand-drawn SVG illustrations and animations (plus a small markdown card for Obsidian search); markdown notes with inline SVG are available on request. Uses the yt-transcript skill to get the transcript, description and chapters first. Use this whenever the user shares a YouTube link and asks for notes, study notes, a write-up, a breakdown, a summary to keep, "notes I can refer to later", or wants to "learn this video", even if they don't say "notes" explicitly. Also use it to regenerate or improve notes for a video already processed. For transcript files or screenshots the user already has (e.g. from a course platform) with no YouTube link, use lecture-distiller instead.
---

# yt-notes

Make notes that let the user understand and revise a topic weeks later without rewatching the video. Notes are saved by topic under the shared notes root (default `~/YouTubeNotes`; settings live in `~/.yt-notes/config.json` on the user's computer, or in the yt-transcript skill's `config.json` on claude.ai):

```
<notes_root>/
  _index.md                                   all topics (auto-generated)
  <Topic>/_index.md                           notes in that topic (auto-generated)
  <Topic>/<Note_Title>/<Note_Title>.html      the note (HTML format, the default)
  <Topic>/<Note_Title>/<Note_Title>.md        card for Obsidian search/tags/links (HTML format),
                                              or the note itself (markdown format)
  _sources/<Video_Title>_<id>/                transcript package from yt-transcript
```

**Naming rule:** folder and file names use underscores instead of spaces, e.g. `System_Design/Consistent_Hashing/Consistent_Hashing.html`. Pass normal titles with spaces to the scripts; they convert them. Follow the same rule for anything you name yourself (Drive folders, extra files). Titles *inside* notes (headings, frontmatter `title`, wikilink labels) keep their spaces.

**Format:** `note_format` in the settings, `html` by default. The user can override it per request ("as markdown", "as HTML"), and you pass that to `prepare` with `--format`.

**Distilled, not exhaustive:** keep the ideas that matter, explained well and shown visually; leave out repetition, side stories and minor details. There's no length limit. Length comes from how much important material the video has, not from covering everything said.

## Step 1: Tell the user where notes will be saved (every time)

```bash
python3 <skill_dir>/scripts/notes_paths.py where
```

Tell the user in one line where the notes will go, from the "Notes root" in the banner. If the environment is `cloud-sandbox`, say they'll be saved to their Google Drive folder (the banner's "Drive folder") instead, because the local disk is temporary; if they ask how to change it, point them to `config.json` in the yt-transcript skill. Do this on every run. Keep the `topics` list it returns; you'll reuse existing topic names.

## Step 2: Get the source package

Use the **yt-transcript** skill (its script is usually at `<skill_dir>/../yt-transcript/scripts/fetch.py`; if it isn't there, find the yt-transcript skill folder):

```bash
python3 <yt-transcript-dir>/scripts/fetch.py "<youtube url>"
```

Follow yt-transcript's own instructions for exit codes, missing credentials (show the user the credentials message and stop), and the claude.ai connector route. It reuses an already-fetched package, so regenerating notes costs no API credits. You need `source_dir` from its result JSON.

If the transcript can't be obtained, stop and explain why. Never write notes from the title or description alone; the user relies on these notes being real.

## Step 3: Read everything before writing

- Read `meta.json` (title, channel, description, links, chapters, transcript method and kind).
- Read the **whole** transcript markdown. For long videos (over ~15k words), read it in parts, chapter by chapter, and keep a running outline of the ideas, examples, numbers and claims as you go. You read everything so you can choose well, not so that everything goes into the note.
- Note the transcript kind. For `auto`, `ai-generated` and similar, expect misheard jargon and fix it from context.

## Step 4: Plan

Decide, briefly and internally:
- **Note title**: the concept, not the clickbait (e.g. "Consistent Hashing", not "You NEED to know this!!"). Keep the original video title as an alias.
- **Topic**: a broad, reusable folder name in Title Case ("System Design", "Machine Learning", "Python"). **Reuse an existing topic** from the list whenever one fits, so notes on the same subject stay together. Use `Parent/Child` only for big topics.
- **What stays**: distil your outline as described in `references/note-structure.md` (keep, compress or leave out each item). Usually 3–7 key ideas.
- **The visual for each idea** (see `references/visuals.md`): a hand-drawn SVG figure, cards, a compare toggle or a step-through animation. Prefer a picture to a paragraph whenever it explains faster.
- **Tabs** (HTML) or sections (markdown): Overview, Key ideas, plus Walkthrough / Compare only when the video has them, then Takeaways and Source.

## Step 5: Create the folder

```bash
python3 <skill_dir>/scripts/notes_paths.py prepare --source "<source_dir>" --topic "<Topic>" --title "<Note title>"
```

Add `--format markdown` (or `html`) when the user asked for a specific format. It prints JSON with `format`, `note_file` (the `.html` page, or the `.md` note in markdown format), `card_file` (HTML format), `page_wikilink`, `page_embed_block`, `transcript_wikilink`, `drive_dir`, `drive_files` and `today`. If a note for this video already exists, it returns that location (`regenerating_existing_note: true`), and you overwrite it there rather than creating a duplicate. Only pass `--new-location` if the user wants a separate copy.

In a cloud sandbox the user's earlier notes are on Drive, not on this disk, so first search Drive for `fullText contains '<video_id>' and title contains '.md'` (following `nextPageToken`). If a note for this video exists, reuse its topic and title in `prepare`, so the regenerated note replaces it instead of landing in a second folder.

## Step 6: Write the note

Read `references/note-structure.md` (what goes in) and `references/visuals.md` (how to draw it) now.

**HTML format (default):**
1. Read `references/html-notes.md`, copy `assets/note-template.html` to `note_file`, and build the page from its components: tabs, TL;DR, cards, figures with SVG, stepper, compare, takeaways. Delete the template's `data-example` blocks.
2. Write the markdown card to `card_file`: frontmatter, the `page_wikilink`, the TL;DR, related links and the source (format in `note-structure.md`).

**Markdown format:** write the note to `note_file` with `##` sections and inline SVG visuals (rules in `visuals.md`; no Mermaid unless the user asks).

What makes these notes good:
- Distilled: the important ideas only, each explained clearly and pictured where a picture helps.
- Faithful to the video, with anything you add marked as "Added context" or "Correction".
- Intuition first, then the precise point.
- No timestamps, interview questions or flashcards (the user makes those across many notes).
- Links to related notes as `[[File_Name|Readable Name]]`, in the card or markdown note (links can't work inside the HTML page).

## Step 7: Check it

```bash
python3 <skill_dir>/scripts/check_note.py "<note_file>" [--card "<card_file>"]
```

Fix every `ERROR` and re-run until it says `RESULT: OK`. Errors include leftover template blocks, inline handlers that HTML Viewer would strip, broken tabs or anchors, JavaScript errors, invalid SVG and missing frontmatter keys. A warning about Playwright not being installed is fine; then check by reading the page source against `references/html-notes.md` yourself.

## Step 8: Update the indexes

```bash
python3 <skill_dir>/scripts/notes_paths.py index --topic "<Topic>"
```

This rebuilds `<Topic>/_index.md` and the root `_index.md`. In a cloud sandbox, skip this step: the local copy doesn't have the user's other notes. The index will refresh the next time notes are made on their computer, or when they ask to "rebuild my notes index" (`index --all`).

## Step 9: Save to Google Drive (cloud sandbox only)

On claude.ai (web, mobile, desktop chat) the disk is temporary. Use the **gdrive-save** skill to save the files in `drive_files` (the HTML page and its card, or the markdown note) to `drive_dir` from the prepare output, with conflict rule `replace` so regenerated notes overwrite the old ones. If yt-transcript didn't already save the source package to Drive, include `meta.json` and the transcript markdown at `<drive_root>/_sources/<folder>/`.

If gdrive-save isn't installed, use the Google Drive connector directly: find or create each folder (search by title + `parentId`, following `nextPageToken` to the end), then `create_file` with `textContent`, the right `contentMimeType` (`text/markdown`, `text/html`) and `disableConversionToGoogleType: true`. To replace a file, trash the old one first. Never claim the notes are saved when they only exist in the sandbox.

On the user's own computer, files under `notes_root` are already in place; if `notes_root` is inside their Google Drive folder, Drive syncs them.

## Step 10: Report

Keep it short:
- Where the note was saved (full path, and the Drive path if uploaded), and whether it replaced an earlier version.
- One line on what's inside (e.g. "5 tabs: 4 key ideas, 5 illustrations, a step-through of the ring rebalancing").
- For HTML notes, a reminder that the page opens in Obsidian with the HTML Viewer plugin (Scripts ON) or in any browser.
- Transcript caveats (auto/AI-generated) and any credits spent, plus any warnings from yt-transcript.

## Other requests

- **"Regenerate / improve the notes for <video>"**: run the steps again. The cached transcript is reused, and the note is overwritten in place.
- **"Move this note to topic X"**: move the folder on disk, then run `index --all`.
- **Several videos**: process them one at a time, reusing topics so related notes land together.
- **Playlist or series**: one note per video in the same topic, each linking to the others with wikilinks.
