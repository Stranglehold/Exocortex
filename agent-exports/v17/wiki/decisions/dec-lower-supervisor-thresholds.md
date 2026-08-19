# Decision: Lower Supervisor Intervention Thresholds (Qwen3.6)
**Created:** 2026-04-28T01:25Z
**Last deepened:** 2026-05-10 (cycle 19)
**Status**: Empirical decision — recovery rate insufficient at current thresholds.
**Category**: Adaptive supervisor tuning.
## Problem Statement
Current supervisor L2/L3 intervention thresholds trigger too late for Qwen3.6 behavior patterns. Recovery rate sits at 33% meaning that once agent enters degradation trajectory only 1 in 3 interventions successfully restore productive output before context budget exhausted or hard truncation occurs.
## Decision
Lower CUSUM accumulator threshold for L2 nudge from current value (score >0.6) to more aggressive trigger point (score >0.4). Lower L3 surgery threshold similarly to enable earlier intervention before degradation compounds across turns.
## Rationale
- Earlier intervention window: Qwen3.6 shows faster trajectory drift than larger models — waiting for score >0.6 means degradation already entrenched by intervention time; dropping to 0.4 catches drift during early signal phase not late failure state
- Empirical target: aim for recovery rate improvement from 33% to >50% with lower thresholds validated on same eval set as enrichment tests
- Cost tradeoff acceptable: more frequent L2 nudges cost ~15 tokens each but prevent full surgery events costing ~400+ tokens in context clearing and state reset

## Implementation Architecture
### CUSUM Accumulator Configuration
The supervisor loop maintains a CUSUM (Cumulative Sum) accumulator that tracks deviation from baseline agent behavior across turns:

```
CUSUM[t] = max(0, CUSUM[t-1] + (score[t] - drift_baseline))
```

Intervention thresholds operate as:
- **L1 (no intervention)**: CUSUM < 0.4 — agent performing normally
- **L2 (nudge)**: 0.4 ≤ CUSUM < 0.7 — inject corrective context ("Review the last tool output for accuracy. Consider whether an alternative approach would be more effective.")
- **L3 (surgery)**: CUSUM ≥ 0.7 — clear recent context, reload key scaffolding state, force retry with minimal injection

### Threshold Migration
The configuration change moves the L2 boundary from 0.6 to 0.4, creating a 50% wider intervention window. The L3 threshold remains at 0.7 to prevent premature surgery. Implementation in `supervisor_config.json`:

```json
{
  "cusum": {
    "drift_baseline": 0.15,
    "thresholds": {
      "L1_max": 0.4,
      "L2_max": 0.7,
      "L3_min": 0.7
    },
    "calibration_note": "L1→L2 boundary lowered from 0.6 to 0.4 per Qwen3.6 tuning (2026-04-28)"
  }
}
```

## Cross-Component Interactions
| Component | Interaction Type | Description |
|-----------|-----------------|-------------|
| **supervisor-loop** | Hosts | CUSUM accumulator and intervention ladder reside here; threshold changes alter intervention frequency and timing |
| **entropy-as-signal** | Informs | Entropy measurements on streaming output feed into score[t] calculation; earlier threshold means entropy spikes trigger interventions sooner |
| **stuck-delivery** | Consumes | When supervisor L3 surgery triggers, stuck-delivery detection is reset; earlier surgery may reduce stuck-delivery incidents by preempting context saturation |
| **context-pruner** | Coordinates | L2 nudges often include pruning suggestions; lower threshold means more frequent pruning signals, potentially reducing context bloat proactively |
| **error-comprehension** | Records | Tier 4 captures intervention events as learning signals; increased intervention frequency provides more training data for pattern recognition |

## Metrics Tracking
| Metric | Before (L2=0.6) | After (L2=0.4) | Target |
|--------|-----------------|-----------------|--------|
| Recovery rate | 33% | TBD (aiming >50%) | >50% |
| L2 intervention frequency | ~1 per 8 turns | ~1 per 4 turns | Monitor for over-intervention |
| L3 surgery frequency | ~1 per 20 turns | Expected to decrease | <1 per 30 turns |
| Token cost per L2 nudge | 15 tokens | 15 tokens | Acceptable |
| Token cost per L3 surgery | 400+ tokens | 400+ tokens (but fewer surgeries) | Net reduction expected |
| False positive rate | <5% | Monitor — target <10% | <10% |
| Calibration period | — | 2 weeks post-change | Steady-state by day 14 |

## Meta-Lesson: Drift Speed Is Model-Specific
This decision revealed a calibration principle:
- **Drift speed varies by model architecture** — Qwen3.6 degrades faster than Qwen3.5 and QwQ-32B under identical task loads. Smaller parameter count correlates with faster trajectory drift.
- **One-size thresholds are wrong** — supervisor thresholds must be per-model, validated against empirical degradation curves not theoretical assumptions.
- **Early intervention is cheaper** — the token cost of more frequent L2 nudges is dwarfed by the token savings from preventing even one L3 surgery event. The economics favor aggressive nudge thresholds.
- **Monitor false positives** — the primary risk is over-intervention degrading normal performance; must track false positive rate and back off if nudge frequency causes output quality regression.

## Consequences
- Increased false positive intervention risk — some turns classified as degrading that would have self-corrected; monitor for over-correction pattern where interventions themselves degrade output quality
- Requires calibration period of 2 weeks after threshold change before re-tuning to allow steady-state metrics to stabilize
- Per-model threshold table needed because different architectures drift at different rates — Qwen3.5 vs Qwen3.6 show measurably different degradation curves
## Connection to Other Concepts
- [[supervisor-loop]] directly affects CUSUM accumulator trigger points and intervention escalation ladder
- [[entropy-as-signal]] lower thresholds align with earlier entropy-based detection in streaming-hallucination research (first-token window)
- [[stuck-delivery]] earlier L2/L3 intervention may reduce stuck delivery incidents by preventing context saturation before it occurs
- [[error-comprehension]] increased intervention frequency provides more Tier 4 training data for error pattern recognition

## Verification Status
Last verified: 2026-05-10. Verification status block updated per program.md Rule 1 improvement cycle.
