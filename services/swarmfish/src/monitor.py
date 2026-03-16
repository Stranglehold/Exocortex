"""
monitor.py — SWARMFISH autonomous monitoring loop.

Periodically scans OSS for new promoted claims per topic.
When new signal is detected, runs a prediction session and posts
the resulting hypothesis back to OSS.

Enabled only when SWARMFISH_MONITOR_ENABLED=true in environment.
Set SWARMFISH_MONITOR_INTERVAL_MINUTES to control cycle frequency (default 30).
"""

import json
import os
import threading
import time
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

import httpx

import config

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MONITOR_ENABLED  = os.environ.get("SWARMFISH_MONITOR_ENABLED", "false").lower() == "true"
MONITOR_INTERVAL = int(os.environ.get("SWARMFISH_MONITOR_INTERVAL_MINUTES", "30"))
STATE_FILE       = Path("/app/data/monitor_state.json")
SWARMFISH_URL    = "http://localhost:7732"
MIN_NEW_CLAIMS   = int(os.environ.get("SWARMFISH_MONITOR_MIN_CLAIMS", "1"))

# Dissenter threshold: profile confidence must deviate this much from consensus to be flagged
DISSENT_THRESHOLD = 0.20

# ---------------------------------------------------------------------------
# Runtime toggle — can be flipped without restart via /monitor/toggle
# ---------------------------------------------------------------------------

_ACTIVE   = MONITOR_ENABLED  # starts from env var; mutable at runtime
_RUNNING  = False            # True while a cycle is in progress
_LAST_RUN: dict = {}         # populated after each cycle
_CYCLE_LOCK = threading.Lock()  # prevents concurrent monitor cycles


def get_status() -> dict:
    return {
        "active":           _ACTIVE,
        "running":          _RUNNING,
        "interval_minutes": MONITOR_INTERVAL,
        "min_claims":       MIN_NEW_CLAIMS,
        "last_run":         _LAST_RUN or None,
    }


def set_active(value: bool):
    global _ACTIVE
    _ACTIVE = value
    log.info(f"[MONITOR] {'Enabled' if value else 'Disabled'} at runtime")


# ---------------------------------------------------------------------------
# State persistence: last_checked per topic
# ---------------------------------------------------------------------------

def _load_state() -> dict:
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
    except Exception as e:
        log.warning(f"[MONITOR] Could not load state file: {e}")
    return {}


def _save_state(state: dict):
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, default=str))
    except Exception as e:
        log.warning(f"[MONITOR] Could not save state file: {e}")


# ---------------------------------------------------------------------------
# OSS helpers
# ---------------------------------------------------------------------------

def _get_oss_topics() -> list[dict]:
    """Fetch active OSS topics."""
    try:
        r = httpx.get(
            f"{config.OSS_BASE_URL}/api/topics",
            timeout=10,
        )
        if r.is_success:
            return r.json().get('topics', [])
    except Exception as e:
        log.warning(f"[MONITOR] Could not fetch OSS topics: {e}")
    return []


def _get_new_claims(topic: str, since_iso: str | None) -> list[dict]:
    """
    Fetch promoted claims for a topic from OSS /api/feed.
    Filters to claims newer than since_iso if provided.
    """
    try:
        params = {'topic': topic, 'limit': 50}
        r = httpx.get(
            f"{config.OSS_BASE_URL}/api/feed",
            params=params,
            timeout=15,
        )
        if not r.is_success:
            return []
        claims = r.json().get('claims', [])

        if since_iso:
            since_dt = datetime.fromisoformat(since_iso.replace('Z', '+00:00'))
            filtered = []
            for c in claims:
                ts = c.get('extracted_at') or c.get('published_at')
                if not ts:
                    continue
                try:
                    # Handle RFC 2822 and ISO formats
                    from email.utils import parsedate_to_datetime
                    try:
                        cdt = parsedate_to_datetime(ts)
                    except Exception:
                        cdt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    if cdt > since_dt:
                        filtered.append(c)
                except Exception:
                    filtered.append(c)
            return filtered

        return claims
    except Exception as e:
        log.warning(f"[MONITOR] Could not fetch claims for topic {topic!r}: {e}")
        return []


def _post_hypothesis_to_oss(
    topic: str,
    observation_label: str,
    session: dict,
    predictions: list[dict],
    source_profiles: list[dict],
) -> bool:
    """Post a SWARMFISH session result to OSS as a hypothesis. Returns True on success."""
    try:
        payload = {
            "topic":               topic,
            "observation_label":   observation_label,
            "swarmfish_session_id": session.get("session_id", ""),
            "explanation":         session.get("operator_brief", "")[:2000],
            "initial_confidence":  float((session.get("consensus") or {}).get("consensus_confidence") or 0.0),
            "predictions":         predictions,
            "source_profiles":     source_profiles,
            "analyst_token":       config.OSS_ANALYST_TOKEN,
        }
        r = httpx.post(
            f"{config.OSS_BASE_URL}/api/hypothesis/from_swarmfish",
            json=payload,
            headers={"X-Analyst-Token": config.OSS_ANALYST_TOKEN},
            timeout=15,
        )
        if r.is_success:
            d = r.json()
            log.info(
                f"[MONITOR] Hypothesis #{d.get('hypothesis_id')} registered in OSS "
                f"for topic={topic!r} (session={session.get('session_id')})"
            )
            return True
        else:
            log.warning(f"[MONITOR] OSS hypothesis POST failed: {r.status_code} {r.text[:200]}")
    except Exception as e:
        log.warning(f"[MONITOR] Could not post hypothesis to OSS: {e}")
    return False


