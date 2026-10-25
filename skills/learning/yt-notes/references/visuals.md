# Visuals

Visuals carry the note. Each one should answer one question ("how does a request flow?", "what are the parts?", "what changes when a server joins?") faster than a paragraph could, and sit next to the text it replaces.

**Build illustrations from HTML elements, not drawings.** The template defines a library of components (flow, stack, lanes, timeline, circle, bars, tree, graph, cards, compare, stepper). CSS does the layout, colours and animation, so a note only writes short, meaningful markup such as `<div class="node">Server</div>`. This keeps notes cheap to generate and easy to fix, and they look consistent from note to note.

- **Don't hand-draw SVG.** Coordinates, paths and markers are verbose (an SVG figure is often 5–10× the markup of the same idea in components) and easy to get subtly wrong. The checker warns about it. Tiny inline icons are fine.
- **Arrows between free-placed boxes**: use the **graph** component. Its arrows are drawn at load time from the nodes and links you list, so you never write a path.
- **No Mermaid** unless the user asks for it: auto-laid-out diagrams come out cramped and hard to read as a whole.

## Choosing a visual

| Content | Component |
|---|---|
| The parts of a topic and what each does | **cards** (one per part, a colour each) |
| A process, pipeline or request path | **flow** (`vertical` for long chains); a **stepper** if it unfolds in stages |
| A loop, cycle or network of things (agents, services, states) | **graph** (nodes placed by percent, arrows drawn for you; `data-curve` for loops) |
| Layers (architecture, OSI, memory hierarchy, priorities) | **stack** |
| Who does what, or work split between actors | **lanes** |
| Events or phases over time | **timeline** |
| Rings, cycles, round-robin, anything circular | **circle** (`ring` or `cycle`, items placed by angle, `arc` to highlight a span, `--seg` for coloured segments) |
| Numbers, proportions, benchmarks | **bars** (values from `--v`), or a table |
| Hierarchies, decision trees, file layouts | **tree** |
| Before vs after, option A vs B | **compare** toggle (put any components inside the panes), or **row** for side by side |
| Components talking over time, data moving | flow with `arrow moving`, graph links with `moving`, or a stepper using `data-move` |
| Code | `<pre><code>` followed by numbered explanations |

A typical note has a big-picture visual on the Overview tab and one visual for most key ideas. Skip a visual that just restates a list.

## Making them good

- **One question per figure.** Wrap it in `<figure class="figure">` with a `<figcaption>` saying how to read it (it gets an **Expand** button automatically).
- **Short labels** (2–4 words) in nodes; put a second line in `<small>`, and the detail in the caption or text.
- **Emphasis**: highlight the one or two things the figure is about with `hl` (any component) or a colour class (`c-blue`, `c-orange`, `c-teal`, `c-purple`, `c-red`, `c-green`). Leave everything else neutral. Colours adapt to light and dark themes.
- **Accuracy**: draw what the video describes, using its own example values. When positions matter (keys on a ring, values in bars), compute them rather than eyeballing.
- **Space**: if a flow has more than ~5 nodes, go vertical or split it. Give graphs enough height (`style="--h:320px"`) so nodes don't touch.

## Animation, from simplest to richest

1. `class="arrow moving"` in a flow, or `class="link moving"` in a graph: a dot or dashes travelling along the connector.
2. **Stepper**: a scene of components where elements appear (`data-show`), highlight (`data-hl`), animate (`data-move`) or fade (`data-dim`) step by step, with Prev / Play / Next controls. See `html-notes.md`.
3. Custom script: only when the idea really needs it (e.g. a slider that changes a parameter). Attach events with `addEventListener`; see the HTML Viewer rules in `html-notes.md`.

The template respects `prefers-reduced-motion`.

## In markdown notes (HTML snippets)

The template's CSS isn't available in a markdown note, but Obsidian renders HTML blocks with inline `style` attributes, so use small styled snippets. Use Obsidian's theme variables for colours so they follow light and dark themes: `var(--background-modifier-border)` for lines, `var(--background-secondary)` for fills, `var(--text-muted)` for secondary text, `var(--interactive-accent)` for highlights.

Rules:
- **No blank lines inside a snippet.** A blank line ends Obsidian's HTML block and the rest shows as raw text. The checker catches unbalanced snippets.
- **No markdown inside a snippet** (it isn't rendered there): use `<b>`, `<code>`, `<br>`.
- **No scripts, `<style>` or event handlers**; Obsidian strips them.
- Keep each snippet to one idea, with a one-line italic caption under it.

Flow:

```html
<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:12px 0">
<div style="border:1.5px solid var(--background-modifier-border);border-radius:10px;padding:8px 14px"><b>Client</b></div>
<span style="color:var(--text-muted)">── request ──▶</span>
<div style="border:1.5px solid var(--interactive-accent);border-radius:10px;padding:8px 14px"><b>Server</b></div>
<span style="color:var(--text-muted)">── query ──▶</span>
<div style="border:1.5px solid var(--background-modifier-border);border-radius:10px;padding:8px 14px"><b>Database</b></div>
</div>
```
*The server sits between the client and the database.*

Stack (layers) and bars:

```html
<div style="display:grid;gap:6px;margin:12px 0">
<div style="border-left:6px solid var(--interactive-accent);background:var(--background-secondary);border-radius:8px;padding:8px 12px"><b>Application</b> · business logic</div>
<div style="border-left:6px solid var(--text-muted);background:var(--background-secondary);border-radius:8px;padding:8px 12px"><b>Cache</b> · hot keys in memory</div>
<div style="border-left:6px solid var(--text-muted);background:var(--background-secondary);border-radius:8px;padding:8px 12px"><b>Database</b> · source of truth</div>
</div>
<div style="display:grid;grid-template-columns:140px 1fr;gap:6px 12px;align-items:center;margin:12px 0">
<b>mod N</b><div style="background:var(--background-secondary);border-radius:6px"><div style="width:80%;background:var(--interactive-accent);color:var(--text-on-accent);border-radius:6px;padding:4px 8px">~80% move</div></div>
<b>Hash ring</b><div style="background:var(--background-secondary);border-radius:6px"><div style="width:20%;background:var(--interactive-accent);color:var(--text-on-accent);border-radius:6px;padding:4px 8px">~20%</div></div>
</div>
```

A `<details><summary>…</summary>…</details>` block works as a simple toggle. For anything richer than these (graphs, rings, animation), suggest the HTML format.

## Other visual patterns

- **Comparison tables** with a final "Choose when…" row.
- **Annotated code**: a short block followed by numbered explanations.
- **Callouts** for the one insight, warning or tip that matters.
- **Formulas** in LaTeX (`$$ … $$` in markdown). In HTML, write simple formulas with `<code>` or plain text.
