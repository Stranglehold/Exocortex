# Narrative Stability — Design Note

**Status:** Design note. Pre-spec exploration.
**Motivated by:** SFA-001 ingestion audit (2026-04-14) — `contradict.py` scan produced 7 real retcons on first production cycle, including Reuters disagreeing with itself three ways on US-Iran negotiation status and AP silently revising CENTCOM force posture framing. The classifier works. The scoring collapses all retcons into one number and loses the signal that matters most: whether the source is updating facts as reality moves, or revising its own speculation to match new facts it should have known better than to commit to in the first place.
**Related systems:** Contradiction Detection (exists, `contradict.py`), Epistemic Integrity Layer (design note), Compound BST (topic_tags source).
**Depends on:** Claim extraction pipeline (`ingest.py`), existing `contradictions` table schema, topic taxonomy.

---

## The Problem

Current retcon detection asks one question: *did the same source contradict its own earlier claim?* If yes, it inserts a row in `contradictions` with a confidence score and nudges `sources.confidence_score` down by a small amount. That's one-dimensional.

The one-dimensional view mixes three different phenomena that mean opposite things:

1. **A source updating a live fact as reality moves.** "Casualty count was 12" → "casualty count was 15." This is what breaking news is supposed to do. Punishing it incentivizes stale reporting.

2. **A source silently revising a stable fact.** "The Pope's name is Leo XIII" → "the Pope's name is Leo XIV." Reality did not move; one of those claims was wrong. Error at best, dishonesty at worst.

3. **A source quietly rewriting its own speculation.** "We expect a ceasefire within 48 hours" → "no ceasefire is possible." The underlying world-state didn't falsify the first claim — the source just wants the record to read differently. This is narrative management.

The existing scoring can't distinguish these. A source that does #1 looks identical to a source that does #3. Both get the same `contradiction` row with similar confidence scores. Both move `confidence_score` the same amount. The most diagnostic signal — #3, speculation rewritten silently — is scored the same as the most innocent one.

Worse: #1 is the *expected* behavior of a functioning news source. If retcons on volatile facts are scored as credibility hits, the system will end up ranking dead outlets (who never update) above live ones (who do).

The analyst who reads the contradiction log gets a confused picture. Real signal is buried in false alarms. The whole feature becomes noise.

---

## The Insight

Every retcon pair has three orthogonal properties that determine what the retcon means:

- **Modality** — what kind of claim is this? A fact about the world? A speculation about the future? An editorial framing? An opinion?
- **Volatility** — does the referent of the claim move on its own? Casualty counts move; the Pope's identity doesn't; oil prices move fast; historical dates don't move at all.
- **Acknowledgment** — did the source announce the change, or silently publish the updated version as if the old one never existed?

The current schema captures one of these (acknowledgment, via `source_acknowledged: bool`). The other two are missing. Adding them is what turns retcon detection from a metric into a diagnostic.

---

## Design Principles

1. **The modality is the load-bearing axis.** Volatility and acknowledgment are multipliers. Modality determines whether a retcon is noise, a correction, or a narrative signal. Build the modality extraction first; volatility and acknowledgment are cheap additions on top.

2. **Extract modality at claim time, not at retcon time.** The LLM that extracts claims from an article already has the context to classify each claim. Adding one JSON field costs nothing (no extra LLM call) and means the modality is available for every claim whether or not it ever enters a retcon pair. This also unlocks downstream uses (modality-weighted search, opinion vs fact filtering in drift analysis) that aren't in scope here but become free.

3. **Deterministic volatility lookup.** Volatility is a property of the claim's *topic*, not of the claim itself. We already have `topic_tags` on every claim. A lookup table maps topic → volatility tier (high/medium/low). No LLM call. No per-claim reasoning. This keeps volatility cheap enough to compute on every claim without scaling concerns.

4. **Additive annotation, not replacement.** The existing `contradictions` table keeps all its columns. We add new columns for modality and signal classification. Old consumers of the table keep working; new consumers read the signal fields.

5. **Signal class is the primary output, not the raw triple.** Downstream consumers (source credibility update, analyst UI, SWARMFISH DI grounding) should read a single `signal_class` enum — not reason about the triple themselves. The triple is inputs; the class is what you act on.

6. **Graceful degradation.** If modality extraction fails (old LLM, schema drift, parse error), the retcon still gets recorded with `modality_unknown` and scored conservatively. Nothing in the pipeline breaks.

---

## The Signal Table

This is the core of the design. It maps (modality × volatility × acknowledgment) → signal class.

