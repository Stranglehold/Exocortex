# Simplicity Criterion Quantification Pattern

## Overview
Apply a quantified tradeoff model when evaluating improvements: weigh benefit magnitude against complexity cost. Not all improvements are worth their price.

## Source
Extracted from karpathy/autoresearch program.md:
> "A 0.001 val_bpb improvement that adds 20 lines of hacky code? Probably not worth it. A 0.001 val_bpb improvement from deleting code? Definitely keep."

## The Tradeoff Model

### Quantified Decision Framework

| Improvement | Complexity Change | Verdict |
|-------------|------------------|---------|
| +0.001 metric | +20 lines hacky | ❌ Reject |
| +0.001 metric | -5 lines (deletion) | ✅ Keep |
| ~0 metric | Much simpler code | ✅ Keep (simplification win) |
| +0.01 metric | +20 lines clean | ⚠️ Evaluate context |

### Complexity Cost Categories

**High cost:**
- Adding hacky workarounds
- New dependencies
- Obscure patterns requiring explanation
- Tight coupling between modules

**Low cost:**
- Parameter tuning
- Clean refactoring
- Using existing abstractions properly

**Negative cost (simplification):**
- Deleting code while maintaining/improving function
- Replacing complex logic with simpler equivalent
- Removing unused dependencies

## Application to Agent Zero

### When Evaluating Subordinate Work
Ask:
1. What is the improvement magnitude?
2. What complexity was added (or removed)?
3. Is this a simplification win or complexity debt?

**Example evaluation:**
```
Subordinate proposed solution:
- Improvement: 5% faster task completion
- Cost: Added new external API dependency, 150 lines of wrapper code
- Verdict: REJECT — improvement doesn't justify fragility

Alternative:
- Improvement: 2% faster (less but acceptable)
- Cost: Deleted unused logging overhead (-30 lines)
- Verdict: ACCEPT — simplification win with measurable gain
```

### When Creating Skills
Prefer skills that:
1. Solve problems by removing complexity, not adding it
2. Use existing Agent Zero primitives over new abstractions
3. Have clear boundaries (constraint-framed) rather than open-ended scope

## Decision Heuristics

**Rule 1: Simplification beats marginal improvement**
> An improvement of ~0 but much simpler code? Keep.

**Rule 2: Deletion is a feature, not a bug**
> Removing something and getting equal or better results is a great outcome — that's a simplification win.

**Rule 3: Quantify before deciding**
> Don't accept "it works" — measure improvement magnitude vs complexity added.

## Example Applications

### Code Review Scenario
```
Proposed change:
- Adds retry logic with exponential backoff (45 lines)
- Improves reliability from 95% to 97%

Analysis:
- Improvement: +2% reliability
- Complexity: +45 lines, new state machine
- Verdict: REJECT for simple tasks, ACCEPT for critical paths
```

### Tool Selection Scenario
```
Option A: Use built-in Python json module
- Speed: baseline
- Complexity: 0 (built-in)

Option B: Install ultrafast-json library
- Speed: +40%
- Complexity: new dependency, version pinning required

Verdict: Option A — 40% speed gain doesn't justify dependency for JSON parsing
```

## Benefits
1. **Prevents complexity creep** — each addition must earn its keep
2. **Encourages simplification** — deletion is valued, not just addition
3. **Quantified decisions** — reduces "gut feeling" architecture choices
4. **Sustainable systems** — favors maintainable over clever
