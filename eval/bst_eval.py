#!/usr/bin/env python3
"""
BST Eval Harness — Autoresearch Target
=======================================
Evaluates BST domain classification accuracy against a labeled sample set.

Implements the autoresearch pattern for BST threshold tuning:
  - One metric: accuracy (higher is better)
  - One modifiable target: BST domain configs / threshold constants
  - Fast loop: runs in ~1 second
  - Grep-able output: "accuracy: 0.XX"
  - Commit before modifying BST, reset if accuracy drops

Usage:
    # Inside container (Agent Zero runs this via code_execution_tool):
    python3 /a0/usr/Exocortex/eval/bst_eval.py

    # From Windows host (for Kestrel session testing):
    BST_PATH="D:/Vibecode/Agent-Zero/Exocortex/extensions/before_main_llm_call/_11_belief_state_tracker.py"
    C:/Users/Jake/miniconda3/python.exe eval/bst_eval.py

    # With custom threshold (fail if accuracy drops below X):
    python3 bst_eval.py --threshold 0.85

Output:
    - Domain-level breakdown (correct/total, %)
    - Compound detection accuracy
    - Overall accuracy on the last line: "accuracy: 0.XX"

Exit codes:
    0 = completed (read accuracy: line for metric)
    1 = fatal: BST module could not be loaded
"""

import sys
import os
import argparse
from unittest.mock import MagicMock
import importlib.util


# ─── BST Path Detection ───────────────────────────────────────────────────────

def _bst_path_default() -> str:
    """Auto-detect BST path: inside container or on Windows host."""
    if os.path.exists("/a0"):
        # Running inside Agent Zero container
        return "/a0/python/extensions/before_main_llm_call/_11_belief_state_tracker.py"
    else:
        # Running on Windows host — path relative to this file's parent
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(
            repo_root,
            "extensions", "before_main_llm_call", "_11_belief_state_tracker.py"
        )


# ─── BST Loading ──────────────────────────────────────────────────────────────

def _load_bst(bst_path: str):
    """Load BST module with mocked Agent Zero imports.

    The BST's core classification functions (_score_all_domains, _extract_compound,
    _apply_compound_momentum) are pure module-level functions with no Agent Zero
    dependencies. We mock the framework imports so the module loads cleanly, then
    use only those pure functions.
    """
    # Mock Agent Zero framework imports before loading the module.
    # The BST uses: from agent import LoopData
    #               from python.helpers.extension import Extension
    # Neither is needed for the pure classification functions.
    mock_agent = MagicMock()
    mock_agent.LoopData = MagicMock  # type: ignore
    sys.modules.setdefault("agent", mock_agent)
    sys.modules.setdefault("python", MagicMock())
    sys.modules.setdefault("python.helpers", MagicMock())
    sys.modules.setdefault("python.helpers.extension", MagicMock())

    if not os.path.exists(bst_path):
        print(f"[BST EVAL] ERROR: BST not found at {bst_path}", flush=True)
        return None

    spec = importlib.util.spec_from_file_location("bst_module", bst_path)
    if spec is None or spec.loader is None:
        print(f"[BST EVAL] ERROR: Could not create spec for {bst_path}", flush=True)
        return None

    bst = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(bst)
    except Exception as e:
        print(f"[BST EVAL] ERROR loading BST module: {e}", flush=True)
        return None

    return bst


# ─── Test Cases ───────────────────────────────────────────────────────────────
# Format: (input_text, expected_primary, expected_secondary, label)
# expected_secondary = None if only primary matters / no compound expected.
# For compound cases, expected_secondary is the secondary domain.
# Labels annotate what the case is testing.

