"""
memory_recall_tag.py — which memories were recalled into the current monologue (R4)

WHY THIS EXISTS
---------------
Recall re-seeds the store. A memory recalled into a cycle gets saved again as if it were new
evidence, and each re-save makes the next recall of it more likely.
  - 09-08, Fable's third carrier of the 09-02 belief: status memories recalled into each
    MAINTAIN cycle were written again through memory_save, keeping the belief alive.
  - 2026-09-23 19:37:52Z: "search_library still down this cycle" was saved at the end of #739,
    after #738 had confirmed the library up at 19:05Z.

Opus's ruling (memory lifecycle design note, R4 + A11): the injectors mark what they recall;
the writers (the memory_save gate, then _52 as defence in depth) refuse to re-save it. This
module is the one place the key and its meaning live, so the markers and the readers cannot
drift apart. The same pattern as OP_SIG_KEY in failure_fingerprint.py.

SCOPE: ONE MONOLOGUE
--------------------
`reset()` runs at monologue_start. The injectors call `tag()` as they inject during the message
loop. The writers read `recalled()` during the monologue (memory_save) and at monologue_end
(_52), so the set has to span the whole monologue, not one loop iteration.

WHAT THIS DOES NOT DO
---------------------
- It does not refuse anything. It only records. The refusal is the writers' job.
- It does not cover A0's own recall (_50/_91): that injects plain text with no ids, and stands
  untagged whenever _92 returns early (subordinate contexts, no db, no query). Accepted as a
  bounded gap in the design note (A17); covering it would mean patching A0 core (DEC-030).

WHO CALLS tag()
---------------
- _92_memory_enhancement (message_loop_prompts_after): everything it injects, memories and
  solutions. It writes the prompt's memories block last, so this is what the model sees.
- _55_memory_relevance_filter: the same call, inside its injection path. Inert while it is
  retired by config.
- tool_execute_after/_35_recall_tag_memory_load: the ids in the memory_load tool's output.

WHO CALLS trace() (the persistent per-turn ledger, state/recall_trace.jsonl; 2026-09-24)
------------------------------------------------------------------------------------------
- _92_memory_enhancement: one row per call, early returns included (the A17 gap as a count).
- _35_recall_tag_memory_load: one row per memory_load call, `ids: []` included.
- _55 does NOT: it is retired by config. Re-enabling it without adding a trace() call would put
  recall into the prompt that the ledger cannot see.
Read by scripts/recall_trace_report.py, which joins it to cycle_endings.jsonl by context_id.
!! This module is imported by bare name: an edit is live only after a container restart.

No LLM calls. A set of memory ids on the agent's data; every function degrades to a no-op.
"""

import json
import os
import threading
from datetime import datetime, timezone

RECALLED_KEY = "_recalled_memory_ids"

# ── Recall trace (2026-09-24; build order approved by Jake, refinements by Opus and Fable) ──────
# tag() (below) feeds the re-save gate for ONE monologue and is never persisted, so a false
# conclusion could not be traced to the memory that fed it: cycle #731 journaled "search_library
# down" from a recalled memory with no probe run, and it was found by hand in chat.json. trace()
# is the persistent ledger an instrument joins to the daemon's cycle_endings.jsonl (by context id)
# and to her journal. The overridable path exists for tests; production uses the plugin state dir.
TRACE_PATH = os.environ.get("EXO_RECALL_TRACE_PATH", "/a0/usr/plugins/_exocortex/state/recall_trace.jsonl")
_TRACE_LOCK = threading.Lock()


def trace(agent, ids, via, turn=None, source=None, early=None, error=None, dropped=None) -> bool:
    """Append one row: the memory ids recalled into THIS turn, by which hook, from which query source.

    PER TURN, not per monologue: a memory recalled on turn 1 and again on turn 7 appears on both
    rows, so its arrival can be read against the turn a conclusion was written on. `turn` is A0's
    loop_data.iteration: 0-based, and it restarts with each monologue, so order rows by `at`.
    An EMPTY `ids` is recorded too: `ids: []` means the hook ran and recalled nothing. `early`
    names why a hook returned before recalling (subordinate, no_db, no_docs, no_query, exception);
    on such a turn A0's own untagged recall stands, which is the A17 gap, and a row per such turn
    makes the gap a number. `error` names what failed on a run that did not return early (e.g. the
    pipelines that raised). `source` is recall_query's class (recent_work / idle_charge /
    user_message) or the tool that recalled. `dropped` (graduated trust, Phase 1) lists candidates
    the trust verdict withheld (helpers/memory_trust.py). _92 passes it on EVERY full run, so
    `dropped: []` means "checked, none withheld", while a row without the key is an early return,
    a memory_load row, or a row written before Phase 1.

    Never raises: a failed write is printed, so an untraced turn is visible rather than silent.
    """
    try:
        ctx = getattr(getattr(agent, "context", None), "id", None)
        row = {"at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "context_id": ctx, "agent": getattr(agent, "number", None), "turn": turn,
               "via": via, "source": source,
               "ids": sorted({str(i) for i in (ids or []) if i})}
        if early:
            row["early"] = early
        if error:
            row["error"] = error
        if dropped is not None:
            row["dropped"] = sorted({str(i) for i in dropped if i})
        d = os.path.dirname(TRACE_PATH)
        if d:
            os.makedirs(d, exist_ok=True)
        line = json.dumps(row, ensure_ascii=False) + "\n"
        with _TRACE_LOCK:
            with open(TRACE_PATH, "a", encoding="utf-8") as fh:
                fh.write(line)
        return True
    except Exception as e:
        print("[RECALL-TRACE] write failed (%s: %s); this turn is untraced" % (type(e).__name__, e),
              flush=True)
        return False


def reset(agent) -> bool:
    """Start a monologue with nothing recalled. False if the agent's data could not be written."""
    try:
        agent.set_data(RECALLED_KEY, set())
        return True
    except Exception:
        return False


def tag(agent, ids) -> int:
    """Add recalled memory ids. Returns the set's size afterwards, or -1 if it could not be written."""
    try:
        cur = agent.get_data(RECALLED_KEY)
        s = set(cur) if isinstance(cur, (set, frozenset, list, tuple)) else set()
        s.update(str(i) for i in (ids or []) if i)
        agent.set_data(RECALLED_KEY, s)
        return len(s)
    except Exception:
        return -1


def recalled(agent) -> frozenset:
    """The ids recalled so far this monologue. Empty if nothing was recorded or it cannot be read."""
    try:
        cur = agent.get_data(RECALLED_KEY)
        return frozenset(cur) if isinstance(cur, (set, frozenset, list, tuple)) else frozenset()
    except Exception:
        return frozenset()
