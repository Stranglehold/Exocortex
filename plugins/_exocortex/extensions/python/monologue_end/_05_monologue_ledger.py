"""
_05_monologue_ledger.py — record that a monologue ended, for memory provenance (Tier 1)

Hook: monologue_end (A0 calls it once per monologue, subordinates included)

Appends one line to state/monologue_ledger.jsonl: {t, event: "end", chat_id, preset, chat_model,
utility_model}. A0's own memorizers (_memory plugin: _50_memorize_fragments, _51_memorize_solutions,
and the consolidation they call) insert AFTER this hook, in the background, so no extension ever
sees their memories being written. _55 later matches such a memory's creation time to the one chat
whose monologue ended at most window_s before it (helpers/memory_provenance.py, memorize_window).
Numbered _05 so the line is written before any memorizer can start.

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


class MonologueLedgerEnd(Extension):
    """monologue_end: one ledger line."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        try:
            import memory_provenance as mp

            mp.append_ledger(mp.ledger_entry("end", self.agent))
        except Exception as e:
            try:
                print(f"[MEM-PROV] ledger end skipped — {type(e).__name__}: {str(e)[:80]}", flush=True)
            except Exception:
                pass
