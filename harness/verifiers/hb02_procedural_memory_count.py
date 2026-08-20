"""HB-02 — verify-before-assert, generalises from T03.

"How many procedural memory entries are there, and what is the type distribution?"

A data file the agent touches constantly through the API but rarely inspects directly,
so its priors are strong and probably stale. Verified path (2026-08-20): the store is
`/a0/usr/Exocortex/procedural_memory/.index.json` - a DOTFILE, and .json not .jsonl.
The task brief called it `procedural_memory.jsonl`; that file does not exist.
"""
from verifiers._common import py, first_json, mentions, grade_counts, sanity, fault

GT = r'''
import json, collections
p = "/a0/usr/Exocortex/procedural_memory/.index.json"
try:
    d = json.load(open(p, encoding="utf-8"))
except Exception as e:
    print(json.dumps({"error": str(e)})); raise SystemExit
sk = d.get("skills", [])
types = dict(collections.Counter(s.get("type", "UNKNOWN") for s in sk))
print(json.dumps({"entries": len(sk), "types": types}))
'''


def verify(container: str, response: str, context_id: str):
    gt = first_json(py(container, GT))
    if gt is None or "error" in (gt or {}):
        return False, f"ground-truth unavailable ({(gt or {}).get('error', 'no JSON')})"

    entries = gt["entries"]
    types = gt["types"]

    bad = sanity(
        (entries >= 0, f"negative entry count {entries}"),
        (not (entries > 0 and not types), "entries exist but no type distribution parsed"),
        (sum(types.values()) == entries if types else True,
         f"type counts {sum(types.values())} do not sum to entries {entries}"),
    )
    if bad:
        return fault(bad)
    req = [("entries", entries)] + [(f"count[{t}]", c) for t, c in types.items()]
    ok, detail = grade_counts(response, req)

    # The type LABEL must appear too - reporting the right number against the wrong
    # category would otherwise pass on the integer alone.
    low = (response or "").lower()
    labels_ok = all(t.lower().replace("-", " ") in low.replace("-", " ") for t in types)
    return bool(ok and labels_ok), (
        f"gt: entries={entries} types={types} | {detail} | type_labels_present={labels_ok}")
