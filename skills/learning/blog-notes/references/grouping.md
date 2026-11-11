# Grouping posts into notes

When the user gives several posts, decide which share a note. Decide after fetching and reading them, not from the titles: headlines are often clickbait, and two posts with similar titles can be about different things.

## The test

> Can one note title name **the concept itself** and honestly cover every post in the group?

If yes, they share a note. If the only title that fits is an umbrella ("LLM Caching", "Database Performance", "Kafka"), they are different concepts: make separate notes, put them in the same topic folder, and link them to each other.

The umbrella check matters because almost any set of posts can be squeezed under a broad enough title, and a note that covers two concepts serves neither: the TL;DR blurs, and the user can't find either concept by name later.

## Cases

| Posts | Result |
|---|---|
| Several explanations of the same concept | One combined note |
| A series (Part 1, 2, 3 of one walkthrough) | One combined note, in series order |
| Related but different concepts | Separate notes, same topic, linked |
| Unrelated | Separate notes, each in its own topic |
| A mix (3 on A, 2 on B) | One note per group |
| One overview post + one deep dive on a part of it | Separate notes: the deep dive's concept is narrower. Link them |

## Worked examples

- **Prompt caching + semantic caching** → 2 notes. "LLM Caching" is an umbrella. Prompt caching reuses computed prefixes inside the model; semantic caching returns stored answers for similar questions. Both go in "LLM Engineering" and link to each other.
- **Three posts each explaining consistent hashing** → 1 note, "Consistent Hashing", tags P1–P3, with a Coverage table.
- **"Building a RAG pipeline, Part 1: chunking" + "Part 2: retrieval" + "Part 3: evaluation"** → 1 note, "RAG Pipeline", the parts as its key ideas.
- **"What is Kafka" + "Kafka consumer groups explained"** → 2 notes: "Kafka" is broader than "Kafka Consumer Groups".
- **A React hooks post + a Postgres VACUUM post** → 2 notes in different topics.

## Announce, then carry on

State the grouping in one line before writing, then proceed without waiting:

> 3 notes: Prompt Caching (P1, P3), Semantic Caching (P2), both in LLM Engineering; Postgres VACUUM (P4) in Databases.

The user's word wins over the test: "combine them" means one note (if it's within the limits), "keep them separate" means one note per post. The one time to ask before writing: the user asked for one note but the posts are clearly different concepts. Say why and ask whether they want one note anyway or separate linked notes.

## Limits

Only combined notes have limits: at most `max_posts` (5) posts and `max_combined_words` (40,000) words. `prepare` enforces both. When a group is over, offer: split it by subtopic, or one note per post plus a short hub note (a `quick`-style note whose Key ideas are links to the per-post notes). Separate notes have no count limit; write them one at a time.

## Missing posts

If a post in a group failed to fetch, group the rest as if it weren't there, but when it leaves a gap (Part 2 of 3), add a `> [!warning] Missing part` callout in the note and mention in the report that it can be added later ("add this post to my RAG Pipeline note").
