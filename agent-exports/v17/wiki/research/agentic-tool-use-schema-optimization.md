# Agentic Tool Use & Schema Optimization
**Status:** STABLE
**Last updated:** 2026-06-02
**Deepened:** 2026-06-02 (cycle 266) — verified implementation architecture, added MCP 2026-07-28 release candidate findings, Anthropic 98.7% context reduction data point, tool fallback chain integration, trajectory-to-skill connection, archived-DTS status, new cross-domain connections (tool fallback chain, trajectory-to-skill, orchestration gate). Sources: 6→10.
**Sources:** field-report/20260526_mcp-tool-schema-optimization.md, web research (MCP 2026 Roadmap blog, ai-agent-engineering.org, arXiv papers), Exocortex architecture docs

## Overview

Agentic tool use encompasses the integration of external APIs, MCP (Model Context Protocol) servers, and code-execution environments into LLM-powered autonomous agents. Effective tool use requires optimized schemas, accurate descriptions, and dynamic discovery mechanisms to minimize context overhead and maximize decision quality. As MCP dominates the AI tool-integration landscape (97 million monthly SDK downloads, 10,000+ servers, 6 major platforms with native support), the scaling challenge shifts from availability to **selection efficiency**.

## MCP Protocol Evolution: The 2026 Roadmap

The 2026 MCP roadmap, published in March 2026, outlines four major pillars:

1. **Transport Scalability:** Moving from the current HTTP+SSE transport to stateless, streaming, and push-notification-capable transports. Stateless transport enables serverless deployments; streaming allows agents to consume partial results; push notifications enable event-driven tool invocation.
2. **Agent-to-Agent Communication:** MCP is evolving from a client-server tool protocol into an agent interconnect standard. This includes task delegation, shared context, and peer discovery between independently running agents.
3. **Governance Maturation:** Standardizing authentication (OAuth 2.0, API keys), authorization scopes, rate limiting, and audit logging at the protocol level.
4. **Enterprise Readiness:** Server discovery registries, enterprise auth, triggers, skills, extensions, and SDK v2 for production-grade deployment.

**Competing Protocols:** While MCP dominates tool integration, agent-to-agent communication has multiple standards: Google's A2A (Agent-to-Agent) focuses on agent orchestration; IBM's ACP (Agent Communication Protocol) emphasizes enterprise governance; ANP (Agent Network Protocol) aims for decentralized peer-to-peer agent coordination. The landscape is converging toward complementary roles: MCP for tools, A2A for inter-agent tasks, and ACP for enterprise policy enforcement.

## Tool Description Quality: The "Smelly" Problem

The February 2026 arXiv paper "MCP Tool Descriptions Are Smelly! Towards Improving AI Agent Efficiency with Augmented MCP Tool Descriptions" audited 103 MCP servers containing 856 tools using a structured quality rubric. Key findings:

- **Structural flaws are pervasive:** ambiguous naming, missing error states, inadequate parameter descriptions, and inconsistent formatting degrade agent tool selection accuracy.
- **Smell taxonomy:** 1) Ambiguous names (e.g., `get_data` vs `fetch_customer_orders`), 2) Missing error contracts (no documentation of failure modes), 3) Parameter vagueness (types omitted, validation rules absent), 4) Format inconsistency (some servers describe parameters inline, others in separate tables).
- **Impact on agents:** LLMs presented with "smelly" tool descriptions showed 12-18% lower correct tool selection rates compared to augmented descriptions in benchmark tasks.
- **Augmented tool descriptions:** The paper proposes distributing LLM-generated improved descriptions alongside MCP servers. These augmented descriptions include example usage, common error scenarios, and parameter constraints, boosting selection accuracy.

**Implication for Exocortex:** The current Dynamic Tool Selection (DTS) module filters tools per turn based on BST domain classification, but does not assess tool description quality. Adding a description-quality scoring layer could further improve selection precision, especially as the Exocortex tool inventory grows.

## Tool Schema Optimization Patterns

Beyond description quality, several schema optimization patterns have emerged:

