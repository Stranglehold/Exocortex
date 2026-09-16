"""
attendedness.py — is this turn being watched by a human, or is it an idle cycle?

ONE implementation, imported by every extension that needs the answer. Lifted verbatim from
`_07_recovery_gate`'s methods on 2026-09-15 when `_10_plaintext_response_fallback` needed the
same question answered: a rule that lives in two files is free to drift, and the drift is
silent because both copies keep working until the day they disagree.

THE FAIL-CLOSED RULE
--------------------
If attendedness cannot be positively determined, the turn is UNATTENDED. Reading a state key to
decide whether to guard means that if the key is absent, renamed, or reshaped, the guard
silently does nothing in exactly the case it exists for — the severed-consumer defect, applied
to the guard against it.

    The file can only ever confirm UNATTENDED. It can never confirm ATTENDED.

"Present and wrong" is why. `idle_watch.py` fires first and writes second, so a failed write —
or a daemon dying between the two — leaves the previous cycle's id in `engine_state.json`.
Verified live 2026-09-10: the file held `cycle_context_id: "TrPI3dyd"` while that chat was
already gone from disk. A gate keyed on that file alone would have failed open on every turn
that day. The primary signal is therefore the in-process marker set by `api/idle_cycle.py`,
which has no file, no daemon and no window.

The marker is a DICT, never a boolean, and this reads PRESENCE of the key — never `is True`.

THE ASYMMETRY THAT JUSTIFIES THE DEFAULT — and the third case, which is evidence, not argument
---------------------------------------------------------------------------------------------
A driven turn misread as idle costs one nudge and one extra turn: visible and recoverable.
An idle cycle misread as driven executes recovered garbage unattended.

And, measured on 2026-09-15 by cycle 578 — the first SYNTHESIZE this system ever ran — a third
case, worse than either: an idle cycle misread as driven SILENTLY DISCARDS COMPLETED WORK. She
wrote a genuine synthesis joining two distinct sources, then described her remaining steps in
prose; `_10` wrapped that description as a final `response`, which ends the task. The page
survived on disk. The index entry, the candidate questions, the memory, and the close did not.
Every counter in the system reported that nothing happened, while the artifact sat there.

That is not a hypothetical about garbage. It is the strongest argument for failing closed that
this project has, and it arrived as an observation rather than an argument.
"""

import json

IDLE_MARKER_KEY = "idle_cycle"
# MUST match helpers/parallel_tools.py:21 PARALLEL_WORKER_PARENT_CONTEXT_KEY exactly.
# I transcribed this as "_parent_context_id" on 2026-09-15 and shipped it: the walk then
# finds no parent, falls through to the file, the file names the PARENT's context, and a
# parallel worker inside an idle cycle reads ATTENDED -- both guards stop vetoing in the
# exact case they exist for. The differential control passed because none of its five
# scenarios walked a parent chain.
PARENT_CONTEXT_KEY = "_parallel_parent_context_id"
MAX_PARENT_HOPS = 8
ENGINE_STATE = "/a0/usr/workdir/workspace/office/engine_state.json"

ATTENDED = "attended"
UNATTENDED = "unattended"
UNDETERMINED = "undetermined"

#: Observations that must NOT be treated as a watched turn. Both veto, and callers should test
#: against this rather than `== UNATTENDED`, so a future fourth observation is handled by
#: whoever adds it instead of silently falling into the attended branch.
VETOES = (UNATTENDED, UNDETERMINED)


def marker(agent):
    """(marker, walk_fault). The idle marker, or None. Presence is the signal, not the value.

    Walks up the parallel-worker parent chain, bounded, so a child inherits its parent cycle's
    attendedness. A failure anywhere returns None, which reads as "no marker" and falls through
    to the file — which can only ever confirm unattended, so the failure is still not fail-open.
    """
    try:
        ctx = agent.context
    except Exception:
        return None, None

    try:
        from agent import AgentContext
    except Exception:
        AgentContext = None  # type: ignore[assignment]

    for _hop in range(MAX_PARENT_HOPS):
        try:
            m = ctx.get_data(IDLE_MARKER_KEY)
        except Exception as exc:
            return None, "read failed at hop %d: %s" % (_hop, type(exc).__name__)
        if m is not None:
            return m, None
        if AgentContext is None:
            return None, "AgentContext unavailable at hop %d" % _hop
        try:
            parent_id = ctx.get_data(PARENT_CONTEXT_KEY)
            if not parent_id:
                return None, None           # top of the chain. Not a fault.
            parent = AgentContext.get(parent_id)
        except Exception as exc:
            return None, "parent lookup failed at hop %d: %s" % (_hop, type(exc).__name__)
        if parent is None:
            return None, "parent %s not resolvable at hop %d" % (parent_id, _hop)
        if parent is ctx:
            return None, "parent chain cycles at hop %d" % _hop
        ctx = parent

    # Depth bound exceeded. Falling through to the file is SAFE — the file can only ever confirm
    # unattended — but it is not the same as "no marker", and Opus's ruling of 2026-09-11 is the
    # reason this is distinguished: *"silent safety and observed safety are different
    # categories."* The returned fault is the only instrument that would tell us the bound was
    # too shallow.
    return None, "depth bound %d exceeded" % MAX_PARENT_HOPS


def attendedness(agent):
    """(observation, marker, walk_fault). Fails closed to UNDETERMINED.

    ATTENDED requires all three: no marker, the file read AND parsed, and its id empty or
    different. Anything else is unattended or undetermined, and both of those veto.
    """
    m, fault = marker(agent)
    if m is not None:
        return UNATTENDED, m, fault

    try:
        with open(ENGINE_STATE, encoding="utf-8") as fh:
            state = json.load(fh)
    except Exception:
        return UNDETERMINED, None, fault
    if not isinstance(state, dict):
        return UNDETERMINED, None, fault

    try:
        here = agent.context.id
    except Exception:
        return UNDETERMINED, None, fault

    there = state.get("cycle_context_id")
    if there and here and there == here:
        return UNATTENDED, None, fault
    # Empty or different. This is the ONLY branch that may say attended, and it is wrong
    # whenever the file is stale — which is why a stale file can only ever cost a nudge, never
    # an unattended execution.
    return ATTENDED, None, fault
