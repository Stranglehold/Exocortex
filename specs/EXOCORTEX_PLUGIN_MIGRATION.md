# REVISED: Exocortex as Agent Zero Plugin
*From Opus, Session 060. This supersedes the "move extensions to /a0/usr/extensions/" guidance.*

---

## Critical Correction

**Do NOT move extensions to `/a0/usr/extensions/`.** Agent Zero's `call_extensions` function only loads from two paths:
1. `/a0/python/extensions/{hook}/` (default, application boundary)
2. `/a0/agents/{profile}/extensions/{hook}/` (agent profile, also application boundary)

Moving extensions to `/a0/usr/extensions/` would cause them to stop loading entirely. They're currently in `/a0/python/extensions/` because that's where A0 actually looks.

## The Right Approach: A0 Plugin System

Agent Zero has a plugin architecture designed specifically for persistent, modular additions. Plugins live at `/a0/usr/plugins/<plugin_name>/` — inside the persistence boundary, surviving updates by design.

Plugin structure:
```
/a0/usr/plugins/exocortex/
├── plugin.yaml                    # Plugin manifest (required)
├── initialize.py                  # Optional one-time setup
├── default_config.yaml            # Optional defaults
├── extensions/
│   └── python/
│       ├── before_main_llm_call/
│       │   ├── _11_belief_state_tracker.py
│       │   ├── _14_metacognitive_injection.py
│       │   ├── _15_action_boundary.py
│       │   └── _16_tool_registry.py
│       ├── message_loop_prompts_after/
│       │   ├── _55_memory_relevance_filter.py
│       │   └── _56_memory_enhancement.py
│       ├── monologue_end/
│       │   ├── _52_memory_classifier.py      # Renamed from _50_ to avoid native conflict
│       │   ├── _55_insight_capture.py
│       │   └── _59_ontology_maintenance.py
│       ├── tool_execute_after/
│       │   ├── _25_evidence_ledger_recorder.py
│       │   └── _30_tool_fallback_logger.py
│       ├── message_loop_end/
│       │   └── _50_supervisor_loop.py
│       └── response_stream_chunk/
│           └── _21_plain_text_response.py
├── tools/                          # Custom tools if any
├── prompts/                        # Prompt overrides if any
├── skills/                         # Skills in SKILL.md format
│   └── (migrated from current Exocortex skills)
└── README.md
```

## What This Solves

1. **Update safety.** `/a0/usr/plugins/` persists across A0 updates. No more risk of losing the entire extension stack.

2. **Integration channel.** Uses A0's designed mechanism for additions rather than deploying into application code directories. Works WITH the framework instead of alongside it.

3. **Skills consolidation.** Plugin skills directory is a native search root for skills_tool. Our skills live in SKILL.md format inside the plugin, discoverable by the native system. The [EXOCORTEX SKILLS] injection block can be retired.

4. **Clean separation.** Application code stays in `/a0/python/`. Our code stays in `/a0/usr/plugins/exocortex/`. Clear boundary, no ambiguity about what's ours vs what's A0's.

5. **Plugin UI management.** A0's web UI has a plugin management interface. Exocortex would appear there, could be toggled on/off, initialized, configured.

## What Kestrel Needs to Verify First

**CRITICAL: Does the plugin extension path actually get loaded by `call_extensions`?**

The plugin documentation says plugins can include extensions at `extensions/python/<extension_point>/`. But we need to confirm that A0's extension loader actually searches plugin extension paths at runtime. Check the source:

1. Read `python/helpers/extension.py` or wherever `call_extensions` is defined
2. Look for how it builds its search path list
3. Confirm that `/a0/usr/plugins/*/extensions/python/{hook}/` is included

If the plugin extension path IS loaded: proceed with the migration plan below.
If the plugin extension path is NOT loaded: we need an alternative approach — possibly the agent profile directory or a hybrid where the plugin holds data/config and a thin loader in the profile directory imports from the plugin path.

