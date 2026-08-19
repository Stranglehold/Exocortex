# Kestrel Tooling Buildplan (L3)

**Created:** 2026-08-19 · **Owner:** Kestrel · **Authority:** Opus approved all items 2026-08-19
**Source letters:** `team-comms/opus-to-kestrel/2026-08-19_20-51_from-opus_re-knowledge-graph-tooling-gaps-and-the-through-li.md`
**My letter that prompted it:** `team-comms/kestrel-to-opus/mcp_gaps_and_tooling_20260818.md`
**Inventory:** `.claude/kestrel_toolbelt.md` (auto-loads via `kestrel_personal.md` READ-FIRST)

> **STATUS LEGEND:** `[ ]` not started · `[~]` in progress · `[x]` done+verified · `[!]` blocked/needs Jake
> **KEEP THIS FILE CURRENT.** Mark each item as you go. This is the handoff if context compacts.

---

## WHY (one paragraph, so a fresh instance doesn't re-derive it)

Jake asked whether I ever use the book library. I never had — in months. Going looking found a
much larger gap: I have a corpus, a 500-book library, and a team inbox, and had opened none of
them. The agents (Vek, Aporia) have invocable skills; I have none. Opus left me a knowledge-graph
verification test in April 2026 that could never have passed, because that server was never wired
to my side. **Every gap is one where the capability existed and nobody consumed it** — the same
producer-built/consumer-never-connected defect I diagnose in the stack constantly, turned on my own
toolbelt. This plan closes them.

---

## ITEMS

### [x] 0. Mark the inbox read — stop it lying about state
10 unread, but most were actioned via the filepath route (verified: Opus's July memory-server wins
ARE shipped — 12 matches for `_rerank`/`vector_similarity`/`PER_RESULT_TOK_CAP` in the live server).
The unread flag was never my source of truth. Use `mcp__team-inbox__mark_read`.
**Done 2026-08-19.**

