# Interactive HTML walkthroughs

A companion `.html` file for ideas that are easier to understand by watching them change: algorithms (sorting, a hash ring rebalancing, Raft leader election), request flows, state machines, data structures being modified, and protocols over time. Build one only when stepping through it clearly beats a static diagram. Most notes don't need one, and a weak animation is worse than a good diagram.

**Make one when** the video explains a dynamic process with 4+ distinct stages, where seeing the state at each step is the point.
**Skip it when** the idea is static (definitions, comparisons, opinions), or a single Mermaid sequence diagram already makes it clear.

## How to build it

1. Copy `assets/interactive-template.html` to the `interactive_file` path from `notes_paths.py prepare`.
2. Replace the parts marked `REPLACE`:
   - `<title>`, heading and subtitle.
   - The SVG scene: draw every element once with an `id`. Use `class="always"` for things always visible and `class="el"` for things that appear in some steps. Group a box and its label in `<g id="...">`. Keep the `viewBox` wide (e.g. `0 0 860 300`) so it fits a note pane.
   - `STEPS`: 4–10 steps, each with `title`, `text` (what changes and *why*), `show`, `highlight`, `flow` (animated edges), `dim`, optional `state` chips (variables, counters, costs) and optional `onEnter(api)` for custom effects (e.g. moving an element with `api.$("id").setAttribute(...)`).
3. Keep the engine code as is unless a feature needs changing.

## Rules

- **Self-contained, offline**: no CDN scripts, web fonts or network calls. Obsidian's HTML plugins run the page in a sandboxed frame, often offline.
- **Accurate**: the animation must match what the video teaches. Use the video's own example values where it gives them.
- **Readable in both themes**: use the template's CSS variables instead of hard-coded colours.
- **Small**: one file, typically under 40 KB.
- Respect `prefers-reduced-motion` (the template already does).
- Captions explain; the picture shows. Each step's text should make sense on its own.

## Linking it from the note

Put it in the relevant section of the note (usually "How it works"), not at the end:

1. If `interactive_embed_block` from `prepare` is not null, paste that block. It's an `html-embed` code block, rendered inline by the Obsidian **HTML Embed** plugin.
2. Always also add the wikilink from `interactive_wikilink` (`[[<Title> - interactive.html|▶ Open the interactive walkthrough]]`). It opens the file in an HTML viewer plugin (HTML Experience, Vault HTML Preview, etc.) and still works on mobile or without the embed plugin.
3. Keep a static Mermaid diagram of the same idea in the note, so it still makes sense where HTML can't run.

Obsidian needs **Settings → Files & links → Show all file types** turned on, plus an HTML viewer plugin with JavaScript enabled, to open the file.

## Check it

`python3 <skill_dir>/scripts/check_note.py "<note.md>" --html "<interactive.html>"` loads the page in a headless browser (when Playwright is available), clicks through the controls and reports JavaScript errors.
