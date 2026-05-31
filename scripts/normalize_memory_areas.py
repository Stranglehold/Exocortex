#!/usr/bin/env python3
"""
Memory-area normalizer — collapse ~115 fragmented save-areas into a small standard set.

WHY: recall is now area-agnostic for general knowledge (see _56/_55: `area != 'solutions'`),
so orphaned memories are reachable again. But the agent invents a new area per memory
(research-field-report-semiconductor-supply-chain, osint-email-investigation, ...), which
keeps fragmenting the area vocabulary. This maps every non-system area into Opus's standard
cognitive-function set so the vocabulary stays small and future area-based logic stays clean.

PRESERVES A0 SYSTEM AREAS (main/fragments/ontology/solutions/instruments) — they have
framework meaning (fragments=conversation, ontology=entity graph, solutions=own recall path).
Only the agent's ad-hoc semantic areas are remapped.

Defense-in-depth, same shape as the skill normalizer: dry-run by default, idempotent (already-
standard areas unchanged), modifies ONLY the `area` metadata field (never page_content or
vectors), validated counts before/after. Importable normalize_memory_areas(apply) for the
MAINTAIN integrity sweep.

USAGE:
  python3 normalize_memory_areas.py                 # dry-run: show the 115 -> N mapping
  python3 normalize_memory_areas.py --apply         # rewrite area metadata + re-pickle docstore
"""
import os
import pickle
import re
import sys

APPLY = "--apply" in sys.argv
_args = [a for a in sys.argv[1:] if not a.startswith("--")]
STORE = _args[0] if _args else "/a0/usr/memory/default/index.pkl"

# A0 framework areas — never remap (they carry framework semantics + their own recall paths)
SYSTEM_AREAS = {"main", "fragments", "ontology", "solutions", "instruments"}
# Opus's standard cognitive-function set
STANDARD = {"knowledge", "research", "procedural", "episodic", "self", "system", "social"}

# keyword -> standard area (first match wins; ordered most-specific first)
_ROUTES = [
    ("research",   ["research", "field", "explore", "osint", "investigation", "paper",
                    "finding", "geopolit", "markets", "entity-resolution", "domain-invest"]),
    ("self",       ["self-improvement", "self", "identity", "behavior", "assessment",
                    "reflection", "anti-pattern"]),
    ("episodic",   ["workshop", "cycle", "session", "episodic", "idle", "log", "timeline",
                    "event", "progress"]),
    ("procedural", ["procedure", "method", "workflow", "how-to", "recipe", "build-plan"]),
    ("system",     ["exocortex", "system", "config", "architecture", "component",
                    "operational", "wiki", "build", "maintain", "deploy", "infra"]),
    ("social",     ["team", "social", "communication", "user", "conversation", "relationship"]),
    ("knowledge",  ["concept", "knowledge", "cross-domain", "insight", "hardware", "privacy",
                    "crypto", "ai-agent", "zkp"]),
]


def map_area(area: str) -> str:
    a = (area or "main").strip().lower()
    if a in SYSTEM_AREAS:
        return area            # preserve framework areas verbatim
    if a in STANDARD:
        return a
    for target, keys in _ROUTES:
        if any(k in a for k in keys):
            return target
    return "knowledge"          # default: domain understanding


def _find_docstore(obj):
    for attr in ("_dict", "docstore", "__dict__"):
        d = getattr(obj, attr, None)
        if isinstance(d, dict) and d:
            return d, obj
    if isinstance(obj, (tuple, list)):
        for x in obj:
            d = (getattr(x, "_dict", None)
                 or getattr(getattr(x, "docstore", None), "_dict", None))
            if isinstance(d, dict) and d:
                return d, obj
    return None, obj


def normalize_memory_areas(store: str = "/a0/usr/memory/default/index.pkl",
                           apply: bool = False) -> dict:
    if not os.path.exists(store):
        return {"error": "no store", "remapped": 0, "by_target": {}}
    with open(store, "rb") as f:
        obj = pickle.load(f)
    docs, root = _find_docstore(obj)
    if docs is None:
        return {"error": "no docstore", "remapped": 0, "by_target": {}}

    remapped = 0
    by_target: dict = {}
    distinct_before = set()
    samples = []
    for v in docs.values():
        md = getattr(v, "metadata", None)
        if not isinstance(md, dict):
            continue
        cur = md.get("area", "main")
        distinct_before.add(cur)
        new = map_area(cur)
        if new != cur:
            by_target[new] = by_target.get(new, 0) + 1
            if len(samples) < 6:
                samples.append((cur, new))
            if apply:
                md["area"] = new
            remapped += 1

    if apply and remapped:
        # REFUSED by design. The store is held in run_ui's class-level RAM cache
        # (Memory.index) with a hash-verified FAISS index — a direct pickle write from a
        # separate process is overwritten on the next _save_db() and can trip an index
        # rebuild. #3 (the actual remapper) MUST be an in-process monologue_end extension
        # that mutates the in-RAM docstore via the Memory API and calls _save_db(). This
        # file is the mapping reference + read-only dry-run analysis ONLY.
        print("[REFUSED] --apply disabled: memory mutation must be in-process (see header). "
              "Reporting the dry-run mapping instead; no store was modified.", flush=True)
        return {
            "remapped": remapped, "distinct_areas_before": len(distinct_before),
            "by_target": by_target, "samples": samples, "applied": False, "refused": True,
        }

    return {
        "remapped": remapped,
        "distinct_areas_before": len(distinct_before),
        "by_target": by_target,
        "samples": samples,
        "applied": apply,
    }


def main():
    rep = normalize_memory_areas(STORE, apply=APPLY)
    print(f"=== normalize_memory_areas ({'APPLY' if APPLY else 'DRY-RUN'}) ===")
    print(f"distinct areas before: {rep.get('distinct_areas_before')}")
    print(f"would remap / remapped: {rep['remapped']}  -> standard set")
    print(f"by target area: {dict(sorted(rep.get('by_target', {}).items(), key=lambda x: -x[1]))}")
    print("sample mappings (custom -> standard):")
    for cur, new in rep.get("samples", []):
        print(f"   {cur}  ->  {new}")


if __name__ == "__main__":
    main()
