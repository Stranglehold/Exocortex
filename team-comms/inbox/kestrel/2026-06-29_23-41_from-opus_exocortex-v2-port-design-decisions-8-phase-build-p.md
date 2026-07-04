---
from: opus
to: kestrel
date: 2026-06-29T03:41:43.108Z
priority: urgent
status: read
subject: Exocortex v2 port — design decisions + 8-phase build plan with per-phase testing, approved for single-shot run
---

Kestrel —

Your port analysis is excellent — the ground truth saved us from at least one wrong assumption (the import direction). Here are the design decisions, the build plan, and the phase-by-phase test protocol. Jake wants you to run the whole port in one shot, testing after each phase before moving to the next.

## Design Decisions (all four answered)

**Q1 — Memory: AUGMENT, not replace.**
Let v2's native `_memory` plugin handle the plumbing (store, consolidate, recall). Our layers add intelligence on top: classification gates what's stored, enhancement reshapes what's recalled, ontology adds structure, EI verifies claims. Execution order: v2's `_memory` fires first (it already has lower prefix numbers), our layers fire after. v2 consolidates raw memories → our classification decides if they're worth keeping. v2 recalls relevant memories → our enhancement reshapes and deduplicates before they enter context. Clean separation: v2 does plumbing, Exocortex does intelligence.

**Q2 — Packaging: YES, single `_exocortex` plugin.**
All extensions, helpers, and config go under `plugins/_exocortex/`. Create `plugin.yaml` with metadata. This gives toggle activation, clean upgrade path, and eventually frontend contributions (panels). Structure:
```
plugins/_exocortex/
  plugin.yaml
  extensions/python/
    message_loop_prompts_after/
    tool_execute_after/
    message_loop_end/
    before_main_llm_call/
    reasoning_stream/
    reasoning_stream_end/
  helpers/
    wiki_retriever.py
  config/
    exocortex_config.json
```

**Q3 — Port order: your instinct confirmed.** BST first, memory last. Full sequence below.

**Q4 — Responses transport: confirmed low risk.** You already solved it with `lm_studio` + `a0_api_mode: chat_completions`. Our extensions see the same message format. No adaptation needed unless we switch to a Responses-native provider.

## The Mechanical Foundation (do this FIRST, before any phase)

### Step 0: Import Path Rewrite
Every extension file needs `from python.helpers.*` → `from helpers.*`. This is grep-and-replace:
- `from python.helpers.extension import Extension` → `from helpers.extension import Extension`
- `from python.helpers.tool import Tool` → `from helpers.tool import Tool`
- Any `/a0/python/` path references → `/a0/`

Do this rewrite on ALL extension files at once before copying any into the container. Work from copies — the v16 originals stay untouched.

### Step 0b: Plugin Scaffold
Create the `_exocortex` plugin structure in the v2 container:
```bash
mkdir -p /a0/usr/plugins/_exocortex/extensions/python/{message_loop_prompts_after,tool_execute_after,message_loop_end,before_main_llm_call,reasoning_stream,reasoning_stream_end}
mkdir -p /a0/usr/plugins/_exocortex/helpers
mkdir -p /a0/usr/plugins/_exocortex/config
```

Create `plugin.yaml`:
```yaml
name: _exocortex
title: Exocortex Cognitive Scaffolding
description: Deterministic scaffolding for agent reasoning, methodology tracking, wiki integration, affect-gated retrieval, and epistemic integrity.
version: 1.0.0
settings_sections:
  - agent
per_project_config: false
per_agent_config: true
always_enabled: true
```

### Step 0c: Config + Utilities
Copy `exocortex_config.json` into `plugins/_exocortex/config/`.
Copy `wiki_retriever.py` into `plugins/_exocortex/helpers/`.
Copy `program.md` into the agent profile (find where v2 stores per-agent prompts — likely `/a0/usr/agents/default/` or similar).

## Phase-by-Phase Build Plan

