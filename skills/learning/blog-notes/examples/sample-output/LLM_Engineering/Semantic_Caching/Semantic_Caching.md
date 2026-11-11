---
title: "Semantic Caching"
aliases: ["Semantic Caching", "How does Semantic Caching work?"]
summary: "A cache keyed on meaning: embed the question, find the most similar saved question, and return its stored answer if the similarity clears a threshold; otherwise call the LLM and store the result."
topic: "LLM Engineering"
tags: [llm, caching, embeddings, vector-search, cost-optimization]
status: new
format: markdown
mode: distilled
critique: false
source_type: blog
source_url: "https://outcomeschool.com/blog/how-does-semantic-caching-work"
author: "Amit Shekhar"
site: "outcomeschool.com"
published: "2026-07-08"
source: "[[article_aacfb5185d|Saved article]]"
explainers: []
created: "2026-11-11"
---

# Semantic Caching

## Overview

### TL;DR

- **Semantic caching matches questions by meaning, not exact text**, and returns a previously saved LLM answer when a new question means the same thing.
- Questions become **embeddings** (vectors where similar meaning means nearby points); a **similarity score** (usually cosine) measures closeness.
- **Hit** = best score ≥ **threshold**, so the saved answer is returned with no model call. **Miss** = call the model, then store question, embedding and answer.
- The **threshold is the whole game**: too high and nothing matches; too low and you return wrong answers. ~0.85–0.95 is a common start; tune it on real queries.
- Use it for answers that **don't change quickly**, and refresh entries over time.

Related: [[Prompt_Caching|Prompt Caching]]

### Why it matters

Every LLM call costs money and time, and users ask the same things in many different words. **Exact-match caching** only hits on identical strings, so "What is the capital of France?" and "Tell me the capital city of France." are two misses and two paid calls. Semantic caching turns those paraphrases into hits.

## Key ideas

### 1. Embeddings put meaning on a map

An **embedding** is a list of numbers (hundreds in practice) produced by an **embedding model**, placed so that sentences with similar meaning land close together.

| Question | Toy 2-D embedding |
|---|---|
| "What is the capital of France?" | `[0.91, 0.10]` |
| "Tell me the capital city of France." | `[0.89, 0.12]`, close: same meaning |
| "How do I bake a chocolate cake?" | `[0.05, 0.95]`, far: different meaning |

**Similarity** turns two embeddings into one score, roughly 0 (unrelated) to 1 (same meaning). Higher score means closer meaning.

### 2. The lookup flow: hit or miss

<div style="display:grid;gap:6px;margin:12px 0;max-width:520px">
<div style="border:1.5px solid var(--background-modifier-border);border-radius:10px;padding:8px 14px"><b>1 · User question</b></div>
<div style="border:1.5px solid var(--background-modifier-border);border-radius:10px;padding:8px 14px"><b>2 · Embed it</b> <small style="color:var(--text-muted)">embedding model → vector</small></div>
<div style="border:1.5px solid var(--background-modifier-border);border-radius:10px;padding:8px 14px"><b>3–4 · Search the cache</b> <small style="color:var(--text-muted)">best similarity among saved questions</small></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
<div style="border:1.5px solid var(--interactive-accent);border-radius:10px;padding:8px 14px"><b>score ≥ threshold → HIT</b><br><small>return saved answer · no LLM call</small></div>
<div style="border:1.5px dashed var(--background-modifier-border);border-radius:10px;padding:8px 14px"><b>score &lt; threshold → MISS</b><br><small>ask LLM · store question + embedding + answer</small></div>
</div>
</div>
*Every question pays for one embedding and one search; only misses pay for the LLM.*

```python
def get_answer(question):
    new_embedding = embed(question)                   # text -> vector
    best_match, score = search_cache(new_embedding)   # closest saved question
    if score >= 0.85:                                 # hit
        return best_match.answer
    answer = ask_model(question)                      # miss
    store_in_cache(question, new_embedding, answer)
    return answer
```

In production the saved embeddings live in a **vector database**, which finds the closest ones fast with **approximate nearest neighbour (ANN)** search.

### 3. A worked example (threshold 0.85)

Cache holds: *"What is the capital of France?" → "Paris"*.

<div style="display:grid;grid-template-columns:230px 1fr 60px;gap:6px 12px;align-items:center;margin:12px 0">
<span>"Tell me the capital city of France."</span><div style="background:var(--background-secondary);border-radius:6px"><div style="width:93%;background:var(--interactive-accent);color:var(--text-on-accent);border-radius:6px;padding:3px 8px">0.93</div></div><b>hit</b>
<span>"What is the population of France?"</span><div style="background:var(--background-secondary);border-radius:6px"><div style="width:40%;background:var(--text-muted);color:var(--background-primary);border-radius:6px;padding:3px 8px">0.40</div></div><span>miss</span>
<span>"How do I bake a chocolate cake?"</span><div style="background:var(--background-secondary);border-radius:6px"><div style="width:8%;background:var(--text-muted);color:var(--background-primary);border-radius:6px;padding:3px 4px">0.05</div></div><span>miss</span>
</div>
*Bar = similarity to the saved question; only the paraphrase clears 0.85. Note the "population" question shares words ("France") but not meaning.*

### 4. Choosing the threshold

<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin:12px 0">
<div style="border:1.5px solid var(--background-modifier-border);border-radius:10px;padding:8px 12px"><b>Too low (0.50)</b><br><small>"capital of France" matches "capital of Germany", so the user gets the wrong city</small></div>
<div style="border:1.5px solid var(--interactive-accent);border-radius:10px;padding:8px 12px"><b>~0.85–0.95</b><br><small>common starting range; tune on real user questions</small></div>
<div style="border:1.5px solid var(--background-modifier-border);border-radius:10px;padding:8px 12px"><b>Too high (0.99)</b><br><small>only near-copies match, so most of the benefit is gone</small></div>
</div>

> A high threshold means fewer hits but safer answers. A low threshold means more hits but a higher chance of a wrong answer.

### 5. When it fits, and when it doesn't

| Good fit | Poor fit |
|---|---|
| Stable answers ("capital of France", product FAQs, policy questions) | Time-sensitive answers ("weather right now", prices, stock levels) |
| Many users phrasing the same intent differently | Answers personalised per user or per session |

Refresh or expire entries over time so answers that went stale don't stay forever.

> [!info] Added context
> Semantic caching skips the model entirely by reusing a stored *answer*. [[Prompt_Caching|Prompt caching]] still runs the model and reuses its *computation* on a repeated prompt prefix. They stack: a miss here can still benefit from a cached prefix.

## Takeaways

1. Cache on **meaning**: embed → nearest saved question → compare to a threshold.
2. A hit returns the saved answer with **no LLM call**: cheaper, faster, less load on the model.
3. **Tune the threshold on real traffic.** It's a precision/recall dial; a bad value either wastes the cache or serves wrong answers.
4. Only cache **answers that don't change quickly**, and refresh entries periodically.
5. Store question + embedding + answer in a **vector database** with ANN search at scale.

## Source

| | |
|---|---|
| Post | [How does Semantic Caching work?](https://outcomeschool.com/blog/how-does-semantic-caching-work) |
| Author | Amit Shekhar · outcomeschool.com |
| Published | 2026-07-08 |
| Saved article | [[article_aacfb5185d\|Saved article]] |

FAQ section skipped (it repeats the points above). Course promotions and newsletter boxes left out.
