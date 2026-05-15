#!/usr/bin/env python3
"""
Idle Watch Daemon
=================
Managed by supervisord. Starts on container boot, independent of A0's event loop.

Responsibilities (sole owner of the firing decision):
  - Poll engine_state.json every 60 seconds for last_user_ts
  - When idle threshold exceeded: acquire file lock, run all guards, fire one cycle
  - Stale cycle detection: clear hung cycles so the next poll can fire

What this is NOT responsible for (owned by _70_idle_trigger.py extension):
  - Writing last_user_ts when real users make tool calls
  - Writing cycle_heartbeat during running cycles
  - Clearing cycle_active when cycles complete normally

Shared state: /a0/usr/Exocortex/office/engine_state.json
Coordination: /a0/usr/Exocortex/office/.idle_engine.lock (fcntl.flock)

Start: supervisord [program:idle_watch] in /etc/supervisor/conf.d/supervisord.conf
Logs:  docker logs exocortex_v16 | grep IDLE-WATCH
"""

import fcntl
import json
import os
import socket
import sys
import time
from datetime import datetime, timezone

# A0's helpers live here — provides create_auth_token, get_web_ui_port
sys.path.insert(0, "/a0")

_CONFIG_PATH  = "/a0/usr/Exocortex/config.json"
_OFFICE_DIR   = "/a0/usr/Exocortex/office"
_STATUS_PATH  = "/a0/usr/Exocortex/office/status.json"
_CONTROL_PATH = "/a0/usr/Exocortex/office/control.json"
_STATE_PATH   = "/a0/usr/Exocortex/office/engine_state.json"
_LOCK_PATH    = "/a0/usr/Exocortex/office/.idle_engine.lock"
_PROMPT_PATH  = "/a0/usr/Exocortex/prompts/idle_activation.md"
_SIGNAL_PATH  = "/a0/usr/Exocortex/office/cycle_result.json"

_ACTIVATION_SENTINEL = "## IDLE-TIME CYCLE ACTIVATED"
_STEP_BUDGETS        = {"MAINTAIN": 15, "BUILD": 30, "EXPLORE": 20}
_POLL_INTERVAL       = 60   # seconds between polls
_STARTUP_GRACE       = 30   # seconds to wait on boot before first poll (A0 startup time)
MAX_TOTAL_CYCLES     = 50   # absolute cap — requires manual reset to clear (~3 nights at 16 cycles/night)


def main() -> None:
    print("[IDLE-WATCH] Daemon started.", flush=True)
    time.sleep(_STARTUP_GRACE)
    print("[IDLE-WATCH] Starting poll loop.", flush=True)
    while True:
        try:
            _poll_once()
        except Exception as e:
            print(f"[IDLE-WATCH] Poll error: {e}", flush=True)
        time.sleep(_POLL_INTERVAL)


def _poll_once() -> None:
    config = _load_config()
    if not config.get("enabled", False):
        return

    control      = _read_control()
    paused_until = control.get("paused_until", 0)
    if paused_until and time.time() < paused_until:
        return

    # Quick pre-lock check (optimization — re-checked authoritatively inside lock)
    state     = _read_state()
    now       = time.time()
    threshold = config.get("idle_threshold_seconds", 1800)
    if now - state.get("last_user_ts", now) < threshold:
        return

    fired = _atomic_check_and_fire(config)
    if fired:
        state       = _read_state()
        cycle_type  = state.get("last_cycle_type", "")
        cycle_count = state.get("cycle_count", 0)
        print(f"[IDLE-WATCH] Cycle {cycle_count} ({cycle_type}) fired.", flush=True)
        _write_status({
            "state":      "working",
            "label":      "Working",
            "cycle_type": cycle_type.lower(),
            "started":    datetime.now(timezone.utc).isoformat(),
            "priority":   "routine",
        })