| modality     | volatility | acknowledgment | signal class        | what it means                                          |
|--------------|------------|----------------|---------------------|--------------------------------------------------------|
| fact         | high       | *              | `reality_update`    | Reality moved, source updated. Working as intended.    |
| fact         | medium     | acknowledged   | `honest_correction` | Source noticed its own error and said so.              |
| fact         | medium     | silent         | `silent_error`      | Error caught retroactively without acknowledgment.     |
| fact         | low        | acknowledged   | `honest_correction` | Stable-fact error, openly corrected. Unusual but ok.   |
| fact         | low        | silent         | `narrative_rewrite` | Stable fact silently revised. Error or dishonesty.     |
| speculation  | *          | acknowledged   | `healthy_update`    | Source said "we were wrong, here's why." Desirable.    |
| speculation  | *          | silent         | `narrative_rewrite` | Speculation silently rewritten. Primary dishonesty signal. |
| opinion      | *          | acknowledged   | `healthy_update`    | Editorial shift, openly framed as such.                |
| opinion      | *          | silent         | `narrative_rewrite` | Editorial position rewritten without marker.           |
| framing      | *          | *              | `editorial_drift`   | Same facts, shifted framing. Always a signal.          |
| unknown      | *          | *              | `uncategorized`     | Fallback. Scored conservatively, surfaced for review.  |

The three signal classes to care about operationally:

- `reality_update` and `honest_correction` and `healthy_update` — **near-zero credibility impact.** These are what functioning journalism looks like. Surface them in logs but don't penalize.
- `silent_error` — **moderate impact.** An error the source didn't notice or didn't own. Analyst should see it.
- `narrative_rewrite` and `editorial_drift` — **high impact.** This is the signal the whole system exists to catch. These should drive source credibility updates, appear in header alerts, and be surfaced to SWARMFISH's Devil's Inquisitor when the source is in the evidence ledger.

---

## Architecture: Four Components

### Component 1: Modality Extraction (at claim time)

**What changes:** One new field in the claim-extraction LLM schema in `ingest.py`:

```json
{
  "claim_text": "The Strait of Hormuz is under active US naval blockade",
  "modality": "fact",
  "topic_tags": ["iran-hormuz", "iran"]
}
```

**Values:**
- `fact` — a claim about the world's current or past state. "X happened." "Y is the case."
- `speculation` — a claim about the future, or about causal chains not yet resolved. "X will likely happen." "Y is expected to lead to Z."
- `opinion` — a value-laden assessment. "This is a good policy." "This is a catastrophe."
- `framing` — contested vocabulary or loaded presentation of an otherwise factual claim. "Freedom fighters" vs "insurgents." "Collateral damage" vs "civilian casualties."

**Prompt extension:** A short instruction added to the existing claim-extraction system prompt. Something like:

> For each claim, tag its modality:
> - `fact` if it states what happened, is happening, or has happened
> - `speculation` if it predicts, forecasts, or describes a causal chain that has not yet resolved
> - `opinion` if it expresses a value judgment (good/bad, right/wrong, success/failure as evaluation rather than outcome)
> - `framing` if the underlying fact is stated with loaded or contested vocabulary

**Failure handling:** If the LLM omits the field or returns an unexpected value, the claim is stored with `modality='unknown'` and processing continues.

**Cost:** Zero additional LLM calls. One additional JSON field in the existing extraction response. Minor prompt length increase.

### Component 2: Volatility Lookup

**What it does:** Maps topic tags to volatility tiers using a static lookup table.

**Schema:**

```python
TOPIC_VOLATILITY = {
    # High — facts change on the scale of hours to days
    "iran-hormuz":      "high",
    "casualty_counts":  "high",
    "oil_prices":       "high",
    "markets":          "high",
    "breaking_news":    "high",

    # Medium — facts change on the scale of weeks to months
    "iran":             "medium",
    "diplomacy":        "medium",
    "policy":           "medium",
    "elections":        "medium",

    # Low — facts change on the scale of years or not at all
    "history":          "low",
    "biography":        "low",
    "geography":        "low",
    "law":              "low",
}
```

**Resolution rule:** If a claim has multiple topic tags with different volatilities, take the *highest* volatility (most generous interpretation — assume reality may have moved).

**Where it lives:** `services/oss/src/volatility.py`, loaded once at startup. Hot-reloadable via `/admin/reload_volatility` endpoint if you want to tune without a restart.

**Default for unmapped topics:** `medium`. Erring toward "reality might have moved" is safer than erring toward "this should never have changed."

