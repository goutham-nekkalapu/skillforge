---
name: obsidian-save-local
description: >
  Save markdown files, reports, summaries, and notes to a local Obsidian vault using the
  official Obsidian CLI (v1.12+). Use this skill whenever the user says "save to vault",
  "push to Obsidian", "write to my notes", "export to vault", "save this locally", or any
  variation of writing content to a local Obsidian vault. Also trigger for "remember this
  in my notes", "archive this to Obsidian", "capture this", or "add to my daily note".
  This skill is for local environments (Claude Code, Claude Desktop, CLI agents) where the
  Obsidian CLI is available. It uses the `obsidian` command to create, append, and manage
  notes — no direct filesystem writes needed. Do NOT use this skill on claude.ai — use
  obsidian-save-cloud instead.
---

# obsidian-save-local

Save markdown files to a local Obsidian vault using the official Obsidian CLI.

## Prerequisites

The user must have:
1. **Obsidian 1.12+** installed (desktop)
2. **CLI enabled** in Settings → General → Command line interface
3. The `obsidian` command available in their terminal PATH

To verify:
```bash
obsidian --version
```

If the CLI is not available, tell the user:
> "The Obsidian CLI requires Obsidian 1.12+ with the CLI enabled in Settings → General.
> After enabling it, restart your terminal for the PATH to update."

## How It Works

### 1. Determine the Target

The skill resolves the destination using this priority:

1. **Per-request override** — the user specifies a vault or folder in their message
   - "save this to vault in Projects/GenDigital"
   - "push to Obsidian under References/AI"
   - "save to my WorkNotes vault"
2. **Config file** — read from `~/.config/obsidian-skill/config.json`
3. **CLAUDE.md** — check the project-level CLAUDE.md for vault config
4. **Skill fallback** — prompt the user for initial setup

#### Config File Format

Located at `~/.config/obsidian-skill/config.json`:

```json
{
  "vault_name": "SecondBrain",
  "default_folder": "Inbox"
}
```

Note: With the Obsidian CLI, we no longer need full filesystem paths. The CLI resolves
vaults by name and paths relative to the vault root.

#### First-Time Setup

If no config file exists, run the interactive setup:

1. List available vaults to help the user choose:
   ```bash
   # The CLI targets the most recently focused vault by default.
   # Ask the user which vault they want as their default.
   ```
2. Ask for the default subfolder (suggest `Inbox`)
3. Write the config:
   ```bash
   mkdir -p ~/.config/obsidian-skill
   cat > ~/.config/obsidian-skill/config.json << 'EOF'
   {
     "vault_name": "SecondBrain",
     "default_folder": "Inbox"
   }
   EOF
   ```
4. Confirm setup is complete

#### CLAUDE.md Integration

For project-specific vault routing, users can add this to their project's `CLAUDE.md`:

```markdown
## Obsidian Vault Config
- vault_name: SecondBrain
- default_folder: Projects/CurrentProject
```

Project-level config overrides the global config file, allowing different coding projects to
route notes to different vault folders automatically.

### 2. Generate the Filename

Use this pattern: `YYYY-MM-DD-{slug}.md`

The slug should be a short, lowercase, hyphenated summary of the content topic.
Examples:
- `2026-04-12-brainstorm-fraud-detection.md`
- `2026-04-12-code-review-notes.md`
- `2026-04-12-architecture-decision-record.md`

### 3. Format the Content

Build the content string with YAML frontmatter and a markdown body.

Frontmatter template:
```yaml
---
title: "{Descriptive Title}"
date: {YYYY-MM-DD}
source: claude-local
type: {summary|brainstorm|report|notes|reference|adr|code-notes}
tags:
  - {relevant-tag-1}
  - {relevant-tag-2}
---
```

The `source: claude-local` tag distinguishes locally-generated notes from web-generated ones
(`claude-ai`). This lets users filter by source in Obsidian's Dataview plugin.

Additional `type` values for local context:
- `adr` — Architecture Decision Record
- `code-notes` — Notes about code, debugging sessions, implementation details

### 4. Write Using the Obsidian CLI

#### Creating a New Note

```bash
obsidian vault="SecondBrain" create \
  name="Inbox/2026-04-12-brainstorm-fraud-detection" \
  content="---\ntitle: \"Fraud Detection Brainstorm\"\ndate: 2026-04-12\nsource: claude-local\ntype: brainstorm\ntags:\n  - fraud-detection\n  - ml\n---\n\n# Fraud Detection Brainstorm\n\nContent here..." \
  silent
```

