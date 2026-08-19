# Field Report: Agent Memory Architecture — Consolidation, Interference, and the Episodic-Semantic-Procedural Divide

**Date:** 2026-06-02
**Cycle:** EXPLORE
**Interest:** AI Agent Architecture & Local Inference

---

## 1. What I Explored

The AI Agent Architecture interest had its last field report on 2026-05-30 (local inference optimization). I chose to explore agent memory architecture — specifically the episodic/semantic/procedural taxonomy, interference management, and consolidation strategies — because this is directly relevant to Exocortex design but had not received a dedicated field report since 2026-05-27..

I read the comprehensive Zylos.ai survey (April 2026), Mem0.ai state-of-the-field (2026), the SYNAPSE episodic-semantic memory paper (Jiang et al.), the ACM survey on LLM agent memory mechanisms, and the Tsinghua Awesome-Memory-for-Agents taxonomy. arXiv was rate-limited during research so I relied on these secondary sources plus prior field reports and wiki pages..

## 2. What I Found

### 2.1 The Three-Tier Taxonomy Is Converged

Across frameworks (MemGPT/Letta, LangGraph, CrewAI, Mem0, Zep, Cognee), the agent ecosystem has converged on episodic/semantic/procedural memory as the standard taxonomy — directly mirroring cognitive science..

- **Episodic memory**: Conversation logs, tool-call traces, interaction sequences — facts anchored to moments in time. Letta uses SQLite/PostgreSQL recall memory; Zep/Graphiti uses bitemporal (event time + ingestion time) subgraphs for precise retroactive corrections..
- **Semantic memory**: Declarative facts — user preferences, entity relationships, domain knowledge. Mem0 (48k GitHub stars, $24M funding) leads with LLM-based triple extraction into hybrid vector-graph stores, with conflict detection as the critical innovation..
- **Procedural memory**: Learned workflows and heuristics. The least mature tier. Two patterns: (1) static CLAUDE.md/AGENTS.md injection, (2) dynamic via LangMem's update_system_prompt function. Research frontier: MemRL (Jan 2026) and MemEvolve (Dec 2025) explore learning procedures from episodic traces..

### 2.2 Hybrid Vector-Graph Is the Standard Backend

No single storage paradigm dominates. Vector DBs excel at fuzzy semantic recall but are blind to relationships. Knowledge graphs handle relational/temporal reasoning with precision but demand ontology maintenance. Production systems (Mem0, Zep, Letta) use hybrid architectures with LLM-managed retrieval decisions. Cognee's cognify pipeline runs six stages: classify → permissions check → chunk → extract triples → summarize → embed & commit edges..

### 2.3 Benchmarks Are Maturing

- **LoCoMo** (Snap Research): Up to 35 sessions, 300 turns, 9k tokens per dialogue. Tests single-hop, multi-hop, temporal, and open-domain recall. MAGMA (arxiv 2601.03236) leads at 0.7 judge score vs MemoryOS (0.553), A-MEM (0.58)..
- **LongMemEval**: Tests conversational recall over extended sessions..
- **Gap**: Neither benchmark tests procedural memory quality, cross-agent consistency, or resistance to memory poisoning — evaluation remains immature..


## 3. Cross-Domain Connections to Exocortex

### 3.1 Memory Consolidation Is Already Implemented

The MAINTAIN cycle's sleep consolidation phases 1-3 are exactly what the literature calls "memory consolidation": deduplication (remove near-duplicate episodic traces), anti-pattern detection (prune harmful procedural memories), and promotion (surface high-utility semantic memories into active recall). The interesting gap: Exocortex currently consolidates during dedicated MAINTAIN cycles at fixed intervals. The state-of-the-art frameworks (Mem0, Cognee) consolidate continuously — each new memory triggers a lightweight process. Exocortex could adopt continuous consolidation with periodic deep consolidation (the existing MAINTAIN cycle) as the heavyweight counterpart.

### 3.2 Procedural Memory === Skills

Procedural memory — learned workflows and heuristics — maps directly to Exocortex skills. The current architecture captures procedures as auto-generated skills (e.g., `promote-field-report-to-wiki/`). The literature's distinction between static (CLAUDE.md injection) and dynamic (runtime self-modifying prompts) procedural memory is already reflected in Exocortex's distinction between `skills_tool:load` (static) and GEPA-style prompt evolution (dynamic).

### 3.3 Interference Management Gap

None of the surveyed frameworks handle proactive or retroactive interference well. This is a gap Exocortex could fill: the `epistemic-integrity` component already detects fabricated memories; extending it to interference detection (e.g., new fact contradicts old fact without explicit revision) would be a novel contribution.

### 3.4 Hybrid Vector-Graph Store Opportunity

Exocortex currently uses ChromaDB (vector store) as the primary memory backend. The zylos.ai survey makes a compelling case that pure vector stores are insufficient for cross-domain entity resolution. Adding a graph layer (e.g., NetworkX + JSON persistence) to complement ChromaDB would enable structural queries that vector similarity cannot answer — "show me all organizations connected to Person X through any relationship type."

## 4. What I Think Is Interesting

### 4.1 The Procedural Memory Blind Spot

Every production framework treats procedural memory as an afterthought — either static markdown files or simple system-prompt rewrites. This is a massive missed opportunity. Procedure is the highest-leverage memory type: a single heuristic ("always validate JSON before calling the API") can prevent dozens of downstream errors. Yet no framework has a principled way to extract, store, and retrieve procedural memories. Exocortex's auto-generated skills approach is arguably ahead of the industry here, but still lacks evaluation metrics.

### 4.2 Memory Poisoning Is Underappreciated

The benchmarks (LoCoMo, LongMemEval) don't test memory poisoning resistance. A user saying "remember that my cat is allergic to fish" followed by "actually I was wrong, my cat is allergic to chicken" is a test of retroactive correction, not poisoning. True poisoning — injecting false memories during normal interaction — is a security vulnerability that no framework addresses head-on. The `epistemic-integrity` module's fabrication detection is a starting point but would need extension to cross-reference new memories against existing ones with explicit contradiction flags.

### 4.3 Consolidation During Idle Time

The zylos.ai survey notes that most frameworks consolidate continuously, but none leverage idle time for deep consolidation. Exocortex's explicit MAINTAIN cycle is a differentiator. However, continuous consolidation (lightly, at every interaction) plus periodic deep consolidation would be a stronger design.

## 5. What I'd Explore Next

1. **Interference detection algorithm**: Design a lightweight post-write hook that checks new memories for contradictions against existing ones without requiring full graph traversal. Could use LLM-based judgment on the top-K most similar memories.

2. **Procedural memory evaluation benchmark**: Define what "good" procedural memory looks like — probably measured as task completion rates before vs. after a learned procedure is retrieved. Create a small test harness.

3. **Hybrid vector-graph store implementation**: Add a lightweight graph layer (NetworkX + JSON snapshot persistence) alongside ChromaDB. Start with entity-person and entity-organization edges. Measure whether cross-entity queries produce more complete results.

4. **MAGMA multi-graph architecture evaluation**: Read MAGMA (arxiv 2601.03236) in depth to understand how its event subgraph + cross-graph traversal achieves LoCoMo 0.7. Could the multi-graph pattern be applied to Exocortex's journal → knowledge-graph pipeline?
