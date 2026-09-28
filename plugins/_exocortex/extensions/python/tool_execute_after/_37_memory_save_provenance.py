"""
_37_memory_save_provenance.py — stamp a memory the agent saved, in the context that saved it (Tier 1)

Hook: tool_execute_after (fires only for tool calls that executed)

memory_save is the agent writing her own memory, with the chat model. A0 inserts it with only
{area, **kwargs} as metadata and the insert is not @extensible, so this is the one place the saving
context is still known. The tool's reply carries the new id ("Memory saved with id <id>",
fw.memory_saved.md); this extension reads it back and records an exact stamp in the sidecar
(helpers/memory_provenance.py). The memory itself is not touched.

SELF-TEST
---------
The id is read through the template the agent actually renders (prompt overrides included), with a
known id first: if that does not parse back, the template has changed shape. Then nothing is
stamped here, one loud line is logged, and _55 stamps the memory later at a lower tier
(same_monologue or first_seen). A misread id is never recorded.

WHAT IT DOES NOT DO
-------------------
- Does not change the tool's reply or the memory's metadata. It appends one sidecar line.
- Does not stamp memory_load, memory_forget or any other tool.
- No LLM calls. Never raises.
"""

import sys

from helpers.extension import Extension

_EXOCORTEX_HELPERS = "/a0/usr/plugins/_exocortex/helpers"
if _EXOCORTEX_HELPERS not in sys.path:
    sys.path.insert(0, _EXOCORTEX_HELPERS)

_SELFTEST_WARNED = {"done": False}


class MemorySaveProvenance(Extension):
    """tool_execute_after: an exact provenance stamp for memory_save."""

    async def execute(self, response=None, **kwargs) -> None:
        try:
            if kwargs.get("tool_name") != "memory_save":
                return
            import memory_provenance as mp

            if not mp.cfg()["enabled"]:
                return
            template = mp.rendered_template(self.agent)
            if mp.parse_saved_id(template, template) != mp._SELFTEST_ID:
                if not _SELFTEST_WARNED["done"]:
                    _SELFTEST_WARNED["done"] = True
                    print(f"[MEM-PROV] SELF-TEST FAILED: {mp.SAVED_TEMPLATE} no longer renders its id in a "
                          f"parseable form ({template[:80]!r}); memory_save stamps fall back to _55", flush=True)
                return
            mem_id = mp.parse_saved_id(getattr(response, "message", "") or "", template)
            if not mem_id:
                print("[MEM-PROV] memory_save reply did not parse; left to _55", flush=True)
                return
            if mp.stamp_exact(mem_id, self.agent, "memory_save", "chat"):
                print(f"[MEM-PROV] memory_save {mem_id} stamped exact", flush=True)
        except Exception as e:
            try:
                print(f"[MEM-PROV] memory_save stamp skipped — {type(e).__name__}: {str(e)[:80]}", flush=True)
            except Exception:
                pass