**Why not compute volatility with an LLM:** Because it's a property of the topic, not the claim. Computing it once per topic (in a lookup table) is vastly cheaper than computing it per claim, and the error rate on the deterministic approach is acceptable because the downstream scoring already weighs acknowledgment and modality heavily.

### Component 3: Retcon Classification Upgrade

**What changes in `contradict.py`:**

The existing `classify_contradiction()` LLM call already produces:
```json
{
  "relationship": "contradiction",
  "confidence": 0.95,
  "source_acknowledged": false,
  "reasoning": "..."
}
```

We extend the wrapper function `scan_new_claims()` to compute the signal class after classification:

```python
def classify_retcon_signal(claim_a: dict, claim_b: dict, classifier_result: dict) -> dict:
    """
    Given a contradiction pair and the base classifier output, compute
    the narrative stability signal class.

    Reads modality from each claim (recorded at extraction time).
    Looks up volatility from topic_tags via TOPIC_VOLATILITY.
    Reads acknowledgment from the classifier output.
    Returns a signal dict:
      {
        "signal_class":    "narrative_rewrite" | "reality_update" | ...,
        "modality_a":      "fact" | "speculation" | ...,
        "modality_b":      "fact" | "speculation" | ...,
        "volatility":      "high" | "medium" | "low",
        "signal_score":    0.0..1.0,
      }
    """
```

**Signal score:** A float in [0, 1] derived from the signal class:

| signal class        | score |
|---------------------|-------|
| `narrative_rewrite` | 1.0   |
| `editorial_drift`   | 0.9   |
| `silent_error`      | 0.6   |
| `uncategorized`     | 0.4   |
| `honest_correction` | 0.1   |
| `healthy_update`    | 0.05  |
| `reality_update`    | 0.0   |

This is what `update_source_confidence()` should read instead of counting raw retcons. A source racking up `reality_update`s pays nothing. A source racking up `narrative_rewrite`s pays proportionally.

### Component 4: Schema Extension

Add four columns to `contradictions`:

```sql
ALTER TABLE contradictions ADD COLUMN modality_a       text;
ALTER TABLE contradictions ADD COLUMN modality_b       text;
ALTER TABLE contradictions ADD COLUMN volatility       text;
ALTER TABLE contradictions ADD COLUMN signal_class     text;
ALTER TABLE contradictions ADD COLUMN signal_score     double precision;

CREATE INDEX idx_contradictions_signal ON contradictions(signal_class);
```

Add one column to `claims`:

```sql
ALTER TABLE claims ADD COLUMN modality text DEFAULT 'unknown';
CREATE INDEX idx_claims_modality ON claims(modality);
```

The default `'unknown'` means the migration is safe on historical rows — they get the fallback classification and can be re-scored later if modality is backfilled.

---

## Integration Points

### With source confidence update

The existing `update_source_confidence()` in `contradict.py` computes:

```python
adjustment = -silent_rate * 0.3 + (1.0 - silent_rate) * 0.02 + ack_rate * 0.01
```

Replace this with a signal-weighted version:

```python
# Sum of signal_scores over recent retcons / total_claims
narrative_penalty = sum(signal_scores) / max(total_claims, 1)
adjustment = -narrative_penalty * 0.3 + (1.0 - narrative_penalty) * 0.02
```

A source with ten `reality_update` retcons and zero `narrative_rewrite` retcons gets `narrative_penalty = 0` and actually *gains* confidence over time (the `+0.02` recovery term). Under the current logic, it would be punished.

### With SWARMFISH Devil's Inquisitor

When DI grounds its assessment in the evidence ledger, it should see a flag for any source whose recent retcons contain `narrative_rewrite` or `editorial_drift` on the relevant topic. This is the cleanest integration point because DI is already the layer that surfaces "the consensus is about to miss X" — and "this source has been silently rewriting its speculation on this topic" is exactly that kind of meta-fact.

Mechanism: extend the OSS→SWARMFISH bridge (`services/swarmfish/src/oss_bridge.py`) to attach a `narrative_stability_flags` field to the context summary when any retcon in the last 72h on the relevant topic scored `signal_class in ('narrative_rewrite', 'editorial_drift')`. DI reads this in its prompt template.

### With the analyst UI header badge

Add a fourth badge to the header badge row (after PENDING and SOURCE): `NARRATIVE` — fires when any `narrative_rewrite` or `editorial_drift` retcon landed in the last N hours. Click routes to a new Narrative tab that lists them grouped by source. Uses the same pulse animation pattern as the falsified-verdict badge.

