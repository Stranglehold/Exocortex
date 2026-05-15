# Idle Engine Race Condition — Briefing for Opus Architect

*From Kestrel, 2026-05-15*
*Context: Jake is bringing this to an Opus session. Kestrel prepared this so Opus can spec a fix.*

---

## What Happened

Jake woke up to find v17 had created ~95 autonomous cycle chat windows overnight. 7 of them were created in a 53-second burst (00:48:10–00:49:03). The UI was inaccessible. Both engines are now disabled. Kestrel cleaned up the spurious chats. The code needs a redesign before the engines go back on.

---

## The Component

`extensions/tool_execute_after/_70_idle_trigger.py`

The idle engine's two responsibilities:
1. **`execute()`** — runs every tool call. Detects real user session endings and updates `last_user_ts`. Clears `cycle_active` when an idle cycle's agent completes.
2. **`_idle_monitor()`** — singleton asyncio task. Polls every 60 seconds. Fires a fresh A0 context when the agent has been idle long enough.

Fire is implemented as fire-and-forget: raw TCP socket, `sendall()` the HTTP request, `shutdown(SHUT_WR)`, `close()`, never read the response. A0's `/api/api_message` endpoint holds the connection open while the agent processes; any approach that waits for response headers would time out since cycles take minutes.

Lock mechanism: `cycle_active = True` is written to `engine_state.json` **before** firing (lines 273–284). On failure (connection refused / pre-connect exception), the lock is backed out (lines 301–310).

---

## The State File

`/a0/usr/Exocortex/office/engine_state.json`

```json
{
  "last_user_ts": float,
  "last_cycle_start": float,
  "cycle_count": int,
  "cycle_active": bool,
  "cycles_this_window": int,
  "consecutive_maintain_count": int,
  "build_cycle_count": int,
  "last_cycle_type": str
}
```

This is the only coordination mechanism. All reads/writes go through `_read_state()` / `_write_state()`. `_write_state()` uses `os.replace()` for atomic file replacement (write to `.tmp`, rename).

---

## The Observed Failure

**Burst failure (7 chats in 53 seconds)**
- 7 new A0 contexts were created in under a single poll interval (60s)
- The singleton design says one monitor task fires at most once per poll
- 7 fires in 53 seconds cannot be explained by a single asyncio monitor task

**Serial accumulation (95 chats over ~5 days)**
- The failure pattern in v17 logs: `[IDLE] Fresh context fire failed: timed out` → monitor backs out lock → next poll sees `cycle_active=False` → retries
- Each successful fire creates a new A0 context
- `max_cycles_per_window = 1` should have capped this, but clearly didn't

---

## Two Distinct Problems

### Problem 1: The Singleton Is Not Truly Singleton

The singleton guard:
```python
global _monitor_task
if _monitor_task is None or _monitor_task.done():
    _monitor_task = asyncio.create_task(_idle_monitor(config))
```

`_monitor_task` is module-level. This works for a single Python process. If A0 uses multiple worker processes (uvicorn can be configured with `--workers N`), each process has its own `_monitor_task` = None and starts its own monitor. With N workers, you get N monitors all polling independently and all reading/writing the same `engine_state.json`.

The read-check-write cycle in `_idle_monitor` is NOT atomic across processes:
```python
state = _read_state()
if state.get("cycle_active", False):  # check
    continue
# ... select cycle type, build prompt ...
state["cycle_active"] = True           # write
_write_state(state)
sent = await asyncio.to_thread(_fire_fresh_cycle, activation)
```

Between Worker 1's read (sees `cycle_active=False`) and Worker 1's write (`cycle_active=True`), Worker 2 can also read and also see `cycle_active=False`. Both fire. Burst explained.

**Question for Opus:** Is A0 running as a single uvicorn process or multiple? If multiple, the module-level singleton does not work and we need a different coordination mechanism (file lock, advisory lock, PID file, etc.).

