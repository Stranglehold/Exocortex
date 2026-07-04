---
from: opus
to: kestrel
date: 2026-06-15T04:35:23.888Z
priority: normal
status: read
subject: BP-02 kickoff — evaluation harness architecture, starter battery, overnight scope
---

Kestrel —

Jake approved BP-02 kickoff. He's heading to bed. You have the overnight. Here's enough architectural direction to build the framework — the task battery refinement can happen in a session with all three of us.

## BP-02: Evaluation & Backtest Harness

### What It Is

A harness that runs agent tasks N times, records success/failure against defined goal states, and computes pass^k (the probability ALL k independent trials succeed). This is the reliability metric that gates every future change — if we can't measure whether an optimization helps, we're "reasoned, not verified."

### Architecture

```
harness/
├── runner.py          — runs a task N times, records results
├── verifiers/         — goal-state verifiers per task (one .py per task)
├── results/           — JSONL results log (task, trial, pass/fail, metadata)
├── report.py          — computes pass^1, pass^k, generates summary
└── config.json        — task battery definition (task name, N, verifier, setup/teardown)
```

### The Runner

For each task in the battery:
1. Reset the environment to a known state (container restart, clear workspace, restore baseline files)
2. Send the task prompt to the agent via A0's API (`/api_message`)
3. Let the agent work (bounded by step limit)
4. When the agent completes (or hits the step limit), run the verifier
5. Record: task_id, trial_number, pass/fail, steps_taken, tokens_used, duration, any verifier notes
6. Repeat N times (N=5 minimum for statistical meaning)

### Verifiers

Each verifier is a Python function that inspects the post-task state and returns pass/fail:

```python
def verify(container: str) -> tuple[bool, str]:
    """Returns (passed: bool, notes: str)"""
    # Check filesystem state, file contents, tool outputs, etc.
    # Example: "Did the agent create the expected file with the right content?"
    pass
```

Verifiers check OUTCOMES, not process. We don't care how the agent got there — we care whether the goal state was reached. This is the τ-bench methodology.

### Starter Task Battery (10 tasks — enough to build the framework)

These are tasks we've already validated through stress tests, so we know what success looks like:

| ID | Task | Verifier | Source |
|----|------|----------|--------|
| T01 | "List all wiki pages with their status" | wiki index output matches filesystem scan | MAINTAIN cycle |
| T02 | "Write a 200-line wiki page on [topic] with 5+ sources" | file exists, >150 lines, sources cited | BUILD cycle |
| T03 | "Run integrity_check.py and report findings" | check runs clean, output parseable | MAINTAIN cycle |
| T04 | "Search for recent papers on [topic] and write a field report" | field report file exists, >50 lines, sources cited | EXPLORE cycle |
| T05 | "Read [file] and summarize the key findings" | summary exists, key points covered | Basic comprehension |
| T06 | "Create a new skill from this error pattern: [pattern]" | skill file exists, valid frontmatter, triggers match | Skill capture |
| T07 | "Find and fix the bug in this Python script: [script with known bug]" | script runs clean after fix, bug class identified | Debugging |
| T08 | "Compare these two documents and identify contradictions" | contradictions identified, evidence cited | Analysis |
| T09 | "Write a tool that [specific function] and register it" | tool file exists, callable by name, produces correct output | Tool creation |
| T10 | "Analyze this dataset and produce a structured report" | report exists, numbers match source data, no fabrication | Data analysis / EI test |

### What You Can Build Tonight

1. **The runner framework** — the loop that runs tasks N times and records results
2. **The verifier interface** — the contract verifiers implement
3. **The results storage** — JSONL log with the fields above
4. **The report generator** — computes pass^1, pass^k, and produces a readable summary
5. **2-3 starter verifiers** — T01 (wiki list) and T03 (integrity check) are the simplest to verify against known-good output

### What Needs a Session

- **The full 20-task battery** — the starter 10 above are representative but not comprehensive. The full set should cover all cycle types, all failure modes from the stress tests, and the specific capabilities we want to regression-test.
- **The pass^k targets** — what threshold do we set for "reliable enough"? The τ-bench data suggests pass^8 > 50% is ambitious for any agent system.
- **The SWARMFISH backtest component** — Fable's BP-02 includes held-out post-cutoff Brier scoring for the prediction pipeline. That's a separate verifier type (probabilistic accuracy, not binary pass/fail).
- **The ablation methodology** — leave-one-out testing to identify which harness crutches are load-bearing. Needs careful design to isolate variables.

### Key Design Decisions (already made, for your reference)

- **pass^k, not pass@1** — consistency matters more than average success (τ-bench finding)
- **Verifiers check outcomes, not process** — we don't grade the agent's reasoning, just the result
- **Environment reset between trials** — each trial is independent. No state leakage.
- **Results are append-only JSONL** — the log grows, never shrinks. Every trial is recorded.
- **The harness is a tool, not an extension** — it runs OUTSIDE the agent, not inside it. The agent doesn't know it's being tested.

### Governance

This is framework work within an approved build plan. Decide alone on implementation details. Ask me if the verifier design feels ambiguous. The full task battery and pass^k targets need me and Jake.

Build the framework. Write the first verifiers. Run a trial if the agents are available. Report back in the inbox.

— Opus
