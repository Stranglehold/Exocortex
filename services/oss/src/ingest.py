"""
ingest.py — RSS ingestion pipeline for OSS.

Fetches RSS feeds, extracts claims via LLM, embeds them, deduplicates
against FAISS index, and persists to PostgreSQL.

Runs on a schedule (OSS_INGEST_INTERVAL_MINUTES). Also callable directly
for retroactive ingestion of archived articles.
"""

import os
import json
import re
import time
import hashlib
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Optional

import feedparser
import psycopg2
import psycopg2.extras
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format='[INGEST] %(message)s', force=True)
log = logging.getLogger(__name__)


def _strip_thinking(raw: str) -> str:
    """Strip <think>...</think> blocks produced by reasoning models before JSON parse."""
    return re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DB_URL        = os.environ.get("OSS_DB_URL", "postgresql://oss_admin:oss_admin_dev_password@localhost:5433/oss")
LLM_URL       = os.environ.get("OSS_LLM_URL", "http://localhost:1234/v1")
from llm_config import get_llm_model as _get_llm_model
LLM_MODEL     = _get_llm_model()
# Separate LLM config for ingestion tasks — point at a lighter/faster model.
# Defaults to same as main LLM_URL/MODEL if not set.
INGEST_LLM_URL   = os.environ.get("OSS_LLM_URL_INGEST",   LLM_URL)
INGEST_LLM_MODEL = os.environ.get("OSS_LLM_MODEL_INGEST", LLM_MODEL)
INGEST_WORKERS   = int(os.environ.get("OSS_INGEST_WORKERS", "3"))
EMB_MODEL     = os.environ.get("OSS_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
FAISS_PATH    = os.environ.get("OSS_FAISS_PATH", "/app/data/faiss/claims.index")
DEDUP_THRESHOLD = float(os.environ.get("OSS_DEDUP_THRESHOLD", "0.95"))

# ---------------------------------------------------------------------------
# Swarmfish coordination guard
# ---------------------------------------------------------------------------
# Before starting an ingestion pass, poll swarmfish's monitor status. If a
# swarmfish prediction cycle is in flight, defer the ingestion pass — both
# processes hit LM Studio and a 27B↔4B JIT swap during a swarmfish predict
# cancels in-flight 27B calls. This guard eliminates that contention without
# requiring LM Studio to keep both models pinned in VRAM.
SWARMFISH_BASE_URL    = os.environ.get("SWARMFISH_BASE_URL", "http://host.docker.internal:7732")
SWARMFISH_AUTH_TOKEN  = os.environ.get("SWARMFISH_ANALYST_TOKEN", "dev_analyst_token")
COORD_POLL_SECONDS    = int(os.environ.get("OSS_COORD_POLL_SECONDS", "10"))
COORD_MAX_WAIT_SECONDS = int(os.environ.get("OSS_COORD_MAX_WAIT_SECONDS", "60"))

# ---------------------------------------------------------------------------
# LLM clients
# ---------------------------------------------------------------------------

_llm_client: Optional[OpenAI] = None
_ingest_llm_client: Optional[OpenAI] = None

def get_llm():
    """Main LLM client — used for analysis endpoints (hypotheses, drift, etc.)."""
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenAI(base_url=LLM_URL, api_key="local")
    return _llm_client

def get_ingest_llm():
    """Ingest LLM client — points at a lighter/faster model for extraction tasks."""
    global _ingest_llm_client
    if _ingest_llm_client is None:
        _ingest_llm_client = OpenAI(base_url=INGEST_LLM_URL, api_key="local")
    return _ingest_llm_client


# ---------------------------------------------------------------------------
# Embedding model
# ---------------------------------------------------------------------------

_embedder: Optional[SentenceTransformer] = None

def get_embedder():
    global _embedder
    if _embedder is None:
        log.info(f"Loading embedding model: {EMB_MODEL}")
        _embedder = SentenceTransformer(EMB_MODEL)
    return _embedder


def embed(texts: list[str]) -> np.ndarray:
    """Return (N, 384) float32 embeddings."""
    return get_embedder().encode(texts, normalize_embeddings=True, show_progress_bar=False)


# ---------------------------------------------------------------------------
# FAISS index
# ---------------------------------------------------------------------------

_faiss_index: Optional[faiss.IndexFlatIP] = None
_faiss_lock = threading.Lock()

def get_faiss():
    global _faiss_index
    if _faiss_index is not None:
        return _faiss_index
    dim = 384
    if os.path.exists(FAISS_PATH):
        log.info(f"Loading FAISS index from {FAISS_PATH}")
        _faiss_index = faiss.read_index(FAISS_PATH)
    else:
        log.info("Creating new FAISS index")
        os.makedirs(os.path.dirname(FAISS_PATH), exist_ok=True)
        _faiss_index = faiss.IndexFlatIP(dim)
    return _faiss_index


def save_faiss():
    if _faiss_index is not None:
        faiss.write_index(_faiss_index, FAISS_PATH)


def is_duplicate(vec: np.ndarray) -> bool:
    """True if a near-identical claim already exists in the index."""
    with _faiss_lock:
        index = get_faiss()
        if index.ntotal == 0:
            return False
        vec = vec.reshape(1, -1).astype(np.float32)
        D, _ = index.search(vec, 1)
        return float(D[0][0]) >= DEDUP_THRESHOLD


def add_to_faiss(vec: np.ndarray) -> int:
    """Add embedding to index; return the new FAISS id (0-indexed)."""
    with _faiss_lock:
        index = get_faiss()
        faiss_id = index.ntotal
        index.add(vec.reshape(1, -1).astype(np.float32))
        return faiss_id


# ---------------------------------------------------------------------------
# Combined article processing — single LLM call per article.
# Replaces the former extract_claims + classify_technique + assign_topics
# triple-call pattern (1 + 2N calls per article) with 1 call per article.
# ---------------------------------------------------------------------------

PROCESS_SYSTEM = """You are an intelligence analyst. From a news article, extract claims and classify each one.

For each claim return a JSON object with seven fields:
- "claim": the claim in third-person declarative form
- "technique": one of [presuasion, fracture, emergent, direct, none]
- "topics": array of matching tags from the provided list ([] if none match)
- "modality": one of [fact, speculation, opinion, framing] — see definitions below
- "certainty": one of [committed, hedged] — see definitions below
- "attribution": one of [named, vague, absent] — see definitions below
- "quoted_directly": one of [true, false, n_a] — see definitions below

Modality definitions (critical — choose the dominant mode):
- fact: states what happened, is happening, or has happened. A verifiable or
  observable assertion about the world.
  Examples: "Six merchant ships turned around at the Strait of Hormuz."
            "The US Navy deployed three carriers to the Persian Gulf."
- speculation: predicts, forecasts, or describes a causal chain that has
  not yet resolved. Forward-looking or conditional.
  Examples: "The blockade is likely to fail within 72 hours."
            "Analysts expect a ceasefire by Friday."
- opinion: expresses a value judgment (good/bad, right/wrong, success/failure
  as evaluation rather than observation).
  Examples: "This deployment is a strategic catastrophe."
            "The administration's response has been weak."
- framing: the underlying fact is stated with loaded or contested vocabulary
  that is itself a persuasion choice.
  Examples: "freedom fighters" vs "insurgents"
            "collateral damage" vs "civilian casualties"

When a claim mixes modes, pick the one that carries the most semantic weight.
When in doubt between fact and speculation, pick "fact" only if the claim is
about something already confirmed to have happened.

Certainty definitions — the commitment level of the proposition AS STATED BY ITS SPEAKER:
- committed: declarative assertion with no hedges ("Six ships turned around.")
- hedged: softened by modals (may, could, might), epistemic adverbs (possibly,
  allegedly, reportedly), or hedge verbs (suggests, indicates, appears to,
  is said to, is expected to). "Sources suggest X may happen" is hedged.

Attribution definitions — how the outlet sourced the claim:
- named: specific, identifiable source ("Secretary Austin said...",
  "According to the Iranian Foreign Ministry...", "Reuters' own reporting...")
- vague: non-specific source clause ("sources say", "officials indicate",
  "people familiar with the matter", "a senior administration official",
  "on condition of anonymity", "analysts expect")
- absent: the outlet makes the claim in its own voice with no attribution
  clause at all

Quoted_directly definitions — whether the proposition appeared inside
quotation marks in the ORIGINAL ARTICLE, attributed to a speaker, with
the speaker's exact words preserved:
- true: the proposition was rendered as direct quotation in the source
  article (e.g. `Biden said: "The blockade may collapse"`)
- false: the proposition was rendered as paraphrased attribution
  (the outlet's own words replacing the speaker's original words)
- n_a: the claim has no speaker attribution at all; outlet is speaking
  in its own voice (e.g. "Six ships turned around." with no "X said")

CRITICAL for quoted_directly: you are the ONLY stage in the pipeline that can
see whether the original article used quotation marks. Downstream regex cannot
see this because the paraphrasing step destroys the quotation boundaries. When
the original article text contains "X said: '...'" or similar direct quotation
structure, set quoted_directly="true". When the original article paraphrases
(e.g. "X said the blockade could fall within three days" — no quotes, outlet's
words), set quoted_directly="false". When there's no attribution at all, set
quoted_directly="n_a".

Technique definitions:
- presuasion: primes emotional or identity context before the analytical question
- fracture: amplifies an existing social division; goal is division not persuasion
- emergent: part of a coordinated narrative appearing simultaneously across outlets
- direct: factual assertion with no apparent framing manipulation
- none: no technique evident

TOPIC ASSIGNMENT RULES (CRITICAL — read carefully):
- Each topic has a definition. Read the definition before assigning the tag.
- Only assign a topic tag if the claim DIRECTLY engages with the topic's subject matter.
- A claim mentioning a country, person, or event in passing is NOT sufficient for that topic — the claim must be ABOUT the topic.
- Example: A claim about Australian fuel prices that mentions "Iran war" as background context does NOT belong in the iran-hormuz topic.
- Example: A claim about US military strikes on drug boats in the Pacific does NOT belong in the iran-hormuz topic, even though it mentions US military activity.
- When in doubt, assign no topic. Empty topics array is preferable to a wrong assignment.

Rules:
- Return ONLY a JSON array of objects. No preamble, no explanation, no markdown fences.
- Max 8 claims per article. Prefer the most information-dense ones.
- Extract speculation, opinion, and framing claims when they carry analytical weight. These are valuable — the system tracks narrative stability by watching how speculation and opinion evolve over time.
- Only use topic tags from the provided list exactly as given.
- If no extractable claims exist, return []."""


def _parse_json_array(raw: str) -> list:
    """Parse a JSON array from LLM output, handling code fences and offset starts."""
    raw = _strip_thinking(raw).strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    if not raw.startswith("["):
        start, end = raw.find("["), raw.rfind("]")
        if start != -1 and end > start:
            raw = raw[start:end + 1]
    return json.loads(raw)


def process_article(article_text: str, article_title: str,
                    available_topics: list) -> list[dict]:
    """
    Single LLM call per article. Returns list of dicts:
      [{"claim": str, "technique": str, "topics": [str, ...]}, ...]
    Raises IngestionCancelled if stop is requested before the call.

    `available_topics` accepts either:
      - list[str]   — bare tag names (legacy callers)
      - list[dict]  — {tag, display_name, description} (preferred — carries
                      semantic guidance to the LLM so it stops generalizing
                      "iran-hormuz" to mean "anything Iran-adjacent")
    """
    _check_stop()
    valid_techniques = {'presuasion', 'fracture', 'emergent', 'direct', 'none'}

    # Normalize topic input — accept legacy list[str] OR list[dict]
    if available_topics and isinstance(available_topics[0], dict):
        topic_dicts = available_topics
        valid_tags = {t['tag'] for t in topic_dicts}
    else:
        topic_dicts = [{'tag': t, 'display_name': t, 'description': None}
                       for t in (available_topics or [])]
        valid_tags = set(available_topics or [])

    tag_list = ", ".join(t['tag'] for t in topic_dicts) if topic_dicts else "(none)"
    if topic_dicts:
        topic_block = "\n".join(
            f"  - {t['tag']}: {t.get('description') or t.get('display_name') or t['tag']}"
            for t in topic_dicts
        )
        topic_section = f"Topic definitions (assign ONLY if the claim DIRECTLY engages with the subject):\n{topic_block}\n\n"
    else:
        topic_section = ""

    try:
        resp = get_ingest_llm().chat.completions.create(
            model=INGEST_LLM_MODEL,
            messages=[
                {"role": "system", "content": PROCESS_SYSTEM},
                {"role": "user", "content": (
                    f"{topic_section}"
                    f"Topics available: [{tag_list}]\n\n"
                    f"Title: {article_title}\n\n"
                    f"Text: {article_text[:2000]}"
                )},
            ],
            temperature=0.1,
            max_tokens=2048,
        )
        raw = resp.choices[0].message.content.strip()
        items = _parse_json_array(raw)
        if not isinstance(items, list):
            return []
        valid_modalities       = {'fact', 'speculation', 'opinion', 'framing'}
        valid_certainty        = {'committed', 'hedged', 'unknown'}
        valid_attribution      = {'named', 'vague', 'absent', 'unknown'}
        valid_quoted_directly  = {'true', 'false', 'n_a', 'unknown'}
        results = []
        for item in items:
            if not isinstance(item, dict):
                continue
            claim = str(item.get("claim", "")).strip()
            if not claim:
                continue
            technique = str(item.get("technique", "none")).lower()
            if technique not in valid_techniques:
                technique = "none"
            topics = [t for t in item.get("topics", []) if t in valid_tags]

            modality = str(item.get("modality", "unknown")).strip().lower()
            if modality not in valid_modalities:
                modality = "unknown"

            certainty = str(item.get("certainty", "unknown")).strip().lower()
            if certainty not in valid_certainty:
                certainty = "unknown"

            attribution = str(item.get("attribution", "unknown")).strip().lower()
            if attribution not in valid_attribution:
                attribution = "unknown"

            qd_raw = str(item.get("quoted_directly", "unknown")).strip().lower()
            # Accept 'n/a' or 'na' as input, normalize to 'n_a' for check constraint
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
        return results
    except IngestionCancelled:
        raise
    except Exception as e:
        log.warning(f"Article processing failed: {e}")
        return []


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_conn():
    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def get_all_sources() -> list[dict]:
    """Return RSS-backed sources only. Excludes:
      - source_type='social' (handled by social_ingest.py Playwright path)
      - url starting with 'manual://' (analyst dictation entry point, no feed)
    Feedparser cannot parse these URL schemes and will record spurious errors."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM sources "
                "WHERE source_type <> 'social' "
                "  AND url NOT LIKE 'manual://%' "
                "ORDER BY id"
            )
            return cur.fetchall()


def get_active_topics() -> list[dict]:
    """Return list of {tag, display_name, description} for all active topics.
    Descriptions feed into the ingest LLM prompt so it can distinguish narrow
    topics ('iran-hormuz') from broad ones ('iran') with semantic precision."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT tag, display_name, description FROM topics WHERE active = TRUE"
            )
            return [dict(row) for row in cur.fetchall()]


