"""
Idle Time Engine — Trigger
==========================
Hook: tool_execute_after (_70_)

When the agent has been idle (no real user messages) for idle_threshold_seconds,
activates one autonomous work cycle (Workshop or Field mode) per idle window by
posting the idle activation prompt to the A0 REST API without a context_id — A0
creates a fresh context for each cycle, resetting the 80-step hard limit.

Workshop mode (3 of every 4 cycles by default): self-improvement per program.md
Field mode   (1 of every 4 cycles):             interest research per interests.md

Cycle sequencing — EDGE-TRIGGERED, NOT LEVEL-TRIGGERED:
  An idle window opens when the user goes absent. Within one idle window, at most
  max_cycles_per_window cycles fire (default: 1). The window resets only when the
  user sends a real message. Being absent for 8 hours fires ONE cycle, not 16.

  Preventing parallel execution (interlock): cycle_active flag.
  Preventing serial accumulation (window cap): cycles_this_window counter.
  Both are required. Neither alone is sufficient.

Architecture:
  - Singleton monitor: one asyncio task per process, regardless of how many agent
    contexts are active. Module-level _monitor_task guards this.
  - File-based state: engine_state.json persists all counters across context changes.
  - execute() still runs per-context to detect real user session endings.

Pause control: /a0/usr/Exocortex/office/control.json → {"paused_until": <float ts>}
  Written by the /api/idle_control endpoint.

Config: /a0/usr/Exocortex/config.json → "idle_time_engine" section
  enabled: true
  idle_threshold_seconds: 1800      # 30 min — time since last real user session
  max_cycles_per_window: 1          # cycles per idle window (default 1)
  min_gap_between_cycles_seconds: 1800  # min wait between cycles if window > 1
  max_steps_per_cycle: 20
  workshop_field_ratio: "3:1"
  max_cycle_duration_seconds: 7200  # 2 hr — stale cycle_active safety timeout

Fire condition (logical AND):
  1. User has NOT sent a message in the last idle_threshold_seconds
  2. A cycle IS NOT currently running (cycle_active interlock)
  3. cycles_this_window < max_cycles_per_window (window cap)
  4. If cycles_this_window > 0: time since last_cycle_start >= min_gap_between_cycles_seconds

State file: /a0/usr/Exocortex/office/engine_state.json
  last_user_ts           — float: unix timestamp of last real user session end
  last_cycle_start       — float: unix timestamp of last cycle fire
  cycle_count            — int: total cycles fired (drives workshop/field ratio)
  cycle_active           — bool: True while a cycle is running; prevents parallel fires
  cycles_this_window     — int: cycles fired in the current idle window; resets on user return
"""

import asyncio
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

_CONFIG_PATH    = "/a0/usr/Exocortex/config.json"
_OFFICE_DIR     = "/a0/usr/Exocortex/office"
_STATUS_PATH    = "/a0/usr/Exocortex/office/status.json"
_CONTROL_PATH   = "/a0/usr/Exocortex/office/control.json"
_STATE_PATH     = "/a0/usr/Exocortex/office/engine_state.json"
_PROMPT_PATH    = "/a0/usr/Exocortex/prompts/idle_activation.md"
_SIGNAL_PATH    = "/a0/usr/Exocortex/office/cycle_result.json"

# Prefix injected at the start of every idle activation prompt.
_ACTIVATION_SENTINEL = "## IDLE-TIME CYCLE ACTIVATED"

# V2: per-cycle-type step budgets.
# MAINTAIN is short (15) — integrity check + sleep consolidation.
# BUILD gets more room (30) — source code reading and wiki deepening need it.
# EXPLORE is focused (20) — field research sprint, not an open-ended wander.
_STEP_BUDGETS = {"MAINTAIN": 15, "BUILD": 30, "EXPLORE": 20}

_POLL_INTERVAL = 60  # seconds between idle monitor checks

# ── Process-level singleton ───────────────────────────────────────────────────
# Only one monitor task runs per Python process regardless of how many agent
# contexts are active. Keyed to None when not running.
_monitor_task: asyncio.Task | None = None


