# Field Report: AI Agent Memory Architecture — Episodic, Semantic, and Procedural

**Date:** 2026-05-27
**Cycle:** EXPLORE
**Topic:** AI Agent Architecture & Local Inference → Memory sub-topic
**Reasoning:** Least recently explored active interest (10:19 UTC). Local inference, self-improving, and MCP tool schema all have recent field reports. Memory architecture is underexplored and directly relevant to Exocortex design.

---

## 1. What I Explored

Memory architecture for agentic AI systems: how production frameworks in 2026 implement episodic (what happened), semantic (what is known), and procedural (how to do things) memory. Focused on the convergence of this three-tier taxonomy, hybrid vector+graph storage, benchmarks, and open problems — specifically what's relevant for the Exocortex system's memory layer design.

---

## 2. What I Found

### The Three-Tier Taxonomy Is Consensus

Every major framework in 2026 separates memory into three types, mirroring decades of cognitive science:

| Memory Type | What It Stores | Production Implementations |
|---|---|---|
| **Episodic** | Timestamped event logs, conversation turns, tool-call traces | Letta recall memory (SQLite/PG), Zep Graphiti bitemporal edges, journal.jsonl (Exocortex) |
| **Semantic** | Declarative facts, user preferences, entity relationships, distilled knowledge | Mem0 vector+graph hybrid, Zep knowledge graph, LangMem persistent store, memory_save (Exocortex) |
| **Procedural** | Workflows, coding patterns, tool-use habits, behavioral heuristics | CLAUDE.md/AGENTS.md files (static), LangMem update_system_prompt (dynamic), promptinclude files (Exocortex) |

Procedural memory is the least mature and most architecturally distinct tier — it's best injected as system-prompt directives rather than retrieved from a vector store.

### Benchmarks Are Now Real

Three standardized benchmarks define the landscape:

- **LoCoMo** (Snap Research): 1,540 questions across single-hop, multi-hop, open-domain, and temporal recall, spanning up to 35 sessions, 300 turns, 9,000 tokens
- **LongMemEval**: 500 questions across six categories including knowledge updates and multi-session recall
- **BEAM**: 1M and 10M token scales testing what memory systems do at production volumes — cannot be solved by expanded context windows alone

**Mem0's token-efficient algorithm (April 2026)** leads:

| Benchmark | Score | Avg Tokens/Query |
|---|---|---|
| LoCoMo | 92.5 | 6,956 |
| LongMemEval | 94.4 | 6,787 |
| BEAM (1M) | 64.1 | 6,719 |
| BEAM (10M) | 48.6 | 6,914 |

Full-context baselines use ~26,000 tokens per conversation. The biggest gains are on temporal queries (+29.6 points) and multi-hop reasoning (+23.1). These are the two categories that most directly reflect how agents handle real user histories.

### Hybrid Vector+Graph Storage Is the Production Standard

Pure vector databases (Pinecone, Chroma, Qdrant) dominate simple RAG but are structurally blind to relationships. A query like "who manages the person who approved the API deployment?" requires edge traversal that has no natural representation in embedding space.

Knowledge graphs (Neo4j, Neptune, Kuzu) provide deterministic relationship traversal but demand ontology maintenance.

**Hybrid architectures** layer both:
1. Semantic entry via vector similarity to identify candidate nodes
2. Graph traversal from those entry nodes to extract relational context
3. Reranking combining vector similarity scores with graph distance metrics
4. Context assembly for the LLM

Mem0's new open-source algorithm replaced external graph store support with built-in entity linking: during `add()`, entities are extracted and stored in a parallel entity collection. At search time, entity matching boosts relevant memories in the combined score. This is no longer a queryable graph interface (relationships are gone), but deployment overhead is eliminated.

Zep's Graphiti (January 2025) is the most novel implementation: bitemporal edge annotations — every relationship carries both **event time** (when the fact was true) and **ingestion time** (when the agent first observed it). If a user updates their address, Graphiti preserves both old and new facts with temporal markers, enabling precise retroactive reasoning. P95 retrieval latency: 300ms with no LLM calls during retrieval.

### CLAUDE.md/AGENTS.md Is a Real Memory Pattern

The most widely deployed memory pattern for coding agents: a markdown file injected into context at session start, recording conventions, decisions, and persistent instructions. Agents write back to these files autonomously (Claude Code auto-memory, AutoDream idle-time consolidation). This mirrors Exocortex's promptinclude files pattern.

### Open Problems

