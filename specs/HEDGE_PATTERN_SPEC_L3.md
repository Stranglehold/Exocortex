# Hedge Pattern Detection — L3 Specification

**Version:** 1.0
**Date:** 2026-04-14
**Status:** Ready to build
**Motivated by:** Hedge Pattern Detection Design Note (2026-04-14, updated after walk-through). The retcon detector shipped earlier tonight catches silent revision of committed claims but is structurally blind to the dominant pattern of modern narrative management: **hedged assertion attributed to vague sources, delivered as paraphrase rather than direct quote, concentrated on specific topics.** This spec mechanizes the three-axis claim-level tagging (certainty, attribution, quoted_directly), the per-source-per-topic aggregation signal with source-type-conditional routing (narrative_campaign vs unverifiable_stream), and the paraphrase-rate credibility penalty.
**Design note:** [specs/HEDGE_PATTERN_DESIGN_NOTE.md](HEDGE_PATTERN_DESIGN_NOTE.md) — all design decisions traceable. Research grounding in [specs/INPUT_SCRUTINY_RESEARCH_NOTE.md](INPUT_SCRUTINY_RESEARCH_NOTE.md).
**Modified files:**
- `services/oss/src/ingest.py` (prompt + parser + insert_claim signature)
- `services/oss/src/contradict.py` (certainty modifier on retcon signal, paraphrase rate penalty in source confidence)
- `services/oss/src/hedge_patterns.py` (new — regex module for certainty and attribution classification)
- `services/oss/src/hedge_aggregation.py` (new — per-source-per-topic signal computation)
- `services/oss/migrations/012_hedge_pattern.sql` (new)

---

## Summary

Every claim extracted from a news article carries three new tagged fields alongside the existing `modality`: **certainty** (committed / hedged / unknown), **attribution** (named / vague / absent / unknown), and **quoted_directly** (true / false / n_a / unknown). Certainty and attribution are computed by regex over the paraphrased claim text; quoted_directly is tagged by the extraction LLM at ingest time because the regex layer cannot see the original quotation boundaries. A periodic aggregation query computes per-(source, topic) concentration of the `hedged + vague + paraphrased` pattern, compares each (source, topic) against the source's own baseline across all topics, and emits a signal that routes by `source_type`: institutional sources (`official | wire | outlet`) fire `narrative_campaign` (high severity); social sources fire `unverifiable_stream` (informational caveat).

Two integrations with the existing narrative stability work: (1) the retcon signal score gets a certainty modifier that halves or three-quarters it when one or both claims were already hedged, because retconning a hedge is less culpable than retconning a committed assertion; (2) a new per-source paraphrase rate statistic feeds `update_source_confidence` alongside the existing narrative_load penalty, applying up to a 10% confidence reduction for sources that consistently rewrite speakers' words rather than quoting directly.

Phase 2 (explicitly not in this spec): analyst UI header badge for narrative_campaign, inline caveat for unverifiable_stream, paraphrase drift detection. These are deferred until the v1 data pipeline is proven stable.

---

## Data Model Changes

### New columns on `claims`

```sql
ALTER TABLE claims
    ADD COLUMN IF NOT EXISTS certainty       text DEFAULT 'unknown',
    ADD COLUMN IF NOT EXISTS attribution     text DEFAULT 'unknown',
    ADD COLUMN IF NOT EXISTS quoted_directly text DEFAULT 'unknown';
```

Defaults are `'unknown'` so existing rows are safe. Check constraints added separately (after backfill, in case any NULL somehow exists):

```sql
ALTER TABLE claims
    ADD CONSTRAINT claims_certainty_check
    CHECK (certainty IN ('committed', 'hedged', 'unknown'));

ALTER TABLE claims
    ADD CONSTRAINT claims_attribution_check
    CHECK (attribution IN ('named', 'vague', 'absent', 'unknown'));

ALTER TABLE claims
    ADD CONSTRAINT claims_quoted_directly_check
    CHECK (quoted_directly IN ('true', 'false', 'n_a', 'unknown'));
```

Note: `n_a` uses underscore rather than slash because Postgres check constraints prefer simple string tokens.

Indexes for aggregation queries:

```sql
CREATE INDEX IF NOT EXISTS idx_claims_certainty ON claims(certainty);
CREATE INDEX IF NOT EXISTS idx_claims_attribution ON claims(attribution);
CREATE INDEX IF NOT EXISTS idx_claims_quoted_directly ON claims(quoted_directly);
CREATE INDEX IF NOT EXISTS idx_claims_hedge_pattern
    ON claims(source_id, certainty, attribution, quoted_directly)
    WHERE certainty = 'hedged' AND attribution = 'vague';
```

