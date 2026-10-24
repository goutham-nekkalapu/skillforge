---
name: gdrive-save
description: Save files to an exact folder path in the user's Google Drive using the Google Drive connector, keeping them as real files instead of converting them to Google Docs. Handles markdown, HTML pages (including JavaScript and CSS), JSON, CSV, SVG, code and other text, plus small images or PDFs. Creates missing folders and replaces existing files instead of piling up duplicates. Use it whenever the user asks to save, upload, put, back up or store a file or something Claude made "to Drive", "to Google Drive" or "to my Drive folder", including notes for an Obsidian vault that syncs through Drive, and whenever another skill needs to persist files to Drive (for example, from claude.ai, where the sandbox disk is temporary). Not for creating or editing Google Docs, Sheets or Slides.
---

# gdrive-save

Put one or more files at an exact path in Google Drive, byte for byte, as the file type they really are. A `.md` stays markdown (so Obsidian can open it), and an `.html` page keeps its scripts and styles.

This skill uses the Google Drive connector tools `search_files`, `create_file` and `trash_file` (they may need loading through tool search). If the connector isn't connected, say so and offer to connect it (SuggestConnectors or suggest_connectors, if available). Never claim a file was saved when it wasn't.

**Skip this skill when the destination is already on the local disk.** If Claude runs on the user's own computer and the target is a Google-Drive-synced folder (e.g. `~/Library/CloudStorage/GoogleDrive-…/My Drive/…`), just write the file there and Drive for desktop syncs it. Use this skill when the connector is the only route, such as on claude.ai (web, mobile, desktop chat) or when no synced folder is available.

## 1. Work out what to save and where (and say it first)

- **Files**: content from the conversation (a page or note Claude just wrote) or files on disk. Read files from disk exactly; don't retype or "clean up" content.
- **Destination**: a path from the top of My Drive, like `Notes/YouTube Notes/System Design`. "My Drive/…" means the same thing. If the user didn't give one, use the folder they've used before in this conversation, or else ask once (suggest `Claude Files`). Shared drives are out of scope.
- **File names**: keep the given name and extension. When naming something new, use a readable name with the right extension (`Consistent Hashing.md`, `ring-demo.html`).
- **If a file with the same name already exists**:
  - Replace it when the user or the calling skill says to update, overwrite or regenerate, or when re-saving a newer version of the same thing in this conversation.
  - Otherwise ask whether to replace it or keep both.
  - When nobody can be asked (scheduled or unattended run), keep both by adding ` (2)` before the extension, and say so.

Before uploading, tell the user in one line where the files will go, e.g. *"Saving 2 files to My Drive/Notes/YouTube Notes/System Design/Consistent Hashing/"*.

## 2. Find or create each folder in the path

Walk the path one folder at a time, starting from parent `root` (My Drive):

1. Search: `title = '<name>' and mimeType = 'application/vnd.google-apps.folder' and parentId = '<parent id>'` with `excludeContentSnippets: true`. Escape a `'` inside a name as `\'`.
   - **Follow `nextPageToken` until it is absent.** The connector often returns an empty or partial first page with a token, and the match is on the next page. An empty first page doesn't mean "not found".
   - Trashed items aren't returned. Don't add `trashed = false`; the connector rejects that field.
2. If found, use its `id`. If several match, use the oldest (`createdTime`) and mention the duplicates to the user.
3. If not found, create it with `create_file`: `title`, `parentId`, `contentMimeType: "application/vnd.google-apps.folder"`, with no content. The response contains the new `id`.
4. **Reuse IDs you already have.** A newly created folder or file can take a while to appear in search, so never re-search for something you just created; keep the ID from the create response.

## 3. Upload each file

`create_file` with:

| Field | Value |
|---|---|
| `title` | file name with extension |
| `parentId` | target folder ID |
| `textContent` | the full text, for text files |
| `base64Content` | base64 of the bytes, for binary files only (instead of `textContent`) |
| `contentMimeType` | from the table below |
| `disableConversionToGoogleType` | **`true`, always.** Without it, Drive converts text and HTML into a Google Doc, which strips scripts and makes the file unusable in Obsidian or a browser. |

| Extension | contentMimeType |
|---|---|
| `.md` | `text/markdown` |
| `.html`, `.htm` | `text/html` |
| `.css` | `text/css` |
| `.js`, `.mjs` | `text/javascript` |
| `.json`, `.canvas` (Obsidian canvas) | `application/json` |
| `.csv` | `text/csv` |
| `.txt`, `.log` | `text/plain` |
| `.svg` | `image/svg+xml` |
| `.xml` | `application/xml` |
| `.yaml`, `.yml` | `application/yaml` |
| `.py`, `.ts`, `.sh` and other code | `text/plain` |
| `.png`, `.jpg`/`.jpeg`, `.gif`, `.webp` | `image/png`, `image/jpeg`, `image/gif`, `image/webp` (binary) |
| `.pdf` | `application/pdf` (binary) |

Check the response: `mimeType` should match what you sent (not `application/vnd.google-apps.document`). Keep the `id` and `viewUrl`.

**Replacing a file.** The connector can't overwrite contents. Search the target folder for the same title (`title = '<name>' and parentId = '<folder id>'`, following page tokens), call `trash_file` on each match, then create the new file. Trashed files stay recoverable in Drive's trash for 30 days.

## 4. HTML pages

- A page that loads its own CSS or JS files by relative path (`<script src="app.js">`) only works if those files sit next to it. Upload them into the same folder with the same names, or better, inline them so the page is a single self-contained file. Pages that load libraries from a CDN keep working wherever there's internet access, but not offline (for example inside Obsidian).
- Drive's web preview doesn't run JavaScript; it shows the page source or offers a download. Tell the user the page runs when opened from their synced Drive folder in a browser, or inside Obsidian with an HTML plugin that has scripts enabled.

## 5. Size and cost

Every byte passes through the conversation as tool input, so large files are slow and use a lot of the user's usage. Text files up to a few hundred KB are fine. Warn before uploading bigger files or many images, and prefer leaving out redundant copies (for example, a raw JSON dump when a readable markdown version is also being saved).

## 6. Report

List each saved file with its full Drive path and `viewUrl`, note any file that replaced an older one or got a ` (2)` suffix, and remind the user that Drive for desktop will sync it to their computer. When called by another skill, also hand back the folder and file IDs so it can save more files without searching again.

## Notes for skills that call this one

Pass the destination path, the list of files (local paths or content), and the conflict rule (`replace` for regenerated output). This skill returns IDs and links. Calling skills keep their own decisions about naming and folder layout; this skill only does the Drive mechanics.
