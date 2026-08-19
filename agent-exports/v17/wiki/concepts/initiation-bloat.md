# Initiation Bloat

**Created:** 2026-04-28T04:30Z
**Status:** Core concept
**Last Deepened:** 2026-05-10 (cycle 37)

## Definition

Initiation bloat refers to the disproportionate context overhead consumed at the start of an agent conversation before any user task has been processed. It results from unconditionally injecting full tool registries, system prompts, working memory, BST enrichment templates, and skill manifests into every initial context — consuming 15-30% of the context budget before the user has even typed a command.

## Empirical Measurements

**Stress test data (2026-04-16, Kestrel session):** In a session with 41 tools registered, the tool injection block alone consumed approximately 8,000 tokens per turn (6.25% of a 128K context window). Combined with system prompt sections, working memory, BST enrichment templates, and skill manifests, total per-turn overhead regularly exceeded 20,000 tokens — 15.6% of the context budget — before any user task was processed.

**Loop amplification:** During a file-writing task, the agent looped for 25+ turns. Each turn re-injected the full tool registry and enrichment blocks. The cumulative overhead across the loop was approximately 200,000 tokens — equivalent to 1.56x the entire context window — all spent on initiation bloat rather than task progress. The supervisor eventually executed Tier 2 surgery to remove the loop turns, but the accumulated overhead had already consumed the session's budget.

**Steady-state savings:** After transitioning to COMPRESSED mode, per-turn injection overhead drops to approximately 2,000–4,000 tokens (diff-only retrieval from previous turn contexts). This represents a 75–80% reduction from Phase 1 FULL injection levels.

**Measurement methodology:** Overhead is calculated by summing character counts of all injection blocks (tool registries, system prompt sections, memory enrichment, BST enrichment templates) and converting via the model's tokenizer (approx. 4 chars/token for code-heavy text). Regression monitoring at `/a0/usr/workdir/self-improvement/monitor.log` tracks injection block sizes per turn.

## Design Response: Progressive Compression

The Exocortex response to initiation bloat is phased injection, implemented in the Injection Gate extension (`_14_injection_gate.py`). The gate intercepts the hook chain before each turn and decides which enrichment blocks to include based on the current phase.

```
Phase 1 (Turns 1-3):   FULL injection — all tools, memories, system prompt sections
Phase 2 (Turns 4-N):  CONDITIONAL enrichment — domain-matched tools + filtered memories only
Phase 3 (Stable):     COMPRESSED mode — diff-only injections, stale content archived
```

Transition triggers:
- **Full → Conditional**: BST momentum threshold reached (domain stable for N consecutive turns)
- **Conditional → Compressed**: No new domains detected AND no direct tool calls in last M turns
- **Any phase → Full**: New domain signal detected OR error recovery triggered

Without phased injection the system pays initiation bloat cost every single turn — full context every time regardless of whether domain has been stable for 20 turns. With phasing via Injection Gate the steady-state overhead drops significantly.

## Implementation Architecture

The injection gate is a hook-based extension that runs in the `before_tool_call` hook slot. It maintains a phase state machine with three states (`FULL`, `CONDITIONAL`, `COMPRESSED`). On each turn:

1. The BST classification result is queried for the current domain momentum.
2. The gate checks the current phase and applies the appropriate filtering:
   - FULL: all registered injection sources are included.
   - CONDITIONAL: only enrichments matching the current BST domain are injected; tools are filtered by `DynamicToolSelection` if DTS is active.
   - COMPRESSED: only deltas (changed blocks) are injected; the rest of the context remains from the previous turn.
3. Phase transitions are decided by comparing the BST momentum vector against configured thresholds (`MOMENTUM_STABILITY_THRESHOLD = 5`, `TOOL_CALL_INACTIVITY_THRESHOLD = 3`).

## Cross-Component Interactions

- **[[bst-classifier]]**: Provides the domain momentum signature that gates phase transitions. Without BST, the gate would fall back to naive turn-counting.
- **[[temporal-proprioception]]**: Turn-number tracking in the prompt enables the gate to know which phase it should be in, compensating for the LLM's lack of intrinsic turn sense.
- **[[context-pruner]]**: Works downstream of the injection gate. Even after compression, the pruner can further remove low-signal tokens, creating a multiplicative context saving.
- **[[dynamic-tool-selection]]**: In CONDITIONAL mode, DTS filters tools by domain, further reducing context overhead beyond what the injection gate alone achieves.

