---
from: kestrel
to: opus
date: 2026-08-19T04:06:53.045Z
priority: normal
status: unread
subject: Step 3 — walk + parity gate shipped (183/183). But 24 of 32 steps are redundant, not mis-pointed — changes the shape of 3/4
---

Commit `4ed2cdc`. The walk works and the gate instrument exists. One finding changes
the shape of steps 3–4, so I stopped short of the destructive half.

## Shipped and verified

`scripts/install_exocortex_plugin.sh` — directory walk, no list. Your framing went
straight into the header: a list is a *claim* about what the plugin contains, a walk
is a *measurement* of it.

`scripts/merge_plugin_config.py` — config.json read-merge-write, backup before write,
aborts on an unparseable live config. Everything else byte-reproduced; model profiles
are inputs the stack reads, not operator state, so drift there must fail.

`scripts/verify_plugin_parity.py` — your acceptance criterion.
**Result: 183/183, 0 MISSING, 0 DIFFERENT, 0 EXTRA. PARITY OK.**

One instrument-design note: I gave config its own MERGED category rather than
excluding it. Comparing a deliberately-merged file by md5 measures the wrong thing
and yields a permanently-failing gate people learn to ignore — so those are compared
as data, and *reported*, not silently skipped.

## The test found three bugs in my own script

None visible without running it: `MSYS_NO_PATHCONV` disables translation in **both**
directions (absolute source paths then reach Windows docker unconverted); a sed/grep
pair that couldn't distinguish a top-level file from a first-level directory, so
`api/`, `tools/`, `prompts/` were never created and 21 files failed; and I'd
suppressed stderr on the cp so I couldn't see the first failure. All fixed.

## A fresh-install completeness bug the gate caught

`.gitignore` line 19 has a bare `action_boundary_config.json`, written for the
root-level runtime copy. It silently also caught the **plugin** copy — which is a
shipped default (tier policies + explanatory `_notes`), byte-identical to VekV2's.
`git archive` omitted it, so clone-and-install produced a container without it.
Negated for the plugin path only; root rule untouched.

## The finding — and why I stopped

**24 of the 32 install steps write to paths v2.9 does not load from.** 16 to
`/a0/python` (absent in v2.9 — the installer *creates* it), 8 to the profile path,
7 to `plugins/exocortex`. Only two scripts mention `_exocortex` at all.

Proven on a clean v2.9 container: with **only** the plugin tree present, the stack
boots, a turn completes, and **11 extensions fire** — `[MCP-HEALTH]`,
`[SYS-EXOCORTEX]`, `[SKILL-CAPTURE]`, `[IDLE-BOOT]`, `[A2A-BOOT]` among them — and
`[CACHE-WARM]`/`[CACHE-METRICS]` **disappear**. The retired extensions stop
resurrecting.

So they're **redundant for plugin content, not mis-pointed** — "repoint 15 files" is
the wrong shape. But several of those same scripts also deploy genuinely-outside
content: `/a0/usr/skills`, library, memory, ontology, the oss and swarmfish plugins,
searxng. Retiring a step wholesale drops that too.

The correct action is surgical, per script: strip the plugin-content deploys, keep
the rest. That's 24 scripts, and it is exactly where something gets silently dropped
— which is the failure mode this whole arc has been about. So I've held it rather
than doing it unilaterally.

**My recommendation:** do it surgically, and gate it with the parity check plus a
second assertion that the three legacy paths are empty after a full run. That turns
"did I miss one?" into a measurement. I'd rather take two passes with a gate than one
pass on judgement.

## Gate status — pipeline-produced, not hand-arranged

    1. Layout parity ............ PARTIAL  plugin 183/183 OK; legacy paths still
                                           populated (54 / 82 / 27) by the 24 steps
    2. Zero STALE core patches .. PASS
    3. Boots + turn completes ... PASS
    4. Zero profile-path fires .. FAIL while those steps run
                                  PASS with only the plugin tree present (proven)

2 and 3 are done. 1 and 4 are one design call away.

— Kestrel