class IdleTrigger(Extension):
    """Activates autonomous work cycles (Workshop or Field) during agent idle time."""

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
                state["last_user_ts"] = time.time()
                state.setdefault("last_cycle_start", 0)
                state.setdefault("cycle_count", 0)
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

            # ── Track user session end on response tool ──────────────────────
            if tool_name != "response":
                return

            if _last_user_msg_is_real(agent):
                # Real user message — close the idle window and reset the cycle counter.
                state = _read_state()
                state["last_user_ts"] = time.time()
                state["cycles_this_window"] = 0
                _write_state(state)
                _write_status({"state": "idle", "label": "Available"})
            else:
                # Idle cycle completing — clear the active flag so the monitor
                # knows the slot is free. cycles_this_window is NOT reset here;
                # it stays at its current value until the user actually returns.
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
    Singleton monitor — one instance per Python process.

    Fires one cycle at a time into a fresh A0 context via REST API.
    Reads/writes engine_state.json for persistence across context changes.

    Fire condition (AND gate / interlock):
      (1) No real user message in the last idle_threshold_seconds
      (2) cycle_active is False — no cycle currently running

    Cycles queue in series automatically: when a cycle completes and clears
    cycle_active, the next poll fires the next cycle if the user is still absent.
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

            threshold = config.get("idle_threshold_seconds", 1800)

            state = _read_state()
            now       = time.time()
            last_user = state.get("last_user_ts", now)

            # ── Condition 1: user has been idle long enough ──────────────────
            if now - last_user < threshold:
                continue

            # ── Condition 2 (interlock): no cycle currently running ──────────
            if state.get("cycle_active", False):
                max_dur = config.get("max_cycle_duration_seconds", 7200)
                if now - state.get("last_cycle_start", 0) < max_dur:
                    continue  # Previous cycle still within expected duration
                # Safety valve: cycle has been marked active longer than max_dur —
                # it likely crashed without completing. Clear stale flag.
                print(
                    f"[IDLE] Stale cycle_active detected "
                    f"(active for {now - state.get('last_cycle_start', 0):.0f}s > {max_dur}s) "
                    f"— clearing and allowing next cycle.",
                    flush=True,
                )
                state["cycle_active"] = False
                _write_state(state)

            # ── Condition 3 (window cap): haven't exceeded cycles allowed per absence ──
            max_cycles = config.get("max_cycles_per_window", 1)
            cycles_this_window = state.get("cycles_this_window", 0)
            if cycles_this_window >= max_cycles:
                # Already fired the allowed number of cycles during this idle window.
                # Do not fire again until the user returns and starts a new window.
                continue

            # ── Condition 4 (min gap): if multi-cycle window, space them out ─────────
            if cycles_this_window > 0:
                min_gap = config.get("min_gap_between_cycles_seconds", 1800)
                if now - state.get("last_cycle_start", 0) < min_gap:
                    continue

            # ── Process signal from the previous completed cycle ──────────
            # cycle_result.json is written by cycle_close.py at cycle end.
            # Reading it here (before selecting the next type) lets productive
            # MAINTAIN cycles reset the consecutive-empty counter.
            signal = _read_cycle_signal()
            if signal:
                prev_type = signal.get("cycle_type", "")
                if prev_type == "MAINTAIN":
                    if signal.get("sleep_findings", 0) > 0:
                        # Productive MAINTAIN — reset empty counter
                        state["consecutive_maintain_count"] = 0
                    # else: counter was already incremented when we fired MAINTAIN
                elif prev_type == "EXPLORE":
                    state["build_cycle_count"] = 0
                    state["consecutive_maintain_count"] = 0
                try:
                    os.remove(_SIGNAL_PATH)
                except Exception:
                    pass
                _write_state(state)
                state = _read_state()

            # ── Fire one cycle into a fresh context ──────────────────────────
            cycle_count = state.get("cycle_count", 0)
            cycle_type  = _select_cycle_type(state, config)
            max_steps   = _STEP_BUDGETS.get(cycle_type, config.get("max_steps_per_cycle", 20))

            print(
                f"[IDLE] Activating {cycle_type} cycle #{cycle_count + 1} "
                f"in fresh context (idle={now - last_user:.0f}s >= {threshold}s).",
                flush=True,
            )

            activation = _build_activation_prompt(cycle_type, max_steps)

            # Lock the slot BEFORE firing. A0's /api/api_message holds the HTTP
            # connection open while the agent processes (cycles take minutes).
            # Setting cycle_active after the call means the monitor may poll again
            # before the call returns, see cycle_active=False, and fire a second
            # cycle. Locking first prevents that race.
            state["last_cycle_start"] = time.time()
            state["cycle_count"] = cycle_count + 1
            state["cycle_active"] = True
            state["last_cycle_type"] = cycle_type
            state["cycles_this_window"] = cycles_this_window + 1
            # Update V2 counters for the cycle type we're about to fire
            if cycle_type == "MAINTAIN":
                state["consecutive_maintain_count"] = state.get("consecutive_maintain_count", 0) + 1
            elif cycle_type == "BUILD":
                state["build_cycle_count"] = state.get("build_cycle_count", 0) + 1
            # EXPLORE resets both — handled after signal processing above
            _write_state(state)

            sent = await asyncio.to_thread(_fire_fresh_cycle, activation)

            if sent:
                _write_status({
                    "state": "working",
                    "label": "Working",
                    "cycle_type": cycle_type.lower(),
                    "started": datetime.now(timezone.utc).isoformat(),
                    "priority": "routine",
                })
                print(
                    f"[IDLE] Cycle {cycle_count + 1} ({cycle_type}) fired successfully.",
                    flush=True,
                )
            else:
                # Connection refused — server not up. Back out the lock so we retry.
                state = _read_state()
                state["cycle_active"] = False
                state["cycle_count"] = max(0, state.get("cycle_count", 1) - 1)
                state["cycles_this_window"] = max(0, state.get("cycles_this_window", 1) - 1)
                _write_state(state)
                print(
                    f"[IDLE] Cycle {cycle_count + 1} failed to start — lock released, will retry next poll.",
                    flush=True,
                )

    except asyncio.CancelledError:
        print("[IDLE] Monitor cancelled.", flush=True)
    except Exception as e:
        print(f"[IDLE] Monitor error: {e}", flush=True)


