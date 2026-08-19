# MCP Agentic Tool Use — Protocol Evolution & Tool Schema Optimization

**Status:** STABLE  
**Last Updated:** 2026-05-31  
**Sources:** 7  
**Cross-domain connections:** 6

---

## Overview

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) is an open standard for connecting AI agents to external tools and data sources. Originally open-sourced by Anthropic in November 2024, MCP has become the de facto standard for agent-tool integration with 97 million monthly SDK downloads, 19,831+ servers indexed on Glama registry (as of 2026), and backing from Anthropic, OpenAI, Google, and Microsoft.

This page tracks MCP protocol evolution toward agent-to-agent communication, tool description quality optimization, dynamic tool discovery patterns, and the MCP-vs-A2A protocol landscape — with direct implications for Exocortex's deterministic scaffolding and dynamic tool selection architecture.

---

## MCP Protocol Evolution (2024–2026)

### Timeline

| Date | Milestone | Significance |
|------|-----------|-------------|
| Nov 2024 | Anthropic open-sources MCP | Initial goal: standardized tool-calling for LLMs |
| Mid-2025 | Widespread adoption | MCP wins tool integration war; adopted across all major providers |
| Nov 2025 | First spec anniversary release | Formal specification with server/client architecture, transports (stdio, SSE, Streamable HTTP) |
| Jan 2026 | Core maintainer update | Shift from feature-driven to WG-driven governance; SEP process formalized |
| Mar 2026 | 2026 Roadmap published | Four priority areas defined; transition to working group governance model |

### 2026 Roadmap Priority Areas

Per lead maintainer David Soria Parra (March 2026), the four priorities are:

1. **Transport Evolution and Scalability:** MCP's original transport architecture (persistent connections keyed to client-server sessions) was designed for local tools. Production deployments require stateless transports, connection pool management, and horizontal scaling. The roadmap targets server-initiated communication (server→client push), streaming improvements, and HTTP/2 optimizations.

2. **Agent Communication (agent-to-agent):** MCP is expanding beyond tool-calling to support agent-to-agent communication. Key initiatives include the Tasks primitive (long-running operations with retry semantics), server discovery mechanisms, and inter-agent negotiation. This moves MCP from a client-server tool protocol to a peer-to-peer agent network protocol.

3. **Governance Maturation:** Transition from Anthropic-led development to community governance via Working Groups and Spec Enhancement Proposals (SEPs). Working groups for Transports, Security, and Agent Communication were forming in early 2026.

4. **Enterprise Readiness:** Authentication/authorization standards, audit logging, rate limiting, and compliance tooling for deployment in regulated environments.

### SEP Prioritization

The SEP process allows community-proposed spec changes. Priorities for 2026 were informed by production experience: transport scalability is the top concern, followed by agent communication primitives. Contributors were directed to align proposals with the four roadmap pillars.

---

## Tool Schema Optimization

### The "Smelly" Tool Description Problem

The arXiv paper **"MCP Tool Descriptions Are Smelly! Towards Improving AI Agent Efficiency with Augmented MCP Tool Descriptions"** (Feb 2026) identified a critical failure mode: poorly written tool descriptions directly impair agent tool selection accuracy. The paper established a taxonomy of description "smells":

| Smell Category | Example | Impact |
|---------------|---------|--------|
| **Ambiguous naming** | `process()` vs `validate_and_submit()` | Agent calls wrong tool or misapplies parameters |
| **Missing error states** | No documentation of failure modes | Agent cannot recover from tool errors |
| **Inadequate parameter descriptions** | `data: string` without format constraints | Invalid arguments, wasted calls |
| **Inconsistent formatting** | Mixed description styles across tools | Agent must re-learn each tool's interface |

### Augmented Tool Descriptions

The corrective proposed is LLM-generated augmented tool descriptions: an LLM analyzes raw tool descriptions, identifies smells, and rewrites them with precise parameter schemas, error state documentation, consistent naming conventions, and contextual usage guidance. The augmentation is a one-time preprocessing step — no runtime overhead.

For Exocortex, this has direct implications. The agent-zero prompt contains extensive tool descriptions (browser, code_execution_tool, skills_tool, etc.). Auditing these against the smell taxonomy could yield immediate tool selection accuracy improvements without architectural changes.

### GEPA-Style Closed-Loop Improvement

Reflection-based optimization applies directly to tool descriptions. If an agent can reason about why a tool selection failed (wrong tool called, wrong parameters, misleading description), that reflection can generate improved descriptions — closed-loop improvement without weight modification. This aligns with Exocortex's prompt evolution architecture.

---

## Dynamic Tool Discovery

### Server Discovery and Registry

As the MCP ecosystem grows (19,831+ servers indexed), agent agents need to discover available tools without hardcoded server lists. Key patterns:

1. **Registry-based discovery:** Glama, Smithery, and other registries provide server indices with capability metadata. Agents query registries dynamically based on task requirements.

2. **Semantic tool retrieval:** Embed tool descriptions, index them, and retrieve relevant tools by embedding similarity against the current task. This prevents context bloat from listing hundreds of tools while ensuring the right tools are available.

3. **Capability negotiation:** In agent-to-agent scenarios, agents advertise tool capabilities via MCP's tool listing, enabling dynamic composition of tool chains without prior integration.

### Embedding-Based Tool Selection

