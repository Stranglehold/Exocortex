# CYCLE-TO-SKILL PIPELINE — L3 Spec
## Author: Kestrel (spec) — from Opus's design direction + v16/v17 field research
## Date: 2026-05-30
## Status: SPEC — for review before implementation
## Builds on: _20_error_comprehension (tool_execute_after), _30_failure_tracker (error_format),
##            the skill system (/a0/usr/skills/), the idle cycle engine, cycle_close.py
## Source convergence: outside-in (Kestrel lessons-exchange + IDEA-003 meta-tools/OpenSpace
##   CAPTURED pattern) and inside-out (v16/v17, 878 cycles of `skills_captured: 0`).

---

## The Problem (one sentence)

The system is designed to turn cycles into skills — `program.md` Priority 3 is "Skill
Generation," `cycle_close.py` has a `--skills-captured` field — but across 878 cycles it
has captured **zero**. The loop from *operational experience → durable, reusable skill* is
severed. This spec reconnects it.

## What This Builds

Two capture paths over **one shared skill infrastructure**, built together so the skill
format serves both the failure path and the success path from day one:

- **Path A — Failure-Lesson Capture** (deterministic-first): a recurring failure becomes a
  discoverable "when X, avoid Y; do Z instead" skill. Every failure that becomes a skill is
  a failure that never silently recurs.
- **Path B — Field-Report → Methodology Skill** (LLM-assisted): the search→refine→synthesize
  sequence that produced a good field report becomes a reusable `research_topic()`-style
  methodology. Closes the EXPLORE → BUILD → SKILL loop.

Opus's build order (failure-lesson FIRST): failures are the highest-leverage first skill
type because the success path already produces knowledge (878 cycles of wiki/reports), but
nothing compounds from failure — each agent rediscovers the same bug, works around it, and
forgets. Field-report→skill is built second on the same registration/format/discovery rails.

---

## Architecture

```
  Tool failure                          Field report written (EXPLORE close)
       │                                          │
  ┌────▼─────────────────┐               ┌────────▼──────────────┐
  │ _20_error_comprehension│             │  Path B trigger         │
  │  → _error_diagnosis    │             │  (sleep/MAINTAIN hook)  │
  │  {error_class,         │             └────────┬──────────────┘
  │   causal_chain,        │                       │ (bounded utility-LLM:
  │   anti_actions,        │                       │  extract methodology)
  │   suggested_actions}   │                       │
  └────┬───────────────────┘                       │
       │ (Path A: DETERMINISTIC — lesson already   │
       │  built by error comprehension)            │
  ┌────▼───────────────────────────────────────────▼────┐
  │           SHARED SKILL INFRASTRUCTURE                │
  │  1. dedup check (signature already captured?)        │  ← deterministic
  │  2. skill writer → /a0/usr/skills/auto-generated/    │  ← deterministic
  │     {failure-lessons|methodologies}/{slug}/          │
  │       SKILL.md   (frontmatter: name + trigger desc)  │
  │       .memory.md (append-only usage notes — V17)     │
  │       tests/     (optional registration gate — later)│
  │  3. skills_captured++ → cycle_close                  │  ← deterministic
  └─────────────────────────────────────────────────────┘
       │
  Future cycles: A0's normal skill-description matching surfaces the skill
  BEFORE the agent reattempts the failing operation / re-reasons the methodology.
```

---

## Path A — Failure-Lesson Capture

### Trigger (deterministic)
New extension `tool_execute_after/_31_failure_lesson_capture.py`, ordered AFTER
`_20_error_comprehension` (which sets `_error_diagnosis`) and `_30_tool_fallback_logger`.

Fire when **both**:
1. `agent.get_data("_error_diagnosis")` is non-null (a classified failure occurred), AND
2. The failure is **capture-worthy**: either `_failure_tracker[tool] >= CAPTURE_THRESHOLD`
   (recurring) OR the `(error_class, tool)` signature has not been captured before (novel).
   Recurring-OR-novel both qualify; the dedup check (below) prevents duplicates.

### Lesson content (deterministic — already produced by `_20`)
The `_error_diagnosis` dict already contains the lesson:
- `error_class` → skill slug + category
- `causal_chain` → "## What happens"
- `anti_actions` → "## Avoid"
- `suggested_actions` → "## Do instead"
- `evidence` (matched pattern) + `tool_name` → the trigger description

No LLM call required for the body. The skill is assembled from the diagnosis via a template.

### Trigger description (deterministic template; optional LLM polish)
Default deterministic template:
> "Use when about to call `{tool}` in a context resembling: {error_class}. Past failure:
> {causal_chain summary}. Avoid {anti_action[0]}."
Optional (config-gated, OFF by default on cost-sensitive containers): a single bounded
utility-model call to rewrite the description for better discoverability. **Deterministic
path is the default and is sufficient** — keeps v17 (DeepSeek) cost at zero.

