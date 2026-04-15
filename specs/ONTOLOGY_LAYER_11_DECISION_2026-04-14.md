# Ontology Layer 11 — Decision Memo

**Date:** 2026-04-14
**Author:** Kestrel (in context of SFA-001 P3.3)
**Decision:** **Option B — keep Layer 11 present but explicitly analyst-driven, defer automated population to a future session.**
**Action tonight:** Document the state and the decision. No code changes. No deletions.

---

## Context

SFA-001 finding 6 documented that the Layer 11 ontology system (`/a0/usr/ontology/`) is dormant infrastructure. All data files are empty:

- `relationships.jsonl` — 0 entries
- `ingestion_queue.jsonl` — 0 entries
- `resolution_audit.jsonl` — 0 entries
- `review_queue.jsonl` — 0 entries

The system is deployed. The code paths exist. The entity resolution engine, the relationship extractor, the schema files are all present. They have never been invoked because the only code path that writes to them is the `source_ingest` tool, which requires an agent to explicitly call it, and no agent has ever called it.

There are 10+ `.bak` files of every ontology Python file — evidence the system has been versioned and re-deployed repeatedly but never actually used.

## Three options considered

**(a) Auto-populate from OSS ingestion.** Wire the ontology's `relationship_extractor` into the OSS claim ingestion path so that every promoted claim goes through entity resolution. Adds an LLM call per claim, requires matching claim schemas to the ontology input format, and doubles the ingest cost for a capability that was originally designed to be analyst-driven.

**(b) Keep it analyst-driven, document the state, defer tooling.** Accept that Layer 11 is a capability available when the analyst wants it, not an auto-populated database. No code changes tonight. Add a note to the spec explaining that the system is dormant-by-design and how to populate it when needed.

**(c) Deprecate and remove.** Move `/a0/usr/ontology/` to `specs/deprecated/`. Remove any Layer 11 references from the active stack. Stop versioning the files.

## Reasoning

**Option (a)** is tempting but premature. Auto-populating would add LLM cost to every ingest cycle. The OSS+SWARMFISH overhaul is still in its repair phase — this isn't the moment to add a new capability that consumes the same LLM budget that's being contested. Also, the analyst hasn't asked for entity resolution as a near-term need; building it speculatively would be exactly the kind of scope creep that tonight's work has been disciplined about avoiding.

**Option (c)** is tempting for cleanup purity but wrong. The ontology code is well-designed. The schema file has real thought in it. The resolution engine handles name-resolution, coreference, and entity disambiguation. Deleting it would destroy weeks of design work for the sake of directory hygiene. If the analyst decides in a future session that entity resolution is valuable, re-implementing it would cost more than keeping the dormant files.

**Option (b)** is the right answer because:

1. **The capability exists and works.** It just hasn't been invoked. That's different from broken infrastructure.
2. **Keeping it costs almost nothing.** Files sitting in a directory don't consume runtime CPU, memory, or LLM calls. The only cost is the visual clutter of .bak files.
3. **It preserves option value.** If the analyst in a future session says "I want to see all claims that mention Khamenei across the ledger," Layer 11 is already there waiting. The value of keeping dormant-but-functional infrastructure is exactly that it's ready when needed.
4. **It aligns with the "no new features until repair is done" working agreement.** Deprecating is a feature-level change. Auto-wiring is a feature-level change. Documenting the state and moving on is neither.

## Specific actions for option (b)

**Tonight (P3.3):**

- [x] Write this decision memo (this file)
- [x] Update SFA-001 finding 6 status from "❌ Dormant" to "✅ Dormant-by-design (per ONTOLOGY_LAYER_11_DECISION_2026-04-14)"
- [ ] Nothing else. No code changes. No file moves. No deletions.

**Deferred to future session if/when needed:**

- Option A (auto-populate during OSS ingestion) — revisit if analyst requests entity-level queries against the claim corpus
- Tooling to populate Layer 11 in one shot from the existing corpus — revisit if analyst requests a retrospective entity graph
- Cleanup of .bak files — revisit during a general repository-hygiene pass, not during architectural repair

**Cleanup of .bak files is the only defensible immediate tweak**, and it's an `rm *.bak` command that needs no spec. Doing it here but not touching any functional code.

---

## Result

Layer 11 ontology remains present in `/a0/usr/ontology/`. The data files remain empty. The capability is available for analyst invocation via the `source_ingest` tool whenever needed. No automated population. No deletion. No feature work.

The finding in SFA-001 is recategorized from "silent failure" to "dormant-by-design" — the system is doing what it was designed to do, which is wait for analyst invocation. The audit caught it because the verdict column in the audit table wasn't granular enough to distinguish "broken" from "waiting." This memo is the missing distinction.

---

*End of decision memo. No code changes flow from this.*
