# LLM Self-Correction & Error Recovery Mechanisms

## Status: RESEARCHED + SYSTEM GAP DOCUMENTED

## Summary

The Exocortex plugin contains **no explicit self-correction or error-recovery mechanisms** in its source code. This is a known architectural gap. The broader LLM research landscape (2025-2026) shows active development in self-correction, with several promising approaches that could inform future Exocortex improvements.

## What Exists Today (Exocortex Plugin)

| Component | Error Handling Approach | Limitation |
|-----------|----------------------|----------|
| HTN Plan Selector | Retry loops (attempt 1/3) | Exhausts then escalates, no adaptive retry |
| Supervisor Loop | Stall detection, loop detection | Reactive — fires only after threshold breach |
| Context Watchdog | Token utilization warnings (70%/85%) | Warning only, no auto-remediation |
| Working Memory | Entity decay/promotion | No corruption detection |
| Belief State Tracker | Signal discrimination | No self-validation |

## Research Landscape: LLM Self-Correction (2025-2026)

### Key Findings

**Accuracy-Correction Paradox** (Wang et al., arXiv:2601.00828, Jan 2026):
- Weaker models achieve 1.6x higher intrinsic correction rates than stronger models
- GPT-3.5 (66% accuracy): 26.8% self-correction rate
- DeepSeek (94% accuracy): 16.7% self-correction rate
- Proposed **Error Depth Hypothesis**: stronger models make fewer but deeper errors that resist self-correction

**Verification & Internal States** (arXiv:2604.22271, Apr 2026):
- Verbal confidence does NOT reliably predict verification or self-correction outcomes
- Internal activation states are better predictors than surface-level confidence signals
- Implication: Exocortex belief-state tracker could use activation-based confidence rather than verbal

**Feedback Control Dynamics** (arXiv:2604.22273, Apr 2026):
- Iterative self-correction as a feedback control system
- Stability analysis shows repeated refinement can DEGRADE performance if error dynamics are unstable
- Need confidence-weighted retry rather than fixed-count retry

**RL-Based Self-Correction** (OpenReview SCoRe):
- Multi-turn online RL approach (SCoRe) improves self-correction using entirely self-generated data
- No external model or supervision needed
- Applicable to Exocortex: could train plugin to self-correct working memory states

**Mixed Strategy Benchmarking** (arXiv:2510.16062, Oct 2025):
- Self-correction improves accuracy, especially for complex reasoning tasks
- Mixing different self-correction strategies yields further improvements but reduces efficiency
- Reasoning LLMs (DeepSeek-R1) show limited optimization under self-correction

### Implications for Exocortex

1. **Adaptive retry with confidence weighting** — replace fixed 3-attempt HTN retry with confidence-weighted retry
2. **Activation-based state validation** — use internal confidence signals rather than verbal self-assessment
3. **Circuit breaker pattern** — prevent error cascade when self-correction becomes unstable
4. **Selective self-correction** — not all errors benefit from self-correction; route by error depth
5. **Graceful degradation** — fallback modes when components fail rather than hard escalation

## What's Missing (Exocortex)

1. **Self-healing**: No mechanism to detect and repair degraded plugin state
2. **Adaptive retry**: HTN retries are fixed-count, not confidence-weighted
3. **Graceful degradation**: No fallback mode when components fail
4. **State validation**: No checksums or integrity checks on working memory
5. **Auto-recovery**: No restart/reinitialization of failed extension modules

## Recommended Future Work

1. Implement `on_error` hooks per extension module
2. Add working memory integrity validation (hash-based)
3. Build adaptive retry with exponential backoff for HTN plans
4. Create circuit-breaker pattern for plugin modules
5. Add self-diagnostic endpoint for runtime health checks

## Cross-References

- [[dec-oss-dispatch-bug.md]] — recent decision log showing dispatch bug resolution
- [[architecture-overview.md]] — component dependency map
- [[consolidation-idempotency.md]] — consolidation stability validated 5+ cycles

---
*Updated: 2026-05-09 | Cycle 25+ Workshop | Confidence: HIGH (source grep + 6 papers reviewed)*
