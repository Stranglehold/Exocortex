"""
_04_monologue_ledger.py — record that a monologue started, for memory provenance (Tier 1)

Hook: monologue_start (A0 calls it once per monologue, subordinates included)

Appends one line to state/monologue_ledger.jsonl: {t, event: "start", chat_id, preset, chat_model,
utility_model}. _55 reads the ledger to find which chat was running when a memory it did not see
written was created (helpers/memory_provenance.py). The matching end event is written by
monologue_end/_05_monologue_ledger.py.

WHAT IT DOES NOT DO
-------------------
- Does not touch any memory, prompt or agent data. It appends one line.
- Does not call an LLM. Never raises.
"""

import sys

from agent import LoopData
from helpers.extension import Extension

_EXOCORTEX_HELPERS = "/a0/usr/plugins/_exocortex/helpers"
if _EXOCORTEX_HELPERS not in sys.path:
    sys.path.insert(0, _EXOCORTEX_HELPERS)


class MonologueLedgerStart(Extension):
    """monologue_start: one ledger line."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        try:
            import memory_provenance as mp

            mp.append_ledger(mp.ledger_entry("start", self.agent))
        except Exception as e:
            try:
                print(f"[MEM-PROV] ledger start skipped — {type(e).__name__}: {str(e)[:80]}", flush=True)
            except Exception:
                pass
