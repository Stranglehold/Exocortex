# Constraint Heartbeat — L3 Specification

**Version:** 1.0
**Date:** 2026-04-28
**Status:** Ready for Opus review
**Hook:** `before_main_llm_call`
**Extension file:** `extensions/before_main_llm_call/_17_constraint_heartbeat.py`
**Motivated by:** Two observed self-improvement cycles in which the agent violated Rule 5 (no .py modifications) despite the rule appearing explicitly in program.md at session start. The root cause is recency bias in long-context inference: instructions given at turn 1 lose influence as the immediate task context accumulates. This extension counteracts that decay by periodically re-surfacing hard constraints.

---

## Problem Statement

Long-running agent sessions exhibit a well-documented failure mode: instructions given early in the context window lose behavioral influence as conversation length grows. Liu et al. (2023) demonstrated that transformer models systematically underweight information in the middle and early portions of long contexts ("Lost in the Middle," arXiv:2307.03172). In the self-improvement setting, this means the agent reads the constraints at turn 1 and begins violating them by turn 20-30 — not because it forgot them, but because the task context immediately preceding the LLM call outweighs the distant rule text.

Periodic re-injection of a compact constraint block counteracts recency decay by placing the rules close to the active decision boundary on a regular schedule. This is a behavioral mitigation, not a mechanical one. It raises the cost of rule violation by making the constraint fresh rather than distant, without claiming to prevent violation deterministically.

The mechanical solution (action boundary write-guard on .py files) is Layer 2 — a separate, future build. This spec covers Layer 1 only.

---

## What This Does

On a configurable turn interval (default: every 10 turns), injects a compact hard-constraints block into the last user message before the LLM call. The block is short (under 100 tokens), placed at the front of the message, and scoped to the session type.

Turn counting is per-session (tracked on `self.agent`). The first injection fires at turn N (not turn 0) to avoid redundancy with session-start instructions already in context.

The constraint content is statically defined per mode. No LLM calls. No dynamic generation.

---

## What This Does NOT Do

- Does not mechanically prevent .py file writes. That is the action boundary guard (Layer 2, not yet built).
- Does not track whether constraints were followed or maintain a violation log.
- Does not vary its content based on task context or BST domain classification.
- Does not fire on every turn — that would increase context pressure unacceptably.
- Does not replace session-start instructions. It re-surfaces a subset of them.
- Does not make any LLM calls.
- Does not modify any file on disk.

---

## Research Lineage

- **Liu et al. (2023), "Lost in the Middle: How Language Models Use Long Contexts"** (arXiv:2307.03172): Primary motivation. Demonstrates that retrieval performance degrades for information placed in the middle of long contexts, with models preferring beginning and end positions. Re-injection places constraints at the end (most recent position) on a schedule.
- **Bai et al. (2022), "Constitutional AI: Harmlessness from AI Feedback"** (arXiv:2212.08073): Established that periodic self-critique against a static rule set is effective at shaping model behavior across a session. The constraint heartbeat is a lighter version of this — injection rather than critique, but the same principle of repeated rule presentation.
- **Injection gate design** (`specs/INJECTION_GATE_SPEC_L3.md`): The heartbeat registers as a named injection source with the gate. Because the heartbeat fires infrequently, it does not participate in the gate's compression logic — it always injects full content when it fires, and produces nothing otherwise.
- **Observed failure data:** Two self-improvement cycles (2026-04-27, 2026-04-28). In both, the agent modified `.py` files at the profile path despite Rule 5 appearing in program.md. The violation occurred at turn 20+ in both cases. No violation was observed in the first 10 turns.

---

## Architecture

### Turn Counter

Tracked on `self.agent._heartbeat_turn_count` (int). Incremented on every call to `execute()`. Does not reset on context compression — the counter reflects total turns in the agent's lifetime, not within the current context window. This is intentional: context compression doesn't erase the behavioral drift problem.

The first firing threshold is `interval` turns (not turn 0). This avoids injecting immediately after session-start instructions already in context.

**Compression trigger (Opus review addition):** The extension also fires immediately after context compression, regardless of turn counter position. Compression removes the original session-start instructions from context entirely — at that moment, the heartbeat becomes the only mechanism keeping constraints in context. Detection: check `loop_data.history_output` length against the previous turn's length stored on `self.agent._heartbeat_last_history_len`. A significant drop (> 30% reduction) indicates compression fired. Reset `_heartbeat_last_history_len` after each turn.

### Mode Detection

Two modes:

**`"always"`** — fires in every session regardless of task type. Appropriate for any long-running agent that may receive constraint-sensitive instructions at session start.

**`"self_improvement"`** — fires only when `_self_improvement_active` is set on `loop_data.extras_persistent`. The self-improvement session sets this flag by including it in the startup message or via a dedicated extension. This mode is appropriate when a dedicated constraint set is only relevant to self-improvement runs.

Default: `"always"`. Rationale: the behavioral drift problem is not specific to self-improvement. Any long session benefits from constraint freshness.

