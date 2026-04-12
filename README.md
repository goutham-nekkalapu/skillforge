# 🔨 Skillforge

A curated collection of reusable AI skills for **claude.ai**, **Claude Code**, **Cursor**, and other agentic frameworks.

Each skill is a self-contained folder with a `SKILL.md` definition and optional supporting files. Install one skill or all of them — your choice.

## Skills Catalog

| Skill | Platform | Description |
|-------|----------|-------------|
| [obsidian-save-cloud](skills/obsidian/obsidian-save-cloud/) | claude.ai | Save conversation content to an Obsidian vault on Google Drive |
| [thinking-patterns](skills/thinking-patterns/thinking-patterns/) | Claude Code / claude.ai / Cursor | Structured thinking and reasoning patterns for deeper analysis |

## Quick Start

### Install a specific skill

**Option A — npx (easiest)**

```bash
npx skillforge install obsidian/obsidian-save-cloud
npx skillforge install thinking-patterns            # installs all skills in the group
```

**Option B — Install script**

```bash
git clone https://github.com/gouthi/skillforge.git
cd skillforge
./install.sh obsidian/obsidian-save-cloud thinking-patterns
./install.sh --platform cursor thinking-patterns    # install to Cursor's skill dir
```

**Option C — Sparse checkout (developers)**

```bash
git clone --filter=blob:none --sparse https://github.com/gouthi/skillforge.git
cd skillforge
git sparse-checkout add skills/obsidian/obsidian-save-cloud
```

**Option D — Direct download (single file)**

```bash
curl -sL -o SKILL.md \
  https://raw.githubusercontent.com/gouthi/skillforge/main/skills/obsidian/obsidian-save-cloud/SKILL.md
```

See [docs/installation.md](docs/installation.md) for all installation methods including remote one-liners and GitHub Releases.

## Repo Structure

```
skillforge/
├── skills/
│   ├── obsidian/                    # Group: Obsidian-related skills
│   │   └── obsidian-save-cloud/     # Save notes to Obsidian via Google Drive
│   │       ├── SKILL.md
│   │       └── README.md
│   └── thinking-patterns/           # Group: Structured reasoning patterns
│       └── thinking-patterns/       # Core thinking patterns skill
│           ├── SKILL.md
│           └── README.md
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
