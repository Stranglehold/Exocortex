"""
_05_recall_tag_reset.py — start each monologue with an empty recalled-memory set (R4)

Hook: monologue_start (A0 calls it at agent.py ~L399, once per monologue)

The injectors (_55, _92, message_loop_prompts_after) add the ids of the memories they recall to
a set on the agent's data; the writers refuse to re-save those as new evidence. The set spans
one monologue, so it is emptied here, before the first recall of the next one.
See helpers/memory_recall_tag.py.

WHAT IT DOES NOT DO
-------------------
- Does not refuse or change any memory. It empties one set.
- Does not call an LLM.
"""

import sys

from agent import LoopData
from helpers.extension import Extension

_EXOCORTEX_HELPERS = "/a0/usr/plugins/_exocortex/helpers"
if _EXOCORTEX_HELPERS not in sys.path:
    sys.path.insert(0, _EXOCORTEX_HELPERS)


class RecallTagReset(Extension):
    """monologue_start: empty the recalled-memory set."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        try:
            import memory_recall_tag as mrt

            if not mrt.reset(self.agent):
                print("[RECALL-TAG] reset could not write the agent's data", flush=True)
        except Exception as e:
            try:
                print(f"[RECALL-TAG] reset skipped — {type(e).__name__}: {str(e)[:80]}", flush=True)
            except Exception:
                pass
