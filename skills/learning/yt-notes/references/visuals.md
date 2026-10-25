# Visuals

Visuals carry the note. Each one should answer one question ("how does a request flow?", "what are the parts?", "what changes when a server joins?") faster than a paragraph could, and sit next to the text it replaces.

**Draw SVG by hand, not Mermaid.** Auto-laid-out Mermaid diagrams come out cramped and hard to read as a whole. Hand-placed SVG lets you control layout, spacing, emphasis and animation. Use Mermaid only if the user explicitly asks for it.

## Choosing a visual

| Content | Visual |
|---|---|
| The parts of a topic and how they relate | Cards grid (HTML) or a hub-and-spoke / layered SVG |
| A process, pipeline or algorithm | Left-to-right flow SVG; a **stepper** if it unfolds in stages |
| Components talking over time (requests, protocols) | Swim-lane / sequence SVG, or a stepper with moving arrows |
| States and transitions | State SVG (rounded boxes, labelled arrows) |
| Architecture (services, stores, queues) | Layered SVG with grouped zones |
| Before vs after, option A vs B | **Compare** toggle (HTML) or side-by-side SVG |
| A decision ("which DB?") | Decision-tree SVG with diamond questions |
| Numbers, proportions, trends | Simple SVG bar or line chart with labelled values, or a table |
| Data structures (arrays, rings, trees, memory) | Precise SVG drawing; animate changes with a stepper |
| Something that moves | CSS-animated flow (`.flow`) or SMIL `animateMotion` dots |

A typical note has a big-picture visual on the Overview tab and one visual for most key ideas. Skip a visual that just restates a list.

## Drawing good SVG

- **Canvas**: use `viewBox` (e.g. `0 0 800 300`) with `width:100%`. Plan positions on a grid (multiples of 20). Leave 20px margins.
- **Readable text**: labels 14–16px, secondary text 12–13px, never smaller. Keep labels short (2–4 words) and put the detail in the caption or text.
- **Space**: boxes at least 140×56, and at least 40px gaps between boxes. If it feels cramped, widen the `viewBox` or split it into two figures.
- **Emphasis**: highlight the one or two things the figure is about. Leave everything else neutral.
- **Arrows**: define one `<marker>` per SVG with a unique id (`arr-1`, `arr-2`…). Ids must be unique across the whole page.
- **Captions**: one sentence on how to read the figure.
- **Accuracy**: draw what the video describes, using its own example values where it gives them.

### In HTML notes (the template's classes)

| Class | Use |
|---|---|
| `box`, `box soft`, `box hl` (or `<g class="hl">`) | Rectangles: neutral, subtle fill, highlighted |
| `lbl`, `sub` | Centred label and secondary text |
| `edge`, `edge hl` | Connector lines and highlighted connectors |
| `flow` | Animated dashes along a path (data moving) |
| `c-blue` … `c-green` + `fill-c` / `stroke-c` | Accent colours that adapt to light and dark themes |

Wrap each figure in `<figure class="figure">…<figcaption>`. It gets an **Expand** button automatically for a full-screen view.

**Animation options**, from simplest to richest:
1. `class="edge flow"`: marching dashes. Shows direction or data moving.
2. SMIL, which needs no JavaScript: a dot travelling along a path:
   ```html
   <circle r="6" class="fill-c c-teal"><animateMotion dur="2.5s" repeatCount="indefinite" path="M200,100 L600,100"/></circle>
   ```
3. **Stepper**: a scene where elements appear or highlight step by step, with Prev / Play / Next controls. See `html-notes.md`.
4. Custom script: only when the idea really needs it (e.g. a slider that changes a parameter and redraws). Attach events with `addEventListener`; see the HTML Viewer rules in `html-notes.md`.

Respect `prefers-reduced-motion`; the template's CSS already does this for `.flow`.

### In markdown notes (inline SVG)

Paste the `<svg>…</svg>` straight into the markdown. Obsidian renders inline SVG in reading view.

- **No blank lines inside the SVG.** A blank line ends the HTML block and the rest shows as raw text.
- **No CSS classes, `<style>` or scripts.** Obsidian doesn't load the template's styles and strips scripts. Put attributes on each element: `fill`, `stroke`, `stroke-width`, `font-size`, `text-anchor`.
- **Theme-safe colours**: use `currentColor` for text and neutral lines so they follow Obsidian's light and dark themes. Use mid-tone accents with partial opacity for fills (`fill="#4f7cff" fill-opacity="0.15"`, `stroke="#4f7cff"`).
- Keep each SVG under ~12 elements per idea, and add a one-line italic caption below.
- SMIL `animateMotion` usually still runs in Obsidian, so simple motion is possible.

Example:

```html
<svg viewBox="0 0 640 140" width="100%" role="img" aria-label="Request flows from client to server to database">
  <defs><marker id="m-arr-1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
  <rect x="20" y="40" width="160" height="60" rx="10" fill="none" stroke="currentColor" stroke-opacity="0.5"/>
  <text x="100" y="75" text-anchor="middle" font-size="15" fill="currentColor">Client</text>
  <rect x="240" y="40" width="160" height="60" rx="10" fill="#4f7cff" fill-opacity="0.15" stroke="#4f7cff" stroke-width="2"/>
  <text x="320" y="75" text-anchor="middle" font-size="15" fill="currentColor">Server</text>
  <rect x="460" y="40" width="160" height="60" rx="10" fill="none" stroke="currentColor" stroke-opacity="0.5"/>
  <text x="540" y="75" text-anchor="middle" font-size="15" fill="currentColor">Database</text>
  <path d="M180,70 L236,70" stroke="currentColor" stroke-width="2" marker-end="url(#m-arr-1)"/>
  <path d="M400,70 L456,70" stroke="currentColor" stroke-width="2" marker-end="url(#m-arr-1)"/>
</svg>
```
*The server sits between the client and the database.*

The user's Obsidian setup also renders HTML snippets in markdown, so small HTML blocks (a styled table, a details/summary toggle) are fine too. Keep them script-free.

## Other visual patterns

- **Comparison tables** with a final "Choose when…" row.
- **Annotated code**: a short block followed by numbered explanations.
- **Callouts** for the one insight, warning or tip that matters.
- **Formulas** in LaTeX (`$$ … $$` in markdown). In HTML, write simple formulas with `<code>` or plain text.
