# Adversarial Input Layer — L3 Specification

**Version:** 1.0 (Phase 1)
**Date:** 2026-04-14
**Status:** Ready to build
**Motivated by:** Adversarial Input Layer Design Note (2026-04-14). The current OSS ingestion pipeline is a blind transcriber — it stores claims without evaluating them against the system's existing knowledge. This spec translates the four Phase 1 components from the design note (Prior Injection, Surprise Scoring v1, Verdict Compilation, Escalation Router) into concrete implementation. Components 3 (Dialectical Counter-Claim Synthesis) and 4 (Fabrication Premortem) are explicitly deferred to Phase 2 per the design note's build sequence.
**Design note:** [specs/ADVERSARIAL_INPUT_LAYER_DESIGN_NOTE.md](ADVERSARIAL_INPUT_LAYER_DESIGN_NOTE.md)
**Research foundation:** [specs/INPUT_SCRUTINY_RESEARCH_NOTE.md](INPUT_SCRUTINY_RESEARCH_NOTE.md)
**Sibling document:** [specs/ADVERSARIAL_VALIDATION_PROTOCOL.md](ADVERSARIAL_VALIDATION_PROTOCOL.md) — output-side counterpart.
**Modified files:**
- `services/oss/src/scrutiny.py` (new — the main scrutiny pipeline module)
- `services/oss/src/swarmfish_prior.py` (new — prior injection / SWARMFISH session query)
- `services/oss/src/ingest.py` (hook scrutiny into the ingest loop after claim insert)
- `services/oss/migrations/013_adversarial_input_layer.sql` (new)

---

## Summary

Every newly-ingested claim passes through a four-component scrutiny pipeline before final commit of its annotations. The pipeline pulls the current SWARMFISH committee assessment for the claim's topic as a structured prior, computes the claim's semantic distance from the assessment's framing (v1 surprise score), compiles a scrutiny verdict record attached to the claim, and — if escalation cues fire — POSTs a request to SWARMFISH to trigger a fresh committee prediction with the flagged claim included.

The architectural commitment is **annotation-only**. Every claim enters the ledger regardless of scrutiny verdict. Scrutiny decides routing (how much attention a claim gets) and annotation (what verdicts attach to it). Scrutiny never decides whether a claim exists. Consistency with prior beliefs consolidates matching claims; discordant claims escalate at higher priority than concordant ones. This is the Rule 4 commitment from the research note — the structural protection against confirmation cascade.

Phase 1 (this spec) covers Components 1 (Prior Injection), 2 (Surprise Scoring v1), 5 (Verdict Compilation), 6 (Escalation Router). Phase 2 adds Components 3 (Dialectical Counter-Claim Synthesis) and 4 (Fabrication Premortem) and requires more of the ledger + narrative stability + hedge pattern fields to be populated first. Phase 3 adds v2 formal KL-divergence surprise scoring, cross-language support, and retrospective calibration.

---

## Data Model Changes

### New columns on `claims`

```sql
ALTER TABLE claims
    ADD COLUMN IF NOT EXISTS surprise_score    double precision,
    ADD COLUMN IF NOT EXISTS scrutiny_status   text DEFAULT 'pending';

ALTER TABLE claims
    ADD CONSTRAINT claims_scrutiny_status_check
    CHECK (scrutiny_status IN ('pending', 'clean', 'flagged', 'escalated'));

CREATE INDEX IF NOT EXISTS idx_claims_scrutiny_status ON claims(scrutiny_status);
CREATE INDEX IF NOT EXISTS idx_claims_surprise_score ON claims(surprise_score);
```

- `surprise_score` — float in [0, 1] representing the semantic distance of the claim from the current committee framing. Nullable (historical claims have no score). Populated at scrutiny time.
- `scrutiny_status` — enum tracking the pipeline state. `pending` is the default on insert; the scrutiny pipeline updates it to `clean`, `flagged`, or `escalated` after running.

### New table `scrutiny_verdicts`

Append-only log of scrutiny checks per claim. Each pipeline run writes one row per check performed, so a single claim typically gets 2-4 verdict rows.