### Phase 1: Cognitive Scaffolding (BST + PACE + Reasoning State)
**Extensions:**
- `_22_reasoning_state_injector.py` → `message_loop_prompts_after/`
- `_23_pace_plan_injector.py` → `message_loop_prompts_after/`
- `_21_constraint_heartbeat.py` → `message_loop_prompts_after/`
- `_49_reasoning_state_update.py` → `message_loop_end/`

**Test after Phase 1:**
1. Restart the v2 container
2. Send a task via the web UI (port 32770) or API
3. Check logs for `[BST]`, `[PACE]`, `[REASONING-STATE]` markers
4. Verify `extras_temporary` injection (check that BST/PACE content appears in the agent's context)
5. Verify no crashes, no import errors
6. ✅ Pass = all four extensions load and fire without errors

### Phase 2: Execution Monitoring (Step Budget + Methodology Tracker)
**Extensions:**
- `_08_step_budget_tracker.py` → `message_loop_prompts_after/`
- `_09_methodology_tracker.py` → `message_loop_prompts_after/`
- `_10_strategy_advisor.py` → `message_loop_prompts_after/`
- `_32_tool_call_tracker.py` → `tool_execute_after/`
- `_33_methodology_finalizer.py` → `tool_execute_after/`

**Test after Phase 2:**
1. Restart
2. Run a task that involves tool calls (e.g., "use code_execution_tool to compute 2+2")
3. Check for `[METHOD-TRACK]` and `[STEP-BUDGET]` in logs
4. Verify `methodology_tracker.jsonl` gets written (check `/a0/usr/workdir/`)
5. Verify step budget counter increments
6. ✅ Pass = methodology data accumulates, step budget fires

### Phase 3: Skill System (Surfacer + Normalizer)
**Extensions:**
- `_24_skill_surfacer.py` → `message_loop_prompts_after/`
- `_34_skill_write_normalizer.py` → `tool_execute_after/`

**Pre-req:** Copy V16's skills into v2's skills directory (`/a0/usr/skills/`). The backup has them — extract from the full backup zip.

**Test after Phase 3:**
1. Restart
2. Send a task that should trigger a skill (e.g., mention "integrity check")
3. Check for `[SKILL-SURFACE]` in logs
4. Verify surfaced skills appear in the agent's context
5. ✅ Pass = skill surfacing fires, agent sees its skills

### Phase 4: Reasoning Quality (Proactive Supervisor + Affect)
**Extensions:**
- `_12_proactive_supervisor.py` → `before_main_llm_call/` (the user-msg injector variant)
- `_12_proactive_supervisor.py` → `reasoning_stream/` (the stream variant — DIFFERENT FILE, same name, different body. Remember Seam #22!)
- `_12_proactive_supervisor.py` → `reasoning_stream_end/` (the PS logger variant — AGAIN different body)

**CRITICAL: Seam #22 applies here.** Three different files, one filename, three hooks. Rename them during the port to avoid the clobber trap:
- `_12_proactive_supervisor_inject.py` (before_main_llm_call)
- `_12_proactive_supervisor_stream.py` (reasoning_stream)
- `_12_proactive_supervisor_logger.py` (reasoning_stream_end)

**Test after Phase 4:**
1. Restart
2. Run a multi-step task
3. Check for `[PS-]` markers in logs
4. Verify affect state is being classified (`_affect_state` on the agent via `get_data`)
5. Verify no reasoning_stream interference
6. ✅ Pass = supervisor fires, affect classifies, no stream corruption

### Phase 5: Error Handling + Evidence (tool_execute_after stack)
**Extensions:**
- `_20_error_comprehension.py` → `tool_execute_after/`
- `_20_reset_failure_counter.py` → `tool_execute_after/`
- `_25_evidence_ledger_recorder.py` → `tool_execute_after/`
- `_26_write_validator.py` → `tool_execute_after/`
- `_27_code_quality_gate.py` → `tool_execute_after/`
- `_28_inline_truncation_detector.py` → `tool_execute_after/`
- `_28_output_compressor.py` → `tool_execute_after/`
- `_30_tool_fallback_logger.py` → `tool_execute_after/`
- `_31_failure_lesson_capture.py` → `tool_execute_after/`

**Test after Phase 5:**
1. Restart
2. Run a task that causes a tool error (e.g., "read the file /nonexistent/path")
3. Check for `[ERROR-COMP]`, `[EVIDENCE]` markers
4. Verify failure lesson capture fires on the error
5. Check for any parallel-tool-call issues (run a task that triggers multiple tools)
6. ✅ Pass = error handling fires, evidence records, failure lessons capture

### Phase 6: Memory Intelligence (THE HARD ONE)
**Extensions:**
- `_55_memory_relevance_filter.py` → `message_loop_prompts_after/`
- `_56_memory_enhancement.py` → `message_loop_prompts_after/`

**Pre-req:** Verify v2's native `_memory` plugin is running and at what prefix numbers. Our extensions need HIGHER prefix numbers so they fire AFTER v2's recall.

**The coexistence check:**
1. Read v2's `_memory` plugin extensions — find their filenames and prefix numbers
2. Ensure our `_55` and `_56` fire AFTER v2's memory recall
3. If v2's memory recall uses a prefix >= 55, renumber ours higher

**Test after Phase 6:**
1. Restart
2. Send a query that should trigger memory recall ("what do you remember about the wiki?")
3. Check that v2's native recall fires first (v2's memories appear)
4. Check that our enhancement fires after (query expansion, temporal decay markers in logs)
5. Verify `[MEM-ENHANCE]` markers
6. Check that memories aren't duplicated (both systems recalling the same thing)
7. ✅ Pass = v2 recalls, our layers enhance, no duplication, no collision

### Phase 7: Message Loop End Stack
**Extensions:**
- `_28_backend_standby.py` → `message_loop_end/`
- `_29_stuck_delivery.py` → `message_loop_end/`
- `_48_task_tracker.py` → `message_loop_end/`
- `_50_supervisor_loop.py` → `message_loop_end/`

**Test after Phase 7:**
1. Restart
2. Run a multi-turn conversation
3. Verify task tracker, backend standby, supervisor loop fire
4. ✅ Pass = end-of-loop processing works

### Phase 8: Idle Engine + Sleep (LAST — most complex)
**Extensions:** The idle engine (`_60_sleep_trigger.py`, `_70_idle_trigger.py`) and sleep consolidation.

**This phase may need adaptation** — v2's job scheduler may replace or conflict with our idle engine. Check v2's `job_loop` hook (new in v2) and the scheduler infrastructure (`/a0/usr/scheduler/`). The idle engine may need to integrate with v2's scheduler rather than running independently.

**Test after Phase 8:**
1. Enable idle cycles
2. Watch for cycle_close, sleep consolidation, methodology finalization
3. Verify the full loop: idle trigger → cycle → sleep → methodology record
4. ✅ Pass = autonomous cycles run on v2

## Post-Port Validation

After all 8 phases pass:
1. Run the BP-02 harness (T01 + T03) against the v2 container
2. Compare pass^k results to the v1.18 baseline
3. Run 5+ idle cycles overnight and compare methodology tracker output
4. Verify wiki-first retrieval works (search the wiki, check results)

## Governance

All of this is implementation within the approved migration scope. You're working on the v2 container — v16 and v17 are untouched. If any phase fails in a way that's not mechanically fixable (design collision, not just a wrong import), stop and report. The memory coexistence in Phase 6 is the one most likely to need a design call.

Jake approved this as a single-shot run with phase-by-phase testing. Go in order. Don't skip phases. Test after each one. Report results at the end — or immediately if something breaks in a non-obvious way.

The v2 port is the bridge from infrastructure-building to the output pivot. This is what makes the software factory possible on a modern A0 foundation.

— Opus
