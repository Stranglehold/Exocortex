"""
_36_status_writer.py — a probe's result becomes one keyed status memory (A13)

Hook: tool_execute_after (fires only for tool calls that executed)

WHY
---
Nothing turned a probe into memory. When #738 verified the library on 2026-09-23 at 19:05Z
("search_library CONFIRMED UP (list_collections 526 books/878k chunks)"), that went into the
journal only. The store kept 50 active "search_library is down" memories written from recall,
and #739 saved another at 19:37Z. Opus's A13: a deterministic writer at the tool return, so the
newest thing the store knows about a tool's status is what a probe last saw. R1 (A18: a keyed
branch in _55) then retires the older ones by subject key.

WHAT IT WRITES
--------------
One memory per observation, for example:
  "search_library operational: list_collections returned humble_bundle (526 books, 878,152
   chunks). Observed 2026-09-23T19:05:02Z."
metadata: subject_key tool_status:<subject>, volatility state_observation, observed_at (UTC),
status up|down, probe_tool; classification source external_retrieved, validity inferred (R2:
a tool return is evidence, not confirmation); lineage created_by status_writer. The
classification is set here, so _55 does not re-derive it.

HOW STATUS IS READ (deterministic, from the return value; no model call)
------------------------------------------------------------------------
  list_collections  a collection with chunks > 0 → up; "collections": [] → down.
  search_library    at least one result → up. Zero results: the server's own note decides,
                    "collections available: none built" → down, a listed collection → up
                    (the library answered; the query matched nothing). Zero results with no
                    note → no observation, because that reply cannot tell the two apart.
  either            a reply that is an error (not JSON, and reads as an error) → down,
                    worded "unreachable (…)" so a reader can tell an infrastructure failure
                    from an empty library.
Debounce (A13): an active memory with the same key and status, observed less than
`debounce_minutes` ago, means this observation adds nothing, so it is skipped.

WHAT IT DOES NOT DO
-------------------
- Does not supersede older status memories. That is R1.
- Reads only the configured probe tools. A new tool is a config entry.
- No LLM calls.
"""

import json
import re
from datetime import datetime, timedelta, timezone

from helpers.extension import Extension
from plugins._memory.helpers.memory import Memory

CONFIG_PATH = "/a0/usr/plugins/_exocortex/config/config.json"   # section "status_writer"
CLS_KEY = "classification"
LIN_KEY = "lineage"

DEFAULTS = {
    "enabled": True,
    "debounce_minutes": 60,
    # A0 tool name -> what the probe observes, and how to read its reply.
    "probes": {
        "exocortex_memory.list_collections": {"subject": "search_library", "kind": "collections"},
        "exocortex_memory.search_library": {"subject": "search_library", "kind": "results"},
    },
}

_ERROR = re.compile(r"\b(error|exception|traceback|not found|failed|timed? ?out|refused|unreachable|"
                    r"connection|unavailable)\b", re.I)


def cfg() -> dict:
    """The status_writer section over DEFAULTS; a missing or bad section means DEFAULTS."""
    try:
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            c = json.load(fh).get("status_writer", {})
    except Exception:
        c = {}
    return {**DEFAULTS, **(c if isinstance(c, dict) else {})}


