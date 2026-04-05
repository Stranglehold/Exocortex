"""
api_oss_health.py — OSS V2 service health check

URL: GET /api/plugins/oss/api_oss_health

Returns overall service status, claim counts by trust level, source count,
ingestion state, and meta-detection health report.
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/oss")

from helpers.api import ApiHandler, Request

from src.db import get_conn, init_db
from src.meta_detection import run_health_check
from src.ingest import is_paused

_CAPABILITIES = [
    "drift", "contradictions", "silence", "activation", "record",
    "staging", "network", "cascade", "hypotheses", "topic_drift",
    "propagation_dynamics", "meta_detection", "threat_model",
    "operator_state", "submit_claim", "questions", "synthesis",
    "credibility", "rejections",
]


class OssHealth(ApiHandler):
    """OSS V2 service health check.

    URL: GET /api/plugins/oss/api_oss_health
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict:
        try:
            conn = get_conn()
            init_db(conn)

            cur = conn.cursor()

            # Claim counts by trust_level
            cur.execute(
                "SELECT trust_level, COUNT(*) AS n FROM claims GROUP BY trust_level"
            )
            counts = {r["trust_level"]: r["n"] for r in cur.fetchall()}

            # Source count
            cur.execute("SELECT COUNT(*) AS n FROM sources")
            src_count = cur.fetchone()["n"]

            # Last ingestion timestamp
            cur.execute("SELECT MAX(extracted_at) AS last FROM claims")
            last_row = cur.fetchone()
            last_ingestion = last_row["last"] if last_row else None

            # Health report from meta_detection
            health_report = run_health_check(conn)

            conn.close()

            return {
                "ok": True,
                "status": health_report.get("overall_status", "UNKNOWN"),
                "claims": {
                    "total": sum(counts.values()),
                    "staged": counts.get("STAGED", 0),
                    "promoted": counts.get("PROMOTED", 0),
                    "irrelevant": counts.get("IRRELEVANT", 0),
                    "returned": counts.get("RETURNED_TO_STAGED", 0),
                    "falsified": counts.get("FALSIFIED", 0),
                },
                "sources_count": src_count,
                "ingest_paused": is_paused(),
                "last_ingestion": last_ingestion,
                "health_report": health_report,
                "version": "2.0.0",
                "capabilities": _CAPABILITIES,
            }

        except Exception as e:
            return {"ok": False, "error": str(e)}
