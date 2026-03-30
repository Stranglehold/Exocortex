# Results Tracking Including Failures Pattern

## Overview
Track all attempts including failures as first-class data points. The pattern of what doesn't work is as valuable as what does.

## Source
Extracted from karpathy/autoresearch results.tsv schema:
```
commit	val_bpb	memory_gb	status	description
a1b2c3d	0.997900	44.0	keep	baseline
b2c3d4e	0.993200	44.2	keep	increase LR to 0.04
c3d4e5f	1.005000	44.0	discard	switch to GeLU activation
d4e5f6g	0.000000	0.0	crash	double model width (OOM)
```

Note: Crashes are logged with `val_bpb: 0.0` — they're data points too.

## Pattern Structure

### Results Schema Design

| Column | Type | Purpose |
|--------|------|----------|
| commit/hash | string | Traceability to code state |
| metric_value | float | Primary success measure (0.0 for crashes) |
| resource_usage | float | Secondary constraint (memory, time, etc.) |
| status | enum | `keep`, `discard`, or `crash` |
| description | string | Human-readable hypothesis/attempt |

### Status Categories

**Keep:**
- Metric improved over baseline
- Worth advancing the branch/state

**Discard:**
- Metric equal or worse than baseline  
- Hypothesis not validated, but ran cleanly

**Crash:**
- Execution failed (OOM, exception, timeout)
- Still valuable data — tells you what's broken

## Application to Agent Zero

### When Running Iterative Tasks

Create a results log tracking all attempts:

```python
# Example: Debugging session results tracking
results = [
    {"attempt": 1, "hypothesis": "Increase timeout", "status": "discard", "notes": "Still times out at 30s"},
    {"attempt": 2, "hypothesis": "Add retry logic", "status": "crash", "notes": "Recursion depth exceeded"},
    {"attempt": 3, "hypothesis": "Use iterative approach", "status": "keep", "notes": "Works with max_depth=100"},
]
```

### When Delegating to Subordinates

Require results tracking in delegation:

**Delegation prompt:**
```
Track all your attempts in a results log:
- What you tried (hypothesis)
- Whether it worked, failed, or crashed
- Key observations from each attempt

Even crashes are valuable — they tell us what's broken.
```

## Benefits of Tracking Failures

1. **Pattern recognition** — Multiple similar failures reveal systemic issues
2. **Avoid repetition** — Don't retry known-failing approaches
3. **Learning signal** — What doesn't work narrows the search space
4. **Debugging trail** — Crash patterns point to root causes
5. **Honest assessment** — Success rate matters, not just successes

## Example Applications

### Code Optimization Session
```
Results log:
┌─────────┬──────────────────────────────┬─────────┬─────────────────────────────┐
│ Attempt │ Hypothesis                   │ Status  │ Notes                       │
├─────────┼──────────────────────────────┼─────────┼─────────────────────────────┤
│   1     │ Add database index           │ KEEP    │ +15% speedup                │
│   2     │ Switch to async queries      │ CRASH   │ OOM error, too many awaits  │
│   3     │ Add result caching (60s TTL) │ KEEP    │ +40% more speedup           │
│   4     │ Reduce N+1 with select_rel.  │ KEEP    │ +25% additional             │
│   5     │ Use connection pooling       │ DISCARD │ No measurable improvement   │
└─────────┴──────────────────────────────┴─────────┴─────────────────────────────┘

Analysis:
- Success rate: 3/5 = 60%
- Crashes revealed memory constraint (async too aggressive)
- Discards show diminishing returns on optimization
```

### Feature Development Session
```
Results log:
┌─────────┬──────────────────────────────┬─────────┬─────────────────────────────┐
│ Attempt │ Hypothesis                   │ Status  │ Notes                       │
├─────────┼──────────────────────────────┼─────────┼─────────────────────────────┤
│   1     │ Add filter UI component      │ KEEP    │ Works as expected           │
│   2     │ Connect to backend query     │ CRASH   │ Breaks pagination logic     │
│   3     │ Refactor query builder first │ KEEP    │ Foundation laid correctly   │
│   4     │ Re-add filter connection     │ KEEP    │ Works now with refactored base│
└─────────┴──────────────────────────────┴─────────┴─────────────────────────────┘

Analysis:
- Attempt 2 crash revealed hidden coupling in query builder
- Attempt 3 was necessary prerequisite (not wasted effort)
- Total: 4 attempts, 1 crash, 0 discards = clean learning path
```

## Integration with Other Patterns

**With Branch-Based Experiment Isolation:**
- Git history = code changes tried
- Results log = outcomes of each change
- Together they form complete experiment record

**With Constraint Framing:**
- Fixed: Results schema, status categories
- Variable: What attempts to make, order of exploration

## Key Insight

> "The pattern of what doesn't work is as valuable as what does."

Failures aren't wasted effort — they're data that narrows the search space and reveals constraints.