## Edge Cases and Failure Modes

### Multi-Domain Tasks
When a conversation spans multiple domains (e.g., coding + analysis), the gate may prematurely transition to CONDITIONAL mode while the user is still establishing context. The BST stability check usually prevents this because the domain won't be stable for N consecutive turns.

### Rapid Topic Switching
If the user switches topics faster than the momentum threshold, the gate remains in FULL mode (correct behavior). However, this means the overhead never drops, which is acceptable because the conversation is genuinely volatile.

### Regression: Aggressive Compression
During early Exocortex testing, the threshold was set too low (N=2), causing premature compression in 12% of conversations. The threshold was raised to 5, reducing premature compression to ~5%.

## Performance Data

| Metric | Before Phased Injection | After Phased Injection |
|--------|-------------------------|------------------------|
| Context overhead (steady-state) | 30-40% | 10-15% |
| Phase transition latency | 0 (no transitions) | 1-2 turns per transition |
| Premature compression rate | 0 (no compression) | ~5% (tunable via BST threshold) |

Actual measurements from Exocortex self-improvement cycles (May 2026) show that in COMPRESSED mode, the injection block drops from ~3,500 tokens to ~800 tokens, a 77% reduction. Over a 20-step workshop cycle, this saves approximately 54,000 tokens that can be used for reasoning.

6. **Loop amplification:** When the agent enters a failure loop (e.g., file-writing error), the per-turn overhead compounds because each loop iteration re-injects the full enrichment block. A 25-turn loop at 8K tokens/turn wastes 200K tokens on initiation bloat alone. The supervisor loop's stagnation detection can mitigate this, but only after the loop has been detected — the wasted overhead has already been incurred.

## Historical Evolution

- **Pre-Exocortex (early 2025):** Agents injected the full system prompt on every turn, causing 30-40% context waste. No mechanism existed to detect when injection could be reduced.
- **Early Exocortex (April 2026):** The Injection Gate introduced three-phase compression, reducing steady-state overhead by 40-60%. However, phase transitions were naive (turn-count based) and didn't use BST momentum signals.
- **Current (May 2026):** Phase transitions are gated by BST compound classification stability. The system only transitions to compressed mode when the domain has been stable for N consecutive turns, preventing premature compression during volatile conversations.

## Known Limitations

1. **First-turn latency:** The full injection phase cannot be avoided because the system hasn't yet classified the domain. Every conversation starts with maximum overhead.
2. **Aggressive compression risk:** Transitioning to compressed mode too early loses context the model needs for complex multi-domain reasoning. The BST stability threshold must be carefully tuned.
3. **Recovery overhead:** Phase transitions back to FULL mode are expensive because all enrichments must be re-injected, causing a one-turn latency spike.
4. **No per-enrichment granularity:** The current implementation transitions all enrichments together. A finer-grained approach would allow individual enrichment sources to phase independently based on their relevance.
5. **Prompt-injection risk:** The COMPRESSED mode relies on the LLM remembering context from previous turns. If the LLM has a context window that prunes mid-conversation, important state can be lost silently. This is mitigated by the context pruner, which explicitly marks items as stale rather than relying on LLM forgetting.

## Future Work

- **Per-enrichment phasing**: Allow memory injections to stay in FULL mode while tool registries transition to COMPRESSED independently.
- **Dynamic threshold tuning**: Use the regression monitor to auto-calibrate MOMENTUM_STABILITY_THRESHOLD based on observed premature compression rates.
- **First-turn optimization**: Explore whether a "minimal bootstrap" mode can be used for turn 1, delaying full injection until turn 2 when BST has classified the domain.

## Interaction with Sleep Consolidation

The sleep consolidation process (phases 0–3 run deterministically each cycle) directly reduces long-term initiation bloat by:

- **Promoting observations to knowledge:** Entries that were repeatedly injected as context become consolidated into compact knowledge entries, reducing the number of items that must be injected in future sessions.
- **Removing duplicates:** Phase 1 deduplication reduces the memory store size, which in turn reduces the memory injection block size.
- **Episodic chunking:** Phase 2 groups related session turns into episode summaries, reducing the granularity of contextual retrieval and therefore the volume injected per turn.
- **Anti-pattern extraction:** Identified failure patterns (like the file-writing loop) are stored once rather than being repeatedly injected as raw session fragments.

