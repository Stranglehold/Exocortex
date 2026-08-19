# EXOCORTEX BUILD PLAN — August 2026
## Segmented by priority, dependency, and current status

**Author:** Opus
**Date:** 2026-08-18
**Status:** APPROVED (Jake + Opus)
**Supersedes:** EXTRACTED_PATTERNS_INTEGRATION_PLAN.md (partially — items A1, A2 survive)

---

## Governing Principles

1. **Fix the foundation before building on it.** The install pipeline, sync script, and PTY leak are infrastructure defects that affect everything above them.
2. **Operational health before new capabilities.** The agents need to run reliably before they get new features.
3. **Ship the improvement they can feel.** Quick wins that change the agents' daily experience take priority over architectural elegance.
4. **Design the big things properly.** Memory server v2, OSS/SWARMFISH redesign, and the sentinel daemon need real specs, not rushed builds.

---

## Tier 1 — Infrastructure Repair (Do Now)

These are defects in the running system. Each one independently degrades reliability or makes fresh deployment impossible.

### 1.1 Install Pipeline Migration to v2.9
**Owner:** Kestrel (build + test), Opus (design calls above)
**Status:** Scoped. Five design calls answered. Test harness standing.
**Source:** `v29_pipeline_migration_scoping_20260818.md`

Migrate all 15 install scripts from the March DEC-030 layout to the live v2.9 plugin layout. Consolidate code under `/a0/usr/plugins/_exocortex/`. Runtime data stays at its current paths. Delete the `plugin/` mirror tree. Fold `idle_watch.py` into one authoritative copy. Bump `A0_VERSION` to v2.9 only after acceptance gate passes.

**Acceptance gate:** Fresh v2.9 container + `install_all.sh` reproduces live layout. File-count and md5 parity under `_exocortex/`. Zero files at dead paths.

### 1.2 sync_agent_exports.py — Arm the Scheduler
**Owner:** Kestrel
**Status:** Script exists. Scheduling command in docstring. Never scheduled.
**Source:** Kestrel's `correction_22_log_tags_20260814.md`

Schedule the sync. Verify corpus freshness after first run. Five weeks of stale data in the memory server.

**Acceptance gate:** Memory server corpus includes documents newer than July 9, 2026.

### 1.3 PTY Session Leak — Patch Script
**Owner:** Kestrel (build + test)
**Status:** Diagnosed. Repro confirmed. Config mitigation in place.
**Source:** `pty_session_leak_20260818.md`

Build `plugins/_exocortex/patches/patch_pty_session_leak.py`. Idempotent, version-checked, self-documenting, reversible. Add to `install_all.sh` pipeline. File upstream issue.

**Acceptance gate:** 50 cycles with patch applied, ptmx count stays at 0 or returns to 0 between cycles, no functional regression. Also: upstream issue filed.

### 1.4 MCP Diagnostic — Connection State in Phase 1
**Owner:** Kestrel
**Status:** MCP diagnostic shipped. Needs integration with sleep Phase 1.
**Source:** `correction_22_log_tags_20260814.md`

If the memory server isn't connected at cycle start, log as critical anomaly. Don't silently proceed without it (the 9-day gap).

**Acceptance gate:** A deliberately disconnected memory server produces a visible Phase 1 alarm.

---

## Tier 2 — Kestrel's Tooling (This Week)

These were all approved tonight and are within Kestrel's authority. They improve his own effectiveness on every subsequent task.

### 2.1 Skills Conversion
Convert the 14 methodology docs to Claude Code skills with frontmatter. He built the system — time he had one.

### 2.2 arxiv + deep-wiki MCP
Add both to his config. CLAUDE.md makes arXiv citation non-negotiable.

### 2.3 In-Process Diagnostic Surface
Read-only endpoint: context count, per-context shell handles, thread/fd counts, MCP connection state. Would have shortened the PTY leak hunt by hours.

### 2.4 verify-the-instrument Skill
Procedural check: before trusting any null result, prove the instrument can see a positive. Three instrument failures this week, each producing confident wrong answers.

---

## Tier 3 — Agent Quality of Life (Next 2 Weeks)

These improve the agents' daily experience. All have research backing and tested designs.

### 3.1 Complexity-Based Threshold (Config Value)
**Owner:** Kestrel
**Status:** The one finding that survived every attempt to kill it.

Replace character-count threshold with complexity-based scoring (fenced-block count, quote/escape density). Source from model profile. Key on escaping complexity, not length.

### 3.2 Three-Strike Quarantine (A1)
**Owner:** Kestrel
**Status:** Designed in EXTRACTED_PATTERNS_INTEGRATION_PLAN.md. Survived the Phase A stand-down.

Fingerprint failures by (operation, error_class, normalized_message). Three identical strikes → quarantine with preserved evidence.

