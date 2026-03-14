"""
sleep_episode_chunker.py — Exocortex Sleep Consolidation: Episode Chunker

Parses Agent Zero session logs (chat.json) into bounded episodes and
extracts loop patterns for anti-pattern capture.

An episode is the interval between an operator message and the agent's
final response tool call. The chunker tags each episode with:
  - which tools were called
  - whether a supervisor loop warning fired
  - severity of the loop (warn / summarize / reset)
  - whether the operator intervened to break the loop

Anti-pattern gap detection: Tier 4 (supervisor loop) captures anti-patterns
in real time when the agent self-resolves a loop. The chunker catches cases
Tier 4 misses — specifically, loops broken by operator intervention rather
than by the agent resolving the failure itself.

Called from: sleep_consolidation.run_phase2_consolidation()
Reads from:  /a0/usr/chats/{session_id}/chat.json
No LLM calls — purely deterministic.
"""

import json
import os
import re
from typing import Dict, List, Optional, Tuple


# ── Constants ────────────────────────────────────────────────────────────────

CHAT_ROOT = "/a0/usr/chats"

# Supervisor warning prefixes injected into history as system_warning messages
_LOOP_PATTERN    = re.compile(r"\[SUPERVISOR\].*LOOP DETECTED.*tool['\"]?\s*:?\s*['\"]?(\w+)", re.IGNORECASE)
_TIER2_PATTERN   = re.compile(r"\[SUPERVISOR TIER 2", re.IGNORECASE)
_TIER3_PATTERN   = re.compile(r"\[SUPERVISOR TIER 3", re.IGNORECASE)
_FAILING_TOOL    = re.compile(r"Failing tool[:\s]+['\"]?(\w+)['\"]?", re.IGNORECASE)
_LOOP_TOOL_ALT   = re.compile(r"(\w+) has failed \d+ times", re.IGNORECASE)


# ── Public API ───────────────────────────────────────────────────────────────

def load_recent_sessions(n: int = 3) -> List[Dict]:
    """
    Load the N most recent sessions from /a0/usr/chats/.
    Returns list of parsed chat.json dicts, sorted newest first.
    Sessions with no agents or unparseable history are skipped.
    """
    if not os.path.isdir(CHAT_ROOT):
        return []

    sessions = []
    for name in os.listdir(CHAT_ROOT):
        path = os.path.join(CHAT_ROOT, name, "chat.json")
        if not os.path.exists(path):
            continue
        try:
            mtime = os.path.getmtime(path)
            sessions.append((mtime, name, path))
        except OSError:
            continue

    sessions.sort(reverse=True)  # newest first

    result = []
    for _, session_id, path in sessions[:n]:
        parsed = _parse_session(session_id, path)
        if parsed:
            result.append(parsed)

    return result


def chunk_session(session: Dict) -> List[Dict]:
    """
    Chunk a parsed session into episodes.
    Each episode spans from an operator message to the agent's response tool call.
    Returns list of episode dicts.
    """
    messages = session.get("messages", [])
    session_id = session.get("session_id", "unknown")
    episodes = []
    episode_idx = 0
    current: Optional[Dict] = None

    for msg in messages:
        ai = msg.get("ai", False)
        content = msg.get("content", {})

        if isinstance(content, str):
            try:
                content = json.loads(content)
            except Exception:
                content = {"raw": content}

        # Operator message → start new episode
        if not ai and "user_message" in content:
            if current is not None:
                # Previous episode never got a response — operator interrupted
                current["operator_intervened"] = True
                current["successful"] = False
                episodes.append(current)
                episode_idx += 1
            current = _new_episode(session_id, episode_idx, content["user_message"])

        # System warning → supervisor signal (loop detection, cascade, etc.)
        elif not ai and "system_warning" in content:
            warning_text = _extract_warning_text(content["system_warning"])
            if current is not None:
                current["supervisor_warnings"].append(warning_text)
                _tag_loop_info(current, warning_text)

        # AI tool call
        elif ai:
            tool_name = content.get("tool_name", "")
            if not tool_name and isinstance(content.get("raw"), str):
                # Unparsed AI message — skip
                continue

            if current is not None:
                if tool_name:
                    current["tool_calls"].append(tool_name)

                # Response tool = episode complete
                if tool_name == "response":
                    current["successful"] = True
                    episodes.append(current)
                    episode_idx += 1
                    current = None

    # Unclosed episode at end of session
    if current is not None:
        current["operator_intervened"] = True
        current["successful"] = False
        episodes.append(current)

    return episodes


