#!/usr/bin/env python3
"""
Reasoning Persistence — Gap Closure Unit Harness
=================================================
Companion to specs/REASONING_PERSISTENCE_GAP_TESTS.md

Covers the NOW-runnable unit tests (no server, no live cycles):
  GAP-001  T-001-a..e   — corrected _build_state_from_structured_signals logic
  GAP-005  T-005-a,b,d  — tried[] TTL filter + new-plan clear

Design principle (project methodology): every test must be able to FAIL.
This harness runs the GAP-001 scenarios against BOTH the corrected reference
implementation AND the original buggy draft, and asserts:
  - corrected impl PASSES every scenario
  - buggy impl FAILS the regression scenarios (T-001-a, T-001-b, T-001-e)
If the buggy impl ever "passes" a regression test, the test is too weak.

Run: python3 eval/test_reasoning_persistence_gaps.py
Exit 0 = all assertions hold (including buggy-fails-regression). Exit 1 = failure.
"""

import sys

FALLBACK = "<FALLBACK:last_tool>"  # stand-in for _extract_current_from_last_tool()


# ── Reference implementations ────────────────────────────────────────────────

def build_state_corrected(pace):
    """Corrected GAP-001 logic (specs/REASONING_PERSISTENCE_GAP_ANALYSIS.md,
    Kestrel review 2026-05-17). Value-match PACE steps; theory = task_summary."""
    if pace and isinstance(pace, dict):
        theory = pace.get("task_summary", "")[:120]
    else:
        theory = ""

    current = ""
    if pace and isinstance(pace, dict):
        current_step = pace.get("current_step", 1)
        tier = pace.get("active_tier", "primary")
        steps = pace.get("steps", [])
        matching = [s for s in steps if s.get("step") == current_step]
        if matching:
            action = matching[0].get(tier, "")
            current = f"PACE step {current_step}/{len(steps)} ({tier}): {action[:200]}"
        elif current_step > len(steps):
            current = f"PACE plan complete ({len(steps)} steps executed)"
        else:
            current = FALLBACK
    else:
        current = FALLBACK
    return {"theory": theory, "current": current}


def build_state_buggy(pace):
    """The ORIGINAL draft (pre-Kestrel-review). Position-indexed, domain-label
    theory. Kept ONLY so the harness can prove the tests catch the bug."""
    bst_domain = "investigation"  # the draft pulled this from BST belief state
    confidence = 0.85
    theory = f"Domain: {bst_domain} (confidence: {confidence:.0%})"

    if pace and isinstance(pace, dict):
        step = pace.get("current_step", 0)
        tier = pace.get("active_tier", "primary")
        steps = pace.get("steps", [])
        if step < len(steps):
            action = steps[step].get(tier, "")
            current = f"PACE step {step+1}/{len(steps)} ({tier}): {action[:200]}"
        else:
            current = f"PACE plan complete ({len(steps)} steps executed)"
    else:
        current = FALLBACK
    return {"theory": theory, "current": current}


def filter_tried_by_recency(tried_list, current_step, max_age=10):
    """GAP-005 TTL filter. Contract: drop if age > max_age, keep if age == max_age.
    Missing 'step' treated as 0 (legacy entries age out, no crash)."""
    return [e for e in tried_list
            if current_step - e.get("step", 0) <= max_age]


def apply_pace_change(tried_list, new_task: bool):
    """GAP-005 T-005-b: a new PACE plan clears prior tried[] entirely."""
    return [] if new_task else tried_list


# ── Fixtures ─────────────────────────────────────────────────────────────────

def make_plan(current_step, active_tier="primary", task_summary="TASK_X", n=3):
    return {
        "task_summary": task_summary,
        "current_step": current_step,
        "active_tier": active_tier,
        "steps": [
            {"step": i + 1,
             "name": f"Step{i+1}",
             "primary":     f"S{i+1}-primary-action",
             "alternate":   f"S{i+1}-alternate-action",
             "contingency": f"S{i+1}-contingency-action",
             "emergency":   f"S{i+1}-emergency-action"}
            for i in range(n)
        ],
    }


# ── Assertion plumbing ───────────────────────────────────────────────────────

RESULTS = []

def check(test_id, desc, cond):
    RESULTS.append((test_id, desc, bool(cond)))
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {test_id}: {desc}")
    return bool(cond)


# ── GAP-001 scenarios (against corrected impl) ───────────────────────────────

