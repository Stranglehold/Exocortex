"""
api_swarmfish_session.py — Get prediction session detail (V2 transparency levels)

URL: GET /api/plugins/swarmfish/api_swarmfish_session?session_id=<id>&level=<1|2|3>

V2 deliberation transparency levels:
  Level 1 (default) — confidence + one-sentence summary per profile
  Level 2           — structured summary: reasoning, evidence cited, assumptions, dissent
  Level 3           — full LLM reasoning text (show me your work)
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/swarmfish")

import json

from helpers.api import ApiHandler, Request

from src.db import get_conn


class SwarmfishSession(ApiHandler):
    """Get session detail with configurable transparency level.

    URL: GET /api/plugins/swarmfish/api_swarmfish_session
    Query params: session_id (required), level (1|2|3, default 2)
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict:
        # Support both GET query params and POST body
        session_id = input.get("session_id") or ""
        level = int(input.get("level") or 2)

        if not session_id:
            return {"ok": False, "error": "session_id is required"}

        if level not in (1, 2, 3):
            level = 2

        try:
            conn = get_conn()

            # Fetch session
            session = conn.execute(
                "SELECT * FROM acp_sessions WHERE id = ?", (session_id,)
            ).fetchone()

            if not session:
                return {"ok": False, "error": f"Session {session_id} not found"}

            session_dict = dict(session)

            # Parse JSON fields
            for field in ("falsification_checklist", "profiles_used", "committee_config", "analyst_inputs"):
                if session_dict.get(field) and isinstance(session_dict[field], str):
                    try:
                        session_dict[field] = json.loads(session_dict[field])
                    except json.JSONDecodeError:
                        pass

            # Fetch assessments
            assessments = conn.execute("""
                SELECT * FROM acp_assessments
                WHERE session_id = ?
                ORDER BY created_at
            """, (session_id,)).fetchall()

            profile_details = []
            for a in assessments:
                a_dict = dict(a)

                # Parse JSON fields
                for field in ("key_assumptions", "falsification_conditions",
                              "constraints_applied", "profile_extra_data",
                              "similarity_dimensions_matched", "similarity_dimensions_not_matched"):
                    if a_dict.get(field) and isinstance(a_dict[field], str):
                        try:
                            a_dict[field] = json.loads(a_dict[field])
                        except json.JSONDecodeError:
                            pass

                if level == 1:
                    profile_details.append({
                        "assessment_id": a_dict["id"],
                        "profile_name": a_dict["profile_name"],
                        "confidence": a_dict["confidence"],
                        "prediction": (a_dict.get("prediction") or "")[:200],
                        "reasoning_summary": (a_dict.get("reasoning_summary") or "")[:200],
                        "confidence_capped": bool(a_dict.get("confidence_capped")),
                        "error": a_dict.get("error"),
                    })
                elif level == 2:
                    profile_details.append({
                        "assessment_id": a_dict["id"],
                        "profile_name": a_dict["profile_name"],
                        "confidence": a_dict["confidence"],
                        "prediction": a_dict.get("prediction"),
                        "reasoning_summary": a_dict.get("reasoning_summary"),
                        "key_assumptions": a_dict.get("key_assumptions"),
                        "falsification_conditions": a_dict.get("falsification_conditions"),
                        "confidence_capped": bool(a_dict.get("confidence_capped")),
                        "confidence_cap_reason": a_dict.get("confidence_cap_reason"),
                        # Historian-specific
                        "analogue_reference": a_dict.get("analogue_reference"),
                        "overall_similarity_score": a_dict.get("overall_similarity_score"),
                        "relevant_similarity_score": a_dict.get("relevant_similarity_score"),
                        # Profile-specific extras (Reflexivity, Decomposer, etc.)
                        "profile_extra_data": a_dict.get("profile_extra_data"),
                        "error": a_dict.get("error"),
                    })
                else:  # level == 3
                    profile_details.append({
                        "assessment_id": a_dict["id"],
                        "profile_name": a_dict["profile_name"],
                        "confidence": a_dict["confidence"],
                        "prediction": a_dict.get("prediction"),
                        "reasoning_summary": a_dict.get("reasoning_summary"),
                        "full_reasoning": a_dict.get("full_reasoning"),  # complete LLM text
                        "key_assumptions": a_dict.get("key_assumptions"),
                        "falsification_conditions": a_dict.get("falsification_conditions"),
                        "confidence_capped": bool(a_dict.get("confidence_capped")),
                        "confidence_cap_reason": a_dict.get("confidence_cap_reason"),
                        "analogue_reference": a_dict.get("analogue_reference"),
                        "overall_similarity_score": a_dict.get("overall_similarity_score"),
                        "relevant_similarity_score": a_dict.get("relevant_similarity_score"),
                        "similarity_dimensions_matched": a_dict.get("similarity_dimensions_matched"),
                        "similarity_dimensions_not_matched": a_dict.get("similarity_dimensions_not_matched"),
                        "relevance_rationale": a_dict.get("relevance_rationale"),
                        "profile_extra_data": a_dict.get("profile_extra_data"),
                        "error": a_dict.get("error"),
                    })

            return {
                "ok": True,
                "session_id": session_id,
                "question": session_dict["question"],
                "domain": session_dict["domain"],
                "created_at": session_dict["created_at"],
                "committee_config": session_dict.get("committee_config"),
                "consensus_confidence": session_dict.get("consensus_confidence"),
                "consensus_range_low": session_dict.get("consensus_range_low"),
                "consensus_range_high": session_dict.get("consensus_range_high"),
                "meta_confidence": session_dict.get("meta_confidence"),
                "disagreement_level": session_dict.get("disagreement_level"),
                "operator_brief": session_dict.get("operator_brief"),
                "falsification_checklist": session_dict.get("falsification_checklist"),
                "analyst_inputs": session_dict.get("analyst_inputs"),
                "transparency_level": level,
                "profiles": profile_details,
            }

        except Exception as e:
            import traceback
            print(f"[SWARM] session error: {traceback.format_exc()}", flush=True)
            return {"ok": False, "error": str(e)}
