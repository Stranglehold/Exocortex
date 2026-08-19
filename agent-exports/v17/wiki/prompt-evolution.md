# Prompt Evolution

**Created:** 2026-04-28T05:18Z | **Deepened:** 2026-05-10T03:45Z (cycle 22)
**Component** | **Hook:** monologue_end | **Type:** Adaptive constraint management

## Purpose

Prompt Evolution tracks which behavioral constraints fail during task execution and adapts them—tightening wording, adjusting injection timing, or elevating priority—so that the agent learns from past violations. It is the system’s memory of its own mistakes.

## Design Philosophy

The agent operates under a set of behavioral constraints: simplicity-first, surgical changes, think-before-coding, goal-driven execution, response structure, etc. These are injected as prompt text. When a constraint is violated, it indicates that the current wording was insufficient. Prompt Evolution closes that loop.

## Mechanism

### Constraint Registry
Each constraint is a named entity:
- **Name**: e.g., "simplicity_mandate"
- **Version**: integer, incremented on tightening
- **Text**: current injection text
- **Hook Placement**: where in the injection chain it appears (early = more influence)
- **Priority Tier**: 1 (essential), 2 (important), 3 (advisory)
- **Violation Count**: per-session tracker that decays over turns
- **Last Tightened**: timestamp
- **Success Rate**: percentage of turns where constraint was satisfied (computed over last N turns)

### Violation Detection Engine
Violations detected by:
- **Output Pattern Matching**: regex rules for simplicity violations (e.g., "could", "might", "consider" indicating speculative additions)
- **File Diff Analysis**: touching files outside the declared change set (surgical changes violation)
- **Post-hoc Verification**: after task completion, checking if intermediate steps produced unnecessary files
- **Epistemic Scorer**: feeds from [[epistemic-integrity]] for ungrounded claims
- **Supervisor Signals**: supervisor hard signals often correlate with constraint violations

Each violation increments the relevant constraint’s counter.

### Tightening Engine
When a constraint reaches its threshold (default: 3 violations within 50 turns), tightening is triggered:
1. **Wording Adjustment**: text becomes more emphatic, converts "should" to "must", adds explicit consequences ("...do NOT do X; violations logged and reset")
2. **Hook Placement Shift**: moved earlier in the injection chain (e.g., from post-thought to pre-thought) to influence earlier reasoning
3. **Priority Elevation**: if already highest, the constraint may be duplicated to appear in multiple hooks
4. **Version Increment**: new version written to constraint registry

Tightening is logged for post-hoc analysis.

### Relaxation (Anti-Tightening)
If a constraint has zero violations for 100+ turns, it may be relaxed to its original wording to reduce prompt bloat. This prevents constraints from becoming permanently draconian.

## Integration Points

- **Injection Gate (L3)**: Reads injection budget; if multiple constraints are tight, the gate may suppress low-priority ones to stay within budget.
- **Supervisor Loop (L4)**: Escalation from Tier 1 (warn) to Tier 2 (surgery) triggers batch constraint tightening for all constraints with violations.
- **Error Comprehension (L2)**: Structured error types (e.g., "simplicity_violation") map to specific constraints, enabling precise targeting.
- **Epistemic Integrity (L8)**: Ungrounded claim detection feeds directly into epistemic constraint evolution.
- **Stuck Delivery Detection**: When stuck delivery occurs, constraints may be temporarily relaxed to allow simpler delivery.

## Current Constraints Tracked

| Constraint | Threshold | Success Rate (last 100) | Current Version |
|------------|-----------|--------------------------|-----------------|
| simplicity_mandate | 3 | 92% | v2 |
| surgical_changes | 4 | 88% | v2 |
| think_before_coding | 3 | 95% | v1 |
| goal_driven_execution | 4 | 90% | v1 |
| response_structure | 3 | 97% | v1 |
| no_speculation | 3 | 94% | v2 |

## Configuration

Stored in `/a0/usr/Exocortex/config.json` under `prompt_evolution`:
- `threshold_per_constraint`: map of constraint name to violation count threshold
- `decay_rate`: how fast violation counters decay per turn (default 0.02)
- `relaxation_threshold`: turns without violation before relaxation considered
- `auto_relaxation`: boolean, whether to auto-relax (default false, operator review required)
- `log_all_tightenings`: boolean for audit trail

## Known Limitations

- **Reactive only** — cannot predict which constraints will fail next; no pre-emptive tightening
- **Single-constraint tuning** — tightens constraints individually rather than analyzing interaction effects (e.g., simplicity and surgical changes may conflict)
- **No meta-learning** — successful constraint adjustments don't inform future adjustment strategies (no "what worked for simplicity also works for goal-driven")
- **Prompt Bloat Risk** — repeated tightening increases injection length, potentially causing context pressure; must be balanced by injection gate
- **Constraint Interaction Blindness** — tightening one constraint may cause another to violate more (e.g., "be thorough" vs "be concise"); currently no detection of such correlations

## Future Directions

- **Predictive tightening**: use historical session data to predict which constraints are most likely to fail given current domain/task type
- **Constraint correlation analysis**: detect when tightening one causes others to fail, enabling coordinated adjustments
- **A/B testing framework**: run alternate constraint wordings in parallel meta-sessions to evaluate effectiveness
- **External calibration**: share anonymized constraint violation patterns across agent instances for collective tuning

## Related Concepts

- [[entropy-as-signal]] — theoretical foundation for measuring reasoning quality degradation
- [[injection-gate]] — budget management for constraint injection volume
- [[temporal-proprioception]] — progress measurement that detects when constraints aren't working
- [[epistemic-integrity]] — source of epistemic violation signals
- [[supervisor-loop]] — escalation triggers batch tightening

## Verification
Last verified: 2026-05-10. Deepened cycle 22 with constraint registry, violation detection engine, tightening/relaxation mechanics, integration map, configuration schema, and future directions.
