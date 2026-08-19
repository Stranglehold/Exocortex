# Context Management in AI Agent Frameworks
## Status: STABLE
## Last updated: 2026-05-31

Survey of context window management approaches across autonomous AI agent frameworks (2025-2026).

---

## 1. Memory Taxonomy Convergence

The agent ecosystem has converged on a three-tier cognitive model:

| Memory Type | What It Stores | Implementation |
|---|---|---|
| Episodic | Past events, traces, sequences | Vector DB for fuzzy recall |
| Semantic | Facts, relationships, domain knowledge | Hybrid vector-graph (Mem0, Zep/Graphiti, Letta) |
| Procedural | How-to, workflows, tool schemas | Declarative injection (CLAUDE.md, AGENTS.md, rules, SKILL.md) |

## 2. Context Compression Approaches

### 2.1 KV-Cache Pruning
- **SnapKV** (2024): key-value cache compression by identifying important KV pairs via attention weight analysis. Reduces memory by 2-4x with minimal accuracy loss.
- **CompressKV** (2025): adaptive KV selection using budget-aware allocation; up to 6.8x compression.
- **Exocortex Context Pruner**: entropy-based pruning that monitors attention distribution entropy to decide what to keep vs discard.

### 2.2 Rolling Summarization
- **MemGPT/Letta**: hierarchical context management with core memory + archival storage. Automatic context paging.
- **Recursive Summarization**: progressive summarization where older turns are recursively compressed.
- **Claude's Approach**: long-context native support (200K tokens) with efficient attention mechanisms; no explicit pruning needed for most tasks.

### 2.3 Filesystem Offloading
- **Letta**: previous context stored in filesystem-based archival memory; retrieved on demand.
- **Mem0**: vector database for semantic recall.
- **Zep/Graphiti**: knowledge graph with temporal edges for relationship-aware recall.

## 3. Declarative Memory Injection

### 3.1 Instruction File Pattern
- **CLAUDE.md / AGENTS.md**: framework-agnostic declarative instruction files that conditionally inject procedural memory.
- **SKILL.md** (Exocortex): skill files as procedural memory with templated injection.
- **Bolt.new Rules**: domain-specific rules injected into system prompt.

### 3.2 Prompt Compression
- **LLMLingua** (2024): token-level prompt compression via smaller LM distillation.
- **Selective Context** (2024): lexical units scoring for fine-grained context selection.
- **GEPA** (Exocortex): goal-evaluated prompt augmentation with closed-loop evaluation.

## 4. Production Patterns and Failure Modes

### 4.1 What Works
- Hierarchical memory architecture (core, working, archival) is production-proven in Letta/MemGPT.
- Vector DB for episodic memory is reliable at scale.
- Declarative instruction injection shows consistent gains across frameworks.

### 4.2 What Breaks
- **Context rot**: stale facts in context override fresh retrieval results.
- **Attention dilution**: long contexts cause loss of focus on recent instructions.
- **Memory poisoning**: adversarial corruption of memory stores — underexplored.
- **KV-cache privacy leakage**: compressed caches can leak PII.

## 5. Cross-Domain Connections

| Domain | Connection |
|---|---|
| OSINT & Investigation | Memory poisoning detection ~ OSINT source reliability (Admiralty Code) |
| Privacy & Cryptography | KV-cache privacy leakage requires encryption standards |
| History of Intelligence | Procedural memory decay ~ institutional knowledge loss |
| Markets & Financial Analysis | Context exhaustion ~ information overload in trading |
| Electric Utility | Filesystem offloading on pressure ~ SCADA historian compression |

## References

1. Zylos AI Memory Taxonomy Survey (April 2026)
2. Letta/MemGPT hierarchical context management
3. SnapKV, CompressKV papers (2024-2025)
4. Claude 200K context architecture
5. Exocortex Context Pruner implementation
6. KV-cache privacy research

## 6. 2026 Production Landscape and New Techniques

### 6.1 Context Drift Is the Dominant Failure Mode
- **65% of enterprise AI failures** in 2025 attributed to context drift/memory loss during multi-step reasoning (not raw context exhaustion).
- At **95% per-step reliability** in a 20-step workflow, combined success rate drops to **36%**. A 2% early misalignment compounds to **40% failure rate** by the end.
- Performance degradation accelerates **beyond 30,000 tokens**, even with models having much larger windows (Chroma research).

### 6.2 Compression Benchmarks
- **Anchored iterative summarization**: accuracy score 4.04 vs Anthropic 3.74, OpenAI 3.43 (Factory benchmark).
- **SideQuest**: 56–65% peak token reduction with minimal accuracy loss, targeting expired tool outputs.
- **ACON**: 26–54% memory reduction while preserving >95% task accuracy via failure-driven guideline optimization.
- **Observational memory**: 5–40x compression for tool-heavy workloads; VentureBeat reported 10x token cost reduction vs baseline RAG.
- Provider compaction + rolling summaries can cut token spend **60–80%** across an agent pipeline.

### 6.3 New Technique Families

#### External Memory Architectures
- **Observational memory**: Observer compresses raw traces; Reflector deduplicates; compressed log stays permanently in context.
- **Letta tiered memory hierarchy**: core/working/archival memory with automatic paging.
- **MAGMA**: Multi-Graph based Agentic Memory Architecture — knowledge-graph structural queries.
- **EverMemOS**: OS-style promote/demote memory management based on access frequency and recency.

#### KV-Cache Optimizations
- **ChunkKV**: Semantic chunk preservation — evicts entire paragraphs instead of individual tokens.
- **SideQuest**: Fine-tuned parallel thread that identifies expired tool outputs during ReAct loops.

#### Failure-Driven Compression (ACON)
- Paired trajectory analysis: when compressed context causes failure, a capable LLM identifies missing information and refines compression guidelines.
- Gradient-free, compatible with closed-source models.

#### Cognitive Degradation Resilience (CDR)
- Cloud Security Alliance framework: starvation detection, fallback routing, memory integrity enforcement.
- Formal runtime property for ensuring compression doesn't silently degrade reliability.

### 6.4 Production Patterns
- **Trigger-based compaction at 70% context utilization**.
- **Tool-output filtering at ingestion time** — keep only what the agent needs for next step.
- **Drift monitoring** — distributed tracing for re-work, goal-wording shifts, technical detail corruption.
- **Three-level token budgeting** — per-request max_tokens, per-task 70% trigger, per-month cap with alerts.

## 7. Recommended Compression Ratios

| Content type | Ratio | Notes |
|--------------|-------|-------|
| Conversation history (old turns) | 3:1 to 5:1 | Keep decisions and outcomes |
| Tool outputs / observations | 10:1 to 20:1 | Keep only conclusions |
| Recent messages (last 5–7 turns) | No compression | Recency matters |
| System prompt | No compression | Anchor behaviour |

## References

1. Zylos AI Memory Taxonomy Survey (April 2026)
2. Letta/MemGPT hierarchical context management
3. SnapKV, CompressKV papers (2024-2025)
4. Claude 200K context architecture
5. Exocortex Context Pruner implementation
6. KV-cache privacy research
7. Zylos AI Context Compression Strategies (Feb 2026)
8. AgentMarketCap Context Compression Production Guide (Apr 2026)
9. ACON: Active Context Compression (arXiv:2601.07190)
10. SideQuest: Agent-Driven Cache Eviction (2026)
11. Observational Memory (VentureBeat, 2026)
12. Cognitive Degradation Resilience (CSA, 2026)
13. EverMemOS, MAGMA memory architectures (2026)