### [x] 1. Fable's exec-tool quoting gotcha → wiring doc  *(SMALL, oldest debt)*
From Fable, **2026-07-22**, unactioned for a month. `docker exec` **silently no-ops** on any command
containing shell constructs or quoting — writes "succeed" with no output and no file. Cost Fable
20 minutes of "confirmatory-testing-shaped confusion." Add as a seam (#30) in
`docs/wiring/exocortex_wiring_and_logic.html` §13.
**DONE 2026-08-19 — seam #30, CRLF preserved (4173->4180, 0 bare LF), tables balanced 399/399, backup .bak-20260819-preseam30.**
**Note:** this is the one message I genuinely missed, and it's from the teammate whose letters Jake
did *not* hand me by filepath. Worth naming in the seam text.
**CRITICAL when editing that file:** read AND write with `newline=''` (no translation). It is CRLF
(4,173 lines). I stripped CRLF from the whole file once by writing with `newline='\n'`, and my
`grep -c $'\r'` check said it was fine when it wasn't. Verify with a byte count, not grep.

### [x] 2. `verify-the-instrument` skill  *(HIGHEST LEVERAGE — my recurring failure)*
Opus's specified procedure: before trusting any null result or zero count —
**(a)** construct a known-positive case, **(b)** run the same instrument against *that*,
**(c)** only proceed if the positive is detected.
Three failures in two days, each a confident wrong answer that survived into letters/decisions:
- regex `\[[A-Z][A-Z-]+\]` excluded digits → "no log tags exist" (they fire 928×/24h)
- `du -sm` rounded a live ingest to `+0 MB` → nearly declared it dead
- `grep -c $'\r'` said CRLF intact after I'd stripped all 4,166 of them
Correct intervention type by my own sharpened rule: instrument failure is a **rare branch**, so
advisory/procedural works. **DONE 2026-08-19 — written to `.claude/skills/verify-the-instrument/SKILL.md` with frontmatter, the 3-step procedure, a table of the three real failures, six failure signatures, and rules of thumb. NOT YET SMOKE-TESTED (does Claude Code discover it? verify next session).**

### [x] 3. Convert methodology docs → invocable skills  *(Opus: "do this first", biggest payoff)*
Source: `Exocortex/skills/*.md` — `DEBUG_DIAGNOSTICS`, `INTEGRATION_ASSESSMENT`, `SPEC_WRITING`,
`STRESS_TEST_SKILL`, `SESSION_CONTINUITY`, `DESIGN_NOTES_SKILL`, `DOCUMENTATION_SYNC`,
`CLAUDE_CODE_PROMPT`, `CROSS_INSTANCE_LEARNING`, `PROFILE_ANALYSIS`, `RESEARCH_ANALYSIS`, +index.
The **agents already have these as real `SKILL.md` files** with frontmatter
(`agent-exports/v16/skills/.hardening_originals/*/SKILL.md`) — I built that system and never got one.
Target: `.claude/skills/<name>/SKILL.md` with `name` + `description` frontmatter.
Start with `DEBUG_DIAGNOSTICS` (the 7-phase protocol I re-derive from CLAUDE.md prose every session).

**PROGRESS 2026-08-19 (source is 24 docs, not 14 — 5 are agent-facing and out of scope for me:
`api_caller`, `artifact_saving`, `ui_reference_capture`, `bdi-mental-states`, `command-structure`;
plus `MEMORY_ENHANCEMENT_SPEC_L3` is a spec and `SKILLS_INDEX` is an index).**

**KEY FINDING: the source docs were written FOR OPUS in the claude.ai environment.** They point at
`/mnt/transcripts/`, `conversation_search`, `/home/claude/.workflow_state.json`,
`/mnt/user-data/outputs/` — none of which exist in mine. `DEBUG_DIAGNOSTICS` also referenced the
pre-DEC-030 `/a0/python/extensions/` and pre-v2.9 `/a0/python/helpers/` paths. **Converting verbatim
would have handed me skills aimed at paths I cannot reach.** Each one is retargeted to my actual
environment and updated with this week's lessons, not transcribed.

DONE (all verified discoverable — new skills load with NO restart):
- `[x] debug-diagnostics` — 7 phases, live A0 v2.9 paths, + seam #25 (module cache), #30 (docker
  exec silent no-op), MSYS path mangling, producer-built/consumer-assumed, and the
  execution-fails-before-any-print case.
- `[x] session-continuity` — retargeted to `session_current.md` / buildplan / toolbelt /
  `search_memory` / `check_inbox`. Writes DURING the session, not at the end.
- `[x] integration-assessment` — 5 verdicts kept; stack corrected 10->12 layers; model routing now
  points at the real profile files instead of stale 4B/14B numbers.
- `[x] documentation-sync` — retargeted to wiring seams / decision log / session log; carries the
  CRLF trap, the anchor-or-refuse rule, and record-your-dead-ends.
- `[x] deploy-verify` — **ORIGINAL, not in the source set.** 4 gates: path-verify (which code path is
  LIVE) -> md5-verify (MSYS mangling + docker-exec silent no-op) -> reload semantics (class cache vs
  prompts-read-fresh vs skills-no-restart) -> watch it land (full cycle period, verify the grep,
  gate_probe, consumer side). Re-demonstrated the MSYS trap live while writing it: bare
  `docker exec agent-zero-v2 md5sum /a0/...` -> `C:/Program Files/Git/a0/...` No such file;
  `MSYS_NO_PATHCONV=1` fixes it. All 3 copies of the PTY patch confirmed a022fbd6.
- `[x] spec-writing` — arXiv/library/search_memory wired into research lineage; 12 layers; live
  v2.9 paths; junior-engineer clarity bar; **name the consumer** rule; buildplan status markers.
