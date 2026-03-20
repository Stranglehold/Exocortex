"""
Tool Registry — Dynamic Custom Tool Awareness
=============================================
Hook: before_main_llm_call (_16_)

Scans /a0/python/tools/ every turn and injects a compact [CUSTOM TOOLS] block
into the user message — so the model always knows which tool_names are callable
beyond the native Agent Zero set.

Grows with the agent automatically:
  • Any new .py file dropped into /a0/python/tools/ appears the next turn.
  • /a0/usr/Exocortex/tool_manifest.json registers installed programs and
    runtime-discovered capabilities (e.g. nmap after apt-get install).
    Created empty on first run if missing. Agent or analyst can write to it.

No imports of tool files (ast-only parsing). No LLM calls. Deterministic.
Runs after BST (_11_), profile (_13_), and metacognitive injection (_14_).
"""

import ast
import json
import os
import re
import textwrap
from typing import Optional

from agent import LoopData
from python.helpers.extension import Extension

# ── Configuration ──────────────────────────────────────────────────────────────

TOOLS_DIR     = "/a0/python/tools"
MANIFEST_PATH = "/a0/usr/Exocortex/tool_manifest.json"

# Native Agent Zero tool filenames — excluded from custom listing.
NATIVE_TOOLS = {
    "response", "a2a_chat", "behaviour_adjustment", "browser_agent",
    "call_subordinate", "code_execution_tool", "document_query", "input",
    "memory_load", "memory_save", "memory_delete", "memory_forget",
    "notify_user", "search_engine", "skills_tool",
}


# ── Extension ──────────────────────────────────────────────────────────────────

class ToolRegistry(Extension):
    """Inject custom tool registry into user message before each LLM call."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            custom_tools = _scan_custom_tools()
            programs     = _read_manifest()

            if not custom_tools and not programs:
                return

            block = _build_block(custom_tools, programs)
            if not block:
                return

            user_msg = _get_last_user_message(loop_data.history_output)
            if not user_msg:
                return

            existing = user_msg.get("content", "")
            user_msg["content"] = block + "\n\n" + str(existing)

            tool_files = [name for name, _, _ in custom_tools]
            print(
                f"[TOOL-REG] Injected {len(custom_tools)} custom tools "
                f"({', '.join(tool_files)}), {len(programs)} programs",
                flush=True,
            )

        except Exception as e:
            print(f"[TOOL-REG] error (passthrough): {e}", flush=True)


# ── Tool Scanning ───────────────────────────────────────────────────────────────

def _scan_custom_tools() -> list:
    """
    Return list of (filename_stem, [snake_case_tool_names], description) tuples
    for all non-native tool files in TOOLS_DIR.
    """
    if not os.path.isdir(TOOLS_DIR):
        return []

    results = []
    for fname in sorted(os.listdir(TOOLS_DIR)):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        stem = fname[:-3]
        if stem in NATIVE_TOOLS:
            continue

        path = os.path.join(TOOLS_DIR, fname)
        names, desc = _extract_tool_info(path)
        if names:
            results.append((stem, names, desc))

    return results


def _extract_tool_info(path: str) -> tuple:
    """
    Parse a tool file with ast (no import) and return:
      ([snake_case_tool_names], description_string)
    Tool names come from class names that subclass Tool.
    Description comes from the module docstring first line.
    Returns ([], "") on any parse error.
    """
    try:
        with open(path, encoding="utf-8") as f:
            src = f.read()

        tree = ast.parse(src)

        # Module docstring — first non-blank line
        raw_doc = ast.get_docstring(tree) or ""
        desc = next((ln.strip() for ln in raw_doc.splitlines() if ln.strip()), "")
        desc = textwrap.shorten(desc, width=90, placeholder="...")

        # Class names that directly or indirectly subclass Tool
        names = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for base in node.bases:
                is_tool = (
                    (isinstance(base, ast.Name) and base.id == "Tool") or
                    (isinstance(base, ast.Attribute) and base.attr == "Tool")
                )
                if is_tool:
                    names.append(_to_snake(node.name))
                    break

        return names, desc

    except Exception:
        return [], ""


def _to_snake(name: str) -> str:
    """CamelCase → snake_case. OssHealth → oss_health."""
    s = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name)
    return s.lower()


# ── Manifest ────────────────────────────────────────────────────────────────────

def _read_manifest() -> dict:
    """
    Read tool_manifest.json. Returns programs dict (name → description).
    Creates the file empty if missing so the agent can write to it.
    """
    if not os.path.exists(MANIFEST_PATH):
        try:
            os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
            with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "programs": {},
                        "notes": (
                            "Add installed programs or agent-discovered capabilities here. "
                            "Each key is the program name; value is a brief description. "
                            "The tool registry extension injects these into every turn."
                        ),
                    },
                    f,
                    indent=2,
                )
        except Exception:
            pass
        return {}

    try:
        with open(MANIFEST_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return {k: str(v) for k, v in data.get("programs", {}).items() if k and v}
    except Exception:
        return {}


# ── Block Construction ──────────────────────────────────────────────────────────

def _build_block(custom_tools: list, programs: dict) -> str:
    """Build the [CUSTOM TOOLS] injection block."""
    lines = ["[CUSTOM TOOLS — call by tool_name]"]

    for _stem, names, desc in custom_tools:
        name_str = " | ".join(names)
        if desc:
            lines.append(f"{name_str} — {desc}")
        else:
            lines.append(name_str)

    if programs:
        lines.append("")
        lines.append("[INSTALLED PROGRAMS — invoke via code_execution_tool]")
        for prog, pdesc in programs.items():
            lines.append(f"{prog} — {pdesc}")

    lines.append("[/CUSTOM TOOLS]")
    return "\n".join(lines)


# ── Message Helper (shared pattern with _13, _14) ──────────────────────────────

def _get_last_user_message(history_output: list) -> Optional[dict]:
    """Find the most recent operator message in loop history."""
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