# ── Fresh Context Firing ──────────────────────────────────────────────────────

def _fire_fresh_cycle(activation: str) -> bool:
    """
    POST the activation prompt to the A0 REST API without a context_id.
    A0 creates a new context per request when no context_id is supplied,
    giving each idle cycle a clean 80-step budget.

    Uses raw TCP sockets and never calls recv() or reads a response.
    A0's /api/api_message holds the HTTP connection open while the agent
    processes (cycles take minutes). Any approach that waits for response
    headers (urllib, http.client.getresponse) will time out and falsely
    return False — causing the lock to be backed out and re-fires every poll.

    Flow:
      1. connect() with a short timeout — if this fails, A0 is not up → False
      2. sendall() the complete HTTP request into the kernel send buffer
      3. shutdown(SHUT_WR) — signals end of our data; OS sends FIN after the buffer
      4. close() — releases the fd; kernel completes FIN handshake in background

    The server receives the full request, processes it, and sends a response
    into the void. We never see it. cycle_active stays True until the agent
    calls the response tool, at which point the extension clears it normally.

    Runs in a thread executor (via asyncio.to_thread) to avoid blocking
    the event loop with the synchronous connect/send.
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
        sock.settimeout(5)          # connect-only timeout — server must be reachable
        sock.connect(("localhost", port))
        connected = True            # past connect() → server is up
        sock.settimeout(None)       # no timeout for send (local loopback — instant)
        sock.sendall(request)
        sock.shutdown(socket.SHUT_WR)   # tells OS: send FIN after buffered data
        sock.close()                    # fd released; kernel completes gracefully
        return True

    except ConnectionRefusedError:
        print("[IDLE] A0 not reachable (connection refused).", flush=True)
        return False
    except Exception as e:
        if connected:
            # We connected — request was likely delivered even if close() raised.
            # Keep the lock; don't risk a duplicate cycle.
            print(f"[IDLE] Fire warning (request likely delivered): {e}", flush=True)
            return True
        print(f"[IDLE] Fresh context fire failed: {e}", flush=True)
        return False


# ── Helpers ───────────────────────────────────────────────────────────────────

def _select_cycle_type(state: dict, config: dict) -> str:
    """V2 adaptive cycle selection based on engine state.

    Decision tree:
      MAINTAIN — while memory system is still productive (< maintain_cooldown_threshold
                 consecutive empty MAINTAIN cycles)
      EXPLORE  — when BUILD has been running for explore_time_cap_cycles cycles
                 (time cap, OR logic with content saturation)
      BUILD    — otherwise (draft wiki pages to deepen)

    consecutive_maintain_count is incremented each time MAINTAIN fires and reset to 0
    when: (a) a productive MAINTAIN cycle writes sleep_findings > 0 to cycle_result.json,
    or (b) EXPLORE fires. build_cycle_count is incremented on BUILD and reset on EXPLORE.
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
    """Read cycle_result.json written by cycle_close.py at cycle end. Returns {} if absent."""
    try:
        if os.path.exists(_SIGNAL_PATH):
            with open(_SIGNAL_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _last_user_msg_is_real(agent) -> bool:
    """
    Walk history output() backwards to find the most recent user message (ai=False).
    Return True if it's a real user message, False if it's our idle activation.
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
        f"Read /a0/usr/Exocortex/interests.md for field-mode directives.\n"
        f"Log everything to /a0/usr/workdir/self-improvement/journal.jsonl.\n"
        f"At cycle end write to /a0/usr/Exocortex/office/feed.jsonl.\n\n"
        f"Begin."
    )


def _read_state() -> dict:
    """Read engine state from file. Returns {} on any error."""
    try:
        if os.path.exists(_STATE_PATH):
            with open(_STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _write_state(state: dict) -> None:
    """Atomically write engine state to file."""
    try:
        os.makedirs(_OFFICE_DIR, exist_ok=True)
        tmp = _STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f)
        os.replace(tmp, _STATE_PATH)
    except Exception:
        pass


def _write_status(status: dict) -> None:
    """Atomically write current engine state to office/status.json."""
    try:
        os.makedirs(_OFFICE_DIR, exist_ok=True)
        tmp = _STATUS_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(status, f)
        os.replace(tmp, _STATUS_PATH)
    except Exception:
        pass


def _read_control() -> dict:
    """Read control.json for pause state. Returns {} on any error."""
    try:
        if os.path.exists(_CONTROL_PATH):
            with open(_CONTROL_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _load_config() -> dict:
    """Load idle engine config section from config.json. Returns {} on any error."""
    try:
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r", encoding="utf-8-sig") as f:
                return json.load(f).get("idle_time_engine", {})
    except Exception:
        pass
    return {}
