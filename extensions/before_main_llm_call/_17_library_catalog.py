"""
_17_library_catalog.py — Exocortex Library Catalog Injection
=============================================================

Injects a compact [LIBRARY] block into the agent's context before each LLM
call so the agent always knows what reference documents are available.

Fires silently when the library is empty.
Fires with a compact list when documents are present (max 10 shown inline;
overflow directed to library_list tool).

Slot: 17 (after _16_tool_registry, before _18_memory_catalog)
Hook: before_main_llm_call

Pattern: prepend to last user message in loop_data.history_output
         (same as _13_reasoning_state.py, _16_tool_registry.py)

Spec: specs/LIBRARY_SPEC_L3.md
"""

import json
import os

from python.helpers.extension import Extension
from agent import LoopData

CATALOG_PATH    = "/a0/usr/library/catalog.json"
MAX_INLINE_DOCS = 10


class LibraryCatalog(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        try:
            block = _build_block()
            if not block:
                return

            user_msg = _get_last_user_message(loop_data.history_output)
            if user_msg is None:
                return

            existing = user_msg.get("content", "")
            if isinstance(existing, list):
                # multi-part message — prepend to first text part
                for part in existing:
                    if isinstance(part, dict) and part.get("type") == "text":
                        part["text"] = block + "\n\n" + part.get("text", "")
                        break
            else:
                user_msg["content"] = block + "\n\n" + str(existing)

        except Exception:
            pass  # never break the pipeline


def _load_catalog() -> dict:
    if not os.path.exists(CATALOG_PATH):
        return {"documents": []}
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"documents": []}


def _build_block() -> str:
    catalog = _load_catalog()
    docs = catalog.get("documents", [])
    if not docs:
        return ""

    total = len(docs)
    shown = docs[:MAX_INLINE_DOCS]

    lines = [f"[LIBRARY — {total} document(s) available; use library_search or library_list]"]
    for d in shown:
        lid    = d.get("library_id", "")
        title  = d.get("title", "")[:45]
        topics = ", ".join(d.get("topics", []))[:40]
        lines.append(f"  {lid} | {title} | {topics}")

    if total > MAX_INLINE_DOCS:
        lines.append(f"  (+{total - MAX_INLINE_DOCS} more — use library_list for full catalog)")

    lines.append("[/LIBRARY]")

    n = min(total, MAX_INLINE_DOCS)
    print(f"[LIB-CAT] Injected {n}/{total} library document(s) into context", flush=True)
    return "\n".join(lines)


def _get_last_user_message(history: list) -> dict | None:
    if not history:
        return None
    for msg in reversed(history):
        if not msg.get("ai", True):
            return msg
    return None