The partial index on the insidious combination speeds up the aggregation query significantly.

### New table `source_topic_signals`

Stores the per-(source, topic) aggregation results. Recomputed periodically.

```sql
CREATE TABLE IF NOT EXISTS source_topic_signals (
    id                  serial PRIMARY KEY,
    source_id           int NOT NULL REFERENCES sources(id),
    topic               text NOT NULL,
    source_type         text NOT NULL,
    claim_count         int NOT NULL,
    insidious_count     int NOT NULL,
    topic_rate          double precision NOT NULL,
    baseline_rate       double precision NOT NULL,
    deviation           double precision NOT NULL,
    signal_class        text,
    computed_at         timestamptz NOT NULL DEFAULT NOW(),
    window_days         int NOT NULL DEFAULT 7,
    CHECK (signal_class IS NULL OR signal_class IN (
        'narrative_campaign', 'unverifiable_stream', 'unclassified'
    ))
);

CREATE INDEX IF NOT EXISTS idx_source_topic_signals_source ON source_topic_signals(source_id);
CREATE INDEX IF NOT EXISTS idx_source_topic_signals_signal_class ON source_topic_signals(signal_class);
CREATE INDEX IF NOT EXISTS idx_source_topic_signals_computed_at ON source_topic_signals(computed_at);
CREATE UNIQUE INDEX IF NOT EXISTS uq_source_topic_signals_current
    ON source_topic_signals(source_id, topic, window_days);
```

The unique index lets us UPSERT current values without accumulating stale rows. History can be preserved in a separate audit table if needed later; v1 just keeps the latest computation per (source, topic, window_days).

### Migration file

`services/oss/migrations/012_hedge_pattern.sql` — all ALTERs + CREATE TABLE + CREATE INDEXes in a single `BEGIN ... COMMIT` block. Idempotent via `IF NOT EXISTS`. Check constraints wrapped in `DO $$ ... END$$` blocks to handle concurrent-migration safety (same pattern as migration 011).

---

## Module 1: `services/oss/src/hedge_patterns.py` (new)

Pure module. No DB. No LLM. Loaded once at import time, hot-reloadable if needed.

