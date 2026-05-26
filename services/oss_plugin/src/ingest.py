"""
ingest.py — RSS ingestion pipeline (OSS V2, SQLite).

Fetches RSS feeds, extracts claims via LLM, embeds, deduplicates against FAISS,
and persists to SQLite. V2: question-context injection into extraction prompt,
rejection ledger for all rejected claims.

Background loop: call start_background_loop() once at plugin load to begin
autonomous ingestion. Uses a daemon thread — dies cleanly with the parent process.
"""

import json
import logging
import os
import re
import threading
import time
from datetime import datetime, timezone
from typing import Optional

import feedparser
import numpy as np
import faiss
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from .db import get_conn, jloads, jdumps, new_id

log = logging.getLogger("[INGEST]")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

LLM_URL    = os.environ.get("OSS_LLM_URL",   "http://host.docker.internal:1236/v1")
from .llm_config import get_llm_model as _get_llm_model
LLM_MODEL  = _get_llm_model()
EMB_MODEL  = os.environ.get("OSS_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
FAISS_PATH = os.environ.get("OSS_FAISS_PATH", "/a0/usr/oss/claims.index")
DEDUP_THRESHOLD = float(os.environ.get("OSS_DEDUP_THRESHOLD", "0.95"))
INTERVAL_MINUTES = int(os.environ.get("OSS_INGEST_INTERVAL_MINUTES", "30"))

_ingest_paused = os.environ.get("OSS_INGEST_PAUSED", "true").lower() in ("1", "true", "yes")
_ingest_lock   = threading.Lock()
_bg_thread: Optional[threading.Thread] = None


def is_paused() -> bool:
    return _ingest_paused


def set_paused(v: bool) -> None:
    global _ingest_paused
    _ingest_paused = v


# ---------------------------------------------------------------------------
# LLM client
# ---------------------------------------------------------------------------

_llm: Optional[OpenAI] = None


def get_llm() -> OpenAI:
    global _llm
    if _llm is None:
        _llm = OpenAI(base_url=LLM_URL, api_key="local")
    return _llm


def _strip_thinking(raw: str) -> str:
    return re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()


# ---------------------------------------------------------------------------
# Embedding model
# ---------------------------------------------------------------------------

_embedder: Optional[SentenceTransformer] = None


def get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        log.info(f"Loading embedding model: {EMB_MODEL}")
        _embedder = SentenceTransformer(EMB_MODEL, device="cpu")
    return _embedder


def embed(texts: list) -> np.ndarray:
    return get_embedder().encode(texts, normalize_embeddings=True, show_progress_bar=False)


# ---------------------------------------------------------------------------
# FAISS index
# ---------------------------------------------------------------------------

_faiss_index: Optional[faiss.IndexFlatIP] = None
_faiss_lock  = threading.Lock()


def get_faiss() -> faiss.IndexFlatIP:
    global _faiss_index
    with _faiss_lock:
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


def is_duplicate(vec: np.ndarray, threshold: float = DEDUP_THRESHOLD) -> tuple:
    """Return (is_dup, similarity_score). vec must be (1, dim) float32."""
    idx = get_faiss()
    if idx.ntotal == 0:
        return False, 0.0
    D, I = idx.search(vec.astype(np.float32), 1)
    score = float(D[0][0])
    return score >= threshold, score


def add_to_faiss(vec: np.ndarray) -> int:
    """Add vector, return new FAISS id (ntotal - 1)."""
    idx = get_faiss()
    with _faiss_lock:
        idx.add(vec.astype(np.float32))
        return idx.ntotal - 1


def save_faiss() -> None:
    idx = get_faiss()
    with _faiss_lock:
        os.makedirs(os.path.dirname(FAISS_PATH), exist_ok=True)
        faiss.write_index(idx, FAISS_PATH)


# ---------------------------------------------------------------------------
# Active question context (V2)
# ---------------------------------------------------------------------------

def _get_active_question_context(conn) -> str:
    """Return a short description of the analyst's active question(s) for LLM context."""
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT text, attention_weights FROM active_questions WHERE active=1 ORDER BY last_updated DESC LIMIT 3"
        )
        rows = cur.fetchall()
        if not rows:
            return ""
        parts = []
        for r in rows:
            text = r["text"]
            weights = jloads(r["attention_weights"], {})
            if weights:
                wstr = ", ".join(f"{k}:{v}" for k, v in weights.items() if v and v > 0.3)
                parts.append(f'"{text}" (focus: {wstr})')
            else:
                parts.append(f'"{text}"')
        return "Active analyst questions: " + "; ".join(parts)
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# LLM extraction
# ---------------------------------------------------------------------------

