"""
retcon_ledger.py — Claim trust lifecycle management.

Handles promotion, return-to-staged, irrelevance marking. Creates frozen
promotion snapshots at decision time. Manages source scrape_weight based
on irrelevance accumulation.

scrape_weight formula: max(0.1, 1.0 - (irrelevance_count * 0.05))
"""
import logging
from datetime import datetime, timezone

from .db import jloads, jdumps
from .operator_state import get_threshold_multiplier

log = logging.getLogger("[RETCON_LEDGER]")

_PROMOTION_BASE_THRESHOLD = 0.5  # baseline before operator multiplier


# ---------------------------------------------------------------------------
# Promotion
# ---------------------------------------------------------------------------

def promote_claim(conn, claim_id: int, analyst_token: str = None,
                  promoting_evidence=None,
                  falsification_predictions=None) -> dict:
    """
    Validate claim is STAGED, create a frozen promotion_snapshot, and
    set trust_level to PROMOTED.

    Raises ValueError if claim is not in STAGED state.
    Returns the updated claim row.
    """
    cur = conn.cursor()
    cur.execute(
        "SELECT id, trust_level, staging_confidence, source_id FROM claims WHERE id=?",
        (claim_id,),
    )
    claim = cur.fetchone()
    if not claim:
        raise ValueError(f"Claim {claim_id} not found")
    if dict(claim)["trust_level"] != "STAGED":
        raise ValueError(
            f"Claim {claim_id} is not STAGED (current: {dict(claim)['trust_level']})"
        )

    # Get source info for snapshot
    cur.execute(
        "SELECT name, source_type, confidence_score FROM sources WHERE id=?",
        (dict(claim)["source_id"],),
    )
    source = cur.fetchone()
    source_name = dict(source)["name"] if source else "unknown"
    source_conf  = float(dict(source)["confidence_score"]) if source else 0.7

    op_multiplier  = get_threshold_multiplier(conn)
    threshold_used = round(_PROMOTION_BASE_THRESHOLD * op_multiplier, 4)
    promotion_conf = float(dict(claim)["staging_confidence"])
    now = datetime.now(timezone.utc).isoformat()

    try:
        # Freeze promotion snapshot
        conn.execute("""
            INSERT INTO promotion_snapshots
                (claim_id, promoted_at, promotion_confidence,
                 source_weights, threshold_at_promotion,
                 promoting_evidence, falsification_predictions)
            VALUES (?,?,?,?,?,?,?)
        """, (
            claim_id,
            now,
            promotion_conf,
            jdumps({source_name: source_conf}),
            threshold_used,
            jdumps(promoting_evidence or []),
            jdumps(falsification_predictions or []),
        ))

        # Promote the claim
        conn.execute(
            "UPDATE claims SET trust_level='PROMOTED' WHERE id=?",
            (claim_id,),
        )
        conn.commit()
        log.info(f"Promoted claim id={claim_id} (conf={promotion_conf:.2f}, threshold={threshold_used:.2f})")
    except Exception as e:
        log.warning(f"promote_claim failed: {e}")
        raise

    return _get_claim(conn, claim_id)


# ---------------------------------------------------------------------------
# Return to staged
# ---------------------------------------------------------------------------

def return_to_staged(conn, claim_id: int, reason: str) -> dict:
    """
    Demote a PROMOTED claim back to STAGED with an explanatory note.
    Returns the updated claim row.
    """
    try:
        conn.execute(
            "UPDATE claims SET trust_level='RETURNED_TO_STAGED' WHERE id=? AND trust_level='PROMOTED'",
            (claim_id,),
        )
        conn.commit()
        # Append reason as a note to the most recent promotion snapshot
        conn.execute("""
            UPDATE promotion_snapshots
            SET promoting_evidence = json_insert(
                COALESCE(promoting_evidence, '[]'),
                '$[#]',
                ?
            )
            WHERE claim_id=?
              AND id = (SELECT MAX(id) FROM promotion_snapshots WHERE claim_id=?)
        """, (f"RETURNED: {reason}", claim_id, claim_id))
        conn.commit()
        log.info(f"Returned claim id={claim_id} to STAGED: {reason}")
        return _get_claim(conn, claim_id)
    except Exception as e:
        log.warning(f"return_to_staged failed: {e}")
        raise


