"""
swarmfish_prior.py — Prior injection for the adversarial input layer.

Pulls the current SWARMFISH committee assessment for each active topic and
packages it as a structured TopicPrior that the scrutiny pipeline uses as
its reference model for surprise scoring.

Design: specs/ADVERSARIAL_INPUT_LAYER_DESIGN_NOTE.md, Component 1
Spec: specs/ADVERSARIAL_INPUT_LAYER_SPEC_L3.md, Module 1
"""

import os
import json as _json
import logging
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional, List

log = logging.getLogger(__name__)

SWARMFISH_URL     = os.environ.get("SWARMFISH_BASE_URL", "http://host.docker.internal:7732")
SWARMFISH_TIMEOUT = float(os.environ.get("SWARMFISH_QUERY_TIMEOUT", "5.0"))
PRIOR_CACHE_TTL   = int(os.environ.get("OSS_PRIOR_CACHE_TTL", "60"))  # seconds
ANALYST_TOKEN     = os.environ.get("SWARMFISH_ANALYST_TOKEN", "dev_analyst_token")

# OSS topic tags don't exactly match SWARMFISH session question phrasing.
# SWARMFISH sessions have questions like "Assess the current situation for:
# Iran / Strait of Hormuz", and the /acp/archive endpoint uses ILIKE on the
# question field. Map OSS topic tags to SWARMFISH search substrings.
TOPIC_TO_SEARCH = {
    "iran-hormuz":     "Hormuz",
    "iran":            "Iran",
    "private-credit":  "Private Credit",
    "iran-war":        "Iran",
    "nuclear_program": "nuclear",
}


@dataclass
class TopicPrior:
    """The committee's current framing of a topic, packaged for scrutiny."""
    topic: str
    committee_consensus: float
    committee_range_low: float
    committee_range_high: float
    committee_meta: str              # "HIGH" | "MEDIUM" | "LOW"
    committee_sigma: float
    di_surprising_facts: list = field(default_factory=list)
    di_consensus_warning: Optional[str] = None
    assessment_timestamp: Optional[datetime] = None
    freshness: Optional[timedelta] = None   # now - assessment_timestamp
    framing_text: Optional[str] = None      # composed natural-language framing

    def is_stale(self, max_age_minutes: int = 90) -> bool:
        if self.freshness is None:
            return True
        return self.freshness > timedelta(minutes=max_age_minutes)

    def authority_weight(self) -> float:
        """
        Freshness-based weighting on the prior's authority.
        Fresh priors (< 15 min) weight ~1.0. Stale priors (> 2 hours)
        weight ~0.3. Linear decay in between. Capped at [0.3, 1.0].
        """
        if self.freshness is None:
            return 0.3
        mins = self.freshness.total_seconds() / 60
        if mins < 15:
            return 1.0
        if mins > 120:
            return 0.3
        return max(0.3, 1.0 - (mins - 15) / 150)  # linear decay 1.0 → 0.3


# In-memory cache: {topic: (TopicPrior, fetched_at_datetime)}
_prior_cache: dict = {}


def get_topic_prior(topic: str) -> Optional[TopicPrior]:
    """
    Fetch the current committee assessment for a topic. Returns None if
    SWARMFISH has not assessed this topic or if the service is unreachable.
    Cached for PRIOR_CACHE_TTL seconds to avoid hammering the endpoint.
    """
    if not topic:
        return None

    now = datetime.now(timezone.utc)

    # Cache hit?
    if topic in _prior_cache:
        cached_prior, fetched_at = _prior_cache[topic]
        if (now - fetched_at).total_seconds() < PRIOR_CACHE_TTL:
            return cached_prior

    # Fresh fetch — use /acp/archive which supports topic filtering via ILIKE
    # on the question field. Returns the most recent session first.
    # Uses stdlib urllib instead of requests (avoid adding a container dep).
    search_term = TOPIC_TO_SEARCH.get(topic, topic)
    try:
        query = urllib.parse.urlencode({
            "topic": search_term,
            "limit": "1",
            "outcome": "all",
        })
        url = f"{SWARMFISH_URL}/acp/archive?{query}"
        req = urllib.request.Request(
            url,
            headers={"X-Analyst-Token": ANALYST_TOKEN},
        )
        with urllib.request.urlopen(req, timeout=SWARMFISH_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
        data = _json.loads(raw)
    except Exception as e:
        log.warning(f"[PRIOR] Failed to fetch SWARMFISH assessment for topic={topic!r}: {e}")
        return None

    sessions = data.get("sessions") or []
    if not sessions:
        log.info(f"[PRIOR] No SWARMFISH assessment found for topic={topic!r}")
        return None

    session = sessions[0]

    # Parse the session fields into a TopicPrior
    try:
        created_at_raw = session.get("created_at")
        assessment_ts = None
        if created_at_raw:
            try:
                assessment_ts = datetime.fromisoformat(
                    created_at_raw.replace("Z", "+00:00")
                )
            except Exception:
                pass

        freshness = (now - assessment_ts) if assessment_ts else None

        prior = TopicPrior(
            topic=topic,
            committee_consensus=float(session.get("consensus_confidence") or 0.5),
            committee_range_low=float(session.get("consensus_range_low") or 0.0),
            committee_range_high=float(session.get("consensus_range_high") or 1.0),
            committee_meta=(session.get("meta_confidence") or "MEDIUM").upper(),
            committee_sigma=float(session.get("disagreement_level") or 0.0),
            di_surprising_facts=session.get("di_surprising_facts") or [],
            di_consensus_warning=session.get("di_consensus_warning"),
            assessment_timestamp=assessment_ts,
            freshness=freshness,
        )
        prior.framing_text = compose_framing_text(prior)

        _prior_cache[topic] = (prior, now)
        return prior
    except Exception as e:
        log.warning(f"[PRIOR] Failed to parse SWARMFISH session for topic={topic!r}: {e}")
        return None


def compose_framing_text(prior: TopicPrior) -> str:
    """
    Compose a natural-language summary of the committee's current framing
    of the topic. This text is embedded and used as the anchor for
    surprise scoring.
    """
    parts = [
        f"Topic: {prior.topic}.",
        f"Committee consensus: {prior.committee_consensus:.2f} "
        f"(range {prior.committee_range_low:.2f}-{prior.committee_range_high:.2f}).",
        f"Meta-confidence: {prior.committee_meta}. "
        f"Disagreement sigma: {prior.committee_sigma:.2f}.",
    ]

    if prior.di_surprising_facts:
        parts.append(
            "Surprising facts: "
            + " | ".join(str(f) for f in prior.di_surprising_facts[:3])
        )

    if prior.di_consensus_warning:
        parts.append(f"Consensus warning: {prior.di_consensus_warning}")

    return " ".join(parts)


def clear_cache():
    """Testing hook — drop the in-memory prior cache."""
    _prior_cache.clear()
