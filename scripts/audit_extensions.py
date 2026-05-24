#!/usr/bin/env python3
"""
audit_extensions.py — DEC-026 verification gate as a tool.

Surveys all extension paths on a running A0 container, identifies which copies
A0 actually loads, and flags duplicates, mis-deploys, and dead extensions.

Background:
  A0's extension loader (helpers/extension._get_extension_classes) calls
  helpers/subagents.get_paths(agent, "extensions/python", <hook>). The path
  MUST include the "python" segment. The natural-feeling path that omits it
  (extensions/<hook>/ instead of extensions/python/<hook>/) is invisible to
  the loader. See wiring doc §02 and §13 seam #8.

  Three extension-host paths exist in the container at this time, only two
  of which the loader actually checks:

    1. /a0/usr/agents/agent0/extensions/python/<hook>/   ← profile (canonical)
    2. /a0/usr/plugins/exocortex/extensions/python/<hook>/   ← plugin (canonical)
    3. /a0/usr/agents/agent0/extensions/<hook>/  ← WRONG (missing python/)
    4. /a0/python/extensions/<hook>/  ← A0 core; loaded via default_root

Usage:
  python3 scripts/audit_extensions.py <container_name>
  python3 scripts/audit_extensions.py exocortex_v16
  python3 scripts/audit_extensions.py exocortex_v17 --json
  python3 scripts/audit_extensions.py exocortex_v16 --hook before_main_llm_call

Output: human-readable report by default; --json emits structured findings.

Exit codes:
  0 — no problems found
  1 — divergent duplicates or wrong-path-only extensions found
  2 — container unreachable or audit failed
"""

import argparse
import json
import subprocess
import sys
from collections import defaultdict

HOOKS = [
    "before_main_llm_call",
    "message_loop_prompts_after",
    "message_loop_end",
    "monologue_end",
    "tool_execute_before",
    "tool_execute_after",
    "hist_add_before",
    "error_format",
    "response_stream_chunk",
    "reasoning_stream_chunk",
    "system_prompt",
    "agent_init",
    "message_loop_start",
]

CANONICAL_PREFIXES = [
    "/a0/usr/agents/agent0/extensions/python",
    "/a0/usr/plugins/exocortex/extensions/python",
    "/a0/python/extensions",
]

WRONG_PREFIXES = [
    "/a0/usr/agents/agent0/extensions",
    "/a0/usr/extensions/python",
]


