---
name: yt-transcript
description: Fetch and save everything about a YouTube video — title, channel, description, links, chapters/timestamps and the full transcript — to a standard "source package" on disk (and Google Drive from claude.ai). Tries free local yt-dlp first, then TranscriptAPI.com when YouTube blocks it, then Supadata AI transcription when the video has no captions at all. Use this whenever the user shares a YouTube link and wants its transcript, captions, subtitles, description or chapters, says "get/grab/pull/download the transcript", or when another skill (such as yt-notes) needs a video's content. Use it even if the user only says "what does this video say" with a YouTube URL.
---

# yt-transcript

Turn a YouTube URL into a saved source package that other skills (notably `yt-notes`) build on:

```
<notes_root>/_sources/<Video Title> - <video_id>/
  meta.json                     # title, channel, dates, tags, description, links, chapters, how the transcript was obtained
  transcript - <video_id>.md    # readable in Obsidian: description, chapters, transcript grouped by chapter
  transcript.json               # raw timed segments [{start, text}]
```

The default `notes_root` is `~/YouTubeNotes` (the device's home folder). The user changes it in the config file `~/.yt-notes/config.json`, which is shared with `yt-notes`.

## Step 1: Tell the user where things will be saved (every time)

Before fetching anything, run:

```bash
python3 <skill_dir>/scripts/fetch.py --where
```

Then tell the user in one line where the transcript will be saved, using the "Notes root" / "Transcripts" paths it prints. Do this on every run, not just the first: the user wants to see the location each time. If it says `Environment: cloud-sandbox`, the local disk is temporary, so tell them the files will go to their Google Drive folder `<drive_root>/_sources/` instead (see Step 4). If the banner says the config file was just created, mention that they can edit `notes_root` in it.

## Step 2: Fetch

```bash
python3 <skill_dir>/scripts/fetch.py "<youtube url or id>"
```

The script prints progress and ends with a block between `=== RESULT JSON ===` and `=== END RESULT ===`. Read that block; it holds the paths, transcript method and any warnings.

- It reuses an existing package for the same video (status `cached`) instead of spending API credits again. Add `--force` only if the user asks to re-fetch.
- `--tiers supadata` (or any comma list) forces specific sources; `--root <path>` overrides the location for one run.

What the tiers do, so you can explain results:

| Tier | Cost | Gets | Fails when |
|---|---|---|---|
| `ytdlp` | free | metadata, real chapters, YouTube captions | not installed, or YouTube's bot check (common on cloud IPs) |
| `transcriptapi` | 1 credit transcript + 1 metadata | YouTube captions (manual or auto) | video has **no captions** (it cannot transcribe audio) |
| `supadata` (`mode=auto`) | 1 credit if captions exist, else **2 credits per minute** | captions, or AI speech-to-text | key missing, private/age-restricted video |

When yt-dlp shows the video has no captions, the script skips TranscriptAPI (it would fail) and goes straight to Supadata. Long AI transcriptions run as background jobs; the script polls until done (can take minutes), so give it a generous timeout (e.g. 30 minutes) and let it run.

## Step 3: Handle the exit code

| Exit | Meaning | What to do |
|---|---|---|
| 0 | Saved (or reused from cache) | Report: title, transcript source and kind, words, chapters, credits used, saved path. Relay every item in `warnings`. |
| 3 | `credentials_needed` | Show the user the `=== CREDENTIALS NEEDED ===` block (which key is missing, where to get it, and how to set it), then stop and wait. **On claude.ai, first try the connector route** in `references/connector-path.md`, since connectors avoid keys entirely. |
| 4 | `network_blocked` | The sandbox can't reach the APIs (typical on claude.ai). Use `references/connector-path.md`. |
| 2 | `failed` / `video_unavailable` | Explain the `log` lines in plain words. Private, deleted, members-only and live videos can't be fetched. |
| 5 | Bad input | Ask for a valid YouTube link. |

Never invent or reconstruct a transcript yourself if all tiers fail; the notes depend on it being real.

Fixes worth suggesting when relevant:
- **yt-dlp not installed** (Claude Code / Cursor on a Mac): `brew install yt-dlp deno` or `pip install -U yt-dlp`. Deno lets yt-dlp solve YouTube's JavaScript checks. Keep yt-dlp updated (`brew upgrade yt-dlp`), because YouTube changes often break old versions.
- **"bot check"** on the user's own computer: set `"ytdlp_args": ["--cookies-from-browser", "chrome"]` (or `safari`/`firefox`) in the config. This uses their signed-in browser session and is free.
- **Auto/AI transcript**: the transcript file already carries a warning that names and technical terms may be misheard. Pass that caveat on.

## Step 4: Make sure the files persist

- **Local (Claude Code, Cursor, or any agent running on the user's own computer):** the files are already in `notes_root`. If `notes_root` sits inside the user's Google Drive folder, Drive syncs it.
- **Cloud sandbox (claude.ai web, mobile, desktop chat):** the sandbox disk disappears after the session, so save `meta.json` and `transcript - <id>.md` to Google Drive at `<drive_root>/_sources/<folder name>/` using the **gdrive-save** skill (conflict rule: `replace`). Skip `transcript.json` on Drive: it duplicates the markdown and costs a lot of tokens to upload.
  - If gdrive-save isn't installed, do the same directly with the Google Drive connector: find or create each folder (search by title + `parentId`, following `nextPageToken` to the end), then `create_file` with `textContent`, the right `contentMimeType` and `disableConversionToGoogleType: true`. To replace a file, trash the old one first.
  - Before fetching on claude.ai, it's worth checking Drive for an existing package: search `<drive_root>/_sources` for a folder whose title contains ` - <video_id>` and reuse its files instead of spending credits again.

Finish by telling the user exactly where the package was saved (local path and/or Drive path).

## When called from yt-notes

Do Steps 1–4 as usual, then hand back the `source_dir` and file paths from the result JSON. The notes skill reads `meta.json` and the transcript markdown from there.
