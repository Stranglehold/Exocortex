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

PROFILE SOURCING
----------------
Read from the active profile's `meta_gate.write_size` section, e.g.

    "meta_gate": {
      "write_size": {
        "base_limit": 5000,
        "fence_penalty": 0.35,
        "escape_penalty": 6.0,
        "max_score": 4.0
      }
    }

Absent section -> defaults below. `describe()` reports which profile actually supplied
the numbers, so a caller can tell a per-model threshold from a silent default.

No LLM calls. Arithmetic and character counting.
"""

import re

DEFAULTS = {
    # today's hardcoded value, kept so plain prose is unaffected
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


def resolve(agent=None) -> tuple[dict, str]:
    """Config for the active model, and the profile id it came from."""
    try:
        import model_profile as mp
        prof, src = mp.load_profile(agent)
        mg = prof.get("meta_gate", {}) if isinstance(prof, dict) else {}
        ws = mg.get("write_size", {}) if isinstance(mg, dict) else {}
        return {**DEFAULTS, **(ws if isinstance(ws, dict) else {})}, (src or "none")
    except Exception:
        return dict(DEFAULTS), "none"


def describe(content: str, agent=None) -> dict:
    """Everything the gate needs, including where the numbers came from."""
    conf, src = resolve(agent)
    limit, sig = effective_limit(content, conf)
    sig["profile"] = src
    sig["length"] = len(content or "")
    sig["over"] = sig["length"] > limit
    return sig
