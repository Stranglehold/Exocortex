# Methodology Tracker — Deployment Guide for Kestrel

## Kestrel Build-Out (2026-06-21) — gaps found + closed

Reviewed Opus's three files; found five real gaps (all verified against running code, DEC-041) and built the fixes. **Now FOUR files** (added the finalizer Opus flagged).

1. **Finalize trigger (the flagged integration question) — SOLVED.** `cycle_close.py` runs as a *subprocess* (agent invokes it via code_execution with `--cycle-type` args), so it cannot reach the in-process `_methodology_cycle_data` attr. Added **`_33_methodology_finalizer.py`** (tool_execute_after) that finalizes on the cycle-closing `response()` call — mirrors `_70_idle_trigger`'s detection. Option 2 from Opus's list.
2. **Affect read mismatch (critical).** The affect layer STORES via `agent.set_data("_affect_state")`; the tracker/advisor READ via `getattr(agent, "_affect_state")` → always "unknown" → advisor never fires. Fixed to `agent.get_data("_affect_state")` in `_09` and `_10`.
3. **Cycle type.** `_idle_current_mode` is set nowhere. Real source is `engine_state.json` → `last_cycle_type` (EXPLORE/BUILD/MAINTAIN). Fixed in `_09` and `_10`.
4. **Idle-cycle gating + boundary detection.** `_09` now tracks only when `cycle_active` (no interactive-turn pollution) and detects cycle boundaries via `last_cycle_start` — abnormal cycles (no clean response) are flushed as `outcome="incomplete"` when the next cycle starts. Captures failures, not just completions.
5. **Outcome inference.** Finalize infers outcome from cycle data (FLOW→completed, STAGNATION→stalled, DESPERATION→desperation, <50% tool success→error) so the advisor has success/failure signal instead of all-"completed".

**Validated on v16:** standalone logic tests pass (inference, finalize→JSONL, record_tool, engine_state read); 4 extensions load clean after restart; non-idle turns produce zero errors and zero spurious cycle inits (gating works). **Pending:** real idle-cycle run (needs v16 idle cycles enabled) to confirm end-to-end JSONL accumulation + advisor firing during FRICTION. v17 deploy held until v16 validates with real cycles.

---

## Overview

Three extensions that form the methodology learning layer:

| File | Hook | Priority | Purpose |
|------|------|----------|---------|
| `_09_methodology_tracker.py` | `message_loop_prompts_after` | _09 | Accumulates per-cycle data (steps, affect, strategy) |
| `_32_tool_call_tracker.py` | `tool_execute_after` | _32 | Records each tool call (name, success/failure) |
| `_10_strategy_advisor.py` | `message_loop_prompts_after` | _10 | Reads history, recommends strategies (affect-gated) |

## Deployment

### Step 1: Copy extensions to the correct hooks

```bash
# In the container (exocortex_v16):

# _09 tracker → message_loop_prompts_after (alongside _08_step_budget)
cp _09_methodology_tracker.py \
   /a0/usr/agents/agent0/extensions/python/message_loop_prompts_after/

# _10 strategy advisor → same hook (fires after _09)
cp _10_strategy_advisor.py \
   /a0/usr/agents/agent0/extensions/python/message_loop_prompts_after/

# _32 tool tracker → tool_execute_after (alongside _31_failure_lesson_capture)
cp _32_tool_call_tracker.py \
   /a0/usr/agents/agent0/extensions/python/tool_execute_after/
```

### Step 2: Wire finalization into cycle_close

The tracker accumulates data but needs a trigger to finalize (write to JSONL).
The cleanest integration: call `finalize()` from the existing cycle_close logic.

```python
# In whatever handles cycle completion:
from _09_methodology_tracker import finalize
finalize(agent, outcome="completed", artifacts=[...])
```

If cycle_close isn't easily hookable, add a `_09_methodology_finalizer.py`
to `message_loop_end/` that checks if the cycle is ending and calls finalize.

### Step 3: Add config section (optional)

In `/a0/usr/Exocortex/config.json`:

```json
{
    "methodology_tracker": {
        "enabled": true
    },
    "strategy_advisor": {
        "enabled": true
    }
}
```

Both default to enabled if the config section is missing.

### Step 4: Verify

Run a cycle and check:
1. `[METHOD-TRACK] Cycle init:` appears in logs at cycle start
2. `[TOOL-TRACK]` does NOT crash (silent passthrough on error)
3. `[METHOD-TRACK] Finalized:` appears at cycle end
4. `methodology_tracker.jsonl` exists in `/a0/usr/workdir/` with one record
5. After 5+ cycles: `[STRATEGY]` appears during FRICTION cycles with a recommendation

### Step 5: Deploy to v17

Same files, same hook locations. The tracker file path is per-container
(each agent builds its own history).

## How It Works

```
Turn 1: _09 initializes → reads cycle_type, strategy, affect
Turn 2: _09 increments steps, tracks affect transition
         Tool call → _32 records tool name + success
Turn 3: _09 increments, _10 checks affect
         If FRICTION: _10 reads history, recommends strategy
         ...
Turn N: cycle_close → finalize() writes JSONL record
```

## Data Format (methodology_tracker.jsonl)

Each line is one cycle:
```json
{
    "cycle_id": "agent_1718916000",
    "ts_start": "2026-06-20T20:00:00Z",
    "ts_end": "2026-06-20T20:03:00Z",
    "cycle_type": "EXPLORE",
    "strategy_tag": "investigation",
    "affect_start": "FLOW",
    "affect_end": "FLOW",
    "affect_transitions": ["FLOW"],
    "steps_taken": 7,
    "tool_count": 4,
    "tool_ok": 4,
    "tool_fail": 0,
    "tool_success_rate": 1.0,
    "unique_tools": ["search_engine", "wiki_read"],
    "outcome": "completed",
    "artifacts": ["wiki/quantum_sensing.md"]
}
```

## Dependencies

None beyond Agent Zero's existing `agent`, `helpers.extension`, and standard library.
No LLM calls. No API costs. No external packages.

## Verification Checklist

- [ ] _09 fires every turn (check `[METHOD-TRACK] Cycle init:` in logs)
- [ ] _32 fires on tool calls (check that tool_ok/tool_fail increment)
- [ ] Finalization writes to JSONL (check file exists after first cycle)
- [ ] _10 stays silent during FLOW (no strategy noise)
- [ ] _10 recommends during FRICTION (after 5+ history records)
- [ ] No crashes on any edge case (subordinate agents, missing attrs, empty history)
- [ ] Cache not busted (extras_temporary used, not history_output mutation)
