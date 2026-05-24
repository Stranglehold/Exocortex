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
import http.client
import json
import os
import socket
import sys
import threading
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
MAX_TOTAL_CYCLES     = 100000   # effectively unlimited — Jake explicit on 2026-05-16 ("no cap or limit"). Counter still tracks for observability; cap is just very far away.

# ── Cache Warmer (v2.1 — Opus spec + measured corrections, 2026-05-18) ────────
# Principle: don't replicate A0's prompt — send a trivial request THROUGH A0 so
# A0 builds its real ~12K prefix and llama-server caches it. Two triggers:
#   T1 server-restart warm, T2 periodic idle keepalive.
# No cold detection (the Indras fork's /slots exposes no n_past). Gated by the
# same flock + is_processing as cycle fires so a warm-up can never overlap a
# real cycle (the overlap-OOM the heartbeat saga fixed). Config-gated, default
# OFF. Runs independent of idle_time_engine.enabled. Ratified spec:
# team-comms/kestrel-to-opus/cache_warmer_v2.1_corrected_20260518.md
_LLAMA_HOST          = "host.docker.internal"  # llama-server is on the host, not localhost
_LLAMA_PORT          = 1235
_WARM_REGISTER_GRACE = 30   # s — covers request-accepted → prefill-registers gap; is_processing carries the rest

