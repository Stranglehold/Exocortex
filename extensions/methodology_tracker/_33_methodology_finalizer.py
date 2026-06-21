"""
Methodology Finalizer — flushes the per-cycle record on cycle completion
========================================================================
Hook: tool_execute_after (_33_)

THE integration point Opus flagged. cycle_close.py runs as a SUBPROCESS (the
agent invokes it via code_execution with --cycle-type args), so it has no access
to the in-process _methodology_cycle_data attr. Finalization must happen in-process.

This mirrors _70_idle_trigger's cycle-close detection: when the agent calls
response() to close an idle cycle, finalize the methodology record (outcome
inferred from the accumulated cycle data). Abnormal cycles (no response) are
finalized as "incomplete" by _09's boundary detector on the next cycle.

Runs after _32_tool_call_tracker (so the last tool call is recorded) and before
_70_idle_trigger clears cycle_active.
"""

import importlib
import os
import sys

from helpers.extension import Extension


def _tracker_module():
    """Import the methodology tracker's finalize() from the sibling hook dir."""
    try:
        d = os.path.join(os.path.dirname(os.path.dirname(__file__)), "message_loop_prompts_after")
        if d not in sys.path:
            sys.path.insert(0, d)
        return importlib.import_module("_09_methodology_tracker")
    except Exception:
        return None


class MethodologyFinalizer(Extension):
    """tool_execute_after: on the cycle-closing response(), write the JSONL record."""

    async def execute(self, response=None, **kwargs) -> None:
        try:
            if (kwargs.get("tool_name") or "") != "response":
                return
            mod = _tracker_module()
            if mod and hasattr(mod, "finalize"):
                # outcome=None → inferred from cycle data (completed | stalled | error | desperation).
                # No-op if there is no tracked cycle (interactive response, subordinate, etc.).
                mod.finalize(self.agent)
        except Exception as e:
            print(f"[METHOD-FINAL] Error (passthrough): {e}", flush=True)