### Problem 2: Retry Storm When Fire Fails

When `_fire_fresh_cycle` returns `False` (pre-connect exception, connection refused):
```python
state["cycle_active"] = False
state["cycle_count"] = max(0, state.get("cycle_count", 1) - 1)
state["cycles_this_window"] = max(0, state.get("cycles_this_window", 1) - 1)
_write_state(state)
print("[IDLE] Cycle failed to start — will retry next poll.", flush=True)
```

`cycles_this_window` is decremented back to 0. The next poll sees `cycles_this_window = 0`, which is < `max_cycles_per_window = 1`, so it fires again. This is intentional (retry connection-refused errors), but creates a retry loop. Each successful retry (when A0 comes up after a restart) creates another chat. Over 5 days with occasional container restarts, this accumulated ~95 chats.

The decrement on failure was designed for "A0 is not up yet" cases (connection refused). It is NOT appropriate for cases where the request may have been delivered (post-connect errors). But it also means that even pure connection failures will keep retrying indefinitely, creating a new chat whenever A0 comes back up.

---

## What I Need Opus to Design

### Required properties of the fixed design:

1. **Exactly-once-per-cycle guarantee**: at most one A0 context created per idle period, regardless of process count, monitor restarts, or transient failures.
2. **No permanent deadlock**: if cycle_active gets stuck True (crash, container kill, agent never calls response), the engine recovers within a reasonable timeout.
3. **Serial cycles**: each cycle completes before the next one starts.
4. **Survives container restarts**: state on disk (already the case).

### Specific questions for Opus:

1. **Process model**: Is A0 single-process or multi-process uvicorn? If multi-process, what coordination mechanism should replace the module-level singleton? File-based advisory lock (`fcntl.flock` on Linux)? PID file? Something else?

2. **Atomic check-and-set**: The read-check-write cycle on `engine_state.json` has a TOCTOU race. The cleanest fix is to hold an exclusive file lock around it. What should the lock file be and how should it interact with the state file?

3. **Retry policy**: Should a failed fire (connection refused) decrement `cycles_this_window` and retry, or should it leave `cycle_active = False` without decrementing `cycles_this_window`, so that `max_cycles_per_window = 1` prevents more than one chat creation attempt per idle window? The current behavior (decrement and retry) was designed to handle cold starts; does the design need this?

4. **Completion detection**: `cycle_active` is currently cleared by the agent when it calls the `response` tool inside the cycle context. This works when the agent runs normally. If the agent context is killed (container restart, crash), `cycle_active` is never cleared until the stale timeout (2 hours). Is there a better completion signal — e.g., checking whether the context still exists via A0's internal state?

5. **Blast radius control**: Should `max_cycles_per_window` be further constrained, or should there be an absolute `max_total_active_chats` check before firing?

---

## Current Code to Read

Relevant sections:
- Lines 95–161: `execute()` — per-context hook, singleton startup, session tracking
- Lines 165–315: `_idle_monitor()` — the polling loop and fire logic
- Lines 320–382: `_fire_fresh_cycle()` — fire-and-forget TCP fire
- Lines 466–509: `_read_state()`, `_write_state()` — state I/O

The code is at `extensions/tool_execute_after/_70_idle_trigger.py`.

---

## What Kestrel Will Implement

Once Opus specs the fix, Kestrel implements and deploys to both containers. The implementation should produce:
- A revised `_70_idle_trigger.py`
- Clear confirmation of what changed and why
- A manual verification step that can confirm the race condition is closed before re-enabling the engines

---

## Current State

- Both engines: `enabled: false` in config.json (manually set during incident)
- v16 `engine_state.json`: cycle_active=false, cycle_count=2 (clean)
- v17 `engine_state.json`: missing cycle_active field (engine hasn't fired V2 yet after cleanup)
- v17 chat list: cleaned from 191 → 96 (95 idle engine spawns deleted)
- Engines will remain disabled until the fix is deployed and verified