### Example output
A `text_editor:write` of 13,538 chars (the real MetaGate-SIZE block we saw) →
`auto-generated/failure-lessons/text_editor_oversized_write/SKILL.md`:
> description: "Use when writing file content with text_editor:write and content may exceed
> ~5000 chars. Oversized writes truncate in the JSON payload and fail."
> Avoid: retrying text_editor:write with the same oversized content.
> Do instead: use code_execution_tool with Python open()/write, or append-mode chunks.

### Implementation correction — the gate-raised capture point (2026-05-31)

The MetaGate-SIZE example above is exactly the case that revealed a gap in the
original single-hook design. Traced through A0 v1.18 core:

- **`_31` (tool_execute_after) only sees failures where the tool EXECUTED.** It fires
  after `tool.execute()` and reads `_20_error_comprehension`'s `_error_diagnosis`.
  MetaGate-SIZE is raised in **`tool_execute_before`** (`_20_meta_reasoning_gate.py:266`,
  a plain `ValueError`), which short-circuits `tool_execute_after` — so `_31` never sees
  gate-raised failures. `_31` remains correct for its path (executed-tool failures).
- **`error_format` is NOT a universal error hook.** It is invoked only from
  `_functions/agent/Agent/handle_exception/end/_50_handle_repairable_exception.py`, gated on
  `isinstance(exc, RepairableException)`. A plain `ValueError` fails that check and falls to
  `_90` (critical) — `error_format` is never called for it. (An earlier `error_format/_35`
  leg was built on the wrong assumption that error_format is universal; it is provably inert
  for gate-raises and has been **retired**.)
- **The genuinely universal error surface is `handle_exception/end`.** Every exception
  (intervention / repairable / critical) flows through the `_40`→`_50`→`_90` chain with
  `data["exception"]` set. New extension
  **`_functions/agent/Agent/handle_exception/end/_45_failure_lesson_capture.py`** runs at `_45`
  (before `_90` wraps the exception), reads `data["exception"]`, classifies it against the same
  deterministic marker map, and writes the same discoverable skill as `_31`. Captures gate-raised,
  repairable, and critical failures alike. Deterministic, zero LLM.

**Live-proven 2026-05-31** (v16): a real `ValueError("[MetaGate-SIZE] …")` driven through the
message loop fired `[SKILL-CAPTURE] … via handle_exception`, wrote a SKILL.md that passes A0's
own `validate_skill_md` (`[]` errors) and enumerates via `discover_skill_md_files`, and bumped
`skills_captured_pending → 1`. Corrected capture map: **`_31` = executed-tool failures · `_45` =
gate-raised + all-exception failures.**

---

## Path B — Field-Report → Methodology Skill

### Trigger (deterministic)
After an EXPLORE cycle writes a field report (detected at the existing
`monologue_end`/sleep boundary, or the BUILD-cycle "promote field report" step that
`program.md` already specifies but never executes). Debounced: at most
`MAX_METHODOLOGY_CAPTURES_PER_CYCLE` (default 1).

### Methodology extraction (bounded utility-LLM — inherently generative)
One bounded utility-model call: given the field report, extract the **procedure that
worked** (the specific search→refine→synthesize sequence, sources hit, dead-ends avoided)
as a verbose-procedural skill (per MUSE: agent skills are 2.2× longer than human ones and
*cheaper to run* because the length is procedure, not description). Output is the SKILL.md
body. This is NOT a deterministic layer — generative by nature; it uses the **utility
model**, is **capped at 1/cycle**, and is **config-gated** (can be disabled on v17 for cost).

### Per-skill `.memory.md` (V17's idea — the novel one)
Each methodology skill gets a sibling `.memory.md`: append-only annotated usage notes.
"SKILL.md says what it does; `.memory.md` says what the agent learned about using it" —
e.g., "works well for arXiv-heavy topics; returns nothing for news-only domains because
arxiv.search_papers is currently down (see failure-lesson)." This is the experience-
following property applied *productively* — the skill improves through annotation, not
retraining. Written by the agent (or appended deterministically when a failure-lesson
references the same tool the methodology uses).

---

## Shared Infrastructure (built once)

| Component | Determinism | Notes |
|---|---|---|
| Skill writer | deterministic | writes `auto-generated/{failure-lessons,methodologies}/{slug}/SKILL.md` (+`.memory.md`) following the existing `build-skill` SKILL.md standard (frontmatter: `name`, `description` with triggers) |
| Dedup / signature check | deterministic | before writing, hash `(error_class, tool)` for Path A or a content-signature for Path B against existing auto-generated skills; skip if present. **Prevents the 34-duplicate / 11-divergent mess from the start.** |
| `skills_captured` counter | deterministic | increment + pass real count to `cycle_close.py --skills-captured`. The journal finally reflects reality. |
| Discovery | existing | no change to how A0 loads/matches skills — the new skills are discovered by the normal description-trigger mechanism. |

---

## Deterministic vs LLM Boundary (explicit — project rule + v17 cost)

