# reasoning-playbook

Structured reasoning frameworks for deeper analysis, decision-making, and problem-solving.

## What It Does

A playbook of 8 thinking frameworks — first principles decomposition, pre-mortems, trade-off matrices, steel-manning, second-order thinking, and more. When you ask Claude to "think deeply" or tackle a complex problem, it selects the right framework and shows its work step by step.

## Platform

- **claude.ai**
- **Claude Code**
- **Cursor**
- Adaptable to other agentic frameworks

## Included Patterns

| Pattern | Best For |
|---------|----------|
| First Principles Decomposition | Re-examining assumptions, simplifying over-engineered solutions |
| Inversion (Pre-Mortem) | Identifying blind spots in plans and strategies |
| Trade-off Matrix | Choosing between options with competing dimensions |
| Steel-Manning | Fair evaluation of controversial or unfamiliar approaches |
| Second-Order Thinking | Policy, process, and design decisions with downstream effects |
| Constraints-First | System design and resource allocation |
| Root Cause Analysis | Debugging failures and recurring problems |
| Decision Journal | High-stakes decisions that need documented reasoning |

## Trigger Phrases

```
"Think deeply about..."
"Analyze this critically"
"Break this down for me"
"What are the trade-offs?"
"Think harder about this"
"Don't give me the obvious answer"
"Help me decide between..."
"What could go wrong with this plan?"
```

## Install

```bash
# Via npx
npx skillforge install thinking-tools/reasoning-playbook

# From the skillforge repo
./install.sh thinking-tools/reasoning-playbook

# Or direct download
curl -sL -o SKILL.md \
  https://raw.githubusercontent.com/gouthi/skillforge/main/skills/thinking-tools/reasoning-playbook/SKILL.md
```

## Example

**User:** "We're debating whether to build our ML pipeline on AWS Step Functions vs Airflow. Help me think through this."

**Claude (with reasoning-playbook skill):**
- Selects **Trade-off Matrix** + **Constraints-First Thinking**
- Maps hard constraints (AWS-only infra, team familiarity, budget)
- Scores both options on: operational overhead, debugging, cost, ecosystem lock-in, scaling
- Applies **Second-Order Thinking** to flag long-term implications
- Ends with a clear recommendation and what it trades away
