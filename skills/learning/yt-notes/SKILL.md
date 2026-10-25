---
name: yt-notes
description: Turn a YouTube video into deep, visual study notes saved to the user's notes folder (Obsidian-ready markdown with Mermaid diagrams, worked examples, comparison tables, and an optional interactive HTML walkthrough), organised by topic so they can be revisited for learning and interview prep. Uses the yt-transcript skill to get the transcript, description and chapters first. Use this whenever the user shares a YouTube link and asks for notes, study notes, a write-up, a breakdown, a summary to keep, "notes I can refer to later", or wants to "learn this video", even if they don't say "notes" explicitly. Also use it to regenerate or improve notes for a video already processed. For transcript files or screenshots the user already has (e.g. from a course platform) with no YouTube link, use lecture-distiller instead.
---

# yt-notes

Make notes that let the user understand and revise a topic weeks later without rewatching the video. Notes are saved by topic under the shared notes root (default `~/YouTubeNotes`, set in `~/.yt-notes/config.json`):

```
<notes_root>/
  _index.md                                   all topics (auto-generated)
  <Topic>/_index.md                           notes in that topic (auto-generated)
  <Topic>/<Note_Title>/<Note_Title>.md        the note
  <Topic>/<Note_Title>/<Note_Title>_interactive.html   (only when it earns its place)
  _sources/<Video_Title>_<id>/                transcript package from yt-transcript
```

**Naming rule:** folder and file names use underscores instead of spaces, e.g. `System_Design/Consistent_Hashing/Consistent_Hashing.md`. Pass normal titles with spaces to the scripts; they convert them. Follow the same rule for anything you name yourself (Drive folders, extra files). Titles *inside* notes (headings, frontmatter `title`, wikilink labels) keep their spaces.

Depth defaults to **deep**. Use quick mode only if the user asks for a summary or quick notes.

## Step 1: Tell the user where notes will be saved (every time)

```bash
python3 <skill_dir>/scripts/notes_paths.py where
```

Tell the user in one line where the notes will go, from the "Notes root" in the banner. If the environment is `cloud-sandbox`, say they'll be saved to their Google Drive folder `<drive_root>/…` instead, because the local disk is temporary. Do this on every run. Keep the `topics` list it returns; you'll reuse existing topic names.

## Step 2: Get the source package

