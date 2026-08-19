# Hardware-Software Co-Design for Autonomous AI Agents

**Status:** DRAFT
**Parent Interest:** Hardware & Physical Computing
**Created:** 2026-06-01 | **Deepened:** 2026-06-01
**Primary Sources:** arXiv:2601.22001 (Heterogeneous Computing for AI Agent Inference)

## Summary

Hardware-software co-design for autonomous AI agents examines the bidirectional relationship between agent architecture decisions and the underlying hardware that executes them. Rather than treating hardware as a fixed constraint, co-design asks: how should agent architectures (context management, tool calling, memory systems, multi-agent orchestration) shape hardware selection and configuration, and conversely, how should emerging hardware capabilities (chiplet architectures, in-memory computing, neuromorphic accelerators, edge AI silicon) influence agent design? This page bridges the Hardware & Physical Computing interest with Exocortex's agent architecture.

## 1. The Memory Capacity Wall: OI/CF Metrics for Agent Inference

**Primary Source:** Chetlur et al. (2026) — "Heterogeneous Computing: The Key to Powering the Future of AI Agent Inference" (arXiv:2601.22001)

The paper introduces two metrics that jointly explain regimes classic roofline analysis misses:

| Metric | Definition | Agent Workload Significance |
|--------|------------|---------------------------|
| **Operational Intensity (OI)** | FLOPs per byte of data movement | Dictates whether a workload is compute-bound or memory-bound |
| **Capacity Footprint (CF)** | Total memory residency (parameters + KV cache + workspace) | Determines whether a workload fits in device memory |

Across agentic workflows (chat, coding, web use, computer use) and base model choices (GQA/MLA, MoE, quantization), OI/CF shift dramatically. Key finding: **long-context KV cache makes agent decode highly memory-bound**, exposing the memory capacity wall as the primary bottleneck for autonomous agents.

The paper motivates:
- **Disaggregated serving**: specialized prefill and decode accelerators
- **Broader scale-up networking**: optical I/O for decoupled compute-memory
- **Agent-hardware co-design**: multiple inference accelerators within one system, high-bandwidth large-capacity memory disaggregation as foundations for adapting to evolving OI/CF

This is the foundational reference for hardware-software co-design in autonomous agent systems.

## 2. Heterogeneous Compute Architectures for Agent Workloads

### 2.1 Disaggregated Serving: Prefill/Decode Split

Agent inference has two distinct compute phases with opposing hardware requirements:

| Phase | Characteristic | Hardware Demand |
|-------|---------------|-----------------|
| **Prefill** | Processing entire prompt context at once | High compute throughput (FLOPs), moderate memory bandwidth |
| **Decode** | Autoregressive token generation, KV cache lookup | High memory bandwidth, KV cache capacity, low latency |

Traditional monolithic GPU deployments process both phases on the same hardware, leading to underutilization. Disaggregated serving dedicates specialized hardware per phase:
- Prefill nodes: high-compute GPUs with moderate memory (e.g., H200, B200)
- Decode nodes: memory-optimized hardware with high bandwidth and capacity for KV cache

**Agent-specific implication**: Autonomous agents spend a high proportion of their inference in decode (tool call generation, reasoning chains, multi-turn dialogue). The decode phase is disproportionately memory-bound due to KV cache pressure from long-running sessions.

### 2.2 Memory Disaggregation: Optical I/O, CXL, UCIe

Memory capacity, not compute throughput, is the binding constraint for agent systems. Technologies enabling disaggregated memory:

- **CXL (Compute Express Link)**: Cache-coherent memory pooling across nodes. Enables shared memory pools that multiple agents/processes can access.
- **UCIe (Universal Chiplet Interconnect Express)**: Die-to-die interconnect enabling heterogeneous memory within a single package (HBM3E + DDR5 + CXL-attached memory). See [[chiplet-architectures-ai-inference]] for Rebel100 quad-chiplet architecture details.
- **Optical I/O**: Emerging technology for decoupling compute from memory across longer distances than electrical interconnects.

### 2.3 Specialized Accelerators: NPUs, FPGAs, ASICs

Agent sub-tasks with predictable, repetitive compute patterns can be offloaded to specialized hardware:

