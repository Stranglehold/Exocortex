# NOT RUNTIME-AUTHORITATIVE

**The runtime reads `plugins/_exocortex/config/model_profiles/`.** Nothing else.

`helpers/model_profile.py` sets `PROFILE_ROOT` to that plugin path and resolves
`<model_id>.json` there. A profile in this directory has no effect on a running agent.

## Why this file exists

There were three copies of the same profiles — this one, `eval_framework/profiles/`, and
the plugin tree — and they drifted. `jackrong_qwen3.6-27b` carried
`recommended_prosthetic_level: full` in `eval_framework/` and `light` in the other two.
Three sources of truth are zero sources of truth.

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