_server_was_down       = True   # assume cold on daemon start → first /health-ok warms
_last_keepalive        = 0.0
_warmup_inflight_until = 0.0    # real cycles defer until now passes this (belt; _llama_busy is the primary guard)


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

    # Cache warmer runs independent of the idle CYCLE engine being enabled —
    # it only needs the daemon up + llama-server up. Default OFF via config.
    try:
        _cache_warmer_tick(config)
    except Exception as e:
        print(f"[CACHE-WARM] tick error: {e}", flush=True)

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

        # Guard: cache-warmer in flight / server busy (only when warmer enabled).
        # A warm-up is a throwaway A0 context that does NOT set cycle_active;
        # without this a real cycle could fire on top of a 5-8 min warm prefill
        # → the overlap OOM the heartbeat fix addressed. _llama_busy() is the
        # primary guard (is_processing spans the whole warm); the short grace
        # covers the request-accepted → prefill-registers gap. Inert when off.
        if config.get("cache_warmer_enabled", False):
            if now < _warmup_inflight_until or _llama_busy():
                print("[IDLE-WATCH] Deferring fire — cache warm-up in flight / server busy.", flush=True)
                return False

        # Guard: active cycle?
        if state.get("cycle_active", False):
            if _is_stale_cycle(state, now):
                print("[IDLE-WATCH] Stale cycle detected — clearing. Will fire next poll.", flush=True)
                state["cycle_active"]             = False
                state["total_cycles_since_clear"] = state.get("total_cycles_since_clear", 0) + 1
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
        # Per-container override: config.json "step_budgets" merges over the
        # hardcoded defaults so v17 can tune budgets (cost) without diverging
        # v16's deployed code. Absent config key -> defaults (v16 unchanged).
        budgets    = {**_STEP_BUDGETS, **(config.get("step_budgets") or {})}
        max_steps  = budgets.get(cycle_type, config.get("max_steps_per_cycle", 20))
        activation = _build_activation_prompt(cycle_type, max_steps)

        # Save pre-increment values for cold-start grace rollback
        pre_cycle_count     = state.get("cycle_count", 0)
        pre_consec_maintain = state.get("consecutive_maintain_count", 0)
        pre_build_count     = state.get("build_cycle_count", 0)

        print(
            f"[IDLE-WATCH] Activating {cycle_type} cycle #{pre_cycle_count + 1} "
            f"(idle={now - state.get('last_user_ts', now):.0f}s >= {threshold}s).",
            flush=True,
        )

        # Set cycle_active BEFORE firing — prevents parallel fires from other polls.
        # total_cycles_since_clear is NOT incremented here — only on completion (sensor)
        # or stale detection (above). A running cycle occupies the slot but consumes
        # no budget unit until it finishes.
        state["cycle_active"]    = True
        state["cycle_heartbeat"] = now
        state["last_cycle_start"] = now
        state["cycle_count"]     = pre_cycle_count + 1
        state["last_cycle_type"] = cycle_type
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
            # One grace retry per window — roll back type-selection counters
            print("[IDLE-WATCH] Cold start grace — will retry once next poll.", flush=True)
            state["cycle_count"]                = pre_cycle_count
            state["consecutive_maintain_count"] = pre_consec_maintain
            state["build_cycle_count"]          = pre_build_count
            state["cold_start_grace"]           = False
        else:
            print("[IDLE-WATCH] Fire failed — skipped, no budget consumed.", flush=True)
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

    Uses http.client in a daemon thread so the connection stays open while A0
    processes (cycles take minutes). Raw-socket close caused Uvicorn to discard
    requests; keeping the connection alive ensures delivery.

    The thread waits up to 3 seconds for a quick rejection (4xx). If no response
    arrives in that window, A0 is processing — return True.
    """
    try:
        from helpers.settings import create_auth_token
        token   = create_auth_token()
        port    = _A0_PORT
        payload = json.dumps({"message": activation}).encode("utf-8")
        headers = {
            "X-API-KEY":    token,
            "Content-Type": "application/json",
        }

        # Quick synchronous check — is A0 listening?
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.settimeout(5)
        try:
            probe.connect(("localhost", port))
            probe.close()
        except ConnectionRefusedError:
            print("[IDLE-WATCH] A0 not reachable (connection refused).", flush=True)
            return False

        rejected = threading.Event()

        def _send() -> None:
            try:
                conn = http.client.HTTPConnection("localhost", port, timeout=3600)
                conn.request("POST", "/api/api_message", body=payload, headers=headers)
                resp = conn.getresponse()
                if resp.status >= 400:
                    rejected.set()
                conn.close()
            except Exception:
                pass

        t = threading.Thread(target=_send, daemon=True)
        t.start()
        t.join(timeout=3)  # wait briefly for quick rejection; timeout = A0 is processing

        if rejected.is_set():
            print("[IDLE-WATCH] Fire rejected by A0 — will retry next poll.", flush=True)
            return False
        return True

    except ConnectionRefusedError:
        print("[IDLE-WATCH] A0 not reachable (connection refused).", flush=True)
        return False
    except Exception as e:
        print(f"[IDLE-WATCH] Fire failed: {e}", flush=True)
        return False


# ── Cache Warmer functions ───────────────────────────────────────────────────

def _llama_health() -> bool:
    """True iff llama-server answers /health 200 with status ok."""
    try:
        conn = http.client.HTTPConnection(_LLAMA_HOST, _LLAMA_PORT, timeout=4)
        conn.request("GET", "/health")
        resp = conn.getresponse()
        ok   = resp.status == 200
        body = resp.read(64) if ok else b""
        conn.close()
        return ok and b"ok" in body.lower()
    except Exception:
        return False


def _llama_busy() -> bool:
    """True if any slot is generating. Fail-safe: any error → True (can't
    tell → assume busy → don't stack a warm/cycle on top)."""
    try:
        conn = http.client.HTTPConnection(_LLAMA_HOST, _LLAMA_PORT, timeout=5)
        conn.request("GET", "/slots")
        resp = conn.getresponse()
        if resp.status != 200:
            conn.close()
            return True
        slots = json.loads(resp.read())
        conn.close()
        return any(s.get("is_processing", False) for s in slots)
    except Exception:
        return True


def _send_warmup(reason: str) -> bool:
    """Send a trivial message through A0's real API — same mechanism as
    _fire_fresh_cycle (http.client, port 80, create_auth_token, daemon-thread
    fire-and-forget). A0 builds its real ~12K prefix; llama-server caches it.
    Returns True if delivered (not rejected within 3s)."""
    try:
        from helpers.settings import create_auth_token
        token   = create_auth_token()
        port    = _A0_PORT
        payload = json.dumps(
            {"message": "[CACHE-WARM] Respond with the single word OK."}
        ).encode("utf-8")
        headers = {"X-API-KEY": token, "Content-Type": "application/json"}

        # Is A0 listening? (mirror _fire_fresh_cycle's probe)
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.settimeout(5)
        try:
            probe.connect(("localhost", port))
            probe.close()
        except ConnectionRefusedError:
            print("[CACHE-WARM] A0 not reachable (connection refused).", flush=True)
            return False

        rejected = threading.Event()

        def _send() -> None:
            try:
                conn = http.client.HTTPConnection("localhost", port, timeout=3600)
                conn.request("POST", "/api/api_message", body=payload, headers=headers)
                resp = conn.getresponse()
                if resp.status >= 400:
                    rejected.set()
                conn.close()
            except Exception:
                pass

        t = threading.Thread(target=_send, daemon=True)
        t.start()
        t.join(timeout=3)  # brief wait for quick 4xx; timeout = A0 is processing

        if rejected.is_set():
            print(f"[CACHE-WARM] Warm-up ({reason}) rejected by A0 — retry next poll.", flush=True)
            return False
        print(f"[CACHE-WARM] Warm-up sent ({reason}).", flush=True)
        return True

    except Exception as e:
        print(f"[CACHE-WARM] Warm-up failed ({reason}): {e}", flush=True)
        return False


def _cache_warmer_tick(config: dict) -> None:
    """T1 server-restart warm + T2 periodic idle keepalive. Gated by the same
    flock + is_processing as cycle fires (a warm-up is a do-nothing cycle the
    safety system must respect). Default OFF; independent of engine.enabled."""
    global _server_was_down, _last_keepalive, _warmup_inflight_until

    if not config.get("cache_warmer_enabled", False):
        return

    if not _llama_health():
        _server_was_down = True
        return

    server_restarted = _server_was_down
    _server_was_down  = False  # up is up — the down→up edge is consumed once

    now            = time.time()
    keepalive_int  = config.get("cache_keepalive_interval_seconds", 600)
    warm_timeout   = config.get("cache_warm_timeout_seconds", 900)
    idle_threshold = config.get("idle_threshold_seconds", 1800)

    state     = _read_state()
    last_user = state.get("last_user_ts", now)
    is_idle   = (now - last_user) >= idle_threshold

    if server_restarted:
        # Warm once on the restart edge. If the server is mid-traffic (Jake
        # active), the busy/lock re-check below skips it — his own traffic
        # warms the cache and we don't interrupt him.
        reason = "server-restart"
    elif is_idle and (now - _last_keepalive) >= keepalive_int:
        reason = "keepalive"
    else:
        return

    # Acquire the SAME lock the fire path uses — mutual exclusion with cycles.
    try:
        lock_fd = open(_LOCK_PATH, "w")
    except OSError:
        return
    try:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (IOError, OSError):
            return  # a cycle (or another holder) owns it — skip this poll
        st = _read_state()
        if st.get("cycle_active", False) or _llama_busy():
            return  # never overlap a real cycle or active generation
        if _send_warmup(reason):
            # _llama_busy() carries the long overlap protection (is_processing
            # spans the whole warm prefill+decode); this short grace only
            # covers request-accepted → prefill-registers. warm_timeout kept
            # as the absolute ceiling.
            _warmup_inflight_until = now + min(_WARM_REGISTER_GRACE, warm_timeout)
            _last_keepalive        = now
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        except Exception:
            pass
        lock_fd.close()


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
