"""
Memory Catalog — Session Start Injection
=========================================
Hook: before_main_llm_call (_18_)

Injects a compact catalog of what's in memory at the start of each session —
once only, before the first LLM call. Addresses "library without a catalog":
the agent can't effectively query memory without knowing what domains and
topics are stored.

What it injects:
    [MEMORY CATALOG — session start]
    380 fragments across 12 domains. Top domains:
      git_ops (66) | codegen (54) | agentic (53) | ...
    Most recent:
      · "system uses litellm for LLM interactions..."
      · "loop detection requires different tool call..."

Gate: only fires once per session (per agent instance). Does nothing if
      memory is empty or inaccessible.

No LLM calls. Reads only — no writes to the memory store.
"""

from collections import Counter
from typing import Optional

from agent import LoopData
from python.helpers.extension import Extension
from python.helpers.memory import Memory

# Per-agent flag — set after first injection
_CATALOG_ATTR = "_memory_catalog_built"


class MemoryCatalog(Extension):
    """Inject memory domain catalog once at session start."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            # Once per session — skip if already injected
            if getattr(self.agent, _CATALOG_ATTR, False):
                return

            # Find the user message to prepend to
            user_msg = _get_last_user_message(loop_data.history_output)
            if not user_msg:
                return

            catalog = _build_catalog(self.agent)
            if not catalog:
                self.agent.__dict__[_CATALOG_ATTR] = True
                return

            existing = user_msg.get("content", "")
            user_msg["content"] = catalog + "\n\n" + str(existing)

            self.agent.__dict__[_CATALOG_ATTR] = True

            print("[MEM-CAT] Memory catalog injected.", flush=True)
            try:
                self.agent.context.log.log(type="info", content="[MEM-CAT] Memory catalog injected.")
            except Exception:
                pass

        except Exception:
            pass


# ── Catalog Builder ────────────────────────────────────────────────────────────

def _build_catalog(agent) -> str:
    """Read memory store and build compact domain summary."""
    try:
        memory = Memory.get(agent)
        all_docs = memory.db.get_all_docs()

        # Filter to episodic fragments (not raw knowledge imports)
        frags = [
            v for v in all_docs.values()
            if v.metadata.get("area") == "fragments"
        ]

        if not frags:
            return ""

        # Count by BST domain from lineage metadata
        domains = Counter(
            (v.metadata.get("lineage") or {}).get("bst_domain") or "unclassified"
            for v in frags
        )

        total = len(frags)
        top_domains = sorted(domains.items(), key=lambda x: -x[1])[:8]

        # Most recent 3 entries by timestamp
        def _ts(doc):
            return (doc.metadata.get("timestamp") or "") or (
                (doc.metadata.get("lineage") or {}).get("created_at") or ""
            )

        recent = sorted(frags, key=_ts, reverse=True)[:3]
        snippets = [str(doc.page_content)[:80].replace("\n", " ").strip() for doc in recent]

        lines = ["[MEMORY CATALOG — session start]"]
        domain_str = " | ".join(f"{d} ({c})" for d, c in top_domains)
        lines.append(f"{total} fragments across {len(domains)} domains: {domain_str}")
        if snippets:
            lines.append("Most recent:")
            for s in snippets:
                lines.append(f"  · {s}...")

        return "\n".join(lines)

    except Exception:
        return ""


# ── Message Extraction ─────────────────────────────────────────────────────────

def _get_last_user_message(history_output: list) -> Optional[dict]:
    """Find the last operator message in loop history."""
    if not history_output:
        return None
    for msg in reversed(history_output):
        if not isinstance(msg, dict):
            continue
        if not msg.get("ai", True):
            content = msg.get("content", "")
            if isinstance(content, dict) and "user_message" in content:
                return msg
            if isinstance(content, str) and content:
                return msg
    return None
