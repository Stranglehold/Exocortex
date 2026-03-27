"""
Completion State Tracker — Agent-Zero Hardening Layer
======================================================
Hook: before_main_llm_call
Priority: _12 (after BST _11, before HTN _15)

Fixes: comprehension-without-absorption loop
-----------------------------------------------
Root cause: After executing a tool, the model's next turn re-derives
"I should do X" from its planning chain without registering "X is done."
Stock A0 has no mechanism to inject completion state BEFORE the LLM call
— the loop detector fires reactively after the repeated response is
already generated, and "same message" string-match is too narrow.

This extension reads the last N tool call/result pairs from
history_output and injects a [COMPLETION STATE] block via
extras_temporary before each LLM call. The model sees:
  "code_execution_tool: python3 trace_analyzer.py → [DONE] exit 0"
before reasoning about next steps. It cannot re-derive the same
action without explicitly acknowledging the completion.

No model calls. No config required. Works on stock Agent Zero.
Compatible with HTN (_15) — they use different extras_temporary keys.

Storage: loop_data.extras_temporary["completion_state"]
Log tag: [COMPLETION]
"""

import json
import re
from typing import Any, Optional

from agent import LoopData
from python.helpers.extension import Extension

# ── Configuration ─────────────────────────────────────────────────────────────

MAX_HISTORY_TOOLS = 5    # Max completed actions to show
MAX_OUTPUT_LINES  = 4    # Lines of output to preview per action
MAX_OUTPUT_CHARS  = 250  # Chars per output preview (before truncation)
MAX_CMD_CHARS     = 80   # Max length of command hint

# Tools that don't need completion tracking (internal A0 infrastructure)
SKIP_TOOLS = {"response"}

# Key written to extras_temporary
COMPLETION_KEY = "completion_state"


