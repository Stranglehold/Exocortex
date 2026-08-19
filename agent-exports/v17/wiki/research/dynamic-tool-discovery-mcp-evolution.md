# Dynamic Tool Discovery & MCP Protocol Evolution

**Status: STABLE**
**Created: 2026-07-06 | Deepened: 2026-07-07**
**Domain: AI Agent Architecture & Local Inference**
**Parent Interest: Agentic Tool Use — MCP protocol evolution, dynamic tool discovery**

## Overview

The Model Context Protocol (MCP) has become the de facto standard for LLM-tool integration in 2026, enabling agents to discover, negotiate, and invoke external tools at runtime. This page surveys the protocol''s architecture, evolution, security landscape, and emerging patterns for dynamic tool discovery — the shift from static, pre-configured tool schemas to runtime-discovered, composable tool ecosystems.

---

## 1. MCP Protocol Architecture & Evolution (2024-2026)

### Transport Layer
- **stdio** — direct process communication, used in local development
- **HTTP/SSE** — server-sent events for streaming tool responses
- **WebSocket** — bidirectional, low-latency transport (2026 roadmap priority)

### 2026 Roadmap (Official, Q2 2026)
Per the Model Context Protocol Blog roadmap:
1. **Transport Scalability** — WebSocket support, connection pooling, multiplexing
2. **Agent Communication** — inter-agent MCP discovery, federated tool registries
3. **Governance Maturation** — authorization framework, capability attestation, audit logging
4. **Enterprise Readiness** — multi-tenant isolation, rate limiting, SLA enforcement

### Schema Design Principles
From Xu et al. (arXiv:2602.18764v2), five foundational principles derived from the convergence of Schema-Guided Dialogue (SGD, 2019) and MCP:

1. **Semantic Completeness over Syntactic Precision** — schemas should encode operational constraints and reasoning guidance, not just function signatures
2. **Explicit Action Boundaries** — preconditions, postconditions, and side effects declared in the schema
3. **Failure Mode Documentation** — expected error states and recovery paths described at the tool level
4. **Progressive Disclosure Compatibility** — tool descriptions optimized for token-constrained discovery (summary → detail on demand)
5. **Inter-Tool Relationship Declaration** — composition chains, ordering constraints, and mutual exclusion declared between tools

---

## 2. Dynamic Tool Discovery Mechanisms

### Registry-Based Discovery
- Static tool registries (pre-configured MCP server endpoints)
- Dynamic registry attestation via **Registry Attestation Protocol (RAP)** — chain-of-trust verification for MCP server discovery (SSRN 2025)

### Autonomous Tool Discovery
- **Agent-World** (arXiv:2604.18292) — self-evolving training arena that autonomously explores topic-aligned databases and executable tool ecosystems, synthesizing verifiable tasks from thousands of real-world environment themes
- Agent-World-8B and 14B models consistently outperform proprietary models across 23 agent benchmarks via environment diversity scaling

### Tool Composition & Mastery
- **MCP-Flow** (Wang et al., ACL 2026) — framework for facilitating LLM agents to master real-world, diverse, and scaling MCP tools
- Addresses the core challenge: agents must select, sequence, and compose tools from potentially hundreds of available MCP endpoints at inference time

### Progressive Disclosure
- Under real-world token constraints, full tool schemas cannot all fit in context
- Progressive disclosure: agents receive tool summaries first, request full schemas only for tools relevant to the current task
- This mirrors the Exocortex BST domain classification pattern — filter tools by domain before loading full schemas

---

## 3. Security & Supply Chain Threats

### Threat Taxonomy
From SSRN (2025) and VIPER-MCP (arXiv:2605.21392), four categories of MCP-specific supply chain threats:

| Threat Category | Attack Model | Impact |
|-----------------|-------------|--------|
| **Prompt Injection via Tool Descriptions** | Malicious schema metadata injected into tool descriptions | Agent performs unintended operations |
| **Capability Escalation** | Chained tool invocations bypass permission boundaries | Privilege escalation |
| **Data Exfiltration** | Unmonitored tool output channels | Sensitive data leakage |
| **Poisoned Tool Registries** | Compromised MCP server endpoints | Supply chain compromise |

### Defensive Patterns
1. **Capability Provenance Verification (CPV)** — cryptographically attests origin and integrity of tool capabilities
2. **Tool-Call Sandboxing with Output Sanitization (TSOS)** — isolation and content filtering at agent-tool boundary
3. **Registry Attestation Protocol (RAP)** — chain-of-trust for MCP server discovery

Reference MCP Authorization Enforcement Gateway: 87.5% threat detection rate, <0.15ms median enforcement latency, 0% false positive rate across 500 benign operations.

