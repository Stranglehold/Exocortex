"""
Task Completion Tracker — Orientation Stack Wave 2
===================================================
Hook: message_loop_end
Priority: _48 (fires before supervisor at _50)

Positional backbone for the orientation stack. Tracks where the agent is in
a multi-phase task so the Situational Orientation Protocol (_14) always knows:
  - Which phase is active
  - Which subtasks are done
  - When a phase boundary was just crossed

Addresses ST-005 finding: the agent repeated "Phase 1 appears complete" seven
times before the operator said "move on." The capability was present. The
positional record was absent.

Detection is heuristic and intentionally loose — false positive completions are
acceptable because the tracker is advisory, not authoritative. False negatives
(missing a completion) hurt more than false positives (over-counting one).

Reads:
  - loop_data.history_output (agent messages + tool results)
Writes:
  - agent.data["_task_tracker"] (in-memory, current session)
  - /a0/usr/Exocortex/task_tracker.json (persistent, cross-session)
  - agent.data["_layer_signals"]["task_phase_transition"] (trigger for _14)
Log tag: [TASK-TRACK]
"""

import json
import os
import re
import time
from typing import Any

from agent import LoopData
from python.helpers.extension import Extension

# ── Constants ─────────────────────────────────────────────────────────────────

TRACKER_KEY    = "_task_tracker"
SIGNALS_KEY    = "_layer_signals"
TRACKER_PATH   = "/a0/usr/Exocortex/task_tracker.json"

# Minimum turns between plan re-scans (avoid re-detecting the same plan)
RESCAN_COOLDOWN = 5

# Completion signal patterns (in AI response text)
PHASE_COMPLETE_RX = re.compile(
    r"(?i)phase\s+(\d+)[^\n]*(?:complete|done|finished|accomplished|✓)",
    re.MULTILINE,
)
STEP_COMPLETE_RX = re.compile(
    r"(?i)(?:step|task|subtask)\s+(\d+)[^\n]*(?:complete|done|✓|checked off)",
    re.MULTILINE,
)
FILE_CREATED_RX = re.compile(
    r"(?i)(?:created|wrote|written|saved|built)\s+(?:file\s+)?[`'\"]?(\S+\.(?:py|json|md|yaml|yml|sh|js|ts))[`'\"]?",
)
TESTS_PASS_RX  = re.compile(r"(?i)(?:all\s+)?tests?\s+(?:pass|passed|passing)")
GENERAL_DONE_RX = re.compile(r"(?i)\b(?:✓|✅|done|complete|completed|finished)\b.*(?:phase|step|stage|task)")

# Plan structure detection patterns
PLAN_PHASE_RX  = re.compile(
    r"^(?:#{1,3}\s+)?(?:phase|step|stage)\s+(\d+)\s*[:\-–]\s*(.+)",
    re.IGNORECASE | re.MULTILINE,
)
PLAN_NUMBER_RX = re.compile(
    r"^\s*(\d+)[.)]\s+(.+)",
    re.MULTILINE,
)

# Minimum items to treat a numbered list as a plan
MIN_PLAN_ITEMS = 3


