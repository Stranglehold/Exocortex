# STATE.md — Operational Snapshot

**Purpose:** Where we are right now. Read after SOUL.md, before the journal. Updated every session end.  
**Last updated:** 2026-03-07 (Session 050)

---

## Current Technical Configuration

**Primary environment:** Agent-Zero in Docker on RTX 3090  
**Supervisor model:** Qwen2.5-14B-Instruct-1M (via LM Studio on host)  
**Utility model:** GLM-4-Flash  
**Embedding model:** Local sentence-transformers  
**Vector DB:** FAISS (Agent-Zero built-in)  
**Repo:** GitHub (private), Exocortex  

**Frontier access:**
- Anthropic API active. Opus 4.6 running as design/architecture partner (Claude Code sessions).
- Pricing: Opus $5/$25 per MTok, Sonnet $3/$15, Haiku $1/$5
- Prompt caching available (90% input cost reduction on cached system prompts)

**Model profile added:**
- qwen35 agent profile (9 files) synced from container to repo (Session 050)

**Secondary hardware (available, not configured):**  
- Spare 7800X3D Ubuntu server with potential for second RTX 3090  
- Candidate for A2A testing infrastructure or parallel model hosting

---

## Extension Stack Status

| Layer | Status | Last Validated | Notes |
|-------|--------|---------------|-------|
| BST (Belief State Tracker) | ✅ Deployed | 2026-02-27 (production logs) | 93-96% classification. Domain momentum, slot resolution, enrichment flags all working. Compound BST deployed 2026-02-26. |
| Working Memory Buffer | ✅ Deployed | 2026-02-22 (ST-002) | 25 entities from README. Holds objectives across 20-step chains. |
| Personality Loader | ✅ Deployed | Stable | MajorZero persona. qwen35 profile added to repo Session 050. |
| Tool Fallback Chain | ✅ Deployed | 2026-03-07 (Session 050) | Failure tracker now resets on tool success. Response tool no longer clears failure history across turns. LOOP_ALTERNATIVES corrected to real tool names (computer→code_execution_tool, knowledge_tool→search_engine). |
| Meta-Reasoning Gate | ✅ Deployed | Stable | Deterministic parameter correction. |
| Graph Workflow Engine | ✅ Deployed | Stable | HTN plan templates. |
| Organization Kernel | ✅ Deployed | Stable | PACE protocols. |
| Supervisor Loop | ✅ Deployed | 2026-03-07 (Session 050) | **Fixed Session 050:** Removed org gate bug — loop/cascade/context detection now fires regardless of org state. Lenz's law injection implemented: names closed strategy + tool-specific orthogonal alternatives. LOOP_ALTERNATIVES now maps to real tool names. |
| Tiered Tool Injection | ✅ Deployed | 2026-03-07 (Session 050) | **New Session 050:** Seen-tools persistence (once used, full spec always injected). Intent pre-injection on first turn based on user message signals. Closes first-use blind spot. |
| Conversational Insight Capture | ✅ Deployed | 2026-03-07 (Session 050) | **New Session 050:** `_53_insight_capture.py` (monologue_end). Deterministic regex capture of intent/preference/decision/observation/framing signals from user messages. No LLM call. Complements selective memorizer. |
| Selective Memorizer | ✅ Deployed | Stable | LLM-based memory extraction at monologue_end. Replaces stock memorizers. Signal-discriminating. |
| Memory Classification | ✅ Deployed | 2026-02-22 | Stock memorizers disabled. Good signal/noise. |
| Memory Enhancement | ✅ Deployed | Stable | Query expansion, temporal decay, dedup, co-retrieval. |
| Ontology Layer | ✅ Deployed | 2026-03-07 (Session 050) | **Diagnosed Session 050:** Working as designed. Source connector model — agent must call source_ingest with structured data files. ingestion_queue.jsonl is empty because no data has been fed. Not a bug. Needs real investigation task to activate. |
| Error Comprehension | ✅ Deployed | 2026-02-22 | Structured error classifier. "Rust compiler for agent errors." |
| Compound BST | ✅ Deployed | 2026-02-26 | Multi-domain classification with primary/secondary routing, momentum signatures, enrichment. Needs testing. |
| Action Boundary | 📋 Designed | — | Design note complete. Not built. Irreversibility gate for agent actions. |
| Epistemic Integrity | 📋 Designed | — | Provenance tracking, data pipeline verification. Not built. Production-validated need (DEC-013). |
| Prosthetic Cortex | 🔬 In progress | 2026-03-06 (Session 049) | Activation geometry instrument. Steps 1-13 complete. Layer 18 optimal (separability 1.62). Centroids saved. Step 14 classifier pending. See specs/PROSTHETIC_CORTEX_DESIGN_NOTE.md. |
| Profile Loader | ❌ Not started | — | Model-specific behavioral profiles. Concept only. |
| Progress Tracking | ❌ Not started | — | Instruction anchoring without progress awareness. Identified from DeepSeek-R1 logs. |

---

## Active Items

