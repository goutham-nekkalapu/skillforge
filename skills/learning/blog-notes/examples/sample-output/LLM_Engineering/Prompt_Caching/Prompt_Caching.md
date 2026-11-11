---
title: "Prompt Caching"
aliases: ["Prompt Caching", "How does Prompt Caching work?"]
summary: "Saving the model's prefill work (the KV cache) for a stable prompt prefix so later requests that start the same way skip recomputing it: faster and ~90% cheaper on the cached part."
topic: "LLM Engineering"
tags: [llm, caching, inference, kv-cache, cost-optimization]
status: new
format: markdown
mode: distilled
critique: false
source_type: blog
source_url: "https://outcomeschool.com/blog/how-does-prompt-caching-work"
author: "Amit Shekhar"
site: "outcomeschool.com"
published: "2026-06-09"
source: "[[article_d5272c24e9|Saved article]]"
explainers: ["Prompt_Caching__Cache_Reuse.html"]
created: "2026-11-11"
---

# Prompt Caching

## Overview

### TL;DR

- **Prompt caching saves the model's internal work** (the KV cache built during prefill) for a repeated *beginning* of a prompt, and reuses it on later requests.
- It only works on an **exact prefix**: the cached part must match character for character from the very first token. One early change breaks the cache for everything after it.
- So **put stable content first** (tools, instructions, documents, examples) and the **changing part last** (the user's message).
- A **cache write** costs ~1.25× normal; a **cache read** costs ~0.1× (≈90% saving). The cache expires after its **TTL** (commonly 5 min, optionally 1 h).
- Answers don't change: the model still sees the whole prompt, it just skips redoing work.

Related: [[Semantic_Caching|Semantic Caching]]

### Why it matters

Real apps send the same big block (system instructions, a policy document, tool definitions) with every request, and the model re-reads all of it each time. That repeated prefill makes every reply slower and costs money for work that was already done.

<div style="display:grid;grid-template-columns:110px 1fr;gap:6px 12px;align-items:center;margin:12px 0">
<b>Without cache</b><div style="display:flex;border-radius:6px;overflow:hidden"><div style="flex:100;background:var(--interactive-accent);color:var(--text-on-accent);padding:4px 8px">5,000 stable tokens · recomputed every time</div><div style="flex:6;background:var(--background-modifier-border);padding:4px 2px;text-align:center">50</div></div>
<b>With cache</b><div style="display:flex;border-radius:6px;overflow:hidden"><div style="flex:100;background:var(--background-secondary);color:var(--text-muted);padding:4px 8px">5,000 stable tokens · loaded from cache</div><div style="flex:6;background:var(--interactive-accent);color:var(--text-on-accent);padding:4px 2px;text-align:center">50</div></div>
</div>
*Highlighted = work the model actually does. In the article's support-bot example, only 50 of 5,050 tokens are new per request.*

## Key ideas

### 1. What's being cached: the prefill work

Before writing a reply, the model reads the whole prompt token by token (**prefill**) and stores per-token internal values in the **KV cache**: a "note" on what each token means given everything before it. Building it is the expensive part, and it grows with prompt length.

**Prompt caching = keep the KV cache for a repeated prefix, load it next time, and only prefill the new tokens.**

<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:12px 0">
<div style="border:1.5px solid var(--background-modifier-border);border-radius:10px;padding:8px 14px"><b>Prompt</b><br><small>text</small></div>
<span style="color:var(--text-muted)">── tokenize ──▶</span>
<div style="border:1.5px solid var(--background-modifier-border);border-radius:10px;padding:8px 14px"><b>Tokens</b></div>
<span style="color:var(--text-muted)">── prefill ──▶</span>
<div style="border:1.5px solid var(--interactive-accent);border-radius:10px;padding:8px 14px"><b>KV cache</b><br><small>what gets saved</small></div>
<span style="color:var(--text-muted)">── decode ──▶</span>
<div style="border:1.5px solid var(--background-modifier-border);border-radius:10px;padding:8px 14px"><b>Reply</b></div>
</div>
*Prompt caching saves the highlighted step's output for the stable prefix.*

> [!info] Added context
> This is different from [[Semantic_Caching|semantic caching]], which skips the model entirely by reusing a stored *answer* for a question with the same meaning. Prompt caching still runs the model and writes a fresh reply.

### 2. The exact-prefix rule

The cache is reused **only up to the first token that differs**. Everything after that point is recomputed.

<div style="font-family:var(--font-monospace);font-size:0.9em;margin:12px 0;line-height:1.9">
<div><span style="color:var(--text-muted)">cached&nbsp;</span> <span style="background:var(--background-secondary);border-radius:4px;padding:2px 4px">You are a polite support agent. Return window is </span><span style="padding:2px 4px">30 days.</span></div>
<div><span style="color:var(--text-muted)">new&nbsp;&nbsp;&nbsp;&nbsp;</span> <span style="background:var(--background-secondary);border-radius:4px;padding:2px 4px">You are a polite support agent. Return window is </span><span style="border:1.5px solid var(--interactive-accent);border-radius:4px;padding:2px 4px">45 days.</span></div>
</div>
*Shaded = read from cache. Outlined = first difference: recomputed from here on.*

The classic mistake: something that changes on every request near the top, like `Today's date is 2026-06-07`, a random request ID or the user's name. It silently breaks the cache for the whole prompt.

> **Rule:** stable part first, changing part last.

Step through how the cache is written once, read on later requests, and broken by an early change:

[[Prompt_Caching__Cache_Reuse.html|▶ Step through cache write, reads and a broken prefix]]

1. Request 1 prefills everything and **writes** the stable prefix to the cache.
2. Requests 2–4 share the prefix, so they **read** it and only prefill their new question.
3. A request whose first line changed (a date) **misses**: it prefills everything again.

### 3. Write once, read cheaply, until the TTL

| | When | Cost (vs. normal input) |
|---|---|---|
| **Cache write** | first request with this prefix | ~1.25× |
| **Cache read** | later requests within the TTL | ~0.1× (≈90% saving) |

- **TTL** (time to live): how long the cache stays. A common default is **5 minutes**, and a **1 hour** option exists (its write costs a bit more).
- No request with the same prefix within the TTL means the cache expires, and the next request pays for a fresh write.
- So it pays off when **many requests share a prefix and arrive close together**. A one-off request is slightly *more* expensive.

> [!warning] Check your provider
> The 1.25× / 0.1× multipliers and TTL options are the article's rough figures. Exact prices and minimum cacheable lengths vary by provider and model.

### 4. What to put in the cached prefix

<div style="display:grid;gap:6px;margin:12px 0">
<div style="border-left:6px solid var(--interactive-accent);background:var(--background-secondary);border-radius:8px;padding:8px 12px"><b>Tool definitions</b> · fixed descriptions of tools</div>
<div style="border-left:6px solid var(--interactive-accent);background:var(--background-secondary);border-radius:8px;padding:8px 12px"><b>System instructions</b> · how the model should behave</div>
<div style="border-left:6px solid var(--interactive-accent);background:var(--background-secondary);border-radius:8px;padding:8px 12px"><b>Large documents</b> · policies, manuals, knowledge base</div>
<div style="border-left:6px solid var(--interactive-accent);background:var(--background-secondary);border-radius:8px;padding:8px 12px"><b>Few-shot examples</b> · sample Q&amp;A for style</div>
<div style="border-left:6px solid var(--text-muted);border:1.5px dashed var(--background-modifier-border);border-radius:8px;padding:8px 12px"><b>User's message</b> · changes every request, goes last, not cached</div>
</div>
*Top to bottom is prompt order. Everything above the dashed block is the cacheable prefix.*

### 5. Where it shines

- **Agents**: the same instructions, tool definitions and growing history are re-sent on *every step* of a multi-step task, so the prefix is read again and again.
- **RAG**: large fixed instructions and repeated documents. It also makes *contextual retrieval* affordable, where the same full document is sent once per chunk.
- **Providers and engines**: Anthropic and OpenAI offer it as a built-in feature (mark the stable part; the response reports tokens written to and read from the cache). Inference engines do the same thing internally: vLLM shares identical prefixes, SGLang matches them with a radix tree, TensorRT-LLM calls it prefix reuse.

## Takeaways

1. Prompt caching reuses **computation** (the KV cache for a prefix), not answers. Output quality is unchanged.
2. **Order the prompt stable → changing.** Tools, system prompt, documents, examples first; the user's message last.
3. **Never put volatile values at the top** (dates, IDs, names). One changed character early breaks the whole cache. This is the usual reason for "no cache hits".
4. It's a **volume and timing** play: write ~1.25×, read ~0.1×, within the TTL. Low-traffic or one-off prompts gain little.
5. **Verify it's working** with the cache read/write token counts in the provider's response.

## Source

| | |
|---|---|
| Post | [How does Prompt Caching work?](https://outcomeschool.com/blog/how-does-prompt-caching-work) |
| Author | Amit Shekhar · outcomeschool.com |
| Published | 2026-06-09 |
| Saved article | [[article_d5272c24e9\|Saved article]] |

FAQ section skipped (it repeats the points above). Course promotions and newsletter boxes left out.
