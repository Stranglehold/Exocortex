"""
contradict.py — Contradiction detection engine for OSS.

Compares new claims against existing claims from the same source
to detect contradictions, silent retcons, and acknowledged retcons.
Distinguishes these explicitly — Reuters issuing a correction is journalism;
a source silently editing its story is what this system is designed to detect.

Runs after each ingestion pass or on-demand.
"""

import os
import re
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import psycopg2
import psycopg2.extras
import faiss
from openai import OpenAI

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

DB_URL      = os.environ.get("OSS_DB_URL", "postgresql://oss_admin:oss_admin_dev_password@localhost:5433/oss")
LLM_URL     = os.environ.get("OSS_LLM_URL", "http://localhost:1234/v1")
from llm_config import get_llm_model as _get_llm_model
LLM_MODEL   = _get_llm_model()
FAISS_PATH  = os.environ.get("OSS_FAISS_PATH", "/app/data/faiss/claims.index")

# Cosine similarity threshold: above this, two claims are semantically close
# enough to warrant contradiction analysis
SIMILARITY_THRESHOLD = float(os.environ.get("OSS_CONTRADICTION_SIMILARITY", "0.72"))

# ---------------------------------------------------------------------------
# Narrative Stability signal classification
# Spec: specs/NARRATIVE_STABILITY_SPEC_L3.md
# ---------------------------------------------------------------------------

SIGNAL_REALITY_UPDATE    = "reality_update"
SIGNAL_HONEST_CORRECTION = "honest_correction"
SIGNAL_HEALTHY_UPDATE    = "healthy_update"
SIGNAL_SILENT_ERROR      = "silent_error"
SIGNAL_NARRATIVE_REWRITE = "narrative_rewrite"
SIGNAL_EDITORIAL_DRIFT   = "editorial_drift"
SIGNAL_UNCATEGORIZED     = "uncategorized"

SIGNAL_SCORES: dict = {
    SIGNAL_NARRATIVE_REWRITE: 1.0,
    SIGNAL_EDITORIAL_DRIFT:   0.9,
    SIGNAL_SILENT_ERROR:      0.6,
    SIGNAL_UNCATEGORIZED:     0.4,
    SIGNAL_HONEST_CORRECTION: 0.1,
    SIGNAL_HEALTHY_UPDATE:    0.05,
    SIGNAL_REALITY_UPDATE:    0.0,
}

VALID_MODALITIES = {"fact", "speculation", "opinion", "framing", "unknown"}


def apply_certainty_modifier(signal_score: float,
                             certainty_a: str,
                             certainty_b: str) -> float:
    """
    Reduce retcon signal score when one or both retconned claims were already
    hedged. A hedge is a partial disclaimer — retconning a hedge is less
    dishonest than retconning a committed assertion.

    Rules (from HEDGE_PATTERN_SPEC_L3.md):
      both hedged    → 0.5x  (both were already disclaimers)
      one hedged     → 0.75x (partial disclaimer)
      both committed → 1.0x  (full weight, no discount)
      unknown        → treat as committed (conservative, full weight)
    """
    a_hedged = (certainty_a or "unknown").lower() == "hedged"
    b_hedged = (certainty_b or "unknown").lower() == "hedged"
    if a_hedged and b_hedged:
        return signal_score * 0.5
    if a_hedged or b_hedged:
        return signal_score * 0.75
    return signal_score


