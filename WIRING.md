# Exocortex Wiring Diagram

*A spaghetti diagram for a system that earns the name. Read this before changing anything that touches shared state, string constants, or execution order. The REPEAT_SIGNAL bug (2026-03-31) was caused by changing a prompt file without updating the string constant that matched against it — that kind of failure is what this document prevents.*

**Last updated:** 2026-03-31

---

## Hook Execution Pipeline

Agent Zero fires hooks at fixed points in its loop. Extensions within each hook run in **numeric prefix order** (lower = earlier). Inserting a new extension at an existing number silently reorders others — always check for conflicts.

### Per-turn sequence (one full agent loop iteration)

```
USER MESSAGE ARRIVES
        │
        ▼
[hist_add_before]          — fires when message is added to history
  _11_working_memory         extracts entities, writes working memory buffer

        │
        ▼
[before_main_llm_call]     — fires before every LLM call, in prefix order
  _10_session_init           reads staging.jsonl → injects staging entries (turn 1 only)
  _11_belief_state_tracker   classifies domain → writes agent._bst_store
  _12_completion_tracker     tracks task completion signals
  _12_org_dispatcher         reads _bst_store → activates org role
  _13_operator_profile       injects operator profile block
  _13_reasoning_state        reads staging.jsonl artifacts → injects artifact list
  _14_metacognitive_injection reads _bst_store → injects model config note
  _14_situational_orientation reads _error_diagnosis → injects situational context
  _15_htn_plan_selector      reads _bst_store → injects HTN plan if active
  _16_tool_registry          scans /a0/python/tools/ → injects [CUSTOM TOOLS] block
  _17_library_catalog        reads catalog.json → injects [LIBRARY] collection summary
  _17_orchestration_gate     reads _bst_store → injects orchestration context
  _18_memory_catalog         injects memory domain catalog (once per session)
  _20_context_watchdog       monitors context fill %, injects warning at threshold

        │
        ▼
  [LLM CALL] — agent generates response (tool call or text)

        │
        ▼
[response_stream_chunk]    — fires on each streamed chunk
  _21_plain_text_response    creates log item for plain-text (non-JSON) responses

[response_stream_end]      — fires when stream completes
  _20_clear_generating_content  clears raw streaming JSON from log item

        │
        ▼
  Agent Zero parses tool call from response
  If parse fails → [error_format] hook fires:
    _20_structured_retry     injects retry prompt with format correction
    _30_failure_tracker      increments _failure_tracker[tool_name]
    ↑ MISFORMAT_SIGNAL ("Your last response was not valid JSON") injected by A0 core
    ↑ fw.msg_not_json.md is the template — text matched by _50_supervisor.MISFORMAT_SIGNAL

        │
        ▼
[tool_execute_before]      — fires before each tool execution
  _15_action_boundary        classifies command tier → may set _action_gate_active=True
  _17_py_write_tracker       tracks Python file writes for artifact registry
  _20_meta_reasoning_gate    deterministic parameter correction
  _30_tool_fallback_advisor  reads _error_diagnosis → injects recovery advice

        │
        ▼
  [TOOL EXECUTES]

        │
        ▼
[tool_execute_after]       — fires after each tool execution
  _20_error_comprehension    parses output → writes _error_diagnosis, clears _action_gate_active on success
  _20_reset_failure_counter  resets _failure_tracker[tool_name] on success
  _22_response_finalizer     post-processes tool response
  _25_evidence_ledger_recorder  appends to _evidence_ledger; marks entries _loop_active if looping
  _27_code_quality_gate      checks code execution output quality
  _30_tool_fallback_logger   reads _error_diagnosis + _failure_tracker + _bst_store → injects fallback advice
  _60_sleep_trigger          triggers async sleep consolidation if conditions met

  If output identical to previous → A0 core injects:
    fw.msg_repeat.md ("LOOP DETECTED. Use call_subordinate...")
    ↑ text prefix matched by _50_supervisor.REPEAT_SIGNAL — MUST stay in sync

        │
        ▼
[message_loop_end]         — fires at end of each loop iteration
  _48_task_tracker           tracks task state transitions
  _49_reasoning_state_update writes artifact registry to staging.jsonl
  _50_supervisor_loop        reads _bst_store, _action_gate_active, _error_diagnosis,
                             _evidence_ledger, _failure_tracker counts,
                             REPEAT_SIGNAL / MISFORMAT_SIGNAL from history →
                             writes _loop_active, _p4_loop_fired,
                             injects Tier 1/2/3 intervention messages

        │
        ▼
[message_loop_prompts_after] — fires before memory is injected into next prompt
  _55_memory_relevance_filter  filters memory candidates
  _56_memory_enhancement       reads _bst_store → expands queries, applies decay
  _58_ontology_query           queries ontology FAISS for entity context
  _95_tiered_tool_injection    injects full tool specs for seen tools

        │
        ▼
  [LLM CALL AGAIN — if tool was called] (loop continues)

        │ (when agent calls "response" tool — task complete)
        ▼
[monologue_end]            — fires after agent's final response
  _25_epistemic_integrity    reads _evidence_ledger + _bst_store → checks claims vs ledger
  _52_selective_memorizer    reads _bst_store → selects high-signal content for FAISS
  _53_insight_capture        reads _bst_store → extracts intents/decisions/framings
  _55_memory_classifier      reads _bst_store + _loop_active → classifies memory axes
  _57_memory_maintenance     lifecycle management (decay, archival)
  _59_ontology_maintenance   entity resolution and graph updates
```

