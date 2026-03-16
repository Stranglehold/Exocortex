"""
social_ingest.py — X/Twitter social monitor scraper

Uses Playwright (headless Chromium) to log into X via stored cookie tokens,
searches each active social_monitor query, and feeds results through the
standard OSS claim pipeline: embed → dedup → classify_technique → assign_topics → INSERT.

Credentials from environment:
    X_AUTH_TOKEN   — auth_token cookie value from twitter.com
    X_CT0_TOKEN    — ct0 cookie value from twitter.com

To get these: log into X in a browser, open DevTools → Application →
Cookies → https://twitter.com, copy the values for auth_token and ct0.

Graceful fallback: if credentials are not set or Playwright fails,
run_social_monitors_sync() logs a warning and returns 0 without crashing.
"""

import os
import asyncio
import logging
from datetime import datetime, timezone

from ingest import embed, is_duplicate, add_to_faiss, save_faiss

log = logging.getLogger(__name__)

X_AUTH_TOKEN = os.environ.get("X_AUTH_TOKEN", "")
X_CT0_TOKEN  = os.environ.get("X_CT0_TOKEN", "")

# Source record for X/Twitter — auto-created if absent
X_SOURCE_NAME = "X/Twitter"
_x_source_id: int | None = None


def _get_or_create_x_source(conn) -> int:
    """Return the source_id for X/Twitter, creating the row if needed."""
    global _x_source_id
    if _x_source_id is not None:
        return _x_source_id
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM sources WHERE name = %s", (X_SOURCE_NAME,))
        row = cur.fetchone()
        if row:
            _x_source_id = row['id']
            return _x_source_id
        cur.execute(
            """
            INSERT INTO sources (name, url, source_type, cluster, confidence_score)
            VALUES (%s, %s, 'social', 'independent', 0.5)
            ON CONFLICT (url) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            (X_SOURCE_NAME, "https://x.com"),
        )
        _x_source_id = cur.fetchone()['id']
        conn.commit()
        log.info(f"[X INGEST] Created X/Twitter source (id={_x_source_id})")
    return _x_source_id


async def _scrape_x_query(query: str, count: int = 20) -> list[dict]:
    """
    Launch headless Chromium, inject X auth cookies, run a search,
    extract up to `count` tweets.

    Returns list of dicts: {text, author, url, published_at}
    """
    if not X_AUTH_TOKEN or not X_CT0_TOKEN:
        log.warning("[X INGEST] X_AUTH_TOKEN or X_CT0_TOKEN not set — skipping scrape")
        return []

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        log.warning("[X INGEST] playwright not installed — skipping scrape")
        return []

    results = []
    search_url = f"https://x.com/search?q={query.replace(' ', '%20')}&f=live"

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            ctx = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            # Inject auth cookies so we appear logged in
            await ctx.add_cookies([
                {
                    "name": "auth_token",
                    "value": X_AUTH_TOKEN,
                    "domain": ".twitter.com",
                    "path": "/",
                    "secure": True,
                    "httpOnly": True,
                },
                {
                    "name": "ct0",
                    "value": X_CT0_TOKEN,
                    "domain": ".twitter.com",
                    "path": "/",
                    "secure": True,
                },
            ])
            page = await ctx.new_page()
            await page.goto(search_url, wait_until="networkidle", timeout=30_000)
            await page.wait_for_timeout(3000)

            seen_urls: set[str] = set()
            retries = 0
            while len(results) < count and retries < 5:
                # Extract visible tweet articles
                tweets = await page.query_selector_all('article[data-testid="tweet"]')
                for tweet in tweets:
                    if len(results) >= count:
                        break
                    try:
                        # Text
                        text_el = await tweet.query_selector('[data-testid="tweetText"]')
                        if not text_el:
                            continue
                        text = (await text_el.inner_text()).strip()
                        if not text:
                            continue

                        # Permalink
                        link_el = await tweet.query_selector('a[href*="/status/"]')
                        href = await link_el.get_attribute("href") if link_el else None
                        url = f"https://x.com{href}" if href and href.startswith("/") else href
                        if url in seen_urls:
                            continue
                        seen_urls.add(url or text[:64])

                        # Author handle
                        author_el = await tweet.query_selector('[data-testid="User-Name"] span')
                        author = (await author_el.inner_text()).strip() if author_el else "unknown"

                        # Timestamp
                        time_el = await tweet.query_selector("time")
                        pub_at_str = await time_el.get_attribute("datetime") if time_el else None
                        try:
                            pub_at = datetime.fromisoformat(pub_at_str.replace("Z", "+00:00")) if pub_at_str else datetime.now(timezone.utc)
                        except Exception:
                            pub_at = datetime.now(timezone.utc)

                        results.append({
                            "text": text,
                            "author": author,
                            "url": url or f"https://x.com/search?q={query}",
                            "published_at": pub_at,
                        })
                    except Exception as inner_e:
                        log.debug(f"[X INGEST] Tweet parse error: {inner_e}")
                        continue

                if len(results) < count:
                    # Scroll down for more
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)
                    retries += 1

            await browser.close()

    except Exception as e:
        log.error(f"[X INGEST] Playwright scrape failed: {e}")

    log.info(f"[X INGEST] Scraped {len(results)} tweets for query={query!r}")
    return results


def _classify_technique(text: str) -> str:
    """
    Simple heuristic technique classifier for social media posts.
    Full LLM classification is expensive per-tweet; use keyword signals.
    Returns one of: presuasion|fracture|emergent|direct|none
    """
    tl = text.lower()
    if any(w in tl for w in ["breaking", "exclusive", "source says", "report:"]):
        return "direct"
    if any(w in tl for w in ["imagine if", "what if", "could this mean", "some say"]):
        return "presuasion"
    if any(w in tl for w in ["both sides", "divide", "they don't want you", "mainstream won't"]):
        return "fracture"
    return "none"


def _assign_topics(text: str, provided_tags: list[str], conn) -> list[str]:
    """
    Assign topic tags: start with any caller-provided tags that exist in topics table,
    then skip LLM call (too expensive per tweet at scale).
    """
    if not provided_tags:
        return []
    with conn.cursor() as cur:
        cur.execute(
            "SELECT tag FROM topics WHERE tag = ANY(%s) AND active = TRUE",
            (provided_tags,),
        )
        return [r['tag'] for r in cur.fetchall()]


def _ingest_tweets(conn, tweets: list[dict], topic_tags: list[str], source_id: int) -> tuple[int, int]:
    """
    Feed a list of raw tweet dicts through the OSS claim pipeline.
    Returns (staged_count, skipped_count).
    """
    staged = 0
    skipped = 0

    valid_tags = _assign_topics("", topic_tags, conn)

    for tweet in tweets:
        text = tweet['text']
        vector = embed(text)

        if is_duplicate(vector):
            skipped += 1
            continue

        technique = _classify_technique(text)

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO claims
                    (source_id, raw_text, claim_text, article_url, article_title,
                     topic_tags, technique_class, published_at, staging_confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, faiss_id
                """,
                (
                    source_id,
                    text,
                    text,
                    tweet['url'],
                    f"@{tweet['author']}",
                    valid_tags,
                    technique,
                    tweet['published_at'],
                    0.0,
                ),
            )
            row = cur.fetchone()
            claim_id = row['id']

            # Update topic staged counts
            for tag in valid_tags:
                cur.execute(
                    "UPDATE topics SET total_staged_count = total_staged_count + 1 WHERE tag = %s",
                    (tag,),
                )

        add_to_faiss(vector, claim_id)
        staged += 1

    if staged > 0:
        conn.commit()
        save_faiss()

    return staged, skipped