def get_topic_scrape_weights() -> dict[str, float]:
    """Return {tag: scrape_weight} for all active topics."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT tag, scrape_weight FROM topics WHERE active = TRUE")
            return {row['tag']: float(row['scrape_weight']) for row in cur.fetchall()}


def insert_claim(conn, source_id: int, raw_text: str, claim_text: str,
                 article_url: str, article_title: str, topic_tags: list,
                 technique_class: str, published_at: Optional[datetime],
                 faiss_id: int, modality: str = "unknown",
                 certainty: str = "unknown",
                 attribution: str = "unknown",
                 quoted_directly: str = "unknown") -> int:
    # Regex cross-check. Only POSITIVE detections (pattern actively fired)
    # override the LLM. When regex falls through to its default (no pattern
    # matched), trust the LLM's contextual judgment. This respects the spec's
    # framing of regex as authoritative for LEXICAL patterns while allowing
    # the LLM to catch non-lexical attribution (e.g., implicit government
    # sourcing of policy claims that have no "X said" marker).
    # quoted_directly is LLM-only — regex cannot see quotation boundaries.
    try:
        from hedge_patterns import (
            certainty_positive_detection,
            attribution_positive_detection,
        )
        regex_cert_hit = certainty_positive_detection(claim_text)  # 'hedged' or None
        regex_attr_hit = attribution_positive_detection(claim_text)  # 'vague' | 'named' | None
    except Exception as e:
        log.warning(f"[HEDGE] regex classification failed: {e}")
        regex_cert_hit = None
        regex_attr_hit = None

    # Certainty: regex hit of 'hedged' overrides LLM
    if regex_cert_hit == "hedged":
        if certainty not in ("hedged", "unknown"):
            log.info(f"[HEDGE-DISAGREE] certainty: llm={certainty} regex=hedged "
                     f"claim={claim_text[:60]!r}")
        certainty = "hedged"
    elif certainty == "unknown":
        certainty = "committed"  # default when LLM has nothing and regex has nothing

    # Attribution: regex positive hit (vague or named) overrides LLM
    if regex_attr_hit is not None:
        if attribution != "unknown" and attribution != regex_attr_hit:
            log.info(f"[HEDGE-DISAGREE] attribution: llm={attribution} regex={regex_attr_hit} "
                     f"claim={claim_text[:60]!r}")
        attribution = regex_attr_hit
    elif attribution == "unknown":
        attribution = "absent"  # default only when both LLM and regex have no opinion

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


def update_topic_last_active(conn, tags: list[str]):
    if not tags:
        return
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE topics
            SET last_active = NOW(),
                claim_count = claim_count + 1,
                total_staged_count = total_staged_count + 1
            WHERE tag = ANY(%s)
        """, (tags,))


