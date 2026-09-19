"""Compare the repo's plugins/_exocortex/ tree against a container's live tree.

Acceptance instrument for Tier 1.1 step 3. The installer's job is to faithfully
reproduce the repo tree; this measures whether it did, rather than asserting it.

    python scripts/verify_plugin_parity.py <container> [--source DIR] [--quiet]

Reports seven sets:
  MISSING     in repo, absent from the container   -> the installer did not deploy it
  RETIRED     in repo, absent ON PURPOSE           -> expected; see scripts/retired_manifest.txt
  RESURRECTED retired but PRESENT in the container -> hard failure, see below
  EXTRA       in the container, absent from repo   -> hand-deployed, or runtime output
  DIFFERENT   present in both, md5 mismatch        -> stale deploy
  MERGED      config files, compared semantically  -> see below
  MATCH       identical

Exit 0 only when MISSING, DIFFERENT and RESURRECTED are all empty, and no MERGED
file differs semantically.

RETIRED exists for the same reason as MERGED, one category over. On 2026-09-18 this
gate read PARITY FAIL with 26 MISSING, 18 of which are files retired deliberately --
the Arm M prune of 2026-09-08 and the PACE injector retired 2026-09-02. For those,
"the installer did not deploy it" is exactly backwards, and acting on the report
resurrects them. A gate whose category names the wrong action is worse than a silent
one, because it recruits the reader into undoing what the gate should protect.

It is NOT an exemption: retired-and-absent is the expected steady state and passes,
while retired-and-PRESENT is a HARD FAIL. That second half is what makes it an
instrument rather than a mute button -- resurrection (a clone-and-install into a
fresh container, an A0 upgrade, a well-meaning fix of a "missing" file) is now
detected, which it previously was not. The list lives in a file the gate READS so
that recording a retirement never means editing the instrument.

EXTRA is reported but does not fail: runtime state legitimately lives under the
plugin on a running container and is not the installer's business.

MERGED exists because config/ is deliberately NOT byte-reproduced. Config is
read-merge-write (new sections added, existing operator values never clobbered),
so an md5 comparison there measures the wrong thing and would produce a
permanently-failing gate that people learn to ignore. These files are instead
parsed and compared as data: key order and formatting are allowed to drift,
CONTENT is not. Reported explicitly rather than silently skipped.
"""

import argparse
import hashlib
import os
import subprocess
import sys

DEFAULT_SOURCE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "plugins", "_exocortex",
)
CONTAINER_ROOT = "/a0/usr/plugins/_exocortex"

# Never the installer's concern: build artefacts, local backups, runtime output.
SKIP_DIR_NAMES = {"__pycache__", ".git", "memory", "sleep_reports", "state"}
SKIP_SUFFIXES = (".pyc", ".pyo")


def _skip(rel: str) -> bool:
    parts = rel.split("/")
    if any(p in SKIP_DIR_NAMES for p in parts):
        return True
    if rel.endswith(SKIP_SUFFIXES):
        return True
    base = parts[-1]
    return ".bak" in base or base.endswith("~")


def repo_manifest(root: str) -> dict:
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            if _skip(rel):
                continue
            with open(full, "rb") as fh:
                out[rel] = hashlib.md5(fh.read()).hexdigest()
    return out


def container_manifest(container: str) -> dict:
    # Single exec, quoted so MSYS cannot rewrite the absolute paths and so the
    # shell constructs survive (docker exec silently no-ops otherwise — seam #30).
    script = (
        f'cd {CONTAINER_ROOT} 2>/dev/null || exit 9; '
        "find . -type f ! -path '*/__pycache__/*' ! -name '*.pyc' "
        "! -path './memory/*' ! -path './sleep_reports/*' ! -path './state/*' "
        "-exec md5sum {} +"
    )
    env = dict(os.environ, MSYS_NO_PATHCONV="1")
    res = subprocess.run(
        ["docker", "exec", container, "sh", "-c", script],
        capture_output=True, text=True, env=env,
    )
    if res.returncode == 9:
        print(f"ERROR: {CONTAINER_ROOT} does not exist in {container}")
        sys.exit(2)
    if res.returncode != 0:
        print(f"ERROR: docker exec failed: {res.stderr.strip()[:300]}")
        sys.exit(2)

    out = {}
    for line in res.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        digest, _, path = line.partition("  ")
        rel = path[2:] if path.startswith("./") else path
        if _skip(rel):
            continue
        out[rel] = digest
    return out


# Only the main plugin config is merged. Model profiles and other config/ data
# files ARE byte-reproduced — they are inputs the stack reads, not operator state,
# so a drift there is a real staleness finding and must fail the gate.
MERGED_FILES = {"config/config.json"}


def _is_merged(rel: str) -> bool:
    """Files the installer merges rather than byte-reproduces."""
    return rel in MERGED_FILES