def classify_retcon_signal(
    modality_a: str,
    modality_b: str,
    volatility: str,
    acknowledged: bool,
) -> tuple:
    """
    Map (modality × volatility × acknowledgment) → (signal_class, signal_score).

    Pure function. No DB, no LLM. Deterministic given the inputs.
    See NARRATIVE_STABILITY_SPEC_L3.md for the full signal table.

    Decision order:
      1. framing on either side → editorial_drift
      2. speculation/opinion on either side:
           acknowledged → healthy_update
           silent       → narrative_rewrite
      3. both fact:
           high volatility          → reality_update (ack irrelevant)
           medium vol + ack         → honest_correction
           medium vol + silent      → silent_error
           low vol + ack            → honest_correction
           low vol + silent         → narrative_rewrite
      4. fallback (unknown modality) → uncategorized
    """
    ma = (modality_a or "unknown").lower()
    mb = (modality_b or "unknown").lower()
    if ma not in VALID_MODALITIES:
        ma = "unknown"
    if mb not in VALID_MODALITIES:
        mb = "unknown"
    vol = (volatility or "medium").lower()
    if vol not in ("high", "medium", "low"):
        vol = "medium"

    # Rule 1: framing is always a signal, ack-independent
    if ma == "framing" or mb == "framing":
        return SIGNAL_EDITORIAL_DRIFT, SIGNAL_SCORES[SIGNAL_EDITORIAL_DRIFT]

    # Rule 2: speculation/opinion — silent is the dishonesty signal
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

    # Rule 4: one or both unknown (and none of the above fired)
    return SIGNAL_UNCATEGORIZED, SIGNAL_SCORES[SIGNAL_UNCATEGORIZED]

# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------

_llm_client: Optional[OpenAI] = None

def get_llm():
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenAI(base_url=LLM_URL, api_key="local")
    return _llm_client


CONTRADICTION_SYSTEM = """You are a fact-checking assistant analyzing pairs of news claims from the same source.

Classify the relationship between claim A and claim B:

- contradiction: The claims assert mutually exclusive facts (e.g., A says suspect had ISIS ties; B says suspect had no ISIS ties).
- retcon_silent: B supersedes A on the same topic but no correction is stated. The story changed without acknowledgment.
- retcon_acknowledged: B explicitly corrects or updates A. The source acknowledged the change.
- elaboration: B adds detail to A without contradiction. Both can be simultaneously true.
- unrelated: The claims do not address the same facts.

Return ONLY a JSON object with exactly these fields:
{
  "relationship": "<one of the five categories>",
  "confidence": <float 0.0-1.0>,
  "source_acknowledged": <true if the source explicitly noted a correction, false otherwise>,
  "reasoning": "<one sentence>"
}"""

# SFA-001 P1.1 fix — thinking-token stripping for reasoning-distilled models.
# The prior implementation used max_tokens=200 and did not strip XML-style
# reasoning blocks. Reasoning models (e.g. qwen3.5-27b-claude-distilled) emit
# <think>...</think> tokens BEFORE any JSON, which exceeded the 200-token
# budget and produced empty/garbage output on every call. Zero contradictions
# were ever stored across the entire deployment. Ported from the working
# pattern in services/swarmfish/src/acp/predictor.py:extract_json.
_THINK_TAG_RE = re.compile(r"<[a-zA-Z_]+>.*?</[a-zA-Z_]+>", re.DOTALL)
_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)

# SFA-001 P3.1 — boundary assertion: rolling counter of "did the classifier
# produce a real result or fall back to 'classification error'?" If the
# fallback rate stays high for many consecutive calls, the classifier is
# silently broken and we should log an error so the operator notices.
_CLASSIFIER_STATS = {
    'total_calls': 0,
    'fallback_returns': 0,
    'warn_threshold': 10,  # only start checking after this many calls
    'fallback_rate_ceiling': 0.5,  # if fallback rate exceeds this, log error
}


def _extract_json_from_llm(raw: str) -> Optional[dict]:
    """Extract a JSON object from an LLM response that may contain reasoning
    tokens, markdown fences, or surrounding prose. Returns None on parse
    failure rather than raising — caller decides whether to retry or skip."""
    if not raw:
        return None

    # Strip reasoning tokens (<think>...</think>, <analysis>...</analysis>, etc.)
    cleaned = _THINK_TAG_RE.sub("", raw).strip()

    # Strip markdown code fences
    cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned).strip()
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    if not cleaned:
        return None

    # Direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Extract JSON block embedded in prose
    m = _JSON_BLOCK_RE.search(cleaned)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            return None
    return None


