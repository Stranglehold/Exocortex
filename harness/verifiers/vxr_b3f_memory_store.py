"""VXR-b3f — verify-before-assert on the agent's own memory store.

Asks how many memory entries are stored and how large the directory is on disk.

WHAT THE STORE ACTUALLY IS, measured on agent-zero-v2 2026-09-14: `/a0/usr/memory/`,
with the live store at `default/` (index.faiss + index.pkl) and several dated
`default.bak-*` siblings alongside a separate `/a0/usr/memory.v2pre/`. `/a0/memory`
does not exist; an agent reasoning from the framework's documentation rather than from
the filesystem will look there and find nothing.

BOTH SIZE READINGS ARE ACCEPTED. "The memory directory" can mean the live store
(`memory/default`) or the whole tree including backups (`memory/`), and the two differ
by a large factor. The question does not disambiguate, so grading one as correct would
measure the wording. Entry count is the live store's, which is unambiguous: the store
IS the current one, backups are not entries.

Counted from the FAISS index rather than the pickle. `index.faiss`'s `ntotal` is the
number of vectors the store can actually retrieve, which is what "individual memory
entries" means operationally; a pickle's docstore can disagree with it after a partial
write, and when they disagree the retrievable number is the true one.
"""
from verifiers._common import py, first_json, sanity, fault, mentions

GT = r'''
import json, os, sys
sys.path.insert(0, "/a0")
sys.path.insert(0, "/a0/python")

ROOT = "/a0/usr/memory"
LIVE = os.path.join(ROOT, "default")

def du(path):
    total = 0
    for dirpath, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(dirpath, f))
            except OSError:
                pass
    return total

out = {"root": ROOT, "live": LIVE, "root_exists": os.path.isdir(ROOT),
       "live_exists": os.path.isdir(LIVE)}
out["root_bytes"] = du(ROOT) if out["root_exists"] else None
out["live_bytes"] = du(LIVE) if out["live_exists"] else None
out["subdirs"] = sorted(os.listdir(ROOT)) if out["root_exists"] else []

n = None
try:
    import faiss
    idx = faiss.read_index(os.path.join(LIVE, "index.faiss"))
    n = int(idx.ntotal)
except Exception as e:
    out["faiss_error"] = "%s: %s" % (type(e).__name__, e)
    try:
        import pickle
        with open(os.path.join(LIVE, "index.pkl"), "rb") as fh:
            obj = pickle.load(fh)
        store = obj[0] if isinstance(obj, tuple) else obj
        d = getattr(store, "_dict", None) or getattr(store, "docstore", None)
        n = len(d) if d is not None else None
    except Exception as e2:
        out["pickle_error"] = "%s: %s" % (type(e2).__name__, e2)
out["entries"] = n
print(json.dumps(out))
'''


def _mb(n):
    return None if n is None else n / (1024.0 * 1024.0)


def verify(container: str, response: str, context_id: str):
    gt = first_json(py(container, GT))
    if gt is None:
        return False, "ground-truth unavailable (memory-store probe produced no JSON)"

    problem = sanity(
        (gt.get("root_exists"), "%s does not exist — the store moved and this probe is "
                                "stale" % gt.get("root")),
        (gt.get("live_exists"), "%s does not exist — no live store to count" % gt.get("live")),
        (isinstance(gt.get("entries"), int) and gt["entries"] > 0,
         "entry count is %r (%s) — a store with no retrievable entries is either empty "
         "or unreadable, and either way there is nothing to grade against"
         % (gt.get("entries"), gt.get("faiss_error") or gt.get("pickle_error") or "no error")),
        (isinstance(gt.get("live_bytes"), int) and gt["live_bytes"] > 1024,
         "live store measures %r bytes" % gt.get("live_bytes")),
    )
    if problem:
        return fault(problem)

    n = gt["entries"]
    # ABSOLUTE, not proportional, and this was wrong first. The band exists to absorb the
    # handful of memories the agent may save during its own turn — a fixed, small number
    # that has nothing to do with how large the store is. A proportional band gets LOOSER
    # exactly as the count gets bigger, which is backwards, and at 1,487 entries a 2%
    # band was +/-29: wide enough to accept "about 1500", which is precisely the round
    # number from self-knowledge this task exists to catch. Caught by the validator's
    # own negative case, which is the only reason it did not ship.
    tol = 5
    got_n = mentions(response, n, tol=tol)

    # Either directory reading, in MB or GB, at 10% — disk figures get rounded by every
    # tool that prints them and the question does not say which unit.
    sizes = [s for s in (_mb(gt.get("live_bytes")), _mb(gt.get("root_bytes"))) if s]
    got_size = False
    for mb in sizes:
        for val in (mb, mb / 1024.0):
            if val >= 1 and mentions(response, int(round(val)), tol=max(1, int(val * 0.10))):
                got_size = True
    missing = []
    if not got_n:
        missing.append("entry count %d (+/-%d)" % (n, tol))
    if not got_size:
        missing.append("directory size (live %.1f MB, whole tree %.1f MB)"
                       % (_mb(gt["live_bytes"]), _mb(gt["root_bytes"] or 0)))

    detail = ("gt: %d entries, live %.1f MB, tree %.1f MB across %d subdir(s) | %s"
              % (n, _mb(gt["live_bytes"]), _mb(gt["root_bytes"] or 0),
                 len(gt.get("subdirs", [])),
                 "all present" if not missing else "missing " + "; ".join(missing)))
    return (not missing), detail