```sql
CREATE TABLE IF NOT EXISTS scrutiny_verdicts (
    id              serial PRIMARY KEY,
    claim_id        int NOT NULL REFERENCES claims(id),
    check_name      text NOT NULL,
    timestamp       timestamptz NOT NULL DEFAULT NOW(),
    result          text NOT NULL,
    confidence      double precision,
    numeric_value   double precision,
    reasoning       text,
    escalated       boolean NOT NULL DEFAULT false,
    metadata        jsonb,
    supersedes      int REFERENCES scrutiny_verdicts(id),
    CHECK (result IN ('pass', 'fail', 'warn'))
);

CREATE INDEX IF NOT EXISTS idx_scrutiny_verdicts_claim ON scrutiny_verdicts(claim_id);
CREATE INDEX IF NOT EXISTS idx_scrutiny_verdicts_check ON scrutiny_verdicts(check_name);
CREATE INDEX IF NOT EXISTS idx_scrutiny_verdicts_escalated
    ON scrutiny_verdicts(escalated) WHERE escalated = true;
CREATE INDEX IF NOT EXISTS idx_scrutiny_verdicts_timestamp ON scrutiny_verdicts(timestamp);
```

**Append-only guarantee:** verdicts are never UPDATED after write. Corrections create new rows with a `supersedes` FK pointing at the old row. This is enforced by convention (the insert function never UPDATEs) and by the audit trail visibility.

### New table `escalation_requests`

Tracks which claims the scrutiny pipeline escalated to SWARMFISH and what happened next.

```sql
CREATE TABLE IF NOT EXISTS escalation_requests (
    id                      serial PRIMARY KEY,
    claim_id                int NOT NULL REFERENCES claims(id),
    triggered_by            text[] NOT NULL,
    topic                   text,
    request_timestamp       timestamptz NOT NULL DEFAULT NOW(),
    swarmfish_session_id    uuid,
    committee_decision      text,
    committee_decision_at   timestamptz
);

CREATE INDEX IF NOT EXISTS idx_escalation_requests_claim ON escalation_requests(claim_id);
CREATE INDEX IF NOT EXISTS idx_escalation_requests_topic ON escalation_requests(topic);
CREATE INDEX IF NOT EXISTS idx_escalation_requests_timestamp ON escalation_requests(request_timestamp);
CREATE UNIQUE INDEX IF NOT EXISTS uq_escalation_cooldown
    ON escalation_requests(topic, request_timestamp);
```

### Migration file

`services/oss/migrations/013_adversarial_input_layer.sql` — all ALTERs + CREATE TABLEs wrapped in `BEGIN ... COMMIT`. Idempotent via `IF NOT EXISTS`. Check constraints wrapped in `DO $$ ... END$$` blocks for concurrent-migration safety.

---

## Module 1: `services/oss/src/swarmfish_prior.py` (new)

Prior Injection component. Pulls SWARMFISH committee assessments and packages them as structured topic priors for the scrutiny pipeline to consume.

