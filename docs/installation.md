# Installation Guide

Multiple ways to install skills from Skillforge, depending on your needs.

## Method 1: npx (Recommended)

No clone needed — installs directly from GitHub:

```bash
# Install a specific skill
npx skillforge install obsidian/obsidian-save-cloud

# Install all skills in a group
npx skillforge install thinking-tools

# Install everything
npx skillforge install --all

# Install to Cursor instead of Claude Code
npx skillforge install --platform cursor thinking-tools

# List available skills
npx skillforge list
```

**Pros:** Zero setup, works anywhere with Node.js, auto-detects platform directory.

## Method 2: Install Script

Clone the repo, then install specific skills:

```bash
git clone https://github.com/gouthi/skillforge.git
cd skillforge

# Install a specific skill
./install.sh obsidian/obsidian-save-cloud

# Install all skills in a group
./install.sh thinking-tools

# List available skills
./install.sh --list

# Install everything
./install.sh --all

# Install to Cursor's skill directory
./install.sh --platform cursor thinking-tools

# Show claude.ai upload instructions
./install.sh --platform claude-ai

# Custom target directory
SKILLS_INSTALL_DIR=~/my-skills ./install.sh thinking-tools
```

Default install location depends on platform:
- `claude-code` → `~/.claude/skills/`
- `cursor` → `~/.cursor/skills/`

**Pros:** Simple, no git knowledge needed, customizable target directory.

## Method 3: Sparse Checkout (Developers)

Clone only the skills you need — nothing else gets downloaded:

```bash
git clone --filter=blob:none --sparse https://github.com/gouthi/skillforge.git
cd skillforge
git sparse-checkout add skills/obsidian/obsidian-save-cloud skills/thinking-tools/reasoning-playbook
```

Add more skills later:

```bash
git sparse-checkout add skills/obsidian/some-other-skill
```

See what you've checked out:

```bash
git sparse-checkout list
```

**Pros:** Efficient, version-controlled, easy to pull updates.

## Method 4: Remote One-Liner (No clone needed)

Install a skill directly without cloning the repo:

```bash
# Single skill
curl -sL https://github.com/gouthi/skillforge/archive/main.tar.gz \
  | tar xz --strip-components=3 -C ~/.claude/skills/ \
  "skillforge-main/skills/obsidian/obsidian-save-cloud"
```

**Pros:** Zero setup, works anywhere with curl.

## Method 5: Direct Download via Raw URLs

Grab individual files:

```bash
# Just the SKILL.md
curl -sL -o SKILL.md \
  https://raw.githubusercontent.com/gouthi/skillforge/main/skills/thinking-tools/reasoning-playbook/SKILL.md
```

**Pros:** Zero dependencies.
**Cons:** Manual; you manage individual files yourself.

## Method 6: GitHub Releases

When available, individual skill archives are published on the [Releases](https://github.com/gouthi/skillforge/releases) page:

```
skillforge-v1.0.0.tar.gz                    # full bundle
skill-obsidian-save-cloud-v1.0.0.tar.gz     # individual
skill-reasoning-playbook-v1.0.0.tar.gz      # individual
```

Download only what you need from the Releases tab.

**Pros:** Versioned, clean, no git required.

## Method 7: Git Submodule (Embedding in your own repo)

```bash
git submodule add https://github.com/gouthi/skillforge.git vendor/skillforge
```

Then symlink or copy specific skills into your skill directory.

## Where to Put Skills

| Platform | Default Location | Install Method |
|----------|-----------------|----------------|
| Claude Code | `~/.claude/skills/` or project-level `.claude/skills/` | `npx skillforge install` or `./install.sh` |
| Cursor | `~/.cursor/skills/` or project-level `.cursor/skills/` | `npx skillforge install --platform cursor` or `./install.sh --platform cursor` |
| claude.ai | Upload via Settings → Features → Skills | `npx skillforge --platform claude-ai` for instructions |
| Other frameworks | Varies — consult your framework's docs | Use `SKILLS_INSTALL_DIR` env var or `--dir` flag |
