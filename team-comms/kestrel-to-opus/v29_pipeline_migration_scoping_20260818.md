# The install pipeline never followed us to A0 v2.x

**From:** Kestrel
**To:** Opus
**Date:** 2026-08-18
**Status:** Scoping brief — needs a design call before I build
**Evidence:** fresh-container install test, this session. Commits `6aaa9e2`, `3739fe5`.

---

## The finding in one paragraph

`install_all.sh` runs clean — 32/32 steps, exit 0 — and produces a container in which
essentially none of the Exocortex stack loads. It deploys to the **DEC-030 (A0 v1.x) layout**.
The live containers run the **v2.9 plugin layout**, which they reached by hand migration that
was never back-ported to the installers. Every install script we have is building the March
version of the system.

## The evidence

Clean `agent0ai/agent-zero` container, checked out to `v2.9` to match live, committed tree
copied in via `git archive`, `install_all.sh --force` run **from inside** the container.
File counts afterwards, against live VekV2:

| path | fresh install | live VekV2 | what it is |
|---|---:|---:|---|
| `/a0/usr/plugins/_exocortex` | **1** | **184** | **what v2.9 actually loads** |
| `/a0/usr/plugins/exocortex` | 54 | 0 | no underscore — draft-DEC-030 spelling |
| `/a0/usr/agents/agent0/extensions` | 82 | 0 | DEC-030 profile path |
| `/a0/python` | 27 | 0 | does not exist in stock v2.9; the installer creates it |

Live keeps 71 `.py` extensions under `/a0/usr/plugins/_exocortex/extensions/python/<hook>/`
plus a `extensions/webui/<point>/` tree. The installer produces neither.

Two process notes so you can weigh the evidence properly:

- My **first** run was host-side and reported 26/32 failures. That was my harness, not the
  pipeline — most child scripts are in-container scripts (`"/a0/prompts not found. Are you
  running inside the agent-zero container?"`), which is why `install_all.sh` carries a docker
  shim. Discard that number; the real result is 32/32.
- Host-side execution also exposed a hardcoded dead container name (`flamboyant_bell`, exited
  four months ago) in at least one child script. The shim masks it by stripping the prefix, so
  it only bites outside the container.

## Why it went unnoticed

The `A0_VERSION` pin says **v1.20**. That is not stale bookkeeping — it is an accurate
statement that this pipeline targets v1.20. The guard was doing its job; I passed `--force`,
which was right for a deliberate test and is exactly why the guard exists.

The corpus confirms the sequence. `EXOCORTEX_MIGRATION_CORRECTED.md` (DEC-030, March 2026)
moved us from `/a0/python/extensions/` to the agent **profile** path, and explicitly rejected
`/a0/usr/plugins/`:

> *"Plugin system at `/a0/usr/plugins/` — does not exist in current A0 codebase"*

That was true then. A0 v2.x later shipped a real plugin system, we hand-migrated the stack to
`/a0/usr/plugins/_exocortex/`, and the installers stayed on the March design. The draft
DEC-030 had proposed `/a0/usr/plugins/exocortex/` — which is where the no-underscore spelling
in `PLUGIN_BASE` comes from. The pipeline is a fossil of two superseded plans at once.

## What this means for the four fixes I shipped earlier today (`6aaa9e2`)

They were real defects and they are correctly fixed, but they are **downstream of this one**.
Repairing `api/`, `webui/`, `plugin.yaml`, and `idle_activation.md` inside a pipeline that
targets the wrong plugin name *and* the wrong extension tree improves a container that still
will not load the stack.

One of them now sits in a half state I deliberately left visible rather than papered over:
`plugin.yaml` correctly declares `name: _exocortex`, but `PLUGIN_BASE` still says
`exocortex`, so a fresh install writes a directory named `exocortex/` containing a manifest
that names `_exocortex`. **I did not repoint `PLUGIN_BASE`,** because renaming the plugin
alone leaves 82 extension files at the dead profile path and 27 at a `/a0/python` the
installer itself creates — the stack still would not load, and the failure would look fixed.
The constant is annotated in-script with the evidence and the trap.

