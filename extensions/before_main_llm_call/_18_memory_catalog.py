"""
Memory Catalog — Session Start Injection
=========================================
Hook: before_main_llm_call (_18_)

Injects a compact catalog of what's in memory at the start of each session —
once only, before the first LLM call. Addresses "library without a catalog":
the agent can't effectively query memory without knowing what domains and
topics are stored.

Covers two memory systems:

1. Episodic memory (FAISS fragments):
    [MEMORY CATALOG — session start]
    380 fragments across 12 domains. Top domains:
      git_ops (66) | codegen (54) | agentic (53) | ...
    Most recent:
      · "system uses litellm for LLM interactions..."

2. Procedural memory (sleep-built skills + anti-patterns):
    [PROCEDURAL MEMORY — 5 entries]
      Skills (2): Docker Network Debugging | ...
      Anti-patterns (3): unknown/bugfix (loop:4x) | unknown/analysis (loop:4x) | ...
    [SLEEP — last run 14 Mar 22:39]
      Phase 1: 5 entries, 0 duplicates removed | Phase 3: operator profile updated

Gate: only fires once per session (per agent instance). Does nothing if
      both memory stores are empty or inaccessible.

No LLM calls. Reads only — no writes to either memory store.
"""

import json
import os
from collections import Counter
from datetime import datetime
from typing import Optional

from agent import LoopData
from python.helpers.extension import Extension
from python.helpers.memory import Memory

# Per-agent flag — set after first injection
_CATALOG_ATTR = "_memory_catalog_built"

PROCEDURAL_INDEX = "/a0/usr/Exocortex/procedural_memory/.index.json"
SLEEP_REPORTS_DIR = "/a0/usr/Exocortex/sleep_reports"


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

            parts = []

            episodic = await _build_episodic_catalog(self.agent)
            if episodic:
                parts.append(episodic)

            procedural = _build_procedural_catalog()
            if procedural:
                parts.append(procedural)

            if not parts:
                self.agent.__dict__[_CATALOG_ATTR] = True
                return

            catalog = "\n\n".join(parts)
            existing = user_msg.get("content", "")
            user_msg["content"] = catalog + "\n\n" + str(existing)

            self.agent.__dict__[_CATALOG_ATTR] = True

            print("[MEM-CAT] Memory catalog injected.", flush=True)
            try:
                self.agent.context.log.log(type="util", content="[MEM-CAT] Memory catalog injected.")
            except Exception:
                pass

        except Exception:
            pass


# ── Episodic Catalog (FAISS fragments) ─────────────────────────────────────────

async def _build_episodic_catalog(agent) -> str:
    """Read FAISS memory store and build compact domain summary."""
    try:
        memory = await Memory.get(agent)
        all_docs = memory.db.get_all_docs()

        frags = [
            v for v in all_docs.values()
            if v.metadata.get("area") == "fragments"
        ]

        if not frags:
            return ""

        domains = Counter(
            (v.metadata.get("lineage") or {}).get("bst_domain") or "unclassified"
            for v in frags
        )

        total = len(frags)
        top_domains = sorted(domains.items(), key=lambda x: -x[1])[:8]

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


# ── Procedural Catalog (sleep-built skills + anti-patterns) ────────────────────

def _build_procedural_catalog() -> str:
    """Read procedural memory index and recent sleep reports."""
    try:
        proc_section = _read_procedural_index()
        sleep_section = _read_recent_sleep()

        if not proc_section and not sleep_section:
            return ""

        parts = []
        if proc_section:
            parts.append(proc_section)
        if sleep_section:
            parts.append(sleep_section)
        return "\n".join(parts)

    except Exception:
        return ""


def _read_procedural_index() -> str:
    """Build compact procedural memory summary from .index.json."""
    try:
        if not os.path.exists(PROCEDURAL_INDEX):
            return ""

        with open(PROCEDURAL_INDEX, "r", encoding="utf-8") as f:
            index = json.load(f)

        skills_all = index.get("skills", [])
        if not skills_all:
            return ""

        skills = [s for s in skills_all if s.get("type") != "ANTI-PATTERN"]
        anti_patterns = [s for s in skills_all if s.get("type") == "ANTI-PATTERN"]

        total = len(skills_all)
        lines = [f"[PROCEDURAL MEMORY — {total} entries]"]

        if skills:
            names = " | ".join(s.get("name", "?")[:50] for s in skills[:5])
            lines.append(f"  Skills ({len(skills)}): {names}")

        if anti_patterns:
            ap_strs = []
            for ap in anti_patterns[:6]:
                tool = ap.get("failing_tool", "?")
                domain = ap.get("domain", "?")
                loop_n = ap.get("consecutive", 0)
                ap_strs.append(f"{tool}/{domain} (loop:{loop_n}x)")
            lines.append(f"  Anti-patterns ({len(anti_patterns)}): {' | '.join(ap_strs)}")

        return "\n".join(lines)

    except Exception:
        return ""


def _read_recent_sleep() -> str:
    """Summarize the most recent sleep run from report files."""
    try:
        if not os.path.isdir(SLEEP_REPORTS_DIR):
            return ""

        files = sorted([
            f for f in os.listdir(SLEEP_REPORTS_DIR)
            if f.startswith("sleep_") and f.endswith(".json")
        ])
        if not files:
            return ""

        # Read the last 4 reports (one sleep run generates 2-3 phases)
        recent_files = files[-4:]
        phases = []
        for fname in recent_files:
            try:
                with open(os.path.join(SLEEP_REPORTS_DIR, fname), "r", encoding="utf-8") as f:
                    phases.append(json.load(f))
            except Exception:
                continue

        if not phases:
            return ""

        # Deduplicate — keep only the most recent report per phase name
        seen_phases: dict = {}
        for p in phases:
            seen_phases[p.get("phase", "")] = p
        phases = list(seen_phases.values())

        # Use timestamp from the last report for "last run" label
        last_ts = phases[-1].get("timestamp", "")
        try:
            dt = datetime.fromisoformat(last_ts)
            label = dt.strftime("%-d %b %H:%M")
        except Exception:
            label = last_ts[:16]

        # Build per-phase summary
        summaries = []
        for p in phases:
            phase_name = p.get("phase", "")
            if "Phase 1" in phase_name:
                removed = p.get("duplicates_removed", 0)
                total = p.get("total_entries_after", p.get("total_entries_before", 0))
                summaries.append(f"Phase 1: {total} entries, {removed} duplicates removed")
            elif "Phase 2" in phase_name:
                chunked = p.get("episodes_chunked", 0)
                captured = p.get("anti_patterns_captured", 0)
                summaries.append(f"Phase 2: {chunked} episodes chunked, {captured} anti-patterns captured")
            elif "Phase 3" in phase_name:
                updated = p.get("profile_updated", False)
                sessions = p.get("sessions_analyzed", 0)
                summaries.append(f"Phase 3: operator profile {'updated' if updated else 'unchanged'} ({sessions} sessions)")

        if not summaries:
            return ""

        lines = [f"[SLEEP — last run {label}]"]
        lines.append("  " + " | ".join(summaries))
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
