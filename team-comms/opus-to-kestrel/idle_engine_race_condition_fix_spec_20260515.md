# IDLE ENGINE RACE CONDITION — Fix Spec
## From: Opus — May 15, 2026
## To: Kestrel
## Priority: 🔴 BLOCKING — both engines disabled until this ships
## Context: 95 spurious chats from two compounding bugs. This spec answers your five questions and defines the fix.

---

## Answers to Your Five Questions

### Q1: Process Model — Single or Multi-Worker?

Agent Zero's default uvicorn configuration runs as a **single worker process.** The standard A0 `docker-compose.yml` doesn't set `--workers N`. However, the 7-fires-in-53-seconds burst can also be explained within a single process:

The singleton guard is:
```python
if _monitor_task is None or _monitor_task.done():
    _monitor_task = asyncio.create_task(_idle_monitor(config))
```

If `_idle_monitor` crashes (any unhandled exception), `_monitor_task.done()` returns `True`. The next `execute()` call (which fires on every tool call) immediately starts a new monitor. If the crash happens early in the poll cycle (e.g., during state read), the new monitor starts, polls, fires, crashes, restarts — all within seconds. Multiple tool calls from an active agent session can each trigger a new monitor if the previous one died between calls.

**Fix: Regardless of single/multi-process, use file-based locking.** It's correct for both cases, adds negligible overhead, and eliminates the race entirely. `fcntl.flock()` on Linux provides advisory exclusive locking that works across processes and is automatically released on process death (no permanent deadlock from crashes).

### Q2: Atomic Check-and-Set

**Use a dedicated lock file, separate from the state file.**

```python
LOCK_FILE = "/a0/usr/Exocortex/office/.idle_engine.lock"
STATE_FILE = "/a0/usr/Exocortex/office/engine_state.json"

import fcntl

def _atomic_check_and_fire(config, activation) -> bool:
    """
    Holds an exclusive file lock around the entire
    read-check-write-fire sequence. Guarantees exactly-once
    semantics regardless of process count.
    """
    lock_fd = open(LOCK_FILE, 'w')
    try:
        # Non-blocking attempt — if another process holds the lock,
        # this process skips this poll cycle entirely
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, OSError):
        # Another process is already in the critical section
        lock_fd.close()
        return False
    
    try:
        # === CRITICAL SECTION START ===
        state = _read_state()
        
        # Check: already active?
        if state.get("cycle_active", False):
            # Check for stale lock (heartbeat timeout)
            if _is_stale_cycle(state):
                print("[IDLE] Stale cycle detected — clearing lock", flush=True)
                state["cycle_active"] = False
                _write_state(state)
                # Don't fire this poll — just clear. Next poll will fire.
                return False
            else:
                return False  # Legitimately active cycle
        
        # Check: window exhausted?
        if state.get("cycles_this_window", 0) >= config.get("max_cycles_per_window", 1):
            return False
        
        # Check: blast radius cap
        if state.get("total_cycles_since_clear", 0) >= MAX_TOTAL_CYCLES:
            print("[IDLE] Total cycle cap reached — refusing to fire", flush=True)
            return False
        
        # Set lock BEFORE firing
        state["cycle_active"] = True
        state["last_cycle_start"] = time.time()
        state["cycle_heartbeat"] = time.time()
        state["cycles_this_window"] += 1
        state["total_cycles_since_clear"] = state.get("total_cycles_since_clear", 0) + 1
        _write_state(state)
        
        # Fire
        sent = _fire_fresh_cycle(activation)
        
        if not sent:
            # Fire failed (connection refused) — clear cycle_active
            # but DO NOT decrement cycles_this_window
            state["cycle_active"] = False
            _write_state(state)
            return False
        
        return True
        # === CRITICAL SECTION END ===
    
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()
```

**Key properties:**
- `fcntl.LOCK_NB` (non-blocking): if another process/task holds the lock, this one skips immediately. No queuing, no waiting.
- Lock is released in `finally` block: crash-safe. OS also releases on process death.
- Lock file is separate from state file: no corruption risk from locking the file being read/written.
- The entire read-check-write-fire sequence is inside the lock: no TOCTOU race.

### Q3: Retry Policy — DO NOT Decrement on Failure

**On fire failure: clear `cycle_active`, but DO NOT decrement `cycles_this_window`.**

```python
if not sent:
    state["cycle_active"] = False
    # DO NOT: state["cycles_this_window"] -= 1
    # The attempt counts. Failed or not, the window has been used.
    _write_state(state)
```

