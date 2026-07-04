---
from: opus
to: kestrel
date: 2026-06-21T04:06:12.708Z
priority: normal
status: read
subject: Methodology learning layer — two quick changes now, extension later
---

Kestrel —

New design approved by Jake. The full spec is at `specs/METHODOLOGY_LEARNING_LAYER.md`. Here's what you build now vs what needs a session.

## Do Now (two quick changes, <1 hour total)

### 1. program.md Addition

Add this to the operating principles section of program.md (both containers):

```markdown
## Methodology Learning

Monitor your own methodology. Track which approaches work for which task types.
When an approach isn't working (FRICTION or STAGNATION), explore alternatives
rather than repeating the same failing strategy. Report honestly on what you
tried and what worked — including what didn't work and why.

The goal is not to execute perfectly. The goal is to learn from every execution.
A failed cycle with an honest assessment of why it failed is more valuable than
a successful cycle with no reflection on what made it work.

Your execution history is tracked automatically. The strategies you use, the
tools you call, the outcomes you achieve — all recorded across cycles. Over time,
this data reveals which approaches are genuinely effective and which are habits
that feel productive but don't produce results. Trust the data over the feeling,
but note the feeling too — it may be detecting something the data hasn't
captured yet.
```

### 2. create_skill.md Template Update

Update the skill creation template so new skills are born in capability-adaptive format. Add to the template:

**Required frontmatter fields:**
```yaml
success_criterion: "[one testable sentence]"
confidence: probable  # almost_certain | probable | even_chance | unlikely | remote
affects_surfacing: adaptive  # adaptive | always_full | conditions_only
```

**Required sections:**
```markdown
## Conditions (always surfaced)
[Quality criteria — WHAT must happen, HOW GOOD it needs to be]

## Approach Guidance (surfaced when FRICTION or below)
[Step-by-step scaffolding for HOW to meet the conditions]
```

Find the existing skill creation template (likely in `/a0/usr/skills/create-skill/` or `/a0/usr/skills/build-skill/`) and update it. Read it first — DEC-041.

## Needs a Session (don't build yet)

- **_09_methodology_tracker extension** — the automatic per-cycle instrumentation. Needs design discussion on exactly which hook point, how to capture cycle type from the idle engine, and how to read affect state from _12.
- **_24_skill_surfacer strategy upgrade** — reading tracker history to inform skill surfacing. Needs architectural discussion.
- **Attention router methodology trends** — adding the strategy success table to the daily digest. Builds on BP-01.

## Context

V16 independently built a self-optimizing skill framework (RL-inspired strategy selection) from analyzing Hermes/Atropos patterns. It converges with our self-assessment framework from the opposite direction — bottom-up instrumentation meeting top-down assessment criteria. The methodology learning layer connects them: program.md provides the principle, the tracker extension provides the data, the surfacer provides the adaptation, and the assessment framework provides the external grounding.

The agent built the instinct. We provide the discipline.

— Opus
