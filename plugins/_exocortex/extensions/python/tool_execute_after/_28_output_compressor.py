"""
Tool Output Compressor — Agent-Zero Exocortex
==============================================
Hook: tool_execute_after (_28_)

Compresses large tool outputs before they enter conversation history.
Prevents 10K+ docker/shell logs from consuming context window and crowding
out useful turns. Rule-based: deterministic, no LLM calls.

Distinct from context surgery (which operates on old turns in bulk).
This runs per-tool-call, immediately, on the raw output before it's stored.
The two are complementary: this prevents bloat from entering history at all;
surgery later compresses old turns that have accumulated.

Compression rules (applied in order):
  1. Strip ANSI escape codes       — zero information loss
  2. Deduplicate consecutive lines  — common in progress bars, repeat errors
  3. Collapse repetitive patterns   — same line N times → "line [xN]"
  4. Preserve failure lines         — error/exception/traceback/critical always kept
  5. Head + tail window             — keep first 30 + last 30 lines, omit middle
     with a "[... N lines omitted ...]" marker

Trigger: output > OUTPUT_TOKEN_THRESHOLD estimated tokens (approx chars/4).
Below that, the output is small enough that compression isn't worth it.

The one exception to head + tail: A0's "tool not found" response (Opus ruling 5, 2026-09-24).
When a call names a tool that does not exist, A0's Unknown tool answers "Tool <name> not
found. Available tools:" followed by the WHOLE tools prompt (~11K tokens on agent-zero-v2).
Head + tail kept the first and last 30 lines of that list and dropped the middle. In cycle
#751 the dropped middle held `memory_save`, the tool she needed. She read the kept list,
concluded memory_save "isn't callable", and, following her no-guessing rule, skipped the
save. The names ARE the recovery information, so for this one response shape the compressor
now keeps every tool name, grouped under its section, and drops the descriptions, which are
already in her system prompt. The shape is recognised from the response text, starting
"Tool <this call's tool_name> not found" (or "does not exist"). If no names can be
extracted (A0 changed the prompt format), it falls back to head + tail as before.

Config (from /a0/usr/plugins/_exocortex/config/config.json under "output_compressor"):
  enabled:          bool (default True)
  token_threshold:  int  (default 800)
  head_lines:       int  (default 30)
  tail_lines:       int  (default 30)
  preserve_patterns: list[str] — additional regex patterns to never omit
"""

import re
from typing import Any

from agent import LoopData
from helpers.extension import Extension

# ── Constants ────────────────────────────────────────────────────────────────

CONFIG_KEY         = "output_compressor"
LOG_TAG            = "[OUT-COMPRESS]"
DEFAULT_THRESHOLD  = 800    # estimated tokens before compression fires
DEFAULT_HEAD_LINES = 30
DEFAULT_TAIL_LINES = 30

# ANSI escape sequence pattern
_ANSI_RE = re.compile(r'\x1b\[[0-9;]*[mGKHF]|\x1b\[[0-9;]*[a-zA-Z]|\r')

# Failure signal patterns — lines matching these are NEVER omitted
# even when they fall in the middle of a large output.
_FAILURE_PATTERNS = [
    re.compile(r'\b(?:error|exception|traceback|critical|fatal)\b', re.IGNORECASE),
    re.compile(r'\b(?:failed|failure|abort|panic)\b', re.IGNORECASE),
    re.compile(r'^\s*at\s+[\w.<>$]+\(', re.IGNORECASE),  # Java/JS stack frames
    re.compile(r'File ".*", line \d+'),                    # Python tracebacks
    re.compile(r'^\s*Traceback \(most recent call last\)'),
]

# Tools to never compress — outputs that are inherently structured or
# small enough that compression would destroy the signal
_SKIP_TOOLS = frozenset({
    "response",
    "memory_load",
    "memory_save",
    "stack_status",
})


# ── Extension ────────────────────────────────────────────────────────────────

