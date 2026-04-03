"""
swarmfish.py — SWARMFISH Analytic Consensus Protocol tools for Agent Zero.

Provides direct access to the SWARMFISH prediction ensemble: run questions
through the 8-profile analytic committee (Base Rate Analyst, Contrarian,
Historian, Reflexivity Modeler, Decomposer, Network Analyst, Sentiment Decoder,
Risk Manager), inspect calibration state, and review recent session history.

Available tools:
  swarmfish_predict      — run a question through the ensemble, get operator brief
  swarmfish_calibration  — profile accuracy stats and recent session history

Service: SWARMFISH_URL env var (default: http://host.docker.internal:7732)
Auth:    SWARMFISH_ANALYST_TOKEN env var (default: dev_analyst_token)
"""

import json
import os
import urllib.error
import urllib.request

from helpers.tool import Tool, Response

SWARMFISH_URL          = os.environ.get("SWARMFISH_URL", "http://host.docker.internal:7732")
SWARMFISH_ANALYST_TOKEN = os.environ.get("SWARMFISH_ANALYST_TOKEN", "dev_analyst_token")


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _sf_post(endpoint: str, payload: dict, timeout: int = 300) -> dict:
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(
        f"{SWARMFISH_URL}{endpoint}", data=data,
        headers={
            "Content-Type":   "application/json",
            "X-Analyst-Token": SWARMFISH_ANALYST_TOKEN,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _sf_get(endpoint: str, timeout: int = 15) -> dict:
    req = urllib.request.Request(
        f"{SWARMFISH_URL}{endpoint}",
        headers={"X-Analyst-Token": SWARMFISH_ANALYST_TOKEN},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _sf_error(e: Exception) -> Response:
    if isinstance(e, urllib.error.HTTPError):
        body = e.read().decode(errors="replace")[:200]
        return Response(message=f"SWARMFISH error {e.code}: {body}", break_loop=False)
    return Response(message=f"SWARMFISH unreachable: {e}", break_loop=False)


# ---------------------------------------------------------------------------
# swarmfish_predict
# ---------------------------------------------------------------------------

class SwarmfishPredict(Tool):
    """
    Run a question through the SWARMFISH analytic ensemble.

    Three profiles assess the question independently:
      · Base Rate Analyst — calibrated frequentist, anchors to historical base rates
      · Contrarian        — stress-tests consensus, surfaces non-obvious failure modes
      · Historian         — pattern-matches to historical precedents

    Returns an operator brief with consensus confidence, per-profile breakdown,
    and falsification conditions. Optionally accepts context (e.g. recent OSS
    claims) to ground the assessment in current evidence.

    Args:
        question (str):   The analytic question (required)
        domain   (str):   Domain hint — geopolitical_risk | economic | military |
                          general (default: geopolitical_risk)
        context  (str):   Optional operator-supplied data/analysis to include
    """

    async def execute(self, **kwargs) -> Response:
        question = self.args.get("question", "").strip()
        domain   = self.args.get("domain", "geopolitical_risk").strip()
        context  = self.args.get("context", "").strip() or None

        print(f"[SWARMFISH] predict: question={question[:60]!r} domain={domain}", flush=True)

        if not question:
            return Response(message="Error: question argument required", break_loop=False)

        payload: dict = {"question": question, "domain": domain}
        if context:
            payload["context"] = context

        try:
            result = _sf_post("/acp/predict", payload, timeout=300)
        except Exception as e:
            return _sf_error(e)

        session_id    = result.get("session_id", "?")
        brief         = result.get("operator_brief", "")
        consensus     = result.get("consensus") or {}
        c_conf        = consensus.get("consensus_confidence", 0.0)
        spread        = consensus.get("spread", "")
        agreement     = consensus.get("agreement_level", "")
        falsification = result.get("falsification_checklist") or []
        profiles      = result.get("individual_predictions") or []

        lines = [
            f"**SWARMFISH ensemble assessment** (session `{session_id[:8]}…`)",
            "",
        ]

        if brief:
            lines.append(brief[:2000])
            lines.append("")

        lines.append(f"**Consensus: {c_conf:.0%}** | Spread: {spread} | Agreement: {agreement}")
        lines.append("")

        if profiles:
            lines.append("**Per-profile breakdown:**")
            for p in profiles:
                if p.get("error"):
                    lines.append(f"  · {p.get('profile_name', '?')}: ERROR — {p['error'][:80]}")
                    continue
                name     = p.get("profile_name", "?")
                conf     = p.get("confidence", 0.0)
                dissent  = " ⚡ DISSENTER" if abs(conf - c_conf) >= 0.20 else ""
                rationale = (p.get("rationale") or "")[:120]
                lines.append(f"  · **{name}**: {conf:.0%}{dissent}")
                if rationale:
                    lines.append(f"    {rationale}")
            lines.append("")

        if falsification:
            lines.append("**Falsification conditions:**")
            for item in falsification[:6]:
                if isinstance(item, dict):
                    cond   = item.get("condition", str(item))[:120]
                    impact = item.get("impact", "")[:80]
                    lines.append(f"  • {cond}")
                    if impact:
                        lines.append(f"    → {impact}")
                else:
                    lines.append(f"  • {str(item)[:120]}")

        lines.append(f"\nSession ID: `{session_id}` (use for outcome feedback)")
        return Response(message="\n".join(lines), break_loop=False)


# ---------------------------------------------------------------------------
# swarmfish_calibration
# ---------------------------------------------------------------------------

class SwarmfishCalibration(Tool):
    """
    Check SWARMFISH profile calibration state and recent session history.

    Shows per-profile Brier scores, prediction accuracy, and the last
    10 prediction sessions. Use to assess whether the ensemble's track
    record warrants confidence in its current assessments.

    No arguments required.
    """

    async def execute(self, **kwargs) -> Response:
        print("[SWARMFISH] calibration: fetching status and profiles", flush=True)

        try:
            status   = _sf_get("/acp/status")
            profiles = _sf_get("/acp/profiles")
        except Exception as e:
            return _sf_error(e)

        calib    = status.get("calibration", [])
        sessions = status.get("recent_sessions", [])

        lines = ["**SWARMFISH calibration state**", ""]

        if profiles:
            lines.append("**Profile weights:**")
            for p in profiles:
                name    = p.get("name", "?")
                weight  = p.get("consensus_weight", 1.0)
                updated = (p.get("updated_at") or "")[:10]
                lines.append(f"  · {name}: weight={weight:.2f} (updated {updated})")
            lines.append("")

        if calib:
            lines.append("**Prediction accuracy (Brier scores):**")
            for c in calib:
                name       = c.get("profile_name", "?")
                brier      = c.get("brier_score")
                total_pred = c.get("total_predictions", 0)
                total_out  = c.get("total_outcomes", 0)
                brier_str  = f"{brier:.3f}" if brier is not None else "uncalibrated (no outcomes)"
                lines.append(
                    f"  · {name}: Brier={brier_str} "
                    f"({total_out} outcomes / {total_pred} predictions)"
                )
            lines.append("")

        if sessions:
            lines.append("**Recent sessions (last 10):**")
            for s in sessions[:10]:
                sid     = (s.get("id") or "")[:8]
                q       = (s.get("question") or "")[:70]
                conf    = s.get("consensus_confidence")
                created = (s.get("created_at") or "")[:16].replace("T", " ")
                conf_str = f" | consensus={conf:.0%}" if conf else ""
                lines.append(f"  · `{sid}…` {created}{conf_str}")
                lines.append(f"    {q}")
        else:
            lines.append("No sessions recorded yet.")

        return Response(message="\n".join(lines), break_loop=False)
