# Epistemic Integrity Layer

**Created:** 2026-04-28T04:51Z
**Status:** Core Exocortex component
**Implementation**: `_17_epistemic_integrity.py`

## Overview

The Epistemic Integrity (EI) layer audits every claim the agent makes against an evidence ledger with volatility classification. It runs as a `before_main_llm_call` extension, tagging claims as grounded or ungrounded before they reach the LLM context. This is the architectural response to LLM confabulation — it doesn't prevent it, but provides deterministic signals when it's happening.

## Mechanism

### Evidence Ledger

Every factual assertion receives a provenance tag:
- **GROUND** — traced to cited source within conversation window with verifiable link
- **EPHEMERAL** — derived from transient state (runtime metrics, turn counts) subject to staleness
- **UNVERIFIED** — no source citation; flagged for review

### Volatility Classification

Claims classified by temporal stability:
1. **Static** — mathematical facts, structural descriptions (stable indefinitely)
2. **Semi-static** — paper findings, benchmark results (6-18 month half-life)
3. **Dynamic** — runtime metrics, live system state (< 24h half-life)
4. **Ephemeral** — turn-specific observations (expires next cycle)

### Staleness Detection

```
staleness = current_time - claim_timestamp
if staleness > volatility_half_life → flag EPHEMERAL + stale
```

System warning format: `[EPISTEMIC CHECK] X of Y claims grounded. Z ungrounded.`

### Enrichment Injection

The EI layer injects a compact evidence summary into the model's context before each LLM call:
- Total claim count and grounded ratio
- List of ungrounded claims with the instruction to verify or retract
- Staleness warnings for claims beyond their half-life
- A "confidence caveat" when the grounded ratio falls below 0.5

## Historical Evolution

- **v1 (initial):** Simple regex-based claim extraction with manual tagging. Only detected numeric claims.
- **v2 (April 2026):** Added volatility classification and staleness tracking. Evidence ledger became persistent across turns via working memory integration.
- **v3 (planned):** Semantic claim detection using BST compound classification output to identify claim types (factual, procedural, predictive) and apply different evidence standards.

## Failure Modes

1. **Silent stale claims:** When staleness detection isn't triggered because the claim timestamp isn't captured (e.g., claim from a prior session without metadata). The system reports a claim as EPHEMERAL but doesn't know if it's stale.
2. **Citation laundering:** The agent fabricates a plausible-sounding source (e.g., "per arXiv 2401.xxxxx") that passes regex checks but doesn't exist. The EI layer can't verify existence; it only checks if a source format is present.
3. **Over-caveating:** When the grounded ratio is low, the model receives a "low confidence" warning on every turn, which can cause overly cautious behavior and premature escalation.
4. **False positives in claim extraction:** The regex-based claim detector sometimes flags procedural statements ("I will now run the test") as factual claims, inflating the ungrounded count.

## Testing Strategy

- **Unit tests:** Test staleness calculation with known timestamps and half-lives. Test volatility classification of static/semi-static/dynamic/ephemeral claims.
- **Integration tests:** Inject known-good claims and verify enrichment output includes correct grounded/ungrounded counts. Inject fabricated claims with citation-like formatting and verify they're flagged UNVERIFIED.
- **Regression tests:** Run the EI layer against a corpus of past conversation turns with known ground truth and assert the grounded ratio matches expectations.
- **Manual inspection:** Read `[EPISTEMIC CHECK]` lines in agent output during workshop cycles to verify they're accurate.

## Implementation Details

### Hook Chain Position
`_17_epistemic_integrity.py` runs after BST classification (`_14_bst_classifier.py`) and before the orchestration gate (`_17_orchestration_gate.py`). This ordering ensures the EI layer has domain context for claim extraction but can influence the injection budget.

### Evidence Ledger Storage
Claims are stored in JSON format in `/a0/usr/workdir/receipts.jsonl` with timestamp, claim text, volatility class, source citation if any, and staleness status. The ledger is loaded at hook initialization and updated after each turn.

### Performance Impact
Claim extraction uses regex matching, which is fast but imprecise. The staleness check iterates over the full evidence ledger on every turn, which could become a bottleneck with thousands of claims (current ceiling ~500 claims before noticeable latency).

## Known Limitations

- **No semantic verification:** The EI layer checks provenance format, not whether a source actually supports the claim. It's a syntactic gate, not a semantic one.
- **No cross-turn claim tracking:** Claims from prior conversations aren't tracked unless they were explicitly saved, limiting the ability to catch inconsistencies across sessions.
- **Static volatility profiles:** Half-lives are hardcoded per class. Dynamic adjustment based on actual claim decay rates would improve accuracy.
- **No interaction with confabulation detection:** The EI layer and confabulation detector operate independently. Integrating them would allow the EI layer to flag claims the confabulation detector later identifies as false, closing the feedback loop.

## Future Directions

- **Semantic claim verification:** Use tool-calling to verify claims against external sources (search, ArXiv) before they're injected.
- **Adaptive volatility:** Learn claim half-lives from actual staleness patterns observed across sessions.
- **Integrated feedback loop with confabulation detector:** Claims flagged as confabulated by the detector should be retroactively tagged as UNVERIFIED in the evidence ledger.
- **Operator-facing evidence panel:** Show the evidence ledger in the NERV dashboard so the operator can see what claims are being made and their grounding status.

## Connection to Other Concepts

- **[[confabulation]]** — EI catches quantitative confabulation; citation variant still needs semantic checking
- **[[supervisor-loop]]** — ungrounded claims feed as soft signals into CUSUM accumulator
- **[[deterministic-scaffolding]]** — evidence tagging is structural rule not optional behavior
- **[[context-pruner]]** — EI enrichment is subject to pruning when context is tight; the pruner prioritizes grounded claims over ungrounded ones
- **[[injection-gate]]** — EI enrichment is gated by the injection budget; when budget is low, only the grounded ratio summary is injected

## References

- Implementation: `/a0/usr/Exocortex/extensions/before_main_llm_call/_17_epistemic_integrity.py`
- Evidence ledger: `/a0/usr/workdir/receipts.jsonl`

## Verification Status
Last verified: 2026-05-10 (cycle 17). Deepened with Historical Evolution, Failure Modes, Testing Strategy, Implementation Details, Known Limitations, and Future Directions.
