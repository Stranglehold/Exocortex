"""
Reasoning State Persistence — Orientation Stack Wave 2
=======================================================
Hook: message_loop_end
Priority: _49 (after task tracker at _48, before supervisor at _50)

Maintains a compressed reasoning state — what the agent is working on,
what approaches have failed, and what the current theory is. This state
is injected at turn start by _13_reasoning_state.py and survives context
compression via staging.jsonl.

Addresses ST-005 finding: after context compression, the agent retried
approaches that had already failed because the dead-end record was gone.
The compressed reasoning state preserves exactly this information and
reinjects it at the start of every turn.

Format:
  [REASONING STATE — step N]
  Theory: {one-line working theory}
  Tried: {approach} → {outcome}
  Current: {what the agent is doing and why}
  Open: {unresolved question}

Update mechanism (deterministic — no LLM calls):
  - Tool success → advances "Current", clears failed attempts for that tool
  - Tool failure → appends to "Tried" list with failure reason
  - AI response text → extracts Theory/Current from first lines if pattern matches
  - Context compression detected → writes state to staging.jsonl

Reads:
  - loop_data.history_output (last tool call + result)
  - agent.data["_reasoning_state"]
Writes:
  - agent.data["_reasoning_state"]
  - /a0/usr/Exocortex/staging.jsonl (on compression event)
Log tag: [REASON-STATE]
"""

import json
import os
import re
import time
from typing import Any

from agent import LoopData
from python.helpers.extension import Extension

# ── Constants ─────────────────────────────────────────────────────────────────

REASONING_KEY  = "_reasoning_state"
STAGING_PATH   = "/a0/usr/Exocortex/staging.jsonl"
HIST_LEN_KEY   = "_rs_last_hist_len"

MAX_TRIED      = 6    # Maximum "Tried" entries before oldest are dropped
MAX_THEORY_LEN = 120  # Characters for Theory field
MAX_CURRENT_LEN = 200
MAX_TRIED_LEN  = 120
MAX_ARTIFACTS  = 12   # Maximum tracked file paths before oldest are dropped

# File-write detection patterns (terminal and Python runtimes)
HEREDOC_WRITE_RX  = re.compile(r'cat\s+>\s+(/[^\s<]+)', re.MULTILINE)
TEE_WRITE_RX      = re.compile(r'\btee\s+(/[^\s|&;]+)')
# Redirect write: `echo '...' > /path/file` or `printf ... > /path/file`
# Requires file extension to avoid false positives on plain redirect operators
REDIRECT_WRITE_RX = re.compile(r'(?<![>])>\s*(/[^\s|&;>]+\.\w+)')
PY_OPEN_WRITE_RX  = re.compile(r'open\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']w')

# Patterns for extracting reasoning state from AI text
THEORY_RX   = re.compile(r"(?i)(?:theory|hypothesis|approach):\s*(.+?)(?:\n|$)")
CURRENT_RX  = re.compile(r"(?i)(?:current(?:ly)?|now|next step|doing):\s*(.+?)(?:\n|$)")
OPEN_RX     = re.compile(r"(?i)(?:open question|unclear|unknown|question):\s*(.+?)(?:\n|$)")

# Error indicators for tool output classification
ERROR_SIGNALS = [
    "error:", "traceback", "exception:", "failed:", "errno",
    "exit code 1", "exit 1", "no such file", "command not found",
    "permission denied", "syntax error",
]
SUCCESS_SIGNALS = [
    "successfully", "exit code 0", "exit 0", "success", "done", "ok",
    "created", "written", "saved",
]

# Compression detection: history shrinks by this fraction in one turn
COMPRESSION_SHRINK_THRESHOLD = 0.35


