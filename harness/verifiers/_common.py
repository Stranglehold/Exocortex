"""Shared verifier helpers — independent ground truth from the container.

Verifiers check OUTCOMES against ground truth computed independently of the agent.
For the reporting-type starter tasks (T01/T03), ground truth is the canonical
wiki page/issue counts, obtained by running integrity_check.py ourselves.
"""
import json
import re
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
