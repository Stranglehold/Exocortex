# Design Note: Layer Coordination Protocol

**Status:** Pre-spec exploration. No eval data yet. This documents the architectural gap identified during the 2026-02-22 audit and sketches possible approaches. A full L3 spec requires empirical grounding — run the redesigned fallback through ST-002 first, then assess whether the remaining warning overlap justifies this build.

---

## The Problem

The 2026-02-22 audit identified that twelve layers of scaffolding operate without shared awareness of each other's state. Each layer reads its own inputs, performs its own logic, and writes its own outputs. No layer knows whether another layer has already addressed the same situation.

Concrete symptoms:
- **Four warning injectors** can fire simultaneously on a single bad tool call (fallback advisor, meta-reasoning gate, supervisor, structured retry)
- **The fallback system** doesn't know that BST is tracking the domain correctly, that working memory is holding the objective, or that the org kernel has already switched roles
- **The memory classifier** doesn't know whether the stock memorizers are also active (they were, writing duplicates)
- **The supervisor** reads `_tool_failures` but doesn't know whether the fallback advisor has already injected guidance about those same failures

The root cause is not that these layers are badly designed. It is that they have no coordination protocol — no shared medium through which to signal their state and read the state of others.

## What Exists Today

Agent-Zero provides `extras_persistent` — a dictionary on the agent instance that persists across turns within a session. Extensions can read and write arbitrary keys. This is the only shared state mechanism.

Current usage:
- `_tool_failures` — failure tracking (written by logger, read by advisor + supervisor)
- `bst_result` — BST classification output (written by BST, read by org dispatcher + memory enhancement)
- `working_memory` — entity store (written by working memory, read by... nothing else currently)
- `org_role` — current organization role (written by org dispatcher, read by... nothing else currently)

The medium exists. The protocol doesn't. Keys are ad-hoc. No extension publishes what it writes or subscribes to what it reads. No extension signals "I've handled this" in a way that other extensions can detect.

## Design Principles

1. **No new infrastructure.** Use `extras_persistent`. Don't build a message bus, event system, or pub-sub layer. The dictionary is sufficient; what's missing is convention, not mechanism.

2. **Opt-in, not mandatory.** Layers that don't need coordination (ontology query with empty store, memory maintenance on its periodic cycle) shouldn't be forced to participate.

3. **Read-only awareness.** A layer can check whether another layer has acted. It cannot tell another layer what to do. Coordination is achieved through visibility, not command.

4. **Deterministic.** No LLM calls for coordination decisions. If-then rules based on the presence or absence of keys.

## Sketch: The `_layer_signals` Convention

A single `extras_persistent` key — `_layer_signals` — holds a dictionary of layer signals for the current turn. Cleared at the start of each turn by the first extension to run.

```python
# Written by each layer after it acts:
signals = self.agent.get_data("_layer_signals") or {}
signals["bst"] = {
    "active": True,
    "domain": "dependency_mgmt",
    "confidence": 0.93,
    "turn": turn_number,
}
self.agent.set_data("_layer_signals", signals)

# Read by other layers before deciding whether to act:
signals = self.agent.get_data("_layer_signals") or {}
bst = signals.get("bst", {})
if bst.get("active") and bst.get("confidence", 0) > 0.8:
    # BST is tracking this turn confidently — adjust behavior
    pass
```

### Signal Schema (per layer)

Each participating layer writes a small dict under its key:

| Layer | Key | Signals |
|-------|-----|---------|
| BST | `bst` | `active`, `domain`, `confidence`, `turn` |
| Working Memory | `working_memory` | `active`, `objective_held`, `entity_count`, `turn` |
| Org Kernel | `org_kernel` | `active`, `current_role`, `switched_this_turn`, `turn` |
| Fallback Advisor | `fallback` | `active`, `fired_this_turn`, `advice_type`, `turn` |
| Meta-Gate | `meta_gate` | `active`, `correction_applied`, `tool_name`, `turn` |
| Supervisor | `supervisor` | `active`, `intervention_type`, `turn` |
| Structured Retry | `structured_retry` | `active`, `fired_this_turn`, `turn` |
| Memory Classifier | `memory_classifier` | `active`, `memories_stored`, `memories_filtered`, `turn` |