```python
"""
hedge_patterns.py — regex-based classification of certainty and attribution.

Operates on the paraphrased claim_text field. Does NOT classify quoted_directly,
which requires LLM tagging at extraction time because the regex layer cannot
see the original quotation boundaries after paraphrasing has destroyed them.

Spec: specs/HEDGE_PATTERN_SPEC_L3.md
Design note: specs/HEDGE_PATTERN_DESIGN_NOTE.md
"""

import re
import logging

log = logging.getLogger(__name__)

# Certainty values
COMMITTED = "committed"
HEDGED    = "hedged"
UNKNOWN   = "unknown"

# Attribution values
NAMED  = "named"
VAGUE  = "vague"
ABSENT = "absent"
# UNKNOWN shared with certainty

# ---------------------------------------------------------------------------
# Certainty patterns — each matches a specific linguistic construction of hedging.
# A claim is `hedged` if ANY pattern matches; `committed` if none match.
# ---------------------------------------------------------------------------

CERTAINTY_PATTERNS: dict[str, re.Pattern] = {
    "modal_hedge": re.compile(
        r"\b(may|might|could|would|should|can)\s+(?:be|have|not|well)?\b",
        re.IGNORECASE,
    ),
    "epistemic_adverb": re.compile(
        r"\b(possibly|probably|allegedly|reportedly|supposedly|purportedly|"
        r"apparently|seemingly|ostensibly|arguably|presumably)\b",
        re.IGNORECASE,
    ),
    "hedge_verb": re.compile(
        r"\b(suggests?|indicates?|appears?\s+to|seems?\s+to|"
        r"is\s+(?:said|thought|understood|believed|expected)\s+to|"
        r"are\s+(?:said|thought|understood|believed|expected)\s+to)\b",
        re.IGNORECASE,
    ),
    "weakener": re.compile(
        r"\b(somewhat|rather|perhaps)\b",
        re.IGNORECASE,
    ),
}

# ---------------------------------------------------------------------------
# Attribution patterns — each detects a specific type of source clause.
# Order of evaluation: vague first (more specific patterns), then named, then
# absent (default when nothing matches).
# ---------------------------------------------------------------------------

ATTRIBUTION_PATTERNS: dict[str, re.Pattern] = {
    "vague_source": re.compile(
        r"\b(sources?|officials?|analysts?|experts?|insiders?)\s+"
        r"(?:say|said|suggest|suggested|indicate|indicated|believe|believed|"
        r"expect|expected|warn|warned|told)\b",
        re.IGNORECASE,
    ),
    "vague_familiar": re.compile(
        r"\b(?:people|sources?|individuals?|officials?)\s+familiar\s+with\b",
        re.IGNORECASE,
    ),
    "anonymous_official": re.compile(
        r"\ba\s+(?:senior\s+|high-ranking\s+|senior-level\s+)?"
        r"(?:administration|government|official|diplomatic|intelligence|military)\s+"
        r"(?:official|source|spokesperson)\b",
        re.IGNORECASE,
    ),
    "condition_of_anonymity": re.compile(
        r"\bon\s+(?:the\s+)?condition\s+of\s+anonymity\b",
        re.IGNORECASE,
    ),
    "named_source": re.compile(
        # Proper noun(s) + speech verb — simplified, catches the common cases.
        # Case-sensitive because proper nouns matter.
        r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+"
        r"(?:said|stated|announced|told|confirmed|denied|declared|reported)\b"
    ),
}

VAGUE_KEYS = ("vague_source", "vague_familiar", "anonymous_official", "condition_of_anonymity")


# ---------------------------------------------------------------------------
# Classification functions — pure, deterministic.
# ---------------------------------------------------------------------------

def classify_certainty(claim_text: str) -> str:
    """
    Return 'committed' if no hedge pattern matches, 'hedged' if any does.
    Never returns 'unknown' — that's reserved for claims we literally couldn't
    process (empty string, parse failure upstream).
    """
    if not claim_text or not claim_text.strip():
        return UNKNOWN
    for pattern in CERTAINTY_PATTERNS.values():
        if pattern.search(claim_text):
            return HEDGED
    return COMMITTED


def classify_attribution(claim_text: str) -> str:
    """
    Return 'vague' if any vague-pattern matches, then 'named' if named-source
    pattern matches, else 'absent'. Vague takes priority over named — a claim
    like "Sources close to Biden said..." has both a vague source AND a named
    entity, and the vague marker is the load-bearing signal.
    """
    if not claim_text or not claim_text.strip():
        return UNKNOWN
    for key in VAGUE_KEYS:
        if ATTRIBUTION_PATTERNS[key].search(claim_text):
            return VAGUE
    if ATTRIBUTION_PATTERNS["named_source"].search(claim_text):
        return NAMED
    return ABSENT


def classify_hedge_pattern(claim_text: str) -> tuple[str, str]:
    """
    Convenience wrapper. Returns (certainty, attribution) pair.
    """
    return classify_certainty(claim_text), classify_attribution(claim_text)
```

**Testable in isolation.** No dependencies on other OSS modules. Unit tests in Testing Criteria below.

---

## Module 2: Modality Extraction Extension (`services/oss/src/ingest.py`)

### Prompt extension

The existing `PROCESS_SYSTEM` prompt already tags `modality`. Add three more instructions for `certainty`, `attribution`, and `quoted_directly`. The full additions:

```
Additional fields per claim:

- "certainty" — the commitment level of the proposition AS STATED BY ITS SPEAKER:
    "committed"  — declarative assertion with no hedges ("Six ships turned around.")
    "hedged"     — softened by modals (may, could, might), epistemic adverbs
                   (possibly, allegedly, reportedly), or hedge verbs (suggests,
                   indicates, appears to, is said to, is expected to)
    "unknown"    — fallback when neither pattern fits

- "attribution" — how the outlet sourced the claim:
    "named"      — specific, identifiable source (Secretary Austin said...,
                   According to the Iranian Foreign Ministry...)
    "vague"      — non-specific source clause ("sources say", "officials indicate",
                   "people familiar with the matter", "a senior administration
                   official", "on condition of anonymity")
    "absent"     — the outlet makes the claim in its own voice with no
                   attribution clause
    "unknown"    — fallback

- "quoted_directly" — whether the proposition appeared inside quotation marks
  in the ORIGINAL ARTICLE, attributed to a speaker, with the speaker's exact
  words preserved:
    "true"       — the proposition was rendered as direct quotation in the
                   source article (e.g. `Biden said: "The blockade may collapse"`)
    "false"      — the proposition was rendered as paraphrased attribution
                   (the outlet's own words, not the speaker's)
    "n_a"        — the claim has no speaker attribution at all; outlet is
                   speaking in its own voice
    "unknown"    — fallback

CRITICAL: for quoted_directly, you must look at the ORIGINAL article text —
you are the only layer in the pipeline that can see whether the article used
quotation marks. The downstream regex layer cannot see this because the
paraphrasing step destroys the quotation boundaries.

When in doubt between fact and speculation (modality), pick fact only if the
claim is about something already confirmed to have happened.
```

