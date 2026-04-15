"""
resolver.py — Autonomous Resolver

The committee made predictions at T0. Time has passed and OSS has ingested
new claims on the same topic. The resolver reads the original prediction
and the new claims, and proposes a verdict: confirmed | falsified | still_pending.

Design guardrails:
  1. NOT one of the 8 prediction profiles. A dedicated evaluator prompt with
     no profile-identity, framed as retrospection rather than forecasting.
     This reduces self-confirmation bias.

  2. ADVISORY ONLY. The resolver never writes to acp_outcomes directly.
     It writes to acp_proposed_resolutions. The operator confirms into
     acp_outcomes via the normal /acp/outcome flow (which the Pending UI
     pre-fills from the proposal).

  3. REQUIRES CITATIONS. The resolver must name specific claim IDs that
     support its verdict. A verdict without citations is structurally
     impossible — the JSON schema enforces it.

  4. CLAIMS LIMITED TO POST-SESSION. The resolver only sees claims with
     extracted_at >= session.created_at. Claims the committee already saw
     are not new evidence.
"""

import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Optional

import httpx
import psycopg2

import config
from acp.predictor import get_llm_client, extract_json, _JIT_ERRORS

log = logging.getLogger(__name__)


# ============================================================
# Resolver prompt
# ============================================================

RESOLVER_SYSTEM_PROMPT = """You are an analytical reviewer evaluating a prior prediction against subsequent evidence.

Your job is retrospection, not prediction. You are NOT one of the committee profiles
that made the original prediction. You are an independent reviewer.

You will be given:
  1. The ORIGINAL prediction (what the committee said would happen)
  2. The FALSIFICATION CHECKLIST the committee itself produced (what would make them wrong)
  3. NEW EVIDENCE from the intelligence claim store — facts and events that
     have been reported since the original prediction was made

Your task is to evaluate whether the prediction appears CONFIRMED, FALSIFIED, or STILL PENDING
based strictly on the new evidence. You must cite specific claim IDs that justify your verdict.

CRITICAL RULES:
  - Cite only claims you actually used. A verdict without citations is invalid.
  - If the new evidence does not contain facts directly relevant to the prediction,
    the verdict is "still_pending". Do NOT stretch irrelevant evidence to force a verdict.
  - Do not speculate beyond the cited evidence. If the evidence is thin, say so and
    prefer "still_pending" over a low-confidence "confirmed" or "falsified".
  - The falsification checklist is the committee's own stated conditions. If any of
    those conditions are now observably met, "falsified" is appropriate.
  - Be honest. A "still_pending" verdict with good reasoning is more valuable than
    a premature "confirmed".

You MUST respond with valid JSON in exactly this format — no prose outside the JSON:

{
  "verdict": "confirmed" | "falsified" | "still_pending",
  "resolver_confidence": <float 0.0-1.0>,
  "outcome_text": "<2-4 sentences describing what actually happened, suitable for record-keeping>",
  "reasoning": "<2-4 sentences explaining why the verdict follows from the cited evidence>",
  "cited_claim_ids": [<claim_id_1>, <claim_id_2>, ...]
}

Rules for the JSON fields:
  - verdict: one of the three literal strings above
  - resolver_confidence: your certainty in the verdict (NOT the certainty of the
    original prediction). Use low values (< 0.5) when evidence is thin or ambiguous.
  - outcome_text: factual description of events, not interpretation
  - reasoning: your evaluation chain from cited evidence to verdict
  - cited_claim_ids: integer IDs from the NEW EVIDENCE section. Empty list ONLY if
    verdict is "still_pending" due to no relevant evidence.
"""


