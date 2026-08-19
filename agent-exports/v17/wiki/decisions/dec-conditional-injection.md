# Decision: Conditional Injection — Skip When No Signal

**Created:** 2026-04-28T01:25Z
**Deepened:** 2026-05-10 (cycle 15 — implementation status, calibration plan, metric tracking, downstream interactions)
**Status:** Architectural decision — extension injection optimization.
**Category:** Context budget management.

## Problem Statement

Current architecture merges all active extensions into a single injected block regardless of whether any individual extension has actionable signal for the current turn. This wastes ~30% of injection budget on turns where BST is stable, memory recall is empty, and tool registry unchanged since last turn.

## Decision

Implement per-extension conditional gating: each extension outputs `(signal_present: bool, delta_content)` tuple. Injection assembler skips extensions with no signal rather than injecting placeholder or stale content. Extensions are never merged into a monolithic block — kept as separate conditionally-rendered sections.

## Rationale

- **Budget savings measurable:** Internal audit showed 30% of turns have zero active signals across BST, memory, and registry simultaneously. Skipping injection on those turns saves ~250 tokens average per turn, compounding to significant context preservation over long conversations.
- **Signal isolation benefits debugging:** When each extension renders separately, you can identify which specific system is contributing noise vs. signal — not just aggregate "injection block" blame.
- **Delta-only updates align with stateful-injection principle:** Send only what changed since last turn, not full state rebuild.

## Implementation Status

- **Location:** Extension `_20_injector.py` in the `before_main_llm_call` hook path.
- **Current behavior:** The injector evaluates per-extension signal flags from BST, memory, and tool registry hooks.
- **Gating logic:** If `signal_present == False` for all registered extensions on a given turn, the injection block is omitted entirely (still logging the skip to injection budget header).
- **Injection budget header:** Always includes turn count and timestamp for temporal proprioception even on skipped turns — the minimum injection floor.

## Calibration Plan (Unfinished)

- **False negative risk:** If `signal_present` threshold is too strict, useful context gets dropped. False negatives (no_signal when content would help) are worse than false positives (injecting when nothing changed).
- **Calibration period:** Requires logging run with verbose signal-present decisions to measure accuracy.
- **Sensitivity tuning:** Thresholds should be per-extension, not global. BST has different noise characteristics than memory or tool registry.

## Metric Tracking

- `skip_rate`: fraction of turns where injection block omitted (target: ~30% as measured in audit).
- `false_skip_rate`: unknown — requires calibration data. If agent ever asks a question that was answered in skipped content, that's a false skip.
- `avg_tokens_saved_per_skip`: ~250 tokens (audit estimate).

## Consequences

- **Requires refactoring injection assembler:** From monolithic merge to conditional per-extension evaluation — non-trivial code change but contained in a single module.
- **Risk of missed context:** When signal detection is too strict. False negative worse than false positive; needs calibration period with logging enabled.
- **Minimum injection floor:** Even on quiet turns, inject timestamp + turn count for temporal proprioception scaffolding (per temporal-proprioception findings).

## Interactions with Other Components

- **BST classifier:** Drives primary signal; momentum tracking affects how frequently BST re-evaluates, which in turn affects injection freshness.
- **Stateful injection:** Delta-only updates reduce per-turn overhead, enabling longer conversation lifetimes before context exhaustion.
- **Context pruner:** Conditional injection complements downstream pruning by reducing _what needs pruning_ — upstream prevention rather than post-hoc compression.
- **Injection gate:** Budget management layer that enforces token limits; conditional injection reduces pressure on the gate by never submitting stale content.

## Connection to Other Concepts

- [[stateful-injection]] — delta-only updates reduce per-turn overhead.
- [[context-pruner]] — upstream prevention complements downstream compression.
- [[temporal-proprioception]] — minimum floor guarantees turn awareness even on skipped turns.
- [[injection-gate]] — budget enforcement layer that benefits from conditional skipping.

## Verification Status

Last verified: 2026-05-02. Verification status block added per program.md Rule 1 improvement cycle.
Deepened: 2026-05-10 with implementation status, calibration plan, metric tracking, and downstream interaction mapping.

## Edge Cases & Failure Modes

1. **BST momentum lock + stable signal**: When BST remains in the same domain for >5 turns, `signal_present` may remain True even though no new information is provided. This causes injection of stale content, wasting tokens. (Related: [[inc-bst-momentum-lock]])
2. **Memory recall burst**: A single high-signal memory query may trigger injection on that turn but subsequent turns with no new recall are skipped correctly. However, if memory recall fails partially, the injector may skip a turn where partial context would have been useful.
3. **Tool registry updates**: When a skill is loaded mid-conversation, the registry changes but the injector may not detect the update as 'signal' if the timestamp check is too coarse (debounce window). Mitigation: reduce debounce to 500ms.

## Future Work

- Implement per-extension calibration windows (currently global threshold for signal present determination).
- Add per-turn signal justification logging for post-hoc audit — allows supervisor to correlate skips with operator corrections.
- Explore rule-based signal detectors for deterministic extensions (e.g., clock-based injection for [[temporal-proprioception]]).
- Calibrate false_skip_rate metric using production data over 10 cycles.

## Testing Strategy

- Unit tests for signal detection per extension with stubbed inputs.
- Integration test for turn sequences where alternating signal/no-signal patterns trigger correct conditional injection behavior.
- Regression test: ensure minimum injection floor (timestamp + turn count) is never omitted, even when all extensions have signal_present=false.

## Threshold Justification
Empirical testing during cycles 15-20 established current thresholds:
| Metric | Value | Justification |
|--------|-------|---------------|
| BST confidence skip threshold | < 0.5 | Below 0.5, classification is no better than random |
| Minimum enrichment frequency | Every 5 turns | Prevents extended periods without any enrichment |
| Re-enrichment trigger | Δ > 0.3 confidence | When BST changes classification meaningfully |

## Interaction with Other Extensions
1. **Supervisor Loop**: When enrichment is skipped, supervisor is notified and may escalate if behavior indicates confusion (high entropy, tool misuse).
2. **Epistemic Integrity**: Without enrichment, agent relies more on internal knowledge. EI tracks unsourced claims generated during enrichment-skipped turns.
3. **Context Pruner**: Fewer enrichment blocks mean less context to prune, reducing pruner workload.
4. **BST Classifier**: The BST benefits from reduced context pressure — without its own enrichment block, it has more room to analyze tasks.

## Open Questions
- Should enrichment be skipped for simple queries (BST complexity="simple") regardless of confidence?
- Does the 5-turn minimum provide sufficient guard against misclassification?
- Could epistemic integrity flags serve as a back-channel to re-trigger enrichment before the 5-turn minimum?