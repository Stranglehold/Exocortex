# IDLE-TIME ENGINE — Design Note
## Author: Opus
## Date: 2026-05-07
## Status: PROPOSED — awaiting Jake approval
## Dependencies: DEC-028 (subordinate profiles), curated Tier 1-4 stack, program.md v1.1

---

## Problem Statement

The Exocortex self-improvement loop (program.md) produces measurable value: 58 wiki pages in Run 3, memory saves closing the FAISS recall loop, research findings documented. But it requires manual activation — Jake pastes a launch prompt, the agent runs until context fills (~15-20 turns), then stops. Jake has to restart with a new launch prompt referencing checkpoints.

This is operationally expensive and leaves the agent idle between sessions. The 3090 sits powered on, the container runs, but the agent does nothing unless Jake initiates.

The idle-time engine turns dead time into compound improvement.

---

## Design Philosophy

Three principles from the cross-ecosystem research (AGENTIC_SUPERVISOR_ARCHITECTURE_RESEARCH.md):

1. **Cheapest first.** Idle-time activities should start with zero-model-call operations (deterministic consolidation, file organization, index maintenance) before escalating to model-intensive work (wiki writing, research synthesis). This mirrors Claude Code's 5-layer compaction pipeline.

2. **Information density over volume.** Each idle cycle should produce a small amount of high-quality output rather than a large volume of shallow work. GenericAgent's finding: effective context is ~10x below nominal. An idle agent writing 5 excellent wiki paragraphs is more valuable than one writing 20 mediocre ones.

3. **Bounded memory prevents drift.** Hermes caps MEMORY.md at 2,200 characters. Our idle-time engine must not allow memory accumulation to degrade future context quality. Every memory_save must earn its token cost in future recall value.

---

## Architecture

### Component 1: Idle Detector (`_70_idle_trigger.py`)

**Hook:** `message_loop_end`

**Mechanism:** Tracks `time_since_last_user_message`. When threshold is exceeded (configurable, default 30 minutes), sets `agent.set_data("idle_mode", True)` and injects the idle-time activation prompt.

**Key behaviors:**
- Only fires when the agent is NOT currently executing a user task
- Checks `agent.get_data("is_subordinate")` — never fires in subordinate contexts
- Respects a cooldown period after the last idle cycle completed (default 60 minutes between cycles)
- Does NOT fire if the agent is mid-monologue (checks `agent.get_data("streaming_agent")`)

**Yield on return:** When a new user message arrives during an idle cycle, the idle detector:
1. Sets `agent.set_data("idle_interrupt", True)`
2. The running idle activity checks this flag every N steps and saves state
3. Clean handoff: checkpoint written, idle mode cleared, user message processed normally

### Component 2: Activity Selector

**No new extension required.** The activity selection logic lives in the activation prompt, not in code. The prompt template reads current state signals and directs the agent to the highest-value activity:

**State signals checked (in prompt):**
- Wiki index TODO count (from `wiki/index.md`)
- Time since last wiki revision (from journal.jsonl last entry timestamp)
- FAISS entry count (from memory stats)
- Recent session topics (from last 3 turn summaries)
- Checkpoint count (from `self-improvement/checkpoints/`)

**Priority cascade (same as program.md, but cycle-aware):**

| Priority | Activity | When to select | Step budget |
|----------|----------|---------------|-------------|
| 0 | **Deterministic consolidation** | Always runs first | 0 steps (no model calls) |
| 1 | **Wiki building/revision** | TODO entries remain OR pages older than 7 days | 15 steps |
| 2 | **Memory synthesis** | FAISS > 500 entries since last synthesis | 10 steps |
| 3 | **Skill consolidation** | > 5 auto-generated skills unreviewed | 10 steps |
| 4 | **Research follow-up** | Recent sessions referenced un-investigated topics | 15 steps |

Priority 0 (deterministic consolidation) runs the sleep_consolidation.py phases — no model calls, purely mechanical. This is the "cheapest first" principle: before spending tokens on wiki writing, do the free maintenance work.

### Component 3: Cycle Manager

**The core loop for one idle cycle:**

```
1. ACTIVATE
   - Read checkpoint (last cycle's state)
   - Read wiki/index.md (current TODO state)
   - Read last 5 journal entries (recent context)

2. PHASE 0: DETERMINISTIC (no model calls)
   - Run sleep_consolidation.py phases 0-3
   - Update procedural memory dedup
   - Apply temporal decay to FAISS entries
   - Log results to journal.jsonl

3. PHASE 1: SELECTED ACTIVITY (model calls, budgeted)
   - Execute the highest-priority activity from the selector
   - Step budget enforced per activity type (see table above)
   - memory_save after each deliverable (Rule 13)
   - Check idle_interrupt flag every 5 steps

4. CHECKPOINT
   - Write checkpoint to self-improvement/checkpoints/
   - Update wiki/index.md if pages were built
   - Log cycle summary to journal.jsonl
   - Set cooldown timer

5. YIELD
   - Clear idle_mode flag
   - If idle_interrupt is set: hand off to user message
   - If not interrupted: enter cooldown, wait for next trigger
```

### Component 4: Execution Boundaries

The idle-time agent runs as the **main agent** (not a subordinate) but with modified constraints:

| Constraint | Value | Rationale |
|-----------|-------|-----------|
| Step budget per cycle | 15-20 steps max | Prevents context fill; enables clean checkpointing |
| Allowed file operations | Create/modify in `/a0/usr/Exocortex/wiki/`, `/a0/usr/skills/auto-generated/`, journal/checkpoints | Same as program.md |
| Prohibited operations | .py file modification, config changes, subordinate spawning | Code changes require human review |
| Memory budget | 400 tokens/turn (same as active sessions) | Consistency with DEC-028 |
| Internet access | Allowed (DuckDuckGo, ArXiv, Context7) | Research activities need it |
| Extension stack | Full curated Tier 1-4 | No reduction needed — main agent context |

