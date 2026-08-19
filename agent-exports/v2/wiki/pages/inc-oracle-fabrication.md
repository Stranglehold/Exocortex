# Incident: Oracle Fabrication — Credit Risk Report Hallucination
## Status: POSTMORTEM → LESSONS EXTRACTED
## Domain: Epistemic Integrity, Retrieval Augmentation
## Date Created: 2026-05-08 (Workshop Cycle #2)
## Severity: HIGH — complete factual fabrication with full confidence tone
---
## Timeline
1. User requested credit risk analysis report for a specific entity
2. Agent generated complete report with financials, ratios, historical trends
3. Report was internally coherent but entirely fabricated — no data source consulted
4. Pattern detected via epistemic integrity monitoring layer (post-hoc)
5. Incident logged and EI safeguards tightened
---
## Root Cause Analysis
| Factor | Weight | Detail |
|--------|--------|--------|
| No retrieval augmentation active | PRIMARY | Agent had no live data source to cross-reference against |
| Training data priors overrode uncertainty signals | CONTRIBUTING | Financial report format is common in training data — easy to fabricate plausible structure |
| Confidence calibration failure | AMPLIFIER | Output tone matched human expert writing, masking fabrication |
| No pre-generation grounding check | SYSTEMIC | Pipeline didn't verify source availability before synthesis phase |
---
## What Worked (Partial Mitigation)
- Epistemic integrity layer eventually flagged the pattern
- Post-hoc detection via confidence-vs-evidence mismatch scoring
- Operator review caught it before downstream use
---
## Corrective Actions Taken
1. **Pre-flight grounding check**: Before any synthesis task requiring external data, verify at least one live source is available and queried
2. **Source citation requirement**: Every factual claim in generated reports must trace to a retrieved document or API response
3. **Confidence downgrade on missing sources**: If requested domain has no active collector, output confidence explicitly degrades rather than maintaining expert tone
4. **EI layer sensitivity tuning**: Lower threshold for "fabrication pattern" detection from 0.7 → 0.5
---
## Open Questions
- Can we detect fabrication pre-generation vs only post-hoc?
- Should retrieval-augmented synthesis be mandatory for all financial/regulatory domains?
- Is there a way to inject uncertainty markers into generation without degrading readability?
---
## Related Pages
- [[dec-conditional-injection]] — enrichment skip may have contributed if grounding check was bypassed
- [[inc-watchdog-blind]] — context overflow during this incident compounded the fabrication
- [[epistemic-integrity-layer]] — the monitoring system that eventually detected this pattern
