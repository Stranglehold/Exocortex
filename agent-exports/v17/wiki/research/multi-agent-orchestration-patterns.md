# Multi-Agent Orchestration Patterns

**Status:** STABLE
**Created:** 2026-06-05
**Last Updated:** 2026-06-05
**Interest:** AI Agent Architecture & Local Inference
**Line Count:** ~350

## Overview

How do you coordinate multiple AI agents — each with specialized capabilities, tool access, and context windows — to achieve goals beyond any single agent? Multi-agent orchestration patterns address task decomposition, inter-agent communication, conflict resolution, and result aggregation in composable agent systems.

The 2026 landscape has consolidated around three dominant frameworks (LangGraph, CrewAI, Microsoft AutoGen) plus a significant custom-orchestration minority. Orogat et al. (2026) provide the first controlled empirical study showing that framework-level architectural choices alone can increase latency by over 100x, reduce planning accuracy by up to 30%, and lower coordination success from above 90% to below 30% — isolating the effect of architecture from model quality.

Production deployments still favor custom orchestration at the upper end, but frameworks have closed the gap meaningfully (Presenc AI, May 2026). The real success factors are eval pipeline, observability, and failure recovery — not framework selection.

## 2026 Framework Landscape

### Production Adoption (Q1 2026 estimates, Presenc AI)

| Framework | Production Deployments | Primary Pattern | Best For |
|-----------|----------------------|-----------------|----------|
| LangGraph | ~38% | Graph-state machine, supervisor | Enterprise production |
| Custom (Python/TS) | ~28% | Bespoke | Highest-control production |
| CrewAI | ~12% | Role-based crews, hierarchical | Rapid prototyping |
| AutoGen (AG2) | ~9% | Conversational agents, debate | Research & academia |
| Anthropic Skills | ~5% | Skill-based orchestration | Anthropic-native |
| Google ADK | ~4% | Modular agent definitions | GCP-native |
| OpenAI Swarm | ~2% | Handoff pattern | Narrow handoff flows |
| Other (Semantic Kernel, etc.) | ~3% | — | — |

### Core Framework Philosophies (Iterathon, Dec 2025)

- **LangGraph**: Graph-based state machines with explicit edges and conditional routing. Treats agent workflows as deterministic graph traversal problems. Best observability and debugging; steepest learning curve.
- **CrewAI**: Role-based "crew" abstraction — intuitive for prototyping, rapid time-to-demo. Weaker production observability and error recovery.
- **AutoGen**: Generic conversational agent infrastructure. Agents exchange messages through publish-subscribe topics. Maximally flexible; few guardrails.

The framework debate is largely a distraction. The gap between good and bad agent systems is almost never the framework — it's the eval pipeline, observability, and failure recovery logic.

## MAFBench: Empirical Framework Comparison (Orogat et al., arXiv:2602.03128v1, 2026)

Orogat et al. introduce MAFBench, the first unified evaluation suite for multi-agent LLM frameworks that isolates architectural effects from model quality. Their architectural taxonomy covers orchestration overhead, memory behavior, planning, specialization, and coordination.

**Key Findings:**

| Metric | Framework Variance | Significance |
|--------|-------------------|-------------|
| Latency | >100x between frameworks on identical tasks | Architecture overhead dominates model inference time |
| Planning Accuracy | Up to 30% reduction | Some architectures induce systematic planning failures |
| Coordination Success | >90% to <30% in worst case | Some architectures collapse coordination on complex multi-step tasks |

**Design Principles (from MAFBench):**
1. **Routing determinism matters**: Non-deterministic routing (LLM-decided at each step) introduces coordination failure compounding. Supervisor patterns with explicit temperature=0 routing outperform conversational handoffs.
2. **State locality**: Shared mutable state increases debugging complexity superlinearly with agent count. Message-passing with immutable state snapshots scales better.
3. **Recovery surface**: Architectures that allow a supervisor to detect and re-route failed subtasks outperform architectures where agents must self-recover.
4. **Memory isolation**: Separate per-agent memory (with controlled read access) outperforms shared memory architectures on coordination tasks by 40% on MAFBench.

## Message-Passing Architectures

### 1. Supervisor Pattern (LangGraph)

