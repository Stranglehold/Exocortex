"""oss_ingest_resume — Resume the OSS automated RSS ingestion pipeline."""

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


def _oss_error(prefix: str, e: Exception) -> Response:
    return Response(message=f"[OSS] {prefix}: {e}", break_loop=False)


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