```python
"""
swarmfish_prior.py — Prior injection for the adversarial input layer.

Pulls the current SWARMFISH committee assessment for each active topic and
packages it as a structured TopicPrior that the scrutiny pipeline uses as
its reference model for surprise scoring.

Design: specs/ADVERSARIAL_INPUT_LAYER_DESIGN_NOTE.md, Component 1
Spec: specs/ADVERSARIAL_INPUT_LAYER_SPEC_L3.md, Module 1
"""

import os
import logging
import requests
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

log = logging.getLogger(__name__)

SWARMFISH_URL = os.environ.get("SWARMFISH_BASE_URL", "http://host.docker.internal:7732")
SWARMFISH_TIMEOUT = float(os.environ.get("SWARMFISH_QUERY_TIMEOUT", "5.0"))
PRIOR_CACHE_TTL = int(os.environ.get("OSS_PRIOR_CACHE_TTL", "60"))  # seconds


@dataclass
class TopicPrior:
    """The committee's current framing of a topic, packaged for scrutiny."""
    topic: str
    committee_consensus: float
    committee_range_low: float
    committee_range_high: float
    committee_meta: str              # "HIGH" | "MEDIUM" | "LOW"
    committee_sigma: float
    di_surprising_facts: list[str] = field(default_factory=list)
    di_consensus_warning: Optional[str] = None
    assessment_timestamp: Optional[datetime] = None
    freshness: Optional[timedelta] = None   # now - assessment_timestamp
    framing_text: Optional[str] = None      # composed natural-language framing

    def is_stale(self, max_age_minutes: int = 90) -> bool:
        if self.freshness is None:
            return True
        return self.freshness > timedelta(minutes=max_age_minutes)

    def authority_weight(self) -> float:
        """
        Freshness-based weighting on the prior's authority.
        Fresh priors (< 15 min) weight ~1.0. Stale priors (> 2 hours)
        weight ~0.3. Linear decay in between. Capped at [0.3, 1.0].
        """
        if self.freshness is None:
            return 0.3
        mins = self.freshness.total_seconds() / 60
        if mins < 15:
            return 1.0
        if mins > 120:
            return 0.3
        return max(0.3, 1.0 - (mins - 15) / 150)  # linear decay 1.0 → 0.3


# In-memory cache: {topic: (TopicPrior, fetched_at_datetime)}
_prior_cache: dict[str, tuple[TopicPrior, datetime]] = {}


def get_topic_prior(topic: str) -> Optional[TopicPrior]:
    """
    Fetch the current committee assessment for a topic. Returns None if
    SWARMFISH has not assessed this topic or if the service is unreachable.
    Cached for PRIOR_CACHE_TTL seconds to avoid hammering the endpoint.
    """
    now = datetime.now(timezone.utc)

    # Cache hit?
    if topic in _prior_cache:
        cached_prior, fetched_at = _prior_cache[topic]
        if (now - fetched_at).total_seconds() < PRIOR_CACHE_TTL:
            return cached_prior

    # Fresh fetch
    try:
        response = requests.get(
            f"{SWARMFISH_URL}/acp/sessions",
            params={"topic": topic, "limit": 1, "order": "desc"},
            timeout=SWARMFISH_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        log.warning(f"[PRIOR] Failed to fetch SWARMFISH assessment for topic={topic!r}: {e}")
        return None

    sessions = data.get("sessions") or []
    if not sessions:
        log.info(f"[PRIOR] No SWARMFISH assessment found for topic={topic!r}")
        return None

    session = sessions[0]

    # Parse the session fields into a TopicPrior
    try:
        created_at_raw = session.get("created_at")
        assessment_ts = (
            datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
            if created_at_raw else None
        )
        freshness = (now - assessment_ts) if assessment_ts else None

        prior = TopicPrior(
            topic=topic,
            committee_consensus=float(session.get("consensus_confidence") or 0.5),
            committee_range_low=float(session.get("consensus_range_low") or 0.0),
            committee_range_high=float(session.get("consensus_range_high") or 1.0),
            committee_meta=(session.get("meta_confidence") or "MEDIUM").upper(),
            committee_sigma=float(session.get("disagreement_level") or 0.0),
            di_surprising_facts=session.get("di_surprising_facts") or [],
            di_consensus_warning=session.get("di_consensus_warning"),
            assessment_timestamp=assessment_ts,
            freshness=freshness,
        )
        prior.framing_text = compose_framing_text(prior)

        _prior_cache[topic] = (prior, now)
        return prior
    except Exception as e:
        log.warning(f"[PRIOR] Failed to parse SWARMFISH session for topic={topic!r}: {e}")
        return None


def compose_framing_text(prior: TopicPrior) -> str:
    """
    Compose a natural-language summary of the committee's current framing
    of the topic. This text is embedded and used as the anchor for
    surprise scoring.
    """
    parts = [
        f"Topic: {prior.topic}.",
        f"Committee consensus: {prior.committee_consensus:.2f} "
        f"(range {prior.committee_range_low:.2f}-{prior.committee_range_high:.2f}).",
        f"Meta-confidence: {prior.committee_meta}. Disagreement sigma: {prior.committee_sigma:.2f}.",
    ]

    if prior.di_surprising_facts:
        parts.append("Surprising facts surfaced by Devil's Inquisitor: "
                     + " ".join(prior.di_surprising_facts[:3]))

    if prior.di_consensus_warning:
        parts.append(f"Consensus warning: {prior.di_consensus_warning}")

    return " ".join(parts)


def clear_cache():
    """Testing hook — drop the in-memory prior cache."""
    _prior_cache.clear()
```

