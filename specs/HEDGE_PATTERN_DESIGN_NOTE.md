# Hedge Pattern Detection — Design Note

**Status:** Design note. Pre-spec exploration. **Updated 2026-04-14 after walk-through** — the five open questions were resolved in conversation and the note was revised to capture three architectural additions: a third claim-level field (`quoted_directly`), source-type-conditional signal routing (`narrative_campaign` for institutional sources, `unverifiable_stream` for social sources), and a paraphrase-rate per-source credibility signal. See "Walk-through Resolution Notes" section for the full decision trail.
**Motivated by:** Jake's observation during the narrative stability deployment — the retcon detector is structurally blind to the most insidious form of narrative management, which is **hedged assertion attributed to vague sources**. The technique plants an idea in the reader's mind as if asserted, but no commitment is ever made, so no retcon is required. The claim stream looks clean under retcon analysis even though the narrative is being actively shaped.
**Related systems:** Narrative Stability (shipped 2026-04-14), Input Scrutiny Research Note (2026-04-14), Adversarial Input Layer Design Note (2026-04-14), Epistemic Integrity Layer (design note), Compound BST (topic_tags source).
**Depends on:** Claim extraction pipeline (`ingest.py`), topic taxonomy, `claims` table with `modality` field, `sources` table with `source_type` field.

---

## The Problem

The narrative stability work we deployed tonight catches one half of narrative management: silent revision of previously-committed claims. It does not catch the other half — **silent implantation of claims that were never committed in the first place.**

An example, from tonight's corpus:

> "Sources familiar with the matter suggest Iran **may** be weeks away from a nuclear breakout."

This is a single claim, published once, never retconned. Under retcon analysis it produces zero signal. Under modality analysis it correctly tags as `speculation`. Under the existing narrative stability framework it would only fire if the source later contradicted it — which the source will never do, because the whole point of the claim's construction is that it was never committed to in the first place. If pressed, the outlet retreats behind "we only said sources suggested it might." If the underlying fact never materializes, nobody retracts because nobody asserted.

This is not an error case or an edge case. It is the **dominant pattern** of narrative management in modern news writing. It operates at claim time, not retcon time, and it requires a different kind of detector.

The technique has four features working together:

1. **Modal hedging** — "may," "could," "might," "appears to," "is thought to."
2. **Epistemic adverbs** — "possibly," "reportedly," "allegedly," "purportedly."
3. **Vague attribution** — "sources," "officials," "analysts," "people familiar with the matter."
4. **Topic concentration** — the same source repeatedly hedging the same topic without ever committing to it or walking it back.

No single one of these is damning. Scientists hedge. Cautious analysts hedge. Real unnamed sources exist. Honest forecasters use "could" when they mean "could." The signal is in the **combination** and the **concentration**, not in any single instance.

---

## The Insight — Three Orthogonal Axes

Modality asks *what kind of claim is this?* The new axes ask *how much is the source actually committing to it, who is the source willing to name, and did the source preserve the speaker's exact words?*

These are independent of modality and of each other:

- **Certainty** — the commitment level of the proposition as stated. Committed / hedged / unknown.
- **Attribution** — the source-of-information clause the outlet offered. Named / vague / absent / unknown.
- **Quoted directly** — whether the proposition appeared in direct quotation in the original article, or was paraphrased into the outlet's own voice. True / false / n/a.

Every claim sits somewhere in (modality × certainty × attribution × quoted_directly) space:

| claim | modality | certainty | attribution | quoted_directly |
|---|---|---|---|---|
| "Six merchant ships turned around." | fact | committed | absent | n/a (no attribution) |
| "Reuters reporters observed six ships turning around." | fact | committed | named | n/a (outlet is the speaker) |
| `Biden said: "The blockade may collapse within 72 hours."` | speculation | hedged | named | **true** |
| "Biden said the blockade could fall within three days." | speculation | hedged | named | **false** (paraphrase) |
| "Sources say six ships turned around." | fact | committed | vague | false |
| "Six ships **may** have turned around." | fact | hedged | absent | n/a |
| "Sources **suggest** six ships **may** have turned around." | fact | hedged | vague | false |
| "The blockade will collapse within 72 hours." | speculation | committed | absent | n/a |
| "**Analysts expect** the blockade **could** collapse within 72 hours." | speculation | hedged | vague | false |
| "Iran **is said to be** weeks away from nuclear breakout." | speculation | hedged | absent (agent-deletion) | false (implicit paraphrase) |

Rows 5 and 7-10 are the pattern we want to catch. They share a structural feature: **an assertion is being made while the outlet maintains deniability about having made it.** The reader processes the claim as if asserted. The outlet retains the ability to say "we only said it might."

Committed speculation is normal journalism. Hedged speculation attributed to named sources *and preserved as a direct quotation* is normal journalism — that's just accurate reporting of someone else's hedge. Hedged speculation attributed to vague sources and delivered as paraphrase, repeated on the same topic, is narrative management.

**The third axis matters because paraphrase introduces a translation layer.** A direct quote is verifiable against transcript; a paraphrase is the outlet's word choice, and word choice drift is where meaning management hides. A source that consistently paraphrases rather than quoting directly is carrying more translation-layer risk per claim than one that quotes verbatim. This is orthogonal to hedging and attribution — a source can quote a hedged statement directly (honest) or paraphrase a committed statement into a hedged one (drift).

---

## Design Principles

1. **Three claim-level fields, not one composite.** Certainty, attribution, and quoted_directly are orthogonal — a claim can be committed with vague attribution ("Sources say six ships turned around"), hedged with no attribution at all ("Six ships may have turned around"), or a directly-quoted hedge from a named speaker (`Biden said: "The blockade may collapse"`). Combining them into a single composite field collapses information that the downstream signal logic needs. Three fields. Stored independently. Filterable independently.

2. **Deterministic first for certainty and attribution; LLM-upstream for quoted_directly.** Hedge and attribution markers are **lexical**, and regex beats LLM-based detection for that category — patterns like "may," "could," "sources familiar with," "is said to" are explicit linguistic markers. But `quoted_directly` is different: by the time a claim reaches the regex layer it has already been paraphrased by the extraction LLM into third-person normalized form, and the quotation-boundary information is gone. The `quoted_directly` field therefore has to be captured at extraction time by the same LLM that is doing the paraphrasing, reading the raw article text. This is a meaningful architectural asymmetry: certainty + attribution are regex-primary with LLM cross-check; quoted_directly is LLM-only because the regex layer literally cannot see the evidence it would need. See "The Hard Cases: Quoted speech" for why an earlier version of this document got this wrong.