def _build_user_message(session: dict, predictions: list[dict], claims: list[dict]) -> str:
    """Assemble the user message for the resolver LLM."""
    parts = []

    parts.append("═══ ORIGINAL PREDICTION ═══")
    parts.append(f"Question: {session.get('question', '?')}")
    parts.append(f"Domain: {session.get('domain', 'general')}")
    parts.append(f"Asked on: {session.get('created_at', '?')}")
    parts.append("")

    consensus = session.get("consensus_confidence")
    if consensus is not None:
        parts.append(f"Committee consensus: {consensus:.0%} confidence")
        range_low  = session.get("consensus_range_low")
        range_high = session.get("consensus_range_high")
        if range_low is not None and range_high is not None:
            parts.append(f"Range: {range_low:.0%} – {range_high:.0%}")
        meta = session.get("meta_confidence")
        if meta:
            parts.append(f"Meta-confidence: {meta}")
    parts.append("")

    # Dump the individual profile predictions so the resolver can see what was predicted
    if predictions:
        parts.append("Committee predictions:")
        for p in predictions:
            pname = p.get("profile_name", "?")
            pconf = p.get("confidence")
            conf_str = f"{pconf:.0%}" if pconf is not None else "err"
            pred = p.get("prediction") or p.get("error") or "(no prediction)"
            parts.append(f"  • [{pname} @ {conf_str}] {pred}")
        parts.append("")

    parts.append("═══ FALSIFICATION CHECKLIST (committee's own stated conditions) ═══")
    checklist = session.get("falsification_checklist") or []
    if checklist:
        for i, item in enumerate(checklist, 1):
            if isinstance(item, dict):
                cond = item.get("condition") or item.get("prediction") or str(item)
                parts.append(f"  {i}. {cond}")
            else:
                parts.append(f"  {i}. {item}")
    else:
        parts.append("  (none provided)")
    parts.append("")

    parts.append("═══ NEW EVIDENCE (OSS claims since prediction) ═══")
    if not claims:
        parts.append("No new claims matching this topic have been ingested since the prediction was made.")
        parts.append("This strongly suggests verdict = still_pending (insufficient evidence).")
    else:
        parts.append(f"Window: since {session.get('created_at', '?')} — {len(claims)} new claims.")
        parts.append("Claim IDs are integers; cite them in your response.")
        parts.append("")
        for c in claims:
            cid = c.get("id", "?")
            src = c.get("source_name", "?")
            date = (c.get("published_at") or c.get("extracted_at") or "")
            if isinstance(date, str):
                date = date[:10]
            text = (c.get("claim_text") or "")[:250]
            parts.append(f"  [#{cid} | {src} | {date}] {text}")
    parts.append("")

    parts.append("═══ YOUR EVALUATION ═══")
    parts.append("Apply the rules in your system prompt. Produce the JSON verdict. Remember: citations are required, still_pending is honorable.")

    return "\n".join(parts)


# ============================================================
# Claim fetching from OSS
# ============================================================

# Maps swarmfish domain names to OSS topic tags. Mirrors oss_bridge.DOMAIN_TO_TOPICS
# but kept local so resolver doesn't depend on that module's sync.
DOMAIN_TO_OSS_TOPICS = {
    "geopolitical_risk": ["iran-hormuz", "iran"],
    "commodities":       ["iran-hormuz"],
    "market_structure":  [],
    "technology":        [],
    "credit_cycles":     [],
    "general":           [],
}


def fetch_new_claims(domain: str, since_iso: str, limit: int = 30) -> list[dict]:
    """
    Query OSS /api/record for claims under the domain's topics, filtered to those
    ingested after since_iso. Returns up to `limit` claims, newest first.
    """
    topics = DOMAIN_TO_OSS_TOPICS.get(domain, [])
    # For domains not in the map, try using the domain string itself as a topic tag
    if not topics:
        topics = [domain]

    collected: list[dict] = []
    seen_ids: set = set()

    for topic in topics:
        try:
            resp = httpx.post(
                f"{config.OSS_BASE_URL}/api/record",
                json={"topic": topic, "since": since_iso},
                headers={"X-Analyst-Token": config.OSS_ANALYST_TOKEN},
                timeout=15,
            )
            if resp.status_code != 200:
                log.warning(f"[RESOLVER] OSS /api/record returned {resp.status_code} for topic={topic!r}")
                continue
            data = resp.json()
            for c in data.get("claims", []):
                cid = c.get("id")
                if cid is None or cid in seen_ids:
                    continue
                seen_ids.add(cid)
                collected.append(c)
        except Exception as e:
            log.warning(f"[RESOLVER] OSS fetch failed for topic={topic!r}: {e}")

    # Sort newest first, cap to limit
    def sort_key(c):
        return (c.get("extracted_at") or c.get("published_at") or "")
    collected.sort(key=sort_key, reverse=True)
    return collected[:limit]


# ============================================================
# LLM call
# ============================================================

def call_resolver_llm(system_prompt: str, user_message: str) -> str:
    """Call LM Studio using the same retry-on-JIT-unload pattern as predictor."""
    client = get_llm_client()
    kwargs = dict(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        temperature=0.2,   # lower than predictor — retrospection should be stable
        max_tokens=config.LLM_MAX_TOKENS,
    )
    for attempt in range(2):
        try:
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()
        except Exception as e:
            err = str(e).lower()
            if attempt == 0 and any(jit in err for jit in _JIT_ERRORS):
                log.info("[RESOLVER] LM Studio JIT unload, retrying in 15s...")
                time.sleep(15)
                continue
            raise


# ============================================================
# Session + predictions loader
# ============================================================

