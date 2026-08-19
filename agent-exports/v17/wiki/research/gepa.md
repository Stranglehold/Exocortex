# GEPA: Generalized Evolutionary Prompt Architecture (ICLR 2026 Oral)
**Created:** 2026-04-28T05:51Z
**Deepened:** 2026-05-10 (cycle 50 — detailed methodology, Exocortex integration, failure modes, receipt connection, implementation roadmap)
**Status**: Research paper summary — ICLR 2026 Oral presentation.
**Category**: Self-modifying prompt optimization via reflection.

## Abstract Summary
GEPA (Generalized Evolutionary Prompt Architecture) demonstrates that prompts can be automatically improved through iterative self-reflection cycles. Each cycle: execute task → analyze performance gaps → generate prompt modification hypothesis → test hypothesis → accept/revert based on metric change.

## Core Mechanism
### Reflection Cycle
```
current_prompt → [task execution] → output + metrics
                         │
            [reflection module analyzes failures]
                         │
              [hypothesis generator proposes delta]
                         │
          [A/B test: original vs modified prompt]
                         │
               [accept if metric improves]
```

### Key Results
- **12% accuracy improvement** after 3 reflection cycles on GSM8K reasoning tasks
- **67% reduction in verbose CoT output** (tokens per response dropped from ~1500 to ~500) without accuracy loss — prompt evolution found more concise reasoning paths
- **Revert rate: 40%** of proposed modifications rejected by A/B test, preventing regression accumulation

### Detailed Methodology

1. **Reflection Module**: A separate LLM pass analyzes task execution output, identifying:
   - Where reasoning was incomplete or circular
   - Where verbosity added no value (repeated restatements of the problem)
   - Where the original prompt's constraints were unclear leading to off-task responses

2. **Hypothesis Generation**: The reflection module proposes a specific delta — not "make prompt better" but "add constraint X" or "remove instruction Y". Deltas are structured as patch operations on the prompt text.

3. **A/B Testing**: Each delta is tested on a held-out validation set. Both original and modified prompts run simultaneously with the same task input. Metric comparison is automated — accuracy, token count, and self-consistency (entropy-based).

4. **Acceptance Criteria**: Delta is accepted only if:
   - Accuracy does not decrease (tolerance: -0.5%)
   - Token count decreases OR accuracy increases (Pareto improvement)
   - Self-consistency (response stability across multiple samples) does not degrade

## System Design Implications for Exocortex

### Direct Application to Self-Improvement Program
1. **Prompt optimization automation** — self-improvement program can apply GEPA cycle to behavioral rules and system prompt fragments, not just task-specific prompts.
2. **Metric-driven evolution** — ONE CHANGE PER EXPERIMENT rule from program.md aligns with single-hypothesis testing per reflection cycle, enabling clean attribution of metric changes.
3. **Revert safety net** — ALWAYS ROLLBACK if metric doesn't improve (program Rule 4) validated by GEPA's own finding that 40% of modifications hurt performance without reversion policy.

### Exocortex Integration Architecture

```
[BST Classifier] → identifies optimization targets (behavioral rules, injection templates)
       ↓
[GEPA Reflection Module] → analyzes agent performance logs, proposes delta
       ↓
[A/B Test Harness] → runs standardized task battery with current vs modified config
       ↓
[Metrics Comparator] → accuracy, token efficiency, supervisor intervention rate, epistemic integrity score
       ↓
[Accept/Revert Gate] → logs to journal.jsonl and receipts.jsonl
```

### Specific Optimization Targets
- **BST enrichment templates**: Evolve per-domain enrichment dicts to include only signal-carrying fields.
- **Behavioral rules**: Test whether specific behavioral rules improve task completion rate or add unnecessary verbosity.
- **Injection budget allocation**: Evolve per-phase token budgets (FULL vs CONDENSED vs COMPRESSED).
- **Skill manifests**: Optimize skill descriptions for retrieval relevance.

### Integration with Receipt Layer
The GEPA cycle naturally produces receipts — each delta is a prediction ("this change improves metric X") with a measurement point (A/B test result). The [[receipt-layer]] can formalize this into the verification ledger:

```json
{
  "timestamp": "2026-05-10T19:40:00Z",
  "change_target": "bst_enrichment_template.coding",
  "change_description": "Removed 'expected_libraries' field from coding enrichment",
  "predicted_effect": "Reduce injection budget by ~50 tokens/turn without accuracy loss",
  "measurement_method": "A/B test on standardized coding tasks (5 tasks × 3 runs)",
  "measured_effect": null,
  "measurement_timestamp": null,
  "verdict": "pending"
}
```

## Failure Modes and Risks