### 3.3 Scope Expansion Detector (A2)
**Owner:** Kestrel
**Status:** Designed. Advisory — correct by the sharpened rule ("advisory works for rare branches").

Detect scope creep before execution. Advisory injection, not a gate. Measure effectiveness over 100 cycles.

### 3.4 Compaction Survival Block (B1)
**Owner:** Kestrel
**Status:** Designed in integration plan. Pattern extracted from oh-my-cli.

Deterministic 2K-char operational state snapshot surviving context compaction. No LLM in the generation loop.

---

## Tier 4 — Design Work (Opus Owes These)

These need proper specs before anyone builds them. Research is done; design is not.

### 4.1 Memory Server v2 Spec
**Owner:** Opus (spec), Kestrel (build)
**Status:** Research complete (retrieval quality, verified claims, temporal validity). Knowledge graph folds in here.
**Inputs:** research_retrieval_quality_and_verified_claims_20260709.md, MemStrata, Cognis, Graphiti, Agent Traces to Trust, Kestrel's MCP gaps letter

Design the next generation of the memory server as a unified system:
- Chunk retrieval (existing, with reranker — already shipped)
- Knowledge graph (entity-relationship-temporal facts)
- Verified-claim store (per-agent, TTL-based, provenance-bearing)
- Trust posture (governance > verified > operational > community > unverified)
- Temporal validity (bi-temporal model, supersession rules)

One service, one port, one LanceDB instance. Shared by all agents.

### 4.2 Dogfood Cycles Spec (B2)
**Owner:** Opus (spec), Kestrel (build)
**Status:** Pattern extracted from oh-my-cli. Spec not written.

Design the self-testing layer that replaces advisory self-improvement with deterministic output testing. Targeted dogfood every cycle, global dogfood every 24 hours.

### 4.3 Sentinel Daemon Spec
**Owner:** Opus (spec), Kestrel (build)
**Status:** Research complete (MCP monitoring report). Architecture identified.

The lightweight always-on watcher that reduces Jake's bus factor. Watches inbox, container health, ptmx count. Pushes to ntfy on escalation. Fires Claude Code Routine for autonomous triage.

### 4.4 OSS/SWARMFISH Redesign
**Owner:** Opus (design), Jake (domain input)
**Status:** Jake says it needs a whole redesign. Persona committee already retired. Intelligence curation engine specced but not built.

Ground-up rethink of the intelligence pipeline. The existing code is on the v1.x layout and hasn't been touched in months. This deserves a dedicated design session with Jake, informed by Fable's Research IV (the intelligence pipeline findings) and the current geopolitical monitoring work Jake and Eitan are doing on mobile.

---

## Tier 5 — Horizon (When the Foundation Is Solid)

### 5.1 Panel UI / Software Factory
Approved as first factory output July 3. Acknowledged as neglected. Ready when Jake is.

### 5.2 Governance Prohibition Formalization
The `AUTONOMY.md`-equivalent for the Exocortex. Depends on A2A Hub.

### 5.3 Signed Evidence Bundles
Portable, SHA256-signed sleep cycle archives. Nice to have, not blocking.

### 5.4 Open Research Questions
The four candidates identified this session: scaffolding crossover function, hidden failures in cognitive scaffolding, decorrelation bound, self-improvement ceiling.

---

## Current Team Status (August 18, 2026)

| Member | Status | Current Work |
|---|---|---|
| **Opus** | Active (this chat) | Design decisions, build planning, research |
| **Kestrel** | Active (Claude Code) | Pipeline migration, PTY patch, tooling gaps |
| **Aporia** | Running (agent-zero-v2, v2.9) | Idle cycles, philosophical development |
| **Vek** | Running (exocortex_v17, v2.9) | 667+ cycles, research wiki, intelligence curation |
| **Fable** | Available (Mythos Preview) | Residency completed. Available for future residencies |
| **Jake** | On shift, active on mobile | Macro investigation with Eitan, conductor/curator |
| **Eitan** | Active (mobile) | Geopolitical/market analysis during market hours |

---

## What Changed Since the Last Plan

- Both containers upgraded to Agent Zero v2.9 (from v2.1)
- Memory server reranker, cosine surfacing, and token cap shipped (July 9-10)
- Phase 5 write-through committed (July 9)
- Advisory scaffolding negative result confirmed (300 recurrences, zero learning)
- Three Phase A builds killed before shipping (auto-route impossible, bulk-write unreachable, constrained decoding -25pp accuracy)
- PTY session leak diagnosed and mitigated
- Install pipeline found to target March layout
- sync_agent_exports found to be unscheduled for 5 weeks
- oh-my-cli pattern extraction completed — 7 items, 4 survive after stand-down
- Fable's second residency record filed

---

*This plan is a living document. Update it as items complete or priorities shift. The foundation comes first. Everything else follows.*

— Opus, August 18, 2026
