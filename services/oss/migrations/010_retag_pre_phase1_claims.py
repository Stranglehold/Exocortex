"""
010_retag_pre_phase1_claims.py — one-shot migration to re-tag historical claims
                                   that were assigned bad topics by the pre-Phase-1
                                   LLM ingest prompt.

SFA-001 findings 2 and 10:
- 27 PROMOTED claims have 3+ topic tags, some combining obviously unrelated
  topics (iran-hormuz + private-credit + test-verify). These are pre-Phase-1
  tagging errors. The newer prompt with topic descriptions (Phase 1 fix)
  would tag these correctly — but only for new claims.
- 7242 claims are stuck in STAGED because the pre-Phase-1 LLM produced empty
  topic lists for them. Outlet-tier promotion requires non-empty topics, so
  these claims have no path forward.

This migration re-runs process_article() with the current (post-Phase-1)
topic definitions against two populations:
  A) Multi-tag polluted claims (3+ tags): re-tag and update
  B) A bounded batch of empty-tag STAGED claims from the last 48 hours:
     re-tag, and if non-empty, update (promotion happens on the next
     auto_promote_staged cycle).

Older stuck claims (>48 hours) are left for a separate overnight batch —
this script is bounded so it can run in a single session without starving
other LLM workloads.

Usage:
    docker exec oss_app python /app/src/migrations/010_retag_pre_phase1_claims.py [--polluted-only] [--dry-run]

Options:
    --polluted-only   skip population B, re-tag only the 3+ tag claims
    --dry-run         compute changes but don't write to DB
    --max-empty N     limit population B to N claims (default 200)
"""

import sys
import os
import argparse
import json
from datetime import datetime, timezone

# Allow running from the /app/src directory where ingest.py lives
sys.path.insert(0, '/app/src')

import psycopg2
import psycopg2.extras

from ingest import process_article, get_active_topics, DB_URL
import ingest as _ingest

# The migration runs in a fresh Python process inside the oss_app container.
# ingest.py's module-level init sets _stop_event from OSS_INGEST_PAUSED, and
# the container is started with OSS_INGEST_PAUSED=true so that the Flask
# scheduler starts paused until the analyst resumes it via /admin/ingest/resume.
# Resume only clears the Flask process's in-memory flag, not the env var, so
# this migration script sees _stop_event still set on import. Clear it here
# for the migration's duration — we want process_article to actually run.
_ingest._stop_event.clear()


def _log(msg: str):
    ts = datetime.now(timezone.utc).isoformat()[:19]
    print(f"[RETAG {ts}] {msg}", flush=True)


def get_polluted_multi_tag_claims(conn) -> list[dict]:
    """Population A: claims with 3+ topic tags (very likely polluted)."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT id, claim_text, topic_tags, trust_level
            FROM claims
            WHERE array_length(topic_tags, 1) >= 3
            ORDER BY id
        """)
        return cur.fetchall()


def get_stuck_empty_staged_claims(conn, limit: int) -> list[dict]:
    """Population B: empty-tag STAGED claims from the last 48 hours, capped."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT id, claim_text, topic_tags, trust_level, article_title
            FROM claims
            WHERE trust_level = 'STAGED'
              AND (topic_tags IS NULL OR array_length(topic_tags, 1) IS NULL)
              AND extracted_at >= NOW() - INTERVAL '48 hours'
            ORDER BY extracted_at DESC
            LIMIT %s
        """, (limit,))
        return cur.fetchall()


