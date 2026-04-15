"""oss_hypotheses — Manage competing hypotheses using Chamberlin's method."""

import json
import os
import sys

from helpers.tool import Tool, Response

PLUGIN_PATH = os.environ.get("OSS_PLUGIN_PATH", "/a0/usr/plugins/oss")


def _ensure_plugin() -> None:
    for _k in list(sys.modules.keys()):
        if _k == 'src' or _k.startswith('src.'):
            del sys.modules[_k]
    if PLUGIN_PATH in sys.path:
        sys.path.remove(PLUGIN_PATH)
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
    return Response(message=f"[OSS] {prefix}: {e}", break_loop=False)


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
