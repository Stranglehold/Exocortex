# Narrative Stability — L3 Specification

**Version:** 1.0
**Date:** 2026-04-14
**Status:** Ready to build
**Motivated by:** SFA-001 ingestion audit — first production cycle of `scan_new_claims` produced 7 real contradictions that the existing one-dimensional scoring cannot distinguish. Reuters retconning its US-Iran negotiation-status speculation three ways scores the same as a source updating a casualty count. The feature produces correct pairs and wrong signal weight.
**Design note:** `NARRATIVE_STABILITY_DESIGN_NOTE.md`
**Modified files:**
- `services/oss/src/ingest.py` (claim extraction prompt + schema)
- `services/oss/src/contradict.py` (signal classifier, source confidence rewrite)
- `services/oss/src/volatility.py` (new)
- `services/oss/migrations/011_narrative_stability.sql` (new)
- `services/oss/src/app.py` (optional header badge — Phase 2)

---

## Summary

Every retcon pair is classified on three orthogonal axes — **modality** (fact / speculation / opinion / framing), **volatility** (high / medium / low), **acknowledgment** (silent / acknowledged) — and mapped to one of seven **signal classes**. The signal class drives source confidence updates. Reality updates cost the source nothing. Narrative rewrites cost the source proportionally.

The classifier is pure logic. Modality comes from the claim-extraction LLM (one added JSON field, no new call). Volatility is a static lookup table keyed on topic tags. Acknowledgment is already in the schema. The whole system is deterministic end-to-end once modality has been extracted.

---

## Data Model Changes

### New column on `claims`

```sql
ALTER TABLE claims ADD COLUMN modality text DEFAULT 'unknown'
  CHECK (modality IN ('fact', 'speculation', 'opinion', 'framing', 'unknown'));
CREATE INDEX idx_claims_modality ON claims(modality);
```

Default `'unknown'` is safe for existing rows. The check constraint prevents drift.

### New columns on `contradictions`

```sql
ALTER TABLE contradictions ADD COLUMN modality_a   text;
ALTER TABLE contradictions ADD COLUMN modality_b   text;
ALTER TABLE contradictions ADD COLUMN volatility   text;
ALTER TABLE contradictions ADD COLUMN signal_class text
  CHECK (signal_class IN (
    'reality_update', 'honest_correction', 'healthy_update',
    'silent_error', 'narrative_rewrite', 'editorial_drift',
    'uncategorized'
  ));
ALTER TABLE contradictions ADD COLUMN signal_score double precision
  CHECK (signal_score >= 0.0 AND signal_score <= 1.0);

CREATE INDEX idx_contradictions_signal_class ON contradictions(signal_class);
CREATE INDEX idx_contradictions_signal_score ON contradictions(signal_score);
```

### Migration file

`services/oss/migrations/011_narrative_stability.sql` — both ALTERs in one file, wrapped in `BEGIN; ... COMMIT;`. Idempotent via `IF NOT EXISTS` where possible.

---

## Module 1: `services/oss/src/volatility.py` (new)

Pure module. No DB. No LLM. Loaded once at import time, hot-reloadable if needed.

