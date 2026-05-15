"""
Verification Gate — Epistemic Checkpoint at Completion Boundaries
=================================================================
Hook: message_loop_end (_16_)
Tier: 2 — cheap heuristic, fires conditionally, zero model calls

Detects completion-language in the agent's last AI output. When found,
injects a structured verification question as agent.intervention on the
next turn, requiring the agent to prove integration before declaring done.

Fire-once-per-claim: gate fires → awaits outcome → records outcome → resets.
Can fire multiple times per session, never twice in a row without an outcome
recorded in between.

Journal schema (appended to first found _JOURNAL_CANDIDATES path):
  - action: "verification_gate_fired"   — gate triggered, intervention injected
  - action: "verification_gate_outcome" — what the agent did in response

Outcome types:
  - "tool_called"  — agent ran a tool (good; at least checked something)
  - "verbal_only"  — agent responded without any tool call (unchecked claim)

The journal drives pattern calibration: trigger_phrase, trigger_label,
outcome_type, and outcome_tool are the fields that matter.

Design: Opus / Jake (2026-05-09). Implementation: Kestrel.
Note: fires at _16_, before supervisor (_50_) and stuck-delivery (_29_).
      If supervisor also sets agent.intervention the same turn, supervisor
      wins (fires later). This is intentional — supervisor escalations take
      precedence over epistemic gates.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Optional

_PM_PATH = "/a0/usr/Exocortex"
if _PM_PATH not in sys.path:
    sys.path.insert(0, _PM_PATH)

from agent import LoopData
from helpers.extension import Extension
from helpers.history import UserMessage

# ── Journal path ──────────────────────────────────────────────────────────────
_JOURNAL_CANDIDATES = [
    "/a0/usr/workdir/self-improvement/journal.jsonl",
]

# ── High-confidence completion patterns ───────────────────────────────────────
# These fire unconditionally when matched in the last AI output.
# Ordered specific → general. First match wins.
_HARD_PATTERNS = [
    (r"\btask\s+(?:is\s+)?complete(?:d)?\b",                         "task_complete"),
    (r"\bdeployment\s+(?:is\s+)?complete(?:d)?\b",                   "deployment_complete"),
    (r"\binstallation\s+(?:is\s+)?complete(?:d)?\b",                 "installation_complete"),
    (r"\ball\s+tests?\s+pass(?:ed|ing)?\b",                          "tests_pass"),
    (r"\bfully\s+(?:deployed|integrated|wired(?:\s+up)?)\b",         "fully_deployed"),
    (r"\bsuccessfully\s+(?:deployed|installed|integrated|wired\s+up)\b", "successfully_deployed"),
    (r"\bdeployed\s+(?:and\s+)?(?:verified|confirmed|tested)\b",     "deployed_verified"),
    (r"\bimplemented\s+(?:and\s+)?(?:verified|confirmed|tested)\b",  "implemented_verified"),
    (r"\bextension\s+is\s+(?:now\s+)?(?:active|running|loaded|live)\b", "extension_live"),
    (r"\bwired\s+(?:up\s+)?(?:and\s+)?(?:deployed|complete|verified)\b", "wired_complete"),
    (r"\bstep\s+\d+\s*(?:of\s*\d+\s*)?(?:is\s+)?(?:complete|done)\b", "step_done"),
]

# ── Soft completion patterns ───────────────────────────────────────────────────
# Only fire when a path/file reference is also present in the same message.
# Reduces false positives on conversational "done", "complete", etc.
_SOFT_PATTERNS = [
    (r"\bdeployed\b",       "deployed"),
    (r"\binstalled\b",      "installed"),
    (r"\bimplemented\b",    "implemented"),
    (r"\bcomplete(?:d)?\b", "completed"),
    (r"\bfinished\b",       "finished"),
    (r"\bdone\b",           "done"),
]

# Signal that a soft pattern is referring to a file/system artifact
_PATH_SIGNAL = re.compile(
    r"/a0/|\.py\b|\.json\b|\.sh\b|\.md\b|"
    r"\bextension\b|\bdeployed to\b|\binstalled to\b"
)

# Gate's own marker — prevent self-triggering
_GATE_MARKER = "[VERIFICATION GATE]"

# ── Verification prompts ───────────────────────────────────────────────────────
_PROMPT_PY_FILE = (
    "[VERIFICATION GATE] You claimed this task is complete. "
    "You wrote or modified a Python file. Before finalizing:\n"
    "1. Run grep or find: is this module imported anywhere in the active codebase?\n"
    "2. If nothing imports it, the artifact exists but is not integrated — wire it in.\n"
    "3. Show the command output. Do not reason from memory."
)

_PROMPT_GENERIC = (
    "[VERIFICATION GATE] You claimed this task is complete. Before finalizing:\n"
    "1. State the concrete deliverable: filename, config key, or test result.\n"
    "2. Run ONE tool call proving the deliverable is integrated — not just that the "
    "artifact exists, but that something uses it or the expected behaviour is observable.\n"
    "3. If the check fails, the task is not complete. Revise.\n"
    "Do not answer from memory. Run the check."
)

# ── Agent attribute keys ───────────────────────────────────────────────────────
_FIRED_KEY        = "_vgate_fired"
_AWAITING_KEY     = "_vgate_awaiting_outcome"
_TRIGGER_KEY      = "_vgate_trigger_label"
_PHRASE_KEY       = "_vgate_trigger_phrase"
_CONTEXT_KEY      = "_vgate_trigger_context"
_FIRED_LEN_KEY    = "_vgate_fired_at_len"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _journal_path() -> Optional[str]:
    for path in _JOURNAL_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def _log(path: Optional[str], record: dict) -> None:
    if not path:
        return
    try:
        record.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        with open(path, "a") as fh:
            fh.write(json.dumps(record) + "\n")
    except Exception as e:
        print(f"[VGATE] Journal write failed: {e}", flush=True)


def _get_last_ai_text(loop_data: LoopData) -> str:
    """Return the text content of the last AI output — monologue str OR response tool args."""
    for msg in reversed(loop_data.history_output or []):
        if not isinstance(msg, dict):
            continue
        if not msg.get("ai", True):
            continue
        content = msg.get("content", "")
        # Path 1: plain string monologue
        if isinstance(content, str) and content.strip():
            if _GATE_MARKER in content:
                continue
            return content
        # Path 2: response tool call — completion language lives in tool_args text
        if isinstance(content, dict) and content.get("tool_name") == "response":
            args = content.get("tool_args", {}) or {}
            text = args.get("text") or args.get("message") or ""
            if isinstance(text, str) and text.strip():
                if _GATE_MARKER in text:
                    continue
                return text
    return ""


def _get_last_tool_call(loop_data: LoopData) -> Optional[dict]:
    """Return last non-response tool call {tool_name, tool_result}, or None."""
    for msg in reversed(loop_data.history_output or []):
        if not isinstance(msg, dict):
            continue
        if msg.get("ai", True):
            continue
        content = msg.get("content", "")
        if not isinstance(content, dict):
            continue
        tool_name = content.get("tool_name", "")
        if not tool_name or tool_name == "response":
            continue
        return {
            "tool_name": tool_name,
            "tool_result": str(content.get("tool_result", ""))[:300],
        }
    return None


def _detect_completion(text: str) -> tuple:
    """
    Scan text for completion language.
    Returns (label, matched_phrase) or ("", "") if no match.
    """
    if not text or _GATE_MARKER in text:
        return "", ""

    lower = text.lower()

    for pattern, label in _HARD_PATTERNS:
        m = re.search(pattern, lower)
        if m:
            return label, m.group(0)

    if _PATH_SIGNAL.search(text):
        for pattern, label in _SOFT_PATTERNS:
            m = re.search(pattern, lower)
            if m:
                return label, m.group(0)

    return "", ""


def _is_py_write_context(tool: Optional[dict]) -> bool:
    """True if the last tool call before the gate fired wrote a .py file."""
    if not tool:
        return False
    name = tool.get("tool_name", "")
    result = tool.get("tool_result", "")
    return ".py" in result or name in ("code_execution_tool", "file_write", "save_file")


# ── Extension ─────────────────────────────────────────────────────────────────

class VerificationGate(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        try:
            journal   = _journal_path()
            hist_len  = len(loop_data.history_output or [])

            # ── Phase A: Record outcome from previous gate firing ──────────────
            if getattr(self.agent, _AWAITING_KEY, False):
                fired_at = getattr(self.agent, _FIRED_LEN_KEY, 0)

                if hist_len - fired_at > 10:
                    # History grew too much — likely a different task; skip outcome
                    print("[VGATE] Task appears to have changed — skipping outcome.", flush=True)
                else:
                    last_tool = _get_last_tool_call(loop_data)
                    if last_tool:
                        outcome_type    = "tool_called"
                        outcome_tool    = last_tool["tool_name"]
                        outcome_snippet = last_tool["tool_result"]
                    else:
                        outcome_type    = "verbal_only"
                        outcome_tool    = "none"
                        outcome_snippet = _get_last_ai_text(loop_data)[:200]

                    _log(journal, {
                        "action":           "verification_gate_outcome",
                        "trigger_label":    getattr(self.agent, _TRIGGER_KEY, "unknown"),
                        "trigger_phrase":   getattr(self.agent, _PHRASE_KEY,  "unknown"),
                        "outcome_type":     outcome_type,
                        "outcome_tool":     outcome_tool,
                        "outcome_snippet":  outcome_snippet,
                        "status":           "recorded",
                    })
                    print(
                        f"[VGATE] Outcome recorded: {outcome_type} via {outcome_tool}",
                        flush=True,
                    )

                # Reset — gate can fire again on next completion claim
                setattr(self.agent, _AWAITING_KEY, False)
                setattr(self.agent, _FIRED_KEY,    False)
                return  # don't scan this same turn for new completion language

            # ── Phase B: Skip if already fired (awaiting outcome) ─────────────
            if getattr(self.agent, _FIRED_KEY, False):
                return

            # ── Phase C: Scan last AI output for completion language ───────────
            last_text = _get_last_ai_text(loop_data)
            if not last_text:
                return

            label, phrase = _detect_completion(last_text)
            if not label:
                return

            # ── Phase D: Fire ──────────────────────────────────────────────────
            last_tool  = _get_last_tool_call(loop_data)
            py_context = _is_py_write_context(last_tool)
            prompt     = _PROMPT_PY_FILE if py_context else _PROMPT_GENERIC

            setattr(self.agent, _FIRED_KEY,     True)
            setattr(self.agent, _AWAITING_KEY,  True)
            setattr(self.agent, _TRIGGER_KEY,   label)
            setattr(self.agent, _PHRASE_KEY,    phrase)
            setattr(self.agent, _CONTEXT_KEY,   last_text[:200])
            setattr(self.agent, _FIRED_LEN_KEY, hist_len)

            _log(journal, {
                "action":               "verification_gate_fired",
                "trigger_phrase":       phrase,
                "trigger_label":        label,
                "trigger_context":      last_text[:200],
                "last_tool_before_fire": last_tool.get("tool_name") if last_tool else None,
                "prompt_variant":       "py_file" if py_context else "generic",
                "status":               "injected",
            })

            self.agent.intervention = UserMessage(message=prompt)

            print(
                f"[VGATE] Gate fired — trigger='{phrase}' ({label}), "
                f"prompt={'py_file' if py_context else 'generic'}",
                flush=True,
            )

        except Exception as e:
            print(f"[VGATE] Error (passthrough): {e}", flush=True)
