# Archive: the legacy `extensions/` tree

This is the repository's old top-level `extensions/` tree, from the layout before the A0 v2.9 plugin (the
DEC-030 profile path and the v1.x `/a0/python/extensions`). It was moved here on **2026-09-24 by Kestrel**, on
Jake's approval of the plugin audit's order (step 8, "Phase 2"). Audit:
`Kestrel/studies/2026-09-24-exocortex-plugin-audit.md`, finding 7.

**Nothing installs from here.** The live stack is `plugins/_exocortex/`, and `scripts/install_exocortex_plugin.sh`
walks only that tree. The last installers that read this tree either wrote to dead roots inside `if false`
blocks (stripped 2026-08-19) or were retired on 2026-09-24 (`archive/a0-core-writes-v29/`).

## What it held (measured 2026-09-24, 101 tracked files)

| class | count | meaning |
|---|---|---|
| byte-duplicate of a plugin file | 35 | nothing lost |
| differs from its plugin copy | 26 | all older than the plugin copy; none was committed later than it |
| only here | 34 | DEC-030 drops, cache warmers, installers retired 08-19, `methodology_tracker/`, a 2026-02 backups folder, older extensions the plugin dropped |
| `archived/` | 5 | already archived inside the tree |
| live work that existed only here | 1 | `message_loop_prompts_after/_71_model_identity_verify.py`, now carried into the plugin tree (a21568f) |

The tree kept attracting edits after it stopped deploying: `_71` on 2026-09-03, and a widened MetaGate alias set
on 2026-09-20 (commit aa07af6 itself calls this the "retired install tree, not deployed"). That is why it moved.

## What still reads it

These read the same bytes as before, at the new path:

- `eval/bst_domain_sync_test.py` reads `_11_belief_state_tracker.py` and `slot_taxonomy.json`. The local pre-commit
  hook runs this test when either name is staged.
- `eval/bst_eval.py` reads `_11_belief_state_tracker.py` by default on the host.
- `eval/test_loop_alternatives.py` reads `message_loop_end/_50_supervisor_loop.py`.

Be careful with the results: **these are the legacy copies, not what was deployed.** The BST that ran until
2026-09-08 is at `archive/plugins-_exocortex/2026-09-08-prune/`. The supervisor that runs today is
`plugins/_exocortex/extensions/python/message_loop_end/_50_supervisor_loop.py`. Whether the evals should follow
the deployed code is a separate decision.
