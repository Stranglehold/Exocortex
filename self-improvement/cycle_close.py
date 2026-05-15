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
  python3 /a0/usr/Exocortex/self-improvement/cycle_close.py \
    --cycle-type MAINTAIN \
    --sleep-findings 3 \
    --pages-deepened 0 \
    --skills-captured 0 \
    --memories-saved 2 \
    --priority routine \
    --activity "Sleep consolidation, 3 memories promoted" \
    --status completed

All flags except --cycle-type and --activity have sensible defaults (0 or "routine").
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

_WORKDIR        = "/a0/usr/workdir/self-improvement"
_JOURNAL_PATH   = "/a0/usr/workdir/self-improvement/journal.jsonl"
_CHECKPOINT_DIR = "/a0/usr/workdir/self-improvement/checkpoints"
_OFFICE_DIR     = "/a0/usr/Exocortex/office"
_FEED_PATH      = "/a0/usr/Exocortex/office/feed.jsonl"
_SIGNAL_PATH    = "/a0/usr/Exocortex/office/cycle_result.json"
_STATE_PATH     = "/a0/usr/Exocortex/office/engine_state.json"


def _read_state() -> dict:
    try:
        if os.path.exists(_STATE_PATH):
            with open(_STATE_PATH) as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def main():
    parser = argparse.ArgumentParser(description="Close an idle cycle — batch bookkeeping")
    parser.add_argument("--cycle-type",     required=True,
                        choices=["MAINTAIN", "BUILD", "EXPLORE"],
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

    os.makedirs(_WORKDIR, exist_ok=True)
    os.makedirs(_CHECKPOINT_DIR, exist_ok=True)
    os.makedirs(_OFFICE_DIR, exist_ok=True)

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
    }
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
    }
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
        "priority":         args.priority,
        "status":           args.status,
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
