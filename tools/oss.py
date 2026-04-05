"""
oss.py — OSS V2 (Office of Strategic Services) Agent Zero tools.

V2 rewrite: uses direct plugin imports instead of HTTP calls to localhost:7731.
Plugin path: /a0/usr/plugins/oss

Available tools:
  oss_topic          — query claims for a topic from the ledger
  oss_drift          — detect narrative framing shift for a topic
  oss_dynamics       — propagation velocity, alert level, time-to-escape
  oss_hypotheses     — list/register/confirm/falsify/promote competing hypotheses
  oss_health         — system operational health report
  oss_submit         — log a new claim directly to the ledger (analyst dictation)
  oss_list_topics    — list all monitored topics with claim counts
  oss_add_topic      — register a new topic tag for the ingestion pipeline
  oss_ingest_pause   — pause the automated RSS ingestion pipeline
  oss_ingest_resume  — resume the automated RSS ingestion pipeline
  oss_question       — manage analyst active questions (create/evolve/list/deactivate)
  oss_synthesize     — ask the ledger a question; receive evidence-based synthesis

The analyst holds the conclusions. The system provides the record.
"""

import json
import os
import sys

from helpers.tool import Tool, Response

# ---------------------------------------------------------------------------
# Plugin import helpers
# ---------------------------------------------------------------------------

PLUGIN_PATH = os.environ.get("OSS_PLUGIN_PATH", "/a0/usr/plugins/oss")


def _ensure_plugin() -> None:
    """Add plugin src to sys.path if not already present."""
    if PLUGIN_PATH not in sys.path:
        sys.path.insert(0, PLUGIN_PATH)


def _get_conn():
    _ensure_plugin()
    from src.db import get_conn, init_db
    conn = get_conn()
    init_db(conn)
    return conn


def _jloads(s, default=None):
    _ensure_plugin()
    from src.db import jloads
    return jloads(s, default)


def _oss_error(prefix: str, e: Exception) -> Response:
    return Response(
        message=f"[OSS] {prefix}: {e}",
        break_loop=False,
    )


# ---------------------------------------------------------------------------
# OssTopic
# ---------------------------------------------------------------------------

class OssTopic(Tool):
    """
    Query claims about a topic from the OSS intelligence ledger.

    Args:
        topic      (str):  Topic tag to query (e.g. 'iran-hormuz', 'taiwan-strait') [required]
        limit      (int):  Max claims to return (default 50)
        trust_level (str): Filter to STAGED / PROMOTED / FALSIFIED / RETURNED_TO_STAGED / IRRELEVANT
    """

    async def execute(self, **kwargs) -> Response:
        topic       = (self.args.get("topic") or "").strip()
        limit       = int(self.args.get("limit") or 50)
        trust_level = (self.args.get("trust_level") or "").strip().upper() or None
        print(f"[OSS] oss_topic: topic={topic!r} limit={limit} trust_level={trust_level}", flush=True)

        if not topic:
            return Response(message="[OSS] Error: topic argument required", break_loop=False)

        try:
            conn = _get_conn()
            cur  = conn.cursor()

            sql    = "SELECT c.*, s.name AS source_name FROM claims c JOIN sources s ON s.id=c.source_id WHERE ? IN (c.topic_tags, '') AND c.topic_tags LIKE ?"
            params = [topic, f"%{topic}%"]

            if trust_level:
                sql    = "SELECT c.*, s.name AS source_name FROM claims c JOIN sources s ON s.id=c.source_id WHERE c.topic_tags LIKE ? AND c.trust_level=? ORDER BY c.extracted_at DESC LIMIT ?"
                params = [f"%{topic}%", trust_level, limit]
            else:
                sql    = "SELECT c.*, s.name AS source_name FROM claims c JOIN sources s ON s.id=c.source_id WHERE c.topic_tags LIKE ? ORDER BY c.extracted_at DESC LIMIT ?"
                params = [f"%{topic}%", limit]

            cur.execute(sql, params)
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
        except Exception as e:
            return _oss_error("oss_topic query failed", e)

        if not rows:
            return Response(
                message=f"OSS Intelligence Ledger — no claims found for topic '{topic}'",
                break_loop=False,
            )

        trust_order = {"PROMOTED": 0, "STAGED": 1, "RETURNED_TO_STAGED": 2, "IRRELEVANT": 3, "FALSIFIED": 4}
        rows.sort(key=lambda c: trust_order.get(c.get("trust_level", ""), 9))

        lines = [f"OSS Intelligence Ledger — {len(rows)} claim(s) for '{topic}'\n"]
        for c in rows[:15]:
            trust  = c.get("trust_level", "?")
            text   = (c.get("claim_text") or "")[:160]
            source = c.get("source_name", "?")
            tech   = c.get("technique_class") or "none"
            conf   = c.get("staging_confidence")
            conf_s = f", conf={conf:.2f}" if conf is not None else ""
            lines.append(f"[{trust}] {text}")
            lines.append(f"  Source: {source} | technique: {tech}{conf_s}\n")

        if len(rows) > 15:
            lines.append(f"… and {len(rows) - 15} additional claims (use trust_level filter to narrow).")

        return Response(message="\n".join(lines), break_loop=False)


