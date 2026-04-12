# Lecture Distiller

Distills video transcripts and course screenshots into structured, scannable study notes optimized for quick revision.

## What It Does

Takes raw lecture transcripts (the kind full of "um", repeated explanations, and tangents) and produces clean, hierarchical notes you can review in minutes instead of re-watching hours of video. Screenshots are integrated inline with captions, and diagrams are generated where they help.

## When to Use

- You have video transcripts (v1.md, v2.md, etc.) from an online course
- You want concise study notes from lecture recordings
- You need screenshots integrated into structured notes
- You want visual aids and diagrams generated from course content
- You're preparing revision material from educational content

Works well with deeplearning.ai, Coursera, Udemy, and similar platforms.

## Platform

Works on **claude.ai**, **Claude Code**, and **Cursor**.

## What You Get

- Structured markdown notes at 20-30% of the original transcript length
- Screenshots placed in context with numbered figure captions
- Generated mermaid diagrams, comparison tables, and formula references
- Quick-reference sections and self-test questions
- Cross-referenced concepts with anchor links

## Included Files

| File | Purpose |
|------|---------|
| `SKILL.md` | The skill definition (what the agent reads) |
| `references/note-templates.md` | Templates for technical, theoretical, conceptual, and hands-on courses |
| `references/visual-patterns.md` | Diagram templates — mermaid, ASCII, tables, LaTeX |
| `scripts/process_transcripts.py` | Optional Python helper for transcript pre-processing |

## Install

```bash
npx skillforge install learning/lecture-distiller

# Or via install script
./install.sh learning/lecture-distiller
```
