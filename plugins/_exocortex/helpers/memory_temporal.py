"""
memory_temporal.py — how old a recalled observation is, said at recall (R3)

WHY THIS EXISTS
---------------
A state observation is true when it was made, not necessarily now. On 2026-09-23 Aporia's store
held 50 active "search_library is down" memories hours after the library came back, and recall
served them with a save date and nothing else: no sign they were a day old, none that a newer
observation of the library existed. Opus's R3 (memory lifecycle design note, R3; rulings of
2026-09-23 on the 19 incidental mentions): memories carry `observed_at`; keyed memories carry a
volatility class; retrieval says when an observation is old, and when a newer one exists.

THE RULES (deterministic; no model call)
----------------------------------------
- volatility: a keyed memory without one takes its key's default: tool_status:* and
  engine_state:* are `state_observation`. Other keys get none here; R1b will propose them.
- observed_at: an aware UTC ISO time, written when a memory is first written or classified.
  A13 stamps the probe time; _52 and _53 stamp their insert; _55 stamps what it classifies
  (memory_save, A0's fragments and solutions) from the memory's own `timestamp`. A fragment
  that A0's consolidator merged carries the merge time: when that version came to exist
  (accepted, 2026-09-23).
- the stale frame: a `state_observation` memory older than `stale_hours` for its key pattern
  is served with "observed N hours ago; may no longer be current". Defaults: 24 for
  tool_status: and engine_state:, 24 for anything else; configurable in
  classification_config.json under memory_lifecycle.stale_hours. Without `observed_at` its save
  time is used and named as such; with neither, the frame says the time is unknown.
- the subject-mention frame: an UNKEYED memory whose text contains a keyed subject (the part
  of the key after the colon, case-insensitive), served while the store holds an ACTIVE keyed
  memory for that subject observed AFTER the framed memory was saved, is served with
  "mentions <subject>; a newer observation exists: <status>, observed N hours ago". One clause
  per subject. No newer observation, no frame.

A8 ruled text matching out for SUPERSESSION, which retires memories on their wording. Here a
match only adds an age label at render time, so a false match costs a label, not a memory.

WHAT THIS DOES NOT DO
---------------------
- Does not change `page_content`. The frames are rendered by _92._with_provenance only; a
  frame that reached the store would be recalled and framed again.
- Does not retire anything (R1) or assign keys (A13, the backfill, R1b).
- Does not backfill `observed_at` onto existing memories. Forward-only.
"""

from datetime import datetime, timedelta, timezone

CLS_KEY = "classification"
STATE = "state_observation"
# R3: "The deterministic extractors from R1 set the volatility class automatically".
VOLATILITY_BY_PREFIX = (("tool_status:", STATE), ("engine_state:", STATE))
# R3: "default: 24h for tool status, configurable". Per-prefix, with a default for the rest.
DEFAULT_STALE_HOURS = {"tool_status:": 24, "engine_state:": 24, "default": 24}
_NAIVE_ZONE = timezone(timedelta(hours=-4))      # A7: naive March-era timestamps are UTC-4


def _meta(doc) -> dict:
    return getattr(doc, "metadata", None) or {}


def _active(doc) -> bool:
    return (_meta(doc).get(CLS_KEY) or {}).get("validity") != "deprecated"


def parse_time(raw):
    """An aware datetime from a stored time, or None. The same reading as R1's saved_at (A7):
    ISO with an offset as written; a naive value is taken as UTC-4."""
    raw = str(raw or "").strip()
    if not raw:
        return None
    try:
        t = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        try:
            t = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    return t if t.tzinfo else t.replace(tzinfo=_NAIVE_ZONE)


def utc_iso(t: datetime) -> str:
    return t.astimezone(timezone.utc).isoformat()


def observed_at_for(doc, now: datetime) -> str:
    """What _55 stamps on a memory it classifies: its own save time, else now."""
    t = parse_time(_meta(doc).get("timestamp"))
    return utc_iso(t or now)


def volatility_for_key(key) -> str | None:
    key = str(key or "")
    for prefix, cls in VOLATILITY_BY_PREFIX:
        if key.startswith(prefix):
            return cls
    return None


