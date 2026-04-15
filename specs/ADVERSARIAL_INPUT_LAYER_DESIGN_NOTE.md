# Adversarial Input Layer — Design Note

**Status:** Design note. Pre-spec exploration.
**Date:** 2026-04-14
**Motivated by:** Jake's observation that OSS currently operates as a blind transcriber — it stores incoming RSS claims without evaluating them against the system's existing knowledge. A dedicated analyst does not read a cable the way a scribe files it. The goal of this layer is to translate trained analyst tradecraft into an automated component that acknowledges every incoming claim, stores it, and annotates it with the system's reasoning about whether the claim represents reality accurately given what is already known.
**Grounded in:** [specs/INPUT_SCRUTINY_RESEARCH_NOTE.md](INPUT_SCRUTINY_RESEARCH_NOTE.md) — the full research foundation, twelve rules distilled from psychology, intelligence tradecraft, and adversarial reasoning literature. All citations live in that document; this one references them by name rather than duplicating them.
**Sibling document:** [specs/ADVERSARIAL_VALIDATION_PROTOCOL.md](ADVERSARIAL_VALIDATION_PROTOCOL.md) — DEC-021, Session 051. That document defines how the Exocortex team validates its own intellectual outputs (papers, design notes, identity documents) before publication using Klein pre-mortem + cold-read-by-fresh-instance. This document defines the *input-side counterpart*: how the OSS ingestion pipeline scrutinizes incoming claims from external sources before storage. **Same adversarial pattern, opposite ends of the system.** Both draw on Kahneman's adversarial collaboration, Klein's pre-mortem, and the Schwenk / Schweiger devil's advocacy literature — the connection is architectural, not coincidental.
**Related systems:** Narrative Stability (shipped 2026-04-14), Hedge Pattern Detection (design note in progress), SWARMFISH Devil's Inquisitor (shipped), Counter-Patriots Source Intelligence (prior research), Cognitive Defense System v1/v2 (prior research).

---

## Part 0: What This Document Answers

The research note establishes twelve rules that converge across three independent research traditions. This document translates those rules into concrete architecture for the OSS ingestion pipeline. It is not a spec — file paths, SQL migrations, and test assertions come later. This is the *thinking artifact* that the eventual L3 spec is derived from, and the reference document we check against after build to see which assumptions held and which fell apart.

The four load-bearing commitments from Jake's original framing — and which rules in the research note each one maps to:

1. **Acknowledge, don't discard.** Every claim enters the ledger regardless of system disagreement. → Rules 1, 8, 11.
2. **Adversarially evaluate against prior knowledge.** The system compares incoming claims against its existing model and flags disagreement. → Rules 3, 4, 5.
3. **Not a filter.** Output is annotation, not selection. Nothing is suppressed. → Rules 1, 4, 8.
4. **Feedback loop to SWARMFISH.** The committee's current assessment becomes OSS's prior; OSS anomalies escalate back to the committee. → Rules 3, 5, 11.

The central design commitment — the one that makes this layer different from a "smarter filter" — is **Rule 4**: Bayesian surprise boosts, never suppresses. Any filter that uses "consistency with current beliefs" as a rejection criterion is architecturally wrong. Consistency can consolidate matching claims; it can never drop discordant ones. Discordant claims route to adversarial review at *higher* priority than concordant ones. This is the structural protection against the confirmation-cascade failure mode.

---

## Part I: Architectural Overview

### The flow

```
    Incoming claim (from ingest.py LLM extraction)
                        |
                        v
    +-------------------+--------------------+
    |  Scrutiny pipeline (new)               |
    |                                        |
    |  1. Prior injection                    |  ← pull current SWARMFISH
    |     (SWARMFISH → OSS)                  |    assessment for topic T
    |                                        |
    |  2. Surprise scoring                   |  ← how much would the
    |     (anomaly detection)                |    assessment change if
    |                                        |    this claim were accepted?
    |                                        |
    |  3. Dialectical counter-claim          |  ← retrieve the strongest
    |     synthesis                          |    contradicting existing
    |                                        |    claim from the ledger
    |                                        |
    |  4. Fabrication premortem              |  ← assume this claim is
    |                                        |    false; check against
    |                                        |    known fabrication
    |                                        |    signatures
    |                                        |
    |  5. Verdict compilation                |  ← combine 2-4 into a
    |                                        |    scrutiny record attached
    |                                        |    to the claim
    +-------------------+--------------------+
                        |
                        v
    +-------------------+--------------------+
    |  Claim stored in ledger with full      |
    |  scrutiny annotations attached.        |
    |  NOTHING is suppressed.                |
    +-------------------+--------------------+
                        |
                        v
            +-----------+-----------+
            |                       |
            v                       v
     Escalation cue?         No escalation —
     (high surprise,         claim enters
     premortem hit,          ledger and is
     deception match)        visible to analyst
            |               with scrutiny
            v               annotations
    +-------+---------+
    |  Trigger SWARMFISH  |
    |  fresh prediction   |
    |  cycle with flagged |
    |  claim in context   |
    +---------+-----------+
              |
              v
       Committee decides
       whether to update
       its assessment
              |
              v
       Updated assessment
       → next OSS cycle
       prior injection
       (feedback loop closes)
```