Use the **yt-transcript** skill (its script is usually at `<skill_dir>/../yt-transcript/scripts/fetch.py`; if it isn't there, find the yt-transcript skill folder):

```bash
python3 <yt-transcript-dir>/scripts/fetch.py "<youtube url>"
```

Follow yt-transcript's own instructions for exit codes, missing credentials (show the user the credentials message and stop), and the claude.ai connector route. It reuses an already-fetched package, so regenerating notes costs no API credits. You need `source_dir` from its result JSON.

If the transcript can't be obtained, stop and explain why. Never write notes from the title or description alone; the user relies on these notes being real.

## Step 3: Read everything before writing

- Read `meta.json` (title, channel, description, links, chapters, transcript method and kind).
- Read the **whole** transcript markdown. For long videos (over ~15k words), read it in parts, chapter by chapter, and keep a running outline of concepts, examples, numbers and claims as you go. Depth comes from the details: the specific numbers, examples, caveats and comparisons the speaker gives.
- Note the transcript kind. For `auto`, `ai-generated` and similar, expect misheard jargon and fix it from context.

## Step 4: Plan

Decide, briefly and internally:
- **Note title**: the concept, not the clickbait (e.g. "Consistent Hashing", not "You NEED to know this!!"). Keep the original video title as an alias.
- **Topic**: a broad, reusable folder name in Title Case ("System Design", "Machine Learning", "Python"). **Reuse an existing topic** from the list whenever one fits, so notes on the same subject stay together. Use `Parent/Child` only for big topics.
- The core concepts, the mechanisms worth a diagram (see `references/visuals.md`), the worked examples, and the comparisons.
- Whether an interactive walkthrough is worth building (see `references/interactive-html.md`). Usually it isn't, unless something changes step by step.

## Step 5: Create the folder

```bash
python3 <skill_dir>/scripts/notes_paths.py prepare --source "<source_dir>" --topic "<Topic>" --title "<Note title>"
```

It prints JSON with `note_file`, `interactive_file`, `transcript_wikilink`, `interactive_wikilink`, `interactive_embed_block` and `today`. If a note for this video already exists, it returns that location (`regenerating_existing_note: true`), and you overwrite it there rather than creating a duplicate. Only pass `--new-location` if the user wants a separate copy.

In a cloud sandbox the user's earlier notes are on Drive, not on this disk, so first search Drive for `fullText contains '<video_id>' and title contains '.md'` (following `nextPageToken`). If a note for this video exists, reuse its topic and title in `prepare`, so the regenerated note replaces it instead of landing in a second folder.

## Step 6: Write the note

Follow `references/note-structure.md` (read it now): frontmatter, TL;DR, Why this matters, Big picture, Core concepts, How it works, Worked examples, Comparisons, Pitfalls, Takeaways, Glossary, Related, Source. Use `references/visuals.md` for diagrams and Obsidian-safe Mermaid syntax.

What makes these notes good:
- Faithful to the video, with anything you add marked in `> [!info] Added context` or `> [!warning] Correction` callouts.
- Intuition first, then precise detail; a concrete example for every core concept.
- Diagrams placed where they explain something, each with a sentence on how to read it.
- No timestamps, interview questions or flashcards (the user makes those across many notes).
- Wikilinks to related concepts as `[[File_Name|Readable Name]]`, which builds the user's Obsidian graph. Link targets use the underscore file name, since a plain `[[Cache Stampede]]` won't find `Cache_Stampede.md`.

Write the note to `note_file`. If you build an interactive walkthrough, copy `assets/interactive-template.html` to `interactive_file`, fill it in, and link it in the note as described in `references/interactive-html.md`.

## Step 7: Check it

```bash
python3 <skill_dir>/scripts/check_note.py "<note_file>" [--html "<interactive_file>"]
```

Fix every `ERROR` (broken Mermaid, missing frontmatter keys, leftover placeholders, JavaScript errors) and re-run until it says `RESULT: OK`. Warnings about missing optional tools (mmdc, Playwright) are fine; in that case re-read your Mermaid blocks against the rules in `references/visuals.md` yourself.

## Step 8: Update the indexes

```bash
python3 <skill_dir>/scripts/notes_paths.py index --topic "<Topic>"
```

This rebuilds `<Topic>/_index.md` and the root `_index.md`. In a cloud sandbox, skip this step: the local copy doesn't have the user's other notes. The index will refresh the next time notes are made on their computer, or when they ask to "rebuild my notes index" (`index --all`).

## Step 9: Save to Google Drive (cloud sandbox only)

On claude.ai (web, mobile, desktop chat) the disk is temporary. Use the **gdrive-save** skill to save the note (and the interactive file, if any) to `drive_dir` from the prepare output, with conflict rule `replace` so regenerated notes overwrite the old ones. If yt-transcript didn't already save the source package to Drive, include `meta.json` and the transcript markdown at `<drive_root>/_sources/<folder>/`.

If gdrive-save isn't installed, use the Google Drive connector directly: find or create each folder (search by title + `parentId`, following `nextPageToken` to the end), then `create_file` with `textContent`, the right `contentMimeType` (`text/markdown`, `text/html`) and `disableConversionToGoogleType: true`. To replace a file, trash the old one first. Never claim the notes are saved when they only exist in the sandbox.

On the user's own computer, files under `notes_root` are already in place; if `notes_root` is inside their Google Drive folder, Drive syncs them.

## Step 10: Report

Keep it short:
- Where the note was saved (full path, and the Drive path if uploaded), and whether it replaced an earlier version.
- One line on what's inside (e.g. "6 concepts, 4 diagrams, 2 worked examples, interactive walkthrough of the ring rebalancing").
- Transcript caveats (auto/AI-generated) and any credits spent, plus any warnings from yt-transcript.

## Other requests

- **"Regenerate / improve the notes for <video>"**: run the steps again. The cached transcript is reused, and the note is overwritten in place.
- **"Move this note to topic X"**: move the folder on disk, then run `index --all`.
- **Several videos**: process them one at a time, reusing topics so related notes land together.
- **Playlist or series**: one note per video in the same topic, each linking to the others with wikilinks.
