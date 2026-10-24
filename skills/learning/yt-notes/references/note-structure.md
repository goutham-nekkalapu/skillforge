# Note structure (deep notes, the default)

The reader is the user weeks later, revising a topic or preparing for interviews, possibly in Obsidian on a phone. Optimise for **re-reading and understanding**, not for proving the video was watched. A good test: could someone who never saw the video explain the topic correctly after reading this note?

Sections marked *(if relevant)* are left out when the video has nothing for them. Never pad a section to fill the template.

````markdown
---
title: "Consistent Hashing"
aliases: ["Consistent Hashing Explained in 10 Minutes"]   # the original video title
summary: "How consistent hashing spreads keys over a ring so adding or removing servers only moves ~1/N of keys."
topic: "System Design"
tags: [system-design, distributed-systems, hashing, load-balancing]
status: new                       # new | reviewing | mastered (the user updates this)
depth: deep
video_url: "https://www.youtube.com/watch?v=..."
video_id: "..."
channel: "..."
published: "2023-04-01"
duration: "12:34"
transcript: "[[transcript - VIDEO_ID|Full transcript]]"
transcript_method: "ytdlp (manual)"
created: "2026-10-24"
---

# Consistent Hashing

> [!abstract] TL;DR
> - 3–5 bullets a reader could recite. Each is a complete idea, not a teaser.

## Why this matters
The problem the topic solves, and what goes wrong without it. 2–4 sentences. Start from the pain ("with `hash(key) % N`, adding one server remaps almost every key…").

## Big picture
One overview diagram (a flowchart or mindmap) showing the main parts and how they relate, plus 2–3 sentences walking through it.

## Core concepts
One `###` per concept, in an order that builds understanding:
- **What it is**: a precise one-line definition.
- **Intuition**: an analogy or plain-words explanation.
- **Details**: how it actually works; include the numbers, formulas and constraints from the video.
- A diagram or small example where it helps.

## How it works (step by step)                  *(if there's a process, algorithm or flow)*
A numbered walkthrough, with a sequence or flow diagram. Say what changes at each step and why.

## Worked examples
Concrete scenarios with real values: input, the steps, the result. Use code blocks for code, and mark code you reconstructed from narration (rather than copied from the screen) with a comment.

## Comparisons and trade-offs                  *(if the video compares approaches)*
A table: options as rows, criteria as columns. Follow it with "when to pick which".

## Pitfalls and misconceptions                  *(if relevant)*
Mistakes, edge cases and "gotchas" the video warns about, or that follow clearly from it.

## Key takeaways and mental models
The handful of ideas worth remembering, phrased as rules of thumb.

## Glossary                                      *(if 4+ new terms)*
| Term | Meaning |

## Related
- [[Wikilinks]] to concepts that deserve their own notes (prefer names of existing notes; the list of existing topics comes from `notes_paths.py where`)
- Links from the video description that are worth keeping, with a few words on what each is

## Source
- Video: [title](url) · Channel · published date · duration
- [[transcript - VIDEO_ID|Full transcript]] · transcript source and kind (warn if auto or AI-generated)
````

## Writing rules

- **Faithful first.** The note reflects what the video teaches. When you add something the video didn't say (a missing definition, a correction, a clearer example, important context), put it in a callout so the user can tell the difference:
  `> [!info] Added context` (extra background) · `> [!warning] Correction` (the video is wrong or outdated). Keep additions purposeful and short.
- **Fix transcript errors.** Auto and AI transcripts mishear jargon ("cash" for "cache", "Kafka" spelled oddly). Use the correct term. If you genuinely can't tell what was said, note it once rather than guessing silently.
- **No timestamps** in the note body, and no interview questions or flashcards. The user builds those across many notes.
- **Explain, don't summarise.** "The speaker talks about sharding" is useless; explain sharding as the speaker did.
- **Intuition, then precision.** Give an analogy or picture first, then the exact definition, numbers and conditions.
- **Concrete beats abstract.** Every core concept gets an example with actual values, code or a scenario.
- **Use the structure of the video, not its order.** Chapters help to understand the flow, but organise the note by concept so it works as a reference.
- **Scannable.** Short paragraphs, bold the key term where it's defined, tables for comparisons, callouts for warnings and tips. Keep heading levels consistent (`##` sections, `###` concepts).
- **Obsidian-friendly.** Wikilinks `[[Like This]]`, callouts `> [!tip]`, tags in frontmatter as lowercase-hyphenated words. Write `==highlight==` sparingly.
- **Length follows content.** A dense 40-minute lecture may need 2,500+ words. A 6-minute explainer might need 700. Cover everything substantive; cut filler such as sponsor reads, "like and subscribe" and long anecdotes.

## Quick mode

Only when the user asks for a summary or quick notes: frontmatter (`depth: quick`), TL;DR, Big picture diagram, Core concepts (definition + one line each), Key takeaways, Source.

## Videos that aren't concept explainers

Adapt the section names to the content while keeping the same spirit:
- **Tutorials / coding walkthroughs**: Goal → Prerequisites → Steps (with code) → Final result → Common errors.
- **Talks / interviews / podcasts**: Thesis → Key arguments (with the evidence given) → Notable claims → Where speakers disagree → Takeaways. Attribute opinions to the speaker.
- **Case studies / postmortems**: Context → Timeline (timeline diagram) → Root cause → Fixes → Lessons.