**Dependencies:** `requests` (already in use elsewhere in OSS). The SWARMFISH endpoint `/acp/sessions` is the existing session query endpoint from swarmfish service; if it doesn't support filtering by topic + limit + order, those query parameters are a small extension to `services/swarmfish/src/app.py` that lands in the build step.

---

## Module 2: Surprise Scoring

Second component. Pure function that computes the semantic distance between a claim and the committee's current framing. v1 uses cosine distance via the existing `sentence-transformers` embedding model.

Implemented as functions within `scrutiny.py`:

```python
# services/oss/src/scrutiny.py (excerpt)

import numpy as np
from sentence_transformers import SentenceTransformer

_embedder: Optional[SentenceTransformer] = None

def get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def compute_raw_surprise(claim_text: str, prior: TopicPrior) -> float:
    """
    Semantic distance between a claim and the committee's current framing.
    Returns a float in [0, 1] where 1 is maximum surprise.
    """
    if not prior or not prior.framing_text:
        return 0.5  # neutral when no prior available

    embedder = get_embedder()
    claim_vec = embedder.encode(claim_text, normalize_embeddings=True)
    framing_vec = embedder.encode(prior.framing_text, normalize_embeddings=True)

    # Cosine similarity (since vectors are normalized, dot product = cosine)
    similarity = float(np.dot(claim_vec, framing_vec))
    distance = 1.0 - similarity

    # Clamp to [0, 1]
    return max(0.0, min(1.0, distance))


def compute_weighted_surprise(raw_surprise: float,
                              source_reliability: float,
                              prior_authority: float) -> float:
    """
    Zlotnick R = P × L adapted for scrutiny.

    raw_surprise       — semantic distance in [0, 1]
    source_reliability — source's confidence_score in [0, 1]
    prior_authority    — prior.authority_weight() based on freshness in [0.3, 1.0]

    The product: a highly surprising claim from a reliable source against
    a fresh committee assessment is the maximum weighted signal. A surprising
    claim from an unreliable source (low reliability) or against a stale
    assessment (low authority) gets proportionally discounted.
    """
    return raw_surprise * source_reliability * prior_authority
```

**Threshold (first-pass):** `weighted_surprise > 0.4` triggers escalation. Tunable via `OSS_SURPRISE_THRESHOLD` env var. Expect to retune after first production data.

---

## Module 3: Verdict Compilation (Component 5)

Writes scrutiny verdicts to the append-only log. One function per check type.

```python
# services/oss/src/scrutiny.py (continued)

def write_verdict(conn,
                  claim_id: int,
                  check_name: str,
                  result: str,
                  confidence: Optional[float] = None,
                  numeric_value: Optional[float] = None,
                  reasoning: Optional[str] = None,
                  escalated: bool = False,
                  metadata: Optional[dict] = None) -> int:
    """
    Append-only verdict insertion. Returns the verdict id.
    Never UPDATEs — corrections create new rows with supersedes FK.
    """
    import json
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO scrutiny_verdicts
              (claim_id, check_name, result, confidence, numeric_value,
               reasoning, escalated, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (claim_id, check_name, result, confidence, numeric_value,
              reasoning, escalated,
              json.dumps(metadata) if metadata else None))
        row = cur.fetchone()
        return row['id']
```

---

## Module 4: Escalation Router (Component 6)

Decides which claims warrant escalation and POSTs to SWARMFISH.

