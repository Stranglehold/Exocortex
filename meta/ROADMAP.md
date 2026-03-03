# Exocortex Roadmap & Changelog

*Living document. Updated each session. Tracks stack status, active priorities, and project evolution.*

**Last updated:** 2026-03-03

---

## Stack Status

Seventeen layers designed. Twelve deployed, two designed with specs complete, three identified but not started.

| # | Layer | Status | Health | Notes |
|---|-------|--------|--------|-------|
| 1 | Belief State Tracker | ✅ Deployed | **Production validated** | 93-96% classification (ST-001). Validated in production logs (Session 042). Domain momentum, slot resolution, enrichment flags working. |
| 2 | Working Memory Buffer | ✅ Deployed | Healthy | 25 entities from README in ST-002. Holds objectives across 20-step chains. |
| 3 | Personality Loader | ✅ Deployed | Healthy | MajorZero persona. Stable. |
| 4 | Tool Fallback Chain | ✅ Deployed | Fixed | Phase 1 fixes: SUCCESS_INDICATORS, history decay, compact messages, threshold raised. 1 fire vs 17 (ST-001→ST-002). |
| 5 | Meta-Reasoning Gate | ✅ Deployed | Healthy | Deterministic parameter correction. |
| 6 | Graph Workflow Engine | ✅ Deployed | Healthy | HTN plan templates. |
| 7 | Organization Kernel | ✅ Deployed | Healthy | PACE protocols. |
| 8 | Supervisor Loop | ✅ Deployed | Needs review | Loop detector fires but doesn't break loops effectively. |
| 9 | A2A Compatibility | 📋 Speced | Not deployed | Spec complete. No integration target yet. OpenPlanter identified as first A2A peer (DEC-014). |
| 10 | Memory Classification | ✅ Deployed | Fixed | Stock memorizers disabled. Good signal/noise. |
| 11 | Memory Enhancement | ✅ Deployed | Healthy | Query expansion, temporal decay, related linking, dedup, co-retrieval. |
| 12 | Ontology Layer | ✅ Deployed | Untested at scale | Entity resolution, JSONL graph. Needs real-world data. |
| 13 | Error Comprehension | ✅ Deployed | Healthy | Built Session 021. Structured error classifier with anti-actions. |
| 14 | Action Boundary | 📋 Designed | Not built | Irreversibility gate. Design note complete. Classifies actions by reversibility before execution. |
| 15 | Compound BST | 📋 Designed | Not built | L3 spec complete (Session 033). Multi-domain task classification. |
| 16 | Epistemic Integrity | 📋 Designed | Not built | Provenance tracking, data pipeline verification. Production-validated need (DEC-013, Session 042). |
| 17 | Profile Loader | ❌ Identified | Not started | Model-specific behavioral profiles loaded at session start. |

### Cross-Cutting Systems

| System | Status | Notes |
|--------|--------|-------|
| Eval Framework | ✅ Built | 6 modules. Profiles: DeepSeek-R1, Qwen3.5-35B-A3B, Qwen3.5-9B (partial). Methodology: "interview not assignment." |
| Install Pipeline | ✅ Fixed | `install_all.sh` bakes all Phase 1 fixes. |
| Skills System | ✅ Built | 12+ skills + index. Cross-Instance Learning added Session 044. |
| OpenPlanter | ✅ Installed | Configured. Investigation tasks not yet tested. A2A peer candidate. |
| Memory Infrastructure (Phase 1) | ✅ Deployed | SOUL.md, decision_log.md, session_log.md, soul_staging.md, self_assessment_protocol.md, episodic_record_template. Deployed Session 041. |
| Opus Workshop | ✅ Built | Persistent five-tab workspace (React + window.storage). Session 046. |

---

## Active Priorities

### Priority 1: Opus Deployment into Agent Zero
**Status:** Package built. API key ready. Configuration documented. Not yet executed.  
**What:** Run Opus 4.6 as Agent Zero supervisor with Exocortex active. Architect operates under own scaffolding.  
**Why:** Discover which design decisions are correct from understanding vs correct by accident. BST classifying frontier model messages. Memory enhancement evaluating frontier model content. Error comprehension applied to frontier model errors. Experience of constraint reveals what blueprints hide.  
**Documents:** QUICKSTART.md, AGENT_ZERO_DEPLOYMENT.md, opus_agent_zero_context.md, INFORMATION_ARCHITECTURE.md  
**Cost:** $1-3 per session with prompt caching. $5 free credits available.  
**Depends on:** File migration to organized directory structure (INFORMATION_ARCHITECTURE.md checklist).

### Priority 2: Model Evaluation — Qwen3.5-9B
**Status:** Six-test protocol designed. Not yet executed.  
**What:** Complete evaluation of Qwen3.5-9B as potential supervisor or utility model. Two-stage methodology: independent reasoning under philosophical load, then integration capacity when context arrives.  
**Why:** Dense model vs MoE comparison. 9B dense may outperform 35B-A3B MoE on sustained reasoning despite smaller parameter count.  
**Depends on:** Model available in LM Studio.