For Exocortex, tool retrieval by embedding (DTS with semantic search) is a natural evolution. The current flat-listing approach in the prompt works for ~30 tools but would not scale to dynamic tool discovery from external MCP servers. An embedded tool index would enable:
- Task-contextual tool filtering (only show tools relevant to the current task)
- Integration of external MCP servers without modifying the agent prompt
- Reduced context overhead from tool descriptions

---

## Protocol Landscape: MCP vs A2A

As of early 2026, the agent communication protocol landscape consolidated to two complementary protocols:

| Dimension | MCP (Anthropic) | A2A (Google, Linux Foundation) |
|-----------|-----------------|-------------------------------|
| **Primary purpose** | Agent-to-tool integration | Agent-to-agent communication |
| **Architecture** | Client-server (tools are servers) | Peer-to-peer (agents are peers) |
| **Key primitives** | Tools, Resources, Prompts, Sampling | Tasks (long-running with retry), Agent Cards (capability advertising) |
| **Transport** | stdio, SSE, Streamable HTTP | HTTP/JSON-RPC |
| **Governance** | MCP org (community WG) | Linux Foundation |
| **MCP 2026 expansion** | Adding agent-to-agent via Tasks primitive | Natively agent-to-agent |

**Historical note:** IBM's Agent Communication Protocol (ACP) merged into A2A under the Linux Foundation in late 2025, reducing the three-horse race to two complementary standards.

### Convergence Trend

MCP's 2026 roadmap explicitly targets agent communication, while A2A supports tool invocation. The two protocols are converging in capability while maintaining distinct design philosophies. The practical recommendation for 2026: use MCP for tool integration, use A2A for multi-agent orchestration, and expect convergence over time.

---

## Exocortex Integration

### Validated Design Decisions

The MCP evolution validates several Exocortex architectural choices:

- **Deterministic scaffolding:** MCP's structured, explicit interfaces reinforce the value of deterministic scaffolding vs. implicit agent behavior.
- **Prompt evolution:** Augmented tool descriptions are essentially prompt evolution applied to tool metadata — the same pattern as Exocortex's GEPA-style reflection.
- **Dynamic tool selection:** The wiki concept at `[[dynamic-tool-selection]]` is directly aligned with the state of the art in tool retrieval by embedding.

### Practical Integration Pathway

1. **Tool description audit:** Audit Agent Zero's tool descriptions against the arXiv smell taxonomy. Quantify which smells are present and their frequency in tool selection errors.

2. **Augmented descriptions:** Generate improved tool descriptions using the framework's own LLM and benchmark selection accuracy improvements. This is a low-risk, high-reward optimization.

3. **MCP client integration:** Implement an MCP client in the Agent Zero framework to connect to public MCP servers, expanding tool capability without custom integration code. The code_execution_tool could forward MCP tool calls.

4. **Embedded tool index:** Build a semantic index of tool descriptions and test whether retrieval-augmented tool selection outperforms the current flat-listing approach.

5. **Subordinate agent communication via MCP Tasks:** Could subordinate agents communicate via MCP Tasks with retry semantics rather than the current call_subordinate prompt-based mechanism? This would add error recovery, progress tracking, and structured output schemas.

---

## Cross-Domain Connections

1. **OSINT & Investigation Methodology:** OSINT agents face tool proliferation — an investigator with access to 10+ search tools, 5+ database connectors, and 3+ document parsers needs intelligent tool selection. Tool retrieval by embedding (matching task context to tool description embeddings) is directly applicable to investigation workflows.

2. **Entity Resolution:** Dynamic tool discovery for entity resolution means an agent discovers a new corporate registry MCP server and resolves entities against it without human integration work. Schema matching (mapping tool output schemas to entity schemas) mirrors entity resolution across datasets.

3. **Hardware & Local Inference:** Semantic tool description embedding models must run locally for air-gapped environments. The local inference work (RTX 3090 optimization, quantization) makes tool retrieval by embedding feasible on premises.

4. **Self-Improving Agent Architecture:** The GEPA-style closed-loop improvement pattern (agent fails → analyzes why → generates better description → retries) applies to tool descriptions as a self-improvement mechanism. This is a lightweight form of agentic self-learning without weight modification.

5. **ATLAS-Style Autonomous Coding:** The Smelly paper's augmented description technique can be applied to code-generation tool descriptions, improving code-writing agent accuracy through better tool specifications.

6. **Context Management / Compression:** Embedding-based tool retrieval reduces context overhead by selecting only relevant tools per task, complementing the context-pruner and injection-gate architectures.

---

## References

1. MCP 2026 Roadmap — Official Blog (Mar 9, 2026). David Soria Parra. [Link](https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/)
2. "MCP Tool Descriptions Are Smelly!" arXiv (Feb 2026). Tool description smell taxonomy and augmented description methodology.
3. "MCP vs A2A vs ACP: The 2026 Guide" — Optinampout (Feb 5, 2026). Protocol comparison and decision framework.
4. MCP 2026 Roadmap Analysis — A2A-MCP.org (Mar 2026). Community analysis of roadmap priorities.
5. "The Future of MCP: Enterprise Adoption" — Toloka.ai (2026). Production deployment patterns.
6. "Code execution with MCP: Building more efficient agents" — Anthropic Engineering (Nov 2025). Code-execution paradigm shift.
7. MCP Specification v2025-11-25. [modelcontextprotocol.io](https://modelcontextprotocol.io/specification/2025-11-25/)
