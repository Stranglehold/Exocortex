# Decision: Enable Upstream Pruning

**Date:** 2026-04-28  
**Domain:** Context Management / Hook Pipeline  
**Status:** Deployed  
**Supersedes:** None  
**Superseded By:** None  

---

## Context

The Exocortex context pruning pipeline sits inside the hook chain that runs before each LLM tool call. Content flows through enrichment hooks, then pruning hooks, then injection hooks. The pruning stage reduces the token budget by removing low-utility content before it reaches the injection layer.

Two possible placement strategies exist:

1. **Upstream pruning (before enrichment):** Run pruning early in the hook chain, so enrichment only runs on high-utility content, saving enrichment compute and token cost at the enrichment stage itself.
2. **Downstream pruning (after enrichment):** Enrich everything first, then prune — more expensive but ensures no content is pruned before enrichment has a chance to assign utility.

## Decision

**Enable upstream pruning.** Place a pruning hook *before* the heaviest enrichment hooks in the chain. Specifically, the `_40_context_pruner` hook runs before `_50_enrichment_document`, `_52_enrichment_bst`, and `_53_enrichment_skills`.

## Rationale

- **Cost savings in enrichment:** The enrichment hooks perform significant work (parsing documents, querying BST memory, searching skill descriptions). Pruning low-utility content first prevents that compute from being wasted on content that will never reach the LLM.
- **Token budget preservation:** Every byte of context counts against the model's input limit. Running enrichment on pruned content consumes both enrichment token budget (for intermediate LLM calls within enrichment) and final context budget.
- **Measurable improvement:** In preliminary testing, upstream pruning reduced enrichment cost by ~38% without measurable degradation in injection quality (see Metrics below).
- **Simplicity over safety:** The concern that enrichment might discover high utility in content that initially appears low-utility was deemed low-risk because content utility signals (source, age, length, structural markers) correlate strongly enough with enrichment-boosted utility that false negatives are rare.

## Implementation Status

1. **Pruner hook reordering** — The `_40_context_pruner` hook's execution position was moved earlier in the hook chain in `config/hooks.json`. The original ordering had pruning at position 60.
2. **Metric instrumentation** — Added counters for `pruned_before_enrichment`, `enrichment_tokens_saved`, and `false_negative_prunes` (content pruned that would have been selected by enrichment).
3. **Regression test** — `test_hook_ordering.py` verifies that `_40_context_pruner` fires before `_50_enrichment_*` hooks.

## Metrics

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Avg tokens before enrichment | 12,400 | 7,680 | -38% |
| Avg enrichment time (ms) | 340 | 210 | -38% |
| False negative prunes (per session) | — | 0.2 | baseline |
| Final model output quality (human eval) | 4.1/5 | 4.0/5 | negligible |

## Downstream Interactions

- **Injection hooks:** The injection gate (`_60_injection_gate`) now receives pruned context that is ~38% smaller, reducing both token cost and noise.
- **BST enrichment:** `_52_enrichment_bst` runs on a smaller context window, improving BST signal-to-noise ratio.
- **Skill enrichment:** `_53_enrichment_skills` no longer loads skill descriptions for messages that will be pruned.
- **Context Pruner Component:** Must be monitored for calibration drift — if the population of messages changes (e.g., longer messages become more common), the per-domain thresholds may need recalibration.

## Known Limitations

1. **False negatives** occur when a message initially scored low by the pruner but would have been boosted by enrichment (e.g., a terse command that references a skill name not yet expanded). The false negative rate is 0.2 per session on average, which is below the 0.5/session mitigation trigger.
2. **Static thresholds** in the pruner are not adaptive to session length. Very long sessions may see gradual decline in recall as the pruning budget fills early.
3. **Enrichment quality** may degrade if the pruner thresholds drift too aggressive; regular monitoring is required.

## Related

- [[context-pruner]] — the pruner component itself
- [[context-pruning-architecture]] — broader pruning architecture
- [[conditional-injection-true-negative-rate]] — related injection quality metric
- [[dec-conditional-injection]] — sibling decision on conditional injection

## Decisions Log

- **2026-04-28** — Upstream pruning enabled after 2-week trial showed consistent enrichment cost savings with no measurable quality degradation.
- **2026-05-01** — Thresholds recalibrated after false negative rate crept to 0.4/session (still below 0.5 trigger).

## Implementation Details

### Hook Chain Ordering
Before upstream pruning is active, the hook chain after enrichment was:

```
msg -> enrichment_hooks (document, BST, skills) -> context_pruner -> injection_gate
```

After:

```
msg -> context_pruner (early) -> enrichment_hooks -> context_pruner (late) -> injection_gate
```

The early pruner removes clearly low-utility messages, saving enrichment compute. The late pruner catches any content that became low-utility after enrichment (rare).

### Calibration Process
1. Establish baseline false negative rate with no pruning (0% skip).
2. Run with incremental cut thresholds (percentile 20, 25, 30) and measure enrichment cost savings and output quality.
3. Select threshold that maximizes enrichment cost reduction while keeping false negatives below 0.5 per session.
4. Recalibrate every 5 cycles using the last 10 sessions of data.

## Failure Modes and Mitigations

1. **False negative (prune useful message)**: Rate 0.2/session. Mitigations: maintain threshold at conservative value, monitor via operator corrections logged in receipts. If rate rises above 0.5/session, rollback threshold.
2. **False positive (keep useless message)**: Not a safety issue, only a cost issue. Mitigations: if enrichment costs rise unexpectedly, check if pruner threshold is too permissive.
3. **Calibration drift**: As agent behavior or task domains change, the distribution of message utilities shifts. Scheduled recalibration (every 5 cycles) addresses this.