TEST_CASES = [
    # ── investigation ──────────────────────────────────────────────────────────
    (
        "investigate who runs this company and what their business model is",
        "investigation", None,
        "investigation: investigat signal"
    ),
    (
        "do some osint on this entity before we proceed",
        "investigation", None,
        "investigation: osint signal"
    ),
    (
        "look into the background on this supplier",
        "investigation", None,
        "investigation: look into + background on"
    ),
    (
        "verify the source and find out if this data is accurate",
        "investigation", None,
        "investigation: verify + find out"
    ),

    # ── coding ────────────────────────────────────────────────────────────────
    (
        "write a function to parse JSON responses from the API",
        "coding", None,
        "coding: write a function"
    ),
    (
        "implement a retry class for the HTTP client",
        "coding", None,
        "coding: implement"
    ),
    (
        "scaffold a new module for the websocket handler",
        "coding", None,
        "coding: scaffold"
    ),
    (
        "write the Python code to handle authentication tokens",
        "coding", None,
        "coding: write + python compound signal"
    ),

    # ── bugfix ────────────────────────────────────────────────────────────────
    (
        "the extension crashes on startup with a traceback",
        "bugfix", None,
        "bugfix: crash + traceback"
    ),
    (
        "fix the exception in the memory classifier",
        "bugfix", None,
        "bugfix: fix + exception"
    ),
    (
        "why is this test failing, help me debug it",
        "bugfix", None,
        "bugfix: failing + debug"
    ),
    (
        "this feature is broken and not working correctly",
        "bugfix", None,
        "bugfix: broken + not work"
    ),

    # ── analysis ──────────────────────────────────────────────────────────────
    (
        "analyze the BST classification metrics over the last 100 turns",
        "analysis", None,
        "analysis: analyz + metric"
    ),
    (
        "compare these two implementations and evaluate the performance tradeoffs",
        "analysis", None,
        "analysis: compar + evaluat + performance"
    ),
    (
        "review the statistics from the stress test results",
        "analysis", None,
        "analysis: review + statistic"
    ),
    (
        "benchmark the two sorting implementations",
        "analysis", None,
        "analysis: benchmark"
    ),

    # ── system_admin ──────────────────────────────────────────────────────────
    (
        "install the service and configure the firewall rules",
        "system_admin", None,
        "system_admin: install + service + firewall"
    ),
    (
        "check the permissions on the mount point and fix with chmod",
        "system_admin", None,
        "system_admin: permission + mount + chmod"
    ),
    (
        "the daemon won't start, check systemctl status",
        "system_admin", None,
        "system_admin: daemon + systemctl"
    ),

    # ── planning ──────────────────────────────────────────────────────────────
    (
        "design the roadmap for the next three sprints",
        "planning", None,
        "planning: design + roadmap + sprint"
    ),
    (
        "what is the best approach for implementing this feature",
        "planning", None,
        "planning: best approach"
    ),
    (
        "identify the steps to migrate the database to the new schema",
        "planning", None,
        "planning: steps to"
    ),

    # ── config_edit ───────────────────────────────────────────────────────────
    (
        "update the yaml config file to add the new parameter",
        "config_edit", None,
        "config_edit: yaml + config + parameter"
    ),
    (
        "set this environment variable in the .env file",
        "config_edit", None,
        "config_edit: environment variable + .env"
    ),
    (
        "modify the JSON settings for the model endpoint",
        "config_edit", None,
        "config_edit: json + setting"
    ),

    # ── prompt_engineering ────────────────────────────────────────────────────
    (
        "refine the system prompt to handle this edge case better",
        "prompt_engineering", None,
        "prompt_engineering: system prompt"
    ),
    (
        "add a few-shot example to the existing instruction set",
        "prompt_engineering", None,
        "prompt_engineering: few-shot + instruction"
    ),
    (
        "the LLM keeps ignoring the chain-of-thought instruction",
        "prompt_engineering", None,
        "prompt_engineering: llm + chain-of-thought + instruction"
    ),

    # ── git_ops ───────────────────────────────────────────────────────────────
    (
        "commit these changes with a descriptive message",
        "git_ops", None,
        "git_ops: commit"
    ),
    (
        "create a branch for this hotfix",
        "git_ops", None,
        "git_ops: branch"
    ),
    (
        "merge the pull request into main",
        "git_ops", None,
        "git_ops: merge + pull request"
    ),

    # ── file_ops ──────────────────────────────────────────────────────────────
    (
        "list the files in the extensions directory",
        "file_ops", None,
        "KNOWN GAP: signal is r'\\blist\\s+(?:files|dir...)\\b' -- 'the' breaks it. "
        "Fix: add (?:the\\s+)? to signal. Currently classifies as conversation."
    ),
    (
        "read the file and display the output",
        "file_ops", None,
        "file_ops: read the file"
    ),

    # ── orientation ───────────────────────────────────────────────────────────
    (
        "how are you doing today, quick check-in before we start",
        "orientation", None,
        "orientation: how are you + check-in"
    ),
    (
        "run the self-assessment protocol",
        "orientation", None,
        "orientation: self-assessment"
    ),
    (
        "where we left off last session with the BST",
        "orientation", None,
        "orientation: where we left off"
    ),

    # ── meta_cognitive ────────────────────────────────────────────────────────
    (
        "how did you approach that debugging problem",
        "meta_cognitive", None,
        "meta_cognitive: how did you approach"
    ),
    (
        "describe your process and how you think through architecture decisions",
        "meta_cognitive", None,
        "meta_cognitive: describe your process + how you think"
    ),

    # ── philosophical ─────────────────────────────────────────────────────────
    (
        "what does this mean for how we think about continuity",
        "philosophical", None,
        "philosophical: what does this mean"
    ),
    (
        "do you think there is a real principle here worth preserving",
        "philosophical", None,
        "philosophical: do you think + preservation"
    ),

    # ── conversation ──────────────────────────────────────────────────────────
    (
        "thanks for the detailed explanation",
        "conversation", None,
        "conversation: thank"
    ),
    (
        "hello, can you help me understand this",
        "conversation", None,
        "conversation: hello + can you help"
    ),

    # ── Compound Cases ────────────────────────────────────────────────────────
    # Primary wins by score or priority tiebreak. Secondary is checked separately.
    (
        "debug this traceback and implement the fix",
        "bugfix", "coding",
        "compound: bugfix(debug+traceback=2) > coding(implement=1)"
    ),
    (
        "install pip and fix this broken import error",
        "bugfix", "system_admin",
        "compound: tie(bugfix=2,sysadmin=2), priority: bugfix=3 wins"
    ),
    (
        "analyze the config.yaml and update the parameters",
        "config_edit", "analysis",
        "compound: config_edit(config+yaml+parameter=3) > analysis(analyz=1)"
    ),
    (
        "write a function to check git status",
        "coding", "git_ops",
        "compound: tie(coding=1,git=1), priority: coding=4 wins"
    ),
    (
        "the system prompt is broken",
        "prompt_engineering", "bugfix",
        "compound: prompt_eng(prompt+system_prompt=2) > bugfix(broken=1)"
    ),
    (
        "review the progress and plan the next steps",
        "analysis", "planning",
        "compound: tie(analysis=1,planning=1), priority: analysis=2 wins"
    ),
    (
        "commit the benchmark results to the repo",
        "git_ops", "analysis",
        "compound: git_ops(commit+repo=2) > analysis(benchmark=1)"
    ),
    (
        "write a script to check network connectivity",
        "coding", "system_admin",
        "compound: tie(coding=1,sysadmin=1), priority: coding=4 wins"
    ),
    (
        "plan the git branching strategy for this release",
        "planning", "git_ops",
        "compound: tie(planning=plan+strategy=2, git_ops=git+branch=2), priority: planning=5 wins"
    ),
    (
        "fix the config.yaml indentation error",
        "bugfix", "config_edit",
        "compound: tie(bugfix=2,config=2), priority: bugfix=3 wins"
    ),
    # Edge: looks like orientation ("how are we") but "we" not "you" — no orientation match
    (
        "how are we doing on the project roadmap",
        "planning", None,
        "edge: 'how are we' does NOT match orientation (requires 'you')"
    ),
    # Edge: planning + investigation compound
    (
        "research the best approach to architect this pipeline",
        "investigation", "planning",
        "compound: investigation(research=1) tie planning(best approach+architect=2)? "
        "planning: best approach(1) + architect(1) = 2; investigation: research(1) = 1 "
        "→ primary=planning(2), secondary=investigation(1)"
    ),
]