The supervisor pattern uses a central orchestration agent that routes tasks to specialized sub-agents, receives results, and decides next steps. Implemented in LangGraph via `create_supervisor()` from the `langgraph-supervisor` helper package (LangGraph 0.6.x, CallSphere 2026).

**Topology**: Star — supervisor at center, workers at leaves. Workers return to supervisor; supervisor decides next step or FINISH.

```
User -> Supervisor -> [Research | Code | Math | Writing] -> Supervisor -> FINISH
```

**Production-grade concerns** (CallSphere, 2026):
- **Supervisor temperature=0**: Routing must be deterministic. Workers can use temperature for creativity.
- **Worker scope defense**: Each worker prompt includes explicit deferral instructions ("if asked to do math, route to math specialist"). This prevents scope creep at leaves.
- **`output_mode="last_message"`**: Reduces context window pressure vs `"full_history"`. Full history logged to LangSmith for debugging.
- **`recursion_limit=25`**: Bounds worst-case routing loops. When hit, fix the supervisor prompt, not the limit.
- **Custom State subclass**: Workers append structured updates (citations, draft) to shared state without dumping entire conversation history.

**Eval Pipeline** (CallSphere): Three metrics scored per run: (1) Route accuracy — did supervisor pick the right specialist? (2) Tool calls per task — efficiency signal. (3) Task completion — did the team deliver the correct answer?

### 2. Conversation/Debate Pattern (AutoGen)

The multi-agent debate pattern (AutoGen `publish_message()` API) simulates multi-turn interaction where agents exchange and refine responses based on neighbor input. Uses sparse communication topology ("Improving Multi-Agent Debate with Sparse Communication Topology").

**Architecture**:
- **Solver agents**: Each receives the problem, publishes an answer to its neighbors in each round, refines using neighbor responses, then publishes a final answer.
- **Aggregator agent**: Distributes problems, collects final responses, applies majority voting to produce the answer.
- **Sparse connections**: Not all solvers see all others — reduces communication overhead and diversity collapse.

**Evaluated on**: GSM8K math benchmark with majority voting aggregation.

**Pros/Cons**:
- **Strength**: Diversity of perspectives reduces single-agent hallucination; majority voting suppresses outlier errors.
- **Weakness**: Multi-round debate is token-expensive (N agents x M rounds x K tokens each). Communication overhead grows quadratically with dense topologies.
- **Empirical**: Debate improves accuracy on reasoning tasks by 5-15% over single-agent baselines, but cost increases 3-8x (AutoGen docs).

### 3. Hierarchical Pattern

Supervisor of supervisors — sub-teams have internal supervisors, with a top-level supervisor coordinating sub-teams. LangGraph supports this but CallSphere notes it's overkill below ~8 specialists. Triple the cost; only worth it for large teams with internal specialization.

### 4. Network/P2P Pattern

Every agent can call every other agent. LangGraph's "network" topology — genuinely peer-to-peer collaboration. Rare in practice because combinatorial routing decisions make evaluation and debugging near-impossible.

### 5. Sequential/Parallel Pipeline

Fixed-order agent execution: A -> B -> C. Agents process sequentially without routing decisions. Simple, debuggable, predictable latency. Used for well-understood workflows (research -> draft -> review -> publish).

## Task Decomposition Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| Functional | Split by capability: research, code, math, writing | General-purpose teams |
| Sequential | Phase-gated: plan -> execute -> verify -> summarize | Structured workflows |
| Multi-perspective | Same problem to N agents, aggregate results | Factual verification, debate |
| Hierarchical | Sub-teams with internal decomposition | Large-scale projects |
| Dynamic | Supervisor decomposes at runtime based on task | Flexible, variable-scope tasks |

## Failure Modes

| Failure | Description | Mitigation |
|---------|-------------|------------|
| Routing loops | Supervisor keeps routing to wrong specialist who defers back | Strong deferral instructions in worker prompts; recursion limit |
| Scope creep | Worker agent performs work outside its specialization | Explicit scope boundaries in worker system prompts |
| Context bleed | Agent receives irrelevant conversation history from other agents | `output_mode="last_message"`; structured state over raw history |
| Hallucination cascade | One agent's hallucination propagates through subsequent agents | Multi-perspective debate; verify before downstream passing |
| Deadlock | Multiple agents waiting for each other's output | Supervisor timeout and re-route; explicit handoff protocols |
| Bottleneck | Supervisor becomes overloaded with routing decisions | Hierarchical delegation for >8 specialists |
| Coordination collapse | >90% to <30% on complex tasks due to architecture (MAFBench) | Supervisor pattern with deterministic routing; explicit termination criteria |