# ---------------------------------------------------------------------------
# OssDrift
# ---------------------------------------------------------------------------

class OssDrift(Tool):
    """
    Detect narrative framing drift for a topic.

    Compares current window vs prior window for technique shifts, cluster
    shifts, salience changes, and volume changes.

    Args:
        topic        (str): Topic tag to analyze [required]
        window_hours (int): Window length in hours (default 24)
    """

    async def execute(self, **kwargs) -> Response:
        topic        = (self.args.get("topic") or "").strip()
        window_hours = int(self.args.get("window_hours") or 24)
        print(f"[OSS] oss_drift: topic={topic!r} window={window_hours}h", flush=True)

        if not topic:
            return Response(message="[OSS] Error: topic argument required", break_loop=False)

        try:
            _ensure_plugin()
            from src.narrative_drift import detect_drift
            conn   = _get_conn()
            result = detect_drift(conn, topic, window_hours=window_hours)
            conn.close()
        except Exception as e:
            return _oss_error("oss_drift failed", e)

        signals        = result.get("signals", {})
        drift_detected = any(s.get("detected") for s in signals.values()) if signals else result.get("drifted", False)
        drift_score    = result.get("drift_score", 0.0)
        dominant       = result.get("dominant_signal", "none")

        status = "DRIFT DETECTED" if drift_detected else "Stable"
        lines  = [
            f"OSS Narrative Drift — '{topic}'",
            f"Status: {status} (score={drift_score:.3f}, dominant={dominant})",
        ]

        cur_window = result.get("current_window", {})
        pri_window = result.get("prior_window", {})
        if cur_window or pri_window:
            lines.append(
                f"Current window: {cur_window.get('claim_count', '?')} claims | "
                f"Prior window: {pri_window.get('claim_count', '?')} claims"
            )
        lines.append("")

        for name, sig in signals.items():
            mag = sig.get("delta", sig.get("magnitude", 0.0))
            if mag > 0.05:
                desc   = sig.get("description", "")
                detail = f"  {desc}" if desc else ""
                lines.append(f"  {name}: delta={mag:.3f}{detail}")

        if not any(s.get("delta", s.get("magnitude", 0)) > 0.05 for s in signals.values()):
            lines.append("  No significant shifts detected in this window.")

        return Response(message="\n".join(lines), break_loop=False)


# ---------------------------------------------------------------------------
# OssDynamics
# ---------------------------------------------------------------------------