def _record_classifier_call(is_fallback: bool):
    """SFA-001 P3.1 — track classifier fallback rate so silent degradation
    becomes visible. Logs an error once if the fallback rate exceeds the
    ceiling after the warm-up threshold."""
    _CLASSIFIER_STATS['total_calls'] += 1
    if is_fallback:
        _CLASSIFIER_STATS['fallback_returns'] += 1
    total = _CLASSIFIER_STATS['total_calls']
    if total < _CLASSIFIER_STATS['warn_threshold']:
        return
    rate = _CLASSIFIER_STATS['fallback_returns'] / total
    if rate > _CLASSIFIER_STATS['fallback_rate_ceiling']:
        # Log once per many calls to avoid log spam, using a bucketed check
        if total % 20 == 0:
            log.error(
                f"[HEALTH] Contradiction classifier fallback rate is "
                f"{rate:.0%} over {total} calls "
                f"({_CLASSIFIER_STATS['fallback_returns']} fallbacks). "
                f"Classifier may be silently broken."
            )


def classify_contradiction(claim_a: str, claim_b: str) -> dict:
    """
    Classify the relationship between two claims from the same source.
    Returns dict with relationship, confidence, source_acknowledged, reasoning.
    """
    raw = ""
    try:
        resp = get_llm().chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": CONTRADICTION_SYSTEM},
                {"role": "user", "content": f"Claim A: {claim_a}\n\nClaim B: {claim_b}"}
            ],
            temperature=0.1,
            # SFA-001 P1.1 — raised from 200 to 2048. Reasoning-distilled
            # models need budget for the thinking block AND the JSON output;
            # 200 tokens gets truncated mid-thought and never reaches JSON.
            max_tokens=2048,
        )
        raw = resp.choices[0].message.content or ""
        result = _extract_json_from_llm(raw)
        if result is None:
            # Log with truncated raw content so future failures are diagnosable.
            log.warning(
                f"Contradiction classification returned unparseable output "
                f"(first 200 chars): {raw[:200]!r}"
            )
            _record_classifier_call(is_fallback=True)
            return {'relationship': 'unrelated', 'confidence': 0.0,
                    'source_acknowledged': False, 'reasoning': 'classification parse error'}
        valid_relationships = {'contradiction', 'retcon_silent', 'retcon_acknowledged', 'elaboration', 'unrelated'}
        if result.get('relationship') not in valid_relationships:
            result['relationship'] = 'unrelated'
        result['confidence'] = max(0.0, min(1.0, float(result.get('confidence', 0.5))))
        result['source_acknowledged'] = bool(result.get('source_acknowledged', False))
        _record_classifier_call(is_fallback=False)
        return result
    except Exception as e:
        log.warning(f"Contradiction classification failed: {e} (raw: {raw[:200]!r})")
        _record_classifier_call(is_fallback=True)
        return {'relationship': 'unrelated', 'confidence': 0.0,
                'source_acknowledged': False, 'reasoning': 'classification error'}


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_conn():
    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def get_recent_claims_for_source(source_id: int, since_id: int, limit: int = 200) -> list[dict]:
    """Claims from a source older than since_id, for comparison."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, claim_text, faiss_id, topic_tags, article_url, modality, certainty
                FROM claims
                WHERE source_id = %s AND id < %s AND faiss_id IS NOT NULL
                ORDER BY id DESC
                LIMIT %s
            """, (source_id, since_id, limit))
            return cur.fetchall()


def contradiction_already_exists(conn, claim_a_id: int, claim_b_id: int) -> bool:
    """Avoid duplicate contradiction entries for the same pair."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1 FROM contradictions
            WHERE (claim_a_id = %s AND claim_b_id = %s)
               OR (claim_a_id = %s AND claim_b_id = %s)
            LIMIT 1
        """, (claim_a_id, claim_b_id, claim_b_id, claim_a_id))
        return cur.fetchone() is not None