## Exocortex Architecture Mapping

- **`call_subordinate`**: Implements the central coordinator/supervisor pattern — Agent Zero delegates to specialized subordinates.
- **BST classification**: Domain-sensitive routing analogous to hierarchical task decomposition.
- **Supervisor loop**: Multi-tier intervention patterns (WARN -> SUMMARIZE -> RESET) map to production failure recovery.
- **Knowledge graph**: Shared memory architecture between subordinate agents.
- **Receipt layer**: Structural verification — every self-modifying action closes the loop, analogous to supervisor eval pipeline.
- **Epistemic Integrity**: Cross-agent claim verification analogous to multi-agent debate/verification.

## Cross-Domain Connections

- **Intelligence analysis**: All-source fusion, collection management -> multi-INT corresponds to multi-agent result aggregation. Analysis of Competing Hypotheses (ACH) maps to multi-agent debate pattern for hypothesis verification.
- **Entity resolution**: Parallel matching across registries -> embarrassingly parallel agent task decomposes cleanly into functional separation.
- **Bridging local-to-frontier**: Distributing inference across models -> tiered agent execution (small models at leaves, frontier model as supervisor) implements the supervisor pattern with heterogeneous capability.
- **OSINT investigation**: Multi-tool orchestration -> tool delegation and result synthesis mirrors the supervisor pattern.
- **Distribution automation**: Multi-agent FLISR solutions -> decentralized agent coordination with explicit recovery boundaries.
- **Influence operations detection**: Multi-agent ACH -> debate/verification pattern for detecting coordinated narratives.
- **Intelligence failure analysis**: Groupthink, mirror-imaging -> isomorphic to hallucination cascade and coordination collapse in multi-agent systems.
- **Memory architecture taxonomy**: Per-agent episodic memory -> maps to per-agent memory isolation in MAFBench findings (40% coordination improvement).

## References

- Orogat, A., Rostam, A., & Mansour, E. (2026). "Understanding Multi-Agent LLM Frameworks: A Unified Benchmark and Experimental Analysis." arXiv:2602.03128v1.
- Presenc AI (May 2026). "Multi-Agent Orchestration Frameworks 2026." presenc.ai/research/multi-agent-orchestration-frameworks-2026
- Iterathon (Dec 2025). "Agent Orchestration 2026: LangGraph, CrewAI & AutoGen Guide." iterathon.tech
- Tensoria (May 2026). "LangGraph vs CrewAI vs AutoGen vs Custom [2026 Benchmark]." tensoria.fr
- CallSphere (2026). "LangGraph Supervisor Pattern: Orchestrating Multi-Agent Teams in 2026." callsphere.ai/blog/langgraph-supervisor-multi-agent-orchestration-2026
- Microsoft AutoGen Documentation. "Multi-Agent Debate." microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/multi-agent-debate.html
- LangCopilot (Nov 2025). "Best Multi-Agent AI Frameworks 2026: CrewAI vs AutoGen vs LangGraph." langcopilot.com
- Zhu, C., Dastani, M., & Wang, S. (2022). "A Survey of Multi-Agent Deep Reinforcement Learning with Communication." arXiv:2203.08975v2.

## Verification Status

- [x] MAFBench empirical framework comparison integrated (arXiv:2602.03128v1)
- [x] AutoGen debate pattern deep-dive with architecture and evaluation
- [x] LangGraph supervisor pattern with production case studies (CallSphere)
- [x] Message-passing architectures enumerated (supervisor, debate, hierarchical, network, pipeline)
- [x] Failure modes with mitigations
- [x] Exocortex architecture mapping
- [x] Cross-domain connections with intelligence analysis, entity resolution, bridging local-to-frontier, intelligence failure analysis
- [ ] Additional arXiv sources on multi-agent LLM coordination (MAFBench is primary; secondary sources pending)
- [ ] Production deployment case study from a major enterprise user
