"""
sleep_consolidation.py — Exocortex Sleep Consolidation Engine

Phase 1: Procedural memory deduplication + utility counter initialization.
Phase 2: Episode chunking + missed anti-pattern capture.
Phase 3: Operator interaction modeling — learns communication patterns and
         maintains operator_profile.json.

Called by the sleep trigger extension after idle timeout.
No LLM calls — purely deterministic operations.

This module lives at /a0/usr/Exocortex/sleep_consolidation.py (alongside
procedural_memory_api.py). Both are imported via sys.path from within the
Agent Zero container.

Called from: extensions/tool_execute_after/_60_sleep_trigger.py
Storage: /a0/usr/Exocortex/procedural_memory/ (reads + writes)
Reports: /a0/usr/Exocortex/sleep_reports/ (write-only)
Profile: /a0/usr/Exocortex/operator_profile.json (write)
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Ensure Exocortex module path is available
_EXOCORTEX_PATH = "/a0/usr/Exocortex"
if _EXOCORTEX_PATH not in sys.path:
    sys.path.insert(0, _EXOCORTEX_PATH)


# ── Public API ───────────────────────────────────────────────────────────────

def run_phase1_consolidation(session_id: str = "unknown") -> dict:
    """
    Phase 1 consolidation — two deterministic operations:

    1. Initialize utility fields (utility_score, use_count, last_used) on all
       procedural memory entries that don't have them yet.

    2. Deduplicate anti-patterns by problem_pattern_hash — same tool+domain
       pattern that was captured multiple times collapses into one entry,
       retaining the highest consecutive count observed.

    Returns a summary dict that the trigger logs and writes to the report dir.
    """
    from procedural_memory_api import ProceduralMemory

    pm = ProceduralMemory()

    result = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "phase": "Phase 1 - Self-Consolidation",
        "utility_fields_initialized": 0,
        "duplicates_removed": 0,
        "groups_processed": 0,
        "total_entries_before": len(pm.index["skills"]),
        "total_entries_after": 0,
    }

    changed = False

    # --- Operation 1: Initialize utility metadata on all entries ---
    for entry in pm.index["skills"]:
        if "utility_score" not in entry:
            entry["utility_score"] = 1.0      # neutral starting score
            entry["use_count"] = 0
            entry["last_used"] = None
            result["utility_fields_initialized"] += 1
            changed = True

    # --- Operation 2: Deduplicate anti-patterns by problem_pattern_hash ---
    anti_patterns = [
        s for s in pm.index["skills"]
        if s.get("type") == "ANTI-PATTERN" and s.get("problem_pattern_hash")
    ]

    groups: Dict[str, List[dict]] = {}
    for ap in anti_patterns:
        h = ap["problem_pattern_hash"]
        groups.setdefault(h, []).append(ap)

    result["groups_processed"] = len(groups)

    for h, entries in groups.items():
        if len(entries) <= 1:
            continue

        # Keep the entry with highest consecutive count (captures the worst observed loop)
        best = max(entries, key=lambda e: e.get("consecutive", 0))
        # Promote the peak consecutive count so the surviving entry reflects worst case
        best["consecutive"] = max(e.get("consecutive", 0) for e in entries)

        to_remove = [e for e in entries if e is not best]
        for entry in to_remove:
            filepath = entry.get("filepath", "")
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass
            try:
                pm.index["skills"].remove(entry)
                result["duplicates_removed"] += 1
                changed = True
            except ValueError:
                pass

    result["total_entries_after"] = len(pm.index["skills"])

    if changed:
        pm._save_index()

    # --- Operation 3: Write sleep report ---
    _write_sleep_report(result)

    return result


def run_phase2_consolidation(session_id: str = "unknown") -> dict:
    """
    Phase 2 consolidation — episode chunking + missed anti-pattern capture:

    1. Load the 3 most recent sessions from /a0/usr/chats/.
    2. Chunk each into episodes (operator message → response tool call).
    3. Find episodes with supervisor loop warnings.
    4. For each loop pattern, check if an anti-pattern already exists in
       procedural memory (Tier 4 may have captured it in real time).
    5. Capture any that Tier 4 missed — specifically loops broken by operator
       intervention rather than by the agent self-resolving.

    Returns a summary dict logged and written to the report dir.
    """
    from procedural_memory_api import ProceduralMemory
    from sleep_episode_chunker import (
        load_recent_sessions,
        chunk_session,
        extract_loop_patterns,
    )

    result = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "phase": "Phase 2 - Episode Chunking + Missed Anti-Pattern Capture",
        "sessions_analyzed": 0,
        "episodes_chunked": 0,
        "loop_patterns_found": 0,
        "anti_patterns_captured": 0,
        "already_covered": 0,
    }

    pm = ProceduralMemory()
    sessions = load_recent_sessions(n=3)
    result["sessions_analyzed"] = len(sessions)

    all_episodes = []
    for session in sessions:
        episodes = chunk_session(session)
        all_episodes.extend(episodes)
    result["episodes_chunked"] = len(all_episodes)

    patterns = extract_loop_patterns(all_episodes)
    result["loop_patterns_found"] = len(patterns)

    for pattern in patterns:
        failing_tool = pattern["failing_tool"]
        domain = pattern.get("domain", "unknown")
        consecutive = pattern.get("consecutive", 3)

        # Check if this tool+domain pair is already in procedural memory
        existing = pm.search_by_tags(
            tags=[failing_tool],
            type_filter="ANTI-PATTERN",
        )
        if existing:
            result["already_covered"] += 1
            continue

        # Tier 4 missed this one — capture it now
        pre_check = (
            f"Before calling '{failing_tool}': verify the tool can handle the "
            f"input in this context."
        )
        source = "sleep-phase2-operator-interrupted" if pattern.get("operator_intervened") else "sleep-phase2"
        pm.create_anti_pattern(
            failing_tool=failing_tool,
            domain=domain,
            consecutive=consecutive,
            pre_action_check=pre_check,
            session_id=session_id,
            tags=[failing_tool, domain, "loop-recovery", source],
        )
        result["anti_patterns_captured"] += 1

    _write_sleep_report(result)
    return result


def run_phase3_consolidation(session_id: str = "unknown") -> dict:
    """
    Phase 3 consolidation — operator interaction modeling:

    1. Load the 3 most recent sessions (reusing the episode chunker's loader).
    2. Extract interaction metrics: turn lengths, floor-giving events,
       correction signals, intervention patterns.
    3. Merge metrics into the persistent operator profile using exponential
       smoothing (α=0.3), preserving human-readable, editable JSON.

    Returns a summary dict logged and written to the report dir.
    OBSERVE AND RECORD ONLY — no behavioral changes in this phase.
    """
    from sleep_episode_chunker import load_recent_sessions
    from sleep_interaction_analyzer import analyze_sessions, update_operator_profile

    result = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "phase": "Phase 3 - Operator Interaction Modeling",
        "sessions_analyzed": 0,
        "avg_operator_turn_length": 0,
        "floor_giving_rate": 0,
        "avg_corrections": 0,
        "profile_updated": False,
    }

    sessions = load_recent_sessions(n=3)
    result["sessions_analyzed"] = len(sessions)

    if not sessions:
        _write_sleep_report(result)
        return result

    aggregate = analyze_sessions(sessions)
    if not aggregate:
        _write_sleep_report(result)
        return result

    result["avg_operator_turn_length"] = aggregate.get("avg_operator_turn_length", 0)
    result["floor_giving_rate"] = aggregate.get("floor_giving_rate", 0)
    result["avg_corrections"] = aggregate.get("avg_corrections", 0)

    update_operator_profile(aggregate, len(sessions))
    result["profile_updated"] = True

    _write_sleep_report(result)
    return result


# ── Internal Helpers ─────────────────────────────────────────────────────────

def _write_sleep_report(result: dict):
    """Write the consolidation result as a JSON report file."""
    report_dir = "/a0/usr/Exocortex/sleep_reports"
    try:
        os.makedirs(report_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(report_dir, f"sleep_{ts}.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"[SLEEP] Report written: {report_path}", flush=True)
    except Exception as e:
        print(f"[SLEEP] Failed to write report: {e}", flush=True)
