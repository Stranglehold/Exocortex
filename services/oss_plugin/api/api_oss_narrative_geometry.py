"""
api_oss_narrative_geometry.py — narrative-coordination geometry of the claim stream.

URL: POST /api/plugins/oss/api_oss_narrative_geometry

Input:
  topic   str   optional — analyse one topic; default = all active topics

Returns the representational-geometry signature per topic (effective dimensionality,
cross-cluster echo span, soft coordination verdict). See src/narrative_geometry.py.
"""

import os
import sys
sys.path.insert(0, "/a0/usr/plugins/oss")

from helpers.api import ApiHandler, Request

from src.db import get_conn, init_db
from src.narrative_geometry import analyze_topic_geometry, analyze_all_topics


class OssNarrativeGeometry(ApiHandler):
    """Claim-stream narrative-coordination geometry.

    URL: POST /api/plugins/oss/api_oss_narrative_geometry
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict:
        topic = (input.get("topic") or "").strip() or None
        try:
            import faiss
            faiss_path = os.environ.get("OSS_FAISS_PATH", "/a0/usr/oss/claims.index")
            if not os.path.exists(faiss_path):
                return {"ok": True, "result": [], "note": "no FAISS index yet"}

            index = faiss.read_index(faiss_path)
            conn = get_conn()
            init_db(conn)
            if topic:
                result = [analyze_topic_geometry(conn, index, topic)]
            else:
                result = analyze_all_topics(conn, index)
            conn.close()
            return {"ok": True, "result": result}

        except Exception as e:
            return {"ok": False, "error": str(e)}