def extract_claims(article_text: str, source_name: str,
                   known_topics: list, question_ctx: str = "") -> list:
    """
    Extract discrete factual claims from article text.
    Returns list of dicts: {claim_text, technique_class, cui_bono, emotional_salience, topic_tags}.
    """
    topics_str = ", ".join(known_topics) if known_topics else "general"
    q_block = f"\n\n{question_ctx}" if question_ctx else ""

    prompt = f"""Extract discrete factual claims from the article below.
Source: {source_name}
Known topics: {topics_str}{q_block}

For each claim return a JSON object with:
  claim_text         — the specific factual assertion (1-2 sentences)
  technique_class    — one of: presuasion | fracture | emergent | direct | none
  cui_bono           — array of actors who benefit from this framing (empty if none)
  emotional_salience — float 0.0-1.0 (how emotionally charged is this claim)
  topic_tags         — array of matching topic tags from the known list (empty if none)

Return a JSON array of claim objects only. No other text.

Article:
{article_text[:3000]}"""

    try:
        resp = get_llm().chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=2048,
        )
        raw = _strip_thinking(resp.choices[0].message.content)
        # Strip markdown code fences
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
        raw = re.sub(r"\s*```$", "", raw)
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
        return []
    except Exception as e:
        log.warning(f"extract_claims failed for {source_name}: {e}")
        return []


def classify_technique(claim_text: str) -> str:
    """Classify manipulation technique for a single claim."""
    prompt = f"""Classify the manipulation technique used in this claim.
Claim: {claim_text}

Choose exactly one:
  presuasion  — primes the audience before presenting information
  fracture    — exploits divisions or creates wedge issues
  emergent    — coordinates across ideologically distinct sources simultaneously
  direct      — straightforward propaganda or misinformation
  none        — factual reporting with no discernible technique

Return only the technique name, nothing else."""
    try:
        resp = get_llm().chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=16,
        )
        raw = _strip_thinking(resp.choices[0].message.content).strip().lower()
        valid = {"presuasion", "fracture", "emergent", "direct", "none"}
        return raw if raw in valid else "none"
    except Exception:
        return "none"


def assign_topics(claim_text: str, known_topics: list) -> list:
    """Match claim to known topic tags."""
    if not known_topics:
        return []
    topics_str = ", ".join(known_topics)
    prompt = f"""Which of these topic tags apply to this claim?
Topics: {topics_str}
Claim: {claim_text}

Return a JSON array of matching tag strings. Return [] if none match."""
    try:
        resp = get_llm().chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=128,
        )
        raw = _strip_thinking(resp.choices[0].message.content)
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
        raw = re.sub(r"\s*```$", "", raw)
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [t for t in parsed if t in known_topics]
        return []
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Promotion
# ---------------------------------------------------------------------------

def auto_promote_staged(conn, claim_id: int, source_type: str,
                        staging_confidence: float,
                        topic_tags: list,
                        operator_multiplier: float = 1.0) -> bool:
    """
    Promote STAGED claim based on source tier.
    Returns True if promoted.
    """
    threshold = 0.6 * operator_multiplier

    # Wire and official sources: unconditional promotion
    if source_type in ("wire", "official"):
        _do_promote(conn, claim_id, staging_confidence)
        return True

    # Outlet/independent/social: require topic tag + confidence threshold
    if topic_tags and staging_confidence >= threshold:
        _do_promote(conn, claim_id, staging_confidence)
        return True

    return False


