"""Phase 2 — reality-feedback resolution engine.
INTELLIGENCE_LOOP_BUILDPLAN_L3 (Decision 1b: web-verify reality at deadline).

The A0 RESOLVE cycle web-verifies each falsification condition against reality
(it has the web tools); this engine *consumes* those verdicts and applies a
deterministic resolution rule, then closes the calibration loop:

  - any condition OCCURRED            -> baseline FALSIFIED (was_correct=False)
  - all conditions NOT_OCCURRED       -> baseline PROMOTED  (was_correct=True)
  - some AMBIGUOUS (none occurred)    -> ESCALATE to operator (leave ACTIVE)
  - not all conditions verdicted yet  -> PARTIAL (leave ACTIVE, re-check later)

Reuses hypothesis.falsify_hypothesis / promote_hypothesis and fires the SWARMFISH
V2 outcome endpoint (Brier calibration) exactly as app.py does. Deterministic by
design — the only judgment input is the per-condition reality verdict.
"""
import os
import json
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras

import hypothesis

log = logging.getLogger("ingest")

DB_URL     = os.environ.get("OSS_DB_URL",
                            "postgresql://oss_admin:oss_admin_dev_password@localhost:5433/oss")
_SF_V2_URL = os.environ.get("SWARMFISH_V2_URL", "")
_SF_V2_KEY = os.environ.get("SWARMFISH_V2_API_KEY", "")

VERDICT_OCCURRED  = "occurred"
VERDICT_NOT       = "not_occurred"
VERDICT_AMBIGUOUS = "ambiguous"


def get_conn():
    return psycopg2.connect(DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def get_due_hypotheses(as_of: str = None) -> list:
    """ACTIVE hypotheses with >=1 unresolved prediction whose deadline is
    on/before `as_of` (default today UTC). These are what the RESOLVE cycle
    must web-verify."""
    cutoff = as_of or datetime.now(timezone.utc).date().isoformat()
    due = []
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, observation_label, current_confidence, swarmfish_session_id, "
                "predictions_generated FROM hypothesis_registry WHERE status='ACTIVE'"
            )
            rows = cur.fetchall()
    for r in rows:
        preds = r["predictions_generated"] or []
        unresolved_due = [
            p for p in preds
            if isinstance(p, dict) and not p.get("resolved")
            and p.get("deadline") and str(p["deadline"]) <= cutoff
            and p.get("falsifiable_by")
        ]
        if unresolved_due:
            due.append({
                "hypothesis_id":        r["id"],
                "label":                r["observation_label"],
                "confidence":           r["current_confidence"],
                "swarmfish_session_id": r["swarmfish_session_id"],
                "conditions":           [p["falsifiable_by"] for p in unresolved_due],
            })
    return due


def _fire_swarmfish_outcome(session_id, was_correct: bool, notes: str) -> bool:
    """Fire SWARMFISH V2 outcome -> Brier calibration. Mirrors app.py
    _swarmfish_request('/acp/outcome') V2 translation: {session_id, outcome:
    1.0|0.0, notes}."""
    if not session_id or not _SF_V2_URL:
        return False
    body = {
        "session_id": str(session_id),
        "outcome":    1.0 if was_correct else 0.0,
        "notes":      str(notes)[:500],
    }
    url = f"{_SF_V2_URL}/api/plugins/swarmfish/api_swarmfish_outcome"
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type": "application/json", "X-API-KEY": _SF_V2_KEY},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            json.loads(resp.read().decode())
        log.info(f"[RESOLVE] swarmfish_outcome posted (correct={was_correct}, session={session_id})")
        return True
    except Exception as e:
        log.warning(f"[RESOLVE] swarmfish_outcome callout failed (session={session_id}): {e}")
        return False


def apply_resolution(hypothesis_id: int, verdicts: dict, session_id=None) -> dict:
    """Apply reality verdicts to one hypothesis.

    verdicts: {falsification_condition (str) -> 'occurred'|'not_occurred'|'ambiguous'}
    Returns {hypothesis_id, decision, occurred, not_occurred, ambiguous, ...}.
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, status, swarmfish_session_id, predictions_generated, "
                "observation_label FROM hypothesis_registry WHERE id=%s",
                (hypothesis_id,),
            )
            hyp = cur.fetchone()
    if not hyp:
        raise ValueError(f"Hypothesis {hypothesis_id} not found")
    if hyp["status"] != "ACTIVE":
        return {"hypothesis_id": hypothesis_id, "decision": "skipped",
                "reason": f"status={hyp['status']} (terminal)"}

    preds = hyp["predictions_generated"] or []
    occurred, not_occurred, ambiguous = [], [], []
    total_conditions = 0
    verdicted = 0
    for p in preds:
        if not isinstance(p, dict) or not p.get("falsifiable_by"):
            continue
        total_conditions += 1
        cond = p["falsifiable_by"]
        v = verdicts.get(cond)
        if v is None:
            continue  # not web-verified yet — leave for a later RESOLVE pass
        verdicted += 1
        p["verdict"] = v
        if v == VERDICT_OCCURRED:
            p["resolved"] = True; p["outcome"] = "falsified"; occurred.append(cond)
        elif v == VERDICT_NOT:
            p["resolved"] = True; p["outcome"] = "held"; not_occurred.append(cond)
        else:
            p["resolved"] = True; p["outcome"] = "ambiguous"; ambiguous.append(cond)

    sf_sid = hyp.get("swarmfish_session_id")
    n_conf, n_fals = len(not_occurred), len(occurred)

    # --- deterministic decision rule ---
    if occurred:
        evidence = ("Baseline falsified — disconfirming event(s) occurred by deadline: "
                    + "; ".join(occurred))
        hypothesis.falsify_hypothesis(hypothesis_id, evidence, session_id=session_id)
        _fire_swarmfish_outcome(sf_sid, was_correct=False, notes=evidence)
        decision = "FALSIFIED"
    elif verdicted < total_conditions:
        decision = "PARTIAL"  # some conditions not yet web-verified; re-check later
    elif ambiguous:
        decision = "ESCALATED"  # all verdicted, none occurred, but some ambiguous
        log.warning(f"[RESOLVE][ESCALATE] Hypothesis #{hypothesis_id} "
                    f"({hyp['observation_label']}) has ambiguous conditions — operator review: "
                    + "; ".join(ambiguous))
    else:
        hypothesis.promote_hypothesis(hypothesis_id, session_id=session_id)
        _fire_swarmfish_outcome(sf_sid, was_correct=True,
                                notes="Baseline held — no disconfirming events by deadline.")
        decision = "PROMOTED"

    # bookkeeping (separate txn from falsify/promote; distinct columns)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE hypothesis_registry SET predictions_generated=%s, "
                "predictions_confirmed=%s, predictions_falsified=%s, "
                "last_prediction_check=NOW() WHERE id=%s",
                (psycopg2.extras.Json(preds), n_conf, n_fals, hypothesis_id),
            )

    log.info(f"[RESOLVE] #{hypothesis_id} ({hyp['observation_label']}) -> {decision} "
             f"(occurred={n_fals}, held={n_conf}, ambiguous={len(ambiguous)}, "
             f"verdicted={verdicted}/{total_conditions})")
    return {
        "hypothesis_id": hypothesis_id, "decision": decision,
        "occurred": occurred, "not_occurred": not_occurred, "ambiguous": ambiguous,
        "verdicted": verdicted, "total_conditions": total_conditions,
        "swarmfish_outcome_fired": bool(sf_sid and _SF_V2_URL
                                        and decision in ("FALSIFIED", "PROMOTED")),
    }