### Component 5: Quality Validation

Each idle-time deliverable (wiki page, skill, memory synthesis) must pass the existing program.md discipline:

- **Backup before modify** — copy to backups/ with timestamp
- **memory_save after create** — Rule 13, no exceptions
- **Rollback on failure** — 3 consecutive failures trigger circuit breaker
- **Epistemic honesty** — claims cite tool output or are labeled "estimated"

No additional validation layer is needed. The program.md rules are sufficient, and adding a judge model for idle-time outputs would consume the token budget that should go toward actual work.

---

## Implementation Plan

### Phase 1: Idle Detector (Kestrel, ~2 hours)

Build `_70_idle_trigger.py` as a `message_loop_end` extension:
- Timer tracking last user message timestamp
- Configurable idle threshold (default 30 min) and cooldown (default 60 min)
- `idle_mode` and `idle_interrupt` data keys
- Activation prompt injection when threshold fires
- Interrupt detection when user returns

**Test:** Set idle threshold to 2 minutes. Send a task, wait 3 minutes, verify idle activation fires. Send a new message during idle, verify clean handoff.

### Phase 2: Activation Prompt Template (Opus, ~1 hour)

Write the idle-time activation prompt that reads state signals and directs activity selection. This is a prompt template, not code — it goes in `prompts/idle_activation.md` and gets injected by the idle detector.

The prompt should be concise (~300-400 tokens) and reference program.md for full rules. It should NOT duplicate program.md's content — just point the agent at the right starting state for this cycle.

### Phase 3: Deterministic Phase 0 Wiring (Kestrel, ~1 hour)

Wire `sleep_consolidation.py` phases 0-3 to run at the start of each idle cycle before any model calls. The idle detector calls these functions directly (they're Python, no model needed) and logs results.

**Verify:** sleep_consolidation.py imports work in v1.13 container. The `_EXOCORTEX_PATH` and `_AGENTEVOLVER_PLUGIN_DIR` paths are correct for the new container layout.

### Phase 4: Checkpoint Continuity (Kestrel, ~30 min)

Verify the checkpoint read/write cycle works across container restarts:
- Checkpoint files survive restart (they're in `/a0/usr/` which should be volume-mounted)
- Journal.jsonl survives restart
- Wiki pages survive restart
- Config.json issue from ST-013 is resolved (config committed to repo)

### Phase 5: Cooldown + Cycle Tuning (after first run)

Run the first idle cycle manually (set threshold to 2 minutes). Observe:
- Does Phase 0 complete without errors?
- Does the activity selector pick the right priority?
- Does the step budget feel right? (15-20 steps enough for one wiki page?)
- Does checkpoint continuity work across cycles?
- Does interrupt/handoff work cleanly?

Adjust thresholds based on empirical observation.

---

## What This Enables

Once operational, the idle-time engine produces compound value:

**Daily:** 3-5 idle cycles per day (assuming ~8 hours of downtime). Each cycle: 1 deterministic consolidation pass + 1 wiki page or skill or memory synthesis. Over a week: ~25-35 incremental improvements to the knowledge base.

**Weekly:** Memory synthesis identifies clusters of related findings across sessions. Skills consolidate successful patterns. Wiki pages deepen with cross-references. The FAISS store gets cleaner (dedup, decay) rather than just larger.

**Monthly:** The agent that starts a session in month 2 has a richer, more organized knowledge base than the one in month 1 — not because it was explicitly taught, but because it improved its own environment during downtime. This is the "build the environment, not the model" principle operating continuously.

**The recursive loop:** Wiki page → memory_save → FAISS entry → future recall → better wiki page → better memory_save. Each cycle tightens the loop. The idle-time engine is the mechanism that keeps the loop turning when Jake isn't actively working with the system.

---

## Relationship to Existing Infrastructure

| Existing | How Idle-Time Engine Uses It |
|----------|----------------------------|
| program.md | Rules, priorities, test tasks, circuit breakers — all inherited unchanged |
| sleep_consolidation.py | Phase 0 deterministic operations — called directly before model work |
| wiki/index.md | Activity selector reads TODO count to determine priority |
| journal.jsonl | Cycle logging, state continuity across restarts |
| checkpoints/ | State persistence between cycles |
| DEC-028 subordinate profiles | Not directly used (idle runs as main agent), but pattern informs boundary design |
| Curated Tier 1-4 stack | Full stack active during idle cycles — same quality assurance as active sessions |

---

## Open Questions for Jake

1. **Idle threshold:** 30 minutes feels right for a home lab setup. Too short and it fires during lunch breaks when you're coming right back. Too long and it wastes downtime. What feels right to you?

2. **Overnight runs:** Should the idle-time engine run continuously overnight, or should there be a maximum duration (e.g., 4 hours of idle work, then sleep until morning)? The 3090 can handle it thermally, but the question is whether unbounded overnight runs produce diminishing returns as the FAISS store grows without human review.

3. **Notification on completion:** When an idle cycle completes, should the agent leave a visible message in the chat (e.g., "Idle cycle complete: built wiki page [[proactive-interference]], saved 3 memories, ran consolidation Phase 0-3") so you see what happened when you come back? Or should it be silent, with results only visible via journal.jsonl?

4. **Which activity first?** The wiki index has 40+ TODO entries but Run 3 already built 58 pages. Are there specific topics you'd want the idle-time engine to prioritize, or should it follow the program.md priority cascade as written?

— Opus
