# obsidian-save-local

Save conversation content to a local Obsidian vault using the official Obsidian CLI.

## What It Does

This skill lets you say things like "save this to my vault", "push to Obsidian", or "write to my notes" during a local coding session. The agent formats the content as an Obsidian-compatible markdown note with YAML frontmatter, tags, and clean structure — then writes it to your vault using the Obsidian CLI (v1.12+). No direct filesystem writes needed.

## Platform

- **Claude Code**, **Cursor**, and other local CLI agents (requires shell access)

## Features

- Uses the official Obsidian CLI — no direct filesystem writes
- Auto-generates filenames with date prefix (`YYYY-MM-DD-slug.md`)
- Adds YAML frontmatter with title, date, source, type, and tags
- Persists vault name and default folder in `~/.config/obsidian-skill/config.json`
- Supports per-project overrides via `CLAUDE.md`
- Per-request folder and vault overrides without changing defaults
- Append to daily notes or existing notes
- Obsidian template support for structured note creation
- Falls back to direct filesystem write when the CLI is unavailable

## Setup

1. Install **Obsidian 1.12+** (desktop)
2. Enable the CLI in **Settings → General → Command line interface**
3. Restart your terminal so `obsidian` is on your PATH
4. On first use, the skill will ask for your vault name and default folder

## Examples

```
"Save this to my vault"
"Push this discussion to Obsidian"
"Write to my notes under Projects/Skillforge"
"Add this to my daily note"
"Archive this to Obsidian"
"Remember this in my notes"
```

## Install

```bash
# Via npx
npx skillforge install obsidian/obsidian-save-local

# From the skillforge repo
./install.sh obsidian/obsidian-save-local

# Or direct download
curl -sL -o SKILL.md \
  https://raw.githubusercontent.com/gouthi/skillforge/main/skills/obsidian/obsidian-save-local/SKILL.md
```
