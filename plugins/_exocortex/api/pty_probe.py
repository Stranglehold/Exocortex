"""
Exocortex PTY Reaper Acceptance Probe
=====================================
Route (auto-registered by A0 plugin dispatch): POST /api/plugins/_exocortex/pty_probe

DISABLED BY DEFAULT. Returns 403 unless the sentinel file exists:

    docker exec <container> touch /tmp/exocortex_pty_probe_enabled

Why this exists
---------------
`plugins/_exocortex/patches/patch_pty_session_leak.py` mitigates an A0 core leak: every
AgentContext that runs code_execution allocates a PTY master + child shell that nothing
ever closes. The patch adds an idle reaper that calls the existing (correct) close().

The acceptance question is not "does one shell get closed" -- that was proven end to end
on 2026-08-18. It is whether handles stay BOUNDED under sustained load, i.e. whether the
reaper keeps up across many sessions and there is no second leak path.

Answering that from outside is impossible, and answering it by waiting for organic cycles
is unreliable: measured 2026-08-19, both live containers had run ZERO cycles in 25 hours,
so their `ptmx: 0` reading was indistinguishable from a working reaper and from no load
at all. A null result is a claim; it needs evidence like any other.

A `docker exec ... python3` probe cannot answer it either -- that is a DIFFERENT process
with its own event loop, its own module import of tty_session, and its own (empty)
`_exo_live_sessions`. It would exercise a private copy of the reaper and tell you nothing
about the running server. Same blindness as wiring seam #29.

So the probe has to run INSIDE the A0 process. This is that.

What it does
------------
  spawn (n)  create N real TTYSessions through the LIVE patched module, exactly as
             code_execution does, and hold strong references -- because in production the
             agent holds them via `_cet_state`, and `_exo_live_sessions` is a WeakSet.
             Without strong refs the objects would be garbage collected and the test would
             measure Python's GC instead of the reaper.
  state      ptmx handle count, registered/live/terminated counts, reaper task state, and
             the per-session idle age the reaper actually keys on.
  close      escape hatch. Explicitly closes every probe-created session. For cleanup if
             the reaper does NOT work -- which is the outcome this probe exists to detect.

USE exo_installtest, NOT A LIVE AGENT CONTAINER. Spawning tens of shells is precisely the
handle count that deadlocked VekV2 twice. If the reaper is broken, this probe reproduces
the outage.
"""

import os
import time

from helpers.api import ApiHandler, Request, Response

_SENTINEL = "/tmp/exocortex_pty_probe_enabled"
_MAX_SPAWN = 60          # hard ceiling per call; the observed deadlock was ~38 handles
_PROBE_SESSIONS: list = []   # strong refs, mirroring the agent's _cet_state


