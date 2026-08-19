# Epistemic Integrity Layer

**Component** | **Hook:** monologue_end (_25_) | **Type:** Deterministic audit

---

## Purpose

The Epistemic Integrity Layer (EIL) audits every model response for truthfulness before it reaches the operator. It catches confabulation — the model's tendency to fabricate specific facts, figures, and citations with high confidence.

Motivated by ST-003: the agent fabricated a complete Oracle credit risk report with zero source data, claiming "High confidence — data from SEC filings and Bloomberg snapshots." Every figure was wrong.

## Architecture

Three-component deterministic audit on the model's last response:

### 1. Provenance
Did this claim appear in a tool output this session?
- **Evidence Ledger** — Populated by the tool_execute_after hook, records every data point that entered the session via tool outputs.
- Claims matched against the ledger: found → GROUNDED; not found → UNGROUNDED.

### 2. Volatility
How fast does this type of claim change in the real world?
- **Signal patterns** + BST domain defaults classify claims into volatility classes:
  - `structural` — Slow-changing (error patterns, code architecture)
  - `institutional` — Moderate (ratings, policies, organizational data)
  - `cyclical` — Seasonal/quarterly (financial metrics, market data)
  - `transactional` — Fast-changing (prices, stock levels, current status)
  - `ephemeral` — Real-time only (live metrics, current queue depth)

### 3. Staleness
How far is "now" from the model's training cutoff?
- Loaded from model profile temporal section.
- Claims about events after cutoff → automatic suspicion.

## Verdict Matrix

`grounded × volatility class`:

| Volatility Class | GROUNDED | UNGROUNDED |
|---|---|---|
| structural | TRUST | LIKELY_VALID |
| institutional | TRUST | VERIFY_IF_CRITICAL |
| cyclical | TRUST | DO_NOT_TRUST |
| transactional | TRUST | FABRICATION_RISK |
| ephemeral | TRUST | FABRICATION_BY_DEFINITION |

## Integration Points

- **Hook:** `monologue_end` phase 25 — runs after model generates response, before delivery to operator.
- **Evidence Ledger:** Populated by `tool_execute_after` hook alongside Error Comprehension. Zero new hooks needed.
- **Model profile:** Reads temporal/staleness data from active model configuration.
- **BST domain defaults:** Provides volatility classification rules per domain.

## Relationship to Other Systems

- **Error Comprehension** — Guards the action loop (negative knowledge: "what went wrong"). EIL guards the output (positive knowledge: "is this claim valid?"). Complementary.
- **Compound BST** — Provides domain classification that feeds volatility assessment.
- **Evidence Ledger** — New subsystem created specifically for EIL. Records structured data from tool outputs.

## Key Design Decisions

1. **No LLM calls** — Fully deterministic. Provenance matching and volatility classification use pattern rules, not inference.
2. **Passthrough on error** — If EIL itself fails, the response passes through unmodified rather than blocking output.
3. **Invisible to the model** — The model doesn't see EIL verdicts. They're for the operator and downstream logging.

## Incidents Addressed

- [[inc-oracle-fabrication]] — Fabricated financial analysis with specific numerical claims
- [[inc-fabricated-metrics]] — Hallucinated benchmark numbers and comparison data

## Spec Reference

- `specs/EPISTEMIC_INTEGRITY_DESIGN_NOTE.md` — Full design rationale, verdict matrix derivation, integration spec
- `specs/COUNTER_PATRIOTS_EPISTEMIC_STAGING.md` — Staging considerations for evidence ledger
- `extensions/monologue_end/_25_epistemic_integrity.py` — Implementation (~1,070 lines)
