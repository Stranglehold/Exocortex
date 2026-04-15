"""oss_ingest_pause — Pause the OSS automated RSS ingestion pipeline."""

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


class OssIngestPause(Tool):
    """
    Pause the OSS automated RSS ingestion pipeline.

    Stops the scheduler from issuing new LLM extraction calls. No state is
    lost. Use oss_ingest_resume to restart.

    No arguments required.
    """

    async def execute(self, **kwargs) -> Response:
        print("[OSS] oss_ingest_pause: pausing ingestion pipeline", flush=True)
        try:
            _ensure_plugin()
            from src.ingest import set_paused
            set_paused(True)
        except Exception as e:
            return _oss_error("oss_ingest_pause failed", e)

        return Response(
            message="[OSS] Ingestion pipeline paused. No new extraction calls will be issued until resumed.",
            break_loop=False,
        )
