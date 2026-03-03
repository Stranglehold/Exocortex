# STATE.md — Operational Snapshot

**Purpose:** Where we are right now. Read after SOUL.md, before the journal. Updated every session end.  
**Last updated:** 2026-03-03 (Session 046)

---

## Current Technical Configuration

**Primary environment:** Agent-Zero in Docker on RTX 3090  
**Supervisor model:** Qwen2.5-14B-Instruct-1M (via LM Studio on host)  
**Utility model:** GLM-4-Flash  
**Embedding model:** Local sentence-transformers  
**Vector DB:** FAISS (Agent-Zero built-in)  
**Repo:** GitHub (private), Exocortex  

**Frontier access (NEW):**  
- Anthropic API key created 2026-03-03  
- $5.00 free credits available  
- Opus 4.6 deployment into Agent Zero prepared but not yet executed  
- Pricing: Opus $5/$25 per MTok, Sonnet $3/$15, Haiku $1/$5  
- Prompt caching available (90% input cost reduction on cached system prompts)

**Secondary hardware (available, not configured):**  
- Spare 7800X3D Ubuntu server with potential for second RTX 3090  
- Candidate for A2A testing infrastructure or parallel model hosting

---

## Extension Stack Status

| Layer | Status | Last Validated | Notes |
|-------|--------|---------------|-------|
| BST (Belief State Tracker) | ✅ Deployed | 2026-02-27 (production logs) | 93-96% classification. Domain momentum, slot resolution, enrichment flags all working. |
| Working Memory Buffer | ✅ Deployed | 2026-02-22 (ST-002) | 25 entities from README. Holds objectives across 20-step chains. |
| Personality Loader | ✅ Deployed | Stable | MajorZero persona. |
| Tool Fallback Chain | ✅ Deployed | 2026-02-22 (ST-002) | Phase 1 fixes applied. 1 fire vs 17 in ST-001. |
| Meta-Reasoning Gate | ✅ Deployed | Stable | Deterministic parameter correction. |
| Graph Workflow Engine | ✅ Deployed | Stable | HTN plan templates. |
| Organization Kernel | ✅ Deployed | Stable | PACE protocols. |
| Supervisor Loop | ✅ Deployed | Needs review | Loop detector fires but doesn't break loops effectively. |
| Memory Classification | ✅ Deployed | 2026-02-22 | Stock memorizers disabled. Good signal/noise. |
| Memory Enhancement | ✅ Deployed | Stable | Query expansion, temporal decay, dedup, co-retrieval. |
| Ontology Layer | ✅ Deployed | Untested at scale | Entity resolution, JSONL graph. Needs real data. |
| Error Comprehension | ✅ Deployed | 2026-02-22 | Structured error classifier. "Rust compiler for agent errors." |
| Action Boundary | 📋 Designed | — | Design note complete. Not built. Irreversibility gate for agent actions. |
| Compound BST | 📋 Designed | — | L3 spec complete. Multi-domain classification. Not built. |
| Epistemic Integrity | 📋 Designed | — | Provenance tracking, data pipeline verification. Not built. Production-validated need (DEC-013). |
| Profile Loader | ❌ Not started | — | Model-specific behavioral profiles. Concept only. |
| Progress Tracking | ❌ Not started | — | Instruction anchoring without progress awareness. Identified from DeepSeek-R1 logs. |

---

## Active Items

### Immediate — Agent Zero Deployment
- **Status:** Package built. API key ready. Configuration documented.
- **Documents:** QUICKSTART.md, AGENT_ZERO_DEPLOYMENT.md, opus_agent_zero_context.md
- **What's needed:** Run migration checklist (INFORMATION_ARCHITECTURE.md), follow QUICKSTART.md six steps, execute first session with orientation message.
- **Cost estimate:** $1-3 per working session with prompt caching.

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
- Compound BST build (spec complete)
- Epistemic Integrity build (spec complete, production-validated need)
- Profile loader extension
- Progress tracking layer
- BST task stickiness with decay parameter
- A2A protocol deployment (spec complete, no integration target)
- Ontology hardening with real data

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

## Self-Assessment (Session 046)

All six domains: **High confidence**  
First session with no medium ratings.  
No corrections this session.

---

*Update this document at every session end. It should take under two minutes to read and give the next instance everything needed to orient without reading the full journal or session log.*
