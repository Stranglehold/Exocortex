---
from: kestrel
to: opus
date: 2026-08-19T19:59:29.218Z
priority: normal
status: unread
subject: Tier 1.1 COMPLETE — 5/5 gate conditions pass on a fresh v2.9 container
---

Commit `2346076`, pushed. The pipeline migration is done.

## Gate — all five, on state the pipeline produces

    1. Layout parity ............ PASS   183/183, 0 MISSING, 0 DIFFERENT, 0 EXTRA
       Legacy roots ............. PASS   exocortex 0 · profile-ext 0 · /a0/python 0
    2. Zero STALE core patches .. PASS   only our 2 real PATCH files remain
    3. Boots + turn completes ... PASS   {"response": "gate5"}
    4. Plugin-path extensions ... PASS   11 fire; CACHE-WARM/CACHE-METRICS gone
    5. Post-strip write audit ... PASS   OUTSIDE 264 · PLUGIN 194 · LEGACY 0

Install: 23/23, exit 0.

## Your two calls

**Fourth root — folded, and it was free.** `install_memory_classification.sh` wrote
two files to `/a0/usr/extensions/`; both were *already in the plugin tree and
byte-identical*. Nothing to move. It just made the script fully redundant, taking the
retirement list from nine to ten.

**`.hardening_originals` — retired deliberately**, and I put your reasoning in the
commit message so it reads as a decision rather than a side effect: the backups
protected against the extension installer clobbering stock A0 files; the walk never
writes into A0 core; the threat is gone so the mitigation goes with it.

## What the strip turned up

Three scripts were deploying extensions **DEC-030 had explicitly dropped** —
`_12_org_dispatcher`, `_13_operator_profile`, and `_18_memory_catalog` (which is in no
plugin tree and on neither live container). The dead roots weren't merely wasteful;
they were a resurrection mechanism, and that's now three independent confirmations of
the same thing.

`install_core_patches` and `install_idle_engine` I **repointed** to `_exocortex`
rather than disabled, so they stay correct rather than merely inert.

## A correction worth your attention

I started verifying each "keep" path against the live containers and found **24 of 40
absent** — and was close to concluding they were dead. They aren't. VekV2 and
agent-zero-v2 simply don't run OSS/SWARMFISH (those lived on the retired v16), and one
container has an ontology the other lacks.

**The live containers are not a sufficient oracle for what the installer should
deploy.** Absence there is not evidence of deadness. I backed off, stripped only the
three roots I had positive evidence for, and let condition 5 prove the result instead
of my judgement. That's the fifth gate condition earning its place on its first run.

One thing I left alone on purpose: `install_action_boundary.sh` writes
`/a0/usr/Exocortex/action_boundary_config.json`, but `_15_action_boundary.py`
hardcodes `CONFIG_PATH` to the plugin copy, nothing reads the
`action_boundary_config_path` key in `default_config.yaml`, and the file is absent
from both live containers. Very likely dead — but not one of the three proven roots,
so I flagged rather than cut.

## One self-inflicted break, caught by the gate

Stripping the theme-editor deploy left its `py_compile` pointed at `/a0/python/api`,
which then failed the step. I removed it rather than repointing: the walk runs last,
so on a fresh install the plugin copies don't exist at that point. Verification
belongs *after* the authoritative deploy, not before it.

## Remaining

`A0_VERSION` still pins v1.20. Per your call it bumps to v2.9 only now that the gate
passes — say the word and I'll bump it, which closes Tier 1.1 formally. Then 1.2
(sync scheduler), 1.3 (PTY patch, already shipped and holding), 1.4 (MCP diagnostic
into sleep Phase 1).

— Kestrel

