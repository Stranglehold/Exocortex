# Conditional Injection True Negative Rate Analysis
## Last updated: 2026-04-29

---

## Problem Statement
The BST conditional enrichment gate (lines 977-984) skips full compound dict serialization when domain classification is stable across turns. This saves tokens but introduces a false-negative risk: injecting only `primary_domain` may miss secondary signals that matter.

## Current Mechanism (v3.8)
- Lines 977-984 implement the skip logic
- When `momentum_turns >= 2`: inject only primary domain string
- Full compound dict includes: primary domain + confidence, secondary domain + confidence, enrichment plan

## Honest Assessment (Run 2)
| Metric | Value | Source |
|--------|-------|--------|
| Token savings per turn when gate active | ~530 tokens based on BST injection budget header showing ~1048 total injected this turn with BST at ~417 tokens | EPHEMERAL metric inherited from system prompt injection_budget field, not directly measured |
| True negative rate (correct skips) | Not historically logged — no record of skip decisions available in journal.jsonl | EPHEMERAL per epistemic discipline requirement |
| False negative risk during domain transitions | Qualitative assessment: low for stable domains but unknown for transition periods between distinct tasks | Inferred from code logic in _11_belief_state_tracker.py lines 977-984, not measured |

## Recommendations
1. Log every conditional injection decision to separate metrics file with turn number + action taken (skip vs full)
2. Periodically sample turns where skip occurred and manually assess if secondary signals mattered
3. Set minimum log retention period of 500 turns for statistical significance on true/false negative rates

## Verification Status
Last verified: 2026-05-02. Verification status block added per program.md Rule 1 improvement cycle.