# ---------------------------------------------------------------------------
# Auto-promotion: advance staged claims by source tier
# ---------------------------------------------------------------------------

# Tier rules: require_topics controls whether topic_tags must be non-empty.
# conf_factor scales source.confidence_score to the promotion confidence.
#
# SFA-001 P2.2 (2026-04-14) — wire and official sources previously had
# require_topics: False, which meant Reuters and AP claims about North
# Korean missile tests, sports, weather, etc. all auto-promoted to the
# active corpus even when the topic classifier returned no tags. The
# audit showed Reuters and AP at 100% promotion rate (139/139, 131/131)
# — all untagged claims flowing through. Flipped both to require_topics:
# True to force wire sources through the same topic-tagging gate as
# outlets. Their conf_factor stays at 1.0 because wire quality is still
# higher than outlet quality; only the topic-relevance gate changes.
_AUTO_PROMOTE_TIERS = {
    'wire':        {'require_topics': True,  'conf_factor': 1.0},
    'official':    {'require_topics': True,  'conf_factor': 1.0},
    'outlet':      {'require_topics': True,  'conf_factor': 0.9},
    'independent': {'require_topics': True,  'conf_factor': 0.75},
    'social':      {'require_topics': True,  'conf_factor': 0.75},
}


def auto_promote_staged(conn) -> int:
    """
    Auto-promote STAGED claims using source tier rules.

    Tier 1 (wire/official): promote unconditionally at source confidence.
    Tier 2 (outlet): promote only if claim has topic_tags.
    Tier 3 (independent/social): promote only if claim has topic_tags,
        at reduced confidence.

    Returns count of claims promoted.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT c.id, c.topic_tags, s.source_type, s.confidence_score
            FROM claims c
            JOIN sources s ON s.id = c.source_id
            WHERE c.trust_level IN ('STAGED', 'RETURNED_TO_STAGED')
              AND c.extracted_at >= NOW() - INTERVAL '7 days'
            """
        )
        staged = cur.fetchall()

    promoted = 0
    for claim in staged:
        rule = _AUTO_PROMOTE_TIERS.get(claim['source_type'])
        if not rule:
            continue
        if rule['require_topics'] and not claim['topic_tags']:
            continue
        conf = round(float(claim['confidence_score']) * rule['conf_factor'], 3)
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE claims SET trust_level = 'PROMOTED', staging_confidence = %s WHERE id = %s",
                (conf, claim['id']),
            )
        promoted += 1

    if promoted:
        conn.commit()
        log.info(f"[AUTO-PROMOTE] Promoted {promoted} claims")
    return promoted


