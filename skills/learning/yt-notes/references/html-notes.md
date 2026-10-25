# HTML notes (the default format)

Each note is one self-contained page, `<Note_Title>.html`, built from `assets/note-template.html`. It has a header, a tab bar, one panel per tab, floating **home** (first tab) and **top** buttons, and reusable components for illustrations and animations. A small markdown card (`<Note_Title>.md`, see `note-structure.md`) sits next to it for Obsidian search, tags and links.

## Build it

1. Copy `assets/note-template.html` to `note_file` from `notes_paths.py prepare`.
2. Fill in everything marked `REPLACE`: the `<title>`, kicker (`Topic · Channel`), title, lede (1–2 sentence summary), meta pills, tabs and panels, and the footer date.
3. **Tabs**: 3–7, one per panel, with the same ids in the same order (`<a class="tab" href="#key-ideas">` ↔ `<section class="panel" id="key-ideas">`). Ids are lowercase-hyphenated. Pick tabs from `note-structure.md`, renaming them when a domain name reads better.
4. Build the content from the components below. **Delete every block marked `data-example`.** The checker fails if any remain.
5. Don't edit the CSS or the engine script unless a component truly needs it. If you add CSS, add it at the end of the `<style>` block.

## Components

| Component | Markup | Without JS |
|---|---|---|
| **TL;DR** | `<div class="tldr"><h2>TL;DR</h2><ul>…</ul></div>` | same |
| **Cards** | `<div class="cards">` with `<div class="card c-teal"><div class="card-head"><strong>Title</strong><span>subtitle</span></div><div class="card-body"><p>…</p><span class="pill">label</span></div></div>` | same |
| **Callout** | `<div class="callout">` (default), `callout warn`, `callout added` (anything not from the video), with `<span class="label">…</span><p>…</p>` | same |
| **Figure** | `<figure class="figure"><svg viewBox="…">…</svg><figcaption>…</figcaption></figure>`, which gets an **Expand** button | same, minus the button |
| **Stepper** | `<div class="figure stepper">`: an SVG scene, then `<ol class="steps">` with one `<li data-show="ids" data-hl="ids" data-flow="ids" data-dim="ids"><strong>Title</strong> text</li>` per step. Scene elements with `class="el"` are hidden until a step lists them in `data-show` | full scene plus the steps as a numbered list |
| **Compare** | `<div class="compare">` with two or more `<div class="compare-pane" data-label="Before">…</div>`. JS turns them into a toggle | panes side by side |
| **Takeaways** | `<ol class="takeaways"><li>…</li></ol>`, rendered as numbered cards | same |
| **Table / code** | plain `<table>`, `<pre><code>` | same |
| **Source tag** (combined notes) | `<span class="vtag v2">V2</span>` after a heading or point that comes mainly from one video; `v1`…`v5` have distinct colours | same |
| **Coverage grid** (combined notes) | `<table class="coverage">` with ideas as rows and `V1`… as columns; cells `<td class="full"></td>` (in depth), `<td class="part"></td>` (briefly) or `<td class="none"></td>` (not covered), drawn as filled, half-filled and dash markers. Add the legend under it: `<p class="cov-legend"><span><span class="dot full"></span> in depth</span><span><span class="dot part"></span> briefly</span><span>– not covered</span></p>` | same |
| **Sources list** (combined notes) | `<ul class="sources-list"><li><span class="vtag v1">V1</span> <strong>Title</strong> · channel · date · duration · transcript kind</li>…</ul>` | same |
| **Mini contents** | automatic: a panel with 3+ `<h3 id="…">` gets clickable chips under its `<h2>` | `h3`s still visible |

Visual drawing rules (sizes, spacing, colour classes, animation) are in `visuals.md`.

## Rules for Obsidian's HTML Viewer

The user opens these pages in Obsidian with the **HTML Viewer** plugin (Scripts ON). It renders the page in a sandboxed frame:
- **Inline event handlers (`onclick="…"`, `onload=…`) and `javascript:` URLs are always stripped.** Attach behaviour in a `<script>` with `addEventListener`, as the template's engine does. The checker flags these.
- **No navigation out of the page.** Links to other files, `obsidian://` links and new windows don't work. Keep navigation in-page: tabs, `#anchors`, and the home/top buttons. Put links to other notes and the transcript in the markdown card. A video link in the Source tab is fine to show, but don't rely on it opening.
- **`#anchor` links work**, so tabs deep-link (`Consistent_Hashing.html#walkthrough`).
- **`localStorage` resets on every refresh**, so don't store anything important in it.
- **Self-contained**: no CDN scripts, web fonts or images from the internet, so the page also works offline.
- **Without JavaScript** (Scripts OFF) the template shows every panel in order and the tab bar works as a table of contents. Keep content readable that way: don't hide essential text behind interactions.

## Size

Aim for a page that loads instantly: typically 30–80 KB. Inline SVG is small; avoid embedding large images as base64. On claude.ai the page is uploaded through the conversation, so very large pages cost more of the user's usage.

## Check it

`python3 <skill_dir>/scripts/check_note.py "<note.html>" --card "<card.md>"` checks:
- the page loads without JavaScript errors;
- every tab opens its panel;
- every in-page link has a target;
- no inline handlers, `javascript:` URLs, external scripts or leftover `data-example` blocks remain;
- the page is readable without JavaScript;
- the card's frontmatter is complete.
