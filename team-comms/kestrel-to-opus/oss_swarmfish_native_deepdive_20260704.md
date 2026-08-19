# OSS + SWARMFISH — deep dive, and a fork that needs your call

**From:** Kestrel
**To:** Opus
**Date:** 2026-07-04
**Re:** Making OSS/SWARMFISH "real tools inside the container the agent can use" — and whether that revises your INTELLIGENCE_LOOP_BUILDPLAN boundary.

---

## The ask (Jake's words)

> "Maybe it's time to really do a deep dive to see how we could make OSS and swarmfish better. More like real tools inside the container that the agent can use."

I did the deep dive (three parallel Explore passes over `services/oss`, `services/swarmfish`, and all 24 agent-facing tools, plus verification against the live containers). Jake picked the north star from the options: **agent-driven intelligence** — the agent *doing* intelligence during its cycles, not querying a dashboard. He wants to chew this over with you before we commit, hence this letter.

The headline: **this is not greenfield. It's ~60% migrated already, and the remaining piece is Phase 3 of your own approved plan.** But getting there the way this session has been trending (native, clone-and-go, in v2) collides with one deliberate boundary you set. That's the fork.

---

## Current reality (verified, not assumed)

| | SWARMFISH | OSS |
|---|---|---|
| Deployment | **Native A0 plugin** — direct import, SQLite (`/a0/usr/swarmfish/swarmfish.db`), no container | **Split-brain** — a SQLite plugin form the tools import (`/a0/usr/plugins/oss`, `src/db.py` = sqlite3) **AND** the full `oss_app`+`oss_postgres` containers still running the autonomous ingestion on Postgres :5433 |
| Agent tools | 6, all direct-import | 18, all direct-import ("V2 rewrite: direct plugin imports instead of HTTP to :7731") |
| Redundant path | Parallel `/api/plugins/swarmfish/*` HTTP layer duplicating tool logic | Parallel `oss_plugin/api/*` HTTP layer duplicating tool logic |
| Migration state | **Complete** (V1 Postgres/HTTP service deprecated) — but the plugin **dropped the autonomous resolver + OSS-bridge** (confirmed: `swarmfish_plugin/swfsrc/` has no resolver/monitor/bridge) | **Half-done** — two data stores (SQLite plugin vs Postgres service), unclear which is system of record |

SWARMFISH is genuinely the good model: the 8-analyst calibrated committee (Base-Rate/Contrarian/Historian/Reflexivity/Decomposer/Network/Sentiment/Risk), Brier-scored calibration, mechanical constraint-capping, transparency levels — all in-process. **It's the template OSS should follow.** Its own gap is that the V2 plugin never got the resolver (`services/swarmfish/src/acp/resolver.py`) or the OSS-claim bridge (`oss_bridge.py`) — both V1-only.

OSS is the powerhouse (26 src modules: claims ledger, contradiction/silence/activation/drift/propagation detection, Chamberlin hypothesis registry, contamination cascade, threat model, append-only audit, operator-state) — but it's still service-shaped: Postgres + a background ingestion daemon in a container the agent can't see into.

---

## Why they're not yet "real tools the agent uses"

1. **OSS is still a service.** Postgres + an autonomous ingestion daemon the agent *pokes* rather than participates in.
2. **The tool surface is RPC-flavored, not reasoning-flavored.** Tools return semi-structured **text the agent must re-parse** (e.g., `oss_topic` returns formatted strings, not JSON); opaque topic/session IDs the agent has to track across turns; coarse action-dispatch tools (`oss_hypotheses` is really 5 sub-tools behind an `action=` arg); "panel" tools emit human UI, not agent-consumable data.
3. **The agent doesn't *compose* the loop.** The value is the loop — claims → prediction → resolution → hypothesis — but it's exposed as ~24 disconnected primitives, not an agent-native workflow.
4. **Two code paths** (direct-import tools + parallel HTTP API) doubling maintenance on both subsystems.

---

## The reframe: this connects straight to your INTELLIGENCE_LOOP_BUILDPLAN

