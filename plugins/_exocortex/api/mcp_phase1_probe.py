"""
Exocortex Phase 1 MCP-Anomaly Acceptance Probe
==============================================
Route (auto-registered by A0 plugin dispatch): POST /api/plugins/_exocortex/mcp_phase1_probe

DISABLED BY DEFAULT. Returns a refusal unless the sentinel exists:

    docker exec <container> touch /tmp/exocortex_phase1_probe_enabled

Why this exists
---------------
Tier 1.4 makes sleep Phase 1 say out loud when the memory server is unreachable, instead
of running a consolidation cycle that looks identical to a healthy one. The acceptance
question is whether the WRITER (`_02_mcp_health`, which caches `agent._mcp_health`) and
the READER (`_mcp_connection_state` in `helpers/sleep_consolidation.py`) actually agree
on the shape of that cache -- end to end, in the process where both really run.

Two ways of answering that are wrong, and both look green:

  * Hand-building a fake `_mcp_health` dict in a unit test. Session 123: a gate test
    passed because it populated the exact field the buggy code read, while production
    wrote somewhere else. A fixture I author cannot falsify my own assumption about the
    fixture. So this probe runs the REAL extension to produce the cache.

  * Running it from `docker exec ... python3`. That process gets a fresh MCPConfig
    singleton which never loaded any config, so `get_servers_status()` returns [], so a
    required server always looks missing, so the alarm always fires -- green for
    entirely the wrong reason. Same blindness as wiring seam #29. So this runs in-process.

What it does
------------
  1. Runs the real `MCPHealth` extension against a throwaway stub agent, so
     `_mcp_health` is written by the code that writes it in production.
  2. Feeds that stub to the real `_mcp_connection_state()` and reports the verdict.
  3. Optionally (`"run_phase1": true`) calls the real `run_phase1_consolidation` and
     returns its `mcp` / `anomalies` fields, proving the alarm reaches the phase result
     and therefore the written sleep report.

`run_phase1` MUTATES procedural memory (dedup + utility-field init). Test containers
only. Everything else here is read-only.
"""

import os

from helpers.api import ApiHandler, Request, Response

# Its OWN sentinel, deliberately not the PTY probe's. `run_phase1` MUTATES procedural
# memory, and enabling a shell-spawning probe should never silently also enable a
# memory-mutating one. Two instruments, two switches.
_SENTINEL = "/tmp/exocortex_phase1_probe_enabled"


class _StubAgent:
    """Minimal stand-in: MCPHealth only ever setattr/getattr's on the agent."""

    def __init__(self):
        self.agent_name = "phase1-mcp-probe"


class McpPhase1Probe(ApiHandler):
    """POST /api/plugins/_exocortex/mcp_phase1_probe - Tier 1.4 acceptance instrument."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict | Response:
        if not os.path.exists(_SENTINEL):
            return {"ok": False, "error": "probe disabled",
                    "enable_with": f"touch {_SENTINEL}"}

        out: dict = {"ok": True, "steps": []}
        stub = _StubAgent()

        # ── 1. real writer ────────────────────────────────────────────────
        try:
            import importlib.util
            path = ("/a0/usr/plugins/_exocortex/extensions/python/"
                    "before_main_llm_call/_02_mcp_health.py")
            spec = importlib.util.spec_from_file_location("_exo_mcp_health_probe", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore
            ext = mod.MCPHealth(agent=stub)  # type: ignore
            await ext.execute()
            out["steps"].append("ran real MCPHealth.execute()")
        except Exception as e:
            out["steps"].append(f"MCPHealth FAILED: {type(e).__name__}: {e}")

        out["written_cache"] = getattr(stub, "_mcp_health", None)
        out["degraded_flag"] = getattr(stub, "_mcp_degraded", None)

        # ── 2. real reader ────────────────────────────────────────────────
        try:
            import sys
            sys.path.insert(0, "/a0/usr/plugins/_exocortex/helpers")
            from sleep_consolidation import _mcp_connection_state  # type: ignore
            out["reader_verdict"] = _mcp_connection_state(stub)
            out["steps"].append("ran real _mcp_connection_state()")
        except Exception as e:
            out["ok"] = False
            out["steps"].append(f"reader FAILED: {type(e).__name__}: {e}")
            return out

        # Writer/reader agreement is the whole point: if the reader saw no cache while
        # the writer just wrote one, the two halves disagree about the field.
        out["writer_reader_agree"] = bool(
            isinstance(out["written_cache"], dict)
            and out["reader_verdict"]["status"] != "unknown"
        ) or out["written_cache"] is None

        # ── 3. optional: the real phase ───────────────────────────────────
        if input.get("run_phase1"):
            try:
                from sleep_consolidation import run_phase1_consolidation  # type: ignore
                r1 = run_phase1_consolidation("mcp-phase1-probe", agent=stub)
                out["phase1"] = {"mcp": r1.get("mcp"), "anomalies": r1.get("anomalies")}
                out["steps"].append("ran real run_phase1_consolidation()")
            except Exception as e:
                out["phase1"] = {"error": f"{type(e).__name__}: {e}"}
                out["steps"].append("run_phase1_consolidation FAILED")

        return out
