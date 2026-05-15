"""
Idle Time Engine — Trigger
==========================
Hook: tool_execute_after (_70_)

When the agent has been idle (no real user messages) for idle_threshold_seconds,
activates one autonomous work cycle (MAINTAIN/BUILD/EXPLORE) per idle window by
posting the idle activation prompt to the A0 REST API without a context_id.

Race Condition Fix (2026-05-15):
  Previous version had two compounding bugs:
  (1) No cross-process/cross-task lock — multiple monitor instances could fire in
      parallel. Fixed with fcntl.flock() exclusive file lock around the entire
      read-check-write-fire sequence (_atomic_check_and_fire).
  (2) Failed fires decremented cycles_this_window, enabling unlimited retries.
      Fixed: failed attempts count against the window. One cold-start grace retry
      per window (for container cold starts), then no more retries until next window.
  Additional guards: heartbeat timeout (20 min), absolute cycle cap (MAX_TOTAL_CYCLES).

Cycle sequencing — EDGE-TRIGGERED, NOT LEVEL-TRIGGERED:
  An idle window opens when the user goes absent. Within one idle window, at most
  max_cycles_per_window cycles fire. The window resets when the user sends a real
  message. Being absent for 8 hours fires ONE cycle (or max_cycles_per_window), not 16.

Architecture:
  - Singleton monitor: one asyncio task per process, regardless of how many agent
    contexts are active. Module-level _monitor_task guards this.
  - File-based state: engine_state.json persists all counters across context changes.
  - File-based lock: .idle_engine.lock (fcntl.flock) prevents parallel fires across
    processes and rapid monitor restarts.
  - execute() still runs per-context to detect real user session endings and update
    the heartbeat for the running idle cycle.

Pause control: /a0/usr/Exocortex/office/control.json → {"paused_until": <float ts>}
  Written by the /api/idle_control endpoint.

Config: /a0/usr/Exocortex/config.json → "idle_time_engine" section
  enabled: true
  idle_threshold_seconds: 1800
  max_cycles_per_window: 1
  min_gap_between_cycles_seconds: 1800
  max_steps_per_cycle: 20
  max_cycle_duration_seconds: 7200  (legacy — replaced by heartbeat + absolute cap)
  maintain_cooldown_threshold: 3
  explore_time_cap_cycles: 5

Fire condition (logical AND, all checked inside file lock):
  1. User absent for >= idle_threshold_seconds
  2. No cycle currently running (cycle_active interlock)
  3. cycles_this_window < max_cycles_per_window
  4. total_cycles_since_clear < MAX_TOTAL_CYCLES (blast radius cap)
  5. If cycles_this_window > 0: time since last_cycle_start >= min_gap

Stale cycle detection (inside lock, when cycle_active is True):
  - No heartbeat update in 20 minutes → stale (cycle crashed or hung)
  - Cycle older than 60 minutes absolute → stale regardless of heartbeat
  Stale: clear cycle_active this poll, fire next poll.

State file: /a0/usr/Exocortex/office/engine_state.json
  last_user_ts               — float: unix timestamp of last real user session end
  last_cycle_start           — float: unix timestamp of last cycle fire
  cycle_active               — bool: True while a cycle is running
  cycle_heartbeat            — float: updated on every tool call in idle cycle context
  cycle_count                — int: total cycles fired (lifetime)
  cycles_this_window         — int: cycles fired in current idle window
  total_cycles_since_clear   — int: cycles since manual reset; caps at MAX_TOTAL_CYCLES
  cold_start_grace           — bool: one retry per window after connection-refused
  consecutive_maintain_count — int: MAINTAIN cycles in a row (drives cooldown)
  build_cycle_count          — int: BUILD cycles since last EXPLORE
  last_cycle_type            — str: MAINTAIN / BUILD / EXPLORE
"""

import asyncio
import fcntl
import json
import os
import socket
import sys
import time
from datetime import datetime, timezone

from agent import LoopData, UserMessage
from helpers.extension import Extension

_EXOCORTEX_PATH = "/a0/usr/Exocortex"
if _EXOCORTEX_PATH not in sys.path:
    sys.path.insert(0, _EXOCORTEX_PATH)

