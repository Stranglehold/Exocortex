"""
hedge_aggregation.py — per-source-per-topic hedge concentration signal.

Computes the narrative_campaign / unverifiable_stream signals by aggregating
claims over a rolling window, comparing each (source, topic) against the
source's own baseline, and gating the signal class by source_type.

Runs periodically (after each ingestion pass). Writes to source_topic_signals.

Spec: specs/HEDGE_PATTERN_SPEC_L3.md
Design note: specs/HEDGE_PATTERN_DESIGN_NOTE.md
"""

import os
import logging

log = logging.getLogger(__name__)

# Thresholds — first-pass guesses, tunable via env vars
WINDOW_DAYS     = int(os.environ.get("OSS_HEDGE_WINDOW_DAYS", "7"))
MIN_CLAIM_COUNT = int(os.environ.get("OSS_HEDGE_MIN_CLAIMS", "5"))
MIN_TOPIC_RATE  = float(os.environ.get("OSS_HEDGE_MIN_RATE", "0.4"))
MIN_DEVIATION   = float(os.environ.get("OSS_HEDGE_MIN_DEVIATION", "0.25"))


def compute_narrative_signals(conn) -> int:
    """
    Recompute the source_topic_signals table for the current window.
    Returns the count of (source, topic) pairs that fired a non-null signal.

    The query:
      1. Counts (source, topic) claim totals and insidious-pattern matches
         over a rolling window.
      2. Computes per-source baseline as total_insidious / total_claims.
      3. Gates the signal class by source_type: institutional sources get
         narrative_campaign, social sources get unverifiable_stream.
      4. Filters by claim_count minimum + topic_rate minimum + deviation
         minimum so we only fire when there's real signal.
    """
    with conn.cursor() as cur:
        # Delete stale rows for the current window (recomputed each pass)
        cur.execute(
            "DELETE FROM source_topic_signals WHERE window_days = %s",
            (WINDOW_DAYS,),
        )

        # Single INSERT ... SELECT with the full aggregation logic
        cur.execute("""
            WITH topic_stats AS (
                SELECT
                    c.source_id,
                    s.source_type,
                    unnest(c.topic_tags) AS topic,
                    COUNT(*) AS claim_count,
                    COUNT(*) FILTER (
                        WHERE c.certainty = 'hedged'
                          AND c.attribution = 'vague'
                          AND c.quoted_directly IN ('false', 'unknown')
                    ) AS insidious_count
                FROM claims c
                JOIN sources s ON c.source_id = s.id
                WHERE c.extracted_at >= NOW() - (%s || ' days')::interval
                GROUP BY c.source_id, s.source_type, unnest(c.topic_tags)
            ),
            source_baseline AS (
                SELECT
                    source_id,
                    SUM(insidious_count)::float / NULLIF(SUM(claim_count), 0) AS baseline_rate
                FROM topic_stats
                GROUP BY source_id
            )
            INSERT INTO source_topic_signals (
                source_id, topic, source_type, claim_count, insidious_count,
                topic_rate, baseline_rate, deviation, signal_class,
                computed_at, window_days
            )
            SELECT
                ts.source_id,
                ts.topic,
                ts.source_type,
                ts.claim_count,
                ts.insidious_count,
                (ts.insidious_count::float / NULLIF(ts.claim_count, 0)) AS topic_rate,
                COALESCE(sb.baseline_rate, 0) AS baseline_rate,
                (ts.insidious_count::float / NULLIF(ts.claim_count, 0))
                    - COALESCE(sb.baseline_rate, 0) AS deviation,
                CASE
                    WHEN ts.claim_count < %s THEN NULL
                    WHEN (ts.insidious_count::float / NULLIF(ts.claim_count, 0)) < %s THEN NULL
                    WHEN (ts.insidious_count::float / NULLIF(ts.claim_count, 0))
                         - COALESCE(sb.baseline_rate, 0) < %s THEN NULL
                    WHEN ts.source_type IN ('official', 'wire', 'outlet') THEN 'narrative_campaign'
                    WHEN ts.source_type = 'social' THEN 'unverifiable_stream'
                    ELSE 'unclassified'
                END AS signal_class,
                NOW() AS computed_at,
                %s AS window_days
            FROM topic_stats ts
            LEFT JOIN source_baseline sb USING (source_id)
            ON CONFLICT (source_id, topic, window_days) DO NOTHING
        """, (
            WINDOW_DAYS,
            MIN_CLAIM_COUNT, MIN_TOPIC_RATE, MIN_DEVIATION,
            WINDOW_DAYS,
        ))

        cur.execute("""
            SELECT COUNT(*) AS n FROM source_topic_signals
            WHERE window_days = %s AND signal_class IS NOT NULL
        """, (WINDOW_DAYS,))
        row = cur.fetchone()
        n_fired = row['n'] if row else 0

    conn.commit()
    log.info(f"[HEDGE-AGG] Recomputed narrative signals — {n_fired} (source, topic) pairs fired")
    return n_fired