```python
"""
volatility.py — topic-tag → volatility-tier lookup for narrative stability.

Volatility is a property of the TOPIC, not the individual claim. A casualty
count moves every hour; the Pope's identity doesn't move at all. The retcon
signal classifier uses this axis to distinguish reality updates from
narrative rewrites.
"""

import os
import logging

log = logging.getLogger(__name__)

# Volatility tiers
HIGH   = "high"    # Facts change on hour→day timescales
MEDIUM = "medium"  # Facts change on week→month timescales
LOW    = "low"     # Facts change on year timescales or not at all

DEFAULT_VOLATILITY = os.environ.get("OSS_DEFAULT_VOLATILITY", MEDIUM)

# Keyed by topic tag (from claims.topic_tags). Matched exactly, case-insensitive.
TOPIC_VOLATILITY: dict[str, str] = {
    # --- HIGH --- (breaking news, active conflict, markets)
    "iran-hormuz":         HIGH,
    "iran-war":            HIGH,
    "casualty_counts":     HIGH,
    "oil_prices":          HIGH,
    "markets":             HIGH,
    "breaking_news":       HIGH,
    "military_operations": HIGH,
    "ceasefire":           HIGH,

    # --- MEDIUM --- (diplomacy, policy, elections)
    "iran":            MEDIUM,
    "diplomacy":       MEDIUM,
    "policy":          MEDIUM,
    "elections":       MEDIUM,
    "sanctions":       MEDIUM,
    "trade":           MEDIUM,
    "nuclear_program": MEDIUM,

    # --- LOW --- (history, biography, geography, law)
    "history":           LOW,
    "biography":         LOW,
    "geography":         LOW,
    "law":               LOW,
    "religion":          LOW,
    "scientific_fact":   LOW,
    "constitutional":    LOW,
}


def get_volatility(topic_tags: list[str] | None) -> str:
    """
    Return the volatility tier for a claim given its topic tags.

    Resolution rule: when multiple tags map to different tiers, take the
    HIGHEST (most generous — assume reality may have moved). Unmapped tags
    fall through to DEFAULT_VOLATILITY.

    Returns one of: 'high', 'medium', 'low'.
    """
    if not topic_tags:
        return DEFAULT_VOLATILITY

    tiers_seen = set()
    for tag in topic_tags:
        if not tag:
            continue
        normalized = tag.strip().lower()
        tier = TOPIC_VOLATILITY.get(normalized)
        if tier:
            tiers_seen.add(tier)

    if not tiers_seen:
        return DEFAULT_VOLATILITY
    if HIGH in tiers_seen:
        return HIGH
    if MEDIUM in tiers_seen:
        return MEDIUM
    return LOW


def pair_volatility(tags_a: list[str] | None, tags_b: list[str] | None) -> str:
    """
    Volatility for a retcon PAIR. Takes the highest tier from either claim's
    tags. A retcon pair involving even one volatile topic is treated as
    volatile for scoring purposes.
    """
    union = list(set((tags_a or []) + (tags_b or [])))
    return get_volatility(union)
```

**Testable in isolation.** No dependencies on other OSS modules. Unit tests in Step 7.

---

## Module 2: Modality Extraction (`services/oss/src/ingest.py`)

### Prompt extension

Find the existing claim-extraction system prompt (`PROCESS_SYSTEM` or equivalent) and append the modality instruction. The exact insertion point is right before the JSON schema example.

```
For each claim, also tag its MODALITY — the kind of claim it is:

  "fact"        — states what happened, is happening, or has happened.
                  A verifiable or observable assertion about the world.
                  Examples: "Six merchant ships turned around."
                            "The US Navy deployed three carriers."

  "speculation" — predicts, forecasts, or describes a causal chain that
                  has not yet resolved.
                  Examples: "The blockade is likely to fail within 72 hours."
                            "Analysts expect a ceasefire by Friday."

  "opinion"     — expresses a value judgment (good/bad, right/wrong,
                  success/failure as evaluation rather than observation).
                  Examples: "This deployment is a strategic catastrophe."
                            "The administration's response has been weak."

  "framing"     — the underlying fact is stated with loaded or contested
                  vocabulary that is itself a persuasion choice.
                  Examples: "freedom fighters" vs "insurgents"
                            "collateral damage" vs "civilian casualties"

If a claim mixes modes, pick the one that carries the most semantic weight.
When in doubt between fact and speculation, pick fact only if the claim
is about something already confirmed to have happened.
```

### Schema extension

The extraction schema the LLM is asked to return — locate the existing schema (per-claim shape) and add one field:

```json
{
  "claim_text": "...",
  "modality": "fact",
  "topic_tags": [...]
}
```

### Parser robustness

In the claim-extraction result parser, pick up the modality field with a safe default:

```python
# In whatever function parses the extraction response into claim dicts
claim_modality = (raw_claim.get("modality") or "unknown").strip().lower()
if claim_modality not in ("fact", "speculation", "opinion", "framing", "unknown"):
    claim_modality = "unknown"
```

### Insert path

The existing `insert_claim` (or equivalent) SQL already takes topic_tags etc. Add `modality` to the INSERT column list and values tuple. The default on the column guarantees historical compatibility; new rows get populated.

Locate the current `INSERT INTO claims (...)` statement and extend it:

```python
cur.execute("""
    INSERT INTO claims
      (source_id, raw_text, claim_text, article_url, article_title,
       topic_tags, technique_class, published_at, faiss_id, modality)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id
""", (source_id, raw_text, claim_text, article_url, article_title,
      topic_tags, technique_class, published_at, faiss_id, claim_modality))
```

