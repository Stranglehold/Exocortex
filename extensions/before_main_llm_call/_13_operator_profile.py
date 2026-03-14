"""
Operator Profile — Agent-Zero Phase 4 Behavioral Integration
============================================================
Hook: before_main_llm_call (_13_)

Reads the operator's approved profile snapshot and injects behavioral
calibration into the LLM context before each call.

Two behaviors:

1. Calibration block — prepended to the user message so the LLM matches
   the operator's communication style and autonomy expectations:
     [OPERATOR PROFILE — approved snapshot]
     - Operator writes substantive turns (avg 424 chars). Match information density.
     - Short operator turns (8% frequency) are quick directives — respond concisely.
     - Correction rate is low (0.33/session). Trust your judgment unless redirected.
     - When corrections occur, they tend to arrive early in the session.

2. Floor-giving detection — checks the current operator turn against the
   approved floor-giving phrases. When detected, prepends an explicit
   autonomy signal to the calibration block and sets
   loop_data.extras_persistent["_operator_floor_given"] = True.

Gate: does nothing unless /a0/usr/Exocortex/operator_profile_approved.json
      exists. The operator creates this file by reviewing operator_profile.json
      (Phase 3 proposal) and promoting it. Each promotion is auto-versioned
      in /a0/usr/Exocortex/operator_profile_versions/.

No LLM calls. All logic is deterministic pattern matching + template fill.
Runs after BST (_11_) — the calibration block prepends before BST enrichment.
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, Optional

from agent import LoopData
from python.helpers.extension import Extension

APPROVED_PATH = "/a0/usr/Exocortex/operator_profile_approved.json"
VERSIONS_DIR  = "/a0/usr/Exocortex/operator_profile_versions"

# Attribute name for per-agent mtime cache
_CACHE_ATTR = "_operator_profile_cache"


class OperatorProfile(Extension):
    """Inject operator calibration context before each LLM call."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            profile = _load_approved_profile(self.agent)
            if not profile:
                return  # No approved profile — gate holds

            # Find the current operator turn
            user_msg = _get_last_user_message(loop_data.history_output)
            if not user_msg:
                return

            content = user_msg.get("content", "")
            if isinstance(content, dict):
                content = (
                    content.get("user_message", "")
                    or content.get("message", "")
                    or str(content)
                )
            content = str(content).strip()

            # Detect floor-giving in current turn using approved phrases
            floor_given = _detect_floor_giving(content, profile)

            # Build calibration block
            block = _build_calibration_block(profile, floor_given)
            if not block:
                return

            # Prepend to user message content (BST enrichment may already be there)
            existing = user_msg.get("content", "")
            user_msg["content"] = block + "\n\n" + str(existing)

            # Persist floor-given signal for downstream use
            ep = getattr(loop_data, "extras_persistent", None)
            if ep is None:
                loop_data.extras_persistent = {}
                ep = loop_data.extras_persistent
            ep["_operator_floor_given"] = floor_given

            log_msg = (
                f"[PROFILE] Calibration injected."
                + (" Floor given: TRUE." if floor_given else "")
            )
            print(log_msg, flush=True)
            try:
                self.agent.context.log.log(type="info", content=log_msg)
            except Exception:
                pass

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[PROFILE] Error (passthrough): {e}",
                )
            except Exception:
                pass


# ── Profile Loading ───────────────────────────────────────────────────────────

def _load_approved_profile(agent) -> Optional[Dict]:
    """
    Load approved profile with mtime-based caching.
    Writes a versioned copy when the approved file changes.
    """
    if not os.path.exists(APPROVED_PATH):
        return None

    try:
        current_mtime = os.path.getmtime(APPROVED_PATH)
        cache = getattr(agent, _CACHE_ATTR, None) or {}

        if cache.get("mtime") == current_mtime:
            return cache.get("profile")

        # File changed (or first load) — reload
        with open(APPROVED_PATH, "r", encoding="utf-8") as f:
            profile = json.load(f)

        if cache.get("mtime") is not None:
            # Not first load — operator updated the approved file; version it
            _write_version_snapshot()

        agent.__dict__[_CACHE_ATTR] = {"mtime": current_mtime, "profile": profile}
        print(f"[PROFILE] Approved profile loaded.", flush=True)
        return profile

    except Exception as e:
        print(f"[PROFILE] Failed to load approved profile: {e}", flush=True)
        return None


def _write_version_snapshot():
    """Write a timestamped copy of the approved profile to the versions dir."""
    try:
        os.makedirs(VERSIONS_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(VERSIONS_DIR, f"operator_profile_approved_{ts}.json")
        shutil.copy2(APPROVED_PATH, dest)
        print(f"[PROFILE] Approved snapshot versioned: {dest}", flush=True)
    except Exception as e:
        print(f"[PROFILE] Failed to version snapshot: {e}", flush=True)


# ── Floor-Giving Detection ────────────────────────────────────────────────────

def _detect_floor_giving(text: str, profile: Dict) -> bool:
    """
    Check text against floor-giving phrases from the approved profile.
    Substring match, case-insensitive. Deterministic — no LLM calls.
    """
    if not text:
        return False
    phrases = profile.get("floor_giving", {}).get("detected_phrases", [])
    text_lower = text.lower()
    for phrase in phrases:
        if phrase and phrase.lower() in text_lower:
            return True
    return False


# ── Calibration Block ─────────────────────────────────────────────────────────

def _build_calibration_block(profile: Dict, floor_given: bool) -> str:
    """
    Generate the calibration block from approved profile data.
    Returns empty string if profile has no communication data yet.
    """
    comm   = profile.get("communication_patterns", {})
    interv = profile.get("intervention_patterns", {})

    avg_len    = comm.get("avg_turn_length_chars", 0)
    short_rate = comm.get("short_turn_rate", 0)
    avg_corr   = interv.get("avg_corrections_per_session", 0)
    corr_pos   = interv.get("typical_correction_position")

    if avg_len == 0:
        return ""  # Profile not populated yet

    lines = ["[OPERATOR PROFILE — approved snapshot]"]

    if floor_given:
        lines.append(
            "- FLOOR GIVEN — Operator has handed initiative. "
            "Proceed with full autonomy. Use tools independently. Report when complete."
        )

    lines.append(
        f"- Operator writes substantive turns (avg {avg_len:.0f} chars). "
        "Match information density."
    )

    if short_rate > 0.05:
        lines.append(
            f"- Short operator turns ({short_rate*100:.0f}% frequency) are quick directives — "
            "respond concisely."
        )

    if avg_corr < 1.0:
        lines.append(
            f"- Correction rate is low ({avg_corr:.1f}/session). "
            "Trust your judgment unless explicitly redirected."
        )
    else:
        lines.append(
            f"- Correction rate ({avg_corr:.1f}/session) suggests checking in before major steps."
        )

    if corr_pos:
        lines.append(
            f"- When corrections occur, they tend to arrive {corr_pos} in the session."
        )

    return "\n".join(lines)


# ── Message Extraction ────────────────────────────────────────────────────────

def _get_last_user_message(history_output: list) -> Optional[Dict]:
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
