"""
_35_recall_tag_memory_load.py — mark memories recalled through the memory_load tool (R4)

Hook: tool_execute_after (fires only for tool calls that executed)

memory_load is recall on demand: the agent searches its store and reads the results back. Those
memories are recall exactly like the ones _92 injects. Re-saving them as new evidence is the
09-08 re-seeding path (Fable's third carrier). Opus's ruling A17: cover it here, from the
tool's own output.

HOW
---
The tool returns `Memory.format_docs_plain(docs)`. That writes every metadata key of every doc
as a `key: value` line, then `Content: …`, so each recalled memory's id arrives as a line
`id: <id>`. This extension reads those lines and adds the ids to the monologue's recalled set
(helpers/memory_recall_tag.py). The tool's own "not found" message carries no id lines, and
marks nothing.

WHAT IT DOES NOT DO
-------------------
- Does not refuse or change anything. It records; the writers refuse.
- Does not re-run the search. The ids come from the tool's own output.
- A memory whose *content* has a line of exactly the form `id: <word>` would add that word too.
  That over-tags in the safe direction: nothing can be saved under an id that does not exist.
- No LLM calls.
"""

import re
import sys

from helpers.extension import Extension

_EXOCORTEX_HELPERS = "/a0/usr/plugins/_exocortex/helpers"
if _EXOCORTEX_HELPERS not in sys.path:
    sys.path.insert(0, _EXOCORTEX_HELPERS)

# One metadata line per doc, as format_docs_plain writes it. Store ids are short alphanumerics
# (e.g. EgGAUgvVPV); the pattern admits a range, anchored to whole lines.
_ID_LINE = re.compile(r"^id: ([A-Za-z0-9_-]{4,64})\s*$", re.M)


def ids_in(text: str) -> list:
    """The memory ids in memory_load's output, in order, without duplicates."""
    seen = []
    for m in _ID_LINE.finditer(text or ""):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


class RecallTagMemoryLoad(Extension):
    """tool_execute_after: add memory_load's results to the recalled set."""

    async def execute(self, response=None, **kwargs) -> None:
        try:
            if kwargs.get("tool_name") != "memory_load":
                return
            ids = ids_in(getattr(response, "message", "") or "")
            if not ids:
                return
            import memory_recall_tag as mrt

            n = mrt.tag(self.agent, ids)
            print(f"[RECALL-TAG] memory_load recalled {len(ids)}; {n} this monologue", flush=True)
        except Exception as e:
            try:
                print(f"[RECALL-TAG] memory_load tag skipped — {type(e).__name__}: {str(e)[:80]}",
                      flush=True)
            except Exception:
                pass