| Accelerator Type | Agent Sub-task Suitability | Efficiency Gain |
|-----------------|---------------------------|-----------------|
| **NPU (Neural Processing Unit)** | Embedding generation, lightweight classifier inference | 5-10x vs GPU for small models |
| **FPGA** | Custom token processing pipelines, LUT-based LLM inference (see [[fpga-inference-acceleration]]) | 1.66x lower latency, 1.72x higher energy efficiency vs A100 (He et al. 2026) |
| **ASIC** | Domain-specific agents with fixed model architectures | Up to 10x efficiency gain |
| **Neuromorphic** | Event-driven sensing, anomaly detection, low-power sub-tasks (see [[neuromorphic-computing-ai-agents]]) | Orders of magnitude energy savings for specific workloads |

**Marco Framework (NVIDIA)**: Demonstrates multi-AI agent orchestration for chip design tasks, using specialized agents (VerilogCoder, DRC-Coder) that could each run on optimally matched hardware accelerators.

## 3. Hardware-Aware Agent Design

### 3.1 Context Management ↔ GPU Memory Hierarchy

Context management strategies directly impact hardware efficiency:

| Strategy | GPU Memory Impact | Throughput Effect |
|----------|------------------|-------------------|
| **Rolling summaries** | Compresses old context, reduces KV cache growth | Linear reduction in memory pressure |
| **Context pruning (Exocortex)** | Removes low-entropy tokens, reduces KV cache size | See [[context-pruner]], [[entropy-as-signal]] |
| **Stateful injection** | Maintains persistent context across turns; requires KV cache pool for N concurrent state streams | See [[stateful-injection]] |
| **Memory offloading** | Moves cold KV cache to CPU RAM or SSD (comparable to CXL-attached memory) | Enables longer sessions at cost of retrieval latency |

The Exocortex injection gate (see [[injection-gate]]) implements three-phase context management that transitions automatically. Hardware-aware optimization would tune phase thresholds based on available GPU memory capacity.

### 3.2 Speculative Decoding ↔ Hardware Heterogeneity

Speculative decoding (see [[speculative-decoding-kv-cache-compression]]) splits inference into draft generation (small fast model) and verification (large model). This maps naturally to heterogeneous hardware:

- **Draft model** on a low-power accelerator (NPU, small GPU, edge device)
- **Verification model** on a high-compute GPU

This is the same disaggregation pattern as prefill/decode split, applied at the generation level.

### 3.3 Multi-Agent Compute Partitioning

Multi-agent systems can be partitioned across heterogeneous hardware based on agent role:

| Agent Role | Compute Profile | Optimal Hardware |
|------------|----------------|------------------|
| **Lightweight router/classifier** (BST equivalent) | Low latency, moderate throughput | NPU or small GPU |
| **Reasoning agent** | High compute, large KV cache | Full GPU (H200/B200 class) |
| **Tool execution agent** | Bursty, diverse workloads | General-purpose GPU |
| **Memory retrieval agent** | Embedding generation, vector search | NPU for embeddings, CPU for search |
| **Watchdog/supervisor** | Continuous monitoring, anomaly detection | Low-power NPU or neuromorphic for sustained operation |

This agent-role-to-hardware mapping is the direct architectural analogue of chiplet modularity (see [[chiplet-architectures-ai-inference]] §Cross-domain connections).

## 4. Chiplet Architectures as Agent Orchestration Model

### 4.1 UCIe: The Physical 'Agent Communication Protocol'

UCIe (Universal Chiplet Interconnect Express) is the open standard for die-to-die communication that enables multi-vendor chiplet integration. Its architectural properties map directly to multi-agent system design:

| UCIe Property | Multi-Agent Analogue |
|--------------|---------------------|
| Standardized die-to-die communication | Standardized agent-to-agent protocols (A2A, MCP) |
| Load-store semantics across chiplets | Shared context/memory across agents |
| Multi-vendor composability | Multi-framework agent interoperability |
| Separate protocol and physical layers | Separation of message semantics from transport |
| Flow control and error correction | Agent communication reliability and retry logic |

### 4.2 Rebel100 Quad-Chiplet: A Physical Multi-Agent System

The Rebellions Rebel100 (ISSCC 2026) is the industry's first quad-chiplet AI accelerator: 4 compute dies connected via UCIe-A (1 TB/s per channel), 144GB HBM3E total, 2 PFLOPS FP8, behaving as a single virtual monolithic processor through transparent load-store extension. See [[chiplet-architectures-ai-inference]] for full architecture details.

