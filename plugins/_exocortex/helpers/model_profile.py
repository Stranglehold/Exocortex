"""
model_profile.py — one resolution of "which model profile is active"

WHY THIS EXISTS
---------------
The resolution logic (agent.config -> plugin config -> strip quant suffix -> flatten
"/" to "_" -> look up <id>.json) was written inside `_50_supervisor_loop.py`. A3 needs
the same resolution in `_20_meta_reasoning_gate.py`. Two copies would be two notions of
"the active model", free to drift the moment either is edited — the defect class this
codebase produces most reliably. So it is extracted here and both callers import it.

WHAT A PROFILE IS FOR
---------------------
Per-model calibration: this model's thresholds, not a global constant. Note the live
gap as of 2026-08-19 — `agent-zero-v2` runs ornith-1.0-35b and HAS a profile;
`VekV2` runs deepseek-v4-flash and does NOT, so it silently resolves to `default.json`.
Vek is also the container where the oversized-write failure was worst (203 of 300
recurrences). Any per-model tuning is therefore inert on Vek until that profile exists.
`active_model_id()` is exported so a caller can report which profile it actually got
rather than assuming it got the right one.

No LLM calls. File reads and string handling only.
"""

import json
import os

PROFILE_ROOT = "/a0/usr/plugins/_exocortex/config/model_profiles"
MODEL_CONFIG_PATH = "/a0/usr/plugins/_model_config/config.json"
PRESETS_PATH = "/a0/usr/plugins/_model_config/presets.yaml"


def active_model_id(agent=None) -> str:
    """Resolve the active chat model to a profile id. "" if undeterminable.

    Order: the live UI state on the agent first, then the plugin config file. The
    quantization suffix is stripped ("...@q4_k_m") and "/" is flattened to "_", so
    "jackrong/qwen3.6-27b@q4_k_m" -> "jackrong_qwen3.6-27b".
    """
    raw = ""

    # 1. Live UI state, if this A0 exposes it.
    #    NOTE: A0 v2.9's AgentConfig has only {mcp_servers, profile, knowledge_subdirs,
    #    additional} — there is NO chat_model_name. This lookup is kept for older/other
    #    A0s but returns "" on v2.9. It was the FIRST branch of the original resolver,
    #    which is why the whole profile system silently resolved to nothing here.
    try:
        if agent is not None:
            raw = getattr(getattr(agent, "config", None), "chat_model_name", "") or ""
    except Exception:
        raw = ""

    # 2. A0 v2.9: config.json holds only {"model_preset": "..."} and the real model
    #    name lives in presets.yaml under that preset. This is the path that actually
    #    works on the current containers; verified 2026-08-20 against both.
    if not raw:
        raw = _name_from_presets()

    # 3. Pre-v2.9 layout: config.json carried chat_model.name directly.
    if not raw:
        try:
            with open(MODEL_CONFIG_PATH, encoding="utf-8") as fh:
                raw = json.load(fh).get("chat_model", {}).get("name", "") or ""
        except Exception:
            raw = ""

    if not raw:
        return ""
    return raw.split("@")[0].strip().replace("/", "_")


def _name_from_presets() -> str:
    """Read the active preset's chat model name from the v2.9 preset layout."""
    try:
        with open(MODEL_CONFIG_PATH, encoding="utf-8") as fh:
            selected = (json.load(fh) or {}).get("model_preset") or ""
    except Exception:
        selected = ""
    try:
        import yaml  # present in the A0 venv (6.x)
        with open(PRESETS_PATH, encoding="utf-8") as fh:
            presets = yaml.safe_load(fh) or []
    except Exception:
        return ""
    if not isinstance(presets, list):
        return ""
    # Prefer the selected preset; fall back to the first one that names a chat model,
    # so a missing/renamed selection still resolves rather than silently going default.
    for want_selected in (True, False):
        for p in presets:
            if not isinstance(p, dict):
                continue
            if want_selected and selected and p.get("name") != selected:
                continue
            name = ((p.get("chat") or {}) if isinstance(p.get("chat"), dict) else {}).get("name")
            if name:
                return str(name)
    return ""


def active_api_base() -> str:
    """The active chat model's api_base, resolved the v2.9 way.

    Added 2026-08-21. `_28_backend_standby` hardcoded
    `/a0/usr/agents/agent0/plugins/_model_config/config.json` with NO fallback — a path
    that does not exist on v2.9 — so `_get_health_urls()` returned [] and the backend
    health check had nothing to probe. It was doubly inert: even at the correct path it
    read `chat_model.api_base`, and v2.9's config.json is `{"model_preset": "..."}`.
    The real api_base lives in presets.yaml alongside the model name, which is the same
    schema move that made the whole profile system inert until it was fixed.

    Mirrors _name_from_presets() deliberately: same file, same selected-then-any
    fallback, so the two cannot disagree about which preset is active.

    Returns "" when unresolvable. A cloud provider legitimately has an EMPTY api_base
    (deepseek, openrouter), so "" means "no local endpoint to health-check" rather than
    "lookup failed" — callers should treat it as a skip, not an error.
    """
    try:
        with open(MODEL_CONFIG_PATH, encoding="utf-8") as fh:
            selected = (json.load(fh) or {}).get("model_preset") or ""
    except Exception:
        selected = ""
    try:
        import yaml
        with open(PRESETS_PATH, encoding="utf-8") as fh:
            presets = yaml.safe_load(fh) or []
    except Exception:
        return ""
    if not isinstance(presets, list):
        return ""
    for want_selected in (True, False):
        for p in presets:
            if not isinstance(p, dict):
                continue
            if want_selected and selected and p.get("name") != selected:
                continue
            chat = p.get("chat") if isinstance(p.get("chat"), dict) else {}
            if chat.get("name"):
                return str(chat.get("api_base") or "")
    return ""


def load_profile(agent=None) -> tuple[dict, str]:
    """Return (profile_dict, source_id).

    source_id is the profile actually loaded — the model id, or "default", or "" if
    nothing resolved. Returned deliberately rather than swallowed: a caller that
    thinks it applied a per-model threshold while silently reading default.json is
    exactly the kind of quiet mismatch that goes unnoticed for weeks.
    """
    mid = active_model_id(agent)
    for candidate in ([mid] if mid else []) + ["default"]:
        path = os.path.join(PROFILE_ROOT, f"{candidate}.json")
        try:
            if os.path.exists(path):
                with open(path, encoding="utf-8") as fh:
                    return json.load(fh), candidate
        except Exception:
            continue
    return {}, ""


def profile_section(section: str, agent=None) -> dict:
    """One section of the active profile ({} if absent)."""
    prof, _src = load_profile(agent)
    val = prof.get(section, {})
    return val if isinstance(val, dict) else {}
