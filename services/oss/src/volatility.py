"""
volatility.py — topic-tag → volatility-tier lookup for narrative stability.

Volatility is a property of the TOPIC, not the individual claim. A casualty
count moves every hour; the Pope's identity doesn't move at all. The retcon
signal classifier (contradict.py) uses this axis to distinguish reality
updates from narrative rewrites.

Spec: specs/NARRATIVE_STABILITY_SPEC_L3.md
"""

import os
import logging

log = logging.getLogger(__name__)

# Volatility tiers
HIGH   = "high"    # Facts change on hour→day timescales
MEDIUM = "medium"  # Facts change on week→month timescales
LOW    = "low"     # Facts change on year timescales or not at all

DEFAULT_VOLATILITY = os.environ.get("OSS_DEFAULT_VOLATILITY", MEDIUM)

# Keyed by topic tag (from claims.topic_tags). Matched case-insensitive.
# Resolution rule: when a claim has multiple tags spanning tiers, the
# HIGHEST tier wins (reality may have moved).
TOPIC_VOLATILITY: dict[str, str] = {
    # --- HIGH --- (breaking news, active conflict, markets)
    "iran-hormuz":         HIGH,
    "iran-war":            HIGH,
    "casualty_counts":     HIGH,
    "oil_prices":          HIGH,
    "markets":             HIGH,
    "breaking_news":       HIGH,
    "military_operations": HIGH,
    "ceasefire":           HIGH,

    # --- MEDIUM --- (diplomacy, policy, elections)
    "iran":            MEDIUM,
    "diplomacy":       MEDIUM,
    "policy":          MEDIUM,
    "elections":       MEDIUM,
    "sanctions":       MEDIUM,
    "trade":           MEDIUM,
    "nuclear_program": MEDIUM,

    # --- LOW --- (history, biography, geography, law)
    "history":         LOW,
    "biography":       LOW,
    "geography":       LOW,
    "law":             LOW,
    "religion":        LOW,
    "scientific_fact": LOW,
    "constitutional":  LOW,
}


def get_volatility(topic_tags) -> str:
    """
    Return the volatility tier for a claim given its topic tags.

    Resolution rule: when multiple tags map to different tiers, take the
    HIGHEST (most generous — assume reality may have moved). Unmapped tags
    fall through to DEFAULT_VOLATILITY.

    Accepts None or empty list and returns DEFAULT_VOLATILITY.

    Returns one of: 'high', 'medium', 'low'.
    """
    if not topic_tags:
        return DEFAULT_VOLATILITY

    tiers_seen = set()
    for tag in topic_tags:
        if not tag:
            continue
        normalized = str(tag).strip().lower()
        tier = TOPIC_VOLATILITY.get(normalized)
        if tier:
            tiers_seen.add(tier)

    if not tiers_seen:
        return DEFAULT_VOLATILITY
    if HIGH in tiers_seen:
        return HIGH
    if MEDIUM in tiers_seen:
        return MEDIUM
    return LOW


def pair_volatility(tags_a, tags_b) -> str:
    """
    Volatility for a retcon PAIR. Takes the union of both claims' tags and
    resolves via get_volatility. A pair involving even one volatile topic
    is treated as volatile — we do not average down.
    """
    union = list(set((tags_a or []) + (tags_b or [])))
    return get_volatility(union)
