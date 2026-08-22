"""constraint_provenance.py — retract a lesson when the constraint that made it changes.

THE PROBLEM THIS SOLVES
-----------------------
A failure lesson is evidence about a system in a particular configuration. Change the
configuration and the lesson can become not merely outdated but actively wrong, while
continuing to surface with full confidence.

Measured instance, 2026-08-22. A hardcoded 5,000-character write cap produced 357 blocked
writes across the two live agents (Vek 249, Aporia 108). Each was captured as a lesson
teaching avoidance of `text_editor`. The caps were then raised to 400,000 and 100,000 —
and the lessons stayed. Aporia's own reasoning during a later test:

    "The user's explicit instruction overrides the stale memory about text_editor
     being prohibited."

She had to be told explicitly to ignore guidance the system was still serving her. The
capture loop worked perfectly; nothing retracted its output when the premise moved.

WHY GENERAL AND NOT SIZE-SPECIFIC
---------------------------------
Opus's call 2026-08-22: build the general mechanism. Any lesson generated under a
constraint that later changes is stale, and a size-only fix would need rebuilding the
first time a different gate moved. So EVERY lesson records the model, profile and tier it
was born under, and lessons whose gate has a registered probe additionally record that
gate's parameters.

That makes the tier system a first-class input: when a model moves from `local_small` to
`local_large`, the lessons generated under small-model scaffolding stop surfacing, because
the posture that produced them no longer applies.

WHAT STALENESS MEANS HERE
-------------------------
Ordered, first match wins:

  1. No snapshot recorded    -> NOT stale. Unknown is not the same as changed, and
                                suppressing every pre-existing lesson on rollout would be
                                a silent mass deletion.
  2. Tier changed            -> stale. The scaffolding posture differs.
  3. Constraint gone         -> stale. The gate that produced it no longer resolves.
  4. Limit relaxed >= 2x     -> stale. A tightened limit is NOT stale: the lesson is more
                                relevant than when it was captured, not less.
  5. otherwise               -> fresh.

SUPPRESS, NEVER DELETE. A stale lesson stops surfacing and is annotated. It stays on disk
with its recurrence ledger intact, because "this was true under a configuration we no
longer run" is worth keeping and is not the same as "this was wrong".

STORED AS A SIDECAR, NOT FRONTMATTER
------------------------------------
`.constraint.json` beside SKILL.md. Deliberately not frontmatter: A0's
`validate_skill_md` drops any skill whose frontmatter fails validation, and an invalid
skill is INVISIBLE rather than loudly broken (verified 2026-08-22). Adding speculative
keys there risks silently unpublishing the very lessons this is meant to curate. A dotfile
is also skipped by A0's skill discovery, which rglobs but ignores dot-entries.

No LLM calls. File I/O, dict comparison and arithmetic.
"""

import json
import os
import time

PROVENANCE_FILENAME = ".constraint.json"

# A limit must relax by at least this factor before its lessons are considered stale.
# 5,000 -> 100,000 is 20x; 5,000 -> 6,000 is not a change of kind and should not wipe
# accumulated evidence.
DEFAULT_RELAX_FACTOR = 2.0

PLUGIN_CONFIG_PATH = "/a0/usr/plugins/_exocortex/config/config.json"
_HELPERS = "/a0/usr/plugins/_exocortex/helpers"


def cfg() -> dict:
    """Config with explicit defaults. Absent section -> defaults, never a crash."""
    out = {"enabled": True, "relax_factor": DEFAULT_RELAX_FACTOR}
    try:
        with open(PLUGIN_CONFIG_PATH, encoding="utf-8") as fh:
            section = (json.load(fh) or {}).get("constraint_provenance", {})
        if isinstance(section, dict):
            out.update({k: section[k] for k in out if k in section})
    except Exception:
        pass
    return out


# ── constraint probes ─────────────────────────────────────────────────────────
# error_class -> callable(agent) -> dict | None
#
# A probe reports the CURRENT state of the gate that produces this error class. Returning
# None means "this gate no longer constrains anything", which is itself a staleness
# signal. Add an entry when a new gate starts generating lessons; a lesson with no probe
# still gets model/profile/tier tracking, which is enough for tier-change staleness.


