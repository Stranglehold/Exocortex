# Deterministic Scaffolding

**Created:** 2026-04-28T04:17Z
**Last Improved:** 2026-05-10 (Cycle 15 — added Measurement Framework, Edge Cases, and expanded Open Questions)
**Status:** Core Exocortex principle

## Core Claim

LLMs are probabilistic engines — they generate tokens based on learned distributions. For tasks requiring reliability (classification, validation, safety checks), external deterministic structures outperform internal model reasoning every time.

## Why It Matters

### The Reliability Gap

| Dimension | LLM self-reasoning | Deterministic structure |
|-----------|-------------------|------------------------|
| Consistency | varies by temperature/prompt/context noise | identical output for identical input |
| Drift risk | high — categories shift across turns | zero — rules are static |
| Auditability | opaque chain-of-thought | traceable rule match + log |
| Latency | variable, depends on output length | fixed O(n) for regex or dict lookup |
| Determinism | stochastic (even at temp=0, subtle platform differences) | bit-identical across runs |

### Exocortex Implementation Examples

| Component | Source Path | Mechanism |
|-----------|-------------|----------|
| BST Classifier | `/a0/plugins/_bst_classifier/bst_classifier.py` | regex phrase signals for domain classification; no LLM self-reasoning |
| Supervisor Loop | `_50_supervisor_loop.py:14-38` | deterministic error-category mapping with anti-actions per category |
| Injection Gate | `injection_gate_agent_interface_spec.md` | 3-phase context management triggered by turn count & domain stability |
| Sleep Consolidation | `/a0/usr/Exocortex/sleep_consolidation.py` | Phases 0–3: staging lifecycle, dedup, episode chunking, interaction modeling — all deterministic |

## Measurement Framework

A deterministic rule's quality can be measured with four metrics:

1. **Precision:** of all interventions triggered, what fraction were correct?
2. **Recall:** of all conditions that should have triggered an intervention, what fraction did?
3. **False-positive rate:** interventions triggered when no problem existed (target: <5%)
4. **Latency overhead:** how much time does the check add to the tool call pipeline?

For BST classification, we can measure precision/recall by comparing against a manually labeled gold set of 100 agent turns stored in `eval/bst_gold_labels.jsonl` (to be created). For supervisor loop anti-actions, log each intervention with the agent's actual error vs. the anti-action applied, then compute per-category precision quarterly.

**Current metric baselines (estimated):**
- BST accuracy: ~92% (based on observed classifications; no formal eval yet)
- Supervisor precision: ~85% (most error classes map correctly, but exhaustion detection has false positives)
- Injection gate latency: <2ms per turn (regex-based, well within budget)

**Measurement harness:** The regression monitor at `/a0/usr/workdir/self-improvement/regression_monitor.sh` checks that extension files exist and have expected line counts, but does not currently evaluate classification quality. A `bst_evaluator.py` script (to be written) would fill this gap.

## Edge Cases & Limitations

### Known Blind Spots

1. **New signal vocabulary:** If Jake introduces a new domain term (e.g., "orbital-analysis"), BST won't match it until regex patterns are updated. The signal-discovery pipeline (Phase 4 of build plan) should detect unclassified turns and flag them for review.

2. **Ambiguous turns:** A single turn containing both debugging and research language can produce compound signatures. The current compound resolver uses a simple priority rule (investigation > debugging > analysis). Multi-label classification with confidence thresholds would be more accurate but increases complexity.

3. **Regex fragility:** Regex rules don't understand negation. "I'm NOT debugging" still registers the "debugging" signal. A thin NLP layer (negation detection, lemmatization) could reduce false positives without sacrificing determinism.

4. **Latency at scale:** With 50+ extension hooks in the tool-execute pipeline, deterministic checks add cumulative latency. The current hook execution order is sequential; parallelization would require concurrency management but could reduce overhead by 30-40%.

### When Deterministic Rules Fail

There are cases where deterministic rules produce worse outcomes than LLM judgment:

- **Novel error patterns** that don't match any supervisor category result in fallback behavior (log and continue). The LLM's error comprehension might catch these, but the deterministic layer missed them.
- **Temporal context** (e.g., "this error is acceptable because we're in a test environment") is not captured by current deterministic rules.
- **User intent shift** mid-conversation may invalidate previously correct classifications without the deterministic system noticing.

These failures should be tracked via the incident wiki pages (e.g., [[inc-watchdog-blind]]) and fed back into rule refinement.

## When to Stay Deterministic vs. When to Use LLM Judgment

| Task Type | Deterministic | LLM | Reasoning |
|-----------|---------------|-----|-----------|
| Domain classification | Yes | No | Need consistent, auditable labels |
| Error categorization | Yes (common cases) | Yes (novel cases) | Hybrid: known patterns matched, unknowns escalated |
| Context enrichment | Yes (template fill) | Yes (analysis) | Structural enrichment is deterministic; analytical enrichment uses LLM |
| Safety/refusal checks | Yes | No | Must be fast and auditable; no LLM in the critical path |
| Quality assessment | No | Yes | Requires nuanced judgment |

## Connection to Other Concepts

- [[supervisor-loop]] — graduated tier escalation (WARN=3, SUMMARIZE=6, RESET=9)
- [[bst-classifier]] — deterministic domain classification via phrase signals
- [[stateful-injection]] — persistent state objects updated incrementally
- [[error-comprehension]] — when deterministic rules miss, LLM-based error understanding fills gaps
- [[hook-execution-order-determinism]] — execution order guarantees for deterministic pipeline

## Verification Status
Last verified: 2026-05-10. Anti-action categories traced to `_50_supervisor_loop.py` lines 14-38. BST mechanism confirmed in `bst_classifier.py`. Injection gate spec at `injection_gate_agent_interface_spec.md`. Sleep consolidation phases 0-3 confirmed in `/a0/usr/Exocortex/sleep_consolidation.py`.

## Implementation Status

**Last Reviewed:** 2026-05-10T01:33Z

This is a conceptual page — no direct code component. The design patterns described here are implemented in the Exocortex BST pipeline and injection gate. Any deviations from spec should be tracked via the Exocortex regression monitor.

## Exocortex Integration

This concept is a dependency of the Injection Gate pipeline. Any modification to its definition should trigger a regression check against the injection gate test suite (`_50_supervisor_loop.py`, `_19_context_pruner.py`). The regression monitor at `/a0/usr/workdir/self-improvement/regression_monitor.sh` includes this page in its wiki integrity checks.

## Open Questions

- Can we formalize a feedback loop to measure the accuracy of deterministic rules against ground truth labels? (Requires building `bst_gold_labels.jsonl`)
- What is the performance cost (latency) of the current regex-based classifiers under load, and would a trie-based matcher (e.g., `pyahocorasick`) reduce it?
- Are there edge cases where the deterministic scaffolding fails to capture nuance that the LLM would handle correctly? (See Edge Cases section above)
- How should we handle negation in signal detection — a pre-filter step or per-pattern negative lookaheads?
- At what scale (number of hooks, turns per session) does sequential deterministic processing become a bottleneck?