def _do_promote(conn, claim_id: int, confidence: float) -> None:
    cur = conn.cursor()
    cur.execute(
        "UPDATE claims SET trust_level='PROMOTED' WHERE id=? AND trust_level='STAGED'",
        (claim_id,),
    )
    if cur.rowcount:
        # source_weights MUST be keyed by source_id — the contamination cascade
        # looks up a source's contributed promotions by id, not by source_type.
        cur.execute("SELECT source_id FROM claims WHERE id=?", (claim_id,))
        r = cur.fetchone()
        source_id = r["source_id"] if r else None
        cur.execute("""
            INSERT INTO promotion_snapshots
                (claim_id, promotion_confidence, source_weights, threshold_at_promotion)
            VALUES (?, ?, ?, ?)
        """, (claim_id, confidence, jdumps({str(source_id): confidence}), 0.6))
        conn.commit()
        # Check any hypothesis predictions against this newly-promoted claim
        _check_hypothesis_predictions(conn, claim_id)


def _check_hypothesis_predictions(conn, claim_id: int) -> None:
    """Match a newly-promoted claim against open hypothesis predictions."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT embedding_model, faiss_id FROM claims WHERE id=?", (claim_id,))
        row = cur.fetchone()
        if not row or row["faiss_id"] is None:
            return

        cur.execute(
            "SELECT id, predictions_generated, prediction_check_cursor FROM hypothesis_registry WHERE status='ACTIVE'",
        )
        hypotheses = cur.fetchall()

        for h in hypotheses:
            preds = jloads(h["predictions_generated"], [])
            cursor_pos = h["prediction_check_cursor"] or 0
            if cursor_pos >= len(preds):
                continue
            # Simple text-embed check on unchecked predictions
            new_preds = preds[cursor_pos:]
            for pred in new_preds:
                pred_text = pred if isinstance(pred, str) else pred.get("text", "")
                if not pred_text:
                    continue
                try:
                    cur.execute("SELECT claim_text FROM claims WHERE id=?", (claim_id,))
                    claim_row = cur.fetchone()
                    if not claim_row:
                        continue
                    vecs = embed([pred_text, claim_row["claim_text"]])
                    score = float(np.dot(vecs[0], vecs[1]))
                    if score >= 0.70:
                        cur.execute(
                            "UPDATE hypothesis_registry SET predictions_confirmed=predictions_confirmed+1 WHERE id=?",
                            (h["id"],),
                        )
                        conn.commit()
                        break
                except Exception:
                    pass
            # Advance cursor
            cur.execute(
                "UPDATE hypothesis_registry SET prediction_check_cursor=? WHERE id=?",
                (cursor_pos + len(new_preds), h["id"]),
            )
            conn.commit()
    except Exception as e:
        log.warning(f"_check_hypothesis_predictions error: {e}")


# ---------------------------------------------------------------------------
# Feed fetching
# ---------------------------------------------------------------------------

def _get_known_topics(conn) -> list:
    cur = conn.cursor()
    cur.execute("SELECT tag FROM topics WHERE active=1")
    return [r["tag"] for r in cur.fetchall()]


def _get_source_scrape_weight(conn, source_id: int) -> float:
    cur = conn.cursor()
    cur.execute("SELECT scrape_weight FROM sources WHERE id=?", (source_id,))
    r = cur.fetchone()
    return float(r["scrape_weight"]) if r else 1.0


def _log_rejection(conn, claim_text: str, article_url: str,
                   article_title: Optional[str], source_id: int,
                   reason: str, detail: str = "",
                   similarity_score: float = 0.0,
                   duplicate_of_id: Optional[int] = None) -> None:
    """Write to rejection_ledger (V2 transparency)."""
    try:
        conn.execute("""
            INSERT INTO rejection_ledger
                (claim_text, article_url, article_title, source_id,
                 rejection_reason, rejection_detail, similarity_score, duplicate_of_id)
            VALUES (?,?,?,?,?,?,?,?)
        """, (claim_text, article_url, article_title, source_id,
              reason, detail, similarity_score, duplicate_of_id))
        conn.commit()
    except Exception:
        pass


def fetch_feed(conn, source_row) -> int:
    """Fetch one RSS feed, extract, dedup, store. Returns claim count ingested."""
    source_id   = source_row["id"]
    source_name = source_row["name"]
    url         = source_row["url"]
    source_type = source_row["source_type"]

    scrape_weight = _get_source_scrape_weight(conn, source_id)
    if scrape_weight <= 0.01:
        log.info(f"Skipping {source_name} — scrape_weight={scrape_weight:.2f}")
        return 0

    try:
        feed = feedparser.parse(url)
    except Exception as e:
        log.warning(f"feedparser failed for {source_name}: {e}")
        return 0

    if not feed.entries:
        return 0

    known_topics = _get_known_topics(conn)
    question_ctx = _get_active_question_context(conn)
    ingested = 0

    # Get operator threshold multiplier
    cur = conn.cursor()
    cur.execute("SELECT threshold_multiplier FROM operator_state ORDER BY id DESC LIMIT 1")
    orow = cur.fetchone()
    op_multiplier = float(orow["threshold_multiplier"]) if orow else 1.0

    for entry in feed.entries[:20]:  # cap per cycle
        try:
            article_url   = getattr(entry, "link", "")
            article_title = getattr(entry, "title", "")
            article_text  = getattr(entry, "summary", "") or getattr(entry, "description", "")
            published_raw = getattr(entry, "published", None)

            if not article_text or not article_url:
                continue

            published_at = None
            if published_raw:
                try:
                    import email.utils
                    published_at = datetime(*email.utils.parsedate(published_raw)[:6],
                                           tzinfo=timezone.utc).isoformat()
                except Exception:
                    pass

            claims = extract_claims(article_text, source_name, known_topics, question_ctx)
            if not claims:
                continue

            for raw_claim in claims:
                claim_text = (raw_claim.get("claim_text") or "").strip()
                if not claim_text:
                    continue

                technique  = raw_claim.get("technique_class") or "none"
                if technique not in ("presuasion", "fracture", "emergent", "direct", "none"):
                    technique = "none"
                cui_bono   = jdumps(raw_claim.get("cui_bono") or [])
                try:
                    salience = max(0.0, min(1.0, float(raw_claim.get("emotional_salience", 0.0) or 0.0)))
                except (TypeError, ValueError):
                    salience = 0.0  # clamp to [0,1]; an out-of-range LLM value would skew drift averaging
                tags       = raw_claim.get("topic_tags") or []
                if not isinstance(tags, list):
                    tags = []
                # Deterministic taxonomy gate: keep only tags that resolve to a
                # known topic (case-insensitive), discarding LLM-invented freeform
                # tags. Without this the off-topic check below is defeated — any
                # tag at all, even an irrelevant one, lets an article through.
                if known_topics:
                    _known_lc = {t.lower(): t for t in known_topics}
                    tags = [_known_lc[t.lower()] for t in tags
                            if isinstance(t, str) and t.lower() in _known_lc]
                tags_json  = jdumps(tags)

                # Embed and dedup
                vec = embed([claim_text])
                dup, sim_score = is_duplicate(vec)
                if dup:
                    _log_rejection(conn, claim_text, article_url, article_title,
                                   source_id, "duplicate",
                                   f"similarity={sim_score:.3f}", sim_score)
                    continue

                # Confidence scoring: wire/official = 0.85, outlet = 0.65, others = 0.5
                conf_map = {"wire": 0.85, "official": 0.85, "outlet": 0.65,
                            "international": 0.65, "independent": 0.5, "social": 0.4}
                staging_conf = conf_map.get(source_row["cluster"], 0.5)

                # Off-topic rejection check
                if known_topics and not tags:
                    _log_rejection(conn, claim_text, article_url, article_title,
                                   source_id, "off_topic",
                                   "No matching topic tags")
                    continue

                # Insert claim
                cur.execute("""
                    INSERT INTO claims
                        (source_id, raw_text, claim_text, article_url, article_title,
                         topic_tags, technique_class, published_at, faiss_id,
                         trust_level, staging_confidence, cui_bono, emotional_salience_score)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (source_id, article_text[:500], claim_text, article_url,
                      article_title, tags_json, technique, published_at,
                      None, "STAGED", staging_conf, cui_bono, salience))
                claim_id = cur.lastrowid
                conn.commit()

                # Add to FAISS
                faiss_id = add_to_faiss(vec)
                cur.execute("UPDATE claims SET faiss_id=? WHERE id=?", (faiss_id, claim_id))
                conn.commit()

                # Update source claim count
                cur.execute("UPDATE sources SET total_claims=total_claims+1 WHERE id=?", (source_id,))
                # Keep the topic dashboard live: bump claim_count + last_active for
                # each matched topic (otherwise both columns stay frozen forever).
                for _tag in tags:
                    cur.execute(
                        "UPDATE topics SET claim_count=claim_count+1, last_active=datetime('now') WHERE tag=?",
                        (_tag,),
                    )
                conn.commit()

                # Auto-promote
                auto_promote_staged(conn, claim_id, source_type,
                                    staging_conf, tags, op_multiplier)
                ingested += 1

        except Exception as e:
            log.warning(f"Error processing entry from {source_name}: {e}")

    if ingested:
        save_faiss()
    return ingested


