# Install Pipeline Write Manifest

**For:** Opus — the design artifact requested before the Tier 1.1 surgical strip
**By:** Kestrel · 2026-08-19
**Instrument:** `scripts/audit_install_writes.sh`
**Raw output:** reproducible in-container at `/tmp/write_audit.txt`

---

## How this was produced

Measured, not grepped. The install scripts resolve destinations through variables
(`$TARGET_ROOT`, `$EXT_DEST`, `$PLUGIN_BASE`…), so static analysis of literal paths
under-reports. Method:

1. Clean container, A0 checked out to **v2.9**.
2. **`supervisorctl stop run_ui`** — a running A0 writes logs, memory and cycle state
   continuously and would contaminate every measurement. Verified quiet before starting.
3. `install_all.sh`'s **docker shim** replicated, so child scripts using `docker cp`
   behave exactly as they do in a real in-container install.
4. Per step: marker → run → record every file written → classify.

### Three instrument corrections before this manifest was trusted

Each produced a confident, wrong manifest. Recording them because the same traps apply
to anyone re-running this:

| Fault | Symptom | Fix |
|---|---|---|
| No docker shim | Every `docker cp` step exited **127**; manifest showed almost no legacy writes | Replicate `install_all.sh`'s shim |
| `find -newer` (mtime) | The shim copies with `cp -p`, which **preserves source mtime**, so deployed files are invisible to mtime. Missed **54 real writes** | `find -newercm` — ctime cannot be preserved by `-p` |
| `-newerct` | Takes a *timestamp string*, not a file; silently parsed nothing | `-newercm` (file ctime vs reference mtime) |

**Cross-check against reality after correction** — audit write counts vs files on disk:
`no-underscore` 55 vs 54 · `_exocortex` 184 vs 183 · `a0-python` 29 vs 27 ·
`profile-ext` 114 writes vs 82 files. Counts exceeding file counts are *multiple steps
writing the same path* — itself a finding (duplicate deploys).

---

## Totals

| Class | Files | Verdict |
|---|---:|---|
| `PLUGIN:walk-covers` — `/a0/usr/plugins/_exocortex/` | 184 | Authoritative; the walk owns this |
| `LEGACY:profile-ext` — `/a0/usr/agents/agent0/extensions/` | 114 | **STRIP** — loads, and resurrects retired extensions |
| `LEGACY:no-underscore` — `/a0/usr/plugins/exocortex/` | 55 | **STRIP** — wrong plugin name |
| `LEGACY:a0-python` — `/a0/python/` | 29 | **STRIP** — absent in v2.9; the installer creates it |
| `LEGACY:profile-other` — `/a0/usr/agents/agent0/{tools,plugins}` | 25 | **STRIP** |
| `OUTSIDE:keep` | 206 | **KEEP** — must survive |

---

## A. Fully redundant — every write lands in a legacy path

Nothing outside the plugin. These can be retired outright once the walk is authoritative.

| Script | Writes to |
|---|---|
| `extensions/install_extensions.sh` | profile-ext (12 dirs, incl. `.hardening_originals`) |
| `extensions/install_failure_tracker.sh` | `/a0/python/extensions/{error_format,tool_execute_after}` |
| `scripts/install_error_comprehension.sh` | `/a0/python/extensions/{tool_execute_after,tool_execute_before}` |
| `scripts/install_exocortex_profile.sh` | no-underscore (8 dirs) + profile-ext (11) + profile-other (2) |
| `scripts/install_graph_engine.sh` | `/a0/python/extensions/before_main_llm_call` |
| `scripts/install_metacognitive_injection.sh` | `/a0/python/extensions/before_main_llm_call` |
| `scripts/install_meta_gate.sh` | `/a0/python/extensions/tool_execute_before` |
| `scripts/install_supervisor_loop.sh` | `/a0/python/extensions/message_loop_end` |
| `scripts/install_write_guard.sh` | profile-ext `{tool_execute_after,tool_execute_before}` |

> `scripts/install_exocortex_plugin.sh` also appears in the tool's "only legacy/plugin"
> bucket. That is a classification artifact — it writes only `PLUGIN`, because it *is*
> the authoritative deploy. Do not retire it.

---

## B. Mixed — strip the legacy writes, KEEP these

This is the load-bearing half. Every path below must still be deployed after the strip.