### The six components

1. **Prior Injection.** OSS pulls SWARMFISH's current committee assessment per topic at the start of each scrutiny cycle. This becomes the live prior the pipeline evaluates against.

2. **Surprise Scoring.** Compute an anomaly score between the incoming claim and the current assessment. High surprise = the claim would materially shift the posterior if accepted. v1 uses cosine distance from assessment centroid; v2 can upgrade to formal KL divergence.

3. **Dialectical Counter-Claim Synthesis.** For each material claim, retrieve the top-K contradicting claims already in the ledger and attach them as a linked dialectical pair. No claim enters storage as an unopposed assertion. (Mason-Mitroff, Wikipedia NPOV pattern.)

4. **Fabrication Premortem.** Stipulate the claim is false and check its metadata against known fabrication signatures — single-channel corroboration, suspicious timing, hedge-vague-attribution combination, absence of provenance chain. Matches become annotations. (Klein 2007; Heuer on deception detection.)

5. **Verdict Compilation.** All scrutiny outputs aggregate into a single record attached to the claim. Each check is a separate row in an append-only log so ground-truth feedback can retrospectively score past verdicts.

6. **Escalation Router.** A narrow set of cues — surprise above threshold, premortem hit, deception hypothesis match, source novelty — escalates to a fresh SWARMFISH prediction cycle with the flagged claim included in the context bundle. Escalation is one-way: the cheap pipeline can promote, never demote.

---

## Part II: The Six Components in Detail

### Component 1: Prior Injection

**What it does:** Makes the current SWARMFISH committee assessment available to OSS scrutiny as a structured prior.

**Why:** Rule 3 (live hypothesis set) requires the pipeline to compare incoming claims against the system's current model of the world, not a null prior. The Exocortex already has that model — it's what SWARMFISH's committee is computing every ~30 minutes. We don't need to build a separate belief-tracking system; we need to read from the one that already exists.

**Mechanism:**

Every scrutiny cycle starts with a query to SWARMFISH's `/acp/session` endpoint for the most recent committee assessment on each active OSS topic. The assessment carries:

- Consensus value (e.g., 0.68)
- Consensus range (e.g., 0.63–0.73)
- Meta-confidence (HIGH / MEDIUM / LOW)
- Disagreement spread (sigma)
- Per-profile predictions (the 9-member committee, each with confidence and reasoning)
- Devil's Inquisitor output (surprising facts, consensus warnings, predicted blind spots)
- Session timestamp and topic binding

The injection step bundles this into a **structured prior object** that travels with the claim through the rest of the scrutiny pipeline:

```python
class TopicPrior:
    topic: str
    committee_consensus: float
    committee_range: tuple[float, float]
    committee_meta: str                # "HIGH" | "MEDIUM" | "LOW"
    committee_sigma: float
    per_profile_claims: list[ProfilePrediction]
    di_surprising_facts: list[str]
    di_consensus_warning: str | None
    di_blind_spots: list[BlindSpot]
    assessment_timestamp: datetime
    freshness: timedelta               # now - assessment_timestamp
```

**The freshness field is load-bearing.** A prior that is 4 hours stale has weaker authority than one that is 4 minutes stale. The scrutiny logic weights the prior's authority inversely to its age — a very fresh assessment dominates new claims strongly; a very stale assessment is treated as weak prior and requires less surprise to trigger an update.

**Handling missing priors:** If SWARMFISH has never assessed a topic, the prior is `None` and the scrutiny pipeline falls through to source-level and content-level checks only (fabrication premortem, internal consistency). No surprise scoring, no escalation. The claim still enters the ledger normally. Missing priors are not errors — they are the natural state for novel topics.

**Performance:** The query is cheap (read-only, cached with a short TTL). Target: <50ms per topic. SWARMFISH already exposes the session endpoint; we just consume it.

---

### Component 2: Surprise Scoring

**What it does:** Computes how much the current assessment would shift if the incoming claim were accepted. High surprise = strong signal that either (a) the claim is important new information, or (b) the claim is wrong and should be scrutinized.