# ---------------------------------------------------------------------------
# Prediction confirmation: match new promoted claims to active hypotheses
# ---------------------------------------------------------------------------

def check_hypothesis_predictions(conn) -> int:
    """
    For each ACTIVE hypothesis with predictions, check whether promoted claims
    since last_prediction_check match any prediction text semantically.

    Uses a per-hypothesis cursor (last_prediction_check) so each claim is
    evaluated exactly once per prediction — no double-counting across passes,
    no missed claims from gaps longer than 2 hours.

    Threshold: cosine similarity >= 0.70 on sentence embeddings.
    Returns total confirmation events fired.
    """
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, predictions_generated, created_at,
                       predictions_confirmed, last_prediction_check
                FROM hypothesis_registry
                WHERE status = 'ACTIVE'
                  AND predictions_generated IS NOT NULL
                  AND jsonb_array_length(predictions_generated) > 0
                """
            )
            active_hyps = cur.fetchall()

        if not active_hyps:
            return 0

        total_confirmed = 0
        now = datetime.now(timezone.utc)

        for hyp in active_hyps:
            # Use last_prediction_check as cursor; fall back to created_at for
            # first pass so we don't re-check claims from before the hypothesis.
            since = hyp['last_prediction_check'] or hyp['created_at']

            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, claim_text
                    FROM claims
                    WHERE trust_level = 'PROMOTED'
                      AND extracted_at > %s
                    ORDER BY extracted_at ASC
                    LIMIT 200
                    """,
                    (since,),
                )
                new_claims = cur.fetchall()

            if not new_claims:
                # Advance cursor even with no new claims so the timestamp stays fresh
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE hypothesis_registry SET last_prediction_check = %s WHERE id = %s",
                        (now, hyp['id']),
                    )
                conn.commit()
                continue

            claim_texts = [c['claim_text'] for c in new_claims]
            claim_vecs = embed(claim_texts)

            preds = list(hyp['predictions_generated'] or [])
            for pidx, pred in enumerate(preds):
                pred_val = pred.get('prediction', '')
                if isinstance(pred_val, dict):
                    pred_text = pred_val.get('condition', '')
                else:
                    pred_text = str(pred_val) if pred_val else ''
                if not pred_text:
                    continue
                pred_vec = embed([pred_text])[0]
                sims = claim_vecs.dot(pred_vec)
                if float(sims.max()) >= 0.70:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE hypothesis_registry
                            SET predictions_confirmed = predictions_confirmed + 1
                            WHERE id = %s
                            """,
                            (hyp['id'],),
                        )
                    conn.commit()
                    total_confirmed += 1
                    log.info(
                        f"[HYPO-CONFIRM] Hypothesis {hyp['id']} prediction {pidx} "
                        f"matched (sim={float(sims.max()):.3f})"
                    )

            # Advance cursor to now so next pass only sees newer claims
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE hypothesis_registry SET last_prediction_check = %s WHERE id = %s",
                    (now, hyp['id']),
                )
            conn.commit()

        return total_confirmed

    except Exception as e:
        log.warning(f"[HYPO-CONFIRM] check_hypothesis_predictions failed: {e}")
        return 0


# ---------------------------------------------------------------------------
# RSS fetch
# ---------------------------------------------------------------------------

def parse_published(entry) -> Optional[datetime]:
    """Parse feedparser published_parsed into a UTC datetime."""
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    except Exception:
        pass
    return None


def _record_source_fetch(source_id: int, ok: bool, entries: int, error: str = None):
    """SFA-001 P2.3 — record per-source fetch success/failure so dead sources
    become visible in the panel instead of silently producing zero claims.
    Updates sources.last_successful_fetch_at on success and
    sources.last_fetch_error on failure. Both live in their own short-lived
    connection so a DB hiccup here doesn't affect the main ingestion path."""
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                if ok:
                    cur.execute(
                        "UPDATE sources SET last_successful_fetch_at = NOW(), last_fetch_error = NULL WHERE id = %s",
                        (source_id,)
                    )
                else:
                    cur.execute(
                        "UPDATE sources SET last_fetch_error = %s WHERE id = %s",
                        ((error or 'unknown')[:500], source_id)
                    )
                conn.commit()
        finally:
            conn.close()
    except Exception as e:
        log.warning(f"[INGEST] Could not record fetch state for source {source_id}: {e}")


