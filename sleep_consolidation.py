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
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Ensure Exocortex module path is available
_EXOCORTEX_PATH = "/a0/usr/Exocortex"
if _EXOCORTEX_PATH not in sys.path:
    sys.path.insert(0, _EXOCORTEX_PATH)


# ── Public API ───────────────────────────────────────────────────────────────

def stage_journal_observations(
    max_lookback: int = 50,
    journal_path: str = "/a0/usr/workdir/workspace/self-improvement/journal.jsonl",
    staging_path: str = "/a0/usr/Exocortex/staging.jsonl",
) -> dict:
    """Break A (DEC-042): mine recent cycle_close journal entries for real
    findings and stage them as observations.

    The idle self-improvement workload runs short cycles that almost never
    trigger the context-compression event _49 needs to write reasoning-state
    observations — so staging starved (~1 observation vs ~328 artifacts) and
    the promotion loop had no fuel. The journal already holds the agent's
    distilled per-cycle learning; this stages the cycles where the agent
    noticed something about ITSELF (sleep-consolidation findings, captured
    skills, integrity issues, non-clean status) as observations, deduped by
    cycle_number.

    Staged at reactivation_count=0; they become promotion-eligible once
    session_init surfaces them (Break B increments the count). The journal
    path is the LIVE one (/a0/usr/workdir/workspace/...), not the stale
    /a0/usr/Exocortex copy. Deterministic, no LLM calls.
    """
    JOURNAL_PATH = journal_path
    STAGING_PATH = staging_path
    OBS_IMPORTANCE = 0.7
    OK_STATUSES = ("completed", "complete", "ok", "success", "")

    result = {"staged": 0, "skipped_existing": 0, "scanned": 0}
    if not os.path.exists(JOURNAL_PATH):
        return result

    # Existing staging lines + already-staged cycle numbers (dedup)
    existing_lines: List[str] = []
    staged_cycles = set()
    if os.path.exists(STAGING_PATH):
        with open(STAGING_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                existing_lines.append(line)
                try:
                    e = json.loads(line)
                    if e.get("_journal_cycle") is not None:
                        staged_cycles.add(e["_journal_cycle"])
                except json.JSONDecodeError:
                    pass

    # Recent journal entries
    entries: List[dict] = []
    try:
        with open(JOURNAL_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except Exception:
        return result
    entries = entries[-max_lookback:]

    new_lines: List[str] = []
    for e in entries:
        result["scanned"] += 1
        if e.get("type") != "cycle_close":
            continue
        cyc = e.get("cycle_number")
        if cyc is None:
            continue
        if cyc in staged_cycles:
            result["skipped_existing"] += 1
            continue

        sleep_f = e.get("sleep_findings", 0) or 0
        skills = e.get("skills_captured", 0) or 0
        integ = e.get("integrity_issues", 0) or 0
        status = str(e.get("status", "")).lower()
        qualifies = (sleep_f > 0 or skills > 0 or integ > 0
                     or status not in OK_STATUSES)
        if not qualifies:
            continue

        # created = the cycle's own timestamp (unique per cycle) for stable
        # keying by Break B's (created, text) match.
        try:
            created = datetime.fromisoformat(e["timestamp"]).timestamp()
        except Exception:
            created = datetime.now().timestamp()

        obs = {
            "id": f"journal_cycle_{cyc}",
            "category": "observation",
            "status": "active",
            "text": str(e.get("activity", ""))[:500],
            "why": (f"Cycle {cyc} ({e.get('cycle_type', '?')}) finding — "
                    f"sleep_findings={sleep_f}, skills_captured={skills}, "
                    f"integrity_issues={integ}, status={status or 'unknown'}"),
            "importance": OBS_IMPORTANCE,
            "reactivation_count": 0,
            "created": created,
            "_journal_cycle": cyc,
        }
        new_lines.append(json.dumps(obs))
        staged_cycles.add(cyc)
        result["staged"] += 1

    if new_lines:
        try:
            with open(STAGING_PATH, "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(existing_lines + new_lines) + "\n")
        except Exception:
            result["staged"] = 0
    return result


def run_phase0_consolidation(session_id: str = "unknown") -> dict:
    """
    Phase 0 — Staging Tier Lifecycle Management.

    Reviews staging.jsonl and applies promotion, archival, or carry-forward
    decisions to active entries. Runs before Phase 1 so promoted observations
    are available as new procedural memory entries during Phase 1 dedup.

    Promotion criteria (Tononi & Cirelli 2014 — selective consolidation):
      1. Outcome valence / importance score (heuristic assigned at write time)
      2. Reactivation count (was this observation referenced again?)
      3. Category — relational entries never auto-archived
      4. Age — canary entries older than MAX_CANARY_AGE_TURNS are archived

    Destinations:
      observation (importance >= 0.6, reactivation >= 1) → procedural memory
      relational  (all active)                           → persist + score boost
      intention   (all active)                           → carry forward
      canary      (age > MAX_CANARY_AGE_TURNS, no CUSUM fire) → archive
    """
    STAGING_PATH = "/a0/usr/Exocortex/staging.jsonl"
    PROMOTE_IMPORTANCE = 0.6
    PROMOTE_REACTIVATION = 1
    MAX_CANARY_AGE_TURNS = 30  # archive canaries that never fired within ~30 agent turns

    result = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "phase": "Phase 0 - Staging Lifecycle",
        "observations_promoted": 0,
        "intentions_carried": 0,
        "relationals_anchored": 0,
        "canaries_archived": 0,
        "total_active": 0,
        "errors": 0,
        "journal_observations_staged": 0,
    }

    # Break A (DEC-042): mine the cycle journal for findings and stage them as
    # observations BEFORE reviewing staging for promotion. Feeds the promotion
    # loop in the idle workload, where compression-triggered observations from
    # _49 almost never fire.
    try:
        journal_staged = stage_journal_observations()
        result["journal_observations_staged"] = journal_staged["staged"]
    except Exception as e:
        print(f"[SLEEP] Phase 0 journal-mining failed (passthrough): {e}", flush=True)

    if not os.path.exists(STAGING_PATH):
        _write_sleep_report(result)
        return result

    # Load all entries
    entries = []
    try:
        with open(STAGING_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        result["errors"] += 1
    except Exception as e:
        print(f"[SLEEP] Phase 0 staging read failed: {e}", flush=True)
        _write_sleep_report(result)
        return result

    active_count = sum(1 for e in entries if e.get("status") == "active")
    result["total_active"] = active_count

    if active_count == 0:
        _write_sleep_report(result)
        return result

    promotions = []
    updated_entries = []

    for entry in entries:
        if entry.get("status") != "active":
            updated_entries.append(entry)
            continue

        category = entry.get("category", "observation")
        importance = entry.get("importance", 0.2)
        reactivations = entry.get("reactivation_count", 0)
        age_turns = entry.get("session_age_at_write", 0)

        if category == "observation":
            if importance >= PROMOTE_IMPORTANCE and reactivations >= PROMOTE_REACTIVATION:
                promotions.append({
                    "text": entry.get("text", ""),
                    "why": entry.get("why", ""),
                    "source_id": entry.get("id", ""),
                })
                entry["status"] = "promoted"
                entry["promoted_to"] = "procedural_memory"
                result["observations_promoted"] += 1
            # else: remain active, carry forward

        elif category == "relational":
            # Never auto-archive relational entries — increment consolidation score
            entry["consolidation_score"] = round(
                min(1.0, entry.get("consolidation_score", 0.0) + 0.1), 2
            )
            result["relationals_anchored"] += 1

        elif category == "intention":
            result["intentions_carried"] += 1
            # Remain active — session_init will surface them

        elif category == "canary":
            if age_turns > MAX_CANARY_AGE_TURNS:
                entry["status"] = "archived"
                result["canaries_archived"] += 1
            # else remain active

        updated_entries.append(entry)

    # Write back updated statuses
    try:
        with open(STAGING_PATH, "w", encoding="utf-8") as f:
            for e in updated_entries:
                f.write(json.dumps(e) + "\n")
    except Exception as e:
        print(f"[SLEEP] Phase 0 staging write-back failed: {e}", flush=True)
        result["errors"] += 1

    # Write promoted observations to procedural memory
    if promotions:
        try:
            from procedural_memory_api import ProceduralMemory
            pm = ProceduralMemory()
            for p in promotions:
                pm.create_anti_pattern(
                    failing_tool="staging_observation",
                    domain="agent_observation",
                    consecutive=1,
                    pre_action_check=f"{p['text']} (why: {p['why']})",
                    session_id=session_id,
                    tags=["staging", "agent_observation", "promoted"],
                )
        except Exception as e:
            print(f"[SLEEP] Phase 0 procedural write failed: {e}", flush=True)
            result["errors"] += 1

    _write_sleep_report(result)
    return result


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
        "fuzzy_duplicates_removed": 0,
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

    # --- Operation 2b: Fuzzy dedup near-duplicate anti-patterns ---
    # Catches naming variations not caught by exact hash:
    #   e.g. "system_admin" ≈ "system_administration", "code_execution" ≈ "code_execution_tool"
    # Requires rapidfuzz; skips gracefully if not installed.
    try:
        from rapidfuzz import fuzz as _fuzz
        _fuzzy_available = True
    except ImportError:
        _fuzzy_available = False

    if _fuzzy_available:
        survivors = [
            s for s in pm.index["skills"]
            if s.get("type") == "ANTI-PATTERN"
        ]

        def _ap_sig(entry):
            return f"{entry.get('failing_tool', '')}:{entry.get('domain', '')}"

        FUZZY_THRESHOLD = 85
        merged_indices: set = set()

        for i, a in enumerate(survivors):
            if i in merged_indices:
                continue
            sig_a = _ap_sig(a)
            for j in range(i + 1, len(survivors)):
                if j in merged_indices:
                    continue
                b = survivors[j]
                sig_b = _ap_sig(b)
                if sig_a == sig_b:
                    continue  # already handled by exact-hash pass
                if _fuzz.ratio(sig_a, sig_b) >= FUZZY_THRESHOLD:
                    # Merge b into a: keep highest consecutive, union tags
                    if b.get("consecutive", 0) > a.get("consecutive", 0):
                        a["consecutive"] = b["consecutive"]
                        a["pre_action_check"] = b.get("pre_action_check", a.get("pre_action_check", ""))
                    a["tags"] = list(dict.fromkeys(
                        (a.get("tags") or []) + (b.get("tags") or [])
                    ))
                    merged_indices.add(j)

        for idx in sorted(merged_indices, reverse=True):
            entry = survivors[idx]
            filepath = entry.get("filepath", "")
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass
            try:
                pm.index["skills"].remove(entry)
                result["fuzzy_duplicates_removed"] += 1
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


# ── Phase 4: Loop-Period Memory Adjudication ─────────────────────────────────

AMBIGUITY_ESCAPE_THRESHOLD = 3  # Force resolution after this many ambiguous evaluations

_FACT_PATTERNS = [
    re.compile(r"\b(exists?|found|not found|missing|present|absent)\b", re.IGNORECASE),
    re.compile(r"\b(error|returns?|responded?|status)\s+\d{3}\b", re.IGNORECASE),
    re.compile(r"\b(file|path|directory|endpoint)\b.{0,40}\b(exists?|not found|missing)\b", re.IGNORECASE),
]
_ATTEMPT_PATTERNS = [
    re.compile(r"\b(tried?|attempt|retry|retried|trying)\b", re.IGNORECASE),
    re.compile(r"\b(failed?|failing)\s+(again|repeatedly|multiple)\b", re.IGNORECASE),
    re.compile(r"\bconsecutive\b", re.IGNORECASE),
]


async def run_phase4_consolidation(agent, session_id: str = "unknown") -> dict:
    """
    Phase 4 consolidation — loop-period memory adjudication.

    Reviews all memories tagged with validity: loop_period and applies one of:
    - Promote to validity: inferred  (contains verifiable fact assertion)
    - Deprecate permanently          (describes agent attempt / retry pattern)
    - Leave as loop_period           (ambiguous — suppressed at retrieval, reviewed next sleep)

    Design: LOOP_RECOVERY_AND_MEMORY_SURGERY_SPEC_L3.md, File 5.
    No LLM calls. Deterministic regex pattern matching.
    """
    result = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "phase": "Phase 4 - Loop-Period Memory Adjudication",
        "loop_period_found": 0,
        "promoted_to_inferred": 0,
        "deprecated": 0,
        "left_ambiguous": 0,
        "errors": 0,
    }

    try:
        from plugins._memory.helpers.memory import Memory
        db = await Memory.get(agent)
        if not db or not db.db:
            _write_sleep_report(result)
            return result

        all_docs = db.db.get_all_docs()
        if not all_docs:
            _write_sleep_report(result)
            return result

        changed = 0
        for doc_id, doc in all_docs.items():
            if not hasattr(doc, "metadata"):
                continue
            cls = doc.metadata.get("classification", {})
            if cls.get("validity") != "loop_period":
                continue

            result["loop_period_found"] += 1
            text = getattr(doc, "page_content", "")

            is_attempt = any(p.search(text) for p in _ATTEMPT_PATTERNS)
            is_fact    = any(p.search(text) for p in _FACT_PATTERNS)

            if is_attempt and not is_fact:
                cls["validity"] = "deprecated"
                doc.metadata["classification"] = cls
                result["deprecated"] += 1
                changed += 1
            elif is_fact and not is_attempt:
                cls["validity"] = "inferred"
                lin = doc.metadata.get("lineage", {})
                lin["loop_period_promoted"] = True
                doc.metadata["lineage"] = lin
                doc.metadata["classification"] = cls
                result["promoted_to_inferred"] += 1
                changed += 1
            else:
                count = cls.get("ambiguity_count", 0) + 1
                cls["ambiguity_count"] = count
                doc.metadata["classification"] = cls
                changed += 1  # persist counter even when below threshold
                if count >= AMBIGUITY_ESCAPE_THRESHOLD:
                    # Force resolution: attempt wins over fact when both match (or neither)
                    if is_attempt:
                        cls["validity"] = "deprecated"
                        result["deprecated"] += 1
                    else:
                        cls["validity"] = "inferred"
                        lin = doc.metadata.get("lineage", {})
                        lin["loop_period_promoted"] = True
                        doc.metadata["lineage"] = lin
                        result["promoted_to_inferred"] += 1
                    doc.metadata["classification"] = cls
                    changed += 1
                    print(
                        f"[SLEEP] Phase 4 forced resolution (ambiguity_count={count}): "
                        f"validity={cls['validity']}",
                        flush=True,
                    )
                else:
                    result["left_ambiguous"] += 1
                    # Leave as loop_period — retrieval still suppressed

        if changed:
            try:
                db._save_db()
            except Exception as e:
                result["errors"] += 1
                print(f"[SLEEP] Phase 4 save error: {e}", flush=True)

        print(
            f"[SLEEP] Loop-period adjudication: found={result['loop_period_found']}, "
            f"promoted={result['promoted_to_inferred']}, deprecated={result['deprecated']}, "
            f"ambiguous={result['left_ambiguous']}",
            flush=True,
        )

    except Exception as e:
        result["errors"] += 1
        print(f"[SLEEP] Phase 4 error: {e}", flush=True)

    _write_sleep_report(result)
    return result


# ── Phase 5: AgentEvolver Experience Integration ──────────────────────────────

_AGENTEVOLVER_PLUGIN_DIR = "/a0/usr/plugins/agentevolver_self_improvement"


def run_phase5_consolidation(session_id: str = "unknown", phase2_result: Optional[dict] = None) -> dict:
    """
    Phase 5 consolidation — AgentEvolver experience integration.

    Converts sleep-cycle findings into SelfImprovementEngine experiences.
    Two sources:
      1. Anti-patterns captured by Phase 2 this session → failure experiences.
         Lessons = the pre_action_check from the anti-pattern.
      2. Phase 4 deprecated loop-period memories (if phase2_result provided) →
         note the failure type in task_description for context.

    No LLM calls. Deterministic read of this session's procedural memory entries.
    Silently skips if the AgentEvolver plugin is unavailable.
    """
    result = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "phase": "Phase 5 - AgentEvolver Experience Integration",
        "experiences_recorded": 0,
        "engine_unavailable": False,
        "errors": 0,
    }

    # --- Load the SelfImprovementEngine ---
    helpers_path = os.path.join(_AGENTEVOLVER_PLUGIN_DIR, "helpers")
    if helpers_path not in sys.path:
        sys.path.insert(0, helpers_path)

    try:
        from self_improvement import SelfImprovementEngine  # type: ignore
        engine = SelfImprovementEngine(Path(_AGENTEVOLVER_PLUGIN_DIR))
    except Exception as e:
        result["engine_unavailable"] = True
        result["errors"] += 1
        print(f"[SLEEP] Phase 5 engine load failed (plugin missing?): {e}", flush=True)
        _write_sleep_report(result)
        return result

    # --- Source 1: anti-patterns captured by Phase 2 this session ---
    try:
        from procedural_memory_api import ProceduralMemory  # type: ignore
        pm = ProceduralMemory()

        new_patterns = [
            s for s in pm.index.get("skills", [])
            if s.get("type") == "ANTI-PATTERN"
            and s.get("session_id") == session_id
            and any("sleep-phase2" in tag for tag in s.get("tags", []))
        ]

        for pattern in new_patterns:
            tool = pattern.get("failing_tool", "unknown")
            domain = pattern.get("domain", "general")
            pre_check = pattern.get("pre_action_check", "").strip()
            lessons = [pre_check] if pre_check else [f"Avoid repeated {tool} calls without state change"]
            consecutive = pattern.get("consecutive", 3)

            engine.add_experience(
                task_type=domain,
                task_description=(
                    f"Agent looped on tool '{tool}' in domain '{domain}' "
                    f"({consecutive} consecutive calls) — captured by sleep Phase 2."
                ),
                actions=[f"called '{tool}' {consecutive}+ times without progress"],
                outcome="failure",
                lessons_learned=lessons,
            )
            result["experiences_recorded"] += 1

    except Exception as e:
        result["errors"] += 1
        print(f"[SLEEP] Phase 5 anti-pattern read error: {e}", flush=True)

    summary_msg = (
        f"Phase 5 — experiences_recorded={result['experiences_recorded']}, "
        f"errors={result['errors']}"
        + (" (engine unavailable)" if result["engine_unavailable"] else "")
    )
    print(f"[SLEEP] {summary_msg}", flush=True)

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