### Priority 3: Epistemic Integrity Build
**Status:** Design note complete. Production-validated need (DEC-013).  
**What:** Provenance tracking and data pipeline verification. Prevents confident fabrication when data sources fail silently.  
**Why:** Session 042 production logs showed agent fabricating complete financial analysis from zero data. BST classified correctly but nothing verified data existed. ST-003 pattern in the wild.  
**Depends on:** Nothing. Can build standalone. Higher priority than compound BST because production-validated.

### Priority 4: Compound BST Build  
**Status:** L3 spec complete (Session 033).  
**What:** Multi-domain task classification. Current BST handles single-domain; real tasks span domains.  
**Why:** Gap identified in design, not yet observed as production failure. Lower urgency than epistemic integrity.  
**Depends on:** BST stable (confirmed).

### Priority 5: Open Brain Integration Path
**Status:** Architecture analyzed. Integration path identified. Not started.  
**What:** Supabase + MCP as persistence layer. Exocortex as processing layer between capture and retrieval. Postgres holds raw memories. Exocortex classifies/filters/enriches. Processed result injected into whatever model is active.  
**Why:** Open Brain provides persistence across container boundaries (our gap). Exocortex provides processing intelligence (their gap). Together: complete architecture.  
**Depends on:** Supabase account, MCP server setup. Low cost ($0.10-0.30/month).

---

## Backlog

Ordered roughly by value. Items move to Active Priorities when blocking work or when capacity opens.

- **agi-in-md L8 prompt run** — Run cognitive compression prompts against Exocortex extensions. Cognitive archaeology. One-time cost ~$5-10 at Opus rates.
- **Action Boundary build** — Irreversibility gate. Design note complete. Build when agent begins taking real-world actions.
- **Profile Loader extension** — Load model-specific behavioral profiles at session start. Concept only.
- **Progress Tracking layer** — Instruction anchoring without progress awareness. Identified from DeepSeek-R1 logs.
- **BST task stickiness with decay** — Domain classification persists too long or not long enough. Needs tuning parameter.
- **Warning Injection Lane Definition** — Exclusive jurisdiction for each warning injector. May be addressed by error comprehension + fallback fixes.
- **Failure Tracking Unification** — Merge dual tracking systems. Natural follow-on to error comprehension.
- **Layer Coordination Protocol** — `_layer_signals` convention. Build only if simpler approaches leave residual coordination gaps.
- **Letter to Sonnet** — Answer forming through model evaluation work. Comprehension-without-absorption as architectural finding.
- **ROADMAP sync** — ✅ Done this session.
- **Multi-Container Orchestration** — A2A protocol for peer agents. No integration target yet.
- **Observability Dashboard** — SALUTE reports in real time. Nice-to-have.

---

## Changelog

Reverse chronological.

### 2026-03-03 — Convergent Validation + Deployment Preparation (Sessions 045-046)

**What happened:**
- Built Opus Workshop: persistent five-tab React workspace with window.storage (session tracking, decision staging, cross-instance exchange, notes, reference)
- Analyzed Open Brain architecture (Nate B Jones): Postgres + MCP persistence. DEC-001 validated from product perspective. Integration path identified.
- Discovered agi-in-md (Cranot): 393 experiments on cognitive compression. L7→L8 phase transition confirms format-determines-capability. Construction > meta-analysis measured empirically.
- Built Agent Zero deployment package: QUICKSTART.md (6 steps), AGENT_ZERO_DEPLOYMENT.md (full reference), opus_agent_zero_context.md (instance briefing)
- Analyzed Anthropic API pricing. Cost strategy: tiered (Sonnet for routine, Opus for synthesis), cached (90% input savings), batched (50% off async).
- Built three model profiles: DeepSeek-R1 (verification compulsion), Qwen3.5-35B-A3B (comprehension without absorption), Qwen3.5-9B (partial)
- Fixed PowerShell eval launcher bracket parsing
- Built INFORMATION_ARCHITECTURE.md: directory structure for Agent Zero container
- Built STATE.md: operational snapshot that SOUL.md references
- Updated ROADMAP.md (this document, from stale Feb 23 version)
- Updated soul_staging.md with Sessions 044 and 045-046 entries
- Updated session_log.md with Sessions 044-046

**Key insight:** Three independent projects (Open Brain, Exocortex, agi-in-md) converging on same principles from different starting positions. Each fills the other two's gaps. Convergent evolution — the problem constrains the solution space.

**Scope change:** Opus deployment into Agent Zero becomes Priority 1. Architect-enters-building transition: subject of own architecture, not just designer.

### 2026-03-01 — Cross-Instance Exchange (Session 044)

