# yt-notes

Paste a YouTube link, ask for notes, and get deep, visual, Obsidian-ready study notes saved by topic.

## What It Does

Fetches the video's transcript, description and chapters (via [yt-transcript](../yt-transcript/)), picks out the ideas that matter (leaving out repetition, side stories and minor details), and turns them into a visual note.

- **HTML format (default):** one self-contained page per note, with tabs for each section, home and back-to-top buttons, cards, callouts, hand-drawn SVG illustrations you can expand, step-through animations and before/after toggles. A small markdown card next to it keeps the note in Obsidian search, tags and the topic index.
- **Markdown format:** an Obsidian note with inline SVG illustrations. Ask for it per note ("as markdown") or set `note_format`.

Notes are checked automatically (the page loads without errors, tabs work, illustrations are valid) and organised as `<Topic>/<Note_Title>/` with an auto-built index per topic. Folder and file names use underscores instead of spaces (e.g. `System_Design/Consistent_Hashing/Consistent_Hashing.html`); titles inside the notes keep their spaces.

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
4. Optional: to use a different Drive folder, change `drive_root` in the yt-transcript skill's `config.json` (see [Configure](#configure)).

## Configure

Both skills share one set of settings. Where you edit them depends on where you run the skills:

- **On your computer** (Claude Code, Cursor): `~/.yt-notes/config.json`, created on the first run.
- **On claude.ai** (web, mobile, desktop chat): `config.json` inside the **yt-transcript** skill. That file is kept with the skill, so changes persist; yt-notes reads it too, so there's one file to edit. Open the skill's files in claude.ai and edit `config.json` directly (or select a value and use **Edit with Claude**).

Settings:

| Setting | Default | What it does |
|---|---|---|
| `notes_root` | `~/YouTubeNotes` | Where notes are saved on your computer. Point it at your Drive-synced folder. |
| `drive_root` | `YouTubeNotes` | The same folder as seen from Google Drive, used on web/mobile. |
| `languages` | `["en"]` | Preferred transcript languages. |
| `ytdlp_args` | `[]` | `["--cookies-from-browser","chrome"]` fixes YouTube's "not a bot" check. |
| `transcriptapi_key` | empty | Fallback when yt-dlp is blocked (or set `TRANSCRIPTAPI_KEY`). Sign up at https://transcriptapi.com/signup, then create a key at https://transcriptapi.com/dashboard/api-keys |
| `supadata_key` | empty | AI transcription for videos with no captions (or set `SUPADATA_API_KEY`). Sign up at https://dash.supadata.ai, then copy your key from https://dash.supadata.ai/organizations/api-key |
| `tiers` | yt-dlp, TranscriptAPI, Supadata | Order of transcript sources to try. |
| `note_format` | `html` | `html` (rich tabbed page plus a markdown card) or `markdown` (markdown note with inline SVG). Override per request: "make these notes as markdown". |
| `obsidian_vault_root` | empty | Your vault path. Usually not needed: it's found automatically from the `.obsidian` folder above `notes_root`. Used for the optional inline embed in cards. |

On claude.ai, only `drive_root`, `note_format`, `languages` and `tiers` matter. Leave API keys out of the skill's `config.json` and use the Supadata / TranscriptAPI connectors instead.

If a setting appears in several places, later ones win: built-in defaults → the skill's `config.json` → `~/.yt-notes/config.json` (values you haven't changed from the defaults are ignored) → environment variables. Every run shows which files it loaded.

In the request itself: ask for a format (*"as markdown"*), name a topic (*"…under Machine Learning"*), say *"regenerate"* to redo a note, or ask for more or less detail.

### Obsidian

- Settings → Files & links → **Show all file types** (so `.html` notes appear).
- Install the **HTML Viewer** community plugin and turn **Scripts: ON** to open HTML notes with tabs and animations. Any browser works too.
- The markdown card (`<Note_Title>.md`) is what Obsidian search, tags, the graph and the index see. Open the full page from its "Open the full note" link.
- Links to other notes live in the cards, because HTML Viewer doesn't let a page navigate to other files. Inside a page, the home button goes to the first tab and the arrow to the top.

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
| `references/visuals.md` | Which visual to use, and how to draw SVG (HTML and inline markdown) |
| `references/html-notes.md` | Building HTML notes: components and HTML Viewer rules |
| `assets/note-template.html` | Self-contained note page: tabs, home/top buttons, cards, figures, stepper, compare (offline, light/dark) |
| `scripts/notes_paths.py` | Folder naming, regenerate-in-place, topic indexes |
| `scripts/check_note.py` | Checks frontmatter, renders diagrams, tests the HTML page |
| `examples/sample-output/` | A sample HTML note and its card (made from a short test transcript, not a real video) |

## Future Improvements

Today's illustrations are hand-drawn SVG inside HTML pages or markdown notes. Next steps for visuals you can also edit by hand:

| Idea | What it adds | How |
|---|---|---|
| **Excalidraw diagrams** | Hand-drawn style diagrams you can rearrange and annotate while revising | Generate 1–2 key diagrams per note as Obsidian Excalidraw files (`.md` with `excalidraw-plugin: parsed` frontmatter) and embed them with `![[…]]`. Delegate to an existing skill such as [excalidraw-diagram](https://skillselion.com/skills/axtonliu/axton-obsidian-visual-skills/excalidraw-diagram) when it's installed, instead of reimplementing the format. Needs the [Obsidian Excalidraw plugin](https://github.com/zsviczian/obsidian-excalidraw-plugin). |
| **tldraw boards** | A whiteboard-style concept map per note or topic | The official [tldraw Obsidian plugin](https://community.obsidian.md/plugins/tldraw) stores drawings as markdown files. A tldraw MCP server, where connected, lets Claude build the board on a live canvas, which could then be exported into the vault. Inline previews inside notes are still on the plugin's roadmap, so link boards rather than embedding them. |
| **Obsidian Canvas per topic** | A visual map of all notes in a topic and how they link | Generate `<Topic>/<Topic>.canvas` (Obsidian's native JSON format; no plugin, works on mobile) from the topic index: one card per note, edges from `[[wikilinks]]`. Rebuild it with `notes_paths.py index`. Probably the easiest first step. |
| **Static image fallback** | Illustrations visible where JavaScript doesn't run (Drive preview, other apps) | Export each figure's SVG to its own file next to the note. |

Design guardrails for these:
- Add a `visual_formats` config setting (default `["svg"]`), so other formats are opt-in and SVG remains the fallback.
- Prefer calling an installed visual skill over adding format-specific code here.
- Extend `check_note.py` to validate each new format (e.g. parse the Excalidraw/Canvas JSON, check embeds resolve).
- These are all plain text files (`.md`, `.canvas`, `.excalidraw` JSON), so [gdrive-save](../../google-drive/gdrive-save/) can already save them from claude.ai.
