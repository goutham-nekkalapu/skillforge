---
name: obsidian-save-cloud
description: >
  Turn conversation content (summaries, reports, brainstorms) into a formatted Obsidian note
  and save it to the user's vault on Google Drive. Use this skill whenever the user says
  things like "save this to my vault", "push this to Obsidian", "export to my notes",
  "send to vault", "write to Obsidian", or any variation of saving conversation content to
  an Obsidian vault. Also trigger when the user asks to "remember this in my notes",
  "archive this discussion", or "export this chat". This skill decides the note's content,
  frontmatter, filename and folder; the gdrive-save skill does the actual Google Drive upload.
  For saving existing files (HTML pages, JSON, a file as-is) to Drive without turning them
  into a note, use gdrive-save directly. This skill is for cloud/web environments (claude.ai).
---

# obsidian-save-cloud

Turn conversation content into an Obsidian note and save it to a vault on Google Drive from claude.ai conversations.

## Prerequisites

This skill saves through the **gdrive-save** skill, which needs the **Google Drive connector** connected in claude.ai. If the connector isn't connected, gdrive-save tells the user and offers to connect it.

## How It Works

### 1. Determine the Target Path

The skill resolves the destination folder using this priority:

1. **Per-request override** — the user specifies a folder in their message
   - "save this to my vault in Projects/GenDigital"
   - "push to Obsidian under References/AI"
2. **Stored user preference** — check Claude's memory for a stored default
   - Look for memory containing vault config (vault name, default folder)
3. **Skill fallback** — `Inbox/` inside the vault root

The full Google Drive path follows this pattern:

```
/{vault_name}/{folder}/{filename}.md
```

For example: `/SecondBrain/Inbox/2026-04-11-brainstorm-ai-agents.md`

If this is the **first time** the user is using the skill and no vault config exists in memory,
ask the user two things:
- What is your Obsidian vault name on Google Drive? (e.g., "SecondBrain")
- What should the default folder be? (e.g., "Inbox", "ClaudeNotes", "Captures")

Then store this in memory using `memory_user_edits` so future invocations just work.

### 2. Generate the Filename

Use this pattern: `YYYY-MM-DD-{slug}.md`

The slug should be a short, lowercase, hyphenated summary of the content topic.
Examples:
- `2026-04-11-brainstorm-fraud-detection.md`
- `2026-04-11-summary-mcp-architecture.md`
- `2026-04-11-meeting-notes-team-sync.md`

### 3. Format the Content

Every file must include YAML frontmatter followed by the markdown body:

```markdown
---
title: "{Descriptive Title}"
date: {YYYY-MM-DD}
source: claude-ai
type: {summary|brainstorm|report|notes|reference}
tags:
  - {relevant-tag-1}
  - {relevant-tag-2}
---

# {Title}

{Content body here}
```

The `source: claude-ai` tag lets the user identify AI-generated notes in their vault.
Choose `type` based on the content being saved.
Generate 2-4 relevant tags based on the discussion topic.

### 4. Write the File

Hand the note to the **gdrive-save** skill with:
- destination: `{vault_name}/{folder}`
- the file: `{filename}.md` with the content from step 3
- conflict rule: keep both (a new note never overwrites an existing one), unless the user asked to update a note they saved earlier

gdrive-save creates missing folders, keeps the file as real markdown (not a Google Doc, which Obsidian can't open), and returns the Drive path and link.

If the **vault folder itself** doesn't exist on Drive, ask the user whether the vault name is right before creating it, since a typo would create a whole new vault folder.

If gdrive-save isn't installed, use the Google Drive connector directly: find or create each folder (search by title + `parentId`, following `nextPageToken` to the end), then `create_file` with `textContent`, `contentMimeType: "text/markdown"` and `disableConversionToGoogleType: true`.

### 5. Confirm to the User

After writing, confirm with:
- The full path where the file was saved
- A brief note that it will sync to their devices via Google Drive
- A reminder that they can say "change my default vault folder to X" to update the default

Example confirmation:
> Saved to **SecondBrain/Inbox/2026-04-11-brainstorm-fraud-detection.md**
> This will sync to your devices via Google Drive. To change your default folder, just tell me.

## Handling Path Overrides

When the user specifies a folder in their request, use it for this invocation only — don't
change the stored default. Examples:

| User says | Vault | Folder | Stored default changes? |
|-----------|-------|--------|------------------------|
| "save to vault" | stored default | stored default | No |
| "save to vault in Projects" | stored default | Projects/ | No |
| "save to SecondBrain/References/AI" | SecondBrain | References/AI/ | No |
| "set my default folder to Projects" | — | — | Yes → Projects/ |
| "change my vault to WorkNotes" | — | — | Yes → WorkNotes |

## Content Generation Guidelines

When the user asks to "save this discussion" or "export this chat", generate a well-structured
summary of the conversation so far. Include:

- A clear title summarizing the main topic
- Key decisions or conclusions reached
- Action items if any were discussed
- Important technical details or code snippets (in fenced code blocks)
- Links or references mentioned

Don't just dump the raw conversation. Synthesize it into useful reference material that will
be valuable when the user revisits the note in their Obsidian vault later.

If the user provides specific content to save (e.g., "save this report I just asked you to write"),
save that content directly rather than summarizing the conversation.

## Error Handling

- **Drive connector not connected / permission errors**: handled by gdrive-save. Pass its message on to the user.
- **Vault folder not found**: Ask if the vault name is right before creating it.
- **File already exists**: Keep both (gdrive-save adds ` (2)`), unless the user asked to update the earlier note.
