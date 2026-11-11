---
title: "LLM Engineering - index"
type: yt-notes-index
---

# LLM Engineering

2 note(s). This page is rebuilt automatically; don't edit it.

| Note | Summary | Source | Added | Status |
|---|---|---|---|---|
| [[Semantic_Caching/Semantic_Caching\|Semantic Caching]] | A cache keyed on meaning: embed the question, find the most similar saved question, and return its stored answer if the similarity clears a threshold; otherwise call the LLM and store the result. | outcomeschool.com | 2026-11-11 | new |
| [[Prompt_Caching/Prompt_Caching\|Prompt Caching]] | Saving the model's prefill work (the KV cache) for a stable prompt prefix so later requests that start the same way skip recomputing it: faster and ~90% cheaper on the cached part. | outcomeschool.com | 2026-11-11 | new |