def _exec(container: str, command: str) -> str:
    """Run a shell command in the container, return stdout, "" on failure."""
    try:
        result = subprocess.run(
            ["docker", "exec", container, "sh", "-c", command],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return ""
        return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def _list_py_files(container: str, path: str) -> list[str]:
    out = _exec(
        container,
        f"ls {path} 2>/dev/null | grep -E '^_[0-9].*\\.py$' | grep -v '__pycache__'",
    )
    return [line.strip() for line in out.splitlines() if line.strip()]


def _md5(container: str, filepath: str) -> str:
    out = _exec(container, f"md5sum {filepath} 2>/dev/null")
    if not out:
        return ""
    return out.split()[0] if out.split() else ""


def _check_container(container: str) -> bool:
    out = _exec(container, "echo ok")
    return out.strip() == "ok"


def audit_hook(container: str, hook: str) -> dict:
    """Return a per-hook map: filename -> [(path, md5), ...]."""
    by_file: dict[str, list[tuple[str, str, bool]]] = defaultdict(list)
    for prefix in CANONICAL_PREFIXES + WRONG_PREFIXES:
        path = f"{prefix}/{hook}"
        is_wrong = prefix in WRONG_PREFIXES
        files = _list_py_files(container, path)
        for filename in files:
            full = f"{path}/{filename}"
            md5 = _md5(container, full) or "?"
            by_file[filename].append((full, md5, is_wrong))
    return dict(by_file)


def classify(filename: str, entries: list[tuple[str, str, bool]]) -> tuple[str, str]:
    """Return (category, summary) for a file's deployment pattern."""
    if not entries:
        return ("none", "no copies found")

    canonical = [(p, m) for p, m, w in entries if not w]
    wrong = [(p, m) for p, m, w in entries if w]
    all_md5s = {m for _, m, _ in entries}

    if not canonical and wrong:
        return ("wrong_only", f"only at wrong path: {wrong[0][0]} (md5 {wrong[0][1][:8]})")

    if canonical and wrong:
        if len(all_md5s) == 1:
            return ("dup_same", f"{len(canonical)} canonical + {len(wrong)} wrong, same md5 {entries[0][1][:8]}")
        return ("dup_divergent", f"{len(canonical)} canonical + {len(wrong)} wrong with DIFFERENT md5s — silent stale copy risk")

    # only canonical
    if len(canonical) == 1:
        return ("ok", f"loaded from {canonical[0][0]}")
    if len(all_md5s) == 1:
        return ("dup_same_canonical", f"{len(canonical)} canonical copies, same md5 {entries[0][1][:8]}")
    return ("dup_canonical_divergent", f"{len(canonical)} canonical copies with DIFFERENT md5s — loader picks first by sort order")


def main():
    parser = argparse.ArgumentParser(description="Audit A0 extension deploy state.")
    parser.add_argument("container", help="Container name (e.g., exocortex_v16)")
    parser.add_argument("--hook", help="Audit one hook only", default=None)
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--quiet", action="store_true", help="Suppress OK rows")
    args = parser.parse_args()

    if not _check_container(args.container):
        print(f"ERROR: container {args.container} unreachable", file=sys.stderr)
        sys.exit(2)

    hooks_to_audit = [args.hook] if args.hook else HOOKS

    findings = {}
    issues = 0
    for hook in hooks_to_audit:
        by_file = audit_hook(args.container, hook)
        hook_results = {}
        for filename in sorted(by_file.keys()):
            category, summary = classify(filename, by_file[filename])
            hook_results[filename] = {
                "category": category,
                "summary": summary,
                "entries": [
                    {"path": p, "md5": m, "wrong_path": w}
                    for p, m, w in by_file[filename]
                ],
            }
            if category in ("wrong_only", "dup_divergent", "dup_canonical_divergent"):
                issues += 1
        findings[hook] = hook_results

    if args.json:
        print(json.dumps({"container": args.container, "findings": findings, "issue_count": issues}, indent=2))
        sys.exit(1 if issues else 0)

    # Human-readable report
    print(f"\n=== Extension Audit — {args.container} ===\n")
    severity_label = {
        "ok": "OK",
        "wrong_only": "WRONG-PATH (DEAD)",
        "dup_same": "DUP (same md5)",
        "dup_divergent": "DUP DIVERGENT",
        "dup_same_canonical": "DUP CANONICAL (same)",
        "dup_canonical_divergent": "DUP CANONICAL DIVERGENT",
        "none": "NONE",
    }
    severity_order = {"wrong_only": 0, "dup_divergent": 1, "dup_canonical_divergent": 2, "dup_same": 3, "dup_same_canonical": 4, "ok": 5}

    for hook in hooks_to_audit:
        hook_results = findings.get(hook, {})
        if not hook_results:
            if not args.quiet:
                print(f"  [empty] {hook}/")
            continue

        sorted_files = sorted(
            hook_results.items(),
            key=lambda kv: (severity_order.get(kv[1]["category"], 99), kv[0]),
        )

        # Skip OK hooks entirely in quiet mode
        if args.quiet and all(v["category"] == "ok" for v in hook_results.values()):
            continue

        print(f"\n--- {hook} ---")
        for filename, info in sorted_files:
            cat = info["category"]
            if args.quiet and cat == "ok":
                continue
            label = severity_label[cat]
            marker = "  " if cat == "ok" else "! "
            print(f"  {marker}[{label}] {filename}")
            print(f"      {info['summary']}")
            if cat in ("wrong_only", "dup_divergent", "dup_canonical_divergent"):
                for entry in info["entries"]:
                    flag = " (WRONG)" if entry["wrong_path"] else ""
                    print(f"        {entry['md5'][:12]}  {entry['path']}{flag}")

    print(f"\n=== Summary ===")
    print(f"  Hooks audited : {len(hooks_to_audit)}")
    print(f"  Issues found  : {issues}")
    if issues:
        print("\n  Action items:")
        print("    - WRONG-PATH (DEAD): file exists but isn't loaded; either deploy to canonical path or delete.")
        print("    - DUP DIVERGENT: same filename at canonical + wrong path with different md5s; loader uses canonical, wrong-path copy is stale.")
        print("    - DUP CANONICAL DIVERGENT: same filename at multiple canonical paths with different md5s; loader picks first by sort order — fragile.")

    sys.exit(1 if issues else 0)


if __name__ == "__main__":
    main()