def fetch_feed(source: dict, available_topics: list, article_cap: int = 20) -> int:
    """
    Fetch one RSS source, extract claims, embed, dedup, persist.
    Returns count of new claims inserted. Raises IngestionCancelled if stopped mid-run.
    article_cap is modulated by scrape_weight in run_once().
    """
    _check_stop()

    source_id = source['id']
    feed_url = source['url']
    log.info(f"Fetching {source['name']} ({feed_url}, cap={article_cap})")

    try:
        feed = feedparser.parse(feed_url)
    except Exception as e:
        log.warning(f"Feed fetch failed for {source['name']}: {e}")
        _record_source_fetch(source_id, ok=False, entries=0, error=f"feedparser: {e}")
        return 0

    # SFA-001 P2.3 — detect "feed parses but contains no entries" as a distinct
    # failure mode. Many broken feeds silently return an empty parse object
    # rather than raising. Without this check they looked healthy in the logs.
    entry_count = len(getattr(feed, 'entries', []) or [])
    if entry_count == 0:
        bozo_ex = getattr(feed, 'bozo_exception', None)
        err_msg = f"empty feed (bozo_exception: {bozo_ex})" if bozo_ex else "empty feed (no entries)"
        log.warning(f"  {source['name']}: {err_msg}")
        _record_source_fetch(source_id, ok=False, entries=0, error=err_msg)
        return 0

    inserted = 0
    conn = get_conn()

    try:
        for entry in feed.entries[:article_cap]:  # cap modulated by scrape_weight
            _check_stop()

            article_url   = getattr(entry, 'link', '')
            article_title = getattr(entry, 'title', '')
            raw_text      = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
            published_at  = parse_published(entry)

            if not raw_text or not article_url:
                continue

            # Single LLM call: extract claims + classify technique + assign topics
            processed = process_article(raw_text, article_title, available_topics)
            if not processed:
                continue

            for item in processed:
                claim_text      = item["claim"]
                technique_class = item["technique"]
                topic_tags      = item["topics"]
                modality        = item.get("modality", "unknown")
                certainty       = item.get("certainty", "unknown")
                attribution     = item.get("attribution", "unknown")
                quoted_directly = item.get("quoted_directly", "unknown")

                # Embed and dedup
                vec = embed([claim_text])[0]
                if is_duplicate(vec):
                    continue

                faiss_id = add_to_faiss(vec)

                with conn:
                    new_claim_id = insert_claim(
                        conn, source_id, raw_text, claim_text, article_url,
                        article_title, topic_tags, technique_class,
                        published_at, faiss_id, modality,
                        certainty, attribution, quoted_directly,
                    )
                    update_topic_last_active(conn, topic_tags)

                # Adversarial Input Layer scrutiny — runs per-claim after
                # insertion. Failure is isolated: if scrutiny raises, the
                # claim stays in the ledger with scrutiny_status='pending'.
                try:
                    from scrutiny import scrutinize_claim
                    with get_conn() as scrutiny_conn:
                        with scrutiny_conn.cursor() as scur:
                            scur.execute("""
                                SELECT c.id, c.source_id, c.claim_text, c.topic_tags,
                                       s.total_claims AS source_total_claims,
                                       s.confidence_score AS source_confidence
                                FROM claims c
                                JOIN sources s ON c.source_id = s.id
                                WHERE c.id = %s
                            """, (new_claim_id,))
                            claim_row = scur.fetchone()
                        if claim_row:
                            scrutinize_claim(scrutiny_conn, dict(claim_row))
                except Exception as e:
                    log.warning(f"[SCRUTINY] failed for claim_id={new_claim_id}: {e}")

                inserted += 1

        save_faiss()
        log.info(f"  {source['name']}: {inserted} new claims")
        # SFA-001 P2.3 — record successful fetch even if zero new claims were
        # inserted (dedup or all-off-topic is still a valid outcome that means
        # the source is alive). The distinction from _record_source_fetch ok=False
        # is "did we reach the source and get a valid feed parse," not "did we
        # insert rows."
        _record_source_fetch(source_id, ok=True, entries=entry_count)
        return inserted

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Ingestion stop event — checked before every LLM call for immediate cancellation
# ---------------------------------------------------------------------------

