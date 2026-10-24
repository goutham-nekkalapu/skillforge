# Google Drive

Skills for working with files in Google Drive through the Google Drive connector.

## Skills in This Group

| Skill | Platform | Description |
|-------|----------|-------------|
| [gdrive-save](gdrive-save/) | claude.ai (any client with the Drive connector) | Save files (markdown, HTML with JS, JSON…) or conversation notes to an exact Drive folder, e.g. your Obsidian vault, without converting them to Google Docs |

`gdrive-save` replaces the former `obsidian-save-cloud` skill: "save this discussion to my vault" now writes the note and saves it in one step. For saving notes into a local vault without Drive, see [obsidian/obsidian-save-local](../obsidian/obsidian-save-local/).

## Install All Google Drive Skills

```bash
npx skillforge install google-drive

# Or via install script
./install.sh google-drive
```