class PtyProbe(ApiHandler):
    """POST /api/plugins/_exocortex/pty_probe - PTY reaper acceptance instrument."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict | Response:
        if not os.path.exists(_SENTINEL):
            return {
                "ok": False,
                "error": "probe disabled",
                "enable_with": f"touch {_SENTINEL}",
                "warning": "spawns real shells; use the test container, not a live agent",
            }

        action = (input.get("action") or "state").strip().lower()
        if action == "spawn":
            return await _spawn(int(input.get("n") or 1))
        if action == "close":
            return await _close_all()
        if action == "state":
            return _state()
        return {"ok": False, "error": f"unknown action {action!r}",
                "actions": ["spawn", "state", "close"]}


def _background_loop():
    """A0's PERSISTENT event loop -- the one agent turns actually run on.

    MEASURED 2026-08-19, and it invalidated the first version of this probe:
    A0 serves each API request on its OWN event loop. Two successive calls to this
    handler reported different `id(asyncio.get_running_loop())`. So sessions spawned
    directly from a request armed `_exo_reaper_task` in a loop that stopped the moment
    the request returned. The reaper then never swept -- 50 sessions sat 773s idle
    against a 600s limit with zero closings -- and `task.done()` was still False,
    because an ABANDONED task is indistinguishable from a scheduled one. A false red
    that looked exactly like a broken patch.

    Production does not work that way: `helpers.defer.EventLoopThread` owns a
    `run_forever()` loop on a daemon thread, and agent turns run there via
    DeferredTask. That is why the 2026-08-18 end-to-end test genuinely reaped at
    t+80s. To measure the reaper the way production experiences it, the sessions have
    to be created on THAT loop -- so the probe submits its work there.
    """
    from helpers.defer import EventLoopThread
    return EventLoopThread().loop


async def _on_background_loop(coro):
    """Run `coro` on the persistent loop and await the result from this request."""
    import asyncio as _a
    fut = _a.run_coroutine_threadsafe(coro, _background_loop())
    return await _a.wrap_future(fut)


def _tty_module():
    """Resolve the tty_session module object THE SERVER ALREADY IMPORTED.

    Deliberately NOT a plain `import`: if the import path we guess differs at all from
    the one A0 used, Python builds a SECOND module object with its own
    `_exo_live_sessions` WeakSet and its own reaper task. The probe would then spawn
    into a private copy and report on a reaper the server is not running -- a green
    result measuring the wrong thing. So: scan sys.modules for the loaded module and
    only fall back to importing if it genuinely is not there yet.
    """
    import sys
    for name, mod in list(sys.modules.items()):
        if mod is None or not name.endswith("tty_session"):
            continue
        if hasattr(mod, "TTYSession"):
            return mod
    from plugins._code_execution.helpers import tty_session  # type: ignore
    return tty_session


def _ptmx_count() -> int:
    n = 0
    try:
        for name in os.listdir("/proc/self/fd"):
            try:
                if "ptmx" in os.readlink(os.path.join("/proc/self/fd", name)):
                    n += 1
            except OSError:
                continue
    except OSError:
        return -1
    return n


def _reaper_state(mod) -> dict:
    """Report the reaper AND the loop it lives in.

    `task.done()` is False both for a task that is being scheduled and for a task
    that was created in an event loop which has since stopped -- an abandoned task
    looks identical to a healthy one. If A0 serves each API request on its own
    loop, a reaper armed from this probe is orphaned the moment the request ends,
    and the probe would report a broken reaper that is really a broken probe.
    So: report the current loop id, the loop the task belongs to, and whether that
    loop is still running. Compare across two calls -- differing current_loop_id
    means per-request loops and this probe cannot test the reaper at all.
    """
    import asyncio as _a
    task = getattr(mod, "_exo_reaper_task", None)
    cur = None
    try:
        cur = id(_a.get_running_loop())
    except Exception:
        pass
    task_loop_id = task_loop_running = None
    if task is not None:
        try:
            tl = task.get_loop()
            task_loop_id, task_loop_running = id(tl), tl.is_running()
        except Exception:
            pass
    return {
        "current_loop_id": cur,
        "task_loop_id": task_loop_id,
        "task_loop_running": task_loop_running,
        "task_loop_is_current": (cur is not None and cur == task_loop_id),
        "patched": hasattr(mod, "_exo_live_sessions"),
        "idle_limit_seconds": getattr(mod, "_EXO_IDLE_LIMIT_SECONDS", None),
        "interval_seconds": getattr(mod, "_EXO_REAP_INTERVAL_SECONDS", None),
        "task_exists": task is not None,
        "task_running": bool(task is not None and not task.done()),
        "registered": len(getattr(mod, "_exo_live_sessions", ()) or ()),
    }


def _state() -> dict:
    mod = _tty_module()
    now = time.monotonic()
    live = terminated = 0
    ages = []
    for s in _PROBE_SESSIONS:
        try:
            if s.is_terminated():
                terminated += 1
                continue
            live += 1
            last = getattr(s, "_exo_last_used", None)
            if last is not None:
                ages.append(round(now - last, 1))
        except Exception:
            pass
    ages.sort()
    return {
        "ok": True,
        "ptmx": _ptmx_count(),
        "probe_sessions": len(_PROBE_SESSIONS),
        "probe_live": live,
        "probe_terminated": terminated,
        "idle_ages_seconds": {"min": ages[0], "max": ages[-1]} if ages else {},
        "reaper": _reaper_state(mod),
    }


async def _do_spawn(n: int) -> tuple:
    """Runs ON THE PERSISTENT LOOP. Creating the session here is what arms the reaper
    in a loop that will still be alive to sweep -- see _background_loop()."""
    mod = _tty_module()
    made, errors = 0, []
    for _ in range(n):
        try:
            # `cmd` is joined and handed to create_subprocess_shell, same as the real
            # caller. A bare shell is exactly what code_execution allocates.
            sess = mod.TTYSession("/bin/sh")
            await sess.start()
            _PROBE_SESSIONS.append(sess)   # strong ref: the agent does this via _cet_state
            made += 1
        except Exception as e:
            errors.append(repr(e))
            break
    return made, errors


async def _spawn(n: int) -> dict:
    n = max(1, min(int(n), _MAX_SPAWN))
    before = _ptmx_count()
    made, errors = await _on_background_loop(_do_spawn(n))
    out = _state()
    out.update({"requested": n, "spawned": made, "ptmx_before": before})
    if errors:
        out["errors"] = errors
    return out


async def _do_close() -> tuple:
    """Also on the persistent loop: close() cancels the session's _pump_task, and a
    task can only be cancelled from the loop that owns it."""
    closed, errors = 0, []
    for s in list(_PROBE_SESSIONS):
        try:
            await s.close()
            closed += 1
        except Exception as e:
            errors.append(repr(e))
    _PROBE_SESSIONS.clear()
    return closed, errors


async def _close_all() -> dict:
    closed, errors = await _on_background_loop(_do_close())
    out = _state()
    out.update({"closed": closed})
    if errors:
        out["errors"] = errors[:5]
    return out