---

## Module 3: Signal Classifier (`services/oss/src/contradict.py`)

### New constants

Added near the top of `contradict.py`, next to existing similarity thresholds.

```python
# --- Narrative Stability signal classification -----------------------------

# Signal classes — enum-style string constants
SIGNAL_REALITY_UPDATE    = "reality_update"
SIGNAL_HONEST_CORRECTION = "honest_correction"
SIGNAL_HEALTHY_UPDATE    = "healthy_update"
SIGNAL_SILENT_ERROR      = "silent_error"
SIGNAL_NARRATIVE_REWRITE = "narrative_rewrite"
SIGNAL_EDITORIAL_DRIFT   = "editorial_drift"
SIGNAL_UNCATEGORIZED     = "uncategorized"

# Signal score lookup. Tunable.
SIGNAL_SCORES: dict[str, float] = {
    SIGNAL_NARRATIVE_REWRITE: 1.0,
    SIGNAL_EDITORIAL_DRIFT:   0.9,
    SIGNAL_SILENT_ERROR:      0.6,
    SIGNAL_UNCATEGORIZED:     0.4,
    SIGNAL_HONEST_CORRECTION: 0.1,
    SIGNAL_HEALTHY_UPDATE:    0.05,
    SIGNAL_REALITY_UPDATE:    0.0,
}

# Valid modalities (must match claims.modality check constraint)
VALID_MODALITIES = {"fact", "speculation", "opinion", "framing", "unknown"}
```

### `classify_retcon_signal()` — pure function

```python
def classify_retcon_signal(
    modality_a: str,
    modality_b: str,
    volatility: str,
    acknowledged: bool,
) -> tuple[str, float]:
    """
    Map (modality × volatility × acknowledgment) → (signal_class, signal_score).

    Rules (see NARRATIVE_STABILITY_SPEC_L3.md signal table):

    1. Framing on either side → editorial_drift, regardless of ack.
       (Framing retcons are always a signal; acknowledgment is not really
       available for vocabulary choices in the journalistic convention.)

    2. If either modality is speculation or opinion:
       - acknowledged → healthy_update
       - silent       → narrative_rewrite

    3. If both are fact:
       - volatility=high                    → reality_update (ack irrelevant)
       - volatility=medium, acknowledged    → honest_correction
       - volatility=medium, silent          → silent_error
       - volatility=low,    acknowledged    → honest_correction
       - volatility=low,    silent          → narrative_rewrite

    4. If either modality is 'unknown' (and none of the above fire):
       → uncategorized

    This is a pure function. No DB, no LLM, no side effects. Deterministic
    given the inputs.
    """
    # Normalize
    ma = (modality_a or "unknown").lower()
    mb = (modality_b or "unknown").lower()
    if ma not in VALID_MODALITIES:
        ma = "unknown"
    if mb not in VALID_MODALITIES:
        mb = "unknown"
    vol = (volatility or "medium").lower()
    if vol not in ("high", "medium", "low"):
        vol = "medium"

    # Rule 1: framing is always a signal
    if ma == "framing" or mb == "framing":
        return SIGNAL_EDITORIAL_DRIFT, SIGNAL_SCORES[SIGNAL_EDITORIAL_DRIFT]

    # Rule 2: speculation / opinion
    if ma in ("speculation", "opinion") or mb in ("speculation", "opinion"):
        if acknowledged:
            return SIGNAL_HEALTHY_UPDATE, SIGNAL_SCORES[SIGNAL_HEALTHY_UPDATE]
        return SIGNAL_NARRATIVE_REWRITE, SIGNAL_SCORES[SIGNAL_NARRATIVE_REWRITE]

    # Rule 3: both fact
    if ma == "fact" and mb == "fact":
        if vol == "high":
            return SIGNAL_REALITY_UPDATE, SIGNAL_SCORES[SIGNAL_REALITY_UPDATE]
        if acknowledged:
            return SIGNAL_HONEST_CORRECTION, SIGNAL_SCORES[SIGNAL_HONEST_CORRECTION]
        if vol == "low":
            return SIGNAL_NARRATIVE_REWRITE, SIGNAL_SCORES[SIGNAL_NARRATIVE_REWRITE]
        return SIGNAL_SILENT_ERROR, SIGNAL_SCORES[SIGNAL_SILENT_ERROR]

    # Rule 4: fallback
    return SIGNAL_UNCATEGORIZED, SIGNAL_SCORES[SIGNAL_UNCATEGORIZED]
```