### Coordination Rules

With signals visible, layers can implement simple coordination:

**Fallback advisor:**
```python
signals = self.agent.get_data("_layer_signals") or {}
bst = signals.get("bst", {})
wm = signals.get("working_memory", {})
meta = signals.get("meta_gate", {})

# If BST is tracking confidently and working memory holds the objective,
# the agent is oriented. Raise the threshold before firing.
if bst.get("confidence", 0) > 0.85 and wm.get("objective_held"):
    effective_threshold = TOOL_THRESHOLD + 2  # More lenient
else:
    effective_threshold = TOOL_THRESHOLD

# If meta-gate already applied a correction this turn, don't pile on.
if meta.get("correction_applied"):
    return  # Meta-gate handled it deterministically
```

**Supervisor:**
```python
signals = self.agent.get_data("_layer_signals") or {}
fallback = signals.get("fallback", {})

# If fallback already fired this turn, don't inject a second warning.
if fallback.get("fired_this_turn"):
    # Log that we deferred to fallback, but don't inject.
    return
```

**Warning injection lane enforcement:**
```python
# Before any injector fires, check if another injector already fired this turn.
signals = self.agent.get_data("_layer_signals") or {}
injectors_fired = [
    k for k in ["fallback", "meta_gate", "supervisor", "structured_retry"]
    if signals.get(k, {}).get("fired_this_turn")
]
if len(injectors_fired) >= 1:
    # One warning is enough. Log and defer.
    return
```

## What This Enables

1. **Layer-aware fallback** (Priority 1 from ST-001): The fallback checks BST confidence and working memory state before firing. If other prosthetics are handling the situation, it stays quiet.

2. **Warning deduplication** (Phase 3 from audit): No more than one warning injector fires per turn. First to fire claims the slot; others defer.

3. **Self-describing system**: At any point, reading `_layer_signals` tells you which layers are active, what they're doing, and whether they've intervened. This is the "circulatory map" — the system describing its own state.

4. **Audit-free conflict detection**: If two layers both write `fired_this_turn: True` to the signals dict, that's a detectable event. The system can log it, measure it, and flag it for review — automatically, not through manual audit.

## What This Does NOT Do

- **Does not add LLM calls.** All coordination is if-then logic on dictionary values.
- **Does not change any layer's core function.** BST still classifies. Fallback still advises. Supervisor still steers. They just check the signals first.
- **Does not require all layers to participate.** Layers that don't write signals are simply invisible to the protocol. Other layers treat absent signals as "unknown" and fall back to their current behavior.
- **Does not create dependencies between layers.** No layer requires another layer's signal to function. Signals are advisory, not mandatory. The system degrades gracefully to current behavior if signals are missing.

## Open Questions

1. **Who clears the signals?** The first extension to run in the turn should initialize `_layer_signals` to `{}`. But execution order varies by hook. Need to identify the guaranteed-first hook point.

2. **Cross-turn memory?** Should signals persist across turns for trend detection (e.g., "BST has been high-confidence for the last 5 turns, so the agent is stable")? Or strictly per-turn? Per-turn is simpler and sufficient for warning coordination. Cross-turn enables richer adaptive behavior but adds complexity.

3. **Signal ordering within a turn?** If the fallback advisor runs in `tool_execute_before` and the supervisor runs in `message_loop_end`, the supervisor can see the fallback's signal but not vice versa. Is this a problem? Probably not — they're in different phases of the loop — but the hook execution order needs to be documented.

4. **Testing?** How do you write a test for "these two layers don't fire simultaneously"? Need a test harness that can simulate a full turn with all extensions active and assert on the final signal state.

## Recommendation

Don't build this yet. Run ST-002 with the current fallback fix. Measure the warning injection overlap empirically. If the lane-definition approach (Phase 3 from audit) reduces overlap sufficiently without inter-layer signaling, the simpler approach wins. If overlap persists despite lane definitions because layers can't see each other's state, this protocol becomes the necessary next step.

The right time to build this is when we have empirical evidence that lane definitions alone are insufficient. Until then, this design note serves as the architectural sketch for when that evidence arrives.