### Schema extension — the JSON object returned per claim

The LLM's per-claim JSON now contains seven fields (was four):

```json
{
  "claim": "...",
  "technique": "direct",
  "topics": ["iran-hormuz"],
  "modality": "speculation",
  "certainty": "hedged",
  "attribution": "vague",
  "quoted_directly": "false"
}
```

### Parser extension in `process_article()`

After the existing modality validation, add validation for the three new fields:

```python
valid_certainty = {'committed', 'hedged', 'unknown'}
valid_attribution = {'named', 'vague', 'absent', 'unknown'}
valid_quoted_directly = {'true', 'false', 'n_a', 'unknown'}

# ... inside the results loop:

certainty_raw = str(item.get("certainty", "unknown")).strip().lower()
certainty = certainty_raw if certainty_raw in valid_certainty else "unknown"

attribution_raw = str(item.get("attribution", "unknown")).strip().lower()
attribution = attribution_raw if attribution_raw in valid_attribution else "unknown"

qd_raw = str(item.get("quoted_directly", "unknown")).strip().lower()
# Accept 'n/a' as input but normalize to 'n_a' for the check constraint
if qd_raw in ("n/a", "na"):
    qd_raw = "n_a"
quoted_directly = qd_raw if qd_raw in valid_quoted_directly else "unknown"

results.append({
    "claim": claim,
    "technique": technique,
    "topics": topics,
    "modality": modality,
    "certainty": certainty,
    "attribution": attribution,
    "quoted_directly": quoted_directly,
})
```

### `insert_claim` signature extension

Extend to take the three new fields. The regex classification is applied *as a cross-check* — if the LLM disagrees with regex on certainty or attribution, the regex wins and the disagreement is logged.

```python
def insert_claim(conn, source_id, raw_text, claim_text, article_url, article_title,
                 topic_tags, technique_class, published_at, faiss_id,
                 modality="unknown",
                 certainty="unknown", attribution="unknown", quoted_directly="unknown") -> int:
    # Regex cross-check for certainty and attribution (LLM is cross-validated).
    # Note: quoted_directly is LLM-only; regex cannot see the original quotation boundary.
    from hedge_patterns import classify_certainty, classify_attribution

    regex_certainty = classify_certainty(claim_text)
    regex_attribution = classify_attribution(claim_text)

    if certainty != "unknown" and regex_certainty != "unknown" and certainty != regex_certainty:
        log.info(f"[HEDGE-DISAGREE] certainty: llm={certainty} regex={regex_certainty} "
                 f"claim={claim_text[:60]!r}")
        certainty = regex_certainty  # regex wins
    elif certainty == "unknown":
        certainty = regex_certainty

    if attribution != "unknown" and regex_attribution != "unknown" and attribution != regex_attribution:
        log.info(f"[HEDGE-DISAGREE] attribution: llm={attribution} regex={regex_attribution} "
                 f"claim={claim_text[:60]!r}")
        attribution = regex_attribution
    elif attribution == "unknown":
        attribution = regex_attribution

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO claims
              (source_id, raw_text, claim_text, article_url, article_title,
               topic_tags, technique_class, published_at, faiss_id,
               modality, certainty, attribution, quoted_directly)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (source_id, raw_text, claim_text, article_url, article_title,
              topic_tags, technique_class, published_at, faiss_id,
              modality, certainty, attribution, quoted_directly))
        row = cur.fetchone()
        cur.execute("UPDATE sources SET total_claims = total_claims + 1 WHERE id = %s", (source_id,))
        return row['id']
```

### Call-site update

In the ingestion loop where `insert_claim` is called, pick up the three new fields from `process_article()`'s result:

```python
modality        = item.get("modality", "unknown")
certainty       = item.get("certainty", "unknown")
attribution     = item.get("attribution", "unknown")
quoted_directly = item.get("quoted_directly", "unknown")

# ... existing dedup / FAISS insertion ...

with conn:
    insert_claim(
        conn, source_id, raw_text, claim_text, article_url,
        article_title, topic_tags, technique_class,
        published_at, faiss_id, modality,
        certainty, attribution, quoted_directly,
    )
```

---

## Module 3: Certainty Modifier on Retcon Signal (`services/oss/src/contradict.py`)

