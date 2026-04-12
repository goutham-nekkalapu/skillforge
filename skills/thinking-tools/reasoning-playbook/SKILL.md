---
name: reasoning-playbook
description: >
  Structured thinking and reasoning patterns for deeper analysis, decision-making, and
  problem-solving. Use this skill whenever the user asks to "think deeply", "analyze critically",
  "reason through", "break down", "think step by step", or when tackling complex problems that
  benefit from structured reasoning frameworks. Also trigger for architecture decisions, trade-off
  analysis, root cause analysis, strategic planning, debugging complex issues, or any request
  where the user wants more rigorous thinking rather than a quick answer. Works in claude.ai and
  Claude Code. If the user says "think harder", "go deeper", "be more rigorous", or "don't just
  give me the obvious answer", this skill should activate.
---

# reasoning-playbook

Structured reasoning frameworks for deeper analysis.

## When to Use

Activate this skill when:
- The user asks for deep/critical/rigorous thinking
- A problem has multiple competing trade-offs
- Architecture or design decisions need evaluation
- Root cause analysis is needed
- The user is making a high-stakes decision
- A question has non-obvious second-order effects
- The user says "think harder" or "go deeper"

## Core Thinking Patterns

### 1. First Principles Decomposition

Break a problem down to its fundamental truths, then build up from there.

**When to use:** The user is stuck in conventional thinking, or a solution feels
over-engineered and needs to be re-examined from scratch.

**Structure:**
```
1. State the problem clearly
2. List assumptions being made
3. Challenge each assumption — which are actually true vs inherited?
4. Identify the fundamental constraints (physics, math, hard requirements)
5. Rebuild the solution from only the verified constraints
```

**Example prompt:** "Should we use a microservices architecture?"
- Don't start with "microservices vs monolith" — start with what the system actually needs:
  team size, deployment frequency, scaling dimensions, data coupling.

### 2. Inversion (Pre-Mortem)

Instead of asking "how do we succeed?", ask "how could this fail?" then work backward.

**When to use:** Evaluating a plan, architecture, strategy, or decision where blind spots
are the real risk.

**Structure:**
```
1. Assume the project/decision has failed spectacularly
2. List all plausible reasons it failed
3. Group by: within our control vs external
4. For each controllable failure mode, define a mitigation
5. Rank by likelihood × impact
```

### 3. Trade-off Matrix

Explicitly map the dimensions that matter and how each option scores.

**When to use:** Choosing between 2+ options where no single option dominates on all dimensions.

**Structure:**
```
1. List all options under consideration
2. Identify the evaluation dimensions (cost, speed, quality, risk, maintainability, etc.)
3. Weight the dimensions by importance to this specific context
4. Score each option on each dimension (use relative scoring, not absolute)
5. Note where scores are uncertain and what would change the answer
6. State the recommendation with explicit acknowledgment of what you're trading away
```

### 4. Steel-Manning

Before criticizing an idea, construct the strongest possible version of it.

**When to use:** The user is evaluating a controversial approach, comparing philosophies,
or dismissing something too quickly.

**Structure:**
```
1. State the idea as its strongest proponent would
2. Identify the contexts where this idea genuinely works best
3. Acknowledge the real strengths
4. Only then: identify the specific conditions where it breaks down
5. Conclude with a nuanced position rather than a binary judgment
```

### 5. Second-Order Thinking

Go beyond "what happens next?" to "and then what happens after that?"

**When to use:** Policy decisions, system design choices, process changes — anything
where the downstream effects matter more than the immediate ones.

**Structure:**
```
1. State the proposed action
2. First-order effects (immediate, obvious consequences)
3. Second-order effects (reactions to those consequences)
4. Third-order effects (long-term systemic shifts)
5. Identify feedback loops (positive or negative)
6. Flag any irreversible consequences
```

### 6. Constraints-First Thinking

Start by mapping what you can't change, then find the solution space within those boundaries.

**When to use:** System design, resource allocation, debugging — any situation where
the solution space is bounded.

**Structure:**
```
1. Hard constraints (non-negotiable: budget, deadlines, compliance, physics)
2. Soft constraints (negotiable with effort: team skills, existing tech, conventions)
3. Preferences (nice-to-have, can be dropped)
4. Define the solution space that satisfies all hard constraints
5. Optimize within that space for soft constraints and preferences
```

### 7. Root Cause Analysis (5 Whys + Fishbone)

Drill past symptoms to the actual cause.

**When to use:** Something went wrong and the obvious explanation feels too shallow.
Debugging production issues, project failures, recurring problems.

**Structure:**
```
1. State the symptom clearly
2. Ask "why?" — and answer honestly
3. For each answer, ask "why?" again (up to 5 levels)
4. At each level, check: am I describing a symptom or a cause?
5. Map contributing factors: People, Process, Technology, Environment
6. Identify the deepest actionable cause
```

### 8. Decision Journal Pattern

For high-stakes decisions, document the reasoning *before* the outcome is known.

**When to use:** The user is about to make a big decision and wants to think clearly
about it, or wants to build a track record of decision quality.

**Structure:**
```
1. The decision to be made
2. What I know (facts, data)
3. What I don't know (uncertainties, assumptions)
4. What I expect to happen and why (prediction + reasoning)
5. What would change my mind (pre-defined criteria)
6. The decision and the primary reason
```

## How to Apply

When a user presents a complex problem, the skill should:

1. **Identify complexity** — Is this a problem that benefits from structured thinking, or is
   a direct answer better? Not everything needs a framework.
2. **Select 1-2 patterns** — Don't apply all patterns to every problem. Pick the most relevant.
3. **Show your work** — Walk through the framework explicitly so the user can see the reasoning,
   challenge it, and learn the pattern for themselves.
4. **End with a clear recommendation** — Frameworks are tools, not substitutes for a conclusion.
   Always close with "Given the above, I'd recommend X because Y."

## Anti-Patterns to Avoid

- **Framework theater** — Applying a framework for show without it changing the answer
- **Analysis paralysis** — Using structured thinking as an excuse to avoid committing to a position
- **Over-abstracting** — If the user asked a simple question, answer it simply
- **Missing the emotional context** — Sometimes the user needs validation or support, not a matrix
