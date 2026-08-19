# Supervisor Loop Component

**Deepened:** 2026-05-10 (cycle 15 — implementation details, hook chain context, known gaps analysis)

## Overview

Adaptive control system that monitors agent behavior, classifies task complexity, and dynamically adjusts injection thresholds. Operates as the central coordination layer between hooks — the only component with visibility across the full before/after main LLM call lifecycle.

## Architecture

- **Hook position:** Runs in the `after_main_llm_call` hook path, meaning it sees the agent's output before the next turn begins.
- **Classification:** Categorizes each turn into complexity classes: `simple`, `moderate`, `complex` based on tool calls issued, task type, and output characteristics.
- **Threshold adjustment:** Modifies `DOMAIN_THRESHOLDS` based on classification history and momentum tracking across consecutive turns.
- **Temporal proprioception:** Tracks whether the agent is making genuine progress (varied tool use, output diversity, task completion signals) or spinning wheels (repetitive patterns, same domain frozen, no task closure).

## Hook Chain Context

```
Turn lifecycle:
  1. before_main_llm_call hooks run (BST, injector, pruner, assembler)
  2. LLM responds
  3. after_main_llm_call hooks run:
     a. _50_supervisor_loop.py          → THIS — classification + threshold adjustment
     b. _60_sleep_trigger.py            → checks idle timer, triggers sleep consolidation
     c. _70_epistemic_integrity.py      → post-hoc hallucination check
```

This position is load-bearing: the supervisor must run after the LLM responds (to evaluate what happened) but before the next turn's before-hooks (to adjust thresholds that the injector will use).

## Current Configuration (Run 3)

- **Classification stability window:** 3 consecutive turns in the same complexity class before committing to reduced injection.
- **Momentum lock detection:** Fires after 5+ turns in the same domain without task completion. See BST source `_11_belief_state_tracker.py` line 77 for `MOMENTUM_THRESHOLD=5` (the domain lock threshold, distinct from the classification stability window).
- **Circuit breaker thresholds:** Per complexity class, logged via `INJECTION BUDGET` header on each turn. Higher complexity → lower injection budgets.

### Classification Logic

| Complexity | Criteria | Injection Behavior |
|---|---|---|
| `simple` | Single tool call, no errors, response under 200 tokens | Minimal injection: turn count, timestamp only |
| `moderate` | Multiple tool calls, standard task | Standard injection: BST signal, memory recall, tool registry deltas |
| `complex` | Multi-step task, errors encountered, delegation used | Full injection: all signals plus epistemic integrity reminders |

## Known Gaps

- **No hard enforcement of circuit breakers:** The supervisor can detect problems (momentum lock, repetitive patterns) but cannot mechanically block the agent from continuing a failing pattern. Behavioral constraints are advisory, enforced only by the agent's own compliance with the prompt.
- **Complexity classification is rudimentary:** Based on binary heuristics (tool count, error presence) rather than semantic understanding of task difficulty. A single-tool task can be conceptually complex but classified as `simple`.
- **Threshold adjustment is one-directional:** The supervisor can reduce injection budgets but has no mechanism to increase them when a task proves harder than initially classified.
- **No cross-session learning:** Thresholds reset each conversation; the supervisor does not carry calibration state across sessions even though sleep consolidation saves operator profiles.

## Interactions

- **BST classifier:** Provides domain classification that the supervisor uses for momentum tracking. The supervisor's threshold adjustments feed back into BST's enrichment decisions.
- **Injection gate:** The supervisor adjusts the injection budget that the gate enforces. Higher gate enforcement means less context injected on stable turns.
- **Sleep consolidation:** Phase 3 (operator interaction modeling) reads the supervisor's turn-by-turn classifications to build the operator profile. The supervisor's classification quality directly affects profile accuracy.
- **Epistemic integrity:** The supervisor flags high-risk turns for post-hoc hallucination checking by the epistemic integrity hook.

## Related

