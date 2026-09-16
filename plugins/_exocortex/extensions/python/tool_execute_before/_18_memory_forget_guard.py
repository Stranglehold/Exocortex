"""
memory_forget guard (tool_execute_before, _18_)
================================================
Refuses a memory_forget call that would delete more of the store than a bounded cleanup can mean.

Why (2026-09-14/15): Aporia's memory store was emptied twice in one day by her own memory_forget calls, 1,710 of
1,713 at 04:21 UTC and 1,717 of 1,718 at 18:17 UTC (MAINTAIN cycle 573, query "confirmed via sleep_findings.json
output consolidation zero-finding state", meant for about three entries). The tool hands the query to
delete_documents_by_query with the default 0.7 threshold, include_exact=True and cascade=True, deletes a page of a
hundred at a time until a page comes back short, then deletes everything related to what it removed, and reports the
number only after it has done it. She noticed both times ("Deleting 1717 memories is concerning") and could not stop it.
Ruling (Opus under delegation, 2026-09-15 04:1x UTC): hard cap max(10, 5 % of the store); refuse, return the count,
log the query; no override argument. The agent narrows the query or decides not to.

How: before the tool runs, walk the same selection the tool would (threshold matches with the tool's own threshold
and filter, exact-text matches, then the cascade of documents whose metadata references any of those ids) WITHOUT
deleting, count it against the cap, and raise RepairableException with the count when it is over. A0 turns that into
the tool's error response, so she reads "would delete N of M, refused" instead of "memories_deleted: 1717".

Fails closed: if the dry run cannot run (memory plugin API moved, store unreadable), the call is refused with the
reason, because a guard that fails open is the hole it was built to close. A legitimate one-to-three-entry forget
that hits the closed guard costs one refused call and one log line; a wipe costs the store.

Logs one line either way: [FORGET-GUARD] allowed|refused ... so docker logs carry the count and the query.
"""
import math

from helpers.extension import Extension
from helpers.errors import RepairableException

CAP_FLOOR = 10          # never below this many on a store that can afford it, so cleanup stays possible
CAP_FRACTION = 0.05     # never above this share of the store
SAMPLE = 8              # matched entries quoted in the refusal, so she can see WHY the query is wide
TOOL = "memory_forget"


def cap_for(store_size: int) -> int:
    """Opus's ruling max(10, 5 %) bounded by half the store (Kestrel's note, 2026-09-15): on a store that has
    already been emptied the floor of 10 would be most of what is left, and that store is the one to protect.
    1,718 → 86; 200 → 10; 17 → 8; 3 → 1; 0 → 0."""
    n = max(0, int(store_size))
    ruled = max(CAP_FLOOR, int(math.ceil(CAP_FRACTION * n)))
    return min(ruled, n // 2)


def _snippet(doc, width: int = 90) -> str:
    text = " ".join(str(getattr(doc, "page_content", "") or "").split())
    return text[:width] + ("…" if len(text) > width else "")


def parse_threshold(value, default: float) -> float:
    try:
        t = float(value)
    except (TypeError, ValueError):
        return default
    if not (0.0 <= t <= 1.0):
        return default
    return t


async def dry_run(db, query: str, threshold: float, filter: str) -> dict:
    """Count what memory_forget would delete, the way delete_documents_by_query selects it, deleting nothing.
    Returns {"store": M, "threshold": a, "exact": b, "cascade": c, "total": n}. Raises on any API mismatch."""
    all_docs = db.db.get_all_docs()
    store = len(all_docs)
    ids: set[str] = set()
    hits = await db.search_similarity_threshold(query, limit=max(store, 1), threshold=threshold, filter=filter)
    for d in hits:
        ids.add(str(d.metadata["id"]))
    n_threshold = len(ids)
    exact = db._find_exact_query_docs(query, filter, ids)      # the tool passes include_exact=True
    for d in exact or []:
        ids.add(str(d.metadata["id"]))
    n_exact = len(ids) - n_threshold
    related = db._find_related_docs_by_ids(ids, filter) if ids else []   # the tool passes cascade=True
    n_cascade = len({str(d.metadata["id"]) for d in related or []} - ids)
    sample = [_snippet(d) for d in list(hits)[:SAMPLE]]
    if len(sample) < SAMPLE:
        sample += [_snippet(d) for d in list(exact or [])[:SAMPLE - len(sample)]]
    if len(sample) < SAMPLE:
        sample += [_snippet(d) for d in list(related or [])[:SAMPLE - len(sample)]]
    return {"store": store, "threshold": n_threshold, "exact": n_exact, "cascade": n_cascade,
            "total": n_threshold + n_exact + n_cascade, "sample": sample}


class MemoryForgetGuard(Extension):

    async def execute(self, tool_name: str = "", tool_args: dict | None = None, **kwargs) -> None:
        if tool_name != TOOL:
            return
        args = tool_args or {}
        query = str(args.get("query") or "")
        filter_ = str(args.get("filter") or "")
        try:
            from plugins._memory.helpers.memory import Memory
            from plugins._memory.tools.memory_load import DEFAULT_THRESHOLD
            threshold = parse_threshold(args.get("threshold"), DEFAULT_THRESHOLD)
            db = await Memory.get(self.agent)
            counts = await dry_run(db, query, threshold, filter_)
        except Exception as e:  # fail closed
            msg = (f"memory_forget refused: the deletion guard could not measure what this call would delete "
                   f"({type(e).__name__}: {e}). Nothing was deleted. Report this; do not retry the same call.")
            print(f"[FORGET-GUARD] refused (dry run failed: {type(e).__name__}: {e}) query={query[:160]!r}", flush=True)
            raise RepairableException(msg)
        cap = cap_for(counts["store"])
        if counts["total"] > cap:
            print(f"[FORGET-GUARD] refused: would delete {counts['total']} of {counts['store']} "
                  f"(threshold {counts['threshold']}, exact {counts['exact']}, cascade {counts['cascade']}; cap {cap}; "
                  f"similarity {threshold}) query={query[:160]!r} filter={filter_[:80]!r}", flush=True)
            shown = "\n".join(f"  - {s}" for s in counts["sample"]) or "  (no text available)"
            raise RepairableException(
                f"memory_forget refused: this query would delete {counts['total']} of {counts['store']} memories "
                f"(cap {cap}: {counts['threshold']} by similarity at {threshold}, {counts['exact']} exact, "
                f"{counts['cascade']} by cascade). Nothing was deleted. The first {len(counts['sample'])} it would "
                f"have taken:\n{shown}\nmemory_forget is for one to a few specific entries: narrow the query to the "
                f"exact wording of the entries you mean, raise the threshold, or add a filter; never use it for "
                f"broad cleanup."
            )
        print(f"[FORGET-GUARD] allowed: would delete {counts['total']} of {counts['store']} (cap {cap}) "
              f"query={query[:160]!r}", flush=True)
