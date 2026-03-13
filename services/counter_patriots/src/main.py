"""
main.py — Counter-Patriots process entrypoint.

Starts the ingestion scheduler in a background thread,
then runs the Flask API in the foreground.
"""

import threading
import logging
import os

log = logging.getLogger(__name__)

def start_background_scheduler():
    """Run ingestion scheduler in background thread."""
    from ingest import run_scheduler
    t = threading.Thread(target=run_scheduler, daemon=True, name="ingest-scheduler")
    t.start()
    log.info("[main] Ingestion scheduler started in background")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='[CP] %(message)s', force=True)

    log.info("[main] Counter-Patriots starting...")
    start_background_scheduler()

    port = int(os.environ.get("CP_PORT", "7731"))
    log.info(f"[main] Flask API starting on port {port}")

    from app import app
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
