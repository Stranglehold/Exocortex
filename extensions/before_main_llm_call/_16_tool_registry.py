"""
Tool Registry — Dynamic Custom Tool Injection
=============================================
Hook: before_main_llm_call (_16_)

Scans user plugin tool directories every turn and injects a compact
[CUSTOM TOOLS] block into the last user message. Ensures the model
always knows what custom tools are callable by name.

Covers:
  /a0/usr/plugins/*/tools/*.py   — all user-plugin tools

For each file: extracts module docstring (first non-empty line) as
description and all class X(Tool) names -> snake_case as callable tool
names. Uses ast -- no imports, no side effects.

Also reads /a0/usr/Exocortex/tool_manifest.json for installed
programs that the agent or analyst has registered manually.

No LLM calls. Reads only.
"""

import ast
import glob
import json
import os
import re
import textwrap
from typing import Optional

from agent import LoopData
from helpers.extension import Extension

TOOLS_GLOB    = "/a0/usr/plugins/*/tools/*.py"
MANIFEST_PATH = "/a0/usr/Exocortex/tool_manifest.json"

# Files to skip even if they match the glob
SKIP_FILES = {"__init__.py"}

# Known native tool names -- skip if accidentally scanned
NATIVE_TOOLS = {
    "response", "a2a_chat", "behaviour_adjustment", "browser_agent",
    "call_subordinate", "code_execution_tool", "document_query", "input",
    "memory_load", "memory_save", "memory_delete", "memory_forget",
    "notify_user", "search_engine", "skills_tool", "text_editor",
}


def _to_snake(name: str) -> str:
    """CamelCase -> snake_case."""
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name).lower()


def _extract_tool_info(path: str) -> tuple:
    """Parse a tool file with ast. Returns ([tool_names], description)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            src = f.read()
        tree = ast.parse(src)

        doc = ast.get_docstring(tree) or ""
        first_line = next((l.strip() for l in doc.splitlines() if l.strip()), "")
        desc = textwrap.shorten(first_line, 90) if first_line else ""

        tools = []
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
                    tools.append(snake)

        return tools, desc
    except Exception:
        return [], ""


def _scan_tools() -> list:
    """
    Scan user plugin tool files.
    Returns [(stem, [tool_names], description), ...]
    """
    results = []
    try:
        for path in sorted(glob.glob(TOOLS_GLOB)):
            fname = os.path.basename(path)
            if fname in SKIP_FILES:
                continue
            tools, desc = _extract_tool_info(path)
            if tools:
                stem = os.path.splitext(fname)[0]
                results.append((stem, tools, desc))
    except Exception:
        pass
    return results


def _read_manifest() -> dict:
    """Read tool_manifest.json. Creates an empty one on first call."""
    try:
        if not os.path.exists(MANIFEST_PATH):
            os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
            with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
                json.dump(
                    {"programs": {},
                     "notes": "Add programs/capabilities here when the agent installs them."},
                    f, indent=2,
                )
            return {}
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _build_block(tool_files: list, programs: dict) -> str:
    """Build the [CUSTOM TOOLS] injection block."""
    if not tool_files and not programs:
        return ""

    lines = ["[CUSTOM TOOLS -- call by tool_name]"]

    for _stem, names, desc in tool_files:
        name_str = ", ".join(names)
        if desc:
            lines.append(f"{name_str} -- {desc}")
        else:
            lines.append(name_str)

    if programs:
        lines.append("")
        lines.append("[INSTALLED PROGRAMS]")
        for prog, pdesc in programs.items():
            lines.append(f"  {prog} -- {pdesc}")

    lines.append("[/CUSTOM TOOLS]")
    return "\n".join(lines)


def _get_last_user_message(history_output: list) -> Optional[dict]:
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


class ToolRegistry(Extension):
    """Inject custom tool registry block every LLM turn."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            user_msg = _get_last_user_message(loop_data.history_output)
            if not user_msg:
                return

            tool_files = _scan_tools()
            programs   = _read_manifest().get("programs", {})

            if not tool_files and not programs:
                return

            block = _build_block(tool_files, programs)
            if not block:
                return

            existing = user_msg.get("content", "")
            user_msg["content"] = block + "\n\n" + str(existing)

            stems     = [s for s, _, _ in tool_files]
            all_names = [n for _, names, _ in tool_files for n in names]
            print(
                f"[TOOL-REG] Injected {len(stems)} tool files "
                f"({', '.join(stems)}), "
                f"{len(all_names)} tools, "
                f"{len(programs)} programs",
                flush=True,
            )

        except Exception:
            pass