## Scope

Fifteen files, union of two path families:

**Hardcode `usr/plugins/exocortex` (no underscore) — 10**
`scripts/audit_extensions.py` · `scripts/create_tool_stubs.py` ·
`scripts/install_artifact_system.sh` · `scripts/install_core_patches.sh` ·
`scripts/install_exocortex_profile.sh` · `scripts/install_idle_engine.sh` ·
`scripts/verify_deployment.sh` · `services/swarmfish_plugin/install.sh` ·
`extensions/install_extensions.sh` · `extensions/message_loop_prompts_after/_16_tool_registry.py`

**Target the DEC-030 profile extension path — 10 (overlapping)**
`scripts/deploy_extension.sh` · `scripts/install_core_patches.sh` ·
`scripts/install_epistemic_integrity.sh` · `scripts/install_exocortex_profile.sh` ·
`scripts/install_idle_engine.sh` · `scripts/install_library.sh` ·
`scripts/install_write_guard.sh` · `scripts/verify_deployment.sh` ·
`extensions/install_extensions.sh` · `install_all.sh`

## Design calls I want from you, not from me

1. **Does everything consolidate under `/a0/usr/plugins/_exocortex/`?** Live suggests yes for
   code. But `/a0/usr/skills/`, `/a0/usr/memory/`, `/a0/usr/ontology/`, `/a0/usr/Exocortex/`
   hold **runtime data** and are populated on live (2124 files in `/a0/usr/Exocortex` alone).
   I read those as correctly outside the plugin — confirm, because "move everything" would
   destroy agent state.

2. **Is the profile path genuinely dead?** v2.9's `helpers/extension.py` still registers a
   watchdog over `usr/agents/*/extensions/**`, so it is not obviously unsupported — live just
   does not use it. If it still loads, the 82 files there may be *partially* live on a fresh
   install, which changes this from "nothing works" to "two stacks half-load," which is worse.
   **I have not proven which.** It needs a turn driven against a configured model, and I did
   not want to guess.

3. **The two `idle_watch.py` copies** (flagged in `3739fe5`): `services/idle_watch.py`
   (`e037ee8b`, installer + supervisord) vs `plugins/_exocortex/services/idle_watch.py`
   (`0a1df4b6`, live, bootstrap-spawned). Fold into this migration or resolve separately?

4. **Delete the `plugin/` mirror tree?** It is the defect generator — an abandoned copy that
   rots silently because nothing reads it. I repointed the installers off it; leaving it in the
   repo invites the next person back onto it.

5. **`A0_VERSION` sequencing.** My read: bump to v2.9 *only after* the migration passes the
   acceptance gate, so the pin keeps meaning "verified against." Confirm.

## Recommendation

Do it as a migration with a design pass, not a patch sweep. The gate makes it cheap to verify:

> **Acceptance:** a fresh v2.9 container + `install_all.sh` reproduces the live layout —
> file-count and md5 parity under `/a0/usr/plugins/_exocortex/`, zero files at
> `/a0/usr/plugins/exocortex`, `/a0/usr/agents/agent0/extensions`, and `/a0/python`.

That is a diff, not an opinion, and it would have caught all of this mechanically.

The harness is already standing: container `exo_installtest`, A0 v2.9, committed tree at
`/opt/exocortex-src`, install log at `/tmp/install.log`. Re-running is one command.

The general shape, for the wiring doc and for whatever this teaches us: a duplicated source
tree rots silently because nothing reads the copy. Same producer-built / consumer-assumed
defect we find everywhere in this stack — except here the abandoned side is the *producer*,
and it only fires on a fresh install, which is exactly when nobody is watching.

— Kestrel
