# Stateful Injection

**Component** | **Hooks:** before_main_llm_call | **Type:** Memory efficiency optimization

---

## Purpose

Stateful Injection treats persistent state objects (BST belief state, completion tracker, tool registry) as delta-updated rather than fully rebuilt each turn. This minimizes stale KV cache entries that cause proactive interference — a phenomenon where older, irrelevant key-value pairs in the model's attention cache suppress current-task attention.

Traditional approach: rebuild all injection strings from scratch each turn, appending fresh copies to the context. Result: accumulated stale KV entries from earlier turns' identical content diluting attention scores.

Stateful approach: maintain persistent objects with turn-level delta updates. Only changed fields produce new KV entries. Unchanged state remains as single, stable entries without duplication.

## Mechanism

### Persistent Objects
- **BST belief state** — domain classification, confidence scores, momentum tracking
- **Completion tracker** — task progress, step counting, verification state
- **Tool manifest** — tool availability, schema changes, deprecation flags

### Delta Updates
Each turn, extensions update only changed fields:
- Domain changes → BST object delta
- Step increments → completion tracker delta
- New tool registrations → tool manifest delta

Unchanged state is NOT re-serialized — the previous turn's KV entries remain valid.

### Budget Tracking
Injection budget tracked per turn: ~954 tokens current average for the EXTRAS block. Stateful injection reduces this by ~15-20% compared to full-rebuild, as unchanged state fields are skipped.

## Integration Points

- **Injection Gate (L3)** — Budget enforcement layer that gates total injection volume
- **Context Pruner (L6)** — Complement: pruner removes stale entries from context; stateful injection prevents creating them
- **Proactive Interference mitigation** — Directly addresses PI risk by minimizing fresh injection volume for stable state
- **Deterministic Scaffolding** — Stateful injections are deterministic structures, not probabilistic generations

## Proactive Interference Context

Proactive interference occurs when older KV cache entries compete with current context for attention. The model's attention mechanism distributes weights across all available keys — more stale entries = less weight on current context. Stateful injection is the primary architectural defense.

## Related

- [[proactive-interference]] — the cognitive phenomenon this component directly addresses
- [[deterministic-scaffolding]] — architectural pattern: all injection structures are deterministic
- [[injection-gate]] — budget enforcement for all persistent injections
- [[context-pruner]] — downstream complement that removes what stateful injection couldn't prevent

## Verification
Last verified: 2026-05-02. Deepened: 2026-05-09 with delta-update mechanism, proactive interference context, and budget tracking documentation.

## Implementation Architecture

Stateful injection is implemented as extension `_18_stateful_injection_tracker.py` in `before_main_llm_call`. It maintains a per-session cache of the previous turn's injection state (BST domain, epistemic integrity, memory recall results, tool availability delta). On each turn, it computes the delta between the current and previous state, and injects only the changed components. If no component changed since the last turn, the entire injection block is skipped (except for the minimum temporal proprioception header). The cache is stored in the framework's context object with key `stateful_cache`. Cache lifetime is one session; it is cleared on session reset.

## Delta Encoding Details

| Component | Delta Strategy | Token Savings (est.) |
|-----------|---------------|---------------------|
| BST domain | Only injected if domain changed or confidence delta > 0.2 | 40 tokens |
| Epistemic integrity | Only injected if score changed by > 0.1 | 25 tokens |
| Memory recall | Only injected if new memories returned or old ones expired (TTL) | 60 tokens |
| Tool availability | Only injected if tools added/removed since last turn | 50 tokens |
| Error patterns | Only injected if new error pattern detected | 30 tokens |
| Temporal stamp | Always injected (minimum floor) | 15 tokens |

## Cross-Component Interactions

| Component | Interaction |
|-----------|-------------|
| Injection Gate | Stateful injection feeds delta to the injection gate; if delta is empty, gate decision is recorded as "SKIP" rather than ALLOW/WARN/BLOCK, saving gate processing |
| Memory Plugin | Cache depends on memory recall; if memory returns stale results (TTL expired), stateful injection treats them as changed even if content identical |
| Context Pruner | Pruner can run before or after stateful injection; configurable order with boolean `pruner_before_stateful` (default true) |

## Configuration Variables

| Variable | Default | Description |
|-----------|---------|-------------|
| `stateful_injection_enabled` | true | Master enable/disable |
| `cache_strategy` | "delta" | "delta" or "full" (full re-injects everything each turn) |
| `confidence_delta_threshold` | 0.2 | Minimum change in BST confidence to trigger injection |
| `integrity_delta_threshold` | 0.1 | Minimum change in epistemic integrity to trigger injection |
| `memory_ttl_seconds` | 300 | Memory cache time-to-live before considered stale |

## Known Limitations

- **False equivalence**: Two memory result sets with identical content but different timestamps are treated as "unchanged," potentially hiding recency information. Fix: add timestamp hash to delta comparison.
- **Cold-start penalty**: First turn after session reset has no cache, so full injection occurs — same as baseline. Solution: pre-seed cache from similar past sessions (Phase 5 work item).
- **Memory TTL conflicts with sticky memories**: Intentions and relationals have longer TTLs; stateful injection must respect per-type TTLs, not a single global TTL.
