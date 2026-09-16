#!/usr/bin/env python3
"""
cycle_close.py — V2 Idle Cycle Bookkeeping
===========================================
Called by the agent as its final step at the end of every idle cycle.
Batches three separate agent tool calls into one:
  1. Append cycle summary to journal.jsonl
  2. Append to office/feed.jsonl (with priority field)
  3. Write cycle_result.json (signal for idle trigger state machine)

Usage:
  python3 /a0/usr/workdir/workspace/self-improvement/cycle_close.py \
    --cycle-type MAINTAIN \
    --sleep-findings 3 \
    --pages-deepened 0 \
    --skills-captured 0 \
    --memories-saved 2 \
    --priority routine \
    --activity "Sleep consolidation, 3 memories promoted" \
    --status completed

All flags except --cycle-type and --activity have sensible defaults (0 or "routine").

Step 0 of the synthesis ladder (2026-09-14, Fable's §11.3, Jake's go): a fourth cycle type SYNTHESIZE, two new
arguments, and one gate.
  --syntheses N          synthesis pages written this cycle (SYNTHESIZE cycles; default 0)
  --builds-on "p1,p2"    the paths the synthesis joined, comma-separated, relative to the workspace or absolute
  --page PATH            the synthesis page itself (wiki/synthesis/{date}_{slug}.md). Required in effect whenever
                         --syntheses > 0: the gate validated only the INPUTS until Kestrel found (2026-09-14, before
                         the first SYNTHESIZE) that a cycle naming two real sources and writing no page closed as a
                         clean synthesis, inflating the one number step 0 exists to move. A missing or absent page
                         corrects syntheses to 0 with the claim recorded in verify_flag; the close itself never fails
                         on it (a failed close is a reaped cycle, which is worse than a corrected count).
  gate                   builds_on_width_slugs = number of DISTINCT slugs among the builds_on paths that exist on
                         disk (slug = basename minus extension minus a leading date prefix). A synthesis with
                         width < 2 is an R1 page wearing a synthesis heading and counts as 0; the claim and the
                         measured width are recorded in verify_flag. The field is named _slugs because slugs
                         over-count one thread's artifacts; the ledger's distinct-thread measure arrives later as a
                         SEPARATE field (builds_on_width_threads), never under this name (Kestrel, 2026-09-14).
  verify_flag            JOURNAL SCHEMA NOTE: from 2026-09-14 this is a dict keyed by the check that fired
                         ({"pages_deepened": {claimed, actual_writes}} and/or {"syntheses": {claimed, existing,
                         missing, width_slugs}}). Before that date it was the flat pages object
                         {"claimed": N, "actual_writes": M}; two historical journal rows carry that flat form. A
                         reader must accept both shapes (no code consumer existed at the change; Kestrel checked).
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

_WORKDIR        = "/a0/usr/workdir/workspace/self-improvement"
_JOURNAL_PATH   = "/a0/usr/workdir/workspace/self-improvement/journal.jsonl"
_CHECKPOINT_DIR = "/a0/usr/workdir/workspace/self-improvement/checkpoints"
_OFFICE_DIR     = "/a0/usr/workdir/workspace/office"
_FEED_PATH      = "/a0/usr/workdir/workspace/office/feed.jsonl"
_SIGNAL_PATH    = "/a0/usr/workdir/workspace/office/cycle_result.json"
_STATE_PATH     = "/a0/usr/workdir/workspace/office/engine_state.json"
_WIKI_DIR       = "/a0/usr/workdir/workspace/wiki"
_WORKSPACE      = "/a0/usr/workdir/workspace"

_DATE_PREFIX = re.compile(r"^(\d{4}-\d{2}-\d{2}|\d{8})[_-]")


def _read_state() -> dict:
    try:
        if os.path.exists(_STATE_PATH):
            with open(_STATE_PATH) as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _count_wiki_writes_since(cycle_start: float) -> int:
    """Deterministic ground truth for pages_deepened: count distinct wiki .md files
    modified at/after the cycle start (excludes the index). Returns -1 if unknowable
    (no valid cycle_start) so the caller degrades gracefully and trusts the claim."""
    if not cycle_start or cycle_start <= 0:
        return -1
    count = 0
    try:
        for root, _dirs, files in os.walk(_WIKI_DIR):
            for fn in files:
                if fn.endswith(".md") and fn != "index.md":
                    try:
                        if os.path.getmtime(os.path.join(root, fn)) >= cycle_start:
                            count += 1
                    except OSError:
                        pass
    except Exception:
        return -1
    return count


def _slug(path: str) -> str:
    base = os.path.splitext(os.path.basename(path.replace("\\", "/")))[0]
    return _DATE_PREFIX.sub("", base).strip().lower()


def _builds_on_width(builds_on: str) -> dict:
    """Resolve the comma-separated builds_on paths; count distinct slugs among those that exist."""
    paths = [p.strip() for p in (builds_on or "").split(",") if p.strip()]
    existing, missing = [], []
    for p in paths:
        full = p if os.path.isabs(p) else os.path.join(_WORKSPACE, p)
        (existing if os.path.isfile(full) else missing).append(p)
    return {
        "paths": paths,
        "existing": existing,
        "missing": missing,
        "width_slugs": len({_slug(p) for p in existing}),
    }


def main():
    parser = argparse.ArgumentParser(description="Close an idle cycle — batch bookkeeping")
    parser.add_argument("--cycle-type",     required=True,
                        choices=["MAINTAIN", "BUILD", "EXPLORE", "SYNTHESIZE"],
                        help="Type of cycle being closed")
    parser.add_argument("--activity",       required=True,
                        help="One-line summary of what this cycle accomplished")
    parser.add_argument("--sleep-findings", type=int, default=0,
                        help="MAINTAIN: total promotions + deduplications + anti-patterns")
    parser.add_argument("--pages-deepened", type=int, default=0,
                        help="BUILD: number of wiki pages deepened")
    parser.add_argument("--skills-captured", type=int, default=0,
                        help="Skills written to auto-generated/ this cycle")
    parser.add_argument("--memories-saved", type=int, default=0,
                        help="memory_save calls made this cycle")
    parser.add_argument("--field-reports",  type=int, default=0,
                        help="EXPLORE: field reports produced")
    parser.add_argument("--integrity-issues", type=int, default=0,
                        help="MAINTAIN: issues found by integrity_check.py")
    parser.add_argument("--syntheses",      type=int, default=0,
                        help="SYNTHESIZE: synthesis pages written (gated on builds_on width >= 2)")
    parser.add_argument("--builds-on",      default="",
                        help="SYNTHESIZE: comma-separated paths the synthesis joined (workspace-relative or absolute)")
    parser.add_argument("--page",           default="",
                        help="SYNTHESIZE: path of the synthesis page written this cycle (gated on existence when --syntheses > 0)")
    parser.add_argument("--priority",       default="routine",
                        choices=["routine", "notable", "urgent"],
                        help="Office panel priority (routine/notable/urgent)")
    parser.add_argument("--status",         default="completed",
                        choices=["completed", "interrupted", "circuit_breaker"],
                        help="Cycle completion status")
    parser.add_argument("--steps-used",     type=int, default=0,
                        help="Number of steps consumed this cycle")
    args = parser.parse_args()

    now_iso = datetime.now(timezone.utc).isoformat()
    state   = _read_state()
    cycle_n = state.get("cycle_count", 0)
    # context_id is the JOIN KEY between this row and the watcher's cycle_endings.jsonl (cycle numbers repeat across
    # the journal's history). Source of truth: engine_state.cycle_context_id, written by the daemon at fire time;
    # A0_CHAT_ID only as a fallback (it is "a secondary confirmation when available" by its own comment). Until
    # 2026-09-14 no journal row carried one, so a join on it found nothing (Kestrel).
    context_id = (state.get("cycle_context_id") or os.environ.get("A0_CHAT_ID") or "") or None

    os.makedirs(_WORKDIR, exist_ok=True)
    os.makedirs(_CHECKPOINT_DIR, exist_ok=True)
    os.makedirs(_OFFICE_DIR, exist_ok=True)

    # ── Ground-truth skills_captured (Cycle-to-Skill Pipeline, Path A) ─────────
    # _31_failure_lesson_capture tallies auto-captured skills to this counter file.
    # Use it as the authoritative count (the agent's --skills-captured is often 0
    # because it doesn't know the deterministic capture extension fired). Then reset.
    _PENDING_SKILLS = os.path.join(_OFFICE_DIR, "skills_captured_pending.json")
    try:
        if os.path.exists(_PENDING_SKILLS):
            with open(_PENDING_SKILLS, encoding="utf-8") as _f:
                _auto = int(json.load(_f).get("count", 0))
            if _auto > 0:
                args.skills_captured = max(int(args.skills_captured), _auto)
            os.remove(_PENDING_SKILLS)  # reset for the next cycle
    except Exception as _e:
        print(f"[cycle_close] WARNING: skills_captured tally read failed: {_e}", file=sys.stderr)

    # ── Verify-before-log gate: pages_deepened vs real file writes ─────────────
    # Deterministic check (same spirit as the skills_captured ground-truth above):
    # a cycle can only have deepened pages that were actually written this cycle.
    # Count wiki .md files modified since the cycle started; if the agent's claim
    # exceeds that, correct it down and record the discrepancy in the journal.
    # Catches over-reporting / confabulation regardless of which model is loaded.
    pages_verify = None
    _real_writes = _count_wiki_writes_since(float(state.get("last_cycle_start", 0) or 0))
    if _real_writes >= 0 and args.pages_deepened > _real_writes:
        pages_verify = {"claimed": args.pages_deepened, "actual_writes": _real_writes}
        print(f"[cycle_close] VERIFY-GATE: pages_deepened claimed={args.pages_deepened} "
              f"but {_real_writes} wiki file(s) written this cycle — corrected to {_real_writes}",
              file=sys.stderr)
        args.pages_deepened = _real_writes

    # ── Synthesis gate: a synthesis must join >= 2 distinct sources that exist ───
    synth_verify = None
    bo = _builds_on_width(args.builds_on) if (args.builds_on or args.syntheses) else None
    page = (args.page or "").strip()
    page_full = (page if os.path.isabs(page) else os.path.join(_WORKSPACE, page)) if page else ""
    page_exists = bool(page_full) and os.path.isfile(page_full)
    if args.syntheses > 0 and not page_exists:
        # OUTPUT gate: the synthesis page must exist. A cycle that joined two real sources and wrote nothing is not
        # a synthesis, however good its inputs (Kestrel, 2026-09-14).
        synth_verify = {"claimed": args.syntheses, "page": page or None, "page_exists": False,
                        "existing": len(bo["existing"]) if bo else 0,
                        "missing": bo["missing"] if bo else [], "width_slugs": bo["width_slugs"] if bo else 0}
        print(f"[cycle_close] VERIFY-GATE: syntheses claimed={args.syntheses} but the synthesis page "
              f"{'was not given (--page)' if not page else 'does not exist: ' + page} — corrected to 0", file=sys.stderr)
        args.syntheses = 0
    elif bo is not None and args.syntheses > 0 and bo["width_slugs"] < 2:
        synth_verify = {"claimed": args.syntheses, "page": page, "page_exists": True,
                        "existing": len(bo["existing"]),
                        "missing": bo["missing"], "width_slugs": bo["width_slugs"]}
        print(f"[cycle_close] VERIFY-GATE: syntheses claimed={args.syntheses} but builds_on joins "
              f"{bo['width_slugs']} distinct existing source(s) ({len(bo['existing'])} of {len(bo['paths'])} "
              f"paths exist) — corrected to 0", file=sys.stderr)
        args.syntheses = 0

    # ── 1. Journal entry ──────────────────────────────────────────────────────
    journal_entry = {
        "type":             "cycle_close",
        "cycle_number":     cycle_n,
        "cycle_type":       args.cycle_type,
        "timestamp":        now_iso,
        "activity":         args.activity,
        "status":           args.status,
        "priority":         args.priority,
        "sleep_findings":   args.sleep_findings,
        "pages_deepened":   args.pages_deepened,
        "skills_captured":  args.skills_captured,
        "memories_saved":   args.memories_saved,
        "field_reports":    args.field_reports,
        "integrity_issues": args.integrity_issues,
        "steps_used":       args.steps_used,
        "syntheses":        args.syntheses,
        "context_id":       context_id,
    }
    if bo is not None:
        journal_entry["builds_on"] = bo["paths"]
        journal_entry["builds_on_width_slugs"] = bo["width_slugs"]
    if page or args.cycle_type == "SYNTHESIZE":
        journal_entry["page"] = page or None
        journal_entry["page_exists"] = page_exists
    verify = {}
    if pages_verify:
        verify["pages_deepened"] = pages_verify
    if synth_verify:
        verify["syntheses"] = synth_verify
    if verify:
        journal_entry["verify_flag"] = verify
    try:
        with open(_JOURNAL_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(journal_entry) + "\n")
        print(f"[cycle_close] Journal entry written (cycle {cycle_n}, {args.cycle_type})")
    except Exception as e:
        print(f"[cycle_close] WARNING: journal write failed: {e}", file=sys.stderr)

    # ── 2. Office feed entry ──────────────────────────────────────────────────
    feed_entry = {
        "timestamp":        now_iso,
        "cycle_number":     cycle_n,
        "cycle_type":       args.cycle_type.lower(),
        "priority":         args.priority,
        "activity":         args.activity,
        "status":           args.status,
        "sleep_findings":   args.sleep_findings,
        "pages_deepened":   args.pages_deepened,
        "skills_captured":  args.skills_captured,
        "memories_saved":   args.memories_saved,
        "field_reports":    args.field_reports,
        "integrity_issues": args.integrity_issues,
        "steps_used":       args.steps_used,
        "syntheses":        args.syntheses,
        "context_id":       context_id,
    }
    if bo is not None:
        feed_entry["builds_on_width_slugs"] = bo["width_slugs"]
    try:
        with open(_FEED_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(feed_entry) + "\n")
        print(f"[cycle_close] Office feed updated (priority={args.priority})")
    except Exception as e:
        print(f"[cycle_close] WARNING: feed write failed: {e}", file=sys.stderr)

    # ── 3. Cycle result signal (read by idle trigger on next poll) ────────────
    signal = {
        "cycle_type":       args.cycle_type,
        "cycle_number":     cycle_n,
        "timestamp":        now_iso,
        "sleep_findings":   args.sleep_findings,
        "pages_deepened":   args.pages_deepened,
        "syntheses":        args.syntheses,
        "priority":         args.priority,
        "status":           args.status,
        # Self-reported completion: the daemon DEASSERTS the "cycle in progress"
        # flag on this signal (authoritative), instead of inferring completion from
        # task-liveness. Primary key is `completed_ts` — a completion written AFTER
        # the cycle fired unambiguously identifies THIS cycle (only one runs at a
        # time), so it works even when A0_CHAT_ID is unset. `context_id` is a
        # secondary confirmation when available.
        "completed_ts":     datetime.now(timezone.utc).timestamp(),
        "context_id":       context_id or "",
    }
    try:
        tmp = _SIGNAL_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(signal, f)
        os.replace(tmp, _SIGNAL_PATH)
        print(f"[cycle_close] Cycle result signal written")
    except Exception as e:
        print(f"[cycle_close] WARNING: signal write failed: {e}", file=sys.stderr)

    print(f"[cycle_close] Cycle {cycle_n} ({args.cycle_type}) closed — {args.status}")


if __name__ == "__main__":
    main()
