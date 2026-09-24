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

No LLM calls. A set of memory ids on the agent's data; every function degrades to a no-op.
"""

RECALLED_KEY = "_recalled_memory_ids"


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