**Why:** Rule 4 — Bayesian surprise as the primary escalation signal. The mechanism is identical to how the brain allocates attention (Friston, Itti & Baldi) and how intelligence analysts prioritize incoming cables (Heuer's "diagnosticity" concept, Zlotnick Bayesian update).

**Critical point:** high surprise does NOT mean "reject." It means "pay attention." The rational response to a surprising claim is to examine it more carefully, because a surprising claim is the one most likely to correct a wrong model if true. This is the direct inversion of the confirmation-cascade failure mode.

**Mechanism (v1 — cosine distance):**

```python
def surprise_score(claim: Claim, prior: TopicPrior) -> float:
    """
    v1 implementation: semantic distance between the claim and the
    committee's current framing of the topic. Returns a float in [0, 1]
    where 1 is maximum surprise.
    """
    # Embed the claim (already done at extraction time)
    claim_vec = claim.faiss_vec

    # Embed the committee's current framing as a composite of
    # consensus-range, DI warnings, and the strongest dissent
    framing_text = compose_framing_text(prior)
    framing_vec = embed(framing_text)

    # Cosine distance, normalized
    distance = 1.0 - cosine_similarity(claim_vec, framing_vec)
    return clamp(distance, 0.0, 1.0)
```

**Mechanism (v2 — formal KL divergence):**

A later refinement computes `S(D, M) = KL(P(M | D) || P(M))` — the formal Itti-Baldi Bayesian surprise. This requires an explicit probabilistic model of the committee's posterior and an update step that computes what the posterior would look like if the claim were accepted. The machinery is heavier and requires a well-calibrated prior distribution; v1 is a semantic proxy that captures the same signal at lower engineering cost.

**The Zlotnick reliability weighting:**

Raw surprise is insufficient. A highly surprising claim from an unreliable source should not carry the same weight as a highly surprising claim from a trusted one. The final scrutiny metric combines:

```python
def weighted_surprise(raw_surprise: float, source_reliability: float) -> float:
    """
    Zlotnick R = P × L formulation adapted for scrutiny.
    Source reliability is treated as a confidence multiplier on the surprise.
    A raw_surprise of 0.9 from an F-tier source weights less than a
    raw_surprise of 0.6 from an A-tier source, because the low-reliability
    source has substantial probability mass on "the observation didn't
    actually occur as reported."
    """
    return raw_surprise * source_reliability
```

**What gets stored:** Both the raw surprise and the reliability-weighted surprise. Downstream consumers (the escalation router, the analyst UI) can read either depending on whether they want to see "how unusual is this claim?" or "how much attention does it deserve given its source?"

**Threshold (first-pass):** `weighted_surprise > 0.4` triggers escalation. This is a guess. Expect to retune after a week of production data.

---

### Component 3: Dialectical Counter-Claim Synthesis

**What it does:** For every incoming claim above a materiality threshold, retrieves the strongest contradicting existing claim from the ledger and links it as a dialectical pair. The claim enters the ledger with its counter-claim attached.

**Why:** Rule 8 — dialectical storage, not verdict storage. Mason-Mitroff's dialectical inquiry and Wikipedia's NPOV structure both encode the same principle: no claim enters the corpus as an unopposed assertion. Contradicting evidence is preserved alongside the claim rather than resolved into a single verdict.

**This is also the direct mechanical form of Jake's phrase** — "acknowledge what was said but say 'this is why I don't think this represents reality accurately.'" The counter-claim IS the "this is why."

**Mechanism:**

For an incoming claim on topic T:

1. **Retrieval query.** Search the ledger for the top-K (k=3) existing claims that are *semantically similar but logically opposed* — same topic, same referents, opposite polarity. This is implemented as semantic similarity above a threshold (FAISS cosine > 0.7) filtered to claims whose `signal_class` or modality suggests contradiction potential.
2. **Negation detection.** For each retrieved candidate, run a cheap sign-detection pass: does the candidate contradict the incoming claim on a shared predicate? This can be regex-based for v1 (presence of "not", "no", "never", quantifier reversals) and LLM-validated for v2.
3. **Rank by contradiction strength.** Score each candidate by semantic closeness × sign-opposition strength × source reliability.
4. **Attach as linked record.** The top candidate is stored as a `counter_claim_id` pointing at the contradicting claim. If multiple candidates are all strong, store all of them as a list.

**No synthesis, only retrieval.** This is important. The counter-claim is not generated by an LLM from scratch — it is *retrieved from the existing ledger*. The pipeline's job is to surface the contradiction that already exists in the corpus, not to invent one. Synthesis would require the LLM to commit to a claim it can't verify. Retrieval guarantees the counter-claim is grounded in a real source that has already survived ingestion.

**What if no counter-claim exists?** Then the pipeline stores the incoming claim without a dialectical pair and annotates the scrutiny record with `counter_claim_status: none_found`. This is not a failure — it means either (a) the topic is novel to the corpus, or (b) the claim is uncontroversial in the corpus. Both are legitimate states. A subsequent scrutiny pass on the next claim on the same topic may pair it against this one.

**Asymmetric pairing:** The dialectical pair is bidirectional in practice — when claim A is ingested and paired with existing claim B, a link is written in both directions. This matters for the analyst UI: when you view claim B later, you can see that a newer claim contradicted it.

---

### Component 4: Fabrication Premortem

**What it does:** Before accepting an incoming claim, stipulates the claim is false and checks its metadata against known fabrication signatures. Matches become annotations, not rejections.

**Why:** Rule 9 — Klein's premortem applied to claim ingestion. The mechanism leverages prospective hindsight (Mitchell, Russo & Pennington 1989): imagining an outcome as already realized increases the ability to identify failure modes by ~30% compared to forward-looking evaluation. Here the "outcome" is "the claim is false" and the "failure modes" are the mechanisms that would produce exactly this false claim.

**The fabrication signatures:**

A claim matches a fabrication signature when its metadata exhibits a pattern consistent with a specific failure mode. These are not single-dimensional — each signature is a combination of features. First-pass signatures:

1. **Single-channel corroboration.** The claim is factually specific (names, dates, numbers) but exists in only one source with no independent reporting. Requires checking: is the claim present in ≥1 other source in the ledger?

2. **Hedge-vague-attribution cluster.** High hedge density + vague attribution + high topic salience. This is the narrative-management pattern detected by the hedge pattern layer; an incoming claim that fits this cluster on a hot topic is a fabrication candidate.

3. **Suspicious temporal alignment.** The claim appears within a narrow time window of other similar-topic claims across multiple sources, suggesting coordinated propagation rather than independent observation. (Corresponds to the "emergent" technique class we already track.)

4. **Absent provenance chain.** The claim asserts knowledge that requires a specific access path (intelligence source, insider leak, proprietary data) but provides no attribution or a vague one. High-specificity claim + low-specificity source = provenance mismatch.

5. **Confidence-specificity mismatch.** High stated confidence combined with high specificity on an unverifiable matter. An analyst saying "absolutely certain" about an unverifiable future event is a signature of motivated prediction, not genuine certainty.

6. **Hallucination fingerprint.** The claim references entities (people, places, organizations) that are not present in the ledger at all and are not cross-referable to any external knowledge source. This catches LLM-extraction errors where the upstream LLM invented details during paraphrase.

**Mechanism:**

Each signature is implemented as a deterministic check — mostly regex, some ledger queries, some cross-reference to the existing `technique_class`, `modality`, `certainty`, and `attribution` fields from the narrative stability + hedge pattern layers. The signature module returns a list of matched signatures plus a confidence score for each match.

```python
def run_fabrication_premortem(claim: Claim, ledger: Ledger, prior: TopicPrior) -> PremortemResult:
    matches = []
    for signature in FABRICATION_SIGNATURES:
        match = signature.check(claim, ledger, prior)
        if match.matched:
            matches.append(match)
    return PremortemResult(
        matches=matches,
        match_count=len(matches),
        max_confidence=max((m.confidence for m in matches), default=0.0),
    )
```

**Threshold (first-pass):** `match_count >= 2` OR `max_confidence >= 0.8` triggers escalation.

**Annotation, not rejection.** Premortem matches do not prevent the claim from entering the ledger. They become part of the scrutiny record attached to the claim, visible to downstream consumers, and — if the threshold is hit — trigger escalation. The claim is still stored. This is Rule 1 (default to doubt) combined with Rule 8 (dialectical storage): we write our doubts next to the claim rather than discarding either.

---

### Component 5: Verdict Compilation

**What it does:** Aggregates the outputs of components 2-4 into a single scrutiny record attached to the claim. The record is append-only and carries enough structure that a future retrospective calibration pass can score each past verdict against eventual ground truth.

**Why:** Rule 12 — structural humility. A claim ingestion pipeline that gets hundreds of claims per day and rarely sees ground truth fails the Kahneman-Klein conditions for trustworthy intuitive judgment. The pipeline's decisions must be *auditable and reversible*, and the evidence trail must be preserved so future feedback can calibrate earlier choices.

**Schema (conceptual, not SQL yet):**

Each claim gets zero or more `scrutiny_verdicts` entries:

```python
class ScrutinyVerdict:
    claim_id: int
    check_name: str                    # "surprise_score", "fabrication_premortem_single_channel", etc.
    timestamp: datetime
    result: str                        # "pass" | "fail" | "warn"
    confidence: float                  # [0, 1]
    numeric_value: float | None        # for scoreable checks
    reasoning: str                     # human-readable explanation
    escalated: bool                    # did this check trigger escalation?
    metadata: dict                     # check-specific details
```

Multiple verdicts per claim. A claim that triggers escalation carries 4-6 verdict rows (one per check plus the escalation decision). A claim that passes cleanly carries the same number with `result=pass` on each. Nothing is elided — the audit trail is complete.

**Append-only guarantee.** Verdicts are never updated after write. Corrections or revisions produce new verdict rows with a `supersedes` pointer to the old one. This is Wikipedia-style edit history, enforced at the schema level.

**Retrospective calibration hook:** Each verdict carries enough metadata that a future pass — triggered by ground-truth arrival (treaty signing, military action, public disclosure) — can retrospectively score the verdict. "This claim scored surprise=0.7 and escalated; the committee updated; the ground truth turned out to confirm the original assessment. The escalation was a false positive." These retrospective scores feed into threshold tuning.

---

### Component 6: Escalation Router

**What it does:** Decides which scrutiny verdicts warrant escalation to the expensive verification stage (a fresh SWARMFISH prediction cycle with the flagged claim in context), and triggers it.

**Why:** Rule 11 — tip-and-cue asymmetric escalation. The ingestion pipeline is the cheap, high-recall, deliberately-noisy tip stage. A narrow set of cues escalates to expensive processing. Escalation is one-way: the cheap stage can promote, never demote.

**The cues:**

1. **Weighted surprise exceeds threshold** (initial: 0.4)
2. **Fabrication premortem match count ≥ 2** OR **max confidence ≥ 0.8**
3. **Explicit deception hypothesis match** — single-channel, high-diagnosticity, convenient-timing combination
4. **Source novelty** — claim arrives from a source that has been active for <N days OR has <M claims in the ledger (first-pass: N=30, M=50)
5. **Hedge pattern narrative_campaign signal** (from the sibling hedge pattern work) — this crosses layers

A claim that hits *any* of these triggers escalation. The thresholds are ORed, not ANDed — one hit is enough. This is deliberate: the cheap stage is tuned toward recall, not precision. False escalation wastes a SWARMFISH cycle; false non-escalation misses a potentially model-breaking claim. The asymmetric cost makes recall the right default.

**The escalation mechanism:**

When a cue fires, the scrutiny pipeline writes an `escalation_request` record and POSTs to SWARMFISH's monitor endpoint with:

- The flagged claim ID
- The scrutiny verdicts that triggered escalation
- The current topic prior that was used in scoring
- A short reasoning summary

SWARMFISH's monitor receives the request and, on its next cycle, includes the flagged claim in the evidence bundle passed to the committee. The committee then decides whether the claim warrants a full re-prediction or merely annotation. The decision routes back to OSS as an additional verdict attached to the claim.

**Rate limiting.** The escalation router enforces a per-topic cooldown (initial: 15 minutes) to prevent a burst of correlated claims from triggering a flood of SWARMFISH cycles. If multiple claims on the same topic would trigger escalation within the cooldown window, they are bundled into a single escalation request.

**One-way flow.** The router can trigger escalation, but it cannot suppress or delete a claim. Even claims that don't escalate are still stored in the ledger with their scrutiny verdicts. The route-or-not decision affects expensive downstream processing, not the ledger's contents.

---

## Part III: Data Model Extensions

The scrutiny layer requires three new storage structures plus two extensions to existing ones. No claim extraction schema changes — modality, certainty, and attribution come from the narrative stability + hedge pattern work; scrutiny reads those fields rather than setting them.

### New: `scrutiny_verdicts` table

Append-only log of scrutiny checks per claim. Schema sketch:

```
scrutiny_verdicts
  id              serial PK
  claim_id        int FK → claims
  check_name      text
  timestamp       timestamptz
  result          text ('pass' | 'fail' | 'warn')
  confidence      double precision
  numeric_value   double precision nullable
  reasoning       text
  escalated       boolean
  metadata        jsonb
  supersedes      int nullable FK → scrutiny_verdicts
```

Indexed on `claim_id`, `check_name`, `escalated`. Never UPDATED; only INSERTED.

### New: `claim_counter_claims` table

Dialectical pair links. Bidirectional.

```
claim_counter_claims
  id               serial PK
  claim_a_id       int FK → claims
  claim_b_id       int FK → claims
  relationship     text ('contradicts' | 'qualifies' | 'updates')
  strength         double precision
  created_at       timestamptz
  detection_method text
```

The existing `contradictions` table tracks same-source retcons from narrative stability. This is a different table for dialectical pairs across claims regardless of source, generated at scrutiny time. Overlap with `contradictions` is expected — a narrative_rewrite row can also exist as a dialectical pair.

### New: `escalation_requests` table

Tracks when scrutiny escalated a claim to SWARMFISH and what happened next.

```
escalation_requests
  id                      serial PK
  claim_id                int FK → claims
  triggered_by            text[] (list of cue names that fired)
  topic                   text
  request_timestamp       timestamptz
  swarmfish_session_id    uuid nullable FK → acp_sessions
  committee_decision      text nullable
  committee_decision_at   timestamptz nullable
```

### Extension: `claims.surprise_score`

New float column. Populated at scrutiny time. Nullable (historical claims have no score).

### Extension: `claims.scrutiny_status`

New enum column. `pending` | `clean` | `flagged` | `escalated`. Default `pending` on insert, updated to one of the terminal states after scrutiny runs. Claims whose scrutiny is still in progress are visible in the ledger but carry the pending marker so downstream consumers know the scrutiny verdict is not yet attached.

---

## Part IV: The Feedback Loop

The bidirectional flow, concrete:

**Step 1 — OSS ingest cycle begins.** ingest.py pulls RSS feeds, extracts claims, embeds, dedups. (This is the existing pipeline; no changes here.)

**Step 2 — Scrutiny pipeline runs per-claim.** For each newly extracted claim, the scrutiny pipeline:
- Pulls the current SWARMFISH topic prior (Component 1)
- Computes surprise (Component 2)
- Synthesizes counter-claim by ledger retrieval (Component 3)
- Runs fabrication premortem (Component 4)
- Writes scrutiny verdicts to the log (Component 5)
- Evaluates escalation cues (Component 6)

**Step 3 — Claim enters the ledger.** With scrutiny verdicts attached and dialectical pair linked if found. This happens regardless of whether the claim escalated.

**Step 4 — If escalated:** An escalation request is written and POSTed to SWARMFISH. SWARMFISH's next monitor cycle includes the flagged claim in its evidence bundle.

**Step 5 — SWARMFISH committee re-predicts.** The committee sees the flagged claim as new evidence, considers it, and issues a new assessment. The Devil's Inquisitor profile gives it extra weight because it's flagged.

**Step 6 — Committee decision routes back.** The updated assessment becomes the new topic prior for the next OSS scrutiny cycle. The specific committee decision about the flagged claim ("accepted, consensus shifted" / "flagged for analyst review" / "rejected as low-credibility") is stored in the `escalation_requests` table.

**Step 7 — Loop closes.** The next claim ingested on the same topic uses the updated prior as its scrutiny baseline.

**The protection against confirmation cascade:**

The loop has a direction. New evidence flows from OSS up to SWARMFISH. Updated assessments flow from SWARMFISH down to OSS. The question is: can the downward flow corrupt the upward flow?

Specifically: **does using the committee assessment as a prior make OSS more likely to suppress claims that contradict it?** This is exactly the failure mode the research note warns about.

The answer has to be no, and it's enforced by Rule 4. OSS does not suppress based on prior disagreement. Prior disagreement is exactly what triggers escalation. A claim that scores `weighted_surprise = 0.9` against the current prior is treated as a *more important* claim, not a less important one. It goes into the ledger, its counter-claim is linked, and it escalates to SWARMFISH for committee review.

The confirmation cascade failure mode arises when a filter uses "consistency with prior" as a rejection criterion. This layer never rejects. It routes. The worst a surprising claim can experience is *escalation for expensive review* — which is precisely the correct treatment. A concordant claim is stored with a "consistent" annotation; a discordant claim is stored with a "surprising, escalated" annotation. Both end up in the ledger. Neither is dropped.

---

## Part V: Confirmation Cascade Protection — The Explicit Check

Because this is the single most important failure mode, I want to lay out exactly how the architecture prevents it.

**The failure mode:** A filter scores incoming evidence by consistency with current beliefs. High-consistency items reinforce those beliefs, the filter's threshold tightens, and evidence that would correct the model gets filtered out first. Runaway confidence in whatever initial model happened to take hold. This is what a naive "smart filter" would produce.

**The six structural protections in this design:**

1. **Nothing gets filtered.** The scrutiny pipeline is annotation-only. Even claims that hit every fabrication signature and max out the surprise score are stored in the ledger with their verdicts attached. The ledger's contents are not gated by scrutiny — only downstream processing is.

2. **Surprise boosts, not demotes.** High-surprise claims get *more* attention, not less. They trigger escalation to SWARMFISH committee review. A surprising claim is treated as higher-priority than a confirming one.

3. **Dialectical storage preserves both sides.** When a claim contradicts an existing ledger claim, both are stored and linked. Neither is deleted. The dispute log is permanent and additive.

4. **Escalation is one-way.** The cheap pipeline can promote a claim to expensive review, but the expensive stage can only annotate; it cannot retroactively erase a claim from the ledger. Wrong committee decisions are visible in the escalation_requests log and can themselves be revisited.

5. **Posterior delta, not posterior replacement.** When SWARMFISH incorporates flagged claims, it computes a delta-weighted update (Zlotnick formulation) and flags the magnitude of the shift. Large shifts are flagged for human review rather than auto-committed. This is the "reliability-weighted Bayesian update with human-review threshold" rule.

6. **Retrospective calibration.** The scrutiny verdict log is append-only and carries enough metadata that future ground-truth signals can retrospectively score past verdicts. If the system develops a systemic bias (e.g., surprise-threshold tuned too tight, missing correct contradictions), the calibration pass will surface it.

The key architectural commitment is **separation of routing from storage**. Scrutiny decides *how much attention* a claim gets and *where* to route it. Scrutiny does *not* decide whether the claim exists. The ledger is the ground state; scrutiny operates on top of it.

---

## Part VI: Relationship to the Existing Stack

The adversarial input layer slots into a pattern that is already emerging in the Exocortex architecture. It's the fourth member of a family:

| Layer | When it runs | What it scrutinizes | Shipped / design |
|---|---|---|---|
| **Narrative Stability** | After ingest | Source retconning itself | ✅ shipped 2026-04-14 |
| **Hedge Pattern** | At ingest | Source planting deniable claims | 🛠 design in progress |
| **Adversarial Input Layer** | At ingest | Claim vs. system's current knowledge | 📋 this design note |
| **Devil's Inquisitor** | Committee time | Consensus missing surprising facts | ✅ shipped |

Together they cover the four places where narrative management can shape the system:

- **Walkback of committed claims** → narrative stability catches it
- **Implantation of deniable claims** → hedge pattern catches it
- **Injection of claims contradicting current knowledge** → input layer catches it
- **Committee consensus overlooking evidence** → DI catches it

The adversarial input layer is the ingest-time analog of the Devil's Inquisitor. DI runs at output time (after the committee has predicted) and says "the consensus is about to miss X." The input layer runs at ingest time (before the claim hits the ledger) and says "this claim is about to enter the ledger, here's why it might not represent reality accurately." Same pattern, different location. Both are designed to surface what the system is about to overlook.

The layers share the same underlying data model (the `claims` table, the topic taxonomy, the source reliability scores, the modality/certainty/attribution fields). A claim can be flagged by any combination of them. Flags are additive — a single claim can carry a narrative_rewrite from narrative stability, an unverifiable_stream flag from hedge pattern, and an escalation verdict from the input layer simultaneously. They don't conflict; they layer.

---

## Part VII: What This Does NOT Do

- **It does not filter.** Every claim enters the ledger. The layer is annotation-only.
- **It does not auto-update SWARMFISH's posterior.** It flags, surfaces, and escalates. Update decisions stay with the committee and ultimately with the human analyst on review.
- **It does not replace the existing ingestion pipeline.** ingest.py still fetches, extracts, embeds, and stores. The scrutiny layer runs after extraction and before final commit of the scrutiny annotations. If the scrutiny pipeline fails for any reason, the claim still lands in the ledger with `scrutiny_status=pending`.
- **It does not require perfect Bayesian surprise computation.** v1 is cosine distance from the committee's composite framing embedding. v2 can formalize as KL divergence. The v1 implementation captures most of the signal at much lower engineering cost.
- **It does not solve the ground-truth feedback problem.** The Kahneman-Klein feedback condition is still unmet. The layer's decisions are designed to be auditable and reversible, but we do not have a primary mechanism for retrospective calibration yet. That is a separate, later build.
- **It does not replace Narrative Stability, Hedge Pattern, or Devil's Inquisitor.** It complements them. Building this layer does not make the others redundant.
- **It does not handle non-English text.** All the regex-based fabrication signatures and hedge-attribution checks are English-only. The layer degrades gracefully on non-English claims — they get stored with `scrutiny_status=pending` and no verdict annotations.
- **It does not identify intent.** A flag means "this claim is surprising / contradictory / premortem-matched." It does not mean "this source is lying" or "this is state propaganda" or "this is a campaign." Intent classification is out of scope and probably unsolvable at the mechanical layer.

---

## Part VIII: Open Questions

Things I don't know yet and the document should not pretend to decide. Each of these gets resolved empirically during build or in production.

1. **Surprise threshold calibration.** `weighted_surprise > 0.4` is a guess. Will retune on first 48 hours of production data. The real question is whether the distribution of surprise scores is bimodal (clear escalation candidates vs. clear consolidation candidates) or unimodal (a smooth distribution with an arbitrary cut). The shape of the distribution tells us how sensitive the threshold needs to be.

2. **Committee assessment freshness decay curve.** The design says the prior's authority decays with age, but I haven't specified the curve. Linear? Exponential? Step function? Depends on how quickly the committee's assessments go stale on the real topic mix — probably faster on iran-hormuz than on structural claims about financial systems. May need per-topic decay curves.

3. **Counter-claim retrieval quality.** v1 uses semantic similarity + sign-detection. Will this actually find good contradictions, or will it mostly retrieve near-duplicates? Won't know until we run it against a corpus with a few thousand claims per topic. If it produces noise, the fallback is LLM-assisted retrieval at higher cost.

4. **Fabrication premortem false positive rate.** Each signature is a pattern that *correlates* with fabrication, not a proof of it. Legitimate claims can match signatures. The match-count threshold is a blunt way to handle this. A more sophisticated approach weights signatures by their precision on a hand-labeled evaluation set. We don't have that eval set yet.

5. **Escalation rate control.** If the scrutiny layer escalates 20% of claims, SWARMFISH will spend all its cycles on re-predictions. If it escalates 0.5%, we miss most of the value. The right escalation rate is probably ~2-5% of claims, but this is intuition, not calibration.

6. **What counts as a "material" claim for dialectical pairing?** Not every claim needs a counter-claim retrieved — that would be wasteful for trivial claims. Threshold: maybe claims above median `staging_confidence` OR on high-volatility topics. Needs empirical tuning.

7. **Cross-language handling.** Current regex is English-only. Do we add Farsi/Arabic/Russian patterns now, or accept the English-only limitation until a later phase? Depends on what the incoming source mix looks like — most RSS in the current corpus is English but some Iranian state sources publish multilingual.

8. **Interaction with committee staleness.** What happens when OSS receives a claim on a topic SWARMFISH hasn't assessed in 6+ hours? The prior is stale; the scrutiny is weaker. Do we trigger SWARMFISH to re-assess proactively, or do we just tag the claim with low-confidence scrutiny and move on?

---

## Part IX: Phase Plan

1. **This design note.** ✅ (you are here)
2. **Walk-through with Jake.** Confirm architectural shape, flag anything that doesn't match instincts, lock the design.
3. **L3 Spec** — `ADVERSARIAL_INPUT_LAYER_SPEC_L3.md`. Exact file paths, SQL migrations, function signatures, test assertions, deployment sequence.
4. **Build Phase 1** — Components 1 (prior injection), 2 (surprise scoring v1), 5 (verdict compilation), 6 (escalation router). These are the minimum viable scrutiny pipeline. Component 3 (counter-claims) and 4 (premortem) can ship in Phase 2.
5. **Validate in production** — let the pipeline run for a week. Hand-audit the top 20 escalations, the top 20 non-escalations, and the top 20 flagged-but-not-escalated claims. Retune thresholds.
6. **Build Phase 2** — Components 3 (dialectical counter-claims) and 4 (fabrication premortem). These require more of the ledger to be populated and more of the narrative stability + hedge pattern fields to be available.
7. **Phase 3** — v2 surprise scoring (formal KL divergence), cross-language support, retrospective calibration hook.

Each phase is deployable in isolation. The pipeline is correct at every intermediate state because the core architectural commitment — nothing gets filtered, scrutiny is annotation-only — means each component adds capability without removing anything.

---

## Part X: Reference Check (After Build)

Jake's explicit purpose for this document: *see what assumptions hold in practice and what fall apart*. The architecture above is built on a set of empirical claims that will be tested the moment we turn the pipeline on. Listing them explicitly so we can check each one after production data accumulates:

1. **SWARMFISH assessments are available at the freshness the layer needs.** The prior injection design assumes that for any topic with active ingestion, SWARMFISH has a recent-enough committee assessment to use as a prior. If SWARMFISH coverage lags ingestion, the layer degrades. Check: fraction of incoming claims whose topic has a SWARMFISH assessment <1 hour old.

2. **Cosine distance from committee framing is a usable proxy for Bayesian surprise.** The v1 surprise score is a semantic distance, not a formal probability. The assumption is that semantic distance correlates with model-update magnitude. Check: compare v1 scores against hand-audited "would this update the committee" judgments on 50 sample claims.

3. **Counter-claim retrieval finds meaningful contradictions, not near-duplicates.** Dialectical pairing only works if the retrieved counter-claim is genuinely opposed to the incoming claim, not just topically similar. Check: precision of top-K retrieval on a hand-audited sample.

4. **Fabrication signatures correlate with actual fabrication.** The signatures are based on tradecraft intuition and the literature. They have never been tested on this specific corpus. Some may fire on legitimate claims at high rates; others may miss actual fabrication. Check: false positive and false negative rates on a hand-audited sample.

5. **Escalation rate is in the useful range.** Too high and SWARMFISH overloads; too low and the layer is invisible. Check: weekly escalation rate, committee update rate on escalated claims, analyst feedback on escalation quality.

6. **The confirmation cascade protection works.** No architectural commitment is self-enforcing. The six protections in Part V have to actually hold in operation. Check: spot-audit for cases where a high-reliability source reported something contradicting current assessment — did the layer escalate, or quietly absorb?

7. **The feedback loop closes without oscillation.** OSS updates prior → SWARMFISH updates assessment → OSS uses new prior. This could oscillate if the updates are too sensitive or the freshness windows are too tight. Check: per-topic posterior movement over time; look for high-frequency oscillations.

8. **Dialectical storage is usable by analysts.** Storing a claim with a linked counter-claim is only valuable if the analyst can see and reason about both. This is a UI question as much as a data question. Check: does the analyst panel actually surface dialectical pairs in a useful way?

9. **Scrutiny verdicts are interpretable in aggregate.** The verdict log is supposed to enable retrospective calibration. That requires verdicts to be categorically consistent — a `surprise_score` check in April should mean the same thing as a `surprise_score` check in July. Check: verdict-log consistency over time, against retuning events.

10. **The layer doesn't slow ingestion meaningfully.** The scrutiny pipeline is supposed to be cheap. If it adds >500ms per claim, the overall ingestion loop will fall behind the source update rate. Check: per-claim scrutiny latency in production.

Every one of these has a concrete check. After we've been running in production for a week, we walk through this list and mark each one **held** / **modified** / **broken**. That's the reference check Jake asked for.

---

## Closing

The architecture in this document is twelve rules of research translated into six components, three new tables, and one bidirectional feedback loop with SWARMFISH. Every commitment is traceable to a line in the research note, which is itself traceable to primary-source literature across three traditions.

It is not a finished design. The thresholds are guesses, the v1 implementations will be replaced, the counter-claim retrieval is a hypothesis, the escalation rate is a bet. What the document establishes is the *shape* — the architectural commitments that are not allowed to move once we start building. The things that can move are the numeric parameters and the specific implementations. The things that cannot move are the twelve rules, the annotation-only principle, the append-only audit log, the asymmetric escalation flow, and the dialectical storage commitment.

When we build, we will learn things that force us to revise. This document is the record of what we believed going in, so we can see clearly what changed.

---

*The sibling document protects our outputs from ourselves. This document protects our inputs from whoever is trying to shape them. Same discipline, both directions.*
