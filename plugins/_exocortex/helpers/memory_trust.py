"""
memory_trust.py — what a recalled memory may be used as, decided from its metadata alone
(graduated trust, Phase 1)

WHY THIS EXISTS
---------------
Opus's graduated-trust note (Opus/design-notes/graduated-trust-render-time-provenance.md,
2026-09-25), as corrected by Kestrel's review against the live code and store:
  - GT-2: content cannot promote its own trust. Every input here is METADATA the pipeline wrote,
    never the memory's text: a memory that says "Jake confirmed this" is data, not provenance.
  - Three verdicts. `evidence` is the default. `excluded` means do not present (v3's word; the
    lesson suppressor's `suppressed` is a different store and a different code path).
    `instruction` is unreachable today: nothing in the store can prove human confirmation after
    the fact (GT-1, GT-5), so no path returns it.
  - One home for the rule. Before this file, the exclusion rule lived inline in _92's scoring
    filter (`validity == "deprecated"`). _92 now asks `excluded()` at that same point, so the
    decision is made once, here, and the recall trace can record what it withheld.
  - The frame. render_trust() also returns the clause _92's `_with_provenance` appends to its
    existing head, "recalled memory (saved <date>; source: <...>; <R3 clauses>)": one head per
    memory, outside the passage body, with no second label (v3 items 1-2). The source shown obeys
    GT-2a: the stored value only with the derivation marker, else `legacy`. `trust` is not shown:
    it is `evidence` for every rendered memory until Phase 2, a token with zero bits (v3).

WHAT IS EXCLUDED (measured in her store 2026-09-25: 137 of 2,100)
------------------------------------------------------------------
`classification.validity == "deprecated"`, which two writers set:
  - R1 keyed supersession (helpers/memory_supersede.py): also sets lineage.superseded_by and
    lineage.deprecated_reason = "subject_key:<key>" (31 in the store);
  - the classifier's dedup/contradiction path (_55): sets lineage.superseded_by without a reason.
The reason returned below distinguishes them for the trace and for audit; it changes nothing
about the verdict. Exactly the set _92 excluded before this file existed: behaviour is unchanged.

WHAT THIS DOES NOT DO
---------------------
- It does not change what is recalled. excluded() is the validity filter _92 already ran.
- It does not reach memory_load output (formatted by A0 core, DEC-030) or A0's base recall when
  _92 returns early (the A17 gap). Those get neither the verdict nor the frame; the recall trace
  counts those turns.
- It does not consult lesson_suppressor: that predicate governs procedural anti-patterns
  (ProceduralMemory, markdown + .index.json), which never reach this pipeline.
- It does not mutate the store. No LLM calls.

!! Imported by bare name (like recall_query and memory_recall_tag), so an edit is live only after a
container restart; see recall_query.py's docstring.
"""

CLS_KEY = "classification"
LIN_KEY = "lineage"

VERDICT_EVIDENCE = "evidence"
VERDICT_EXCLUDED = "excluded"         # v3: `suppressed` is the lesson suppressor's word, not ours
VERDICT_INSTRUCTION = "instruction"   # unreachable in Phase 1 (GT-1): no confirmation mechanism

# GT-2a: a stored source is shown only when the derivation marker says a rule produced it.
LEGACY_SOURCE = "legacy"


def _meta(doc) -> dict:
    m = getattr(doc, "metadata", None)
    return m if isinstance(m, dict) else {}


def _part(doc, key) -> dict:
    v = _meta(doc).get(key)
    return v if isinstance(v, dict) else {}


def verdict(doc):
    """(verdict, reason) for one recalled memory. Never raises; an unreadable memory is evidence,
    which is what it was before this file existed (the filter only ever excluded `deprecated`)."""
    try:
        if _part(doc, CLS_KEY).get("validity") == "deprecated":
            lin = _part(doc, LIN_KEY)
            reason = str(lin.get("deprecated_reason") or "")
            if reason.startswith("subject_key:"):
                return VERDICT_EXCLUDED, "R1 " + reason
            if lin.get("superseded_by"):
                return VERDICT_EXCLUDED, "superseded_by %s" % lin.get("superseded_by")
            return VERDICT_EXCLUDED, "deprecated"
        return VERDICT_EVIDENCE, ""
    except Exception:
        return VERDICT_EVIDENCE, ""


def excluded(doc) -> bool:
    """True when the memory must not be presented. The one rule _92's filter applies."""
    return verdict(doc)[0] == VERDICT_EXCLUDED


def source_clause(doc) -> str:
    """The provenance clause for the recall frame (GT-2a).

    With `classification.source_rule` (a derivation rule produced the source): the stored value,
    e.g. "source: agent_inferred". Without it: "source: legacy". Before the marker, the stored
    value is the model's claim about itself (all 209 user_asserted in her store are pre-R2), and
    showing it in this position would let content promote its own trust (GT-2). `legacy` states the
    mechanism: no derivation record exists for this label. It is deliberately not "(pre-R2)": seven
    memories were saved after R2 went live and before the marker existed.
    """
    try:
        cls = _part(doc, CLS_KEY)
        src = str(cls.get("source") or "").strip()
        if src and cls.get("source_rule"):
            return "source: " + src
    except Exception:
        pass
    return "source: " + LEGACY_SOURCE


def render_trust(doc):
    """(verdict, clauses) for one recalled memory: the trust verdict, and the clauses the recall
    frame appends to its head. An excluded memory is never rendered, so it gets no clauses."""
    v, _reason = verdict(doc)
    if v == VERDICT_EXCLUDED:
        return v, []
    return v, [source_clause(doc)]
