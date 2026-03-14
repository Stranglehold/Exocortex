"""
sleep_interaction_analyzer.py — Exocortex Sleep Consolidation: Interaction Modeling

Analyzes the operator's communication patterns from session logs and maintains
a persistent operator profile. This is Phase 3 of the sleep consolidation
architecture — the component nobody else is building.

Every surveyed memory system (MemRL, mnemos, Mnemosyne) treats the agent as a
solo learner reviewing its own task performance. This module analyzes the
collaboration itself — how the operator communicates, when they intervene,
what their floor-giving phrases look like, how their turn length tracks with
task complexity.

Storage: /a0/usr/Exocortex/operator_profile.json
  Human-readable, editable, versioned.
  The operator can inspect and correct any learned pattern.
  Transparent nurture, not hidden adaptation.

This is Phase 3: OBSERVE AND RECORD ONLY.
Phase 4 (behavioral integration) gates all behavioral changes behind operator
approval. Nothing here modifies agent behavior.

No LLM calls — purely deterministic signal extraction from message text.
Called from: sleep_consolidation.run_phase3_consolidation()
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# ── Storage Path ─────────────────────────────────────────────────────────────

PROFILE_PATH = "/a0/usr/Exocortex/operator_profile.json"


# ── Floor-Giving Signals ──────────────────────────────────────────────────────
# Phrases where the operator explicitly hands the initiative to the agent.
# From SOUL.md: Jake uses "the floor is yours" as an explicit floor-giving phrase.

FLOOR_GIVING_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"the floor is yours",
        r"go ahead",
        r"run with it",
        r"your call",
        r"build (it|whatever|what)",
        r"I want you to (build|design|create|implement|write)",
        r"what do you think",
        r"up to you",
        r"whatever (you think|feels right|works)",
        r"I'll (let you|leave it to you)",
        r"proceed",
    ]
]


# ── Correction Signals ────────────────────────────────────────────────────────
# Phrases that typically signal the operator is redirecting or correcting.

CORRECTION_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"^actually[,\s]",
        r"^no[,\s]",
        r"^wait[,\s]",
        r"^hold on",
        r"^stop[,\s\.]",
        r"that'?s? (wrong|not right|incorrect|not what)",
        r"I meant",
        r"I mean ",
        r"no wait",
        r"not (quite|exactly)",
        r"let me (clarify|correct|rephrase)",
    ]
]


# ── Turn Length Thresholds ────────────────────────────────────────────────────

SHORT_TURN_CHARS = 50    # brief acknowledgment or single directive
LONG_TURN_CHARS  = 200   # detailed instruction or context provision


# ── Public API ───────────────────────────────────────────────────────────────

def analyze_sessions(sessions: List[Dict]) -> Dict:
    """
    Analyze a list of parsed sessions and return aggregate interaction metrics.
    Each session comes from sleep_episode_chunker.load_recent_sessions().
    """
    all_metrics = []
    for session in sessions:
        m = _analyze_session(session)
        if m:
            all_metrics.append(m)

    if not all_metrics:
        return {}

    return _aggregate_metrics(all_metrics)


def update_operator_profile(aggregate: Dict, sessions_analyzed: int) -> Dict:
    """
    Load the existing operator profile (or create a baseline) and merge in
    the new aggregate metrics. Writes the updated profile to PROFILE_PATH.

    Returns the updated profile dict.
    """
    profile = _load_profile()

    now = datetime.now().isoformat()

    # Update rolling averages with exponential smoothing (α=0.3)
    # New value = α * new + (1-α) * old. This lets recent sessions influence
    # the profile without letting one unusual session dominate.
    alpha = 0.3

    comm = profile.setdefault("communication_patterns", {})
    _smooth(comm, "avg_turn_length_chars",   aggregate.get("avg_operator_turn_length", 0),   alpha)
    _smooth(comm, "short_turn_rate",         aggregate.get("short_turn_rate", 0),             alpha)
    _smooth(comm, "long_turn_rate",          aggregate.get("long_turn_rate", 0),              alpha)
    _smooth(comm, "avg_turns_per_session",   aggregate.get("avg_operator_turns", 0),          alpha)

    floor = profile.setdefault("floor_giving", {})
    _smooth(floor, "frequency_per_session",  aggregate.get("floor_giving_rate", 0),           alpha)
    # Accumulate detected phrases (union, no duplicates)
    new_phrases = aggregate.get("floor_giving_phrases_seen", [])
    existing_phrases = floor.setdefault("detected_phrases", [])
    for phrase in new_phrases:
        if phrase not in existing_phrases:
            existing_phrases.append(phrase)

    interv = profile.setdefault("intervention_patterns", {})
    _smooth(interv, "avg_corrections_per_session", aggregate.get("avg_corrections", 0), alpha)
    # Correction-after-loop: does operator typically intervene during loops?
    interv["corrections_after_loop_rate"] = round(
        alpha * aggregate.get("corrections_after_loop_rate", 0)
        + (1 - alpha) * interv.get("corrections_after_loop_rate", 0),
        3,
    )
    # Typical correction position (early/mid/late — whichever is most common)
    pos = aggregate.get("typical_correction_position")
    if pos:
        interv["typical_correction_position"] = pos

    # Session history (keep last 20 entries)
    history = profile.setdefault("session_history", [])
    history.append({
        "analyzed_at": now,
        "sessions_in_batch": sessions_analyzed,
        "metrics_snapshot": {
            "avg_turn_length": aggregate.get("avg_operator_turn_length", 0),
            "short_turn_rate": aggregate.get("short_turn_rate", 0),
            "floor_giving_rate": aggregate.get("floor_giving_rate", 0),
            "avg_corrections": aggregate.get("avg_corrections", 0),
        },
    })
    if len(history) > 20:
        profile["session_history"] = history[-20:]

    profile["last_updated"] = now
    profile["sessions_analyzed_total"] = profile.get("sessions_analyzed_total", 0) + sessions_analyzed

    # Generate proposed behavioral changes for Phase 4 review
    profile["proposed_behavioral_changes"] = _build_proposed_changes(profile)
    profile["_promotion_note"] = (
        "Review proposed_behavioral_changes, edit as needed, then copy this file to "
        "operator_profile_approved.json to activate Phase 4 behavioral integration. "
        "Each promotion creates a versioned backup in operator_profile_versions/."
    )

    _save_profile(profile)
    return profile


def load_operator_profile() -> Dict:
    """Return the current operator profile, or an empty baseline."""
    return _load_profile()


# ── Internal: Per-Session Analysis ──────────────────────────────────────────

def _analyze_session(session: Dict) -> Optional[Dict]:
    """
    Extract interaction metrics from a single session's message list.
    Returns None if the session has no operator messages.
    """
    messages = session.get("messages", [])
    session_id = session.get("session_id", "unknown")

    operator_turns = []
    agent_turns = []
    corrections = 0
    floor_giving_events = []
    floor_giving_phrases_seen = []
    corrections_after_loop = 0
    correction_positions = []   # 0.0–1.0 normalized position within session

    total_msgs = len(messages)
    prev_was_loop_warning = False

    for i, msg in enumerate(messages):
        ai = msg.get("ai", False)
        content = msg.get("content", {})

        if isinstance(content, str):
            try:
                content = json.loads(content)
            except Exception:
                content = {"raw": content}

        if not ai:
            # ── Operator / system message ────────────────────────────────────
            if "user_message" in content:
                text = str(content["user_message"])
                turn_len = len(text)
                operator_turns.append(turn_len)

                # Floor-giving detection
                for pattern in FLOOR_GIVING_PATTERNS:
                    m = pattern.search(text)
                    if m:
                        floor_giving_events.append(i)
                        phrase = m.group(0).lower()[:40]
                        if phrase not in floor_giving_phrases_seen:
                            floor_giving_phrases_seen.append(phrase)
                        break

                # Correction detection
                for pattern in CORRECTION_PATTERNS:
                    if pattern.search(text):
                        corrections += 1
                        pos = i / total_msgs if total_msgs > 0 else 0.0
                        correction_positions.append(pos)
                        if prev_was_loop_warning:
                            corrections_after_loop += 1
                        break

                prev_was_loop_warning = False

            elif "system_warning" in content:
                warning = str(content["system_warning"])
                prev_was_loop_warning = "[SUPERVISOR]" in warning

        else:
            # ── Agent message ────────────────────────────────────────────────
            tool_name = content.get("tool_name", "")
            if tool_name == "response":
                text = str(content.get("tool_args", {}).get("text", ""))
                agent_turns.append(len(text))
            elif tool_name:
                agent_turns.append(0)  # tool calls are zero-length for this metric
            prev_was_loop_warning = False

    if not operator_turns:
        return None

    avg_op = sum(operator_turns) / len(operator_turns)
    short_rate = sum(1 for t in operator_turns if t < SHORT_TURN_CHARS) / len(operator_turns)
    long_rate  = sum(1 for t in operator_turns if t > LONG_TURN_CHARS)  / len(operator_turns)

    # Typical correction position: early (<0.33), mid (0.33–0.66), late (>0.66)
    typical_pos = None
    if correction_positions:
        avg_pos = sum(correction_positions) / len(correction_positions)
        typical_pos = "early" if avg_pos < 0.33 else ("late" if avg_pos > 0.66 else "mid")

    return {
        "session_id": session_id,
        "operator_turn_count": len(operator_turns),
        "avg_operator_turn_length": round(avg_op, 1),
        "short_turn_rate": round(short_rate, 3),
        "long_turn_rate":  round(long_rate, 3),
        "floor_giving_count": len(floor_giving_events),
        "floor_giving_phrases_seen": floor_giving_phrases_seen,
        "corrections": corrections,
        "corrections_after_loop": corrections_after_loop,
        "typical_correction_position": typical_pos,
    }


# ── Internal: Aggregation ────────────────────────────────────────────────────

def _aggregate_metrics(metrics_list: List[Dict]) -> Dict:
    """Aggregate per-session metrics into a single summary."""
    n = len(metrics_list)
    if n == 0:
        return {}

    def avg(key):
        vals = [m[key] for m in metrics_list if key in m]
        return round(sum(vals) / len(vals), 3) if vals else 0

    # Typical correction position: majority vote
    positions = [m["typical_correction_position"] for m in metrics_list if m.get("typical_correction_position")]
    typical_pos = max(set(positions), key=positions.count) if positions else None

    # Corrections after loop rate
    total_corrections = sum(m.get("corrections", 0) for m in metrics_list)
    corrections_after_loop = sum(m.get("corrections_after_loop", 0) for m in metrics_list)
    cal_rate = round(corrections_after_loop / total_corrections, 3) if total_corrections > 0 else 0.0

    # Floor-giving phrases: union across sessions
    all_phrases = []
    for m in metrics_list:
        for p in m.get("floor_giving_phrases_seen", []):
            if p not in all_phrases:
                all_phrases.append(p)

    return {
        "sessions_in_batch": n,
        "avg_operator_turns": avg("operator_turn_count"),
        "avg_operator_turn_length": avg("avg_operator_turn_length"),
        "short_turn_rate": avg("short_turn_rate"),
        "long_turn_rate":  avg("long_turn_rate"),
        "floor_giving_rate": avg("floor_giving_count"),
        "floor_giving_phrases_seen": all_phrases,
        "avg_corrections": avg("corrections"),
        "corrections_after_loop_rate": cal_rate,
        "typical_correction_position": typical_pos,
    }


# ── Internal: Profile I/O ─────────────────────────────────────────────────────

def _load_profile() -> Dict:
    """Load the profile from disk, or return a fresh baseline."""
    if os.path.exists(PROFILE_PATH):
        try:
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return {
        "_note": (
            "Auto-generated by Exocortex sleep consolidation Phase 3. "
            "Review and edit freely — this file is yours. "
            "Corrections here take precedence over learned values on next sleep cycle."
        ),
        "profile_version": "1.0",
        "created": datetime.now().isoformat(),
        "last_updated": None,
        "sessions_analyzed_total": 0,
        "communication_patterns": {},
        "floor_giving": {"detected_phrases": [], "frequency_per_session": 0},
        "intervention_patterns": {},
        "session_history": [],
    }


def _save_profile(profile: Dict):
    """Write the profile to disk."""
    try:
        os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)
        with open(PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)
        print(f"[SLEEP] Operator profile updated: {PROFILE_PATH}", flush=True)
    except Exception as e:
        print(f"[SLEEP] Failed to save operator profile: {e}", flush=True)


def _smooth(target: Dict, key: str, new_val: float, alpha: float):
    """Exponential smoothing update in place."""
    old = target.get(key, new_val)  # first time: old = new (no history bias)
    target[key] = round(alpha * new_val + (1 - alpha) * old, 3)


def _build_proposed_changes(profile: Dict) -> Dict:
    """
    Derive human-readable proposed behavioral changes from current profile metrics.
    Written into operator_profile.json as proposals; active only after promotion
    to operator_profile_approved.json (Phase 4 gate).
    """
    proposed = {}
    comm = profile.get("communication_patterns", {})
    interv = profile.get("intervention_patterns", {})
    floor = profile.get("floor_giving", {})

    avg_len = comm.get("avg_turn_length_chars", 0)
    if avg_len > 200:
        proposed["verbosity"] = (
            f"Match operator information density — substantive responses default "
            f"(operator avg: {avg_len:.0f} chars/turn)"
        )
    elif avg_len > 0:
        proposed["verbosity"] = (
            f"Operator prefers concise exchanges (operator avg: {avg_len:.0f} chars/turn)"
        )

    short_rate = comm.get("short_turn_rate", 0)
    if short_rate > 0.05:
        proposed["short_turn_handling"] = (
            f"Short turns ({short_rate*100:.0f}% frequency) are quick directives — "
            "respond concisely without over-explaining"
        )

    avg_corr = interv.get("avg_corrections_per_session", 0)
    if avg_corr < 0.5:
        proposed["autonomy_baseline"] = (
            f"Very low correction rate ({avg_corr:.1f}/session) — high operator trust, "
            "reduce check-in frequency and proceed autonomously"
        )
    elif avg_corr < 1.5:
        proposed["autonomy_baseline"] = (
            f"Low correction rate ({avg_corr:.1f}/session) — trust judgment unless "
            "explicitly redirected"
        )
    else:
        proposed["autonomy_baseline"] = (
            f"Moderate correction rate ({avg_corr:.1f}/session) — check in before "
            "committing to major steps"
        )

    corr_pos = interv.get("typical_correction_position")
    if corr_pos:
        proposed["correction_timing"] = (
            f"Corrections typically arrive {corr_pos} in the session — "
            + {
                "early": "present a plan first so redirection happens before execution",
                "mid": "checkpoint after initial steps before continuing",
                "late": "complete the approach, operator steers at the end",
            }.get(corr_pos, "")
        )

    phrases = floor.get("detected_phrases", [])
    if phrases:
        proposed["floor_recognition"] = (
            f"These phrases signal explicit handoff of initiative: {phrases}. "
            "Activate autonomous mode when detected."
        )

    return proposed