class OssDynamics(Tool):
    """
    Compute propagation dynamics for a topic.

    Returns velocity (unique sources/hour), acceleration, cluster coverage,
    time until correction becomes impractical, and alert level.

    Alert levels:
      INFORMATIONAL — baseline monitoring
      WARNING       — spreading faster than expected
      URGENT        — time to escape velocity < 24h

    Args:
        topic        (str): Topic tag to analyze [required]
        window_hours (int): Velocity measurement window (default 24)
    """

    async def execute(self, **kwargs) -> Response:
        topic        = (self.args.get("topic") or "").strip()
        window_hours = int(self.args.get("window_hours") or 24)
        print(f"[OSS] oss_dynamics: topic={topic!r}", flush=True)

        if not topic:
            return Response(message="[OSS] Error: topic argument required", break_loop=False)

        try:
            _ensure_plugin()
            from src.propagation_dynamics import compute_dynamics
            conn   = _get_conn()
            result = compute_dynamics(conn, topic, window_hours=window_hours)
            conn.close()
        except Exception as e:
            return _oss_error("oss_dynamics failed", e)

        alert    = result.get("alert_level", "?")
        velocity = result.get("propagation_velocity", 0.0)
        accel    = result.get("acceleration", 0.0)
        coverage = result.get("cluster_coverage_pct", 0.0)
        t_escape = result.get("time_to_escape_velocity_hours")
        half     = result.get("half_life_hours")

        t_escape_str = f"{t_escape:.1f}h" if t_escape is not None else "N/A (not accelerating)"
        half_str     = f"{half:.1f}h"     if half      is not None else "insufficient falsified claims"

        lines = [
            f"OSS Propagation Dynamics — '{topic}'",
            f"Alert:            {alert}",
            f"Velocity:         {velocity:.4f} sources/h",
            f"Acceleration:     {accel:.6f} sources/h²",
            f"Cluster coverage: {coverage:.0%}",
            f"Time to escape:   {t_escape_str}",
            f"Half-life proxy:  {half_str}",
        ]

        cur = result.get("current_window", {})
        pri = result.get("prior_window", {})
        if cur or pri:
            lines.append(
                f"Window: {cur.get('claim_count', '?')} claims (current) / "
                f"{pri.get('claim_count', '?')} claims (prior {window_hours}h)"
            )

        return Response(message="\n".join(lines), break_loop=False)


# ---------------------------------------------------------------------------
# OssHypotheses
# ---------------------------------------------------------------------------

class OssHypotheses(Tool):
    """
    Manage competing hypotheses using Chamberlin's method.

    Actions:
      list              — list hypotheses (filtered by observation_id/status)
      register          — create a new hypothesis for an observation
      confirm_prediction — increment confirmed-predictions counter
      falsify           — mark falsified with supporting evidence
      promote           — elevate to working model status

    Args:
        action               (str):   list | register | confirm_prediction | falsify | promote [required]
        observation_id       (int):   observation ID (for list/register)
        hypothesis_id        (int):   hypothesis ID (for confirm_prediction/falsify/promote)
        candidate_explanation (str):  explanation text (for register)
        evidence             (str):   falsification evidence (for falsify)
        predictions          (list):  list of falsifiable prediction strings (for register)
        confidence           (float): initial confidence 0.0–1.0 (for register, default 0.0)
    """

    async def execute(self, **kwargs) -> Response:
        action = (self.args.get("action") or "list").strip().lower()
        print(f"[OSS] oss_hypotheses: action={action}", flush=True)

        try:
            _ensure_plugin()
            from src.hypothesis import (
                register_hypothesis, get_hypotheses,
                confirm_prediction, falsify_hypothesis, promote_hypothesis,
            )
            conn = _get_conn()
        except Exception as e:
            return _oss_error("oss_hypotheses import failed", e)

        try:
            if action == "list":
                obs_id = self.args.get("observation_id")
                status = (self.args.get("status") or "").strip().upper() or None
                limit  = int(self.args.get("limit") or 20)
                hyps   = get_hypotheses(
                    conn,
                    observation_id=int(obs_id) if obs_id else None,
                    status=status,
                    limit=limit,
                )
                conn.close()

                if not hyps:
                    msg = "OSS Hypotheses — no hypotheses found"
                    if obs_id:
                        msg += f" for observation {obs_id}"
                    if status:
                        msg += f" with status {status}"
                    return Response(message=msg, break_loop=False)

                icon_map = {"ACTIVE": "◉", "PROMOTED": "✓", "FALSIFIED": "✗", "SUSPENDED": "⊘"}
                lines    = [f"OSS Hypotheses — {len(hyps)} result(s)\n"]
                for h in hyps:
                    icon   = icon_map.get(h.get("status", ""), "?")
                    conf   = h.get("current_confidence", 0.0)
                    n_pred = len(_jloads(h.get("predictions_generated"), default=[]))
                    n_conf = h.get("predictions_confirmed", 0)
                    expl   = (h.get("candidate_explanation") or "")[:130]
                    lines.append(f"{icon} [{h['status']}] conf={conf:.2f} predictions: {n_conf}/{n_pred} confirmed")
                    lines.append(f"  {expl}")
                    if h.get("status") == "FALSIFIED" and h.get("falsification_evidence"):
                        lines.append(f"  Falsified by: {h['falsification_evidence'][:100]}")
                    lines.append("")
                return Response(message="\n".join(lines), break_loop=False)

            elif action == "register":
                obs_id  = self.args.get("observation_id")
                expl    = (self.args.get("candidate_explanation") or "").strip()
                preds   = self.args.get("predictions") or []
                conf    = float(self.args.get("confidence") or 0.0)
                if not obs_id or not expl:
                    conn.close()
                    return Response(message="[OSS] register requires observation_id and candidate_explanation", break_loop=False)
                row = register_hypothesis(conn, int(obs_id), expl, predictions=preds, initial_confidence=conf)
                conn.close()
                return Response(
                    message=f"OSS Hypothesis registered — id={row.get('id')} observation={obs_id}",
                    break_loop=False,
                )

            elif action == "confirm_prediction":
                hid = self.args.get("hypothesis_id")
                if not hid:
                    conn.close()
                    return Response(message="[OSS] confirm_prediction requires hypothesis_id", break_loop=False)
                row = confirm_prediction(conn, int(hid))
                conn.close()
                return Response(
                    message=f"OSS Hypothesis {hid} — confirmed predictions now {row.get('predictions_confirmed', '?')}",
                    break_loop=False,
                )

            elif action == "falsify":
                hid      = self.args.get("hypothesis_id")
                evidence = (self.args.get("evidence") or "").strip()
                if not hid or not evidence:
                    conn.close()
                    return Response(message="[OSS] falsify requires hypothesis_id and evidence", break_loop=False)
                row = falsify_hypothesis(conn, int(hid), evidence)
                conn.close()
                return Response(
                    message=f"OSS Hypothesis {hid} falsified. Evidence: {evidence[:100]}",
                    break_loop=False,
                )

            elif action == "promote":
                hid = self.args.get("hypothesis_id")
                if not hid:
                    conn.close()
                    return Response(message="[OSS] promote requires hypothesis_id", break_loop=False)
                row = promote_hypothesis(conn, int(hid))
                conn.close()
                return Response(
                    message=f"OSS Hypothesis {hid} promoted to working model.",
                    break_loop=False,
                )

            else:
                conn.close()
                return Response(
                    message=f"[OSS] Unknown action '{action}'. Valid: list / register / confirm_prediction / falsify / promote",
                    break_loop=False,
                )

        except Exception as e:
            try:
                conn.close()
            except Exception:
                pass
            return _oss_error(f"oss_hypotheses action={action} failed", e)


