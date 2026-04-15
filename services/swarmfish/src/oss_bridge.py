"""
oss_bridge.py — SWARMFISH → OSS context bridge

Queries the OSS claim store for promoted intelligence matching the
prediction domain, formats it as a structured context block, and
returns it for injection before profiles run.

Graceful fallback: if OSS is unreachable or has no matching claims,
returns None and logs a warning. The predict pipeline continues
without OSS context.

SFA-001 P4.1 / Phase 2.5 — sampling diversity:
  The prior implementation took the newest 12 claims by published_at.
  ST-007 validation (session a11d07e0) showed this biased the committee
  toward whatever was most recent, obscuring the full situation. This
  version fetches a larger pool (up to 60) and composes the final 24-claim
  context from three distinct slices:
    (a) 10 newest by published_at — "what just arrived"
    (b) 10 matching question-specific keywords — "what's directly relevant"
    (c) 4 diverse oldest-of-new-batch — "what's been sitting as background"
  Diversification happens AFTER the server-side PROMOTED filter so we
  never degrade input quality; we only broaden the sampling lens.
"""

import re
import random
import httpx
import config

# Maps SWARMFISH domain names to OSS topic tags.
# Add entries here as new topics are seeded in OSS.
DOMAIN_TO_TOPICS = {
    "geopolitical_risk": ["iran-hormuz", "iran"],
    "commodities":       ["iran-hormuz"],
    "market_structure":  [],
    "technology":        [],
    "credit_cycles":     [],
    "general":           [],
}

# SFA-001 P4.1 — keyword expansion map. When the analyst asks a question
# about a topic, the bridge extracts topic-adjacent keywords from the
# question and uses them to preferentially include claims that actually
# engage with those concepts, not just the newest ones on the topic.
_KEYWORD_FAMILIES = {
    'iran':    {'iran', 'iranian', 'tehran', 'irgc', 'khamenei', 'pezeshkian',
                'mojtaba', 'vahidi', 'jaffari', 'assembly of experts'},
    'hormuz':  {'hormuz', 'strait', 'persian gulf', 'arabian sea', 'gulf of oman',
                'centcom', 'tanker', 'blockade', 'mine', 'mining', 'imo',
                'carrier strike group', 'csg', 'gerald r. ford', 'abraham lincoln'},
    'oil':     {'oil', 'crude', 'brent', 'wti', 'opec', 'barrel', 'insurance',
                'lloyd', 'war risk', 'war-risk'},
    'nuclear': {'nuclear', 'enrichment', 'uranium', 'iaea', 'jcpoa', 'heu',
                'centrifuge', 'fordow', 'natanz'},
    'israel':  {'israel', 'israeli', 'idf', 'mossad', 'netanyahu'},
    'houthi':  {'houthi', 'houthis', 'yemen', 'ansar allah'},
    'hezbollah':{'hezbollah', 'lebanon', 'lebanese', 'nasrallah'},
    'russia':  {'russia', 'russian', 'kremlin', 'putin', 'moscow'},
    'china':   {'china', 'chinese', 'beijing', 'xi jinping', 'pla'},
    'ukraine': {'ukraine', 'ukrainian', 'kyiv', 'zelensky'},
}

_GATE_STOPWORDS = frozenset({
    'for', 'the', 'a', 'an', 'of', 'and', 'or', 'in', 'on', 'at', 'to',
    'is', 'are', 'was', 'were', 'be', 'will', 'what', 'when', 'how', 'why',
    'who', 'where', 'which', 'this', 'that', 'these', 'those', 'with',
    'from', 'by', 'as', 'situation', 'current', 'assess', 'about',
    'most', 'likely', 'trajectory', 'conditions', 'change', 'assessment',
})

# Pool size we fetch from OSS per topic before sampling. Larger than the
# final context cap so we have room to diversify.
_POOL_PER_TOPIC = 30

# Final context budget — the number of claims the bridge ultimately injects.
# Was 12 in the pre-P4.1 version; 24 gives each profile more substrate
# while staying under the ~4KB context block that fits comfortably in the
# profile prompt.
_CONTEXT_CAP_NEWEST  = 10
_CONTEXT_CAP_KEYWORD = 10
_CONTEXT_CAP_OLDEST  = 4


def _extract_keywords(question: str) -> set[str]:
    """Extract topic-adjacent keywords from the question and expand via
    the keyword family map. Used to preferentially surface claims that
    engage with question-specific concepts, not just the newest claims."""
    text = question.lower()
    # Look for 'for: ...' clause first (autonomous monitor format)
    m = re.search(r'\bfor:\s*([^.?\n]+)', text)
    if m:
        text = m.group(1) + " " + text

    words = {w.strip('.,;:!?()[]') for w in re.split(r'\s+', text)}
    seeds = {w for w in words if w and w not in _GATE_STOPWORDS and len(w) > 2}

    expanded = set(seeds)
    for seed in seeds:
        for family_key, family_set in _KEYWORD_FAMILIES.items():
            if seed in family_set or seed == family_key:
                expanded |= family_set
    return expanded