def insert_contradiction(conn, claim_a_id: int, claim_b_id: int,
                         relationship: str, confidence: float,
                         source_acknowledged: bool, technique_class: Optional[str],
                         reasoning: str,
                         modality_a: Optional[str] = None,
                         modality_b: Optional[str] = None,
                         volatility: Optional[str] = None,
                         signal_class: Optional[str] = None,
                         signal_score: Optional[float] = None,
                         raw_signal_score: Optional[float] = None):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO contradictions
                (claim_a_id, claim_b_id, relationship, confidence,
                 source_acknowledged, technique_class, notes,
                 modality_a, modality_b, volatility,
                 signal_class, signal_score, raw_signal_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (claim_a_id, claim_b_id, relationship, confidence,
              source_acknowledged, technique_class, reasoning,
              modality_a, modality_b, volatility,
              signal_class, signal_score, raw_signal_score))


def update_source_retcon_stats(conn, source_id: int, relationship: str):
    """Update source confidence tracking counters."""
    if relationship == 'retcon_silent':
        col = 'silent_retcon_count'
    elif relationship == 'retcon_acknowledged':
        col = 'acknowledged_retcon_count'
    else:
        return
    with conn.cursor() as cur:
        cur.execute(f"UPDATE sources SET {col} = {col} + 1 WHERE id = %s", (source_id,))


def compute_paraphrase_rate(conn, source_id: int, window_days: int = 30) -> float:
    """
    Return the source's paraphrase rate over the rolling window:
      paraphrased_count / (quoted_count + paraphrased_count)

    Only claims with attribution IN ('named', 'vague') count — unattributed
    claims (attribution='absent' or 'unknown') don't carry the distinction.

    Returns 0.0 if the source has fewer than 5 attributed claims in the window
    (too little signal to compute a rate).

    Spec: HEDGE_PATTERN_SPEC_L3.md — Module 5
    """
    try:
        window_days = max(1, int(window_days))
    except Exception:
        window_days = 30
    interval_literal = f"{window_days} days"

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