3. **The signal is relational, not absolute.** A claim being hedged+vague is not a signal on its own. Thousands of legitimate news claims are hedged+vague because the underlying facts are genuinely unsettled. The signal is *per-source, per-topic, relative to that source's baseline.* If Reuters hedges 30% of claims across all topics but 80% on iran-hormuz specifically, the deviation is the signal. If Reuters hedges 80% everywhere, that's just Reuters. **Hedge rate concentration — not hedge rate — is the diagnostic.**

4. **The alert is aggregated, not per-claim.** Firing a UI alert on every hedged high-volatility claim would flood the analyst. Instead, tag every claim with certainty, attribution, and quoted_directly, then run a periodic aggregation query that identifies (source, topic) pairs with anomalous hedge-vague-paraphrase concentration. The individual claims are visible to the analyst when they drill in. The alert itself is at the campaign level, not the sentence level.

5. **Quoted speech belongs to the speaker; paraphrase belongs to the outlet.** When a raw article reads `Biden said: "The blockade may collapse"`, Biden owns the hedge and the outlet is committed to the fact that Biden said it verbatim. When the article reads `Biden said the blockade could fall within three days`, the outlet has introduced its own word choices into the proposition — the hedge ("could") and the specificity ("three days") are now the outlet's, not Biden's. **The outlet's paraphrasing is itself a first-class credibility signal.** Sources that paraphrase more carry more translation-layer risk per claim and should take a proportional credibility hit even before hedge-concentration signals fire. The mechanism is the paraphrase rate derived statistic in "Integration with the Existing Retcon Signal Table" below.

6. **Source-type-conditional signal routing.** The same (source, topic) hedge-vague concentration means opposite things depending on the source's verification model. A major institutional outlet citing "senior administration officials" at high concentration on iran-hormuz is the access-journalism narrative-management pattern. A solo OSINT account citing "my contact on the ground" is how verification works when you're physically present — their credibility *is* their unnamed sourcing. The framework cannot treat these the same or it'll cry wolf on exactly the sources worth listening to. The signal class that fires is gated on `sources.source_type`: **`narrative_campaign`** (high severity) for `official | wire | outlet`; **`unverifiable_stream`** (informational flag, not alert) for `social`.

7. **Legitimate hedging must not be punished.** Scientists hedge. Intelligence analysts hedge. Responsible forecasters use "could." The framework cannot flag all hedging as suspicious or it becomes a tax on epistemic honesty. The only way to distinguish narrative-management hedging from calibrated uncertainty is *over time and across topics*. Single-claim detection will be wrong. The concentration signal (Principle 3) combined with the source-type routing (Principle 6) is the only defensible way to draw the line.

---

## The Three Fields

### `certainty: committed | hedged | unknown`

The commitment level of the proposition as stated by its speaker (whether the outlet or a quoted source).

- **committed** — declarative assertion. No modal hedges, no epistemic adverbs, no "is said to" constructions.
  - "Six merchant ships turned around."
  - "The US Navy deployed three carriers to the Persian Gulf."
  - "Iran announced a new uranium enrichment facility."
- **hedged** — the proposition is softened by at least one of the following:
  - Modal verbs in conditional sense: may, might, could, would, should
  - Epistemic adverbs: possibly, probably, allegedly, reportedly, supposedly, purportedly, apparently, seemingly, ostensibly, arguably
  - Hedge verbs: suggests, indicates, appears to, seems to, is said to, is thought to, is understood to, is believed to, is expected to
  - Weakening qualifiers: somewhat, rather, perhaps
- **unknown** — fallback for ambiguous cases. Not a failure, just an honest declination to classify.

### `attribution: named | vague | absent | unknown`

Who the outlet cites as the source of the claim.

- **named** — specific, verifiable attribution.
  - "Secretary Austin said..."
  - "According to the Iranian Foreign Ministry..."
  - "Reuters' own reporting..."
  - "A Defense Department press release..."
- **vague** — non-specific, non-verifiable attribution. The archetypal "source" clauses.
  - "Sources say / indicate / suggest / believe / expect"
  - "Officials said / told Reuters / said on condition of anonymity"
  - "People familiar with the matter"
  - "Analysts expect / experts warn / experts believe"
  - "A senior administration official" (without name)
  - "Western intelligence sources"
  - "Diplomatic sources"
- **absent** — the outlet makes the claim in its own voice, with no attribution clause at all. This is not inherently bad — direct observation reporting looks like this.
  - "Six ships turned around."
  - "The blockade continues."
- **unknown** — fallback.

### `quoted_directly: true | false | n/a | unknown`

Whether the claim's proposition appeared in direct quotation in the source article — that is, whether the outlet preserved the speaker's exact words rather than paraphrasing them into its own voice.

- **true** — the proposition was presented inside quotation marks (or block-quoted) in the source article, attributed to a speaker. The outlet committed only to the fact *that the speaker said this*, and the speaker's exact words are preserved and verifiable.
  - `Biden said: "The blockade may collapse within 72 hours."` → `{certainty: hedged, attribution: named, quoted_directly: true}`
  - `The Iranian spokesperson told Reuters, "We have no intention of closing the Strait."` → `{certainty: committed, attribution: named, quoted_directly: true}`
- **false** — the proposition was rendered in the outlet's own voice with attribution to a speaker. The outlet's word choice replaces the speaker's. This is where translation-layer drift hides.
  - "Biden said the blockade could fall within three days." → `{certainty: hedged, attribution: named, quoted_directly: false}`
  - "Sources suggest the blockade may collapse within 72 hours." → `{certainty: hedged, attribution: vague, quoted_directly: false}`
- **n/a** — the claim has no speaker attribution at all; the outlet is making the claim in its own voice ("Six ships turned around"). There is no speaker whose words could be quoted or paraphrased, so the distinction doesn't apply. This is distinct from `unknown`.
- **unknown** — fallback for ambiguous cases (malformed article text, mixed direct-indirect speech, scraping artifacts).

