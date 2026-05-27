#!/usr/bin/env python3
"""
check_a0_updates.py — Agent-Zero upgrade & security radar for the Exocortex stack.

Answers the two questions that matter for keeping the repo safe and reproducible:
  1. Are we behind upstream A0, and does any newer release carry a SECURITY fix?
  2. Of the files A0 changed since our pin, which ones do we OVERWRITE in patches/?
     (Those are the re-base set — a blind install would revert A0's version of them,
     including security fixes. See docs/UPGRADE_A0.md.)

Reads the pinned version from ./A0_VERSION and the overwrite surface from ./patches/.
Hits the public GitHub API (unauthenticated, ~60 req/hr — this uses < 12). To beat
the compare API's 300-file cap it diffs each ADJACENT tag pair and unions the result,
so the patches/ overlap is complete, not truncated.

Exit codes (CI-usable):  0 up to date · 1 updates pending · 2 security-flagged update pending.

Usage:  python scripts/check_a0_updates.py [--repo agent0ai/agent-zero]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request

REPO_DEFAULT = "agent0ai/agent-zero"
# Descriptive terms / stems — substring match is fine.
SECURITY_SUBSTRINGS = (
    "security", "vulnerab", "sanitiz", "injection", "exploit", "privilege esc",
    "auth bypass", "sandbox escape",
)
# Acronyms — MUST be word-bounded, else "rce" matches "resou(rce)", "ssrf"/"csrf"
# match unrelated tokens, etc. (caught v1.17/v1.18 false-flagging on "resource").
SECURITY_ACRONYMS = ("cve", "xss", "rce", "csrf", "ssrf", "lfi", "rfi")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def gh(path: str):
    """GET the GitHub API (follows the repo-rename redirect automatically)."""
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "exocortex-a0-radar",
    })
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read())


def read_pin() -> str:
    p = os.path.join(HERE, "A0_VERSION")
    if not os.path.isfile(p):
        return ""
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#"):
            return line.split()[0]
    return ""


def vkey(tag: str):
    """Sort key for vX.Y.Z tags; non-numeric parts sort low."""
    parts = tag.lstrip("v").split(".")
    out = []
    for p in parts:
        out.append(int(p) if p.isdigit() else -1)
    return tuple(out)


def patched_relpaths() -> set:
    """Relative paths under patches/ (mirrors A0's tree). Path-suffix matching
    against A0's changed files avoids basename false positives — e.g. our
    patches/webui/messages.js must NOT match A0's webui/js/messages.js."""
    rels = set()
    base = os.path.join(HERE, "patches")
    for root, _, files in os.walk(base):
        if "__pycache__" in root:
            continue
        for f in files:
            if f.endswith((".py", ".md", ".js", ".html", ".css", ".json")):
                rel = os.path.relpath(os.path.join(root, f), base).replace(os.sep, "/")
                rels.add(rel)
    return rels


def _matches(a0_path: str, patch_rels: set) -> str | None:
    """Return the patch relpath that corresponds to an A0 changed file by path
    suffix (a0_path ends with the patch's relative path), else None."""
    for rel in patch_rels:
        if a0_path == rel or a0_path.endswith("/" + rel):
            return rel
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO_DEFAULT)
    args = ap.parse_args()

    print("=" * 72)
    print("AGENT-ZERO UPGRADE & SECURITY RADAR")
    print("=" * 72)

    pinned = read_pin()
    if not pinned:
        print("  No A0_VERSION pin found — cannot compare. Create ./A0_VERSION first.")
        return 1
    print(f"  Pinned (tested):  {pinned}")

    try:
        tags = [t["name"] for t in gh(f"/repos/{args.repo}/tags?per_page=50")]
    except Exception as e:
        print(f"  Could not reach GitHub: {e}")
        return 1

    known = [t for t in tags if vkey(t) >= (0,)]
    known.sort(key=vkey)
    if pinned not in known:
        print(f"  WARN: pinned {pinned} not in upstream tag list (renamed/yanked?).")
    latest = known[-1]
    print(f"  Latest upstream:  {latest}")

    newer = [t for t in known if vkey(t) > vkey(pinned)]
    if not newer:
        print("\n  UP TO DATE — no newer releases.\n")
        return 0

    print(f"\n  {len(newer)} newer release(s): {', '.join(newer)}")

    # --- security scan of release notes ---
    print("\n--- release notes (security scan) ---")
    security_pending = False
    for tag in newer:
        body = ""
        try:
            rel = gh(f"/repos/{args.repo}/releases/tags/{tag}")
            body = (rel.get("body") or "").lower()
        except Exception:
            body = ""
        hits = {k for k in SECURITY_SUBSTRINGS if k in body}
        hits |= {k for k in SECURITY_ACRONYMS if re.search(rf"\b{k}\b", body)}
        hits = sorted(hits)
        if hits:
            security_pending = True
            print(f"  {tag}: SECURITY-RELEVANT — keywords: {', '.join(hits)}")
        else:
            print(f"  {tag}: (no security keywords in notes)")

    # --- changed-files overlap with our patches/ (the re-base set) ---
    print("\n--- patch overlap (A0-changed files matching a patch path) ---")
    patched = patched_relpaths()
    chain = [pinned] + newer  # adjacent-pair compares beat the 300-file cap
    changed_in = {}  # A0 path -> set(tags where it changed)
    for a, b in zip(chain, chain[1:]):
        try:
            cmp = gh(f"/repos/{args.repo}/compare/{a}...{b}")
        except Exception as e:
            print(f"  WARN: compare {a}...{b} failed: {e}")
            continue
        for fobj in cmp.get("files", []):
            if _matches(fobj["filename"], patched):
                changed_in.setdefault(fobj["filename"], set()).add(b)

    if not changed_in:
        print("  None — A0's changes do not match any patch path. "
              "Upgrade is purely additive (low risk).")
    else:
        print(f"  {len(changed_in)} candidate(s) — A0 changed a file matching a patch path.")
        print("  Confirm each one's deploy mechanism (see docs/UPGRADE_A0.md):")
        print("    overwrite (docker cp)  -> RE-BASE: 3-way merge our delta onto A0's new file")
        print("    sed-injection          -> verify the injection anchor still exists")
        print("    unused/stale patch     -> no action (not deployed)")
        for fn in sorted(changed_in):
            print(f"    {fn}   (changed in: {', '.join(sorted(changed_in[fn], key=vkey))})")

    print("\n" + "=" * 72)
    if security_pending:
        print("  ACTION: security-relevant update pending. Plan an upgrade (docs/UPGRADE_A0.md).")
        print("=" * 72)
        return 2
    print("  Updates pending (no security flags). Upgrade at convenience (docs/UPGRADE_A0.md).")
    print("=" * 72)
    return 1


if __name__ == "__main__":
    sys.exit(main())