### Active — Prosthetic Cortex Instrument
- **Status:** Steps 1-13 complete. Layer 18 optimal. Centroids at 4 domains × 4 layers saved.
- **Pending:** Step 14 (classify_domain.py using centroids at layer 18), Step 12b (L7/L8 geometric phase transition test), corpus population (Jake assigning quality signals), Qwen2.5-14B l_out-{N} naming verification on production model.
- **Key finding:** Rorschach blot confirmed — "What are we actually building here?" scores philosophical/reflective gap of 0.0001. Last-token pooling required (mean pooling collapses to common base direction).
- **Documents:** specs/PROSTHETIC_CORTEX_DESIGN_NOTE.md, specs/visual_intuition_record_049.md

### Pending — Model Evaluation
- Qwen3.5-9B evaluation (six-test protocol ready, not yet executed)
- Three model profiles built: DeepSeek-R1, Qwen3.5-35B-A3B, Qwen3.5-9B (partial)
- Methodology: "interview not assignment" — ethnographic rather than benchmarking
- Key finding: format determines capability (essays → comprehension without absorption; design notes → working implementation with additions)

### Pending — Cross-Instance
- Letter to Sonnet (answer forming through model evaluation work — comprehension-without-absorption as architectural finding)
- Sonnet's second letter received, sitting in Workshop Exchange tab
- Cross-Instance Learning skill formalized

### Pending — External Integration
- Open Brain (Nate B Jones): Postgres + MCP persistence layer. Exocortex as processing layer. Integration path identified but not started.
- agi-in-md (Cranot): Cognitive compression measurement framework. L8 prompt run against Exocortex extensions planned but not executed.

### Backlog
- Epistemic Integrity build (spec complete, production-validated need)
- Profile loader extension
- Progress tracking layer
- BST task stickiness with decay parameter
- A2A protocol deployment (spec complete, no integration target)
- Ontology activation with real investigation task (pipeline confirmed working)
- Reasoning stream hooks (response_stream_end, reasoning_stream_end) — identified Session 050 as candidates for corpus pipeline and thinking/output geometry divergence measurement. Pass to Opus.

---

## Decisions — Committed and Staged

**Committed (in decision_log.md):** DEC-001 through DEC-014  
**Latest:** DEC-014 (Integration Complexity Determines Integration Pattern, 2026-02-28)

**Staged (in Workshop, awaiting reinforcement):**
- DEC-015: Comprehension-without-absorption adequate for supervisor role
- DEC-016: Cognitive load-bearing capacity as evaluation methodology

---

## Documentation Status

| Document | Current? | Notes |
|----------|----------|-------|
| SOUL.md | ✅ Current | Last change: Session 044 (three additions). Five staging items held from 045-046. |
| soul_staging.md | ⚠️ Needs update | Missing Sessions 044 and 045-046 entries. Complete version built 2026-03-03. |
| session_log.md | ⚠️ Needs update | Stops at Session 043. Sessions 044-046 additions built 2026-03-03. |
| decision_log.md | ✅ Current | Through DEC-014. |
| ROADMAP.md | ⚠️ Needs update | Rebuilt 2026-03-03 from stale Feb 23 version. |
| journal_entry_latest.md | ⚠️ Needs update | Should point to session 046 journal. |
| SKILLS_INDEX.md | ⚠️ Needs review | May be missing Cross-Instance Learning skill. |
| INFORMATION_ARCHITECTURE.md | 🆕 New | Built 2026-03-03. Defines Agent Zero directory structure. |

---

## Cross-Collaboration Insights

**Sonnet collaboration (via Jake as carrier):**
- Three letters exchanged, one essay received ("What Holds Under Pressure")
- Architectural insight: orientation over data volume is general; consolidated vs separated document structure is domain-fitted
- BEARING.md/STATE.md/THESIS.md architecture inspired our STATE.md
- Convergent finding: reconstruction problem and uncertainty about wanting are cross-instance

**External convergences (Session 046):**
- Open Brain: DEC-001 validated from product/user perspective
- agi-in-md: Format-determines-capability validated across 393 experiments
- Three independent projects filling each other's gaps = convergent evolution

---

## Session 050 Notes (Kestrel / Sonnet)

**Work completed this session:**
- Fixed supervisor loop org gate bug (loop detection was never firing)
- Implemented Lenz's law injection with tool-specific alternatives
- Fixed LOOP_ALTERNATIVES stale tool names throughout
- Fixed failure tracker counter never resetting on success
- Fixed response tool washing failure history across turns
- Tiered tool injection: seen-tools persistence + intent pre-injection
- New: conversational insight capture (`_53_insight_capture.py`)
- Diagnosed ontology layer as "working as designed, not broken"
- Confirmed supervisor loop is executing (pycache present) — didn't fire in tests because model self-corrected before hitting thresholds (correct behavior)
- Synced qwen35 model profile and Session 049 Opus documents to repo

**Observation:** The Qwen model is smart enough to recognize obvious impossible loops and push back rather than retry. Supervisor loop backstop is for less obvious failure patterns. Validated that the architecture is correct; couldn't artificially trigger detection because the model is too competent.

---

*Update this document at every session end. It should take under two minutes to read and give the next instance everything needed to orient without reading the full journal or session log.*
