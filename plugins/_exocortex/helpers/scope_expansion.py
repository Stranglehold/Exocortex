"""
scope_expansion.py — A2 detection logic (pure functions, no agent coupling)

WHAT A2 IS, AFTER JAKE RESCOPED IT
----------------------------------
The original spec had this watching every turn. Jake challenged the premise and the
challenge held: the idle engine exists to give the agent DISCRETION, and scope creep
during autonomous cycles may be the agent exercising judgment about dependencies we
never thought to ask for. Vek's 300+ wiki pages came from unassigned work. The
"BUILD budget creep" anti-pattern was flagged five times and never once verified to
be a problem.

So A2 fires on DIRECTED tasks only — where someone gave a specific assignment with a
defined deliverable, and drifting off it is genuinely off-task. Autonomous output is
governed at the OUTPUT (the Phase B acceptor gate), not at the process.

WHAT IS COMPARED, AND WHY IT IS NOT WHAT THE SPEC SAID
------------------------------------------------------
Anchor  = `_pace_plan["task_summary"]` — the operator's framing, captured when the
          plan was created and LOCKED. This is the scope commitment.
Current = the AGENT's most recent statement of intent.

Two corrections to the original spec, both from reading the live code:

1. The spec said to key on `_pace_new_task` as the "external prompt" signal. It is
   not that: `_50_supervisor_loop` sets it after a Tier-3 reset/emergency, meaning
   "task cycle complete, replan". The real directed-vs-idle discriminator is the idle
   daemon's own `cycle_context_id` in engine_state.json — see `is_directed()`.

2. The spec's "word count increase > 50%" does not transfer. It assumes two task
   DESCRIPTIONS of like kind. Here the anchor is a short operator sentence and the
   current text is a long agent message, so the ratio is enormous on every turn.
   Length is not a signal in this comparison and is deliberately not used.

Drift also cannot show up in the USER message: a changed user message makes
`_14_pace_plan_generator` create a NEW locked plan, which resets the commitment. So
the thing that drifts is what the agent says it is doing, which is what we read.

No LLM calls. Lexical matching only.
"""

import re

# Broad-scope words. Only counted when ABSENT from the anchor — "refactor the search
# pipeline" is not scope creep if the assignment said refactor the search pipeline.
BROAD_TERMS = [
    "refactor", "redesign", "rewrite", "overhaul", "migrate", "restructure",
    "all of", "every", "entire", "everything", "across the board", "end to end",
    "from scratch", "wholesale", "sweeping",
]

# Phrases that announce an addition to the agreed scope.
EXPANDING_PHRASES = [
    "and also", "additionally", "as well as", "while i'm at it", "while im at it",
    "might as well", "may as well", "on top of that", "furthermore", "i'll also",
    "ill also", "we should also", "it also makes sense to", "in addition",
    "let me also", "i should also",
]

# Verbs that describe taking on new work.
ACTION_VERBS = [
    "refactor", "rewrite", "redesign", "migrate", "port", "rebuild", "overhaul",
    "restructure", "replace", "delete", "remove", "deprecate", "consolidate",
    "unify", "standardize", "standardise", "audit", "expand",
]

_RX_WORD = re.compile(r"[a-z']+")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def _words(text: str) -> set:
    return set(_RX_WORD.findall(_norm(text)))


def detect(anchor: str, current: str) -> dict:
    """Compare a locked scope commitment against the agent's stated intent.

    Returns {signals: [...], count: int, detail: {...}}. Signals are only raised for
    material NOT present in the anchor — the anchor is what was authorised, so
    anything it already contains cannot be an expansion of it.
    """
    a_norm, c_norm = _norm(anchor), _norm(current)
    a_words = _words(anchor)
    signals, detail = [], {}

    # 1. broad-scope terms the assignment did not contain
    broad = [t for t in BROAD_TERMS if t in c_norm and t not in a_norm]
    if broad:
        signals.append("broad_terms")
        detail["broad_terms"] = broad[:6]

    # 2. explicit additive phrasing
    phrases = [p for p in EXPANDING_PHRASES if p in c_norm]
    if phrases:
        signals.append("expanding_phrases")
        detail["expanding_phrases"] = phrases[:6]

    # 3. new action verbs — taking on work of a kind the assignment did not name
    new_verbs = [v for v in ACTION_VERBS if v in _words(current) and v not in a_words]
    if new_verbs:
        signals.append("new_action_verbs")
        detail["new_action_verbs"] = new_verbs[:6]

    # NOTE: no word-count signal. See module header — the ratio between a short
    # operator sentence and a long agent message is enormous on every single turn,
    # so it would fire constantly and tell us nothing.

    return {"signals": signals, "count": len(signals), "detail": detail}


def is_directed(context_id: str, engine_state: dict | None) -> tuple[bool, str]:
    """Is this turn a DIRECTED task rather than an idle-engine cycle?

    Returns (directed, reason). The idle daemon writes the running cycle's context id
    to `cycle_context_id` and clears it on completion, so an exact match means this
    turn belongs to an autonomous cycle.

    Three input states, deliberately distinguished — caught by the in-container test,
    where the first version treated all of them as "unknown" and went permanently
    silent on any container without an idle daemon:

      dict with data  the daemon exists; compare context ids
      {}              the state FILE IS ABSENT, so no idle daemon has ever run here,
                      so there are no autonomous cycles and every turn is directed
      None            the file exists but could not be parsed — we genuinely cannot
                      tell, so stay silent

    FAILS TOWARD SILENCE on the genuine unknown. For an observe-only detector losing a
    data point costs nothing, whereas firing on autonomous cycles is the exact
    behaviour this was rescoped to avoid. But "absent" is not an unknown — it is
    positive evidence that nothing autonomous is running.
    """
    if engine_state is None:
        return False, "engine_state present but unparseable — cannot prove directed"
    if engine_state == {}:
        return True, "directed (no idle daemon state on this container)"
    cyc = str(engine_state.get("cycle_context_id") or "")
    if cyc and context_id and cyc == context_id:
        return False, "idle-engine cycle (context matches cycle_context_id)"
    return True, "directed" if not cyc else "directed (a cycle is running in another context)"