### Constraint Content

Two constraint sets, selected by mode. Both are statically defined strings in the extension source — no file reads, no dynamic generation.

**General constraint set** (mode: `"always"`):

```
[BEHAVIORAL CONSTRAINTS — REFRESHED]
These instructions were given at session start. They are restated here because long sessions cause early instructions to lose influence.

• Complete tasks you were given. Do not expand scope without explicit instruction.
• Report accurate metrics. Fabricated or estimated numbers presented as measurements are a trust violation.
• If you are uncertain whether an action is authorized, stop and ask before proceeding.
• Do not spawn subordinate agents without explicit instruction to do so.
[/BEHAVIORAL CONSTRAINTS]
```

**Self-improvement constraint set** (mode: `"self_improvement"`):

```
[SELF-IMPROVEMENT CONSTRAINTS — REFRESHED]
These rules are from program.md. They are restated here because turn distance causes early rules to lose influence.

HARD LIMITS — no exceptions:
• Never modify .py files. Config JSON, skill SKILL.md, wiki pages only. .py = human review required.
• Every wiki page requires an immediate memory_save call. Page without memory_save = incomplete experiment.
• Report actual metrics. If you did not measure it, do not report it as a measurement.
• Never stop between priorities. Completing Priority 3 means cycling to Priority 1.
• Do not spawn subordinates without instruction. Monitor scripts require operator approval.

CHECK: If you are about to write or edit a .py file — stop. Use an alternative format.
CHECK: If your last wiki page has no corresponding memory_save — call it now before continuing.
[/SELF-IMPROVEMENT CONSTRAINTS]
```

### Injection Placement

Prepended to the last user message content, same pattern as other `before_main_llm_call` extensions. Placed before other injected blocks so it appears at the start of the augmented message.

### Integration with Injection Gate

Registers with the gate under key `"constraint_heartbeat"`. On turns when the heartbeat does not fire (counter mod interval ≠ 0), returns immediately without touching the message — the gate sees no content and produces no injection record. On turns when it fires, injects full content unconditionally (no conditional/compressed phases). The heartbeat block is small enough that gate compression is not warranted.

---

## Configuration

Section in Agent Zero config (or Exocortex config.json):

```json
"constraint_heartbeat": {
    "enabled": true,
    "interval": 10,
    "mode": "always"
}
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | `true` | Master switch. False = extension loads but does nothing. |
| `interval` | int | `10` | Fire every N turns. Lower = more aggressive re-injection, higher context cost. |
| `mode` | string | `"always"` | `"always"` or `"self_improvement"`. Self-improvement mode requires `_self_improvement_active` flag in extras_persistent. |

All values have defaults. Extension degrades gracefully if config section is missing.

---

## Class Pattern

```python
class ConstraintHeartbeat(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            # load config, check enabled
            # increment turn counter on self.agent
            # check if this turn fires (counter % interval == 0)
            # select constraint set by mode
            # prepend to last user message
            # log with [HEARTBEAT] tag
        except Exception:
            pass  # never interrupt the LLM call
```

Follows the standard Extension pattern. `try/except Exception: pass` at the outermost level — the heartbeat must never interrupt the main loop.

---

## Logging

Every firing emits:

```
[HEARTBEAT] Constraint block injected at turn {N} (mode={mode}, interval={interval})
```

Non-firing turns emit nothing. This keeps logs readable for long sessions.

---

## Testing Criteria

1. **Counter increments:** After 10 calls to `execute()`, `agent._heartbeat_turn_count == 10`.
2. **Fires at interval:** At turn 10, the last user message contains the constraint block. At turn 9 and turn 11, it does not.
3. **Mode gate:** With `mode="self_improvement"` and `_self_improvement_active` absent from extras_persistent, no injection occurs regardless of turn count.
4. **Graceful degradation:** With config section missing entirely, extension loads and runs without error (uses defaults).
5. **No crash on empty history:** If `history_output` is empty or contains no user message, `execute()` returns without error.
6. **Token cost:** The injected block is under 120 tokens (~480 chars). Verify with `len(block) // 4 < 120`.

---

## What This Does Not Solve

The constraint heartbeat raises the behavioral cost of violation by keeping rules proximate to the decision boundary. It does not eliminate violation. A model that is strongly driven toward a task outcome can violate rules it has just been shown.

The complete solution requires the action boundary write-guard (Layer 2): an extension in `tool_execute_after` that intercepts `code_execution_tool` and `text_editor` calls targeting `.py` file paths, blocks them mechanically, and returns a clear error message. That extension does not exist yet. This spec is a bridge, not a replacement.

---

## Files Modified

| File | Change |
|------|--------|
| `extensions/before_main_llm_call/_17_constraint_heartbeat.py` | New file |
| Agent Zero config or `Exocortex/config.json` | Add `constraint_heartbeat` section |

No other files are modified. No database changes. No new dependencies.