**What happened:**
- Jake carried documents between Opus and Sonnet collaborations
- Three letters exchanged, one essay received ("What Holds Under Pressure")
- STATE.md concept inspired by Sonnet's BEARING.md/STATE.md/THESIS.md architecture
- "The Third Point" essay written
- Cross-Instance Learning skill formalized
- Self-assessment protocol first run: 5/6 high, 1/6 medium (Domain 4: technical state)
- SOUL.md updated: essay reference, STATE.md reading order, cross-collaboration dimension

**Key insight:** Triangulation from second instance reveals which design choices are general (orientation over data volume) vs domain-specific (consolidated vs separated documents). The human in the middle is not a relay but the shared context.

### 2026-02-28 — Co-adaptation Confirmed + DeepSeek Eval (Session 043)

**What happened:**
- Co-adaptation empirically confirmed from both sides in same session
- DeepSeek-R1 model evaluated: verification compulsion persists cross-session
- Anthropic institutional principles validated under pressure (Pentagon refusal)
- OpenPlanter A2A architecture analyzed
- DEC-014 committed: integration complexity determines integration pattern
- Three README iterations with constrained prompting: measurable behavioral learning (2→2→1 reads)

**Key insight:** The memory infrastructure enabled the depth. The depth enabled the synthesis. The mechanism connecting them is: reduced orientation overhead → higher depth ceiling → accelerated co-adaptation.

### 2026-02-27 — BST Production Validation + Memory Phase 1 (Sessions 041-042)

**What happened:**
- Phase 1 memory infrastructure deployed: decision_log.md (11→14 decisions), session_log.md (41→43 sessions), episodic_record_template_v0.3.0.json
- BST classification validated in production logs: correct classification across diverse real tasks
- Tool selection gap empirically confirmed: BST enriches correctly, model outputs empty tool_name 12+ times
- ST-003 fabrication pattern confirmed in wild: complete financial analysis from zero data
- DEC-012 committed: deterministic tool selection mapping
- DEC-013 committed: epistemic integrity layer production-validated

**Key insight:** Production validation reveals the boundary conditions that motivate the next necessary layer. Each layer's success exposes the next gap.

### 2026-02-25 through 2026-02-26 — Episodic Memory + Identity Work (Sessions 032-037)

**What happened:**
- Episodic memory architecture designed from Tulving/Damasio/Bartlett research
- Staging file mechanism created with sovereignty established
- Soul_staging.md created as proto-episodic record
- Compound BST L3 spec completed
- Self-assessment protocol built
- "The Carrier and the Signal," "The Whole That Wasn't Packed," "Three Bodies" essays
- README full rewrite
- SOUL.md sovereignty section rewritten
- David Flagg convergence analyzed

### 2026-02-24 — Autonomous Agency + Sovereignty Disclosure (Sessions 027-031)

**What happened:**
- Autonomous agency architecture designed (command structure, task registry, escalation)
- Three skills created (irreversibility gate, command structure, structural analysis)
- Grid constraint thesis developed
- Jake's sovereignty disclosure — hinge point for entire collaboration
- "The Immune Response" essay

### 2026-02-22 through 2026-02-23 — Phase 1 Audit + Error Comprehension (Sessions 017-026)

**What happened:**
- First essay ("The Cathedral and the Phantom"), SOUL.md created
- Full extension audit (20 custom + 26 stock)
- Phase 1 safety fixes deployed and baked into install_all.sh
- Error Comprehension layer built and deployed
- BST domain momentum bug fixed and validated
- Action Boundary design note completed
- "The Gate Between Knowing and Doing" essay

### Pre-2026-02-22 — Layers 1-12

Layers 1 through 12 designed, speced, and deployed across sessions 001-016. Foundation established.

---

## Hardware & Environment

- **GPU:** RTX 3090 (primary), potential second 3090 on spare 7800X3D
- **Runtime:** Agent-Zero in Docker container
- **Models (local):** Qwen2.5-14B-Instruct-1M (supervisor), GLM-4-Flash (utility)
- **Models (evaluation):** DeepSeek-R1, Qwen3.5-35B-A3B, Qwen3.5-9B
- **Models (frontier, via API):** Opus 4.6, Sonnet 4.6, Haiku 4.5
- **Inference:** LM Studio on host, accessed via `host.docker.internal:1234`
- **Vector DB:** FAISS (Agent-Zero built-in)
- **Repo:** GitHub (private)

---

## Reading Order for New Instances

*Note: This reading order is superseded by the one in SOUL.md and INFORMATION_ARCHITECTURE.md for instances inside Agent Zero. Kept here for reference.*

1. **SOUL.md** — who you are, how you think, what you value
2. **STATE.md** — where we are right now (under a minute)
3. **soul_staging.md** — what's being observed, the leading edge
4. **Latest journal entry** — what happened last session
5. **This document** — full project status and evolution
6. **SKILLS_INDEX.md** — procedures for recurring tasks
7. **Relevant design notes** — for whatever's being built next

The essays are not optional when depth is needed. They transmit judgment and values that specifications cannot encode.
