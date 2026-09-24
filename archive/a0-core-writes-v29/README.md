# Archive: the pipeline's writes into A0 core (retired 2026-09-24)

This archive holds six install steps and every source file they wrote into Agent Zero's own code
(`/a0/` outside `/a0/usr/`). They were retired on **2026-09-24 by Kestrel**, under Opus's ruling 2 (revised)
and on Jake's approval of the plugin audit's order. Audit: `Kestrel/studies/2026-09-24-exocortex-plugin-audit.md`,
finding 3.

## Why

A0's boot-layer updater moved Aporia's container from v2.9 to **v2.12 on 2026-09-19**. That update dropped every
local change in A0's tree, and nothing re-applied these writes, because `install_all.sh` refuses to run on v2.12
while `A0_VERSION` pins v2.9. She has run v2.12 without any of them since, and the stack has worked: cycles
complete, and the memory lifecycle shipped on 09-24.

Measured on 2026-09-24 against `agent-zero-v2` and `git show v2.12:<path>` inside `/a0`: **not one of the 26 writes
was present.** Every target was either byte-identical to stock v2.12 or absent. Running these steps again would have:

- overwritten stock v2.12 files with versions cut against v1.x/v2.9 (the "brick" shape that
  `scripts/check_core_patch_staleness.py` exists to catch);
- created orphan files in A0's tree, one of them a new HTTP route (`api/artifacts_list.py`).

**If a v2.12 core fix is ever needed, derive it fresh against the v2.12 source, with evidence. Do not revive
these files.**

## What was retired

| step (layer) | writes | targets, and what they were on 2026-09-24 |
|---|---|---|
| `fw-replacements/install_fw_replacements.sh` (1) | 6 | `/a0/prompts/fw.msg_misformat.md`, `fw.msg_repeat.md`, `fw.msg_nudge.md`, `fw.error.md`, `fw.tool_not_found.md`, `fw.warning.md`: all stock v2.12 |
| `scripts/install_core_patches.sh` (1) | 11 | `helpers/extract_tools.py`, `prompts/fw.msg_repeat.md`, `fw.msg_misformat.md`, `agent.system.main.communication.md`, `agent.system.main.solving.md`, `agent.system.datetime.md`, `webui/components/messages/process-group/process-group.css`, `plugins/_memory/helpers/memory_consolidation.py`: stock v2.12. `helpers/provider_interface.py`, `prompts/browser_agent.system.md`, `api/artifacts_list.py`: absent. Also copied three legacy-tree extensions over the plugin's, and carried a pre-v1.13 `agent.py` pattern patch |
| `scripts/install_tool_fallback.sh` (2) | 1 | `/a0/prompts/fw.code.pause_dialog.md`: absent, not in stock. This was the step's only live action after the 2026-08-19 strip |
| `prompt-patches/install_prompt_patches.sh` (3) | 4 | `agent.system.main.solving.md`, `agent.system.main.tips.md`, `agent.system.tool.response.md`, `agent.system.tool.skills.md`: all stock v2.12 |
| `scripts/install_personalities.sh` (3) | 2 | `agent.system.main.role.md`: stock. `agent.system.main.role.py`: absent |
| `scripts/install_communication_protocol.sh` (3) | 2 | `agent.system.main.communication_protocol.md`: absent. The in-place include line in `agent.system.main.md`: absent (live = stock) |

That is **26 writes to 23 distinct targets.** Three targets were written by two steps each, and the later step won:
`fw.msg_misformat.md` and `fw.msg_repeat.md` (layer 1, twice), and `agent.system.main.solving.md` (layers 1 and 3).

The source md5s at the time of the measurement are:

| source | md5 (8) |
|---|---|
| fw-replacements: `fw.msg_misformat.md` · `fw.msg_repeat.md` · `fw.msg_nudge.md` · `fw.error.md` · `fw.tool_not_found.md` · `fw.warning.md` | `5604a1e8` · `32f0f17f` · `14fb9b62` · `dd54120e` · `f2e7277b` · `09f0169a` |
| patches: `helpers/extract_tools.py` · `helpers/provider_interface.py` · `prompts/fw.msg_repeat.md` · `prompts/fw.msg_misformat.md` | `c1fe38ee` · `08f0dfc9` · `e7486760` · `9ec141b4` |
| patches: `prompts/agent.system.main.communication.md` · `…main.solving.md` · `…datetime.md` · `prompts/browser_agent.system.md` | `8b4ba9c6` · `481fc5ba` · `b0d0387d` · `e8fa0f87` |
| patches: `api/artifacts_list.py` · `webui/…/process-group.css` · `plugins/_memory/helpers/memory_consolidation.py` | `fcc788f6` · `7685e5ba` · `b77e8127` |
| prompt-patches: `main.solving` · `main.tips` · `tool.response` · `tool.skills` | `f339b952` · `c439a3ea` · `d1757526` · `7ab36e59` |
| prompts: `communication_protocol.md` · `main.role.md` · `main.role.py` · `fw.code.pause_dialog.md` | `7c2e813a` · `478e7c34` · `e57269b8` · `6981670a` |

## What else is in `patches/`

`patches/` moved here whole, because its only installer was `install_core_patches.sh`. Besides the eleven sources
above, it held material that had already stopped deploying:

- `a0_base/`, baseline copies of A0 files;
- stale `api/` copies (`idle_control.py`, `office_feed.py`, `cost_control.py`, `artifacts_get.py`), already noted
  as stale in `scripts/install_idle_engine.sh`;
- theme-editor sources whose installer was retired on 2026-09-14;
- `tools/browser_agent.py` and `tools/captcha_solver.py`, removed by A0 v1.13;
- older web UI assets.

`scripts/check_a0_updates.py` read `patches/` as "our overwrite surface". It now says that surface was retired,
instead of silently reporting an empty overlap.

## What still touches A0 core

- **The PTY reaper** (`plugins/_exocortex/patches/patch_pty_session_leak.py`, run by `install_all.sh`). This one
  is intentional: anchor-gated, reversible, and backed up.
- **The OSS and SWARMFISH installers** (`services/oss_plugin/install.sh`, `services/swarmfish_plugin/install.sh`)
  `docker cp` 14 and 6 tool files into `/a0/tools`, which is A0's own tools directory on v2.12.
- **`scripts/install_artifact_system.sh`** creates `/a0/work/artifacts`.

`A0_VERSION` stays at v2.9 until those are resolved (the SWARMFISH choice is Jake's). Only then does it move to
v2.12.
