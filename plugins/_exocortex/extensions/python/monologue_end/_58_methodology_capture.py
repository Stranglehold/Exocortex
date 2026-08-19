"""
Methodology Capture (monologue_end) — Cycle-to-Skill Pipeline, Path B
=====================================================================
Hook: monologue_end · Priority _58

Path A (_31/_45) turns recurring FAILURES into discoverable skills, deterministically.
Path B is its twin for SUCCESSES: when an EXPLORE cycle writes a field report, extract
the reusable RESEARCH METHODOLOGY — the search→refine→synthesize procedure that worked,
the sources that produced signal, the dead-ends to avoid — into a `research_topic()`-style
methodology skill. Closes the EXPLORE → BUILD → SKILL loop (spec: skills_captured was 0
across 878 cycles; the prompt asks the agent to self-capture but it doesn't reliably happen).

The FACTS belong in the wiki; the reusable PROCEDURE belongs in the skill.

Boundary (project rule + v17 cost): extraction is inherently generative, so it uses ONE
bounded UTILITY-model call, capped at 1 report/cycle, config-gated behind
`methodology_capture_llm` (set false on cost-sensitive containers like v17 → zero LLM cost,
extension becomes a no-op). Runs in a background DeferredTask so it never blocks the cycle.
Writes the same auto-generated/{slug}/SKILL.md + .memory.md rails as Path A (methodologies/
root). Pass-through on every error — never breaks a cycle.

Spec: specs/CYCLE_TO_SKILL_PIPELINE_SPEC_L3.md (Path B)
Log tag: [SKILL-CAPTURE]
"""

import json
import os
import re
import time

from agent import LoopData
from helpers.extension import Extension
from helpers.dirty_json import DirtyJson
from helpers.defer import DeferredTask, THREAD_BACKGROUND

# Portable across containers: v2 (_exocortex plugin) vs v16/v17 (/a0/usr/Exocortex).
# The field-report / skills / office paths are identical on all three.
_CONFIG_PATHS     = ("/a0/usr/plugins/_exocortex/config/config.json",
                     "/a0/usr/Exocortex/config.json")
FIELD_REPORTS_DIR = "/a0/usr/workdir/workspace/field-reports"
SKILLS_ROOT       = "/a0/usr/skills/auto-generated/methodologies"
PENDING_COUNT     = "/a0/usr/workdir/workspace/office/skills_captured_pending.json"
LAST_PROCESSED    = "/a0/usr/workdir/workspace/office/methodology_last_processed.json"

_DEFAULTS = {
    "enabled": True,
    "methodology_capture": True,
    "methodology_capture_llm": True,   # set false on cost-sensitive containers (v17)
    # backlog policy on the FIRST run (no marker yet):
    #   "skip"  -> adopt all existing reports as already-processed; capture forward-only (safe default)
    #   "drain" -> work through the existing backlog too, one report per cycle
    "methodology_backlog": "skip",
}
_MIN_REPORT_CHARS = 300     # skip thin reports
_MAX_REPORT_CHARS = 8000    # bound the utility-model input
_CAPTURE_HUNG_CAP = 600     # seconds; a capture in-flight longer than this is treated as dead
_INFLIGHT_ATTR = "_methodology_capture_inflight"   # agent attr: 0 or start-timestamp
DEFAULT_CONFIDENCE = "probable"

_SYSTEM = (
    "You extract a REUSABLE RESEARCH METHODOLOGY from an EXPLORE research field report — the "
    "transferable way of mapping this KIND of topic that a DIFFERENT agent on a DIFFERENT topic "
    "could follow.\n\n"
    "A field report documents FINDINGS. Do NOT restate them. Instead reconstruct the research "
    "APPROACH behind them as a move-sequence — for example: 'anchor on the flagship result or "
    "market signal → find the inspectable open-source counterpart → map the surrounding tooling "
    "as a separate layer → identify the cross-cutting problem → extrapolate the pattern.' "
    "Most substantive reports — INCLUDING topic surveys and framework landscapes — contain such "
    "a transferable approach, and whenever one is clearly present you SHOULD capture it. Judge "
    "the APPROACH, not the format: a findings-list or a survey is exactly what you extract the "
    "procedure FROM.\n\n"
    "Capture the transferable procedure, NOT the facts (facts belong in the wiki). Write it so "
    "a different agent could follow it on a different but similar topic.\n\n"
    "Only return {\"skip\": true} when the report genuinely offers NO reusable procedure — it is "
    "empty, an error dump, only a couple of sentences, or undifferentiated notes with no "
    "discernible research approach at all. A rich report with a clear method is NOT a skip, even "
    "if the method is a familiar survey pattern.\n\n"
    "When you extract, return ONLY a JSON object (no prose, no code fence) with these fields:\n"
    '{\n'
    '  "name": "short-kebab-slug for the methodology, e.g. research-arxiv-heavy-topic",\n'
    '  "description": "one sentence: when to reach for this methodology (used for skill matching)",\n'
    '  "triggers": ["3-6 short phrases a matcher would see when this applies"],\n'
    '  "when_to_use": "1-2 sentences on the class of topic/task this fits",\n'
    '  "procedure": ["ordered, concrete, transferable steps — the reusable move-sequence, generalized past this topic\'s specifics"],\n'
    '  "sources": ["kinds of sources/tools that produced signal, e.g. web_search for the flagship result, arxiv for the open-source prover, GitHub for tooling"],\n'
    '  "pitfalls": ["dead-ends / traps to avoid next time; [] if none evident"]\n'
    '}'
)


