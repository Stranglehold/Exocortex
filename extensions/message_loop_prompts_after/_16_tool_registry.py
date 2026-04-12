"""
Dynamic Tool Registry — Agent-Zero Exocortex
=============================================
Hook: message_loop_prompts_after (_16_)

Scans the user plugin tools directory every turn and injects a compact
[CUSTOM TOOLS] block into the last user message so the model always knows
which tools are callable — by name, without hallucinating their existence
or manually reimplementing them.

Problem solved: Agent Zero auto-discovers Tool subclasses at container init,
but custom tool names are never surfaced in the per-turn system context.
The model explores the filesystem or reimplements tools it could just call.

Grows automatically: as new tools are added (docker cp, skill installs, or
agent-installed programs), they appear in the next turn without config changes.

Tool name derivation: CamelCase class name → snake_case (matches A0 dispatch).
Example: OssHealth → oss_health, SwarmfishPredict → swarmfish_predict

Scan paths (in order):
  1. /a0/usr/plugins/exocortex/tools/     — primary Exocortex tools
  2. /a0/usr/plugins/<name>/tools/         — other user-installed plugins
  3. /a0/usr/Exocortex/tool_manifest.json — installed programs (nmap, etc.)

No LLM calls. Fully deterministic. Runs early (order 16) so the tool list
is visible to all subsequent extensions and to the main LLM call.
"""

import ast
import json
import os
import re
import textwrap
from typing import Any, Optional

from agent import LoopData
from helpers.extension import Extension

# ── Constants ────────────────────────────────────────────────────────────────

CONFIG_KEY = "tool_registry"

# Primary tool scan path — exocortex user plugins
PRIMARY_TOOL_DIR = "/a0/usr/plugins/exocortex/tools"

# Root for scanning other user plugin tool directories
USER_PLUGIN_ROOT = "/a0/usr/plugins"

# Manifest for agent-installed programs (nmap, etc.)
TOOL_MANIFEST_PATH = "/a0/usr/Exocortex/tool_manifest.json"

# Agent Zero native tools — skip files that match these names.
# These are documented in A0 prompts already; we only add custom ones.
NATIVE_TOOLS = frozenset({
    "response", "a2a_chat", "behaviour_adjustment", "browser_agent",
    "call_subordinate", "code_execution_tool", "document_query", "input",
    "memory_load", "memory_save", "memory_delete", "memory_forget",
    "notify_user", "search_engine", "skills_tool", "text_editor",
    "camofox_session", "camofox_auth", "camofox_browse", "camofox_media",
    "camofox_admin", "camofox_eval",
    # agentevolver tools — internal, not for general use
    "self_questioning_tool",
})

# Max description length per file entry
DESC_MAX_LEN = 90

LOG_TAG = "[TOOL-REG]"


# ── Extension ────────────────────────────────────────────────────────────────

