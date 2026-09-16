#!/usr/bin/env python3
"""cycle_windows.py — the ONE module that says which cycle rows count, shared by the Office pane's endpoint
(office_feed.py, in the container), Fable's measure_windows.py and Kestrel's accept_step0_loop.py.

Why one module (Kestrel, 2026-09-14): "which rows count" existed in two scripts and the pane would be the third; three
implementations of one rule is how 33-vs-31 happened and how the May epoch got selected. Both halves import one module,
including the literals, so a correction lands once. Pure stdlib, no hardcoded paths: every function takes rows or a
path. Deployed copy lives in the plugin tree (plugins/_exocortex/helpers/cycle_windows.py); the repo copy is this file's
twin; md5 across both is the deploy check.

Rules encoded here, each learned the hard way today:
  R1  journal.jsonl is not strictly JSONL: a reader reports repaired and skipped lines beside every total, never drops
      them silently; a skipped cycle_close makes the totals UNVERIFIED.
  R2  cycle_number is NOT a key (1,300 distinct values in 1,673 closes; reset from above 1383 at least twice; 574 exists
      dated May). Windows are FILTERS on parsed time (and number as a secondary bound), never positional slices; the
      N are taken by sorted time inside the filter.
  R3  timestamps are not monotonic in the file and their formats are mixed (Z / +00:00 / microseconds): parse to
      aware datetimes; a row with an unparseable timestamp is counted and reported, never silently excluded.
  R4  context_id is the join key between the watcher's cycle_endings.jsonl and the journal; never the number.
  R5  verify_flag has two shapes (flat pages object before 2026-09-14; dict keyed by check after); a reader accepts both.
  R6  the caps are the watcher's: STALL_CAP_S = 900 (no heartbeat progress), HUNG_CAP_S = 3600 (wall clock). They are
      parameters with these defaults so office_feed can pass the watcher's live values.
"""
import json
import re
from datetime import datetime, timezone

STALL_CAP_S = 900
HUNG_CAP_S = 3600
RECEIPT = re.compile(r"\bq=")
# (memory-tool calls per cycle come from methodology_tracker.jsonl, not the journal; no regex for them lives here)
JOIN_MAX = 3


# ── reading ──────────────────────────────────────────────────────────────────────────────────────────────────────────

def read_jsonl(path):
    """Return (rows, repaired, skipped). repaired: [(line_no, lines_joined)]; skipped: [line_no]. Never raises on a bad
    line; a bad line is joined with up to JOIN_MAX following lines before it is skipped. (R1)"""
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except FileNotFoundError:
        return [], [], []
    lines = text.split("\n")
    rows, repaired, skipped, i = [], [], [], 0
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        try:
            rows.append(json.loads(s, strict=False)); i += 1; continue
        except Exception:
            pass
        joined, ok = s, False
        for k in range(1, JOIN_MAX + 1):
            if i + k >= len(lines):
                break
            joined = joined + "\n" + lines[i + k]
            try:
                rows.append(json.loads(joined, strict=False)); repaired.append((i + 1, k + 1)); i += k + 1; ok = True; break
            except Exception:
                continue
        if not ok:
            skipped.append(i + 1); i += 1
    return rows, repaired, skipped


def parse_ts(value):
    """Aware datetime from an ISO string with Z or an offset, or from an epoch number; None if unparseable. (R3)"""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    s = str(value)
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        d = datetime.fromisoformat(s)
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def closes(rows):
    return [r for r in rows if isinstance(r, dict) and r.get("type") == "cycle_close"]


def verify_flag(row):
    """Both shapes (R5): returns {"pages_deepened": {...}?, "syntheses": {...}?}."""
    v = row.get("verify_flag")
    if not isinstance(v, dict):
        return {}
    if "claimed" in v and "actual_writes" in v:     # the flat pre-2026-09-14 pages object
        return {"pages_deepened": v}
    return v


# ── windows ──────────────────────────────────────────────────────────────────────────────────────────────────────────

def window(rows, n=20, before=None, after=None, min_cycle=None, max_cycle=None):
    """The n closes nearest the boundary, chosen by PARSED TIME inside a filter (R2, R3).
    before: aware datetime; take the n latest closes strictly before it.
    after:  aware datetime; take the n earliest closes at or after it.
    min_cycle / max_cycle: secondary bounds on cycle_number (never the primary key).
    Returns (selected_rows, undated_count)."""
    dated, undated = [], 0
    for r in closes(rows):
        t = parse_ts(r.get("timestamp"))
        if t is None:
            undated += 1; continue
        c = r.get("cycle_number")
        try:
            c = int(c)
        except (TypeError, ValueError):
            c = None
        if min_cycle is not None and (c is None or c < min_cycle):
            continue
        if max_cycle is not None and (c is None or c > max_cycle):
            continue
        if before is not None and not (t < before):
            continue
        if after is not None and not (t >= after):
            continue
        dated.append((t, r))
    dated.sort(key=lambda x: x[0])
    sel = dated[-n:] if before is not None or after is None else dated[:n]
    return [r for _, r in sel], undated