def _atomic_check_and_fire(config: dict) -> bool:
    """
    Acquire exclusive file lock, run all guards, fire one cycle if conditions met.

    Lock semantics:
    - LOCK_EX | LOCK_NB — non-blocking exclusive.
    - If another holder exists: return False (skip this poll).
    - Lock released in finally: crash-safe, OS releases on process death.
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
        return False

    try:
        # === CRITICAL SECTION ===
        state = _read_state()
        now   = time.time()

        # Re-check threshold inside lock (user may have returned since pre-lock check)
        threshold = config.get("idle_threshold_seconds", 1800)
        if now - state.get("last_user_ts", now) < threshold:
            return False

        # Guard: active cycle?
        if state.get("cycle_active", False):
            if _is_stale_cycle(state, now):
                print("[IDLE-WATCH] Stale cycle detected — clearing. Will fire next poll.", flush=True)
                state["cycle_active"] = False
                _write_state(state)
            return False

        # Guard: blast radius cap
        max_total = config.get("max_total_cycles", MAX_TOTAL_CYCLES)
        if state.get("total_cycles_since_clear", 0) >= max_total:
            print(
                f"[IDLE-WATCH] Total cycle cap ({max_total}) reached — engine halted. "
                "Reset: set total_cycles_since_clear=0 in engine_state.json",
                flush=True,
            )
            return False

        # Guard: min gap between fires (replaces window-based cap)
        # Allows continuous cycling during long absences — one cycle per gap interval.
        if state.get("last_cycle_start", 0) > 0:
            min_gap = config.get("min_gap_between_cycles_seconds", 1800)
            if now - state.get("last_cycle_start", 0) < min_gap:
                return False

        # Process completion signal from previous cycle (written by cycle_close.py)
        signal = _read_cycle_signal()
        if signal:
            prev_type = signal.get("cycle_type", "")
            if prev_type == "MAINTAIN" and signal.get("sleep_findings", 0) > 0:
                state["consecutive_maintain_count"] = 0
            elif prev_type == "EXPLORE":
                state["build_cycle_count"]          = 0
                state["consecutive_maintain_count"] = 0
            try:
                os.remove(_SIGNAL_PATH)
            except Exception:
                pass

        cycle_type = _select_cycle_type(state, config)
        max_steps  = _STEP_BUDGETS.get(cycle_type, config.get("max_steps_per_cycle", 20))
        activation = _build_activation_prompt(cycle_type, max_steps)

        # Save pre-increment values for cold-start grace rollback
        pre_cycle_count     = state.get("cycle_count", 0)
        pre_total           = state.get("total_cycles_since_clear", 0)
        pre_consec_maintain = state.get("consecutive_maintain_count", 0)
        pre_build_count     = state.get("build_cycle_count", 0)

        print(
            f"[IDLE-WATCH] Activating {cycle_type} cycle #{pre_cycle_count + 1} "
            f"(idle={now - state.get('last_user_ts', now):.0f}s >= {threshold}s).",
            flush=True,
        )

        # Set cycle_active BEFORE firing — prevents parallel fires from other polls
        state["cycle_active"]             = True
        state["cycle_heartbeat"]          = now
        state["last_cycle_start"]         = now
        state["cycle_count"]              = pre_cycle_count + 1
        state["last_cycle_type"]          = cycle_type
        state["total_cycles_since_clear"] = pre_total + 1
        if cycle_type == "MAINTAIN":
            state["consecutive_maintain_count"] = pre_consec_maintain + 1
        elif cycle_type == "BUILD":
            state["build_cycle_count"] = pre_build_count + 1
        _write_state(state)

        sent = _fire_fresh_cycle(activation)
        if sent:
            return True

        # Fire failed — clear cycle_active
        state["cycle_active"] = False
        if state.get("cold_start_grace", True):
            # One grace retry per window — roll back all counters so next poll retries
            print("[IDLE-WATCH] Cold start grace — will retry once next poll.", flush=True)
            state["cycle_count"]                = pre_cycle_count
            state["total_cycles_since_clear"]   = pre_total
            state["consecutive_maintain_count"] = pre_consec_maintain
            state["build_cycle_count"]          = pre_build_count
            state["cold_start_grace"]           = False
        else:
            print("[IDLE-WATCH] Fire failed — attempt counts against total cap.", flush=True)
        _write_state(state)
        return False

    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()


_A0_PORT = 80  # A0 always starts with --port=80 inside the container (run_A0.sh → self_update_manager.py)


def _fire_fresh_cycle(activation: str) -> bool:
    """
    POST activation prompt to A0's REST API without a context_id.
    A0 creates a new context per request when no context_id is supplied.

    Uses raw TCP. After sending the request we peek at the status line with a
    short timeout:
    - No data / timeout: A0 is processing (expected — cycles take minutes).
    - 4xx response: A0 rejected the request — treat as failure so cold-start
      grace can roll back counters and retry next poll.
    - Connection refused: A0 not up yet.
    """
    connected = False
    try:
        from helpers.settings import create_auth_token
        token   = create_auth_token()
        port    = _A0_PORT
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

        # Peek at the HTTP status line. A0 holds the connection while it processes,
        # so normally we get nothing (timeout) — that means success. If A0 returns
        # a 4xx quickly it rejected the request.
        sock.settimeout(2)
        try:
            peek = sock.recv(32)
            if peek:
                status_line = peek.decode("ascii", errors="replace")
                # e.g. "HTTP/1.1 400 Bad Request"
                parts = status_line.split()
                if len(parts) >= 2 and parts[1].startswith("4"):
                    print(
                        f"[IDLE-WATCH] Fire rejected by A0 ({parts[1]}) — will retry.",
                        flush=True,
                    )
                    sock.close()
                    return False
        except (socket.timeout, OSError):
            pass  # timeout = A0 is processing (good)

        sock.close()
        return True

    except ConnectionRefusedError:
        print("[IDLE-WATCH] A0 not reachable (connection refused).", flush=True)
        return False
    except Exception as e:
        if connected:
            print(f"[IDLE-WATCH] Fire warning (request likely delivered): {e}", flush=True)
            return True
        print(f"[IDLE-WATCH] Fire failed: {e}", flush=True)
        return False


def _is_stale_cycle(state: dict, now: float) -> bool:
    heartbeat = state.get("cycle_heartbeat", 0)
    start     = state.get("last_cycle_start", 0)
    if heartbeat and now - heartbeat > 1200:  # 20 minutes no heartbeat
        return True
    if now - start > 3600:                    # 60 minutes absolute cap
        return True
    return False


def _select_cycle_type(state: dict, config: dict) -> str:
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
    try:
        if os.path.exists(_SIGNAL_PATH):
            with open(_SIGNAL_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _build_activation_prompt(cycle_type: str, max_steps: int) -> str:
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


if __name__ == "__main__":
    main()
