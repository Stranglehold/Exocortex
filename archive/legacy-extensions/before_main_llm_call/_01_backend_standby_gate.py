"""
Backend Standby Gate — Exocortex Infrastructure Recovery
=========================================================
Hook: before_main_llm_call (_01_ — fires first, before BST and everything else)

When the inference backend is down, _28_backend_standby.py (message_loop_end)
sets _backend_standby = True and starts a health poller. This extension reads
that flag and pauses the agent loop via context.paused, preventing litellm from
hammering a dead socket on every turn.

The pause is lifted by the health poller when the backend comes back online.
No LLM calls. No exceptions. No operator intervention required.
"""

import sys as _sys

_PM_PATH = "/a0/usr/Exocortex"
if _PM_PATH not in _sys.path:
    _sys.path.insert(0, _PM_PATH)

from agent import LoopData
from helpers.extension import Extension

STANDBY_FLAG = "_backend_standby"


class BackendStandbyGate(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        try:
            if not getattr(self.agent, STANDBY_FLAG, False):
                return

            # Backend is down. Pause the agent loop here.
            # handle_intervention() is called immediately after before_main_llm_call
            # extensions complete — it calls wait_if_paused(), which spins on
            # asyncio.sleep(0.1) until context.paused is cleared. The health poller
            # in _28_backend_standby.py clears it when the backend recovers.
            self.agent.context.paused = True
            print(
                "[BACKEND-GATE] Backend standby active — loop paused, waiting for recovery.",
                flush=True,
            )

        except Exception as e:
            print(f"[BACKEND-GATE] Error in standby gate: {e}", flush=True)
