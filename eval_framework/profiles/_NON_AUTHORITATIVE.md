# NOT RUNTIME-AUTHORITATIVE

**The runtime reads `plugins/_exocortex/config/model_profiles/`.** Nothing else.

`helpers/model_profile.py` sets `PROFILE_ROOT` to that plugin path and resolves
`<model_id>.json` there. A profile in this directory has no effect on a running agent.

## Why this file exists

There were three copies of the same profiles and they drifted. Corrected 2026-08-22 —
an earlier version of this paragraph named this directory twice and omitted the third.
The three are:

| directory | role | count on 2026-08-22 |
|---|---|---|
| `plugins/_exocortex/config/model_profiles/` | **RUNTIME AUTHORITATIVE** | 15 |
| `eval_framework/profiles/` (here) | raw generator output, never deployed | 15 |
| `eval/model_profiles/` | legacy deploy source for `install_epistemic_integrity.sh` | 14 |

That installer copies **two explicit filenames** from `eval/model_profiles/`, not a
glob, so a new file landing in this directory is not deployed anywhere.

They drifted: `jackrong_qwen3.6-27b` carried `recommended_prosthetic_level: full` here
and `light` in the other two. Three sources of truth are zero sources of truth.

Worse, the drift was silent in the dangerous direction: on 2026-08-22 both live models'
profiles existed HERE and not in the plugin tree, so a fresh install would have shipped
containers with no profile for either — both write caps reverted to the global default,
with nothing to indicate it had happened.

## What is stale here, on purpose

`evaluation_summary.recommended_prosthetic_level` was re-derived against the three-tier
design (`frontier` / `local_large` / `local_small`) in the plugin tree ONLY. The values in
this directory still use the retired `full` / `moderate` / `light` / `targeted`
vocabulary. Do not read them, and do not translate them — Opus's instruction was not to
rescue the old values but to re-derive from the tiers.

## If you are changing a profile

Change it in `plugins/_exocortex/config/model_profiles/` and verify with:

    python scripts/verify_plugin_parity.py <container>

Consolidating or retiring this directory is an open item; it was left in place rather than
deleted because `scripts/install_epistemic_integrity.sh` still deploys two files from
here to the legacy `/a0/usr/Exocortex/eval/model_profiles` path.

**2026-08-22:** `eval_framework/eval_runner.py` defaulted `output_dir` to the CWD-relative
`"./profiles"`, so running it from the repo root created a stray *fourth* `profiles/`.
The default is now anchored to this directory. `qwen3.8-27b.json` was moved here from
that stray dir; like everything here it carries the RETIRED tier vocabulary
(`light`) — the re-derived `local_large` lives only in the plugin tree.

