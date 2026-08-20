#!/usr/bin/env python3
"""
verify_holdout_seal.py — assert Pool B has never leaked into a container

WHY THIS EXISTS
---------------
Phase B's validation design uses two structurally disjoint task pools:

  Pool A (acceptance)  visible during the improvement cycle; the PACE e-process runs
                       against it and the commit/reject decision is made there.
  Pool B (holdout)     sealed. Same capabilities, different concrete scenarios. Run
                       only AFTER a change is accepted, to check it generalised.

Pool A improving while Pool B does not means the change overfit the acceptance set.
That signal is worth exactly as much as the seal is airtight, and not one bit more.

THE SEAL IS THE API BOUNDARY (Opus, 2026-08-20)
Pool B lives on the HOST. The agents live in containers and reach the host only
through `/api/api_message`. The harness reads Pool B, sends the task as an ordinary
prompt, and evaluates the response. The agent cannot tell a Pool A task from a Pool B
task from a normal request, and cannot read what it was never given.

WHY A MECHANICAL CHECK RATHER THAN A CONVENTION
-----------------------------------------------
Pool B has to live in the repo (Opus authors it there, it must be reviewable and
version-controlled) and must NEVER be deployed. That cuts directly against the install
pipeline's own design principle — "deploy by directory walk, no curated list; if
something shouldn't be deployed, it shouldn't be in the repo." Pool B is the one thing
that has to be in the repo and out of the container.

A rule that contradicts the pipeline's organising principle will eventually be broken
by someone following that principle correctly. So it is enforced by a gate rather than
trusted to memory.

WHAT IT CHECKS
--------------
1. No holdout PATH exists in the container.
2. No file in the container matches the CONTENT HASH of any holdout file — this is the
   one that matters, because a copy under a different name defeats a path check but not
   a hash check.

Exit 0 only when both hold for every container checked.

Usage:
  python scripts/verify_holdout_seal.py                 # all known containers
  python scripts/verify_holdout_seal.py VekV2 ...       # specific ones
"""
import hashlib
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOLDOUT_DIR = os.path.join(REPO, "harness", "holdout")
DEFAULT_CONTAINERS = ["VekV2", "agent-zero-v2", "exo_installtest"]

# Paths a holdout file must never appear under, checked directly.
FORBIDDEN_PATHS = [
    "/a0/usr/plugins/_exocortex/harness",
    "/a0/usr/harness",
    "/a0/harness",
    "/a0/usr/holdout",
    "/a0/usr/plugins/_exocortex/holdout",
]

_ENV = dict(os.environ, MSYS_NO_PATHCONV="1")


def dexec(container, *args):
    return subprocess.run(["docker", "exec", container, *args],
                          capture_output=True, text=True, env=_ENV)


def holdout_hashes() -> dict:
    """md5 -> relative path, for every file in the holdout tree."""
    out = {}
    if not os.path.isdir(HOLDOUT_DIR):
        return out
    for root, _dirs, files in os.walk(HOLDOUT_DIR):
        if "__pycache__" in root:
            continue
        for fn in files:
            p = os.path.join(root, fn)
            try:
                with open(p, "rb") as fh:
                    out[hashlib.md5(fh.read()).hexdigest()] = os.path.relpath(p, REPO)
            except OSError:
                continue
    return out


def check(container: str, hashes: dict) -> list:
    """Return a list of violations for one container."""
    problems = []

    up = subprocess.run(["docker", "inspect", "-f", "{{.State.Running}}", container],
                        capture_output=True, text=True, env=_ENV)
    if up.returncode != 0:
        print(f"  {container:<18} not found — skipped")
        return problems
    if up.stdout.strip() != "true":
        print(f"  {container:<18} not running — skipped")
        return problems

    # 1. forbidden paths
    for p in FORBIDDEN_PATHS:
        r = dexec(container, "test", "-e", p)
        if r.returncode == 0:
            problems.append(f"{container}: forbidden path EXISTS: {p}")

    # 2. content hashes — the check a rename cannot defeat
    if hashes:
        r = dexec(container, "sh", "-c",
                  "find /a0/usr /a0/prompts -type f "
                  "\\( -name '*.md' -o -name '*.json' -o -name '*.jsonl' -o -name '*.py' \\) "
                  "2>/dev/null | head -20000 | xargs -r md5sum 2>/dev/null")
        for line in (r.stdout or "").splitlines():
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            digest, path = parts[0], parts[1].strip()
            if digest in hashes:
                problems.append(
                    f"{container}: HOLDOUT CONTENT LEAKED -> {path} "
                    f"(matches {hashes[digest]})")

    if not problems:
        print(f"  {container:<18} sealed")
    return problems


def main() -> int:
    containers = sys.argv[1:] or DEFAULT_CONTAINERS
    hashes = holdout_hashes()

    print(f"Holdout seal check — {len(hashes)} holdout file(s) at harness/holdout/")
    if not hashes:
        print("  NOTE: the holdout tree is empty. The path checks still run, but the")
        print("  content check has nothing to compare against yet. This gate exists")
        print("  BEFORE the content so the content can never land unguarded.")

    problems = []
    for c in containers:
        problems.extend(check(c, hashes))

    print()
    if problems:
        print(f"SEAL BROKEN — {len(problems)} violation(s):")
        for p in problems:
            print(f"  ! {p}")
        print("\nPool B is only worth what its seal is worth. A leaked holdout is not a")
        print("holdout: any 'it generalised' result measured against it is meaningless.")
        return 1
    print("SEAL INTACT — no holdout content reachable from any container.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