def extract_loop_patterns(episodes: List[Dict]) -> List[Dict]:
    """
    Find episodes that had loops. Returns list of loop pattern dicts
    suitable for anti-pattern capture.
    """
    patterns = []
    for ep in episodes:
        if not ep.get("had_loop"):
            continue
        for tool in ep.get("loop_tools", []):
            if not tool:
                continue
            patterns.append({
                "session_id": ep["session_id"],
                "failing_tool": tool,
                "domain": "unknown",   # BST domain not available in log; Phase 3 can enrich
                "consecutive": _severity_to_consecutive(ep.get("loop_severity", "warn")),
                "operator_intervened": ep.get("operator_intervened", False),
                "episode_idx": ep["episode_idx"],
            })
    return patterns


# ── Internal Helpers ─────────────────────────────────────────────────────────

def _parse_session(session_id: str, path: str) -> Optional[Dict]:
    """Parse a single chat.json file into a flat message list."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)

        agents = data.get("agents", [])
        if not agents:
            return None

        agent0 = agents[0]
        history_raw = agent0.get("history", "")
        if isinstance(history_raw, str):
            history = json.loads(history_raw)
        else:
            history = history_raw

        # Flatten all topics' messages into one list
        messages = []
        for topic in history.get("topics", []):
            messages.extend(topic.get("messages", []))

        if not messages:
            return None

        return {
            "session_id": session_id,
            "created_at": data.get("created_at", ""),
            "messages": messages,
        }

    except Exception:
        return None


def _new_episode(session_id: str, idx: int, user_message: str) -> Dict:
    return {
        "session_id": session_id,
        "episode_idx": idx,
        "user_message": user_message[:200],
        "tool_calls": [],
        "had_loop": False,
        "loop_tools": [],
        "loop_severity": "none",
        "operator_intervened": False,
        "successful": False,
        "supervisor_warnings": [],
        "turn_count": 0,
    }


def _extract_warning_text(raw) -> str:
    """Normalize a system_warning value to a string."""
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        return " ".join(str(x) for x in raw)
    return str(raw)


def _tag_loop_info(episode: Dict, warning: str):
    """Parse supervisor warning text and tag the episode with loop metadata."""
    # Detect tier
    if _TIER3_PATTERN.search(warning):
        episode["had_loop"] = True
        episode["loop_severity"] = "reset"
    elif _TIER2_PATTERN.search(warning):
        episode["had_loop"] = True
        if episode["loop_severity"] not in ("reset",):
            episode["loop_severity"] = "summarize"
    elif "[SUPERVISOR]" in warning and "LOOP DETECTED" in warning.upper():
        episode["had_loop"] = True
        if episode["loop_severity"] == "none":
            episode["loop_severity"] = "warn"

    # Extract failing tool name
    if episode["had_loop"]:
        for pattern in (_FAILING_TOOL, _LOOP_TOOL_ALT, _LOOP_PATTERN):
            m = pattern.search(warning)
            if m:
                tool = m.group(1)
                if tool and tool not in episode["loop_tools"]:
                    episode["loop_tools"].append(tool)
                break


def _severity_to_consecutive(severity: str) -> int:
    """Map severity label to an approximate consecutive count for the index."""
    return {"warn": 3, "summarize": 6, "reset": 9}.get(severity, 3)