def _claim_matches_keywords(claim: dict, keywords: set[str]) -> int:
    """Return a count of how many question keywords appear in the claim text.
    Higher is better — used to rank claims for the keyword slice."""
    if not keywords:
        return 0
    text = (claim.get('claim_text') or '').lower()
    return sum(1 for k in keywords if k in text)


def _diversify_pool(pool: list[dict], question: str) -> list[dict]:
    """Take the full deduplicated pool and compose a diversified context
    from three slices: newest, keyword-matched, and background oldest.
    Claims are deduplicated across slices so we don't double-count."""
    keywords = _extract_keywords(question)

    # Slice A: newest by published_at
    by_date_desc = sorted(
        pool, key=lambda c: c.get('published_at') or c.get('extracted_at') or '', reverse=True
    )
    newest = by_date_desc[:_CONTEXT_CAP_NEWEST]
    used_ids = {c.get('id') for c in newest}

    # Slice B: keyword-matched (not yet in newest)
    remaining_for_keyword = [c for c in pool if c.get('id') not in used_ids]
    by_keyword_desc = sorted(
        remaining_for_keyword,
        key=lambda c: (_claim_matches_keywords(c, keywords),
                       c.get('published_at') or ''),
        reverse=True,
    )
    # Only take keyword matches that actually match at least one keyword —
    # if no matches exist, fall back to nothing (the newest slice covers it)
    keyword_slice = [c for c in by_keyword_desc
                     if _claim_matches_keywords(c, keywords) > 0][:_CONTEXT_CAP_KEYWORD]
    used_ids.update(c.get('id') for c in keyword_slice)

    # Slice C: a handful of older-in-the-pool claims for background context
    remaining_for_background = [c for c in pool if c.get('id') not in used_ids]
    by_date_asc = sorted(
        remaining_for_background,
        key=lambda c: c.get('published_at') or c.get('extracted_at') or '',
    )
    background = by_date_asc[:_CONTEXT_CAP_OLDEST]

    combined = newest + keyword_slice + background
    return combined


def get_oss_context(question: str, domain: str) -> str | None:
    """
    Query OSS for promoted claims matching the domain's topic tags.
    Returns a formatted context block string, or None if nothing relevant found.
    """
    topics = DOMAIN_TO_TOPICS.get(domain, [])
    if not topics:
        return None

    all_claims: list[dict] = []
    for topic in topics:
        try:
            # Use /api/feed which server-side filters to promoted claims
            # (trust_level != 'IRRELEVANT') and supports limit/sort. Fetch
            # a larger pool than we need (_POOL_PER_TOPIC) so the
            # diversification step in _diversify_pool has room to work.
            resp = httpx.get(
                f"{config.OSS_BASE_URL}/api/feed",
                params={"topic": topic, "limit": _POOL_PER_TOPIC},
                headers={"X-Analyst-Token": config.OSS_ANALYST_TOKEN},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                claims = data.get("claims", [])
                all_claims.extend(claims)
                print(f"[OSS BRIDGE] Fetched {len(claims)} claims for topic {topic!r}",
                      flush=True)
            else:
                print(f"[OSS BRIDGE] {topic!r} returned HTTP {resp.status_code}",
                      flush=True)
        except Exception as e:
            print(f"[OSS BRIDGE] Warning: could not reach OSS for topic {topic!r}: {e}",
                  flush=True)

    if not all_claims:
        print(f"[OSS BRIDGE] No claims returned for any topic in domain={domain!r}",
              flush=True)
        return None

    # Deduplicate by id (same claim may appear in multiple topic results)
    seen: set = set()
    deduped: list[dict] = []
    for c in all_claims:
        cid = c.get("id")
        if cid and cid not in seen:
            seen.add(cid)
            deduped.append(c)

    # SFA-001 P4.1 — diversify the pool into three slices instead of taking
    # the newest N. See _diversify_pool for the composition strategy.
    diversified = _diversify_pool(deduped, question)

    lines = [
        "[OSS CLAIM STORE — Promoted intelligence as of ingestion]",
        f"[Sampling: newest + question-keyword + background — {len(diversified)} total]",
    ]
    for c in diversified:
        src  = c.get("source_name", "?")
        date = (c.get("published_at") or "")[:10]
        text = c.get("claim_text", "")
        lines.append(f"• [{src} | {date}] {text}")

    result = "\n".join(lines)
    print(
        f"[OSS BRIDGE] Injecting {len(diversified)} claims for domain={domain!r} "
        f"(from pool of {len(deduped)})",
        flush=True,
    )
    return result