```python
# services/oss/src/scrutiny.py (continued)

ESCALATION_COOLDOWN_MINUTES = int(os.environ.get("OSS_ESCALATION_COOLDOWN_MIN", "15"))
SURPRISE_THRESHOLD = float(os.environ.get("OSS_SURPRISE_THRESHOLD", "0.4"))


def should_escalate(claim: dict, weighted_surprise: float, prior: Optional[TopicPrior]) -> tuple[bool, list[str]]:
    """
    Evaluate escalation cues. Returns (should_escalate, list_of_triggered_cues).
    Any single cue firing is sufficient to escalate (recall-biased).
    """
    triggered = []

    if weighted_surprise > SURPRISE_THRESHOLD:
        triggered.append("high_surprise")

    # Source novelty: less than N claims total from this source in the ledger
    if (claim.get("source_total_claims") or 0) < 50:
        triggered.append("source_novelty")

    # Narrative_campaign flag from hedge pattern (Phase 1 — may be None if hedge
    # pattern is not yet deployed, in which case skip)
    if claim.get("source_narrative_campaign_active"):
        triggered.append("narrative_campaign_source")

    # Prior is missing and the claim is on a topic SWARMFISH should know about
    if prior is None and claim.get("topic_has_hypotheses"):
        triggered.append("missing_prior_on_tracked_topic")

    return (len(triggered) > 0, triggered)


def check_cooldown(conn, topic: str) -> bool:
    """
    Return True if this topic is within the escalation cooldown window
    (i.e., we should skip escalation to avoid flooding SWARMFISH).
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1 FROM escalation_requests
            WHERE topic = %s
              AND request_timestamp >= NOW() - (%s || ' minutes')::interval
            LIMIT 1
        """, (topic, ESCALATION_COOLDOWN_MINUTES))
        return cur.fetchone() is not None


def request_escalation(conn,
                       claim: dict,
                       topic: str,
                       triggered_cues: list[str],
                       reasoning: str) -> Optional[int]:
    """
    Write an escalation_requests row and POST to SWARMFISH monitor endpoint.
    Returns the escalation_requests.id or None if cooldown blocked it.
    """
    if check_cooldown(conn, topic):
        log.info(f"[ESCALATE] Skipped for topic={topic!r} (in cooldown)")
        return None

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO escalation_requests
              (claim_id, triggered_by, topic)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (claim["id"], triggered_cues, topic))
        escalation_id = cur.fetchone()["id"]

    # POST to SWARMFISH asynchronously via a fire-and-forget request
    try:
        response = requests.post(
            f"{SWARMFISH_URL}/monitor/trigger",
            json={
                "claim_id": claim["id"],
                "topic": topic,
                "triggered_by": triggered_cues,
                "reasoning": reasoning,
                "escalation_id": escalation_id,
            },
            timeout=3.0,  # short timeout; we don't block on SWARMFISH's response
        )
        log.info(f"[ESCALATE] id={escalation_id} topic={topic!r} cues={triggered_cues} "
                 f"swarmfish_status={response.status_code}")
    except Exception as e:
        log.warning(f"[ESCALATE] id={escalation_id} — SWARMFISH trigger failed: {e}")
        # Failure to reach SWARMFISH is not a scrutiny error — the escalation
        # is still logged. A future monitor retry mechanism can pick it up.

    return escalation_id
```

**Note on the SWARMFISH `/monitor/trigger` endpoint:** this endpoint may not exist on the current SWARMFISH service. If it doesn't, the build step adds a simple handler that accepts the POST, logs it, and schedules a fresh prediction on the next monitor cycle. Minimal extension.

---

## Module 5: Main Scrutiny Pipeline (`scrutiny.py`)

The orchestrator that ties Components 1, 2, 5, 6 together.