_CONFIG_PATH  = "/a0/usr/Exocortex/config.json"
_OFFICE_DIR   = "/a0/usr/Exocortex/office"
_STATUS_PATH  = "/a0/usr/Exocortex/office/status.json"
_CONTROL_PATH = "/a0/usr/Exocortex/office/control.json"
_STATE_PATH   = "/a0/usr/Exocortex/office/engine_state.json"
_LOCK_PATH    = "/a0/usr/Exocortex/office/.idle_engine.lock"
_PROMPT_PATH  = "/a0/usr/Exocortex/prompts/idle_activation.md"
_SIGNAL_PATH  = "/a0/usr/Exocortex/office/cycle_result.json"

_ACTIVATION_SENTINEL = "## IDLE-TIME CYCLE ACTIVATED"

_STEP_BUDGETS = {"MAINTAIN": 15, "BUILD": 30, "EXPLORE": 20}

_POLL_INTERVAL = 60  # seconds between idle monitor checks

# Absolute maximum chats before requiring manual reset.
# At one cycle per idle window with 30-min threshold + 60-min cooldown,
# 10 gives ~2 nights of headroom before needing manual reset.
MAX_TOTAL_CYCLES = 10

# ── Process-level singleton ───────────────────────────────────────────────────
_monitor_task: asyncio.Task | None = None


