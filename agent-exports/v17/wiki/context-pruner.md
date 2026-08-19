# Context Pruner

**Component** | **Hook:** before_main_llm_call (_05) | **Type:** Deterministic compression

---

## Purpose

The Context Pruner reduces prompt bloat by filtering injected memories and context segments before they reach the LLM. Without within-session compression, Agent Zero's context window fills in 15-30 turns from tool output accumulation — a single file read can be 10K+ tokens. The pruner provides within-session compression (complementing between-session sleep consolidation) to extend operational runs.

## Research Basis

### JetBrains / TUM (NeurIPS 2025 DL4Code Workshop)
Two approaches compared: LLM summarization vs. observation masking.

**Key finding:** Summarization caused "Trajectory Elongation" — the LLM summarizer smoothed over failure severity, causing the agent to not realize how stuck it was. The agent kept retrying failed approaches because the summary softened the signal. **Observation masking** — replacing tool outputs with placeholders while keeping reasoning/action history verbatim — preserved the harsh reality of failures and produced better agent performance.

**Implication:** The pruner should mask/compress tool outputs, not summarize reasoning history. The model needs to remember it failed, not that a summary said "attempt was made."

### Three-Tier Memory Architecture
| Tier | Scope | Retention |
|------|-------|-----------|
| Working Memory | Current task's turn history | Session lifetime |
| Episodic Buffer | Key decision points + failures | Days (decay-based) |
| Semantic Store | Patterns, anti-patterns, skills | Permanent (FAISS) |

The pruner operates on Working Memory — compressing tool outputs and stale intermediate steps while preserving decision points, error signals, and operator corrections.

## Mechanism

- **Hook:** `before_main_llm_call/_05_context_pruner.py`
- **Injection budget:** Caps total injected memories at 8 per DOMAIN_THRESHOLDS configuration
- **Decay-based pruning:** 168-hour half-life threshold for injected memory relevance
- **Tool output compression:** Replaces verbose tool outputs with structured summaries for completed actions, retains full output for failed steps
- **Failure signal preservation:** Never compresses error messages, syntax errors, or failed tool call results — these are the highest-value learning signals

## Known Gaps
- **No delta caching layer** for repeated turns. When classification is stable across consecutive turns, the pruner still re-evaluates all segments rather than skipping unchanged regions.
- **No dynamic budget allocation** — the 8-memory cap is static regardless of task complexity or domain.
- **Single-pass operation** — doesn't re-compress earlier segments if later turns reveal they're irrelevant. A tiered re-evaluation across the session would improve efficiency.

## Metrics (Run 3)
- Hook load time: ~0.4ms (min 0.383ms per P2 profiling)
- Injection budget tracking: ~698 tokens injected per turn after pruning

## Integration Points
- **Injection Gate (L3)** — Provides the memory candidates that the pruner filters
- **Supervisor Loop (L4)** — Supervisor escalation at Tier 2 requests additional compression from pruner
- **Backend Standby (L1)** — If standby mode extends, pruner buys time by compressing context before Tier 3 forced response
- **Selective Memorizer** — Episodic buffer decay feeds into pruner's relevance scoring

## Related
- [[injection-gate]] — upstream provider of memory candidates
- [[supervisor-loop]] — escalates to compression at Tier 2
- [[backend-standby]] — buys time during backend outages
- [[entropy-as-signal]] — theoretical foundation for relevance scoring
- [[deterministic-scaffolding]] — broader architecture context

## Verification
Last verified: 2026-05-02. Expanded: 2026-05-09 with research basis and three-tier architecture from CONTEXT_COMPRESSION_DESIGN_NOTE.md.
