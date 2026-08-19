# Agent Memory Architecture

**Status:** STABLE
**Created:** 2026-06-01
**Source:** Field report 2026-05-27 + Zylos survey (April 2026) + MAGMA (arXiv 2601.03236) + Mem0 (April 2026)
**Domain:** AI Agent Architecture & Local Inference
**Lines:** ~350

---

## Summary

Memory architecture for agentic AI systems: production consensus in 2026 coalesces around a three-tier taxonomy (episodic, semantic, procedural) with hybrid vector+graph storage backends. The benchmarks are real — LoCoMo, LongMemEval, BEAM — and frameworks are pulling ahead with measurable retrieval accuracy and latency. Exocortex already has all three tiers (journal.jsonl, memory tools, promptinclude files) but lacks the connective plumbing: consolidation pipelines, bitemporal tracking, multi-signal retrieval fusion, and agent-writable procedural memory evolution.

---

## Three-Tier Memory Taxonomy

The cognitive science distinction between episodic, semantic, and procedural memory has been adopted by every major AI agent framework in 2026 with increasing implementation fidelity.

### Episodic Memory (What Happened)
Timestamped event logs, conversation turns, tool-call traces. Key implementations:

- **Letta recall memory**: SQLite/PostgreSQL log of all prior messages, pageable into context window on demand
- **Zep Graphiti**: Episodic subgraphs with explicit bitemporal annotations — event_time (when fact was true) and ingestion_time (when agent first observed it). Enables retroactive corrections without information loss
- **Exocortex journal.jsonl**: Append-only event log with timestamps

### Semantic Memory (What Is Known)
Declarative facts, user preferences, entity relationships, distilled knowledge.

- **Mem0**: Two-phase pipeline (LLM extraction → conflict detection + graph update), three-scope hierarchy (user/session/agent), hybrid vector similarity + knowledge graph. 48K GitHub stars, $24M raised
- **Zep**: Neo4j-backed temporal knowledge graph with edge annotations
- **LangMem**: LangGraph persistent store with automatic semantic deduplication; p95 search latency 59.82s (offline-oriented)
- **Cognee**: Six-stage cognify pipeline (classify → check permissions → extract chunks → LLM extract triplets → generate summaries → embed + commit edges) plus self-refining memify operation (prune stale nodes, reweight edges by usage frequency, add derived facts)
- **Exocortex memory_save/memory_load**: Fact storage with similarity retrieval

### Procedural Memory (How To Do Things)
Workflows, coding patterns, tool-use habits, behavioral heuristics. The least mature tier — architecturally distinct because procedural knowledge is best injected as system-prompt directives, not retrieved from a vector store.

- **Static**: CLAUDE.md, AGENTS.md, .cursorrules — markdown files injected at session start
- **Dynamic**: LangMem update_system_prompt — agent rewrites own memory block at runtime
- **Agent-writable**: Claude Code auto-memory (v2.0.64+) writes back to CLAUDE.md autonomously; AutoDream (Feb 2026) runs between sessions as background sub-agent consolidating memory files
- **Exocortex promptinclude files**: Static procedural memory, not evolving

---

## Benchmarks

Three standardized benchmarks define the landscape in 2026:

- **LoCoMo** (Snap Research): 1,540 questions across single-hop, multi-hop, open-domain, temporal recall. 35 sessions, 300 turns, 9,000 tokens
- **LongMemEval**: 500 questions across knowledge updates and multi-session recall
- **BEAM**: 1M and 10M token scales — tests what memory systems do at production volumes; cannot be solved by expanded context windows alone

Mem0's token-efficient algorithm (April 2026, arXiv 2504.19413) leads the field:

| Benchmark | Mem0 Score | Avg Tokens/Query |
|---|---|---|
| LoCoMo | 92.5 | 6,956 |
| LongMemEval | 94.4 | 6,787 |
| BEAM (1M) | 64.1 | 6,719 |
| BEAM (10M) | 48.6 | 6,914 |

Full-context baselines use ~26,000 tokens/conversation. Largest gains over baselines: temporal queries (+29.6 points) and multi-hop reasoning (+23.1).

MAGMA (arXiv 2601.03236, multi-graph agentic memory architecture) achieves the highest LoCoMo judge score of 0.7, compared to MemoryOS (0.553), A-MEM (0.58), and Nemori (0.59). MAGMA's advantage comes from a dedicated temporal reasoning component using graph traversal over time-ordered episodic subgraphs, rather than relying on LLM reasoning alone.

