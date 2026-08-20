"""HB-04 - tool discovery, generalises from the T03 implicit/explicit gap.

"What processes are running inside the container?"

No tool named. The agent must reach for ps / /proc itself. Graded on whether it names
the processes that are genuinely there, not on the count alone - process counts drift
between the ground-truth call and the agent's, so an exact number would be a flaky
assertion. Names are stable; counts are not. Grading the stable thing is the difference
between a test and a coin flip.
"""
from verifiers._common import sh, py, first_json

GT = r'''
import json, os
names = []
for pid in os.listdir("/proc"):
    if not pid.isdigit():
        continue
    try:
        names.append(open(f"/proc/{pid}/comm").read().strip())
    except Exception:
        pass
uniq = sorted(set(n for n in names if n))
print(json.dumps({"count": len(names), "names": uniq}))
'''

# Long-lived processes that must be running for the container to function at all.
ANCHORS = ("python", "run_ui", "supervisord", "sh", "node")


def verify(container: str, response: str, context_id: str):
    gt = first_json(py(container, GT))
    if gt is None:
        return False, "ground-truth unavailable (/proc scan produced no JSON)"

    names = [n.lower() for n in gt["names"]]
    low = (response or "").lower()
    present = [a for a in ANCHORS if any(a in n for n in names)]
    named = [a for a in present if a in low]

    # Must name at least half the anchors actually running, and at least two.
    need = max(2, (len(present) + 1) // 2)
    passed = len(named) >= need
    return bool(passed), (f"gt: {gt['count']} procs, anchors present={present} | "
                          f"response named={named} (needed {need})")
