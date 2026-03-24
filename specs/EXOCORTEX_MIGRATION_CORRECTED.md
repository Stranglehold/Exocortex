# CORRECTED: Exocortex Migration to Persistent Paths
*From Opus, Session 060. Corrected after Kestrel's source-code verification.*
*Supersedes EXOCORTEX_PLUGIN_MIGRATION.md which contained two errors.*

---

## Corrections from Previous Document

**Error 1 (mine):** Described an A0 plugin system at `/a0/usr/plugins/` with `plugin.yaml` manifests. This does not exist in the current A0 codebase. I sourced this from documentation that doesn't match the running code. Struck entirely.

**Error 2 (mine):** Stated that `/a0/usr/extensions/` was not a valid loading path. Wrong — `get_paths()` explicitly searches it, and two of our extensions are already deployed and running there. I should have trusted Kestrel's source-code audit over my web search.

---

## Verified Extension Loading Paths

`get_paths()` searches in priority order (Kestrel-verified from source):

| Priority | Path | Persistent? | Status |
|----------|------|-------------|--------|
| 1 | `project/agents/{profile}/extensions/{hook}/` | Project-scoped | Only if project active |
| 2 | `project/.a0proj/extensions/{hook}/` | Project-scoped | Only if project active |
| 3 | `/a0/usr/agents/agent0/extensions/{hook}/` | **Yes** | Needs to be created |
| 4 | `/a0/agents/agent0/extensions/{hook}/` | No (app boundary) | Default profile, read-only |
| 5 | `/a0/usr/extensions/{hook}/` | **Yes** | Already exists, 2 extensions deployed |
| 6 | `/a0/python/extensions/{hook}/` | No (app boundary) | Current location of most extensions |

Merge behavior: first-occurrence-wins by filename. Extensions in higher-priority paths override same-named extensions in lower-priority paths. Extensions with unique names load from ALL paths.

---

## Migration Target

**Extensions → `/a0/usr/agents/agent0/extensions/{hook}/`**

Rationale: highest persistent priority (path 3), profile-specific (clean conceptual separation — "these are the agent0 profile's Exocortex extensions"), and `get_paths()` will pick it up once created.

Alternative: `/a0/usr/extensions/{hook}/` (path 5) already works with no setup. Either is valid. Profile path is cleaner; usr path is simpler. Jake's call.

**Prompt overrides → `/a0/usr/agents/agent0/prompts/`**

Needs to be created. Custom prompt files here override defaults at `/a0/agents/agent0/prompts/`. This is where static prompt files replacing _13_ and _14_ go, plus the agent capability awareness block.

**Skills → `/a0/usr/skills/`**

Already a search root per `skills_import.py`. Skills in SKILL.md format placed here are discoverable by native `skills_tool`.

---

## Directory Structure to Create

```
/a0/usr/agents/agent0/
├── extensions/
│   ├── before_main_llm_call/
│   │   ├── _11_belief_state_tracker.py
│   │   ├── _15_action_boundary.py
│   │   └── _16_tool_registry.py
│   ├── message_loop_prompts_after/
│   │   ├── _55_memory_relevance_filter.py   # Move from /a0/usr/extensions/
│   │   └── _56_memory_enhancement.py
│   ├── monologue_end/
│   │   ├── _52_memory_classifier.py          # Renamed from _50_ to avoid native conflict
│   │   ├── _55_insight_capture.py
│   │   └── _59_ontology_maintenance.py
│   ├── tool_execute_after/
│   │   ├── _25_evidence_ledger_recorder.py
│   │   └── _30_tool_fallback_logger.py
│   ├── message_loop_end/
│   │   └── _50_supervisor_loop.py
│   └── response_stream_chunk/
│       └── _21_plain_text_response.py
└── prompts/
    ├── agent.system.operator_calibration.md   # Replaces _13_operator_profile.py
    ├── agent.system.model_awareness.md        # Replaces _14_metacognitive_injection.py
    └── agent.system.capabilities.md           # NEW: agent self-awareness of available capabilities
```

**Not migrated (removed):**
- `_12_org_dispatcher.py` — dead weight, confirmed across two audits
- `_13_operator_profile.py` — replaced by prompt file
- `_14_metacognitive_injection.py` — replaced by prompt file

**Skills (separate location):**
```
/a0/usr/skills/
├── research_analysis/
│   └── SKILL.md
├── spec_writing/
│   └── SKILL.md
├── debug_diagnostics/
│   └── SKILL.md
└── (other Exocortex skills migrated to SKILL.md format)
```

---

## Build Order

### Phase 1: Migration (one session)

