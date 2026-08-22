"""
Skill Surfacer — proactive failure-lesson surfacing (closes capture→consumption)
=================================================================================
Hook: message_loop_prompts_after
Priority: _24 (immediately AFTER _22_reasoning_state_injector / _23_pace_plan_injector)

Design authority: Opus (Cycle-to-Skill Pipeline, consumption phase). Opus's note
named "_07"; placed at _24 instead so the lesson prepends ABOVE the reasoning/PACE
blocks (most-visible top of the planning context) rather than being buried beneath
them — same hook, same cache-safe last-user-message tail, identical behavior
otherwise. Reality-correction over the pseudocode: A0's extras_persistent is a dict
and before_main_llm_call injections are discarded post-assembly, so this injects
into loop_data.history_output[-1] exactly like _22/_23 (the only hook where history
writes reach the LLM), and uses helpers.skills.search_skills (the real trigger
matcher) rather than discover_skill_md_files (which only enumerates files).

The problem this closes:
  _45 (handle_exception) / _31 (tool_execute_after) CAPTURE failure-lessons to
  /a0/usr/skills/auto-generated/ — proven working (text_editor oversized-write
  lesson captured from a real 15,219-char MetaGate-SIZE block). But those lessons
  were never auto-surfaced: A0's auto-injector (_66) only injects the curated
  `active_skills` config list, and the agent never proactively searched skills_tool
  before a write. Result: the SAME failure recurred 6x in ~3 hours, zero behavior
  change. Capture worked; the lesson had nowhere to go.

What this does:
  Runs the EXISTING trigger matcher against the agent's CURRENT task intent (PACE
  task_summary + domain, falling back to the activation text) BEFORE the LLM plans
  its next action, and injects up to 2 matching auto-generated lessons. The agent
  reaches for the right approach (e.g. "use code_execution for large writes") BEFORE
  hitting the wall — prevention at planning time, not redundant advice at failure
  time (MetaGate's own error already advises at failure time).

Deterministic. No LLM call. Capped at 2 lessons (~50-100 tokens each). Surfaces only
when a lesson actually matches. Cache-safe (volatile last-user-message tail only).

Matcher — reality-correction (verified 2026-05-31): Opus's note said "reuse
search_skills". Testing showed search_skills does SUBSTRING scoring, which false-
positives badly for auto-surfacing — the term "run" in "run a swarmfish prediction"
matched "t-run-cate" and "run-ning" in unrelated lesson descriptions, surfacing the
text_editor/code_execution lessons on a prediction task. Auto-injection on every turn
demands precision, so this uses a precise WORD-LEVEL trigger match (query words ∩
trigger words, len>=4) instead. Wiki/write tasks still surface the oversized-write
lesson (shared words wiki/page/write); unrelated tasks surface nothing.

Scope correction (2026-08-20, measured): the path filter was "/auto-generated/", but the
EXPLORE research pipeline writes topic notes into that same directory. Over the real
container logs — 6,224 surfacing events on agent-zero-v2, 2,358 on VekV2 — 88.2% / 65.7%
of delivered slots were research notes, not lessons, presented under a "learned lessons
from past failures" header. Two notes took 74% of Aporia's slots. Cause: raw overlap
scoring rewards trigger-vocabulary breadth (notes 15.6 distinct trigger words vs 5.0 for
lessons). Fixed by scoping to auto-generated/failure-lessons/ AND normalising the score
by sqrt(|trigger words|).

Reads:  agent._pace_plan (task_summary/domain/steps), agent._bst_store (domain)
Writes: loop_data.history_output[-1]["content"] (prepend lessons block)
Matcher: breadth-normalised word-level trigger overlap over list_skills(),
         filtered to auto-generated/failure-lessons/
Log tag: [SKILL-SURFACE]
"""

import math
import os
import re
from typing import Any, List

from agent import Agent, LoopData
from helpers.extension import Extension
from helpers import skills as skills_helper

