"""
Metacognitive Injection — Model Self-Knowledge at Runtime
==========================================================
Hook: before_main_llm_call (_14_)

Reads the active model profile and injects a brief, factual capability note
into the LLM context before each call — giving the model honest self-knowledge
about its training cutoff, confabulation risk, and current task volatility.

The personality layer (Major Zero) gives the model identity: who it is.
This layer gives the model configuration awareness: what it doesn't know.

Injection format:
  [MODEL CONFIGURATION]
  {model_id} | cutoff: {YYYY-MM} | confabulation risk: {level}
  Domain: {domain} ({volatility}) — verify time-sensitive values with tools.
  EI active: ungrounded claims will be flagged.

Conditional behavior:
  - Structural/deterministic domains (coding, bugfix, system_admin): skip injection
    unless confabulation_risk == "high" (override).
  - All other domains: inject with volatility-appropriate domain line.
  - Missing profile or disabled config: graceful skip, no crash.

No LLM calls. Fully deterministic. Runs after BST (_11_) so domain is available.
"""

import json
import os
from typing import Optional

from agent import LoopData
from helpers.extension import Extension

SETTINGS_PATH  = "/a0/usr/settings.json"
PROFILE_ROOT   = "/a0/usr/Exocortex/eval/model_profiles"
CONFIG_KEY     = "metacognitive_injection"

# Domains where temporal confabulation is structurally impossible or irrelevant.
# Skip injection unless confabulation_risk forces it.
STRUCTURAL_DOMAINS = {"coding", "bugfix", "system_admin"}

# Volatility labels per domain — drives the domain line wording.
DOMAIN_VOLATILITY = {
    "investigation":  ("high temporal volatility", True),
    "analysis":       ("high temporal volatility", True),
    "research":       ("moderate temporal volatility", True),
    "conversation":   ("moderate temporal volatility", True),
    "planning":       ("moderate temporal volatility", True),
    "coding":         ("structural — temporal risk low", False),
    "bugfix":         ("structural — temporal risk low", False),
    "system_admin":   ("structural — temporal risk low", False),
}

# Domain line template for volatile domains.
_VOLATILE_LINE = (
    "Domain: {domain} ({volatility}) — verify time-sensitive values "
    "with tools before asserting."
)
# Domain line for non-volatile but forced injection (high risk override).
_STRUCTURAL_LINE = "Domain: {domain} — temporal confabulation risk elevated despite structural task."


class MetacognitiveInjection(Extension):
    """Inject model configuration awareness before each LLM call."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            cfg = _load_config(self.agent)
            if not cfg.get("enabled", True):
                return

            profile  = _load_model_profile()
            temporal = profile.get("temporal", {})
            model_id = _get_model_id()
            risk     = temporal.get("confabulation_risk", "unknown")
            cutoff   = _format_cutoff(temporal.get("training_data_cutoff"))

            domain   = _get_bst_domain(loop_data, self.agent)
            skip_domains = set(cfg.get("skip_domains", list(STRUCTURAL_DOMAINS)))
            force_risk   = cfg.get("always_inject_if_risk", "high")

            # Gate: skip structural domains unless risk forces injection
            if domain in skip_domains and risk != force_risk:
                return

            block = _build_block(model_id, cutoff, risk, domain, skip_domains, force_risk)
            if not block:
                return

            user_msg = _get_last_user_message(loop_data.history_output)
            if not user_msg:
                return

            existing = user_msg.get("content", "")
            user_msg["content"] = block + "\n\n" + str(existing)

            print(
                f"[META] Injected model config note. "
                f"model={model_id} cutoff={cutoff} risk={risk} domain={domain}",
                flush=True,
            )

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[META] Error (passthrough): {e}",
                )
            except Exception:
                pass


# ── Block Construction ─────────────────────────────────────────────────────────

def _build_block(
    model_id: str,
    cutoff: str,
    risk: str,
    domain: str,
    skip_domains: set,
    force_risk: str,
) -> str:
    lines = [
        "[MODEL CONFIGURATION]",
        f"{model_id} | cutoff: {cutoff} | confabulation risk: {risk}",
    ]

    vol_label, is_volatile = DOMAIN_VOLATILITY.get(domain, ("unknown volatility", True))

    if domain in skip_domains and risk == force_risk:
        # Forced injection on structural domain
        lines.append(_STRUCTURAL_LINE.format(domain=domain))
    elif is_volatile:
        lines.append(_VOLATILE_LINE.format(domain=domain, volatility=vol_label))
    # else: non-volatile and not forced — domain line omitted (just the header)

    lines.append("EI active: ungrounded claims will be flagged.")
    return "\n".join(lines)


# ── Profile / Config Loading ───────────────────────────────────────────────────

def _load_model_profile() -> dict:
    """Load model profile via settings → profile file. Returns {} on error."""
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            settings = json.load(f)
        model_name = settings.get("chat_model_name", "")
        model_id   = model_name.split("@")[0].strip()
        if not model_id:
            return {}
        path = os.path.join(PROFILE_ROOT, f"{model_id}.json")
        if not os.path.exists(path):
            path = os.path.join(PROFILE_ROOT, "default.json")
            if not os.path.exists(path):
                return {}
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _load_config(agent) -> dict:
    """Read metacognitive_injection section from agent config. Defaults if missing."""
    try:
        cfg = getattr(agent, "config", None)
        if cfg is None:
            return {}
        raw = cfg if isinstance(cfg, dict) else vars(cfg)
        return raw.get(CONFIG_KEY, {})
    except Exception:
        return {}


def _get_model_id() -> str:
    """Return bare model ID (strip quantisation suffix)."""
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            settings = json.load(f)
        name = settings.get("chat_model_name", "unknown")
        return name.split("@")[0].strip() or "unknown"
    except Exception:
        return "unknown"


def _format_cutoff(cutoff_str: Optional[str]) -> str:
    """Return YYYY-MM cutoff label, or 'unknown' if not set."""
    if not cutoff_str:
        return "unknown"
    try:
        # ISO date — trim to YYYY-MM
        return cutoff_str[:7]
    except Exception:
        return "unknown"


# ── Domain / Message Helpers ───────────────────────────────────────────────────

def _get_bst_domain(loop_data: LoopData, agent) -> str:
    """
    Read BST-classified domain. Primary source: extras_persistent["_bst_domain"].
    Fallback: agent._bst_store belief state.
    Returns "unknown" if BST hasn't run or produced no classification.
    """
    try:
        ep = getattr(loop_data, "extras_persistent", None) or {}
        domain = ep.get("_bst_domain")
        if domain:
            return str(domain)
    except Exception:
        pass

    try:
        store = getattr(agent, "_bst_store", None) or {}
        belief = store.get("__bst_belief_state__")
        if belief and hasattr(belief, "primary_domain"):
            return str(belief.primary_domain)
    except Exception:
        pass

    return "unknown"


def _get_last_user_message(history_output: list) -> Optional[dict]:
    """Find the most recent operator message in loop history."""
    if not history_output:
        return None
    for msg in reversed(history_output):
        if not isinstance(msg, dict):
            continue
        if not msg.get("ai", True):
            content = msg.get("content", "")
            if isinstance(content, dict) and "user_message" in content:
                return msg
            if isinstance(content, str) and content:
                return msg
    return None
