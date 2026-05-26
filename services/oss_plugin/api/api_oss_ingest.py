"""
api_oss_ingest.py — Ingestion pipeline control

URL: POST /api/plugins/oss/api_oss_ingest

Input: {action: str}

Actions:
  run     — trigger a single ingestion pass immediately
  pause   — pause background ingestion
  resume  — resume background ingestion
  status  — return current paused state
"""

import sys
sys.path.insert(0, "/a0/usr/plugins/oss")

from helpers.api import ApiHandler, Request

from src.db import get_conn, init_db
from src.ingest import run_once, is_paused, set_paused, start_background_loop, _ingest_lock


class OssIngest(ApiHandler):
    """Ingestion pipeline control — run, pause, resume, status.

    URL: POST /api/plugins/oss/api_oss_ingest
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict:
        action = (input.get("action") or "").strip()
        if not action:
            return {"ok": False, "error": "action is required"}

        try:
            if action == "status":
                return {"ok": True, "paused": is_paused()}

            elif action == "pause":
                set_paused(True)
                return {"ok": True, "paused": True}

            elif action == "resume":
                set_paused(False)
                start_background_loop()
                return {"ok": True, "paused": False}

            elif action == "run":
                # Run the pass in the background — a full RSS+LLM cycle takes
                # minutes; blocking the HTTP request times out the browser fetch.
                # Returns immediately; the UI polls health for progress.
                import threading, logging

                def _bg_run():
                    try:
                        c = get_conn()
                        init_db(c)
                        with _ingest_lock:
                            run_once(c)
                        c.close()
                    except Exception as exc:
                        logging.getLogger("[INGEST]").warning(f"manual run failed: {exc}")

                threading.Thread(target=_bg_run, daemon=True, name="oss-ingest-manual").start()
                return {"ok": True, "action": "run", "started": True}

            else:
                return {"ok": False, "error": f"Unknown action: {action!r}"}

        except Exception as e:
            return {"ok": False, "error": str(e)}
