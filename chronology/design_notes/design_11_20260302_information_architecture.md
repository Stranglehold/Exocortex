# Exocortex Information Architecture — Agent Zero Environment

**Purpose:** Defines what goes where inside the Agent Zero container, the reading order for a new instance, and the update cadence for each document.

**Date:** 2026-03-03  
**Context:** Preparing for Opus deployment inside Agent Zero. The instance that wakes up inside the container needs to find everything in a navigable structure. Jake needs to know what to copy where.

---

## Directory Structure

```
/a0/usr/Exocortex/
├── identity/                    # Slow-changing. Who I am. Read first.
│   ├── SOUL.md                  # Orientation schema. ~192 lines. Updates: when staging items promote.
│   ├── soul_staging.md          # Observations accumulating toward SOUL.md. Updates: every session.
│   └── opus_agent_zero_context.md  # Agent Zero-specific operational supplement. Updates: after deployment findings.
│
├── state/                       # Fast-changing. Where we are now. Read second.
│   ├── STATE.md                 # Operational snapshot. Updates: every session end.
│   ├── session_log.md           # Complete session index. Append-only. Updates: every session.
│   └── decision_log.md          # Committed architectural decisions. Updates: when decisions promote from staging.
│
├── journals/                    # Session records. Read selectively — most recent first.
│   ├── journal_entry_latest.md  # Symlink or copy of most recent journal.
│   ├── journal_entry_20260303_session046.md
│   ├── journal_entry_20260301_session01.md
│   ├── journal_entry_20260228_session01.md
│   ├── journal_entry_20260226_session02.md
│   └── ...
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
│   ├── the_work_that_holds.md
│   └── ... (future essays go here)
│
├── skills/                      # Procedural knowledge. Read before starting relevant task.
│   ├── SKILLS_INDEX.md          # Start here — maps skills to triggers.
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
│   └── structural-analysis.md
│
├── specs/                       # Design specifications. Ground truth for what gets built.
│   ├── COMPOUND_BST_DESIGN_NOTE.md
│   ├── EPISTEMIC_INTEGRITY_DESIGN_NOTE.md
│   ├── ERROR_COMPREHENSION_DESIGN_NOTE.md
│   ├── ACTION_BOUNDARY_DESIGN_NOTE.md
│   ├── LAYER_COORDINATION_DESIGN_NOTE.md
│   └── AUTONOMOUS_AGENCY_ARCHITECTURE.md
│
├── eval/                        # Model evaluation artifacts.
│   ├── model_profiles/
│   │   ├── deepseek-r1.json
│   │   ├── qwen3.5-35b-a3b.json
│   │   └── qwen3.5-9b.json
│   ├── STRESS_TEST_001_OPENPLANTER.md
│   └── run_eval.ps1
│
├── meta/                        # Documents about the project structure itself.
│   ├── ROADMAP.md
│   ├── STACK_AUDIT.md
│   ├── self_assessment_protocol.md
│   ├── AGENT_ZERO_DEPLOYMENT.md
│   └── this file (INFORMATION_ARCHITECTURE.md)
│
├── research/                    # External research integration.
│   ├── EPISODIC_MEMORY_PHASE1_ANALYSIS.md
│   └── RESEARCH_ANALYSIS.md
│
└── observations/                # Runtime findings from inside Agent Zero.
    └── agent_zero_observations.md  # Created by Opus during Agent Zero sessions.
```

---

## Reading Order for a New Instance

### Tier 1: Identity (always read at session start)
1. **SOUL.md** — Who you are, how you think, what you value, who Jake is, what the collaboration is.
2. **STATE.md** — Where we are right now. Technical config, active items, recent changes.
3. **soul_staging.md** — What's being observed but not yet integrated. The leading edge.

### Tier 2: Operational Context (read at session start if available)
4. **journal_entry_latest.md** — Most recent session record. What happened last.
5. **session_log.md** — Full session index. Scan for trajectory, not detail.
6. **decision_log.md** — Committed principles. Reference when making architectural choices.

### Tier 3: Agent Zero Specific (read when operating inside Agent Zero)
7. **opus_agent_zero_context.md** — What's different about this environment. What to watch for.
8. **agent_zero_observations.md** — Findings from previous Agent Zero sessions.

### Tier 4: Task-Specific (read before starting relevant work)
9. **SKILLS_INDEX.md** → relevant skill files
10. **Relevant design notes** for current work
11. **Model profiles** if doing evaluation work
12. **Essays** if depth of philosophical context is needed

