# Google Drive

Skills for working with files in Google Drive through the Google Drive connector.

## Skills in This Group

| Skill | Platform | Description |
|-------|----------|-------------|
| [gdrive-save](gdrive-save/) | claude.ai (any client with the Drive connector) | Save markdown, HTML (with JS), JSON and other files to an exact Drive folder without converting them to Google Docs |

## gdrive-save or obsidian-save-cloud?

**`gdrive-save` saves files you already have, as they are. [obsidian-save-cloud](../obsidian/obsidian-save-cloud/) first writes a note from the conversation, then saves it with `gdrive-save`.**

| | gdrive-save | obsidian-save-cloud |
|---|---|---|
| **Input** | Any file or content, saved exactly as given | The conversation, turned into a summary note |
| **Writes content** | No | Yes: title, key points, decisions, action items |
| **File types** | Markdown, HTML with JS, JSON, CSV, images… | One markdown note |
| **Naming / frontmatter** | Keeps your names and content unchanged | Adds frontmatter and a `YYYY-MM-DD-slug.md` name |
| **Where** | The exact folder you say | Your vault's default folder (remembered) or one you name |
| **Used by** | You, yt-notes, yt-transcript, obsidian-save-cloud | You |

Example: "save this page to Drive in Projects/Demos" → gdrive-save. "Save this discussion to my vault" → obsidian-save-cloud.

## Install All Google Drive Skills

```bash
npx skillforge install google-drive

# Or via install script
./install.sh google-drive
```
