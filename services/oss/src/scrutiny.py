"""
scrutiny.py — The adversarial input layer main pipeline.

Runs after claim insertion in the ingest loop. For each claim:
  1. Pulls the current SWARMFISH committee assessment (prior injection).
  2. Computes semantic distance from the committee's framing (surprise score).
  3. Writes scrutiny verdicts to an append-only log.
  4. Escalates high-surprise claims to SWARMFISH for committee re-prediction.

The pipeline NEVER filters claims. It annotates and routes. Every claim that
enters the ingest loop lands in the ledger regardless of verdict.

Design: specs/ADVERSARIAL_INPUT_LAYER_DESIGN_NOTE.md
Spec: specs/ADVERSARIAL_INPUT_LAYER_SPEC_L3.md
"""

import os
import json
import logging
import urllib.parse
import urllib.request
from typing import Optional

import numpy as np

from swarmfish_prior import TopicPrior, get_topic_prior

log = logging.getLogger(__name__)

# Config
SURPRISE_THRESHOLD = float(os.environ.get("OSS_SURPRISE_THRESHOLD", "0.3"))
ESCALATION_COOLDOWN_MINUTES = int(os.environ.get("OSS_ESCALATION_COOLDOWN_MIN", "15"))
SWARMFISH_URL = os.environ.get("SWARMFISH_BASE_URL", "http://host.docker.internal:7732")
SWARMFISH_TIMEOUT = float(os.environ.get("SWARMFISH_QUERY_TIMEOUT", "5.0"))
ANALYST_TOKEN = os.environ.get("SWARMFISH_ANALYST_TOKEN", "dev_analyst_token")

# Embedding model — shared instance (loaded once on first use)
_embedder = None


def get_embedder():
    """Lazy-load the sentence-transformers model. Shares with FAISS embedder."""
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


# ---------------------------------------------------------------------------
# Component 2: Surprise scoring
# ---------------------------------------------------------------------------

def compute_raw_surprise(claim_text: str, prior: Optional[TopicPrior]) -> float:
    """
    Semantic distance between a claim and the committee's current framing.
    Returns a float in [0, 1] where 1 is maximum surprise.
    No prior → neutral 0.5.
    """
    if not prior or not prior.framing_text:
        return 0.5

    try:
        embedder = get_embedder()
        claim_vec = embedder.encode(
            claim_text, normalize_embeddings=True, show_progress_bar=False
        )
        framing_vec = embedder.encode(
            prior.framing_text, normalize_embeddings=True, show_progress_bar=False
        )
        similarity = float(np.dot(claim_vec, framing_vec))
        distance = 1.0 - similarity
        return max(0.0, min(1.0, distance))
    except Exception as e:
        log.warning(f"[SCRUTINY] compute_raw_surprise failed: {e}")
        return 0.5


def compute_weighted_surprise(raw_surprise: float,
                              source_reliability: float,
                              prior_authority: float) -> float:
    """
    Zlotnick R = P × L adapted for scrutiny.

    raw_surprise       — semantic distance in [0, 1]
    source_reliability — source's confidence_score in [0, 1]
    prior_authority    — prior.authority_weight() based on freshness [0.3, 1.0]

    Product: a highly surprising claim from a reliable source against a fresh
    committee assessment is the maximum weighted signal.
    """
    return max(0.0, min(1.0, raw_surprise * source_reliability * prior_authority))


# ---------------------------------------------------------------------------
# Component 5: Verdict compilation
# ---------------------------------------------------------------------------

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
        return row['id'] if row else -1


# ---------------------------------------------------------------------------
# Component 6: Escalation router
# ---------------------------------------------------------------------------

def should_escalate(claim: dict,
                    weighted_surprise: float,
                    prior: Optional[TopicPrior]) -> tuple:
    """
    Evaluate escalation cues. Returns (should_escalate, triggered_cues_list).
    Any single cue firing is sufficient to escalate (recall-biased).
    """
    triggered = []

    if weighted_surprise > SURPRISE_THRESHOLD:
        triggered.append("high_surprise")

    # Source novelty — very few claims from this source yet
    if (claim.get("source_total_claims") or 0) < 50:
        triggered.append("source_novelty")

    # Missing prior on a topic that should be tracked (proxy: any topic_tags)
    if prior is None and claim.get("topic_tags"):
        triggered.append("missing_prior_on_tagged_topic")

    return (len(triggered) > 0, triggered)


