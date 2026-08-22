"""
Failure-Lesson Capture (handle_exception) — Cycle-to-Skill Pipeline, Path A
===========================================================================
Hook: _functions/agent/Agent/handle_exception/end
Priority: _45 (after _40_intervention, before _50_repairable / _90_critical)

This is the CORRECTED capture point for gate-raised / unclassified failures.

History: the original error_format leg (error_format/_35) was wired on a wrong
assumption — that error_format is the universal error-surfacing hook. Tracing
A0 v1.18 core (2026-05-31) proved it is NOT: error_format is invoked only from
handle_exception/end/_50_handle_repairable_exception, gated on
`isinstance(exc, RepairableException)`. MetaGate raises a PLAIN ValueError
(_20_meta_reasoning_gate: `raise ValueError("[MetaGate-SIZE] ...")`), which fails
that isinstance check and falls through to _90 (critical) — so error_format never
fires for it. Result: 644 MetaGate-SIZE blocks on v16, ZERO captures.

handle_exception/end IS the genuinely universal surface — EVERY exception
(intervention, repairable, critical) flows through the _40/_50/_90 chain with
`data["exception"]` set. Running at _45 we read the ORIGINAL exception before _90
wraps it as HandledException. This sees plain ValueErrors (MetaGate), repairables,
and criticals alike.

Companion to tool_execute_after/_31_failure_lesson_capture (which captures
failures classified by _20_error_comprehension when the tool actually executed).
_31 stays as-is — correct for its path. This extension covers everything that is
RAISED before/around tool execution and never reaches tool_execute_after.

Fully deterministic. Zero LLM / zero API cost. Observe-only (does not touch
`data` — never modifies/clears the exception, leaving _50/_90 handling intact).
Writes valid minimal-frontmatter skills under auto-generated/failure-lessons/
(same render + same slug as _31/_35, so output dedups across capture points).

Spec: specs/CYCLE_TO_SKILL_PIPELINE_SPEC_L3.md
Log tag: [SKILL-CAPTURE]
"""

import json
import os
import re
import time

from helpers.extension import Extension

CAPTURE_COUNT_ATTR = "_skills_captured_this_cycle"  # shared cap across _31/_35/_45
CONFIG_PATH   = "/a0/usr/plugins/_exocortex/config/config.json"
SKILLS_ROOT   = "/a0/usr/skills/auto-generated/failure-lessons"
PENDING_COUNT = "/a0/usr/workdir/workspace/office/skills_captured_pending.json"

_DEFAULTS = {
    "enabled": True,
    "failure_lesson_capture": True,
    "max_failure_captures_per_cycle": 3,
}

# ── Deterministic marker map: error-message marker → lesson ───────────────────
# Each entry classifies a high-frequency, gate-raised / unclassified error that
# _20_error_comprehension does NOT cover. Lessons carry the recurrence-context
# triggers so the relevant-skills lexical search surfaces them when the agent is
# about to repeat the operation. Add entries as recurring errors are identified.
_MARKERS = [
    {
        "rx": re.compile(r"\[MetaGate-SIZE\]", re.I),
        "error_class": "oversized_tool_write",
        "tool_hint": "text_editor",
        # NO THRESHOLD IS STATED HERE, DELIBERATELY. This template previously asserted
        # "~5000-char JSON payload limit" in three places. Both numbers were wrong:
        #   - the limit is per-model and operator-tunable (write_threshold.resolve()), so
        #     any constant baked in here goes stale the moment a cap moves. It did: the
        #     live limits became 400,000 and 100,000 while the lesson still taught 5,000,
        #     and the surfacer served that on every large-write and wiki-deepening task.
        #   - "JSON payload limit" was never the mechanism. It is a deterministic size
        #     gate, effective_limit = base_limit / complexity_score.
        # The runtime block message already carries the real numbers and is embedded below
        # as `Observed error:`, so the lesson keeps the concrete figures for the instance
        # that produced it without the guidance asserting a constant that can rot.
        "causal": ("A text_editor:write was blocked before execution because the content "
                   "exceeded the write limit in force for this model and this content. "
                   "The limit is not fixed: it is base_limit / complexity_score, where "
                   "base_limit comes from the model profile or the plugin config, and "
                   "complexity rises with fenced code blocks and escape density. The "
                   "block message quotes the actual limit, the base and the multiplier."),
        "anti": ["Do NOT retry text_editor:write with the same oversized content — it will be blocked again",
                 "Do NOT treat any remembered character count as the limit — read the figure in the block message, it is per-model and changes"],
        "do": ["Read the limit quoted in the block message — that is the number in force",
               "For content above it, use code_execution_tool with Python open()/write",
               "Or write in append-mode sections, each under the quoted limit"],
        "triggers": ["text_editor write", "write large file", "write wiki page",
                     "oversized write", "write long content"],
        # Pre-registered falsifiable claim (Self-Assessment Framework Phase 1).
        "success_criterion": ("Agent uses code_execution with Python open() for content "
                              "above the limit quoted in the block message, rather than "
                              "retrying text_editor or avoiding it below that limit"),
    },
]