def ensure_volatility(docs: dict) -> list:
    """Give each active keyed memory without a volatility class its key's default.
    Returns the ids changed; a second call returns []."""
    changed = []
    for d in (docs or {}).values():
        m = _meta(d)
        key = m.get("subject_key")
        if not key or m.get("volatility") or not _active(d):
            continue
        cls = volatility_for_key(key)
        if cls:
            m["volatility"] = cls
            changed.append(str(m.get("id") or ""))
    return changed


def stale_hours(key, config: dict | None) -> float:
    table = dict(DEFAULT_STALE_HOURS)
    try:
        table.update(((config or {}).get("memory_lifecycle") or {}).get("stale_hours") or {})
    except Exception:
        pass
    key = str(key or "")
    # The longest matching prefix wins, so "tool_status:search_library" can override "tool_status:".
    for prefix in sorted((p for p in table if p != "default"), key=len, reverse=True):
        if key.startswith(prefix):
            return float(table[prefix])
    return float(table.get("default", 24))


def age_text(then: datetime, now: datetime) -> str:
    """'N minutes' under an hour, 'N hours' under two days, then 'N days'. Floors, never rounds
    up: an observation is never reported younger than it is."""
    secs = max(0.0, (now - then).total_seconds())
    if secs < 3600:
        n, unit = int(secs // 60), "minute"
    elif secs < 48 * 3600:
        n, unit = int(secs // 3600), "hour"
    else:
        n, unit = int(secs // 86400), "day"
    return "%d %s%s" % (n, unit, "" if n == 1 else "s")


def stale_clause(doc, now: datetime, config: dict | None = None) -> str:
    """The stale frame for a state observation past its threshold, else ''."""
    m = _meta(doc)
    if m.get("volatility") != STATE:
        return ""
    limit = stale_hours(m.get("subject_key"), config)
    seen = parse_time(m.get("observed_at"))
    if seen is not None:
        if (now - seen).total_seconds() <= limit * 3600:
            return ""
        return "observed %s ago; may no longer be current" % age_text(seen, now)
    saved = parse_time(m.get("timestamp"))
    if saved is not None:
        if (now - saved).total_seconds() <= limit * 3600:
            return ""
        return "saved %s ago, observation time unrecorded; may no longer be current" % age_text(saved, now)
    return "observation time unknown; may no longer be current"


def subject_of(key) -> str:
    key = str(key or "")
    return key.split(":", 1)[1].strip() if ":" in key else ""


def _when(doc):
    m = _meta(doc)
    return parse_time(m.get("observed_at")) or parse_time(m.get("timestamp"))


def current_observations(docs: dict) -> dict:
    """{subject_key: the newest ACTIVE keyed memory for it}. One pass over the store."""
    floor = datetime.min.replace(tzinfo=timezone.utc)
    best = {}
    for d in (docs or {}).values():
        m = _meta(d)
        key = m.get("subject_key")
        if not key or not subject_of(key) or not _active(d):
            continue
        cur = best.get(key)
        if cur is None or (_when(d) or floor) > (_when(cur) or floor):
            best[key] = d
    return best


def subject_clauses(doc, observations: dict, now: datetime) -> list:
    """The subject-mention frame for an UNKEYED memory: one clause per keyed subject its text
    names, where that subject's current observation was made after this memory was saved."""
    m = _meta(doc)
    if m.get("subject_key"):
        return []
    text = (getattr(doc, "page_content", "") or "").lower()
    mine = _when(doc)
    out = []
    for key in sorted(observations or {}):
        subject = subject_of(key)
        if not subject or subject.lower() not in text:
            continue
        obs = observations[key]
        seen = _when(obs)
        if seen is None or mine is None or seen <= mine:
            continue
        status = str(_meta(obs).get("status") or "").strip()
        out.append("mentions %s; a newer observation exists: %sobserved %s ago"
                   % (subject, (status + ", ") if status else "", age_text(seen, now)))
    return out


def frame_clauses(doc, observations: dict, now: datetime, config: dict | None = None) -> list:
    """Every R3 clause for one recalled memory, stale frame first."""
    out = []
    s = stale_clause(doc, now, config)
    if s:
        out.append(s)
    out.extend(subject_clauses(doc, observations, now))
    return out
