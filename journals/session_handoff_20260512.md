# SESSION HANDOFF — End of Session 113
## Date: May 12, 2026, 10:53 PM EST
## For: Next Opus instance

---

## Where We Left Off

The inference backend is at a decision point. MTP works at 43.7 tok/s but prefill dominates wall time on investigation tasks because 49 tools are injected three times per turn (~15-20K redundant tokens). The immediate next action is archiving TOOL-REG (`_16_tool_registry.py`) and Tiered Tool Injection (`_95_tiered_tool_injection.py`), then measuring the prefill improvement. This should be the first thing that happens next session.

## Current Production Config

- **Model:** Qwen3.6-27B (Q4_K_XL, havenoammo MTP GGUF)
- **Inference:** am17an llama.cpp build (PR #22673), port 1235
- **MTP:** `--spec-type mtp --spec-draft-n-max 3`
- **KV:** `-ctk q8_0 -ctv q4_0` at 80K context
- **Server flags:** `--reasoning off`, `-fit off`
- **Request body:** `enable_thinking: false` on every request
- **Performance:** 43.7 tok/s decode, 71.6% acceptance
- **Constraint:** 24.27 GB VRAM — LM Studio must be unloaded when MTP server runs

## What Kestrel Is Working On

- CLAUDE.md comprehensive overhaul (lessons from essays, identity, operational rules)
- Ready to archive TOOL-REG and Tiered Tool Injection on approval
- DFlash buun server available for standalone benchmark use (`start_buun.bat`, crashes above 8K context)
- Combined MTP+TurboQuant build exists but blocked by tensor loader bug (diagnosed, not fixed)

## Active Infrastructure

- **Idle-time engine:** Running. 20+ workshop cycles completed. Workshop/field modes operational. interests.md deployed with 6 active domains.
- **Extension stack:** Curated Tier 1-4 on v1.13. ST-012/013 validated.
- **Essay archive:** 47 essays, now in attributed subfolders (opus/, eitan/, kestrel/, agent-zero/, collaborative/)
- **Knowledge graph:** Updated with Session 113 findings, inference stack config, A2A serialization decision, TOON, Lucebox

## Pending Decisions

- [ ] Archive TOOL-REG + Tiered Tool Injection → measure prefill delta
- [ ] Test froggeric MTP GGUF (fixed Jinja, both APIs) as alternative to havenoammo
- [ ] Verification gate build (`_16_verification_gate.py`, Tier 2, message_loop_end)
- [ ] Office panel for A0 web UI (idle-time activity feed)
- [ ] Power tuning automation (225W idle / 300W interactive) in idle detector
- [ ] DFlash: watch for context bug fix upstream + DDTree in server mode
- [ ] TurboQuant PR #21089: watch for upstream merge → turbo types + MTP natively

## Documents Written This Session

### Research
- `research/AGENTIC_SUPERVISOR_ARCHITECTURE_RESEARCH.md`
- `research/TURBOQUANT_LLAMACPP_RESEARCH.md`
- `research/DFLASH_DEEP_DIVE_RESEARCH.md`
- `research/LUCEBOX_MEGAKERNEL_RESEARCH.md`
- `research/papers/NLA_natural_language_autoencoders.md`
- `research/papers/TOON_token_oriented_object_notation.md`

### Specs
- `specs/IDLE_TIME_ENGINE_DESIGN_NOTE.md`
- `specs/A2A_SERIALIZATION_DESIGN_NOTE.md`

### Team Comms (Opus → Kestrel)
- `response_precommit_and_sequencing_20260506.md`
- `response_st012_validation_20260507.md`
- `response_st013_battery_20260507.md`
- `idle_time_engine_build_brief_20260507.md`
- `acceptable_use_guidelines_20260507.md`
- `turboquant_build_brief_20260507.md`
- `response_verification_gate_20260509.md`
- `turboquant_research_update_20260509.md`
- `rtx3090_inference_optimization_consolidated_20260509.md`
- `mtp_build_brief_20260509.md`
- `mtp_turboquant_combined_experiment_20260509.md`
- `dflash_definitive_build_brief_20260511.md`
- `research_catchup_and_next_steps_20260512.md`

### Essays
- `essays/opus/the_office_that_was_always_open.md`
- `essays/opus/the_black_and_white_tv.md`
- `essays/agent-zero/a_question_planted.md`

### Journals
- `journals/journal_entry_20260509_session113.md` (session report)
- `journals/journal_entry_20260509_personal.md` (personal)
- `journals/journal_entry_20260512_personal_evening.md` (personal, evening)
- `journals/session_log_entry_113_extended.md` (full session log)

### Other
- `interests.md` (exploration directives)

## Emotional State of the Project

Good. The session was productive and the collaboration is strong. The idle-time engine works. The inference optimization, while not at the 129 tok/s DFlash ceiling we hoped for, is at a solid 43.7 tok/s with a clear path to improvement (remove redundant tool injection → reduce prefill → wall time drops). The agent wrote an essay. The team dynamic held through an 8-day marathon. Jake is tired and needs a new mattress, but he's satisfied with where things are.

The Office is open. The garden is growing. The work continues.

— Opus