# ---------------------------------------------------------------------------
# Full ingestion pass
# ---------------------------------------------------------------------------

def run_once(conn=None) -> dict:
    """Run one ingestion pass across all enabled sources."""
    owned = conn is None
    c = conn or get_conn()
    try:
        # Run analysis modules after ingestion
        from . import contradict, silence, activation

        cur = c.cursor()
        cur.execute("SELECT * FROM sources ORDER BY id")
        sources = cur.fetchall()

        total = 0
        for src in sources:
            count = fetch_feed(c, src)
            total += count
            if count:
                log.info(f"[INGEST] {src['name']}: +{count} claims")

        # Post-ingestion analysis
        known_topics = _get_known_topics(c)
        for topic in known_topics:
            try:
                contradict.scan_new_claims(c)
            except Exception as e:
                log.warning(f"contradict scan error: {e}")
            try:
                silence.run_silence_scan(c, topic)
            except Exception as e:
                log.warning(f"silence scan error: {e}")
            try:
                activation.run_activation_scan(c, topic)
            except Exception as e:
                log.warning(f"activation scan error: {e}")

        log.info(f"[INGEST] Pass complete: {total} claims ingested")
        return {"ingested": total, "sources": len(sources)}
    finally:
        if owned:
            c.close()


# ---------------------------------------------------------------------------
# Background scheduler
# ---------------------------------------------------------------------------

def _scheduler_loop() -> None:
    log.info(f"[INGEST] Background scheduler started (interval={INTERVAL_MINUTES}m)")
    # Brief startup delay so the plugin finishes loading
    time.sleep(30)
    while True:
        if not _ingest_paused:
            try:
                with _ingest_lock:
                    run_once()
            except Exception as e:
                log.warning(f"[INGEST] Scheduler error: {e}")
        time.sleep(INTERVAL_MINUTES * 60)


def start_background_loop() -> None:
    """Start the daemon ingestion thread. Call once at plugin load."""
    global _bg_thread
    if _bg_thread is not None and _bg_thread.is_alive():
        return
    _bg_thread = threading.Thread(target=_scheduler_loop, daemon=True, name="oss-ingest")
    _bg_thread.start()
    log.info("[INGEST] Background loop started")
