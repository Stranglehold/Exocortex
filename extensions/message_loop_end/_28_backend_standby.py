"""
Backend Standby Recovery — Exocortex Infrastructure Recovery
=============================================================
Hook: message_loop_end (_28_ — fires before supervisor at _50_)

Detects when the inference backend is unreachable (ConnectionRefusedError,
aiohttp connection failure) and distinguishes this from reasoning loops.

On detection (2 consecutive backend-down failures):
  1. Sets agent._backend_standby = True
  2. Injects a UI-visible warning into history
  3. Starts an asyncio background task that polls the health endpoint
  4. The gate at _01_backend_standby_gate.py pauses the loop via context.paused

On recovery (health endpoint returns 200 + model_loaded=true):
  1. Clears agent._backend_standby
  2. Sets context.paused = False (unblocks the gate)
  3. Injects recovery warning + context hint for the model

Critical distinction:
  - ConnectionRefusedError on CONNECT → backend DOWN → enter standby
  - SocketTimeoutError on READ → backend SLOW → do NOT enter standby
    (this is the long-generation timeout; increasing litellm timeout handles it)

No LLM calls anywhere in this extension. Deterministic infrastructure monitor.
"""

import asyncio
import json
import sys as _sys
import urllib.request
import urllib.error
from pathlib import Path

_PM_PATH = "/a0/usr/plugins/_exocortex/helpers"
if _PM_PATH not in _sys.path:
    _sys.path.insert(0, _PM_PATH)

from agent import LoopData
from helpers.extension import Extension

# ── Constants ─────────────────────────────────────────────────────────────────

STANDBY_FLAG       = "_backend_standby"
FAILURE_COUNT_KEY  = "_backend_failure_count"
POLL_TASK_KEY      = "_backend_poll_task"

# How many consecutive backend-down failures before entering standby
DETECTION_THRESHOLD = 2

# Seconds between health poll attempts (index = attempt number, last value repeats)
BACKOFF_SCHEDULE = [10, 10, 10, 30, 30, 30, 60]

# Model config path — source of api_base
MODEL_CONFIG_PATH = "/a0/usr/agents/agent0/plugins/_model_config/config.json"

# ── Error pattern detection ───────────────────────────────────────────────────

# Strings that indicate the backend process is DOWN (not slow)
_DOWN_PATTERNS = [
    "connectionrefusederror",
    "connect call failed",
    "lm_studioexception - connection error",
    "aiohttp.clientconnectorerror",
    "connection refused",
    "no connection could be made",        # Windows variant
    "network is unreachable",
]

# Strings that indicate a READ timeout (backend is SLOW, not DOWN — do NOT standbify)
_SLOW_PATTERNS = [
    "sockettimeouterror: timeout on reading",
    "readtimeouterror",
    "read timeout",
]


def _is_backend_down(exc_str: str) -> bool:
    """True if the exception string indicates the backend process is unreachable."""
    lower = exc_str.lower()
    if any(p in lower for p in _SLOW_PATTERNS):
        return False  # Slow, not down — don't enter standby
    return any(p in lower for p in _DOWN_PATTERNS)


# ── Health check ──────────────────────────────────────────────────────────────

def _get_health_urls() -> list[str]:
    """Derive health check URLs from the agent's model config api_base.

    FIXED 2026-08-21 (found by the extension survey's "does it still resolve?" pass).
    This read MODEL_CONFIG_PATH — a hardcoded /a0/usr/agents/agent0/... path with NO
    fallback, which does not exist on A0 v2.9 — so it always raised, always returned [],
    and the backend health check had NOTHING to probe. Doubly inert: even at the correct
    path it read `chat_model.api_base`, and v2.9's config.json is just
    {"model_preset": "..."}; the api_base moved to presets.yaml. Same schema change that
    made the whole model-profile system inert.

    Now resolves through helpers/model_profile.active_api_base(), which mirrors the
    model-name resolution so the two cannot disagree about the active preset. The old
    path is kept as a fallback for v1.x layouts rather than deleted.
    """
    api_base = ""
    try:
        import sys
        if "/a0/usr/plugins/_exocortex/helpers" not in sys.path:
            sys.path.insert(0, "/a0/usr/plugins/_exocortex/helpers")
        import model_profile as _mp
        api_base = _mp.active_api_base() or ""
    except Exception:
        api_base = ""

    try:
        if not api_base:
            # v1.x layout fallback — harmless when the file is absent.
            with open(MODEL_CONFIG_PATH, "r") as f:
                cfg = json.load(f)
            api_base = cfg.get("chat_model", {}).get("api_base", "")
        if not api_base:
            # A cloud provider has no local endpoint. Nothing to health-check is a
            # legitimate state, not a failure.
            return []
        # Strip /v1 suffix if present, then build candidate endpoints
        base = api_base.rstrip("/")
        if base.endswith("/v1"):
            base = base[:-3]
        return [
            f"{base}/health",      # Exocortex wrapper
            f"{base}/v1/models",   # LM Studio fallback
        ]
    except Exception:
        return []


