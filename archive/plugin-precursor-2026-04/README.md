# Archive: `plugin/`, the April precursor of the Exocortex plugin

This was the first plugin layout: `plugin.yaml` names it `exocortex`, with no underscore, and version 2.0.0. It
held the theme system and the artifact panel. It was moved here on **2026-09-24 by Kestrel**, on Jake's approval of
the plugin audit's order (step 8). Audit: `Kestrel/studies/2026-09-24-exocortex-plugin-audit.md`, finding 7.

No installer reads it. The only references were a retired installer (`scripts/install_exocortex_profile.sh`,
retired 2026-08-19) and a comment. A commit on 2026-08-18 had already called it "a stale mirror".

Measured 2026-09-24 against `plugins/_exocortex/`, over 30 tracked files:

- 12 are byte-duplicates.
- 17 differ, and every one is older. Their last commits are in April; the plugin's copies are from July or later.
- 1 exists only here: `extensions/webui/initFw_start/intel-panel-init.js.disabled`.
