#!/usr/bin/env python3
"""
LOOP_ALTERNATIVES Regression Test — GAP-10 (Audit Session 002)
================================================================
Verifies that every tool name in LOOP_ALTERNATIVES resolves to a known
valid tool. The Session 050 fix replaced stale names (computer,
code_execution, knowledge_tool) with real ones (code_execution_tool,
search_engine). This test ensures a future edit doesn't re-introduce
a stale or invented tool name.

Usage:
    C:/Users/Jake/miniconda3/python.exe eval/test_loop_alternatives.py
    python3 /a0/usr/Exocortex/eval/test_loop_alternatives.py

Exit codes:
    0 — All tool names valid
    1 — Stale/invalid tool name found
    2 — Could not load supervisor file
"""

import re
import sys
from pathlib import Path

# ── File paths ────────────────────────────────────────────────────────────────

SCRIPT_DIR  = Path(__file__).parent
REPO_ROOT   = SCRIPT_DIR.parent

SUPERVISOR_PATH = REPO_ROOT / "extensions" / "message_loop_end" / "_50_supervisor_loop.py"
SUPERVISOR_CONTAINER = Path("/a0/usr/agents/agent0/extensions/python/message_loop_end/_50_supervisor_loop.py")

# ── Valid tool names (current A0 + Exocortex custom tools) ────────────────────
#
# Add new tools here when they're deployed. Removing a tool from this list
# will cause the test to flag it — do both together.

VALID_TOOL_NAMES = {
    # Agent Zero native tools
    "response",
    "code_execution_tool",
    "call_subordinate",
    "document_query",
    "search_engine",
    "memory_load",
    "memory_save",
    "memory_delete",
    "memory_forget",
    "browser_agent",
    "input",
    "notify_user",
    "skills_tool",
    "text_editor",
    # Exocortex custom tools
    "stack_status",
    "staging_note",
    "library_add",
    "library_list",
    "library_search",
    "library_remove",
    "library_collections",
    "oss_health",
    "oss_topic",
    "oss_drift",
    "oss_dynamics",
    "oss_hypotheses",
    "oss_submit",
    "oss_ingest_pause",
    "oss_ingest_resume",
    "oss_list_topics",
    "oss_add_topic",
    "oss_x_search",
    "swarmfish_predict",
    "swarmfish_session",
    "swarmfish_sessions",
    "swarmfish_calibration",
    "swarmfish_outcome",
    "ontology_search",
    "source_ingest",
    "entity_resolve",
    "relationship_query",
    "investigation_report",
    "tla_check",
}

# Special keys that are not tool names (documented exceptions)
NON_TOOL_KEYS = {
    "response_format",  # Special key for format failures — not a tool name
}

# ── Extraction ────────────────────────────────────────────────────────────────

def extract_loop_alternatives_keys(supervisor_path: Path) -> list[str]:
    """Extract top-level keys from LOOP_ALTERNATIVES in the supervisor file."""
    src = supervisor_path.read_text(encoding="utf-8", errors="replace")

    # Find LOOP_ALTERNATIVES = { ... }
    m = re.search(r"LOOP_ALTERNATIVES\s*=\s*\{", src)
    if not m:
        raise ValueError("LOOP_ALTERNATIVES not found in supervisor file")

    start = m.end()
    depth = 1
    i = start
    while i < len(src) and depth > 0:
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
        i += 1
    block = src[start : i - 1]

    # Extract top-level string keys
    keys = re.findall(r"""^    ["']([\w_]+)["']\s*:""", block, re.MULTILINE)
    initial_keys = set(keys)

    # Also find any LOOP_ALTERNATIVES["key"] = [...] assignments after the initial dict
    remainder = src[i:]
    assigned = re.findall(r"""LOOP_ALTERNATIVES\s*\[["']([\w_]+)["']\]""", remainder)

    return sorted(initial_keys | set(assigned))


# ── Test logic ────────────────────────────────────────────────────────────────

def run_test(supervisor_path: Path) -> int:
    """
    Verify all LOOP_ALTERNATIVES keys are known valid tools.
    Returns 0 on pass, 1 on failure, 2 on error.
    """
    print("=== LOOP_ALTERNATIVES Regression Test (GAP-10) ===")
    print()

    # Resolve container path if needed
    if not supervisor_path.exists() and SUPERVISOR_CONTAINER.exists():
        supervisor_path = SUPERVISOR_CONTAINER
        print(f"[INFO] Running from container")

    if not supervisor_path.exists():
        print(f"[ERROR] Supervisor file not found: {supervisor_path}", file=sys.stderr)
        return 2

    print(f"Supervisor: {supervisor_path}")
    print()

    try:
        keys = extract_loop_alternatives_keys(supervisor_path)
    except Exception as e:
        print(f"[ERROR] Could not parse LOOP_ALTERNATIVES: {e}", file=sys.stderr)
        return 2

    print(f"Keys found in LOOP_ALTERNATIVES: {len(keys)}")
    print()

    invalid = []
    non_tool = []
    valid = []

    for key in keys:
        if key in NON_TOOL_KEYS:
            non_tool.append(key)
        elif key in VALID_TOOL_NAMES:
            valid.append(key)
        else:
            invalid.append(key)

    print("=== VALID TOOL KEYS ===")
    for k in valid:
        print(f"  OK  {k}")
    print()

    if non_tool:
        print("=== NON-TOOL KEYS (documented exceptions) ===")
        for k in non_tool:
            print(f"  OK  {k}  [non-tool, documented]")
        print()

    if invalid:
        print("=== INVALID/UNKNOWN KEYS ===")
        for k in invalid:
            print(f"  FAIL  {k}  <-- not in VALID_TOOL_NAMES")
        print()
        print("ACTION: Either add to VALID_TOOL_NAMES if this is a real tool,")
        print("        or fix the key in LOOP_ALTERNATIVES to use the correct name.")
        print()

    print("=== SUMMARY ===")
    if invalid:
        print(f"  FAIL - {len(invalid)} invalid key(s): {invalid}")
        print()
        print("  HISTORY: Session 050 replaced stale names (computer, code_execution,")
        print("  knowledge_tool) with real names. This test ensures they don't come back.")
    else:
        print(f"  PASS - {len(valid)} valid tool keys, {len(non_tool)} documented non-tool keys")
    print()

    return 1 if invalid else 0


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="LOOP_ALTERNATIVES tool-name regression test (GAP-10)"
    )
    parser.add_argument(
        "--supervisor-path",
        type=Path,
        default=SUPERVISOR_PATH,
        help=f"Path to supervisor file (default: {SUPERVISOR_PATH})",
    )
    args = parser.parse_args()
    sys.exit(run_test(args.supervisor_path))


if __name__ == "__main__":
    main()
