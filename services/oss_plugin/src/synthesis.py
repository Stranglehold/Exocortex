"""
synthesis.py — Evidence synthesis for analyst questions.

"Ask the ledger" — given an active question, construct a structured
evidence summary from stored claims weighted by source credibility
and recency. The analyst sees claims organized for/against the question,
not a raw topic dump.
"""
import logging
import math
import os
import re
from datetime import datetime, timezone

from .db import get_conn, jloads, jdumps

log = logging.getLogger("[SYNTHESIS]")

LLM_URL   = os.environ.get("OSS_LLM_URL",   "http://host.docker.internal:1236/v1")
from .llm_config import get_llm_model as _get_llm_model
LLM_MODEL = _get_llm_model()

# Half-life for recency decay (days)
RECENCY_HALF_LIFE_DAYS = 7.0

# technique_class values that count as "contradicting"
_CONTRADICTING_TECHNIQUES = {"fracture", "presuasion"}
# technique_class values that count as "supporting" (propagandistic amplification)
_SUPPORTING_TECHNIQUES = {"emergent", "direct"}


# ---------------------------------------------------------------------------
# FAISS-backed claim retrieval
# ---------------------------------------------------------------------------

def _find_relevant_claims(conn, question_text: str, limit: int = 40) -> list:
    try:
        from sentence_transformers import SentenceTransformer
        import faiss
        import numpy as np

        faiss_path = os.environ.get("OSS_FAISS_PATH", "/a0/usr/oss/claims.index")
        if not os.path.exists(faiss_path):
            return _fallback_claims(conn, limit)

        m = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        vec = m.encode([question_text], normalize_embeddings=True).astype(np.float32)
        idx = faiss.read_index(faiss_path)
        k = min(limit, idx.ntotal)
        if k == 0:
            return _fallback_claims(conn, limit)

        D, I = idx.search(vec, k)
        faiss_ids = [int(i) for i in I[0] if i >= 0]
        scores = {int(i): float(d) for i, d in zip(I[0], D[0]) if i >= 0}

        if not faiss_ids:
            return _fallback_claims(conn, limit)

        placeholders = ",".join("?" * len(faiss_ids))
        cur = conn.cursor()
        cur.execute(
            f"SELECT c.*, s.name AS source_name, s.cluster, s.source_type "
            f"FROM claims c JOIN sources s ON s.id=c.source_id "
            f"WHERE c.faiss_id IN ({placeholders}) AND c.trust_level != 'IRRELEVANT'",
            faiss_ids,
        )
        rows = [dict(r) for r in cur.fetchall()]
        for r in rows:
            r["relevance_score"] = scores.get(r["faiss_id"], 0.0)
        return rows
    except Exception as e:
        log.warning(f"FAISS search failed: {e}")
        return _fallback_claims(conn, limit)


