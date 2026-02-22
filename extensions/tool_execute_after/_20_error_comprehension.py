"""
Error Comprehension — Agent-Zero Hardening Layer
=================================================
Hook: tool_execute_after
Priority: _20 (runs BEFORE _30_tool_fallback_logger)

Deterministic error classifier. Parses command output into a structured
diagnosis dict and injects it into agent context before model reasoning.

Addresses two failure modes observed in stress tests:
  - ST-001: Keyword matching cannot distinguish pip warnings from failures
  - ST-002: Model misread interactive prompt as "command not found" under context pressure

Anti-action principle: every error class specifies what NOT to do.
Loop prevention is the primary goal.

Reads:
  - response.message (from hook kwargs)
  - /a0/usr/memory/classification_config.json (error_comprehension section, optional)
Writes:
  - agent._error_diagnosis (via set_data) — cleared at start of each call
  - agent context (via hist_add_warning, if inject_into_context enabled)
"""

import json
import os
import re
from typing import Any

from python.helpers.extension import Extension
from python.helpers.tool import Response

# ── Constants ─────────────────────────────────────────────────────────────────

CONFIG_PATH = "/a0/usr/memory/classification_config.json"
DIAGNOSIS_KEY = "_error_diagnosis"

DEFAULT_CONFIG = {
    "enabled": True,
    "inject_into_context": True,
    "log_prefix": "[ERROR-DX]",
    "max_output_tail_chars": 500,
}

# ── Signal / Indicator Lists ──────────────────────────────────────────────────

SUCCESS_INDICATORS = [
    r"(?i)successfully installed",
    r"(?i)successfully built",
    r"(?i)requirement already satisfied",
    r"(?i)already installed",
    r"(?i)is up to date",
    r"(?i)install complete",
    r"(?i)done\.\s*$",
    r"(?i)^ok\b",
    r"(?i)setting up \S+",
    r"(?i)unpacking \S+",
    r"(?i)processing triggers",
    r"(?i)created wheel for",
    r"(?i)stored in directory:",
]

ERROR_CLASSES = [
    {
        "class": "interactive_prompt",
        "description": "Command waiting for stdin input that cannot be provided",
        "signals": [
            r"(?i)(enter|input|password|key|token|confirm|y/n|press)\s*[:>]\s*$",
            r"(?i)\?\s*$",
            "Potential dialog detected",
        ],
        "anti_signals": [
            r"(?i)successfully",
            r"(?i)complete",
        ],
        "causal_chain": (
            "Command entered interactive mode requiring keyboard input. "
            "This execution environment cannot provide stdin input to running commands."
        ),
        "suggested_actions": [
            "Kill the current terminal session",
            "Use environment variables instead of interactive configuration",
            "Write configuration directly to the config file",
            "Use CLI flags to pass values non-interactively",
        ],
        "anti_actions": [
            "Do NOT retry the same command — it will hang again for the same reason",
            "Do NOT try to 'type' into the prompt — stdin is not connected",
            "Do NOT wait for more output — the command is blocked on input",
        ],
        "confidence": 0.95,
    },
    {
        "class": "terminal_session_hung",
        "description": "Previous command still occupying the terminal session",
        "signals": [
            r"Terminal session \d+ might be still running",
        ],
        "anti_signals": [],
        "causal_chain": (
            "A previous command is still running or hung in this terminal session. "
            "New commands cannot execute until the session is reset."
        ),
        "suggested_actions": [
            "Reset the terminal session (kill the hung process)",
            "Open a new terminal session with a different session ID",
        ],
        "anti_actions": [
            "Do NOT keep checking the session — it will not resolve itself",
            "Do NOT replan the same command — execute the reset first",
        ],
        "confidence": 0.92,
    },
]

# ── Pre-compile all regexes at module level ───────────────────────────────────

_SUCCESS_RX = [re.compile(p) for p in SUCCESS_INDICATORS]