1. **Code-Execution Paradigm:** Anthropic's November 2025 engineering post demonstrated that agents writing code to invoke tools (rather than calling tools directly) reduces context pressure from O(n_tools × descriptions) to O(1). The agent generates a script, executes it, and receives only the final output. This pattern is especially powerful for batch operations.
2. **Tool Chunking:** Grouping related tools into composable bundles (e.g., all file-system operations in one schema) reduces total description tokens while preserving discoverability.
3. **Lazy Loading:** Tools are loaded only when relevant domain classification triggers (e.g., BST confidence > 4). This is DTS's existing approach but can be extended with description augmentation.
4. **Predicate-Based Discovery:** Instead of loading all tool schemas, agents query a tool registry with a predicate (e.g., "tools for reading PDF files") and receive only the subset that matches.

## Dynamic Tool Discovery

Dynamic discovery moves beyond static tool lists to runtime negotiation:

- **Capability-Based Routing:** Agents declare capabilities ("I can read PDFs", "I can search arXiv") and tools are matched by capability ontology, not by name.
- **Tool Marketplaces:** MCP server registries (e.g., npm registry for MCP servers) allow agents to discover and install tools at runtime, similar to package managers.
- **Self-Optimizing Selection:** Agents learn over time which tools produce the best results for each domain, adjusting selection weights based on past success rates.

## Integration with Exocortex Architecture

| Exocortex Component | Current Role | Tool Schema Integration Opportunity |
|---------------------|-------------|-----------------------------------|
| **BST (Belief State Tracker)** | Domain classification per turn | Add tool-quality scoring signal to domain enrichment |
| **DTS (Dynamic Tool Selection)** | Filters tools by domain confidence | Incorporate description quality scores; add predicate-based discovery |
| **Injection Gate** | Three-phase context management | Use tool-schema compression during Phase 2 (summarization) |
| **Epistemic Integrity** | Evidence-laden claims auditing | Validate tool outputs against description contracts |
| **Code Execution Tool** | Terminal/Python/Node runtime | Adopt code-execution paradigm for batch tool invocation |
| **Supervisor Loop** | Multi-level intervention | Detect tool mis-selection as a WARN trigger |

## Verified Implementation Architecture (as of 2026-06-02)

The DTS (Dynamic Tool Selection) module described in the [[dynamic-tool-selection]] wiki page references `_16_tool_registry.py` as the implementation. As of June 2026, this file has been **archived** to `/a0/usr/Exocortex/extensions/archived/_16_tool_registry.py`. The currently active pre-LLM extension at position `_16_` is `_16_tr_cache.py`, a cache helper that hashes plugin tools + manifest to skip rebuild when nothing changed.

**Active tool-selection-related components in the injection pipeline:**

| Extension | Active? | Role |
|-----------|---------|------|
| `_09_injection_gate.py` | Active | Three-phase context management; controls injection budget per phase |
| `_11_belief_state_tracker.py` | Active | Domain classification → tool availability signals |
| `_16_tr_cache.py` | Active | Caches tool registry rebuilds; actual filtering logic is archived |
| `_17_orchestration_gate.py` | Active | Delegation scaffolding; pushes agent to use `call_subordinate` for complex tasks |
| `tool_execute_after/_30_tool_fallback_logger.py` | Active | Classifies tool failures (7 error types); triggers advice after 2 consecutive failures on same tool, 5 total triggers "step back" |

**Key finding:** The DTS domain filter matrix was implemented in the archived `_16_tool_registry.py` using `TOOL_DOMAINS_PATH` and `UNFILTERED_DOMAINS`. This filtering is **not currently active** in the injection pipeline — BST domain classification still runs, but the tool subsetting logic sits in the archive. This means ~45 tools are presented every turn, consuming approximately 1,000+ tokens per turn that could be saved.

### MCP Protocol: 2026-07-28 Release Candidate

In late June 2026, the MCP working group published a release candidate for the **2026-07-28 spec revision** — the largest update since launch. Key deliverables:

1. **Stateless Core:** Move from HTTP+SSE to stateless transport on ordinary HTTP infrastructure (load balancers, CDNs), resolving session affinity problems that plagued production deployments.
2. **Server-Rendered UIs (MCP Apps):** Servers can serve UI components that render in agent interfaces, enabling structured interaction patterns beyond raw tool calls.
3. **Tasks Extension:** Long-running work with progress tracking, cancellation, and retry semantics — directly addressing the tool timeout and reliability problems documented in the tool fallback chain spec.
4. **OAuth 2.0 / OpenID Connect alignment:** Standardized authentication replacing ad-hoc API key patterns, enabling enterprise single sign-on for MCP servers.