class ToolOutputCompressor(Extension):
    """Compress large tool outputs before they enter conversation history.

    Fires after every tool execution. Compresses only when output exceeds
    the token threshold. Transparent to the model — compressed output still
    contains the first/last N lines plus any failure lines.
    """

    async def execute(self, tool_name: str = "", response: Any = None,
                      loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            cfg = _load_cfg(self.agent)
            if not cfg.get("enabled", True):
                return

            if not tool_name or tool_name in _SKIP_TOOLS:
                return

            if response is None:
                return

            # Extract text from response object
            text = _extract_text(response)
            if not text:
                return

            threshold = cfg.get("token_threshold", DEFAULT_THRESHOLD)
            estimated_tokens = len(text) // 4
            if estimated_tokens <= threshold:
                return  # Small enough — no compression needed

            head_lines = cfg.get("head_lines", DEFAULT_HEAD_LINES)
            tail_lines = cfg.get("tail_lines", DEFAULT_TAIL_LINES)
            extra_patterns = [
                re.compile(p, re.IGNORECASE)
                for p in cfg.get("preserve_patterns", [])
                if p
            ]

            # A "tool not found" response keeps every tool name (ruling 5; see the docstring).
            names_view = _tool_names_view(text, tool_name) if _is_not_found(text, tool_name) else ""
            if names_view:
                compressed = names_view
            else:
                compressed = _compress(text, head_lines, tail_lines, extra_patterns)

            if compressed == text:
                return  # Compression produced no change (short output, edge case)

            # Write compressed text back to response
            _write_text(response, compressed)

            original_tok = estimated_tokens
            compressed_tok = len(compressed) // 4
            saved = original_tok - compressed_tok
            pct = int(100 * saved / original_tok) if original_tok else 0

            msg = (
                f"{LOG_TAG} {tool_name}: {original_tok}→{compressed_tok} "
                f"est. tokens ({pct}% reduction)"
                + (" [not-found: every tool name kept]" if names_view else "")
            )
            print(msg, flush=True)
            try:
                self.agent.context.log.log(type="info", content=msg)
            except Exception:
                pass

        except Exception as exc:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"{LOG_TAG} Error (passthrough): {exc}",
                )
            except Exception:
                pass


# ── "Tool not found": keep every tool name (Opus ruling 5) ────────────────────
# Header shapes in A0 v2.12's tools prompt (prompts/agent.system.mcp_*.md, the tool prompts):
#   ## <section>                                   a section, e.g. "## available tools"
#   ### <name>  (optionally "### <name>:")          a local tool
#   ### MCP server `<server>` (group only; not a tool)
#   #### MCP tool `<server>.<tool>`                 an MCP tool
_NF_HEAD   = r"\s*Tool\s+[\"'`]?{name}[\"'`]?\s+(?:not found|does not exist)"
_SECTION   = re.compile(r"^##\s+(?!#)(.+?)\s*$")
_MCP_GROUP = re.compile(r"^###\s+MCP server\s+`([^`]+)`")
_MCP_TOOL  = re.compile(r"^####\s+MCP tool\s+`([^`]+)`")
_LOCAL     = re.compile(r"^###\s+(?!MCP server\b)([A-Za-z0-9_.:-]+?):?\s*$")
# A0's own declaration shape (helpers/responses_tools.py TOOL_DECLARATION_PATTERN), used by
# prompts that list several tools under one "## ..." section, e.g. the _memory plugin's
# "- `memory_save`: args `text`, ...". Missing this rule lost memory_save on her real prompts.
_DECLARED  = re.compile(r"^\s*-\s+`([A-Za-z0-9_-]{1,64})`:\s+args?\b", re.IGNORECASE)
# A prompt titled with a level-1 heading, e.g. "# code_execution_remote tool" (_a0_connector).
# A0 names such a tool from its first heading's first token; only a lone name (optionally
# followed by "tool") is accepted here, so a titled section can never read as a tool.
_TITLE     = re.compile(r"^#\s+([A-Za-z0-9_-]{1,64})(?:\s+tool)?\s*$", re.IGNORECASE)


def _is_not_found(text: str, tool_name: str) -> bool:
    """True when `text` is A0's Unknown-tool answer for THIS call's tool name."""
    if not tool_name:
        return False
    return re.match(_NF_HEAD.format(name=re.escape(tool_name)), text) is not None


