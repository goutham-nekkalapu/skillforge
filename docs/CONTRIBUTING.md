# Contributing to Skillforge

Thanks for your interest in contributing! Here's how to add a new skill or improve an existing one.

## Adding a New Skill

### 1. Choose or create a group

Skills are organized into groups under `skills/`. Check the existing groups first:

```
skills/
├── google-drive/          # Google Drive file skills
├── learning/              # Study and learning skills
├── obsidian/              # Obsidian vault integration skills
├── prompts/               # Prompt engineering and extraction skills
└── thinking-tools/        # Reasoning, analysis, and communication skills
```

If your skill fits an existing group, add it there. If it doesn't fit, propose a new group in your PR description.

### 2. Create the skill folder

```bash
mkdir -p skills/<group>/your-skill-name/{references,examples}
```

For example:

```bash
mkdir -p skills/obsidian/obsidian-local-save/{references,examples}
```

### 3. Write the SKILL.md

Every skill needs a `SKILL.md` with YAML frontmatter:

```markdown
---
name: your-skill-name
description: >
  What this skill does and when it should trigger. Be specific about trigger
  phrases and contexts. Err on the side of being "pushy" in the description —
  skills tend to under-trigger rather than over-trigger.
---

# your-skill-name

Instructions for Claude on how to execute this skill.
```

Guidelines:
- Keep SKILL.md under 500 lines
- Use `references/` for large supporting docs (Claude reads these on demand)
- Include clear trigger conditions so the skill activates reliably
- End with error handling guidance

### 4. Write the README.md

Each skill should have its own README with:
- What it does (one paragraph)
- Platform compatibility (claude.ai, Claude Code, Cursor, other)
- Setup/prerequisites
- Example trigger phrases
- Install command using the new grouped path

### 5. Test it

- Load the SKILL.md into a conversation and try various trigger phrases
- Test edge cases (missing prerequisites, ambiguous requests)
- Verify it doesn't activate for unrelated queries

### 6. Submit a PR

- One skill per PR (unless they're closely related)
- Update the root README catalog table with the grouped path
- If creating a new group, add a group-level `README.md` listing its skills
- Include example interactions in your PR description

## Improving an Existing Skill

- File an issue first to discuss the change
- Keep backward compatibility — don't break existing trigger patterns
- Test before and after

## Skill Quality Checklist

- [ ] SKILL.md has proper YAML frontmatter (name + description)
- [ ] Description includes specific trigger phrases and contexts
- [ ] README.md exists with install instructions
- [ ] Skill is inside a group directory (`skills/<group>/<skill>/`)
- [ ] Tested on target platform(s)
- [ ] Root README catalog table updated
- [ ] Group README updated (or created for new groups)
- [ ] No sensitive or proprietary content included