class DynamicToolRegistry(Extension):
    """Inject [CUSTOM TOOLS] block into per-turn context."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
        try:
            cfg = _load_config(self.agent)
            if not cfg.get("enabled", True):
                return

            # Scan tool files
            tool_entries = _scan_tool_dirs()

            # Load manifest programs
            programs = _load_manifest()

            if not tool_entries and not programs:
                return

            # Build block
            block = _build_block(tool_entries, programs)

            # Inject into last user message
            _inject(loop_data, block)

            total_tools = sum(len(e["names"]) for e in tool_entries)
            msg = (
                f"{LOG_TAG} Injected {total_tools} custom tool(s) "
                f"from {len(tool_entries)} file(s), "
                f"{len(programs)} program(s)"
            )
            print(msg, flush=True)
            try:
                self.agent.context.log.log(type="info", content=msg, flush=True)
            except Exception:
                pass

        except Exception as exc:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"{LOG_TAG} Error (passthrough): {exc}",
                    flush=True,
                )
            except Exception:
                pass


# ── Scan ─────────────────────────────────────────────────────────────────────

def _scan_tool_dirs() -> list[dict]:
    """
    Scan all tool directories and return a list of entries:
      {"names": [snake_case, ...], "desc": "...", "file": "stem"}

    Primary path first, then other user plugins. Skips native tools.
    Groups multiple Tool subclasses from the same file under one entry.
    """
    entries: list[dict] = []
    seen_files: set[str] = set()

    # Primary: /a0/usr/plugins/exocortex/tools/
    if os.path.isdir(PRIMARY_TOOL_DIR):
        for fn in sorted(os.listdir(PRIMARY_TOOL_DIR)):
            if fn.endswith(".py") and not fn.startswith("_"):
                path = os.path.join(PRIMARY_TOOL_DIR, fn)
                entry = _parse_tool_file(path)
                if entry:
                    entries.append(entry)
                    seen_files.add(os.path.basename(path))

    # Secondary: other user plugins (skip exocortex — already scanned)
    if os.path.isdir(USER_PLUGIN_ROOT):
        for plugin_name in sorted(os.listdir(USER_PLUGIN_ROOT)):
            if plugin_name in ("exocortex",):
                continue
            tool_dir = os.path.join(USER_PLUGIN_ROOT, plugin_name, "tools")
            if not os.path.isdir(tool_dir):
                continue
            for fn in sorted(os.listdir(tool_dir)):
                if fn.endswith(".py") and not fn.startswith("_") and fn not in seen_files:
                    path = os.path.join(tool_dir, fn)
                    entry = _parse_tool_file(path)
                    if entry:
                        entries.append(entry)
                        seen_files.add(fn)

    return entries


def _parse_tool_file(path: str) -> Optional[dict]:
    """
    Parse a tool file with ast (no import). Returns:
      {"names": [snake_case, ...], "desc": "...", "file": "stem"} or None.

    Extracts:
    - Module docstring first line → description
    - All `class X(Tool)` / `class X(tools.Tool)` → snake_case names

    Returns None if no Tool subclasses found or all names are native.
    """
    try:
        src = open(path, encoding="utf-8").read()
        tree = ast.parse(src)
    except Exception:
        return None

    # Module docstring
    doc = ast.get_docstring(tree) or ""
    first_line = next((ln.strip() for ln in doc.splitlines() if ln.strip()), "")
    desc = textwrap.shorten(first_line, DESC_MAX_LEN)

    # Tool subclasses
    names = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        is_tool = any(
            (isinstance(b, ast.Name) and b.id == "Tool") or
            (isinstance(b, ast.Attribute) and b.attr == "Tool")
            for b in node.bases
        )
        if is_tool:
            snake = _to_snake(node.name)
            if snake not in NATIVE_TOOLS:
                names.append(snake)

    if not names:
        return None

    stem = os.path.splitext(os.path.basename(path))[0]
    return {"names": names, "desc": desc, "file": stem}


def _to_snake(name: str) -> str:
    """Convert CamelCase to snake_case (matches Agent Zero dispatch logic)."""
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return s.lower()


# ── Manifest ─────────────────────────────────────────────────────────────────

def _load_manifest() -> dict[str, str]:
    """
    Load installed programs from tool_manifest.json.
    Creates an empty manifest if the file doesn't exist yet.
    Returns {name: description} or {}.
    """
    if not os.path.exists(TOOL_MANIFEST_PATH):
        try:
            os.makedirs(os.path.dirname(TOOL_MANIFEST_PATH), exist_ok=True)
            with open(TOOL_MANIFEST_PATH, "w") as f:
                json.dump({"programs": {}}, f, indent=2)
        except Exception:
            pass
        return {}
    try:
        data = json.loads(open(TOOL_MANIFEST_PATH).read())
        return data.get("programs", {})
    except Exception:
        return {}


# ── Block builder ─────────────────────────────────────────────────────────────

def _build_block(entries: list[dict], programs: dict[str, str]) -> str:
    """
    Build the [CUSTOM TOOLS] block.

    Format (one line per file, comma-separated names if multiple classes):
      [CUSTOM TOOLS — call by tool_name]
      stack_status — Exocortex Stack Introspection Tool.
      oss_topic, oss_drift, oss_health, oss_submit, ... → OSS intelligence ledger.
      swarmfish_predict, swarmfish_calibration → SWARMFISH geopolitical consensus.
      tla_check — TLA+ model checker.

      [INSTALLED PROGRAMS]
      nmap — Network scanner (use via code_execution_tool)
      [/CUSTOM TOOLS]
    """
    lines = ["[CUSTOM TOOLS — call by tool_name]"]

    for entry in entries:
        names = entry["names"]
        desc = entry["desc"]
        if len(names) == 1:
            lines.append(f"  {names[0]} — {desc}")
        else:
            # Multi-tool file: comma-sep names, then arrow + desc
            name_str = ", ".join(names)
            lines.append(f"  {name_str} → {desc}")

    if programs:
        lines.append("")
        lines.append("  [INSTALLED PROGRAMS]")
        for prog_name, prog_desc in programs.items():
            lines.append(f"  {prog_name} — {prog_desc}")

    lines.append("[/CUSTOM TOOLS]")
    return "\n".join(lines)


# ── Injection ─────────────────────────────────────────────────────────────────

def _inject(loop_data: LoopData, block: str) -> None:
    """
    Prepend the [CUSTOM TOOLS] block to the last user message in history_output.

    history_output is a list of OutputMessage dicts: {"ai": bool, "content": str|...}
    We find the last non-AI message and prepend the block to its content.
    """
    history = getattr(loop_data, "history_output", None)
    if not history:
        return

    # Find the last user message (ai=False)
    for msg in reversed(history):
        if not msg.get("ai", True):
            existing = msg.get("content", "")
            if isinstance(existing, str):
                msg["content"] = block + "\n\n" + existing
            else:
                # Non-string content (list/dict) — prepend as separate string entry
                # by converting to string and prepending
                msg["content"] = block + "\n\n" + str(existing)
            return

    # No user message found — this shouldn't happen in normal operation
    # but don't crash; the model will just lack the block this turn


# ── Config ────────────────────────────────────────────────────────────────────

_CONFIG_PATH = "/a0/usr/Exocortex/config.json"


def _load_config(agent) -> dict:
    try:
        if os.path.exists(_CONFIG_PATH):
            data = json.loads(open(_CONFIG_PATH).read())
            return data.get(CONFIG_KEY, {})
    except Exception:
        pass
    return {}
