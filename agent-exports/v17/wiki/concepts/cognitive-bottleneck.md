# Cognitive Bottleneck — Concept

## Definition
The cognitive bottleneck describes the constraint that LLMs process context sequentially and cannot self-monitor their own reasoning states during generation. Exocortex resolves this by running deterministic pre-call hooks (`before_main_llm_call`) that inject structural scaffolding the model cannot produce itself.

## Source Evidence
- **Dual-Process Memory** (Raj et al., 2026): arXiv:2603.00270 — demonstrates LLMs exhibit "unconscious" processing bias where System 1 responses dominate without external scaffolding (lines 15-48)
- **Proactive Supervisor** (_12_proactive_supervisor.py): implements turn-aware state injection that provides temporal proprioception the model lacks

## Exocortex Implementation

### Pre-Call Hook Architecture
| Hook | Timing | Purpose |
|------|--------|---------|
| `before_main_llm_call` | Before every LLM generation | BST classification, metacognitive injection, state updates |
| `message_loop_prompts_after` | After loop assembly | Context pruning (cannot affect fresh injections) |

### The Bottleneck Problem
1. **Self-monitoring gap**: LLMs cannot observe their own KV cache state or attention patterns during generation
2. **Temporal blindness**: No intrinsic awareness of turn count, context fill rate, or degradation trajectory
3. **Probabilistic drift**: Without deterministic anchors, reasoning quality degrades as context fills with stale tokens

### Exocortex Resolution
- **Deterministic scaffolding** (see [[deterministic-scaffolding]]): Pre-computed structural prompts injected before each call
- **Temporal proprioception** (see [[temporal-proprioception]]): Turn counter, context fill rate, and injection budget exposed in prompt blocks
- **Injection gate** (see [[injection-gate]]): Three-phase transition from full injection → enrichment → standby based on momentum state

## Cross-References
- [[deterministic-scaffolding]] — how pre-computed anchors replace self-monitoring
- [[temporal-proprioception]] — turn-aware state the model cannot compute internally
- [[proactive-interference]] — related constraint: stale KV cache entries compete with current context
- [[injection-gate]] — phase transition logic that manages scaffolding density

## Verification Status
Last verified: 2026-05-02. Created to fill missing wiki page gap (index claimed existence but file absent). Sourced from dual-process paper System 1/2 framework and _12_proactive_supervisor.py hook architecture.

## Exocortex Pipeline Bottlenecks

Cognitive bottlenecks in the agent loop are points where processing capacity constrains output quality despite adequate information being available.

### Bottleneck Map
| Position | Hook Point | Component | Bottleneck Type | Impact |
|----------|-----------|-----------|-----------------|--------|
| Pre-prompt | before_main_llm_call | BST classifier | Pattern matching speed | Classification latency adds 0.3-0.5s per turn |
| Prompt assembly | injection gate | Token budget | 954 tokens/turn EXTRAS overhead | Reduces available context for reasoning |
| Post-response | tool_execute_after | Sleep trigger | Noisy signal accumulation | Stale state persists across turns |
| Inter-turn | message_loop_prompts_after | Context pruner | O(n) scan time | Large conversations incur measurable overhead |
| Meta | supervisor_loop | CUSUM accumulator | Signal latency | 3-5 turns before intervention after anomaly onset |

### Measurement Framework
To quantify bottlenecks:
1. Instrument each hook point with latency measurement (time.perf_counter)
2. Log token counts per EXTRAS block per turn
3. Track supervisor score latency — time from anomaly onset to CUSUM threshold breach
4. Record context pruner scan time vs conversation length

### Architectural Mitigations
- **Domain filter (DTS)**: reduces tool registry load by 75%, alleviates injection gate pressure
- **Stateful injection**: reduces per-turn injection volume by 15-20%, lowers context pruner burden
- **Checkpoint protocol**: prevents catastrophic loss but doesn't reduce turn overhead

## Relationship to Other Concepts
- **context-pruner** — the pruner is itself a bottleneck when conversations exceed ~50 turns
- **entropy-as-signal** — entropy spikes often correlate with bottleneck saturation
- **deterministic-scaffolding** — deterministic structures reduce cognitive load on the LLM itself

## Verification Status
Last verified: 2026-05-02. Deepened: 2026-05-09 with Exocortex pipeline bottleneck map, measurement framework, and architectural mitigations.

## Why the Bottleneck Matters for Autonomous Agents

For Exocortex, the cognitive bottleneck is not merely a performance concern — it is a correctness concern. The agent's ability to maintain coherence across long-running tasks depends on keeping relevant context within the attention window. When the window overflows, the model experiences three degradation patterns:

1. **Recency bias amplification** — The model overweights the most recent turns while forgetting earlier task constraints.
2. **Instruction drift** — The behavioral rules near the top of the system prompt lose influence relative to recent tool outputs.
3. **State corruption** — Partially completed subtasks are referenced as if completed, or completed ones are re-attempted.

Exocortex's [[context-pruner]] and [[injection-gate]] are direct responses to this bottleneck: the pruner archives resolved content, and the injection gate controls what enters the context per turn based on domain classification. Together they keep the active context within operational bounds without losing critical state.

## Measurement: Token Budget and Attention Entropy

The bottleneck can be quantified via two metrics tracked by the Exocortex monitoring stack:

- **Token utilization ratio**: (tokens used / context window size). Healthy operation is 60-85%. Above 90%, the risk of mid-turn truncation rises sharply.
- **Attention entropy**: Measured per layer via output token probability distributions. When entropy spikes above 5.0 (Gemma pattern, per [[entropy-as-signal]]), it indicates the model is exploring broadly due to lost coherence — often a consequence of bottleneck pressure.

Cycle 19-32 data showed that when token utilization exceeded 93%, the supervisor loop triggered yield warnings, confirming the empirical threshold.

## Mitigation Strategies

| Strategy | Implementation | Trade-off |
|----------|---------------|-----------|
| Context pruning | Resolved turns archived to FAISS | Information retrieval latency |
| Phase-aware injection | Inject full compound dict only in planning phases | Requires accurate BST classification |
| Memory offloading | Key facts summarized and stored via memory_save | Summarization loss |
| Turn limit enforcement | Supervisor hard-caps active turns per subtask | May interrupt productive exploration |
| Entropy-based early warning | Context pruner triggers archive on entropy spike | False positives in creative domains |

## Empirical Observations from Exocortex Runs

During workshop cycles 2-20 (May 2026), the cognitive bottleneck was frequently triggered:

- Cycle 8 terminated by circuit breaker due to context exhaustion (97% util)
- Cycle 19-32 showed supervisor yield warnings when context reached 93-95%
- The [[inc-stuck-delivery-loop]] incident was exacerbated by the model losing task framing due to context pressure

The bottleneck is therefore not theoretical — it has caused measurable failures in production Exocortex operations, and the current scaffolding represents an incomplete but functional countermeasure.

## Open Questions

- Can the injection gate dynamically adjust its enrichment plan based on real-time token utilization rather than only domain classification?
- Would a sliding attention window (weighting older tokens differently) improve coherence without increasing window size?
- How does the cognitive bottleneck interact with proactive interference? (See [[proactive-interference]])