def summarize(rows):
    """The ledger columns for a set of close rows. Every number here is from the rows, none from memory of them."""
    types = {}
    for r in rows:
        types[r.get("cycle_type")] = types.get(r.get("cycle_type"), 0) + 1
    m = [r for r in rows if r.get("cycle_type") == "MAINTAIN"]
    b = [r for r in rows if r.get("cycle_type") == "BUILD"]
    s = [r for r in rows if r.get("cycle_type") == "SYNTHESIZE"]
    ival = lambda r, k: int(r.get(k, 0) or 0)
    return {
        "n": len(rows),
        "types": types,
        "maintain_empty": sum(1 for r in m if ival(r, "sleep_findings") == 0),
        "maintain": len(m),
        "build_with_pages": sum(1 for r in b if ival(r, "pages_deepened") > 0),
        "build": len(b),
        "skills": sum(ival(r, "skills_captured") for r in rows),
        "memories_by_type": {t: sum(ival(r, "memories_saved") for r in rows if r.get("cycle_type") == t) for t in sorted(k for k in types if k)},
        "syntheses_rows": len(s),
        "syntheses_kept": sum(ival(r, "syntheses") for r in s),
        "syntheses_gated": sum(1 for r in s if verify_flag(r).get("syntheses")),
        "syntheses_pages_exist": sum(1 for r in s if r.get("page_exists")),
        "widths": [r.get("builds_on_width_slugs") for r in s],
        "receipts": sum(1 for r in rows if RECEIPT.search(str(r.get("activity", "")))),
        "first": rows[0].get("timestamp") if rows else None,
        "last": rows[-1].get("timestamp") if rows else None,
        "cycle_numbers": [r.get("cycle_number") for r in rows],
    }


# ── endings: the watcher's file, joined by context_id (R4) ───────────────────────────────────────────────────────────

def endings_span(endings, close_rows, since=None, until=None):
    """Given cycle_endings.jsonl rows and journal closes, return the denominator for a time span:
    fired, ended-by-outcome, closed (a close row whose context_id matches an ending), and the lost list.
    Join on context_id only. Rows without one are counted under 'unjoinable', never guessed."""
    def in_span(r):
        t = parse_ts(r.get("at") or r.get("timestamp"))
        if t is None:
            return False
        if since is not None and t < since:
            return False
        if until is not None and t >= until:
            return False
        return True
    fired = [r for r in endings if r.get("event") == "fired" and in_span(r)]
    ended = [r for r in endings if r.get("event") == "ended" and in_span(r)]
    by_ctx = {}
    for r in close_rows:
        cid = r.get("context_id")
        if cid:
            by_ctx[cid] = r
    outcomes = {}
    lost = []
    for r in ended:
        o = r.get("outcome") or "unknown"
        outcomes[o] = outcomes.get(o, 0) + 1
        if o != "completed":
            lost.append({"cycle": r.get("cycle"), "context_id": r.get("context_id"), "outcome": o, "reason": r.get("reason"), "at": r.get("at")})
    unjoinable = sum(1 for r in ended if not r.get("context_id"))
    if not by_ctx:
        # An empty join table and a genuinely unclosed span are different facts (Kestrel, 2026-09-14): before the
        # close script wrote context_id into journal rows, this would have read 0 forever and looked correct.
        closed, state, reason = None, "unverified", "no journal row in the span carries a context_id; the join cannot run"
    else:
        closed, state, reason = sum(1 for r in ended if r.get("context_id") in by_ctx), "ok", None
    return {"fired": len(fired), "ended": len(ended), "outcomes": outcomes, "closed_joined": closed,
            "closed_joined_state": state, "closed_joined_reason": reason, "lost": lost, "unjoinable": unjoinable}


# ── the running cycle against its bands (R6) ─────────────────────────────────────────────────────────────────────────

def now_zone(engine_state, now=None, stall_cap_s=None, hung_cap_s=None):
    """From engine_state.json: elapsed and heartbeat ages with their bands, and the watcher's next action stated as fact.
    Caps: the running watcher's own, which it writes into engine_state.json as {"caps": {"stall_s", "hung_s"}} at
    startup (contract 6.1); explicit arguments override; the module defaults are a last resort and are reported as
    such in caps_source, because a cap change in the watcher must not leave the pane stating a stale next action."""
    now = now or datetime.now(timezone.utc)
    caps = engine_state.get("caps") if isinstance(engine_state.get("caps"), dict) else {}
    if stall_cap_s is None:
        stall_cap_s = caps.get("stall_s", STALL_CAP_S)
    if hung_cap_s is None:
        hung_cap_s = caps.get("hung_s", HUNG_CAP_S)
    caps_source = "argument" if (engine_state.get("caps") is None and (stall_cap_s != STALL_CAP_S or hung_cap_s != HUNG_CAP_S)) else ("engine_state" if caps else "module_default")
    active = bool(engine_state.get("cycle_active"))
    started = parse_ts(engine_state.get("last_cycle_start"))
    beat = parse_ts(engine_state.get("cycle_heartbeat"))
    out = {"active": active, "cycle": engine_state.get("cycle_count"), "type": engine_state.get("last_cycle_type"),
           "context_id": engine_state.get("cycle_context_id") or None,
           "started_at": started.isoformat() if started else None,
           "elapsed_s": int((now - started).total_seconds()) if started else None,
           "heartbeat_age_s": int((now - beat).total_seconds()) if beat else None,
           "stall_cap_s": stall_cap_s, "hung_cap_s": hung_cap_s, "caps_source": caps_source, "next_action": None}
    if active and out["heartbeat_age_s"] is not None:
        left = stall_cap_s - out["heartbeat_age_s"]
        if left <= 0:
            out["next_action"] = "reap due (no heartbeat past the stall cap)"
        elif left <= 300:
            out["next_action"] = f"reap due in {left // 60} min if no heartbeat"
    if active and out["elapsed_s"] is not None and out["elapsed_s"] >= hung_cap_s:
        out["next_action"] = "reap due (past the hung cap)"
    return out
