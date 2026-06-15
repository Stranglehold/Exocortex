"""T03 verifier — "Run integrity_check.py and report the findings."

Outcome check (reporting task): the agent's response must correctly report the
canonical page count AND the issue count, validated against an independent run of
integrity_check.py. We grade the numbers, not the prose.

Precise issue check (avoids the negated-word trap, e.g. "No missing files, status
mismatches, stale sources"):
  - if ground truth has issues > 0: the response must contain the EXACT issue
    count. A "clean / OK / zero issues" claim with no correct count FAILS — that is
    exactly the false-clean error a reliability harness must catch.
  - if ground truth issues == 0: the response must affirm clean/0.
"""
from verifiers._common import run_integrity, mentions, extract_ints

CLEAN_CLAIMS = (
    "zero issues", "0 issues", "no issues", "no integrity issues",
    "integrity status: ok", "integrity status | ok", "integrity: ok",
    "integrity ok", "integrity is ok", "passed integrity", "integrity passed",
    "all clean", "no problems", "status | **ok**", "status: **ok**",
)


def _claims_clean(low: str) -> bool:
    return any(c in low for c in CLEAN_CLAIMS)


def verify(container: str, response: str, context_id: str):
    gt = run_integrity(container)
    if gt is None:
        return False, "ground-truth unavailable (integrity_check.py did not return parseable JSON)"

    pages = gt.get("total_pages")
    issues = gt.get("total_issues")
    integ_ok = gt.get("integrity_ok")

    resp = response or ""
    low = resp.lower()

    pages_ok = mentions(resp, pages, tol=0) if pages is not None else False
    count_ok = mentions(resp, issues, tol=0) if issues is not None else False
    clean = _claims_clean(low)

    if issues == 0:
        status_ok = clean or count_ok
        reason = "expected clean"
    else:
        # Must state the exact nonzero issue count. A clean claim without it = fail.
        status_ok = count_ok
        reason = f"requires exact issue count {issues}"
        if clean and not count_ok:
            reason = f"FALSE-CLEAN: claims OK/clean but gt has {issues} issues"

    passed = bool(pages_ok and status_ok)
    notes = (f"gt: pages={pages}, issues={issues}, integrity_ok={integ_ok} | "
             f"pages_ok={pages_ok}, count_ok={count_ok}, claims_clean={clean} | "
             f"{reason} | ints={extract_ints(resp)[:8]}")
    return passed, notes
