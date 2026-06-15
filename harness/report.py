#!/usr/bin/env python3
"""
BP-02 Evaluation Harness — Report
=================================

Reads a results JSONL log and computes pass^1 and pass^k per task, plus a
readable summary.

pass^k (tau-bench): the probability that a randomly chosen set of k of the N
trials ALL pass. Unbiased estimator with c passes out of n trials:

    pass^k = C(c, k) / C(n, k)        (0 if c < k; undefined/skipped if n < k)

pass^1 = c/n (average single-trial success). pass^k decays faster than pass^1
when failures are present — which is the point: it measures consistency, not
average success. A system that passes 4/5 looks fine at pass^1 (0.80) but
pass^5 = 0 (it never passed all five).

Usage:
  python report.py --run-id manual
  python report.py --file results/results_manual.jsonl
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(HARNESS_DIR, "results")

K_REPORT = (1, 2, 3, 5, 8)


def pass_k(c: int, n: int, k: int) -> float | None:
    if k > n:
        return None
    if c < k:
        return 0.0
    return math.comb(c, k) / math.comb(n, k)


def main():
    ap = argparse.ArgumentParser(description="BP-02 harness report")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--file", default=None)
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    path = args.file or os.path.join(RESULTS_DIR, f"results_{args.run_id or 'manual'}.jsonl")
    if not os.path.exists(path):
        print(f"[report] no results file: {path}")
        return 1

    by_task: dict[str, list[dict]] = defaultdict(list)
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            by_task[r.get("task_id", "?")].append(r)

    print(f"=== BP-02 report: {os.path.basename(path)} ===\n")
    header = f"{'task':<8} {'n':>3} {'pass':>5} " + " ".join(f"p^{k:<4}" for k in K_REPORT) + f"  {'avg_s':>6}"
    print(header)
    print("-" * len(header))

    overall = []
    for task_id in sorted(by_task):
        rows = by_task[task_id]
        n = len(rows)
        c = sum(1 for r in rows if r.get("passed"))
        durs = [r.get("duration_s", 0) or 0 for r in rows]
        avg_s = sum(durs) / n if n else 0
        cells = []
        for k in K_REPORT:
            v = pass_k(c, n, k)
            cells.append("  -  " if v is None else f"{v:5.2f}")
        print(f"{task_id:<8} {n:>3} {c:>2}/{n:<2} " + " ".join(cells) + f"  {avg_s:6.1f}")
        overall.append((task_id, c, n))

    tc = sum(c for _, c, _ in overall)
    tn = sum(n for _, _, n in overall)
    print("-" * len(header))
    print(f"TOTAL trials: {tc}/{tn} passed (pass@1={tc/tn:.2f})" if tn else "no trials")

    # surface failures with notes
    fails = [(r["task_id"], r["trial"], r.get("notes", ""))
             for rows in by_task.values() for r in rows if not r.get("passed")]
    if fails:
        print("\nFailures:")
        for tid, trial, notes in fails:
            print(f"  {tid} trial {trial}: {notes[:160]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
