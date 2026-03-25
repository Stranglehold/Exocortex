"""
Code Quality Gate — Post-Execution Checks
==========================================
Hook: tool_execute_after (_27_)

Two checks on code_execution_tool results:

1. py_compile check
   Reads paths stored by _17_py_write_tracker. Runs python3 -m py_compile on each.
   Appends [CODE QUALITY] warning to response if syntax errors are found.
   Clears the pending list whether or not errors are found.

2. Test import gate
   When pytest/unittest output is detected in the response, extracts test file paths
   from the output. Checks each test file for imports from non-stdlib/non-conftest
   modules. If all imports are stdlib/conftest only, appends a warning that tests
   may be validating inline stubs rather than real deliverable code.

No LLM calls. Runs after evidence ledger (_25_), before fallback logger (_30_).
"""

import ast
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from python.helpers.extension import Extension
from python.helpers.tool import Response

PENDING_KEY = "_pending_py_check"

# Patterns that indicate a test run result in the response output
_TEST_RUN_PATTERNS = [
    re.compile(r"\d+\s+(?:passed|failed|error)", re.IGNORECASE),
    re.compile(r"Ran \d+ test", re.IGNORECASE),
    re.compile(r"OK\s*\(tests=\d+\)", re.IGNORECASE),
]

# Pytest output often contains file paths like: test_foo.py, path/to/test_bar.py
_TEST_FILE_PATTERN = re.compile(r"([\w./\\-]+test[\w./\\-]*\.py)", re.IGNORECASE)

# Stdlib and test-infrastructure module roots — not considered deliverable imports
_INFRA_ROOTS = {
    "unittest", "pytest", "conftest", "sys", "os", "re", "json",
    "pathlib", "typing", "dataclasses", "datetime", "collections",
    "itertools", "functools", "math", "random", "time", "tempfile",
    "shutil", "hashlib", "io", "abc", "copy", "enum", "logging",
    "warnings", "contextlib", "threading", "asyncio", "textwrap",
    "string", "struct", "base64", "uuid", "platform", "subprocess",
    "inspect", "traceback", "types", "weakref", "gc", "pprint",
}

# Common test workdir locations to search when resolving relative test paths
_SEARCH_DIRS = [
    Path("/a0/usr/workdir"),
    Path("/a0/usr/workdir/framework_tests"),
    Path("/a0/usr/workdir/phase4"),
    Path("/a0/usr/workdir/phase5"),
]


def _run_py_compile(path: str) -> Optional[str]:
    """Run py_compile on path. Returns error string or None on success."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return (result.stderr or result.stdout or "unknown error").strip()
        return None
    except Exception as e:
        return str(e)


def _check_test_imports(test_path: str) -> List[str]:
    """
    Parse test file AST for import statements.
    Returns list of non-infra module root names found.
    Empty list means all imports are stdlib/confra — potential stub test.
    """
    try:
        with open(test_path, encoding="utf-8") as f:
            src = f.read()
        tree = ast.parse(src)
        external = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root not in _INFRA_ROOTS:
                        external.add(root)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split(".")[0]
                    if root not in _INFRA_ROOTS:
                        external.add(root)
        return list(external)
    except Exception:
        return []


def _resolve_test_path(raw: str) -> Optional[Path]:
    """Try to find the actual file for a test path string from pytest output."""
    p = Path(raw)
    if p.exists():
        return p
    # Try by filename in known workdir locations
    for base in _SEARCH_DIRS:
        candidate = base / p.name
        if candidate.exists():
            return candidate
    return None


class CodeQualityGate(Extension):
    """Post-execution checks: py_compile and test import validation."""

    async def execute(self, response: Response | None = None, **kwargs) -> None:
        try:
            if not response:
                return
            if kwargs.get("tool_name", "") != "code_execution_tool":
                return

            warnings = []

            # ── Check 1: py_compile ───────────────────────────────────────────
            pending = self.agent.get_data(PENDING_KEY) or []
            if pending:
                self.agent.set_data(PENDING_KEY, [])  # clear before check
                for path in pending:
                    err = _run_py_compile(path)
                    if err:
                        warnings.append(
                            f"[CODE QUALITY] \u2717 Syntax error in {path}:\n{err}\n"
                            f"Fix this file before proceeding."
                        )
                        print(f"[CODE-GATE] py_compile FAILED: {path}", flush=True)
                    else:
                        print(f"[CODE-GATE] py_compile OK: {path}", flush=True)

            # ── Check 2: test import gate ─────────────────────────────────────
            output = response.message or ""
            if any(p.search(output) for p in _TEST_RUN_PATTERNS):
                raw_paths = list(set(_TEST_FILE_PATTERN.findall(output)))
                for raw in raw_paths:
                    resolved = _resolve_test_path(raw)
                    if not resolved:
                        continue
                    external = _check_test_imports(str(resolved))
                    if not external:
                        warnings.append(
                            f"[CODE QUALITY] \u26a0 {resolved.name}: no deliverable imports found.\n"
                            f"All imports are stdlib/unittest/conftest — these tests may be "
                            f"validating inline stubs rather than real module code.\n"
                            f"Ensure the test file imports from the actual deliverable module."
                        )
                        print(f"[CODE-GATE] Stub-only test: {resolved.name}", flush=True)
                    else:
                        print(
                            f"[CODE-GATE] Test imports OK ({resolved.name}): {external}",
                            flush=True,
                        )

            if warnings:
                response.message = response.message + "\n\n" + "\n".join(warnings)

        except Exception as e:
            print(f"[CODE-GATE] Error: {e}", flush=True)