# ---------------------------------------------------------------------------
# Promotion snapshot retrieval
# ---------------------------------------------------------------------------

def get_promotion_snapshot(conn, claim_id: int) -> dict:
    """Return the most recent promotion snapshot for a claim, or {}."""
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM promotion_snapshots WHERE claim_id=? ORDER BY id DESC LIMIT 1",
            (claim_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else {}
    except Exception as e:
        log.warning(f"get_promotion_snapshot failed: {e}")
        return {}


# ---------------------------------------------------------------------------
# List queries
# ---------------------------------------------------------------------------

def get_staged_claims(conn, topic_tag: str = None, limit: int = 50) -> list:
    """Return STAGED claims, optionally filtered by topic tag."""
    try:
        cur = conn.cursor()
        params: list = []
        topic_clause = ""
        if topic_tag:
            topic_clause = "AND EXISTS (SELECT 1 FROM json_each(c.topic_tags) WHERE value=?)"
            params.append(topic_tag)
        params.append(limit)
        cur.execute(f"""
            SELECT c.*, s.name AS source_name, s.cluster
            FROM claims c
            JOIN sources s ON s.id = c.source_id
            WHERE c.trust_level = 'STAGED'
            {topic_clause}
            ORDER BY c.id DESC LIMIT ?
        """, params)
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.warning(f"get_staged_claims failed: {e}")
        return []


def get_promoted_claims(conn, topic_tag: str = None, since: str = None,
                        limit: int = 100) -> list:
    """Return PROMOTED claims, optionally filtered by topic tag and date."""
    try:
        cur = conn.cursor()
        clauses = ["c.trust_level = 'PROMOTED'"]
        params: list = []
        if topic_tag:
            clauses.append("EXISTS (SELECT 1 FROM json_each(c.topic_tags) WHERE value=?)")
            params.append(topic_tag)
        if since:
            clauses.append("c.extracted_at >= ?")
            params.append(since)
        where = "WHERE " + " AND ".join(clauses)
        params.append(limit)
        cur.execute(f"""
            SELECT c.*, s.name AS source_name, s.cluster
            FROM claims c
            JOIN sources s ON s.id = c.source_id
            {where}
            ORDER BY c.id DESC LIMIT ?
        """, params)
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.warning(f"get_promoted_claims failed: {e}")
        return []


# ---------------------------------------------------------------------------
# Mark irrelevant
# ---------------------------------------------------------------------------

def mark_irrelevant(conn, claim_id: int, reason: str) -> dict:
    """
    Set trust_level=IRRELEVANT and increment source.irrelevance_count.
    Recompute scrape_weight: max(0.1, 1.0 - (irrelevance_count * 0.05)).
    Returns the updated claim row.
    """
    try:
        cur = conn.cursor()
        cur.execute("SELECT source_id FROM claims WHERE id=?", (claim_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Claim {claim_id} not found")
        source_id = dict(row)["source_id"]

        # Mark irrelevant
        conn.execute(
            "UPDATE claims SET trust_level='IRRELEVANT' WHERE id=?",
            (claim_id,),
        )

        # Increment irrelevance count and recompute weight
        conn.execute(
            "UPDATE sources SET irrelevance_count = irrelevance_count + 1 WHERE id=?",
            (source_id,),
        )
        cur.execute("SELECT irrelevance_count FROM sources WHERE id=?", (source_id,))
        src_row = cur.fetchone()
        new_count = int(dict(src_row)["irrelevance_count"]) if src_row else 1
        new_weight = max(0.1, 1.0 - (new_count * 0.05))

        conn.execute(
            "UPDATE sources SET scrape_weight=? WHERE id=?",
            (round(new_weight, 4), source_id),
        )
        conn.commit()
        log.info(
            f"Marked claim {claim_id} irrelevant. Source {source_id}: "
            f"irrelevance_count={new_count}, scrape_weight={new_weight:.2f}"
        )
        return _get_claim(conn, claim_id)
    except Exception as e:
        log.warning(f"mark_irrelevant failed: {e}")
        raise


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_claim(conn, claim_id: int) -> dict:
    cur = conn.cursor()
    cur.execute("SELECT * FROM claims WHERE id=?", (claim_id,))
    row = cur.fetchone()
    return dict(row) if row else {}
