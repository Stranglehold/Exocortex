"""
Skill-Write Normalizer (write-time trigger)
===========================================
Hook: tool_execute_after (_34_)
Tier 1: Mechanical — zero LLM calls.

Closes the LATENCY gap in skill-frontmatter self-heal.

The deterministic repair already exists: scripts/normalize_skills.py:normalize_root()
fixes invalid SKILL.md frontmatter — including the "no top frontmatter / readme-style"
case (# title + prose, YAML block missing) — and integrity_check.py runs it during
MAINTAIN cycles. But until the next MAINTAIN, a freshly-authored invalid skill is
INVISIBLE to A0's discovery. On 2026-06-21 the self-improvement agent authored a
`financial-services` meta-skill as a readme (# title + prose, no frontmatter at byte 0)
and could not see its own creation — the latest, most-wanted capability, lost until a
maintenance sweep it might not reach for cycles.

This extension runs the SAME normalizer immediately, at write time: after a file-writing
tool, if any SKILL.md under the skill roots was written in the last few minutes, it calls
normalize_root(apply=True) so the repair lands before the agent's next turn. The skill the
agent built is visible on the very next discovery pass.

Design choices:
- REUSE, don't duplicate. The repair logic (name-from-dir, description-from-body,
  validate-first idempotency, hidden-dir skip) lives in normalize_root. This extension
  is only the write-time TRIGGER.
- Bounded: a cheap recent-mtime pre-check gates the (heavier) normalize_root call, so
  most tool calls do near-zero work.
- Idempotent + safe: normalize_root validates each skill first and only rewrites INVALID
  frontmatter, never the body; clean skills are untouched.
- Graceful passthrough on every error — never breaks a tool call.

Pattern source: _31/_32 (same hook, same signature). Repair logic: scripts/normalize_skills.py.
Sibling (maintenance-time): self-improvement/integrity_check.py.
Spec: specs/SKILL_WRITE_NORMALIZER_DESIGN_NOTE.md
"""

import importlib
import json
import os
import sys
import time
from pathlib import Path

from helpers.extension import Extension

CONFIG_PATH  = "/a0/usr/plugins/_exocortex/config/config.json"
_WRITE_TOOLS = {"code_execution_tool", "text_editor"}
_RECENT_SEC  = 180
# Skill roots where agent-authored skills land (discoverable roots; user-space first).
_ROOTS       = ("/a0/usr/skills", "/a0/skills", "/a0/usr/agents/agent0/skills")
# Candidate locations of the deterministic normalizer (repo clone path is canonical).
_SCRIPT_DIRS = ("/a0/usr/Exocortex/scripts", "/a0/usr/workdir/workspace/scripts")

_DEFAULTS = {"enabled": True}


def _cfg() -> dict:
    try:
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            return json.load(fh).get("skill_normalizer", _DEFAULTS)
    except Exception:
        return _DEFAULTS


def _load_normalizer():
    for d in _SCRIPT_DIRS:
        if os.path.isfile(os.path.join(d, "normalize_skills.py")):
            if d not in sys.path:
                sys.path.insert(0, d)
            try:
                return importlib.import_module("normalize_skills")
            except Exception:
                return None
    return None


def _roots_with_recent_skill(now: float) -> list:
    """Cheap gate: which roots have a SKILL.md written in the last _RECENT_SEC.
    Skips hidden dirs (.hardening_originals, .archive) — same as discovery."""
    hits = []
    for root in _ROOTS:
        rp = Path(root)
        if not rp.exists():
            continue
        for p in rp.rglob("SKILL.md"):
            if any(seg.startswith(".") for seg in p.parts):
                continue
            try:
                if now - p.stat().st_mtime <= _RECENT_SEC:
                    hits.append(root)
                    break
            except Exception:
                continue
    return hits


class SkillWriteNormalizer(Extension):
    """tool_execute_after: repair a just-authored invalid SKILL.md immediately."""

    async def execute(self, response=None, **kwargs) -> None:
        try:
            if not _cfg().get("enabled", True):
                return
            if (kwargs.get("tool_name") or "") not in _WRITE_TOOLS:
                return

            now = time.time()
            roots = _roots_with_recent_skill(now)
            if not roots:
                return  # nothing written recently — near-zero work

            mod = _load_normalizer()
            if not mod or not hasattr(mod, "normalize_root"):
                return

            for root in roots:
                try:
                    report = mod.normalize_root(root=root, apply=True)
                    fixed = report.get("fixed", []) if isinstance(report, dict) else []
                    if fixed:
                        print(f"[SKILL-NORMALIZE] write-time repair under {root} "
                              f"-> now discoverable: {fixed}", flush=True)
                except Exception as e:
                    print(f"[SKILL-NORMALIZE] normalize_root error ({root}): {e}", flush=True)

        except Exception as e:
            print(f"[SKILL-NORMALIZE] Error (passthrough): {e}", flush=True)