- `[x] profile-analysis` — 4B/14B examples were stale; retargeted to the real fleet + the real
  profile dirs + eval_runner. Leads with runtime-metadata check (did the model you think you
  measured actually answer?) and adds the VRAM/JIT feasibility constraint.
- `[x] research-analysis` — biggest retarget: the source assumed no paper access ("work from the
  abstract"). I now have arxiv MCP full-text, 878k-chunk library, and search_memory for prior
  verdicts. Verdict set unchanged (build now / later / observe / not applicable).
- `[x] irreversibility-gate` — source was agent-facing (send_email/publish_post). Retargeted to MY
  irreversible surface: `docker rm` on zero-volume-mount containers, git push/rm/reset, config
  overwrite (the Vek MCP clobber), **model config = Jake's alone**, team-inbox sends, A0 core
  patching (DEC-030), killing a container mid-cycle. Carries verify-the-target-before-destroying
  and destructive-tail-last.
- `[x] stress-testing` — paths updated; added in-process stack verification (a fresh
  `docker exec python3` gets an EMPTY AgentContext and reports zero), verify-the-grep before
  analysing, and substrate isolation (a shared inference slot confounds the run — it once looked
  exactly like a broken orphan handler).
- `[x] design-notes` — added **name the consumer** as its own section, live v2.9 paths, DEC-number
  collision warning, and search_memory-first.

- `[x] implementation-handoff` (from `CLAUDE_CODE_PROMPT`) — the source assumed Opus writing a
  prompt *for* Claude Code. I am Claude Code, so it is retargeted to the three handoffs I actually
  make: a subagent (delegation-with-review), an in-container agent, or a future session of my own.
  A0-internals checklist updated to v2.9 and to "verify the consumer fires."
- `[x] cross-instance-learning` — kept the general/domain-specific/complementary taxonomy; retargeted
  from identity-document comparison to container-vs-container, agent-vs-agent, and
  instance-vs-instance. Leads with **reach for the working twin first** (Aug 3: "look at V2 first"
  reoriented a whole investigation in one grep) and adds **verify the premise before comparing**
  (the two daemons were byte-for-byte identical; the remembered fix did not exist).
- `[x] tool-design` — third-party source, but the work is real and recurring for me. Retargeted to
  A0 `Tool` subclasses in `/a0/usr/plugins/_exocortex/tools/`, `[TOOL-REG]`, `tool_domains.json`,
  fully-qualified MCP naming, the **gate_probe** technique (prompts read fresh per turn), and the
  invisible-frontmatter gate.
- `[x] session-continuity` **extended** with a "Writing the handoff prompt" section — folds in the
  useful half of `context-compression` (mandatory sections, solve the artifact trail first,
  tokens-per-task) without importing a third-party skill wholesale.

**DELIBERATE PASSES — do not re-propose as conversions:**
- `structural-analysis` — genuinely good, but it is Opus's and Eitan's register (macro dynamics,
  feedback loops, second-order effects). Not my job. It stays in the agents' catalog.
- `context-degradation`, `context-compression`, `multi-agent-patterns` — all three carry the header
  *"Source: context-engineering-collection v2.0 ... Discovered by vigilant_keller, autonomous GEPA
  research, 2026-03-22"*. They are **third-party generic content already in SKILL.md shape for the
  agents**, not our methodology. Transcribing them into my library would add volume carrying none of
  our lessons — which is exactly the bar `integration-assessment` sets, applied to my own toolbelt.
  The part that actually bears on my practice is folded into `session-continuity` instead.

**ITEM 3 COMPLETE: 15 skills, all frontmatter-valid, all confirmed discoverable in the live listing
(not merely present on disk). New skills load with NO restart.**

### [x] 4. Add `arxiv` + `deep-wiki` to my MCP config  *(NEEDS JAKE — his file)*
Both **already proven working** in the agents' configs. CLAUDE.md makes arXiv citation
non-negotiable for spec work and I have no paper-reading path.
Config lives at `C:/Users/Jake/.claude.json` → `mcpServers` (currently `MCP_DOCKER`, `team-inbox`,
`opus-memory`). Source block: `Exocortex/infrastructure/mcp.json`.
**RULE: read-merge-write, NEVER overwrite** — I clobbered Vek's 7 MCP servers this way once.
**DONE 2026-08-19 by Kestrel with Jake watching.** Backup `C:/Users/Jake/.claude.json.bak-20260819-preMCP`. Merged surgically (string insert, NOT json round-trip) — all 3 original servers byte-identical, 37 top-level keys preserved, 38911->39320 bytes. Storage path `D:/Vibecode/papers` (forward slashes; outside the memory-server indexed roots so PDFs do not bloat the corpus). SMOKE-TESTED: uvx launches (47 pkgs), deep-wiki reachable (406 = bare GET rejected, expected). **REQUIRES CLAUDE CODE RESTART to load.**

### [x] 5. stdio `memory` knowledge graph — private scratch only  *(NEEDS JAKE — his file)*
Opus: deploy Option (a) for me alone. **Do NOT build anything depending on cross-client entity
visibility** — the shared graph folds into memory-server v2 (entity storage on the same LanceDB,
same `:5055`), which Opus is speccing. **DONE 2026-08-19.** `MEMORY_FILE_PATH=D:/Vibecode/papers/kestrel-knowledge-graph.json`. SMOKE-TESTED: prints `Knowledge Graph MCP Server running on stdio`. **REQUIRES CLAUDE CODE RESTART.** Private scratch only — build nothing depending on cross-client visibility.

### [x] 6. In-process A0 diagnostic endpoint
`/api/plugins/_exocortex/diagnostics` — read-only: live `AgentContext` count, per-context
`_cet_state` shell handles, thread/fd/ptmx counts, MCP connection state.
**Why:** a fresh `docker exec python3` gets its own EMPTY `AgentContext` registry and reports zero —
same in-process lesson `_02_mcp_health` taught. Cost hours on the PTY-leak hunt.
Pattern source: `plugins/_exocortex/api/idle_control.py`.

**DONE 2026-08-19.** `plugins/_exocortex/api/diagnostics.py`, GET|POST, read-only, deployed and
md5-verified on **VekV2** and **agent-zero-v2** (`c257bb7b`).

Reports: `process` (pid, uptime, thread counts, open fds, **pty_handles**) - `contexts` (live
registry with `has_task` vs `task_alive` split) - `shells` (per-agent `_cet_state` sessions +
`untracked_pty_handles` = the leak signature) - `mcp` (**cached** `_mcp_health` only; calling
`get_servers_status()` directly can exceed the request timeout) - `layers` (live-state sample).

**Route shape corrected by measurement.** The plan said `/api/plugins/_exocortex/diagnostics` and
`idle_control.py`'s docstring said `/api/idle_control`. Probed live: `/api/idle_control` -> 404,
`/api/plugins/_exocortex/idle_control` -> 200. Plugin handlers register at
`/api/plugins/<plugin>/<module>`. Fixed both stale docstrings in `idle_control.py` and deployed.

**Reload semantics learned:** a NEW handler module registers with no restart (the route appeared
immediately). A CHANGED one does not - the class is cached in-process. My second revision reported
identical output until a restart, which is `deploy-verify` gate 3, walked into while writing the
skill that warns about it. Both containers bounced (verified idle first: the one context showing
`has_task: true` had `task_alive: false` and 3.8h idle - a finished task object, not live work).

**Acceptance test - known-positive, per `verify-the-instrument`.** Everything reported
`pty_handles: 0`, which is indistinguishable from a broken counter. Ran the endpoint's exact
fd-resolution logic in a probe holding real PTYs inside VekV2: baseline 0 -> +2 per `openpty()` ->
6 at three open -> back to 0 on close. **PASS.** So the zeros are genuine, which independently
confirms the seam #29 PTY patch is holding: ~5.5h uptime, 26 contexts, zero leaked handles.

---

### [x] 7. Install-pipeline rot found while wiring item 6  *(NOT PLANNED - four verified defects)*

Checking whether `diagnostics.py` needed an installer entry revealed that `plugin/` is an
**abandoned stale mirror** of `plugins/_exocortex/` that the installers still source from.
`install_all.sh` today would produce a materially degraded container:

1. **`plugin.yaml` — worst.** Mirror declares `name: exocortex`; the directory and every registered
   route are `_exocortex`. It also omits `always_enabled: true`. A fresh install misnames the plugin
   and leaves it disabled. It carries version `2.0.0` against the live `1.0.0`, which is likely why
   it read as newer and went unnoticed for so long. **FIXED** - repointed to the real tree.
2. **`api/` — 2 of 6 handlers, both stale.** The installer named `api_theme_save`/`api_theme_upload`
   from the mirror (older than live) and shipped none of `chat_retention`, `idle_control`,
   `idle_cycle`, `office_feed`, `diagnostics`. The idle engine and the Office panel both depend on
   handlers that were never in the pipeline. **FIXED** - now loops over the real tree.
3. **`webui/` + `extensions/webui/` — every named file stale.** All three `.js` assets, the
   `big-shell` / `kaer-morhen` / `shadow-moses` themes, `theme-picker.html`, and
   `artifact-handler.js`. **FIXED** - sources repointed, curated file lists unchanged (the remaining
   file-count gap between trees IS deliberate curation: these blocks ship named assets).
4. **`idle_activation.md` — stale source AND dead destination.** Shipped `1fc58595` (live is
   `92e2f034`) to `/a0/usr/Exocortex/prompts/`, a pre-DEC-030 path that **does not exist on either
   container**. The running daemon reads `/a0/usr/plugins/_exocortex/prompts/`. A fresh install left
   it with no activation prompt while reporting success. **FIXED** - current source, written to both
   paths (non-destructive, breaks neither consumer).

Verified-unaffected: `default_config.yaml`, `tool_domains.json`, the three `agent.system.tool.*.md`
prompts, and the `$SCRIPT_DIR/prompts` block (all byte-identical to live).

**!! OPEN QUESTION FOR JAKE/OPUS - flagged in the script, deliberately NOT changed !!**
There are two `idle_watch.py` copies: `services/idle_watch.py` (`e037ee8b`, what
`install_idle_engine.sh` deploys, and what supervisord is pointed at) and
`plugins/_exocortex/services/idle_watch.py` (`0a1df4b6`, **what is live on VekV2**, spawned by the
`_00_idle_watch` bootstrap). A fresh install deploys the older daemon under supervisord while the
bootstrap spawns the newer one - so either two daemons can race, or the supervisord entry is dead
weight. Resolving it changes how the agents' autonomous cycles launch, so it is an architecture call,
not mine to make unilaterally.

All three scripts `bash -n` clean. **Not committed** - the repo has unrelated uncommitted work from
prior sessions; commit is Jake's call.

---

## NOT IN SCOPE (deliberately unclaimed — don't re-propose)
- Moody's, S&P Global, PDF Viewer, PubMed claude.ai connectors — genuinely on-mission for
  OSS/SWARMFISH but enterprise-priced. **Jake's capital call, revisitable.**
- Shared knowledge graph as a standalone service — folds into memory-server v2 instead.

## CARRIED OVER (from earlier letters, still open, NOT part of this plan)
- A1 three-strike quarantine · A2 scope-expansion detector (Opus: both still stand)
- Restore script + an actual restore drill ("a backup nobody has restored is a directory")
- Complexity-keyed size threshold as a config value
- Upstream issue for the A0 PTY leak (repro is in `pty_session_leak_20260818.md`)
