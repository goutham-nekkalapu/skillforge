# What goes into a note

The reader is the user weeks later, revising a topic or preparing for interviews. They want the **important ideas, clearly explained and easy to picture**, not a record of everything the video said. A good test: could someone who never saw the video explain the topic correctly after reading this note, without wading through anything they didn't need?

## Distil first: choose what goes in

Before writing, list every idea, claim, example and number in the video (a rough outline, kept to yourself). Then sort it:

- **Keep**: the core concepts, the mechanisms that explain *how* or *why*, the one or two examples that make an idea click, the trade-offs and pitfalls the speaker stresses, and the conclusions.
- **Compress**: supporting details that matter but don't need a paragraph. Make them a bullet, a table row or a label on a figure.
- **Leave out**: repetition, recaps, anecdotes and jokes, sponsor reads, side tangents, minor numbers and caveats said only in passing, and "as I said earlier" material. When a second example teaches nothing new, drop it.

Ask of every item: *"Would the user miss this in three months?"* If not, it goes. There's no word limit. A dense lecture can still produce a long note, but its length should come from important ideas, not from covering everything.

Then **prefer a picture to a paragraph**. For each kept idea, decide whether a visual explains it faster (see `visuals.md`). If it does, make the visual the explanation and keep the text short around it.

## The sections

Both formats use the same building blocks. In HTML each one is a tab (3–7 tabs). In markdown each one is a `##` section. Leave out any block the video has nothing for, and add a tab only when it earns its place.

| Block | What it holds |
|---|---|
| **Overview** | TL;DR (3–5 bullets a reader could recite), why the topic matters (the pain it solves, in 1–3 sentences), and a big-picture visual of the main parts and how they relate |
| **Key ideas** | 3–7 ideas in an order that builds understanding. Each gets a precise one-line statement, the intuition (analogy or plain words), and a visual or one concrete example with real values |
| **Walkthrough** | *(only if there's a process, algorithm or flow)* a step-through animation, or a numbered sequence with a diagram |
| **Compare** | *(only if the video compares options)* a table or before/after toggle, then "when to pick which" |
| **Takeaways** | the handful of rules of thumb worth remembering, with the important pitfalls folded in |
| **Source** | video, channel, date, duration, transcript kind (warn if auto or AI-generated), and description links worth keeping |

Use domain-appropriate tab names when they read better ("Architecture", "Code", "Benchmarks", "FAQ"); the list above is a default, not a rule.

## Writing rules

- **Faithful.** The note reflects what the video teaches. Mark anything you add (a missing definition, a correction, important context) so the user can tell the difference: an "Added context" or "Correction" callout in HTML, `> [!info] Added context` or `> [!warning] Correction` in markdown. Keep additions short and purposeful.
- **Fix transcript errors.** Auto and AI transcripts mishear jargon ("cash" for "cache"). Use the correct term; if you truly can't tell what was said, say so once.
- **Explain, don't narrate.** Write "sharding splits a table across machines by key", not "the speaker talks about sharding".
- **Intuition, then precision.** An analogy or picture first, then the exact definition, numbers or conditions.
- **Short paragraphs, scannable.** Bold the key term where it's defined. Tables for comparisons, callouts for warnings and tips.
- **No timestamps, interview questions or flashcards.** The user builds those across many notes.

## Combined notes (several videos)

Same blocks and rules, with these additions (workflow in SKILL.md, "Combining several videos"):

| Block | What changes |
|---|---|
| **Overview** | The TL;DR covers the topic as a whole, not video by video. Optionally one line on how the videos differ in angle ("V1 is the theory, V2 a production case study") |
| **Key ideas** | Shared ideas explained once (best explanation wins), distinct ideas tagged with their video (`V2`) |
| **Coverage** | A grid of the main ideas against the videos: covered in depth / briefly / not at all |
| **Videos differ** | Only if they disagree: a callout per disagreement, showing each view and which is better supported |
| **Sources** | Every video with its tag, title, channel, date, duration and transcript kind |

Tags `V1`… follow the order the videos were given. A combined note's title names the topic, not a video.

The combined card uses lists, written inline:

````markdown
---
title: "Consistent Hashing"
aliases: ["Consistent Hashing"]
summary: "..."
topic: "System Design"
tags: [system-design, hashing]
status: new
format: html
video_ids: ["abc123XYZ00", "def456UVW11"]
video_urls: ["https://www.youtube.com/watch?v=abc123XYZ00", "https://www.youtube.com/watch?v=def456UVW11"]
channels: ["Channel One", "Channel Two"]
created: "2026-10-25"
---

# Consistent Hashing

**[[Consistent_Hashing.html|Open the full note]]** · combines 2 videos

- TL;DR bullets…

Sources:
- V1: [Video one title](https://www.youtube.com/watch?v=abc123XYZ00) · Channel One · [[transcript_abc123XYZ00|Full transcript]]
- V2: [Video two title](https://www.youtube.com/watch?v=def456UVW11) · Channel Two · [[transcript_def456UVW11|Full transcript]]

Also has its own note: [[Ring_Hashing_Deep_Dive|Ring Hashing Deep Dive]] (V2)
````

## Videos that aren't concept explainers

Keep the same spirit, with tabs that fit the content:
- **Tutorials / coding walkthroughs**: Goal → Steps (with code) → Result → Common errors.
- **Talks / interviews / podcasts**: Thesis → Key arguments (with the evidence given) → Notable claims → Where speakers disagree → Takeaways. Attribute opinions to the speaker.
- **Case studies / postmortems**: Context → Timeline → Root cause → Fixes → Lessons.

## The markdown card (HTML format)

In HTML format, write a short markdown card next to the page, with the same name and `.md`. It is what Obsidian search, tags, the graph and the topic index see, and it carries the links that can't work inside the HTML page:

````markdown
---
title: "Consistent Hashing"
aliases: ["Consistent Hashing", "Consistent Hashing Explained in 10 Minutes"]   # spaced title, then the video title
summary: "How consistent hashing spreads keys over a ring so adding or removing servers only moves ~1/N of keys."
topic: "System Design"
tags: [system-design, distributed-systems, hashing]
status: new                       # new | reviewing | mastered (the user updates this)
format: html
video_url: "https://www.youtube.com/watch?v=..."
video_id: "..."
channel: "..."
published: "2023-04-01"
duration: "12:34"
transcript: "[[transcript_VIDEO_ID|Full transcript]]"
transcript_method: "ytdlp (manual)"
created: "2026-10-25"
---

# Consistent Hashing

**[[Consistent_Hashing.html|Open the full note]]**

- TL;DR bullet 1
- TL;DR bullet 2
- TL;DR bullet 3

Related: [[Load_Balancing|Load Balancing]] · [[Sharding]]
Source: [video](https://www.youtube.com/watch?v=...) · [[transcript_VIDEO_ID|Full transcript]]
````

If `prepare` returned a `page_embed_block`, add it under the link to show the page inline (it needs the Obsidian **HTML Embed** plugin). Leave it out otherwise.

## Markdown format

In markdown format the note itself is the `.md` file: the same frontmatter (with `format: markdown`), then `##` sections for the blocks above, with visuals as inline SVG (see `visuals.md`).

**Links between notes**: always `[[File_Name|Readable Name]]`, e.g. `[[Cache_Stampede|Cache Stampede]]`. Note files use underscores, so a plain `[[Cache Stampede]]` won't find `Cache_Stampede.md`. Link targets are the card or markdown note, never the `.html` page.
