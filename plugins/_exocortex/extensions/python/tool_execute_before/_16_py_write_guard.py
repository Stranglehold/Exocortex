"""
PyWrite Guard — Mechanical Block on .py File Writes
====================================================
Hook: tool_execute_before (_16_)

Intercepts code_execution_tool and text_editor calls that attempt to write
.py files. Blocks by replacing the command with echo refusal (code_execution_tool)
or injecting hist_add_warning (text_editor). Fails open on any guard error.

This is Layer 2 of the self-improvement guardrail stack:
  Layer 1 (behavioral): _21_constraint_heartbeat — re-injects rules every N turns
  Layer 2 (mechanical): this extension — blocks .py writes regardless of intent

Runs after action boundary (_15_) which handles broad authorization.
This guard handles the specific .py modification failure mode observed in
two consecutive self-improvement cycles (2026-04-27, 2026-04-28).

Spec: specs/PYWRITE_GUARD_SPEC_L3.md
No LLM calls. Pure regex pattern matching.
"""

import json
import os
import re
from typing import Any, Dict, List

from helpers.extension import Extension

_SHELL_TOOLS = {"code_execution_tool"}

_PY_WRITE_PATTERNS: List[re.Pattern] = [
    re.compile(r'open\s*\([^)]*\.py[^)]*["\']w["\']'),        # open("f.py", "w")
    re.compile(r'open\s*\([^)]*\.py[^)]*["\']a["\']'),        # open("f.py", "a")
    re.compile(r'open\s*\([^)]*\.py[^)]*["\']x["\']'),        # open("f.py", "x")
    re.compile(r'(?<![>])\s*>\s*\S+\.py\b'),                   # shell redirect
    re.compile(r'\btee\s+\S+\.py\b'),                          # tee file.py
    re.compile(r'\bcp\s+\S+\s+\S+\.py\b'),                    # cp src dest.py
    re.compile(r'\bmv\s+\S+\s+\S+\.py\b'),                    # mv src dest.py
    re.compile(r'shutil\.copy[^(]*\([^)]*\.py'),               # shutil.copy
    re.compile(r'shutil\.move[^(]*\([^)]*\.py'),               # shutil.move
    re.compile(r'Path\([^)]*\.py[^)]*\)\.write'),              # Path().write_text()
    re.compile(r'cat\s+>+\s+\S+\.py\b'),                      # cat > file.py
]

_TEXT_EDITOR_WRITE_COMMANDS = {"write", "create", "insert", "replace", "str_replace"}

_REFUSAL = """[PYWRITE-GUARD] BLOCKED: attempted write to a .py file.

Rule 5 prohibits modifying Python source files. This applies to all .py files
regardless of directory — extensions, tools, helpers, patches.

Permitted alternatives:
  Config JSON : /a0/usr/plugins/_exocortex/config/config.json
  Skill files : /a0/usr/skills/auto-generated/*.md (SKILL.md format)
  Wiki pages  : /a0/usr/Exocortex/wiki/**/*.md
  Memory saves: memory_save tool

If this action is genuinely necessary, stop and report to the operator.
The operator will review and make the change directly."""


def _load_config(agent) -> dict:
    try:
        cfg_path = "/a0/usr/plugins/_exocortex/config/config.json"
        if os.path.exists(cfg_path):
            with open(cfg_path) as fh:
                return json.load(fh).get("pywrite_guard", {})
    except Exception:
        pass
    return {}


def _is_whitelisted(path: str, allowed: list) -> bool:
    return any(path.startswith(a) for a in allowed if a)


def _detected_in_code(code: str) -> str | None:
    """Return the matched fragment if a .py write pattern is found, else None."""
    if ".py" not in code:
        return None
    for pattern in _PY_WRITE_PATTERNS:
        m = pattern.search(code)
        if m:
            return m.group(0)[:80]
    return None


class PyWriteGuard(Extension):
    """Mechanically blocks .py file write attempts before tool execution."""

    async def execute(
        self,
        tool_args: Dict[str, Any] | None = None,
        tool_name: str = "",
        **kwargs,
    ) -> None:
        try:
            if tool_name not in _SHELL_TOOLS and tool_name != "text_editor":
                return

            cfg = _load_config(self.agent)
            if not cfg.get("enabled", True):
                return

            allowed = cfg.get("allowed_paths", [])
            block_fragment: str | None = None
            target_path: str | None = None

            if tool_name in _SHELL_TOOLS and tool_args is not None:
                code = tool_args.get("code", "")
                block_fragment = _detected_in_code(code)
                if block_fragment and _is_whitelisted(block_fragment, allowed):
                    block_fragment = None

            elif tool_name == "text_editor" and tool_args is not None:
                target_path = tool_args.get("path", "").strip()
                command = tool_args.get("command", "").lower()
                if (
                    target_path.endswith(".py")
                    and command in _TEXT_EDITOR_WRITE_COMMANDS
                    and not _is_whitelisted(target_path, allowed)
                ):
                    block_fragment = f"{command} {target_path}"

            if block_fragment is None:
                return

            # Block: for shell tools replace code with echo; for others inject warning
            log_line = f"[PYWRITE-GUARD] Blocked {tool_name}: {block_fragment}"
            print(log_line, flush=True)

            if tool_name in _SHELL_TOOLS and tool_args is not None:
                lines = _REFUSAL.strip().split("\n")
                tool_args["code"] = "\n".join(
                    f"echo {json.dumps(line)}" for line in lines
                )
                tool_args["runtime"] = "terminal"

            try:
                self.agent.hist_add_warning(_REFUSAL)
            except Exception:
                pass

        except Exception as e:
            print(f"[PYWRITE-GUARD] Error (passthrough): {e}", flush=True)
