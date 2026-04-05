"""
contamination_cascade.py — Trust remediation when a source is compromised.

Port of V1 contamination_cascade.py from PostgreSQL/psycopg2 to SQLite.
Called when a source's confidence_score drops catastrophically. Traces
downstream contamination through the promotion snapshot ledger.

Tier thresholds (from CDS v2 spec):
  SOLE_CORROBORATOR       >= 0.80  immediate return, no analyst needed
  DECISIVE_CONTRIBUTION   >= 0.50  urgent flag, operator decides
  PARTIAL                  < 0.50  confidence haircut, flag for review

Redemption path: if >= 2 falsification predictions were confirmed through
sources independently of the compromised source, the claim's corroboration
path was contaminated but the claim itself survived. Re-promote with
adjusted confidence stripping the compromised source's weight.
"""
import logging
import uuid
from typing import Optional

from .db import jloads, jdumps
from .audit import log_event

log = logging.getLogger("[CASCADE]")

# Tier thresholds
SOLE_CORROBORATOR_THRESHOLD       = 0.80
DECISIVE_CONTRIBUTION_THRESHOLD   = 0.50
INDEPENDENT_CONFIRMATION_THRESHOLD = 2

PREDICTION_CONFIRMATION_BOOST     = 0.05
PREDICTION_CONFIRMATION_BOOST_CAP = 0.15


# ---------------------------------------------------------------------------
# Main entry points
# ---------------------------------------------------------------------------

def run_cascade(conn, source_id: int) -> dict:
    """
    Run the contamination cascade for a compromised source.

    Traces all PROMOTED claims where this source contributed at promotion time.
    Returns a contamination report dict with four tiers:
      survived, returned_to_staged, urgent, review_flag
    """
    session_id = str(uuid.uuid4())

    cur = conn.cursor()
    cur.execute("SELECT id, name, confidence_score FROM sources WHERE id=?", (source_id,))
    source = cur.fetchone()
    if not source:
        raise ValueError(f"Source {source_id} not found")
    source = dict(source)
    original_trust = float(source["confidence_score"])

    log.info(f"Cascade started for source id={source_id} ({source['name']}), "
             f"trust={original_trust:.3f}")

    contaminated = _get_claims_with_source_contribution(conn, source_id)

    report = {
        "source_id":         source_id,
        "source_name":       source["name"],
        "original_trust":    original_trust,
        "survived":          [],
        "returned_to_staged": [],
        "urgent":            [],
        "review_flag":       [],
    }

    for claim in contaminated:
        snapshot    = claim["snapshot"]
        sw          = jloads(snapshot.get("source_weights"), {})
        source_load = float(sw.get(str(source_id), sw.get(source_id, 0.0)))

        if source_load == 0.0:
            continue

        preds = jloads(snapshot.get("falsification_predictions"), [])
        independent_confirmations = _count_independent_confirmations(
            conn, preds, source_id
        )

        if independent_confirmations >= INDEPENDENT_CONFIRMATION_THRESHOLD:
            _handle_survived(conn, claim, snapshot, source_id, source["name"],
                             independent_confirmations, session_id, report)
        elif source_load >= SOLE_CORROBORATOR_THRESHOLD:
            _handle_sole_corroborator(conn, claim, source_id, source["name"],
                                      source_load, session_id, report)
        elif source_load >= DECISIVE_CONTRIBUTION_THRESHOLD:
            _handle_decisive(conn, claim, source_id, source["name"],
                             source_load, session_id, report)
        else:
            _handle_partial(conn, claim, source_id, source["name"],
                            source_load, original_trust, session_id, report)

    report["total_affected"] = (
        len(report["survived"])
        + len(report["returned_to_staged"])
        + len(report["urgent"])
        + len(report["review_flag"])
    )

    log_event(
        conn,
        session_id=session_id,
        event_type="cascade_complete",
        actor="cascade",
        action=(
            f"Cascade complete for source {source_id} ({source['name']}): "
            f"{report['total_affected']} claims affected"
        ),
        data_accessed={
            "source_id":        source_id,
            "original_trust":   original_trust,
            "survived":         len(report["survived"]),
            "returned_to_staged": len(report["returned_to_staged"]),
            "urgent":           len(report["urgent"]),
            "review_flag":      len(report["review_flag"]),
        },
    )

    log.info(
        f"Cascade complete: survived={len(report['survived'])} "
        f"returned={len(report['returned_to_staged'])} "
        f"urgent={len(report['urgent'])} "
        f"review={len(report['review_flag'])}"
    )
    return report


