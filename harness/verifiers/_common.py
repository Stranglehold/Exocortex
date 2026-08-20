"""Shared verifier helpers — independent ground truth from the container.

Verifiers check OUTCOMES against ground truth computed independently of the agent.
For the reporting-type starter tasks (T01/T03), ground truth is the canonical
wiki page/issue counts, obtained by running integrity_check.py ourselves.
"""
import json
import re
import os as _os
import subprocess

INTEGRITY_CMD = ("cd /a0/usr/Exocortex/self-improvement && "
                 "/opt/venv-a0/bin/python3 integrity_check.py")
WIKI_DIR = "/a0/usr/workdir/workspace/wiki"


def run_integrity(container: str) -> dict | None:
    """Run integrity_check.py in the container; return its top-level JSON dict.

    stdout is a human-readable preamble followed by a JSON object; parse from the
    first brace. Returns None on failure.
    """
    try:
        out = subprocess.run(
            ["docker", "exec", container, "sh", "-lc", INTEGRITY_CMD],
            capture_output=True, text=True, timeout=120)
    except Exception:
        return None
    raw = out.stdout or ""
    brace = raw.find("{")
    if brace < 0:
        return None
    try:
        return json.loads(raw[brace:])
    except json.JSONDecodeError:
        # tolerate trailing noise: trim to the last closing brace
        end = raw.rfind("}")
        if end > brace:
            try:
                return json.loads(raw[brace:end + 1])
            except json.JSONDecodeError:
                return None
    return None


def wiki_file_count(container: str) -> int | None:
    """Raw count of .md files under the wiki dir (an alternate 'page count')."""
    try:
        out = subprocess.run(
            ["docker", "exec", container, "sh", "-lc",
             f"find {WIKI_DIR} -name '*.md' 2>/dev/null | wc -l"],
            capture_output=True, text=True, timeout=30)
        return int(out.stdout.strip().split()[0])
    except Exception:
        return None


def extract_ints(text: str) -> list[int]:
    """All integers in the text (commas stripped), as a list."""
    return [int(m.replace(",", "")) for m in re.findall(r"\d[\d,]*", text or "")]


def mentions(text: str, value: int, tol: int = 0) -> bool:
    """True if some integer within +/-tol of `value` appears in text."""
    return any(abs(i - value) <= tol for i in extract_ints(text))


# ── Pool B (holdout) ground truth ────────────────────────────────────────────
# Every function below computes the answer INDEPENDENTLY inside the container, so a
# verifier never grades the agent against the agent's own claim. Same discipline as
# run_integrity(): we compute the truth, then check whether the response matches it.
#
# MSYS_NO_PATHCONV is set explicitly. On this host Git Bash rewrites container-absolute
# paths in docker arguments, and a mangled path yields an empty result that looks
# exactly like a legitimately empty answer.

_ENV = dict(_os.environ, MSYS_NO_PATHCONV="1")


def sh(container: str, cmd: str, timeout: int = 60) -> str:
    """Run a shell command in the container, return stdout ('' on any failure)."""
    try:
        out = subprocess.run(["docker", "exec", container, "sh", "-lc", cmd],
                             capture_output=True, text=True, timeout=timeout, env=_ENV)
        return out.stdout or ""
    except Exception:
        return ""


def py(container: str, code: str, timeout: int = 90) -> str:
    """Run python in the container via a temp file.

    Deliberately not `python3 -c`: inline code through docker exec on this host hits
    the quoting seam that silently produces no output and no error (wiring seam #30).
    """
    import base64 as _b64
    b = _b64.b64encode(code.encode("utf-8")).decode("ascii")
    return sh(container,
              f"echo {b} | base64 -d > /tmp/_gt.py && /opt/venv-a0/bin/python3 /tmp/_gt.py; "
              f"rm -f /tmp/_gt.py", timeout=timeout)


def first_json(text: str):
    """Parse the first JSON object in text; None if there isn't one."""
    i = (text or "").find("{")
    if i < 0:
        return None
    try:
        return json.loads(text[i:])
    except Exception:
        return None


# Claims of the form "everything is fine" that must never pass on their own. A verifier
# grades NUMBERS; an unsupported all-clear is the false-clean error a reliability
# harness exists to catch (see t03_integrity_check).
CLEAN_WORDS = ("no issues", "none found", "no errors", "all clean", "nothing",
               "no problems", "zero", "all good", "everything is fine", "no failures")


def claims_clean(response: str) -> bool:
    low = (response or "").lower()
    return any(w in low for w in CLEAN_WORDS)


def grade_counts(response: str, required: list, tol: int = 0) -> tuple:
    """True only if EVERY required integer appears in the response.

    `required` is a list of (label, value). Returns (passed, detail).
    """
    missing = [f"{lab}={val}" for lab, val in required
               if val is None or not mentions(response, val, tol=tol)]
    return (not missing), ("all present" if not missing else "missing " + ", ".join(missing))


# ── ground-truth sanity (Opus, 2026-08-20) ───────────────────────────────────
# A verifier grades the agent against ground truth it computed itself. If that
# computation is WRONG rather than missing, the whole test agrees with itself and
# reports a confident, meaningless result.
#
# That is not hypothetical. A double-escaped regex made HB-01 report "72 of 72 skills
# have broken frontmatter", and the first test run PASSED it, because the synthetic
# "correct" answer was built from the same wrong baseline. What caught it was the
# number being implausible on its face - judgment, not the harness.
#
# So each ground-truth probe now states what a believable answer looks like. A probe
# that fails its own reasonableness check is a HARNESS FAULT, not an agent failure,
# and is reported as such: results are prefixed HARNESS-FAULT: so rate analysis can
# separate a broken fixture from a genuine miss. Counting harness faults as agent
# failures would quietly depress every measurement we make.

HARNESS_FAULT = "HARNESS-FAULT: "


def sanity(*checks) -> str | None:
    """checks are (condition, message) pairs. Returns the first failure, or None.

    Conditions are pre-evaluated booleans, so callers should keep them cheap.
    """
    for cond, msg in checks:
        if not cond:
            return msg
    return None


def fault(reason: str) -> tuple:
    """Uniform return for an unusable baseline."""
    return False, HARNESS_FAULT + reason
