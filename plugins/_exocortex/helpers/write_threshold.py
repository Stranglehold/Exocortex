"""
write_threshold.py — A3: complexity-keyed, profile-sourced write limit

THE FINDING THIS IMPLEMENTS
---------------------------
From the JSON-reliability arc (Aug 2026), the one conclusion that survived every
attempt to kill it: **complexity predicts failure, length does not.** A 20K prose
payload can pass where a 12K payload with three code fences fails, because what
truncates a tool call is the escaping burden inside a JSON string field, not the
character count.

The gate it replaces used a single hardcoded `len(content) > 5000` for every model and
every kind of content.

DESIGN — AND WHAT IT DELIBERATELY DOES NOT CLAIM
------------------------------------------------
    effective_limit = base_limit / complexity_score        (score >= 1.0)

Complexity can only ever *lower* the limit, never raise it. With plain prose the score
is 1.0 and the gate behaves **exactly as it does today**. That is the point: A3 ships a
mechanism, not a behaviour change, so nothing regresses on evidence we do not have.

**The coefficients below are UNMEASURED starting points, not findings.** The JSON
coherence sweep that would calibrate them (each active model, payloads at
4K/8K/12K/16K/24K/32K, measuring where structural validity breaks) was specified but
never run — no results exist in the repo. So these are conservative placeholders chosen
to be roughly neutral on ordinary content, every one of them overridable from the model
profile, and they should be replaced with measured values the moment a sweep exists.
Writing invented numbers into a profile as though they were measurements is precisely
what the project's epistemic rules forbid, so the profile ships without them.

SOURCING (three layers, lowest to highest)
------------------------------------------
    DEFAULTS below          last-resort backstop, only when the files below are unreadable
    plugin config.json      `meta_gate.write_size` — the operator-tunable global default
    model profile           `meta_gate.write_size` — per-model, and only where MEASURED

Each layer overrides only the keys it sets, so a profile may carry `base_limit` alone
without inheriting stale penalties, and an operator may move the global default without
touching code or inventing a per-model measurement.

`describe()` reports which layer supplied `base_limit`, not merely which profile resolved
— those are different questions, and conflating them previously let a block report
`profile=<id>` while the number in force came from the hardcoded backstop.

Profile section shape, e.g.

    "meta_gate": {
      "write_size": {
        "base_limit": 5000,
        "fence_penalty": 0.35,
        "escape_penalty": 6.0,
        "max_score": 4.0
      }
    }

Absent at every layer -> the backstops below.

No LLM calls. Arithmetic and character counting.
"""

import re

# LAST-RESORT BACKSTOP ONLY — not the operator-facing default.
#
# `base_limit` used to live here as the single hardcoded number that decided every
# write on every model. That literal is what produced 357 blocked writes across the two
# live agents (Vek 249, Aporia 108 by 2026-08-22), each one captured as a failure lesson
# that then taught the agent to avoid text_editor entirely.
#
# Resolution order is now, lowest to highest (see resolve()):
#     these backstops  <  plugin config meta_gate.write_size  <  profile meta_gate.write_size
#
# The operator-tunable value belongs in the plugin config; a per-model MEASURED value
# belongs in that model's profile. Values here apply only when both of those are
# unreadable, so this is a guard against a missing file, not a policy.
DEFAULTS = {
    # Backstop, held at the historical value so behaviour cannot silently change when
    # config is absent. NOT a measurement — the coherence sweep that would calibrate it
    # has still never been run.
    "base_limit": 5000,
    # each fenced code block tightens the limit by this fraction (UNMEASURED)
    "fence_penalty": 0.35,
    # multiplier on the density of characters that need JSON escaping (UNMEASURED)
    "escape_penalty": 6.0,
    # ceiling on the score, so a pathological payload still gets a usable limit
    "max_score": 4.0,
    # never tighten below this, or the agent cannot write anything at all
    "floor_limit": 800,
}

_RX_FENCE = re.compile(r"```")
# The characters that actually cost something inside a JSON string field.
_RX_ESCAPE = re.compile(r'["\\\n\t\r]')


def complexity(content: str, conf: dict | None = None) -> tuple[float, dict]:
    """Return (score >= 1.0, signals). Score 1.0 means 'plain prose, no penalty'."""
    c = {**DEFAULTS, **(conf or {})}
    text = content or ""
    n = max(len(text), 1)

    fences = len(_RX_FENCE.findall(text)) // 2          # pairs, not delimiters
    escapes = len(_RX_ESCAPE.findall(text))
    escape_density = escapes / n

    score = 1.0
    score += float(c["fence_penalty"]) * fences
    score += float(c["escape_penalty"]) * escape_density
    score = max(1.0, min(score, float(c["max_score"])))

    return score, {
        "fenced_blocks": fences,
        "escape_chars": escapes,
        "escape_density": round(escape_density, 4),
        "score": round(score, 3),
    }