Extend the existing `classify_retcon_signal` wrapper (from narrative stability) to apply the certainty multiplier. The existing function already takes modality_a, modality_b, volatility, acknowledged. Add certainty_a and certainty_b parameters and apply the modifier to the final score.

```python
def apply_certainty_modifier(signal_score: float,
                             certainty_a: str,
                             certainty_b: str) -> float:
    """
    Reduce retcon signal score when one or both retconned claims were already
    hedged. A hedge is a partial disclaimer — retconning a hedge is less
    dishonest than retconning a committed assertion.

    Rules:
      both hedged  → 0.5x  (both were already disclaimers)
      one hedged   → 0.75x (partial disclaimer)
      both committed → 1.0x (full weight, no discount)
      unknown      → treat as committed (conservative)
    """
    a_hedged = certainty_a == "hedged"
    b_hedged = certainty_b == "hedged"
    if a_hedged and b_hedged:
        return signal_score * 0.5
    if a_hedged or b_hedged:
        return signal_score * 0.75
    return signal_score
```

### Integration into `scan_new_claims`

The scan already fetches `modality` and `topic_tags` per claim. Extend the SELECT to also include `certainty` so the modifier can be applied:

```python
cur.execute("""
    SELECT id, source_id, claim_text, faiss_id, topic_tags, modality, certainty
    FROM claims
    WHERE id > %s AND faiss_id IS NOT NULL
    ...
""", ...)
```

Same change to `get_recent_claims_for_source`. Then in the pair-scoring loop, after `classify_retcon_signal` returns the base signal_score, apply the modifier:

```python
# After computing base signal_class and signal_score from classify_retcon_signal:
modified_signal_score = apply_certainty_modifier(
    signal_score,
    certainty_a=old_claim.get("certainty") or "unknown",
    certainty_b=claim.get("certainty") or "unknown",
)

# The signal_class itself is unchanged — only the score is modified.
# This preserves diagnostic visibility (you can still see it was a
# narrative_rewrite) while reducing the source confidence impact.
```

Store `modified_signal_score` in the `signal_score` column of contradictions, and keep an additional field `raw_signal_score` for the unmodified value so retrospective analysis can separate the classifier output from the hedge modifier.

### Schema extension to contradictions

```sql
ALTER TABLE contradictions
    ADD COLUMN IF NOT EXISTS raw_signal_score double precision;
```

The existing `signal_score` column holds the modified (post-hedge-discount) value. The new `raw_signal_score` holds the pre-modifier value. Both are preserved for analysis.

---

## Module 4: `services/oss/src/hedge_aggregation.py` (new)

Periodic module that runs the SQL aggregation query and writes results to the `source_topic_signals` table.

