"""llm_config.py — Dynamic LLM model resolution for SWARMFISH.

When SWARMFISH_LLM_MODEL is not set, discovers the active model from LM Studio's
/v1/models endpoint at startup. This keeps SWARMFISH in sync with Agent Zero's
model config automatically — change the model in A0, restart SWARMFISH, done.

Priority:
  1. SWARMFISH_LLM_MODEL env var  (explicit override)
  2. First model from LM Studio /v1/models  (auto-discover)
  3. Empty string  (LM Studio uses whatever is loaded)
"""
import json
import logging
import os
import urllib.request

log = logging.getLogger(__name__)

_LLM_URL   = os.environ.get("SWARMFISH_LLM_URL", "http://host.docker.internal:1234/v1").rstrip("/")
_MODEL_ENV = os.environ.get("SWARMFISH_LLM_MODEL", "").strip()

_resolved: str | None = None  # None = not yet queried; "" = query failed


def get_llm_model() -> str:
    """Return the model name for SWARMFISH LLM calls, resolving once per process."""
    global _resolved

    if _MODEL_ENV:
        return _MODEL_ENV

    if _resolved is not None:
        return _resolved

    try:
        req = urllib.request.Request(
            f"{_LLM_URL}/models",
            headers={"Authorization": "Bearer lm-studio"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        models = data.get("data", [])
        if models:
            _resolved = models[0].get("id", "")
            log.info("[SWARMFISH] Auto-discovered LLM model: %s", _resolved)
            return _resolved
    except Exception as exc:
        log.warning("[SWARMFISH] Could not auto-discover model from %s/models: %s", _LLM_URL, exc)

    _resolved = ""
    return _resolved
