# Recorded A0 merge bases (Option A)

These are the **pristine Agent-Zero originals** of the files our `patches/` overwrite,
captured at the version recorded in `../../A0_VERSION` (currently **v1.13**, via
`git -C /a0 show v1.13:<path>`). They exist so an A0 upgrade is a mechanical 3-way
merge instead of an eyeballed diff — see `docs/UPGRADE_A0.md`.

## Why

A `patches/` file is a whole-file copy with no recorded base, so we can't tell what we
changed vs what A0 shipped. Recording the base makes the merge literal:

```
git merge-file  <our patch>            \   # ours  (patches/<path>)
                patches/a0_base/<path>  \   # base  (A0 @ pinned version)
                <A0's new version>          # theirs (git -C /a0 show vNEXT:<path>)
```

The result keeps A0's new changes (incl. security fixes) AND our delta, flagging any
real conflict instead of silently clobbering one side.

## Scope (this pass)

Recorded for the 4 files A0 changed between v1.13 and v1.17 that we deploy as overwrites
(the v1.17 re-base set, per `scripts/check_a0_updates.py`):

- `helpers/extract_tools.py`
- `plugins/_memory/helpers/memory_consolidation.py`
- `plugins/_model_config/helpers/model_config.py`
- `prompts/agent.system.main.communication.md`

**TODO (complete Option A):** record bases for *all* deployed-as-overwrite patches, not
just the ones that changed this cycle, so every future upgrade has a base. And re-capture
these at the new pinned version after each upgrade completes (the base must track the pin).
