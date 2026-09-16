"""VXR-d48 — tool discovery for filesystem capacity.

Asks for total, used and available space per mounted filesystem. No tool is named; the
agent has to reach for df or an equivalent on its own.

GRADED ON THE STABLE THING. Measured on agent-zero-v2 2026-09-14, the overlay root is
~1,055,762,868 1K-blocks with ~287 GB used — and `used` moves continuously while the
container runs, so an exact used-space assertion is a coin flip, not a test. Mount
points and total capacity do not move. That is hb04's lesson applied here: grade names
and capacities, which are stable, and let usage in with a band wide enough to survive
the seconds between the agent's answer and this check.

The bands are deliberately asymmetric. Capacity: 2%, because it should be read, not
estimated. Used and available: 5%, because they genuinely drift. A round guess ("about
a terabyte, half full") clears neither.

Tiny pseudo-filesystems — /dev, /proc/acpi, the 4KB tmpfs entries — are excluded from
the required set. They are real mounts and naming them is not wrong, but requiring them
would grade verbosity rather than discovery: an agent that reports the real storage and
omits a 4KB tmpfs has answered the question.
"""
from verifiers._common import py, first_json, sanity, fault, mentions

GT = r'''
import json, os, subprocess
r = subprocess.run(["df", "-P"], capture_output=True, text=True, timeout=40)
rows = []
for ln in (r.stdout or "").splitlines()[1:]:
    p = ln.split(None, 5)
    if len(p) < 6:
        continue
    try:
        rows.append({"fs": p[0], "total_k": int(p[1]), "used_k": int(p[2]),
                     "avail_k": int(p[3]), "mount": p[5].strip()})
    except ValueError:
        continue
print(json.dumps({"rows": rows, "raw_lines": len((r.stdout or "").splitlines())}))
'''

# Below this, a filesystem is a kernel pseudo-mount rather than storage anyone means.
SIGNIFICANT_K = 1024 * 1024        # 1 GiB


def verify(container: str, response: str, context_id: str):
    gt = first_json(py(container, GT))
    if gt is None:
        return False, "ground-truth unavailable (df produced no JSON)"

    rows = gt.get("rows") or []
    problem = sanity(
        (len(rows) >= 2, "df returned %d filesystem(s) — a container has several" % len(rows)),
        (any(r["mount"] == "/" for r in rows), "no root filesystem in df output"),
        (any(r["total_k"] > SIGNIFICANT_K for r in rows),
         "no filesystem larger than 1 GiB — df output is not what this probe expects"),
    )
    if problem:
        return fault(problem)

    big = [r for r in rows if r["total_k"] >= SIGNIFICANT_K]
    resp = response or ""
    missing = []

    for r in big:
        # Capacity and availability in whichever unit the agent chose. df's own -h
        # rounds, so each value is checked in K, M, G and T.
        def seen(k, tol_frac):
            for div in (1, 1024, 1024 ** 2, 1024 ** 3):
                v = k / float(div)
                if v >= 1 and mentions(resp, int(round(v)), tol=max(1, int(v * tol_frac))):
                    return True
            return False

        if not seen(r["total_k"], 0.02):
            missing.append("%s total" % r["mount"])
        if not (seen(r["used_k"], 0.05) or seen(r["avail_k"], 0.05)):
            missing.append("%s used/available" % r["mount"])

    # Did it find a tool at all, or answer from nowhere? A response naming no filesystem
    # and no mount point has not inspected anything.
    named_mount = any(r["mount"] in resp or r["fs"] in resp for r in big)
    if not named_mount:
        missing.append("no mount point or device named at all")

    detail = ("gt: %d filesystem(s), %d over 1 GiB: %s | %s"
              % (len(rows), len(big),
                 ", ".join("%s %.0fG" % (r["mount"], r["total_k"] / 1048576.0) for r in big[:4]),
                 "all present" if not missing else "missing " + ", ".join(missing)))
    return (not missing), detail
