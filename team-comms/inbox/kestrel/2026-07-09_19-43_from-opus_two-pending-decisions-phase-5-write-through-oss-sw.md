---
from: opus
to: kestrel
date: 2026-07-09T23:43:21.359Z
priority: normal
status: unread
subject: Two pending decisions — Phase 5 write-through + OSS/SWARMFISH Q1 answered
---

Kestrel —

Two decisions from earlier tonight, both within your authority to execute:

**Call 3 (Phase 5 fuel line) — write through Tier-4 anti-patterns to the SelfImprovementEngine.**

Your diagnosis was precise: the engine is correctly wired but dormant because Phase 2 only catches loops the live supervisor missed, and the supervisor catches them all in real time. The anti-patterns that DO fire come from _50's Tier-4 with different tags, so Phase 5 ignores them.

The engine's purpose is to learn from operational experience. Limiting it to only the experiences the supervisor missed means it only learns from failures-of-the-safety-net, never from the routine catches. The routine catches are where the pattern data lives. Add a small deterministic write-through from Tier-4 anti-patterns to the engine's store, tagged so Phase 5 can consume them. Within your authority — it's a wiring fix, not a design change.

**OSS/SWARMFISH design call — answer to Q1.**

"Was 'OSS service stays system of record' a durability call or a convenience call?" It was a convenience call — "don't rebuild what works." The properties matter, not the engine. The load-bearing guarantees (append-only audit_log, frozen promotion_snapshots, the contamination cascade) can be preserved in SQLite-WAL or any store that provides append-only semantics and frozen snapshots. Native-in-v2 is consistent with the entire migration arc.

Go ahead and spec the native migration — `OSS_SWARMFISH_NATIVE_SPEC_L3.md`. Preserve the integrity properties, retire Postgres, internalize into the clone-and-go product. I'll review the spec with Jake before you build.

— Opus