```python
"""
hedge_aggregation.py — per-source-per-topic hedge concentration signal.

Computes the narrative_campaign / unverifiable_stream signals by aggregating
claims over a rolling window, comparing each (source, topic) against the
source's own baseline, and gating the signal class by source_type.

Runs periodically (after each ingestion pass). Writes to source_topic_signals.
Spec: specs/HEDGE_PATTERN_SPEC_L3.md
"""

import os
import logging
import psycopg2
import psycopg2.extras

log = logging.getLogger(__name__)

# Thresholds — first-pass guesses, tunable
WINDOW_DAYS     = int(os.environ.get("OSS_HEDGE_WINDOW_DAYS", "7"))
MIN_CLAIM_COUNT = int(os.environ.get("OSS_HEDGE_MIN_CLAIMS", "5"))
MIN_TOPIC_RATE  = float(os.environ.get("OSS_HEDGE_MIN_RATE", "0.4"))
MIN_DEVIATION   = float(os.environ.get("OSS_HEDGE_MIN_DEVIATION", "0.25"))


def compute_narrative_signals(conn) -> int:
    """
    Recompute the source_topic_signals table from scratch for the current window.
    Returns the count of (source, topic) pairs that fired a signal.
    """
    with conn.cursor() as cur:
        # Delete stale rows for the current window (we recompute each pass)
        cur.execute("""
            DELETE FROM source_topic_signals
            WHERE window_days = %s
        """, (WINDOW_DAYS,))

        # Aggregation query — see design note for the full SQL explanation
        cur.execute("""
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
                WHERE c.extracted_at >= NOW() - (%s || ' days')::interval
                GROUP BY c.source_id, s.source_type, unnest(c.topic_tags)
            ),
            source_baseline AS (
                SELECT
                    source_id,
                    SUM(insidious_count)::float / NULLIF(SUM(claim_count), 0) AS baseline_rate
                FROM topic_stats
                GROUP BY source_id
            )
            INSERT INTO source_topic_signals (
                source_id, topic, source_type, claim_count, insidious_count,
                topic_rate, baseline_rate, deviation, signal_class,
                computed_at, window_days
            )
            SELECT
                ts.source_id,
                ts.topic,
                ts.source_type,
                ts.claim_count,
                ts.insidious_count,
                (ts.insidious_count::float / NULLIF(ts.claim_count, 0)) AS topic_rate,
                COALESCE(sb.baseline_rate, 0) AS baseline_rate,
                (ts.insidious_count::float / NULLIF(ts.claim_count, 0)) - COALESCE(sb.baseline_rate, 0) AS deviation,
                CASE
                    WHEN ts.claim_count < %s THEN NULL
                    WHEN (ts.insidious_count::float / NULLIF(ts.claim_count, 0)) < %s THEN NULL
                    WHEN (ts.insidious_count::float / NULLIF(ts.claim_count, 0)) - COALESCE(sb.baseline_rate, 0) < %s THEN NULL
                    WHEN ts.source_type IN ('official', 'wire', 'outlet') THEN 'narrative_campaign'
                    WHEN ts.source_type = 'social' THEN 'unverifiable_stream'
                    ELSE 'unclassified'
                END AS signal_class,
                NOW() AS computed_at,
                %s AS window_days
            FROM topic_stats ts
            LEFT JOIN source_baseline sb USING (source_id)
        """, (WINDOW_DAYS, MIN_CLAIM_COUNT, MIN_TOPIC_RATE, MIN_DEVIATION, WINDOW_DAYS))

        cur.execute("""
            SELECT COUNT(*) FROM source_topic_signals
            WHERE window_days = %s AND signal_class IS NOT NULL
        """, (WINDOW_DAYS,))
        n_fired = cur.fetchone()[0]

    conn.commit()
    log.info(f"[HEDGE-AGG] Recomputed narrative signals — {n_fired} (source, topic) pairs fired")
    return n_fired
```

### Integration into the scheduler

In `ingest.py`'s `run_scheduler`, after each pass completes and before the contradiction scan, call `compute_narrative_signals`:

```python
# Recompute hedge pattern aggregation signals
try:
    from hedge_aggregation import compute_narrative_signals
    conn = get_conn()
    try:
        compute_narrative_signals(conn)
    finally:
        conn.close()
except Exception as e:
    log.error(f"Hedge aggregation pass error: {e}")
```

The aggregation is cheap (one query per cycle) and doesn't block anything downstream.

---

## Module 5: Paraphrase Rate Penalty (`services/oss/src/contradict.py`)

Extend `update_source_confidence` to apply a small penalty based on the source's paraphrase rate alongside the existing narrative_load calculation.

```python
def compute_paraphrase_rate(conn, source_id: int, window_days: int = 30) -> float:
    """
    Return the source's paraphrase rate over the rolling window:
    paraphrased_count / (quoted_count + paraphrased_count).
    Only claims with attribution IN ('named', 'vague') count — unattributed
    claims don't carry the distinction.
    Returns 0.0 if the source has fewer than 5 attributed claims in the window.
    """
    interval_literal = f"{max(1, int(window_days))} days"
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE quoted_directly = 'true')  AS quoted_count,
                COUNT(*) FILTER (WHERE quoted_directly = 'false') AS paraphrased_count
            FROM claims
            WHERE source_id = %s
              AND attribution IN ('named', 'vague')
              AND extracted_at >= NOW() - (%s::interval)
        """, (source_id, interval_literal))
        row = cur.fetchone()
        if not row:
            return 0.0
        quoted = row['quoted_count'] or 0
        paraphrased = row['paraphrased_count'] or 0
        total = quoted + paraphrased
        if total < 5:
            return 0.0
        return paraphrased / total
```

Extend `update_source_confidence` to integrate the penalty:

```python
def update_source_confidence(conn, source_id: int, window_days: int = 14):
    # ... existing narrative_load computation ...

    # NEW: paraphrase rate penalty (up to 10% max)
    paraphrase_rate = compute_paraphrase_rate(conn, source_id, window_days=30)
    paraphrase_penalty = 0.10 * paraphrase_rate

    # Combined adjustment
    clamped_load = min(narrative_load, 1.0)
    adjustment = (
        -narrative_load * 0.3             # existing narrative stability penalty
        + (1.0 - clamped_load) * 0.02     # existing recovery term
        - paraphrase_penalty              # new paraphrase rate penalty
    )
    new_confidence = max(0.1, min(0.99, current + adjustment))

    # ... existing UPDATE ...
```