def gap001_corrected():
    print("\nGAP-001 — corrected impl (must PASS all):")

    # T-001-a: last step must NOT be reported complete
    r = build_state_corrected(make_plan(3, "primary"))
    check("T-001-a", "last step (3/3) not 'complete', has step 3 action",
          "step 3/3" in r["current"]
          and "S3-primary-action" in r["current"]
          and "complete" not in r["current"])

    # T-001-b: current_step=1 references step 1, not step 2
    r = build_state_corrected(make_plan(1, "primary"))
    check("T-001-b", "current_step=1 -> step 1 action (not step 2)",
          "S1-primary-action" in r["current"]
          and "S2-primary-action" not in r["current"]
          and "step 1/3" in r["current"])

    # T-001-b2: tier is respected
    r = build_state_corrected(make_plan(2, "alternate"))
    check("T-001-b2", "active_tier=alternate at step 2 -> step 2 alternate action",
          "S2-alternate-action" in r["current"] and "(alternate)" in r["current"])

    # T-001-c: out of range
    r = build_state_corrected(make_plan(99))
    check("T-001-c", "current_step=99 -> 'PACE plan complete (3 steps executed)'",
          r["current"] == "PACE plan complete (3 steps executed)")

    # T-001-d: no pace plan
    r = build_state_corrected(None)
    check("T-001-d", "no _pace_plan -> theory='' and current falls back",
          r["theory"] == "" and r["current"] == FALLBACK)

    # T-001-d2: step-number gap -> safe fallback, not wrong step, not crash
    gap_plan = make_plan(3)
    gap_plan["steps"] = [s for s in gap_plan["steps"] if s["step"] != 3]  # steps 1,2 only
    gap_plan["current_step"] = 3  # 3 <= len? len now 2, 3 > 2 -> "complete" branch
    r = build_state_corrected(gap_plan)
    check("T-001-d2", "missing current step, current_step>len -> 'complete' (no wrong step, no crash)",
          "complete" in r["current"] and "S" not in r["current"].split(":")[0])

    # T-001-e: theory is task_summary, not domain label
    r = build_state_corrected(make_plan(1, task_summary="Investigate homomorphic encryption libraries"))
    check("T-001-e", "theory == task_summary (not 'Domain: ...')",
          r["theory"] == "Investigate homomorphic encryption libraries"
          and "Domain:" not in r["theory"])

    # T-001-e2: theory respects MAX_THEORY_LEN (120)
    long_summary = "X" * 300
    r = build_state_corrected(make_plan(1, task_summary=long_summary))
    check("T-001-e2", "theory truncated to 120 chars", len(r["theory"]) == 120)


def gap001_buggy_must_fail():
    """Prove the regression tests actually catch the original bug."""
    print("\nGAP-001 — buggy impl (regression tests MUST fail against it):")

    # Against buggy: last step (3/3) -> '3 < 3' false -> wrongly 'complete'
    r = build_state_buggy(make_plan(3, "primary"))
    a_fails = not ("step 3/3" in r["current"] and "complete" not in r["current"])
    check("T-001-a/buggy", "buggy reports last step as 'complete' (test catches it)",
          a_fails and "complete" in r["current"])

    # Against buggy: current_step=1 -> steps[1] = step 2's action
    r = build_state_buggy(make_plan(1, "primary"))
    b_fails = "S2-primary-action" in r["current"]
    check("T-001-b/buggy", "buggy returns step 2's action for current_step=1 (test catches it)",
          b_fails)

    # Against buggy: theory is a domain label
    r = build_state_buggy(make_plan(1, task_summary="Investigate HE"))
    e_fails = "Domain:" in r["theory"] and r["theory"] != "Investigate HE"
    check("T-001-e/buggy", "buggy theory is a domain label, not task_summary (test catches it)",
          e_fails)


# ── GAP-005 scenarios ────────────────────────────────────────────────────────

def gap005():
    print("\nGAP-005 — tried[] TTL filter:")

    tried = [
        {"approach": "a1", "outcome": "x", "step": 1},   # age 11 -> drop
        {"approach": "a2", "outcome": "x", "step": 2},   # age 10 -> KEEP (== boundary)
        {"approach": "a5", "outcome": "x", "step": 5},   # age 7  -> keep
        {"approach": "a9", "outcome": "x", "step": 9},   # age 3  -> keep
    ]
    out = filter_tried_by_recency(tried, current_step=12, max_age=10)
    kept = {e["approach"] for e in out}
    check("T-005-a", "age>max_age dropped, age==max_age kept (exact boundary)",
          kept == {"a2", "a5", "a9"} and "a1" not in kept)

    # T-005-b: new PACE plan clears all regardless of age
    out = apply_pace_change(tried, new_task=True)
    check("T-005-b", "new PACE plan clears tried[] entirely", out == [])
    out = apply_pace_change(tried, new_task=False)
    check("T-005-b2", "no new task -> tried[] preserved", len(out) == 4)

    # T-005-d: legacy entry without 'step' -> treated as 0, ages out, no crash
    legacy = [{"approach": "old", "outcome": "x"},               # no step -> age=current_step
              {"approach": "new", "outcome": "x", "step": 20}]
    try:
        out = filter_tried_by_recency(legacy, current_step=21, max_age=10)
        kept = {e["approach"] for e in out}
        ok = kept == {"new"}  # 'old' age=21>10 dropped; 'new' age=1 kept
    except Exception as e:
        ok = False
        print(f"      (exception: {e})")
    check("T-005-d", "legacy entry w/o step -> aged out, no crash", ok)

    # T-005-a-neg: boundary off-by-one guard — keep age==max_age must hold
    one = [{"approach": "edge", "step": 0}]
    out = filter_tried_by_recency(one, current_step=10, max_age=10)
    check("T-005-a-neg", "age exactly == max_age is KEPT (inclusive contract)",
          len(out) == 1)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 64)
    print("Reasoning Persistence — Gap Closure Unit Harness")
    print("=" * 64)

    gap001_corrected()
    gap001_buggy_must_fail()
    gap005()

    total = len(RESULTS)
    passed = sum(1 for _, _, ok in RESULTS if ok)
    print("\n" + "=" * 64)
    print(f"RESULT: {passed}/{total} assertions held")
    failed = [(tid, d) for tid, d, ok in RESULTS if not ok]
    if failed:
        print("FAILURES:")
        for tid, d in failed:
            print(f"  - {tid}: {d}")
        print("=" * 64)
        return 1
    print("All assertions held: corrected impl passes; buggy impl fails the")
    print("regression tests (proving the tests can actually catch the bug).")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