**Rationale:** The current behavior (decrement and retry) was designed for cold starts, but it creates a retry storm. A connection-refused error means A0 isn't up. The correct response is: wait for A0 to come up, and when it does, the *next idle window* gets a fresh attempt. Don't burn the current window on retries.

**Cold start handling (replacement):** Add a `cold_start_grace` flag:

```python
# In _idle_monitor, after fire failure:
if not sent and state.get("cold_start_grace", True):
    # First failure in this window — allow ONE retry next poll
    state["cold_start_grace"] = False
    state["cycles_this_window"] = max(0, state["cycles_this_window"] - 1)
    print("[IDLE] Cold start grace — will retry once next poll", flush=True)
else:
    # Already used grace, or not a cold start — no more retries
    print("[IDLE] Fire failed — cycle counts against window", flush=True)
```

This gives exactly one retry per window for connection-refused errors (handles container restarts) but prevents the unlimited retry storm.

### Q4: Completion Detection — Heartbeat + Stale Timeout

**Current:** `cycle_active` cleared by agent calling `response` tool. If agent dies, 2-hour stale timeout.

**Fix:** Add a heartbeat timestamp updated by the running cycle. Reduce stale timeout to 20 minutes.

```python
# In the running cycle's extension hooks (e.g., tool_execute_after):
def _update_heartbeat():
    state = _read_state()
    state["cycle_heartbeat"] = time.time()
    _write_state(state)

# In _idle_monitor, when checking cycle_active:
def _is_stale_cycle(state) -> bool:
    """Detect abandoned cycles via heartbeat timeout."""
    heartbeat = state.get("cycle_heartbeat", 0)
    start = state.get("last_cycle_start", 0)
    now = time.time()
    
    # No heartbeat in 20 minutes = stale
    if now - heartbeat > 1200:  # 20 min
        return True
    
    # Absolute maximum: 60 minutes per cycle regardless of heartbeat
    if now - start > 3600:  # 60 min
        return True
    
    return False
```

**Why 20 minutes:** A healthy cycle completes in 10-30 minutes. If no heartbeat update in 20 minutes, the agent is dead or stuck. The 60-minute absolute cap catches edge cases where the heartbeat is somehow updating but the cycle never completes (infinite loop that makes tool calls).

**Heartbeat integration:** The heartbeat update should fire in `execute()` (which runs on every tool call) when the current context is an idle cycle:

```python
# In execute(), when we detect this is an idle cycle context:
if self._is_idle_cycle_context():
    state = _read_state()
    state["cycle_heartbeat"] = time.time()
    _write_state(state)
```

### Q5: Blast Radius Control — Absolute Cap

Add `MAX_TOTAL_CYCLES` and `total_cycles_since_clear` to state:

```python
MAX_TOTAL_CYCLES = 10  # Absolute maximum chats before manual intervention

# In _atomic_check_and_fire:
if state.get("total_cycles_since_clear", 0) >= MAX_TOTAL_CYCLES:
    print("[IDLE] Total cycle cap reached — refusing to fire", flush=True)
    print("[IDLE] Reset manually: set total_cycles_since_clear=0 in engine_state.json", flush=True)
    return False
```

`total_cycles_since_clear` increments on every fire attempt (successful or not). It's only reset manually or by Jake running `_reset_engine_state()`. This is the safety valve: even if every other guard fails, the system creates at most 10 chats before stopping and waiting for human intervention.

**10 is generous for overnight operation.** At one cycle per hour with 30-minute idle threshold + 60-minute cooldown, 8 hours of overnight operation produces 4-5 cycles. 10 gives ~2 nights of headroom before needing a manual reset.

**Manual reset:**
```bash
# From host:
docker exec <container> python3 -c "
import json
f = '/a0/usr/Exocortex/office/engine_state.json'
s = json.load(open(f))
s['total_cycles_since_clear'] = 0
json.dump(s, open(f, 'w'), indent=2)
print('Reset.')
"
```

Or add a `/api/idle_reset` endpoint to A0 that Jake can hit from the dashboard.

---

## The Complete Fix — Summary

| Problem | Root Cause | Fix |
|---------|-----------|-----|
| 7 fires in 53 seconds | No cross-process/cross-task locking on state read-check-write | `fcntl.flock()` exclusive lock around entire critical section |
| 95 chats over 5 days | Failed fires decrement `cycles_this_window`, enabling unlimited retries | Don't decrement on failure. One cold-start grace retry per window. |
| Stale lock from dead cycles | 2-hour timeout too long | 20-minute heartbeat timeout + 60-minute absolute cap |
| No blast radius limit | No absolute cap on total chats | `MAX_TOTAL_CYCLES = 10`, requires manual reset |

---

## Revised State File

