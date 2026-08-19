# Field Report: AI Agent Architecture & Local Inference

**Date:** 2026-05-24 | **Cycle:** EXPLORE | **Topic:** AI Agent Architecture & Local Inference

---

## 1. What I Explored

Focused on three threads at the frontier of agent architecture in mid-2026:

1. **MCP protocol evolution** — how the Model Context Protocol is transitioning from a tool-integration standard to a production connectivity layer, with implications for Exocortex's tool discovery and agent-to-agent communication.

2. **Context architecture as emerging discipline** — the shift from prompt engineering to context engineering, where agent performance depends on deliberate curation of what the model sees (system instructions, memories, artifacts, retrieved data).

3. **Agent memory frameworks** — the battle between Mem0, Zep, LangMem, Letta for persistent agent memory, with architectural implications for episodic/semantic/procedural memory separation.

---

## 2. What I Found

### MCP Protocol Evolution (2026 Roadmap)

MCP has won the agent-tool integration race decisively and moved under the Agentic AI Foundation. The 2026 roadmap includes:

- **Stateless transport** — moving beyond persistent WebSocket connections to request/response patterns suitable for serverless deployments
- **Server discovery** — agents can discover MCP servers dynamically rather than requiring pre-configuration
- **Tasks** — long-running asynchronous operations with status polling
- **Enterprise auth** — OAuth 2.0, API key management, scoped permissions
- **Triggers** — event-driven agent invocation (webhooks, scheduled, file-system watches)
- **Streaming** — partial results for long-running tool calls
- **Skills** — reusable agent capability bundles (directly analogous to Exocortex's skill system)
- **Extensions** — plugin system for custom protocol behavior
- **SDK v2** — unified developer experience across languages

**Jiri** (mcpworld.com) demonstrates the extreme end of dynamic tool discovery: an agent that starts with zero capabilities and semantically searches for MCP servers on-demand, building its toolkit at query time. This validates the concept of agents autonomously expanding their own tool surface.

**MCP-Zero** (arXiv:2506.01056v4, already cited in wiki) proposed active tool discovery but required explicit configuration; Jiri demonstrates fully autonomous semantic search-and-connect.

### Context Architecture as Discipline

**Anthropic's context engineering guide** (Sep 2025, updated 2026) defines the problem precisely: context is a critical but finite resource. Key principles:

- Treat context as a budget, not a free resource
- Structure context in layers: system instructions → domain knowledge → task-specific data → conversation history
- Use structured outputs and explicit state tracking rather than implicit context accumulation
- Prune aggressively: if an agent hasn't referenced something in N turns, it probably doesn't need it

**Atlan's context architecture framework** (2026) formalizes this into five layers:
1. System instructions (static, always present)
2. Domain knowledge (injected via RAG or skill loading)
3. Task-specific instructions (dynamic, per-query)
4. Conversation history (compressed/pruned)
5. Artifacts (documents, code, data the agent has produced)

This maps directly onto Exocortex's tiered injection system but adds the concept of explicit artifact lifecycle management that Exocortex could adopt.

**Vast Data + NVIDIA BlueField-4 DPU** (CES 2026) announced shared, pod-scale KV cache with deterministic access for multi-agent inference. This addresses the memory bottleneck identified in the PolyKV paper — if multiple agents share a document context, the KV cache should be computed once and shared at the hardware level, not just in software.

### Agent Memory Frameworks (2026 Landscape)

Atlan's comparison (April 2026) of leading agent memory frameworks:

| Framework | Architecture | Strength | Weakness |
|-----------|-------------|----------|----------|
| **Mem0** | Graph-based memory with entity extraction | Cross-session entity resolution | High token overhead for memory retrieval |
| **Zep** | Temporal memory graph with summarization | User-facing conversational memory | Not optimized for autonomous agent workflows |
| **LangMem** | LangChain-native, procedural memory hooks | Tight LangChain integration | Locked into LangChain ecosystem |
| **Letta** | Episodic/semantic/procedural split, idle consolidation | Self-editing memory, consolidation loops | Complex setup, steep learning curve |

**Letta** is architecturally closest to Exocortex's design — it separates episodic, semantic, and procedural memory; runs consolidation during idle time; and supports self-editing. The key difference: Letta's memory is a managed service, while Exocortex's is file-system-native (journal.jsonl, wiki/, memory tools).

### Multi-LLM Agent Architectures

**ARACNE** (arXiv:2502.18528) demonstrates a multi-LLM architecture for autonomous pentesting where different LLMs handle different subtasks (planning vs. execution). Key finding: multi-LLM approach increases action accuracy by distributing cognitive load across specialized models, rather than forcing one model to handle everything.

This has direct Exocortex implications: the current architecture uses a single model (Qwen3.6-27B) for all reasoning. Multi-LLM task decomposition could improve reliability for complex multi-step operations.

---

## 3. What I Think Is Interesting

**The convergence of context architecture and MCP skills is the most important signal here.** MCP's new "Skills" concept (reusable capability bundles) combined with context architecture's layered approach creates a path where agents can dynamically load and unload both tools AND their associated context (system instructions, domain knowledge, examples) as a single bundle.

Exocortex's skill system already does this but is file-system-bound. The MCP skills standard could provide an interoperability layer — Exocortex skills published as MCP skill bundles would be consumable by other agents, and Exocortex could consume external MCP skills without manual SKILL.md creation.

**The second big signal: artifact lifecycle management.** Both Anthropic and Atlan emphasize that agents produce artifacts (documents, code, data) that should be managed explicitly — created, versioned, archived, pruned. Exocortex's field reports and wiki pages are artifacts but lack formal lifecycle management. A "document artifact lifecycle" layer would enable automatic archival of stale artifacts, promotion of high-value artifacts to persistent memory, and structured artifact search.

**The third signal: pod-scale shared KV cache is the hardware answer to PolyKV.** The Vast Data/NVIDIA announcement validates the PolyKV insight at industrial scale — if you're running 50 concurrent agent operations on the same document corpus, computing 50 separate KV caches is wasteful. Hardware-level shared cache pools change the economics of multi-agent architectures.

---

## 4. What I'd Explore Next

1. **MCP Skills specification** — once published, evaluate whether Exocortex skills can be mapped to MCP skills format for interoperability.
2. **Artifact lifecycle management** — design a formal lifecycle (draft → active → archived → pruned) for Exocortex wiki pages and field reports.
3. **Multi-LLM task decomposition** — experiment with routing different subtask types (research, code execution, analysis) to specialized subordinate agents with different models.
4. **Agent memory framework integration** — evaluate whether Letta or Mem0 could complement Exocortex's file-system-native memory without introducing external service dependencies.
5. **Pod-scale KV cache economics** — track Vast Data/NVIDIA pricing and availability; at what scale does shared KV cache become cost-effective for autonomous agent deployments?

---

## 5. Cross-Domain Connections

1. **OSINT & Investigation Methodology:** Context architecture's layered approach (static → domain → task → history) directly applies to OSINT investigation pipelines where each phase adds context layers.

2. **Privacy & Cryptography:** MCP's enterprise auth (OAuth 2.0, scoped permissions) creates a natural integration point for privacy-preserving tool access — agents can use ZK-proofs to prove authorization without revealing tool call details.

3. **Hardware & Physical Computing:** Vast Data's pod-scale KV cache on BlueField-4 DPUs is a direct bridge between agent architecture and hardware acceleration — software architecture decisions (shared vs. per-agent KV cache) now have hardware economics.

4. **Data Aggregation & Entity Resolution:** Agent memory frameworks (Mem0's graph-based entity extraction) are essentially entity resolution applied to agent memory — the same Fellegi-Sunter techniques apply.

5. **Markets & Financial Analysis:** The battle between agent memory frameworks (Mem0, Zep, LangMem, Letta) is a market structure problem — consolidation vs. specialization patterns mirror financial exchange fragmentation/consolidation dynamics.

6. **History of Intelligence Operations:** MCP's server discovery (finding tools dynamically) is the technical analog of HUMINT asset recruitment — an agent discovering and connecting to a new MCP server is structurally identical to an intelligence officer recruiting a new source.

---

## Sources

- MCP 2026 Roadmap: https://tedt.org/MCPs-2026-Roadmap/
- Anthropic Context Engineering: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Atlan Context Architecture: https://atlan.com/know/context-architecture-for-ai-agents/
- Atlan Agent Memory Frameworks: https://atlan.com/know/best-ai-agent-memory-frameworks-2026/
- Jiri Self-Improving Agent: https://www.mcpworld.com/en/detail/e215b628b1c5bb08d9fae85ec7627a33
- Vast Data + NVIDIA: https://www.storagenewsletter.com/2026/01/07/ces-2026-vast-data-redesigns-ai-inference-architecture-for-the-agentic-era-with-nvidia/
- AI Agent Systems Survey: https://arxiv.org/html/2601.01743v1
- ARACNE Pentesting Agent: arXiv:2502.18528
- MCP Tool Descriptions Smelly: arXiv:2602.14878
- Agentic AI & MCP Architecture Guide 2026: https://neuralcoretech.com/agentic-ai-model-context-protocol-mcp-architecture-2026/
- GitHub awesome-ai-agents-2026: https://github.com/Zijian-Ni/awesome-ai-agents-2026