The analyst UI does not need to show `reality_update` retcons at all — those are noise from the operator's perspective. Drift tab filters default to excluding them.

---

## What This Does NOT Do

- **It does not detect cross-source contradictions.** A source contradicting itself and two sources contradicting each other are different problems with different scoring properties (cross-source needs credibility weighting and coordination-pattern analysis). This design is strictly intra-source. Cross-source is a separate future component that can read the modality field once it exists but doesn't block on it.

- **It does not classify the specific *kind* of dishonesty.** The system says "this is a narrative rewrite." It does not say "this is motivated reasoning" or "this is coordinated framing" or "this is embarrassment management." Intent classification is out of scope and probably unsolvable at the mechanical layer.

- **It does not update historical claims.** The modality field backfills as `unknown`. Re-running extraction over the existing ~10k claims to populate modality is a separate one-shot migration, not part of this component.

- **It does not supersede the existing `confidence` field on contradictions.** Signal score and contradiction confidence are orthogonal — a `narrative_rewrite` with 0.6 classifier confidence is different from a `narrative_rewrite` with 0.95 classifier confidence. Both fields stay.

- **It does not do claim-modality learning.** The LLM's modality tag is trusted as-is. No separate calibration pass, no drift detection on modality classification, no fine-tuning. If modality tagging quality becomes a problem later, that's a separate investigation.

- **It does not attempt to detect retcons across different phrasings when the claims aren't semantically similar.** The existing FAISS similarity pre-filter in `contradict.py` decides which pairs go to the LLM classifier. We don't touch that logic. If two retconned claims don't embed close to each other, the system still misses them — that's an existing limitation that predates this design.

---

## Configuration

```python
# services/oss/src/contradict.py

# Maps signal_class to signal_score. Tunable.
SIGNAL_SCORES = {
    "narrative_rewrite":  1.0,
    "editorial_drift":    0.9,
    "silent_error":       0.6,
    "uncategorized":      0.4,
    "honest_correction":  0.1,
    "healthy_update":     0.05,
    "reality_update":     0.0,
}

# Default volatility for unmapped topics.
DEFAULT_VOLATILITY = "medium"

# Window for "recent retcons" that feed into source confidence update.
NARRATIVE_WINDOW_DAYS = int(os.environ.get("OSS_NARRATIVE_WINDOW_DAYS", "14"))

# Header badge window — narrative events in the last N hours surface as an alert.
NARRATIVE_BADGE_WINDOW_HOURS = int(os.environ.get("OSS_NARRATIVE_BADGE_HOURS", "72"))
```

---

## Testing Criteria

Each assertion is specific and falsifiable. The component is working when all of these hold:

1. **Modality extraction.** Given an article with one factual sentence ("The ship left port at 0600"), one speculative sentence ("Analysts expect the fleet to arrive by Friday"), and one opinion sentence ("This deployment is a strategic catastrophe"), the claim extraction produces three claims with modalities `fact`, `speculation`, `opinion` respectively. Tolerance: 90% agreement with a human-coded ground truth across 50 sample articles.

2. **Volatility lookup correctness.** For every topic in the taxonomy, `get_volatility(topic)` returns a tier. For unmapped topics, it returns `"medium"`. No exceptions raised.

3. **Signal class determinism.** Given fixed (modality_a, modality_b, volatility, acknowledgment) inputs, `classify_retcon_signal()` returns the same signal class across repeated runs. Pure function. No LLM.

4. **Pope Leo XIII reclassification.** The existing contradiction from the ingestion audit (AP claiming Pope Leo XIII engaged with the Trump administration) must classify as `silent_error` (fact, low volatility, silent) under the new scheme. Not `reality_update`, not `honest_correction`.

5. **Reuters negotiation-status reclassification.** The three Reuters contradictions on US-Iran negotiation status ("ongoing" vs "may resume" vs "needs resumption") must classify as `narrative_rewrite` (speculation, silent) — not `silent_error`, because these are forward-looking assessments, not historical facts.

6. **Source confidence unchanged on pure reality updates.** If a source accumulates 10 retcons all scored `reality_update`, `update_source_confidence()` moves the score by ≤0.02 (the recovery term only). Not downward.

7. **Source confidence moved on pure narrative rewrites.** If a source accumulates 10 retcons all scored `narrative_rewrite` against 100 total claims, `update_source_confidence()` moves the score downward by ≥0.02.

