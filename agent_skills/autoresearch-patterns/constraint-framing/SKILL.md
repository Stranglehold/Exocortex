# Constraint Framing Pattern

## Overview
Explicitly separate fixed constraints from variable boundaries when framing tasks for autonomous agents. This reduces search space and focuses optimization effort.

## Source
Extracted from karpathy/autoresearch architecture where `prepare.py` (fixed) vs `train.py` (variable) creates clear boundaries.

## Pattern Structure

### Fixed Constraints (Read-Only)
These are constants that define the problem space:
```python
# prepare.py - FIXED
time_budget = 300        # seconds per experiment
max_seq_len = 2048       # context length
metric = "val_bpb"       # single optimization target
```

### Variable Boundaries (Agent Can Modify)
These are the knobs available for experimentation:
```python
# train.py - VARIABLE
architecture, hyperparameters, optimizer, batch_size, model_size
```

## Application to Agent Zero

### When Delegating Tasks
Frame constraints explicitly:

**Bad (open-ended):**
> "Improve this code's performance"

**Good (constrained framing):**
> "You have 10 minutes. You can modify the algorithm but not add dependencies. Success metric: reduce runtime by >20% while keeping memory under 500MB."

### When Creating Skills
Define what the skill fixes vs varies:
- **Fixed:** Input format, output schema, time budget
- **Variable:** Internal logic, heuristics, approach selection

## Decision Framework

| Question | Answer |
|----------|--------|
| What is fixed? | Time, resources, interface contracts |
| What can vary? | Implementation details, internal state |
| Success metric? | Single primary metric when possible |
| Hard vs soft constraints? | Hard: must satisfy. Soft: tradeoff acceptable |

## Example Application

**Task:** Debug a failing test suite

**Constraint-framed delegation:**
```
Fixed:
- Time budget: 15 minutes
- Can modify: test code, mock data
- Cannot modify: production code under test
- Success metric: all tests pass, no new failures introduced

Variable:
- Which tests to fix first
- Whether to add mocks or fix real issues
- Approach: isolation vs batch fixing
```

## Benefits
1. **Reduced search space** — agent doesn't waste cycles on constrained dimensions
2. **Clearer success criteria** — single metric beats vague "improve quality"
3. **Easier evaluation** — fixed constraints make comparison straightforward
4. **Faster iteration** — focused optimization converges quicker