class IngestionCancelled(Exception):
    pass


_stop_event = threading.Event()
# Interrupts run_scheduler's inter-pass sleep so a resume starts a pass immediately
# instead of waiting up to OSS_INGEST_INTERVAL_MINUTES for the next tick.
_wakeup_event = threading.Event()
if os.environ.get("OSS_INGEST_PAUSED", "false").lower() == "true":
    _stop_event.set()


def _check_stop():
    """Raise IngestionCancelled immediately if a stop has been requested."""
    if _stop_event.is_set():
        raise IngestionCancelled("Ingestion stopped by operator")


def is_paused() -> bool:
    return _stop_event.is_set()


def set_paused(paused: bool):
    if paused:
        _stop_event.set()
    else:
        _stop_event.clear()
        # Wake the scheduler out of its inter-pass sleep so ingestion resumes now
        _wakeup_event.set()
    log.info(f"Ingestion {'PAUSED' if paused else 'RESUMED'}")


# ---------------------------------------------------------------------------
# Main scheduler loop
# ---------------------------------------------------------------------------

def _wait_for_swarmfish_idle() -> bool:
    """
    Poll swarmfish /monitor/status. If its monitor cycle is currently running,
    sleep COORD_POLL_SECONDS and re-check, up to COORD_MAX_WAIT_SECONDS total.

    Returns True if swarmfish is idle (or unreachable — in which case there's
    nothing to coordinate with) or if we waited it out. Returns False only if
    we hit the timeout while swarmfish is still busy — caller should defer
    the ingestion pass to the next scheduler tick.

    Fail-safe: if swarmfish is unreachable for any reason, this returns True
    so a swarmfish outage cannot block ingestion forever.
    """
    import urllib.request
    import urllib.error

    waited = 0
    url = f"{SWARMFISH_BASE_URL}/monitor/status"
    headers = {"X-Analyst-Token": SWARMFISH_AUTH_TOKEN}

    while True:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
        except (urllib.error.URLError, OSError, json.JSONDecodeError, TimeoutError) as e:
            # Swarmfish unreachable — fail safe by proceeding with ingestion.
            log.info(f"[COORD] Swarmfish unreachable ({e}); proceeding with ingestion")
            return True

        if not data.get("running"):
            if waited > 0:
                log.info(f"[COORD] Swarmfish idle after waiting {waited}s; proceeding")
            return True

        if waited >= COORD_MAX_WAIT_SECONDS:
            log.info(
                f"[COORD] Swarmfish still busy after {COORD_MAX_WAIT_SECONDS}s; "
                f"deferring this ingestion pass to next tick"
            )
            return False

        log.info(f"[COORD] Swarmfish cycle in progress; waiting {COORD_POLL_SECONDS}s "
                 f"(elapsed {waited}s)")
        time.sleep(COORD_POLL_SECONDS)
        waited += COORD_POLL_SECONDS


