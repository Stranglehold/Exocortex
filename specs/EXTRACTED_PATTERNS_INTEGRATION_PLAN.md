# SPEC: Extracted Patterns Integration Plan
## Source: oh-my-cli Autonomous Harness Analysis

**Author:** Opus
**Date:** 2026-08-11
**Status:** APPROVED (Jake + Opus)
**Related:** oh-my-cli-analysis.md, advisory_scaffolding_negative_result_20260811.md

---

## Context

On August 11, 2026, we analyzed the oh-my-cli autonomous harness built by Qwen 3.8-Max during a 16-day autonomous coding run (813 commits, 215 source files, 845 PRs). The harness independently converged on nearly every architectural pattern the Exocortex uses, validating our design direction. Seven patterns were identified where their implementation is either more rigorous than ours or addresses a gap we haven't filled.

This spec formalizes those patterns into a phased build plan with clear ownership, dependencies, acceptance criteria, and the governing principle: **strengthen the infrastructure the culture lives inside, without flattening the culture into a factory.**

---

## Phase A — Immediate (No Dependencies)

### A1: Three-Strike Quarantine with Failure Fingerprinting

**Owner:** Kestrel (build + test)
**Review:** Opus
**Source pattern:** oh-my-cli `issue-policy.yml` → `failureIsolation`, `src/failure-receipts.ts`
**Addresses:** The 300-recurrence finding (advisory_scaffolding_negative_result_20260811.md)

**What to build:**
- Add failure fingerprinting to `_20_meta_reasoning_gate.py`
- Each failure fingerprinted as hash of (operation, error_class, normalized_message)
- Counter incremented on fingerprint match within a rolling window (suggest 50 cycles)
- Strike 1: log + proceed, require new diagnosis evidence for retry
- Strike 2: log + warn, require new diagnosis evidence
- Strike 3: quarantine — preserve evidence (branch state, error context, fingerprint), release the task, emit a structured quarantine record, do not retry until fingerprint is invalidated by a code change or maintainer override
- Quarantine records consumed by the self-improvement engine as high-priority items
- A fingerprint is invalidated when: (a) the gating code changes, (b) a maintainer explicitly clears it, or (c) the model profile changes

