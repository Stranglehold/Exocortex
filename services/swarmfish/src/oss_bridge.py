"""
oss_bridge.py — SWARMFISH → OSS context bridge

Queries the OSS claim store for promoted intelligence matching the
prediction domain, formats it as a structured context block, and
returns it for injection before profiles run.

Graceful fallback: if OSS is unreachable or has no matching claims,
returns None and logs a warning. The predict pipeline continues
without OSS context.
"""

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
            resp = httpx.post(
                f"{config.OSS_BASE_URL}/api/record",
                json={"topic": topic},
                headers={"X-Analyst-Token": config.OSS_ANALYST_TOKEN},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                promoted = [
                    c for c in data.get("claims", [])
                    if c.get("trust_level") == "PROMOTED"
                ]
                all_claims.extend(promoted)
        except Exception as e:
            print(f"[OSS BRIDGE] Warning: could not reach OSS for topic {topic!r}: {e}",
                  flush=True)

    if not all_claims:
        return None

    # Deduplicate by id, sort newest first, cap at 8
    seen: set = set()
    deduped: list[dict] = []
    for c in sorted(all_claims, key=lambda x: x.get("published_at") or "", reverse=True):
        cid = c.get("id")
        if cid and cid not in seen:
            seen.add(cid)
            deduped.append(c)
        if len(deduped) >= 8:
            break

    lines = ["[OSS CLAIM STORE — Promoted intelligence as of ingestion]"]
    for c in deduped:
        src  = c.get("source_name", "?")
        date = (c.get("published_at") or "")[:10]
        text = c.get("claim_text", "")
        lines.append(f"• [{src} | {date}] {text}")

    result = "\n".join(lines)
    print(f"[OSS BRIDGE] Injecting {len(deduped)} claims for domain={domain!r}",
          flush=True)
    return result