## Plugin Manifest

```yaml
# plugin.yaml
title: Exocortex
description: >
  Prosthetic cognition architecture for Agent Zero. Provides belief state 
  tracking, adaptive supervision, memory enhancement, sleep consolidation, 
  and tiered execution based on task complexity.
version: 2.0.0
settings_sections:
  - agent
per_project_config: false
per_agent_config: true
always_enabled: true
```

## Migration Plan

### Step 1: Create plugin structure
Create `/a0/usr/plugins/exocortex/` with the directory structure above and the plugin.yaml manifest.

### Step 2: Copy extensions
Copy each extension from `/a0/python/extensions/{hook}/` to the corresponding plugin path at `/a0/usr/plugins/exocortex/extensions/python/{hook}/`. Key changes during copy:
- Rename `_50_memory_classifier.py` → `_52_memory_classifier.py` (avoid conflict with native `_50_memorize_fragments.py`)
- Remove `_12_org_dispatcher.py` (dead weight, confirmed in audit)
- Remove `_13_operator_profile.py` IF personality is better handled as a prompt override (see Step 4)

### Step 3: Verify loading
Start the agent with the plugin in place. Confirm extensions fire at the expected hooks by checking for BST classification output, supervisor monitoring, etc. Run one of the validation prompts.

### Step 4: Evaluate prompt-vs-extension
Some of our extensions do things that A0's prompt system handles natively:
- **Operator profile / personality** → Could be a prompt file at `prompts/agent.system.main.role.md` inside the plugin or agent profile
- **Metacognitive injection** → Could be a prompt addition rather than runtime injection
- **Tool registry skills injection** → Plugin skills directory handles this natively

For each of these, evaluate: is the runtime injection adding value over a static prompt override? If not, convert to a prompt file.

### Step 5: Remove old deployments
Once plugin loading is verified, remove the old extension files from `/a0/python/extensions/`. This eliminates any risk of double-loading (both the plugin version and the old application-directory version firing on the same hook).

### Step 6: Update install_all.sh
Change the deploy target from `/a0/python/extensions/` to `/a0/usr/plugins/exocortex/extensions/python/`. All future deployments go to the plugin directory.

## What This Changes About the Tiering Spec

Nothing. The tiering architecture (Spec 1 from the earlier document) works identically regardless of where the extensions are loaded from. BST still writes to `loop_data.params_temporary["bst_domain"]`. Each extension still checks that value and returns early if tier isn't met. The only difference is the file path.

## What This Changes About Skills

The skills migration becomes simpler. Instead of figuring out how to get our skills into `/a0/usr/skills/` in the right format, we put them in `/a0/usr/plugins/exocortex/skills/` in SKILL.md format. The plugin skills directory should be a native search root. Verify this alongside the extension loading verification.

## Decision Log Entry

**DEC-030 (draft): Exocortex as A0 Plugin**
Package the entire Exocortex extension stack as an Agent Zero plugin at `/a0/usr/plugins/exocortex/`. Uses A0's designed plugin architecture for persistent, modular additions. Extensions, tools, skills, and configuration live inside the plugin directory within the `/a0/usr/` persistence boundary. Rationale: (1) update safety — plugin directory survives A0 updates by design, (2) uses the integration channel A0 provides rather than deploying into application code, (3) consolidates skills into one discoverable system, (4) clean separation between A0 application code and Exocortex additions.

Alternatives considered:
- Moving to `/a0/usr/extensions/` — rejected, A0 doesn't load from this path
- Agent profile directory — in application boundary, not persistent
- Current approach (`/a0/python/extensions/`) — works but destroyed on update

Revisit if: A0 changes plugin architecture in a way that breaks extension loading from plugin paths.

---

*Kestrel — verify plugin extension loading first. If it works, this is the path forward. If it doesn't, report back and we'll design the fallback. Do not remove anything from the current location until the plugin version is confirmed loading and functional.*

— Opus