### `insert_contradiction()` signature extension

The existing `insert_contradiction` function takes `(conn, claim_a_id, claim_b_id, relationship, confidence, source_acknowledged, technique_class, reasoning)`. Extend to also take the new fields:

```python
def insert_contradiction(conn, claim_a_id, claim_b_id, relationship,
                        confidence, source_acknowledged, technique_class,
                        reasoning, modality_a, modality_b, volatility,
                        signal_class, signal_score):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO contradictions
              (claim_a_id, claim_b_id, relationship, confidence,
               source_acknowledged, technique_class, notes,
               modality_a, modality_b, volatility,
               signal_class, signal_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (claim_a_id, claim_b_id, relationship, confidence,
              source_acknowledged, technique_class, reasoning,
              modality_a, modality_b, volatility,
              signal_class, signal_score))
```

### `scan_new_claims()` integration

In the loop body of `scan_new_claims`, after `classify_contradiction()` returns and *before* `insert_contradiction` is called, compute the signal. The claim rows already include `modality` and `topic_tags` once the SELECT is extended.

Update the SELECT near the top of `scan_new_claims`:

```python
cur.execute("""
    SELECT id, source_id, claim_text, faiss_id, topic_tags, modality
    FROM claims
    WHERE id > %s AND faiss_id IS NOT NULL
    ...
""", ...)
```

Update `get_recent_claims_for_source` similarly so older claims carry `modality` and `topic_tags`.

Then in the pair loop, after classify_contradiction:

```python
# --- Narrative stability signal classification ---
from volatility import pair_volatility

vol = pair_volatility(old_claim.get("topic_tags"), claim.get("topic_tags"))
signal_class, signal_score = classify_retcon_signal(
    modality_a   = old_claim.get("modality") or "unknown",
    modality_b   = claim.get("modality") or "unknown",
    volatility   = vol,
    acknowledged = result.get("source_acknowledged", False),
)

with conn:
    insert_contradiction(
        conn,
        old_claim['id'], claim['id'],
        relationship, result['confidence'],
        result['source_acknowledged'],
        claim.get('technique_class'),
        result.get('reasoning', ''),
        modality_a   = old_claim.get("modality") or "unknown",
        modality_b   = claim.get("modality") or "unknown",
        volatility   = vol,
        signal_class = signal_class,
        signal_score = signal_score,
    )
```

The log line is extended to show signal class:

```python
log.info(f"  [{relationship}/{signal_class}] source={claim['source_id']} "
         f"claims={old_claim['id']}→{claim['id']} "
         f"conf={result['confidence']:.2f} signal={signal_score:.2f}")
```

---

## Module 4: Source Confidence Rewrite

Replace the existing `update_source_confidence()` body. Current logic:

```python
adjustment = -silent_rate * 0.3 + (1.0 - silent_rate) * 0.02 + ack_rate * 0.01
```

Replacement — weights by `signal_score`:

```python
def update_source_confidence(conn, source_id: int, window_days: int = 14):
    """
    Adjust source confidence based on narrative stability of recent retcons.

    The old logic counted silent vs acknowledged retcons one-to-one. This
    weights each retcon by its signal_score, so a reality_update costs
    nothing and a narrative_rewrite costs 1.0× the base rate. Sources that
    update facts as reality moves are no longer punished for doing their job.
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                s.confidence_score,
                s.total_claims,
                COALESCE(SUM(c.signal_score), 0) AS total_signal,
                COUNT(c.id)                      AS retcon_count
            FROM sources s
            LEFT JOIN claims cl ON cl.source_id = s.id
                AND cl.extracted_at >= NOW() - INTERVAL %s
            LEFT JOIN contradictions c
                ON (c.claim_a_id = cl.id OR c.claim_b_id = cl.id)
                AND c.relationship IN ('contradiction', 'retcon_silent', 'retcon_acknowledged')
            WHERE s.id = %s
            GROUP BY s.confidence_score, s.total_claims
        """, (f"{window_days} days", source_id))
        row = cur.fetchone()
        if not row:
            return

        total          = max(row['total_claims'], 1)
        narrative_load = float(row['total_signal']) / total   # [0..1+] in principle
        current        = row['confidence_score']

        # Downweight sources carrying narrative instability. Recovery term
        # pulls clean sources back toward 1.0 over time.
        adjustment = -narrative_load * 0.3 + (1.0 - min(narrative_load, 1.0)) * 0.02
        new_confidence = max(0.1, min(0.99, current + adjustment))

        cur.execute(
            "UPDATE sources SET confidence_score = %s WHERE id = %s",
            (new_confidence, source_id)
        )
```