# ---------------------------------------------------------------------------
# OssHealth
# ---------------------------------------------------------------------------

class OssHealth(Tool):
    """
    System operational health report.

    Detects performance degradation that may indicate the OSS system itself
    is under targeted attack. All metrics computed deterministically.

    Health signals:
      NOMINAL     — all metrics within bounds
      DEGRADED    — 1-2 metrics outside bounds
      COMPROMISED — 3+ metrics simultaneously degraded (coordinated attack)

    No arguments required.
    """

    async def execute(self, **kwargs) -> Response:
        print("[OSS] oss_health", flush=True)

        try:
            _ensure_plugin()
            from src.meta_detection import run_health_check
            from src.ingest import is_paused
            conn   = _get_conn()
            result = run_health_check(conn)

            # Claim counts
            cur = conn.cursor()
            cur.execute("SELECT trust_level, COUNT(*) AS n FROM claims GROUP BY trust_level")
            counts       = {row["trust_level"]: row["n"] for row in cur.fetchall()}
            total_claims = sum(counts.values())

            cur.execute("SELECT COUNT(*) AS n FROM sources")
            source_count = cur.fetchone()["n"]

            cur.execute(
                "SELECT MAX(extracted_at) AS last FROM claims WHERE trust_level != 'IRRELEVANT'"
            )
            last_claim = (cur.fetchone()["last"] or "")[:19]
            conn.close()
        except Exception as e:
            return _oss_error("oss_health failed", e)

        signal   = result.get("health_signal", "?")
        degraded = result.get("degraded_metrics", [])
        metrics  = result.get("metrics", {})

        signal_prefix = {"NOMINAL": "NOMINAL", "DEGRADED": "DEGRADED", "COMPROMISED": "COMPROMISED"}.get(signal, signal)
        paused_s      = "paused" if is_paused() else "active"

        lines = [
            "OSS Intelligence Ledger — Health Report",
            f"Status: {signal_prefix}",
            f"Claims: {total_claims} total ({counts.get('PROMOTED', 0)} promoted, "
            f"{counts.get('STAGED', 0)} staged, {counts.get('IRRELEVANT', 0)} irrelevant)",
            f"Sources: {source_count} registered",
            f"Ingestion: {paused_s} (last claim: {last_claim or 'none'})",
        ]

        if degraded:
            lines.append(f"Degraded metrics: {', '.join(degraded)}")

        lines.append("")
        icon_map = {"OK": "✓", "WARN": "⚠", "DEGRADED": "⚠"}
        for name, m in metrics.items():
            status = m.get("status", "?")
            icon   = icon_map.get(status, "?")
            detail = ""
            if name == "false_positive_rate":
                detail = f"rate={m.get('rate', 0.0):.3f} ({m.get('promoted', '?')} promoted, {m.get('returned', '?')} returned)"
            elif name == "source_trust_skew":
                detail = f"{m.get('low_trust_count', '?')}/{m.get('total', '?')} sources below trust floor"
            elif name == "resolution_time":
                avg = m.get("avg_hours")
                detail = f"avg={avg:.1f}h" if avg is not None else "no data"
            elif name == "volume_anomaly":
                z = m.get("z_score")
                detail = f"z={z:.2f}" if z is not None else "no data"
            lines.append(f"  {icon} {name}: {status}" + (f" — {detail}" if detail else ""))

        return Response(message="\n".join(lines), break_loop=False)


