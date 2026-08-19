"""
Exocortex In-Process Diagnostics
================================
Route (auto-registered by A0 plugin dispatch): GET|POST /api/plugins/_exocortex/diagnostics

NOTE ON THE ROUTE SHAPE: plugin API modules register at /api/plugins/<plugin>/<module>,
NOT /api/<module>. Verified live 2026-08-19 against VekV2: POST /api/idle_control -> 404,
POST /api/plugins/_exocortex/idle_control -> 200. (The docstring in idle_control.py is
wrong about this.)

Why this exists
---------------
A fresh `docker exec ... python3` gets its OWN process: an EMPTY AgentContext registry,
a fresh MCPConfig singleton that never loaded config, and no view of the running event
loop file descriptors. It reports zero for everything and is confidently wrong.
The only place live in-process state is observable is INSIDE the A0 process.

That blindness cost hours on the 2026-08-18 PTY session leak: every external probe said
the shells were fine while /proc/<pid>/fd inside the server accumulated PTY handles, one
per API call, never reaped. Wiring seam #29.

Same shape as _02_mcp_health: a consumer-side instrument for producer-side state that
nothing ever read back.

What it reports
---------------
  process   pid, uptime, thread count, open-fd count, and the PTY handle count
  contexts  live AgentContext registry - id, name, type, paused, task state, timestamps
  shells    per-agent _cet_state shell handles (the PTY leak direct readout)
  mcp       the CACHED agent._mcp_health written by _02_mcp_health - see note below
  layers    a small live-state sample proving the stack is loaded, not merely on disk

Strictly read-only. It never connects, spawns, closes, or mutates anything.

MCP note: this reads the *cached* health dict. It does NOT call get_servers_status()
directly - that triggers connection attempts which can exceed a request timeout.
stale_seconds tells you how old the cache is; a missing cache means the extension has
not fired yet in this process.
"""

import os
import time

from helpers.api import ApiHandler, Request, Response

_PROC_SELF_FD = "/proc/self/fd"
_PROC_SELF_STATUS = "/proc/self/status"