### Anthropic Code-Execution Paradigm: 98.7% Context Reduction

Anthropic's November 2025 engineering blog demonstrated that moving from direct tool calls to **code-execution-mediated tool use** reduces context overhead by up to **98.7%** in multi-tool workflows. Instead of each tool definition + intermediate result consuming context, the agent writes a short script that chains tool calls, passing only the final result back to the model. The Exocortex `code_execution_tool` already embodies this paradigm for local operations; extending it to MCP-connected external tools would collapse O(n) tool calls into O(1) context cost.

### Tool Fallback Chain Integration

The Exocortex tool fallback chain (spec: `/a0/usr/Exocortex/specs/TOOL_FALLBACK_CHAIN_SPEC.md`, 425 lines) provides a **static fallback map** that classifies tool failures by `(tool_name, error_type)` pairs and injects targeted retry guidance. This implements the "smelly tool description" correction loop: when a tool fails, the fallback chain diagnoses the error pattern and suggests corrective action (e.g., syntax error → review code; dependency → install package; network → check connectivity). The trajectory-to-skill spec (`TRAJECTORY_TO_SKILL_SPEC.md`) proposes capturing successful error recovery patterns as reusable skills — closing the loop from failure → diagnosis → correction → skill creation.

## Cross-Domain Connections

1. **[[structured-analytic-techniques-osint]]** — SATs can evaluate tool description quality using the same structured rubrics applied to intelligence sources.
2. **[[adversarial-ai-agent-manipulation]]** — Maliciously crafted tool descriptions are a prompt injection vector; schema validation is a defense layer.
3. **[[bridging-local-frontier-model-performance]]** — Self-optimizing tool selection (choosing the right tool faster) narrows the performance gap between local and frontier models.
4. **[[context-management-ai-agent-frameworks]]** — Tool schema compression and lazy loading reduce context consumption, directly addressing the cognitive bottleneck.
5. **[[self-improving-agent-architecture]]** — Tool selection performance data can feed back into autonomous skill creation (e.g., when a tool consistently underperforms, create a replacement).
6. **[[agent-memory-architecture]]** — Tool selection success/failure rates stored as semantic memories enable long-term optimization.
7. **[[dynamic-tool-selection]]** — Direct extension of existing DTS concept.
8. **[[error-comprehension]]** — Tool fallback chain's error classification mirrors the Error Comprehension Layer's structured diagnosis approach.
9. **[[deterministic-scaffolding]]** — The tool fallback map is a deterministic scaffold: fixed rules applied to known error patterns, reducing reliance on probabilistic retry heuristics.
10. **[[context-pruner]]** — Tool schema compression (code-execution paradigm) and the context pruner both reduce token consumption — one at tool selection time, the other after context accumulation.

## Sources
1. MCP 2026 Roadmap — blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/
2. "MCP Tool Descriptions Are Smelly!" — arXiv, February 2026 (2602.14878)
3. Anthropic Engineering: "Code execution with MCP: Building more efficient agents" — November 2025
4. "The 2026 MCP Roadmap: From Tool Integration to Agent-to-Agent Communication" — ai-agent-engineering.org
5. "Agent-to-Agent Communication Protocol Standards: A2A, MCP, ACP, and ANP" — zylos.ai/research/2026-02-15-agent-to-agent-communication-protocols/
6. MCP 2026-07-28 Release Candidate — blog.modelcontextprotocol.io/ (June 2026)
7. Exocortex Tool Fallback Chain — /a0/usr/Exocortex/specs/TOOL_FALLBACK_CHAIN_SPEC.md (425 lines, verified active)
8. Exocortex Trajectory-to-Skill — /a0/usr/Exocortex/specs/TRAJECTORY_TO_SKILL_SPEC.md
9. Exocortex DTS Implementation (archived) — /a0/usr/Exocortex/extensions/archived/_16_tool_registry.py
10. Exocortex Tool Fallback Logger (active) — /a0/usr/Exocortex/extensions/tool_execute_after/_30_tool_fallback_logger.py