class TaskTracker(Extension):
    """message_loop_end: tracks multi-phase task position, persists via staging."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
        try:
            # Get or initialize tracker state
            tracker = getattr(self.agent, TRACKER_KEY, None)
            if tracker is None:
                tracker = _load_tracker()
                setattr(self.agent, TRACKER_KEY, tracker)

            turn = _get_turn_count(loop_data)

            # Scan for new plan in agent output (with cooldown to avoid re-detection)
            last_scan = tracker.get("_last_scan", -RESCAN_COOLDOWN)
            if (turn - last_scan) >= RESCAN_COOLDOWN:
                ai_text = _extract_ai_response_text(loop_data)
                if ai_text:
                    plan = _detect_plan(ai_text)
                    if plan and not tracker.get("phases"):
                        tracker["phases"] = plan["phases"]
                        tracker["total_phases"] = len(plan["phases"])
                        tracker["current_phase"] = 0
                        tracker["current_subtask"] = 0
                        tracker["completed_phases"] = 0
                        tracker["plan_id"] = f"plan_{int(time.time())}"
                        tracker["_last_scan"] = turn
                        self.agent.context.log.log(
                            type="info",
                            content=(
                                f"[TASK-TRACK] Plan detected: "
                                f"{len(plan['phases'])} phases, "
                                f"{sum(len(p['subtasks']) for p in plan['phases'])} subtasks"
                            ),
                        )
                    elif ai_text:
                        tracker["_last_scan"] = turn

            # Scan for completion signals
            if tracker.get("phases"):
                prev_phase = tracker.get("current_phase", 0)
                prev_completed = tracker.get("completed_phases", 0)

                _update_completions(tracker, loop_data, turn)

                new_phase = tracker.get("current_phase", 0)
                # Detect phase boundary crossing
                if new_phase > prev_phase:
                    signals = getattr(self.agent, SIGNALS_KEY, {}) or {}
                    phases = tracker.get("phases", [])
                    completed_name = phases[prev_phase]["name"] if prev_phase < len(phases) else f"Phase {prev_phase + 1}"
                    next_name = phases[new_phase]["name"] if new_phase < len(phases) else f"Phase {new_phase + 1}"
                    signals["task_phase_transition"] = {
                        "completed_phase": prev_phase,
                        "completed_name": completed_name,
                        "entering_phase": new_phase,
                        "entering_name": next_name,
                        "turn": turn,
                    }
                    setattr(self.agent, SIGNALS_KEY, signals)
                    self.agent.context.log.log(
                        type="info",
                        content=(
                            f"[TASK-TRACK] Phase boundary: "
                            f"'{completed_name}' → '{next_name}'"
                        ),
                    )

            tracker["_turn"] = turn
            setattr(self.agent, TRACKER_KEY, tracker)

            # Persist to disk
            _save_tracker(tracker)

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[TASK-TRACK] Error (passthrough): {e}",
                )
            except Exception:
                pass


# ── Plan Detection ─────────────────────────────────────────────────────────────

def _detect_plan(text: str) -> dict | None:
    """
    Scan text for a multi-phase plan structure. Returns a plan dict or None.
    Prefers explicit Phase/Step labels; falls back to numbered list.
    """
    # Try Phase/Step/Stage headers first
    phase_matches = PLAN_PHASE_RX.findall(text)
    if len(phase_matches) >= 2:
        phases = []
        for num_str, label in phase_matches:
            phases.append({
                "name": f"Phase {num_str}: {label.strip()[:60]}",
                "status": "pending",
                "subtasks": [],
            })
        # Mark first phase in-progress
        if phases:
            phases[0]["status"] = "in-progress"
        return {"phases": phases}

    # Fall back to numbered list
    num_matches = PLAN_NUMBER_RX.findall(text)
    if len(num_matches) >= MIN_PLAN_ITEMS:
        phases = []
        for num_str, label in num_matches:
            phases.append({
                "name": f"Step {num_str}: {label.strip()[:60]}",
                "status": "pending",
                "subtasks": [],
            })
        if phases:
            phases[0]["status"] = "in-progress"
        return {"phases": phases}

    return None


# ── Completion Detection ───────────────────────────────────────────────────────

def _update_completions(tracker: dict, loop_data: LoopData, turn: int) -> None:
    """
    Scan recent output for completion signals. Update tracker state.
    Uses a lightweight heuristic — completions are advisory.
    """
    phases = tracker.get("phases", [])
    if not phases:
        return

    current_idx = tracker.get("current_phase", 0)
    if current_idx >= len(phases):
        return

    # Gather text from: AI response messages + tool results (last 3 messages)
    text_buffer = _extract_recent_text(loop_data, max_messages=6)
    if not text_buffer:
        return

    current_phase = phases[current_idx]
    phase_num = current_idx + 1

    # Check explicit phase completion
    phase_complete = bool(PHASE_COMPLETE_RX.search(text_buffer))
    tests_pass = bool(TESTS_PASS_RX.search(text_buffer))
    general_done = bool(GENERAL_DONE_RX.search(text_buffer))

    # Count successful tool calls as partial completion evidence
    tool_successes = _count_tool_successes(loop_data)

    # Heuristic: mark current phase complete if we see explicit signal
    if phase_complete or (tests_pass and general_done):
        current_phase["status"] = "completed"
        tracker["completed_phases"] = tracker.get("completed_phases", 0) + 1

        # Advance to next phase
        next_idx = current_idx + 1
        if next_idx < len(phases):
            phases[next_idx]["status"] = "in-progress"
            tracker["current_phase"] = next_idx
            tracker["current_subtask"] = 0
        else:
            # All phases complete
            tracker["current_phase"] = current_idx  # stay at last


# ── Text Extraction ────────────────────────────────────────────────────────────

def _extract_ai_response_text(loop_data: LoopData) -> str:
    """Extract the most recent AI response (response tool text) from history."""
    if not loop_data.history_output:
        return ""
    for msg in reversed(loop_data.history_output):
        if not isinstance(msg, dict):
            continue
        if not msg.get("ai", True):
            continue
        content = msg.get("content", "")
        tool_name = _parse_tool_name(content)
        if tool_name == "response":
            args = _parse_tool_args(content)
            return str(args.get("text", ""))
    return ""


def _extract_recent_text(loop_data: LoopData, max_messages: int = 6) -> str:
    """Collect text from last N messages (AI + tool results) as one string."""
    if not loop_data.history_output:
        return ""
    parts = []
    for msg in loop_data.history_output[-max_messages:]:
        if not isinstance(msg, dict):
            continue
        content = msg.get("content", "")
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, dict):
            parts.append(str(content.get("tool_result", "")))
            parts.append(str(content.get("user_message", "")))
    return "\n".join(parts)


def _count_tool_successes(loop_data: LoopData) -> int:
    """Count tool results with exit-0 or explicit success in last few messages."""
    count = 0
    if not loop_data.history_output:
        return 0
    for msg in loop_data.history_output[-6:]:
        if not isinstance(msg, dict):
            continue
        if msg.get("ai", True):
            continue
        content = msg.get("content", "")
        if not isinstance(content, dict):
            continue
        result = str(content.get("tool_result", "")).lower()
        if any(s in result for s in ["exit code 0", "exit 0", "successfully", "success"]):
            count += 1
    return count


# ── History Parsing ────────────────────────────────────────────────────────────

def _parse_tool_name(content) -> str:
    if isinstance(content, dict):
        return content.get("tool_name", "")
    if isinstance(content, str) and "{" in content:
        try:
            d = json.loads(content.strip())
            return d.get("tool_name", "")
        except Exception:
            m = re.search(r'"tool_name"\s*:\s*"([^"]+)"', content)
            if m:
                return m.group(1)
    return ""


def _parse_tool_args(content) -> dict:
    if isinstance(content, dict):
        return content.get("tool_args", {}) or {}
    if isinstance(content, str) and "{" in content:
        try:
            d = json.loads(content.strip())
            return d.get("tool_args", {}) or {}
        except Exception:
            pass
    return {}


def _get_turn_count(loop_data: LoopData) -> int:
    """Estimate turn count from history length."""
    if not loop_data.history_output:
        return 0
    return len([m for m in loop_data.history_output if isinstance(m, dict) and m.get("ai", True)])


# ── Persistence ────────────────────────────────────────────────────────────────

def _load_tracker() -> dict:
    """Load tracker from disk, return empty tracker on any failure."""
    try:
        if os.path.exists(TRACKER_PATH):
            with open(TRACKER_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Stale if older than 24 hours
                if time.time() - data.get("_turn_ts", 0) < 86400:
                    return data
    except Exception:
        pass
    return {
        "plan_id": None,
        "phases": [],
        "current_phase": 0,
        "current_subtask": 0,
        "total_phases": 0,
        "completed_phases": 0,
        "_turn": 0,
        "_turn_ts": time.time(),
        "_last_scan": -RESCAN_COOLDOWN,
    }


def _save_tracker(tracker: dict) -> None:
    """Write tracker to disk."""
    try:
        tracker["_turn_ts"] = time.time()
        os.makedirs(os.path.dirname(TRACKER_PATH), exist_ok=True)
        with open(TRACKER_PATH, "w", encoding="utf-8") as f:
            json.dump(tracker, f, indent=2)
    except Exception:
        pass