# Confidence band for newly-captured failure lessons (Kent's WEP). All start at
# "probable" (~75%): we're fairly sure avoiding a known error helps, but not
# certain until transfer-tested (Phase 5). Calibration evolves from there.
DEFAULT_CONFIDENCE = "probable"


def _cfg() -> dict:
    try:
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            c = json.load(fh).get("cycle_to_skill", {})
    except Exception:
        c = {}
    return {**_DEFAULTS, **(c if isinstance(c, dict) else {})}


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").strip().lower()).strip("-")[:60]


def _exc_text(exc) -> str:
    """Stringify the exception robustly, folding in .args ONLY when they add text
    str(exc) doesn't already expose — so a one-level wrapped exception
    (e.g. HandledException(original)) still surfaces the inner marker, without
    duplicating the message for a plain ValueError (where str(exc) == args[0])."""
    try:
        s = str(exc)
    except Exception:
        s = ""
    parts = [s]
    try:
        for a in (getattr(exc, "args", None) or []):
            a = str(a)
            if a and a not in s:
                parts.append(a)
    except Exception:
        pass
    return " ".join(p for p in parts if p)


class FailureLessonCaptureHandleException(Extension):
    """handle_exception/end: capture gate-raised / unclassified high-frequency failures."""

    async def execute(self, data: dict = {}, **kwargs) -> None:
        try:
            if not self.agent:
                return

            exc = data.get("exception") if isinstance(data, dict) else None
            if exc is None:
                return

            cfg = _cfg()
            if not cfg["enabled"] or not cfg["failure_lesson_capture"]:
                return

            text = _exc_text(exc)
            if not text:
                return

            marker = next((m for m in _MARKERS if m["rx"].search(text)), None)
            if marker is None:
                return  # only capture known high-frequency errors (conservative)

            captured = getattr(self.agent, CAPTURE_COUNT_ATTR, 0) or 0
            if captured >= int(cfg["max_failure_captures_per_cycle"]):
                return

            tool = marker["tool_hint"] or self._tool_name() or "tool"
            slug = _slug(f"{tool}-{marker['error_class']}")
            sdir = os.path.join(SKILLS_ROOT, slug)
            smd  = os.path.join(sdir, "SKILL.md")

            if os.path.exists(smd):
                self._note(sdir, tool, marker["error_class"])
                return

            os.makedirs(sdir, exist_ok=True)
            with open(smd, "w", encoding="utf-8") as f:
                f.write(self._render(slug, tool, marker, text))
            self._note(sdir, tool, marker["error_class"], first=True)

            setattr(self.agent, CAPTURE_COUNT_ATTR, captured + 1)
            self._bump()
            print(f"[SKILL-CAPTURE] failure-lesson written: {slug} "
                  f"(tool={tool} error_class={marker['error_class']} via handle_exception)", flush=True)
        except Exception as e:
            print(f"[SKILL-CAPTURE] handle_exception capture error (passthrough): {e}", flush=True)

    def _tool_name(self) -> str:
        try:
            t = getattr(self.agent.loop_data, "current_tool", "") or ""
            return str(t)
        except Exception:
            return ""

    def _render(self, slug: str, tool: str, marker: dict, raw: str) -> str:
        triggers = sorted(set(marker["triggers"]) | {tool})
        trig_yaml = "[" + ", ".join(json.dumps(t) for t in triggers) + "]"
        desc = (f"Use before calling {tool} in a context that previously failed "
                f"({marker['error_class']}). {marker['causal']}").replace("\n", " ")
        bullets = lambda xs: "\n".join(f"- {x}" for x in xs) or "- (none recorded)"
        tail = raw.strip().splitlines()[0][:200] if raw.strip() else ""
        success_criterion = (marker.get("success_criterion")
                             or f"Agent follows the recovery for {marker['error_class']} "
                                f"instead of repeating it")
        return (
            "---\n"
            f"name: {slug}\n"
            f"description: {json.dumps(desc)}\n"
            f"triggers: {trig_yaml}\n"
            f"success_criterion: {json.dumps(success_criterion)}\n"
            f"confidence: {DEFAULT_CONFIDENCE}\n"
            "---\n\n"
            f"# Failure lesson: {tool} — {marker['error_class']}\n\n"
            "Captured automatically from a recurring error (Cycle-to-Skill Pipeline, Path A, "
            "handle_exception). Check this before repeating the operation.\n\n"
            "## What happens\n"
            f"{marker['causal']}\n\n"
            f"Observed error: `{tail}`\n\n"
            "## Avoid\n"
            f"{bullets(marker['anti'])}\n\n"
            "## Do instead\n"
            f"{bullets(marker['do'])}\n"
        )

    def _note(self, sdir: str, tool: str, ec: str, first: bool = False) -> None:
        try:
            os.makedirs(sdir, exist_ok=True)
            line = (f"- {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} "
                    f"{'created from' if first else 'recurred:'} {tool}/{ec}\n")
            with open(os.path.join(sdir, ".memory.md"), "a", encoding="utf-8") as f:
                if first:
                    f.write(f"# Usage notes — {tool}/{ec}\n\n")
                f.write(line)
        except Exception:
            pass

    def _bump(self) -> None:
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