class Diagnostics(ApiHandler):
    """GET|POST /api/plugins/_exocortex/diagnostics - read-only in-process state."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict | Response:
        now = time.time()
        out: dict = {
            "ok": True,
            "generated_at": now,
            "process": _process_stats(),
            "contexts": [],
            "shells": {"total_handles": 0, "by_context": []},
            "mcp": {"available": False},
            "layers": {},
        }

        contexts = _live_contexts()
        out["context_count"] = len(contexts)

        # Sample mcp/layers from the MOST RECENTLY ACTIVE context. Taking the first
        # in registry order reads a long-dead context and reports null for everything,
        # which looks identical to "the layer never fired".
        for ctx in _by_recency(contexts):
            sampled = _layer_sample(ctx)
            if any(v is not None for v in sampled.values()):
                out["layers"] = sampled
                out["layers"]["sampled_from"] = getattr(ctx, "id", None)
                break
        else:
            out["layers"] = {"note": "no context has live layer state in this process yet"}

        total_handles = 0
        mcp_seen = False

        for ctx in _by_recency(contexts):
            try:
                out["contexts"].append(_context_summary(ctx, now))
            except Exception as e:
                out["contexts"].append({"error": f"{type(e).__name__}: {e}"})

            try:
                shells = _shell_summary(ctx)
                total_handles += shells.get("handles", 0)
                out["shells"]["by_context"].append(shells)
            except Exception as e:
                out["shells"]["by_context"].append({"error": f"{type(e).__name__}: {e}"})

            if not mcp_seen:
                mcp = _mcp_summary(ctx, now)
                if mcp.get("available"):
                    mcp["sampled_from"] = getattr(ctx, "id", None)
                    out["mcp"] = mcp
                    mcp_seen = True

        out["shells"]["total_handles"] = total_handles

        # The leak signature: PTY device handles far exceeding tracked shell handles
        # means sessions were created and never closed. Roughly equal is healthy.
        pty = out["process"].get("pty_handles")
        if isinstance(pty, int):
            out["shells"]["untracked_pty_handles"] = max(0, pty - total_handles)

        return out


# -- process ------------------------------------------------------------------

def _process_stats() -> dict:
    stats: dict = {"pid": os.getpid()}

    try:
        stats["uptime_seconds"] = round(
            time.time() - os.path.getmtime("/proc/%d" % os.getpid()), 1
        )
    except Exception:
        stats["uptime_seconds"] = None

    try:
        import threading
        stats["threads_python"] = threading.active_count()
    except Exception:
        stats["threads_python"] = None

    try:
        with open(_PROC_SELF_STATUS, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("Threads:"):
                    stats["threads_os"] = int(line.split()[1])
                elif line.startswith("VmRSS:"):
                    stats["rss_kb"] = int(line.split()[1])
    except Exception:
        pass
    stats.setdefault("threads_os", None)
    stats.setdefault("rss_kb", None)

    fds = _fd_targets()
    if fds is None:
        stats["open_fds"] = None
        stats["pty_handles"] = None
    else:
        stats["open_fds"] = len(fds)
        stats["pty_handles"] = sum(
            1 for t in fds if t.startswith("/dev/pts/") or t == "/dev/ptmx"
        )

    return stats


def _fd_targets():
    """Resolve every open fd to its target. Returns None if /proc is unreadable."""
    try:
        targets = []
        for name in os.listdir(_PROC_SELF_FD):
            try:
                targets.append(os.readlink(os.path.join(_PROC_SELF_FD, name)))
            except OSError:
                continue  # fd closed between listdir and readlink - normal
        return targets
    except Exception:
        return None


# -- contexts -----------------------------------------------------------------

def _live_contexts() -> list:
    try:
        from agent import AgentContext
        return AgentContext.all()
    except Exception:
        return []


def _by_recency(contexts: list) -> list:
    """Most recently active first. Contexts without a usable timestamp sort last."""
    def key(ctx):
        try:
            return getattr(ctx, "last_message").timestamp()
        except Exception:
            return float("-inf")
    try:
        return sorted(contexts, key=key, reverse=True)
    except Exception:
        return contexts


def _context_summary(ctx, now: float) -> dict:
    task = getattr(ctx, "task", None)
    d: dict = {
        "id": getattr(ctx, "id", None),
        "no": getattr(ctx, "no", None),
        "name": getattr(ctx, "name", None),
        "type": str(getattr(ctx, "type", "")),
        "paused": bool(getattr(ctx, "paused", False)),
        "has_task": task is not None,
    }
    try:
        d["task_alive"] = bool(task and task.is_alive())
    except Exception:
        d["task_alive"] = None
    for field in ("created_at", "last_message"):
        val = getattr(ctx, field, None)
        d[field] = val.isoformat() if hasattr(val, "isoformat") else None
    try:
        d["idle_seconds"] = round(now - getattr(ctx, "last_message").timestamp(), 1)
    except Exception:
        d["idle_seconds"] = None
    return d


# -- shells (the PTY leak readout) --------------------------------------------

def _walk_agents(ctx) -> list:
    """agent0 plus its subordinate chain, defensively bounded."""
    try:
        from agent import Agent
        sub_key = getattr(Agent, "DATA_NAME_SUBORDINATE", "_subordinate")
    except Exception:
        sub_key = "_subordinate"

    agents = []
    seen = set()
    agent = getattr(ctx, "agent0", None)
    while agent is not None and id(agent) not in seen and len(agents) < 32:
        seen.add(id(agent))
        agents.append(agent)
        try:
            agent = agent.get_data(sub_key)
        except Exception:
            break
    return agents


def _shell_summary(ctx) -> dict:
    summary: dict = {"context_id": getattr(ctx, "id", None), "handles": 0, "agents": []}
    for agent in _walk_agents(ctx):
        entry: dict = {"agent_number": getattr(agent, "number", None), "sessions": []}
        try:
            state = agent.get_data("_cet_state")
        except Exception:
            state = None
        if state is None:
            entry["state"] = "none"
            summary["agents"].append(entry)
            continue
        entry["state"] = "present"
        entry["ssh_enabled"] = bool(getattr(state, "ssh_enabled", False))
        shells = getattr(state, "shells", None) or {}
        for sid, wrap in list(shells.items())[:64]:
            entry["sessions"].append({
                "session": sid,
                "running": bool(getattr(wrap, "running", False)),
                "session_class": type(getattr(wrap, "session", None)).__name__,
            })
        summary["handles"] += len(entry["sessions"])
        summary["agents"].append(entry)
    return summary


# -- mcp (cached only - never triggers a connection) --------------------------

def _mcp_summary(ctx, now: float) -> dict:
    agent = getattr(ctx, "agent0", None)
    if agent is None:
        return {"available": False}
    health = getattr(agent, "_mcp_health", None)
    if not health:
        return {
            "available": False,
            "reason": "_02_mcp_health has not fired in this process yet",
        }
    last = getattr(agent, "_mcp_health_last_check", None)
    return {
        "available": True,
        "degraded": bool(getattr(agent, "_mcp_degraded", False)),
        "servers": health,
        "stale_seconds": round(now - last, 1) if isinstance(last, (int, float)) else None,
    }


# -- layers (proof the stack is loaded in THIS process) -----------------------

def _layer_sample(ctx) -> dict:
    agent = getattr(ctx, "agent0", None)
    if agent is None:
        return {}
    sample: dict = {}
    for label, attr in (
        ("bst_domain", "_bst_domain"),
        ("supervisor_turn", "_supervisor_turn"),
        ("supervisor_loop_tier", "_supervisor_loop_tier"),
        ("action_gate_active", "_action_gate_active"),
        ("evidence_ledger_entries", "_evidence_ledger"),
        ("loop_active", "_loop_active"),
    ):
        val = getattr(agent, attr, None)
        if val is None:
            sample[label] = None
        elif isinstance(val, (list, dict, set, tuple)):
            sample[label] = len(val)
        elif isinstance(val, (str, int, float, bool)):
            sample[label] = val
        else:
            sample[label] = type(val).__name__
    return sample