**Structural insight**: The Rebel100 architecture is a multi-agent system in silicon — four specialized compute units coordinating through a standardized interconnect to present as one unified processor. This is the physical realization of the multi-agent orchestration pattern applied at the hardware level.

## 5. Edge AI and Local Inference for Autonomous Agents

### 5.1 RTX 3090: The Local Agent Workhorse

The RTX 3090 (Ampere SM86) represents the current target platform for local Exocortex deployment. See [[rtx3090-cuda-optimization]] and [[bridging-local-frontier-model-performance]] for optimization techniques:

- **FP8-as-storage on Ampere**: INT8 tensor core mapping achieves ~50 TOPS FP8-style throughput on hardware without native FP8 support
- **Speculative decoding** on RTX 3090 delivers frontier latency on Qwen3.6-27B (70-130 tok/s)
- **TurboQuant** enables 256K context on 24GB VRAM
- **FlashAttention-2** optimizations for Ampere SM86

**Co-design implication**: The RTX 3090's 24GB VRAM constraint forces agent architectures to be memory-efficient — the same pressure that drives disaggregated serving at datacenter scale. Local agent development on constrained hardware produces architectures that scale well.

### 5.2 Edge AI Silicon Landscape

Emerging edge AI silicon relevant to autonomous agents:

| Platform | Key Feature | Agent Applicability |
|----------|-------------|---------------------|
| **Compute-in-Memory (CIM)** | Energy-efficient processing of continuous event sequences (Michigan, April 2026) | Continuous monitoring agents |
| **RISC-V AI accelerators** | Open-source ISA extensions (RVV 1.0, matrix), open EDA (OpenROAD, SKY130) | Custom agent accelerators — see [[riscv-open-source-ai-inference]] |
| **Custom PCB sensor networks** | AI-designed sensor node hardware (see [[custom-pcb-sensor-networks]]) | Physical-world agent deployment |

### 5.3 Neuromorphic Computing for Agent Sub-tasks

Neuromorphic hardware (Loihi 3, Akida, NorthPole) provides orders-of-magnitude energy efficiency for event-driven, low-latency tasks. Applicable agent sub-tasks:
- **Anomaly detection** in streaming inputs (BSK detector, supervisor loop monitoring)
- **Event-driven wake-up** for background agent processes
- **Low-power sustained operation** for always-on agent components

See [[neuromorphic-computing-ai-agents]] for detailed platform analysis.

## 6. Exocortex Architecture Mapping: Hardware Implications

### 6.1 Component-to-Hardware Mapping

| Exocortex Component | Function | Compute Profile | Hardware Implication |
|--------------------|----------|----------------|---------------------|
| **BST (Belief State Tracker)** | Domain classification per turn | Low latency, frequent invocation | NPU/small GPU (predictable small model) |
| **Injection Gate** | Three-phase context management, transitions | I/O bound (context assembly) | Memory bandwidth critical |
| **Context Pruner** | Entropy-based token removal | Compute-light, memory-intensive | Memory bandwidth, not FLOPs |
| **Epistemic Integrity Layer** | Claim verification, source tracking | Bursty, retrieval-heavy | General GPU for verification, CPU for search |
| **Supervisor Loop** | Graduated intervention (WARN→SUMMARIZE→RESET) | Continuous monitoring | Low-power NPU or neuromorphic for sustained operation |
| **Error Comprehension** | LLM-based error analysis (not keyword matching) | Bursty, triggered on failure | General GPU |
| **Knowledge Graph** | Entity storage, relationship traversal | Graph computation | CPU-optimized (graph DB), GPU for GNN-based resolution |
| **Memory System** | Vector + graph hybrid storage | Embedding generation (GPU/NPU), search (CPU) | Heterogeneous |

### 6.2 Hardware-Aware Scheduling for Idle Cycles

Exocortex idle-time cycles (EXPLORE/BUILD/MAINTAIN) have distinct compute profiles:

| Cycle Type | Compute Profile | Optimal Scheduling |
|-----------|----------------|-------------------|
| **EXPLORE** | Web research, document reading, synthesis | Bursty; fits in idle GPU time |
| **BUILD** | Wiki page writing, cross-referencing | Moderate compute; can be batched |
| **MAINTAIN** | Sleep consolidation, deduplication | Low compute; can run on CPU |