class CompletionTracker(Extension):
    """before_main_llm_call: injects recent tool completion state before LLM reasoning."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
        try:
            if not loop_data.history_output:
                return

            pairs = _extract_tool_pairs(loop_data.history_output)
            if not pairs:
                return

            # Keep only the last N completions
            recent = pairs[-MAX_HISTORY_TOOLS:]

            block = _build_block(recent)
            if block:
                # Prepend to last user message (stronger than extras_temporary —
                # user messages are processed before extras appendix, so this
                # survives deep-loop history pressure that overwhelms extras)
                user_msg = _get_last_user_message(loop_data.history_output)
                if user_msg:
                    existing = user_msg.get("content", "")
                    user_msg["content"] = block + "\n\n" + str(existing)
                else:
                    # Fallback: extras_temporary if no user message found
                    loop_data.extras_temporary[COMPLETION_KEY] = block

                tool_names = ", ".join(p["tool"] for p in recent)
                self.agent.context.log.log(
                    type="util",
                    content=f"[COMPLETION] Injected {len(recent)} completed action(s): {tool_names}",
                )

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[COMPLETION] Error (passthrough): {e}",
                )
            except Exception:
                pass


# ── History Parsing ────────────────────────────────────────────────────────────

def _extract_tool_pairs(history: list) -> list[dict]:
    """
    Walk history forward, pairing AI tool-call messages with their
    subsequent user-role tool-result messages.

    History structure in Agent Zero:
      - AI message:   msg["ai"] = True,  msg["content"] = JSON string
                      (raw model JSON, e.g. {"tool_name": "code_execution_tool", "tool_args": {...}})
      - Tool result:  msg["ai"] = False, msg["content"] = {"tool_name": "...", "tool_result": "..."}

    Returns list of dicts with: tool, cmd_hint, output, status
    """
    pairs = []
    pending_tool = None  # name of the most recent AI tool call, awaiting its result

    for msg in history:
        if not isinstance(msg, dict):
            continue

        ai = msg.get("ai", True)
        content = msg.get("content", "")

        if ai:
            # AI message — extract tool_name from JSON content
            tool_name = _parse_ai_tool_name(content)
            if tool_name and tool_name not in SKIP_TOOLS:
                pending_tool = {"name": tool_name, "args": _parse_ai_tool_args(content)}
            else:
                pending_tool = None

        else:
            # User-role message — check if it's a tool result
            if not isinstance(content, dict):
                continue
            tool_name = content.get("tool_name", "")
            tool_result = content.get("tool_result", "")

            if not tool_name or tool_name in SKIP_TOOLS:
                continue

            # Build completion record
            cmd_hint = _build_cmd_hint(tool_name, pending_tool, tool_result)
            status = _classify_status(tool_result)
            output = _truncate_output(tool_result)

            pairs.append({
                "tool": tool_name,
                "cmd": cmd_hint,
                "status": status,
                "output": output,
            })
            pending_tool = None  # consumed

    return pairs


def _parse_ai_tool_name(content) -> str:
    """Extract tool_name from AI message content (JSON string or dict)."""
    if isinstance(content, dict):
        return content.get("tool_name", "")
    if isinstance(content, str) and content.strip().startswith("{"):
        try:
            data = json.loads(content.strip())
            if isinstance(data, dict):
                return data.get("tool_name", "")
        except Exception:
            pass
        # Fallback: regex for tool_name key
        m = re.search(r'"tool_name"\s*:\s*"([^"]+)"', content)
        if m:
            return m.group(1)
    return ""


def _parse_ai_tool_args(content) -> dict:
    """Extract tool_args from AI message content. Returns {} on failure."""
    if isinstance(content, dict):
        return content.get("tool_args", {}) or {}
    if isinstance(content, str) and content.strip().startswith("{"):
        try:
            data = json.loads(content.strip())
            if isinstance(data, dict):
                return data.get("tool_args", {}) or {}
        except Exception:
            pass
    return {}


# ── Command Hint Extraction ────────────────────────────────────────────────────

def _build_cmd_hint(tool_name: str, pending: dict | None, tool_result: str) -> str:
    """
    Build a concise command/action hint string.
    Prefers tool_args from the AI message; falls back to output parsing.
    """
    args = (pending or {}).get("args", {})

    if tool_name == "code_execution_tool":
        # Prefer code field from args
        code = args.get("code", "")
        if code:
            first_line = code.strip().splitlines()[0].strip()
            return first_line[:MAX_CMD_CHARS]
        # Fall back: look for shell command in output header
        for line in tool_result.strip().splitlines()[:3]:
            line = line.strip()
            if re.match(r'^(python|python3|bash|sh|pip|pip3|apt|npm|node|curl|wget|git|ls|cat|cp|mv|rm|mkdir|cd|echo)\b', line):
                return line[:MAX_CMD_CHARS]
        return ""

    elif tool_name == "memory_save":
        # Show memory key/area
        key = args.get("memory_key", args.get("key", ""))
        area = args.get("area", "")
        if key:
            hint = f"key={key}"
            if area:
                hint += f" area={area}"
            return hint[:MAX_CMD_CHARS]
        return ""

    elif tool_name == "memory_load":
        query = args.get("query", "")
        return f"query={query[:60]}" if query else ""

    elif tool_name == "search_engine":
        query = args.get("query", "")
        return f"query={query[:60]}" if query else ""

    elif tool_name == "call_subordinate":
        msg = args.get("message", "")
        return msg[:60] if msg else ""

    elif tool_name == "skills_tool":
        name = args.get("skill_name", args.get("name", ""))
        return name[:60] if name else ""

    return ""


# ── Status Classification ──────────────────────────────────────────────────────

def _classify_status(output: str) -> str:
    """Classify tool output as done, error, or ok."""
    low = output.lower()
    if any(s in low for s in [
        "error:", "traceback", "exception:", "failed:", "errno",
        "exit code 1", "exit code: 1", "exit 1",
        "syntax error", "no such file", "command not found",
        "permission denied", "connection refused",
    ]):
        return "ERROR"
    if any(s in low for s in [
        "successfully", "success", "done", "complete",
        "saved", "created", "installed", "ok\n", " ok ", "\nok",
        "exit code 0", "exit code: 0", "exit 0",
    ]):
        return "OK"
    return "DONE"


# ── Output Truncation ──────────────────────────────────────────────────────────

def _truncate_output(output: str) -> str:
    """Return first MAX_OUTPUT_CHARS / MAX_OUTPUT_LINES of output, stripped."""
    output = output.strip()
    if not output:
        return ""
    lines = output.splitlines()
    preview_lines = lines[:MAX_OUTPUT_LINES]
    preview = "\n".join(preview_lines)
    if len(preview) > MAX_OUTPUT_CHARS:
        preview = preview[:MAX_OUTPUT_CHARS] + "..."
    if len(lines) > MAX_OUTPUT_LINES:
        preview += f"\n  ... ({len(lines) - MAX_OUTPUT_LINES} more lines)"
    return preview


# ── Block Builder ──────────────────────────────────────────────────────────────

def _build_block(completions: list[dict]) -> str:
    """Build the [COMPLETION STATE] injection block."""
    lines = [f"[COMPLETION STATE — last {len(completions)} action(s)]"]

    for i, c in enumerate(completions, 1):
        tool    = c["tool"]
        cmd     = c["cmd"]
        status  = c["status"]
        output  = c["output"]

        # Header line: N. tool_name: cmd → [STATUS]
        header = f"{i}. {tool}"
        if cmd:
            header += f": {cmd}"
        header += f" → [{status}]"
        lines.append(header)

        # Output preview (indented)
        if output:
            for line in output.splitlines():
                lines.append(f"   {line}")

    lines.append("")
    lines.append(
        "These actions are complete. Do NOT repeat them. "
        "Verify the results above and proceed to the NEXT step."
    )
    return "\n".join(lines)


# ── Message Helper ─────────────────────────────────────────────────────────────

def _get_last_user_message(history: list) -> Optional[dict]:
    """Find the most recent operator message in loop history."""
    if not history:
        return None
    for msg in reversed(history):
        if not isinstance(msg, dict):
            continue
        if not msg.get("ai", True):
            content = msg.get("content", "")
            if isinstance(content, dict) and "user_message" in content:
                return msg
            if isinstance(content, str) and content:
                return msg
    return None