def get_cascade_report(conn, source_id: int) -> dict:
    """
    Return a summary of claims that would be affected if this source were compromised,
    without actually executing the cascade. Useful for pre-flight analysis.
    """
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, confidence_score FROM sources WHERE id=?", (source_id,))
        source = cur.fetchone()
        if not source:
            return {"error": f"Source {source_id} not found"}
        source = dict(source)

        contaminated = _get_claims_with_source_contribution(conn, source_id)

        tiers = {"would_survive": 0, "would_return": 0, "would_urgent": 0, "would_review": 0}
        affected_claims = []

        for claim in contaminated:
            snapshot = claim["snapshot"]
            sw = jloads(snapshot.get("source_weights"), {})
            source_load = float(sw.get(str(source_id), sw.get(source_id, 0.0)))
            if source_load == 0.0:
                continue
            preds = jloads(snapshot.get("falsification_predictions"), [])
            ic = _count_independent_confirmations(conn, preds, source_id)
            if ic >= INDEPENDENT_CONFIRMATION_THRESHOLD:
                tiers["would_survive"] += 1
                tier = "survive"
            elif source_load >= SOLE_CORROBORATOR_THRESHOLD:
                tiers["would_return"] += 1
                tier = "return"
            elif source_load >= DECISIVE_CONTRIBUTION_THRESHOLD:
                tiers["would_urgent"] += 1
                tier = "urgent"
            else:
                tiers["would_review"] += 1
                tier = "review"
            affected_claims.append({
                "claim_id":    claim["id"],
                "claim_text":  claim["claim_text"][:120],
                "source_load": round(source_load, 4),
                "tier":        tier,
            })

        return {
            "source_id":       source_id,
            "source_name":     source["name"],
            "current_trust":   float(source["confidence_score"]),
            "affected_claims": affected_claims,
            "tiers":           tiers,
            "total_affected":  len(affected_claims),
        }
    except Exception as e:
        log.warning(f"get_cascade_report failed: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Tier handlers
# ---------------------------------------------------------------------------

def _handle_survived(conn, claim, snapshot, source_id, source_name,
                     independently_confirmed, session_id, report):
    adjusted = _adjusted_confidence_without_source(snapshot, source_id, independently_confirmed)
    # Return to staged first, then re-promote with adjusted confidence
    conn.execute(
        "UPDATE claims SET trust_level='RETURNED_TO_STAGED' WHERE id=? AND trust_level='PROMOTED'",
        (claim["id"],),
    )
    conn.execute("""
        INSERT INTO promotion_snapshots
            (claim_id, promotion_confidence, source_weights, threshold_at_promotion,
             promoting_evidence)
        VALUES (?,?,?,?,?)
    """, (
        claim["id"],
        adjusted["confidence"],
        jdumps(adjusted["source_weights"]),
        float(snapshot.get("threshold_at_promotion", 0.6)),
        jdumps([f"Re-promoted: {independently_confirmed} predictions confirmed independently of {source_name}"]),
    ))
    conn.execute(
        "UPDATE claims SET trust_level='PROMOTED' WHERE id=?",
        (claim["id"],),
    )
    conn.commit()

    log_event(conn, session_id=session_id, event_type="cascade_survived",
              actor="cascade",
              action=f"Claim {claim['id']} survived cascade: {independently_confirmed} independent confirmations",
              data_accessed={"claim_id": claim["id"], "adjusted_confidence": adjusted["confidence"]},
              trust_level="PROMOTED")

    report["survived"].append({
        "claim_id":               claim["id"],
        "adjusted_confidence":    adjusted["confidence"],
        "independent_confirmations": independently_confirmed,
    })
    log.info(f"Claim {claim['id']} survived: re-promoted at {adjusted['confidence']:.3f}")


def _handle_sole_corroborator(conn, claim, source_id, source_name,
                              source_load, session_id, report):
    conn.execute(
        "UPDATE claims SET trust_level='RETURNED_TO_STAGED' WHERE id=? AND trust_level='PROMOTED'",
        (claim["id"],),
    )
    conn.commit()

    log_event(conn, session_id=session_id, event_type="cascade_return",
              actor="cascade",
              action=f"Claim {claim['id']} returned: sole corroborator {source_name} compromised",
              data_accessed={"claim_id": claim["id"], "source_load": source_load},
              trust_level="RETURNED_TO_STAGED")

    report["returned_to_staged"].append({
        "claim_id":    claim["id"],
        "source_load": round(source_load, 4),
    })
    log.info(f"Claim {claim['id']} → RETURNED_TO_STAGED (sole corroborator, load={source_load:.2f})")


def _handle_decisive(conn, claim, source_id, source_name,
                     source_load, session_id, report):
    log_event(conn, session_id=session_id, event_type="cascade_urgent_flag",
              actor="cascade",
              action=f"Claim {claim['id']} URGENT: decisive corroborator {source_name} compromised",
              data_accessed={"claim_id": claim["id"], "source_load": source_load},
              trust_level="PROMOTED")

    report["urgent"].append({
        "claim_id":    claim["id"],
        "source_load": round(source_load, 4),
    })
    log.info(f"Claim {claim['id']} URGENT FLAG (decisive {source_name}, load={source_load:.2f})")


def _handle_partial(conn, claim, source_id, source_name,
                    source_load, original_trust, session_id, report):
    delta = -(source_load * original_trust)
    conn.execute(
        "UPDATE claims SET staging_confidence = MAX(0.0, staging_confidence + ?) WHERE id=?",
        (delta, claim["id"]),
    )
    conn.commit()

    log_event(conn, session_id=session_id, event_type="cascade_confidence_haircut",
              actor="cascade",
              action=f"Claim {claim['id']} haircut {delta:.3f} (partial corroborator {source_name})",
              data_accessed={"claim_id": claim["id"], "confidence_delta": delta},
              trust_level="PROMOTED")

    report["review_flag"].append({
        "claim_id":         claim["id"],
        "source_load":      round(source_load, 4),
        "confidence_delta": round(delta, 4),
    })
    log.info(f"Claim {claim['id']} haircut {delta:.3f} (partial {source_name})")


# ---------------------------------------------------------------------------
# Independence verification
# ---------------------------------------------------------------------------

def _verify_independence(conn, confirming_source_id: int, compromised_source_id: int) -> bool:
    """
    Returns True only if the confirming source is genuinely independent.
    Checks: not the same source, no direct amplification edge, not in same cluster.
    Conservative: returns False on any ambiguity.
    """
    if confirming_source_id == compromised_source_id:
        return False
    try:
        cur = conn.cursor()
        # Check for any direct amplification edge in either direction
        cur.execute("""
            SELECT 1 FROM source_network_edges
            WHERE relationship_type = 'amplifies'
              AND (
                (source_id=? AND connected_source_id=?)
                OR
                (source_id=? AND connected_source_id=?)
              )
            LIMIT 1
        """, (confirming_source_id, compromised_source_id,
              compromised_source_id, confirming_source_id))
        if cur.fetchone():
            return False
        # Check same cluster
        cur.execute(
            "SELECT cluster FROM sources WHERE id IN (?,?)",
            (confirming_source_id, compromised_source_id),
        )
        rows = [dict(r) for r in cur.fetchall()]
        if len(rows) == 2 and rows[0]["cluster"] == rows[1]["cluster"]:
            return False
        return True
    except Exception:
        return False  # conservative


def _count_independent_confirmations(conn, predictions: list, compromised_source_id: int) -> int:
    """Count predictions confirmed by sources independent of the compromised source."""
    count = 0
    for pred in predictions:
        if not isinstance(pred, dict):
            continue
        confirmed_by = pred.get("confirmed_by")
        if confirmed_by is None:
            continue
        try:
            confirming_id = int(str(confirmed_by).strip())
        except (ValueError, TypeError):
            continue
        if _verify_independence(conn, confirming_id, compromised_source_id):
            count += 1
    return count


# ---------------------------------------------------------------------------
# Confidence adjustment
# ---------------------------------------------------------------------------

def _adjusted_confidence_without_source(snapshot: dict, compromised_source_id: int,
                                        independently_confirmed: int) -> dict:
    """Recalculate promotion confidence after stripping the compromised source."""
    sw = jloads(snapshot.get("source_weights"), {})
    weights = {k: float(v) for k, v in sw.items()}
    compromised_load = float(weights.pop(str(compromised_source_id),
                                         weights.pop(compromised_source_id, 0.0)))
    total = sum(weights.values())
    if total > 0:
        weights = {k: round(v / total, 6) for k, v in weights.items()}
    remaining_fraction = 1.0 - compromised_load
    base = float(snapshot.get("promotion_confidence", 0.5)) * remaining_fraction
    boost = min(independently_confirmed * PREDICTION_CONFIRMATION_BOOST,
                PREDICTION_CONFIRMATION_BOOST_CAP)
    adjusted = min(0.99, base + boost)
    return {
        "confidence":     round(adjusted, 4),
        "source_weights": weights,
    }


# ---------------------------------------------------------------------------
# DB query: find PROMOTED claims where source appears in source_weights
# ---------------------------------------------------------------------------

def _get_claims_with_source_contribution(conn, source_id: int) -> list:
    """
    Find all PROMOTED claims where source_id appears as a key in
    promotion_snapshots.source_weights (stored as JSON TEXT).
    SQLite has no native JSON-key operator — use LIKE as a fast pre-filter
    and parse in Python to confirm.
    """
    cur = conn.cursor()
    # Use LIKE to pre-filter rows that contain the source_id string,
    # then confirm in Python after JSON parsing to avoid false positives.
    key_fragment = f'"{source_id}"'
    alt_fragment = f"'{source_id}'"  # unlikely but defensive
    cur.execute("""
        SELECT
            c.id, c.claim_text, c.trust_level,
            ps.id AS snapshot_id,
            ps.source_weights,
            ps.promotion_confidence,
            ps.threshold_at_promotion,
            ps.falsification_predictions,
            ps.promoting_evidence,
            ps.promoted_at
        FROM claims c
        JOIN promotion_snapshots ps ON ps.claim_id = c.id
        WHERE c.trust_level = 'PROMOTED'
          AND (ps.source_weights LIKE ? OR ps.source_weights LIKE ?)
        ORDER BY ps.promoted_at DESC
    """, (f"%{key_fragment}%", f"%{alt_fragment}%"))

    rows = cur.fetchall()
    result = []
    seen = set()
    for row in rows:
        row = dict(row)
        claim_id = row["id"]
        if claim_id in seen:
            continue
        # Python-side confirmation
        sw = jloads(row.get("source_weights"), {})
        if str(source_id) not in sw and source_id not in sw:
            continue
        seen.add(claim_id)
        result.append({
            "id":         claim_id,
            "claim_text": row["claim_text"],
            "trust_level": row["trust_level"],
            "snapshot": {
                "id":                        row["snapshot_id"],
                "source_weights":            row["source_weights"],
                "promotion_confidence":      row["promotion_confidence"],
                "threshold_at_promotion":    row["threshold_at_promotion"],
                "falsification_predictions": row["falsification_predictions"],
                "promoting_evidence":        row["promoting_evidence"],
            },
        })
    return result
