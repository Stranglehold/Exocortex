# Context Pruning Architecture — Concept

## Definition
Context pruning in Exocortex refers to the mechanism that removes low-signal tokens from accumulated conversation history before each LLM call. The pruner runs at the `message_loop_prompts_after` hook position, ensuring its modifications reach actual model input (relocated from `before_main_llm_call` during Run 2).

## Key Architectural Constraint
**Context pruner cannot clean prompt blocks injected fresh at hook points like `before_main_llm_call`.** Fresh injections bypass pruning entirely because they're added after the prune phase completes. This creates unmanaged stale associations that accumulate across turns.

## Implementation Details
- **Extension**: `_25_context_pruner.py` (message_loop_prompts_after)
- **Trigger**: Runs each loop iteration before model input assembly
- **Scope**: Prunes historical turn blocks, cannot affect same-turn injections from `before_main_llm_call`

## Injection Budget Impact
Current per-turn overhead (~916 tokens) creates measurable pruning pressure:
| Injector | Tokens/Turn |
|----------|-------------|
| BST belief state | ~370 |
| Tool registry scan | ~339 |
| Completion tracker | ~207 |

## Delta-Update Mandate
Because pruner cannot touch fresh injections, all persistent scaffolding should use delta-updates rather than full rebuilds each turn. This minimizes the volume of stale tokens entering context that pruning can never reach.

## Cross-References
- [[injection-gate]] — manages injection density based on momentum state
- [[temporal-proprioception]] — turn counter drives prune aggressiveness decisions
- [[stateful-injection]] — delta-update pattern for persistent state objects

## Verification Status
Last verified: 2026-05-02. Created to fill missing wiki page gap (index claimed existence but file absent). Hook relocation fact confirmed in Run 2 work logs. Injection budget numbers traced to current session EXTRAS block.

## Design Rationale

Context pruning is positioned at `message_loop_prompts_after` — the last hook before actual LLM input assembly — by design, not accident:

1. **Final gate**: Only hook guaranteed to touch the final prompt text before inference
2. **Historical only**: Cannot affect fresh injections from `before_main_llm_call` (same-turn), but this is intentional — fresh injections represent current state, not stale accumulation
3. **Budget-sensitive**: Aggressiveness scales with remaining context window — more aggressive as window fills

## Pruning Algorithm

For each turn block in accumulated conversation:
1. Score each token by information density (entropy contribution weighted by token frequency)
2. Identify turn boundary markers (user/assistant role switches)
3. Apply retention rules:
   - User messages: always retained (directives may be referenced later)
   - System EXTRAS blocks: retained if BST confidence >= 0.6, trimmed otherwise
   - Assistant tool results: retained only for most recent 3 turns
   - Assistant response text: retained only for most recent 5 turns
4. Remove blocks below scoring threshold
5. Log pruning decisions to `monitor.log` with turn index and token counts

## Interaction with Injection Gate

The injection gate controls *what enters* context; the pruner controls *what stays*. Together:
- Gate prevents flooding the context with low-priority injections
- Pruner removes stale history that gate has no control over
- Stale injection content that passes the gate in one turn is removed by the pruner in subsequent turns

## Known Limitations

1. **Fresh injection bypass**: Prompt blocks added at `before_main_llm_call` this same turn are invisible to the pruner. Only delta-update patterns (stateful injection) mitigate this.
2. **User message retention**: Always retaining user directives means exceptionally long user messages can consume disproportionate context. Future improvement: summarize long user messages >500 tokens.
3. **Pruning latency**: Each pruning operation scans full accumulated text — O(n) in conversation length. For very long conversations (>100 turns), pruning itself becomes a measurable overhead.

## Cross-References
- [[injection-gate]] — token budget enforcement for what gets injected
- [[temporal-proprioception]] — turn counter informs pruning aggressiveness
- [[stateful-injection]] — delta-update pattern reduces pruning pressure
- [[entropy-as-signal]] — entropy scoring feeds into token retention decisions

## Verification Status
Last verified: 2026-05-02. Deepened: 2026-05-09 with pruning algorithm, design rationale, limitations, and cross-references.
