# HTML notes (the default format)

Each note is one self-contained page, `<Note_Title>.html`, built from `assets/note-template.html`. It has a header, a tab bar, one panel per tab, floating **home** (first tab) and **top** buttons, and a library of HTML/CSS components for illustrations and animations. Illustrations are written as short HTML (`<div class="node">…</div>`), never as hand-drawn SVG; the template's CSS does the drawing. A small markdown card (`<Note_Title>.md`, see `note-structure.md`) sits next to it for Obsidian search, tags and links.

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
| **Figure** | `<figure class="figure"><div class="figure-body …">…</div><figcaption>…</figcaption></figure>`: a frame for any illustration below; gets an **Expand** button | same, minus the button |
| **Stepper** | `<div class="figure stepper">`: a `<div class="scene …">` holding any components, then `<ol class="steps">` with one `<li data-show="ids" data-hl="ids" data-move="ids" data-dim="ids"><strong>Title</strong> text</li>` per step. Elements with class `el` are hidden until a step lists them in `data-show`; `data-hl` highlights, `data-move` animates an arrow, link or arc, `data-dim` fades. Ids must be unique on the page | full scene plus the steps as a numbered list |
| **Compare** | `<div class="compare">` with two or more `<div class="compare-pane" data-label="Before">…</div>`. JS turns them into a toggle | panes side by side |
| **Takeaways** | `<ol class="takeaways"><li>…</li></ol>`, rendered as numbered cards | same |
| **Table / code** | plain `<table>`, `<pre><code>` | same |

### Illustration components

All take the colour classes `c-blue`, `c-orange`, `c-teal`, `c-purple`, `c-red`, `c-green` and the highlight class `hl`.

| Component | Markup |
|---|---|
| **Node** | `<div class="node c-teal">Label<small>second line</small></div>`: the basic box |
| **Flow** | `<div class="flow">` with nodes and `<div class="arrow" data-label="request"></div>` between them; `flow vertical` for top to bottom; `arrow moving` animates a dot along it |
| **Graph** | `<div class="graph" style="--h:300px">` with nodes placed by their centre in percent, `<div class="node" id="g-plan" style="--x:15;--y:50">Plan</div>`, and links `<i class="link" data-from="g-plan" data-to="g-act" data-label="next"></i>`. Arrows are drawn at load time, clipped to the boxes; `data-curve="40"` (or negative) bends a link, for loops and return paths; `link moving` animates it. Give links an `id` to target them from a stepper |
| **Stack** | `<div class="stack">` with `<div class="layer c-blue"><b>Layer</b><span>what it does</span></div>`, top layer first |
| **Lanes** | `<div class="lanes">` with `<div class="lane c-orange"><b>Actor</b><div class="items"><span>step</span><span>step</span></div></div>` |
| **Timeline** | `<ol class="timeline"><li><b>2019</b> what happened</li>…</ol>` |
| **Bars** | `<div class="bars">` with `<div class="bar c-red" style="--v:80%"><b>Label</b><div class="track"><i></i><span>80%</span></div></div>` |
| **Tree** | nested `<ul class="tree"><li><span class="node">Root</span><ul><li>…</li></ul></li></ul>` |
| **Circle** | `<div class="circle ring" style="--size:300px">` (or `circle cycle` for a dashed loop). Place items by angle (0° = top, clockwise): `<span class="on-circle" style="--a:90deg"><b class="badge c-blue">B</b></span>`; small markers are `<i class="pin c-teal"></i>` (`pin ring-out` circles one, `pin hl` highlights it); labels outside the ring add `--out:30px`. `<div class="arc" style="--from:120deg;--to:200deg"></div>` highlights a span; `style="--seg:conic-gradient(var(--blue) 0 90deg, var(--orange) 90deg 360deg)"` colours the ring in segments; `<div class="center">` puts text in the middle; wrap markers in `<div class="group el" id="…">` to show a whole set in one stepper step |
| **Row** | `<div class="row">` with `<div>…illustration…<b>Title</b><span class="caption">note</span></div>` per item: illustrations side by side |
| **Cards** | see above; also good as a big-picture "parts" illustration |

### Combined notes and navigation

| Component | Markup | Without JS |
|---|---|---|
| **Source tag** (combined notes) | `<span class="vtag v2">V2</span>` after a heading or point that comes mainly from one video; `v1`…`v5` have distinct colours | same |
| **Coverage grid** (combined notes) | `<table class="coverage">` with ideas as rows and `V1`… as columns; cells `<td class="full"></td>` (in depth), `<td class="part"></td>` (briefly) or `<td class="none"></td>` (not covered), drawn as filled, half-filled and dash markers. Add the legend under it: `<p class="cov-legend"><span><span class="dot full"></span> in depth</span><span><span class="dot part"></span> briefly</span><span>– not covered</span></p>` | same |
| **Sources list** (combined notes) | `<ul class="sources-list"><li><span class="vtag v1">V1</span> <strong>Title</strong> · channel · date · duration · transcript kind</li>…</ul>` | same |
| **Mini contents** | automatic: a panel with 3+ `<h3 id="…">` gets clickable chips under its `<h2>` | `h3`s still visible |

Which component to use for which idea, and how to make it good, is in `visuals.md`.

## Rules for Obsidian's HTML Viewer

The user opens these pages in Obsidian with the **HTML Viewer** plugin (Scripts ON). It renders the page in a sandboxed frame:
- **Inline event handlers (`onclick="…"`, `onload=…`) and `javascript:` URLs are always stripped.** Attach behaviour in a `<script>` with `addEventListener`, as the template's engine does. The checker flags these.
- **No navigation out of the page.** Links to other files, `obsidian://` links and new windows don't work. Keep navigation in-page: tabs, `#anchors`, and the home/top buttons. Put links to other notes and the transcript in the markdown card. A video link in the Source tab is fine to show, but don't rely on it opening.
- **`#anchor` links work**, so tabs deep-link (`Consistent_Hashing.html#walkthrough`).
- **`localStorage` resets on every refresh**, so don't store anything important in it.
- **Self-contained**: no CDN scripts, web fonts or images from the internet, so the page also works offline.
- **Without JavaScript** (Scripts OFF) the template shows every panel in order and the tab bar works as a table of contents. Keep content readable that way: don't hide essential text behind interactions.

## Size

Aim for a page that loads instantly: typically 30–80 KB, most of it the template's CSS and script. Avoid embedding large images as base64. On claude.ai the page is uploaded through the conversation, so very large pages cost more of the user's usage.

## Check it

`python3 <skill_dir>/scripts/check_note.py "<note.html>" --card "<card.md>"` checks:
- the page loads without JavaScript errors;
- every tab opens its panel;
- every in-page link has a target;
- no inline handlers, `javascript:` URLs, external scripts or leftover `data-example` blocks remain;
- graph links and stepper steps point at ids that exist, and graph arrows are drawn;
- illustrations use the components (hand-drawn `<svg>` is a warning);
- the page is readable without JavaScript;
- the card's frontmatter is complete.
