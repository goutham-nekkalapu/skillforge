# What goes into a blog note

The reader is the user weeks later, revising a topic or preparing for interviews. They want **the important ideas, clearly explained and easy to picture**, not the post rewritten. Test: could someone who never read the post explain the concept correctly after reading this note, without wading through anything they didn't need?

## Distil first

Outline every idea, claim, example, number and code block in the post (privately). Then sort:

- **Keep**: core concepts, the mechanisms that explain *how* or *why*, the one or two examples that make an idea click, trade-offs and pitfalls the author stresses, code that carries the idea, and the conclusions.
- **Compress**: details that matter but don't need a paragraph. Make them a bullet, a table row or a label on a figure.
- **Leave out**: repetition, recaps ("as we saw above"), intros that restate the title, "we will cover the following" lists, setup and boilerplate code, marketing, and the boilerplate sections below.

Ask of every item: *"Would the user miss this in three months?"* Length comes from how much important material there is, not from covering everything.

**Restructure, don't paraphrase.** A blog already has the author's headings, and the easy failure is a note that walks the post section by section in slightly shorter words. Order the note to build understanding: the problem, the core idea, how it works, where it breaks, what to do. Merge sections that explain one idea; split a section that hides two.

**Skip boilerplate sections by default:** FAQs, newsletter or subscribe boxes, author bio, "related posts", comments, sponsor or ad blocks, the table of contents. The user can name more ("ignore the benchmarks section") or ask to keep one. An FAQ answer that holds a genuinely important point can be folded into the relevant idea.

**Prefer a picture to a paragraph.** For each kept idea, decide whether a visual explains it faster (`../yt-notes/references/visuals.md`). Static visuals go inline in the markdown as small HTML snippets; a concept that moves gets an explainer (`explainers.md`).

## Sections

`##` sections with `###` subsections. Leave out any section the post has nothing for.

| Section | What it holds |
|---|---|
| **Overview** | `### TL;DR` (3–5 bullets a reader could recite), `### Why it matters` (the pain it solves, 1–3 sentences), and a big-picture visual of the main parts |
| **Key ideas** | One `###` per idea (usually 3–7), in an order that builds understanding: a precise one-line statement, the intuition, then a visual, a concrete example with real values, or the key code |
| **Walkthrough** | *(only if there's a process or flow)* numbered steps with a diagram, or a link to an explainer |
| **Compare** | *(only if the post compares options)* a table, then "when to pick which" |
| **Takeaways** | The rules of thumb worth remembering, with the important pitfalls folded in |
| **Critique** | *(only with `--critique`)* see below |
| **Source** | Title, author, site, published/updated, URL, `source_wikilink`, original image URLs worth keeping |

Domain-appropriate names are fine ("Architecture", "Code", "Benchmarks").

## Modes

| Mode | What changes |
|---|---|
| `quick` | Overview (TL;DR + why it matters), one inline visual, `## Worth a deep read?` with a yes/no and the reason, and Source. No explainers. It's a real note, so it shows in the index and can later be regenerated as `distilled` or `deep` in place |
| `distilled` (default) | Everything above |
| `deep` | Same sections, but keep the full reasoning chain, edge cases, numbers and limits, and every code block that matters, verbatim with its language tag. For engineering posts the user will work from. Still no recaps or filler |

**Critique** (any mode, `--critique`): a `## Critique` section with `### Claims vs. evidence` (which claims are shown, which are asserted), `### Assumptions` (what has to be true for the advice to hold), `### What's missing` (alternatives, failure modes, costs the post skips), and `### Still current?` (judged against the publish date). Be fair and specific; attribute views to the author.

## Writing rules

- **Faithful.** The note reflects what the post teaches. Mark anything you add (a missing definition, a correction, context) as `> [!info] Added context` or `> [!warning] Correction`, short and purposeful.
- **Attribute opinions.** "The author argues…" for opinions and recommendations; plain statements for facts the post establishes.
- **Code**: keep code that carries the idea, verbatim, with the language tag. Drop imports, setup and boilerplate unless they're the point. Never "fix" code silently; use a Correction callout.
- **Staleness**: show `published` (and `updated`) in the Source section. If the post is old for a fast-moving field (LLMs, frontend frameworks, cloud pricing), add `> [!warning] May be outdated` naming what to double-check.
- **Explain, don't narrate**: "a cache hit skips recomputing the prefix", not "the author then explains cache hits".
- **Intuition, then precision.** Short paragraphs, the key term bold where it's defined, tables for comparisons, callouts for warnings and tips.
- **No timestamps, interview questions or flashcards.** The user builds those across many notes.
- **Links between notes**: `[[File_Name|Readable Name]]` (files use underscores). Link related notes in a `Related:` line under the TL;DR, including the other notes from the same batch.

## Frontmatter

```yaml
---
title: "Prompt Caching"
aliases: ["Prompt Caching", "How does Prompt Caching work?"]
summary: "Reusing the processed prefix of a prompt so repeated system prompts, tools and documents aren't recomputed."
topic: "LLM Engineering"
tags: [llm, caching, inference]
status: new                      # new | reviewing | mastered (the user updates this)
format: markdown                 # or html
mode: distilled                  # quick | distilled | deep
critique: false
source_type: blog
source_url: "https://outcomeschool.com/blog/how-does-prompt-caching-work"
author: "Amit Shekhar"
site: "outcomeschool.com"
published: "2026-06-09"
source: "[[article_d5272c24e9|Saved article]]"
explainers: ["Prompt_Caching__Cache_Lookup.html"]    # [] when none
created: "2026-11-11"
---
```

Use the values from `prepare` (`title`, `posts[0]`, `today`). `aliases` holds the readable title, then the post's own title. Lists are written inline.

## Combined notes (several posts on one concept)

Same sections and rules, plus:

| Part | What changes |
|---|---|
| **Overview** | The TL;DR covers the concept as a whole. Optionally one line on how the posts differ in angle |
| **Key ideas** | Shared ideas explained once (best explanation wins, complementary details merged); ideas from one post tagged `(P2)` after the heading or point |
| **Coverage** | A table of the main ideas against the posts: `●` in depth, `◐` briefly, `–` not covered |
| **Posts differ** | Only if they disagree: `> [!question] Posts differ` per disagreement, each view with its tag, and which is better supported if the posts make that clear |
| **Sources** | Every post with its tag, title, author, site, date and `source_wikilink` |

Tags follow the order the posts were given. Frontmatter uses inline lists: `source_urls: [...]`, `authors: [...]`, `sites: [...]`, and `sources: ["[[article_…|Saved article]]", ...]` instead of the single keys. If a post in a series failed to fetch, say so in a `> [!warning] Missing part` callout.

## HTML format

With `--format html` the note is yt-notes' tabbed page plus a markdown card; follow `../yt-notes/references/html-notes.md` and `../yt-notes/references/note-structure.md` (card section). The card gets the frontmatter above with `format: html`, the page link, the TL;DR, Related and Source.
