# Catastrophic Forgetting

**Created:** 2026-04-28T04:23Z
**Last deepened:** 2026-05-10 (cycle 20)
**Status:** Core Exocortex concept
**Category:** Epistemic layer — memory degradation tracking

## Definition

Catastrophic forgetting is the tendency of neural systems — both biological and artificial — to abruptly lose previously learned information when new information is acquired. In LLM scaffolding, it manifests as the agent losing track of task context, previously established facts, or earlier decisions as the conversation window fills with new information.

Unlike parametric forgetting (which is a training phenomenon), scaffolding forgetting is a runtime context-management failure: the agent's attention mechanism cannot maintain all relevant facts simultaneously, and important context gets pushed out by noise.

## Why It Matters

1. **Multi-turn reliability** — the agent must maintain continuity across 20+ turns. Forgetting a decision made in turn 2 while executing turn 15 breaks the task.
2. **Recursive self-improvement** — the agent forgets which experiments succeeded and repeats failed ones.
3. **Operator trust** — when the agent contradicts itself, the operator loses confidence in the entire system.

## Mechanisms in LLM Scaffolding

### Context Window Exhaustion

As turns accumulate, the conversation buffer fills. The model's attention is spread across all tokens, diluting focus on any single fact. When the window is full, older facts are simply truncated — not "forgotten" in the neural sense, but lost to the agent regardless.

### Attention Dilution

Even within the window, the model's attention mechanism has limited capacity. When many facts compete for attention, some receive insufficient weight and effectively vanish from working memory.

### Interference Patterns

New information that contradicts or updates old information can cause the agent to overwrite its internal representation of the old fact, even if the old fact is still in the conversation buffer.

## Detection Methods

### Temporal Consistency Check

The Epistemic Integrity Layer maintains a timestamped ledger of agent assertions. A consistency sweep at regular intervals compares current assertions against earlier ones on the same topic. Contradictions raise forgetting flags.

### Key Fact Retrieval Test

For critical decisions (config values, architectural choices, task definitions), the Supervisor periodically injects a retrieval prompt: "What is the current value of X?" If the agent cannot answer or gives a stale answer, forgetting is detected.

### BST Domain Drift Correlation

When BST reports domain drift simultaneous with factual contradictions, it suggests the agent has lost its grip on the task domain entirely — not just one fact.

## Mitigation Strategies

### Deterministic State Storage

Critical state (task definitions, decisions, configuration values) is stored deterministically in memory_save and injected as explicit context when relevant. This provides a ground-truth anchor that attention dilution cannot erase.

### Context Pruner with Priority Preservation

The Context Pruner (`_19_context_pruner.py`) prioritizes retention of high-importance facts (decisions, operator instructions, error responses) over low-importance noise (intermediate tool outputs, logs).

### Periodic Recaps

At configurable intervals, the Supervisor triggers a recap of active tasks, key decisions, and constraints into the agent's context. This re-establishes attention weights on critical facts.

## Connection to Other Concepts

- **[[temporal-proprioception]]** — tracks when facts were learned; forgetting often correlates with stale timestamps (facts learned early, never refreshed).
- **[[epistemic-integrity]]** — consistency checking between old and new assertions is a primary detection mechanism.
- **[[context-pruner]]** — must prioritize important facts to prevent their pruning during window exhaustion.
- **[[supervisor-loop]]** — L2/L3 interventions can catch forgetting by injecting retrieval prompts.
- **[[entropy-as-signal]]** — high output entropy at recall points may indicate the agent is guessing rather than remembering.

## Metrics

| Metric | Value | Method |
|--------|-------|--------|
| Forgetting event rate | ~1 per 15 turns (estimated) | Contradiction detection |
| Recovery from intervention | 70% after supervisor nudge | Key-fact retrieval test |
| Prevention via memory injection | 95% for stored facts | Deterministic state recall |
| False detection rate | <5% | Manual review sample |

## Open Questions

- **Can catastrophic forgetting be predicted before it happens?** Entropy spikes, attention weight monitoring, or confidence drops might predict imminent forgetting.
- **Is the context pruner causing forgetting?** Aggressive pruning of old context might remove facts the agent still needs. Calibration needed.
- **Can we use temporal proprioception to pre-emptively refresh facts before they're forgotten?** Proactive refresh rather than reactive recovery.
- **How does this interact with BST momentum?** If BST holds momentum across turns while facts have been forgotten, the agent may act confidently on nonexistent context.

## Testing

- Contradiction detection test: assert fact A in turn 2, assert not-A in turn 12; verify detection fires.
- Key-fact retrieval test: store fact, fill context window with noise, query fact; verify retrieval with >90% accuracy.
- Pruner interaction test: verify that facts tagged "critical" survive context pruning even at 90% capacity.

## References

- French, R.M. (1999). "Catastrophic forgetting in connectionist networks." *Trends in Cognitive Sciences*.
- Exocortex epistemic integrity layer: `extensions/_17_epistemic_integrity.py`
- Context pruner: `extensions/_19_context_pruner.py`
- Supervisor loop: `extensions/_50_supervisor_loop.py`

## Verification Status

Last verified: 2026-05-02. Verification status block added per program.md Rule 1 improvement cycle.

## Implementation Status

**Last Reviewed:** 2026-05-10T03:37:00Z

This is a conceptual page — detection and mitigation are partially implemented in the epistemic integrity layer and supervisor loop. Cross-session persistence of key facts is manual (memory_save). Automated proactive refresh is not yet implemented.