class ReasoningStateUpdate(Extension):
    """message_loop_end: update compressed reasoning state after each turn."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
        try:
            # Get or initialize reasoning state
            state = getattr(self.agent, REASONING_KEY, None)
            if state is None:
                state = _empty_state()
                setattr(self.agent, REASONING_KEY, state)

            state["step"] = state.get("step", 0) + 1
            hist_len = len(loop_data.history_output or [])

            # Detect context compression
            last_len = getattr(self.agent, HIST_LEN_KEY, hist_len)
            compressed = False
            if last_len > 10 and hist_len < last_len * (1 - COMPRESSION_SHRINK_THRESHOLD):
                compressed = True
                print(
                    f"[REASON-STATE] Compression detected: history {last_len} → {hist_len}",
                    flush=True,
                )
            setattr(self.agent, HIST_LEN_KEY, hist_len)

            # Update state from last tool call + result
            last_tool = _get_last_tool_pair(loop_data)
            if last_tool:
                _update_from_tool(state, last_tool)

            # Extract Theory/Current from last AI response
            ai_text = _get_last_ai_response(loop_data)
            if ai_text:
                _update_from_ai_text(state, ai_text)

            # Detect and register new file artifacts
            existing_paths = {a["path"] for a in state.get("artifacts", [])}
            new_artifacts = _detect_new_artifacts(
                loop_data.history_output or [],
                existing_paths,
                state["step"],
            )
            if new_artifacts:
                artifact_list = list(state.get("artifacts", []))
                artifact_list.extend(new_artifacts)
                if len(artifact_list) > MAX_ARTIFACTS:
                    artifact_list = artifact_list[-MAX_ARTIFACTS:]
                state["artifacts"] = artifact_list
                _write_artifact_entries(new_artifacts)
                print(
                    f"[REASON-STATE] New artifacts: "
                    + ", ".join(a["path"] for a in new_artifacts),
                    flush=True,
                )

            setattr(self.agent, REASONING_KEY, state)

            # On compression: write to staging so state survives
            if compressed and state.get("current"):
                _write_to_staging(state)
                print("[REASON-STATE] State written to staging (compression event)", flush=True)

            print(
                f"[REASON-STATE] step={state['step']} "
                f"tried={len(state.get('tried', []))} "
                f"artifacts={len(state.get('artifacts', []))} "
                f"compressed={compressed}",
                flush=True,
            )

        except Exception as e:
            print(f"[REASON-STATE] Error (passthrough): {e}", flush=True)


# ── State Initialization ───────────────────────────────────────────────────────

def _empty_state() -> dict:
    return {
        "step": 0,
        "theory": "",
        "tried": [],      # list of {"approach": str, "outcome": str}
        "current": "",
        "open": "",
        "artifacts": [],  # list of {"path": str, "description": str, "step": int}
    }


# ── Tool Pair Extraction ───────────────────────────────────────────────────────

def _get_last_tool_pair(loop_data: LoopData) -> dict | None:
    """
    Get the last tool call + result pair from history.
    Returns dict with: tool_name, cmd_hint, result_text, success
    """
    if not loop_data.history_output:
        return None

    # Find last non-response tool result
    for msg in reversed(loop_data.history_output):
        if not isinstance(msg, dict):
            continue
        if msg.get("ai", True):
            continue
        content = msg.get("content", "")
        if not isinstance(content, dict):
            continue
        tool_name = content.get("tool_name", "")
        if tool_name in ("response", ""):
            continue

        result_text = str(content.get("tool_result", ""))
        success = _classify_success(result_text)

        # Try to get the preceding AI tool call for cmd hint
        cmd_hint = _extract_cmd_hint(tool_name, result_text)

        return {
            "tool_name": tool_name,
            "cmd_hint": cmd_hint,
            "result_text": result_text,
            "success": success,
        }
    return None


def _classify_success(text: str) -> bool:
    lower = text.lower()
    if any(s in lower for s in ERROR_SIGNALS):
        return False
    if any(s in lower for s in SUCCESS_SIGNALS):
        return True
    return True  # default optimistic


def _extract_cmd_hint(tool_name: str, result_text: str) -> str:
    """Brief hint about what the tool did, from output."""
    lines = result_text.strip().splitlines()
    if lines:
        return lines[0][:80]
    return tool_name


# ── State Update Logic ─────────────────────────────────────────────────────────

def _update_from_tool(state: dict, tool: dict) -> None:
    """Update reasoning state from a tool result."""
    tool_name = tool["tool_name"]
    cmd = tool["cmd_hint"]
    success = tool["success"]

    if success:
        # Advance Current field
        state["current"] = f"{tool_name}: {cmd[:MAX_CURRENT_LEN]}"
        # Remove any prior failed attempts for this tool
        state["tried"] = [
            t for t in state.get("tried", [])
            if not t.get("approach", "").startswith(tool_name)
        ]
    else:
        # Extract failure reason from result text
        failure_reason = _extract_failure_reason(tool["result_text"])
        entry = {
            "approach": f"{tool_name}: {cmd[:80]}",
            "outcome": failure_reason[:MAX_TRIED_LEN],
        }
        tried = state.get("tried", [])
        # Don't duplicate identical failures
        if not any(t["approach"] == entry["approach"] for t in tried):
            tried.append(entry)
        # Trim to max
        if len(tried) > MAX_TRIED:
            tried = tried[-MAX_TRIED:]
        state["tried"] = tried


def _extract_failure_reason(text: str) -> str:
    """Extract the most relevant error line from tool output."""
    lines = text.strip().splitlines()
    # Prefer lines with error keywords
    for line in lines:
        low = line.lower()
        if any(s in low for s in ["error:", "exception:", "failed:", "no such", "not found"]):
            return line.strip()
    # Fall back to last non-empty line
    for line in reversed(lines):
        if line.strip():
            return line.strip()
    return "failed"


def _update_from_ai_text(state: dict, text: str) -> None:
    """Extract Theory/Current/Open updates from AI response text."""
    m = THEORY_RX.search(text)
    if m:
        new_theory = m.group(1).strip()[:MAX_THEORY_LEN]
        if new_theory:
            state["theory"] = new_theory

    m = CURRENT_RX.search(text)
    if m:
        new_current = m.group(1).strip()[:MAX_CURRENT_LEN]
        if new_current:
            state["current"] = new_current

    m = OPEN_RX.search(text)
    if m:
        new_open = m.group(1).strip()[:MAX_THEORY_LEN]
        if new_open:
            state["open"] = new_open


# ── History Extraction ─────────────────────────────────────────────────────────

def _get_last_ai_response(loop_data: LoopData) -> str:
    """Get text from the most recent AI response tool call."""
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


# ── Artifact Detection ─────────────────────────────────────────────────────────

def _path_to_description(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    return {
        ".py":   "Python module",
        ".sh":   "Shell script",
        ".json": "JSON config",
        ".md":   "Markdown doc",
        ".txt":  "Text file",
        ".yaml": "YAML config",
        ".yml":  "YAML config",
    }.get(ext, "File")


def _detect_new_artifacts(
    history: list,
    existing_paths: set,
    current_step: int,
) -> list[dict]:
    """
    Walk AI messages in history for code_execution_tool calls.
    Extract file paths written via heredoc, tee, or open(..., 'w').
    Return only paths not already in existing_paths.

    Scans the full history each call; correctness is guaranteed by the
    existing_paths dedup check. For very long sessions (100+ turns), consider
    tracking _last_artifact_scan_idx in state and slicing history from there.
    """
    new_artifacts = []
    seen_this_scan: set = set()

    for msg in history:
        if not isinstance(msg, dict):
            continue
        if not msg.get("ai", True):
            continue
        content = msg.get("content", "")
        tool_name = _parse_tool_name(content)
        if tool_name != "code_execution_tool":
            continue
        args = _parse_tool_args(content)
        runtime = args.get("runtime", "")
        code = args.get("code", "")
        if not code:
            continue

        paths: list[str] = []
        if runtime == "terminal":
            paths += HEREDOC_WRITE_RX.findall(code)
            paths += TEE_WRITE_RX.findall(code)
            paths += REDIRECT_WRITE_RX.findall(code)
        elif runtime == "python":
            paths += PY_OPEN_WRITE_RX.findall(code)

        for path in paths:
            path = path.strip()
            if not path.startswith("/"):
                continue
            if path in existing_paths or path in seen_this_scan:
                continue
            seen_this_scan.add(path)
            new_artifacts.append({
                "path": path,
                "description": _path_to_description(path),
                "step": current_step,
            })

    return new_artifacts


def _write_artifact_entries(artifacts: list[dict]) -> None:
    """
    Write or update artifact entries in staging.jsonl.
    One entry per file path; replaces existing entry for the same path.
    importance=0.9 is intentionally high — these entries serve context recovery
    after API boundary resets, where knowing what files exist is critical to
    avoiding unnecessary rebuilds.
    """
    try:
        os.makedirs(os.path.dirname(STAGING_PATH), exist_ok=True)
        updated_paths = {a["path"] for a in artifacts}

        existing = []
        if os.path.exists(STAGING_PATH):
            with open(STAGING_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        e = json.loads(line)
                        # Drop stale entries for paths being updated
                        if e.get("_artifact_entry") and e.get("path") in updated_paths:
                            continue
                        existing.append(line)
                    except Exception:
                        existing.append(line)

        for a in artifacts:
            entry = {
                "category": "artifact",
                "status": "active",
                "text": f"{a['path']} — {a['description']} (step {a['step']})",
                "why": "File written during this session — path preserved across context reset",
                "importance": 0.9,
                "reactivation_count": 0,
                "created": time.time(),
                "_artifact_entry": True,
                "path": a["path"],
                "description": a["description"],
                "artifact_step": a["step"],
            }
            existing.append(json.dumps(entry))

        with open(STAGING_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(existing) + "\n")
    except Exception:
        pass


# ── Staging Persistence ────────────────────────────────────────────────────────

def _write_to_staging(state: dict) -> None:
    """
    Write current reasoning state to staging.jsonl as an observation entry.
    Overwrites any prior reasoning_state entry to avoid accumulation.
    Uses read-filter-append pattern (no in-place line editing).
    """
    try:
        os.makedirs(os.path.dirname(STAGING_PATH), exist_ok=True)

        # Read existing entries, dropping any prior reasoning_state observation
        existing = []
        if os.path.exists(STAGING_PATH):
            with open(STAGING_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        e = json.loads(line)
                        if e.get("_rs_entry"):
                            continue  # drop prior reasoning state entries
                        existing.append(line)
                    except Exception:
                        existing.append(line)

        # Build compact text representation
        tried_lines = []
        for t in state.get("tried", []):
            tried_lines.append(f"  {t['approach']} → {t['outcome']}")
        tried_text = "\n".join(tried_lines) if tried_lines else "(none)"

        text = (
            f"Reasoning state at step {state['step']}: "
            f"Theory: {state.get('theory', '(unknown)')} | "
            f"Current: {state.get('current', '(unknown)')} | "
            f"Failed approaches: {tried_text}"
        )

        entry = {
            "category": "observation",
            "status": "active",
            "text": text[:500],
            "why": "Reasoning state snapshot — preserved across context compression",
            "importance": 0.8,
            "reactivation_count": 0,
            "created": time.time(),
            "_rs_entry": True,  # marker for de-duplication
        }

        existing.append(json.dumps(entry))

        with open(STAGING_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(existing) + "\n")

    except Exception:
        pass