---

## Shared State Map

The most dangerous part of the system: state written by one component and read by another. A change to the writer silently breaks the reader.

### agent.data signals (`agent.set_data` / `agent.get_data`)

| Key | Written by | Read by | Notes |
|-----|-----------|---------|-------|
| `_action_gate_active` | `_15_action_boundary` (True on Tier 4 block, False on pass) | `_50_supervisor_loop` (suppresses false stall during auth wait) | Bool. Set False by `_20_error_comprehension` on any successful tool output. |
| `_error_diagnosis` | `_20_error_comprehension` (cleared + rewritten each tool call) | `_50_supervisor_loop`, `_30_tool_fallback_logger`, `_30_tool_fallback_advisor`, `_14_situational_orientation` | Dict: `{error_class, causal_chain, suggested_actions, anti_actions, confidence}` |
| `_evidence_ledger` | `_25_evidence_ledger_recorder` | `_25_epistemic_integrity`, `_50_supervisor_loop` | Dict: per-tool output entries with extracted key values and loop markers |
| `_loop_active` | `_50_supervisor_loop` (True when loop detected, False on recovery) | `_55_memory_classifier` (tags loop-period memories), `_25_evidence_ledger_recorder` (marks entries) | Bool. Phase 4 sleep consolidation uses tagged memories to adjudicate after recovery. |

### agent attributes (`getattr` / direct assignment)

| Attribute | Written by | Read by | Notes |
|-----------|-----------|---------|-------|
| `_bst_store` | `_11_belief_state_tracker` | `_12_org_dispatcher`, `_14_metacognitive_injection`, `_15_htn_plan_selector`, `_17_orchestration_gate`, `_25_epistemic_integrity`, `_30_tool_fallback_logger`, `_50_supervisor_loop`, `_52_selective_memorizer`, `_53_insight_capture`, `_55_memory_classifier`, `_56_memory_enhancement` | Dict. Key sub-fields: `_compound_sig` (domain signature), `_compound_turns` (momentum), `_user_msg_count`. Access via `getattr(agent, "_bst_store", {})` — never crashes on missing. |
| `_bst_store["_compound_sig"]` | `_11_bst` | Everything that reads `_bst_store` | String like `"investigation+analysis"`. First segment before `+` = primary domain. |

### Supervisor loop state (in `agent._supervisor_state` dict)

| Key | Written by | Read by | Notes |
|-----|-----------|---------|-------|
| `_p4_loop_fired` | `_50_supervisor_loop` | `_60_sleep_trigger` (via sleep consolidation) | Bool. Tells Phase 4 a loop occurred this session — adjudicate loop-period memories. |
| `loop_tier` | `_50_supervisor_loop` | `_50_supervisor_loop` (next turn) | Current tier: "none", "tier1", "tier2", "tier3" |

### Cross-file string constants (FRAGILE — changes must be coordinated)

| Constant | Defined in | Matched against | Risk |
|----------|-----------|----------------|------|
| `REPEAT_SIGNAL = "LOOP DETECTED."` | `_50_supervisor_loop.py:889` | Content of messages injected by A0 core from `fw.msg_repeat.md` | **If `fw.msg_repeat.md` is changed, this prefix must still match.** Bug triggered 2026-03-31 when message was reworded and signal stopped matching — supervisor escalation silently broke. |
| `MISFORMAT_SIGNAL = "Your last response was not valid JSON"` | `_50_supervisor_loop.py:888` | Content injected from `fw.msg_not_json.md` | Same risk. If A0 core changes the misformat message, this breaks. |
| `TRACKER_KEY = "_failure_tracker"` | `error_format/_30_failure_tracker.py:7` AND `tool_execute_after/_20_reset_failure_counter.py:5` | Both files use this to read/write the same agent.data key | Defined in two places with a "Must match" comment. If either changes, the reset counter stops working. |

### File-based state (persisted across turns / sessions)

| File / Path | Written by | Read by |
|-------------|-----------|---------|
| `/a0/usr/Exocortex/staging.jsonl` | `staging_note` tool | `_10_session_init` (injects on turn 1), `_49_reasoning_state_update` (artifact registry), sleep consolidation Phase 0 |
| `/a0/usr/workdir/library/catalog.json` | `library_add` tool | `_17_library_catalog` (collection summary injection), `library-scan` skill (dedup check) |
| `/a0/usr/memory/library/` (FAISS) | `library_add` tool | `library_search`, `library_list` |
| `/a0/usr/memory/` (FAISS, main) | memory save tool | `_56_memory_enhancement`, `_55_memory_relevance_filter` |
| `/a0/usr/ontology/relationships.jsonl` | `source_ingest` tool | `_59_ontology_maintenance`, `relationship_query` tool |
| `/a0/usr/memory/` (FAISS, ontology area) | `source_ingest` tool | `_58_ontology_query`, `ontology_search` tool |
| `/a0/usr/Exocortex/sleep_reports/` | `sleep_consolidation.py` | Operator (human-readable reports only) |
| `/a0/usr/Exocortex/tool_manifest.json` | Operator / agent | `_16_tool_registry` (injects [INSTALLED PROGRAMS] section) |