def _same_json(container: str, source_root: str, rel: str) -> bool:
    """Compare a merged config as DATA, not bytes. Formatting may drift; content may not."""
    import json

    try:
        with open(os.path.join(source_root, rel.replace("/", os.sep)), encoding="utf-8-sig") as fh:
            repo_data = json.load(fh)
    except Exception:
        return False

    env = dict(os.environ, MSYS_NO_PATHCONV="1")
    res = subprocess.run(
        ["docker", "exec", container, "cat", f"{CONTAINER_ROOT}/{rel}"],
        capture_output=True, text=True, env=env,
    )
    if res.returncode != 0:
        return False
    try:
        live_data = json.loads(res.stdout.lstrip("﻿"))
    except Exception:
        return False

    return repo_data == live_data


RETIRED_MANIFEST = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "retired_manifest.txt")


def load_retired(path: str | None = None) -> set:
    """Paths that are deliberately in the repo and deliberately not deployed.

    A missing manifest yields an empty set, which restores the old behaviour exactly --
    every retired file reverts to MISSING and the gate fails loudly. That is the correct
    direction to fail: absent knowledge must not read as permission.
    """
    path = path or RETIRED_MANIFEST
    out = set()
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.split("  #", 1)[0].strip()
                if not line or line.startswith("#"):
                    continue
                out.add(line.replace(os.sep, "/"))
    except FileNotFoundError:
        return set()
    return out


def classify(repo: dict, live: dict, retired, merged_bad=()) -> dict:
    """Partition the two manifests. Pure -- no docker, no disk -- so it can be controlled.

    Kept separate from main() precisely so the control can drive it with synthetic trees;
    a classifier reachable only through a live container is one nobody can test the edges of.
    """
    retired = set(retired or ())
    both = set(repo) & set(live)
    merged_paths = sorted(k for k in both if _is_merged(k))

    retired_present = sorted(retired & set(live))          # resurrection -> hard fail
    retired_absent = sorted((retired & set(repo)) - set(live))   # expected steady state
    retired_gone = sorted(retired - set(repo) - set(live))       # informational

    missing = sorted(set(repo) - set(live) - retired)
    extra = sorted(set(live) - set(repo) - retired)
    diff = sorted(k for k in both
                  if repo[k] != live[k] and not _is_merged(k) and k not in retired)
    match = len(both) - len(diff) - len(merged_paths) - len(retired & both)

    return {
        "missing": missing,
        "retired_absent": retired_absent,
        "retired_present": retired_present,
        "retired_gone": retired_gone,
        "extra": extra,
        "diff": diff,
        "merged_paths": merged_paths,
        "match": match,
        "ok": not missing and not diff and not merged_bad and not retired_present,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("container")
    ap.add_argument("--source", default=DEFAULT_SOURCE)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    repo = repo_manifest(args.source)
    live = container_manifest(args.container)

    both = set(repo) & set(live)
    merged_paths = sorted(k for k in both if _is_merged(k))
    merged_bad = [k for k in merged_paths if not _same_json(args.container, args.source, k)]

    retired = load_retired()
    r = classify(repo, live, retired, merged_bad)
    missing, extra, diff = r["missing"], r["extra"], r["diff"]
    retired_absent, retired_present = r["retired_absent"], r["retired_present"]
    retired_gone, match = r["retired_gone"], r["match"]

    print(f"source : {args.source}")
    print(f"target : {args.container}:{CONTAINER_ROOT}")
    print(f"\nrepo files {len(repo)}  |  live files {len(live)}")
    print(f"  MATCH      {match}")
    print(f"  MISSING    {len(missing)}   (in repo, not deployed)")
    print(f"  RETIRED    {len(retired_absent)}   (in repo, absent ON PURPOSE — expected)"
          + (f"  [+{len(retired_gone)} manifest entries present nowhere]"
             if retired_gone else ""))
    if retired_present:
        print(f"  RESURRECTED {len(retired_present)}  *** retired but DEPLOYED — hard failure ***")
    print(f"  DIFFERENT  {len(diff)}   (deployed but stale)")
    print(f"  MERGED     {len(merged_paths)}   (config — compared as data; "
          f"{len(merged_bad)} differing)")
    print(f"  EXTRA      {len(extra)}   (in container only — informational)")

    if not args.quiet:
        for label, items in (("RESURRECTED", retired_present), ("MISSING", missing),
                             ("DIFFERENT", diff), ("MERGED-DIFFERING", merged_bad),
                             ("EXTRA", extra)):
            if not items:
                continue
            print(f"\n--- {label} ---")
            for rel in items[:40]:
                print(f"  {rel}")
            if len(items) > 40:
                print(f"  ... and {len(items) - 40} more")

    ok = r["ok"]
    print(f"\n{'PARITY OK' if ok else 'PARITY FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
