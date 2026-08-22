#!/usr/bin/env python3
"""Find state keys that are WRITTEN and never READ — the severed-loop scan.

The defect this codebase produces most reliably is producer-built / consumer-assumed: an
extension faithfully records something and nothing ever consumes it. It has shown up as
skills_captured:0 for 878 cycles, as _49's reasoning state written for months with no
reader, as 476 orphaned memories, and as an acceptor that is verified and uncalled. Every
one of them looked installed.

This makes the class mechanically findable instead of stumbled upon.

    python scripts/scan_severed_loops.py [--root DIR] [--all]

DELIBERATELY OVER-REPORTS. Read every hit before believing it — the lexical critics in
this repo were wrong three times in exactly this way, and each time they accused working
code. A missed severed loop stays invisible for months; a false positive costs the seconds
it takes to read the line. That trade is the right way round, but only if the hits are
actually read.

KNOWN FALSE-POSITIVE CLASSES, all four observed on the first real run (8 hits -> 2 real):

  1. extras_persistent / extras_temporary — A0 CORE is the consumer. agent.py:586 merges
     both into a message and :590 clears them. Writing to extras IS the delivery
     mechanism, so every injector legitimately looks write-only. Reported separately
     below rather than mixed in with real findings.
  2. A consumer in A0 core, outside this tree. `lifetime_hours` looks severed here and is
     read by /a0/extensions/python/job_loop/_20_cleanup_expired_api_chats.py.
  3. A read split across lines. `_sig_guardian_history` is read by a getattr whose call
     spans two lines; these patterns are single-line. Not fixed — multi-line matching
     costs more false positives than it removes.
  4. A reference held to keep an object alive. `setattr(agent, POLL_TASK_KEY, task)`
     exists so asyncio does not garbage-collect the task; holding it IS the consumption,
     and nothing should ever read it.

So: confirm against the whole container, not just this tree, before calling anything
severed. `docker exec <c> grep -rn --include=*.py <key> /a0`

Exit 0 always. This is an instrument, not a gate: the judgement is in reading the output.
"""

import argparse
import os
import re
import sys
from collections import defaultdict

# Each pattern captures the key name in group 1.
ACCESSORS = [
    # agent.set_data("k", v) / agent.get_data("k")
    ("set_data",            re.compile(r'\.set_data\(\s*["\']([^"\']+)["\']')),
    ("get_data",            re.compile(r'\.get_data\(\s*["\']([^"\']+)["\']')),
    # loop_data.extras_persistent["k"] = ...   vs   ... = extras_persistent["k"] / .get("k")
    ("extras_write",        re.compile(r'extras_(?:persistent|temporary)\[\s*["\']([^"\']+)["\']\s*\]\s*=')),
    # The subscript read must NOT also match the write form. `(?!=)` alone does not do
    # that: in `extras_persistent["k"] = v` the `\s*` matches zero characters, the next
    # char is a space rather than `=`, the lookahead passes, and every write is counted as
    # a read of itself — so no extras key could ever appear severed. Caught by the
    # fixture, invisible in a real-tree run. `(?!\s*=[^=])` skips whitespace before
    # deciding, and the `[^=]` keeps `==` comparisons reading as reads.
    ("extras_read",         re.compile(r'extras_(?:persistent|temporary)(?:\[\s*["\']([^"\']+)["\']\s*\](?!\s*=[^=])|\.get\(\s*["\']([^"\']+)["\'])')),
    ("params_write",        re.compile(r'params_(?:temporary|persistent)\[\s*["\']([^"\']+)["\']\s*\]\s*=')),
    ("params_read",         re.compile(r'params_(?:temporary|persistent)(?:\[\s*["\']([^"\']+)["\']\s*\](?!\s*=[^=])|\.get\(\s*["\']([^"\']+)["\'])')),
    # setattr(agent, "_k", v) / getattr(agent, "_k", d)
    ("setattr",             re.compile(r'setattr\(\s*[\w.]+\s*,\s*["\']([^"\']+)["\']')),
    ("getattr",             re.compile(r'getattr\(\s*[\w.]+\s*,\s*["\']([^"\']+)["\']')),
    # agent._foo = ...   vs   agent._foo used
    ("attr_write",          re.compile(r'\b(?:self\.)?agent\.(_[A-Za-z]\w*)\s*=(?!=)')),
    # Same self-matching hazard as extras_read above — `agent._foo = 1` would otherwise
    # count as a read of _foo through backtracking.
    ("attr_read",           re.compile(r'\b(?:self\.)?agent\.(_[A-Za-z]\w*)\b(?!\s*=[^=])')),
]

WRITE_KINDS = {"set_data", "extras_write", "params_write", "setattr", "attr_write"}
READ_KINDS = {"get_data", "extras_read", "params_read", "getattr", "attr_read"}

SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".archive", ".hardening_originals"}