def _cfg() -> dict:
    for p in _CONFIG_PATHS:
        try:
            if not os.path.exists(p):
                continue
            with open(p, encoding="utf-8") as fh:
                c = json.load(fh).get("cycle_to_skill", {})
            return {**_DEFAULTS, **(c if isinstance(c, dict) else {})}
        except Exception:
            continue
    return dict(_DEFAULTS)


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").strip().lower()).strip("-")[:60]


class MethodologyCapture(Extension):
    """monologue_end: turn an EXPLORE field report into a reusable methodology skill."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        try:
            cfg = _cfg()
            if not cfg["enabled"] or not cfg["methodology_capture"]:
                return
            if not cfg.get("methodology_capture_llm", True):
                return  # LLM gated off (v17) → no-op, zero cost

            # Single-in-flight guard: never run two captures at once (avoids background
            # util-model calls stacking → GPU contention). Self-heals if a prior capture
            # died without clearing (stale beyond the hung cap).
            inflight = getattr(self.agent, _INFLIGHT_ATTR, 0) or 0
            if inflight and (time.time() - float(inflight)) < _CAPTURE_HUNG_CAP:
                return

            # First-run backlog policy: with no marker yet, "skip" adopts every existing
            # report as already-processed (capture forward-only); "drain" works the backlog.
            if not os.path.exists(LAST_PROCESSED):
                if str(cfg.get("methodology_backlog", "skip")).lower() != "drain":
                    self._seed_marker_skip_backlog()
                    return

            sel = self._next_report()
            if not sel:
                return
            path, content, mtime = sel

            if len(content.strip()) < _MIN_REPORT_CHARS:
                self._mark_processed(path, mtime)   # thin report: definitive skip, advance
                return
            slug = _slug(os.path.splitext(os.path.basename(path))[0])
            if os.path.exists(os.path.join(SKILLS_ROOT, slug, "SKILL.md")):
                self._mark_processed(path, mtime)   # already captured: advance marker
                return

            setattr(self.agent, _INFLIGHT_ATTR, time.time())
            task = DeferredTask(thread_name=THREAD_BACKGROUND)
            task.start_task(self._capture, path, content[:_MAX_REPORT_CHARS], slug, mtime)
            return task
        except Exception as e:
            print(f"[SKILL-CAPTURE] methodology execute error (passthrough): {e}", flush=True)

    async def _capture(self, path: str, content: str, slug: str, mtime: float, **kwargs):
        try:
            resp = await self.agent.call_utility_model(
                system=_SYSTEM,
                message=f"FIELD REPORT ({os.path.basename(path)}):\n\n{content}",
                background=True,
            )
            wrote = False
            d = None
            if resp and isinstance(resp, str) and resp.strip():
                try:
                    d = DirtyJson.parse_string(resp.strip())
                except Exception:
                    d = None
            if isinstance(d, dict) and not d.get("skip"):
                procedure = [str(s).strip() for s in (d.get("procedure") or []) if str(s).strip()]
                if procedure:
                    sdir = os.path.join(SKILLS_ROOT, slug)
                    os.makedirs(sdir, exist_ok=True)
                    with open(os.path.join(sdir, "SKILL.md"), "w", encoding="utf-8") as f:
                        f.write(self._render(slug, d, path, procedure))
                    self._note(sdir, slug, path)
                    self._bump()
                    wrote = True

            # Completed a full attempt (success / skip / empty / bad-json) → mark processed so
            # we don't re-attempt the same report. Only a hard exception below skips the mark.
            self._mark_processed(path, mtime)
            if wrote:
                print(f"[SKILL-CAPTURE] methodology written: {slug} "
                      f"(from {os.path.basename(path)})", flush=True)
            else:
                print(f"[SKILL-CAPTURE] methodology declined (skip/thin): "
                      f"{os.path.basename(path)}", flush=True)
        except Exception as e:
            # Transient (model unreachable / infra) — do NOT mark; retried next cycle.
            print(f"[SKILL-CAPTURE] methodology capture error (will retry): {e}", flush=True)
        finally:
            try:
                setattr(self.agent, _INFLIGHT_ATTR, 0)
            except Exception:
                pass

    # ── report selection (FIFO: oldest unprocessed, 1/cycle, none skipped) ────────
    def _next_report(self):
        try:
            last = 0.0
            if os.path.exists(LAST_PROCESSED):
                try:
                    with open(LAST_PROCESSED, encoding="utf-8") as f:
                        last = float(json.load(f).get("mtime", 0) or 0)
                except Exception:
                    last = 0.0
            if not os.path.isdir(FIELD_REPORTS_DIR):
                return None
            cands = []
            for fn in os.listdir(FIELD_REPORTS_DIR):
                if not fn.lower().endswith(".md"):
                    continue
                p = os.path.join(FIELD_REPORTS_DIR, fn)
                try:
                    mt = os.path.getmtime(p)
                except Exception:
                    continue
                if mt > last:
                    cands.append((mt, p))
            if not cands:
                return None
            cands.sort()  # oldest-first
            mt, p = cands[0]
            with open(p, encoding="utf-8", errors="replace") as f:
                return p, f.read(), mt
        except Exception:
            return None

    def _mark_processed(self, path: str, mtime: float) -> None:
        try:
            os.makedirs(os.path.dirname(LAST_PROCESSED), exist_ok=True)
            tmp = LAST_PROCESSED + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"mtime": float(mtime), "name": os.path.basename(path)}, f)
            os.replace(tmp, LAST_PROCESSED)
        except Exception:
            pass

    def _seed_marker_skip_backlog(self) -> None:
        """First-run 'skip' policy: adopt every existing report as already-processed by
        seeding the marker to the newest report's mtime. Capture then runs forward-only."""
        try:
            newest = 0.0
            newest_name = "(backlog-seed)"
            if os.path.isdir(FIELD_REPORTS_DIR):
                for fn in os.listdir(FIELD_REPORTS_DIR):
                    if not fn.lower().endswith(".md"):
                        continue
                    try:
                        mt = os.path.getmtime(os.path.join(FIELD_REPORTS_DIR, fn))
                    except Exception:
                        continue
                    if mt > newest:
                        newest, newest_name = mt, fn
            os.makedirs(os.path.dirname(LAST_PROCESSED), exist_ok=True)
            tmp = LAST_PROCESSED + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"mtime": float(newest), "name": newest_name, "seeded": True}, f)
            os.replace(tmp, LAST_PROCESSED)
            print(f"[SKILL-CAPTURE] methodology backlog adopted (forward-only); "
                  f"marker seeded to {newest_name}", flush=True)
        except Exception:
            pass

    # ── skill rendering (verbose-procedural; MUSE: length is the procedure) ────────
    def _render(self, slug: str, d: dict, src: str, procedure: list) -> str:
        name = str(d.get("name") or slug)[:80]
        desc = re.sub(r"\s+", " ", str(d.get("description")
                      or f"Reusable research methodology: {slug}")).strip()[:280]
        triggers = [str(t)[:60] for t in (d.get("triggers") or []) if str(t).strip()][:8] or [slug]
        trig_yaml = "[" + ", ".join(json.dumps(t) for t in triggers) + "]"
        when = str(d.get("when_to_use") or "").strip() or desc
        sources = [str(s).strip() for s in (d.get("sources") or []) if str(s).strip()]
        pitfalls = [str(s).strip() for s in (d.get("pitfalls") or []) if str(s).strip()]
        steps = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(procedure))
        src_b = "\n".join(f"- {s}" for s in sources) or "- (none noted)"
        pit_b = "\n".join(f"- {s}" for s in pitfalls) or "- (none noted)"
        success = f"Agent follows this procedure when researching a topic matching: {desc}"
        return (
            "---\n"
            f"name: {slug}\n"
            f"description: {json.dumps(desc)}\n"
            f"triggers: {trig_yaml}\n"
            f"success_criterion: {json.dumps(success)}\n"
            f"confidence: {DEFAULT_CONFIDENCE}\n"
            "source: methodology-auto-captured\n"
            "---\n\n"
            f"# Methodology: {name}\n\n"
            f"Auto-captured from the research procedure in `{os.path.basename(src)}` "
            "(Cycle-to-Skill Pipeline, Path B). Reuse when researching a similar topic — "
            "this is the *procedure that worked*, not the findings.\n\n"
            f"## When to use\n{when}\n\n"
            f"## Procedure\n{steps}\n\n"
            f"## Sources that produced signal\n{src_b}\n\n"
            f"## Pitfalls / dead-ends\n{pit_b}\n"
        )

    def _note(self, sdir: str, slug: str, src: str) -> None:
        try:
            os.makedirs(sdir, exist_ok=True)
            first = not os.path.exists(os.path.join(sdir, ".memory.md"))
            with open(os.path.join(sdir, ".memory.md"), "a", encoding="utf-8") as f:
                if first:
                    f.write(f"# Usage notes — methodology {slug}\n\n")
                f.write(f"- {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} "
                        f"captured from {os.path.basename(src)}\n")
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
