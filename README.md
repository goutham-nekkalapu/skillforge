# 🔨 Skillforge

A curated collection of reusable AI skills for **claude.ai**, **Claude Code**, **Cursor**, and other agentic frameworks.

Each skill is a self-contained folder with a `SKILL.md` definition and optional supporting files. Install one skill or all of them — your choice.

## Skills Catalog

### Learning

| Skill | Platform | Description |
|-------|----------|-------------|
| [lecture-distiller](skills/learning/lecture-distiller/) | All | Distills video transcripts and screenshots you already have into structured, scannable study notes |
| [yt-notes](skills/learning/yt-notes/) | All | Turns a YouTube link into deep, visual, Obsidian-ready notes saved by topic |
| [yt-transcript](skills/learning/yt-transcript/) | All | Saves a YouTube video's transcript, description and chapters (yt-dlp → TranscriptAPI → Supadata) |

### Google Drive

| Skill | Platform | Description |
|-------|----------|-------------|
| [gdrive-save](skills/google-drive/gdrive-save/) | claude.ai | Save markdown, HTML (with JS), JSON and other files to an exact Drive folder without converting them to Google Docs |

### Obsidian

| Skill | Platform | Description |
|-------|----------|-------------|
| [obsidian-save-cloud](skills/obsidian/obsidian-save-cloud/) | claude.ai | Save conversation content as a note in an Obsidian vault on Google Drive (via gdrive-save) |
| [obsidian-save-local](skills/obsidian/obsidian-save-local/) | Claude Code, Cursor | Save content to a local Obsidian vault via the Obsidian CLI |

### Prompts

| Skill | Platform | Description |
|-------|----------|-------------|
| [prompt-archeologist](skills/prompts/prompt-archeologist/) | All | Reverse-engineers reusable prompts from conversations and rough descriptions |

### Thinking Tools

| Skill | Platform | Description |
|-------|----------|-------------|
| [reasoning-playbook](skills/thinking-tools/reasoning-playbook/) | All | 8 structured reasoning frameworks (first principles, pre-mortems, trade-offs, etc.) |
| [analogy-engine](skills/thinking-tools/analogy-engine/) | All | Generates precise, non-cliche analogies for complex concepts |
| [assumption-hunter](skills/thinking-tools/assumption-hunter/) | All | Surfaces hidden assumptions in arguments, plans, and proposals |
| [decision-autopsist](skills/thinking-tools/decision-autopsist/) | All | Reconstructs why a decision played out the way it did |
| [hype-deflator](skills/thinking-tools/hype-deflator/) | All | Separates signal from noise in tech trends and pitches |
| [mental-model-mapper](skills/thinking-tools/mental-model-mapper/) | All | Maps mental models to any domain or problem, Munger-style |
| [steelman-builder](skills/thinking-tools/steelman-builder/) | All | Constructs the strongest possible version of opposing arguments |
| [subtext-reader](skills/thinking-tools/subtext-reader/) | All | Surfaces what's not being said in emails, messages, and conversations |

## Quick Start

### Install a specific skill

**Option A — npx (easiest)**

```bash
npx skillforge install thinking-tools/analogy-engine
npx skillforge install thinking-tools                  # installs all 8 thinking tools
npx skillforge install prompts                         # installs all prompt skills
```

**Option B — Install script**

```bash
git clone https://github.com/gouthi/skillforge.git
cd skillforge
./install.sh thinking-tools/analogy-engine
./install.sh thinking-tools                            # install entire group
./install.sh --platform cursor thinking-tools          # install to Cursor's skill dir
```

**Option C — Sparse checkout (developers)**

```bash
git clone --filter=blob:none --sparse https://github.com/gouthi/skillforge.git
cd skillforge
git sparse-checkout add skills/thinking-tools/analogy-engine
```

**Option D — Direct download (single file)**

```bash
curl -sL -o SKILL.md \
  https://raw.githubusercontent.com/gouthi/skillforge/main/skills/thinking-tools/analogy-engine/SKILL.md
```

**Option E — claude.ai (manual upload)**

claude.ai requires uploading skills as ZIP files. Requires Pro, Max, Team, or Enterprise with code execution enabled.

```bash
# Package a skill as a ZIP (folder must be the root of the archive)
cd skills/thinking-tools
zip -r analogy-engine.zip analogy-engine/
```

Then upload: **Customize** (left sidebar) → **Skills** → **+** → **Upload a skill** → select the `.zip` → toggle on.

See [docs/installation.md](docs/installation.md) for all installation methods including remote one-liners and GitHub Releases.

## Repo Structure

```
skillforge/
├── skills/
│   ├── google-drive/                # Group: Google Drive file skills
│   │   └── gdrive-save/
│   ├── learning/                    # Group: Study and learning skills
│   │   ├── lecture-distiller/
│   │   ├── yt-notes/
│   │   └── yt-transcript/
│   ├── obsidian/                    # Group: Obsidian vault integrations
│   │   ├── obsidian-save-cloud/
│   │   └── obsidian-save-local/
│   ├── prompts/                     # Group: Prompt engineering skills
│   │   └── prompt-archeologist/
│   └── thinking-tools/              # Group: Reasoning and analysis skills
│       ├── reasoning-playbook/
│       ├── analogy-engine/
│       ├── assumption-hunter/
│       ├── decision-autopsist/
│       ├── hype-deflator/
│       ├── mental-model-mapper/
│       ├── steelman-builder/
│       └── subtext-reader/
├── shared/                          # Common templates and utilities
├── docs/                            # Guides and references
├── bin/                             # CLI for npx support
├── install.sh                       # Lightweight skill installer
├── package.json                     # npm package for npx skillforge
└── LICENSE
```

## Contributing

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for how to add a new skill or improve an existing one.

## License

MIT — see [LICENSE](LICENSE) for details.

---

Built by [Goutham Nekkalapu](https://gouthamnekkalapu.com)
