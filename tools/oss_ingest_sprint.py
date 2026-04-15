"""
oss_ingest_sprint — Trigger a bounded OSS ingestion run and report what was found.

Use when the ledger is empty or stale and you need fresh intelligence before
analysis. Fetches all monitored RSS sources, extracts claims via LLM, deduplicates,
and returns a summary of what was ingested. After the sprint completes, use
oss_topic or oss_synthesize to query the new claims.
"""

import asyncio
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


class OssIngestSprint(Tool):
    """
    Run a bounded OSS ingestion sprint — fetch RSS sources, extract claims via LLM,
    deduplicate, and return a summary of what was found.

    Use when the intelligence ledger is empty or stale. The sprint runs for up to
    duration_minutes, then reports new claims found. After the sprint, use oss_topic
    or oss_synthesize to query the new data.

    The background ingestion loop is also started so the ledger continues to update
    every 30 minutes automatically.

    Args:
        topic            (str): Topic tag to highlight in results (e.g. 'iran-hormuz')
        duration_minutes (int): Max runtime in minutes (default: 7, max: 10)
    """

    async def execute(self, **kwargs) -> Response:
        _ensure_plugin()
        topic    = (self.args.get("topic") or "").strip()
        duration = min(max(int(self.args.get("duration_minutes") or 7), 1), 10)

        print(f"[OSS] oss_ingest_sprint: topic={topic!r} duration={duration}m", flush=True)

        try:
            from src.db import get_conn, init_db
            from src.ingest import run_once, start_background_loop

            conn = get_conn()
            init_db(conn)

            # Baseline counts
            before_total = conn.execute(
                "SELECT COUNT(*) FROM claims WHERE trust_level != 'IRRELEVANT'"
            ).fetchone()[0]
            before_topic = 0
            if topic:
                before_topic = conn.execute(
                    "SELECT COUNT(*) FROM claims WHERE topic_tags LIKE ? AND trust_level != 'IRRELEVANT'",
                    (f"%{topic}%",)
                ).fetchone()[0]
            conn.close()

        except Exception as e:
            return _oss_error("sprint setup failed", e)

        # Run ingestion with timeout
        timed_out = False
        ingest_result = {}
        try:
            ingest_result = await asyncio.wait_for(
                asyncio.to_thread(run_once),
                timeout=duration * 60
            )
        except asyncio.TimeoutError:
            timed_out = True
            print(f"[OSS] sprint timed out after {duration}m — partial results available", flush=True)
        except Exception as e:
            import traceback
            print(f"[OSS] sprint run_once error: {traceback.format_exc()}", flush=True)
            return _oss_error("sprint ingestion failed", e)

        # Start background loop so ledger stays current going forward
        try:
            _ensure_plugin()
            from src.ingest import start_background_loop
            start_background_loop()
        except Exception as e:
            print(f"[OSS] sprint: background loop start warning: {e}", flush=True)

        # Results
        try:
            _ensure_plugin()
            from src.db import get_conn

            conn = get_conn()
            after_total = conn.execute(
                "SELECT COUNT(*) FROM claims WHERE trust_level != 'IRRELEVANT'"
            ).fetchone()[0]

            new_total = after_total - before_total

            after_topic = 0
            new_topic   = 0
            if topic:
                after_topic = conn.execute(
                    "SELECT COUNT(*) FROM claims WHERE topic_tags LIKE ? AND trust_level != 'IRRELEVANT'",
                    (f"%{topic}%",)
                ).fetchone()[0]
                new_topic = after_topic - before_topic

            # Fetch sample of new/recent claims
            if topic:
                recent = conn.execute("""
                    SELECT c.claim_text, c.trust_level, c.technique_class,
                           c.extracted_at, s.name AS source_name
                    FROM claims c
                    JOIN sources s ON s.id = c.source_id
                    WHERE c.topic_tags LIKE ? AND c.trust_level != 'IRRELEVANT'
                    ORDER BY c.extracted_at DESC LIMIT 8
                """, (f"%{topic}%",)).fetchall()
            else:
                recent = conn.execute("""
                    SELECT c.claim_text, c.trust_level, c.technique_class,
                           c.extracted_at, s.name AS source_name
                    FROM claims c
                    JOIN sources s ON s.id = c.source_id
                    WHERE c.trust_level != 'IRRELEVANT'
                    ORDER BY c.extracted_at DESC LIMIT 8
                """).fetchall()

            # Source breakdown for this sprint
            source_counts = conn.execute("""
                SELECT s.name, COUNT(*) AS n
                FROM claims c JOIN sources s ON s.id = c.source_id
                WHERE c.trust_level != 'IRRELEVANT'
                GROUP BY s.name ORDER BY n DESC LIMIT 6
            """).fetchall()

            conn.close()

        except Exception as e:
            return _oss_error("sprint result query failed", e)

        # Format report
        status_str = f"timed out after {duration}m (partial)" if timed_out else "complete"
        lines = [
            f"OSS Ingestion Sprint — {status_str}",
            f"New claims: {new_total}  |  Ledger total: {after_total}",
        ]
        if topic:
            lines.append(f"Claims matching '{topic}': {new_topic} new  |  {after_topic} total")
        lines.append("")

        if source_counts:
            lines.append("Sources with claims:")
            for row in source_counts:
                lines.append(f"  · {row['name']}: {row['n']}")
            lines.append("")

        if recent:
            header = f"Recent claims" + (f" for '{topic}'" if topic else "")
            lines.append(f"{header} ({len(recent)} shown):")
            for r in recent:
                r = dict(r)
                trust  = r.get("trust_level", "?")
                text   = (r.get("claim_text") or "")[:160]
                source = r.get("source_name", "?")
                tech   = r.get("technique_class") or "—"
                lines.append(f"  [{trust}|{tech}] {text}")
                lines.append(f"    — {source}")
            lines.append("")
        else:
            lines.append("No claims found. Possible causes:")
            lines.append("  · LLM endpoint unreachable (check http://host.docker.internal:1234)")
            lines.append("  · RSS sources returned no new items")
            lines.append("  · Sprint timed out before extraction completed")
            lines.append("")

        if after_total > 0:
            if topic:
                lines.append(
                    f"Next steps: oss_topic(topic='{topic}') to query claims, "
                    f"oss_synthesize(question='...') for evidence synthesis, "
                    f"or swarmfish_predict with the findings as context."
                )
            else:
                lines.append(
                    "Next steps: oss_list_topics() to see monitored topics, "
                    "then oss_topic(topic='...') or oss_synthesize(question='...') to query."
                )

        lines.append("")
        lines.append("Background ingestion loop started — ledger will update every 30 minutes.")

        return Response(message="\n".join(lines), break_loop=False)
