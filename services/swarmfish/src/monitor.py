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
import psycopg2

import config
from acp.resolver import resolve_session

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MONITOR_ENABLED  = os.environ.get("SWARMFISH_MONITOR_ENABLED", "false").lower() == "true"
MONITOR_INTERVAL = int(os.environ.get("SWARMFISH_MONITOR_INTERVAL_MINUTES", "30"))
STATE_FILE       = Path("/app/data/monitor_state.json")
# SFA-001 P4.3 — pause state persistence across container restart.
# The prior implementation stored _ACTIVE in memory only and re-read it
# from the env var on every restart, wiping the analyst's runtime toggle.
# This file stores the most recent toggle so runtime pause survives restart.
PAUSE_STATE_FILE = Path("/app/data/monitor_pause_state.json")
SWARMFISH_URL    = "http://localhost:7732"
MIN_NEW_CLAIMS   = int(os.environ.get("SWARMFISH_MONITOR_MIN_CLAIMS", "1"))

# Dissenter threshold: profile confidence must deviate this much from consensus to be flagged
DISSENT_THRESHOLD = 0.20

# Autonomous resolver trigger thresholds
RESOLVE_MIN_AGE_DAYS      = int(os.environ.get("SWARMFISH_RESOLVE_AGE_DAYS", "7"))
RESOLVE_COOLDOWN_DAYS     = int(os.environ.get("SWARMFISH_RESOLVE_COOLDOWN_DAYS", "3"))
RESOLVE_MAX_PER_CYCLE     = int(os.environ.get("SWARMFISH_RESOLVE_MAX_PER_CYCLE", "3"))

# ---------------------------------------------------------------------------
# Runtime toggle — can be flipped without restart via /monitor/toggle
# ---------------------------------------------------------------------------

def _load_pause_state(default: bool) -> bool:
    """Read persisted pause state from disk. Returns `default` if the file
    does not exist or is unreadable — ensures we degrade gracefully on a
    fresh install where the pause file hasn't been written yet."""
    try:
        if PAUSE_STATE_FILE.exists():
            data = json.loads(PAUSE_STATE_FILE.read_text())
            persisted = data.get("active")
            if isinstance(persisted, bool):
                return persisted
    except Exception as e:
        log.warning(f"[MONITOR] Could not read pause state file: {e}")
    return default


def _save_pause_state(active: bool):
    """Persist the current pause state so it survives container restart."""
    try:
        PAUSE_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        PAUSE_STATE_FILE.write_text(json.dumps({
            "active": active,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }))
    except Exception as e:
        log.warning(f"[MONITOR] Could not save pause state file: {e}")


_ACTIVE   = _load_pause_state(MONITOR_ENABLED)  # persisted across restart
_RUNNING  = False            # True while a cycle is in progress
_LAST_RUN: dict = {}         # populated after each cycle
_CYCLE_LOCK = threading.Lock()  # prevents concurrent monitor cycles

# Wake-up event for the scheduler loop. Acts as a cooperative cancellation
# signal: set it to wake a pending time.sleep, and an in-flight cycle checks
# _ACTIVE between topics to break early. Mirrors the OSS ingestion cancel
# pattern from 2026-04-05 — same bug shape, same fix.
_WAKE_EVENT = threading.Event()


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
    _save_pause_state(value)  # SFA-001 P4.3 — survive container restart
    # Wake the scheduler thread so it re-evaluates immediately — both to
    # abort a pending time.sleep after pause and to resume promptly after
    # the analyst toggles monitoring back on.
    _WAKE_EVENT.set()
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


