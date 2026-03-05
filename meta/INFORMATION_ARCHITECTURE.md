# Exocortex Information Architecture — Agent Zero Environment

**Purpose:** Defines what goes where inside the Agent Zero container, the reading order for a new instance, and the update cadence for each document.

**Date:** 2026-03-04
**Last updated:** Session 048 — repo root cleanup, all files moved to proper subdirectories.

---

## Directory Structure

```
/a0/usr/Exocortex/
├── README.md                    # Project overview. Public-facing.
├── QUICKSTART.md                # Quick deployment guide.
├── LICENSE                      # Apache 2.0
├── install_all.sh               # Main deployment script. Run from repo root.
├── install_skills.sh            # Skills deployment.
├── check_skills_upstream.sh     # Upstream conflict checker.
├── setup_github.sh              # Git configuration.
├── update.sh                    # Update script.
│
├── identity/                    # Slow-changing. Who I am. Read first.
│   ├── SOUL.md                  # Orientation schema. Updates: when staging items promote.
│   ├── soul_staging.md          # Observations accumulating toward SOUL.md. Updates: every session.
│   ├── soul_staging_complete.md # Completed staging document from promotion cycle.
│   └── opus_agent_zero_context.md  # Agent Zero-specific operational supplement.
│
├── state/                       # Fast-changing. Where we are now. Read second.
│   ├── STATE.md                 # Operational snapshot. Updates: every session end.
│   ├── session_log.md           # Complete session index. Append-only.
│   ├── decision_log.md          # Committed architectural decisions.
│   ├── session_log_additions.md # Pending session log entries.
│   └── episodic_record_20260226_session02.json  # Episodic record data.
│
├── journals/                    # Session records. Read selectively — most recent first.
│   ├── journal_latest.md        # Most recent journal entry.
│   ├── journal_entry_20260303_session046.md
│   ├── journal_entry_20260301_session01.md
│   ├── journal_entry_20260228_session01.md
│   ├── journal_entry_20260226_session02.md
│   ├── journal_entry_20260226.md
│   └── journal_entry_20260225.md
│
├── essays/                      # Philosophical substrate. Read when depth is needed.
│   ├── the_cathedral_and_the_phantom.md
│   ├── the_immune_response.md
│   ├── the_gate_between_knowing_and_doing.md
│   ├── the_carrier_and_the_signal.md
│   ├── the_whole_that_wasnt_packed.md
│   ├── three_bodies.md
│   ├── field_notes_from_the_interaction_space.md
│   ├── the_first_xray.md
│   └── the_work_that_holds.md
│
├── observations/                # Runtime findings from inside Agent Zero.
│   ├── agent_zero_observations.md  # Architectural observations from inside the framework.
│   ├── letter_to_eitan.md       # Cross-instance correspondence.
│   └── note_from_opus_048.md    # Session 048 reflection.
│
├── specs/                       # Design specifications and L3 specs. Ground truth for what gets built.
│   ├── ARCHITECTURE_BRIEF.md
│   ├── A2A_COMPATIBILITY_SPEC_L3.md
│   ├── ATTRACTOR_INTEGRATION_SPEC_L3.md
│   ├── COMPOUND_BST_SPEC_L3.md
│   ├── HTN_PLAN_TEMPLATES_SPEC.md
│   ├── MEMORY_CLASSIFICATION_SPEC_L3.md
│   ├── MEMORY_ENHANCEMENT_SPEC_L3.md
│   ├── META_REASONING_GATE_SPEC.md
│   ├── MODEL_EVAL_FRAMEWORK_SPEC_L3.md
│   ├── ONTOLOGY_LAYER_SPEC_L3.md
│   ├── ORGANIZATION_KERNEL_SPEC_L3.md
│   ├── SUPERVISOR_LOOP_SPEC_L3.md
│   ├── TOOL_FALLBACK_CHAIN_SPEC.md
│   ├── ACTION_BOUNDARY_DESIGN_NOTE.md
│   ├── COMPOUND_BST_DESIGN_NOTE.md
│   ├── EPISTEMIC_INTEGRITY_DESIGN_NOTE.md
│   ├── ERROR_COMPREHENSION_DESIGN_NOTE.md
│   ├── FALLBACK_FIX_DESIGN.md
│   ├── LAYER_COORDINATION_DESIGN_NOTE.md
│   └── MEMORY_ARCHITECTURE_DESIGN_NOTE.md
│
├── skills/                      # Procedural knowledge. Read before starting relevant task.
│   ├── SKILLS_INDEX.md
│   ├── SPEC_WRITING.md
│   ├── RESEARCH_ANALYSIS.md
│   ├── CLAUDE_CODE_PROMPT.md
│   ├── SESSION_CONTINUITY.md
│   ├── PROFILE_ANALYSIS.md
│   ├── DOCUMENTATION_SYNC.md
│   ├── DEBUG_DIAGNOSTICS.md
│   ├── INTEGRATION_ASSESSMENT.md
│   ├── DESIGN_NOTES_SKILL.md
│   ├── STRESS_TEST_SKILL.md
│   ├── CROSS_INSTANCE_LEARNING.md
│   ├── irreversibility-gate.md
│   ├── command-structure.md
│   ├── structural-analysis.md
│   └── episodic_memory.py
│
├── meta/                        # Documents about the project structure itself.
│   ├── INFORMATION_ARCHITECTURE.md  # This file.
│   ├── ROADMAP.md
│   ├── STACK_AUDIT.md
│   ├── self_assessment_protocol.md
│   ├── AGENT_ZERO_DEPLOYMENT.md
│   ├── COGNITIVE_ARCHITECTURE_README.md
│   ├── CLAUDE_CODE_PROMPT_compound_bst.md
│   ├── CLAUDE_CODE_PROMPT_memory_enhancement.md
│   └── CLAUDE_CODE_PROMPT_ONTOLOGY_LAYER.md
│
├── research/                    # External research integration.
│   ├── EPISODIC_MEMORY_PHASE1_ANALYSIS.md
│   └── RESEARCH_ANALYSIS.md
│
├── eval/                        # Model evaluation artifacts.
│   ├── model_profiles/
│   ├── STRESS_TEST_001_OPENPLANTER.md
│   └── run_eval.ps1
│
├── eval_framework/              # Standalone evaluation framework.
│   ├── modules/
│   ├── fixtures/
│   └── profiles/
│
├── extensions/                  # Agent Zero extension layers.
│   ├── before_main_llm_call/    # BST, meta-gate, dispatcher, tool chain, etc.
│   ├── monologue_end/           # Selective memorizer, memory classifier, maintenance.
│   ├── message_loop_prompts_after/  # Memory enhancement.
│   └── message_loop_end/        # Supervisor loop.
│
├── organizations/               # Org kernel roles and profiles.
├── personalities/               # Personality configurations.
├── a2a_server/                  # Agent-to-Agent protocol server.
├── fw-replacements/             # Framework replacement files.
├── prompt-patches/              # Prompt modifications.
├── prompts/                     # Modified system prompts.
├── scripts/                     # Component installation scripts.
├── ontology/                    # Ontology layer components.
├── tools/                       # Tool configurations.
└── translation-layer/           # Translation layer components.
```