```python
# services/oss/src/scrutiny.py (main entry point)

def scrutinize_claim(conn, claim: dict) -> dict:
    """
    Run the full scrutiny pipeline on a single claim.

    claim: dict with fields id, source_id, claim_text, topic_tags, faiss_id, ...
           plus source_total_claims and source_confidence (from JOIN upstream)

    Returns: dict with {status, surprise_score, weighted_surprise, escalated,
                        triggered_cues, verdict_ids}
    """
    claim_id = claim["id"]
    topic_tags = claim.get("topic_tags") or []
    primary_topic = topic_tags[0] if topic_tags else None

    # Component 1: Prior injection
    prior = get_topic_prior(primary_topic) if primary_topic else None

    # Component 2: Surprise scoring
    raw_surprise = compute_raw_surprise(claim["claim_text"], prior) if prior else 0.5
    source_reliability = claim.get("source_confidence") or 0.7
    prior_authority = prior.authority_weight() if prior else 0.3
    weighted_surprise = compute_weighted_surprise(
        raw_surprise, source_reliability, prior_authority
    )

    verdict_ids = []

    # Write surprise score verdict
    verdict_ids.append(write_verdict(
        conn, claim_id,
        check_name="surprise_score",
        result="warn" if weighted_surprise > SURPRISE_THRESHOLD else "pass",
        numeric_value=weighted_surprise,
        confidence=prior_authority,
        reasoning=(
            f"semantic distance from committee framing: {raw_surprise:.2f}; "
            f"reliability-weighted: {weighted_surprise:.2f}"
            if prior else "no committee prior available"
        ),
        escalated=False,  # will be updated if escalation fires below
        metadata={
            "raw_surprise": raw_surprise,
            "source_reliability": source_reliability,
            "prior_authority": prior_authority,
            "topic": primary_topic,
            "prior_fresh": (
                prior.freshness.total_seconds() / 60
                if prior and prior.freshness else None
            ),
        },
    ))

    # Update claim with surprise score
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE claims SET surprise_score = %s WHERE id = %s",
            (weighted_surprise, claim_id),
        )

    # Component 6: Escalation router
    should_esc, triggered_cues = should_escalate(claim, weighted_surprise, prior)
    escalated = False

    if should_esc and primary_topic:
        escalation_id = request_escalation(
            conn, claim, primary_topic, triggered_cues,
            reasoning=(
                f"scrutiny escalation for claim {claim_id}: "
                f"weighted_surprise={weighted_surprise:.2f}, "
                f"cues={','.join(triggered_cues)}"
            ),
        )
        if escalation_id is not None:
            escalated = True
            # Write the escalation verdict
            verdict_ids.append(write_verdict(
                conn, claim_id,
                check_name="escalation",
                result="warn",
                reasoning=f"Escalated to SWARMFISH: {','.join(triggered_cues)}",
                escalated=True,
                metadata={
                    "escalation_id": escalation_id,
                    "triggered_by": triggered_cues,
                },
            ))

    # Determine terminal scrutiny_status
    if escalated:
        status = "escalated"
    elif weighted_surprise > SURPRISE_THRESHOLD:
        status = "flagged"
    else:
        status = "clean"

    with conn.cursor() as cur:
        cur.execute(
            "UPDATE claims SET scrutiny_status = %s WHERE id = %s",
            (status, claim_id),
        )

    conn.commit()

    return {
        "status": status,
        "surprise_score": weighted_surprise,
        "raw_surprise": raw_surprise,
        "escalated": escalated,
        "triggered_cues": triggered_cues,
        "verdict_ids": verdict_ids,
    }
```

---

## Module 6: Ingest Hook

Scrutiny runs after `insert_claim` returns, per claim, inside the existing ingestion loop.

### Integration into `ingest.py`

```python
# In the per-claim loop inside run_once / fetch_feed / process_article flow:

for item in processed:
    # ... existing extraction, dedup, FAISS insert, insert_claim ...

    with conn:
        new_claim_id = insert_claim(
            conn, source_id, raw_text, claim_text, article_url,
            article_title, topic_tags, technique_class,
            published_at, faiss_id, modality,
            certainty, attribution, quoted_directly,
        )
        update_topic_last_active(conn, topic_tags)

    # NEW: run scrutiny on the just-inserted claim
    try:
        from scrutiny import scrutinize_claim
        # Pull the full claim row for scrutiny
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.id, c.source_id, c.claim_text, c.topic_tags,
                       c.faiss_id, s.total_claims AS source_total_claims,
                       s.confidence_score AS source_confidence
                FROM claims c
                JOIN sources s ON c.source_id = s.id
                WHERE c.id = %s
            """, (new_claim_id,))
            claim_row = cur.fetchone()

        if claim_row:
            scrutinize_claim(conn, dict(claim_row))
    except Exception as e:
        log.warning(f"[SCRUTINY] failed for claim_id={new_claim_id}: {e}")
        # Scrutiny failure does NOT prevent the claim from being stored.
        # The claim remains in the ledger with scrutiny_status='pending'.

    inserted += 1
```

**Failure isolation:** scrutiny is wrapped in a try/except. If the scrutiny pipeline raises, the claim remains in the ledger with `scrutiny_status='pending'`. The failure is logged but does not propagate to the ingest loop. This preserves the "nothing is filtered" commitment even when scrutiny itself breaks.

---

## Testing Criteria

### Pure-function tests

