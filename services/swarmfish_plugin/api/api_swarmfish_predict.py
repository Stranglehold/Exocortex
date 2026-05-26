"""
api_swarmfish_predict.py — Run a prediction through the SWARMFISH committee

URL: POST /api/plugins/swarmfish/api_swarmfish_predict

Body:
  question  str      required — the prediction question
  domain    str      optional — question domain (default: "general")
  context   str      optional — analyst-supplied evidence and context
  committee list     optional — profile names to include (default: all 8)

Returns:
  session_id, consensus, operator_brief, assessments (Level 1 detail),
  dissenters with assessment_ids for follow-up via swarmfish_session
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/swarmfish")

import asyncio

from helpers.api import ApiHandler, Request

from swfsrc.db import get_conn
from swfsrc.profiles import seed_profiles, load_profiles, PROFILE_NAMES
from swfsrc.predictor import run_all_profiles
from swfsrc.aggregator import finalize_session


class SwarmfishPredict(ApiHandler):
    """Run prediction through the SWARMFISH committee.

    URL: POST /api/plugins/swarmfish/api_swarmfish_predict
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict:
        question = (input.get("question") or "").strip()
        if not question:
            return {"ok": False, "error": "question is required"}

        domain  = (input.get("domain") or "general").strip()
        context = (input.get("context") or "").strip() or None
        committee_names = input.get("committee")  # None = all 8

        try:
            conn = get_conn()
            seed_profiles(conn)

            # Load requested profiles
            if committee_names:
                valid_names = [n for n in committee_names if n in PROFILE_NAMES]
                if not valid_names:
                    return {"ok": False, "error": f"No valid profile names in committee: {committee_names}"}
                profiles = load_profiles(conn, valid_names)
            else:
                profiles = load_profiles(conn)

            if not profiles:
                return {"ok": False, "error": "No profiles found — DB may not be initialized"}

            # Create session row
            import uuid
            session_id = str(uuid.uuid4())
            context_summary = context[:200] if context else None

            import json
            conn.execute("""
                INSERT INTO acp_sessions (id, question, domain, context_summary, committee_config)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, question, domain, context_summary,
                  json.dumps(committee_names) if committee_names else None))
            conn.commit()

            print(f"[SWARM] Session {session_id[:8]}... — "
                  f"{len(profiles)} profiles, domain={domain}", flush=True)

            # Run profiles in parallel
            assessments = await run_all_profiles(conn, profiles, question, domain, context, session_id)

            # Compute consensus and write to session
            result = finalize_session(conn, session_id, question, domain, context_summary, assessments, profiles)

            if "error" in result:
                return {"ok": False, "error": result["error"]}

            # Level 1 response: confidence + one-sentence summary per profile
            level1_assessments = []
            for a in result["assessments"]:
                level1_assessments.append({
                    "profile_name": a.get("profile_name"),
                    "confidence": a.get("confidence"),
                    "prediction": (a.get("prediction") or "")[:200],
                    "reasoning_summary": (a.get("reasoning_summary") or "")[:200],
                    "confidence_capped": a.get("confidence_capped", False),
                    "error": a.get("error"),
                    # Include assessment_id so caller can request Level 2/3 via session endpoint
                    "assessment_id": a.get("assessment_id"),
                })

            consensus = result["consensus"]

            return {
                "ok": True,
                "session_id": session_id,
                "question": question,
                "domain": domain,
                "consensus_confidence": consensus["consensus_confidence"],
                "consensus_range_low":  consensus["range_low"],
                "consensus_range_high": consensus["range_high"],
                "meta_confidence": consensus["meta_confidence"],
                "disagreement_level": consensus["disagreement_level"],
                "operator_brief": result["operator_brief"],
                "assessments": level1_assessments,
                "dissenters": consensus.get("dissenters", []),
                "falsification_checklist": result["falsification_checklist"],
            }

        except Exception as e:
            import traceback
            print(f"[SWARM] predict error: {traceback.format_exc()}", flush=True)
            return {"ok": False, "error": str(e)}
