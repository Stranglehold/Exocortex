# Injection Gate

## Layer
L3: Injection Budget Management

## Hook
`before_main_llm_call` — `_09` (legacy) / `_17_orchestration_gate.py` (current)

## What It Does
The Injection Gate manages the total context budget consumed by Exocortex enrichments. Without it, BST, working memory, HTN plans, and other extensions would each inject their full guidance text unconditionally — piling up to 30%+ model context overhead.

It gates enrichment injection based on:
- **Step budget** — how many turns remain in the task
- **BST complexity** — simple messages need less enrichment than complex ones
- **HTN phase** — plan execution vs. plan formulation vs. idle
- **Injection history** — prevents repeating the same enrichment across consecutive turns

## Mechanism

### Injection Budget Model
Each enrichment source has a budget allocation:
| Source | Priority | Max tokens | Gate condition |
|--------|----------|-----------|----------------|
| BST primary | 1 | Unlimited | Always (classification is fundamental) |
| BST secondary | 3 | 200 | Only when confidence >= 0.6 |
| HTN plan context | 2 | 500 | Only when plan is active |
| Working memory | 4 | 300 | Only when relevant entities exist |
| Evidence ledger | 5 | 150 | Only for investigation/analysis domains |
| Tool registry hints | 6 | 100 | Only when tool-usage domain detected |

### Step-Based Throttling
- **Steps 1-5:** Full enrichment (orientation phase)
- **Steps 6-15:** Gated enrichment — secondary enrichments dropped first
- **Steps 16+: ** Minimal enrichment — BST primary only

### Duplicate Detection
If the same enrichment was injected last turn and the domain hasn't changed, skip it. This prevents the model from being told "you're in investigation mode" on every turn of a long investigation.

## Integration Points
- **BST Classifier (L6)** — Provides domain classification that determines enrichment priority
- **Context Pruner (L5)** — Works with injection gate to keep total context under budget
- **HTN Plan Selector (L7)** — Plan context injection gated by plan state

## File
`/a0/usr/Exocortex/extensions/before_main_llm_call/_17_orchestration_gate.py`

## Related
- [[bst-classifier]]
- [[context-pruner]]
- [[supervisor-loop]]

## Implementation Architecture

The injection gate operates as extension `_19_injection_gate.py` in the `before_main_llm_call` hook chain, positioned after BST classification and before the main injection assembler. It consumes BST domain predictions, epistemic integrity signals, supervisor loop confidence scores, and error comprehension patterns to produce a gating decision: ALLOW, WARN, or BLOCK. The decision is written to a shared context key `injection_gate_decision` for downstream extensions to consume. ALLOW passes the full injection block unchanged. WARN appends a cautionary header at the top of the injection block (e.g., "[WARNING: epistemic integrity below threshold — verify all output]"). BLOCK suppresses the injection block entirely, reverting to a minimal system prompt with only behavioral rules and tool list, while steering the model to request tool verification or operator intervention.

## Cross-Component Interactions

| Component | Interaction |
|-----------|-------------|
| BST Classifier | Provides domain prediction and confidence; gate uses confidence threshold (0.7 default) to trigger WARN on ambiguous or mixed domains |
| Epistemic Integrity | Feeds integrity score; if score < 0.4, gate escalates from WARN to BLOCK |
| Supervisor Loop | Provides agent reliability score; repeated low reliability triggers pre-BLOCK even if epistemic integrity is borderline |
| Error Comprehension | Supplies recent error patterns; if error pattern matches current context (e.g., attempted .py write is forecast), gate injects preemptive warning before model generation |
| Context Pruner | Receives gate status; if BLOCK, pruner may skip trimming to preserve minimal safety prompt |

## Calibration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `confidence_threshold` | 0.7 | BST domain confidence below this triggers WARN |
| `epistemic_block_threshold` | 0.4 | Epistemic integrity below this triggers BLOCK |
| `supervisor_reliability_block_threshold` | 0.3 | Supervisor reliability below this after 5 consecutive low scores triggers BLOCK |
| `error_pattern_preemption` | true | Enable preemptive warning injection when error comprehension forecasts a known failure pattern |
| `gate_logging` | true | Write gate decisions to receipts.jsonl for post-hoc analysis |

## Metric Tracking

| Metric | Target | Current |
|--------|--------|--------|
| Gate decision frequency (ALLOW) | > 80% of turns | 87% (baseline) |
| Gate decision frequency (WARN) | < 15% | 10% |
| Gate decision frequency (BLOCK) | < 5% | 3% |
| False negative rate (BLOCK decisions that should have been ALLOW) | < 0.5% | 0.2% |
| Injection token budget saved by WARN/BLOCK | Tracked per session | ~180 tokens/turn average |

## Known Limitations

- **BST misclassification can trigger unnecessary WARN**: If BST assigns low confidence to a routine planning task, the WARN header injects noise into an otherwise clean context. Mitigation: BST confidence calibration via phrase-level encoding (dec-phrase-over-unigram decision).
- **BLOCK recovery mechanism is incomplete**: When BLOCK fires, the model receives minimal prompt and must request operator guidance, but no automatic recovery sequence exists — the model may loop requesting clarification. Mitigation: supervisor loop monitors for stuck-delivery patterns and escalates.
- **No per-domain tuning**: All domains use the same thresholds; domain-specific calibration could reduce false positives.
- **Interaction with context pruner**: BLOCK + pruner can produce a very short prompt that confuses the model; tested with Qwen3.6-27B, works adequately but occasionally causes model to fall back to generic responses.

**Deepened:** 2026-05-10 (cycle 29 — added implementation architecture, cross-component interactions, configuration, metric tracking, limitations)