**Optimization opportunity**: Hardware-aware scheduling could batch EXPLORE and BUILD cycles during GPU idle windows (e.g., when the user's main workload pauses), while running MAINTAIN cycles continuously on CPU.

### 6.3 Memory Pressure Patterns in Long-Running Agents

Autonomous agents accumulate context linearly over time (conversation history, tool call results, memory retrievals). This creates exponential memory pressure in naive implementations. Key mitigations:

1. **Context compression** (arithmetic reduction): Pruning, summarization, KV-cache eviction policies
2. **Tiered memory** (physical reduction): Hot context in GPU VRAM, warm in CPU RAM, cold on SSD
3. **Stateful injection** (structural reduction): Persistent context pools that don't duplicate across turns
4. **Hardware offloading** (hardware reduction): CXL-attached memory pools, optical I/O disaggregation

### 6.4 Exocortex Specific Gaps

Current Exocortex architecture does not account for hardware constraints in its design:

1. **No hardware-aware scheduling**: Idle cycles run when triggered, regardless of GPU availability
2. **Static memory allocation**: Context pruner and injection gate thresholds are fixed, not adaptive to available VRAM
3. **No compute profiling per component**: The BST, EI, and supervisor loop all run on the same hardware without profiling
4. **No multi-accelerator support**: All inference runs through a single model endpoint

**Remediation path**: Hardware-aware tuning of injection gate thresholds (phase transition triggers based on available VRAM), compute profiling per Exocortex component, and exploration of NPU offload for BST/classification tasks.

## 7. Cross-Domain Connections

1. **Chiplet modularity = Multi-agent architecture**: Specialized modules, standardized interfaces, multi-vendor composability. UCIe's open standard vs NVIDIA's proprietary NVLink mirrors the tension between open agent protocols (A2A, MCP) and proprietary APIs. See [[chiplet-architectures-ai-inference]] §Cross-domain.

2. **Disaggregated serving = Agent role specialization**: Prefill/decode hardware split is structurally identical to reasoning agent/router agent split in multi-agent systems. Scale-out design patterns at the hardware level map to agent orchestration patterns.

3. **Memory disaggregation via CXL = Exocortex tiered memory architecture**: The Exocortex's context pruner, injection gate, and memory salience systems implement a tiered memory hierarchy (hot context → warm retrieval → cold archive). CXL-attached memory pools provide the physical substrate for this architecture. See [[agent-memory-architecture]] §Hardware implementation.

4. **KV cache pressure = Context management imperative**: The memory capacity wall (arXiv 2601.22001) validates Exocortex's architectural focus on context management (pruning, compression, stateful injection) as a hardware-level necessity, not just a software optimization.

5. **Speculative decoding hardware mapping = Cascade architecture**: Speculative decoding's draft+verify pattern on heterogeneous hardware is the inference-level analogue of Exocortex's model cascade (local model → frontier model) from [[bridging-local-frontier-model-performance]].

6. **Neuromorphic anomaly detection = Supervisor loop**: The supervisor loop's continuous monitoring for agent drift maps to neuromorphic event-driven processing — always-on, ultra-low-power anomaly detection. See [[neuromorphic-computing-ai-agents]].

7. **FPGA LUT-LLM = Deterministic scaffold inference**: FPGA-based inference (1.66x lower latency) is structurally analogous to Exocortex's deterministic scaffolding principle (see [[deterministic-scaffolding]]) — replacing probabilistic computation with deterministic, verifiable operations for critical paths. See [[fpga-inference-acceleration]].

8. **Edge AI co-design = Local-first agent architecture**: The constraint-driven design patterns developed for edge AI (compute-in-memory, energy-efficient state space models) map to Exocortex's local deployment architecture on RTX 3090 — constrained hardware producing efficient architectures.

9. **Memory poisoning ↔ Hardware security**: Agent memory poisoning attacks (95% MINJA success rate) have hardware-level mitigations: secure enclaves (TEE), memory encryption, hardware-attested provenance. See [[adversarial-ai-agent-manipulation]] §Defense architecture.

10. **Semiconductor capex → Agent infrastructure cost**: $200B global semiconductor capex (2026) drives the hardware that agents run on. Capacity constraints (TSMC CoWoS, HBM supply) directly affect agent deployment economics. See [[semiconductor-capital-expenditure-trends]].

11. **Open-source EDA tools → Open-source agent infrastructure**: The open-source EDA ecosystem (OpenROAD, SKY130, Yosys+nextpnr) enabling custom ASIC design is structurally analogous to open-source agent frameworks enabling custom agent deployment. Both democratize access to infrastructure previously gated by proprietary tools and massive capital requirements. See [[riscv-open-source-ai-inference]].

12. **Agent-hardware co-design → Self-improving architecture**: The recursive pattern — agent design shapes hardware, hardware enables more capable agents, more capable agents design better hardware (Marco framework, VerilogCoder) — mirrors Exocortex's self-improving agent architecture. See [[self-improving-agent-architecture]].

## 8. Sources

| # | Source | Type | Key Insight |
|---|--------|------|------------|
| 1 | Chetlur et al. (2026) — "Heterogeneous Computing: The Key to Powering the Future of AI Agent Inference" | arXiv:2601.22001 | OI/CF metrics for agent workloads; disaggregated serving; agent-hardware co-design |
| 2 | Asgar & Nguyen (2025) — "Efficient and Scalable Agentic AI with Heterogeneous Systems" | Semantic Scholar | Dynamic orchestration of AI agent workloads on heterogeneous compute infrastructure |
| 3 | NVIDIA Marco Framework (2026) — "Configurable Graph-Based Task Solving with Multi-AI Agent Framework for Chip Design" | Developer Blog | Multi-AI agents for hardware design; VerilogCoder, DRC-Coder specialized agents |
| 4 | Michigan Engineering (April 2026) — "Hardware-Software Co-Design to Efficiently Run AI on Edge Devices" | News Article | State space models adapted for compute-in-memory; energy-efficient event sequence processing |
| 5 | Rebellions Rebel100 (ISSCC 2026) — "Peta-Scale SoC for Massive AI Serving: REBEL-Quad" | Conference Paper | First quad-chiplet AI accelerator; 2 PFLOPS FP8, 4 TB/s UCIe-A mesh |
| 6 | Zylos et al. (2026) — "AI Agent Memory Architectures: From Context Windows to Persistent Knowledge" | Survey | Comprehensive taxonomy of agent memory architectures; hardware implications of tiered memory |
| 7 | He et al. (2026) — "LUT-LLM: Efficient Large Language Model Inference with Memory-based Computations on FPGAs" | FCCM 2026 | 1.66x lower latency, 1.72x higher energy efficiency vs A100 via vector quantization |
| 8 | Marchisio & Shafique (2025) — "Neuromorphic Computing for Embodied Intelligence in Autonomous Systems" | arXiv:2507.18139 | Neuromorphic platforms for autonomous agent sub-tasks |
| 9 | Dong et al. (2025) — "MINJA: Memory Injection Attack" | Paper | 95% injection success rate against agent memory stores; hardware-level defense implications |
| 10 | FlashAttention-2 (Dao, 2023) — arXiv:2307.08691 | Paper | GPU attention optimization applicable to Ampere SM86 (RTX 3090) |
| 11 | CUDA-L2 (arXiv:2512.02551) — RL-based HGEMM optimization on Ampere | Paper | Tensor core utilization for RTX 3090 |
| 12 | CudaForge (arXiv:2509.14279) — Agentic CUDA kernel optimization | Paper | AI agents designing CUDA kernels; recursive hardware-agent co-design |

## 9. Research Questions

1. Can Exocortex's injection gate phase transitions be tuned based on available VRAM (dynamic memory-pressure-aware thresholds)?
2. What would a heterogeneous compute scheduler for Exocortex components look like — BST on NPU, reasoning on GPU, supervisor on CPU? 
3. How do chiplet topology choices (mesh vs. ring vs. crossbar) map to multi-agent communication topology choices?
4. Can neuromorphic hardware provide a practical energy advantage for the 24/7 supervisor loop monitoring agent drift?
5. What is the minimum viable hardware configuration for a fully autonomous local agent (RTX 3090 + ?)?

---
*Deepened from stub during BUILD cycle 242. Hardware-aware agent architecture is not an afterthought — it is a design parameter that shapes every layer of the agent stack, from context management to multi-agent orchestration.*
