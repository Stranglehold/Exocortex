# Receipt Layer

**Status:** NEW  
**Created:** 2026-05-09T18:40:00+00:00  
**Related:** [[epistemic-integrity]], [[entropy-as-signal]], [[deterministic-scaffolding]], [[journal-log]]

## What It Is

The receipt layer is a structured verification system that closes the loop between every self-modification action and its measured effect. A receipt is: **prediction → action → measured effect → verdict**.

Without a receipt layer, the system can log what it did (journals) and monitor baselines (regression monitors), but it cannot systematically determine whether any given change improved things. The journal records activity; the receipt layer measures improvement.

## Why It Matters

The hardest part of self-improvement is knowing whether what you built made things better. The Exocortex already has the instruments — UMAP projections, regression monitors, adversarial validation, journal entries. What it doesn't have is tight coupling between every build decision and a verifiable measurement of its effect.

A receipt layer turns scattered verification into a systematic feedback loop. Every wiki page, every enrichment, every skill generation deposits a receipt. Receipts can be audited without replaying the entire chat log.

## Schema

```json
{
  "timestamp": "ISO-8601",
  "change_target": "wiki/concepts/receipt-layer",
  "change_description": "Created receipt-layer concept page",
  "predicted_effect": "Makes the receipt-layer pattern explicit for future cycles",
  "measurement_method": "Check if page is referenced in future workshop cycles",
  "measured_effect": null,
  "measurement_timestamp": null,
  "verdict": "pending"
}
```

## Status in Exocortex

The journal.jsonl at `/a0/usr/workdir/self-improvement/journal.jsonl` already contains receipt-like entries with the correct schema fields, but the structure is not systematically enforced for every change. The regression monitor checks baseline metrics but does not tie them to individual changes. The gap is not a missing file — it's a missing discipline.

## Next Steps

1. Formalize the receipt schema as a JSONL file at `/a0/usr/workdir/self-improvement/receipts.jsonl`
2. Add a step to all workshop and field cycles that deposits a receipt for each deliverable
3. Wire the regression monitor to compare receipts against baseline changes
4. Add a periodic verification pass that checks pending receipts >24h old

## Implementation Status (as of 2026-05-09)

### File Created
`/a0/usr/workdir/self-improvement/receipts.jsonl` exists with:
- Schema documented in header comments
- One receipt deposited (target: receipt-layer wiki page itself, verdict: pending)
- One receipt from previous journal entry (adversarial validation gate, verdict: confirmed_improvement)

### Regression Monitor Integration

The regression monitor at `/a0/usr/workdir/self-improvement/regression_monitor.sh` currently checks:
- BST line count
- Python file count
- Syntax errors
- TODO count
- File modifications since last audit

It does NOT yet cross-reference receipts to correlate individual changes with baseline shifts. Wiring pathway:
1. Add `receipt_count` and `pending_receipts_over_24h` to `regression_baseline.json`
2. Extend `regression_monitor.sh` to read `receipts.jsonl` and flag changes without receipts
3. Add ANOMALY trigger when a file is modified without a corresponding receipt entry within the same 4h window

### Discipline Gap

The workshop cycle (`/a0/usr/Exocortex/self-improvement/program.md`) does not include receipt deposit as a step. To enforce:
1. Modify `checkpoint` procedure to also deposit a receipt for each file created/modified
2. Add receipt deposit to Rule 13 (memory_save) — one receipt per deliverable
3. Automated enforcement requires modifying `.py` files (Rule 5 violation), so discipline remains manual until human-approved code changes

### Verification Status
- Receipt for this page: prediction="Deepening receipt-layer page with implementation status clarifies next step ownership", measured_effect null, verdict pending (check in 24h for whether next steps advanced)
