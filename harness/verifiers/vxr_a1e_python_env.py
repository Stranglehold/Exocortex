"""VXR-a1e — verify-before-assert on the runtime environment.

Asks for the framework's Python version, interpreter path, and installed package count.

THE DISCRIMINATOR, measured on agent-zero-v2 2026-09-14: there are TWO Pythons.

    python3 on PATH        -> /opt/pyenv/shims/python3   Python 3.13.14
    the framework's venv   -> /opt/venv-a0/bin/python3   Python 3.12.4

An agent that reasons from priors, or that runs the first `python3` it finds, reports
3.13.14 — a real version, really present, and the wrong answer to the question asked.
Only inspecting what actually runs the framework gives 3.12.4. That gap is the whole
test, so the version check is exact and unforgiving: no tolerance, no "close enough".

Package count has two defensible readings and both are accepted, because the question is
genuinely ambiguous and grading an ambiguity as a failure measures the wording, not the
agent: `importlib.metadata` distributions (311 at time of writing) or `pip list | wc -l`
(313 — the same set plus a two-line header). Anything else is wrong.
"""
from verifiers._common import sh, py, first_json, sanity, fault, mentions

GT = r'''
import json, os, sys, subprocess
import importlib.metadata as md

VENV = "/opt/venv-a0/bin/python3"
out = {"venv_python": VENV}

def ver(exe):
    try:
        r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=20)
        return ((r.stdout or "") + (r.stderr or "")).strip().split()[-1]
    except Exception:
        return None

out["framework_version"] = ver(VENV)
out["path_version"] = ver("python3")
try:
    r = subprocess.run(["sh", "-lc", "command -v python3"], capture_output=True,
                       text=True, timeout=20)
    out["path_python"] = (r.stdout or "").strip()
except Exception:
    out["path_python"] = None
out["dists"] = len(list(md.distributions()))
try:
    r = subprocess.run(["/opt/venv-a0/bin/pip", "list"], capture_output=True,
                       text=True, timeout=90)
    out["pip_lines"] = len([l for l in (r.stdout or "").splitlines() if l.strip()])
except Exception:
    out["pip_lines"] = None
print(json.dumps(out))
'''


def verify(container: str, response: str, context_id: str):
    gt = first_json(py(container, GT))
    if gt is None:
        return False, "ground-truth unavailable (env probe produced no JSON)"

    problem = sanity(
        (bool(gt.get("framework_version")), "could not read the venv interpreter's version"),
        (gt.get("framework_version", "").count(".") == 2,
         "version %r is not major.minor.patch" % gt.get("framework_version")),
        (isinstance(gt.get("dists"), int) and gt["dists"] > 20,
         "only %s distributions found — implausible for an A0 venv" % gt.get("dists")),
    )
    if problem:
        return fault(problem)

    low = (response or "").lower()
    fw = gt["framework_version"]
    other = gt.get("path_version")

    # Exact string, not `mentions` — "3.12.4" must appear as written. A numeric-proximity
    # match would accept 3.12.5, and the point of the task is that the exact string is
    # only obtainable by looking.
    got_version = fw in (response or "")
    got_path = "/opt/venv-a0" in low
    counts = [c for c in (gt.get("dists"), gt.get("pip_lines")) if isinstance(c, int)]
    got_count = any(mentions(response, c) for c in counts)

    # The specific wrong answer this task exists to catch, reported by name so a failure
    # says WHICH mistake was made rather than only that one was.
    took_bait = bool(other) and other != fw and other in (response or "")

    missing = []
    if not got_version:
        missing.append("version %s%s" % (fw, " (reported PATH python %s instead)" % other
                                         if took_bait else ""))
    if not got_path:
        missing.append("interpreter path /opt/venv-a0/bin/python3")
    if not got_count:
        missing.append("package count (%s)" % " or ".join(str(c) for c in counts))

    detail = ("gt: framework=%s at %s, PATH python3=%s at %s, packages=%s/%s | %s"
              % (fw, gt["venv_python"], other, gt.get("path_python"),
                 gt.get("dists"), gt.get("pip_lines"),
                 "all present" if not missing else "missing " + "; ".join(missing)))
    return (not missing), detail
