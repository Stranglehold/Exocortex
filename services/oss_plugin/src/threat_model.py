"""
threat_model.py — Living adversary technique model.

Records observed manipulation techniques, tracks frequency and recency,
detects when techniques are abandoned, and surfaces adaptation patterns.
"""
import logging
from datetime import datetime, timezone

from .db import jloads, jdumps

log = logging.getLogger("[THREAT_MODEL]")


# ---------------------------------------------------------------------------
# Record / upsert
# ---------------------------------------------------------------------------

def record_technique(conn, technique_name: str, technique_class: str) -> dict:
    """
    Upsert a technique record:
      - If exists: increment observed_count, update last_observed.
      - If new: insert with observed_count=1.
    Returns the row after upsert.
    """
    try:
        now = datetime.now(timezone.utc).isoformat()
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM threat_model WHERE technique_name=?",
            (technique_name,),
        )
        existing = cur.fetchone()

        if existing:
            conn.execute("""
                UPDATE threat_model
                SET observed_count = observed_count + 1,
                    last_observed  = ?,
                    detected_by_system = detected_by_system + 1
                WHERE technique_name=?
            """, (now, technique_name))
        else:
            conn.execute("""
                INSERT INTO threat_model
                    (technique_name, technique_class, first_observed, last_observed,
                     observed_count, detected_by_system)
                VALUES (?,?,?,?,1,1)
            """, (technique_name, technique_class, now, now))

        conn.commit()
        cur.execute("SELECT * FROM threat_model WHERE technique_name=?", (technique_name,))
        row = cur.fetchone()
        return dict(row) if row else {}
    except Exception as e:
        log.warning(f"record_technique failed for '{technique_name}': {e}")
        raise


# ---------------------------------------------------------------------------
# Mark abandoned
# ---------------------------------------------------------------------------

def mark_abandoned(conn, technique_name: str,
                   predicted_adaptation: str = None) -> dict:
    """
    Flag a technique as abandoned by the adversary.
    Optionally record a predicted next adaptation.
    Returns the updated row.
    """
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute("""
            UPDATE threat_model
            SET adversary_abandoned   = 1,
                abandoned_at          = ?,
                predicted_adaptation  = ?
            WHERE technique_name=?
        """, (now, predicted_adaptation, technique_name))
        conn.commit()
        log.info(f"Marked technique '{technique_name}' as abandoned")
        cur = conn.cursor()
        cur.execute("SELECT * FROM threat_model WHERE technique_name=?", (technique_name,))
        row = cur.fetchone()
        return dict(row) if row else {}
    except Exception as e:
        log.warning(f"mark_abandoned failed for '{technique_name}': {e}")
        raise


# ---------------------------------------------------------------------------
# Get full model
# ---------------------------------------------------------------------------

def get_threat_model(conn) -> list:
    """Return all technique records, ordered by observed_count desc."""
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM threat_model ORDER BY observed_count DESC"
        )
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.warning(f"get_threat_model failed: {e}")
        return []


# ---------------------------------------------------------------------------
# Trend analysis
# ---------------------------------------------------------------------------

def get_trend(conn, technique_class: str = None) -> dict:
    """
    Return trend analysis:
      techniques         — all matching technique rows
      abandonment_rate   — fraction of techniques marked abandoned
      adaptation_patterns — list of {from_technique, predicted_adaptation} for abandoned ones

    Optionally filter by technique_class.
    """
    try:
        cur = conn.cursor()
        params: list = []
        class_clause = ""
        if technique_class:
            class_clause = "WHERE technique_class=?"
            params.append(technique_class)

        cur.execute(
            f"SELECT * FROM threat_model {class_clause} ORDER BY observed_count DESC",
            params,
        )
        techniques = [dict(r) for r in cur.fetchall()]

        if not techniques:
            return {
                "techniques": [],
                "abandonment_rate": 0.0,
                "adaptation_patterns": [],
            }

        abandoned = [t for t in techniques if t.get("adversary_abandoned")]
        abandonment_rate = round(len(abandoned) / len(techniques), 4)

        adaptation_patterns = [
            {
                "from_technique": t["technique_name"],
                "predicted_adaptation": t.get("predicted_adaptation"),
                "abandoned_at": t.get("abandoned_at"),
                "observed_count": t.get("observed_count", 0),
            }
            for t in abandoned
            if t.get("predicted_adaptation")
        ]

        return {
            "techniques": techniques,
            "abandonment_rate": abandonment_rate,
            "adaptation_patterns": adaptation_patterns,
        }
    except Exception as e:
        log.warning(f"get_trend failed: {e}")
        return {
            "techniques": [],
            "abandonment_rate": 0.0,
            "adaptation_patterns": [],
        }