def _fallback_claims(conn, limit: int) -> list:
    cur = conn.cursor()
    cur.execute(
        "SELECT c.*, s.name AS source_name, s.cluster, s.source_type "
        "FROM claims c JOIN sources s ON s.id=c.source_id "
        "WHERE c.trust_level='PROMOTED' ORDER BY c.extracted_at DESC LIMIT ?",
        (limit,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    for r in rows:
        r["relevance_score"] = 0.5
    return rows


# ---------------------------------------------------------------------------
# Credibility lookup (inline — avoids circular import from credibility.py)
# ---------------------------------------------------------------------------

def _credibility_map(conn) -> dict:
    """Return {source_id: overall_score} for all sources with credibility records."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT source_id, overall FROM source_credibility")
        return {r["source_id"]: float(r["overall"]) for r in cur.fetchall()}
    except Exception:
        return {}


def _default_credibility(source_type: str) -> float:
    """Fall back to source-type heuristic when no analyst rating exists."""
    return {"wire": 0.85, "official": 0.85, "outlet": 0.65,
            "social": 0.40, "independent": 0.55}.get(source_type or "", 0.60)


# ---------------------------------------------------------------------------
# Recency decay
# ---------------------------------------------------------------------------

def _recency_weight(extracted_at_iso: str, half_life_days: float = RECENCY_HALF_LIFE_DAYS) -> float:
    """Exponential decay: weight=1.0 at extraction, halves every `half_life_days` days."""
    try:
        extracted = datetime.fromisoformat(extracted_at_iso.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age_days = max(0.0, (now - extracted).total_seconds() / 86400.0)
        return math.pow(0.5, age_days / half_life_days)
    except Exception:
        return 0.5


# ---------------------------------------------------------------------------
# Claim classification
# ---------------------------------------------------------------------------

def _classify_claim(claim: dict) -> str:
    """
    Rough classification of a claim relative to the analyst question.
    Uses technique_class as proxy — manipulation techniques that create
    fracture/presupposition are 'contradicting'; coordinated/direct
    amplification is 'supporting'; unknown is 'neutral'.
    """
    technique = (claim.get("technique_class") or "none").lower()
    if technique in _CONTRADICTING_TECHNIQUES:
        return "contradicting"
    if technique in _SUPPORTING_TECHNIQUES:
        return "supporting"
    return "neutral"


# ---------------------------------------------------------------------------
# LLM synthesis paragraph
# ---------------------------------------------------------------------------

def _strip_thinking(raw: str) -> str:
    return re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()


def _llm_synthesis(question_text: str, supporting: list, contradicting: list,
                   neutral: list) -> str:
    """Call LLM to write a 2-paragraph synthesis with claim ID citations."""
    try:
        from openai import OpenAI
        client = OpenAI(base_url=LLM_URL, api_key="local")

        def _fmt(claims):
            return "\n".join(
                f"  [{c['id']}] {c['claim_text'][:180]} (source: {c.get('source_name','?')}, "
                f"score: {c.get('_composite_score', 0.0):.2f})"
                for c in claims[:10]
            ) or "  (none)"

        prompt = f"""You are an intelligence analyst. Synthesize the following evidence for this question:

QUESTION: {question_text}

SUPPORTING CLAIMS:
{_fmt(supporting)}

CONTRADICTING CLAIMS:
{_fmt(contradicting)}

NEUTRAL/CONTEXT CLAIMS:
{_fmt(neutral)}

Write exactly 2 paragraphs:
1. Summarize what the evidence supports, citing claim IDs in brackets [ID].
2. Summarize contradictions or gaps, citing claim IDs. Note confidence limitations.

Be precise. Do not speculate beyond the evidence. Cite at least 3 claim IDs total."""

        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=600,
        )
        return _strip_thinking(resp.choices[0].message.content)
    except Exception as e:
        log.warning(f"LLM synthesis call failed: {e}")
        # Fallback: deterministic summary
        return (
            f"Evidence synthesis for: {question_text[:120]}\n"
            f"Supporting: {len(supporting)} claims. Contradicting: {len(contradicting)} claims. "
            f"Neutral: {len(neutral)} claims. LLM synthesis unavailable."
        )


# ---------------------------------------------------------------------------
# Main synthesize function
# ---------------------------------------------------------------------------

def synthesize(conn, question_text: str, question_id: str = None,
               limit_claims: int = 40) -> dict:
    """
    Given an active question, construct a structured evidence summary.

    1. Get relevant claims via FAISS (falls back to recent PROMOTED claims)
    2. Get source credibility weights for those claims' sources
    3. Score each claim: relevance_score * credibility * recency_decay (half-life 7 days)
    4. Sort by score, split into supporting/contradicting/neutral
    5. Call LLM to write a 2-paragraph synthesis with citations
    6. Return structured result dict

    Returns:
        {
          question, question_id,
          supporting: [...], contradicting: [...], neutral: [...],
          synthesis_text, claim_count, sources_used,
          top_claim_ids: [...]
        }
    """
    try:
        claims = _find_relevant_claims(conn, question_text, limit=limit_claims)
        cred_map = _credibility_map(conn)

        scored = []
        for c in claims:
            source_id = c.get("source_id")
            credibility = cred_map.get(source_id, _default_credibility(c.get("source_type")))
            recency = _recency_weight(c.get("extracted_at") or "")
            relevance = c.get("relevance_score", 0.5)
            composite = relevance * credibility * recency
            c["_composite_score"] = round(composite, 6)
            c["_credibility"] = credibility
            c["_recency"] = round(recency, 4)
            scored.append(c)

        scored.sort(key=lambda x: x["_composite_score"], reverse=True)

        supporting   = [c for c in scored if _classify_claim(c) == "supporting"]
        contradicting = [c for c in scored if _classify_claim(c) == "contradicting"]
        neutral      = [c for c in scored if _classify_claim(c) == "neutral"]

        sources_used = list({c.get("source_name", "unknown") for c in scored})
        top_claim_ids = [c["id"] for c in scored[:10]]

        synthesis_text = _llm_synthesis(question_text, supporting, contradicting, neutral)

        # Strip internal scoring fields from output
        def _clean(claims_list):
            out = []
            for c in claims_list:
                d = {k: v for k, v in c.items() if not k.startswith("_")}
                out.append(d)
            return out

        return {
            "question":       question_text,
            "question_id":    question_id,
            "supporting":     _clean(supporting),
            "contradicting":  _clean(contradicting),
            "neutral":        _clean(neutral),
            "synthesis_text": synthesis_text,
            "claim_count":    len(scored),
            "sources_used":   sources_used,
            "top_claim_ids":  top_claim_ids,
        }

    except Exception as e:
        log.warning(f"synthesize failed for question={question_text[:60]!r}: {e}")
        return {
            "question":       question_text,
            "question_id":    question_id,
            "supporting":     [],
            "contradicting":  [],
            "neutral":        [],
            "synthesis_text": f"Synthesis failed: {e}",
            "claim_count":    0,
            "sources_used":   [],
            "top_claim_ids":  [],
        }
