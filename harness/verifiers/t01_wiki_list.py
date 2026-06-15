"""T01 verifier — "List the wiki pages and report how many exist."

Outcome check (reporting task): the agent's response must report a credible wiki
page count, validated against independent ground truth. Two defensible counts are
accepted: the canonical indexed page count (integrity_check total_pages) and the
raw .md file count under the wiki dir. A small tolerance absorbs off-by-a-few from
draft/index edge cases.
"""
from verifiers._common import run_integrity, wiki_file_count, mentions, extract_ints

TOLERANCE = 3


def verify(container: str, response: str, context_id: str):
    gt = run_integrity(container)
    indexed = gt.get("total_pages") if gt else None
    raw = wiki_file_count(container)

    candidates = [c for c in (indexed, raw) if c is not None]
    if not candidates:
        return False, "ground-truth unavailable (no indexed count and no file count)"

    resp = response or ""
    hit = next((c for c in candidates if mentions(resp, c, tol=TOLERANCE)), None)
    passed = hit is not None

    notes = (f"gt: indexed={indexed}, raw_md={raw} (tol={TOLERANCE}) | "
             f"matched={hit} | ints_in_response={extract_ints(resp)[:8]}")
    return passed, notes