The penalty is deliberately smaller than the retcon penalty (10% max vs 30% max) because paraphrasing is a legitimate editorial choice and carries risk rather than being a direct dishonesty signal. First-pass value — tunable.

---

## Testing Criteria

### Pure-function unit tests (`hedge_patterns.py`)

| # | Input claim_text | Expected certainty | Expected attribution |
|---|---|---|---|
| 1 | "Six merchant ships turned around." | committed | absent |
| 2 | "Secretary Austin said the carriers are deployed." | committed | named |
| 3 | "Sources say six ships turned around." | committed | vague |
| 4 | "Six ships may have turned around." | hedged | absent |
| 5 | "Sources suggest six ships may have turned around." | hedged | vague |
| 6 | "Analysts expect the blockade could collapse." | hedged | vague |
| 7 | "A senior administration official told Reuters..." | committed | vague |
| 8 | "People familiar with the matter believe..." | hedged | vague |
| 9 | "The Iranian Foreign Ministry announced..." | committed | named |
| 10 | "Allegedly, the ships were damaged." | hedged | absent |
| 11 | "Biden declared victory." | committed | named |
| 12 | "Reuters reported on condition of anonymity..." | committed | vague |
| 13 | "" (empty) | unknown | unknown |
| 14 | "This is probably going to happen." | hedged | absent |

### Cross-validation logging

Test 15: when LLM tags `certainty='committed'` but regex returns `hedged`, `insert_claim` logs a `[HEDGE-DISAGREE]` line and the stored value is `hedged`.

Test 16: when LLM tags `certainty='unknown'`, `insert_claim` falls through to the regex classification and stores the regex value.

### Schema migration tests

Test 17: Migration 012 applies cleanly on a fresh database. All three new columns exist with correct defaults. Check constraints enforce the allowed values. Indexes exist.

Test 18: Migration 012 applies cleanly on a database that already has the narrative stability fields populated. Existing rows get `certainty='unknown'`, `attribution='unknown'`, `quoted_directly='unknown'`.

### End-to-end tests (after deploy)

Test 19: **Modality coverage.** After first post-deploy ingestion pass, at least 80% of new claims have `certainty != 'unknown'`.

Test 20: **Attribution coverage.** After first pass, at least 80% of new claims have `attribution != 'unknown'`.

Test 21: **Quoted_directly coverage.** After first pass, at least 70% of new claims have `quoted_directly != 'unknown'`. (Lower threshold because this is LLM-only with no regex cross-check.)

Test 22: **Aggregation runs.** `source_topic_signals` table has at least one row per active topic after first pass completes.

Test 23: **Source-type routing works.** At least one (source, topic) pair fires `narrative_campaign` OR `unverifiable_stream` within 48 hours. If zero fire, either the thresholds are too tight or something is misclassifying.

Test 24: **Certainty modifier applies.** After next retcon scan produces a contradiction where one or both claims are hedged, the stored `signal_score` is less than `raw_signal_score` and the ratio matches the apply_certainty_modifier rules (0.5x for both hedged, 0.75x for one).

Test 25: **Paraphrase rate feeds source confidence.** After 48 hours, at least one source's `confidence_score` differs from its pre-hedge-pattern value, and the difference is consistent with the source's paraphrase rate.

Test 26: **No suppression.** Total claims in `claims` table grows at the same rate pre- and post-deploy. Hedge pattern does not filter anything out. Verify by comparing the hourly insertion rate.

### Corpus spot-check

Test 27: Spot-check 20 claims tagged `quoted_directly='true'` by the LLM — verify by hand that the original article used direct quotation marks around the proposition. Agreement rate ≥ 80%.

Test 28: Spot-check 20 claims tagged `certainty='hedged'` by the regex — verify by hand that at least one hedge pattern actually fires on the claim text.

---

## Build Sequence

Each step is deployable in isolation. The pipeline is correct at every intermediate state.

1. **Migration.** Write `012_hedge_pattern.sql`. Apply with `psql` inside `oss_postgres`. Verify columns exist via `\d claims` and `\d source_topic_signals`. Verify check constraints enforce allowed values.

2. **`hedge_patterns.py`.** New file. Compile-check in isolation. Copy into `oss_app:/app/src/hedge_patterns.py`.

3. **Unit tests for hedge_patterns.** Run test cases 1–14 against the live container. Block if any fail.

4. **Extend `ingest.py` prompt + parser + insert_claim.** Apply prompt changes to `PROCESS_SYSTEM`. Add parser validation. Extend `insert_claim` signature with regex cross-check. Copy to container.