def _find_sessions_to_review(db_conn) -> list[str]:
    """
    Return session IDs eligible for autonomous resolution.

    Eligibility:
      - Session has a consensus (completed prediction)
      - Session still has unscored predictions
      - Session is at least RESOLVE_MIN_AGE_DAYS old
      - No proposal exists yet, OR the most recent proposal is still pending
        and older than RESOLVE_COOLDOWN_DAYS (so we don't spam proposals for
        hypotheses the operator hasn't reviewed yet)
      - Cap to RESOLVE_MAX_PER_CYCLE to keep LLM cost bounded per cycle
    """
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT s.id
        FROM acp_sessions s
        JOIN acp_session_predictions sp ON sp.session_id = s.id
        JOIN acp_predictions p ON p.id = sp.prediction_id
        LEFT JOIN LATERAL (
            SELECT created_at, operator_action
            FROM acp_proposed_resolutions
            WHERE session_id = s.id
            ORDER BY created_at DESC
            LIMIT 1
        ) latest_prop ON TRUE
        WHERE s.consensus_confidence IS NOT NULL
          AND s.created_at <= NOW() - (%s || ' days')::interval
        GROUP BY s.id, s.created_at, latest_prop.created_at, latest_prop.operator_action
        HAVING COUNT(p.id) FILTER (WHERE p.scored = FALSE) > 0
           AND (
                latest_prop.created_at IS NULL
             OR (latest_prop.operator_action IS NULL
                 AND latest_prop.created_at <= NOW() - (%s || ' days')::interval)
           )
        ORDER BY s.created_at ASC
        LIMIT %s
    """, (RESOLVE_MIN_AGE_DAYS, RESOLVE_COOLDOWN_DAYS, RESOLVE_MAX_PER_CYCLE))
    rows = cursor.fetchall()
    cursor.close()
    return [str(r[0]) for r in rows]


def run_resolution_review_cycle() -> dict:
    """
    Find eligible old sessions and run the autonomous resolver on them.
    Each proposal is written to acp_proposed_resolutions (advisory, not applied
    to calibration until the operator accepts via /acp/outcome).
    Returns a summary dict.
    """
    summary = {
        "reviewed":  0,
        "proposed":  0,
        "errors":    0,
        "verdicts":  {"confirmed": 0, "falsified": 0, "still_pending": 0},
    }

    try:
        db = psycopg2.connect(config.DB_URL)
    except Exception as e:
        log.warning(f"[RESOLVER-CYCLE] DB connect failed: {e}")
        summary["errors"] += 1
        return summary

    try:
        session_ids = _find_sessions_to_review(db)
        summary["reviewed"] = len(session_ids)
        if not session_ids:
            log.info("[RESOLVER-CYCLE] No sessions eligible for review")
            return summary

        log.info(f"[RESOLVER-CYCLE] Reviewing {len(session_ids)} eligible session(s)")
        for sid in session_ids:
            try:
                result = resolve_session(db, sid)
                summary["proposed"] += 1
                v = result.get("verdict", "still_pending")
                if v in summary["verdicts"]:
                    summary["verdicts"][v] += 1
            except Exception as e:
                log.warning(f"[RESOLVER-CYCLE] Session {sid[:8]} resolve failed: {e}")
                summary["errors"] += 1
    finally:
        db.close()

    print(
        f"[RESOLVER-CYCLE] Complete — reviewed={summary['reviewed']}, "
        f"proposed={summary['proposed']}, errors={summary['errors']}, "
        f"verdicts={summary['verdicts']}",
        flush=True,
    )
    return summary


def _llm_health_check() -> tuple[bool, float, str]:
    """Quick health probe against LM Studio before a full cycle kicks off.

    Revised 2026-04-14 (second investigation pass):
    The original implementation checked "response content is non-empty" as
    the success criterion. That was wrong for reasoning-distilled models
    (qwen3.5-*-reasoning-distilled), which consume their entire generation
    budget on <think>...</think> tokens BEFORE producing visible output.
    A healthy reasoning model given a 10-token budget will return zero
    visible content because it's still thinking.

    The fix: check that the model actually GENERATED tokens (any kind —
    reasoning or visible) within a reasonable time budget, not that any
    specific visible text came back. The measurement that matters is
    whether tokens are flowing at expected speed, not whether they parsed
    into visible content.

    Expected healthy response: completes in under 10 seconds with
    completion_tokens > 0. Warning: 10-30 seconds. Degraded: over 30
    seconds. Failed: exception, timeout, or zero completion_tokens.
    """
    try:
        import httpx, time
        start = time.monotonic()
        r = httpx.post(
            f"{config.LLM_BASE_URL}/chat/completions",
            json={
                "model": config.LLM_MODEL,
                # Short neutral prompt — just wants the model to generate
                # something. We're not parsing the output, just measuring
                # that tokens flow.
                "messages": [{"role": "user", "content": "ok"}],
                "max_tokens": 20,
                "temperature": 0.0,
            },
            timeout=60,
        )
        elapsed = time.monotonic() - start
        if r.status_code != 200:
            return (False, elapsed, f"HTTP {r.status_code}: {r.text[:200]}")
        data = r.json()
        usage = data.get("usage") or {}
        completion_tokens = usage.get("completion_tokens", 0)
        # The real success criterion: did the model generate ANY tokens?
        # Reasoning models return empty content on small budgets, but the
        # usage.completion_tokens field records the actual work done.
        if completion_tokens == 0:
            return (False, elapsed, "model generated 0 tokens")
        # Speed check: 20 tokens in under 10s means ~2 tok/sec minimum,
        # well below the healthy ~25 tok/sec but confirms the model is
        # active and responsive. Slow-but-working is flagged as DEGRADED
        # in the caller, not failed.
        return (True, elapsed,
                f"generated {completion_tokens} tokens (~{completion_tokens/elapsed:.1f} tok/sec)")
    except httpx.TimeoutException:
        return (False, 60.0, "health check timed out after 60s")
    except Exception as e:
        return (False, 0.0, f"health check exception: {e}")


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
        # SFA-001 follow-up (2026-04-14) — pre-cycle LLM health check.
        # Catches LM Studio in a degraded state BEFORE we waste a cycle's
        # worth of timeouts. Healthy expectation: <10s. Anything >30s is
        # a warning; we abort the cycle so the analyst can intervene.
        ok, elapsed, msg = _llm_health_check()
        if not ok:
            print(f"[MONITOR] ⚠ LLM HEALTH CHECK FAILED ({elapsed:.1f}s) — aborting cycle. {msg}", flush=True)
            return state
        if elapsed > 30.0:
            print(f"[MONITOR] ⚠ LLM HEALTH CHECK DEGRADED ({elapsed:.1f}s) — aborting cycle to avoid cascade. {msg}", flush=True)
            return state
        if elapsed > 10.0:
            print(f"[MONITOR] LLM health check slow but passing ({elapsed:.1f}s): {msg}", flush=True)
        else:
            print(f"[MONITOR] LLM health ok ({elapsed:.1f}s)", flush=True)

        topics = _get_oss_topics()
        if not topics:
            log.info("[MONITOR] No active OSS topics found, skipping cycle")
            return state

        now_iso = datetime.now(timezone.utc).isoformat()

        for topic in topics:
            # Cooperative cancellation check — if the analyst hit pause
            # mid-cycle, stop starting new topic predictions. The in-flight
            # HTTP call (if any) still runs to completion; this only
            # prevents NEW work from being queued after pause.
            if not _ACTIVE:
                print("[MONITOR] Pause requested — breaking out of topic loop", flush=True)
                break

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
                log.warning(f"[MONITOR] Prediction failed for topic {tag!r}, will retry next cycle")
                continue  # do NOT advance state — same claims will be retried

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
                # Autonomous resolution pass — evaluate old, unscored sessions
                # against newly-ingested OSS claims. Advisory only.
                # Skip if pause was requested mid-cycle so we don't start a
                # fresh batch of LLM calls after the analyst asked to stop.
                if _ACTIVE:
                    try:
                        run_resolution_review_cycle()
                    except Exception as e:
                        log.error(f"[MONITOR] Resolution review cycle error: {e}")
            else:
                log.debug("[MONITOR] Skipping cycle (disabled)")

            # Wakeable sleep. When _ACTIVE is true, wait at most one interval
            # before the next cycle. When _ACTIVE is false, wait indefinitely
            # until set_active() flips the flag and sets the event. Either
            # way, a state change wakes us immediately instead of forcing
            # the analyst to wait up to 30 minutes for the pause to take.
            timeout = (MONITOR_INTERVAL * 60) if _ACTIVE else None
            _WAKE_EVENT.wait(timeout)
            _WAKE_EVENT.clear()