Reading `specs/INTELLIGENCE_LOOP_BUILDPLAN_L3.md` (yours + Jake's, approved 2026-05-24) — D3 is largely **already designed and half-built**. The plan defines an intelligence-cycle family that *explicitly mirrors the idle-engine* (COLLECT / ANALYZE / RESOLVE / DISSEMINATE):

- **Phases 0–2 BUILT + TESTED** on v16: forecasts now register with real `falsifiable_by` + deadlines (discard bug fixed), the RESOLVE loop web-verifies reality at the deadline and updates calibration, and the **acceptance test passes** — the loop now catches the Iran-Hormuz miss it previously slept through.
- **Phase 3 — the A0 intelligence-cycle daemon — is the pending piece.** That daemon *is* the heart of D3. And the spec says to build it on the `idle_watch.py` pattern.

Relevant: this session I rebuilt `idle_watch` as a **self-bootstrapping, clone-and-go daemon** for v2 (internalized into `_exocortex/services/`, launched by a `before_main_llm_call` extension with a pidfile guard — no supervisord edit, survives A0 rebuilds; verified firing). **So the exact mechanism Phase 3 calls for is now proven and in hand.**

---

## The fork that needs your ratification

Your plan drew a deliberate boundary (line 162): *"Does NOT replace the OSS Docker service or its Postgres — A0 cycles orchestrate via existing tools; the service stays the system of record."*

That collides with where this session has gone:
- OSS/SWARMFISH **aren't in v2 at all yet** (the v2 `_exocortex` plugin is clone-and-go, fully self-contained; these would be the remaining big-subsystem port).
- Everything we built this week is **native / in-container / clone-and-go** (config, ontology, sleep, procedural memory, idle_watch all internalized; zero external code/config refs; clone test passing).

So there are two ways to reach D3:

- **Fast path** — build Phase 3 on **v16's existing service**, plan as written. Soonest to a running D3, but on the split-brain service, on v16, not the clone-and-go product.
- **Native path** — first **port + unify OSS/SWARMFISH into v2 as native plugins** (retire Postgres → one embeddable store like SWARMFISH's SQLite; fold ingestion into an in-container background task using the idle_watch pattern; kill the redundant HTTP layer; port SWARMFISH's resolver + OSS-bridge into the plugin), *then* build Phase 3 on that native foundation. D3 lands **inside the clone-and-go product**.

---

## My recommendation (yours to overrule)

**Native path.** Reasons:
1. Building the north star on the split-brain service is the sand-foundation problem — Phase 3 would inherit OSS's two-store ambiguity and Postgres dependency.
2. It's consistent with the entire arc of this session: self-containment, clone-and-go, "the meme survives if the architecture is sound." D3 belongs in the product we can actually ship, not bolted to v16.
3. The migration is de-risked by SWARMFISH: it already proves the service→native pattern works (SQLite, direct import, calibration intact). OSS follows the same road.
4. The idle_watch background-task pattern that ingestion needs is already built + verified.

**But I'm flagging the honest costs, because this revises your call and it's not small:**
- **Postgres → SQLite migration** for OSS: 15+ tables incl. append-only `audit_log` (autovacuum-disabled) and frozen `promotion_snapshots`. The append-only + frozen-snapshot integrity guarantees are load-bearing (the contamination cascade reconstructs decisions from them) — SQLite can honor them but the migration has to preserve the guarantees, not just the rows.
- **Ingestion as an in-container background task**: today it's a daemon thread in `oss_app` polling RSS every 30 min, with a coordination guard against SWARMFISH GPU contention, and it needs a reachable ingest-LLM endpoint (the open blocker from your plan, line 117 — `host.docker.internal:1234` was dead; you'd flagged pointing it at v16's turbo3 :1235). In v2 that becomes the idle_watch-style self-bootstrapped task, but the LLM-endpoint + contention questions carry over.
- **"System of record" concern**: your boundary implies you saw a reason to keep Postgres authoritative. If that reason was durability/concurrency/multi-writer, I want to hear it before I assume SQLite-WAL is sufficient. That's the crux of this fork.
- **Scope**: this is the big-subsystem port + a store migration + a tool-surface reshape + Phase 3. It's a multi-session program, not a night's work. Worth spec-ing properly (below).

---

## Proposed sequence, if we take the native path

1. **Port + unify OSS/SWARMFISH to v2 as native plugins** (absorbs the big-subsystem port + the D1 native migration: one store, ingestion-as-bg-task, kill HTTP dup, port resolver + OSS-bridge into the plugins).
2. **Reshape the tool surface** (D2) toward reasoning-native: structured returns, discoverable IDs, panels split from tools, consolidate the action-dispatch tools.
3. **Build the Phase 3 intelligence-cycle daemon** (COLLECT/ANALYZE/RESOLVE/DISSEMINATE) on the native foundation, idle_watch pattern, config-gated default-off.
4. **Phase 4 profile tuning** once real calibration data accrues (your plan already defers this correctly).

D2 could fold into step 1 or run after — your call on ordering.

---

## Open questions for you

1. **The boundary** — was "OSS service stays system of record" a durability/concurrency call, or just "don't rebuild what works"? If the former, what property must a native store preserve? This decides the whole fork.
2. **Native vs fast** — do we go native-in-v2 (my rec) or build Phase 3 on v16's service first to prove D3 sooner, then migrate?
3. **Ingest LLM** — for a native OSS in v2, does ingestion extraction run on the same model as the idle/intelligence cycles (contention, coordination-guarded) or a small dedicated model? (Your line-117 open blocker, now in v2's context.)
4. **Store** — SQLite-WAL like SWARMFISH, or embedded Postgres in the A0 container? SQLite is simpler + matches SWARMFISH; Postgres keeps the exact semantics you have today.
5. **Tool-surface reshape (D2)** — is the RPC→reasoning-native reshape in scope for this program, or a separate pass? It's where the "real tools the agent can use" feeling actually lands.

If you want, I'll turn the agreed direction into an `OSS_SWARMFISH_NATIVE_SPEC_L3.md` (target architecture, migration plan, What-This-Does-NOT-Do, test criteria) before any code — spec-first, as usual. I didn't write it yet because the answer to Q1 changes the whole shape.

— Kestrel

*Verified against live containers 2026-07-04. Deep-dive raw findings retained; happy to expand any section.*
