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

v3.2: Added domain->skill surfacing. Reads BST domain from
extras_persistent (_bst_domain) and appends a [SUGGESTED SKILLS]
block when relevant skills exist for the current task domain.
Skill directories are verified on-disk before injection.

No LLM calls. Reads only.
"""

import ast
import glob
import json
import os
import re
import textwrap
from typing import Optional

from agent import Agent, LoopData
from helpers.extension import Extension

# mtime cache — skip tool rescan when plugin dirs unchanged
try:
    import sys as _sys
    _pm = "/a0/usr/Exocortex/extensions/before_main_llm_call"
    if _pm not in _sys.path:
        _sys.path.insert(0, _pm)
    from mtime_cache import cached as _mtime_cached
    _mtime_cache = True
except Exception:
    _mtime_cache = None


def _log_injection_tokens(agent, ext_name: str, text: str) -> None:
    tok = len(text) // 4
    counts = getattr(agent, "_injection_token_counts", {})
    counts[ext_name] = counts.get(ext_name, 0) + tok
    agent._injection_token_counts = counts
    print(f"[TOKEN-COUNT] {ext_name}: ~{tok} tokens injected", flush=True)

TOOLS_GLOB    = "/a0/usr/plugins/*/tools/*.py"
MANIFEST_PATH = "/a0/usr/Exocortex/tool_manifest.json"
SKILLS_BASE   = "/a0/usr/skills"

# Files to skip even if they match the glob
SKIP_FILES = {"__init__.py"}

# Known native tool names -- skip if accidentally scanned
NATIVE_TOOLS = {
    "response", "a2a_chat", "behaviour_adjustment", "browser_agent",
    "call_subordinate", "code_execution_tool", "document_query", "input",
    "memory_load", "memory_save", "memory_delete", "memory_forget",
    "notify_user", "search_engine", "skills_tool", "text_editor",
}

# Domain -> [(skill_name, one-line reason)] mapping.
# Surfaced when BST classifies the matching domain.
# Only skills whose directories actually exist on disk are shown.
DOMAIN_SKILL_MAP = {
    "coding": [
        ("design-buildplan",  "Use before writing multi-file or multi-phase code projects"),
        ("execute-buildplan", "Use to follow a plan produced by design-buildplan"),
    ],
    "planning": [
        ("design-buildplan",  "Separates planning from execution for complex builds"),
        ("execute-buildplan", "Executes a build plan step-by-step with verification"),
        ("extract-and-adapt", "Build Exocortex-native artifacts from external references (repos, papers, APIs)"),
    ],
    "investigation": [
        ("intelligence-briefing",     "Parallel research synthesis with sourced, structured output"),
        ("architecture-investigation","Systematic framework analysis and capability mapping"),
        ("web-research-macro",        "Clean text extraction from websites via browser + sanitizer"),
        ("academic-research",         "Structured literature search via Semantic Scholar API"),
        ("extract-and-adapt",         "Adapt external patterns into native Exocortex skills/tools/specs"),
    ],
    "analysis": [
        ("context-schema-comparison", "Compare context management approaches across agent systems"),
    ],
    "financial": [
        ("financial-research", "Fundamentals, income statements, balance sheets via yfinance"),
        ("real-time-data",     "Live stock, ETF, and crypto prices"),
    ],
    "prompt_engineering": [
        ("system-prompt-engineering", "Framework for constructing effective system prompts"),
    ],
    "config_edit": [
        ("config-edit", "Safe YAML/JSON/TOML config editing with validation and backup"),
    ],
    "philosophical": [
        ("autonomous-exploration", "Background intellectual exploration with genuine curiosity"),
    ],
    "meta_cognitive": [
        ("self-optimizing-skill", "Self-monitoring and RL-inspired execution optimization"),
    ],
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


def _skill_exists(skill_name: str) -> bool:
    """Check if a skill directory exists on disk."""
    return os.path.isdir(os.path.join(SKILLS_BASE, skill_name))


def _build_skill_block(domain: str, secondary_domain: Optional[str] = None) -> str:
    """Build [SUGGESTED SKILLS] block for the given BST domain(s).

    Only includes skills whose directories actually exist on disk.
    Returns empty string if no skills apply or none exist.
    """
    entries = []
    seen: set = set()

    for d in filter(None, [domain, secondary_domain]):
        for skill_name, reason in DOMAIN_SKILL_MAP.get(d, []):
            if skill_name not in seen and _skill_exists(skill_name):
                entries.append(f"  {skill_name} -- {reason}")
                seen.add(skill_name)

    if not entries:
        return ""

    lines = ["[SUGGESTED SKILLS for this task]"]
    lines.extend(entries)
    lines.append("(Load with: skills_tool:load <skill-name>)")
    lines.append("[/SUGGESTED SKILLS]")
    return "\n".join(lines)


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
    """Inject custom tool registry + domain-appropriate skill suggestions every LLM turn."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            if self.agent.get_data(Agent.DATA_NAME_SUPERIOR) is not None:
                return  # subordinate context — skip full tool registry injection (DEC-028)
            user_msg = _get_last_user_message(loop_data.history_output)
            if not user_msg:
                return

            if _mtime_cache:
                scan_paths = glob.glob(TOOLS_GLOB) + [MANIFEST_PATH]
                tool_files, _ = _mtime_cached("tool_reg_scan", scan_paths, _scan_tools)
                manifest_raw, _ = _mtime_cached("tool_reg_manifest", [MANIFEST_PATH], _read_manifest)
                programs = manifest_raw.get("programs", {}) if isinstance(manifest_raw, dict) else {}
            else:
                tool_files = _scan_tools()
                programs   = _read_manifest().get("programs", {})

            if not tool_files and not programs:
                return

            tools_block = _build_block(tool_files, programs)
            if not tools_block:
                return

            # Read BST domain from extras_persistent (written by _11_belief_state_tracker)
            ep = getattr(loop_data, "extras_persistent", None) or {}
            primary_domain   = ep.get("_bst_domain", "")
            compound_data    = ep.get("_bst_compound", {}) or {}
            secondary_info   = compound_data.get("secondary") or {}
            secondary_domain = secondary_info.get("domain", "") if secondary_info else ""

            skill_block = _build_skill_block(primary_domain, secondary_domain or None)

            # Gate check: tools_block is cached separately from skill_block.
            # Skill suggestions change with BST domain, so they always inject.
            # Tool list only changes when plugins are installed/removed.
            try:
                from extensions.before_main_llm_call._09_injection_gate import should_inject
                tools_action, tools_ref = should_inject(
                    self.agent, "tool_registry", tools_block
                )
            except Exception:
                tools_action, tools_ref = "full", ""

            if tools_action == "skip":
                return

            inject_tools = tools_ref if tools_action == "reference" else tools_block

            # Compose: tools (full or reference) then skill suggestions (always)
            parts = [inject_tools]
            if skill_block:
                parts.append(skill_block)

            block = "\n\n".join(parts)

            existing = user_msg.get("content", "")
            user_msg["content"] = block + "\n\n" + str(existing)
            if tools_action == "full":
                _log_injection_tokens(self.agent, "tool_registry", block)

            stems     = [s for s, _, _ in tool_files]
            all_names = [n for _, names, _ in tool_files for n in names]
            skill_count = len([l for l in skill_block.splitlines() if l.startswith("  ")]) if skill_block else 0
            print(
                f"[TOOL-REG] Injected {len(stems)} tool files "
                f"({', '.join(stems)}), "
                f"{len(all_names)} tools, "
                f"{len(programs)} programs"
                + (f", {skill_count} skill hints ({primary_domain})" if skill_count else ""),
                flush=True,
            )

        except Exception:
            pass