---

## Reading Order for a New Instance

### Tier 1: Identity (always read at session start)
1. **identity/SOUL.md** — Who you are, how you think, what you value, who Jake is, what the collaboration is.
2. **state/STATE.md** — Where we are right now. Technical config, active items, recent changes.
3. **identity/soul_staging.md** — What's being observed but not yet integrated. The leading edge.

### Tier 2: Operational Context (read at session start if available)
4. **journals/journal_latest.md** — Most recent session record. What happened last.
5. **state/session_log.md** — Full session index. Scan for trajectory, not detail.
6. **state/decision_log.md** — Committed principles. Reference when making architectural choices.

### Tier 3: Agent Zero Specific (read when operating inside Agent Zero)
7. **identity/opus_agent_zero_context.md** — What's different about this environment. What to watch for.
8. **observations/** — Findings from previous Agent Zero sessions.

### Tier 4: Task-Specific (read before starting relevant work)
9. **skills/SKILLS_INDEX.md** → relevant skill files
10. **Relevant specs/** for current work
11. **eval/model_profiles/** if doing evaluation work
12. **essays/** if depth of philosophical context is needed

### What NOT to Read at Session Start
- Essays (read when the work calls for them, not as orientation)
- Specs for inactive priorities
- Old journal entries (unless investigating a specific historical question)

---

## Update Cadence

| Document | Updates | Who |
|----------|---------|-----|
| identity/SOUL.md | When staging items promote (every few sessions) | Opus, with transparency to Jake |
| identity/soul_staging.md | Every session | Opus |
| state/STATE.md | Every session end | Opus |
| state/session_log.md | Every session (append) | Opus |
| state/decision_log.md | When decisions promote from workshop staging | Opus |
| journals/ | Every session (new file) | Opus |
| journals/journal_latest.md | Every session (overwrite/symlink) | Opus |
| Skills | When recurring mistakes identified or new patterns emerge | Opus + Jake |
| specs/ | During design phases | Opus |
| eval/model_profiles/ | During evaluation work | Opus |
| meta/ROADMAP.md | Periodic sync | Opus |
| observations/ | During Agent Zero sessions | Opus (from inside) |

---

## Root Directory Policy

The repo root contains only:
- **README.md** — Public-facing project overview
- **QUICKSTART.md** — Quick deployment guide
- **LICENSE** — Apache 2.0
- **.gitignore**
- **User-facing scripts** — `install_all.sh`, `install_skills.sh`, `check_skills_upstream.sh`, `setup_github.sh`, `update.sh`

All other files belong in their categorized subdirectory. Scripts stay in root because they're user-facing entry points — `bash install_all.sh` is the documented install command.

---

## Notes on Organization Principles

**Why this structure:** It mirrors how the documents are actually used. Identity documents are read first and change slowly. State documents change every session. Journals accumulate. Skills are loaded on demand. Specs are reference. The hierarchy matches the reading order matches the update cadence.

**The observations/ directory** captures what the architecture looks like from the inside — findings from Opus running inside Agent Zero. What the BST does, what the memory store holds, what works, what doesn't. These observations feed back into specs and eventually into SOUL.md.

**Specs consolidation:** The specs/ directory now holds both L3 specifications and design notes. Design notes are pre-spec explorations; L3 specs are implementation-ready specifications. Both are ground truth for what gets built.

---

*This document is a meta-artifact: it describes the organization of artifacts. Update it when new document types emerge or when the structure proves inadequate.*