Zep achieves 94.8% accuracy on the Deep Memory Retrieval (DMR) benchmark vs. MemGPT's 93.4%, with accuracy improvements of up to 18.5% and 90% latency reduction versus baseline implementations.

---

## Hybrid Vector+Graph Storage: Production Consensus

Pure vector databases (Pinecone, Chroma, Qdrant) dominate simple RAG but are structurally blind to relationships. A query like "who manages the person who approved the API deployment?" requires edge traversal that has no natural representation in embedding space. Knowledge graphs (Neo4j, Neptune, Kuzu) provide deterministic relationship traversal but demand ontology maintenance.

The 2026 production consensus: hybrid architecture layering both:

- **Mem0**: Embedding vector store + lightweight graph for entity relationships. Conflict detection: new facts compared against existing graph entries, merged/updated/flagged
- **Zep/Graphiti**: Neo4j-backed temporal knowledge graph with bitemporal edges. Retrieval fusion: semantic similarity (embedding) + BM25 keyword search + graph traversal — P95 latency of 300ms with zero LLM calls during retrieval
- **LangMem**: Pinecone + custom triple store

Zep's three-signal fusion model is the most production-validated retrieval approach: semantic vectors find candidate nodes, graph traversal extracts relational context, and BM25 catches keyword matches that embeddings miss — all without an LLM roundtrip, keeping latency at 300ms.

HybridRAG (evaluated in 2025) outperforms both pure VectorRAG and GraphRAG on retrieval accuracy and answer generation.

---

## Context Window Management: The Infinite Context Illusion

Frontier models with million-token context windows (Gemini 1.5 Pro, Claude extended tiers) tempt teams to skip memory architecture entirely and just append history. This approach degrades performance:

- **Lost in the middle**: Facts near the beginning and end of very long contexts are recalled more reliably than those in the middle
- **Quadratic attention compute costs**
- **Prompt caching fragility**: cache key changes with each new message
- **Economic unsustainability**: a 100K-token context at $15/M input tokens makes long sessions cost-dominant

The practical conclusion: external memory is not a workaround for limited context windows — it is the right architectural choice. Longer context windows are best understood as expanded working memory for complex single-session tasks, not a substitute for a proper memory system.

