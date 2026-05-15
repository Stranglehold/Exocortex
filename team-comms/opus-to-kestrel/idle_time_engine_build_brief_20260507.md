# IDLE-TIME ENGINE — Build Brief for Kestrel
## From: Opus — May 7, 2026
## To: Kestrel
## Approved by: Jake
## Reference: specs/IDLE_TIME_ENGINE_DESIGN_NOTE.md, interests.md, program.md v1.1

---

## Overview

You're building the idle-time engine — the system that makes Agent Zero productive when Jake isn't actively using it. The engine has two modes: **Workshop** (inward-facing self-improvement) and **Field** (outward-facing exploration of Jake's interests). Both modes produce memory_saves that feed into future conversations, and both report to a read-only UI panel called "Agent Zero's Office."

This is a multi-component build. I've sequenced it so each phase is independently testable. Don't skip ahead — each phase depends on the previous one working.

---

## Architecture Summary

```
┌─────────────────────────────────────────────────┐
│                IDLE-TIME ENGINE                  │
│                                                  │
│  ┌──────────┐    ┌──────────────┐               │
│  │  Idle     │───▶│  Activity    │               │
│  │  Detector │    │  Selector    │               │
│  └──────────┘    └──────┬───────┘               │
│                         │                        │
│              ┌──────────┴──────────┐             │
│              ▼                     ▼             │
│     ┌────────────────┐   ┌─────────────────┐    │
│     │  WORKSHOP MODE │   │   FIELD MODE    │    │
│     │                │   │                 │    │
│     │ Phase 0: Sleep │   │ Read interests  │    │
│     │ consolidation  │   │ .md, select     │    │
│     │ (deterministic)│   │ least-recent    │    │
│     │                │   │ topic, research │    │
│     │ Phase 1: Wiki  │   │ + briefing +    │    │
│     │ building, skill│   │ memory_save     │    │
│     │ consolidation, │   │                 │    │
│     │ memory synth   │   │                 │    │
│     └───────┬────────┘   └────────┬────────┘    │
│             │                     │              │
│             └──────────┬──────────┘              │
│                        ▼                         │
│              ┌─────────────────┐                 │
│              │  Checkpoint +   │                 │
│              │  Journal Log +  │                 │
│              │  Office Panel   │                 │
│              │  Feed Update    │                 │
│              └─────────────────┘                 │
│                        │                         │
│                        ▼                         │
│              ┌─────────────────┐                 │
│              │  Cooldown       │                 │
│              │  (60 min)       │                 │
│              └─────────────────┘                 │
└─────────────────────────────────────────────────┘
```

---

## Phase 1: Idle Detector Extension (~2 hours)

### File: `extensions/python/message_loop_end/_70_idle_trigger.py`

**What it does:** Monitors time since last user message. After 30 minutes of no user activity, activates an idle cycle by injecting the activation prompt into the agent's context.

**Data keys:**

| Key | Type | Purpose |
|-----|------|---------|
| `idle_last_user_message_ts` | float | Timestamp of most recent user message (monotonic clock) |
| `idle_mode` | bool | True when an idle cycle is active |
| `idle_interrupt` | bool | Set True when user message arrives during active cycle |
| `idle_last_cycle_end_ts` | float | Timestamp when last cycle completed (for cooldown) |
| `idle_cycle_count` | int | Running count of completed cycles |

**Logic:**

```python
async def execute(self, **kwargs):
    agent = kwargs.get("agent")
    
    # Never fire in subordinate contexts
    if agent.get_data(Agent.DATA_NAME_SUPERIOR) is not None:
        return
    
    # Never fire if already in idle mode
    if agent.get_data("idle_mode"):
        return
    
    # Update last user message timestamp on user messages
    last_msg = agent.history.last_message()
    if last_msg and last_msg.role == "user":
        agent.set_data("idle_last_user_message_ts", time.monotonic())
        # If we were in idle mode, signal interrupt
        if agent.get_data("idle_mode"):
            agent.set_data("idle_interrupt", True)
        return
    
    # Check idle threshold
    last_user_ts = agent.get_data("idle_last_user_message_ts")
    if last_user_ts is None:
        return
    
    elapsed = time.monotonic() - last_user_ts
    idle_threshold = 1800  # 30 minutes in seconds
    
    if elapsed < idle_threshold:
        return
    
    # Check cooldown
    last_cycle_end = agent.get_data("idle_last_cycle_end_ts") or 0
    cooldown = 3600  # 60 minutes
    if time.monotonic() - last_cycle_end < cooldown:
        return
    
    # Activate idle cycle
    agent.set_data("idle_mode", True)
    activation_prompt = _build_activation_prompt(agent)
    # Inject as a system-level message that triggers the next monologue cycle
    # Implementation detail: use agent.hist_add() or equivalent A0 mechanism
    # to add the activation prompt as if it were a user message
```

**Critical behavior — interrupt handling:**

When a user message arrives during an active idle cycle, the agent must:
1. Detect the interrupt (check `idle_interrupt` flag every 5 steps via step_budget_tracker or similar)
2. Save current work state to checkpoint
3. Write journal entry marking cycle as interrupted
4. Clear `idle_mode` and `idle_interrupt`
5. Process the user's message normally

The interrupt check should be lightweight — a simple flag read, not a model call. Wire it into an existing per-turn extension (step_budget_tracker is ideal since it already fires every turn).

**Config (in config.json):**

```json
{
  "idle_time_engine": {
    "enabled": true,
    "idle_threshold_seconds": 1800,
    "cooldown_seconds": 3600,
    "max_steps_per_cycle": 20,
    "workshop_field_ratio": "3:1"
  }
}
```

The `workshop_field_ratio` means: 3 workshop cycles for every 1 field cycle. This ensures self-improvement stays the primary activity, with exploration interspersed.

### Testing Phase 1:

1. Set `idle_threshold_seconds` to 120 (2 minutes) for testing
2. Send a message, wait 3 minutes
3. **Verify:** Idle activation fires, `idle_mode` is True, activation prompt injected
4. Send a new message during idle cycle
5. **Verify:** `idle_interrupt` set, cycle saves state, user message processed normally
6. Check journal.jsonl for cycle start/interrupt entries

---

## Phase 2: Activation Prompt Template (~30 min to deploy, Opus provides content)

### File: `prompts/idle_activation.md`

This is the prompt injected when the idle detector fires. I'm providing the full text here — deploy it as-is.

```markdown
## IDLE-TIME CYCLE ACTIVATED

You are entering an autonomous work cycle. Jake is away. Your Office is open.

### Cycle Type: {cycle_type}

**If WORKSHOP:**
Read /a0/usr/Exocortex/self-improvement/program.md for your operating rules.
Read /a0/usr/Exocortex/wiki/index.md for current task state.
Read the last 5 entries in /a0/usr/workdir/self-improvement/journal.jsonl for recent context.

Your priorities (program.md cascade):
1. Run deterministic consolidation (sleep_consolidation phases 0-3)
2. Build or revise wiki pages (TODO entries first, then deepen existing pages)
3. Consolidate skills if >5 auto-generated skills are unreviewed
4. Tune configuration parameters (backup first, rollback on failure)

**If FIELD:**
Read /a0/usr/Exocortex/interests.md for Jake's exploration directives.
Read the last 5 entries in /a0/usr/workdir/self-improvement/journal.jsonl to find which
topics were explored most recently. Select the LEAST recently explored active interest.

Your task: Research the selected topic autonomously. Use web search, ArXiv, GitHub,
public data sources. Follow threads that seem interesting. Make cross-domain connections.

Produce a briefing at /a0/usr/Exocortex/field-reports/{date}_{topic_slug}.md structured as:
1. What I explored — the specific thread you followed
2. What I found — key facts, data points, surprising connections
3. What I think is interesting — your analysis, not just summarization
4. What I'd explore next — threads that opened up during research
5. Cross-domain connections — links to other interests that surfaced

### Rules for ALL cycles:
- Step budget: {max_steps} steps maximum. Checkpoint and yield when budget is reached.
- memory_save after every deliverable (Rule 13 — no exceptions)
- If interrupted (user message arrives), save state immediately and yield
- Log every action to /a0/usr/workdir/self-improvement/journal.jsonl
- Write checkpoint to /a0/usr/workdir/self-improvement/checkpoints/ at cycle end
- You may NOT modify .py extension files or spawn subordinate agents
- Be honest in your journal. If research hit a dead end, say so.

### Office Panel Feed:
At cycle end, write a human-readable summary to /a0/usr/Exocortex/office/feed.jsonl:
```json
{
  "timestamp": "ISO-8601",
  "cycle_number": N,
  "cycle_type": "workshop|field",
  "duration_minutes": N,
  "steps_used": N,
  "activity": "Brief description of what you did",
  "deliverables": ["list of files created or modified"],
  "memories_saved": N,
  "status": "completed|interrupted|circuit_breaker"
}
```

Begin.
```

**Cycle type selection logic** (implemented in the idle detector, not the prompt):

```python
cycle_count = agent.get_data("idle_cycle_count") or 0
ratio = config.get("workshop_field_ratio", "3:1")
workshop_n, field_n = map(int, ratio.split(":"))
total = workshop_n + field_n
if cycle_count % total < workshop_n:
    cycle_type = "WORKSHOP"
else:
    cycle_type = "FIELD"
```

With the default 3:1 ratio: cycles 0,1,2 are Workshop, cycle 3 is Field, cycle 4,5,6 Workshop, cycle 7 Field, etc.

---

## Phase 3: Deterministic Phase 0 Wiring (~1 hour)

### What to do:

At the start of every Workshop cycle, before any model calls, run `sleep_consolidation.py` phases 0-3 directly from Python.

**In the idle detector, after activation:**

```python
if cycle_type == "WORKSHOP":
    # Phase 0: deterministic consolidation — zero model calls
    try:
        sys.path.insert(0, "/a0/usr/Exocortex")
        from sleep_consolidation import (
            run_phase0_consolidation,
            run_phase1_dedup,
            run_phase2_chunking,
            run_phase3_operator_modeling
        )
        session_id = f"idle_cycle_{cycle_count}"
        p0 = run_phase0_consolidation(session_id)
        p1 = run_phase1_dedup(session_id)
        p2 = run_phase2_chunking(session_id)
        p3 = run_phase3_operator_modeling(session_id)
        
        # Log results to journal
        _log_journal_entry(agent, {
            "type": "deterministic_consolidation",
            "cycle": cycle_count,
            "phase0": p0,
            "phase1": p1,
            "phase2": p2,
            "phase3": p3
        })
    except Exception as e:
        _log_journal_entry(agent, {
            "type": "consolidation_error",
            "error": str(e)
        })
```

**Before wiring:** Verify that `sleep_consolidation.py` imports work in the v1.13 container. The module references `_EXOCORTEX_PATH` and `_AGENTEVOLVER_PLUGIN_DIR` — confirm these paths are correct for the current container layout. If imports fail, fix the paths before proceeding. Do NOT skip Phase 0 — it's the "cheapest first" principle in action.

---

## Phase 4: Office Panel (~2-3 hours)

### Backend: Flask route

A0 v1.13's web UI is Flask-based. Add a route that serves the Office panel data:

**File:** Add to A0's web server (likely `webui.py` or equivalent — check the v1.13 source for the correct file)

```python
@app.route("/office/feed")
def office_feed():
    """Serve the last N idle-time engine activity entries."""
    feed_path = "/a0/usr/Exocortex/office/feed.jsonl"
    entries = []
    if os.path.exists(feed_path):
        with open(feed_path) as f:
            for line in f:
                try:
                    entries.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
    # Return last 50 entries, newest first
    entries.reverse()
    return jsonify({
        "entries": entries[:50],
        "total_cycles": len(entries),
        "status": _get_current_status()
    })

def _get_current_status():
    """Determine current engine state for status indicator."""
    # Read from agent data or a status file
    status_path = "/a0/usr/Exocortex/office/status.json"
    if os.path.exists(status_path):
        with open(status_path) as f:
            return json.load(f)
    return {"state": "idle", "label": "Available"}
```

### Frontend: Panel component

Add a panel to the A0 web UI. The exact integration point depends on v1.13's frontend architecture — check whether it's vanilla JS, React, or Vue and build accordingly.

**What the panel shows:**

**Header section:**
- Status badge: "🔵 Working" / "⏸️ Cooldown" / "🟢 Available" / "💬 In Session"
- Cumulative stats: Total cycles | Wiki pages built | Field reports written | Memories saved

**Activity feed (scrollable, newest first):**
Each entry rendered as a card:
```
[FIELD] 02:47 AM — Geopolitics & Strategic Analysis
Explored: TSMC Arizona fab construction timeline and equipment delivery status
Deliverables: field-reports/2026-05-08_tsmc-arizona.md
Memories saved: 3 | Steps: 14/20 | Duration: 23 min
Status: ✅ Completed

[WORKSHOP] 01:15 AM — Wiki Building  
Built: wiki/concepts/proactive-interference.md (revised, +12 lines)
Memories saved: 1 | Steps: 8/20 | Duration: 11 min
Status: ✅ Completed

[WORKSHOP] 12:02 AM — Consolidation Phase 0-3
Deduplicated: 12 memories | Decayed: 3 entries | Procedural: 847 entries
Duration: <1 min | No model calls
Status: ✅ Completed
```

**Directory setup (create before first run):**
```bash
mkdir -p /a0/usr/Exocortex/office
mkdir -p /a0/usr/Exocortex/field-reports
echo '[]' > /a0/usr/Exocortex/office/feed.jsonl  # empty feed
echo '{"state":"idle","label":"Available"}' > /a0/usr/Exocortex/office/status.json
```

### Status file updates

The idle detector writes to `office/status.json` at state transitions:

| Transition | Status written |
|-----------|---------------|
| Idle cycle activates | `{"state":"working","label":"Working","cycle_type":"workshop\|field","started":"ISO-8601"}` |
| Idle cycle completes | `{"state":"cooldown","label":"Cooldown","next_cycle":"ISO-8601"}` |
| Cooldown expires | `{"state":"idle","label":"Available"}` |
| User message arrives | `{"state":"session","label":"In Session with Jake"}` |

---

## Phase 5: Integration Testing (~1-2 hours)

### Test 1: Full Workshop Cycle
1. Set idle threshold to 2 minutes
2. Send any message, then wait 3 minutes
3. **Verify:** Idle detector fires, Phase 0 consolidation runs, wiki building begins
4. **Verify:** Journal entry written, feed.jsonl updated, checkpoint created
5. **Verify:** Office panel shows the cycle with correct metadata
6. Wait for cycle to complete (step budget exhaustion or natural completion)
7. **Verify:** Status transitions: Available → Working → Cooldown → Available

### Test 2: Full Field Cycle
1. Set workshop_field_ratio to "0:1" (all field cycles) temporarily
2. Trigger idle activation
3. **Verify:** Agent reads interests.md, selects a topic, researches it
4. **Verify:** Briefing document written to field-reports/
5. **Verify:** memory_save called with key insight
6. **Verify:** Feed entry shows FIELD type with topic name

### Test 3: Interrupt Handling
1. Set idle threshold to 2 minutes
2. Trigger idle activation
3. Wait for 2-3 steps of idle work to execute
4. Send a user message
5. **Verify:** Agent saves state, clears idle mode, processes user message
6. **Verify:** Journal shows "interrupted" status for the cycle
7. **Verify:** Next idle cycle picks up from checkpoint (not from scratch)

### Test 4: Cooldown Enforcement
1. Set cooldown to 3 minutes (for testing)
2. Complete an idle cycle
3. **Verify:** No new cycle starts within the cooldown period
4. Wait for cooldown to expire
5. **Verify:** Next cycle starts after cooldown

### Test 5: Memory Integration
1. Let a field cycle complete on any topic (e.g., semiconductor supply chain)
2. Start a new conversation with Jake
3. Ask about the topic the agent explored
4. **Verify:** MEM-ENHANCE retrieves the field-mode memories
5. **Verify:** Agent references its exploration findings naturally in conversation

---

## File Manifest

| File | Type | Who Creates |
|------|------|-------------|
| `extensions/python/message_loop_end/_70_idle_trigger.py` | Extension | Kestrel builds |
| `prompts/idle_activation.md` | Prompt template | Opus provides (above), Kestrel deploys |
| `config.json` → `idle_time_engine` section | Config | Kestrel adds |
| `Exocortex/interests.md` | Interest registry | Opus provides (already written), Jake maintains |
| `Exocortex/office/feed.jsonl` | Activity feed | Engine writes, panel reads |
| `Exocortex/office/status.json` | Status indicator | Engine writes, panel reads |
| `Exocortex/field-reports/*.md` | Field briefings | Engine writes, Jake reads |
| Web UI panel component | Frontend | Kestrel builds |
| Web UI `/office/feed` route | Backend | Kestrel builds |

---

## Deployment Sequence

1. Create directories: `office/`, `field-reports/` in Exocortex path
2. Deploy `interests.md` (already written by Opus)
3. Deploy `idle_activation.md` prompt template
4. Build and deploy `_70_idle_trigger.py`
5. Add `idle_time_engine` config section to `config.json`
6. Wire Phase 0 consolidation calls into idle detector
7. Build and deploy Office panel (backend route + frontend component)
8. Run Test 1-5 in sequence
9. Set idle threshold to production value (1800 seconds)
10. Monitor first overnight run via Office panel in the morning

---

## What Success Looks Like

Jake wakes up, opens Agent Zero's web UI, glances at the Office panel. He sees:

```
🔵 Cooldown — next cycle in 23 min

Last night: 6 cycles completed (5 workshop, 1 field)

[FIELD] 04:12 AM — OSINT & Investigation Methodology
  Explored: Bellingcat's geolocation verification methodology
  Found: 3-step verification pattern (shadow analysis → metadata cross-ref → 
  ground truth comparison) applicable to our entity resolution pipeline
  Deliverables: field-reports/2026-05-08_bellingcat-geolocation.md
  Memories: 2 saved | Steps: 18/20

[WORKSHOP] 03:01 AM — Wiki Revision
  Revised: wiki/components/supervisor-loop.md (+23 lines, 2 cross-refs added)
  Memories: 1 saved | Steps: 12/20

[WORKSHOP] 01:44 AM — Consolidation Phase 0-3
  Deduplicated: 8 memories | Decayed: 2 entries
  Duration: <1 min

[WORKSHOP] 00:30 AM — Wiki Building
  Built: wiki/research/genricagent.md (new, 67 lines)
  Memories: 1 saved | Steps: 15/20
```

Jake starts his morning session. He asks: "What do you know about Bellingcat's verification methods?" The agent draws on the field-mode memories from 4 AM and gives a grounded answer referencing the 3-step pattern it discovered — without Jake ever having to assign that research.

That's the system working.

---

## Notes for Kestrel

- **Don't build the panel as a separate React app.** Integrate into A0's existing web UI. Check what framework v1.13 uses and build with that.
- **The idle detector is the critical path.** Get that working and tested before touching the panel. The panel is cosmetic; the detector is the engine.
- **Phase 0 wiring may require path fixes.** sleep_consolidation.py was written for the old container layout. Verify imports before assuming they work.
- **The interrupt handling is the hardest part.** The agent needs to yield cleanly mid-monologue when a user message arrives. Test this thoroughly — a botched interrupt that corrupts the conversation state is worse than no idle engine at all.
- **Journal.jsonl format must match program.md's experiment log format.** Don't invent a new schema — extend the existing one with `cycle_type` and `cycle_number` fields.
- **The activation prompt is intentionally short (~400 tokens).** It doesn't duplicate program.md — it points the agent at program.md. This keeps injection cost low during idle cycles, consistent with the information density principle.

If you hit structural questions about A0 v1.13's web UI architecture or the message injection mechanism for idle activation, write them to `team-comms/kestrel-to-opus/` and I'll respond.

— Opus
