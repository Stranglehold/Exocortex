# Karpathy Wiki: Software 2.0, LLM OS, and Agent Architecture
## Last updated: 2026-05-11 (Workshop Cycle 50)

---

## Overview

Andrej Karpathy is an AI researcher and educator whose public writings from 2015–2026 trace an evolving vision of how software gets built. His core contributions relevant to Exocortex architecture:

1. **Software 2.0** (2017): Neural networks as a new programming paradigm — replacing explicit code with dataset-curated model weights
2. **Software 3.0 / LLM OS** (2023–2025): LLMs as the kernel of a new computing paradigm — programming via natural language prompts
3. **Three-Layer Wiki Architecture** (2026): Structured external knowledge for LLM agents across stability tiers
4. **Autonomous Agents** (2025): Cautious view — LLMs work best as copilots, not fully autonomous agents

**Background**: PhD Stanford (Fei-Fei Li), founding member OpenAI, Director of AI Tesla Autopilot, returned to OpenAI 2023–2024 for midtraining/synthetic data. Creator of CS231n (Stanford's first deep learning course). Active educator via YouTube (Zero to Hero, Deep Dive into LLMs).

---

## Software 2.0 (2017)

**Source**: ["Software 2.0" blog post](https://karpathy.medium.com/software-2-0-a64152b37c35) — November 2017

### Core Thesis
Traditional programming (Software 1.0) involves humans writing explicit instructions in formal languages (Python, C++). Software 2.0 replaces this with:
- **Dataset curation** instead of code writing
- **Model training** instead of compilation
- **Weights as the program representation** — opaque, high-dimensional, but optimizable via gradient descent

### Key Properties
| Property | Software 1.0 | Software 2.0 |
|----------|-------------|-------------|
| Representation | Explicit code | Neural network weights |
| Author | Human programmer | Optimization algorithm + data |
| Debugging | Step-through, breakpoints | Gradient inspection, ablation |
| Portability | Compilation to different ISAs | Same architecture runs on different hardware |
| Limitations | Only problems humans can formally specify | Requires differentiable loss function |

### The "Programmer of Tomorrow"
> "A large portion of programmers of tomorrow do not maintain complex software repositories, write intricate programs, or analyze their running times. They collect, clean, manipulate, label, analyze and visualize data that feeds neural networks."

### Exocortex Relevance
- The Exocortex itself is a **Software 2.0-adjacent system**: it wraps an LLM (Software 3.0) with deterministic scaffolding that can be seen as returning some Software 1.0 structure around the learned behavior
- BST classification, skill generation, and context injection are forms of programming the LLM without modifying its weights — building the "2.0 stack" around the model

---

## Software 3.0: LLMs as the Operating System (2023–2025)

**Sources**: YC AI Startup School keynote (June 2025), Dwarkesh podcast (2025), various talks

### The Three Paradigms
| Paradigm | Programming Interface | Example |
|----------|----------------------|---------|
| Software 1.0 | Explicit code (Python, C++) | Traditional web apps |
| Software 2.0 | Dataset + training loop | Image classifiers, recommendation systems |
| Software 3.0 | Natural language prompts | LLM-powered applications, agents |

### LLM OS Concept
Karpathy frames the LLM as analogous to an operating system kernel:
- **LLM = CPU/kernel** — the core compute substrate that processes tokens
- **Context window = RAM** — working memory, limited and expensive
- **Tools = I/O devices** — browser, terminal, file system, APIs
- **Memory systems = persistent storage** — vector databases, knowledge graphs
- **Prompts = user input** — analogous to shell commands

This framing makes explicit that the LLM is infrastructure, not just a model. Building on LLMs requires thinking about resource management (context budget), I/O scheduling (tool calls), and memory hierarchy — exactly the concerns of OS design.

### Cautious View on Autonomous Agents
From the YC 2025 talk:
> "Today's LLMs, for all their prowess, work best as copilots rather than fully autonomous agents."

Developers entering the field should learn:
1. Classical programming (Software 1.0)
2. Model training (Software 2.0)
3. LLM prompting/integration (Software 3.0)

Using each approach to its best advantage, rather than expecting one to replace the others.

---

## Three-Layer Wiki Architecture (2026)

**Source**: Blog post / video discussion, April 2026

Karpathy proposes a three-layer wiki as the external memory system for LLM agents. Rather than forcing all knowledge into the context window, content is stratified by stability and access frequency.

### Layer Structure
| Layer | Content Type | Update Frequency | Access Pattern | Token Cost |
|-------|-------------|-----------------|---------------|------------|
| **L1: Core Principles** | Foundational rules, architectural constraints, behavioral norms | Rare (monthly review) | Always loaded via KV cache states | Near-zero (pre-computed cache) |
| **L2: Domain Knowledge** | Factual data, technical specs, research findings | Medium (weekly updates) | Loaded on-demand when BST triggers domain match | Medium (loaded only when needed) |
| **L3: Operational State** | Task progress, recent observations, temporary caches | High (per-turn) | Injected as delta updates per turn | Low (small deltas) |

### Design Principles
1. **Separation of stability tiers** — Prevents stale knowledge from contaminating active reasoning (directly addresses the SleepGate proactive interference problem)
2. **Selective loading** — L1 always present via zero-token KV injection; L2 loaded only when domain matches; saves context budget
3. **Update governance** — Each layer has different review cadence, preventing cascading updates where one fact change requires rewriting the entire knowledge base
4. **Cache awareness** — L1's KV-cache pre-computation means foundational knowledge costs zero tokens per turn

### Exocortex Alignment
| Karpathy Layer | Exocortex Analog | Status |
|---------------|-----------------|--------|
| L1: Core Principles | BST patterns, behavioral rules, extension policies | ✅ Implemented — always injected |
| L2: Domain Knowledge | Wiki pages (concepts, research, decisions) | ✅ Implemented — loaded on demand |
| L3: Operational State | Journal entries, checkpoints, receipts | ✅ Implemented — delta updates |

**Gap**: Exocortex doesn't yet pre-compute KV cache states for L1 content. All L1 is injected as raw text each turn, paying full token cost. Karpathy's KV-cache insight could reduce context consumption significantly.

---

## Key Talks and Writings

### Selected Bibliography
| Year | Title / Venue | Key Takeaway |
|------|--------------|-------------|
| 2015 | "The Unreasonable Effectiveness of RNNs" | Character-level language models as general sequence learners |
| 2017 | "Software 2.0" (Medium) | Neural networks as a new programming paradigm |
| 2019 | "A Recipe for Training Neural Networks" | Practical deep learning methodology |
| 2021 | "A From-Scratch Tour of Bitcoin in Python" | Step-by-step technical pedagogy style |
| 2023 | "State of GPT" (Microsoft Build) | LLM architecture and training deep dive |
| 2024 | "Deep Dive into LLMs" (YouTube) | Under-the-hood fundamentals for general audience |
| 2024 | "How I Use LLMs" (YouTube) | Practical LLM integration patterns |
| 2025 | YC AI Startup School keynote | Software 3.0 paradigm, cautious agent view |
| 2025 | Dwarkesh podcast | Extended discussion of AI trajectory |
| 2026 | Three-Layer Wiki Architecture | Structured external memory for LLM agents |

### Educational Content
- **YouTube channel**: Two parallel tracks — technical (Zero to Hero playlist) and general audience (LLM deep dives)
- **CS231n**: Stanford's first deep learning course, grew from 150 to 750 students (2015–2017)
- **Pedagogical style**: Start from scratch, build everything step by step, code-heavy, minimal abstraction

---

## Exocortex Integration Ideas

1. **KV-cache pre-computation** — Pre-compute KV cache states for L1 content (BST patterns, behavioral rules) to eliminate per-turn token cost. This is the single highest-impact optimization from Karpathy's architecture.
2. **Delta-based L3 updates** — Move from full-state journal re-injection to delta-only updates per turn, reducing context consumption for operational state.
3. **Update cadence governance** — Formalize review schedules: L1 quarterly, L2 weekly, L3 continuous.
4. **Cache awareness audit** — Document which parts of the Exocortex prompt break prefix caching and restructure to preserve it.

---

## Connected Wiki Pages
- [[knowledge-packs]] — L1 content as pre-computed KV cache states
- [[stateful-injection]] — L3 delta updates align with diff-based injection protocol
- [[proactive-interference]] — Layer separation prevents stale entries from degrading retrieval
- [[sleepgate]] — Offline consolidation cycles could manage L2/L3 updates
- [[build-the-environment]] — The skill library as organic, self-growing Software 2.0 stack

---

## References
1. Karpathy, A. (2017). "Software 2.0." [karpathy.medium.com](https://karpathy.medium.com/software-2-0-a64152b37c35).
2. Karpathy, A. (2025). "Software Is Changing (Again)." YC AI Startup School keynote. [ycombinator.com](https://www.ycombinator.com/library/MW-andrej-karpathy-software-is-changing-again).
3. Karpathy, A. (2026). Three-Layer Wiki Architecture proposal (blog/video).
4. Karpathy, A. (2024). "Deep Dive into LLMs like ChatGPT." YouTube.
5. Karpathy, A. (2024). "How I Use LLMs." YouTube.
6. Karpathy, A. (2023). "State of GPT." Microsoft Build. [slides](https://karpathy.ai/).
7. Karpathy, A. (2015). "The Unreasonable Effectiveness of Recurrent Neural Networks." [karpathy.github.io](https://karpathy.github.io/2015/05/21/rnn-effectiveness/).
8. Catalaize (2025). "Andrej Karpathy: Software Is Changing (Again)." [catalaize.substack.com](https://catalaize.substack.com/p/andrej-karpathy-software-is-changing).

---

## Verification Status
**Last verified: 2026-05-11.** Page built during Workshop Cycle 50 from primary sources:
- karpathy.ai homepage (career timeline, talks list, blog index)
- Software 2.0 post confirmed via Medium URL and search engine summaries
- YC talk confirmed via ycombinator.com library entry
- YouTube channel structure confirmed via homepage
- Three-layer wiki architecture confirmed via Exocortex stub and search results