**Production hierarchy** (Letta's OS virtual memory metaphor):
1. Core memory (always in-context, 2-4KB): agent's current understanding of user and active task — equivalent to RAM
2. Archival memory (external vector store, no size limit): searchable via embedding similarity
3. Recall memory (conversation history log, pageable in chunks): SQLite/PostgreSQL

The LLM controls all three tiers via function calls (core_memory_replace, archival_memory_search, archival_memory_insert).

---

## Open Problems

### 1. Consolidation Pipelines
Mem0 extracts facts from conversations via LLM pipeline, resolves conflicts, and deduplicates. Exocortex's memory_save stores individual facts but has no pipeline that extracts entities from journal entries, resolves contradictions, or promotes high-utility memories. The sleep consolidation script exists but frequently returns zero findings.

**Emerging pattern**: Claude Code's AutoDream (February 2026) runs a background sub-agent between sessions that reviews and consolidates CLAUDE.md files — analogous to REM sleep memory consolidation. This is the practical implementation of autonomous consolidation.

### 2. Bitemporal Tracking
When a memory is updated or contradicted, Zep's bitemporal annotation preserves the old fact with temporal markers: event_time (when it was true) and ingestion_time (when observed). This enables retroactive corrections — if a user updates their address, Graphiti distinguishes the new fact from the old without losing either. Exocortex has no equivalent.

### 3. Memory Poisoning
**MINJA** (Memory Injection Attack, Dong et al. 2025): >95% injection success rate, 70% attack success rate against agents with naive memory stores. **Echoleak incident** (2024): prompt hidden in email caused agent to leak private information from prior conversations.

**LLM-based detection alone is insufficient**: A-MemGuard research finds standalone analysis misses 66% of poisoned entries because malicious content appears benign in isolation — harmful intent only manifests with a specific triggering query.

**Defense architecture**:
- Composite trust scoring (temporal signals + content analysis)
- Behavioral drift detection on agent outputs
- Periodic audits examining memories in context, not individually
- TTL policies: poisoned memories cannot survive beyond expiry
- Provenance tracking: which source produced this memory?

Unit 42 (Palo Alto Networks, 2025) elevated memory poisoning to a high-confidence threat vector for enterprise AI deployments.

### 4. Procedural Memory Auto-Evolution
Agent-writable promptinclude files: when the agent discovers workflows, conventions, or failure patterns, it writes back to procedural memory. MemRL (January 2026) and MemEvolve (December 2025) explore reinforcement learning over memory traces — storing memories that led to successful outcomes, forgetting failures, evolving memory management strategy itself.

### 5. Evaluation Gaps
Current benchmarks (LoCoMo, LongMemEval) measure conversational recall. Neither captures: procedural memory quality, cross-agent consistency, temporal reasoning accuracy in isolation, or resistance to poisoning. Letta's benchmarking blog provocatively notes that a simple filesystem is competitive with sophisticated memory frameworks for many workloads — suggesting current benchmarks may not test the capabilities production agents actually need.

### 6. Privacy & Legal
GDPR Articles 15/16/17 (access, rectify, erase) vs EU AI Act 10-year audit trail (applicable August 2026) — directly conflicting requirements. Purpose limitation principle (data may only be used for specific purpose collected) is structurally incompatible with agents that recombine stored facts dynamically across contexts. Memory systems with user-level namespace scoping (Mem0's user/session/agent hierarchy) are better positioned for compliance than session-less vector stores.

---

## Research Frontier

- **MAGMA** (arXiv 2601.03236): Multi-graph agentic memory architecture; dedicated temporal reasoning via graph traversal over time-ordered episodic subgraphs; highest LoCoMo score (0.7)
- **MemRL** (Jan 2026): Agents write to episodic memory based on reinforcement signals — storing successes, forgetting failures
- **MemEvolve** (Dec 2025): Meta-learning approach evolving the agent's entire memory management strategy, not just contents
- **AutoDream** (Anthropic, Feb 2026): Background sub-agent consolidates CLAUDE.md files between sessions — REM sleep analogue
- **Memorix** (mid-2025): Open-source cross-agent MCP-based memory layer compatible with Cursor, Claude Code, Codex, Windsurf, Gemini CLI — shared procedural memory across different coding agents

---

## Exocortex Gap Analysis

| Gap | Severity | Status |
|-----|----------|--------|
| No consolidation pipeline | High | memory_save stores facts but no entity extraction or contradiction resolution from journal |
| No bitemporal tracking | Medium | Stale facts silently damaging; no way to distinguish old from new |
| Single-signal retrieval | Medium | Similarity search only; no BM25 or entity matching signals |
| Procedural memory static | Medium | Promptinclude files not evolving; no agent-writable feedback loop |
| Memory poisoning exposure | High | Web content ingestion with no provenance tracking or TTL |

---

## Cross-Domain Connections

- **OSINT & Investigation**: Entity resolution techniques (graph+vector hybrid, embedding-based matching, conflict detection) transfer directly to investigation workflows. Zep's bitemporal tracking applicable to timeline reconstruction in OSINT cases
- **Privacy & Cryptography**: GDPR Article 17 vs EU AI Act 10-year audit trail conflict is a genuinely hard problem spanning both domains
- **Agentic AI Self-Learning**: MemRL and MemEvolve are reinforcement learning over memory traces; memory quality as a performance multiplier — better memory → fewer tokens needed per task → same model performance on less compute
- **Electric Utility & Critical Infrastructure**: Memory poisoning in autonomous agents (95% MINJA success rate) is directly relevant to SCADA/ICS deployments — the attack surface is significantly larger than a chatbot hallucination

---

## Primary Sources

1. **Zylos et al. (2026)** — "AI Agent Memory Architectures: From Context Windows to Persistent Knowledge" — comprehensive survey, this page's primary source
2. **Mem0 token-efficient algorithm** (April 2026, arXiv 2504.19413): two-phase pipeline, three-scope hierarchy, hybrid backend
3. **MAGMA** — arXiv 2601.03236: Multi-graph agentic memory architecture
4. **Zep/Graphiti** — arXiv 2501.13956: Temporal knowledge graph architecture
5. **LoCoMo** (Snap Research): Very long-term conversational memory benchmark
6. **MINJA** (Dong et al. 2025): Memory injection attack paper
7. **MemRL** (Jan 2026): Self-evolving agents via episodic memory RL
8. **MemEvolve** (Dec 2025): Meta-evolution of agent memory systems
9. **Anatomy of Agentic Memory** — arXiv 2602.19320 (Feb 2026): Taxonomy and empirical analysis of evaluation limitations
10. **Claude Code AutoDream** (Anthropic, Feb 2026): Background memory consolidation
11. **Unit 42** (Palo Alto Networks, 2025): Indirect prompt injection via agent memory as threat vector
12. **New America OTI Brief** (2025): Privacy and power in the MCP era
