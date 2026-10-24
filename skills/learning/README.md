# Learning

Skills for transforming educational content into structured, revision-friendly study materials — from video transcripts and course recordings to concise notes and visual aids.

## Skills in This Group

| Skill | Platform | Description |
|-------|----------|-------------|
| [lecture-distiller](lecture-distiller/) | All | Distills video transcripts and screenshots you already have into structured, scannable study notes |
| [yt-notes](yt-notes/) | All | Turns a YouTube link into deep, visual, Obsidian-ready notes (diagrams, examples, interactive walkthroughs), saved by topic |
| [yt-transcript](yt-transcript/) | All | Saves a YouTube video's transcript, description and chapters (yt-dlp → TranscriptAPI → Supadata AI fallback) |

`yt-notes` uses `yt-transcript`, and on claude.ai saves through [google-drive/gdrive-save](../google-drive/gdrive-save/). Install all three together. Setup: [yt-notes README](yt-notes/README.md).

## Install All Learning Skills

```bash
npx skillforge install learning

# Or via install script
./install.sh learning
```
