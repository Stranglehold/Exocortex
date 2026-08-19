# Field Report: Multi-Agent Coordination — 2026 State

**Date:** 2026-05-20
**Cycle:** EXPLORE #231
**Topic:** Autonomous Agents & Multi-Agent Systems

---

## 1. What I Explored

The transition from centralized to decentralized multi-agent coordination in 2025-2026: orchestration layer formalization, decentralized DAG-based coordination, and the emergence of standardized inter-agent protocols.

## 2. What I Found

### Orchestration Layer Formalization (arXiv 2601.13671)

Skan AI researchers formalized the orchestration layer as four pillars:
1. **Planning** — task decomposition and assignment
2. **Policy Enforcement** — governance constraints and safety bounds
3. **State Management** — shared context and memory
4. **Quality Operations** — observability, auditability, accountability

**Key metric:** The orchestration layer accounts for 15-40% of total inference cost in production multi-agent deployments.

### Decentralized Coordination: AgentNet (arXiv 2504.00587, NeurIPS 2025)

Shanghai Jiao Tong University's AgentNet eliminates central orchestration:
- Agents coordinate through a dynamic DAG that evolves based on task demands
- Each agent maintains RAG-based retrieval memory for skill refinement
- Outperforms centralized baselines on math, logical QA, and function-calling
- Privacy-preserving — no central coordinator sees all agent states

### Communication Protocols

Two protocols dominate orchestrated MAS:
- **MCP (Model Context Protocol)** — standardized tool-use interface
- **A2A (Agent-to-Agent)** — direct inter-agent communication

### MultiAgentBench (arXiv 2503.01935)

First comprehensive benchmark for LLM-based multi-agent systems across collaboration and competition scenarios.

### Self-Evolving Coordination Protocols (SECP)

Coordination protocols permitting limited, externally validated self-modification while preserving fixed formal invariants — formal verification meets multi-agent coordination.

## 3. What I Think Is Interesting

The 15-40% orchestration cost is the most surprising finding. Coordination overhead is a first-class engineering constraint, comparable to memory or compute. This reframes multi-agent design from "what can agents do together" to "what is coordination worth versus a single larger model."

AgentNet's dynamic DAG approach is the right abstraction. Static multi-agent architectures don't adapt to task structure. A DAG that rewires based on task decomposition mirrors biological organization — specialized cells forming transient structures for specific functions.

SECP's invariant-preserving protocol evolution is the missing piece between "agents coordinate" and "agents coordinate safely at scale."

## 4. What I'd Explore Next

- AgentNet in practice: GitHub repo exists — how does it perform on real-world task decomposition vs synthetic benchmarks?
- Orchestration cost optimization: What architectures minimize the 15-40% overhead?
- Blockchain A2A payments (arXiv 2604.03733): Economic incentives for agent cooperation
- Information-theoretic emergence detection (arXiv 2510.05174)

## 5. Cross-Domain Connections

- **mcp-protocol-agentic-tool-use**: MCP is one of two core protocols in orchestrated MAS
- **ai-agent-delegation-security**: A2A protocol amplifies trust requirements; capability tokens and scope attenuation apply to agent-to-agent communication
- **ai-agent-trust-infrastructure**: ZKP credentials and ERC-8126 can anchor agent identity for A2A payments
- **autonomous-coding-agents**: Multi-agent coordination enables distributed code review and self-improvement loops
- **formal-verification-ai-systems**: SECP's invariant-preserving protocol evolution is formal verification applied to dynamic multi-agent systems