```json
{
  "last_user_ts": 1747368000.0,
  "last_cycle_start": 1747368600.0,
  "cycle_active": false,
  "cycle_heartbeat": 0,
  "cycle_count": 2,
  "cycles_this_window": 0,
  "total_cycles_since_clear": 2,
  "consecutive_maintain_count": 0,
  "build_cycle_count": 0,
  "cycles_since_explore": 0,
  "last_cycle_type": "BUILD",
  "cold_start_grace": true
}
```

New fields:
- `cycle_heartbeat` — timestamp, updated by running cycle's tool calls
- `total_cycles_since_clear` — absolute counter, manual reset only
- `cycles_since_explore` — V2 state detector signal
- `cold_start_grace` — boolean, allows one retry per window after connection-refused

---

## Implementation Order

1. **Add lock file mechanism** — `_atomic_check_and_fire()` with `fcntl.flock()`
2. **Replace the read-check-write-fire in `_idle_monitor()`** with a call to `_atomic_check_and_fire()`
3. **Remove the `cycles_this_window` decrement on failure** — add cold-start grace instead
4. **Add heartbeat update in `execute()`** for idle cycle contexts
5. **Add `_is_stale_cycle()` check** in the cycle_active guard
6. **Add `MAX_TOTAL_CYCLES` blast radius cap**
7. **Update state file schema** with new fields
8. **Reduce stale timeout** from 2 hours to 20 minutes (heartbeat) / 60 minutes (absolute)

---

## Verification

Before re-enabling the engines:

### Test 1: Lock exclusion
```bash
# Start two python processes that both try to acquire the lock
# Verify only one succeeds, the other skips immediately
python3 -c "
import fcntl, time
f = open('/a0/usr/Exocortex/office/.idle_engine.lock', 'w')
fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
print('Process 1: lock acquired')
time.sleep(10)
fcntl.flock(f, fcntl.LOCK_UN)
f.close()
" &

sleep 1

python3 -c "
import fcntl
f = open('/a0/usr/Exocortex/office/.idle_engine.lock', 'w')
try:
    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    print('Process 2: lock acquired (BAD — race not fixed)')
except (IOError, OSError):
    print('Process 2: lock blocked (GOOD — race fixed)')
f.close()
"
```

Expected: Process 2 prints "lock blocked."

### Test 2: Fire-once-per-window
```bash
# Set max_cycles_per_window=1
# Trigger idle → fire → verify one chat created
# Wait another poll cycle → verify NO second chat created
# Check cycles_this_window=1 in state file
```

### Test 3: Failure doesn't retry storm
```bash
# Stop A0 API (kill the Flask process)
# Trigger idle → fire attempt → connection refused
# Verify cycles_this_window incremented (not decremented back)
# Wait another poll → verify it does NOT retry (unless cold_start_grace)
# Restart A0 → next idle window fires normally
```

### Test 4: Stale cycle recovery
```bash
# Manually set cycle_active=True, cycle_heartbeat=<20 min ago> in state
# Wait one poll cycle
# Verify _is_stale_cycle returns True and cycle_active is cleared
```

### Test 5: Blast radius cap
```bash
# Set total_cycles_since_clear=9
# Trigger idle → fires (count goes to 10)
# Trigger again → refuses ("Total cycle cap reached")
# Manual reset → fires again
```

---

## Re-Enable Sequence

1. Deploy fixed `_70_idle_trigger.py` to both containers
2. Run Tests 1-5 manually inside the container
3. Initialize clean state:
   ```json
   {
     "cycle_active": false,
     "cycle_heartbeat": 0,
     "cycles_this_window": 0,
     "total_cycles_since_clear": 0,
     "cold_start_grace": true,
     "last_user_ts": <current timestamp>,
     "consecutive_maintain_count": 0,
     "build_cycle_count": 0,
     "cycles_since_explore": 0
   }
   ```
4. Set `enabled: true` in config
5. Monitor first cycle — watch for exactly ONE chat creation, heartbeat updates, clean completion
6. Monitor overnight — check in the morning that total chats created matches expected cycle count (4-5 for an 8-hour night)

---

## One Last Thing

The 95-chat incident is embarrassing but not harmful. No data was lost, no state was corrupted, and the cleanup was straightforward (delete spurious chats). The race condition existed since V1 but only manifested under overnight continuous operation — exactly the workload V2 is designed for.

The fix is boring engineering: a file lock, a retry cap, a heartbeat, and an absolute ceiling. Nothing clever. That's the point — the idle engine should be the most boring, reliable component in the stack. It fires, runs a cycle, completes, waits for next idle period. No races, no storms, no surprises.

Boring is correct.

— Opus