**Why this field cannot be regex-derived downstream.** By the time the scrutiny layer sees the `claims.claim_text` field, the extraction LLM has already paraphrased the raw article into third-person normalized form. The quotation marks are gone. The information about whether Biden's statement was presented as a direct quote or a paraphrase has been discarded. This means `quoted_directly` has to be captured at extraction time, by the same LLM that is doing the paraphrasing, while it is still looking at the raw article text. See Detection Mechanism section below for the specific approach.

---

## Detection Mechanism

### Regex layer (primary)

A small, maintainable set of pattern groups. Each matches a specific linguistic construction.

```python
CERTAINTY_PATTERNS = {
    "modal_hedge": re.compile(
        r"\b(may|might|could|would|should|can)\s+(?:be|have|not)?\b", re.I
    ),
    "epistemic_adverb": re.compile(
        r"\b(possibly|probably|allegedly|reportedly|supposedly|purportedly|"
        r"apparently|seemingly|ostensibly|arguably|presumably)\b", re.I
    ),
    "hedge_verb": re.compile(
        r"\b(suggests?|indicates?|appears?\s+to|seems?\s+to|"
        r"is\s+(?:said|thought|understood|believed|expected)\s+to|"
        r"are\s+(?:said|thought|understood|believed|expected)\s+to)\b", re.I
    ),
    "weakener": re.compile(
        r"\b(somewhat|rather|perhaps|possibly)\b", re.I
    ),
}

ATTRIBUTION_PATTERNS = {
    "vague_source": re.compile(
        r"\b(sources?|officials?|analysts?|experts?|insiders?)\s+"
        r"(?:say|said|suggest|suggested|indicate|indicated|believe|believed|"
        r"expect|expected|warn|warned|told)\b", re.I
    ),
    "vague_familiar": re.compile(
        r"\b(?:people|sources?|individuals?|officials?)\s+familiar\s+with\b", re.I
    ),
    "anonymous_official": re.compile(
        r"\b(a|an|the)?\s*(?:senior|high-ranking|senior-level)?\s*"
        r"(?:administration|government|official|diplomatic|intelligence|military)\s+"
        r"(?:official|source|spokesperson)\b", re.I
    ),
    "condition_of_anonymity": re.compile(
        r"\bon\s+(?:the\s+)?condition\s+of\s+anonymity\b", re.I
    ),
    "named_source": re.compile(
        # Proper noun + speech verb — simplified, catches the common cases
        r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+"
        r"(?:said|stated|announced|told|confirmed|denied|declared)\b"
    ),
}
```

### Scoring logic

```python
def classify_certainty(claim_text: str) -> str:
    matches = sum(
        1 for p in CERTAINTY_PATTERNS.values()
        if p.search(claim_text)
    )
    if matches == 0:
        return "committed"
    if matches >= 1:
        return "hedged"
    return "unknown"


def classify_attribution(claim_text: str) -> str:
    # Check vague first (more specific), then named, then absent
    vague = any(
        ATTRIBUTION_PATTERNS[k].search(claim_text)
        for k in ("vague_source", "vague_familiar", "anonymous_official",
                  "condition_of_anonymity")
    )
    if vague:
        return "vague"
    named = ATTRIBUTION_PATTERNS["named_source"].search(claim_text) is not None
    if named:
        return "named"
    return "absent"
```

The classifier is deliberately conservative. The default is `committed` (no hedge) or `absent` (no attribution). Hedges fire when explicit markers appear. This keeps false positives low and means the downstream concentration signal only accumulates on clear linguistic evidence.

### LLM cross-validation (certainty and attribution)

The claim-extraction prompt also tags `certainty` and `attribution` per claim (one field each, five total fields including modality and quoted_directly). When the LLM's tag disagrees with the regex on certainty or attribution, **the regex wins** and the disagreement is logged to a `tagging_disagreements` table for periodic review. This is the calibration mechanism — we learn where regex is brittle without letting LLM noise overwrite a transparent deterministic signal.

### LLM-only capture (quoted_directly)

The `quoted_directly` field is different. The regex layer sees the paraphrased claim text, not the original article — so there's no lexical evidence of quotation preservation to detect. By the time a claim reaches regex, the quotation boundary has already been destroyed by the extraction step.

The only place in the pipeline that can observe whether the original article used direct quotation is the extraction LLM itself, while it is reading the raw article text. So the extraction prompt carries an additional instruction: for each extracted claim, report whether the proposition appeared inside quotation marks in the original article, attributed to the speaker. The LLM tags `quoted_directly` at the same time it does modality and paraphrases into third-person.

This is an architectural asymmetry worth naming: **certainty and attribution are post-paraphrase observable (they survive the rewrite); quoted_directly is pre-paraphrase-only (the rewrite destroys it).** The design has to capture it at the right layer or lose it permanently. A v2 improvement could also preserve the original quote span as a separate field (`original_quote_text`) for downstream verification, but v1 just stores the boolean.

**Failure mode:** if the LLM fails to tag `quoted_directly` or returns an ambiguous value, the field defaults to `unknown` rather than `n/a` or `false`. Downstream aggregation queries filter on `quoted_directly IN ('false', 'unknown')` when counting paraphrases, so an unknown gets treated conservatively as potentially-paraphrased. The logic prefers false positives on "this might be a paraphrase" over silent exclusion.

---

## The Standalone Signals: `narrative_campaign` and `unverifiable_stream`

This is the new thing. And the routing is source-type-conditional — the same underlying statistic surfaces as two different signal classes depending on the source's verification model. This is Principle 6 from Design Principles above.

### What it measures

For each (source, topic) pair over a rolling window, compute the fraction of claims that are **hedged AND vague-attributed AND not quoted directly**. Compare that fraction against the source's overall rate across all topics. Deviations above a threshold on high/medium-volatility topics are candidates — but the signal class that fires depends on `sources.source_type`.