def run_query_sync(conn, query: str, topic_tags: list[str], count: int = 10) -> tuple[int, int]:
    """
    Synchronous entry point for on-demand X search from app.py.
    Returns (staged, skipped).
    """
    source_id = _get_or_create_x_source(conn)
    tweets = asyncio.run(_scrape_x_query(query, count))
    if not tweets:
        return 0, 0
    return _ingest_tweets(conn, tweets, topic_tags, source_id)


def _monitors_due(conn) -> list[dict]:
    """Return active social monitors that are due for a run."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT * FROM social_monitors
            WHERE active = TRUE
              AND (
                  last_run_at IS NULL
                  OR last_run_at + (interval_minutes || ' minutes')::interval <= NOW()
              )
            ORDER BY last_run_at NULLS FIRST
            """,
        )
        return [dict(r) for r in cur.fetchall()]


async def _run_social_monitors_async(conn) -> int:
    """Run all due social monitors. Returns total claims staged."""
    source_id = _get_or_create_x_source(conn)
    monitors = _monitors_due(conn)
    if not monitors:
        return 0

    total_staged = 0
    for monitor in monitors:
        query      = monitor['query']
        topic_tags = monitor.get('topic_tags') or []
        count      = 20  # tweets per monitor run

        log.info(f"[X INGEST] Running monitor {monitor['id']}: {monitor['display_name']!r} (query={query!r})")
        tweets = await _scrape_x_query(query, count)
        staged, skipped = _ingest_tweets(conn, tweets, topic_tags, source_id)
        total_staged += staged

        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE social_monitors
                SET last_run_at = NOW(),
                    result_count = result_count + %s
                WHERE id = %s
                """,
                (staged, monitor['id']),
            )
        conn.commit()
        log.info(f"[X INGEST] Monitor {monitor['id']} complete: staged={staged}, skipped={skipped}")

    return total_staged


def run_social_monitors_sync(conn) -> int:
    """
    Synchronous wrapper for the scheduler loop in ingest.py.
    Returns total claims staged across all monitors.
    """
    try:
        return asyncio.run(_run_social_monitors_async(conn))
    except Exception as e:
        log.warning(f"[X INGEST] social monitors run failed: {e}")
        return 0