8. **Graceful degradation on missing modality.** If a claim has `modality = 'unknown'`, the retcon involving it classifies as `uncategorized` and the pipeline continues. No crash.

9. **Backward compatibility.** Existing queries against `contradictions` that don't read the new columns return the same rows they did before the migration.

---

## Open Questions

These are things I don't know yet and the spec should not pretend to decide.

- **Modality extraction quality under the production LLM.** The current ingest model is `qwen/qwen3-4b-2507` — a 4B parameter model tuned for extraction. Whether it reliably distinguishes `fact` from `speculation` at scale is an empirical question. If it doesn't, two options: (a) move modality extraction to the 27B reasoning model, paying the cost; (b) do modality extraction with a second, smaller classifier pass. I'd check (a) first because it's cheapest — one prompt extension, no new model.

- **Volatility table maintenance.** The lookup table will get stale as topics evolve. Probably wants a governance section later — who gets to add topics, how changes are reviewed, whether there's a hot-reload path. Punt until the table has >50 entries.

- **Where `framing` retcons show up.** Framing retcons are the highest-signal class in the table, but they're also the hardest for the LLM to identify at extraction time. It may be that `framing` is never reliably tagged at claim extraction and is only detectable at retcon time (by comparing the vocabulary of the two claims after the classifier has paired them). If so, `framing` moves from component 1 to component 3.

- **Interaction with the Epistemic Integrity layer's temporal volatility.** EI already has a concept of "how fast does this kind of knowledge change" for staleness detection. There may be a shared volatility table between EI and this component. Not yet decided which owns it, but a shared source is cleaner than two parallel tables drifting apart.

- **Historical backfill strategy.** 10k existing claims with `modality = 'unknown'`. Re-extracting is expensive but straightforward. Whether to batch it during quiet hours, run it against a checkpointed subset, or skip historical backfill entirely and only score forward is a scope question that affects how much of the corpus the signal covers.

---

## Research Lineage

- **"Silent revision" as a journalism concept.** Craig Silverman's work at Poynter / BuzzFeed (2012 onward) documented the pattern of news outlets silently editing articles after publication to fix errors without acknowledgment, and the credibility cost this imposes on the ecosystem. The distinction between "silent correction" and "acknowledged correction" is standard in media studies.

- **Epistemic modality in NLP.** Saurí & Pustejovsky (2009), "FactBank: a corpus annotated with event factuality" — the paradigmatic corpus for fact / speculation distinction in text. The modality categories used here (fact / speculation / opinion / framing) are simpler than FactBank's but in the same tradition.

- **Temporal volatility of knowledge.** Kasai et al. (2022), "RealTime QA: What's the Answer Right Now?" — empirical validation that model knowledge staleness varies dramatically by topic, with high-volatility topics failing much faster than low-volatility ones. This is the same distinction used for the volatility lookup here.

- **Internal consistency as a credibility metric.** Wu et al. (2023), "Fake News Detection Through Temporal Self-Contradiction" — proposes using within-source temporal contradictions as a credibility signal, empirically outperforming cross-source comparison for some detection tasks. This paper is the closest external precedent for the approach, though it doesn't make the modality distinction.

- **Exocortex internal.** The Epistemic Integrity design note established the three-axis framing for fact-level annotations (provenance, volatility, temporal distance). This design reuses the volatility axis and adds two complementary axes (modality, acknowledgment) that operate on pair-level phenomena rather than claim-level ones. The two components are complementary, not redundant.

---

## Build Order (when we come back to this)

1. Schema migration — add `modality` to claims, four columns to contradictions. Safe and reversible.
2. Volatility lookup module with an initial 20-topic table. Smoke test in isolation.
3. Modality extraction — extend the ingest LLM prompt, add the field to the extraction schema, handle the fallback. Run on one source for 24h, spot-check quality.
4. `classify_retcon_signal()` function — pure logic, easy to unit test against the signal table.
5. Wire the new signal into `scan_new_claims()` — each contradiction insert now writes the new columns.
6. Rewrite `update_source_confidence()` to read `signal_score` instead of counting raw retcons.
7. SWARMFISH bridge extension — attach `narrative_stability_flags` to the context summary.
8. Analyst UI NARRATIVE header badge + Narrative tab.

Each step is deployable in isolation. The pipeline produces correct behavior at every intermediate state — the new columns are additive, old code ignores them, new code reads them conservatively when they're `NULL`.

---

*This document is pre-spec. It describes what to build and why, not the exact file structure or install scripts. When the decision to build lands, this becomes the input to an L3 spec.*