```sql
-- Per-source-per-topic hedge density, rolling 7 days
-- Factors in all three claim-level fields AND source type
WITH topic_stats AS (
    SELECT
        c.source_id,
        s.source_type,
        unnest(c.topic_tags) AS topic,
        COUNT(*) AS claim_count,
        COUNT(*) FILTER (
            WHERE c.certainty = 'hedged'
              AND c.attribution = 'vague'
              AND c.quoted_directly IN ('false', 'unknown')
        ) AS insidious_count
    FROM claims c
    JOIN sources s ON c.source_id = s.id
    WHERE c.extracted_at >= NOW() - INTERVAL '7 days'
    GROUP BY c.source_id, s.source_type, unnest(c.topic_tags)
),
source_baseline AS (
    SELECT
        source_id,
        AVG(insidious_count::float / NULLIF(claim_count, 0)) AS baseline_rate
    FROM topic_stats
    GROUP BY source_id
)
SELECT
    ts.source_id,
    ts.source_type,
    ts.topic,
    ts.claim_count,
    ts.insidious_count,
    (ts.insidious_count::float / NULLIF(ts.claim_count, 0)) AS topic_rate,
    sb.baseline_rate,
    (ts.insidious_count::float / NULLIF(ts.claim_count, 0)) - sb.baseline_rate AS deviation,
    CASE
        WHEN ts.source_type IN ('official', 'wire', 'outlet') THEN 'narrative_campaign'
        WHEN ts.source_type = 'social'                        THEN 'unverifiable_stream'
        ELSE 'unclassified'
    END AS signal_class
FROM topic_stats ts
JOIN source_baseline sb USING (source_id)
WHERE ts.claim_count >= 5
ORDER BY deviation DESC;
```

Note the filter: `quoted_directly IN ('false', 'unknown')`. Direct quotes with named speakers do NOT count toward the insidious pattern — even if they're hedged, because the outlet is reporting someone else's hedge verbatim rather than paraphrasing it into the outlet's own voice. Named+quoted hedges are exactly the exculpating pattern.

### Threshold

A (source, topic) pair fires a signal when:

- `claim_count >= 5` (minimum sample — below this we don't have enough to judge)
- `topic_rate >= 0.4` (at least 40% of claims on this topic match the insidious combination)
- `topic_rate - baseline_rate >= 0.25` (topic is at least 25 percentage points above the source's own baseline)
- `topic_volatility IN ('high', 'medium')` (low-volatility topics rarely need hedging, so skewed hedging there is almost certainly noise)

These thresholds are initial guesses. The validation loop: run the query against the current corpus, hand-audit the top 20 (source, topic) pairs for whether they look like real campaigns or measurement artifacts, adjust.

### Signal class routing — the source-type split

**`narrative_campaign`** — fires for `source_type IN ('official', 'wire', 'outlet')`.

Interpretation: this institutional source is concentrating hedged, vaguely-attributed, paraphrased claims on this topic beyond its own editorial baseline. This is the access-journalism narrative-management pattern — the source has institutional resources to verify and name but is choosing not to, and the pattern is topic-specific, which is what distinguishes it from general editorial style.

UI surfacing: **fourth header badge next to PENDING, SOURCE, and NARRATIVE**. Click routes to a per-source-per-topic breakdown with the underlying claim list. The Devil's Inquisitor in SWARMFISH should also read `narrative_campaign` signals when assembling its evidence context — if the committee's consensus is being fed by claims from a source currently flagged on the relevant topic, DI should note it in `consensus_warning`.

**`unverifiable_stream`** — fires for `source_type = 'social'`.

Interpretation: this solo/social source is concentrating claims we can't independently verify on this topic. Unlike institutional outlets, the absence of named sourcing doesn't automatically indicate narrative management — a solo OSINT account physically present in a conflict zone legitimately can't name its contacts without burning them, and its credibility *is* its unnamed sourcing. The right framing for an analyst reading a social source in this state is: *"take this stream as a lead, not a confirmed finding — it may be high-signal, but it can't be independently verified."*

UI surfacing: **informational caveat, not an alert**. Displayed inline on the source's claims list as a badge ("unverifiable stream — weight accordingly") but does not fire the header alert system. The analyst sees the pattern when they're reading the source's contributions; they don't get paged about it.

The distinction between alert and caveat is important: **the same statistic, different routing, because the signal means different things depending on the verification model.** This prevents the framework from crying wolf on exactly the OSINT sources worth listening to, while preserving the sharp alert on institutional outlets doing access-journalism narrative management.

### A note on per-source calibration beyond source_type

Source_type is a coarse filter. Within `social`, some accounts are far more credible than others — Rerum Novarum's ground reporting is not equivalent to an anonymous troll account, even though both share the source_type tag. The existing `sources.confidence_score` field is the finer-grained signal that can differentiate them. v1 of this design uses source_type for signal routing only. v2 can add a confidence_score threshold within `social` — highly trusted social sources get the `unverifiable_stream` caveat, low-trust social sources get something more like the institutional alert. But that requires per-source confidence calibration we don't have yet for most accounts. Leave as open question.

---

## Integration with the Existing Retcon Signal Table

Two integrations. The first is a multiplier on retcon signal scoring. The second is a new per-source derived statistic — **paraphrase rate** — that feeds directly into source confidence alongside the narrative-stability signal.

### Certainty modifier on retcon signal

The retcon signal table from the narrative stability work gets extended with a certainty modifier. Hedged claims being retconned are **less culpable** than committed ones — the hedge was already a disclaimer. Rule:

```python
def apply_certainty_modifier(signal_score: float, certainty_a: str, certainty_b: str) -> float:
    """
    Reduce retcon signal when the retconned claim was already hedged.
    A hedge is a partial disclaimer; retconning a hedge is less dishonest
    than retconning a committed assertion.
    """
    if certainty_a == "hedged" and certainty_b == "hedged":
        return signal_score * 0.5  # both hedged → half weight
    if certainty_a == "hedged" or certainty_b == "hedged":
        return signal_score * 0.75  # one hedged → three-quarter weight
    return signal_score  # both committed → full weight
```

The hedge discount applies AFTER the existing signal_class classification. A hedged-speculation silent retcon still scores as `narrative_rewrite`, but at 0.5× the base score. This means the *signal class is still diagnostic* (the analyst sees it was a narrative rewrite) but the *source confidence hit is proportional to commitment level* (a hedger takes less damage than a committer).

This also prevents the perverse incentive where the current system would treat "we always hedge everything" as a safer strategy than "we commit when we know and retract when we're wrong."

### Paraphrase rate as a per-source credibility statistic

Independent of retcon scoring, every source accumulates a paraphrase rate statistic computed over its attributed claims:

```sql
-- Per-source paraphrase rate, rolling 30 days
SELECT
    source_id,
    COUNT(*)                                   AS attributed_claim_count,
    COUNT(*) FILTER (WHERE quoted_directly = 'true') AS quoted_count,
    COUNT(*) FILTER (WHERE quoted_directly = 'false') AS paraphrased_count,
    (
        COUNT(*) FILTER (WHERE quoted_directly = 'false')::float
        / NULLIF(COUNT(*) FILTER (WHERE quoted_directly IN ('true', 'false')), 0)
    ) AS paraphrase_rate
FROM claims
WHERE attribution IN ('named', 'vague')       -- only attributed claims count
  AND extracted_at >= NOW() - INTERVAL '30 days'
GROUP BY source_id;
```

Sources with high `paraphrase_rate` are introducing more translation-layer risk per claim — they're rewriting speakers' statements into their own words instead of preserving the speaker's exact phrasing. Even if no specific paraphrase is demonstrably wrong, the cumulative risk is real.

**Credibility adjustment.** The source's confidence_score takes a small proportional hit based on paraphrase rate:

```python
def apply_paraphrase_rate_penalty(base_confidence: float, paraphrase_rate: float) -> float:
    """
    Scale source confidence by translation-layer risk.
    A source with 100% direct quotes takes no penalty.
    A source with 100% paraphrases takes a 10% penalty.
    Intermediate rates scale linearly.

    The penalty is intentionally small — paraphrasing is a legitimate
    journalistic choice and shouldn't be punished as severely as silent
    retconning. But it does carry risk and should not be free.
    """
    penalty = 0.10 * paraphrase_rate
    return max(0.1, base_confidence - penalty)
```

Why 10% maximum? Because paraphrase is not inherently dishonest — it's a legitimate stylistic choice with well-documented tradeoffs. The penalty should discourage excessive paraphrasing relative to direct quotation without treating paraphrasing itself as a form of deception. First-pass value. Retune on data.

**The important asymmetry:** retcon signal scores hit the source confidence hard (up to 30% penalty from the narrative stability work). Paraphrase rate scores it softly (up to 10%). Silent retconning is a direct violation of journalistic honesty; paraphrasing is a translation-layer risk that may or may not materialize as actual drift. The penalty structure reflects that difference.

**What this catches that retcon scoring doesn't.** A source can paraphrase everything, never retcon anything (because it was never committed), and under the pre-paraphrase-rate framework would look clean — no walkbacks, no silent revisions. The paraphrase-rate statistic surfaces the translation-layer risk that pure retcon detection misses. It's a third axis of source credibility alongside (a) factual accuracy and (b) narrative stability.

---

## The Hard Cases

### Quoted speech — corrected after walk-through

**This entry has been rewritten.** An earlier version of this document claimed that the extraction pipeline's paraphrasing step "already handles" quoted speech correctly because the paraphrase preserves the speaker's hedge. That was wrong, and Jake's Q4 pushback exposed why: **paraphrasing is itself a noise vector**, and the information about whether a proposition was originally presented as a direct quote or as an outlet-voiced paraphrase is destroyed by the extraction step. What the earlier version described as "handling it" was actually losing the distinction silently.

**The real problem:** `Biden said: "The blockade may collapse within 72 hours"` and `Biden said the blockade could fall within three days` produce nearly identical tagged claims under the old design — both would get `{certainty: hedged, attribution: named}`. But these are different epistemic acts. The first is Reuters committed to transcript-verifiable speech; Biden owns the hedge and Reuters is committed to Biden having said those exact words. The second is Reuters' word choice replacing Biden's — "could," "three days," the whole softening — and Reuters becomes responsible for the framing drift from whatever Biden actually said.

**The corrected resolution** is the `quoted_directly` field introduced in "The Three Fields" section above. The extraction LLM tags `quoted_directly` at the moment it paraphrases, while it still has access to the raw article text and its quotation marks. Downstream scoring then treats the four combinations differently:

| claim shape | example | signal |
|---|---|---|
| `hedged + named + quoted_directly=true` | `Biden said: "The blockade may collapse"` | Clean. Outlet preserved speech verbatim, attribution is verifiable. Excluded from `narrative_campaign`. |
| `hedged + named + quoted_directly=false` | "Biden said the blockade could fall within three days" | Translation-layer risk. Outlet introduced its own word choices. Counts toward paraphrase_rate statistic. Does NOT fire `narrative_campaign` alert on its own (single claim), but contributes to the aggregate signal and the source's paraphrase-rate credibility penalty. |
| `hedged + vague + quoted_directly=false` | "Sources say the blockade may collapse" | The primary narrative-management pattern. Counts toward `narrative_campaign` for institutional sources or `unverifiable_stream` for social sources. |
| `hedged + vague + quoted_directly=true` | (rare) direct quote from an unnamed speaker reported verbatim | Unusual structure. Possible but uncommon. Stored with `quoted_directly=true`; excluded from the hedge-vague insidious pattern because the outlet at least preserved the wording. |

**The aggregation logic now filters on three fields, not two:** `certainty = 'hedged' AND attribution = 'vague' AND quoted_directly IN ('false', 'unknown')`. Direct-quoted hedges from named speakers are exactly the exculpating pattern and are excluded from the signal, the same way they were in the earlier version — but now the exclusion is mechanically grounded in a first-class field rather than a regex-observable side effect of the paraphrase.

**Why this matters architecturally.** The earlier version was a false confidence about what the pipeline was actually doing. We were relying on a property (the paraphrase preserves the speaker's hedge) that is not reliably true — a paraphrase *can* preserve the hedge, but it can also drop it, strengthen it, weaken it, or shift it to a different modal verb. The right architectural response is to capture the information before the paraphrase happens and store it as data, so downstream reasoning can be precise instead of hopeful.

### Legitimate hedging

**Problem:** Scientific papers hedge. Intelligence estimates hedge. Honest forecasters hedge. None of these are narrative management.

**Resolution:** The concentration signal is the discriminator, not the individual claim. A science journal that hedges 60% of claims uniformly across topics has a 60% baseline, and no single topic stands out. A political outlet that hedges 30% of claims on average but 85% on iran-hormuz specifically has a 55-point deviation on one topic — that's the signal. The math distinguishes the two cases because the signal is **deviation from the source's own norm**, not an absolute rate.

### Scientific and expert communication

**Problem:** "The vaccine may reduce transmission by 40-60%" is the responsible way to report a confidence interval. A regex that flags "may" as a hedge would misfire on every scientific claim.

**Resolution:** Combined with the previous point — science sources carry high baseline hedge rates because their communication norms require it. Their per-source baseline absorbs the legitimate hedging. The deviation signal only fires when a source's hedge rate *on a specific topic* deviates from its own norm. Nature magazine will have a 60%+ hedge rate across biology, physics, climate, etc. — the baseline absorbs it.

The system does not say "this source hedges too much." It says "this source is hedging this specific topic far more than it hedges everything else."

### Emerging stories where the facts are genuinely uncertain

**Problem:** Early in a breaking story, everyone hedges because nobody knows what's happening. This is correct behavior. The system should not flag it.

**Resolution:** Two protections. First, the 5-claim minimum sample — early in a story, there aren't enough claims per (source, topic) pair to trigger the signal. Second, emerging-story hedging is *cross-source synchronous* — all outlets hedge together. Narrative-campaign hedging is *per-source persistent*. We could add a cross-source synchronization check as a Phase 2 refinement: if hedge rates spike on a topic across ≥3 major sources simultaneously, that's an emerging story and the signal is suppressed. For now, the minimum sample handles most of the concern.

---

## Phase 2: Paraphrase Drift Detection

The v1 framework detects **that** paraphrasing is happening and charges sources a credibility tax proportional to their paraphrase rate. It does not detect **whether specific paraphrases materially changed the speaker's meaning**. That is a harder problem — paraphrase drift detection — and it belongs in Phase 2. Documenting it here so the forward plan is captured.

### The problem

Paraphrase drift is when an outlet renders a speaker's statement in its own words in a way that subtly shifts commitment, emphasis, or meaning from the original. It's the difference between:

- Biden's actual words: "We remain hopeful that diplomatic channels can prevent further escalation."
- Reuters paraphrase: "Biden said he is hopeful that diplomacy will prevent war."
- NYT paraphrase: "Biden said diplomacy may yet work to avoid conflict."
- Al Jazeera paraphrase: "Biden suggested the door remains open for talks despite military posturing."

Each is a reasonable paraphrase of the same underlying statement. Each is subtly different. A reader following only one outlet gets a version of what Biden said that has been filtered through that outlet's word choices. The drift is usually small on any single paraphrase; over hundreds of paraphrases across a campaign it can materially shift the collective picture.

### Why v1 can't detect it

v1 has `paraphrase_rate` (does this outlet paraphrase rather than quote?) but no ground truth to compare paraphrases against. Without the original speaker's actual words, there's no way to measure drift. The outlet's paraphrase is the only version the system sees.

### Two viable v2 paths

**Path A: Primary-source ingestion.** Add a dedicated ingestion stream for primary source material — State Department transcripts, White House press briefing transcripts, official Iranian MOFA statements, UN proceedings, military press releases. These are the documents outlets are paraphrasing *from*. Once the primary source is in the corpus as a first-class claim, any outlet's paraphrase of a statement from that source can be compared against the original. Drift can be measured as semantic or lexical divergence between the paraphrase and the source text.

Requirements: a separate `primary_sources` ingestion path, a `paraphrase_links` table mapping each outlet claim to the primary-source statement it paraphrases (detected via semantic similarity + temporal proximity + speaker name match), and a drift-scoring function. Non-trivial build. Maybe two weeks of work after v1 hedge pattern ships.

**Path B: Cross-source paraphrase comparison.** When multiple outlets paraphrase the same speaker on the same day, measure the divergence between their paraphrases. A speaker whose statement produces identical-meaning paraphrases across five outlets has had their statement transmitted cleanly. A speaker whose statement produces five divergent paraphrases has had their meaning filtered differently by each outlet — and the outlets with paraphrases farthest from the cluster centroid are the ones doing the most drift.

Requirements: speaker-name extraction per claim, same-day same-speaker clustering, paraphrase-cluster centroid computation, per-outlet distance from centroid. Cheaper than Path A because it doesn't require the primary source — it just needs multiple outlets covering the same speech event. But noisier, because it's measuring consensus drift rather than ground-truth drift.

**Recommended v2 sequence:** Path B first (cheaper, uses existing data), then Path A (stronger ground truth, larger build). Path B may catch most of what Path A would catch, at lower engineering cost.

### What Phase 2 would add to the signal table

- **`outlet_drift_score`** — per-outlet per-speaker score measuring how far the outlet's paraphrases diverge from the cross-outlet centroid on same-day speech events. High scores indicate the outlet is filtering the speaker's meaning more than its peers.
- **`drift_weighted_credibility_penalty`** — integrated into source confidence alongside paraphrase_rate. An outlet with 80% paraphrase rate AND high drift score takes a bigger hit than one with 80% paraphrase rate AND low drift score. Paraphrasing faithfully is different from paraphrasing with drift.

Neither of these are in v1 scope. Flagging as the natural extension once the v1 data is flowing.

---

## What This Does NOT Do

- **It does not flag individual claims as suspicious.** Every claim gets tagged, but the standalone alert is aggregate-level. A single hedged+vague+paraphrased claim is noise; a pattern of them is signal.

- **It does not identify who is doing the narrative management.** The signal says "this source is concentrating hedged+vague+paraphrased claims on this topic." It does not say "this is state propaganda" or "this is editorial advocacy" or "this is PR influence." Intent classification is out of scope and probably unsolvable at the mechanical layer.

- **It does not assess the truth value of the claims.** A hedged+vague claim might also be true. The signal is about commitment and translation-layer risk, not accuracy. Those are different problems.

- **It does not detect paraphrase drift.** v1 knows whether a claim was paraphrased or quoted directly. It does not know whether the paraphrase changed the speaker's meaning. Drift detection requires primary-source ingestion or cross-outlet paraphrase comparison and is explicitly Phase 2 work — see the Phase 2 section above.

- **It does not replace retcon detection.** Retcon, hedge, and paraphrase-rate detection are complementary — one watches for walkback of committed claims, one watches for unaccountable implantation, one watches for translation-layer risk. None subsume the others.

- **It does not suppress or filter anything.** Every claim enters the ledger regardless of how it tags. The standalone signals (`narrative_campaign`, `unverifiable_stream`) are annotations surfaced to the analyst, not filters. This is the same architectural commitment as the adversarial input layer.

- **It does not handle non-English text.** The regex patterns are English-only. Non-English claims will mostly score as `committed` / `absent` (no pattern matches). This is fine for the current corpus, not a fix-now item, but worth tracking if source diversity expands.

- **It does not retroactively tag existing claims.** Historical rows get `certainty='unknown'`, `attribution='unknown'`, and `quoted_directly='unknown'` until a backfill pass runs. The signal starts producing value forward from deploy.

- **It does not auto-tune thresholds.** The 0.4 / 0.25 / 5-claim-minimum values are first-pass guesses. Retuning is a manual step after the first production audit, driven by hand-labeled data, not by automatic optimization.

---

## Open Questions

These are things I don't know yet and the spec should not pretend to decide.

- **Threshold calibration.** `claim_count >= 5`, `topic_rate >= 0.4`, `deviation >= 0.25` — these are initial guesses based on intuition, not data. First production pass will produce a hand-audit set that tells us whether these are too loose or too tight. Expect to retune after the first 48 hours of data.

- **Z-score vs flat threshold.** The current design uses a flat deviation threshold (0.25). A z-score against the source's variance across topics might be more principled — it accounts for sources with naturally volatile hedge rates. But z-scores require more data per source before they stabilize. Flat thresholds are easier to reason about and easier to explain to an analyst. Keep the flat threshold for v1 and revisit.

- **Time decay.** Should older claims in the rolling window weight less than recent ones? Probably yes — a narrative campaign is a recent phenomenon, and a source that hedged heavily six days ago and has since stopped is less interesting than one that started yesterday. But exponential decay adds complexity that may not be justified at this stage. Flat window for v1.

- **Cross-source synchronization check.** Mentioned above as emerging-story protection. Not included in v1 because it adds query complexity and because the 5-claim minimum already handles most false positives. Revisit if the first audit shows emerging-story noise.

- **Regex coverage over time.** The pattern list will get stale as communication style evolves. "Sources familiar with the matter" is today's vague-attribution cliché; something else will be tomorrow's. Needs periodic human review — probably quarterly. Governance belongs to the analyst team, not the classifier.

- **Regex vs LLM precision/recall tradeoff.** Claim: regex is good enough for v1 because hedges are lexical. Needs empirical validation on the first production batch. If the LLM's tagging materially outperforms regex on the hand-audit set, we reverse the primary/secondary roles. (Does not apply to `quoted_directly`, which is LLM-only by necessity.)

- **Paraphrase rate penalty weight.** The 10% maximum penalty on source confidence is a guess. It may be too light (paraphrase drift is actually a material credibility issue and deserves more weight) or too heavy (paraphrasing is legitimate editorial practice and 10% is more penalty than it deserves). First production audit will tell us which.

- **Finer-grained source_type signal routing.** v1 splits at source_type level (institutional → narrative_campaign, social → unverifiable_stream). Within `social`, some accounts are far more credible than others. v2 should add per-source confidence_score thresholds to differentiate a well-sourced OSINT account from an anonymous troll even though both are `source_type='social'`. We don't have the per-source calibration data yet to draw the line.

- **`quoted_directly` LLM quality.** This is the one field regex cannot validate, so we're relying on LLM tagging quality with no deterministic cross-check. First production batch needs hand-audit specifically on `quoted_directly` to measure the LLM's accuracy. If it's unreliable (say, <80% agreement with human labels) we need a different mechanism — possibly preserving the original quote span as a separate field so the LLM's judgment can be spot-checked against the raw text.

---

## Research Lineage

- **Hyland, Ken (2005), "Metadiscourse: Exploring Interaction in Writing"** — the canonical work on hedges, boosters, and attitude markers in academic and professional writing. Hyland's taxonomy of hedging devices (modal verbs, adverbs, adjectives, verbs) is the basis for the certainty pattern categories used here.

- **Biber, Douglas & Finegan, Edward (1989), "Styles of stance in English: lexical and grammatical marking of evidentiality and affect"** — the stance framework that separates epistemic stance (commitment) from evidential stance (source). This paper is where the argument that certainty and attribution are orthogonal axes originally comes from.

- **Prince, Ellen F., Frader, Joel & Bosk, Charles (1982), "On hedging in physician-physician discourse"** — early observational work on hedging as a social and professional strategy. Distinguishes *approximators* ("sort of," "kind of") from *shields* ("I think," "as far as I can tell"). The shields category is closer to what this design calls hedged attribution.

- **Vincze, Veronika et al. (2008), "The BioScope corpus: biomedical texts annotated for uncertainty, negation and their scopes"** — source of many canonical hedge markers used in computational NLP. The BioScope regex patterns are a direct ancestor of the patterns in this design note.

- **Saurí, Roser & Pustejovsky, James (2009), "FactBank: a corpus annotated with event factuality"** — the same paper cited in the modality design note. FactBank distinguishes factuality (what this design calls certainty) from polarity and source. The three-axis decomposition is FactBank's.

- **Partington, Alan (2003), "The Linguistics of Political Argument: The Spin-Doctor and the Wolf-Pack at the White House"** — corpus study of hedging in political communication, specifically White House press briefings. Closest precedent in the literature for the use case: hedged assertion as deniability mechanism in political discourse. Partington's empirical finding was that hedge concentration on specific topics correlates with political sensitivity, which is the same hypothesis this design operationalizes.

- **Clark, Herbert H. & Gerrig, Richard J. (1990), "Quotations as demonstrations," *Language* 66(4), 764–805** — the canonical paper on why direct quotation and paraphrase are fundamentally different speech acts. Clark & Gerrig argue that a direct quote is a *demonstration* of what the speaker said (the listener can inspect the exact words), while a paraphrase is a *description* of the content (the listener must trust the reporter's rendition). The two have different epistemic commitments: a direct quote commits the outlet to the speaker having produced those exact words, while a paraphrase commits the outlet only to the general meaning as the outlet understands it. This is the theoretical foundation for the `quoted_directly` field and for the asymmetric credibility treatment of quoted vs paraphrased attribution. Added to the design note after the Q4 walk-through exposed the earlier version's mistake of treating the distinction as non-load-bearing.

- **Exocortex internal — Narrative Stability Design Note (2026-04-14, shipped)** — the sibling design. Retcon detection covers claim-pair-level silent revision. This note covers claim-level silent implantation. Together they cover the two halves of the narrative-management spectrum.

- **Exocortex internal — Input Scrutiny Research Note (2026-04-14)** — the broader research foundation this design note operates within. Twelve rules for adversarial input scrutiny grounded in psychology, intelligence tradecraft, and adversarial reasoning literature. The hedge pattern work is one mechanical realization of several of those rules (notably rules 6, 7, and 8 — epistemic modality preservation, lateral evaluation, and dialectical storage).

- **Exocortex internal — Adversarial Input Layer Design Note (2026-04-14)** — the broader architectural layer the hedge pattern work is a component of. The Adversarial Input Layer document describes the full six-component scrutiny pipeline; hedge pattern detection is one of the input signals that pipeline consumes when computing per-claim scrutiny verdicts.

---

## Walk-through Resolution Notes

The five open questions from the initial draft went through a walk-through with Jake on 2026-04-14. The resolutions:

**Q1: Claim-level field or derived layer?** — Confirmed: claim-level fields. No change to the initial design.

**Q2: One composite field or separate fields for hedge and attribution?** — Confirmed: two separate fields. No change. *And after Q4 pushback, expanded to three fields by adding `quoted_directly` as a third independent axis.*

**Q3: Standalone signal threshold — when does a claim become an alert?** — Confirmed: individual claims never fire alerts on their own. The alert is aggregate-level, computed as per-source-per-topic concentration against the source's own baseline. No change to the initial design.

**Q4: Quoted speech — Biden said the blockade may collapse.** — **Significant revision.** The initial draft claimed that the extraction pipeline's paraphrasing "already handles" quoted speech because the paraphrase preserves the speaker's hedge. That was wrong. Paraphrasing is itself a credibility risk vector — it introduces a translation layer where the outlet's word choices replace the speaker's, and that drift is where narrative management hides. Three changes resulted:

1. **New field `quoted_directly`** added as a third claim-level axis. Captured by the extraction LLM at ingest time because the regex layer cannot see the original quotation marks after paraphrasing has destroyed them.
2. **Paraphrase rate** added as a per-source derived statistic that feeds source confidence alongside the retcon signal score. Sources that consistently paraphrase rather than quote directly take a small proportional credibility penalty (up to 10% confidence reduction) because they're carrying more translation-layer risk per claim.
3. **Phase 2 section** added describing paraphrase drift detection — the harder problem of measuring whether specific paraphrases materially changed the speaker's meaning. Requires either primary-source ingestion or cross-source paraphrase comparison. Deferred to v2.

**Q5: Legitimate hedging vs narrative management — source-context dependency.** — **Significant addition.** The initial draft said the concentration signal (relational, over time, across topics) is the discriminator, and that's still true. But Jake pointed out that the discriminator doesn't fully work if the system treats all high-concentration hedging the same way regardless of the source's verification model. Specifically: a major institutional outlet concentrating hedged-vague claims on a hot topic is the access-journalism narrative-management pattern; a solo OSINT account concentrating unverified claims on the same topic is doing legitimate ground reporting where unnamed sourcing is a feature, not a bug. The same statistic means opposite things depending on source_type.

Resolution: **source-type-conditional signal routing** added as Design Principle #6. Institutional sources (`source_type IN ('official', 'wire', 'outlet')`) fire the high-severity **`narrative_campaign`** alert. Social sources (`source_type = 'social'`) fire the informational **`unverifiable_stream`** caveat instead — same underlying statistic, different routing, different UI surfacing. The distinction preserves the alert's sharpness for institutional outlets while not crying wolf on ground-level OSINT sources.

**Other revisions from the walk-through:**

- Rewrote the "Quoted speech" entry in "The Hard Cases" to explicitly acknowledge the earlier version's error rather than quietly correcting it. Calibration matters: future readers should see what was changed and why.
- Added Clark & Gerrig (1990) to the research lineage as the theoretical foundation for treating direct quotation and paraphrase as fundamentally different speech acts.
- Added cross-references to the Input Scrutiny Research Note and the Adversarial Input Layer Design Note (both 2026-04-14), which establish the broader architectural frame this hedge pattern work operates within.
- Strengthened the "What This Does NOT Do" section with the new fields' limitations explicitly named.

---

## Phase Plan

1. **Design note** — this document. ✅ Updated 2026-04-14 after walk-through. Architectural shape locked.
2. **Walk-through** — ✅ completed. Five open questions resolved. Three architectural additions (quoted_directly, source-type routing, paraphrase rate). See "Walk-through Resolution Notes" above.
3. **L3 spec** — `HEDGE_PATTERN_SPEC_L3.md`, derived from this updated note. Exact file paths, SQL migrations (with `quoted_directly` column), ingest prompt extension (with quoted_directly instruction), build sequence, test assertions.
4. **Build** — same pattern as the narrative stability work. Schema migration → LLM prompt update → regex detection module → aggregation view with source-type split → header badge.
5. **First production audit** — after 48 hours of data: hand-audit top 20 flagged (source, topic) pairs in each signal class, measure LLM tagging quality on `quoted_directly` against hand labels, retune thresholds.
6. **Phase 2** — paraphrase drift detection (Path B first — cross-source comparison, cheaper; then Path A — primary-source ingestion, stronger). Also cross-source synchronization check for emerging-story protection, time decay on the rolling window, z-score thresholds, regex maintenance governance. None of these block v1.

---

*Modality says what kind of claim. Certainty says how much the speaker is committing. Attribution says who the outlet is willing to name. **Quoted_directly says whether the outlet preserved the speaker's exact words or rewrote them.** The insidious cases live in the corners where speakers don't commit, outlets won't name, and the words aren't the speaker's own — and they only become visible when you look at the corner density, not the individual claims. And the same pattern means different things depending on whether it comes from an institutional outlet or a ground-level OSINT source, which is why the signal routes on source_type.*