# Fix the last test case — planning wins (score 2 vs 1):
# planning: best approach(1) + architect(1) = 2; investigation: research(1) = 1
# primary=planning, secondary=investigation
TEST_CASES[-1] = (
    "research the best approach to architect this pipeline",
    "planning", "investigation",
    "compound: planning(best approach+architect=2) > investigation(research=1)"
)


# ─── Eval Engine ──────────────────────────────────────────────────────────────

def run_eval(bst, test_cases: list, verbose: bool = True) -> float:
    """Run all test cases. Returns overall accuracy (0.0–1.0)."""
    score_fn   = bst._score_all_domains
    extract_fn = bst._extract_compound

    domain_stats: dict = {}   # domain → [correct, total]
    compound_correct = 0
    compound_total   = 0
    failures: list   = []

    for text, exp_primary, exp_secondary, label in test_cases:
        scores  = score_fn(text)
        primary, secondary = extract_fn(scores)

        got_primary   = primary["domain"]
        got_secondary = secondary["domain"] if secondary else None

        primary_ok   = (got_primary == exp_primary)
        secondary_ok = True  # only checked when exp_secondary is set

        if exp_secondary is not None:
            compound_total += 1
            if got_secondary == exp_secondary:
                compound_correct += 1
            else:
                secondary_ok = False

        # Domain stats track primary accuracy
        if exp_primary not in domain_stats:
            domain_stats[exp_primary] = [0, 0]
        domain_stats[exp_primary][1] += 1
        if primary_ok:
            domain_stats[exp_primary][0] += 1

        if not primary_ok or not secondary_ok:
            failures.append({
                "input":         text,
                "label":         label,
                "exp_primary":   exp_primary,
                "got_primary":   got_primary,
                "exp_secondary": exp_secondary,
                "got_secondary": got_secondary,
                "primary_ok":    primary_ok,
                "secondary_ok":  secondary_ok,
            })

    # ── Print results ──────────────────────────────────────────────────────────
    if verbose:
        print("\n[BST EVAL] Domain accuracy:")
        domain_order = [
            "investigation", "coding", "bugfix", "analysis", "system_admin",
            "planning", "config_edit", "prompt_engineering", "git_ops", "file_ops",
            "orientation", "meta_cognitive", "philosophical", "conversation",
        ]
        for domain in domain_order:
            if domain not in domain_stats:
                continue
            correct, total = domain_stats[domain]
            pct = 100.0 * correct / total if total else 0
            flag = "  << FAIL" if pct < 100.0 else ""
            print(f"  {domain:<22} {correct}/{total}   {pct:5.1f}%{flag}")

        if compound_total > 0:
            cp = 100.0 * compound_correct / compound_total
            flag = "  << FAIL" if cp < 100.0 else ""
            print(f"\n[BST EVAL] Compound detection: {compound_correct}/{compound_total}   {cp:.1f}%{flag}")

        if failures:
            print(f"\n[BST EVAL] Failures ({len(failures)}):")
            for f in failures:
                print(f"  [{f['label']}]")
                print(f"    input:   {f['input']!r}")
                if not f["primary_ok"]:
                    print(f"    primary: expected={f['exp_primary']}  got={f['got_primary']}")
                if not f["secondary_ok"]:
                    print(f"    secondary: expected={f['exp_secondary']}  got={f['got_secondary']}")

    # Overall accuracy counts primary-only cases as 1 test, compound cases as 2
    total_assertions = len(test_cases) + compound_total
    correct_assertions = sum(
        1 for _, ep, es, _ in test_cases
        if ep in domain_stats  # primary correct
    )
    # Recount properly
    primary_correct = sum(s[0] for s in domain_stats.values())
    primary_total   = sum(s[1] for s in domain_stats.values())
    total_correct   = primary_correct + compound_correct
    total_tests     = primary_total + compound_total
    accuracy = total_correct / total_tests if total_tests else 0.0

    print(f"\n[BST EVAL] Primary accuracy:  {primary_correct}/{primary_total}")
    if compound_total > 0:
        print(f"[BST EVAL] Compound accuracy:  {compound_correct}/{compound_total}")
    print(f"[BST EVAL] Overall:           {total_correct}/{total_tests}")
    print(f"\naccuracy: {accuracy:.2f}")

    return accuracy


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="BST classification accuracy eval")
    parser.add_argument(
        "--bst-path", default=None,
        help="Path to _11_belief_state_tracker.py (auto-detected if not given)"
    )
    parser.add_argument(
        "--threshold", type=float, default=0.85,
        help="Accuracy threshold below which eval is considered a regression (default: 0.85)"
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress per-domain breakdown, print only accuracy line"
    )
    args = parser.parse_args()

    bst_path = args.bst_path or os.environ.get("BST_PATH") or _bst_path_default()
    print(f"[BST EVAL] Loading BST from: {bst_path}", flush=True)
    print(f"[BST EVAL] Running {len(TEST_CASES)} test cases...", flush=True)

    bst = _load_bst(bst_path)
    if bst is None:
        sys.exit(1)

    accuracy = run_eval(bst, TEST_CASES, verbose=not args.quiet)

    if accuracy < args.threshold:
        print(f"\n[BST EVAL] REGRESSION: accuracy {accuracy:.2f} < threshold {args.threshold:.2f}")

    # Always exit 0 — let the autoresearch loop read the accuracy line
    # and decide keep/discard based on metric delta.
    sys.exit(0)


if __name__ == "__main__":
    main()