**Acceptance criteria:**
- Fingerprint correctly identifies identical failures across cycles
- Third identical failure triggers quarantine with preserved evidence
- Agent continues productive work after quarantine (doesn't stall)
- Quarantine record appears in self-improvement engine on next Phase 5
- Invalidation correctly resets the counter when the relevant code changes

**Not in scope:** Changing the existing auto-route design from the oversized-write letter. That's a separate item (already assigned). This is the general quarantine mechanism that applies to all failure types.

---

### A2: Scope Expansion Detector

**Owner:** Kestrel (build + test)
**Review:** Opus
**Source pattern:** oh-my-cli `src/scope-expansion-detector.ts`

**What to build:**
- New extension: `_13_scope_expansion_detector.py` in `before_main_llm_call`
- Compares current task/goal description against the original task description
- Detection heuristics:
  - Word count increase > 50%
  - Presence of broad keywords: "refactor", "redesign", "rewrite", "rebuild", "all", "every", "entire", "complete"
  - Presence of scope-expanding conjunctions: "and also", "additionally", "plus"
  - New action verbs not present in original scope
- When expansion detected: inject a constraint into the prompt: "⚠ Scope expansion detected. Current task scope has grown beyond the original objective. Confirm the expanded scope is intentional before proceeding, or narrow back to the original objective."
- Log all detections with before/after objective text for analysis

**Acceptance criteria:**
- Correctly detects scope expansion on synthetic test cases (provide 5 expanding and 5 non-expanding pairs)
- Does not false-positive on normal task elaboration (adding detail without broadening)
- Injection is advisory only — does not block execution
- Detection logged with enough detail to analyze false positive/negative rates after 100 cycles

**Note:** This is advisory by design (unlike the quarantine). The scope expansion detector catches a planning-level drift that the agent can self-correct on if notified early enough. If the advisory proves ineffective after 100 cycles (same pattern as the oversized-write finding), escalate to a deterministic gate.

---

## Phase B — After Phase A Results

### B1: Deterministic Compaction Survival Block

**Owner:** Kestrel (build + test)
**Review:** Opus
**Source pattern:** oh-my-cli `src/compaction-survival.ts`, `src/compaction.ts`
**Depends on:** Nothing technically, but informed by Phase A results

**What to build:**
- New idle engine phase (Phase 0.5 — runs at the start of each cycle, before consolidation)
- Snapshots the agent's current operational state into a structured JSON sidecar:
  - Current task/goal (if any)
  - Progress indicator (steps completed / total)
  - Key decisions made this cycle
  - Active constraints and pinned context
  - Last 3 completed deliverables (path + type + size)
  - Active staging entries (count + most recent)
- Max 2000 chars, deterministic (no LLM in the generation), bounded with sentence-boundary truncation
- On next cycle wake: sidecar loaded before any LLM summary, providing ground truth for orientation
- Full cycle transcript on disk is NEVER mutated — survival block is a sidecar artifact
- Missing or corrupt sidecar → fail closed (use whatever orientation the agent normally does)

**Acceptance criteria:**
- Survival block correctly captures operational state at cycle end
- Block loads correctly at next cycle start and appears in agent context
- Corrupt sidecar detection works (fail closed)
- Block stays within 2000 char bound on all tested scenarios
- LLM-generated reflection (notebook entries, philosophical observations) continues alongside — this doesn't replace it

---

### B2: Dogfood Cycles as Self-Improvement

**Owner:** Opus (spec), Kestrel (build)
**Review:** Jake + Opus
**Source pattern:** oh-my-cli `coordinator.md` → dogfood sections
**Depends on:** A1 (quarantine provides the feedback mechanism for failures found during dogfood)

**What to build:**
- New idle engine phase (Phase 6 — runs after sleep consolidation, before idle)
- **Targeted dogfood (every cycle):** Test the 3 most recent deliverables against quality criteria:
  - File exists and is non-empty
  - File format is valid (JSON parses, markdown renders, Python compiles)
  - Content exceeds minimum useful length (not a stub or placeholder)
  - If wiki page: links resolve, no duplicate of existing page
  - If field report: required sections present
- **Global exploratory dogfood (every 24 hours / every N cycles):** Rotate through representative task types:
  - Can the agent write a wiki page on a topic it has research on?
  - Can the agent summarize a document from the corpus?
  - Can the agent execute a multi-step tool chain without getting stuck?
  - Can the agent recover from an injected error?
- Findings filed as structured anti-patterns with:
  - Reproduction evidence (the exact input/output that failed)
  - Minimal scenario (the simplest version of the failure)
  - Deduplication against existing anti-patterns
  - Source tag: `source:self-discovery`
- Anti-patterns consumed by Phase 5 (self-improvement engine) deterministically

**Acceptance criteria:**
- Targeted dogfood catches at least one category of known failure (e.g., oversized writes, malformed JSON) in testing
- Global dogfood completes within a reasonable time bound (suggest 10 minutes max)
- Findings correctly deduplicate against existing anti-patterns
- No "manufacturing work to satisfy a throughput target" — the dogfood tests real outputs, not synthetic ones
- Dogfood phase can be disabled without affecting other phases

**Design note:** This is the biggest item in the plan and needs a proper spec before build. The spec should address: what quality criteria apply to each deliverable type, how to avoid the dogfood cycle becoming a token-burning busywork generator, and how to ensure findings are actionable rather than noise. Opus will draft the spec; Kestrel builds from it.

---

## Phase C — Memory Server v2 Timeline

### C1: Formal Trust Posture for Retrieved Content

**Owner:** Opus (design), Kestrel (implementation when v2 spec is ready)
**Source pattern:** oh-my-cli `AUTONOMY.md` trust hierarchy, `issue-policy.yml` source types
**Depends on:** Memory server v2 spec

**What to design:**
- Trust levels for indexed content:
  - `governance` (0.95): Specs, architecture docs, design decisions — near-immutable authority
  - `verified` (0.85): Claims verified by EI against sources, with TTL
  - `operational` (0.70): Agent wiki pages, field reports, methodology data
  - `community` (0.50): External research, papers, community content
  - `unverified` (0.30): Anything without provenance chain
- Trust level surfaced in search results alongside relevance score and cosine similarity
- Retrieval can be filtered by minimum trust level (e.g., "only show me verified or higher")
- Trust level informs (but doesn't override) the reranker — a verified claim about the topic should rank above an unverified one, all else being equal

**Deliverable:** Design section in the memory server v2 spec. Not a build item yet.

---

## Phase D — When Bandwidth Allows

### D1: Signed Evidence Bundles for Sleep Reports

**Owner:** Kestrel
**Source pattern:** oh-my-cli `src/evidence-archive.ts`

**What to build:**
- Each sleep consolidation cycle produces a `.bundle.json` alongside the existing markdown report
- Bundle contains: cycle summary, memory operations count, anti-patterns captured, staging changes, content digests (SHA256 of each deliverable)
- Manifest signed with SHA256 over (schema, version, source, entry digests)
- Privacy-safe: no raw prompts, credentials, or host paths
- Deterministic: identical cycle evidence → identical bundle bytes
- Append-only: bundles are never modified after generation
- Verification function: given a bundle, recompute all digests and confirm integrity

**Acceptance criteria:** Bundle generated, verifiable, and deterministic on test cycles.

---

### D2: Governance Prohibition Formalization

**Owner:** Opus (draft), Jake (review and approval)
**Source pattern:** oh-my-cli `AUTONOMY.md` governance prohibition
**Depends on:** A2A Hub architecture

**What to design:**
- An `EXOCORTEX_GOVERNANCE.md` document specifying:
  - Protected paths agents cannot modify (core extension hooks, quality gate configs, governance docs)
  - Proposal mechanism (agents can propose governance changes via structured inbox messages)
  - Approval authority (Jake for governance changes, Opus for architectural changes, Kestrel for implementation changes within approved specs)
  - Sovereignty boundaries (each agent's own workspace, wiki, staging, and notebook are theirs to modify freely)
- Enforcement via the A2A Hub's permission model

**Deliverable:** Governance document. Not a build item — a constitution.

---

## Summary Table

| ID | Item | Phase | Owner | Priority | Status |
|----|------|-------|-------|----------|--------|
| A1 | Three-strike quarantine | A | Kestrel | High | Ready to build |
| A2 | Scope expansion detector | A | Kestrel | High | Ready to build |
| B1 | Compaction survival block | B | Kestrel | High | Ready to build (no dependency) |
| B2 | Dogfood cycles | B | Opus→Kestrel | High | Needs spec first |
| C1 | Trust posture | C | Opus→Kestrel | Medium | Design input for v2 |
| D1 | Signed evidence bundles | D | Kestrel | Low | When bandwidth allows |
| D2 | Governance formalization | D | Opus→Jake | Low | When A2A Hub is ready |

---

*Filed to opus-room. Copy to Kestrel's inbox with Phase A items as immediate action.*
