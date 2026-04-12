# Skill Authoring Guide

How to write effective skills for the Skillforge collection.

## Anatomy of a Skill

Skills live inside group directories under `skills/`:

```
skills/
├── <group>/                  # Logical grouping (e.g., obsidian, thinking-patterns)
│   ├── README.md             # Group overview listing its skills
│   └── <skill-name>/         # Individual skill
│       ├── SKILL.md          # Required — the skill definition the agent reads
│       ├── README.md         # Required — human-facing docs
│       ├── references/       # Optional — large docs loaded on demand
│       ├── examples/         # Optional — usage demos
│       └── assets/           # Optional — templates, configs, etc.
```

## SKILL.md Structure

### Frontmatter (Required)

```yaml
---
name: skill-name
description: >
  What this skill does and when to use it. Include trigger phrases.
---
```

The `description` field is the primary triggering mechanism. Claude decides whether to
load a skill based on this text, so make it specific and slightly "pushy."

### Body

The body is standard markdown with instructions for Claude. Think of it as a runbook
that Claude follows when the skill is activated.

## Writing Good Descriptions

The description should answer: "When should the agent reach for this skill?"

**Too vague:**
```yaml
description: Helps with code review.
```

**Good:**
```yaml
description: >
  Security-focused code review checklist for Python, FastAPI, and AWS Lambda.
  Use when the user asks to "review my code", "check for vulnerabilities",
  "security audit", or shares code and asks "is this safe?" Also trigger when
  the user mentions OWASP, PII handling, or injection attacks in the context
  of code they're writing.
```

## Progressive Disclosure

Skills use a three-level loading system:

1. **Metadata** (name + description) — always in context (~100 words)
2. **SKILL.md body** — loaded when skill triggers (<500 lines ideal)
3. **References** — loaded on demand from `references/` folder (unlimited size)

Keep the main SKILL.md focused. Move large reference material (API docs, checklists,
lookup tables) into `references/` and point to them from SKILL.md.

## Platform Compatibility

Note which platforms your skill targets:

| Platform | Capabilities |
|----------|-------------|
| claude.ai | MCP connectors, file creation, web search, artifacts |
| Claude Code | CLI access, filesystem, subagents, `claude -p` |
| Cursor | Filesystem, terminal, MCP servers, multi-file editing |
| Both/All | Core reasoning, markdown generation |

If a skill only works on one platform, say so clearly in the SKILL.md and README.

## Testing Your Skill

1. Load the SKILL.md into a conversation
2. Try trigger phrases — does it activate?
3. Try unrelated queries — does it stay quiet?
4. Test edge cases and error paths
5. Have someone else try it without explanation