_COMPILED_CLASSES = []
for _cls in ERROR_CLASSES:
    _COMPILED_CLASSES.append({
        **_cls,
        "_sig_rx": [re.compile(s) for s in _cls["signals"]],
        "_anti_rx": [re.compile(a) for a in _cls["anti_signals"]],
    })


# ── Extension ─────────────────────────────────────────────────────────────────

class ErrorComprehension(Extension):
    """Deterministic error classifier for tool output.

    Runs before the fallback logger (_30). Writes structured diagnosis to
    shared agent state so downstream extensions can read it without re-running
    regex classification.
    """

    async def execute(self, response: Response | None = None, **kwargs) -> Any:
        try:
            # Step 1: Always clear previous diagnosis — prevent stale state leaking
            self.agent.set_data(DIAGNOSIS_KEY, None)

            # Step 2: Early exit on no response or empty message
            if not response or not response.message:
                return

            config = _load_config()
            if not config.get("enabled", True):
                return

            msg = response.message
            max_tail = config.get("max_output_tail_chars", 500)

            # Step 3: Success fast path — any SUCCESS_INDICATOR match → no diagnosis
            for rx in _SUCCESS_RX:
                if rx.search(msg):
                    return

            # Step 4: Run classifiers in order, first match wins
            diagnosis = None
            for cls in _COMPILED_CLASSES:
                # Anti-signals first — if any match, skip this class
                skip = False
                for anti_rx in cls["_anti_rx"]:
                    if anti_rx.search(msg):
                        skip = True
                        break
                if skip:
                    continue

                # Signal patterns — any single match is sufficient
                matched_pattern = None
                for sig_rx in cls["_sig_rx"]:
                    if sig_rx.search(msg):
                        matched_pattern = sig_rx.pattern
                        break

                if matched_pattern is not None:
                    tail = msg[-max_tail:] if len(msg) > max_tail else msg
                    diagnosis = {
                        "error_class": cls["class"],
                        "confidence": cls["confidence"],
                        "evidence": [matched_pattern],
                        "causal_chain": cls["causal_chain"],
                        "suggested_actions": cls["suggested_actions"],
                        "anti_actions": cls["anti_actions"],
                        "raw_output_tail": tail,
                    }
                    break

            if diagnosis is None:
                return

            # Step 5: Write diagnosis to shared state
            self.agent.set_data(DIAGNOSIS_KEY, diagnosis)

            # Step 6: Log the classification
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[ERROR-DX] {diagnosis['error_class']}",
                )
            except Exception:
                pass

            # Step 7: Inject compact structured summary into context
            if config.get("inject_into_context", True):
                summary = _format_summary(diagnosis)
                try:
                    self.agent.hist_add_warning(summary)
                except Exception:
                    pass

        except Exception:
            pass


# ── Context Formatting ────────────────────────────────────────────────────────

def _format_summary(diagnosis: dict) -> str:
    """Format diagnosis as compact structured summary for context injection."""
    lines = [
        f"[ERROR-DX] {diagnosis['error_class']} (confidence: {diagnosis['confidence']})",
        f"  What happened: {diagnosis['causal_chain']}",
    ]

    suggested = diagnosis.get("suggested_actions", [])
    if suggested:
        lines.append("")
        lines.append("  Do this:")
        for i, action in enumerate(suggested, 1):
            lines.append(f"  {i}. {action}")

    anti = diagnosis.get("anti_actions", [])
    if anti:
        lines.append("")
        lines.append("  Do NOT:")
        for action in anti:
            lines.append(f"  - {action}")

    return "\n".join(lines)


# ── Config Loading ────────────────────────────────────────────────────────────

def _load_config() -> dict:
    """Load error_comprehension config section with defaults."""
    try:
        if os.path.isfile(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                full = json.load(f)
            section = full.get("error_comprehension", {})
            merged = dict(DEFAULT_CONFIG)
            merged.update(section)
            return merged
    except Exception:
        pass
    return dict(DEFAULT_CONFIG)