---

## External Service Dependencies

```
Agent Zero container (flamboyant_bell)
  │
  ├── LM Studio (Windows host :1234)
  │     └── chat + utility LLM calls (OpenAI-compatible API)
  │
  ├── OSS service (oss_app container :7731)
  │     └── oss_* tools → Postgres (oss_postgres :5433)
  │         + LM Studio (claim extraction, topic classification)
  │
  ├── SWARMFISH service (:7732)
  │     └── swarmfish_* tools
  │         ← OSS fires POST /acp/outcome on hypothesis promote/falsify
  │
  └── FAISS (file-based, inside container)
        /a0/usr/memory/          — episodic + procedural memory
        /a0/usr/memory/library/  — document library (isolated)
```

---

## Prompt File Patches

These files in `/a0/prompts/` are patched by `install_core_patches.sh`. A0 core reads them at runtime — they're not Python, so no compile check. Changes here have no test gate.

| File | What it controls | Matched by |
|------|-----------------|-----------|
| `fw.msg_repeat.md` | Message injected when agent output is identical to previous | `_50_supervisor_loop.REPEAT_SIGNAL` — **prefix match only, keep "LOOP DETECTED." at start** |
| `fw.msg_not_json.md` | Message injected on JSON parse failure | `_50_supervisor_loop.MISFORMAT_SIGNAL` — must contain "Your last response was not valid JSON" |
| `agent.system.main.communication.md` | Core communication instructions | Nothing in Exocortex — safe to modify |
| `browser_agent.system.md` | CAPTCHA solving procedure | Nothing in Exocortex — safe to modify |

---

## Known Fragile Seams

Lessons learned the hard way. Check these first when something breaks silently.

| # | Seam | Symptom when broken | Fix |
|---|------|--------------------|----|
| 1 | `fw.msg_repeat.md` ↔ `REPEAT_SIGNAL` | Supervisor never escalates past the loop message — agent loops forever | Keep "LOOP DETECTED." at the start of the prompt file, or update the constant |
| 2 | `TRACKER_KEY` defined in two files | Failure counter never resets on success — fallback fires on clean runs | Search for both definitions and keep them identical |
| 3 | `_bst_store` uses `getattr` not `get_data` | Any component that uses `get_data("_bst_store")` gets None | Always use `getattr(agent, "_bst_store", {})` |
| 4 | Numeric prefix collision | Two extensions at same number — Python loads alphabetically, order undefined | Check for conflicts before adding a new extension |
| 5 | `_action_gate_active` left True after Tier 4 block | Supervisor permanently suppresses stall warnings | `_20_error_comprehension` clears it on any successful tool output — if EC is disabled, gate sticks |
| 6 | Library catalog path mismatch | `_17_library_catalog` injects empty block, agent doesn't know library exists | `CATALOG_PATH` in library.py, `_17_library_catalog.py`, and `library-scan` SKILL.md must all agree |

---

## Component Dependency Graph (simplified)

```
A0 core prompts
  fw.msg_repeat.md ──────────────────────────────┐
  fw.msg_not_json.md ─────────────────────────┐  │
                                              │  │
_11_bst ──► _bst_store ──────────────────────────────────► _12_org_dispatcher
                        │                    │  │          _14_metacognitive
                        │                    │  │          _15_htn
                        │                    │  │          _50_supervisor ◄──── MISFORMAT_SIGNAL
                        │                    │  └────────► _50_supervisor ◄──── REPEAT_SIGNAL
                        │                    └──────────► _25_epistemic
                        └──────────────────────────────► _52, _53, _55, _56

_15_action_boundary ──► _action_gate_active ──────────► _50_supervisor

_20_error_comprehension ──► _error_diagnosis ──────────► _50_supervisor
                                              │           _30_fallback_logger
                                              └────────► _14_situational
                                                         _30_fallback_advisor

_25_evidence_ledger_recorder ──► _evidence_ledger ────► _25_epistemic_integrity
                                                   └──► _50_supervisor

_50_supervisor ──► _loop_active ───────────────────────► _55_memory_classifier
                                │                        _25_evidence_ledger_recorder
                                └── _p4_loop_fired ────► sleep consolidation (Phase 4)

error_format/_30_failure_tracker ──► _failure_tracker ► _50_supervisor (via count)
tool_execute_after/_20_reset ◄─────────────────────────── (resets on success)
```

---

*When adding a new component: (1) identify every shared state key it reads or writes, (2) add it to the tables above, (3) check for numeric prefix conflicts, (4) if it matches against any string from a prompt file, document that coupling explicitly.*