# ---------------------------------------------------------------------------
# OssSubmit
# ---------------------------------------------------------------------------

class OssSubmit(Tool):
    """
    Log a new claim directly to the OSS intelligence ledger.

    Use when the analyst dictates something worth recording that isn't
    coming through monitored RSS feeds. Claim is embedded, deduplicated,
    and inserted as STAGED with auto-promotion.

    Args:
        claim_text     (str):       The claim to record [required]
        topic_tags     (str|list):  Comma-separated or list of topic tags
        technique_class (str):      presuasion | fracture | emergent | direct | none
    """

    async def execute(self, **kwargs) -> Response:
        claim_text      = (self.args.get("claim_text") or "").strip()
        topic_tags      = self.args.get("topic_tags") or []
        technique_class = (self.args.get("technique_class") or "direct").strip()

        print(f"[OSS] oss_submit: claim={claim_text[:60]!r}", flush=True)

        if not claim_text:
            return Response(message="[OSS] oss_submit requires claim_text.", break_loop=False)

        # Normalise topic_tags: accept comma-string or list
        if isinstance(topic_tags, str):
            topic_tags = [t.strip() for t in topic_tags.split(",") if t.strip()]

        try:
            _ensure_plugin()
            import numpy as np
            import faiss as faiss_lib
            from sentence_transformers import SentenceTransformer
            from src.db import get_conn, init_db, jloads, jdumps

            faiss_path = os.environ.get("OSS_FAISS_PATH", "/a0/usr/oss/claims.index")
            dedup_thr  = float(os.environ.get("OSS_DEDUP_THRESHOLD", "0.95"))
            emb_model  = os.environ.get("OSS_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

            conn = get_conn()
            init_db(conn)
            cur  = conn.cursor()

            # Get or create the "Analyst Manual Entry" source
            cur.execute("SELECT id FROM sources WHERE name='Analyst Manual Entry' LIMIT 1")
            row = cur.fetchone()
            if row:
                source_id = row["id"]
            else:
                cur.execute(
                    "INSERT INTO sources (name, url, source_type, cluster, confidence_score) "
                    "VALUES ('Analyst Manual Entry', 'manual://analyst-entry', 'official', 'official', 1.0)"
                )
                conn.commit()
                source_id = cur.lastrowid

            # Embed claim and check for dedup
            model = SentenceTransformer(emb_model)
            vec   = model.encode([claim_text], normalize_embeddings=True).astype(np.float32)

            duplicate = False
            if os.path.exists(faiss_path):
                idx = faiss_lib.read_index(faiss_path)
                if idx.ntotal > 0:
                    D, I = idx.search(vec, 1)
                    if D[0][0] >= dedup_thr:
                        duplicate = True

            if duplicate:
                conn.close()
                return Response(
                    message="[OSS] Near-identical claim already in ledger — not added.",
                    break_loop=False,
                )

            # Insert claim
            now        = __import__("datetime").datetime.utcnow().isoformat()
            tags_json  = jdumps(topic_tags)
            cur.execute("""
                INSERT INTO claims
                    (source_id, raw_text, claim_text, article_url, article_title,
                     topic_tags, technique_class, extracted_at, trust_level,
                     staging_confidence)
                VALUES (?,?,?,?,?,?,?,?,'STAGED',1.0)
            """, (
                source_id, claim_text, claim_text,
                "manual://analyst-entry", "Analyst Manual Entry",
                tags_json, technique_class, now,
            ))
            conn.commit()
            claim_id = cur.lastrowid

            # Embed and persist to FAISS index
            try:
                os.makedirs(os.path.dirname(faiss_path), exist_ok=True)
                if os.path.exists(faiss_path):
                    idx = faiss_lib.read_index(faiss_path)
                else:
                    idx = faiss_lib.IndexFlatIP(vec.shape[1])
                faiss_id = idx.ntotal
                idx.add(vec)
                faiss_lib.write_index(idx, faiss_path)
                cur.execute("UPDATE claims SET faiss_id=? WHERE id=?", (faiss_id, claim_id))
                conn.commit()
            except Exception as faiss_err:
                print(f"[OSS] FAISS persist warning: {faiss_err}", flush=True)

            # Auto-promote analyst entries
            cur.execute(
                "UPDATE claims SET trust_level='PROMOTED' WHERE id=?", (claim_id,)
            )
            conn.commit()

            # Validate topic tags
            matched   = []
            unmatched = []
            for tag in topic_tags:
                cur.execute("SELECT tag FROM topics WHERE tag=?", (tag,))
                if cur.fetchone():
                    matched.append(tag)
                else:
                    unmatched.append(tag)
            conn.close()

        except Exception as e:
            return _oss_error("oss_submit failed", e)

        lines = [
            f"[OSS] Claim submitted and promoted — ID {claim_id}",
            f"Topics matched: {matched if matched else '(none)'}",
        ]
        if unmatched:
            lines.append(f"Topics not recognized (not applied): {unmatched}")
        return Response(message="\n".join(lines), break_loop=False)


# ---------------------------------------------------------------------------
# OssListTopics
# ---------------------------------------------------------------------------

class OssListTopics(Tool):
    """
    List all topics the OSS ingestion pipeline is currently monitoring.

    Shows each topic's tag, display name, claim count, and last activity.

    Args:
        active_only (str): "false" to include inactive topics (default: true)
    """

    async def execute(self, **kwargs) -> Response:
        active_only = (self.args.get("active_only") or "true").lower().strip()
        print(f"[OSS] oss_list_topics: active_only={active_only}", flush=True)

        try:
            conn = _get_conn()
            cur  = conn.cursor()
            if active_only != "false":
                cur.execute("SELECT * FROM topics WHERE active=1 ORDER BY claim_count DESC")
            else:
                cur.execute("SELECT * FROM topics ORDER BY active DESC, claim_count DESC")
            topics = [dict(r) for r in cur.fetchall()]
            conn.close()
        except Exception as e:
            return _oss_error("oss_list_topics failed", e)

        if not topics:
            return Response(
                message="[OSS] No monitored topics registered yet. Use oss_add_topic to add one.",
                break_loop=False,
            )

        lines = [f"OSS Monitored Topics — {len(topics)} registered\n"]
        for t in topics:
            tag    = t.get("tag", "?")
            name   = t.get("display_name", tag)
            count  = t.get("claim_count", 0)
            active = t.get("active", 1)
            last   = (t.get("last_active") or "")[:10]
            desc   = t.get("description") or ""
            status = "" if active else " [inactive]"
            detail = f" — {desc}" if desc else ""
            lines.append(f"  · {tag} ({name}){status}: {count} claims | last active {last}{detail}")

        return Response(message="\n".join(lines), break_loop=False)


# ---------------------------------------------------------------------------
# OssAddTopic
# ---------------------------------------------------------------------------

class OssAddTopic(Tool):
    """
    Register a new topic tag for the OSS ingestion pipeline.

    Tagging applies on the next ingestion pass — no restart required.

    Args:
        tag          (str): Topic tag slug, e.g. 'taiwan-strait' [required]
        display_name (str): Human-readable label (defaults to tag)
        description  (str): What this topic covers (optional)
    """

    async def execute(self, **kwargs) -> Response:
        tag          = (self.args.get("tag") or "").strip()
        display_name = (self.args.get("display_name") or "").strip() or tag
        description  = (self.args.get("description") or "").strip()
        print(f"[OSS] oss_add_topic: tag={tag!r}", flush=True)

        if not tag:
            return Response(message="[OSS] Error: tag argument required", break_loop=False)

        try:
            conn = _get_conn()
            cur  = conn.cursor()
            cur.execute("SELECT tag, active FROM topics WHERE tag=?", (tag,))
            existing = cur.fetchone()

            if existing:
                conn.close()
                active = existing["active"]
                return Response(
                    message=f"[OSS] Topic '{tag}' already registered (active={bool(active)}).",
                    break_loop=False,
                )

            cur.execute(
                "INSERT INTO topics (tag, display_name, description) VALUES (?,?,?)",
                (tag, display_name, description or None),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            return _oss_error("oss_add_topic failed", e)

        return Response(
            message=f"[OSS] Topic '{tag}' ({display_name}) added. Claims will be tagged on the next ingestion pass.",
            break_loop=False,
        )


# ---------------------------------------------------------------------------
# OssIngestPause
# ---------------------------------------------------------------------------

class OssIngestPause(Tool):
    """
    Pause the OSS automated RSS ingestion pipeline.

    Stops the scheduler from issuing new LLM extraction calls. No state is
    lost. Use oss_ingest_resume to restart.

    No arguments required.
    """

    async def execute(self, **kwargs) -> Response:
        print("[OSS] oss_ingest_pause: pausing ingestion pipeline", flush=True)
        try:
            _ensure_plugin()
            from src.ingest import set_paused
            set_paused(True)
        except Exception as e:
            return _oss_error("oss_ingest_pause failed", e)

        return Response(
            message="[OSS] Ingestion pipeline paused. No new extraction calls will be issued until resumed.",
            break_loop=False,
        )


# ---------------------------------------------------------------------------
# OssIngestResume
# ---------------------------------------------------------------------------

class OssIngestResume(Tool):
    """
    Resume the OSS automated RSS ingestion pipeline.

    Re-enables the scheduler after a pause. The next pass runs at the next
    scheduled interval.

    No arguments required.
    """

    async def execute(self, **kwargs) -> Response:
        print("[OSS] oss_ingest_resume: resuming ingestion pipeline", flush=True)
        try:
            _ensure_plugin()
            from src.ingest import set_paused
            set_paused(False)
        except Exception as e:
            return _oss_error("oss_ingest_resume failed", e)

        return Response(
            message="[OSS] Ingestion pipeline resumed. Next pass will run at the scheduled interval.",
            break_loop=False,
        )


# ---------------------------------------------------------------------------
# OssQuestion
# ---------------------------------------------------------------------------

class OssQuestion(Tool):
    """
    Manage analyst active questions — the organizing principle for the ledger.

    Actions:
      list       — list all active questions with attention weights
      create     — create a new question
      evolve     — mark old question inactive, create successor linked to it
      deactivate — mark a question inactive without creating a successor

    Args:
        action           (str):  list | create | evolve | deactivate [required]
        text             (str):  Question text (for create)
        question_id      (str):  Question ID (for evolve/deactivate)
        attention_weights (dict): Domain weight map — e.g. {"logistics": 0.8, "military": 0.6}
    """

    async def execute(self, **kwargs) -> Response:
        action = (self.args.get("action") or "list").strip().lower()
        print(f"[OSS] oss_question: action={action}", flush=True)

        try:
            _ensure_plugin()
            from src.questions import (
                create_question, evolve_question,
                get_active_questions, deactivate_question,
            )
            conn = _get_conn()
        except Exception as e:
            return _oss_error("oss_question import failed", e)

        try:
            if action == "list":
                questions = get_active_questions(conn)
                conn.close()
                if not questions:
                    return Response(
                        message="OSS Active Questions — none registered. Use action=create to add one.",
                        break_loop=False,
                    )
                lines = [f"OSS Active Questions — {len(questions)}\n"]
                for q in questions:
                    qid     = q.get("id", "?")[:8]
                    text    = q.get("text", "")
                    updated = (q.get("last_updated") or "")[:16]
                    weights = _jloads(q.get("attention_weights"), default={})
                    w_str   = " ".join(f"{k}:{v:.1f}" for k, v in weights.items()) if weights else "none"
                    lines.append(f"  [{qid}] {text}")
                    lines.append(f"    Updated: {updated} | Weights: {w_str}\n")
                return Response(message="\n".join(lines), break_loop=False)

            elif action == "create":
                text    = (self.args.get("text") or "").strip()
                weights = self.args.get("attention_weights") or {}
                if not text:
                    conn.close()
                    return Response(message="[OSS] create requires text", break_loop=False)
                q = create_question(conn, text, attention_weights=weights)
                conn.close()
                return Response(
                    message=f"OSS Question created — id={q.get('id', '?')[:8]}: {text}",
                    break_loop=False,
                )

            elif action == "evolve":
                qid     = (self.args.get("question_id") or "").strip()
                text    = (self.args.get("text") or "").strip()
                weights = self.args.get("attention_weights") or {}
                if not qid or not text:
                    conn.close()
                    return Response(message="[OSS] evolve requires question_id and text", break_loop=False)
                new_q = evolve_question(conn, qid, text, attention_weights=weights)
                conn.close()
                return Response(
                    message=f"OSS Question evolved — old id={qid[:8]} → new id={new_q.get('id', '?')[:8]}: {text}",
                    break_loop=False,
                )

            elif action == "deactivate":
                qid = (self.args.get("question_id") or "").strip()
                if not qid:
                    conn.close()
                    return Response(message="[OSS] deactivate requires question_id", break_loop=False)
                ok = deactivate_question(conn, qid)
                conn.close()
                if ok:
                    return Response(message=f"OSS Question {qid[:8]} deactivated.", break_loop=False)
                return Response(message=f"[OSS] Question {qid[:8]} not found.", break_loop=False)

            else:
                conn.close()
                return Response(
                    message=f"[OSS] Unknown action '{action}'. Valid: list / create / evolve / deactivate",
                    break_loop=False,
                )

        except Exception as e:
            try:
                conn.close()
            except Exception:
                pass
            return _oss_error(f"oss_question action={action} failed", e)


# ---------------------------------------------------------------------------
# OssSynthesize
# ---------------------------------------------------------------------------

class OssSynthesize(Tool):
    """
    Ask the OSS ledger a question and receive an evidence-based synthesis.

    Claims are retrieved by semantic similarity and weighted by source
    credibility and recency. LLM writes a 2-paragraph synthesis with
    claim ID citations. Falls back to deterministic summary on LLM failure.

    Args:
        question (str): The analyst question to synthesize evidence for [required]
        limit    (int): Max claims to retrieve (default 40)
    """

    async def execute(self, **kwargs) -> Response:
        question = (self.args.get("question") or "").strip()
        limit    = int(self.args.get("limit") or 40)
        print(f"[OSS] oss_synthesize: question={question[:60]!r}", flush=True)

        if not question:
            return Response(message="[OSS] oss_synthesize requires question", break_loop=False)

        try:
            _ensure_plugin()
            from src.synthesis import synthesize
            conn   = _get_conn()
            result = synthesize(conn, question, limit_claims=limit)
            conn.close()
        except Exception as e:
            return _oss_error("oss_synthesize failed", e)

        synthesis_text = result.get("synthesis_text", "(no synthesis available)")
        n_supporting   = len(result.get("supporting", []))
        n_contra       = len(result.get("contradicting", []))
        n_neutral      = len(result.get("neutral", []))
        sources        = result.get("sources_used", [])

        lines = [
            f"OSS Evidence Synthesis",
            f"Question: {question}",
            f"Evidence: {n_supporting} supporting, {n_contra} contradicting, {n_neutral} neutral",
            f"Sources consulted: {', '.join(sources[:8]) if sources else 'none'}",
            "",
            synthesis_text,
        ]
        return Response(message="\n".join(lines), break_loop=False)