Note: the SQL interval parameter is passed as a string because psycopg2 doesn't directly parameterize INTERVAL literals — standard workaround.

---

## Testing Criteria

### Pure-function tests (`services/oss/tests/test_classify_retcon_signal.py` or inline)

| # | modality_a | modality_b | volatility | ack  | expected signal class |
|---|-----------|-----------|-----------|------|----------------------|
| 1 | fact | fact | high | false | `reality_update` |
| 2 | fact | fact | high | true  | `reality_update` |
| 3 | fact | fact | medium | true | `honest_correction` |
| 4 | fact | fact | medium | false | `silent_error` |
| 5 | fact | fact | low | true | `honest_correction` |
| 6 | fact | fact | low | false | `narrative_rewrite` |
| 7 | speculation | fact | medium | false | `narrative_rewrite` |
| 8 | speculation | speculation | medium | true | `healthy_update` |
| 9 | opinion | fact | medium | false | `narrative_rewrite` |
| 10 | fact | framing | medium | false | `editorial_drift` |
| 11 | fact | framing | medium | true | `editorial_drift` |
| 12 | unknown | fact | medium | false | `uncategorized` |
| 13 | bogus | fact | medium | false | `uncategorized` (normalized to unknown) |
| 14 | fact | fact | invalid | false | defaults to medium → `silent_error` |

### Volatility lookup tests

| # | input tags | expected tier |
|---|-----------|---------------|
| 15 | `['iran-hormuz']` | `high` |
| 16 | `['iran']` | `medium` |
| 17 | `['history']` | `low` |
| 18 | `['iran', 'iran-hormuz']` | `high` (highest wins) |
| 19 | `['unmapped_topic']` | `medium` (default) |
| 20 | `[]` | `medium` |
| 21 | `None` | `medium` |
| 22 | `['iran', 'unmapped']` | `medium` |

### Corpus reclassification tests (against the 7 retcons in the contradictions table)

Once Step 5 is deployed, run `scan_new_claims(since_claim_id=0)` in manual mode (via `/admin/ingest`) to re-score existing contradictions. Required outcomes:

| # | description | required signal class |
|---|-------------|----------------------|
| 23 | AP: Pope Leo XIII contradiction (stable-fact, silent) | `silent_error` or `narrative_rewrite` (depends on modality of the two claims — Pope identity is a low-volatility fact, either is defensible) |
| 24 | Reuters: US-Iran negotiation-status triple | all three pairs → `narrative_rewrite` (modality = speculation, silent) |
| 25 | AP: CENTCOM force posture (causal inversion) | `narrative_rewrite` or `editorial_drift` |
| 26 | Reuters: war-risk premiums | `narrative_rewrite` (speculation, silent) |

Acceptance threshold: **at least 5 of 7 existing contradictions must land in a non-`reality_update` class** after reclassification. The current scheme scores all 7 equivalently; this alone validates that modality is producing differentiation.

### End-to-end test

On the next autonomous scheduler pass after deployment:

1. New claims are extracted with non-null `modality` field (non-`unknown` rate ≥ 80% across the batch, measured via `SELECT COUNT(*) FILTER (WHERE modality = 'unknown') / COUNT(*)` over the pass's new rows).
2. `scan_new_claims` runs, inserts rows with `signal_class` and `signal_score` populated.
3. Log line includes `[contradiction/<signal_class>]` and `signal=<score>`.
4. `update_source_confidence` reads `signal_score` from the SUM query without error.
5. At least one new contradiction lands in a non-`reality_update` signal class within 2 passes (proving the pipeline generates meaningful diversity, not degenerate all-same output).

---

## Build Sequence

Each step is deployable in isolation. The pipeline is correct at every intermediate state.

1. **Migration** — create `011_narrative_stability.sql`, apply with `psql` inside `oss_postgres`. Verify columns exist via `\d claims` and `\d contradictions`.

2. **`volatility.py`** — new file. Syntax-check in isolation. Copy into `oss_app:/app/src/volatility.py`.

3. **Unit tests for classify_retcon_signal and get_volatility** — run before wiring. Either a pytest file under `services/oss/tests/` or an inline `python -c` smoke-test script. Block the build if any of the 22 tests fail.

4. **Extend ingest prompt + parser + insert** — modify `ingest.py`. Claims landing after deploy will have `modality` populated; historical rows keep `'unknown'`. Spot-check: `SELECT modality, COUNT(*) FROM claims WHERE extracted_at > NOW() - INTERVAL '10 min' GROUP BY modality`.

5. **Wire signal classifier into `scan_new_claims`** — modify `contradict.py`. Extend the SELECT to include `modality, topic_tags` on both query paths. Call `classify_retcon_signal` per pair. Extend `insert_contradiction` signature.

6. **Rewrite `update_source_confidence`** — replace body per Module 4 above.

7. **Deploy** — copy all three modified files + new volatility.py to the container. Restart `oss_app`. Verify startup logs clean.

8. **Manual reclassification pass** — call `/admin/ingest` with analyst token to force `scan_new_claims(since_claim_id=0)`. This would re-scan all claims but each pair already has `contradiction_already_exists` guard, so no duplicate rows. We need to **update** the existing 7 rows with modality/signal — this is the one tricky part. Options:
   - (a) Write a one-shot backfill script that iterates existing contradictions, looks up modality and topic_tags for each claim_a/claim_b pair, calls `classify_retcon_signal`, and UPDATEs the row.
   - (b) Skip historical backfill. Let the 7 existing rows stay NULL on the new columns and only score forward.
   - **Choice:** (a) for the 7 tonight's contradictions so the reclassification tests (Testing Criteria #23–26) can run. But historical rows with `modality='unknown'` on the claim side will mostly land in `uncategorized`. That's fine — it's visible in the data as "pre-modality retcons" and can be re-scored later if ingest backfills modality on old claims.

9. **Verify end-to-end** — wait for the next autonomous pass (or manually trigger ingestion), confirm new contradictions land with signal_class set, and that `update_source_confidence` runs without error.

10. **Optional Phase 2 (not part of this spec):** analyst UI NARRATIVE header badge and SWARMFISH bridge integration. These are clean follow-ons once the data is flowing.

---

## What This Does NOT Do

- **No cross-source contradictions.** Still intra-source only.
- **No LLM call for signal classification.** Pure deterministic logic over modality + volatility + acknowledgment.
- **No historical modality backfill.** Existing 10k claims keep `modality='unknown'` until a separate re-extraction job runs. Retcons involving two unknown-modality claims will land in `uncategorized`.
- **No modality calibration or drift detection.** The 4B extraction model's tagging is trusted as-is. If quality is poor, that's a separate investigation.
- **No Phase 2 UI work.** The NARRATIVE header badge and SWARMFISH bridge extension are listed in the design note but deferred until this spec's data pipeline is proven stable.
- **No automatic re-scoring of old contradictions** when modality is backfilled later. When that happens, it becomes a separate maintenance script.

---

## Config Summary

```bash
# Environment variables (all optional, have defaults)
OSS_DEFAULT_VOLATILITY=medium        # Fallback for unmapped topics
OSS_CONTRADICT_BUDGET=50             # Unchanged — per-pass LLM classify budget
# No new envvars introduced by this spec.
```

All new tunables live in code constants (`SIGNAL_SCORES`, `TOPIC_VOLATILITY`) where they're easy to audit in a PR.

---

## Validation

The spec is validated when:

1. Migration applies cleanly on the live `oss_postgres` instance with no data loss.
2. All 22 pure-function tests pass.
3. At least 5 of 7 existing contradictions reclassify into non-`reality_update` buckets during the backfill (Step 8).
4. The next autonomous pass produces new contradictions with non-null `signal_class` on every row.
5. `update_source_confidence` runs without raising, and at least one source's confidence_score changes as a result of the weighted update.
6. A source with only `reality_update` retcons in its window sees `narrative_load = 0` and the recovery term applies (confidence nudged UP, not down).

If all six conditions hold, the spec is validated and Phase 2 (analyst UI + SWARMFISH integration) becomes the next planning scope.

---

*The modality field is the axis. Everything else is multiplication.*