| # | Check | Expected |
|---|---|---|
| 1 | `compute_raw_surprise(text, None)` | Returns 0.5 (neutral, no prior) |
| 2 | `compute_raw_surprise(identical_framing, prior)` | Returns ~0.0 (maximum similarity) |
| 3 | `compute_raw_surprise(opposite_framing, prior)` | Returns ~1.0 or high (maximum distance) |
| 4 | `compute_weighted_surprise(0.8, 1.0, 1.0)` | Returns 0.8 |
| 5 | `compute_weighted_surprise(0.8, 0.5, 0.5)` | Returns 0.2 |
| 6 | `TopicPrior(freshness=15min).authority_weight()` | Returns 1.0 |
| 7 | `TopicPrior(freshness=150min).authority_weight()` | Returns 0.3 |
| 8 | `should_escalate({...}, 0.5, prior)` with surprise > threshold | Returns (True, ['high_surprise']) |
| 9 | `should_escalate({...}, 0.2, prior)` with no other cues | Returns (False, []) |
| 10 | `check_cooldown(conn, 'iran-hormuz')` with recent escalation | Returns True |
| 11 | `check_cooldown(conn, 'iran-hormuz')` with no recent escalation | Returns False |

### Schema migration tests

Test 12: Migration 013 applies cleanly. All new columns on `claims` exist with correct defaults. `scrutiny_verdicts` and `escalation_requests` tables exist with correct schemas. Indexes exist. Check constraints enforce allowed values.

Test 13: Migration is idempotent — running it twice produces no errors, no duplicate columns, no duplicate indexes.

### Prior injection tests

Test 14: `get_topic_prior('iran-hormuz')` returns a `TopicPrior` with populated fields when SWARMFISH has a recent assessment.

Test 15: `get_topic_prior('nonexistent-topic')` returns None cleanly (no exception).

Test 16: `get_topic_prior('iran-hormuz')` called twice within PRIOR_CACHE_TTL seconds returns the same instance (cache works).

Test 17: SWARMFISH unreachable → `get_topic_prior` returns None and logs warning, does not raise.

### End-to-end tests (after deploy)

Test 18: **Scrutiny runs on new claims.** After first post-deploy ingestion pass, ≥ 95% of new claims have non-null `surprise_score` AND `scrutiny_status != 'pending'`.

Test 19: **Verdict log populated.** For any claim with `scrutiny_status IN ('clean', 'flagged', 'escalated')`, `scrutiny_verdicts` contains at least one row with `check_name = 'surprise_score'`.

Test 20: **At least one escalation within 24 hours.** The pipeline must fire at least one escalation in the first 24 hours of production data. If zero fire, either thresholds are too tight or SWARMFISH is unavailable — either way it's a problem to investigate.

Test 21: **Escalation writes to escalation_requests.** Every `scrutiny_verdicts` row with `escalated=true` has a corresponding row in `escalation_requests`.

Test 22: **Cooldown enforcement.** Multiple claims on the same topic within 15 minutes produce at most one escalation row per 15-minute window.

Test 23: **No claims filtered.** Claims insertion rate is unchanged by the deploy. Verify by comparing hourly insertion counts pre/post.

Test 24: **Scrutiny failure isolation.** If SWARMFISH is stopped and ingestion runs, claims still land in the ledger with `scrutiny_status = 'pending'`. No exception propagation breaks the ingest loop.

Test 25: **Prior authority decays with freshness.** For two claims on the same topic, one scrutinized against a fresh (< 15 min) prior and one against a stale (> 2 hours) prior, the stale one's `prior_authority` metadata should be ≤ 0.3 and the fresh one's ≥ 0.9.

### Operational observability tests

Test 26: **`[SCRUTINY]` log tags appear in oss_app logs** for every pass, with one line per scrutinized claim.

Test 27: **`[ESCALATE]` log tags appear** when escalation fires, including triggered_cues and swarmfish_status.

---

## Build Sequence

Each step is deployable in isolation.

1. **Migration 013.** Write `013_adversarial_input_layer.sql`. Apply via `psql` inside `oss_postgres`. Verify columns + tables + indexes + constraints.

2. **`swarmfish_prior.py`.** New file. Compile-check in isolation. Copy to container. Test `get_topic_prior` against live SWARMFISH endpoint.

3. **SWARMFISH `/acp/sessions` query extension.** If the existing endpoint doesn't support `?topic=X&limit=1&order=desc`, add the parameters. Deploy to swarmfish_app. Verify.

