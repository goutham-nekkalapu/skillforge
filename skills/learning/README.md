# Learning

Skills for transforming educational content into structured, revision-friendly study materials — from video transcripts and course recordings to concise notes and visual aids.

## Skills in This Group

| Skill | Platform | Description |
|-------|----------|-------------|
| [lecture-distiller](lecture-distiller/) | All | Distills video transcripts and screenshots you already have into structured, scannable study notes |
| [yt-notes](yt-notes/) | All | Turns a YouTube link into distilled, visual notes: a tabbed HTML page with illustrations and animations (or markdown with inline SVG), saved by topic |
| [yt-transcript](yt-transcript/) | All | Saves a YouTube video's transcript, description and chapters (yt-dlp → TranscriptAPI → Supadata AI fallback) |

`yt-notes` uses `yt-transcript`, and on claude.ai saves through [google-drive/gdrive-save](../google-drive/gdrive-save/). Install all three together. Setup: [yt-notes README](yt-notes/README.md).

## lecture-distiller or yt-notes?

**Rule of thumb: YouTube link → `yt-notes`. Transcript files or screenshots you already have → `lecture-distiller`.**

| | lecture-distiller | yt-notes |
|---|---|---|
| **You give it** | Transcript files (`v1.md`, `v2.md`…) and screenshots, e.g. from Coursera, Udemy, deeplearning.ai | A YouTube link |
| **Gets the transcript** | No, you supply it | Yes, fetches transcript, description and chapters (via `yt-transcript`) |
| **Scope** | A whole course module: several videos merged into one document | One video → one note |
| **Style** | Condensed: 20–30% of the transcript, bullet points, quick revision | Distilled and visual: the ideas that matter, explained with intuition and pictures |
| **Visuals** | Your screenshots as numbered figures, plus diagrams | Hand-drawn SVG illustrations, step-through animations and toggles in a tabbed HTML page |
| **Self-test questions** | Yes | No (build them later across many notes) |
| **Saves to** | One markdown file, wherever you are working | Your notes folder by topic (`<Topic>/<Title>/`): an HTML page plus a markdown card (or a markdown note), with indexes; Google Drive on claude.ai |
| **Obsidian extras** | No | Frontmatter, `[[wikilinks]]`, callouts, links to the saved transcript |

## Install All Learning Skills

```bash
npx skillforge install learning

# Or via install script
./install.sh learning
```