def update_source_confidence(conn, source_id: int, window_days: int = 14):
    """
    Recalculate source confidence based on the NARRATIVE STABILITY signal
    weight of recent retcons.

    Spec: NARRATIVE_STABILITY_SPEC_L3.md — replaces the previous one-dimensional
    "silent retcons bad / acknowledged retcons good" scoring.

    Each contradiction now carries a signal_score in [0, 1]:
      - reality_update      0.00   (reality moved, source updated — working as intended)
      - healthy_update      0.05   (speculation updated, openly acknowledged)
      - honest_correction   0.10   (fact corrected, openly acknowledged)
      - uncategorized       0.40   (unknown modality — fallback)
      - silent_error        0.60   (stable fact silently revised)
      - editorial_drift     0.90   (loaded framing shift)
      - narrative_rewrite   1.00   (speculation or stable fact silently rewritten)

    A source with only reality_updates carries zero narrative load and
    recovers over time. A source racking up narrative_rewrites pays
    proportionally. This is the fix for the old logic that penalized
    functioning news outlets for updating factual claims as events moved.
    """
    # Interval literal cannot be parameterized directly; clamp to a safe int.
    try:
        window_days = max(1, int(window_days))
    except Exception:
        window_days = 14
    interval_literal = f"{window_days} days"

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                s.source_type,
                s.total_claims,
                COALESCE(SUM(c.signal_score), 0.0) AS total_signal,
                COUNT(c.id)                        AS retcon_count
            FROM sources s
            LEFT JOIN claims cl ON cl.source_id = s.id
                AND cl.extracted_at >= NOW() - (%s::interval)
            LEFT JOIN contradictions c
                ON (c.claim_a_id = cl.id OR c.claim_b_id = cl.id)
                AND c.signal_score IS NOT NULL
            WHERE s.id = %s
            GROUP BY s.source_type, s.total_claims
        """, (interval_literal, source_id))
        row = cur.fetchone()
        if not row:
            return

        total          = max(row['total_claims'], 1)
        total_signal   = float(row['total_signal'] or 0.0)
        narrative_load = total_signal / total      # [0..1+] in principle

        # Baseline confidence per source_type — the fixed anchor we recompute
        # against each pass. Without this, repeated calls to this function
        # compound adjustments into current and drift confidence to the floor.
        # The spec's intent is rolling-window-derived, not accumulative.
        SOURCE_TYPE_BASELINE = {
            'wire':     0.9,
            'official': 0.85,
            'outlet':   0.75,
            'social':   0.6,
        }
        baseline = SOURCE_TYPE_BASELINE.get(row['source_type'], 0.7)

        # Downweight sources carrying narrative instability. Recovery term
        # pulls clean sources back toward the baseline over time.
        clamped_load = min(narrative_load, 1.0)
        narrative_adjustment = -narrative_load * 0.3 + (1.0 - clamped_load) * 0.02

        # Hedge pattern spec: paraphrase rate penalty (up to 10% max).
        # Deliberately smaller than the retcon penalty (30% max) because
        # paraphrasing is a legitimate editorial choice carrying risk, not
        # direct dishonesty. Sources that consistently paraphrase rather
        # than quote directly take a small proportional credibility hit.
        paraphrase_rate    = compute_paraphrase_rate(conn, source_id, window_days=30)
        paraphrase_penalty = 0.10 * paraphrase_rate

        adjustment     = narrative_adjustment - paraphrase_penalty
        # CRITICAL: compute from the stable baseline, not from the previous
        # confidence_score. Previous behavior compounded adjustments across
        # calls and drifted confidence to the floor after many scans.
        new_confidence = max(0.1, min(0.99, baseline + adjustment))

        cur.execute(
            "UPDATE sources SET confidence_score = %s WHERE id = %s",
            (new_confidence, source_id)
        )


# ---------------------------------------------------------------------------
# FAISS similarity search
# ---------------------------------------------------------------------------

_faiss_index = None

def get_faiss():
    global _faiss_index
    if _faiss_index is not None:
        return _faiss_index
    if os.path.exists(FAISS_PATH):
        _faiss_index = faiss.read_index(FAISS_PATH)
    return _faiss_index


def get_embedding_for_faiss_id(faiss_id: int) -> Optional[np.ndarray]:
    """Reconstruct embedding vector from FAISS index by internal ID."""
    index = get_faiss()
    if index is None or faiss_id >= index.ntotal:
        return None
    vec = np.zeros((1, index.d), dtype=np.float32)
    index.reconstruct(faiss_id, vec[0])
    return vec[0]


def find_similar_claims(faiss_id: int, candidate_faiss_ids: list[int],
                        top_k: int = 5) -> list[tuple[int, float]]:
    """
    Find which candidate claims are most similar to the query claim.
    Returns list of (faiss_id, cosine_similarity) sorted by similarity desc.
    """
    query_vec = get_embedding_for_faiss_id(faiss_id)
    if query_vec is None:
        return []

    results = []
    for cand_id in candidate_faiss_ids:
        cand_vec = get_embedding_for_faiss_id(cand_id)
        if cand_vec is None:
            continue
        sim = float(np.dot(query_vec, cand_vec))
        if sim >= SIMILARITY_THRESHOLD:
            results.append((cand_id, sim))

    return sorted(results, key=lambda x: x[1], reverse=True)[:top_k]


# ---------------------------------------------------------------------------
# Main contradiction scan
# ---------------------------------------------------------------------------

def scan_new_claims(since_claim_id: int = 0, source_id: Optional[int] = None,
                    max_claims: Optional[int] = None):
    """
    Scan claims newer than since_claim_id for contradictions with older claims
    from the same source. If source_id is given, only scan that source.

    max_claims caps the batch size so the scheduler's forward-scan cannot
    blow out its budget on a large backlog. The caller is responsible for
    advancing its cursor to the highest id actually processed.

    Returns (flagged_count, last_processed_id). If no claims were scanned,
    last_processed_id equals since_claim_id.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT id, source_id, claim_text, faiss_id, topic_tags, modality, certainty
                FROM claims
                WHERE id > %s AND faiss_id IS NOT NULL
            """
            params: list = [since_claim_id]
            if source_id is not None:
                query += " AND source_id = %s"
                params.append(source_id)
            query += " ORDER BY id ASC"
            if max_claims is not None and max_claims > 0:
                query += " LIMIT %s"
                params.append(max_claims)
            cur.execute(query, params)
            new_claims = cur.fetchall()

    log.info(f"[contradict] Scanning {len(new_claims)} new claims for contradictions")
    flagged = 0
    last_processed_id = since_claim_id

    for claim in new_claims:
        last_processed_id = claim['id']
        older = get_recent_claims_for_source(claim['source_id'], claim['id'])
        if not older:
            continue

        # Build faiss_id → claim mapping for older claims
        faiss_id_to_claim = {c['faiss_id']: c for c in older if c['faiss_id'] is not None}
        candidate_faiss_ids = list(faiss_id_to_claim.keys())

        # Find semantically similar older claims from same source
        similar = find_similar_claims(claim['faiss_id'], candidate_faiss_ids)

        conn = get_conn()
        try:
            for old_faiss_id, similarity in similar:
                old_claim = faiss_id_to_claim[old_faiss_id]
                with conn:
                    if contradiction_already_exists(conn, claim['id'], old_claim['id']):
                        continue

                result = classify_contradiction(old_claim['claim_text'], claim['claim_text'])
                relationship = result['relationship']

                # Only persist meaningful relationships
                if relationship in ('contradiction', 'retcon_silent', 'retcon_acknowledged'):
                    # --- Narrative stability signal classification ---
                    try:
                        from volatility import pair_volatility
                    except ImportError:
                        # Defensive — should never happen in the running container
                        pair_volatility = lambda a, b: "medium"

                    vol = pair_volatility(
                        old_claim.get("topic_tags"),
                        claim.get("topic_tags"),
                    )
                    modality_a = old_claim.get("modality") or "unknown"
                    modality_b = claim.get("modality") or "unknown"
                    raw_signal_class, raw_signal_score = classify_retcon_signal(
                        modality_a=modality_a,
                        modality_b=modality_b,
                        volatility=vol,
                        acknowledged=bool(result.get('source_acknowledged', False)),
                    )

                    # Apply certainty modifier (hedge pattern spec) — reduces
                    # the signal score when one or both claims were already
                    # hedged, preserving the diagnostic class while scaling
                    # the source confidence impact.
                    certainty_a = old_claim.get("certainty") or "unknown"
                    certainty_b = claim.get("certainty") or "unknown"
                    modified_signal_score = apply_certainty_modifier(
                        raw_signal_score, certainty_a, certainty_b,
                    )
                    signal_class = raw_signal_class  # class unchanged; only score moves

                    with conn:
                        insert_contradiction(
                            conn,
                            old_claim['id'], claim['id'],
                            relationship, result['confidence'],
                            result['source_acknowledged'],
                            claim.get('technique_class'),
                            result.get('reasoning', ''),
                            modality_a=modality_a,
                            modality_b=modality_b,
                            volatility=vol,
                            signal_class=signal_class,
                            signal_score=modified_signal_score,
                            raw_signal_score=raw_signal_score,
                        )
                        update_source_retcon_stats(conn, claim['source_id'], relationship)
                    flagged += 1
                    mod_tag = ""
                    if modified_signal_score != raw_signal_score:
                        mod_tag = f" (hedge-modified from {raw_signal_score:.2f})"
                    log.info(f"  [{relationship}/{signal_class}] source={claim['source_id']} "
                             f"claims={old_claim['id']}→{claim['id']} "
                             f"conf={result['confidence']:.2f} "
                             f"signal={modified_signal_score:.2f}{mod_tag}")
        finally:
            conn.close()

        # Refresh source confidence after processing each source's claims
        conn2 = get_conn()
        try:
            with conn2:
                update_source_confidence(conn2, claim['source_id'])
        finally:
            conn2.close()

    log.info(f"[contradict] Scan complete: {flagged} contradictions/retcons flagged "
             f"(last_id={last_processed_id})")
    return flagged, last_processed_id
