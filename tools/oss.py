"""
oss.py — OSS (Office of Strategic Services) Cognitive Defense System tools.

Provides Agent Zero access to the OSS intelligence ledger: claims, narrative
drift, propagation dynamics, competing hypotheses, and system health.

Available tools (call by snake_case class name):
  oss_topic       — query claims for a topic from the ledger
  oss_drift       — detect narrative framing shift for a topic
  oss_dynamics    — propagation velocity, alert level, time-to-escape
  oss_hypotheses  — list competing hypotheses for an observation
  oss_health      — system operational health report

Service: OSS_URL env var (default: http://host.docker.internal:7731)
Auth:    OSS_ANALYST_TOKEN env var (default: dev_analyst_token)

The analyst holds the conclusions. The system provides the record.
"""

import json
import os
import urllib.error
import urllib.request

from python.helpers.tool import Tool, Response

OSS_URL          = os.environ.get("OSS_URL", "http://host.docker.internal:7731")
OSS_ANALYST_TOKEN = os.environ.get("OSS_ANALYST_TOKEN", "dev_analyst_token")


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _post(endpoint: str, payload: dict) -> dict:
    payload["analyst_token"] = OSS_ANALYST_TOKEN
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(
        f"{OSS_URL}{endpoint}", data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def _get(endpoint: str) -> dict:
    with urllib.request.urlopen(f"{OSS_URL}{endpoint}", timeout=15) as resp:
        return json.loads(resp.read())


def _oss_error(e: Exception) -> Response:
    if isinstance(e, urllib.error.HTTPError):
        body = e.read().decode(errors="replace")[:200]
        return Response(
            message=f"OSS error {e.code}: {body}", break_loop=False
        )
    return Response(message=f"OSS unreachable: {e}", break_loop=False)


# ---------------------------------------------------------------------------
# oss_topic
# ---------------------------------------------------------------------------

class OssTopic(Tool):
    """
    Query claims about a topic from the OSS intelligence ledger.

    Args:
        topic (str):  Topic tag to query (e.g. 'iran-hormuz', 'taiwan-strait')
        since (str):  Optional ISO datetime — only return claims after this date
    """

    async def execute(self, **kwargs) -> Response:
        topic = self.args.get("topic", "").strip()
        print(f"[OSS] oss_topic: topic={topic!r}", flush=True)

        if not topic:
            return Response(message="Error: topic argument required", break_loop=False)

        payload: dict = {"topic": topic}
        if self.args.get("since"):
            payload["since"] = self.args["since"]

        try:
            result = _post("/api/topic", payload)
        except Exception as e:
            return _oss_error(e)

        claims = result.get("claims", [])
        if not claims:
            return Response(
                message=f"OSS: no claims found for topic '{topic}'",
                break_loop=False,
            )

        trust_order = {"PROMOTED": 0, "STAGED": 1, "RETURNED_TO_STAGED": 2, "FALSIFIED": 3}
        claims = sorted(claims, key=lambda c: trust_order.get(c.get("trust_level", ""), 9))

        lines = [f"**OSS ledger: {len(claims)} claim(s) for '{topic}'**\n"]
        for c in claims[:12]:
            trust   = c.get("trust_level", "?")
            text    = c.get("claim_text", "")[:140]
            source  = c.get("source_name", "?")
            cluster = c.get("cluster", "?")
            conf    = c.get("confidence_score", "?")
            lines.append(f"[{trust}] {text}")
            lines.append(f"  → {source} ({cluster}, conf={conf})\n")

        if len(claims) > 12:
            lines.append(f"…and {len(claims) - 12} additional claims.")

        return Response(message="\n".join(lines), break_loop=False)


# ---------------------------------------------------------------------------
# oss_drift
# ---------------------------------------------------------------------------

class OssDrift(Tool):
    """
    Detect narrative framing drift for a topic.

    Compares current window vs prior window for technique shifts, cluster
    shifts, salience changes, and volume changes. Returns dominant signal
    and whether the framing has materially shifted.

    Args:
        topic (str):          Topic tag to analyze
        window_hours (int):   Window length in hours (default 168 = 7 days)
    """

    async def execute(self, **kwargs) -> Response:
        topic        = self.args.get("topic", "").strip()
        window_hours = int(self.args.get("window_hours", 168))
        print(f"[OSS] oss_drift: topic={topic!r} window={window_hours}h", flush=True)

        if not topic:
            return Response(message="Error: topic argument required", break_loop=False)

        try:
            result = _post("/api/topic_drift", {"topic": topic, "window_hours": window_hours})
        except Exception as e:
            return _oss_error(e)

        drifted  = result.get("drifted", False)
        score    = result.get("drift_score", 0.0)
        signals  = result.get("signals", {})
        dominant = result.get("dominant_signal", "none")

        status = "**DRIFT DETECTED**" if drifted else "Stable"
        lines  = [
            f"**OSS narrative drift: '{topic}'**",
            f"Status: {status} (score={score:.3f}, dominant={dominant})",
            f"Current window: {result['current_window']['claim_count']} claims | "
            f"Prior window: {result['prior_window']['claim_count']} claims",
            "",
        ]

        for name, sig in signals.items():
            mag = sig.get("magnitude", 0)
            if mag > 0.05:
                detail = ""
                if name == "technique_shift":
                    detail = f"  current={sig.get('current')} prior={sig.get('prior')}"
                elif name == "cluster_shift":
                    entered = sig.get("entered", [])
                    exited  = sig.get("exited", [])
                    if entered or exited:
                        detail = f"  entered={entered} exited={exited}"
                elif name in ("salience_shift", "confidence_shift"):
                    detail = (
                        f"  {sig.get('direction', '')} "
                        f"({sig.get('prior_avg', '?'):.3f} → {sig.get('current_avg', '?'):.3f})"
                    )
                elif name == "volume_shift":
                    detail = (
                        f"  ratio={sig.get('ratio', '?')}"
                        f" ({sig.get('prior_count')} → {sig.get('current_count')})"
                    )
                lines.append(f"  {name}: {mag:.3f}{detail}")

        return Response(message="\n".join(lines), break_loop=False)


# ---------------------------------------------------------------------------
# oss_dynamics
# ---------------------------------------------------------------------------

class OssDynamics(Tool):
    """
    Compute propagation dynamics for a topic.

    Returns velocity (unique sources/hour), acceleration, cluster coverage,
    time until correction becomes impractical, and alert level.

    Alert levels:
      INFORMATIONAL — baseline monitoring
      WARNING       — spreading faster than expected or broad cluster coverage
      URGENT        — time to escape velocity < operator response baseline (24h)

    Args:
        topic (str):          Topic tag to analyze
        window_hours (int):   Velocity measurement window (default 24h)
    """

    async def execute(self, **kwargs) -> Response:
        topic        = self.args.get("topic", "").strip()
        window_hours = int(self.args.get("window_hours", 24))
        print(f"[OSS] oss_dynamics: topic={topic!r}", flush=True)

        if not topic:
            return Response(message="Error: topic argument required", break_loop=False)

        try:
            result = _post(
                "/api/propagation_dynamics",
                {"topic": topic, "window_hours": window_hours},
            )
        except Exception as e:
            return _oss_error(e)

        alert    = result.get("alert_level", "?")
        velocity = result.get("propagation_velocity", 0)
        accel    = result.get("acceleration", 0)
        coverage = result.get("cluster_coverage_pct", 0)
        t_escape = result.get("time_to_escape_velocity_hours")
        half     = result.get("half_life_hours")

        t_escape_str = (
            f"{t_escape:.1f}h" if t_escape is not None else "N/A (not accelerating)"
        )
        half_str = f"{half:.1f}h" if half is not None else "insufficient falsified claims"

        lines = [
            f"**OSS propagation dynamics: '{topic}'**",
            f"Alert: **{alert}**",
            f"Velocity:         {velocity:.4f} sources/h",
            f"Acceleration:     {accel:.6f} sources/h²",
            f"Cluster coverage: {coverage:.0%}",
            f"Time to escape:   {t_escape_str}",
            f"Half-life proxy:  {half_str}",
        ]

        cur = result.get("current_window", {})
        pri = result.get("prior_window", {})
        lines.append(
            f"Window: {cur.get('claim_count')} claims (current) / "
            f"{pri.get('claim_count')} claims (prior {window_hours}h)"
        )

        return Response(message="\n".join(lines), break_loop=False)


# ---------------------------------------------------------------------------
# oss_hypotheses
# ---------------------------------------------------------------------------

class OssHypotheses(Tool):
    """
    List competing hypotheses for an observation from the hypothesis registry.

    Implements Chamberlin's method: multiple candidate explanations per
    observation, each generating falsifiable predictions. The survivor is
    the one whose predictions matched reality.

    Args:
        observation_id (int):  Filter by observation ID (optional)
        status (str):          Filter by status: ACTIVE | PROMOTED | FALSIFIED | SUSPENDED
        limit (int):           Max results (default 20)
    """

    async def execute(self, **kwargs) -> Response:
        obs_id = self.args.get("observation_id")
        status = self.args.get("status", "").strip() or None
        limit  = int(self.args.get("limit", 20))
        print(f"[OSS] oss_hypotheses: obs={obs_id} status={status}", flush=True)

        params: dict = {"limit": limit}
        if obs_id:
            params["observation_id"] = int(obs_id)
        if status:
            params["status"] = status.upper()

        try:
            result = _post("/api/hypotheses", params)
        except Exception as e:
            return _oss_error(e)

        hyps = result.get("hypotheses", [])
        if not hyps:
            msg = "OSS: no hypotheses found"
            if obs_id:
                msg += f" for observation {obs_id}"
            if status:
                msg += f" with status {status}"
            return Response(message=msg, break_loop=False)

        status_icon = {
            "ACTIVE": "◉", "PROMOTED": "✓", "FALSIFIED": "✗", "SUSPENDED": "⊘"
        }
        lines = [f"**OSS hypotheses ({len(hyps)} results)**\n"]

        for h in hyps:
            icon    = status_icon.get(h.get("status", ""), "?")
            conf    = h.get("current_confidence", 0)
            n_pred  = len(h.get("predictions_generated") or [])
            n_conf  = h.get("predictions_confirmed", 0)
            expl    = h.get("candidate_explanation", "")[:120]
            lines.append(
                f"{icon} [{h['status']}] conf={conf:.2f} "
                f"predictions={n_conf}/{n_pred} confirmed"
            )
            lines.append(f"  {expl}")
            if h.get("status") == "FALSIFIED" and h.get("falsification_evidence"):
                lines.append(f"  Falsified by: {h['falsification_evidence'][:80]}")
            lines.append("")

        return Response(message="\n".join(lines), break_loop=False)


# ---------------------------------------------------------------------------
# oss_health
# ---------------------------------------------------------------------------

class OssHealth(Tool):
    """
    System operational health report.

    Detects performance degradation that may indicate the OSS system itself
    is under targeted attack. Checks false positive rate, source trust skew,
    resolution time, and volume anomalies.

    Health signals:
      NOMINAL     — all metrics within bounds
      DEGRADED    — 1-2 metrics outside bounds
      COMPROMISED — 3+ metrics simultaneously degraded (coordinated attack)

    Args:
        window_hours (int):  Analysis window (default 168 = 7 days)
    """

    async def execute(self, **kwargs) -> Response:
        window_hours = int(self.args.get("window_hours", 168))
        print(f"[OSS] oss_health: window={window_hours}h", flush=True)

        try:
            result = _get(f"/api/health/meta?window_hours={window_hours}")
        except Exception as e:
            return _oss_error(e)

        signal   = result.get("health_signal", "?")
        degraded = result.get("degraded_metrics", [])
        metrics  = result.get("metrics", {})

        signal_prefix = {
            "NOMINAL": "✓", "DEGRADED": "⚠", "COMPROMISED": "🚨"
        }.get(signal, "?")

        lines = [
            f"**OSS system health: {signal_prefix} {signal}**",
        ]
        if degraded:
            lines.append(f"Degraded metrics: {', '.join(degraded)}")
        lines.append("")

        for name, m in metrics.items():
            status = m.get("status", "?")
            icon   = "✓" if status == "OK" else "⚠"
            detail = ""
            if name == "false_positive_rate":
                detail = f"rate={m.get('rate', '?'):.3f} ({m.get('promoted')} promoted, {m.get('returned')} returned)"
            elif name == "source_trust_skew":
                detail = f"{m.get('low_trust_count')}/{m.get('total')} sources below trust floor ({m.get('skew_pct', 0):.0%})"
            elif name == "resolution_time":
                avg = m.get("avg_hours")
                detail = f"avg={avg:.1f}h" if avg is not None else "no data"
            elif name == "volume_anomaly":
                detail = f"z={m.get('z_score', '?'):.2f} ({m.get('current_count')} claims vs {m.get('baseline_avg', 0):.1f} baseline)"
            lines.append(f"{icon} {name}: {status} — {detail}")

        op = _get("/api/operator_state")
        op_level = op.get("alert_level", "?")
        op_mult  = op.get("threshold_multiplier", 1.0)
        lines.append(f"\nOperator state: {op_level} (staging threshold ×{op_mult})")

        return Response(message="\n".join(lines), break_loop=False)