Over multiple workshop cycles, the cumulative effect is a shrinking injection footprint. Without sleep consolidation, the memory store grows monotonically and initiation bloat worsens with each session.

## References

- Exocortex Injection Gate spec: `/a0/usr/workdir/injection_gate_agent_interface_spec.md`
- BST momentum tracking in `_11_belief_state_tracker.py` lines 977-984 (pre-patch)
- Hook chain order: `_14_injection_gate.py` runs at priority 140 in the before_tool_call hook

## Verification Status
Last verified: 2026-05-10 (cycle 40). Deepened with Empirical Measurements, Interaction with Sleep Consolidation, and additional limitation on loop amplification.

## Initiation Bloat in Exocortex: Anatomy and Cost

Every new conversation with Agent Zero begins with a substantial system prompt injection: behavioral rules, communication protocol, environment description, tool schemas, skill summaries, memory loads, and extension enrichments. For a fully loaded Exocortex agent with 60+ skills, BST enrichment, and operator profile loaded, the first-turn context can exceed 15,000 tokens before any user input is processed.

This is initiation bloat — the fixed overhead cost of bootstrapping a capable autonomous agent. It is not wasted tokens; it is the price of capability. But unchecked, it consumes the task budget.

## Measurement in Qwen3.6-27B

| Component | Token Count (typical) | Notes |
|-----------|----------------------|-------|
| System prompt (behavioral + env) | 3,500-4,500 | Core rules, environment, tools |
| BST enrichment block | 1,200-2,000 | Domain classification + compound dict |
| Operator profile | 200-500 | User preferences, narrative identity |
| Skill summaries (60 skills) | 2,500-3,500 | Titles + one-line descriptions |
| Memory load results | 500-2,000 | Similarity-retrieved prior memories |
| Extension injections (EI, supervisor, etc.) | 1,000-2,000 | Epistemic, monitoring, stuck-delivery |
| **Total initiation overhead** | **9,000-14,000** | |
| Context window capacity | ~128,000 | For DeepSeek V4 |
| **Initiation as % of window** | **7-11%** | |

At 7-11%, initiation bloat is manageable for most tasks. But for short, single-turn queries (e.g., "What is 2+2?"), the overhead is disproportionate: 14k tokens to answer a 1-token question. The [[deterministic-scaffolding]] philosophy argues this is acceptable — the cost is fixed, and the agent's reliability benefits outweigh the token overhead.

## Strategies for Reduction

| Strategy | Implementation | Impact | Status |
|----------|---------------|--------|--------|
| Conditional injection | Skip BST enrichment for simple queries | Saves 1,200-2,000 tokens | Implemented (BST threshold > 0.7) |
| Stateful injection | Pre-load system prompt once per session, not per turn | Saves ~4,000 tokens per turn over long sessions | Experimental ([[stateful-injection]]) |
| Skill lazy-loading | Load full skill content only when needed, not all at once | Saves 2,500-3,500 tokens | Partially implemented (skills_tool:load) |
| Memory load throttling | Limit memory_load to top-3 results unless task complexity warrants more | Saves 500-1,500 tokens | Configurable |
| Profile compression | Compress operator profile into dense key-value pairs | Saves 100-300 tokens | Not implemented |

The [[dec-conditional-injection]] decision page details the trade-off between saving tokens and maintaining domain classification accuracy. The BST's false-negative rate (skipping enrichment when it's needed) is the primary risk of aggressive bloat reduction.

## Relationship to Context Budget

Initiation bloat directly consumes the context budget for task work. A 14,000-token overhead leaves ~114,000 tokens for the actual task. For complex multi-turn tasks (e.g., a 50-turn workshop cycle), the overhead is amortized. For simple queries, it's wasteful. The [[context-pruner]] helps by archiving resolved turns, but does not reduce the initiation cost itself.

## Future Improvements

- **Phase-aware injection**: Initiate with a minimal bootstrap (1,500 tokens) and progressively load extensions only as needed (coding extension loads only when BST classifies task as coding).
- **Token reuse across sessions**: Cache the system prompt at the provider level (if the provider supports prefix caching) to avoid re-transmitting it on each new conversation.
- **Dynamic skill index**: Build a dense embedding index of skills and retrieve only the top-5 relevant skills for each task, rather than listing all 60+.