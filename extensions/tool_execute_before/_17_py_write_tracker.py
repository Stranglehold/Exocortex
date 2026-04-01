"""
Python Write Tracker — Code Quality Pre-check
=============================================
Hook: tool_execute_before (_17_)

When code_execution_tool writes a .py file via terminal, records the target path
in agent data for the code quality gate (_27_) to run py_compile after execution.

No blocking. No LLM calls. Pure path detection.
Runs after action boundary (_15_) and before meta-reasoning gate (_20_).
"""

import re
from typing import Any, Dict

from helpers.extension import Extension

# Patterns that write a .py file via shell — group 1 captures the file path
_PY_WRITE_PATTERNS = [
    # cat > /path/to/file.py << 'EOF'  or  cat >> file.py << EOF
    re.compile(r"cat\s+>+\s+([^\s<]+\.py)\s*<<"),
    # tee /path/to/file.py
    re.compile(r"\btee\s+([^\s|&;]+\.py)\b"),
    # bare redirect: > /path/to/file.py  (not preceded by another >)
    re.compile(r"(?<![>])\s>\s*([^\s<>&|;]+\.py)\b"),
]

PENDING_KEY = "_pending_py_check"


class PyWriteTracker(Extension):
    """Detects .py file writes and stores paths for post-execution compile check."""

    async def execute(
        self,
        tool_args: Dict[str, Any] | None = None,
        tool_name: str = "",
        **kwargs,
    ) -> None:
        try:
            if tool_name != "code_execution_tool":
                return
            if not tool_args:
                return
            if tool_args.get("runtime", "terminal") != "terminal":
                return

            code = tool_args.get("code", "")
            if not code or ".py" not in code:
                return

            paths = []
            for pattern in _PY_WRITE_PATTERNS:
                for m in pattern.finditer(code):
                    path = m.group(1).strip().strip("'\"")
                    if path.endswith(".py") and path not in paths:
                        paths.append(path)

            if paths:
                self.agent.set_data(PENDING_KEY, paths)
                print(f"[PY-TRACK] Queued py_compile for: {paths}", flush=True)

        except Exception as e:
            print(f"[PY-TRACK] Error: {e}", flush=True)
