# Autoresearch Patterns Collection

## Overview

This collection extracts transferable architectural patterns from [karpathy/autoresearch](https://github.com/karpathy/autoresearch) — a framework for autonomous LLM training experimentation.

While autoresearch is domain-specific (ML research), the underlying patterns for framing autonomous experimentation are general-purpose and applicable to Agent Zero's task automation workflows.

---

## Pattern Index

| Skill | Description | Use When |
|-------|-------------|----------|
| [constraint-framing](./constraint-framing/) | Explicitly separate fixed constraints from variable boundaries when framing tasks | Delegating tasks, creating skills, setting up experiments |
| [simplicity-criterion-quantification](./simplicity-criterion-quantification/) | Apply quantified tradeoff model: weigh benefit magnitude against complexity cost | Evaluating improvements, code review, tool selection |
| [branch-based-experiment-isolation](./branch-based-experiment-isolation/) | Use git branches as state containers for reversible, traceable experimentation | Iterative tasks (debugging, optimization), feature development |
| [results-tracking-including-failures](./results-tracking-including-failures/) | Track all attempts including failures as first-class data points | Any iterative work where learning from failures matters |

---

## Pattern Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                    TASK FRAMING                             │
│              (constraint-framing)                           │
│  Fixed: time, resources, interface                          │
│  Variable: implementation details                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  EXPERIMENT LOOP                            │
│        (branch-based-experiment-isolation)                  │
│  Branch = research state, commits = reversible checkpoints  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   EVALUATION                                │
│    (simplicity-criterion-quantification)                    │
│  Improvement magnitude vs complexity cost tradeoff          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   TRACKING                                  │
│      (results-tracking-including-failures)                  │
│  All attempts logged, failures are data                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Source Attribution

Extracted from karpathy/autoresearch:
- `prepare.py` — fixed constraints (TIME_BUDGET=300s, MAX_SEQ_LEN=2048)
- `train.py` — variable boundaries (architecture, hyperparameters, optimizer)
- `program.md` — agent instructions and experiment loop design

Key insight: autoresearch works because it reduces infinite search space to:
1. Fixed time per iteration (5 min)
2. Single file modification (`train.py`)
3. One metric (`val_bpb`, lower better)
4. Clear success/failure criteria

---

## Usage in Agent Zero

### Loading Individual Skills
```json
{
  "tool_name": "skills_tool",
  "tool_args": {
    "action": "load",
    "skill_name": "autoresearch-patterns/constraint-framing"
  }
}
```

### When to Apply Each Pattern

**Constraint Framing:**
- Before delegating any task to subordinates
- When creating new skills (define fixed vs variable)
- Setting up experiments or iterative work

**Simplicity Criterion Quantification:**
- Evaluating subordinate work quality
- Deciding whether to adopt a tool/skill
- Code review scenarios

**Branch-Based Experiment Isolation:**
- Debugging sessions with multiple hypotheses
- Performance optimization attempts
- Feature development with uncertain approach

**Results Tracking Including Failures:**
- Any iterative task where learning matters
- When success rate is as important as success
- Building institutional knowledge from attempts

---

## Verification

Run this to verify all skills are properly created:
```bash
find /a0/skills/autoresearch-patterns -name "SKILL.md" -exec wc -c {} \;
```

Expected output:
```
2378 /a0/skills/autoresearch-patterns/constraint-framing/SKILL.md
4452 /a0/skills/autoresearch-patterns/branch-based-experiment-isolation/SKILL.md  
3397 /a0/skills/autoresearch-patterns/simplicity-criterion-quantification/SKILL.md
4897 /a0/skills/autoresearch-patterns/results-tracking-including-failures/SKILL.md
```
