# gdrive-save

Saves files to an exact folder in your Google Drive as real files (markdown, HTML with JavaScript and CSS, JSON, CSV, SVG, code, small images or PDFs) instead of converting them to Google Docs.

## What It Does

- Creates any missing folders on the path.
- Uploads each file with its real type, so a `.md` stays markdown (Obsidian can open it) and an `.html` page keeps its scripts.
- Replaces existing files instead of creating `file (1).md` duplicates, when you or a calling skill say to update. Otherwise it asks.
- Tells you where files will go before saving, and reports each file's Drive path and link afterwards.

Other skills use it to persist output from claude.ai, where the sandbox disk is temporary. [yt-notes](../../learning/yt-notes/) and [yt-transcript](../../learning/yt-transcript/) do, and [obsidian-save-cloud](../../obsidian/obsidian-save-cloud/) uses it to write vault notes.

## Platform

Anywhere the **Google Drive connector** is connected, mainly **claude.ai** (web, mobile, desktop chat). On your own computer, writing straight into a Drive-synced folder is simpler, and the skill does that when it can.

## Setup

1. Connect **Google Drive** in claude.ai: **Customize → Connectors**.
2. Install this skill.

Good to know:
- Drive's web preview doesn't run JavaScript. HTML pages run when opened from your synced Drive folder in a browser, or in Obsidian with an HTML plugin that has scripts enabled.
- Large files pass through the conversation, so they're slow and use more of your usage. A few hundred KB of text is fine.
- Files go to the Google account the connector is signed in with.

## Trigger Phrases

```
"Save this page to my Drive in Projects/Demos"
"Upload these notes to Google Drive under Notes/AI"
"Put the HTML you just made in my Drive folder"
```

## Install

```bash
npx skillforge install google-drive/gdrive-save

# Or via install script
./install.sh google-drive/gdrive-save
```