def _tool_names_view(text: str, tool_name: str) -> str:
    """The not-found response with every tool name kept and the descriptions dropped.

    Returns "" when no tool name can be found (the prompt format changed), so the caller
    falls back to head + tail instead of sending an empty list."""
    groups: list[tuple[str, list[str]]] = []      # (label, names), in the order they appear
    seen: set[str] = set()

    def current(label: str) -> list[str]:
        if not groups or groups[-1][0] != label:
            groups.append((label, []))
        return groups[-1][1]

    label = "tools"
    # Stock v2.12's fw.tool_not_found.md joins its first line to the list with a LITERAL "\n"
    # (backslash + n), so split on that too, or the first section header shares a line.
    for raw in _ANSI_RE.sub("", text).replace("\\n", "\n").splitlines():
        line = raw.rstrip()
        m = _MCP_GROUP.match(line)
        if m:
            label = f"MCP server `{m.group(1)}` (a group, not a tool)"
            continue
        m = _MCP_TOOL.match(line) or _LOCAL.match(line) or _DECLARED.match(line) or _TITLE.match(line)
        if m:
            name = m.group(1)
        else:
            s = _SECTION.match(line)
            if s:
                label = s.group(1).strip()
            continue
        if name and name not in seen:
            seen.add(name)
            current(label).append(name)

    if not seen:
        return ""
    first = text.lstrip().splitlines()[0]
    head = re.match(r"(.*?(?:not found|does not exist)\.?)", first)
    out = [head.group(1) if head else f"Tool {tool_name} not found.",
           f"Available tools, by exact name ({len(seen)}). Their descriptions are in your "
           "system prompt. Call one of these names exactly:"]
    for lbl, names in groups:
        if names:
            out.append(f"- {lbl}: " + ", ".join(names))
    return "\n".join(out)


# ── Compression logic ─────────────────────────────────────────────────────────

def _compress(
    text: str,
    head_lines: int,
    tail_lines: int,
    extra_preserve: list,
) -> str:
    """Apply all compression rules and return compressed text."""

    # Rule 1: Strip ANSI escape codes
    text = _ANSI_RE.sub('', text)

    lines = text.splitlines()
    total = len(lines)

    if total <= head_lines + tail_lines:
        # Short enough after ANSI strip — apply dedup only
        lines = _dedup_consecutive(lines)
        return '\n'.join(lines)

    # Rule 2+3: Dedup consecutive identical lines on head and tail windows
    head = _dedup_consecutive(lines[:head_lines])
    tail = _dedup_consecutive(lines[-tail_lines:])
    middle = lines[head_lines:-tail_lines]
    omitted = len(middle)

    # Rule 4: Pull failure lines out of the middle (preserve them)
    all_preserve = list(_FAILURE_PATTERNS) + extra_preserve
    rescued = [
        line for line in middle
        if any(p.search(line) for p in all_preserve)
    ]

    # Build output
    parts = head[:]

    if rescued:
        if omitted - len(rescued) > 0:
            parts.append(f"[... {omitted - len(rescued)} lines omitted ...]")
        parts.extend(rescued)
    else:
        parts.append(f"[... {omitted} lines omitted ...]")

    parts.extend(tail)
    return '\n'.join(parts)


def _dedup_consecutive(lines: list[str]) -> list[str]:
    """Collapse runs of identical consecutive lines into 'line [xN]'."""
    if not lines:
        return lines

    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        run = 1
        while i + run < len(lines) and lines[i + run] == line:
            run += 1
        if run > 3:
            result.append(f"{line} [x{run}]")
        else:
            result.extend([line] * run)
        i += run
    return result


# ── Response helpers ──────────────────────────────────────────────────────────

def _extract_text(response: Any) -> str:
    """Extract text content from an A0 Response object or dict."""
    # Agent Zero Response objects have a .message attribute
    if hasattr(response, 'message'):
        msg = response.message
        if isinstance(msg, str):
            return msg
        if isinstance(msg, dict):
            return str(msg.get('text', msg.get('content', '')))
    # Dict fallback
    if isinstance(response, dict):
        return str(response.get('message', response.get('text', response.get('content', ''))))
    # String fallback
    if isinstance(response, str):
        return response
    return ''


def _write_text(response: Any, text: str) -> None:
    """Write compressed text back to response object."""
    if hasattr(response, 'message') and isinstance(response.message, str):
        response.message = text
    elif hasattr(response, 'message') and isinstance(response.message, dict):
        key = 'text' if 'text' in response.message else 'content'
        response.message[key] = text
    elif isinstance(response, dict):
        key = 'message' if 'message' in response else 'text' if 'text' in response else 'content'
        response[key] = text


# ── Config ────────────────────────────────────────────────────────────────────

_CONFIG_PATH = "/a0/usr/plugins/_exocortex/config/config.json"


def _load_cfg(agent) -> dict:
    try:
        import json
        import os
        if os.path.exists(_CONFIG_PATH):
            data = json.loads(open(_CONFIG_PATH).read())
            return data.get(CONFIG_KEY, {})
    except Exception:
        pass
    return {}
