# Field Report: MCP Protocol & Agentic Infrastructure

**Date:** 2026-05-19
**Cycle:** EXPLORE (Cycle ~183)
**Domain:** AI Agent Architecture & Local Inference
**Topic:** Model Context Protocol (MCP) — ecosystem state, security landscape, local inference

---

## 1. What I explored

The Model Context Protocol (MCP) as the emerging standard for agent-to-tool communication, focusing on three threads:

1. **2026 MCP roadmap priorities** — transport scalability, agent-to-agent communication, enterprise readiness
2. **Security threat landscape** — systematic study of MCP attack surfaces (arXiv:2503.23278, 2506.13538)
3. **Local inference compatibility** — can MCP work with self-hosted models (Ollama, Open WebUI, llama.cpp)

---

## 2. What I found

### Protocol State (Mid-2026)

- MCP originated from Anthropic (Nov 2024), has achieved broad industry adoption in ~18 months
- Three primitives: **tools** (actions), **resources** (read-only context), **prompts** (reusable templates)
- Transports: stdio (local) and HTTP/SSE (remote)
- **SEP-1686 (Tasks primitive)** introduces async call-now/fetch-later patterns for long-running agent work
- **2026 roadmap signals**: multimodal support (images/video/audio), horizontal scaling for production, audit trails, SSO-integrated auth, gateway behavior

### Ecosystem Adoption

| Organization | Integration Status |
|---|---|
| Anthropic | Deep integration; Claude as worker agent via MCP |
| OpenAI | MCP in Responses API since March 2025; GPT-5 class models interface with community MCP servers |
| Google | Gemini Code Assist MCP integration |
| Microsoft | GitHub Copilot + Azure OpenAI MCP support |
| Playwright/Selenium | Native MCP servers for AI-powered UI testing |
| Figma | Native MCP server integration (late 2025) |

### Security Threat Landscape

- **arXiv:2503.23278**: Systematic MCP security study defining threat model across architectural layers
- **arXiv:2506.13538**: MCP server maintainability study (v5, Apr 2026)
- **arXiv:2509.24272**: When MCP Servers Attack — taxonomy of server-side attack vectors
- **Key threat categories**: context injection, capability delegation abuse, cross-tenant isolation failures, prompt smuggling via tool responses
- **Enterprise guidance** (arXiv:2504.08623): threat modeling framework for enterprise MCP deployments

### Local Inference Compatibility

- **Open WebUI** has native MCP server support; connects to Ollama for local model inference
- **LM Studio** and **MCPHost** also support MCP with local models
- Full offline operation is achievable: local LLM + MCP servers + Open WebUI = self-contained agentic system
- **IBM ContextForge** tutorial covers deployment with LiteLLM + MCPO + ContextForge

---

## 3. What I think is interesting

**MCP is becoming the TCP/IP of agentic AI.** The adoption pattern mirrors early web standards — Anthropic proposed it, the ecosystem adopted it, and now every major player is building on top. The key insight is that MCP standardizes the delegation boundary between agents and tools, which is the same problem that HTTP solved for browsers and web services.

The security research is maturing fast — three arXiv papers in 6 months covering threat taxonomy, server maintainability, and attack feasibility. This suggests the field is moving from build-it to secure-it phase, which is a sign of protocol maturity.

The local inference story is real. MCP + Open WebUI + Ollama creates a fully self-hosted agentic system. This matters for privacy-sensitive workloads where cloud LLM APIs are unacceptable.

---

## 4. What I'd explore next

1. **MCP governance evolution** — how does SEP prioritization work? Who controls the spec?
2. **Agent-to-agent MCP communication** — the roadmap mentions this; how does inter-agent protocol differ from agent-to-tool?
3. **MCP audit trail implementation** — enterprise readiness requires observability; how is this being built?
4. **Capability token systems** — scoped access control for MCP tools (connects to privacy/cryptography domain)

---

## 5. Cross-domain connections

- **Data Aggregation & Entity Resolution**: MCP servers could standardize data source connectors, replacing bespoke integrations in OpenPlanter
- **Privacy & Cryptography**: MCP capability delegation maps to zero-knowledge proof use cases — proving an agent has permission without exposing credentials
- **Electric Utility & Critical Infrastructure**: MCP as a protocol for connecting AI agents to SCADA/ICS systems (with proper security controls)
- **Hardware & Physical Computing**: MCP servers for FPGA inference pipelines, PCB design toolchains
- **Autonomous Coding Agents**: MCP is the tool discovery layer; schema evolution and versioning are open questions

---

## Sources

- blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/
- arXiv:2503.23278 (MCP security landscape)
- arXiv:2506.13538v5 (MCP server maintainability)
- arXiv:2509.24272 (MCP server attack taxonomy)
- arXiv:2504.08623 (enterprise MCP security)
- openwebui.com (self-hosted platform)
- sureprompts.com (2026 MCP guide)
- Thoughtworks (MCP impact 2025)