def _probe_write_size(agent=None) -> dict | None:
    try:
        import sys
        if _HELPERS not in sys.path:
            sys.path.insert(0, _HELPERS)
        import write_threshold as wt
        conf, src = wt.resolve(agent)
        return {"kind": "write_size",
                "base_limit": int(conf.get("base_limit", 0)),
                "source": src}
    except Exception:
        return None


PROBES = {
    "oversized_tool_write": _probe_write_size,
}


def _model_context(agent=None) -> dict:
    """Model, profile and tier. Recorded for EVERY lesson, probe or not."""
    out = {"model_id": "", "profile": "", "tier": ""}
    try:
        import sys
        if _HELPERS not in sys.path:
            sys.path.insert(0, _HELPERS)
        import model_profile as mp
        out["model_id"] = mp.active_model_id(agent) or ""
        prof, src = mp.load_profile(agent)
        out["profile"] = src or ""
        es = prof.get("evaluation_summary", {}) if isinstance(prof, dict) else {}
        out["tier"] = es.get("recommended_prosthetic_level", "") or ""
    except Exception:
        pass
    return out


# ── snapshot / io ─────────────────────────────────────────────────────────────

def snapshot(agent=None, error_class: str = "") -> dict:
    """The constraint state a lesson is being born under."""
    snap = {
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "error_class": error_class,
        "model": _model_context(agent),
    }
    probe = PROBES.get(error_class)
    if probe:
        snap["constraint"] = probe(agent)
    return snap


def path_for(skill_dir: str) -> str:
    return os.path.join(skill_dir, PROVENANCE_FILENAME)


def write(skill_dir: str, snap: dict) -> bool:
    try:
        os.makedirs(skill_dir, exist_ok=True)
        with open(path_for(skill_dir), "w", encoding="utf-8") as fh:
            json.dump(snap, fh, indent=2)
        return True
    except Exception:
        return False


def load(skill_dir: str) -> dict | None:
    try:
        with open(path_for(skill_dir), encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def skill_dir_of(skill_path: str) -> str:
    """Accept either the SKILL.md path or its directory."""
    p = str(skill_path or "")
    if not p:
        return ""
    return os.path.dirname(p) if p.lower().endswith(".md") else p


# ── the decision ──────────────────────────────────────────────────────────────

def staleness(recorded: dict | None, agent=None, relax_factor: float | None = None):
    """(is_stale, reason). See the ordered rules in the module docstring."""
    if not isinstance(recorded, dict):
        return False, ""          # rule 1 — unknown is not changed

    factor = float(relax_factor if relax_factor is not None else cfg()["relax_factor"])
    now_model = _model_context(agent)
    then_model = recorded.get("model") or {}

    then_tier, now_tier = then_model.get("tier", ""), now_model.get("tier", "")
    if then_tier and now_tier and then_tier != now_tier:
        return True, f"model tier changed {then_tier} -> {now_tier}"

    then_c = recorded.get("constraint")
    if not isinstance(then_c, dict):
        return False, ""          # nothing gate-specific was recorded

    probe = PROBES.get(recorded.get("error_class", ""))
    now_c = probe(agent) if probe else None
    if now_c is None:
        return True, "generating constraint no longer resolves"

    then_limit = then_c.get("base_limit")
    now_limit = now_c.get("base_limit")
    if isinstance(then_limit, (int, float)) and isinstance(now_limit, (int, float)):
        if then_limit > 0 and now_limit >= then_limit * factor:
            return True, (f"{then_c.get('kind', 'constraint')} relaxed "
                          f"{int(then_limit):,} -> {int(now_limit):,} "
                          f"({now_limit / then_limit:.1f}x)")

    return False, ""


STALE_ANNOTATION = "[STALE: generating constraint changed — {reason}]"


def annotate(reason: str) -> str:
    return STALE_ANNOTATION.format(reason=reason or "unknown")
