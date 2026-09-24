"""
Failure-Lesson Capture — Cycle-to-Skill Pipeline, Path A (deterministic)
========================================================================
Hook: tool_execute_after
Priority: _31 (runs AFTER _20_error_comprehension sets the diagnosis,
          and AFTER _30_tool_fallback_logger)

Turns a classified tool failure into a discoverable, reusable skill so the
same failure does not silently recur. FULLY DETERMINISTIC — no LLM call,
zero API cost. The lesson content is already produced by
_20_error_comprehension (_error_diagnosis: error_class, causal_chain,
suggested_actions, anti_actions); this extension templates that into a
valid SKILL.md under /a0/usr/skills/auto-generated/failure-lessons/.

Consumption (verified 2026-05-30): A0 core helpers/skills.py discovers
SKILL.md recursively via root.rglob() under /a0/usr/skills/, validates the
frontmatter, and lexical-matches description/triggers into context via
_66_include_active_skills. So a VALID skill written here is found by future
cycles. (Frontmatter MUST be minimal+valid: name + description [+ triggers];
malformed frontmatter is silently rejected by list_skills validation.)

Spec: specs/CYCLE_TO_SKILL_PIPELINE_SPEC_L3.md
Log tag: [SKILL-CAPTURE]
"""

import json
import os
import re
import time

from agent import LoopData
from helpers.extension import Extension

DIAGNOSIS_KEY        = "_error_diagnosis"      # set by _20_error_comprehension
FAILURE_TRACKER_KEY  = "_failure_tracker"      # {tool: consecutive_count}, _30/_20
CAPTURE_COUNT_ATTR   = "_skills_captured_this_cycle"  # in-session running tally

CONFIG_PATH   = "/a0/usr/Exocortex/config.json"
SKILLS_ROOT   = "/a0/usr/skills/auto-generated/failure-lessons"
# Per-cycle counter file that cycle_close.py reads for ground-truth skills_captured.
PENDING_COUNT = "/a0/usr/workdir/workspace/office/skills_captured_pending.json"

_DEFAULTS = {
    "enabled": True,
    "failure_lesson_capture": True,
    "max_failure_captures_per_cycle": 3,
}


def _cfg() -> dict:
    try:
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            c = json.load(fh).get("cycle_to_skill", {})
    except Exception:
        c = {}
    return {**_DEFAULTS, **(c if isinstance(c, dict) else {})}


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").strip().lower()).strip("-")[:60]