def effective_limit(content: str, conf: dict | None = None) -> tuple[int, dict]:
    """Return (limit_in_chars, signals) for this specific content."""
    c = {**DEFAULTS, **(conf or {})}
    score, sig = complexity(content, c)
    limit = int(float(c["base_limit"]) / score)
    limit = max(limit, int(c["floor_limit"]))
    sig["base_limit"] = int(c["base_limit"])
    sig["effective_limit"] = limit
    return limit, sig


PLUGIN_CONFIG_PATH = "/a0/usr/plugins/_exocortex/config/config.json"


def _section(obj, *path) -> dict:
    """Walk a nested dict path, returning {} at the first thing that is not a dict."""
    cur = obj
    for key in path:
        if not isinstance(cur, dict):
            return {}
        cur = cur.get(key, {})
    return cur if isinstance(cur, dict) else {}


def _config_write_size() -> dict:
    """Operator-tunable `meta_gate.write_size` from the plugin config ({} if absent).

    Separated from the profile lookup deliberately: a profile value is a claim about ONE
    model and should only exist where it was measured, whereas this is the global default
    an operator can change without editing code or inventing a per-model measurement.
    """
    try:
        import json
        with open(PLUGIN_CONFIG_PATH, encoding="utf-8") as fh:
            return _section(json.load(fh), "meta_gate", "write_size")
    except Exception:
        return {}


def resolve(agent=None) -> tuple[dict, str]:
    """Config for the active model, and where the numbers came from.

    Layered lowest to highest: backstop DEFAULTS, then the plugin config, then the active
    model profile. Each layer only overrides the keys it actually sets, so an operator can
    move the global default without disturbing a measured per-model value, and a profile
    can carry `base_limit` alone without inheriting stale penalties.

    The returned source names where `base_limit` — the number the block message quotes —
    actually came from. It used to return the resolved profile id even when that profile
    supplied no write_size section at all, so a block could report `profile=ornith-1.0-35b`
    while the limit in force was the hardcoded backstop. Reporting the layer that really
    set the number is the whole point of having layers.
    """
    conf = dict(DEFAULTS)
    src = "backstop"

    cfg = _config_write_size()
    if cfg:
        conf.update(cfg)
        if "base_limit" in cfg:
            src = "config"

    try:
        import model_profile as mp
        prof, pid = mp.load_profile(agent)
        ws = _section(prof, "meta_gate", "write_size")
        if ws:
            conf.update(ws)
            if "base_limit" in ws:
                src = pid or "profile"
    except Exception:
        pass

    return conf, src


# Models already warned about in this process, so the notice below is loud once rather
# than on every single tool call. Flooding the log would bury the [MetaGate-SIZE] lines
# the warning exists to explain.
_WARNED_NO_PROFILE = set()


def profile_sourced(src: str) -> bool:
    """True when a model PROFILE supplied base_limit, rather than a global default."""
    return src not in ("config", "backstop") and not src.startswith("degraded:")


def describe(content: str, agent=None) -> dict:
    """Everything the gate needs, including where the numbers came from."""
    conf, src = resolve(agent)
    limit, sig = effective_limit(content, conf)
    sig["profile"] = src
    sig["profile_sourced"] = profile_sourced(src)

    # A model with no profile silently inheriting the global default is exactly how the
    # old hardcoded 5,000 manufactured 357 blocked writes without anyone noticing it was
    # a default rather than a decision. Hold the value, but never hold it quietly.
    if not sig["profile_sourced"]:
        try:
            import model_profile as mp
            model = mp.active_model_id(agent) or "<unresolved>"
        except Exception:
            model = "<unresolved>"
        if model not in _WARNED_NO_PROFILE:
            _WARNED_NO_PROFILE.add(model)
            try:
                print(f"[WRITE-LIMIT] No profile-sourced write limit for model "
                      f"'{model}'. Using {src} base_limit={int(conf['base_limit']):,}. "
                      f"This may be too restrictive — run the coherence sweep or add "
                      f"meta_gate.write_size.base_limit to that model's profile.",
                      flush=True)
            except Exception:
                pass
    sig["length"] = len(content or "")
    sig["over"] = sig["length"] > limit
    return sig
