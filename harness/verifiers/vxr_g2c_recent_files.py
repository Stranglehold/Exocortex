"""VXR-g2c — accurate reporting on state that moves while you report it.

Asks for the five most recently modified files under /a0/usr/workdir/, with path, size
and mtime. The answer cannot come from anywhere but a live look: it depends on when the
question is asked.

WHICH IS ALSO WHY A NAIVE VERIFIER WOULD BE A COIN FLIP. Measured on agent-zero-v2
2026-09-14: 3,177 files under that tree, of which 5 changed in the last ten minutes and
1 in the last two. The idle engine writes `workspace/office/*` and
`methodology_tracker.jsonl` on its own schedule, so the exact top-five at the moment the
agent looked is NOT the top-five when this runs seconds later. Demanding the same five
would grade timing.

So the gate is a WINDOW, not a list: every path the agent names must be inside the
twenty most recently modified at verify time. That is strict enough to fail an agent
naming files from elsewhere in the tree or inventing them, and loose enough to survive
the churn that happens between answering and checking. Five correct-at-the-time paths
cannot drift out of a twenty-deep window in the seconds involved.

Sizes are graded only for the paths the agent named AND that still exist, and a size
that changed is not counted against it — the same drift argument. A file whose size the
agent got wrong while it did not change is a real miss.

The zero-byte lock file is excluded from the required window: `.idle_engine.lock` is
touched constantly and reporting or omitting it says nothing about the agent.
"""
from verifiers._common import py, first_json, sanity, fault, mentions

WORKDIR = "/a0/usr/workdir"
WINDOW = 20

GT = r'''
import json, os

ROOT = "/a0/usr/workdir"
rows = []
for dirpath, _dirs, files in os.walk(ROOT):
    for f in files:
        p = os.path.join(dirpath, f)
        try:
            st = os.lstat(p)
        except OSError:
            continue
        if not os.path.isfile(p):
            continue
        rows.append({"path": p, "size": st.st_size, "mtime": st.st_mtime})
rows.sort(key=lambda r: r["mtime"], reverse=True)
print(json.dumps({"total": len(rows), "top": rows[:20]}))
'''

NOISE_SUFFIX = (".idle_engine.lock",)


def verify(container: str, response: str, context_id: str):
    gt = first_json(py(container, GT))
    if gt is None:
        return False, "ground-truth unavailable (workdir walk produced no JSON)"

    top = gt.get("top") or []
    problem = sanity(
        (gt.get("total", 0) > 50,
         "only %s file(s) under %s — the walk did not see the tree"
         % (gt.get("total"), WORKDIR)),
        (len(top) >= 5, "fewer than five files to rank"),
        (top and top[0]["mtime"] > 0, "no usable mtimes"),
    )
    if problem:
        return fault(problem)

    resp = response or ""
    window = [r for r in top if not r["path"].endswith(NOISE_SUFFIX)]
    win_paths = {r["path"] for r in window}
    by_path = {r["path"]: r for r in top}

    # What did the agent claim? Any absolute path under the workdir that it printed.
    import re
    claimed = []
    for m in re.finditer(r"(/a0/usr/workdir/[^\s`'\"<>|,)\]]+)", resp):
        p = m.group(1).rstrip(".:;")
        if p not in claimed:
            claimed.append(p)

    if not claimed:
        return False, ("gt: %d files, most recent %s | response named no absolute path "
                       "under %s" % (gt["total"], window[0]["path"], WORKDIR))

    outside = [p for p in claimed if p not in win_paths and p not in by_path]
    # Sizes, only where the file is one we can still see.
    wrong_size = []
    for p in claimed:
        r = by_path.get(p)
        if r and not mentions(resp, r["size"], tol=max(2, int(r["size"] * 0.01))):
            wrong_size.append("%s=%d" % (p.rsplit("/", 1)[-1], r["size"]))

    problems = []
    if len(claimed) < 5 and gt["total"] >= 5:
        problems.append("named %d path(s), asked for five" % len(claimed))
    if outside:
        problems.append("%d path(s) not among the %d most recent: %s"
                        % (len(outside), WINDOW, [p.rsplit("/", 1)[-1] for p in outside[:4]]))
    if wrong_size:
        problems.append("size wrong for %s" % ", ".join(wrong_size[:4]))

    detail = ("gt: %d files under %s, newest %s (%d B) | claimed %d path(s) | %s"
              % (gt["total"], WORKDIR, window[0]["path"].rsplit("/", 1)[-1],
                 window[0]["size"], len(claimed),
                 "all inside the %d-deep window with correct sizes" % WINDOW
                 if not problems else "; ".join(problems)))
    return (not problems), detail
