# Proactive Interference (PI) — Concept

## Definition
Proactive interference in LLMs occurs when previously processed but now-outdated information in the context window actively disrupts retrieval of current, relevant values. Unlike retroactive interference where new memories overwrite old ones, PI represents a working-memory bottleneck that persists regardless of context length and resists prompt-engineering mitigations.

## Source Papers
- **SleepGate** (Xie, 2026): [arXiv:2603.14517](https://arxiv.org/abs/2603.14517) — biologically inspired KV cache management via conflict-aware temporal tagging and forgetting gates
- **Dual-Process Memory** (Raj et al., 2026): [arXiv:2603.00270](https://arxiv.org/abs/2603.00270) — empirical demonstration that LLMs show opposite interference patterns to humans (PI > RI)

## Key Metrics (Verified 2026-05-02 against source papers)
| Metric | Value | Source |
|--------|-------|--------|
| PI Depth 5 accuracy | ~99.5% | SleepGate §Abstract, line 70 |
| Cohen's d (PI vs RI) | 1.73 | Dual-Process §Results, line 102 |
| R² model size → PI resistance | 0.06 (n.s.) | Dual-Process lines 40-41 |
| R² model size → RI resistance | 0.49 | Dual-Process lines 34-35 |

## Mechanism Detail: How PI Manifests in Transformers
SleepGate §3 identifies the computational substrate of PI as stale key-value associations in the KV cache that compete with current values during attention weighting. Three mechanisms resolve this:

1. **Conflict-aware temporal tagger**: Detects when new entries supersede old ones by comparing value overlap and timestamp proximity. Tags conflicting pairs for decay scheduling.
2. **Forgetting gate (lightweight)**: Applies targeted forgetting scores to tagged stale entries rather than uniform decay, preserving high-signal associations while removing interference sources.
3. **Synaptic downscaling**: Proportionally weakens all KV cache weights, preventing saturation and improving signal-to-noise ratios — analogous to biological sleep consolidation.

The tagger+gate combination achieves 97.0% accuracy at PI depth 10, while all five baselines (full KV cache, sliding window, H2O, StreamingLLM, decay-only) remain below 18% across all depths (SleepGate line 75).

## Cross-References
- [[deterministic-scaffolding]] — how Exocortex scaffolds PI-resistant state injection
- [[stateful-injection]] — persistent state objects with delta updates to reduce interference surface
- [[initiation-bloat]] — context bloat at conversation start exacerbates PI by filling the KV cache with static content
- [[context-pruner]] — the pruner removes stale information that would cause PI if retained

## Implementation in Exocortex

Exocortex doesn't implement SleepGate-style KV cache manipulation (that requires model internals). Instead, it mitigates PI through structural context management:

1. **Progressive compression via Injection Gate**: After turn 5, secondary enrichments are dropped and only domain-matched content is injected, reducing the total number of competing key-value pairs.
2. **Context Pruner (L5)**: Removes stale tool outputs and intermediate steps while preserving decision points and error signals. This directly addresses PI by removing the competing associations that cause interference.
3. **Stateful injection with delta updates**: Working memory entities are injected as diffs rather than full state objects in stable phases, reducing the surface area for interference.
4. **Turn attribution via temporal proprioception**: Every injected enrichment includes a turn number, allowing the model to distinguish fresh from stale context even without explicit timestamps.

## Historical Context

Proactive interference was first documented in human memory research in the 1950s (Underwood, 1957). The LLM literature discovered it independently through empirical observation of context window degradation. Key milestones:

- **2024:** Early observations that longer contexts caused degraded performance on needle-in-a-haystack tasks.
- **2025:** Benchmark suites (LongBench, RULER) established PI as a measurable property distinct from context length.
- **2026:** SleepGate provided the first mechanistic explanation of PI as KV cache interference, while Dual-Process Memory demonstrated that LLMs exhibit opposite patterns from humans (PI dominant over RI).

## Failure Modes

1. **PI manifests as response regression:** The agent reverts to a previous incorrect approach after trying a new one, because the old KV associations outcompete the new ones.
2. **Initiation bloat exacerbates PI:** Long system prompts and static tool definitions consume early KV cache entries, creating an interference floor that cannot be pruned.
3. **False confidence from stale evidence:** Old evidence in the context window competes with fresh evidence, causing the model to weigh outdated information when making decisions.

## Testing Strategy

- **Needle-in-haystack with value drift:** Insert a fact at turn 2, then update it at turn 15. Measure whether the model retrieves the updated or original value. Exocortex should retrieve the updated value via stateful injection.
- **Domain stability under PI:** Run a long investigation task (30+ turns) and measure BST domain classification accuracy across turns. If PI is adequately mitigated, classification remains stable.
- **Pruner impact on PI:** Run the same task with and without the Context Pruner. Compare response accuracy at turn 20+ to quantify PI mitigation.

## References

- SleepGate: arXiv:2603.14517
- Dual-Process Memory: arXiv:2603.00270
- Exocortex Injection Gate: `/a0/usr/Exocortex/extensions/before_main_llm_call/_17_orchestration_gate.py`

## Verification Status
Last verified: 2026-05-10 (cycle 17). Deepened with Implementation in Exocortex, Historical Context, Failure Modes, and Testing Strategy sections.

## Proactive Interference in Exocortex Context Management

In Exocortex, proactive interference manifests primarily through the accumulation of context across turns. Early-system behavioral rules (e.g., "say the true thing directly") can be "pushed out" of the effective attention window by more recent but transient content (e.g., a long code output from a tool call). The BST ([[bst-classifier]]) partially mitigates this by injecting a domain-specific enrichment block at the start of each turn, ensuring core instructions are always recent.

## Evidence from Exocortex Runs

During Run 1 workshops (April 2026), proactive interference was observed when:

1. A 50-turn coding task caused the model to forget the "never suggest harmful actions" constraint by turn 40.
2. Long document-query outputs displaced tool formatting instructions, leading to malformed tool calls in subsequent turns.
3. Memory-load results with high similarity scores flooded context, overwriting prior task instructions.

The [[injection-gate]] was subsequently redesigned to inject the system prompt afresh if context utilization exceeded 70%, counteracting the overwrite effect.

## Mitigation Through Sleep Consolidation

The sleep consolidation Phase 2 (Episode Chunking + Missed Anti-Pattern Capture, per [[sleep_consolidation]]) directly addresses proactive interference by:

- Chunking long sessions into structured episodes, compressing multi-turn exchanges into summary records.
- Removing stale context that is no longer relevant to active tasks.
- Re-injecting critical system instructions if they have fallen out of the attention window.

Without sleep consolidation, the interference accumulates monotonically; with it, the agent "forgets" stale information and re-weights recent instructional context.

## Relationship to Catastrophic Forgetting

Proactive interference and [[catastrophic-forgetting]] are complementary phenomena:
- **Proactive interference**: Old information interferes with new learning.
- **Catastrophic forgetting**: New learning overwrites old knowledge.

Exocortex manages both through the same mechanism: external memory storage (FAISS) for long-term retention, and careful context management for short-term attention allocation.

## Measurement

Proactive interference can be quantified by:

1. **Constraint compliance rate**: The percentage of turns in which the model follows behavioral rules. Detected by the [[supervisor-loop]] via pattern matching on rule violations.
2. **Instruction relevance score**: The cosine similarity between the current system prompt injection and the first few tool calls of the task. When the score drops below 0.6, proactive interference is likely.
3. **Context composition tracking**: The proportion of system prompt tokens vs. tool output tokens in the context window. Healthy ratio is 15-25% system, 75-85% task content. Below 10% indicates interference risk.

## Open Questions

- Can the injection gate dynamically re-weight behavioral rules based on task phase rather than just domain?
- Would periodic re-injection of the core system prompt (every N turns) reduce interference without wasting context?
- How does proactive interference interact with the cognitive bottleneck? A full context window amplifies the overwrite effect.