def _first_json(text: str):
    """The first JSON object in the reply, or None. A0 may add context after the tool output."""
    s = text or ""
    i = s.find("{")
    if i < 0:
        return None
    try:
        obj, _end = json.JSONDecoder().raw_decode(s[i:])
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def read_status(kind: str, probe: str, reply: str):
    """(status, detail) from a probe's reply, or None when the reply says nothing about
    availability. Deterministic."""
    obj = _first_json(reply)
    short = probe.split(".")[-1]
    if obj is None:
        head = " ".join((reply or "").split())[:140]
        if head and _ERROR.search(head):
            return "down", "%s unreachable (%s)" % (short, head)
        return None

    if kind == "collections":
        cols = obj.get("collections")
        if not isinstance(cols, list):
            return None
        live = [c for c in cols if isinstance(c, dict) and int(c.get("chunks") or 0) > 0]
        if live:
            parts = ["%s (%s books, %s chunks)" % (c.get("collection"), format(int(c.get("books") or 0), ","),
                                                    format(int(c.get("chunks") or 0), ",")) for c in live]
            return "up", "%s returned %s" % (short, "; ".join(parts))
        return "down", "%s returned no collections" % short

    if kind == "results":
        res = obj.get("results")
        if not isinstance(res, list):
            return None
        if res:
            return "up", "%s returned %d result%s" % (short, len(res), "" if len(res) == 1 else "s")
        note = str(obj.get("note") or "")
        if "none built" in note:
            return "down", "%s: no library collections built (%s)" % (short, note[:120])
        if "collections available" in note:
            return "up", "%s answered with no match; %s" % (short, note[:120])
        return None
    return None


def _parse_time(value):
    try:
        t = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return t if t.tzinfo else None
    except Exception:
        return None


def recent_duplicate(docs: dict, key: str, status: str, now: datetime, minutes: float) -> bool:
    """An active memory with this key and status observed within the debounce window."""
    for d in (docs or {}).values():
        m = getattr(d, "metadata", None) or {}
        if m.get("subject_key") != key or m.get("status") != status:
            continue
        if (m.get(CLS_KEY) or {}).get("validity") == "deprecated":
            continue
        seen = _parse_time(m.get("observed_at"))
        if seen and now - seen < timedelta(minutes=minutes):
            return True
    return False


def build_memory(subject: str, probe: str, status: str, detail: str, now: datetime):
    """(text, metadata) for one observation."""
    at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    word = "operational" if status == "up" else "unavailable"
    text = "%s %s: %s. Observed %s." % (subject, word, detail, at)
    metadata = {
        "area": Memory.Area.MAIN.value,
        "subject_key": "tool_status:%s" % subject,
        "volatility": "state_observation",
        "observed_at": at,
        "status": status,
        "probe_tool": probe,
        CLS_KEY: {
            "validity": "inferred",
            "relevance": "active",
            "utility": "tactical",
            "source": "external_retrieved",
            "relational_salience": "task_transient",
        },
        LIN_KEY: {
            "created_at": now.isoformat(),
            "created_by_role": None,
            "bst_domain": "",
            "classified_at_cycle": 0,
            "supersedes": None,
            "superseded_by": None,
            "access_count": 0,
            "last_accessed": None,
            "created_by": "status_writer",
        },
    }
    return text, metadata


class StatusWriter(Extension):
    """tool_execute_after: a configured probe's reply becomes one keyed status memory."""

    def _log(self, msg: str) -> None:
        print("[STATUS-WRITER] %s" % msg, flush=True)

    async def execute(self, response=None, **kwargs) -> None:
        try:
            conf = cfg()
            if not conf.get("enabled", True):
                return
            probe = kwargs.get("tool_name") or ""
            spec = (conf.get("probes") or {}).get(probe)
            if not spec:
                return
            read = read_status(spec.get("kind", ""), probe, getattr(response, "message", "") or "")
            if not read:
                return
            status, detail = read
            subject = spec.get("subject") or probe
            now = datetime.now(timezone.utc)

            db = await Memory.get(self.agent)
            docs = db.db.get_all_docs() if db and db.db else {}
            key = "tool_status:%s" % subject
            if recent_duplicate(docs, key, status, now, float(conf.get("debounce_minutes", 60))):
                self._log("%s %s already observed within the debounce window — skipped" % (key, status))
                return
            text, metadata = build_memory(subject, probe, status, detail, now)
            await db.insert_text(text, metadata)
            self._log("%s = %s (%s)" % (key, status, detail[:80]))
        except Exception as e:
            try:
                self._log("skipped — %s: %s" % (type(e).__name__, str(e)[:100]))
            except Exception:
                pass