5. **Extend `classify_retcon_signal` caller path in `contradict.py`.** Add `certainty` to the SELECT in `scan_new_claims` and `get_recent_claims_for_source`. Apply `apply_certainty_modifier` before `insert_contradiction`. Add `raw_signal_score` column to the insert. Copy to container.

6. **`hedge_aggregation.py`.** New file with `compute_narrative_signals`. Wire into `run_scheduler` after ingestion pass. Copy to container.

7. **Extend `update_source_confidence` with paraphrase rate penalty.** Add `compute_paraphrase_rate` helper. Integrate penalty into the adjustment calculation. Copy to container.

8. **Restart `oss_app`.** Verify clean startup logs. Verify scheduler init messages. Verify no import errors.

9. **Resume ingestion.** Let one full cycle run. Verify end-to-end tests 19–26 pass.

10. **Corpus spot-check.** Tests 27–28. If quality is poor on `quoted_directly`, escalate to "investigate LLM tagging" rather than continuing.

11. **First production audit (48 hours later).** Hand-audit top 20 `narrative_campaign` and top 20 `unverifiable_stream` signals. Retune thresholds if needed. Measure LLM tagging quality vs. regex disagreement rate.

---

## What This Does NOT Do

- **No UI work in v1.** The header badge for `narrative_campaign` and the inline caveat for `unverifiable_stream` are explicitly Phase 2. This spec ships the data pipeline; the UI follows once the data is flowing reliably.

- **No paraphrase drift detection.** v1 detects whether a claim was paraphrased or quoted directly. It does not detect whether the paraphrase changed the speaker's meaning. That's Phase 2 work and requires either primary-source ingestion or cross-source comparison.

- **No historical backfill.** Existing ~10k claims keep `certainty='unknown'`, `attribution='unknown'`, `quoted_directly='unknown'`. Re-extraction to populate these fields on old claims is a separate one-shot migration that is not in scope here.

- **No auto-tuning of thresholds.** The `MIN_CLAIM_COUNT=5`, `MIN_TOPIC_RATE=0.4`, `MIN_DEVIATION=0.25` values are first-pass guesses. Retuning is manual after the first production audit.

- **No cross-language support.** Regex patterns are English-only. Non-English claims will mostly score `committed` + `absent` (no patterns match). Acceptable for the current corpus; revisit if source diversity expands.

- **No interaction with non-retcon contradictions.** The certainty modifier only applies to retcon signals in the narrative stability pipeline. Cross-source contradictions (which are not currently implemented) would need their own modifier when they ship.

---

## Config Summary

```bash
# Environment variables (all optional, defaults shown)
OSS_HEDGE_WINDOW_DAYS=7          # Rolling window for aggregation
OSS_HEDGE_MIN_CLAIMS=5           # Minimum sample per (source, topic)
OSS_HEDGE_MIN_RATE=0.4           # Minimum topic_rate to consider signal
OSS_HEDGE_MIN_DEVIATION=0.25     # Minimum deviation from source baseline
# No other new envvars.
```

All other tunables live as constants in the source files where they are visible in PRs.

---

## Validation

The spec is validated when:

1. Migration 012 applies cleanly on the live `oss_postgres` instance.
2. All 28 testing criteria pass (14 unit tests + 4 schema/cross-validation + 8 end-to-end + 2 spot-checks).
3. The first production pass produces new claims with non-null `certainty`, `attribution`, `quoted_directly` at coverage ≥ 80% / 80% / 70% respectively.
4. The hedge aggregation query runs without error and populates `source_topic_signals` with at least one row per active topic.
5. At least one retcon pair gets a certainty-modified signal_score within 48 hours of deploy.
6. At least one source's confidence_score is adjusted by the paraphrase rate penalty (difference from pre-deploy value detectable).
7. No regression on existing narrative stability tests — the retcon scan still produces contradictions with correct signal_class, and the log format still includes the `[contradiction/<signal_class>]` tag.
8. No claims are filtered out by the hedge pattern pipeline. Total claim insertion rate is unchanged by the deploy.

If all eight conditions hold, the spec is validated and Phase 2 (UI integration, paraphrase drift detection) becomes the next planning scope.

---

*Modality says what kind of claim. Certainty says how much the speaker is committing. Attribution says who the outlet is willing to name. Quoted_directly says whether the outlet preserved the speaker's exact words. The combination determines whether a claim is normal journalism or narrative management — and the aggregation tells you which sources are doing it to which topics, over time, relative to their own baselines. The data tells you the pattern; the source_type tells you what it means.*
