#!/usr/bin/env python3
"""recall_trace_report.py — what was recalled into each idle cycle, joined to how the cycle ended
and what it wrote down.

WHY (build order item 2a, 2026-09-24)
-------------------------------------
Cycle #731 journaled "search_library down" from a recalled memory, with no probe run, and the link
was found by hand in chat.json. The recall tag only lasts one monologue. The recall trace
(helpers/memory_recall_tag.trace) records which memories each turn received, and this script
lines those rows up against the cycle they belong to.

READS (read-only: three jsonl files)
------------------------------------
  trace    /a0/usr/plugins/_exocortex/state/recall_trace.jsonl       memory_recall_tag.trace
  endings  /a0/usr/workdir/workspace/office/cycle_endings.jsonl      services/idle_watch._write_ending
  journal  /a0/usr/workdir/workspace/self-improvement/journal.jsonl  self-improvement/cycle_close.py
                                                                     (she runs it: model-authored)
From a container with --container (docker exec cat), or local copies with --trace/--endings/--journal.
Parsed through helpers/cycle_windows: R1 repaired and skipped lines are reported, R3 timestamps are
parsed rather than compared as text, R4 the join is on context_id, never the cycle number.

ATTRIBUTION: a trace row belongs to the ENDED cycle with its context_id whose ending is the first
at or after the row. A row with no such ending is "unjoined": a driven chat, a cycle still
running, or (with --until) one that ended after the window. A context id reused by a later cycle
therefore splits by time, never merges. The window filters trace rows and endings separately, so
a cycle that began before --since shows only its rows inside the window.

WHAT IT REPORTS
---------------
  coverage  rows by hook and by query source; early returns by reason, which is the A17 gap as a
            count (turns where _92 returned before recalling, so A0's own recall, if any, stood
            untagged); pipeline errors.
  cycles    each ended cycle in the window: type, outcome, elapsed, and NO-TOOL when the heartbeat
            never advanced. The daemon stamps cycle_heartbeat at fire (services/idle_watch.py:480,
            the same `now` as last_cycle_start), and _70_idle_trigger.py:82 re-stamps it on every
            top-level tool call, so heartbeat_age_s == elapsed_s means no tool call completed in
            the cycle. Also: rows, full _92 turns, early rows, memory_load calls, distinct ids, the
            ids present on EVERY full _92 turn (constant recall), and whether a journal close
            carries the context_id, with its activity line.
  withheld  (graduated trust, Phase 1) the candidates the trust verdict withheld, from each full
            _92 row's `dropped` list. Rows written before Phase 1 lack the field and are counted
            apart, never read as "none withheld".
  memories  the most-recalled ids with the query-source split. An id recalled only under
            idle_charge may be near the fixed activation charge rather than relevant to the work
            (Opus and Fable, 2026-09-24); those are marked CHARGE-ONLY.
  unjoined  rows whose context has no ending at or after them, by context.

WHAT IT DOES NOT DO
-------------------
  - It does not read memory content, and it does not decide that a recall CAUSED a conclusion.
    It lines the two up so a person can check.
  - It writes nothing, anywhere.
  - A missing or empty trace is UNVERIFIED (exit 3), never zero recall.
  - No LLM calls.

    python scripts/recall_trace_report.py --container agent-zero-v2   # the primary, 2026-09-24
    python scripts/recall_trace_report.py --trace T --endings E --journal J [--since ISO] [--json]

Exit: 0 report printed; 1 a file could not be fetched or read; 3 no trace rows (UNVERIFIED).
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "plugins", "_exocortex", "helpers"))
import cycle_windows as cw  # noqa: E402

PATHS = {
    "trace": "/a0/usr/plugins/_exocortex/state/recall_trace.jsonl",
    "endings": "/a0/usr/workdir/workspace/office/cycle_endings.jsonl",
    "journal": "/a0/usr/workdir/workspace/self-improvement/journal.jsonl",
    # optional: _19's gate ledger (refusals + shadow containment). Written only on events, so a
    # missing file means "nothing refused or shadow-logged yet", not an error.
    "gate": "/a0/usr/plugins/_exocortex/state/resave_gate.jsonl",
}
REQUIRED = ("trace", "endings", "journal")
EXIT_OK, EXIT_ERROR, EXIT_UNVERIFIED = 0, 1, 3


# ── reading ──────────────────────────────────────────────────────────────────────────────────────

def fetch(container, path, dest):
    """Copy one container file to `dest` with `docker exec cat`. Returns "ok", "missing" or an
    "error: ..." string. Read-only: nothing in the container is touched."""
    try:
        r = subprocess.run(["docker", "exec", container, "cat", path], capture_output=True,
                           timeout=120)
    except Exception as e:
        return "error: %s: %s" % (type(e).__name__, e)
    if r.returncode != 0:
        err = r.stderr.decode("utf-8", "replace").strip()
        return "missing" if "No such file" in err else "error: " + err[:300]
    with open(dest, "wb") as fh:
        fh.write(r.stdout)
    return "ok"


def load(path):
    """(rows, repaired, skipped, state): state is "ok", or "missing" when there is no file."""
    if not path or not os.path.isfile(path):
        return [], [], [], "missing"
    rows, repaired, skipped = cw.read_jsonl(path)
    return [r for r in rows if isinstance(r, dict)], repaired, skipped, "ok"


def in_window(row, since, until, key="at"):
    t = cw.parse_ts(row.get(key))
    if t is None:
        return since is None and until is None
    return (since is None or t >= since) and (until is None or t < until)


# ── the join ─────────────────────────────────────────────────────────────────────────────────────

def ended_cycles(endings):
    """The "ended" rows that carry a context_id and a parseable time, in time order."""
    out = []
    for e in endings:
        if e.get("event") != "ended" or not e.get("context_id"):
            continue
        t = cw.parse_ts(e.get("at"))
        if t is not None:
            out.append((t, e))
    out.sort(key=lambda x: x[0])
    return out


def attribute(trace_rows, ended):
    """Assign each trace row to the first ending of its context_id at or after the row.
    Returns ({ending_index: [rows]}, [unjoined rows]); indexes are positions in `ended`."""
    by_ctx = defaultdict(list)
    for i, (t, e) in enumerate(ended):
        by_ctx[e["context_id"]].append((t, i))
    by_cycle, unjoined = defaultdict(list), []
    for r in trace_rows:
        t = cw.parse_ts(r.get("at"))
        hit = None
        if t is not None:
            hit = next((i for (te, i) in by_ctx.get(r.get("context_id")) or [] if te >= t), None)
        if hit is None:
            unjoined.append(r)
        else:
            by_cycle[hit].append(r)
    return by_cycle, unjoined


def journal_by_context(journal_rows):
    """context_id -> the latest cycle_close row carrying it (by parsed time, R3)."""
    dated = []
    for r in cw.closes(journal_rows):
        if r.get("context_id"):
            t = cw.parse_ts(r.get("timestamp"))
            dated.append((t.timestamp() if t else float("-inf"), r))
    dated.sort(key=lambda x: x[0])
    return {r["context_id"]: r for _, r in dated}


def is_full_92(r):
    return r.get("via") == "_92" and not r.get("early")


def gate_counts(gate_rows):
    """{"refused": {rule: n}, "would_refuse": n} for a set of gate-ledger rows."""
    refused = Counter(r.get("rule") for r in gate_rows if r.get("refused"))
    return {"refused": dict(refused), "would_refuse": sum(1 for r in gate_rows if not r.get("refused"))}


def cycle_summary(ending, rows, closes_by_ctx, gate_rows=()):
    full = [r for r in rows if is_full_92(r)]
    constant = None
    if len(full) >= 2:
        constant = sorted(set.intersection(*(set(r.get("ids") or []) for r in full)))
    el, hb = ending.get("elapsed_s"), ending.get("heartbeat_age_s")
    close = closes_by_ctx.get(ending.get("context_id"))
    return {
        "cycle": ending.get("cycle"), "context_id": ending.get("context_id"),
        "type": ending.get("type"), "outcome": ending.get("outcome"), "ended_at": ending.get("at"),
        "elapsed_s": el, "heartbeat_age_s": hb,
        "no_tool": el is not None and hb is not None and el == hb,
        "rows": len(rows), "full_92": len(full),
        "early": dict(Counter(r["early"] for r in rows if r.get("early"))),
        "memory_load": sum(1 for r in rows if r.get("via") == "memory_load"),
        "distinct_ids": len({i for r in rows for i in r.get("ids") or []}),
        "constant_ids": constant,
        "sources": dict(Counter(r.get("source") for r in full)),
        "errors": sum(1 for r in rows if r.get("error")),
        "dropped": sum(len(r.get("dropped") or []) for r in rows),
        "dropped_distinct": len({i for r in rows for i in r.get("dropped") or []}),
        "legacy": sum(len(r.get("legacy") or []) for r in rows),
        "legacy_rows": sum(1 for r in rows if "legacy" in r),
        "gate": gate_counts(gate_rows),
        "closed": close is not None,
        "activity": (close or {}).get("activity"),
    }


def memory_table(trace_rows, top):
    turns, ctxs, src = Counter(), defaultdict(set), defaultdict(Counter)
    for r in trace_rows:
        for i in r.get("ids") or []:
            turns[i] += 1
            ctxs[i].add(r.get("context_id"))
            src[i][r.get("source")] += 1
    out = []
    for i, n in turns.most_common(top):
        out.append({"id": i, "turns": n, "contexts": len(ctxs[i]), "sources": dict(src[i]),
                    "charge_only": set(src[i]) == {"idle_charge"}})
    return out


def build_report(trace_rows, endings, journal_rows, since=None, until=None, top=15, gate_rows=None):
    trace_rows = [r for r in trace_rows if in_window(r, since, until)]
    ended = [(t, e) for (t, e) in ended_cycles(endings) if in_window(e, since, until)]
    by_cycle, unjoined = attribute(trace_rows, ended)
    # _19's gate ledger, attributed exactly like trace rows. None = not read; [] = no events.
    gate_in = [r for r in (gate_rows or []) if in_window(r, since, until)]
    gate_by_cycle, _gate_unjoined = attribute(gate_in, ended)
    closes_by_ctx = journal_by_context(journal_rows)
    ats = sorted(filter(None, (cw.parse_ts(r.get("at")) for r in trace_rows)))
    return {
        "window": {"since": since.isoformat() if since else None,
                   "until": until.isoformat() if until else None,
                   "first_row": ats[0].isoformat() if ats else None,
                   "last_row": ats[-1].isoformat() if ats else None},
        "coverage": {
            "rows": len(trace_rows),
            "by_via": dict(Counter(r.get("via") for r in trace_rows)),
            "full_92_by_source": dict(Counter(r.get("source") for r in trace_rows if is_full_92(r))),
            "early_by_reason": dict(Counter(r["early"] for r in trace_rows if r.get("early"))),
            "errors": dict(Counter(json.dumps(r["error"]) for r in trace_rows if r.get("error"))),
            # Graduated trust, Phase 1: every full _92 row carries `dropped` ([] = checked, none
            # withheld). Full rows WITHOUT the key predate Phase 1 and are counted apart, never as 0.
            "full_92_with_dropped_field": sum(1 for r in trace_rows if is_full_92(r) and "dropped" in r),
            "full_92_without_dropped_field": sum(1 for r in trace_rows if is_full_92(r) and "dropped" not in r),
            "dropped_total": sum(len(r.get("dropped") or []) for r in trace_rows),
            "dropped_distinct": len({i for r in trace_rows for i in r.get("dropped") or []}),
            # GT-2a beside it (Fable, 2026-09-25): injected ids whose head showed "source: legacy".
            # Rows without the key predate the field (or ran without the trust helper): apart, not 0.
            "full_92_with_legacy_field": sum(1 for r in trace_rows if is_full_92(r) and "legacy" in r),
            "legacy_total": sum(len(r.get("legacy") or []) for r in trace_rows),
            "injected_on_legacy_rows": sum(len(r.get("ids") or []) for r in trace_rows if "legacy" in r),
        },
        "gate": {"state": ("not read" if gate_rows is None else ("ok" if gate_in else "no events in the window")),
                 **gate_counts(gate_in)},
        "journal_join": "ok" if closes_by_ctx else "unverified: no cycle_close row carries a context_id",
        "cycles": [cycle_summary(e, by_cycle.get(i, []), closes_by_ctx, gate_by_cycle.get(i, []))
                   for i, (t, e) in enumerate(ended)],
        "memories": memory_table(trace_rows, top),
        "unjoined": {"rows": len(unjoined),
                     "by_context": dict(Counter(r.get("context_id") for r in unjoined))},
    }


# ── printing ─────────────────────────────────────────────────────────────────────────────────────

def clip(text, n):
    """At most ~n characters, cut at WHITESPACE only and marked. A mid-token cut can change what a
    number says (a 48-char cut once turned `PS-ANALYZE=216` into `=2`), so a token is kept whole
    or dropped whole. --json prints the full text."""
    text = " ".join(str(text or "").split())
    if len(text) <= n:
        return text
    cut = text.rfind(" ", 0, n + 1)
    if cut <= 0:
        return "[%d chars, no break to cut at]" % len(text)
    return text[:cut] + " ...(+%d chars)" % (len(text) - cut)


def print_report(rep, files):
    w = rep["window"]
    print("RECALL TRACE REPORT")
    for name, st in files.items():
        print("  %-8s %s" % (name, st))
    print("  window   since=%s until=%s | trace rows from %s to %s"
          % (w["since"], w["until"], w["first_row"], w["last_row"]))
    c = rep["coverage"]
    print("\nCOVERAGE (%d rows in the window)" % c["rows"])
    print("  by hook            %s" % c["by_via"])
    print("  full _92 by source %s" % c["full_92_by_source"])
    print("  early returns      %s   <- A17: _92 did not recall; A0's own recall, if any, stood untagged"
          % (c["early_by_reason"] or "none"))
    print("  errors             %s" % (c["errors"] or "none"))
    print("  trust-withheld     %d ids (%d distinct) on %d full rows carrying the field; %d full rows predate it"
          % (c["dropped_total"], c["dropped_distinct"], c["full_92_with_dropped_field"],
             c["full_92_without_dropped_field"]))
    print("  labelled legacy    %d of %d injected ids, on the %d full rows carrying the field"
          % (c["legacy_total"], c["injected_on_legacy_rows"], c["full_92_with_legacy_field"]))
    g = rep["gate"]
    print("  save gate (_19)    %s: refused %s, would-refuse (containment) %d"
          % (g["state"], g["refused"] or "{}", g["would_refuse"]))
    print("\nCYCLES (%d ended in the window; journal join: %s)" % (len(rep["cycles"]), rep["journal_join"]))
    for s in rep["cycles"]:
        print("  #%s %s ctx=%s %s %s elapsed=%ss hb_age=%ss%s"
              % (s["cycle"], s["ended_at"], s["context_id"], s["type"], s["outcome"],
                 s["elapsed_s"], s["heartbeat_age_s"], "  NO-TOOL" if s["no_tool"] else ""))
        print("      rows=%d full_92=%d early=%s memory_load=%d distinct_ids=%d errors=%d sources=%s"
              % (s["rows"], s["full_92"], s["early"] or "{}", s["memory_load"], s["distinct_ids"],
                 s["errors"], s["sources"] or "{}"))
        print("      withheld=%d (%d distinct)  labelled legacy=%s"
              % (s["dropped"], s["dropped_distinct"],
                 ("%d" % s["legacy"]) if s["legacy_rows"] else "n/a (no row carries the field)"))
        g = s["gate"]
        if g["refused"] or g["would_refuse"]:
            print("      save gate: refused %s  would-refuse (containment) %d"
                  % (g["refused"] or "{}", g["would_refuse"]))
        if s["constant_ids"] is not None:
            print("      on every full _92 turn: %s" % (s["constant_ids"] or "none"))
        print("      journal: %s" % (clip(s["activity"], 160) if s["closed"] else "no close row with this context_id"))
    print("\nMOST-RECALLED IDS (top %d)" % len(rep["memories"]))
    for m in rep["memories"]:
        print("  %-24s turns=%-4d contexts=%-3d %s%s"
              % (m["id"], m["turns"], m["contexts"], m["sources"], "  CHARGE-ONLY" if m["charge_only"] else ""))
    u = rep["unjoined"]
    print("\nUNJOINED %d rows (driven chats, or cycles with no ending in the window): %s"
          % (u["rows"], u["by_context"] or "{}"))


def main(argv=None):
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--container", help="read the three files from this container (read-only)")
    ap.add_argument("--trace")
    ap.add_argument("--endings")
    ap.add_argument("--journal")
    ap.add_argument("--gate", help="optional: _19's gate ledger (resave_gate.jsonl)")
    ap.add_argument("--since", help="ISO time; rows at or after it")
    ap.add_argument("--until", help="ISO time; rows before it")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    since, until = cw.parse_ts(a.since), cw.parse_ts(a.until)
    if (a.since and since is None) or (a.until and until is None):
        print("ERROR: --since/--until must be ISO times", file=sys.stderr)
        return EXIT_ERROR

    paths, files = {}, {}
    tmp = None
    if a.container:
        tmp = tempfile.mkdtemp(prefix="recall_trace_")
        for name, cpath in PATHS.items():
            dest = os.path.join(tmp, name + ".jsonl")
            st = fetch(a.container, cpath, dest)
            files[name] = "%s:%s  %s" % (a.container, cpath, st)
            if st.startswith("error"):
                print("ERROR fetching %s: %s" % (name, st), file=sys.stderr)
                return EXIT_ERROR
            paths[name] = dest if st == "ok" else None
    else:
        missing = [n for n in REQUIRED if not getattr(a, n)]
        if missing:
            print("ERROR: give --container, or all of --trace --endings --journal (missing: %s)"
                  % ", ".join(missing), file=sys.stderr)
            return EXIT_ERROR
        for name in PATHS:
            paths[name] = getattr(a, name)
            files[name] = paths[name] or "(not given)"

    loaded = {}
    for name in PATHS:
        rows, repaired, skipped, st = load(paths[name])
        loaded[name] = rows
        files[name] = "%s  [%s: %d rows, %d repaired, %d skipped]" % (files[name], st, len(rows),
                                                                    len(repaired), len(skipped))
    if not loaded["trace"]:
        print("UNVERIFIED: no recall trace rows (%s). The trace is not deployed, the container has "
              "not restarted since it was, or nothing has recalled since. This is not zero recall."
              % files["trace"])
        return EXIT_UNVERIFIED

    gate_rows = loaded["gate"] if paths.get("gate") else ([] if a.container else None)
    rep = build_report(loaded["trace"], loaded["endings"], loaded["journal"], since, until, a.top,
                       gate_rows=gate_rows)
    if a.json:
        rep["files"] = files
        print(json.dumps(rep, indent=2, ensure_ascii=False))
    else:
        print_report(rep, files)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
