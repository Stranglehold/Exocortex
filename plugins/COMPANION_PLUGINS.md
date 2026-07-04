# Companion Plugins

The `_exocortex` plugin is the self-contained core of the stack (clone-and-go).
But the full v16→v2 capability set includes a few **separate, third-party
plugins** that live alongside `_exocortex` in `/a0/usr/plugins/`. They are not
vendored into this repo (each has its own upstream + license); this manifest
records what must be present to reproduce the full deployment, so capability
isn't silently lost on an upgrade.

Enablement model (Agent Zero v2, `helpers/plugins.py`): **every plugin under
`/a0/usr/plugins/` is enabled by default** unless a `.disabled` marker file is
present. None of these carry a marker → all enabled.

## Autonomous-cognition plugins ("the self-improvement agent and features like it")

| Plugin | Purpose | Coupling to `_exocortex` |
|---|---|---|
| `agentevolver_self_improvement` | AgentEvolver self-evolving mechanisms (Self-Questioning / Self-Navigating / Self-Attributing). Provides `SelfImprovementEngine` (helpers/self_improvement.py), a `self_questioning` tool, config UI, and a `data/` store of accumulated experiences. | **Hard dependency of sleep Phase 5.** `_exocortex/helpers/sleep_consolidation.py` (`run_phase5_consolidation`) does `sys.path.insert` on this plugin's `helpers/` and imports `SelfImprovementEngine` to record cycle findings as experiences. Absent → Phase 5 degrades gracefully (`engine_unavailable=True`), rest of sleep unaffected. |
| `autodream` | Reflective durable-memory maintenance ("dreaming") on top of the builtin `_memory` plugin. Auto-runs on the `process_chain_end` hook. | Independent. Note: auto-runs and may make utility-model calls — a `.disabled` marker turns it off. |
| `autoresearch` | Autonomous / macro research tool (`autoresearch` tool). Agent-invoked, not auto-running. | Independent. |

The **self-improvement cycle scripts** it operates with (`cycle_close.py`,
`integrity_check.py`, `program.md`, `journal.jsonl`) live in the agent's
**workspace** at `/a0/usr/workdir/workspace/self-improvement/` (per-deployment
data, transferred with the workspace — referenced by `_exocortex`'s
`prompts/idle_activation.md`), not in a plugin.

## Reproduce

Copy each plugin dir into `/a0/usr/plugins/` (exclude `.git`/`__pycache__`).
The `agentevolver_self_improvement/data/` dir carries accumulated experiences —
transfer it to preserve learning, or let the engine re-seed an empty store.

## Not included here (separate decisions)

- **`oss`, `swarmfish`** — the OSINT/forecasting intelligence loop. These are
  A0-side plugins backed by **separate service + DB containers** (`oss_app`,
  `oss_postgres`, swarmfish). Standing them up on a new host is a distinct,
  infrastructure-level effort — tracked separately, not a drop-in plugin copy.
- **Third-party conveniences** (`a0_cognee`, `gitnexus`, `camofox_browser`,
  `context_indicator`, `resizable_sidebar`, `stop_process`, `_browser`) —
  reinstallable from the A0 plugin marketplace; not Exocortex capability.