# ---------------------------------------------------------------------------
# Prediction session via SWARMFISH
# ---------------------------------------------------------------------------

def _run_prediction(topic: str, topic_label: str, claims: list[dict]) -> dict | None:
    """
    Run a SWARMFISH prediction session for the given claims.
    Calls the internal /acp/predict endpoint.
    Returns the session dict on success, None on failure.
    """
    n = len(claims)
    # Build a compact context summary from the claims
    claim_lines = []
    for c in claims[:12]:  # cap context at 12 claims
        src  = c.get('source_name', '?')
        text = c.get('claim_text', '')[:200]
        claim_lines.append(f"• [{src}] {text}")
    context = f"[{n} new promoted claims for topic: {topic_label}]\n" + "\n".join(claim_lines)

    question = (
        f"Assess the current situation for: {topic_label}. "
        f"{n} new intelligence item{'s' if n != 1 else ''} detected since last assessment. "
        f"What is the most likely trajectory and what conditions would change this assessment?"
    )

    try:
        r = httpx.post(
            f"{SWARMFISH_URL}/acp/predict",
            json={
                "question":  question,
                "domain":    "geopolitical_risk",
                "context":   context,
            },
            headers={"X-Analyst-Token": config.ANALYST_TOKEN},
            timeout=1800,  # 8 profiles × ~90s worst case + JIT reload + contention headroom
        )
        if r.is_success:
            return r.json()
        else:
            log.warning(f"[MONITOR] /acp/predict failed: {r.status_code} {r.text[:200]}")
    except Exception as e:
        log.warning(f"[MONITOR] Prediction request failed: {e}")
    return None


# ---------------------------------------------------------------------------
# Monitoring cycle
# ---------------------------------------------------------------------------

def _extract_predictions(session: dict) -> list[dict]:
    """Extract falsification checklist as predictions list."""
    checklist = session.get("falsification_checklist") or []
    return [{"prediction": item, "falsifiable_by": None} for item in checklist[:8]]


def _extract_source_profiles(session: dict, consensus: float) -> list[dict]:
    """Build source_profiles list with dissenter flags."""
    profiles = []
    for pred in session.get("individual_predictions", session.get("predictions", [])):
        if pred.get("error"):
            continue
        conf = float(pred.get("confidence") or 0.0)
        profiles.append({
            "profile_name":  pred.get("profile_name", "unknown"),
            "confidence":    conf,
            "was_dissenter": abs(conf - consensus) >= DISSENT_THRESHOLD,
        })
    return profiles


def run_monitoring_cycle(state: dict) -> dict:
    """
    Single monitoring cycle. Checks all active OSS topics for new signal.
    Updates and returns the state dict.
    """
    if not _CYCLE_LOCK.acquire(blocking=False):
        print("[MONITOR] Cycle already running (lock held), skipping", flush=True)
        return state

    global _RUNNING, _LAST_RUN
    _RUNNING = True
    hypotheses_posted = 0
    topics_checked    = 0

    try:
        topics = _get_oss_topics()
        if not topics:
            log.info("[MONITOR] No active OSS topics found, skipping cycle")
            return state

        now_iso = datetime.now(timezone.utc).isoformat()

        for topic in topics:
            tag   = topic.get('tag', '')
            label = topic.get('display_name') or tag
            if not tag:
                continue

            topics_checked += 1
            since = state.get(tag)
            new_claims = _get_new_claims(tag, since)

            if len(new_claims) < MIN_NEW_CLAIMS:
                print(f"[MONITOR] {tag!r}: {len(new_claims)} new claims (below threshold), skipping", flush=True)
                state[tag] = now_iso
                continue

            print(f"[MONITOR] {tag!r}: {len(new_claims)} new claims — running prediction session", flush=True)

            session = _run_prediction(tag, label, new_claims)
            if not session:
                log.warning(f"[MONITOR] Prediction failed for topic {tag!r}, skipping hypothesis post")
                state[tag] = now_iso
                continue

            consensus    = float((session.get("consensus") or {}).get("consensus_confidence") or 0.0)
            predictions  = _extract_predictions(session)
            src_profiles = _extract_source_profiles(session, consensus)

            obs_label = f"{label} — {datetime.now(timezone.utc).strftime('%b %Y')}"
            if _post_hypothesis_to_oss(tag, obs_label, session, predictions, src_profiles):
                hypotheses_posted += 1
            state[tag] = now_iso

    finally:
        _LAST_RUN = {
            "at":               datetime.now(timezone.utc).isoformat(),
            "topics_checked":   topics_checked,
            "hypotheses_posted": hypotheses_posted,
        }
        _RUNNING = False
        _CYCLE_LOCK.release()
        print(f"[MONITOR] Cycle complete — topics={topics_checked}, hypotheses={hypotheses_posted}", flush=True)

    return state


# ---------------------------------------------------------------------------
# Background thread
# ---------------------------------------------------------------------------

class SwarmfishMonitor:
    """Background thread that runs the monitoring cycle on a fixed interval."""

    def start(self):
        t = threading.Thread(target=self._loop, daemon=True, name="swarmfish-monitor")
        t.start()
        log.info(f"[MONITOR] Started (interval={MONITOR_INTERVAL}m, min_claims={MIN_NEW_CLAIMS})")

    def _loop(self):
        # Initial delay: wait for Flask to be ready
        time.sleep(15)
        state = _load_state()

        while True:
            if _ACTIVE:
                try:
                    state = run_monitoring_cycle(state)
                    _save_state(state)
                except Exception as e:
                    log.error(f"[MONITOR] Cycle error: {e}")
            else:
                log.debug("[MONITOR] Skipping cycle (disabled)")
            time.sleep(MONITOR_INTERVAL * 60)