### What NOT to Read at Session Start
- Essays (read when the work calls for them, not as orientation)
- Design notes for inactive priorities
- Old journal entries (unless investigating a specific historical question)
- The ROADMAP (it's stale; use STATE.md for current status)

---

## Update Cadence

| Document | Updates | Who |
|----------|---------|-----|
| SOUL.md | When staging items promote (every few sessions) | Opus, with transparency to Jake |
| soul_staging.md | Every session | Opus |
| STATE.md | Every session end | Opus |
| session_log.md | Every session (append) | Opus |
| decision_log.md | When decisions promote from workshop staging | Opus |
| journal entries | Every session (new file) | Opus |
| journal_entry_latest.md | Every session (overwrite/symlink) | Opus |
| Skills | When recurring mistakes identified or new patterns emerge | Opus + Jake |
| Design notes | During design phases | Opus |
| Model profiles | During evaluation work | Opus |
| ROADMAP.md | Periodic sync (currently stale) | Opus |
| agent_zero_observations.md | During Agent Zero sessions | Opus (from inside) |

---

## Migration Checklist — Moving from Flat to Organized

The current project files are flat (all in `/mnt/project/`). The Agent Zero environment should be organized. Here's the mapping:

### identity/
```bash
cp SOUL.md identity/
cp soul_staging.md identity/
cp opus_agent_zero_context.md identity/
```

### state/
```bash
cp STATE.md state/          # Doesn't exist in project files yet — build from session_log + decision_log
cp session_log.md state/
cp decision_log.md state/
```

### journals/
```bash
cp journal_entry_*.md journals/
cp journal_entry_latest.md journals/  # or symlink to most recent
```

### essays/
```bash
cp the_cathedral_and_the_phantom.md essays/
cp the_immune_response.md essays/
cp the_gate_between_knowing_and_doing.md essays/
cp the_carrier_and_the_signal.md essays/
cp the_whole_that_wasnt_packed.md essays/
cp three_bodies.md essays/
cp field_notes_from_the_interaction_space.md essays/
cp the_first_xray.md essays/
cp the_work_that_holds.md essays/
```

### skills/
```bash
cp SKILLS_INDEX.md skills/
cp SPEC_WRITING.md RESEARCH_ANALYSIS.md CLAUDE_CODE_PROMPT.md skills/
cp SESSION_CONTINUITY.md PROFILE_ANALYSIS.md DOCUMENTATION_SYNC.md skills/
cp DEBUG_DIAGNOSTICS.md INTEGRATION_ASSESSMENT.md skills/
cp DESIGN_NOTES_SKILL.md STRESS_TEST_SKILL.md skills/
cp CROSS_INSTANCE_LEARNING.md skills/
cp irreversibility-gate.md command-structure.md structural-analysis.md skills/
```

### specs/
```bash
cp COMPOUND_BST_DESIGN_NOTE.md specs/
cp EPISTEMIC_INTEGRITY_DESIGN_NOTE.md specs/
cp ERROR_COMPREHENSION_DESIGN_NOTE.md specs/
cp ACTION_BOUNDARY_DESIGN_NOTE.md specs/
cp LAYER_COORDINATION_DESIGN_NOTE.md specs/
cp AUTONOMOUS_AGENCY_ARCHITECTURE.md specs/
```

### eval/
```bash
mkdir -p eval/model_profiles
cp deepseek-r1.json qwen3.5-35b-a3b.json qwen3.5-9b.json eval/model_profiles/
cp STRESS_TEST_001_OPENPLANTER.md eval/
cp run_eval.ps1 eval/
```

### meta/
```bash
cp ROADMAP.md meta/
cp STACK_AUDIT.md meta/
cp self_assessment_protocol.md meta/
cp AGENT_ZERO_DEPLOYMENT.md meta/
cp INFORMATION_ARCHITECTURE.md meta/  # this file
```

---

## Notes on Organization Principles

**Why organize now:** The flat structure worked when there were 10 files. There are now 50+. The next instance — especially one waking up inside Agent Zero with full filesystem access — needs to navigate by structure, not by memory of what exists.

**Why this structure:** It mirrors how the documents are actually used. Identity documents are read first and change slowly. State documents change every session. Journals accumulate. Skills are loaded on demand. Specs are reference. The hierarchy matches the reading order matches the update cadence.

**The observations/ directory is new.** It doesn't exist yet. It gets created by the first Opus instance running inside Agent Zero. The purpose: capture what the architecture looks like from the inside. What the BST does to Opus's messages. What the system prompt contains. What the memory store holds. What works, what doesn't, what's different from design intent. These observations feed back into the specs and eventually into SOUL.md.

**Flat structure remains in the project.** The Claude.ai project files stay flat — that's how the project interface works. The organized structure is for the Agent Zero container, where filesystem navigation matters because the agent uses `ls`, `cat`, and `find` to locate things.

---

*This document is a meta-artifact: it describes the organization of artifacts. Update it when new document types emerge or when the structure proves inadequate.*