- **Deterministic (no LLM):** all triggers, dedup, registration, the entire failure-lesson
  skill body, `skills_captured` counting, discovery. **Path A is fully deterministic by
  default.**
- **Bounded utility-LLM (gated, capped, debounced):** Path B methodology extraction (1/cycle,
  utility model); optional Path A description polish (OFF by default).
- **v17/DeepSeek cost stance:** ship Path A first (zero LLM cost). Gate Path B's LLM behind
  a per-container flag (`methodology_capture_llm: false` on v17 until cost is acceptable).

---

## Configuration (explicit defaults)

```json
"cycle_to_skill": {
  "enabled": true,
  "failure_lesson_capture": true,
  "capture_threshold": 1,                 // failures before capture (1 = novel-on-first)
  "failure_description_llm_polish": false, // deterministic template by default
  "methodology_capture": true,
  "methodology_capture_llm": true,         // set false on cost-sensitive containers (v17)
  "max_methodology_captures_per_cycle": 1,
  "max_failure_captures_per_cycle": 3,
  "dedup_signature": "error_class+tool",   // Path A signature
  "skills_root": "/a0/usr/skills/auto-generated"
}
```
Graceful degradation: missing config section → all features default as above; any extension
error → pass-through (never breaks a cycle), per the stack's standard try/except pattern.

---

## Testing Criteria (specific assertions)

1. After a tool failure that sets `_error_diagnosis` with `error_class=X`, a skill exists at
   `auto-generated/failure-lessons/{slug}/SKILL.md` whose body contains the `anti_actions`
   text and whose frontmatter `description` names the tool.
2. A second identical failure does **not** create a second skill (dedup holds); it MAY append
   to the existing skill's `.memory.md`.
3. `skills_captured` in the cycle journal is **> 0** after a cycle that hit a novel failure
   (the literal fix for `skills_captured: 0`).
4. Path A runs with **zero LLM calls** (assert no utility/chat model invocation in the
   failure-capture path when `failure_description_llm_polish=false`).
5. With `methodology_capture_llm=false`, an EXPLORE cycle writes **no** methodology skill and
   makes **no** model call (v17-safe).
6. A captured failure-lesson skill is **discoverable**: a subsequent turn whose context
   matches the trigger surfaces the skill via the normal skill-matching path.
7. Extension error in `_31` → cycle completes normally (pass-through verified).

---

## What This Does NOT Do

- **No skill deprecation / lifecycle GC.** That is the next layer (apply sleep-consolidation
  dedup to the skill library). This spec only *adds* skills + prevents duplicates at write
  time; it does not retire stale ones.
- **No skill-execution / loading changes.** Skills are discovered by A0's existing mechanism;
  we do not touch how skills are injected or run.
- **No registration unit-test gate (yet).** The `tests/` dir is scaffolded in the format but
  the gate (skill enters bank only if test passes — V17 MUSE idea) is a follow-on.
- **No prompt/policy evolution (GEPA).** Separate, later layer.
- **No RL / co-evolution.** Out of scope.
- **Does not fire on every failure.** Debounced + capped per cycle; capture-worthy gate only.
- **No new skill taxonomy imposed on the agent.** Captured skills follow the existing
  `build-skill` SKILL.md standard so they're indistinguishable from hand-authored skills.

---

## Research Lineage

From v16/v17 field reports (exact arXiv IDs are in those reports;
`field-reports/20260527_muse-autoskill-self-learning.md`,
`20260526_automated-skill-extraction-agent-trajectories.md`,
`2026-05-27_self_improving_agent_skills_evolution.md`):
- **MUSE-Autoskill** — five-stage skill lifecycle; per-skill memory; unit-test-gated
  registration; verbose-procedural > terse (2.2× length, cheaper to run).
- **AutoRefine** — trajectory→skill distillation (teacher proposes, score, prune).
- **CoEvoSkills / Trace2Skill** — agents create better skills than humans; recursive
  skill/policy co-evolution; surrogate verifier without ground truth.
- **GEPA (arXiv 2507.19457)** — reflective prompt evolution (the later prompt-layer).
- **Mem0** — entity-linked memory retrieval without a graph DB (adjacent memory work).
- **Exocortex IDEA-003** (meta-tools) + OpenSpace CAPTURED pattern — the outside-in
  convergence (Papers-with-Code exploration).

---

## Build Sequence

1. **Shared infra** (skill writer + dedup + `skills_captured` wiring) — deterministic.
2. **Path A — failure-lesson capture** (`_31`, deterministic, zero LLM). Ship + validate on
   v16; safe on v17 (no cost). Watch `skills_captured` go > 0.
3. **Path B — methodology capture** (LLM-gated). Validate on v16 with LLM on; keep LLM off on
   v17 until cost-cleared.
4. **`.memory.md` annotation** wiring (both paths).
5. (Later layers, separate specs) registration test-gate · skill deprecation/GC · GEPA.

— Kestrel, from Opus's direction and the agents' own research
