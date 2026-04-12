---
name: obsidian-save-cloud
description: >
  Save conversation summaries, reports, brainstorm notes, and markdown files to an Obsidian vault
  stored on Google Drive — using the Google Drive MCP connector. Use this skill whenever the user
  says things like "save this to my vault", "push this to Obsidian", "export to my notes",
  "save summary to Drive", "send to vault", "write to Obsidian", or any variation of saving
  conversation content to an Obsidian vault or Google Drive notes folder. Also trigger when the
  user asks to "remember this in my notes", "archive this discussion", or "export this chat".
  This skill is for cloud/web environments (claude.ai) — it writes via the Google Drive MCP
  connector, not the local filesystem. If the Google Drive connector is not connected, the skill
  will guide the user to enable it.
---

# obsidian-save-cloud

Save markdown files to an Obsidian vault on Google Drive from claude.ai conversations.

## Prerequisites

This skill requires the **Google Drive MCP connector** to be connected in claude.ai.
If it is not connected, tell the user:

> "To save files to your Google Drive, I need the Google Drive connector enabled.
> You can connect it from the tools menu (the puzzle piece icon) in this chat."

Then use `suggest_connectors` to show the Google Drive connector for easy one-click setup.

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

Use the Google Drive MCP tool to create the file at the resolved path.

The typical tool call sequence:
1. Search for the vault folder to confirm it exists (use `gdrive_search` or similar)
2. Create the file in the target folder (use `gdrive_create_file` or `gdrive_upload`)

If the vault or folder doesn't exist on Drive, inform the user and ask whether to create it.

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

- **Drive connector not connected**: Guide the user to enable it, use `suggest_connectors`
- **Vault folder not found**: Ask if user wants to create it, or if the path is wrong
- **Permission error**: Suggest the user check their Google Drive MCP permissions
- **File already exists**: Append a short suffix (e.g., `-v2`) rather than overwriting
