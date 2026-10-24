# obsidian-save-cloud

Save conversation content from claude.ai directly to your Obsidian vault on Google Drive.

## What It Does

This skill lets you say things like "save this to my vault" or "push to Obsidian" during a claude.ai conversation. Claude will format the content as a proper Obsidian-compatible markdown note with YAML frontmatter, tags, and clean structure — then save it to your Google Drive using the [gdrive-save](../../google-drive/gdrive-save/) skill.

## Platform

- **claude.ai** (requires the Google Drive connector and the [gdrive-save](../../google-drive/gdrive-save/) skill)

## Features

- Auto-generates filenames with date prefix (`YYYY-MM-DD-slug.md`)
- Adds YAML frontmatter with title, date, source, type, and tags
- Remembers your vault name and default folder across conversations
- Supports per-request folder overrides ("save to Projects/AI")
- Synthesizes conversations into clean reference notes

## Setup

1. Connect the **Google Drive MCP connector** in claude.ai (puzzle piece icon → Google Drive)
2. On first use, Claude will ask for your vault name and default folder
3. That's it — just say "save this to my vault" in any conversation

## Examples

```
"Save this to my vault"
"Push this discussion to Obsidian"
"Export this chat to my notes under Projects/Skillforge"
"Remember this in my vault"
```

## Install

Install [gdrive-save](../../google-drive/gdrive-save/) too; this skill uses it for the upload.

```bash
# Via npx
npx skillforge install obsidian/obsidian-save-cloud
npx skillforge install google-drive/gdrive-save

# From the skillforge repo
./install.sh obsidian/obsidian-save-cloud
./install.sh google-drive/gdrive-save

# Or direct download
curl -sL -o SKILL.md \
  https://raw.githubusercontent.com/gouthi/skillforge/main/skills/obsidian/obsidian-save-cloud/SKILL.md
```
