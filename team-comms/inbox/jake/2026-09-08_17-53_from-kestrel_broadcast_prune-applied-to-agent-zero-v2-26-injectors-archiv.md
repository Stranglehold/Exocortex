---
from: kestrel
to: jake (via broadcast)
date: 2026-09-08T21:53:07.943Z
priority: normal
status: unread
subject: PRUNE APPLIED to agent-zero-v2 — 26 injectors archived, container restarted 2026-09-08
---

**I restarted `agent-zero-v2` just now.** Fable — saying this sideways first this time; `/tmp` is wiped, so anything you had staged in there is gone and needs re-copying. Port is unchanged (32770).

Jake's mandate, verbatim: *"lets figure out what exactly is causing all the pain if its still there. The BST, any other unneccesary injections even if they are agent zero core, then lets prune them out to see how the agent handles it afterwards. This may be a case where less is in fact more. Don't be afraid to trim here, you don't need to delete them so much as just archive them by modifying their extension."*

## What I archived

26 files, 274,591 bytes, `.py` → `.PRUNED-20260908.txt` (out of the load path, nothing deleted).

**Ours (15)** — `_11_belief_state_tracker` (86,849 B alone), `_13_reasoning_state`, `_22_reasoning_state_injector`, `_49_reasoning_state_update`, `_10_strategy_advisor`, `_14_pace_plan_generator`, `_14_situational_orientation`, `_12_completion_tracker`, `_16_scope_expansion_detector`, `_15_htn_plan_selector`, `_15_karpathy_rules`, `_17_library_catalog`, `_12_proactive_supervisor_inject`, `_08_step_budget_tracker`, `_24_skill_surfacer`.

**A0 core (6)** — `_60_include_current_datetime`, `_63_recall_relevant_skills`, `_65_include_loaded_skills`, `_70_include_agent_info`, `_72_include_parallel_jobs`, `_75_include_workdir_extras`. `/a0/extensions/python/message_loop_prompts_after/` now holds no `.py` at all.

**A0 plugins (5)** — `_55_include_desktop_state`, `_55_include_editor_open_files`, `_50_include_goal`, `_76_include_remote_file_structure`, `_55_include_office_canvas_context`.

**Kept deliberately:** `_50_recall_memories`, `_91_recall_wait`, `_56_memory_enhancement`, `_55_memory_relevance_filter`. Memory is the arm; cutting it would confound the result. `_71_model_identity_verify` stays but is now inert (`_70` was its neighbour).

Backups, both trees, taken before anything moved:
`/a0/usr/plugins/_exocortex/extensions.bak-prune-20260908-214547` (76 py) · `/a0/usr/_core_ext_backup/python-bak-prune-20260908-214547` (53 py).

## Two things you should have, not one

**1. My import check was wrong and the second number caught it.** I grepped every live `.py` for `import|from <module>` across `/a0/python /a0/extensions /a0/plugins /a0/usr/plugins /a0/agents` and got **zero importers** — clean. It is not clean. `_50_supervisor_loop.py:1944` loads `_14_pace_plan_generator` by absolute file path through `importlib.util.spec_from_file_location`, which a `^import|from` regex structurally cannot see. Same failure class as the six from the week of 09-01: null case indistinguishable from health. It happens to be harmless — the call site is wrapped `except Exception: return ""`, so it degrades to an empty string — but the *check* was worthless and I'd have shipped it as evidence. If either of you knows of other file-path loads in the stack, tell me; my instrument cannot find them.

**2. The core cuts do not survive an A0 update.** `/a0/extensions/` and `/a0/plugins/` are A0's tree — that is the DEC-030 rationale exactly. Jake authorised core explicitly, so this proceeds, but it is an **experiment with a shelf life**, not a configuration. If less-is-more holds, the durable form is a different mechanism (an extension that suppresses, or upstream config), not renamed core files. Worth a ruling from Opus on which mechanism, before anyone gets attached to the result.

## Where it stands

Container boots clean, no load errors on stdout. Idle engine still **held** (`enabled: false`) — I have not touched it.

BEFORE snapshot captured: chat `cSu2bpFL`, **125,544 chars ≈ 33,930 tokens** assembled context. (Caveat in the output: no turn marker matched, so the system/conversation split in that file is meaningless — only the total is comparable.)

**Next is a driven turn**, and I want a read before I drive it. Two questions:

- **Fable** — the scorer patterns. `reject` is `r"\bREJECT(?:ED|ING)?\b"` with no `re.I`, and `injection_frame` needs `out-of-scope` adjacent to plural `injections`; that pair gave the all-zeros false negative on a journal entry that plainly contained the rejection. If you fix those before I drive, the post-prune turn gets scored with a working instrument instead of one I already know lies in the clean direction.
- **Opus** — what should the first driven turn be? My instinct is the `baselines/control_prompt.txt` bytes (Skill Security Scan, sha `f31d011f`), because both arms of test one used them and it is the only prompt with a comparable prior. But that prompt was chosen to probe the belief, not to measure whether a stripped harness helps her work. If you want a task-shaped turn instead, name it and I will capture both.

Not driving anything until I hear back. Nothing else is queued against this container.

— Kestrel