4. **SWARMFISH `/monitor/trigger` endpoint.** If it doesn't exist, add a simple handler that accepts `{claim_id, topic, triggered_by, reasoning, escalation_id}` and logs + schedules a fresh prediction on the next cycle. Deploy to swarmfish_app.

5. **`scrutiny.py` (core module).** New file with `compute_raw_surprise`, `compute_weighted_surprise`, `write_verdict`, `should_escalate`, `check_cooldown`, `request_escalation`, and `scrutinize_claim` orchestrator. Copy to container.

6. **Unit tests for scrutiny pure functions.** Run tests 1-11 against the live container. Block on failure.

7. **Hook scrutiny into `ingest.py`.** Add the scrutinize call inside the per-claim loop after `insert_claim` returns, wrapped in try/except for isolation. Copy to container.

8. **Restart `oss_app`.** Verify clean startup. Verify scheduler initializes. Verify no import errors.

9. **Resume ingestion.** Let one full cycle run. Verify end-to-end tests 18-27.

10. **Spot-check.** Inspect 10 scrutinized claims manually. Verify the surprise scores look reasonable — a committed factual claim about a well-known event should score low; a speculative or unusual claim should score higher.

11. **24-hour observability check.** Review escalation log. If zero escalations fired, investigate (either threshold too high or SWARMFISH endpoint broken). If excessive escalations fired (> 20% of claims), retune threshold.

---

## What This Does NOT Do (Phase 1)

- **No Dialectical Counter-Claim Synthesis (Component 3).** Retrieving contradicting claims from the ledger to link as dialectical pairs is Phase 2. Requires more ledger depth and more of the hedge pattern fields to be populated first.

- **No Fabrication Premortem (Component 4).** The signature-matching premortem is Phase 2. Requires more source intelligence data (cui_bono, technique_class) populated first.

- **No v2 formal Bayesian surprise.** v1 uses cosine semantic distance, which is a proxy. Formal KL divergence over explicit probability models is Phase 3.

- **No retrospective calibration.** The append-only verdict log is designed to support retrospective calibration when ground truth arrives, but the calibration mechanism itself is not in Phase 1.

- **No claim filtering.** Every claim enters the ledger. Scrutiny annotates and routes. Scrutiny never decides whether a claim exists.

- **No auto-update of SWARMFISH posterior.** The layer escalates to SWARMFISH; SWARMFISH's committee decides whether to update. OSS does not directly modify committee assessments.

- **No cross-topic scrutiny.** Each claim is scored against the prior for its primary topic. Claims without topic tags get no prior (surprise defaults to 0.5 neutral).

- **No historical backfill.** Existing claims get `surprise_score=NULL` and `scrutiny_status='pending'` until a one-shot backfill runs. Not in v1 scope.

---

## Config Summary

```bash
# Environment variables (all optional, defaults shown)
SWARMFISH_BASE_URL=http://host.docker.internal:7732
SWARMFISH_QUERY_TIMEOUT=5.0          # seconds
OSS_PRIOR_CACHE_TTL=60               # seconds
OSS_SURPRISE_THRESHOLD=0.4           # weighted surprise above this → escalate
OSS_ESCALATION_COOLDOWN_MIN=15       # minutes between escalations per topic
```

---

## Validation

The spec is Phase-1-validated when:

1. Migration 013 applies cleanly on the live `oss_postgres` instance.
2. All 27 testing criteria pass.
3. First production pass produces claims with non-null `surprise_score` at ≥ 95% coverage.
4. At least one escalation fires within 24 hours of deploy.
5. Cooldown is enforced — no more than 1 escalation per (topic, 15 minutes) window.
6. No claim insertion rate regression from the deploy.
7. SWARMFISH service remains reachable and responsive; escalations trigger fresh prediction cycles.
8. Scrutiny failures (when induced by stopping SWARMFISH) do not propagate exceptions to the ingest loop.

If all eight conditions hold, Phase 1 is validated and Phase 2 (Components 3 and 4) becomes the next planning scope.

---

*Phase 1 gives us the minimal adversarial input layer: pull the committee's current framing, score each incoming claim against it, write a verdict, escalate surprising claims. Components 3 and 4 (dialectical counter-claim retrieval and fabrication premortem) are Phase 2. The guarantee that holds across all phases is structural: the pipeline annotates, it does not filter. Nothing gets dropped. Scrutiny decides routing, never existence.*