class FailureLessonCapture(Extension):
    """tool_execute_after: persist a classified failure as a discoverable skill."""

    async def execute(self, response=None, **kwargs) -> None:
        try:
            cfg = _cfg()
            if not cfg["enabled"] or not cfg["failure_lesson_capture"]:
                return

            diag = self.agent.get_data(DIAGNOSIS_KEY)
            if not isinstance(diag, dict) or not diag.get("error_class"):
                return  # no classified failure this turn

            tool = kwargs.get("tool_name") or "tool"
            if tool == "response":
                return

            # Per-cycle cap — never flood the library from one runaway cycle.
            captured = getattr(self.agent, CAPTURE_COUNT_ATTR, 0) or 0
            if captured >= int(cfg["max_failure_captures_per_cycle"]):
                return

            error_class = str(diag["error_class"])
            slug = _slugify(f"{tool}-{error_class}")
            skill_dir = os.path.join(SKILLS_ROOT, slug)
            skill_md  = os.path.join(skill_dir, "SKILL.md")

            # ── Dedup at write time (heads off the 34-duplicate mess) ──────────
            if os.path.exists(skill_md):
                self._note_recurrence(skill_dir, tool, error_class)
                return

            # ── Write a VALID minimal-frontmatter skill (deterministic) ───────
            os.makedirs(skill_dir, exist_ok=True)
            with open(skill_md, "w", encoding="utf-8") as f:
                f.write(self._render_skill(slug, tool, diag))

            # Seed the per-skill memory (V17 idea: usage/recurrence notes).
            self._note_recurrence(skill_dir, tool, error_class, first=True)

            # Tally — in-session attr + the cross-process counter cycle_close reads.
            setattr(self.agent, CAPTURE_COUNT_ATTR, captured + 1)
            self._bump_pending_count()

            print(
                f"[SKILL-CAPTURE] failure-lesson written: {slug} "
                f"(tool={tool} error_class={error_class})",
                flush=True,
            )
        except Exception as e:
            # Never break a cycle on capture failure.
            print(f"[SKILL-CAPTURE] error (passthrough): {e}", flush=True)

    # ── Skill rendering (valid frontmatter: name + description + triggers) ────
    def _render_skill(self, slug: str, tool: str, diag: dict) -> str:
        causal   = str(diag.get("causal_chain", "")).strip()
        antis    = diag.get("anti_actions", []) or []
        suggests = diag.get("suggested_actions", []) or []
        evidence = (diag.get("evidence") or [""])[0]
        error_class = str(diag.get("error_class", ""))

        # Description + triggers carry lexical phrases that match the RECURRENCE
        # context (so the relevant-skills lexical search surfaces this skill when
        # the agent is about to do the same operation).
        desc = (
            f"Use before calling {tool} in a context that previously failed with "
            f"'{error_class}'. {causal[:160]}"
        ).replace("\n", " ").strip()
        triggers = sorted({
            tool,
            f"{tool} {error_class}".strip(),
            error_class.replace("_", " "),
        } - {""})
        trig_yaml = "[" + ", ".join(json.dumps(t) for t in triggers) + "]"

        def bullets(items):
            return "\n".join(f"- {str(x).strip()}" for x in items if str(x).strip()) or "- (none recorded)"

        # Pre-registered falsifiable claim (Self-Assessment Framework Phase 1),
        # derived from the recovery action; confidence starts at "probable" (Kent's
        # WEP). Validated 2026-06-17: these scalar fields pass list_skills
        # validation (validate_skill only checks name/description/compatibility).
        desired = (str(suggests[0]).strip().rstrip(".") if suggests
                   else "follow the documented recovery")
        success_criterion = (f"Agent applies the recovery ('{desired}') instead of "
                             f"repeating the {error_class.replace('_', ' ')} failure")
        return (
            "---\n"
            f"name: {slug}\n"
            f"description: {json.dumps(desc)}\n"
            f"triggers: {trig_yaml}\n"
            f"success_criterion: {json.dumps(success_criterion)}\n"
            "confidence: probable\n"
            "---\n\n"
            f"# Failure lesson: {tool} — {error_class}\n\n"
            "Captured automatically from a classified tool failure "
            "(Cycle-to-Skill Pipeline, Path A). Check this before repeating the operation.\n\n"
            "## What happens\n"
            f"{causal or '(no causal chain recorded)'}\n\n"
            f"Evidence (matched pattern): `{evidence}`\n\n"
            "## Avoid\n"
            f"{bullets(antis)}\n\n"
            "## Do instead\n"
            f"{bullets(suggests)}\n"
        )

    # ── Per-skill .memory.md (append-only usage/recurrence notes) ─────────────
    def _note_recurrence(self, skill_dir: str, tool: str, error_class: str, first: bool = False) -> None:
        try:
            os.makedirs(skill_dir, exist_ok=True)
            line = (
                f"- {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} "
                f"{'created from' if first else 'recurred:'} {tool}/{error_class}\n"
            )
            with open(os.path.join(skill_dir, ".memory.md"), "a", encoding="utf-8") as f:
                if first:
                    f.write(f"# Usage notes — {tool}/{error_class}\n\n")
                f.write(line)
        except Exception:
            pass

    # ── Cross-process per-cycle counter (cycle_close reads ground truth) ──────
    def _bump_pending_count(self) -> None:
        try:
            os.makedirs(os.path.dirname(PENDING_COUNT), exist_ok=True)
            cur = {"count": 0}
            if os.path.exists(PENDING_COUNT):
                try:
                    with open(PENDING_COUNT, encoding="utf-8") as f:
                        cur = json.load(f)
                except Exception:
                    cur = {"count": 0}
            cur["count"] = int(cur.get("count", 0)) + 1
            tmp = PENDING_COUNT + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(cur, f)
            os.replace(tmp, PENDING_COUNT)
        except Exception:
            pass