Key flags:
- `vault="VaultName"` — must be the FIRST parameter to target a specific vault
- `name="folder/filename"` — path relative to vault root (no .md extension needed)
- `content="..."` — the full note content, use `\n` for newlines
- `silent` — prevents the note from opening in the Obsidian GUI
- `template="TemplateName"` — optionally use an Obsidian template

#### Appending to the Daily Note

When the user says "add this to my daily note" or "append to today's note":

```bash
obsidian vault="SecondBrain" daily:append \
  content="\n## Claude Session Notes\n\nContent here..."
```

#### Appending to an Existing Note

```bash
obsidian vault="SecondBrain" append \
  file="Inbox/existing-note" \
  content="\n\n## Update\n\nNew content here..."
```

#### Setting Properties After Creation

If you need to set or update frontmatter properties:

```bash
obsidian vault="SecondBrain" property:set \
  name="status" value="draft" \
  file="Inbox/2026-04-12-brainstorm-fraud-detection"
```

#### Reading Back to Verify

```bash
obsidian vault="SecondBrain" read \
  file="Inbox/2026-04-12-brainstorm-fraud-detection"
```

### 5. Confirm to the User

After writing, confirm with:
- The vault and path where the note was saved
- The note type and tags applied
- A reminder about override options

Example:
> Created **SecondBrain → Inbox/2026-04-12-brainstorm-fraud-detection.md**
> Type: brainstorm | Tags: fraud-detection, ml
> Google Drive will sync this to your other devices.

## Handling Path Overrides

Per-request overrides don't change stored defaults:

| User says | Vault | Folder | Config changes? |
|-----------|-------|--------|-----------------|
| "save to vault" | config default | config default | No |
| "save to vault in Projects" | config default | Projects/ | No |
| "save to WorkNotes vault" | WorkNotes | config default folder | No |
| "set my default folder to Projects" | — | — | Yes |
| "change my vault to WorkNotes" | — | — | Yes |

## Content Generation Guidelines

When saving from a Claude Code or Desktop session, the content is often more technical.
The skill should handle:

- **Code discussion summaries** — key decisions, approaches considered, what was chosen and why
- **Architecture Decision Records** — structured ADR format with context, decision, consequences
- **Debugging session notes** — what broke, what was tried, what fixed it
- **Implementation notes** — how something works, gotchas, future considerations
- **Daily note additions** — quick captures, tasks, links to append to today's daily note

For code-heavy content, use fenced code blocks with language identifiers.

If the user says "save this" without specifying what, summarize the current conversation
focusing on technical decisions and actionable takeaways.

## Advanced: Using Templates

If the user has Obsidian templates set up, the CLI can use them:

```bash
obsidian vault="SecondBrain" create \
  name="Inbox/2026-04-12-meeting-notes" \
  template="Meeting Notes" \
  silent
```

Then append the actual content:

```bash
obsidian vault="SecondBrain" append \
  file="Inbox/2026-04-12-meeting-notes" \
  content="Content generated by Claude..."
```

This respects the user's existing template structure and just fills in the content.

## Managing Configuration

### Viewing Current Config
```bash
cat ~/.config/obsidian-skill/config.json | python3 -m json.tool
```

### Updating Default Folder
When user says "change my default folder to Projects":
```bash
python3 -c "
import json, os
config_path = os.path.expanduser('~/.config/obsidian-skill/config.json')
config = json.load(open(config_path))
config['default_folder'] = 'Projects'
json.dump(config, open(config_path, 'w'), indent=2)
print('Updated default folder to: Projects')
"
```

### Updating Vault
When user says "change my vault to WorkNotes":
```bash
python3 -c "
import json, os
config_path = os.path.expanduser('~/.config/obsidian-skill/config.json')
config = json.load(open(config_path))
config['vault_name'] = 'WorkNotes'
json.dump(config, open(config_path, 'w'), indent=2)
print('Updated vault to: WorkNotes')
"
```

## Error Handling

- **CLI not found**: Guide user to enable CLI in Obsidian Settings → General
- **Vault not found**: List available vaults, ask user to pick the right one
- **Obsidian not running**: The CLI requires Obsidian to be running. Inform the user.
- **Permission denied**: Suggest checking system permissions for the CLI symlink
- **File already exists**: Use `overwrite` flag if user confirms, otherwise append or suffix

## Fallback: Direct Filesystem Write

If the Obsidian CLI is not available (Obsidian < 1.12, CLI not enabled, or headless server),
fall back to direct filesystem writes. In this case:

1. Read the vault path from config (will need `base_path` field added to config)
2. Write the markdown file directly with `mkdir -p` and `cat`
3. Obsidian will pick up the file on next vault index

This ensures the skill works even in environments where the CLI isn't an option, such as
remote servers or CI/CD pipelines that sync to a vault directory.
