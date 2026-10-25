# yt-transcript

Saves everything about a YouTube video (title, channel, description, links, chapters and the full transcript) as a reusable package on disk or Google Drive.

## What It Does

Tries three sources in order and stops at the first that works:

1. **yt-dlp** (free, local): metadata, chapters and YouTube captions.
2. **TranscriptAPI**: YouTube captions when YouTube blocks yt-dlp (common on cloud and VPN IPs). It can't transcribe videos without captions.
3. **Supadata**: existing captions, or AI speech-to-text when a video has no captions.

When a key is needed but missing, it stops and says which key, where to get it and where to put it. Results are saved to `<notes_root>/_sources/<Video_Title>_<id>/` (`meta.json`, a readable `transcript_<id>.md`, and raw `transcript.json`) and reused on later runs, so the same video never costs credits twice. Folder and file names use underscores instead of spaces. [yt-notes](../yt-notes/) uses it to get the transcript before writing notes.

## Platform

**Claude Code**, **Cursor** and **claude.ai**. On claude.ai it uses the Supadata or TranscriptAPI connectors instead of keys, and saves through [gdrive-save](../../google-drive/gdrive-save/).

## Setup

See the [yt-notes README](../yt-notes/README.md#setup). It covers install, API keys and every config setting (`~/.yt-notes/config.json`, shared by both skills).

## Trigger Phrases

```
"Get the transcript of https://youtu.be/…"
"What does this video say? https://youtube.com/watch?v=…"
"Download the captions and chapters for this video"
```

## Install

```bash
npx skillforge install learning/yt-transcript

# Or via install script
./install.sh learning/yt-transcript
```