class IdleTrigger(Extension):
    """Activates autonomous work cycles (MAINTAIN/BUILD/EXPLORE) during agent idle time."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            tool_name = kwargs.get("tool_name", "")
            agent = self.agent

            # Never fire in subordinate/child agent contexts
            if agent.get_data(agent.__class__.DATA_NAME_SUPERIOR) is not None:
                return

            config = _load_config()
            if not config.get("enabled", False):
                return

            # ── Bootstrap state file on first-ever tool call ─────────────────
            state = _read_state()
            if not state.get("last_user_ts"):
                state["last_user_ts"]            = time.time()
                state.setdefault("last_cycle_start", 0)
                state.setdefault("cycle_count", 0)
                state.setdefault("cold_start_grace", True)
                state.setdefault("total_cycles_since_clear", 0)
                _write_state(state)
                print("[IDLE] Engine initialized. Idle clock starts now.", flush=True)

            # ── Start singleton monitor if not already running ───────────────
            global _monitor_task
            if _monitor_task is None or _monitor_task.done():
                _monitor_task = asyncio.create_task(_idle_monitor(config))
                print(
                    f"[IDLE] Monitor started "
                    f"(threshold={config.get('idle_threshold_seconds', 1800)}s, "
                    f"max_cycles_per_window={config.get('max_cycles_per_window', 1)}).",
                    flush=True,
                )

            # ── Heartbeat — update on every tool call in idle cycle context ──
            # Prevents stale cycle detection from triggering on live cycles.
            # Only runs for idle contexts (last user message is the sentinel).
            if not _last_user_msg_is_real(agent):
                state = _read_state()
                if state.get("cycle_active", False):
                    state["cycle_heartbeat"] = time.time()
                    _write_state(state)

            # ── Session tracking — only on response tool ─────────────────────
            if tool_name != "response":
                return

            if _last_user_msg_is_real(agent):
                # Real user message — close idle window, reset for next window
                state = _read_state()
                state["last_user_ts"]      = time.time()
                state["cycles_this_window"] = 0
                state["cold_start_grace"]   = True
                _write_state(state)
                _write_status({"state": "idle", "label": "Available"})
            else:
                # Idle cycle completing — clear the active flag
                state = _read_state()
                if state.get("cycle_active", False):
                    state["cycle_active"] = False
                    _write_state(state)
                    print("[IDLE] Cycle complete — cycle_active cleared.", flush=True)
                _write_status({"state": "idle", "label": "Available"})

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[IDLE] Trigger error (passthrough): {e}",
                )
            except Exception:
                pass


# ── Idle Monitor ──────────────────────────────────────────────────────────────

async def _idle_monitor(config: dict) -> None:
    """
    Singleton monitor — one asyncio task per Python process.

    Sleeps _POLL_INTERVAL seconds, does a quick idle threshold check,
    then delegates all guard checks and firing to _atomic_check_and_fire()
    which runs under an exclusive file lock in a thread executor.

    The file lock ensures exactly-once fire semantics regardless of:
    - Multiple uvicorn worker processes
    - Rapid monitor task restarts (task dies and is recreated by execute())
    """
    print("[IDLE] Monitor running (singleton).", flush=True)
    try:
        while True:
            await asyncio.sleep(_POLL_INTERVAL)

            config = _load_config()
            if not config.get("enabled", False):
                continue

            control = _read_control()
            paused_until = control.get("paused_until", 0)
            if paused_until and time.time() < paused_until:
                continue

            # Quick pre-lock check (optimization — re-checked authoritatively inside lock)
            threshold = config.get("idle_threshold_seconds", 1800)
            state = _read_state()
            now = time.time()
            if now - state.get("last_user_ts", now) < threshold:
                continue

            # All guards, state updates, and firing happen under exclusive file lock
            fired = await asyncio.to_thread(_atomic_check_and_fire, config)

            if fired:
                state = _read_state()
                cycle_type  = state.get("last_cycle_type", "")
                cycle_count = state.get("cycle_count", 0)
                print(
                    f"[IDLE] Cycle {cycle_count} ({cycle_type}) fired successfully.",
                    flush=True,
                )
                _write_status({
                    "state": "working",
                    "label": "Working",
                    "cycle_type": cycle_type.lower(),
                    "started": datetime.now(timezone.utc).isoformat(),
                    "priority": "routine",
                })

    except asyncio.CancelledError:
        print("[IDLE] Monitor cancelled.", flush=True)
    except Exception as e:
        print(f"[IDLE] Monitor error: {e}", flush=True)


# ── Atomic Critical Section ───────────────────────────────────────────────────

def _atomic_check_and_fire(config: dict) -> bool:
    """
    Acquire exclusive file lock, check all guards, fire one cycle.

    Runs in a thread executor (via asyncio.to_thread). Returns True if
    a cycle was successfully fired, False otherwise.

    Lock semantics:
    - fcntl.LOCK_EX | LOCK_NB — non-blocking exclusive.
    - If another process or task holds the lock: return False (skip poll).
    - Lock released in finally block: crash-safe, process-death-safe.
    - OS releases lock automatically on process exit (no permanent deadlock).
    """
    os.makedirs(_OFFICE_DIR, exist_ok=True)
    try:
        lock_fd = open(_LOCK_PATH, "w")
    except OSError:
        return False

    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, OSError):
        lock_fd.close()
        return False  # Another process is in the critical section — skip this poll

    try:
        # === CRITICAL SECTION — all reads/writes/fire under lock ===
        state = _read_state()
        now = time.time()

        # Re-check threshold inside lock (user may have returned while we waited)
        threshold = config.get("idle_threshold_seconds", 1800)
        if now - state.get("last_user_ts", now) < threshold:
            return False

        # Guard: active cycle?
        if state.get("cycle_active", False):
            if _is_stale_cycle(state, now):
                print("[IDLE] Stale cycle detected — clearing. Will fire next poll.", flush=True)
                state["cycle_active"] = False
                _write_state(state)
            # Whether stale (just cleared) or live — don't fire this poll
            return False

        # Guard: window cap
        max_cycles = config.get("max_cycles_per_window", 1)
        cycles_this_window = state.get("cycles_this_window", 0)
        if cycles_this_window >= max_cycles:
            return False

        # Guard: blast radius cap
        if state.get("total_cycles_since_clear", 0) >= MAX_TOTAL_CYCLES:
            print(
                f"[IDLE] Total cycle cap ({MAX_TOTAL_CYCLES}) reached — engine halted. "
                "Reset: set total_cycles_since_clear=0 in engine_state.json",
                flush=True,
            )
            return False

        # Guard: min gap between cycles within a window
        if cycles_this_window > 0:
            min_gap = config.get("min_gap_between_cycles_seconds", 1800)
            if now - state.get("last_cycle_start", 0) < min_gap:
                return False

        # Process signal from previous completed cycle
        signal = _read_cycle_signal()
        if signal:
            prev_type = signal.get("cycle_type", "")
            if prev_type == "MAINTAIN":
                if signal.get("sleep_findings", 0) > 0:
                    state["consecutive_maintain_count"] = 0
            elif prev_type == "EXPLORE":
                state["build_cycle_count"] = 0
                state["consecutive_maintain_count"] = 0
            try:
                os.remove(_SIGNAL_PATH)
            except Exception:
                pass

        # Select cycle type and build activation prompt
        cycle_type = _select_cycle_type(state, config)
        max_steps  = _STEP_BUDGETS.get(cycle_type, config.get("max_steps_per_cycle", 20))
        activation = _build_activation_prompt(cycle_type, max_steps)

        # Save pre-increment values for rollback on cold-start grace
        pre_cycle_count     = state.get("cycle_count", 0)
        pre_cycles_window   = cycles_this_window
        pre_total           = state.get("total_cycles_since_clear", 0)
        pre_consec_maintain = state.get("consecutive_maintain_count", 0)
        pre_build_count     = state.get("build_cycle_count", 0)

        print(
            f"[IDLE] Activating {cycle_type} cycle #{pre_cycle_count + 1} "
            f"(idle={now - state.get('last_user_ts', now):.0f}s >= {threshold}s).",
            flush=True,
        )

        # Set lock state BEFORE firing — prevents parallel fires from other polls
        state["cycle_active"]             = True
        state["cycle_heartbeat"]          = now
        state["last_cycle_start"]         = now
        state["cycle_count"]              = pre_cycle_count + 1
        state["last_cycle_type"]          = cycle_type
        state["cycles_this_window"]       = cycles_this_window + 1
        state["total_cycles_since_clear"] = pre_total + 1
        if cycle_type == "MAINTAIN":
            state["consecutive_maintain_count"] = pre_consec_maintain + 1
        elif cycle_type == "BUILD":
            state["build_cycle_count"] = pre_build_count + 1
        _write_state(state)

        # Fire — synchronous TCP in this thread (we're already in thread executor)
        sent = _fire_fresh_cycle(activation)

        if sent:
            return True

        # Fire failed — clear cycle_active
        state["cycle_active"] = False

        if state.get("cold_start_grace", True):
            # One grace retry per window — fully roll back all counters
            print("[IDLE] Cold start grace — will retry once next poll.", flush=True)
            state["cycle_count"]                = pre_cycle_count
            state["cycles_this_window"]         = pre_cycles_window
            state["total_cycles_since_clear"]   = pre_total
            state["consecutive_maintain_count"] = pre_consec_maintain
            state["build_cycle_count"]          = pre_build_count
            state["cold_start_grace"]           = False
        else:
            # Grace already used — attempt counts against the window, no retry
            print("[IDLE] Fire failed — attempt counts against window.", flush=True)

        _write_state(state)
        return False

    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()


# ── Fresh Context Firing ──────────────────────────────────────────────────────

def _fire_fresh_cycle(activation: str) -> bool:
    """
    POST the activation prompt to the A0 REST API without a context_id.
    A0 creates a new context per request when no context_id is supplied.

    Uses raw TCP sockets and never calls recv() or reads a response.
    A0's /api/api_message holds the HTTP connection open while the agent
    processes (cycles take minutes). Any approach that waits for response
    headers will time out and falsely return False.

    Flow:
      1. connect() with 5s timeout — if this fails, A0 is not up → False
      2. sendall() the complete HTTP request
      3. shutdown(SHUT_WR) — signals end of our data
      4. close() — kernel completes FIN handshake in background

    Returns True if the request was delivered (connected=True at time of send).
    Returns False only on pre-connect failures (A0 not reachable).
    """
    connected = False
    try:
        from helpers.settings import create_auth_token
        from helpers.runtime import get_web_ui_port
        token   = create_auth_token()
        port    = get_web_ui_port()
        payload = json.dumps({"message": activation}).encode("utf-8")
        request = (
            f"POST /api/api_message HTTP/1.1\r\n"
            f"Host: localhost:{port}\r\n"
            f"X-API-KEY: {token}\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(payload)}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        ).encode("ascii") + payload

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(("localhost", port))
        connected = True
        sock.settimeout(None)
        sock.sendall(request)
        sock.shutdown(socket.SHUT_WR)
        sock.close()
        return True

    except ConnectionRefusedError:
        print("[IDLE] A0 not reachable (connection refused).", flush=True)
        return False
    except Exception as e:
        if connected:
            # Connected — request was likely delivered even if close() raised
            print(f"[IDLE] Fire warning (request likely delivered): {e}", flush=True)
            return True
        print(f"[IDLE] Fresh context fire failed: {e}", flush=True)
        return False


# ── Stale Cycle Detection ─────────────────────────────────────────────────────

def _is_stale_cycle(state: dict, now: float = None) -> bool:
    """Return True if the active cycle appears to be dead.

    Conditions (either sufficient):
    - No heartbeat update in 20 minutes (cycle crashed or hung)
    - Cycle is older than 60 minutes regardless of heartbeat
    """
    if now is None:
        now = time.time()
    heartbeat = state.get("cycle_heartbeat", 0)
    start     = state.get("last_cycle_start", 0)
    if heartbeat and now - heartbeat > 1200:  # 20 minutes
        return True
    if now - start > 3600:                    # 60 minutes absolute
        return True
    return False


# ── V2 Cycle Selection ────────────────────────────────────────────────────────

def _select_cycle_type(state: dict, config: dict) -> str:
    """V2 adaptive cycle selection based on engine state.

    Decision tree:
      MAINTAIN — while memory system is still productive
      EXPLORE  — when BUILD has run for explore_time_cap_cycles
      BUILD    — otherwise
    """
    maintain_count     = state.get("consecutive_maintain_count", 0)
    build_count        = state.get("build_cycle_count", 0)
    maintain_threshold = config.get("maintain_cooldown_threshold", 3)
    explore_time_cap   = config.get("explore_time_cap_cycles", 5)

    if maintain_count < maintain_threshold:
        return "MAINTAIN"
    elif build_count >= explore_time_cap:
        return "EXPLORE"
    else:
        return "BUILD"


def _read_cycle_signal() -> dict:
    """Read cycle_result.json written by cycle_close.py at cycle end."""
    try:
        if os.path.exists(_SIGNAL_PATH):
            with open(_SIGNAL_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _last_user_msg_is_real(agent) -> bool:
    """
    Walk history backwards to find the most recent user message (ai=False).
    Return True if it's a real user message (not an idle activation).
    """
    try:
        for msg in reversed(agent.history.output()):
            if msg.get("ai", True):
                continue
            content = msg.get("content", "")
            if isinstance(content, dict):
                content = content.get("text", "") or str(content)
            return not str(content).startswith(_ACTIVATION_SENTINEL)
    except Exception:
        pass
    return False


def _build_activation_prompt(cycle_type: str, max_steps: int) -> str:
    """Load and format the idle activation prompt template from disk."""
    try:
        if os.path.exists(_PROMPT_PATH):
            with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
                template = f.read()
            return (template
                    .replace("{cycle_type}", cycle_type)
                    .replace("{max_steps}", str(max_steps)))
    except Exception:
        pass
    return (
        f"{_ACTIVATION_SENTINEL}\n\n"
        f"Cycle type: {cycle_type}\n"
        f"Step budget: {max_steps} steps maximum.\n\n"
        f"Read /a0/usr/Exocortex/self-improvement/program.md for operating rules.\n"
        f"Log everything to /a0/usr/workdir/self-improvement/journal.jsonl.\n"
        f"At cycle end write to /a0/usr/Exocortex/office/feed.jsonl.\n\n"
        f"Begin."
    )


def _read_state() -> dict:
    try:
        if os.path.exists(_STATE_PATH):
            with open(_STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _write_state(state: dict) -> None:
    try:
        os.makedirs(_OFFICE_DIR, exist_ok=True)
        tmp = _STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f)
        os.replace(tmp, _STATE_PATH)
    except Exception:
        pass


def _write_status(status: dict) -> None:
    try:
        os.makedirs(_OFFICE_DIR, exist_ok=True)
        tmp = _STATUS_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(status, f)
        os.replace(tmp, _STATUS_PATH)
    except Exception:
        pass


def _read_control() -> dict:
    try:
        if os.path.exists(_CONTROL_PATH):
            with open(_CONTROL_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _load_config() -> dict:
    try:
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r", encoding="utf-8-sig") as f:
                return json.load(f).get("idle_time_engine", {})
    except Exception:
        pass
    return {}