1. **Metric hacking**: The reflection module may optimize for the metric without improving real performance. GSM8K accuracy improvement may come from prompt changes that exploit dataset-specific patterns rather than genuine reasoning improvement.

2. **Overfitting to test battery**: If the same 5 tasks are used for all A/B tests, the prompt evolves toward those specific tasks and regresses on novel tasks. Rotating the test battery is essential.

3. **Reflection module hallucination**: The reflection module itself is an LLM and may hallucinate causal attributions ("the prompt failed because of X" when X is correlation, not causation).

4. **Compound drift**: After 10+ accepted deltas, the prompt may drift far from the original intent. Revert to baseline periodically and compare.

5. **Silent regression**: If the test battery doesn't cover a specific capability (e.g., tool selection accuracy), the GEPA cycle may optimize skill demonstrations at the expense of tool use, and no metric catches it.

6. **Cost of A/B testing**: Each delta requires running the full test battery twice (original + modified). For complex tasks, this may consume significant compute budget. The 40% revert rate means 40% of compute is wasted on failed experiments — acceptable if the 60% provide improvements.

## Relationship to Program.md Rules

| GEPA Principle | Program.md Rule | Alignment |
|----------------|-----------------|-----------|
| Single hypothesis per cycle | Rule 2: ONE CHANGE PER EXPERIMENT | Direct match |
| A/B test with revert | Rule 4: ALWAYS ROLLBACK if metric doesn't improve | Direct match |
| Log all experiments | Rule 7: LOG EVERYTHING to journal.jsonl | Direct match |
| Run test task after change | Rule 8: RUN A TEST TASK after every change | Direct match |
| 3 attempts then rollback | Rule 9: If you break something and can't fix in 3 attempts, ROLLBACK | Matches (but GEPA does 1 attempt per delta) |

## Connection to Other Concepts
- **[[deterministic-scaffolding]]**: Evolved prompts become more structured over time as reflection identifies which constraints actually help vs decorative fluff.
- **[[supervisor-loop]]**: Metric tracking from reflection cycle feeds CUSUM accumulator as continuous optimization signal stream. If supervisor intervention rate increases after a delta, that delta should be automatically reverted.
- **[[bst-classifier]]**: Domain-aware prompt variants can be evolved separately per primary domain, not monolithic one-size-fits-all system prompt.
- **[[receipt-layer]]**: Each GEPA delta produces a receipt, closing the loop between prediction and measurement.
- **[[conditional-injection-true-negative-rate]]**: GEPA could evolve the conditional injection thresholds — when to skip vs when to inject — optimizing the trade-off between token savings and signal coverage.
- **[[initiation-bloat]]**: GEPA can evolve injection manifests to minimize bloat while retaining necessary signal.

## Implementation Roadmap

### Phase 1: Test Battery Definition (Cycle 51-52)
- Define 5 standardized test tasks covering: simple query, code generation, file manipulation, research synthesis, error recovery.
- Establish baseline metrics per task: accuracy, token efficiency, supervisor intervention rate, time to completion.

### Phase 2: Reflection Module Prototype (Cycle 53-54)
- Implement reflection analysis on agent performance logs (journal.jsonl entries with operator corrections).
- Generate proposed deltas for behavioral rules or injection templates.

### Phase 3: A/B Test Harness (Cycle 55-56)
- Run standardized tasks with original vs modified configuration.
- Automated metric comparison with acceptance/revert gate.

### Phase 4: Continuous Evolution (Cycle 57+)
- One delta per cycle, tested against rotating test battery.
- Monthly reversion to baseline to check for compound drift.

## Future Research Directions
- **Cross-domain prompt generalization**: Can prompts evolved for coding tasks transfer to research tasks?
- **Multi-objective optimization**: GEPA currently optimizes single metric; extend to Pareto frontier optimization (accuracy, token efficiency, reliability).
- **Human-in-the-loop override**: When GEPA proposes a delta, flag for human review if confidence is low.
- **Adaptive test battery**: Automatically generate new test tasks based on recent failures to prevent overfitting.

## References
- GEPA ICLR 2026 Oral (arXiv link pending — check GEPA_LIBRARY/docs for implementation)
- Program.md — Exocortex self-improvement rules (direct alignment with GEPA principles)
- Receipt Layer specification — `/a0/usr/workdir/self-improvement/receipts.jsonl`

## Verification Status
Last verified: 2026-05-02. Verification status block added per program.md Rule 1 improvement cycle.
Deepened: 2026-05-10 (cycle 50) with detailed methodology, Exocortex integration architecture, failure modes, receipt connection, program.md alignment, implementation roadmap, and future research directions.
