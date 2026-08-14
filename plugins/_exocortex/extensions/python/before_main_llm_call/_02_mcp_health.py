"""
MCP Health — connection-state diagnostic
========================================
Hook: before_main_llm_call (priority _02 — after bootstraps, before anything that
depends on MCP tools)

Why this exists
---------------
Vek ran 2026-08-03 → 2026-08-12 with NO `exocortex-memory` server configured. His
own BUILD/EXPLORE prompts name `search_memory` / `search_library` as PRIMARY
sources, ahead of web search. Nothing failed loudly: cycles reported `completed`,
journals looked normal, and nine days of research ran without the corpus it was
told to ground itself in. The outage was invisible because **nothing in the stack
reported MCP connection state**.

The same blindness then blocked diagnosis: `MCPConfig.get_instance()` called from a
separate process returns a fresh singleton that has never loaded config (it reports
zero servers regardless of truth), and `/api/mcp_servers_status` triggers connection
attempts that can exceed a request timeout. The only place the live connection state
is observable is INSIDE A0's own process — i.e. from an extension. That is why this
is an extension and not a script.

This is the consumer-side instrument for a producer-side system: MCP config is
written and servers are (maybe) connected, but nothing ever *read* that state back.
Same shape as every severed loop this project has found — the gap lives at the
consumer.

What it does
------------
Throttled (default: once per 300s, plus always on the first turn of a context),
queries the live MCPConfig and logs one line per server: connected, tool_count,
error. If any server named in `required_servers` is missing or disconnected, it
logs a CRITICAL anomaly line instead of proceeding silently, and sets
`agent._mcp_degraded = True` so later layers can see it.

Deterministic. No LLM call. No context injection (costs zero tokens). Read-only
with respect to MCP — it never connects, disconnects, or mutates config.

Reads:  MCPConfig.get_instance().get_servers_status(), config.json[mcp_health]
Writes: agent._mcp_health (dict), agent._mcp_degraded (bool) — diagnostics only
Log tag: [MCP-HEALTH]
"""

import json
import os
import time
from typing import Any

from agent import LoopData
from helpers.extension import Extension

CONFIG_PATH = "/a0/usr/plugins/_exocortex/config/config.json"
CONFIG_SECTION = "mcp_health"

LAST_CHECK_ATTR = "_mcp_health_last_check"
STATE_ATTR = "_mcp_health"
DEGRADED_ATTR = "_mcp_degraded"

DEFAULTS = {
    "enabled": True,
    "check_interval_seconds": 300,
    # servers whose absence is a CRITICAL anomaly rather than a note
    "required_servers": ["exocortex-memory"],
}


def _load_config() -> dict[str, Any]:
    """Config is optional; a missing file or section must never break a turn."""
    cfg = dict(DEFAULTS)
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                section = json.load(f).get(CONFIG_SECTION) or {}
            if isinstance(section, dict):
                cfg.update({k: v for k, v in section.items() if k in DEFAULTS})
    except Exception:
        pass
    return cfg


def _norm(name: Any) -> str:
    """Normalize a server name for comparison.

    A0 normalizes MCP server names for tool namespacing — `deep-wiki` is reported
    as `deep_wiki`, `exocortex-memory` as `exocortex_memory`. Config is written
    with hyphens (that's what the settings UI takes), so a raw string compare
    produces a FALSE CRITICAL: the server is connected and simultaneously reported
    missing. Caught on this extension's very first live fire.
    """
    return str(name).strip().lower().replace("-", "_")


def _server_status() -> list[dict[str, Any]] | None:
    """Live status from A0's own MCP config. None = could not determine.

    None is deliberately distinguished from [] — 'I cannot tell' and 'there are
    no servers' are different findings, and conflating them is what made the
    original outage unreadable.
    """
    try:
        from helpers.mcp_handler import MCPConfig  # imported lazily: A0-version dependent
    except Exception:
        return None
    try:
        return list(MCPConfig.get_instance().get_servers_status() or [])
    except Exception:
        return None


class MCPHealth(Extension):
    """before_main_llm_call: report MCP connection state; flag required-server loss."""

    def _log(self, msg: str) -> None:
        print(f"[MCP-HEALTH] {msg}", flush=True)

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
        try:
            cfg = _load_config()
            if not cfg.get("enabled", True):
                return

            now = time.time()
            last = getattr(self.agent, LAST_CHECK_ATTR, None)
            # always check on the first turn of a context; then throttle
            if last is not None and (now - last) < float(cfg.get("check_interval_seconds", 300)):
                return
            setattr(self.agent, LAST_CHECK_ATTR, now)

            status = _server_status()
            if status is None:
                self._log("state UNDETERMINED — MCP handler unavailable (not the same as 'no servers')")
                return

            # compare on normalized names (see _norm) — never on the raw strings
            required = [str(r) for r in (cfg.get("required_servers") or [])]
            by_name = {str(s.get("name")): s for s in status}
            by_norm = {_norm(n): s for n, s in by_name.items()}

            connected, broken = [], []
            for name, s in by_name.items():
                if s.get("connected"):
                    connected.append(f"{name}({s.get('tool_count', '?')})")
                else:
                    broken.append(f"{name}: {str(s.get('error') or 'not connected')[:60]}")

            self._log(
                f"{len(connected)}/{len(by_name)} connected"
                + (f" — {', '.join(sorted(connected))}" if connected else "")
            )
            for b in sorted(broken):
                self._log(f"  DOWN {b}")

            # required-server check — the case that caused the silent 9-day outage
            missing = [r for r in required if _norm(r) not in by_norm]
            down = [r for r in required if _norm(r) in by_norm and not by_norm[_norm(r)].get("connected")]
            degraded = bool(missing or down)

            if degraded:
                detail = []
                if missing:
                    detail.append(f"NOT CONFIGURED: {', '.join(missing)}")
                if down:
                    detail.append(f"CONFIGURED BUT DOWN: {', '.join(down)}")
                self._log(
                    "CRITICAL — required MCP server unavailable (" + "; ".join(detail) + "). "
                    "Corpus-grounded steps (search_memory/search_library) will silently "
                    "degrade to web-only research this cycle."
                )

            setattr(self.agent, DEGRADED_ATTR, degraded)
            setattr(
                self.agent,
                STATE_ATTR,
                {
                    "checked_at": now,
                    "total": len(by_name),
                    "connected": len(connected),
                    "required_missing": missing,
                    "required_down": down,
                    "degraded": degraded,
                },
            )
        except Exception as e:
            # never break a turn over a diagnostic
            try:
                self._log(f"skipped — {type(e).__name__}: {str(e)[:80]}")
            except Exception:
                pass
