# Confabulation

**Created:** 2026-04-28T04:23Z
**Deepened:** 2026-05-10 (cycle 19 — implementation analysis, detection architecture, testing strategy, edge cases, historical evolution)
**Status:** Core Exocortex concept
**Epistemic Layer target:** Detection + mitigation

## Definition

Confabulation is the production of fabricated, distorted, or misinterpreted information presented with full confidence by the generator. In LLMs it manifests as plausible-sounding but factually incorrect statements that cannot be distinguished from truth by output probability alone. The Exocortex treats confabulation as an architectural problem, not a model behavior problem — the LLM will confabulate; the system must catch it deterministically.

## Two Variants

### Quantitative Confabulation (EI Catches)

Fabricated numbers, statistics, metrics, or measurements presented with false precision.
- **Detection**: Epistemic Integrity Layer cross-references cited figures against known data sources and volatility classifications. Stale metrics trigger staleness flags; unsourced numbers flagged as ungrounded.
- **Example**: "Tool reliability improved 26%" without source citation → EI marks EPHEMERAL + no source.

### Citation Confabulation (EI Doesn't Catch)

Real citations attached to false claims — the paper exists but says something different than claimed, or a real author is attributed a finding they never made.
- **Detection gap**: EI validates provenance (source exists) and volatility (paper age) but cannot verify semantic alignment between claim and source without deep reading.
- **Risk**: Higher because it passes surface-level integrity checks — the citation looks legitimate.

## System Design Implications

1. **Quantitative claims require inline evidence** — every metric, percentage, or statistic must trace to a cited source or logged measurement within the conversation window.
2. **Citation verification needs semantic checking** — not just existence of source but alignment between claim and source content. Requires document_query or arXiv read_paper before asserting what a paper says.
3. **Confidence calibration**: High-confidence low-evidence statements are the hallmark pattern. EI staleness + volatility flags should down-weight ungrounded claims in BST domain classification.

## Detection Architecture

The Epistemic Integrity layer (`_25_epistemic_integrity.py`, monologue_end hook) implements a three-component deterministic audit:

### Component 1: Provenance
Did this value appear in a tool output this session? The Evidence Ledger (`/a0/usr/workdir/receipts.jsonl`) records every observed value from tool outputs. Claims are cross-referenced against this ledger.

### Component 2: Volatility Classification
Claims classified by temporal stability:
1. **Static** — mathematical facts, structural descriptions (stable indefinitely)
2. **Semi-static** — paper findings, benchmark results (6-18 month half-life)
3. **Dynamic** — runtime metrics, live system state (< 24h half-life)
4. **Ephemeral** — turn-specific observations (expires next cycle)

### Component 3: Staleness Detection
How far is "now" from the model's training cutoff? Claims exceeding their volatility class half-life are flagged stale regardless of provenance.

### Verdict Matrix
```
GROUNDED                   → TRUST
UNGROUNDED + structural    → LIKELY_VALID
UNGROUNDED + institutional → VERIFY_IF_CRITICAL
UNGROUNDED + cyclical      → DO_NOT_TRUST
UNGROUNDED + transactional → FABRICATION_RISK
UNGROUNDED + ephemeral     → FABRICATION_BY_DEFINITION
```

No LLM calls in the detection pipeline — fully deterministic. This is motivated by incident ST-003: the agent fabricated a complete Oracle credit risk report with zero source data, expressed "High confidence — data from SEC filings and Bloomberg snapshots." Every figure was wrong.

## Testing Strategy

### Unit Tests (Deterministic)
- **Provenance matching**: Verify GROUNDED verdict when claim value appears in evidence ledger within staleness window.
- **Staleness flagging**: Verify EPHEMERAL claims exceeding volatility half-life are downgraded.
- **Verdict matrix**: Each of 6 cells tested with synthetic claims.

### Integration Tests (Live)
- **Confabulation injection**: Deliberately insert fabricated metrics into agent context; verify EI catches.
- **Cross-detector integration**: When confabulation detector and EI both flag a claim, severity should escalate.

### Regression Guard
- Known confabulation patterns from incident history stored as test cases.
- Each workshop cycle runs regression suite; new anti-patterns added to test corpus.

## Known Limitations

1. **Citation confabulation blind spot**: Surface-level verification only. Semantic alignment between claim and source requires deep reading (planned: document_query integration).
2. **Static volatility profiles**: Half-lives are hardcoded per class. Dynamic adjustment based on actual claim decay rates would improve accuracy.
3. **No feedback loop with confabulation detector**: The EI layer and confabulation detector operate independently. Integrating them would close the loop.
4. **Evidence ledger coverage**: Only tool outputs captured; claims derived from model reasoning without tool use cannot be provenance-checked.
5. **Numerical precision**: Fabricated numbers within plausible ranges (e.g., 61% vs 60%) evade range-based detection.

## Historical Evolution

- **v0 (pre-Exocortex):** Agent confabulated metrics frequently; no detection mechanism.
- **v1 (Feb 2026):** Design note `design_04_20260224_epistemic_integrity.md` established three-component architecture.
- **v2 (Apr 2026):** Implementation at `_25_epistemic_integrity.py` with verdict matrix and evidence ledger.
- **v3 (May 2026 — current):** Deepened with testing strategy, known limitations, and cross-component integration mapping.

## Connection to Other Concepts

- **[[epistemic-integrity]]** — evidence ledger + volatility classification for detection framework
- **[[deterministic-scaffolding]]** — require inline citations as structural rule, not optional behavior
- **[[entropy-as-signal]]** — high output entropy at confabulation points indicates model uncertainty masked by confident phrasing
- **[[error-comprehension]]** — negative knowledge repository; confabulation incidents feed error comprehension patterns
- **[[supervisor-loop]]** — ungrounded claims feed as soft signals into CUSUM accumulator for tier escalation

## References

- Implementation: `/a0/usr/Exocortex/extensions/monologue_end/_25_epistemic_integrity.py`
- Design note: `/a0/usr/Exocortex/chronology/design_notes/design_04_20260224_epistemic_integrity.md`
- Evidence ledger: `/a0/usr/workdir/receipts.jsonl`
- Incident: Oracle fabrication (ST-003) — `/a0/usr/Exocortex/wiki/incidents/inc-oracle-fabrication.md`

## Verification Status
Last verified: 2026-05-10 (cycle 19). Deepened with Detection Architecture, Testing Strategy, Known Limitations, Historical Evolution, and Verdict Matrix sections. Cross-references validated against wiki index.
