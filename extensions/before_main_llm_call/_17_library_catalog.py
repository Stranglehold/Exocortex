"""
_17_library_catalog.py — Exocortex Library Catalog Injection  v2.0
===================================================================

Injects a compact [LIBRARY] block into the agent's context before each LLM
call so the agent always knows what reference collections are available.

v2.0 change: injects COLLECTION-level summaries rather than individual book
titles. With 300+ books across 20+ collections, per-book injection is noise;
per-collection injection is signal.

Format:
  [LIBRARY — 363 books in 22 collections; use library_search or library_list]
  col_a1b2c3d4 | Hacking 2.0 (35 books) | Offensive security, exploitation, malware...
  col_e5f6g7h8 | System Design (12 books) | Distributed systems, architecture...
  ...
  [/LIBRARY]

Fires silently when the library is empty.
Shows up to MAX_INLINE_COLLECTIONS collections inline; overflow directed to
library_collections tool.

Slot: 17 (after _16_tool_registry, before _18_memory_catalog)
Hook: before_main_llm_call
Pattern: prepend to last user message in loop_data.history_output

Spec: specs/LIBRARY_SPEC_L3.md
"""

import json
import os

from python.helpers.extension import Extension
from agent import LoopData

CATALOG_PATH           = "/a0/usr/library/catalog.json"
MAX_INLINE_COLLECTIONS = 15


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
        return {"collections": {}, "documents": []}
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"collections": {}, "documents": []}


def _build_block() -> str:
    catalog     = _load_catalog()
    collections = catalog.get("collections", {})
    documents   = catalog.get("documents", [])

    if not documents:
        return ""

    total_books = len(documents)
    total_cols  = len(collections)

    sorted_cols = sorted(collections.values(), key=lambda c: c.get("name", ""))
    shown       = sorted_cols[:MAX_INLINE_COLLECTIONS]

    header = (
        f"[LIBRARY — {total_books} book(s) in {total_cols} collection(s); "
        f"use library_search, library_list, or library_collections]"
    )
    lines = [header]

    for col in shown:
        col_id  = col.get("collection_id", "")
        name    = col.get("name", "")[:35]
        count   = col.get("book_count", len(col.get("book_ids", [])))
        summary = col.get("summary", "")[:80]
        lines.append(f"  {col_id} | {name} ({count} books) | {summary}")

    if total_cols > MAX_INLINE_COLLECTIONS:
        hidden = total_cols - MAX_INLINE_COLLECTIONS
        lines.append(f"  (+{hidden} more collections — use library_collections for full list)")

    lines.append("[/LIBRARY]")

    n = min(total_cols, MAX_INLINE_COLLECTIONS)
    print(f"[LIB-CAT] Injected {n}/{total_cols} collections ({total_books} books) into context", flush=True)
    return "\n".join(lines)


def _get_last_user_message(history: list) -> dict | None:
    if not history:
        return None
    for msg in reversed(history):
        if not msg.get("ai", True):
            return msg
    return None
