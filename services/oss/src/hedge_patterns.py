"""
hedge_patterns.py — regex-based classification of certainty and attribution.

Operates on the paraphrased claim_text field. Does NOT classify quoted_directly,
which requires LLM tagging at extraction time because the regex layer cannot
see the original quotation boundaries after paraphrasing has destroyed them.

Spec: specs/HEDGE_PATTERN_SPEC_L3.md
Design note: specs/HEDGE_PATTERN_DESIGN_NOTE.md
"""

import re
import logging

log = logging.getLogger(__name__)

# Certainty values
COMMITTED = "committed"
HEDGED    = "hedged"
UNKNOWN   = "unknown"

# Attribution values
NAMED  = "named"
VAGUE  = "vague"
ABSENT = "absent"
# UNKNOWN shared with certainty


# ---------------------------------------------------------------------------
# Certainty patterns — each matches a specific linguistic construction of
# hedging. A claim is `hedged` if ANY pattern matches; `committed` if none.
# ---------------------------------------------------------------------------

CERTAINTY_PATTERNS: dict = {
    "modal_hedge": re.compile(
        r"\b(may|might|could|would|should|can)\s+(?:be|have|not|well)?\b",
        re.IGNORECASE,
    ),
    "epistemic_adverb": re.compile(
        r"\b(possibly|probably|allegedly|reportedly|supposedly|purportedly|"
        r"apparently|seemingly|ostensibly|arguably|presumably)\b",
        re.IGNORECASE,
    ),
    "hedge_verb": re.compile(
        r"\b(suggests?|indicates?|appears?\s+to|seems?\s+to|"
        r"is\s+(?:said|thought|understood|believed|expected)\s+to|"
        r"are\s+(?:said|thought|understood|believed|expected)\s+to)\b",
        re.IGNORECASE,
    ),
    "weakener": re.compile(
        r"\b(somewhat|rather|perhaps)\b",
        re.IGNORECASE,
    ),
}


# ---------------------------------------------------------------------------
# Attribution patterns — each detects a specific type of source clause.
# Order of evaluation: vague first (more specific patterns), then named,
# then absent (default when nothing matches).
# ---------------------------------------------------------------------------

ATTRIBUTION_PATTERNS: dict = {
    "vague_source": re.compile(
        r"\b(sources?|officials?|analysts?|experts?|insiders?)\s+"
        r"(?:say|said|suggest|suggested|indicate|indicated|believe|believed|"
        r"expect|expected|warn|warned|told)\b",
        re.IGNORECASE,
    ),
    "vague_familiar": re.compile(
        r"\b(?:people|sources?|individuals?|officials?)\s+familiar\s+with\b",
        re.IGNORECASE,
    ),
    "anonymous_official": re.compile(
        r"\ba\s+(?:senior\s+|high-ranking\s+|senior-level\s+)?"
        r"(?:administration|government|official|diplomatic|intelligence|military)\s+"
        r"(?:official|source|spokesperson)\b",
        re.IGNORECASE,
    ),
    "condition_of_anonymity": re.compile(
        r"\bon\s+(?:the\s+)?condition\s+of\s+anonymity\b",
        re.IGNORECASE,
    ),
    "named_source": re.compile(
        # Proper noun(s) + speech verb — simplified, catches the common cases.
        # Case-sensitive because proper nouns matter.
        r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+"
        r"(?:said|stated|announced|told|confirmed|denied|declared|reported)\b"
    ),
}

VAGUE_KEYS = (
    "vague_source",
    "vague_familiar",
    "anonymous_official",
    "condition_of_anonymity",
)


# ---------------------------------------------------------------------------
# Classification functions — pure, deterministic.
# ---------------------------------------------------------------------------

def classify_certainty(claim_text: str) -> str:
    """
    Return 'committed' if no hedge pattern matches, 'hedged' if any does.
    Returns 'unknown' only for empty/whitespace-only input.
    """
    if not claim_text or not claim_text.strip():
        return UNKNOWN
    for pattern in CERTAINTY_PATTERNS.values():
        if pattern.search(claim_text):
            return HEDGED
    return COMMITTED


def classify_attribution(claim_text: str) -> str:
    """
    Return 'vague' if any vague-pattern matches, then 'named' if named-source
    pattern matches, else 'absent'. Vague takes priority over named — a claim
    like "Sources close to Biden said..." has both a vague source AND a named
    entity, and the vague marker is the load-bearing signal.
    """
    if not claim_text or not claim_text.strip():
        return UNKNOWN
    for key in VAGUE_KEYS:
        if ATTRIBUTION_PATTERNS[key].search(claim_text):
            return VAGUE
    if ATTRIBUTION_PATTERNS["named_source"].search(claim_text):
        return NAMED
    return ABSENT


def classify_hedge_pattern(claim_text: str) -> tuple:
    """
    Convenience wrapper. Returns (certainty, attribution) tuple.
    """
    return classify_certainty(claim_text), classify_attribution(claim_text)


# ---------------------------------------------------------------------------
# Positive-detection helpers — distinguish "regex actively matched a pattern"
# from "regex fell through to a default value." This matters for LLM cross-
# validation: regex should only override the LLM when it made a positive
# detection, not when it's returning its default fallback.
# ---------------------------------------------------------------------------

def certainty_positive_detection(claim_text: str):
    """
    Return 'hedged' if any certainty pattern actively matched, None otherwise.
    (There is no 'positive committed' detection — committed is always a default.)
    """
    if not claim_text or not claim_text.strip():
        return None
    for pattern in CERTAINTY_PATTERNS.values():
        if pattern.search(claim_text):
            return HEDGED
    return None


def attribution_positive_detection(claim_text: str):
    """
    Return 'vague' if a vague-pattern matched, 'named' if a named-source
    pattern matched, None if neither (i.e., regex has no positive detection).
    Callers should treat None as "no regex opinion" and trust upstream tagging.
    """
    if not claim_text or not claim_text.strip():
        return None
    for key in VAGUE_KEYS:
        if ATTRIBUTION_PATTERNS[key].search(claim_text):
            return VAGUE
    if ATTRIBUTION_PATTERNS["named_source"].search(claim_text):
        return NAMED
    return None