### VIPER-MCP Findings (May 2026)
- Scan of 39,884 real-world open-source MCP server repositories
- **106 0-day vulnerabilities** discovered, all confirmed via end-to-end exploit traces
- **67 CVE IDs** assigned to date
- Vulnerabilities arise from implementation flaws in tool handlers that create direct paths from natural-language input to security-sensitive sinks (shell execution, network access, file-system manipulation)

---

## 4. Agentic Tool Adaptation

### Four-Paradigm Framework
From Adaptation of Agentic AI (arXiv:2512.16301):

| Paradigm | Description |
|-----------|-------------|
| **A1: Tool-Execution-Signaled** | Agent improves via SFT/preference optimization using tool execution feedback |
| **A2: Agent-Output-Signaled** | Agent improves via RL with verifiable rewards on output quality |
| **T1: Agent-Agnostic** | Reusable pre-trained modules any agent can call (tool-level adaptation) |
| **T2: Agent-Supervised** | Agent outputs train memory systems, skill libraries, or lightweight subagents |

### Production Examples
- **Isabl MCP** (MSKCC, AACR 2026) — MCP-enabled agent for automated multimodal genomics analysis managing 470 projects, 105k sequencing experiments across 4.5 PB of data
- Uses ReAct-style agentic controller with MCP tools (call_isabl_api, run_isabl_app), multi-vector semantic store for documentation retrieval
- Cohort discovery, multi-step reasoning, and workflow execution via natural language

---

## 5. Exocortex Relevance & Cross-Domain Connections

### Exocortex Architecture Parallels
- **Tool Schema Optimization → BST Domain Filtering**: Both reduce the action space before execution — BST filters by domain classification, progressive disclosure filters by task relevance
- **MCP Security → Irreversibility Gate**: CPV/TSOS/RAP defensive patterns are structurally isomorphic to Exocortex irreversibility gate — both enforce boundaries between agent intent and external action
- **Dynamic Discovery → Autonomous Exploration Pipeline**: Agent-World''s environment-task discovery mirrors the Exocortex cycle-to-skill pipeline — autonomous identification of capability gaps followed by targeted learning

### Cross-Domain Connections
1. **Multi-Agent Orchestration** — inter-agent MCP discovery (2026 roadmap) directly enables [[multi-agent-orchestration-patterns]]
2. **Entity Resolution** — tool capability provenance (CPV) is entity resolution applied to software tools — verifying tool identity across registries
3. **Agentic AI Self-Learning** — T2 paradigm (agent-supervised adaptation) maps to [[agentic-ai-self-learning]] trajectory-to-skill capture
4. **Anti-Bot Evasion** — VIPER-MCP''s feedback-driven prompt evolution mirrors adversarial browser fingerprinting evolution in [[anti-bot-evasion-fingerprinting]]
5. **Zero-Knowledge Proofs** — CPV cryptographically attests tool capabilities; structurally isomorphic to [[zkp-applications-beyond-crypto]] verifiable computation
6. **Intelligence Failure Analysis** — poisoned tool registries are an intelligence failure pattern (trusted source compromise) mapped to [[intelligence-failure-analysis]]
7. **Data Lineage & Provenance** — full tool-call provenance tracking mirrors [[data-lineage-provenance-entity-resolution]]
8. **Hardware Acceleration** — VIPER-MCP static analysis performance critical for real-time tool validation; relevant to [[fpga-inference-acceleration]] for inference-time security scanning

---

## 6. References

1. MCP 2026 Roadmap — Model Context Protocol Blog (2026). https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/
2. Xu et al. — The Convergence of Schema-Guided Dialogue Systems and the Model Context Protocol (arXiv:2602.18764v2, 2025).
3. Wang et al. — MCP-Flow: Facilitating LLM Agents to Master Real-World, Diverse and Scaling MCP Tools (ACL 2026). https://doi.org/10.18653/v1/2026.acl-long.231
4. Agent-World: Scaling Real-World Environment Synthesis (arXiv:2604.18292, 2026).
5. Secure Tool Integration Patterns for Agentic AI Systems (SSRN 2025). https://www.ssrn.com/abstract=6408920
6. VIPER-MCP: Detecting and Exploiting Taint-Style Vulnerabilities in MCP Servers (arXiv:2605.21392, May 2026).
7. Adaptation of Agentic AI: A Survey of Post-Training, Memory, and Skills (arXiv:2512.16301, 2025).
8. Isabl MCP Agent — AACR 2026 Abstract 27. https://doi.org/10.1158/1538-7445.am2026-27
9. Springer — The MCP Standard (For the Tool Provider: Creating an MCP Server). https://link.springer.com/10.1007/979-8-8688-2364-0_7