def _check_health(urls: list[str]) -> bool:
    """Return True if any health URL responds with 200. Synchronous, fast timeout."""
    for url in urls:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status != 200:
                    continue
                # For the Exocortex wrapper, also verify model_loaded
                try:
                    body = json.loads(resp.read().decode())
                    # /health endpoint: require model_loaded=true
                    if "model_loaded" in body and not body["model_loaded"]:
                        continue
                except Exception:
                    pass  # /v1/models doesn't return model_loaded — 200 is enough
                return True
        except Exception:
            continue
    return False


# ── Background poll task ──────────────────────────────────────────────────────

async def _poll_until_recovered(agent, urls: list[str]):
    """Background asyncio task: poll health endpoint until backend recovers."""
    attempt = 0
    while True:
        # Check if the context is still alive — bail if the agent died
        if not agent.context.task or not agent.context.task.is_alive():
            print("[BACKEND-STANDBY] Context no longer alive — cancelling poll.", flush=True)
            return

        delay = BACKOFF_SCHEDULE[min(attempt, len(BACKOFF_SCHEDULE) - 1)]
        print(
            f"[BACKEND-STANDBY] Poll attempt {attempt + 1}, waiting {delay}s...",
            flush=True,
        )
        await asyncio.sleep(delay)
        attempt += 1

        # Run the blocking HTTP check in a thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        recovered = await loop.run_in_executor(None, _check_health, urls)

        if not recovered:
            continue

        # Backend is back. Clear standby state.
        print("[BACKEND-STANDBY] Backend recovered. Resuming agent.", flush=True)

        setattr(agent, STANDBY_FLAG, False)
        setattr(agent, FAILURE_COUNT_KEY, 0)

        # Inject UI-visible recovery warning
        agent.hist_add_warning(
            "[BACKEND RECOVERED] Inference backend is online. Resuming."
        )

        # Inject context hint as an intervention message — model reads this on resume
        from helpers.history import UserMessage
        agent.intervention = UserMessage(
            message=(
                "The inference backend was temporarily offline. You were in standby. "
                "Your previous context is preserved. The last action you were attempting "
                "may have failed — check whether it completed before continuing. "
                "Do not apologize for the interruption. Simply resume your task."
            )
        )

        # Unpause the loop — the gate at _01 will stop blocking
        agent.context.paused = False

        return


# ── Extension ─────────────────────────────────────────────────────────────────

class BackendStandby(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        try:
            # If already in standby, the gate is handling things — nothing to do here
            if getattr(self.agent, STANDBY_FLAG, False):
                return

            # Check if there's a propagating backend-down exception
            exc_type, exc_val, _ = _sys.exc_info()
            if exc_val is None:
                # No exception propagating — reset failure count on clean turns
                setattr(self.agent, FAILURE_COUNT_KEY, 0)
                return

            exc_str = str(exc_val)
            if not _is_backend_down(exc_str):
                # Exception exists but it's not a backend-down failure (e.g., reasoning loop)
                return

            # Increment consecutive failure count
            count = getattr(self.agent, FAILURE_COUNT_KEY, 0) + 1
            setattr(self.agent, FAILURE_COUNT_KEY, count)

            print(
                f"[BACKEND-STANDBY] Backend-down failure #{count} detected: "
                f"{exc_str[:120]}",
                flush=True,
            )

            if count < DETECTION_THRESHOLD:
                return  # Not yet at threshold — could be a transient blip

            # Threshold reached — enter standby
            print(
                f"[BACKEND-STANDBY] Threshold reached ({count} consecutive). "
                "Entering standby.",
                flush=True,
            )

            setattr(self.agent, STANDBY_FLAG, True)

            # Inject UI-visible standby notice
            self.agent.hist_add_warning(
                "[BACKEND STANDBY] Inference backend unreachable. Entering standby. "
                "No further processing until backend recovers. Existing context preserved."
            )

            # Derive health URLs from model config and start background poller
            urls = _get_health_urls()
            if not urls:
                print(
                    "[BACKEND-STANDBY] Could not derive health URLs from model config. "
                    "Standby flag set but no poller started — manual restart required.",
                    flush=True,
                )
                return

            print(f"[BACKEND-STANDBY] Polling: {urls}", flush=True)

            task = asyncio.create_task(
                _poll_until_recovered(self.agent, urls)
            )
            setattr(self.agent, POLL_TASK_KEY, task)

        except Exception as e:
            print(f"[BACKEND-STANDBY] Error in standby extension: {e}", flush=True)