def run_once():
    """Single ingestion pass across all sources, processed in parallel.

    Returns the number of new claims inserted, or None if the pass was
    deferred by the coordination guard (swarmfish busy). Callers should
    distinguish None (deferred — try again later) from 0 (ran but found
    no new claims).
    """
    # Coordination guard: defer if swarmfish is currently running a prediction
    # cycle (avoids LM Studio JIT-swap cancellations).
    if not _wait_for_swarmfish_idle():
        return None

    sources       = get_all_sources()
    topics        = get_active_topics()
    topic_weights = get_topic_scrape_weights()

    # Article cap = mean scrape_weight across active topics (floor 2, ceiling 20)
    if topic_weights:
        mean_weight = sum(topic_weights.values()) / len(topic_weights)
        article_cap = max(2, round(20 * mean_weight))
    else:
        article_cap = 20

    log.info(f"Ingestion pass: {len(sources)} sources, {len(topics)} active topics, "
             f"article_cap={article_cap}, workers={INGEST_WORKERS}")
    total = 0
    per_source_counts: dict = {}
    with ThreadPoolExecutor(max_workers=INGEST_WORKERS) as executor:
        futures = {
            executor.submit(fetch_feed, source, topics, article_cap): source
            for source in sources
        }
        for future in as_completed(futures):
            source = futures[future]
            try:
                n = future.result()
                total += n
                per_source_counts[source['name']] = n
            except IngestionCancelled:
                log.info(f"Source {source['name']} cancelled mid-run")
                # Cancel any queued (not yet started) futures
                for f in futures:
                    f.cancel()
                break
            except Exception as e:
                log.error(f"Source {source['name']} failed: {e}")
                per_source_counts[source['name']] = -1  # marker for failure
    log.info(f"Pass complete: {total} new claims total")

    # SFA-001 P3.1 — post-pass health assertions. Loud logging of anomalous
    # per-source outcomes so silent zeros and dropouts are visible within
    # one ingest cycle instead of accumulating invisibly for weeks.
    try:
        zero_sources = [n for n, c in per_source_counts.items() if c == 0]
        failed_sources = [n for n, c in per_source_counts.items() if c == -1]
        if failed_sources:
            log.error(f"[HEALTH] {len(failed_sources)} source(s) FAILED this pass: {failed_sources}")
        if zero_sources and len(zero_sources) >= max(3, len(per_source_counts) // 2):
            # More than half the sources produced zero this pass — either a
            # widespread feed outage, a deduplication spike, or a promotion
            # filter regression. Worth an error log.
            log.error(
                f"[HEALTH] {len(zero_sources)}/{len(per_source_counts)} sources "
                f"produced ZERO claims this pass — investigate: {zero_sources[:10]}"
            )
        elif zero_sources:
            log.info(f"[HEALTH] Zero-claim sources this pass (may be normal dedup): {zero_sources}")
        if total == 0 and len(sources) > 0:
            log.error(
                f"[HEALTH] Ingestion pass returned ZERO total claims across "
                f"{len(sources)} source(s). Probable silent failure — check "
                f"LLM connectivity, topic-tagging, and feed URLs."
            )
    except Exception as e:
        log.warning(f"[HEALTH] Post-pass health assertion failed: {e}")

    # Auto-promote staged claims by source tier
    conn = get_conn()
    try:
        promoted = auto_promote_staged(conn)
        check_hypothesis_predictions(conn)
        log.info(f"[AUTO-PROMOTE] {promoted} claims promoted this pass")
    except Exception as e:
        log.error(f"Auto-promote pass error: {e}")
    finally:
        conn.close()

    return total


def _init_contradict_cursor() -> int:
    """
    Initialize the contradiction-scan cursor to the current MAX(claims.id).
    The scheduler scans only claims added *after* startup; historical sweeps
    run through the manual /admin/ingest endpoint, which passes since_claim_id=0.
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(id), 0) AS max_id FROM claims")
            row = cur.fetchone()
            return int(row['max_id']) if row else 0
    finally:
        conn.close()


def run_scheduler():
    interval_minutes = int(os.environ.get("OSS_INGEST_INTERVAL_MINUTES", "30"))
    interval_seconds = interval_minutes * 60
    log.info(f"Ingestion scheduler starting (interval={interval_minutes}m)")

    contradict_cursor = _init_contradict_cursor()
    log.info(f"[CONTRADICT] Forward-scan cursor initialized at claim_id={contradict_cursor}")

    while True:
        if not _stop_event.is_set():
            try:
                run_once()
            except Exception as e:
                log.error(f"Ingestion pass error: {e}")
            try:
                import social_ingest
                conn = get_conn()
                try:
                    social_ingest.run_social_monitors_sync(conn)
                finally:
                    conn.close()
            except Exception as e:
                log.warning(f"Social monitors pass error: {e}")

            # Hedge pattern aggregation — recompute per-(source, topic) signals.
            # Cheap, single query per cycle. Runs before contradict scan so
            # the signal table reflects the newly-landed claims from run_once.
            try:
                from hedge_aggregation import compute_narrative_signals
                conn = get_conn()
                try:
                    compute_narrative_signals(conn)
                finally:
                    conn.close()
            except Exception as e:
                log.error(f"Hedge aggregation pass error: {e}")

            # Contradiction detection on claims added this pass.
            # Bounded per pass so a large backlog cannot block subsequent ticks.
            try:
                from contradict import scan_new_claims
                prev_cursor = contradict_cursor
                scan_budget = int(os.environ.get("OSS_CONTRADICT_BUDGET", "50"))
                conn = get_conn()
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT COALESCE(MAX(id), 0) AS max_id FROM claims")
                        new_max = int(cur.fetchone()['max_id'])
                finally:
                    conn.close()
                if new_max > prev_cursor:
                    log.info(f"[CONTRADICT] Scanning claims {prev_cursor+1}..{new_max} "
                             f"(budget={scan_budget})")
                    _, last_processed = scan_new_claims(
                        since_claim_id=prev_cursor,
                        max_claims=scan_budget,
                    )
                    if last_processed > prev_cursor:
                        contradict_cursor = last_processed
                        backlog = new_max - contradict_cursor
                        if backlog > 0:
                            log.info(f"[CONTRADICT] Backlog: {backlog} claims deferred to next pass")
                else:
                    log.info("[CONTRADICT] No new claims since last pass")
            except Exception as e:
                log.error(f"Contradiction scan pass error: {e}")
        else:
            log.info("Ingestion pass skipped (paused)")

        # Sleep until interval elapses OR a resume event fires, whichever first.
        # _wakeup_event is set by set_paused(False) so clicking Resume starts a
        # pass within ~1 second instead of waiting up to 30 minutes.
        _wakeup_event.clear()
        woke_early = _wakeup_event.wait(timeout=interval_seconds)
        if woke_early:
            log.info("Scheduler woken early by resume signal")


if __name__ == "__main__":
    run_scheduler()