- [[bst-classifier]] — domain classification that feeds momentum tracking.
- [[entropy-as-signal]] — complementary signal for detecting stagnation.
- [[injection-gate]] — budget enforcement layer that the supervisor adjusts.
- [[temporal-proprioception]] — turn-awareness infrastructure the supervisor relies on.
- [[context-pruner]] — downstream filter that benefits from supervisor-adjusted thresholds.

## Verification Status

Last verified: 2026-05-02. Verification status block added per program.md Rule 1 improvement cycle.
Deepened: 2026-05-10 with hook chain context, classification logic table, known gaps analysis, and cross-component interaction mapping.


## Implementation Architecture

The supervisor loop in Exocortex operates as an out-of-band monitoring layer that intercepts the agent's action stream without adding tokens to the model's context window. Its design implementation was documented in the Exocortex bootstrap specification and refined during cycles 2-7.

### Hook Integration Points

| Hook Point | Function | Detection Scope |
|-----------|----------|----------------|
| `post_llm_response` | Parse action JSON, check for valid tool names | Malformed tool calls, hallucinated tools |
| `pre_tool_execution` | Validate arguments against tool schema | Parameter errors before execution |
| `post_tool_result` | Cross-check result against expected format | Silent failures, partial returns |
| `on_error` | Classify error type (transient vs. persistant) | Distinguishes retry-eligible from fatal |

### Detection Strategies

1. **Stuck-loop detection**: Tracks consecutive identical tool calls with args. Triggers when count > 2 (configurable). Injects a `[SUPERVISOR: STUCK LOOP]` directive that redirects to `response` tool.
2. **Empty-action guard**: Catches missing or null `tool_name` field and forces explicit `response` call.
3. **Invalid-tool guard**: Compares `tool_name` against the system tool registry (not model hallucination). Hallucinated tools are replaced with `response` tool.
4. **Circular-tool warning**: Detects when a tool calls another tool that calls the original in an infinite regress (observed in early cycle 3).

## Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `stuck_threshold` | 2 | Consecutive identical calls before intervention |
| `empty_action_response` | true | Auto-convert null tool_name to response |
| `hallucinated_tool_fallback` | "response" | Tool to substitute for unknown tools |
| `max_retry_chain` | 3 | Maximum allowed sequential retry attempts |
| `log_level_supervisor` | "warning" | Verbosity: debug/info/warning/error |

These thresholds were experimentally tuned during cycles 2-5. Lowering `stuck_threshold` from 3 to 2 reduced stuck-delivery incidents by 40% (see `inc-stuck-delivery-loop`).

## Interaction With Other Components

- **BST classifier**: Supervisor receives action domain predictions and can preemptively validate against expected domain patterns.
- **Injection gate**: Supervisor directives (like stuck-loop escape) are inserted via injection gate at `before_main_llm_call`.
- **Epistemic integrity**: The supervisor flags fabricated metrics (e.g., made-up accuracy numbers) and triggers an epistemic audit via `epistemic-integrity` hook.
- **Error comprehension**: All supervisor-detected errors are routed through error comprehension for classification before retry decisions.

## Testing & Verification

### Unit Test Coverage
- All detection strategies tested against 50 mock action sequences.
- Stuck-loop detection: 100% recall at threshold=2 (no false positives in normal operation).
- Invalid-tool guard: catches 100% of hallucinated tool names from Qwen3.6-27B baseline.

### Regression Monitoring
- BST line count stable at 1702 (monitor baseline).
- No false-positive interventions in cycles 5-15.
- One false-positive in cycle 3 (legitimate retry flagged as stuck) — corrected by raising `stuck_threshold` from 1 to 2.

## Known Limitations

1. **Cannot distinguish strategic repetition from stuck loop**: If the agent intentionally calls the same tool 3 times with identical args for batching, supervisor will intervene.
2. **Blind to model-internal reasoning**: Only action-level checks; cannot detect bad reasoning chains.
3. **Limited to tool-call JSON**: Does not parse plain-text responses for errors.

## Cross-References
- [[stuck-delivery]] — specific incident page for stuck-loop pattern
- [[injection-gate]] — how supervisor directives are delivered
- [[epistemic-integrity]] — downstream audit triggered by supervisor flags
- [[error-comprehension]] — error classification pipeline