# Keys are frequently held in a module-level constant rather than inlined at the call
# site — `PACE_LEVEL_KEY = "_org_pace_level"`, then `get_data(PACE_LEVEL_KEY)`. That is
# GOOD practice here (a shared constant is why the two halves of a mechanism cannot drift
# apart), and the first version of this scan was blind to it: it reported _org_pace_level
# and _ei_last_verdict as severed when both have three consumers each. An instrument that
# is defeated by the codebase's own best practice is worse than no instrument, because it
# accuses working code and trains people to ignore it.
#
# So resolve `CONST = "literal"` per file and treat a bare use of CONST inside an accessor
# as a use of that literal.
_CONST_DEF = re.compile(r'^\s*([A-Z][A-Z0-9_]{2,})\s*=\s*["\']([^"\']+)["\']\s*(?:#.*)?$')
_CONST_USE = re.compile(
    r'(?:\.set_data\(\s*|\.get_data\(\s*|setattr\([\w.]+\s*,\s*|getattr\([\w.]+\s*,\s*'
    r'|extras_(?:persistent|temporary)\[\s*|params_(?:temporary|persistent)\[\s*'
    r'|extras_(?:persistent|temporary)\.get\(\s*|params_(?:temporary|persistent)\.get\(\s*)'
    r'([A-Z][A-Z0-9_]{2,})\b')
_WRITE_CONST = re.compile(
    r'(?:\.set_data\(\s*|setattr\([\w.]+\s*,\s*'
    r'|extras_(?:persistent|temporary)\[\s*|params_(?:temporary|persistent)\[\s*)'
    r'([A-Z][A-Z0-9_]{2,})\b')


def scan(root):
    writes = defaultdict(list)
    reads = defaultdict(list)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    lines = fh.readlines()
            except Exception:
                continue
            rel = os.path.relpath(path, root)

            # Pass 1: this file's key constants, so `get_data(PACE_LEVEL_KEY)` resolves.
            consts = {}
            for line in lines:
                m = _CONST_DEF.match(line)
                if m:
                    consts[m.group(1)] = m.group(2)

            # Pass 2: accessors.
            for i, line in enumerate(lines, 1):
                stripped = line.lstrip()
                # Comments and docstring prose describe keys constantly; counting them as
                # reads is how a severed loop hides behind its own documentation.
                if stripped.startswith("#"):
                    continue
                for kind, rx in ACCESSORS:
                    for m in rx.finditer(line):
                        key = next((g for g in m.groups() if g), None)
                        if not key:
                            continue
                        entry = (rel, i, kind, line.strip()[:120])
                        (writes if kind in WRITE_KINDS else reads)[key].append(entry)

                # Constant-mediated access. Writes matched first so a write is not also
                # counted as a read of itself.
                written_here = set()
                for m in _WRITE_CONST.finditer(line):
                    key = consts.get(m.group(1))
                    if key:
                        written_here.add(m.group(1))
                        writes[key].append((rel, i, "const_write:%s" % m.group(1),
                                            line.strip()[:120]))
                for m in _CONST_USE.finditer(line):
                    if m.group(1) in written_here:
                        continue
                    key = consts.get(m.group(1))
                    if key:
                        reads[key].append((rel, i, "const_read:%s" % m.group(1),
                                           line.strip()[:120]))
    return writes, reads


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins", "_exocortex"))
    ap.add_argument("--all", action="store_true", help="also list keys that ARE consumed")
    args = ap.parse_args()

    writes, reads = scan(args.root)
    all_severed = sorted(k for k in writes if k not in reads)
    consumed = sorted(k for k in writes if k in reads)
    read_only = sorted(k for k in reads if k not in writes)

    # extras_* is delivered to the model by A0 core, so a write-only extras key is the
    # normal case, not a defect. Split it out rather than dropping it: an injector that
    # writes a key nobody ever renders is still worth being able to see.
    def _extras_only(key):
        return all(kind == "extras_write" for _, _, kind, _ in writes[key])

    core_delivered = [k for k in all_severed if _extras_only(k)]
    severed = [k for k in all_severed if k not in core_delivered]

    print("root: %s" % args.root)
    print("keys written: %d | read: %d | consumed both ways: %d"
          % (len(writes), len(reads), len(consumed)))
    print()

    print("=" * 72)
    print("WRITTEN, NEVER READ  (%d)  — candidate severed loops" % len(severed))
    print("=" * 72)
    for k in severed:
        print("  %s" % k)
        for rel, ln, kind, src in writes[k][:3]:
            print("      %s:%s  [%s]  %s" % (rel, ln, kind, src))
    if not severed:
        print("  (none)")

    print()
    print("=" * 72)
    print("EXTRAS-ONLY WRITES  (%d)  — delivered to the model by A0 core, normally fine"
          % len(core_delivered))
    print("=" * 72)
    for k in core_delivered:
        print("  %s   (%s)" % (k, writes[k][0][0]))
    if not core_delivered:
        print("  (none)")

    print()
    print("=" * 72)
    print("READ, NEVER WRITTEN  (%d)  — consumer waiting on a producer that isn't here" % len(read_only))
    print("=" * 72)
    print("  (expected for keys A0 core sets; read every hit before believing it)")
    for k in read_only:
        print("  %s" % k)
        for rel, ln, kind, src in reads[k][:2]:
            print("      %s:%s  [%s]  %s" % (rel, ln, kind, src))

    if args.all:
        print()
        print("CONSUMED (%d): %s" % (len(consumed), ", ".join(consumed)))

    return 0


if __name__ == "__main__":
    sys.exit(main())
