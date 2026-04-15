"""oss_synthesize — Ask the OSS ledger a question and receive an evidence-based synthesis."""

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


def _oss_error(prefix: str, e: Exception) -> Response:
    return Response(message=f"[OSS] {prefix}: {e}", break_loop=False)


class OssSynthesize(Tool):
    """
    Ask the OSS ledger a question and receive an evidence-based synthesis.

    Claims are retrieved by semantic similarity and weighted by source
    credibility and recency. LLM writes a 2-paragraph synthesis with
    claim ID citations. Falls back to deterministic summary on LLM failure.

    Args:
        question (str): The analyst question to synthesize evidence for [required]
        limit    (int): Max claims to retrieve (default 40)
    """

    async def execute(self, **kwargs) -> Response:
        question = (self.args.get("question") or "").strip()
        limit    = int(self.args.get("limit") or 40)
        print(f"[OSS] oss_synthesize: question={question[:60]!r}", flush=True)

        if not question:
            return Response(message="[OSS] oss_synthesize requires question", break_loop=False)

        try:
            _ensure_plugin()
            from src.synthesis import synthesize
            conn   = _get_conn()
            result = synthesize(conn, question, limit_claims=limit)
            conn.close()
        except Exception as e:
            return _oss_error("oss_synthesize failed", e)

        synthesis_text = result.get("synthesis_text", "(no synthesis available)")
        n_supporting   = len(result.get("supporting", []))
        n_contra       = len(result.get("contradicting", []))
        n_neutral      = len(result.get("neutral", []))
        sources        = result.get("sources_used", [])

        lines = [
            "OSS Evidence Synthesis",
            f"Question: {question}",
            f"Evidence: {n_supporting} supporting, {n_contra} contradicting, {n_neutral} neutral",
            f"Sources consulted: {', '.join(sources[:8]) if sources else 'none'}",
            "",
            synthesis_text,
        ]
        return Response(message="\n".join(lines), break_loop=False)
