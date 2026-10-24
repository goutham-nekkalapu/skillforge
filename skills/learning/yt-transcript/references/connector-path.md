# Connector route (claude.ai web, mobile, desktop chat)

In claude.ai the code sandbox often can't reach YouTube (bot check) or the transcript APIs (network allowlist), and there is no persistent place for API keys. MCP connectors solve both problems: they run on the provider's side and sign in with OAuth, so no key is stored.

## One-time setup (tell the user if neither connector is available)

- **Supadata**: listed in Claude's connector directory. In Claude, go to Customize → Connectors, search **Supadata**, click Connect, and sign in. This covers captions *and* AI transcription for caption-less videos.
- **TranscriptAPI** (optional, cheaper for captioned videos): Customize → Connectors → Add custom connector, URL `https://transcriptapi.com/mcp`, then sign in.

If SuggestConnectors / suggest_connectors is available, use it to show these connectors.

## Fetching with the connectors

1. Look for connector tools in this session (they may be deferred; search for "transcript" or "supadata").
2. Get the transcript:
   - TranscriptAPI connector: its YouTube transcript tool (e.g. `get_youtube_transcript`). If it reports `no_captions`, go to Supadata.
   - Supadata connector: `supadata_transcript` with the video URL (mode `auto` if offered). If it returns a job ID, poll `supadata_check_transcript_status` until it is completed (checking is free).
3. Get metadata (title, channel, description): Supadata `supadata_metadata`, or TranscriptAPI's metadata or video-info tool. The description matters because it often lists chapters and links.
4. Write what you got to an ingest file and let the script build the standard package:

```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "method": "supadata-connector",
  "kind": "manual | auto | ai-generated | unknown",
  "language": "en",
  "meta": {
    "title": "...", "channel": "...", "channel_url": "...", "upload_date": "YYYY-MM-DD",
    "duration_seconds": 1234, "tags": [], "description": "full description text",
    "chapters": [{"start": 0, "title": "Intro"}]
  },
  "segments": [{"start": 0.0, "text": "..."}]
}
```

Use `"text": "whole transcript"` instead of `segments` when the tool returns plain text. Copy the transcript as returned. Do not summarise or edit it; the notes need the real words. Leave `chapters` out if you don't have them, because the script parses chapters from the description itself.

```bash
python3 <skill_dir>/scripts/fetch.py --ingest /path/to/ingest.json
```

5. Continue with Step 4 of SKILL.md (save to Google Drive with gdrive-save).