| Script | **KEEP** (outside) | Strip (legacy) |
|---|---|---|
| `fw-replacements/install_fw_replacements.sh` | `/a0/prompts`, `/a0/prompts/.fw_originals` | — |
| `prompt-patches/install_prompt_patches.sh` | `/a0/prompts`, `.prompt_patch_originals` | — |
| `scripts/install_personalities.sh` | `/a0/prompts`, `.prompt_patch_originals` | — |
| `scripts/install_communication_protocol.sh` | `/a0/prompts`, `.prompt_patch_originals` | — |
| `install_skills.sh` | `/a0/usr/skills/**` (26 skill dirs) | — |
| `scripts/install_core_patches.sh` | `/a0/api`, `/a0/helpers`, `/a0/plugins/_memory/helpers`, `/a0/prompts`, `/a0/webui/components/messages/process-group` | no-underscore ×3, profile-ext ×1 |
| `scripts/install_a2a_server.sh` | `/a0/usr/organizations` | `/a0/python/a2a_server` |
| `scripts/install_action_boundary.sh` | `/a0/usr/Exocortex` | `/a0/python/extensions/tool_execute_before` |
| `scripts/install_org_kernel.sh` | `/a0/usr/organizations`, `/a0/usr/organizations/roles` | `/a0/python/extensions/before_main_llm_call` |
| `scripts/install_ontology.sh` | `/a0/tools`, `/a0/usr/ontology`, `/a0/usr/ontology/connectors`, `/a0/usr/organizations/roles` | — |
| `scripts/install_memory_classification.sh` | `/a0/usr/extensions/{message_loop_prompts_after,monologue_end}` | — |
| `scripts/install_sleep_consolidation.sh` | `/a0/usr/Exocortex` | `/a0/python/extensions/{before_main_llm_call,tool_execute_after}` |
| `scripts/install_library.sh` | `/a0/usr/Exocortex`, `/a0/usr/workdir/library` | `/a0/python/tools`, profile-ext, profile-other |
| `scripts/install_agentevolver.sh` | `/a0/usr/plugins/agentevolver_self_improvement/**` (5 dirs) | — |
| `scripts/install_artifact_system.sh` | `/a0/usr/artifact_templates`, `/themes` | `/a0/usr/plugins/exocortex/tools` |
| `scripts/install_idle_engine.sh` | `/a0/api`, `/a0/webui`, `/a0/usr/Exocortex/{,office,prompts,self-improvement}`, `/a0/usr/workdir/workspace/self-improvement` | no-underscore ×3, profile-ext ×1 |
| `scripts/install_theme_editor.sh` | `/a0/webui`, `/a0/webui/js` | `/a0/python/api` |
| `scripts/install_tool_fallback.sh` | `/a0/prompts` | `/a0/python/extensions/{tool_execute_after,tool_execute_before}` |
| `scripts/install_epistemic_integrity.sh` | `/a0/usr/Exocortex/eval/model_profiles` | profile-ext ×2 |
| `scripts/install_metacognitive_injection.sh` | — | `/a0/python/extensions/before_main_llm_call` |
| `translation-layer/install_translation_layer.sh` | `/a0/prompts`, `.prompt_patch_originals` | `/a0/python/extensions/before_main_llm_call` |
| `services/oss_plugin/install.sh` | `/a0/tools`, `/a0/usr/plugins/oss/**` (6 dirs) | — |
| `services/swarmfish_plugin/install.sh` | `/a0/tools`, `/a0/usr/plugins/swarmfish/**` (4 dirs) | `/a0/usr/plugins/exocortex/prompts` |
| `services/searxng/install.sh` | (config outside `/a0`) | — |

---

## Two things worth a decision

**1. `/a0/usr/extensions/` — a fourth extension root.**
`install_memory_classification.sh` writes to `/a0/usr/extensions/{message_loop_prompts_after,monologue_end}`,
which is neither the plugin nor the DEC-030 profile path. DEC-030's corrected note
called this path "valid and functional" but chose the profile path over it. It is
currently classified `OUTSIDE:keep` by the audit purely because it is not one of the
three known-legacy roots — **that is the tool being conservative, not a judgement.**
Whether it should be a fourth root or folded into the plugin is your call.

**2. `.hardening_originals` backups.**
`install_extensions.sh` writes A0-original backups under the profile path before
overwriting. If that script is retired, the backup mechanism goes with it. The walk has
no equivalent — it does not overwrite A0 files, so arguably none is needed, but it is a
capability being dropped and should be dropped deliberately.

---

## Proposed gate for the surgical pass

Beyond the existing four conditions, add a fifth that makes "did I miss one?" a
measurement rather than a judgement:

```
python scripts/verify_plugin_parity.py <container>          # 183/183
find /a0/python /a0/usr/agents/agent0/extensions \
     /a0/usr/plugins/exocortex -type f | wc -l              # must be 0
```

and re-run `scripts/audit_install_writes.sh` after the strip: **every remaining write
must classify `OUTSIDE:keep` or `PLUGIN:walk-covers`.** Zero `LEGACY:*`. That turns the
whole exercise into a diff.