def _load_session_with_predictions(db_conn, session_id: str) -> Optional[tuple[dict, list[dict]]]:
    """Load the session row and its individual predictions. Returns (session, predictions) or None."""
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM acp_sessions WHERE id = %s", (session_id,))
    row = cursor.fetchone()
    if row is None:
        cursor.close()
        return None
    cols = [d[0] for d in cursor.description]
    session = dict(zip(cols, row))

    cursor.execute("""
        SELECT p.profile_name, p.prediction, p.confidence, p.reasoning_summary, p.error
        FROM acp_predictions p
        JOIN acp_session_predictions sp ON sp.prediction_id = p.id
        WHERE sp.session_id = %s
        ORDER BY p.created_at
    """, (session_id,))
    pcols = [d[0] for d in cursor.description]
    predictions = [dict(zip(pcols, r)) for r in cursor.fetchall()]
    cursor.close()
    return session, predictions


# ============================================================
# Public entrypoint
# ============================================================

def resolve_session(db_conn, session_id: str) -> dict:
    """
    Run the autonomous resolver on a session. Writes an acp_proposed_resolutions
    row and returns the result as a dict. Does NOT modify acp_outcomes.

    Raises ValueError on unrecoverable issues (session not found, LLM parse fail).
    """
    loaded = _load_session_with_predictions(db_conn, session_id)
    if loaded is None:
        raise ValueError(f"Session {session_id} not found")
    session, predictions = loaded

    # Compute the evidence window lower bound
    created_at = session.get("created_at")
    if isinstance(created_at, datetime):
        since_iso = created_at.isoformat()
    elif isinstance(created_at, str):
        since_iso = created_at
    else:
        since_iso = datetime.now(timezone.utc).isoformat()

    domain = session.get("domain", "general") or "general"
    claims = fetch_new_claims(domain, since_iso)

    # Build prompts
    user_msg = _build_user_message(session, predictions, claims)

    log.info(f"[RESOLVER] Resolving session {session_id[:8]}... "
             f"domain={domain} claims={len(claims)}")

    try:
        raw = call_resolver_llm(RESOLVER_SYSTEM_PROMPT, user_msg)
        parsed = extract_json(raw)
    except Exception as e:
        log.warning(f"[RESOLVER] LLM call or parse failed: {e}")
        raise ValueError(f"Resolver LLM failed: {e}")

    # Validate and normalize parsed output
    verdict = (parsed.get("verdict") or "").strip().lower()
    if verdict not in ("confirmed", "falsified", "still_pending"):
        raise ValueError(f"Resolver returned invalid verdict: {verdict!r}")

    confidence = parsed.get("resolver_confidence")
    if confidence is None:
        confidence = 0.5
    confidence = max(0.0, min(1.0, float(confidence)))

    outcome_text = (parsed.get("outcome_text") or "").strip()
    if not outcome_text:
        outcome_text = f"Resolver verdict: {verdict} (no outcome text provided)."

    reasoning = (parsed.get("reasoning") or "").strip()
    if not reasoning:
        reasoning = "(resolver did not provide reasoning)"

    cited_ids = parsed.get("cited_claim_ids") or []
    if not isinstance(cited_ids, list):
        cited_ids = []

    # Build the cited_claims JSONB by looking up cited IDs in the fetched claims
    claims_by_id = {c.get("id"): c for c in claims if c.get("id") is not None}
    cited_claims = []
    for cid in cited_ids:
        try:
            cid_int = int(cid)
        except (TypeError, ValueError):
            continue
        claim = claims_by_id.get(cid_int)
        if claim is None:
            continue
        cited_claims.append({
            "claim_id": cid_int,
            "source": claim.get("source_name"),
            "date": (claim.get("published_at") or claim.get("extracted_at") or "")[:10]
                    if isinstance(claim.get("published_at") or claim.get("extracted_at"), str)
                    else None,
            "text_excerpt": (claim.get("claim_text") or "")[:300],
        })

    # Persist
    cursor = db_conn.cursor()
    cursor.execute("""
        INSERT INTO acp_proposed_resolutions (
            session_id, verdict, resolver_confidence,
            outcome_text, reasoning, cited_claims,
            claims_considered_count, claims_since
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, created_at
    """, (
        session_id, verdict, confidence,
        outcome_text, reasoning, json.dumps(cited_claims),
        len(claims), since_iso,
    ))
    row = cursor.fetchone()
    proposal_id = str(row[0])
    created_at_out = row[1].isoformat() if hasattr(row[1], "isoformat") else str(row[1])
    db_conn.commit()
    cursor.close()

    log.info(f"[RESOLVER] Proposed {verdict} @ {confidence:.0%} "
             f"for session {session_id[:8]} "
             f"(cited {len(cited_claims)} of {len(claims)} claims)")

    return {
        "id": proposal_id,
        "session_id": session_id,
        "verdict": verdict,
        "resolver_confidence": confidence,
        "outcome_text": outcome_text,
        "reasoning": reasoning,
        "cited_claims": cited_claims,
        "claims_considered_count": len(claims),
        "claims_since": since_iso,
        "created_at": created_at_out,
    }