def check_cooldown(conn, topic: str) -> bool:
    """
    Return True if this topic is within the escalation cooldown window
    (i.e., we should skip escalation to avoid flooding SWARMFISH).
    """
    if not topic:
        return False
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1 FROM escalation_requests
            WHERE topic = %s
              AND request_timestamp >= NOW() - (%s || ' minutes')::interval
            LIMIT 1
        """, (topic, str(ESCALATION_COOLDOWN_MINUTES)))
        return cur.fetchone() is not None


def request_escalation(conn,
                       claim: dict,
                       topic: str,
                       triggered_cues: list,
                       reasoning: str) -> Optional[int]:
    """
    Write an escalation_requests row and POST to SWARMFISH /monitor/run_now.
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
        row = cur.fetchone()
        escalation_id = row['id'] if row else -1

    # POST to SWARMFISH /monitor/run_now — fire-and-forget trigger.
    # Using stdlib urllib to avoid adding a container dependency.
    try:
        req = urllib.request.Request(
            f"{SWARMFISH_URL}/monitor/run_now",
            data=b"{}",
            headers={
                "Content-Type": "application/json",
                "X-Analyst-Token": ANALYST_TOKEN,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            status = resp.status
        log.info(f"[ESCALATE] id={escalation_id} topic={topic!r} "
                 f"cues={triggered_cues} swarmfish_status={status}")
    except Exception as e:
        log.warning(f"[ESCALATE] id={escalation_id} — SWARMFISH trigger failed: {e}")
        # Failure to reach SWARMFISH is NOT a scrutiny error — the escalation
        # is still logged in escalation_requests for later retry.

    return escalation_id


# ---------------------------------------------------------------------------
# Main entry point: orchestrator
# ---------------------------------------------------------------------------

def scrutinize_claim(conn, claim: dict) -> dict:
    """
    Run the full scrutiny pipeline on a single claim.

    claim: dict with fields id, source_id, claim_text, topic_tags,
           source_total_claims, source_confidence

    Returns: dict with {status, surprise_score, raw_surprise, escalated,
                        triggered_cues, verdict_ids}
    """
    claim_id = claim["id"]
    topic_tags = claim.get("topic_tags") or []
    primary_topic = topic_tags[0] if topic_tags else None

    # Component 1: Prior injection
    prior = get_topic_prior(primary_topic) if primary_topic else None

    # Component 2: Surprise scoring
    raw_surprise = compute_raw_surprise(claim["claim_text"], prior)
    source_reliability = float(claim.get("source_confidence") or 0.7)
    prior_authority = prior.authority_weight() if prior else 0.3
    weighted_surprise = compute_weighted_surprise(
        raw_surprise, source_reliability, prior_authority,
    )

    verdict_ids = []

    # Write the surprise score verdict
    reasoning = (
        f"semantic distance from committee framing: {raw_surprise:.2f}; "
        f"reliability-weighted: {weighted_surprise:.2f}"
        if prior else "no committee prior available — neutral score"
    )
    verdict_ids.append(write_verdict(
        conn, claim_id,
        check_name="surprise_score",
        result="warn" if weighted_surprise > SURPRISE_THRESHOLD else "pass",
        numeric_value=weighted_surprise,
        confidence=prior_authority,
        reasoning=reasoning,
        escalated=False,
        metadata={
            "raw_surprise": raw_surprise,
            "source_reliability": source_reliability,
            "prior_authority": prior_authority,
            "topic": primary_topic,
            "has_prior": prior is not None,
            "prior_fresh_mins": (
                prior.freshness.total_seconds() / 60
                if prior and prior.freshness else None
            ),
        },
    ))

    # Update claim row with the score
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
            verdict_ids.append(write_verdict(
                conn, claim_id,
                check_name="escalation",
                result="warn",
                reasoning=f"Escalated to SWARMFISH: {','.join(triggered_cues)}",
                escalated=True,
                metadata={
                    "escalation_id": escalation_id,
                    "triggered_by": triggered_cues,
                    "topic": primary_topic,
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

    log.info(
        f"[SCRUTINY] claim={claim_id} topic={primary_topic!r} "
        f"surprise={weighted_surprise:.2f} status={status} "
        f"cues={','.join(triggered_cues) if triggered_cues else 'none'}"
    )

    return {
        "status": status,
        "surprise_score": weighted_surprise,
        "raw_surprise": raw_surprise,
        "escalated": escalated,
        "triggered_cues": triggered_cues,
        "verdict_ids": verdict_ids,
    }
