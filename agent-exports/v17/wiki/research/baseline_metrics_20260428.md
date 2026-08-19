# Baseline Metrics (April 28, 2026)

## Citation
- **Source**: Exocortex self-improvement setup, Opus design
- **Date**: 2026-04-28
- **Context**: Established during initial Exocortex installation to serve as regression comparison points for configuration tuning experiments.

## Key Findings
1. Extension count (`py_count`) baseline: **60** Python extension files in `/a0/usr/agents/agent0/extensions/`
2. BST line count baseline: **1702** lines in `_11_belief_state_tracker.py`
3. These baselines are automatically detected at install time and stored in `regression_baseline.json`
4. The regression monitor (`regression_monitor.sh`) compares current counts against these baselines to detect drift
5. Any deviation in these numbers indicates an unauthorized code change (py files cannot be modified by the agent under Rule 5)

## Relevance to Exocortex
- Provides a deterministic anchor for the self-improvement loop's configuration tuning (Tier 1 / Priority 4)
- Enables the agent to detect unauthorized or accidental code changes without needing to inspect file contents
- Supports the [[receipt-layer]] concept: baseline → change → measurement → verdict
- Directly referenced by the sanctioned self-monitoring checks in program.md (check BST line count, check extension count)
- Acts as a circuit breaker condition: if BST lines change, the agent must STOP and report the anomaly rather than attempt self-repair

## What We Adopted
- **regression_baseline.json** as the canonical reference file for code invariants
- **regression_monitor.sh** as a read-only script that compares current state against baseline
- **Sanctioned self-monitoring** in program.md that allows the agent to run `wc -l` and `py_compile` checks
- The practice of logging monitoring results to `journal.jsonl` under `"task": "monitoring_check"`

## What We Deferred
- Automatic baseline updating: baselines only change when an operator deliberately updates them. The agent cannot modify baselines.
- More granular baselines (per-extension line counts): kept simple (BST + total count) for reliability — complex baselines are harder to verify
- Integration with configuration tuning metrics: current regression monitor only checks code invariants, not performance metrics

## Connection to Other Pages
- [[receipt-layer]] — baseline data feeds the receipt verification loop
- [[bst-classifier]] — the BST is the most critical extension monitored by baseline
- [[deterministic-scaffolding]] — baselines are deterministic anchors in a probabilistic system
- [[inc-watchdog-blind]] — incorrect context window threshold was caught by baseline drift detection
- [[dcn-pywrite-guard-enforcement]] — baselines provide technical enforcement for the no-py-modify rule

## Verification Status
Last verified: 2026-05-10. Baseline unchanged: py_count=60, bst_lines=1702.
