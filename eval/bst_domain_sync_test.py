#!/usr/bin/env python3
"""
BST Domain Sync Test — GAP-02 (Audit Session 002)
===================================================
Verifies that the compound BST classifier domains (DOMAIN_CONFIGS keys) and
the slot resolver domains (slot_taxonomy.json domains) are synchronized.

When the compound BST classifies a domain that has no slot definition in
slot_taxonomy.json, the BSTEngine falls back to its own internal classification
(line 1323 of _11_belief_state_tracker.py), silently ignoring the compound
result. This test catches that drift before it causes silent behavior changes.

Usage:
    # From Windows host (Kestrel sessions):
    C:/Users/Jake/miniconda3/python.exe eval/bst_domain_sync_test.py

    # From inside container:
    python3 /a0/usr/Exocortex/eval/bst_domain_sync_test.py

    # With strict mode (exit 1 on any mismatch):
    python3 bst_domain_sync_test.py --strict

Exit codes:
    0 — All domains synced (or only known/accepted mismatches)
    1 — New mismatches detected
    2 — File not found or parse error

Architecture note:
    The compound BST (DOMAIN_CONFIGS) handles enrichment and domain detection.
    The slot resolver (_BSTEngine) uses slot_taxonomy.json for slot definitions.
    These are intentionally different abstraction levels — but the compound BST
    domain names MUST match slot_taxonomy.json domain keys for slot resolution
    to work. When they diverge, the slot resolver silently falls back to its own
    domain classification.

    DOMAIN_CONFIGS is canonical. slot_taxonomy.json must match it.
    Reconciled 2026-04-17 per Opus spec (GAP-02): 16/16 domains matched.
    This test is enforcing a standard that is already met — use it as a
    pre-commit hook to keep it that way.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# ── File paths ────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT   = SCRIPT_DIR.parent

# Active BST extension (profile-path version — DEC-030)
BST_PATH = REPO_ROOT / "extensions" / "before_main_llm_call" / "_11_belief_state_tracker.py"
TAX_PATH = REPO_ROOT / "extensions" / "before_main_llm_call" / "slot_taxonomy.json"

# Container paths (for reference when running inside container)
BST_CONTAINER_PATH = Path("/a0/usr/agents/agent0/extensions/python/before_main_llm_call/_11_belief_state_tracker.py")
TAX_CONTAINER_PATH = Path("/a0/usr/agents/agent0/extensions/python/before_main_llm_call/slot_taxonomy.json")

# ── Known accepted mismatches ─────────────────────────────────────────────────
#
# These are documented divergences that are either intentional or pending a
# design decision. New mismatches outside this set fail the test.
# To add a mismatch: document the reason and get Opus to sign off on it.
#
# Reconciled 2026-04-17 (GAP-02, Opus spec): 16/16 domains matched.
# Both dicts are intentionally empty. Any new entry here is a regression —
# fix it in the source instead of adding an exception.

BST_ONLY_ACCEPTED: dict = {}

TAXONOMY_ONLY_ACCEPTED: dict = {}


# ── Parsing ───────────────────────────────────────────────────────────────────

def extract_bst_domains(bst_path: Path) -> set[str]:
    """Parse DOMAIN_CONFIGS top-level keys from BST source without importing it."""
    src = bst_path.read_text(encoding="utf-8")

    m = re.search(r"DOMAIN_CONFIGS\s*(?::\s*dict)?\s*=\s*\{", src)
    if not m:
        raise ValueError("DOMAIN_CONFIGS not found in BST file")

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

    # Match keys at 4-space indent (top-level keys of DOMAIN_CONFIGS)
    keys = re.findall(r"""^\s{4}["'](\w[\w+]*)["']\s*:""", block, re.MULTILINE)
    return set(keys)


def extract_taxonomy_domains(tax_path: Path) -> set[str]:
    """Read domain keys from slot_taxonomy.json."""
    with open(tax_path, encoding="utf-8") as f:
        taxonomy = json.load(f)
    return set(taxonomy.get("domains", {}).keys())


# ── Test logic ────────────────────────────────────────────────────────────────

def run_sync_test(
    bst_path: Path,
    tax_path: Path,
    strict: bool = False,
) -> int:
    """
    Run domain sync test.
    Returns: 0 = pass, 1 = new mismatch found, 2 = file error.
    """
    print("=== BST Domain Sync Test (GAP-02) ===")
    print()

    # Resolve container paths if running inside container
    if not bst_path.exists() and BST_CONTAINER_PATH.exists():
        bst_path = BST_CONTAINER_PATH
        tax_path = TAX_CONTAINER_PATH
        print(f"[INFO] Running from container — using container paths")

    if not bst_path.exists():
        print(f"[ERROR] BST file not found: {bst_path}", file=sys.stderr)
        return 2
    if not tax_path.exists():
        print(f"[ERROR] Taxonomy file not found: {tax_path}", file=sys.stderr)
        return 2

    print(f"BST:      {bst_path}")
    print(f"Taxonomy: {tax_path}")
    print()

    try:
        bst_domains = extract_bst_domains(bst_path)
        tax_domains = extract_taxonomy_domains(tax_path)
    except Exception as e:
        print(f"[ERROR] Parse failure: {e}", file=sys.stderr)
        return 2

    matched     = bst_domains & tax_domains
    bst_only    = bst_domains - tax_domains    # BST domain, no slot definition
    tax_only    = tax_domains - bst_domains    # Slot definition, no BST detection

    print(f"BST DOMAIN_CONFIGS domains  : {len(bst_domains):3d}")
    print(f"Taxonomy domains            : {len(tax_domains):3d}")
    print(f"Matched (slot resolution OK): {len(matched):3d}")
    print()

    # ── Matched domains ──────────────────────────────────────────────────────
    print("=== MATCHED (slot resolution will work) ===")
    for d in sorted(matched):
        print(f"  OK  {d}")
    print()

    # ── BST domains without taxonomy entries ─────────────────────────────────
    new_bst_only    = bst_only - set(BST_ONLY_ACCEPTED.keys())
    known_bst_only  = bst_only & set(BST_ONLY_ACCEPTED.keys())

    print("=== BST-ONLY (no slot resolution — BSTEngine falls back to internal classify) ===")
    if not bst_only:
        print("  (none)")
    else:
        for d in sorted(known_bst_only):
            status = "[KNOWN] " if not strict else "[MISMATCH]"
            print(f"  {status} {d}")
            if not strict:
                print(f"           > {BST_ONLY_ACCEPTED[d]}")
        for d in sorted(new_bst_only):
            print(f"  [NEW-MISMATCH] {d}  ← NO ACCEPTED REASON — NEEDS FIX")
    print()

    # ── Taxonomy domains without BST detection ───────────────────────────────
    new_tax_only   = tax_only - set(TAXONOMY_ONLY_ACCEPTED.keys())
    known_tax_only = tax_only & set(TAXONOMY_ONLY_ACCEPTED.keys())

    print("=== TAXONOMY-ONLY (slot definitions exist but BST never classifies these) ===")
    if not tax_only:
        print("  (none)")
    else:
        for d in sorted(known_tax_only):
            status = "[KNOWN] " if not strict else "[MISMATCH]"
            print(f"  {status} {d}")
            if not strict:
                print(f"           > {TAXONOMY_ONLY_ACCEPTED[d]}")
        for d in sorted(new_tax_only):
            print(f"  [NEW-MISMATCH] {d}  ← NO ACCEPTED REASON — NEEDS FIX")
    print()

    # ── Summary ──────────────────────────────────────────────────────────────
    if strict:
        fail = bool(bst_only or tax_only)
    else:
        fail = bool(new_bst_only or new_tax_only)

    print("=== SUMMARY ===")
    if fail:
        print(f"  FAIL — {len(new_bst_only)} new BST-only, {len(new_tax_only)} new taxonomy-only")
        print()
        print("  ACTION: Add slot definitions in slot_taxonomy.json for new BST domains,")
        print("  OR add BST signal detection for new taxonomy domains,")
        print("  OR add to accepted-mismatch list with documented reason + Opus sign-off.")
    else:
        if strict:
            print(f"  PASS (strict) — all {len(matched)} domains matched")
        else:
            total_known = len(known_bst_only) + len(known_tax_only)
            print(f"  PASS - {len(matched)} matched, {total_known} known/accepted mismatches")
            if total_known > 0:
                print(f"  NOTE: {total_known} known mismatches are pending Opus design decision (GAP-02).")
                print(f"  Run with --strict to treat these as failures.")
    print()

    return 1 if fail else 0


# ── Entrypoint ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="BST domain/taxonomy sync validation test (GAP-02)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on ANY mismatch (including known/accepted ones)",
    )
    parser.add_argument(
        "--bst-path",
        type=Path,
        default=BST_PATH,
        help=f"Path to BST extension file (default: {BST_PATH})",
    )
    parser.add_argument(
        "--taxonomy-path",
        type=Path,
        default=TAX_PATH,
        help=f"Path to slot_taxonomy.json (default: {TAX_PATH})",
    )
    args = parser.parse_args()

    exit_code = run_sync_test(
        bst_path=args.bst_path,
        tax_path=args.taxonomy_path,
        strict=args.strict,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
