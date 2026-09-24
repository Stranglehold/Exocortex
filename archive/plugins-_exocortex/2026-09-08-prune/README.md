# Archive: the Arm M injection prune (DEC-051)

These 18 extensions and 2 data files are switched off. They lived in `plugins/_exocortex/extensions/python/<hook>/`
and were moved here on **2026-09-24 by Kestrel**, on Jake's word ("go ahead with the audit's proposed order").
This is step A1 of Fable's plan (`Fable/studies/2026-09-15-what-exocortex-is.md` §6). DEC-051 in
`state/decision_log.md` names this directory as the restore path.

## Why they moved

The plugin installer (`scripts/install_exocortex_plugin.sh`) is a directory walk: it deploys every `.py` in the
tree. While these files sat there, any routine install, onto Aporia's container or a fresh one, would have brought
them back. **11 of the 18 contain no `enabled` check**, so they would have run. The prune existed only in the
container. Audit: `Kestrel/studies/2026-09-24-exocortex-plugin-audit.md`, finding 1.

## What moved

| file (under this directory) | md5 | retired |
|---|---|---|
| `before_main_llm_call/_10_session_init.py` | `1cbb79283430ae0952dde5a552da71c9` | 2026-09-08 |
| `before_main_llm_call/_11_belief_state_tracker.py` | `6dfa7991ef64431acccb984e0661d63f` | 2026-09-08 |
| `before_main_llm_call/_12_completion_tracker.py` | `ebce546d2df5a68e3c670a284ff0ee29` | 2026-09-08 |
| `before_main_llm_call/_12_proactive_supervisor_inject.py` | `73a8639898df1eab4d3c74f4f021528d` | 2026-09-08 |
| `before_main_llm_call/_13_reasoning_state.py` | `c68aea8f5a6f899dd7a05372a364cc95` | 2026-09-08 |
| `before_main_llm_call/_14_pace_plan_generator.py` | `4a8a142c107e01352f8100fe89003e34` | 2026-09-08 |
| `before_main_llm_call/_14_situational_orientation.py` | `330099219c9472194af56e6aa9febfbe` | 2026-09-08 |
| `before_main_llm_call/_15_htn_plan_selector.py` | `c36d1f261b3a1ad073315625e91026c3` | 2026-09-08 |
| `before_main_llm_call/_15_karpathy_rules.py` | `26a901d42596341d965d52a93d40d8c4` | 2026-09-08 |
| `before_main_llm_call/_16_scope_expansion_detector.py` | `18abab009af2e29361d2b0b9950f1cd0` | 2026-09-08 |
| `before_main_llm_call/_17_library_catalog.py` | `35aa22dffbeed3facc29d56f3ea41c3a` | 2026-09-08 |
| `before_main_llm_call/slot_taxonomy.json` (data for `_11`) | `3e8411ddc9bb7a5d11026020f135d53d` | 2026-09-08 |
| `before_main_llm_call/htn_plan_library.json` (data for `_15`) | `464c7c50f19713dee6139ae08952fc6f` | 2026-09-08 |
| `message_loop_end/_49_reasoning_state_update.py` | `db9e3b980f97f6912be99c6ae3df8e6e` | 2026-09-08 |
| `message_loop_prompts_after/_08_step_budget_tracker.py` | `b659734b931baa51ffbb986cf9e711f6` | 2026-09-08 |
| `message_loop_prompts_after/_10_strategy_advisor.py` | `5a83a3699613ddc92383cada2ee317fd` | 2026-09-08 |
| `message_loop_prompts_after/_21_constraint_heartbeat.py` | `bd210ce4b4d81ba1a27f76b5b9558afa` | 2026-09-08 |
| `message_loop_prompts_after/_22_reasoning_state_injector.py` | `d7ed32fcbea8aa837345e1843db8417c` | 2026-09-08 |
| `message_loop_prompts_after/_24_skill_surfacer.py` | `6312aefe4ec2b1e162895c26fa24a721` | 2026-09-08 |
| `message_loop_prompts_after/_23_pace_plan_injector.py` | `50a0bee4cdcf03d39b58d0b8f799bf11` | 2026-09-02, separately |

These are the repo copies at commit ad09846, moved with `git mv`, so `git log --follow` carries each file's history.

## The container

On Aporia's container (`agent-zero-v2`), each file was renamed in place on its retirement date:
`<name>.PRUNED-20260908.txt`, and `_23_pace_plan_injector.RETIRED-20260902.txt`. The container also holds the
pre-prune snapshot `extensions.bak-prune-20260908-214547/`, which is not tracked here. The markers are the record
of what was switched off and when.

The same mandate on 09-08 also switched off nine A0 core and bundled-plugin injectors. Those are not in this
archive, because they are A0's files, not ours. They are re-applied after A0 updates by
`Kestrel/instruments/reprune_core_includers.py`. Jake restored three files the same day: `_60_include_current_datetime`
and `_70_include_agent_info`, which are A0's, and `_71_model_identity_verify`, which is ours and lives in the
plugin tree.

## The manifest

`scripts/retired_manifest.txt` still lists these 18 paths, and it should keep listing them. The parity gate now
reports them as retired and gone from both sides (informational). If one of them reappears in the container, that
is a resurrection, and the gate hard-fails.

## Restoring one

Removing a path from `retired_manifest.txt` means "this may deploy again". That is un-retiring, and it is Jake's
call (DEC-051, "Revisit if"). To restore a file:

1. `git mv` it back into `plugins/_exocortex/extensions/python/<hook>/`.
2. Remove its manifest line.
3. Deploy.

## Things that still point here

- `scripts/test_14_strip_injected_blocks.py` now reads `_14` from this directory.
- `scripts/test_24_skill_surfacer_scope.py` and `scripts/test_a2_scope_integration.py` read the container path,
  which has been absent since 09-08.
- `plugins/_exocortex/extensions/python/message_loop_end/_50_supervisor_loop.py` (around L1965) loads `_14` by
  its container path inside a `try/except` that returns an empty string. That has been the live behaviour since
  09-08.
- `services/a2a_server/config.py` reads `htn_plan_library.json` from `/a0/python/...`, a path that no longer
  exists, and not from here.
