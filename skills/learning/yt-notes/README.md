# yt-notes

Paste a YouTube link, ask for notes, and get deep, visual, Obsidian-ready study notes saved by topic.

## What It Does

Fetches the video's transcript, description and chapters (via [yt-transcript](../yt-transcript/)), then writes notes with a TL;DR, core concepts, Mermaid diagrams, worked examples, comparison tables, pitfalls and `[[wikilinks]]`. When a topic involves something changing step by step, it also builds an interactive HTML walkthrough. Notes are checked (diagrams must render) and organised as `<Topic>/<Note Title>/<Note Title>.md` with an auto-built index per topic.

Works together with:

| Skill | Does |
|---|---|
| [yt-transcript](../yt-transcript/) | Gets the title, description, chapters and transcript (yt-dlp → TranscriptAPI → Supadata AI) |
| `yt-notes` | Writes the notes from that transcript |
| [gdrive-save](../../google-drive/gdrive-save/) | Saves files to Google Drive (used on web/mobile) |

## Platform

**Claude Code**, **Cursor** and **claude.ai** (web, mobile, desktop chat).

## Setup

### Local: Claude Code / Cursor (Mac)

```bash
brew install yt-dlp deno
./install.sh learning/yt-transcript
./install.sh learning/yt-notes
./install.sh google-drive/gdrive-save          # add --platform cursor for Cursor
```

Ask: *"Make notes from https://youtube.com/watch?v=…"*. Files are saved to `~/YouTubeNotes`.

### Web / mobile: claude.ai

1. Zip each skill folder (`yt-transcript`, `yt-notes`, `gdrive-save`) and upload it: **Customize → Skills → + → Upload a skill**.
2. **Customize → Connectors**: connect **Google Drive** (required) and **Supadata** (gets transcripts; no key needed).
3. Ask the same way. Notes are saved to `My Drive/YouTubeNotes`.

## Configure

Edit `~/.yt-notes/config.json` (created on first run):

| Setting | Default | What it does |
|---|---|---|
| `notes_root` | `~/YouTubeNotes` | Where notes are saved on your computer. Point it at your Drive-synced folder. |
| `drive_root` | `YouTubeNotes` | The same folder as seen from Google Drive, used on web/mobile. |
| `languages` | `["en"]` | Preferred transcript languages. |
| `ytdlp_args` | `[]` | `["--cookies-from-browser","chrome"]` fixes YouTube's "not a bot" check. |
| `transcriptapi_key` | empty | Fallback when yt-dlp is blocked (or set `TRANSCRIPTAPI_KEY`). Sign up at https://transcriptapi.com/signup, then create a key at https://transcriptapi.com/dashboard/api-keys |
| `supadata_key` | empty | AI transcription for videos with no captions (or set `SUPADATA_API_KEY`). Sign up at https://dash.supadata.ai, then copy your key from https://dash.supadata.ai/organizations/api-key |
| `tiers` | yt-dlp, TranscriptAPI, Supadata | Order of transcript sources to try. |
| `obsidian_vault_root` | empty | Your vault path; lets notes embed interactive pages inline. |

On claude.ai the config file isn't kept between sessions. To change `drive_root` there, put a `config.json` with that setting inside the yt-transcript and yt-notes folders before zipping them.

In the request itself: say *"quick notes"* for a shorter version, name a topic (*"…under Machine Learning"*), or say *"regenerate"* to redo a note.

### Obsidian

Settings → Files & links → **Show all file types**. Install **HTML Experience** (with scripts enabled) to open interactive walkthroughs.

## Trigger Phrases

```
"Make notes from https://youtu.be/…"
"Turn this video into study notes I can refer to later"
"Regenerate the notes for this video"
```

## Good to Know

- Every run tells you where files will be saved.
- yt-dlp is free; API keys are only needed as fallbacks. AI transcription (Supadata) costs 2 credits per minute of video.
- Videos already fetched are reused, so regenerating notes costs nothing.
- On web/mobile, notes go to the Google account the Drive connector uses. Sync that account on your computer.
- For transcript files or screenshots you already have (e.g. from a course platform), use [lecture-distiller](../lecture-distiller/).

## Included Files

| File | Purpose |
|------|---------|
| `SKILL.md` | The workflow the agent follows |
| `references/note-structure.md` | Note template and writing rules |
| `references/visuals.md` | Which diagram to use, and Obsidian-safe Mermaid syntax |
| `references/interactive-html.md` | When and how to build interactive walkthroughs |
| `assets/interactive-template.html` | Self-contained walkthrough template (offline, light/dark) |
| `scripts/notes_paths.py` | Folder naming, regenerate-in-place, topic indexes |
| `scripts/check_note.py` | Checks frontmatter, renders diagrams, tests the HTML page |
| `examples/sample-output/` | A sample note (made from a short test transcript, not a real video) |

## Future Improvements

Today every diagram is Mermaid (rendered natively by Obsidian, but fixed layout) plus optional interactive HTML. Next steps for richer, editable visuals:

| Idea | What it adds | How |
|---|---|---|
| **Excalidraw diagrams** | Hand-drawn style diagrams you can rearrange and annotate while revising | Generate 1–2 key diagrams per note as Obsidian Excalidraw files (`.md` with `excalidraw-plugin: parsed` frontmatter) and embed them with `![[…]]`. Delegate to an existing skill such as [excalidraw-diagram](https://skillselion.com/skills/axtonliu/axton-obsidian-visual-skills/excalidraw-diagram) when it's installed, instead of reimplementing the format. Needs the [Obsidian Excalidraw plugin](https://github.com/zsviczian/obsidian-excalidraw-plugin). |
| **tldraw boards** | A whiteboard-style concept map per note or topic | The official [tldraw Obsidian plugin](https://community.obsidian.md/plugins/tldraw) stores drawings as markdown files. A tldraw MCP server, where connected, lets Claude build the board on a live canvas, which could then be exported into the vault. Inline previews inside notes are still on the plugin's roadmap, so link boards rather than embedding them. |
| **Obsidian Canvas per topic** | A visual map of all notes in a topic and how they link | Generate `<Topic>/<Topic>.canvas` (Obsidian's native JSON format; no plugin, works on mobile) from the topic index: one card per note, edges from `[[wikilinks]]`. Rebuild it with `notes_paths.py index`. Probably the easiest first step. |
| **Static image fallback** | Diagrams visible where Mermaid or JavaScript don't run (Drive preview, other markdown apps) | Export each Mermaid diagram to SVG with `mmdc` (already used by `check_note.py`) and keep it next to the note. |

Design guardrails for these:
- Add a `visual_formats` config setting (default `["mermaid"]`), so richer formats are opt-in and Mermaid always remains as a fallback that renders everywhere.
- Prefer calling an installed visual skill over adding format-specific code here.
- Extend `check_note.py` to validate each new format (e.g. parse the Excalidraw/Canvas JSON, check embeds resolve).
- These are all plain text files (`.md`, `.canvas`, `.excalidraw` JSON), so [gdrive-save](../../google-drive/gdrive-save/) can already save them from claude.ai.