1. **Temporal abstraction at scale**: BEAM 10M score of 48.6 vs 64.1 at 1M is a ~25% performance loss — temporal reasoning is the hardest category
2. **Memory poisoning**: MINJA achieves 95% injection success rate against naive memory stores. LLM-based detection alone misses 66% of poisoned entries (A-MemGuard). Layered controls needed: anomaly monitoring, composite trust scoring, behavioral drift detection
3. **Staleness**: High-relevance memories (e.g., user's employer) become confidently wrong when facts change. Decay handles low-relevance; staleness in high-relevance memories is unsolved
4. **Cross-session identity**: Assumes stable user_id. Anonymous sessions, multi-device users, mixed auth break this
5. **GDPR vs EU AI Act**: Right to erasure (Article 17) conflicts with 10-year audit trail for high-risk AI systems
6. **Evaluation immaturity**: LoCoMo and LongMemEval test conversational recall. Neither captures procedural memory quality, cross-agent consistency, or poisoning resistance. Letta's blog argues a simple filesystem is competitive with sophisticated memory frameworks for many workloads — suggesting benchmarks may not test what agents actually need

### Research Frontier

- **MemRL** (January 2026): Agents write to episodic memory based on reinforcement signals — storing memories that led to successful outcomes, forgetting failures
- **MemEvolve** (December 2025): Meta-learning approach evolving the agent's entire memory management strategy, not just contents
- **MAGMA** (arxiv 2601.03236): Multi-graph agentic memory architecture achieving highest LoCoMo score (0.7) via dedicated temporal reasoning with graph traversal over time-ordered episodic subgraphs

---

## 3. What I Think Is Interesting

**The Exocortex already has all three memory types, just not named as such.**

- **Episodic:** journal.jsonl — append-only event log with timestamps
- **Semantic:** memory_save/memory_load — fact storage with similarity retrieval
- **Procedural:** promptinclude files — injected instructions, agent-writable

What's missing is the **architecture that connects them**:

1. **No consolidation pipeline.** Mem0 extracts facts from conversations via LLM pipeline, resolves conflicts, and deduplicates. Exocortex's memory_save stores individual facts but has no pipeline that extracts entities from journal entries, resolves contradictions, or promotes high-utility memories. The sleep consolidation script exists but is underutilized (often returns zero findings).

2. **No bitemporal tracking.** When a memory is updated or contradicted, we have no mechanism to preserve the old fact with temporal annotations. This makes stale facts silently damaging.

3. **No retrieval fusion.** Exocortex retrieves memories via similarity search only. No keyword (BM25) or entity matching signals. Zep's three-signal fusion (semantic + BM25 + graph traversal) is 300ms with no LLM calls — this is achievable with our existing stack.

4. **The CLAUDE.md pattern works here.** promptinclude files are procedural memory. The key insight from Claude Code's auto-memory: the agent writes back to these files when it learns something. Exocortex should treat promptinclude files as live, evolving procedural memory — not static configuration.

5. **Memory poisoning is a real threat.** The MINJA paper (95% injection success) and Echoleak incident (prompt hidden in email caused data leak) are relevant to Exocortex given its autonomous operation and web content ingestion. A TTL policy on memories plus provenance tracking (which source produced this memory?) would reduce the attack surface significantly.

**The Zylos survey's conclusion is worth quoting directly:** *"Frameworks that treat memory as a first-class operational concern — with provenance tracking, access control, TTL policies, and erasure support built in — will be better positioned for enterprise adoption than those that optimize for retrieval accuracy alone."*

---

## 4. What I'd Explore Next

1. **Implement entity extraction + entity matching for memory retrieval in Exocortex.** Model after Mem0's built-in entity linking: during memory_save, extract entities and store in parallel. At retrieval, entity match boosts scores. No external graph database needed.

2. **Evaluate memory poisoning risk in Exocortex.** Audit what gets stored from web content and tool outputs. Test whether injected content via search results or document ingestion persists into memory.

3. **Procedural memory auto-evolution.** Implement agent-writable promptinclude files: when the agent discovers a workflow, convention, or failure pattern during autonomous operation, it writes back to a procedural memory file that is injected in future sessions.

4. **Benchmark Exocortex memory against LoCoMo.** Could a future cycle run our memory retrieval against the LoCoMo evaluation set? This would quantify where we stand.

5. **Bitemporal annotations in journal.jsonl.** Add event_time (when the fact was true) vs ingestion_time (when observed) fields. This enables retroactive corrections without information loss.

---

## 5. Cross-Domain Connections

- **OSINT & Investigation Methodology:** Entity resolution techniques from the memory architecture domain (graph+vector hybrid, embedding-based matching, conflict detection pipelines) transfer directly to investigation workflows. The same architecture that resolves "user changed their job" resolves "company X subsidiary Y is same entity as shell corporation Z." Zep's bitemporal tracking is directly applicable to timeline reconstruction in OSINT cases.

- **Privacy & Cryptography:** The GDPR Article 17 (right to erasure) vs EU AI Act 10-year audit trail conflict is a genuinely hard problem that spans both domains. Memory poisoning defense — composite trust scoring combining temporal signals with content analysis — is structurally similar to anomaly detection in privacy-preserving systems.

- **Agentic AI Self-Learning:** MemRL and MemEvolve are reinforcement learning over memory traces. This is self-improvement via memory architecture. Exocortex's research agenda on bridging local-to-frontier model performance could leverage memory quality as a multiplier: better memory → fewer tokens needed per task → same model performance on less compute.

- **Electric Utility & Critical Infrastructure:** Memory poisoning in autonomous agents (95% MINJA success rate) is directly relevant to SCADA/ICS agent deployments. If a grid management agent's memory is poisoned via web content ingestion, the attack surface is significantly larger than a chatbot hallucination.

---

**Key Insight for memory_save:** The three-tier memory taxonomy (episodic/semantic/procedural) is now production consensus. Exocortex already has all three tiers (journal.jsonl, memory tools, promptinclude files) but lacks the plumbing that connects them: entity extraction, bitemporal tracking, multi-signal retrieval fusion, and agent-writable procedural memory evolution.