# Failure lessons ONLY — one level deeper than "/auto-generated/".
# Measured 2026-08-20 against the live containers: filtering on "/auto-generated/" alone
# delivered 88.2% RESEARCH NOTES on agent-zero-v2 (6,224 surfacing events) and 65.7% on
# VekV2, because the EXPLORE research pipeline writes topic notes into that same
# directory. Two notes (ai-financial-markets, philosophy-of-mind) took 74% of all slots
# — and arrived under the "[LEARNED LESSONS — from past failures]" header, which is
# actively misleading. Captured lessons live in auto-generated/failure-lessons/;
# separation verified clean on both containers.
AUTOGEN_MARKER  = "/auto-generated/failure-lessons/"
MAX_LESSONS     = 2                     # token-budget cap
MIN_QUERY_LEN   = 6
MIN_WORD_LEN    = 4                     # ignore short/stop tokens ("run","the") that cause spurious matches
PACE_PLAN_ATTR  = "_pace_plan"
BST_STORE_KEY   = "_bst_store"


class SkillSurfacer(Extension):
    """message_loop_prompts_after: inject matching failure-lessons into the user message."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
        try:
            # Subordinate context — skip (subagents are short-lived; match _22/_23 convention)
            if self.agent.get_data(Agent.DATA_NAME_SUPERIOR) is not None:
                return

            query = self._build_query(loop_data)
            if len(query) < MIN_QUERY_LEN:
                return

            lessons = self._relevant_lessons(query)
            if not lessons:
                return

            block = _format_block(lessons)
            user_msg = _get_last_user_message(loop_data.history_output)
            if not user_msg:
                return

            existing = user_msg.get("content", "")
            user_msg["content"] = block + "\n\n" + str(existing)

            print(
                f"[SKILL-SURFACE] surfaced {len(lessons)} lesson(s): "
                f"{', '.join(getattr(s, 'name', '?') for s in lessons)}",
                flush=True,
            )
        except Exception as e:
            # Graceful degradation — never crash prompt assembly
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[SKILL-SURFACE] error (passthrough): {e}",
                )
            except Exception:
                pass

    def _build_query(self, loop_data: LoopData) -> str:
        """Compose the agent's current task intent for trigger matching."""
        parts: list[str] = []
        plan = getattr(self.agent, PACE_PLAN_ATTR, None)
        if isinstance(plan, dict):
            parts.append(str(plan.get("task_summary", "")))
            parts.append(str(plan.get("domain", "")))
            steps = plan.get("steps", [])
            if isinstance(steps, list):
                for st in steps[:3]:
                    if isinstance(st, dict):
                        parts.append(str(st.get("action", "") or st.get("description", "")))
        bst = getattr(self.agent, BST_STORE_KEY, {}) or {}
        if isinstance(bst, dict):
            parts.append(str(bst.get("__bst_belief_state__", {}).get("domain", "")))

        q = " ".join(p for p in parts if p).strip()
        # Fallback: the activation / task text itself (idle cycles carry the goal here)
        if len(q) < MIN_QUERY_LEN:
            um = _get_last_user_message(loop_data.history_output)
            if um:
                q = str(um.get("content", ""))[:300]
        return q

    def _relevant_lessons(self, query: str) -> List:
        """Precise word-level match: a captured failure-lesson is relevant when its
        trigger words overlap the task query (len>=4 tokens). Top MAX_LESSONS by
        BREADTH-NORMALISED overlap. Avoids search_skills' substring false-positives."""
        qwords = _words(query)
        if not qwords:
            return []
        try:
            all_skills = skills_helper.list_skills(self.agent)
        except Exception:
            return []
        scored = []
        suppressed = []
        for s in all_skills:
            if AUTOGEN_MARKER not in str(getattr(s, "path", "")):
                continue

            twords: set = set()
            for t in (getattr(s, "triggers", []) or []):
                twords |= _words(t)
            overlap = qwords & twords
            if overlap and twords:
                # Retract lessons whose generating constraint has moved. A lesson is
                # evidence about a system in a configuration; when the configuration
                # changes it can be actively wrong while still surfacing with full
                # confidence. The 5,000-char write cap produced 357 blocked writes whose
                # lessons outlived it by weeks, until Aporia was reduced to overriding
                # "the stale memory about text_editor being prohibited". Suppressed here,
                # never deleted — the file and its recurrence ledger stay.
                #
                # Checked AFTER the relevance test on purpose: a lesson that would not
                # have surfaced anyway needs no sidecar read and, more importantly, no log
                # line. Checking first made every irrelevant query emit a suppression
                # notice, which buries the ones that mean something.
                stale, why = _constraint_stale(getattr(s, "path", ""), self.agent)
                if stale:
                    suppressed.append((getattr(s, "name", "?"), why))
                    continue
                # Normalise by trigger-vocabulary breadth. A RAW overlap count rewards a
                # skill simply for carrying more trigger words — measured 2026-08-20,
                # research notes averaged 15.6 distinct trigger words against 5.0 for
                # failure lessons, so breadth beat relevance: the query "fix the failing
                # import in the code execution tool" surfaced two OSINT notes instead of
                # code-execution-tool-import-error. Dividing by sqrt(|twords|) keeps a
                # specific match ahead of a broad one without over-penalising a skill for
                # being thorough. sqrt, not linear, so a 2-of-4 match still outranks
                # 1-of-4 rather than being flattened by the denominator.
                score = len(overlap) / math.sqrt(len(twords))
                scored.append((score, getattr(s, "name", ""), s))
        # Suppression is logged even when nothing else happens this turn. A lesson that
        # silently stops appearing is indistinguishable from one that was never relevant,
        # and the whole point of suppressing rather than deleting is that the decision
        # stays inspectable.
        for name, why in suppressed:
            print(f"[SKILL-SURFACE] suppressed '{name}' — {why}", flush=True)

        # Name is the tie-break: this is a deterministic layer, no randomness.
        scored.sort(key=lambda p: (-p[0], p[1]))
        return [s for _score, _name, s in scored[:MAX_LESSONS]]