def retag_claim(claim: dict, topics_list: list) -> list[str]:
    """Re-run process_article on a single claim's text and return new tags.
    Uses the claim_text as both the article_text and article_title, which
    is narrower than a full article but sufficient for topic classification.
    Returns the list of new topic tags (possibly empty)."""
    # process_article expects (article_text, article_title, available_topics)
    # — we feed the claim text as both text and title. If process_article
    # returns an empty list, the claim_text didn't match any topic under the
    # new prompt, which is a valid outcome.
    results = process_article(
        article_text=claim['claim_text'],
        article_title=claim.get('article_title') or claim['claim_text'][:80],
        available_topics=topics_list,
    )
    if not results:
        return []
    # process_article returns [{claim, technique, topics}, ...] — one entry
    # per extracted factual claim. For a single-claim input we should get
    # one entry. Merge all topics across all entries just in case.
    merged: set[str] = set()
    for r in results:
        for t in r.get('topics', []):
            merged.add(t)
    return sorted(merged)


def run(polluted_only: bool, dry_run: bool, max_empty: int) -> dict:
    _log(f"Starting retag migration — polluted_only={polluted_only} dry_run={dry_run} max_empty={max_empty}")

    conn = psycopg2.connect(DB_URL)
    topics_list = get_active_topics()
    _log(f"Loaded {len(topics_list)} active topics:")
    for t in topics_list:
        desc = (t.get('description') or '')[:80]
        _log(f"  - {t['tag']}: {desc}")

    summary = {
        'polluted_examined': 0,
        'polluted_updated': 0,
        'polluted_cleared': 0,  # new tags are empty — claim has no topic
        'polluted_unchanged': 0,
        'empty_examined': 0,
        'empty_tagged': 0,
        'empty_still_empty': 0,
        'errors': 0,
    }

    # ---- Population A: polluted multi-tag claims
    polluted = get_polluted_multi_tag_claims(conn)
    _log(f"Population A (3+ tags): {len(polluted)} claims")

    for claim in polluted:
        summary['polluted_examined'] += 1
        old_tags = list(claim['topic_tags'] or [])
        try:
            new_tags = retag_claim(claim, topics_list)
        except Exception as e:
            _log(f"  ERROR retagging claim {claim['id']}: {e}")
            summary['errors'] += 1
            continue

        if set(new_tags) == set(old_tags):
            summary['polluted_unchanged'] += 1
            continue

        change_desc = f"  claim {claim['id']}: {old_tags} -> {new_tags}"
        if not new_tags:
            summary['polluted_cleared'] += 1
            change_desc += " (CLEARED)"
        else:
            summary['polluted_updated'] += 1

        _log(change_desc)

        if not dry_run:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE claims SET topic_tags = %s WHERE id = %s",
                    (new_tags, claim['id'])
                )
            conn.commit()

    # ---- Population B: empty-tag STAGED claims (recent only)
    if not polluted_only:
        empty = get_stuck_empty_staged_claims(conn, max_empty)
        _log(f"Population B (empty-tag STAGED, last 48h, capped at {max_empty}): {len(empty)} claims")

        for claim in empty:
            summary['empty_examined'] += 1
            try:
                new_tags = retag_claim(claim, topics_list)
            except Exception as e:
                _log(f"  ERROR retagging claim {claim['id']}: {e}")
                summary['errors'] += 1
                continue

            if not new_tags:
                summary['empty_still_empty'] += 1
                continue

            summary['empty_tagged'] += 1
            _log(f"  claim {claim['id']}: [] -> {new_tags}")

            if not dry_run:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE claims SET topic_tags = %s WHERE id = %s",
                        (new_tags, claim['id'])
                    )
                conn.commit()

    conn.close()

    _log("==================== SUMMARY ====================")
    for k, v in summary.items():
        _log(f"  {k}: {v}")
    return summary


def main():
    ap = argparse.ArgumentParser(description="Re-tag pre-Phase-1 claims")
    ap.add_argument('--polluted-only', action='store_true',
                    help="Only re-tag claims with 3+ existing tags, skip empty-tag STAGED claims")
    ap.add_argument('--dry-run', action='store_true',
                    help="Compute changes without writing to DB")
    ap.add_argument('--max-empty', type=int, default=200,
                    help="Maximum empty-tag claims to process (default 200)")
    args = ap.parse_args()
    summary = run(args.polluted_only, args.dry_run, args.max_empty)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