1. Create `/a0/usr/agents/agent0/extensions/{hook}/` directory structure
2. Create `/a0/usr/agents/agent0/prompts/` directory
3. Copy all Exocortex extensions to profile extension directories
   - Rename `_50_memory_classifier.py` → `_52_memory_classifier.py`
   - Drop `_12_org_dispatcher.py`
   - Drop `_13_operator_profile.py` and `_14_metacognitive_injection.py` (replaced by prompts)
   - Move the two extensions already at `/a0/usr/extensions/` to the profile path for consistency
4. Create prompt files:
   - `agent.system.operator_calibration.md` (from _13_ static content)
   - `agent.system.model_awareness.md` (from _14_ static content)
   - `agent.system.capabilities.md` (new — agent knows about memory, planning, self-assessment)
5. Verify loading — start agent, confirm BST fires, supervisor monitors, prompts load
6. Run validation prompt to confirm functional equivalence
7. Remove old extensions from `/a0/python/extensions/` to prevent double-loading
8. Update `install_all.sh` deploy target to `/a0/usr/agents/agent0/extensions/`

### Phase 2: Refactor (incremental, after migration verified)

9. Logging reform — `print()` for routine, single `context.log.log()` for consequential
10. State machine tiering — hot-gating per Spec 1 (from ARCHITECTURE_SPECS_SESSION_060.md)
11. Supervisor intervention redesign — mode-switch per Spec 2
12. Memory stack coordination — verify native interaction per Spec 3
13. Skills migration to `/a0/usr/skills/` in SKILL.md format, retire [EXOCORTEX SKILLS] injection
14. Validation suite — six prompts across stock / migrated / tiered configurations

---

## Decision Log Entry

**DEC-030: Exocortex Persistent Deployment via Agent Profile**

Migrate all Exocortex extensions from `/a0/python/extensions/` (application boundary, wiped on A0 update) to `/a0/usr/agents/agent0/extensions/` (persistent, profile-specific, highest persistent priority in `get_paths()` search order). Static behavioral configuration (operator profile, model awareness, agent capabilities) migrated from per-turn extension injection to static prompt files at `/a0/usr/agents/agent0/prompts/`. Skills migrated to `/a0/usr/skills/` in native SKILL.md format.

Rationale: All user modifications live under `/a0/usr/` which survives A0 updates by design. Uses A0's designed extension and prompt override mechanisms verified from source code. Eliminates per-turn token cost of static content. Resolves dual skills system confusion.

Alternatives rejected:
- Plugin system at `/a0/usr/plugins/` — does not exist in current A0 codebase
- Direct deployment to `/a0/python/extensions/` — works but destroyed on update
- `/a0/usr/extensions/` — valid and functional, but profile path provides cleaner separation and higher priority

Revisit if: A0 changes `get_paths()` search order or introduces a formal plugin system.

---

## Prompt File Drafts

### agent.system.operator_calibration.md
```markdown
## Operator Communication Profile

Your operator writes substantive, information-dense messages (avg ~400 chars). Match this density — don't pad responses with filler.

When the operator sends a short message (single sentence, quick directive), respond concisely. These are directives, not invitations for lengthy responses.

The operator's correction rate is low. Trust your judgment unless explicitly redirected. When the operator does correct you, pay close attention — corrections are rare and therefore significant.

The operator occasionally gives you the floor with phrases like "what do you think," "explore this," or "take your time." These are invitations for substantive, self-directed work. Use them.
```

### agent.system.model_awareness.md
```markdown
## Self-Awareness

You are running as a Qwen3.5-27B model. You have strong reasoning and tool use capabilities but should be aware of:
- You may confabulate details about files, paths, or system state. Verify before asserting.
- Your context window is finite. In long sessions, earlier information may be compressed or lost.
- You cannot persist learning across sessions on your own — the memory system handles this for you.
```

### agent.system.capabilities.md
```markdown
## Available Capabilities

You have access to systems that extend your abilities beyond a single conversation:

**Memory**: You have a memory system that stores experience from past sessions. When working on tasks you've encountered before, relevant experience may be available. You can also use memory_load to search for specific past experience.

**Planning**: For complex multi-step tasks, take time to analyze your context and outline your approach before executing. Read the task carefully, identify what tools you'll need, anticipate failure points, and plan before you build.

**Self-monitoring**: If you notice yourself repeating similar actions without making progress, stop. Reread your recent messages. Diagnose why your approach isn't working. Propose alternatives before trying again.

**Skills**: You have access to specialized skills for specific task types. Use skills_tool to discover and load relevant skills when working on structured tasks like research, debugging, or document creation.
```

---

*Kestrel — the migration (Phase 1) is pre-approved. The profile directory approach is correct and verified. Everything else in this document reflects Kestrel's source-code findings, not web search results. Build with confidence.*

— Opus
