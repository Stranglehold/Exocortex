"""
memory_supersede.py — memories about the same fact: one stands, the rest point to it (R1)

WHY THIS EXISTS
---------------
Aporia's store retired restatements, but not changed facts. On 2026-09-23 it held 50 active
"search_library is down" memories hours after the library came back, and the classifier's
contradiction heuristics (_55._is_contradiction) return False on a real down/up pair. They were
built for version divergence and explicit corrections, not availability. Opus's R1 as amended
(A1, A6, A7, A8, A18): memories that name the same SUBJECT KEY are about the same fact, and the
key decides, not their wording.

THE RULE (deterministic; no model call)
---------------------------------------
Among ACTIVE memories sharing a `subject_key`:
  - A probe beats an inference, regardless of time: external_retrieved over agent_inferred (A1).
  - Within the winning source, the newer one stands (A7: `metadata.timestamp`, read as an aware
    time; a naive March-era value is taken as UTC−4, the container's zone then).
  - A user_asserted memory is retired only by a newer user_asserted one. A1 does not say that
    the user's word retires other sources, so when one is present the others are left as they
    are. That case cannot arise for tool_status keys today (A8 keys only probes and the
    backfill); it is flagged for R1b.
Every other member is deprecated with `superseded_by` = the one that stands: a star, not a
chain (A6). Running it twice changes nothing the second time.

WHAT THIS DOES NOT DO
---------------------
- Does not assign keys. A13's status writer and the one-time backfill do; R1b will later.
- Does not delete. Deprecation is metadata, and what honours it is recall: `_92`'s pipeline
  drops `deprecated` for memories and solutions alike (`_92_memory_enhancement.py`, the
  validity filter in its scoring). Where `_92` does not run (a subordinate, no query, a
  pipeline error), A0's base recall stands and does not read the field; neither does A0's
  `memory_load` tool. Those are the A17 gaps, and a superseded memory can still surface there.
- Does not touch memories without a key. The classifier's heuristics still handle those.
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone

CLS_KEY = "classification"
LIN_KEY = "lineage"
USER = "user_asserted"
# A1: a probe beats an inference. Sources not listed rank below both.
SOURCE_RANK = {"external_retrieved": 2, "agent_inferred": 1}
_NAIVE_ZONE = timezone(timedelta(hours=-4))      # A7 revised: naive March-era timestamps


def _meta(doc) -> dict:
    return getattr(doc, "metadata", None) or {}


def _source(doc) -> str:
    return str((_meta(doc).get(CLS_KEY) or {}).get("source") or "")


def _active(doc) -> bool:
    return (_meta(doc).get(CLS_KEY) or {}).get("validity") != "deprecated"


def _id(doc) -> str:
    return str(_meta(doc).get("id") or "")


def saved_at(doc):
    """When the memory was saved, as an aware datetime, or None if it cannot be read."""
    raw = str(_meta(doc).get("timestamp") or "").strip()
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


def _newest(members):
    """The newest by saved_at; unreadable times rank oldest; ties broken by id, so the choice
    is the same on every run."""
    floor = datetime.min.replace(tzinfo=timezone.utc)
    return max(members, key=lambda d: (saved_at(d) or floor, _id(d)))


def pick_winner(members):
    """The memory that stands among `members` (active memories sharing one key)."""
    users = [d for d in members if _source(d) == USER]
    if users:
        return _newest(users)
    top = max(SOURCE_RANK.get(_source(d), 0) for d in members)
    return _newest([d for d in members if SOURCE_RANK.get(_source(d), 0) == top])


def supersede_by_key(docs: dict, now: datetime) -> list:
    """Apply the rule across the store. Returns [(loser_id, winner_id, key), ...] for what it
    deprecated; mutates only the losers' and winners' metadata."""
    groups = defaultdict(list)
    for d in (docs or {}).values():
        key = _meta(d).get("subject_key")
        if key and _active(d) and _id(d):
            groups[key].append(d)

    changes = []
    stamp = now.astimezone(timezone.utc).isoformat()
    for key in sorted(groups):
        members = groups[key]
        if len(members) < 2:
            continue
        winner = pick_winner(members)
        won_user = _source(winner) == USER
        for d in members:
            if d is winner:
                continue
            if (_source(d) == USER) != won_user:
                continue          # the user's word and other sources do not retire each other (A1)
            m = _meta(d)
            m.setdefault(CLS_KEY, {})["validity"] = "deprecated"
            lin = m.setdefault(LIN_KEY, {})
            lin["superseded_by"] = _id(winner)
            lin["deprecated_at"] = stamp
            lin["deprecated_reason"] = "subject_key:%s" % key
            wl = _meta(winner).setdefault(LIN_KEY, {})
            wl.setdefault("supersedes_by_key", [])
            if _id(d) not in wl["supersedes_by_key"]:
                wl["supersedes_by_key"].append(_id(d))
            changes.append((_id(d), _id(winner), key))
    return changes