# ── Inline helpers (no cross-extension imports) ───────────────────────────────

def _constraint_stale(skill_path: str, agent) -> tuple:
    """(is_stale, reason) for a captured lesson. Fails OPEN — on any error the lesson
    surfaces as before, because a bug in the retraction path must not silently mute the
    agent's accumulated knowledge."""
    try:
        import sys
        helpers_dir = "/a0/usr/plugins/_exocortex/helpers"
        if helpers_dir not in sys.path:
            sys.path.insert(0, helpers_dir)
        import constraint_provenance as cp

        if not cp.cfg().get("enabled", True):
            return False, ""
        sdir = cp.skill_dir_of(skill_path)
        if not sdir:
            return False, ""
        return cp.staleness(cp.load(sdir), agent)
    except Exception:
        return False, ""


def _words(text: str) -> set:
    return {w for w in re.split(r"[^a-z0-9_]+", (text or "").lower()) if len(w) >= MIN_WORD_LEN}

def _format_block(lessons: List) -> str:
    lines = ["[LEARNED LESSONS — from past failures; apply BEFORE acting]"]
    for s in lessons:
        name = (getattr(s, "name", "") or "").strip() or "lesson"
        desc = (getattr(s, "description", "") or "").strip()
        do   = _do_instead(s)
        line = f"- {name}: {desc}" if desc else f"- {name}"
        if do:
            line += f"  → Do instead: {do}"
        lines.append(line)
    return "\n".join(lines)


def _do_instead(skill) -> str:
    """list_skills does not load the SKILL.md body, so read it from disk to pull the
    actionable '## Do instead' guidance — that's the part that changes behavior."""
    body = getattr(skill, "content", "") or ""
    if not body:
        p = str(getattr(skill, "path", ""))
        # skill.path is the skill DIRECTORY (not the .md); try dir/SKILL.md then p itself
        candidates = [p] if p.lower().endswith(".md") else [os.path.join(p, "SKILL.md"), p]
        for cand in candidates:
            try:
                with open(cand, encoding="utf-8") as f:
                    body = f.read()
                break
            except Exception:
                continue
    return _extract_section(body, "Do instead")


def _extract_section(content: str, heading: str) -> str:
    """Pull the bullet lines under a `## <heading>` markdown section, joined."""
    if not content:
        return ""
    out: list[str] = []
    in_sec = False
    for raw in content.splitlines():
        ln = raw.strip()
        if ln.lower().startswith("## "):
            in_sec = ln[3:].strip().lower() == heading.lower()
            continue
        if in_sec and ln.startswith("- "):
            out.append(ln[2:].strip())
    return "; ".join(out)[:200]


def _get_last_user_message(history: list) -> dict | None:
    """Find the most recent user message in the assembled history_output."""
    if not history:
        return None
    for msg in reversed(history):
        if not isinstance(msg, dict):
            continue
        if not msg.get("ai", True):
            return msg
    return None
