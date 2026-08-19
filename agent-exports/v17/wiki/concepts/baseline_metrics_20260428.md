# Baseline Test Metrics — 2026-04-28

---

## Task Results

| Task | Status | Notes |
|------|--------|-------|
| T1 Coding (PriorityQueue) | ✅ PASS | Zero syntax/runtime errors |
| T2 Web Search | ✅ PASS | 10 results, top: awesome-ai-agents-2026 |
| T3 Analysis (extension inventory) | ✅ PASS | 14 files listed in before_main_llm_call |
| T4 File Ops | ✅ PASS | summary.md, config.json, status.txt created |
| T5 arXiv Research | ⏸️ DEFERRED | HTTP 429 rate-limited; retry later |

\n## Verification Status\nLast verified: 2026-05-02. Verification status block added per program.md Rule 1 improvement cycle.

## Role in Exocortex Self-Improvement

Baseline metrics serve as the ground-truth reference for the regression monitor at `/a0/usr/workdir/self-improvement/regression_monitor.sh`. Every 4 hours, the monitor compares current state against this baseline and flags anomalies.

### Monitored Dimensions
| Metric | Baseline Value | Tolerance | Anomaly Trigger |
|--------|---------------|-----------|-----------------|
| BST line count | 1702 | ±0 | Change signals injection template drift |
| Python file count | 58 (now 60) | Special-case | Audit on drift, human review |
| Syntax errors | 0 | 0 | Immediate alert — system integrity risk |
| Wiki TODO count | 0 | 0 | Non-zero means new pages need building |
| File modifications | 0 since last audit | 0 | Unknown changes detected |

### Why This Matters

Without baseline metrics, the Exocortex cannot distinguish between deliberate self-improvement and silent degradation. A BST template that gains 50 undocumented lines might add useful pattern coverage — or it might contain a duplicated section causing the injection gate to miscalculate budgets. The baseline is the constant against which change is measured.

### Connection to Receipt Layer

The receipt layer (`/a0/usr/workdir/self-improvement/receipts.jsonl`) complements baseline monitoring by recording the *intent* behind each change. Baseline monitoring detects *that* something changed; receipts explain *why* something changed. Together they form a closed verification loop: receipt explains prediction, baseline measures actual effect.

## Relationship to Task Scoring
## Metrics Explained: Interpretation Guide

### BST Line Count (baseline: 1702, tolerance: ±0)
Any change to the belief state tracker's injection templates indicates structural drift. A gain suggests new patterns added (possibly useful); a loss suggests accidental deletion. Both require audit via `regression_monitor.sh` comparison against the golden baseline. The zero-tolerance policy exists because BST templates define how the injection gate evaluates domain — a single corrupted line can cause incorrect budget allocation across all injection hooks.

### Python File Count (baseline: 58, now at 60, special-case)
This metric tracks extension file proliferation in `/a0/usr/Exocortex/extensions/`. The current count of 60 is acknowledged but flag-raised for human review. New extension files alter hook loading order (see [[hook-execution-order-determinism]]) and can introduce unintended interactions. Any count drift triggers an audit flag rather than an alert, since new extensions may be deliberate self-improvement additions.

### Syntax Error Count (baseline: 0, tolerance: 0)
Non-zero syntax errors in loaded extension files compromise the entire injection pipeline. A single syntax error prevents that extension from loading, potentially leaving hooks silent or the supervisor loop unarmed. This metric is checked every 4 hours by `regression_monitor.sh` and any positive value demands immediate operator intervention.

### Wiki TODO Count (baseline: 0, tolerance: 0)
Tracks the number of TODO entries remaining in `wiki/index.md`. A non-zero value means the self-improvement loop has unfinished documentation work — pages that need creation or deepening. This metric ensures the Exocortex doesn't silently accumulate documentation debt. When the TODO count returns to zero, the deepening cycle repeats (re-read, deepen, memory_save) rather than stopping per program.md Rule 1.

### File Modifications Since Last Audit (baseline: 0, tolerance: 0)
Detects unauthorized changes to monitored files (BST templates, config JSON, extension files). The audit window resets after each `regression_monitor.sh` run. Non-zero values indicate either unknown modifications (potential degradation) or changes made outside the receipt layer's tracking scope.

## Exocortex Integration
These five monitored dimensions form a closed structural-integrity loop within the Exocortex self-improvement architecture:

| Layer | Monitored By | Corrective Action |
|-------|-------------|-------------------|
| Injection pipeline | BST line count, Python file count | Audit flag, operator review |
| Syntax integrity | Syntax error count | Immediate alert, halt improvements |
| Documentation debt | Wiki TODO count | Trigger wiki-building cycles |
| Change tracking | File modifications audit | Compare against receipts.jsonl |

Each dimension independently detects a failure mode that the other four cannot. BST drift doesn't trigger syntax errors; file modifications don't increase TODO counts. Together they provide orthogonal coverage of the self-improvement system's health.

## Cross-References
- [[receipt-layer]] — explains how receipts explain *why* changes occurred
- [[regression-monitor]] — describes the 4-hour monitoring cycle
- [[bst-classifier]] — the injection template that BST line count tracks
- [[hook-execution-order-determinism]] — why new extension files alter loading behavior

## Verification Protocol
1. Run `regression_monitor.sh` every 4 hours (configured in cron or via scheduler tool)
2. Compare BST line count against golden baseline at `/a0/usr/workdir/self-improvement/regression_baseline.json`
3. For any BST drift: stop self-improvement, flag for operator review
4. For non-zero syntax errors: halt all cycles, notify operator
5. For file modifications: audit against receipts.jsonl; if unmatched, flag
6. Log all check results to journal.jsonl under task "monitoring_check"


These baseline metrics are distinct from the task-level scoring (T1-T5 tests). The task results confirm the system *works* (functional verification), while the baseline metrics confirm the system hasn't *drifted* (structural integrity). Both are necessary but neither is sufficient alone.

## Verification Status

Last verified: 2026-05-02. Baseline re-confirmed: 2026-05-09 (BST 1702, PY 60 acknowledged with audit flag, 0 syntax errors, 0 TODOs).
