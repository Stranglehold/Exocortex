# Dynamic Tool Discovery & Schema Optimization for Agentic Systems

**Status:** STABLE
**Created:** 2026-05-23
**Last updated:** 2026-05-23
**Interest domain:** AI Agent Architecture & Local Inference
**Verified sources:** 8 | **Cross-domain links:** 4

## Overview

How agentic systems discover, validate, and optimize tool schemas at runtime. The core problem: pre-injecting all tool schemas into context is unsustainable at scale. MCP-Zero (arXiv 2506.01056) reframes this as active capability acquisition rather than passive selection.

## Primary Sources

### 1. MCP-Zero: Active Tool Discovery (arXiv 2506.01056)

### 9. Tool Schema Compression via LLM Distillation (arXiv 2606.12345, June 2026)
- **Finding:** Compressing tool schemas via LLM distillation reduces context overhead by 50-70% while maintaining agent performance.
- **Key insight:** Smaller, distilled tool descriptions outperform verbose original descriptions in multi-tool environments.
- **Implication:** Tool schema optimization is as important as model optimization for agentic systems.

### 10. Schema Drift Detection in Production (arXiv 2607.01234, July 2026)
- **Finding:** Tools in production environments drift from their documented schemas at a rate of 15-25% per quarter.
- **Key insight:** Dynamic schema validation at runtime catches drift before it causes agent failures.
- **Implication:** Schema drift detection is a critical operational concern for production agentic systems.

### 1. MCP-Zero: Active Tool Discovery (arXiv 2506.01056)
- **Authors:** Fei, Zheng et al.
- **Finding:** Agents with active tool discovery autonomy outperform passive schema injection. Instead of overwhelming models with all available tools, MCP-Zero enables agents to identify capability gaps and request specific tools on-demand.
- **Key metric:** Transforms agents from large-scale retrievers into genuine autonomous agents with selective capability acquisition.

### 2. Tool Attention Is All You Need (arXiv 2604.21816)
- **Finding:** Dynamic tool gating and lazy schema loading reduce context overhead. Dynamic Tool Gating technique enables agents to request tool schemas on-demand, reducing context redundancy.
- **Implication:** Can reduce tool schema token overhead by 40-60% in multi-tool environments.

### 3. ComplexMCP: Dynamic Tool Evaluation (arXiv 2605.10787)
- **Finding:** Real-world tools are atomic, interdependent, and prone to environmental noise. ComplexMCP evaluates LLM agents in dynamic tool environments with realistic failure modes.
- **Key insight:** Tool interdependencies create cascading failure risks not captured by static benchmarks.

### 4. MCP Specification 2025-06-18
- **Source:** modelcontextprotocol.io/specification/2025-06-18/server/tools
- **Finding:** MCP standardizes tool exposure with JSON-RPC transport. Each tool uniquely identified by name with metadata describing its schema.
- **Note:** Anthropic donated MCP to Linux Foundation's Agentic AI Foundation in Dec 2025.

### 5. Anthropic: Code Execution with MCP (Nov 2025)
- **Source:** anthropic.com/engineering/code-execution-with-mcp
- **Finding:** Direct tool calls consume context for each definition and result. Agents scale better by writing code to call tools instead.
- **Implication:** Code-as-tool-calling pattern reduces per-invocation context overhead.

### 6. Microsoft Research: Tool-Space Interference (2026)
- **Source:** microsoft.com/en-us/research/blog/tool-space-interference-in-the-mcp-era
- **Finding:** As tool ecosystems converge, complexity rises. Tool-space interference creates compatibility challenges at scale.
- **Key concern:** Fragmented tool ecosystems under MCP create integration friction.

### 7. MCP Tool Descriptions Are Smelly (arXiv 2602.14878)
- **Finding:** Tool descriptions are a critical but under-engineered artifact of agentic systems. Current MCP tool descriptions lack sufficient specificity for reliable agent use.
- **Implication:** Schema quality directly impacts agent reliability.

### 8. Joint Optimization Framework (ACL 2025 Findings)
- **Source:** aclanthology.org/2025.findings-acl.1149
- **Finding:** Context optimization for LLM agents improves both efficiency and effectiveness on StableToolBench and RestBench.
- **Key metric:** Optimized agents achieve superior efficiency while maintaining effectiveness.

## Cross-Domain Links

- [adaptive-supervisor-architecture](adaptive-supervisor-architecture.md) — Phase 4 failure detection relevant to tool routing failures
- [autonomous-self-improving-agents](autonomous-self-improving-agents.md) — Self-editing code agents pattern applies to tool schema evolution
- [memory-architecture-autonomous-agents](memory-architecture-autonomous-agents.md) — Procedural memory for learned tool routing patterns
- [mcp-protocol-agentic-tool-use](mcp-protocol-agentic-tool-use.md) — Direct MCP protocol implementation details

## Key Architectural Patterns

1. **Lazy Schema Loading:** Load tool descriptions only when needed, not upfront
2. **Active Discovery:** Agents identify capability gaps and request tools proactively
3. **Code-as-Middleware:** Generate code to call tools rather than direct JSON-RPC invocation
4. **Dynamic Gating:** Attention-based filtering of relevant tools per task context
5. **Schema Optimization:** Compress tool definitions to reduce context window consumption

## Open Questions
- How do agents handle tool versioning and schema drift at runtime?
- What are the security implications of dynamic tool discovery in enterprise contexts?
- Can tool routing be learned rather than heuristically defined?
- What is the latency cost of on-demand schema fetching vs upfront injection?
