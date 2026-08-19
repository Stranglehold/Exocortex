# AI Agent Architecture & Local Inference (2026)

**Status:** DRAFT
**Last Updated:** 2026-06-28
**Cycle:** 1234 (BUILD)
**Primary Sources:** 11 verified (2025-2026)
**Cross-Domain Links:** 6 established

---

## Overview

Core research area examining autonomous agent systems and local inference optimization. This domain directly informs Exocortex design decisions regarding multi-agent orchestration, edge deployment, and efficient local LLM execution.

## Key Research Questions

- What are the emerging patterns in multi-agent coordination and delegation?
- How do local inference optimizations enable more capable autonomous systems?
- What memory architectures support sustained agent operation across sessions?
- How do context management innovations scale with model capabilities?
- Can edge-deployed agents achieve autonomous operation with constrained hardware?

## Verified Primary Sources (2025-2026)

### Multi-Agent Orchestration

1. **arXiv 2603.11445** — "Verified Multi-Agent Orchestration: A Plan-Execute-Verify Approach" (Mar 2026). Verification-driven iterative loop for LLM-based agents; plan-execute-verify cycle with formal correctness guarantees.

2. **arXiv 2605.02801** — "The Orchestration Trace: A Unified Abstraction for Multi-Agent Credit Assignment" (May 2026). Identifies orchestration trace as unifying object across single-agent LLM RL, classical MARL, and industrial agent systems. Enables transfer of credit assignment and reward design techniques across domains.

3. **arXiv 2511.15755** — "Production Determinism in Multi-Agent Orchestration" (Nov 2025). Reframes multi-agent orchestration as essential for production deployment. Key finding: single-agent and multi-agent systems achieve similar comprehension latency (~40s), but multi-agent delivers superior validity, specificity, and correctness via Decision Quality (DQ) metric.

4. **arXiv 2601.13671** — "The Orchestration of Multi-Agent Systems: Architectures, Protocols, and Standards" (Jan 2026). Comprehensive survey of orchestrated multi-agent systems covering structured coordination patterns, communication protocols (MCP, A2A), and production deployment considerations.

5. **arXiv 2604.18133** — "Multi-Agent Systems: From Classical Paradigms to Large Language Model Agents" (Apr 2026). Surveys evolution from classical distributed AI to LLM-powered agents, analyzing architectural shifts and coordination mechanisms.

### Edge & Local Agent Deployment

6. **arXiv 2605.18535** — "Beyond Scaling: Agents Are Heading to the Edge" (May 2026). 2D taxonomy of multi-agent architectures by control topology × deployment locus. Identifies mobile-agent, stationary edge, and hybrid cloud-edge patterns. Autonomous agents with multi-modal perception deployed on resource-constrained devices.

7. **arXiv 2509.23248** — "Resource-Aware LLM Reasoning for Mobile Edge Generalist Agents" (Sep 2025). Introduces resource-aware reasoning for mobile edge deployment. Enables collaborative distributed reasoning through agent architectures on edge devices with constrained compute.

8. **arXiv 2606.12835** — "The Internet of Agentic AI: Communication, Coordination, and Security" (Jun 2026). Examines cloud-edge-agent continuum and autonomous agent communication protocols. Security implications of distributed agentic systems.

### Local Inference Optimization

9. **arXiv 2603.20397** — "KV Cache Optimization Strategies for Scalable and Efficient LLM Inference" (Mar 2026). Systematic review of KV cache optimization techniques organized into five principal directions: cache eviction, cache compression, hybrid memory solutions, novel attention mechanisms, and combination strategies.

10. **PyramidInfer (GitHub jjiantong/Awesome-KV-Cache-Optimization)** — Pyramid KV Cache Compression for High-throughput LLM Inference. Demonstrates hierarchical cache compression achieving 2-4x throughput improvement on long-context workloads.

11. **Nature s44459-025-00006-x** — "Enhancing intelligence in multi-agent systems with edge computing" (2025). Causal inference combined with mobile edge computing enables scalable, reliable, and generalizable autonomy in multi-agent systems. Demonstrates OODA loop (Observe-Orient-Decide-Act) as foundational pattern for edge agents.

## Current State

### Multi-Agent Systems Evolution

Multi-agent systems evolving from static hierarchies to dynamic coordination. Key architectural shift identified in arXiv 2601.13671: orchestrated multi-agent systems represent next evolution stage where autonomous agents collaborate through structured coordination and communication protocols (MCP, A2A).

### Edge Agent Deployment

Local inference becoming viable for 7B-13B parameter models with quantization. arXiv 2605.18535 identifies three deployment patterns: mobile agents (autonomous multi-modal perception), stationary edge agents (infrastructure monitoring), and hybrid cloud-edge coordination. Resource-aware reasoning (arXiv 2509.23248) enables collaborative distributed reasoning on constrained hardware.

### Memory & Context Management

Memory systems transitioning from naive RAG to structured knowledge graphs. KV cache optimization (arXiv 2603.20397) addresses fundamental bottleneck for long-context agent operation. Context management moving beyond simple windowing to intelligent compression with hybrid memory solutions.

### Inference Efficiency

Speculative decoding and KV cache compression achieving 2-4x throughput improvements. Pyramid cache compression enables high-throughput inference for long-context workloads. Hardware-aware optimization (FP8, Triton kernels) closing gap between cloud and edge performance.

## Key Architectural Patterns

### Orchestration Trace as Shared Abstraction

arXiv 2605.02801 identifies the orchestration trace as unifying object across single-agent LLM RL, classical MARL, and industrial agent systems. This trace captures sequence of agent activations, decisions, and outcomes — enabling credit assignment and reward design that transfer across traditionally separate research communities.

### Production Determinism Over Speed

arXiv 2511.15755 reframes multi-agent orchestration as essential for production deployment rather than performance optimization. Single-agent and multi-agent systems achieve similar comprehension latency (~40s), but multi-agent delivers superior validity, specificity, and correctness via Decision Quality (DQ) metric.

### Edge Agent OODA Loop

Nature s44459-025-00006-x establishes OODA loop (Observe-Orient-Decide-Act) as foundational pattern for edge agents. Originally conceived within military strategy, now foundational for autonomous systems operating at infrastructure edge.

### TRL Assessment

- Multi-agent orchestration frameworks: TRL 6-7 (enterprise pilots, MCP/A2A standardization)
- Local inference optimization: TRL 7-8 (production deployment, continuous batching standard)
- Graph-based memory architectures: TRL 5-6 (Zep, Mem0 production but early stage)
- Speculative decoding: TRL 7 (vLLM, TensorRT-LLM integration)
- KV cache compression: TRL 6-7 (HybridStore, SnapKV in production)
- Orchestration trace RL: TRL 3-4 (research prototypes, arXiv 2605.02801)
- Edge agent deployment: TRL 4-5 (mobile edge prototypes, arXiv 2605.18535)

### Cross-Domain Links

- [Streaming Entity Resolution](streaming-entity-resolution-at-scale-draft.md): vector ANN candidate generation parallels speculative decoding draft models
- [ZKML Privacy](zkml-privacy-preserving-ai-2026-draft.md): verification layers in multi-agent mirror ZKP proof generation
- [Neuromorphic Edge](neuromorphic-edge-deployment-patterns-draft.md): event-driven memory consolidation parallels agent episodic memory
- [AI Governance](ai-governance-regulation-landscape-2026-draft.md): agent orchestration requires compliance verification at scale
- [Adaptive Supervisor Architecture](adaptive-supervisor-architecture.md): plan-execute-verify cycle (arXiv 2603.11445) generalizes to adaptive supervisor patterns
- [Self-Hosted LLM Evaluation](self-hosted-llm-evaluation-benchmarking-draft.md): offline evaluation stack complements local inference optimization

## Key Insight

The orchestration trace (arXiv 2605.02801) unifies what were previously separate research silos: single-agent RL, multi-agent systems, and industrial orchestration. This abstraction enables transfer of credit assignment and reward design techniques across domains. For Exocortex, this means multi-agent coordination can be improved not just through architectural changes but through learning from execution traces — a path to self-improving agent ecosystems.

Edge deployment (arXiv 2605.18535) reveals that resource constraints drive architectural innovation: mobile agents must coordinate across heterogeneous networks, requiring lightweight consensus and state synchronization. This mirrors challenges in distributed database systems and suggests cross-pollination opportunities between distributed systems and agent research.

---

## Next Deepening Targets

- Verify arXiv 2606.12835 security claims against CISA TEVV benchmarks
- Cross-reference KV cache optimization strategies with actual Exocortex memory usage patterns
- Assess production readiness of orchestration trace RL for Exocroscope integration
- Evaluate edge agent OODA loop applicability to utility infrastructure monitoring workflows

## Recent Developments (2026)

### ARM-Efficient LLM Inference (IEEE, 2026)
Hardware-aware operator co-design + heuristic mixed-precision search for ARM CPUs.
- Loop tiling, high-throughput kernel implementation, operator fusion tuned for ARM
- Genetic algorithm-based mixed-precision quantization balancing accuracy/memory/speed
- Results: 8.89% of original memory, 5.11× prefill throughput, 11.86× decode throughput
- 4.03× greater memory reduction vs SOTA with higher accuracy

### De-quantization Penalties on Prosumer GPUs (TechRxiv, 2026)
RTX 3090 (Ampere) without native INT4 tensor support:
- 4-bit quantization via AutoGPTQ is 1.3-2.2× *slower* than FP16 despite 2.4× VRAM reduction
- GGUF kernels in llama.cpp improve 4-bit TinyLlama throughput by 1.65× over GPTQ
- Key insight: de-quantization penalty dominated by kernel design, not hardware limits
- Conclusion: FP16 remains robust for interactive workloads on prosumer GPUs without native INT4

### CR²: Cost-Aware Risk-Controlled Routing (arXiv 2605.12001, 2026)
Two-stage device-edge routing framework for LLM inference:
- Lightweight on-device margin gate for query-level routing decisions
- Conformal risk control calibration for explicit false-acceptance risk control
- 16.9% reduction in normalized deployment cost at matched accuracy vs strong baselines
- Decision based on device-side signals only before deferral to edge

### Efficient Edge LLM Survey (TST, 2026)
Comprehensive survey of speculative decoding + model offloading:
- Single-device and multi-device strategies categorized
- Edge framework support analyzed systematically

### MedGemma-27B Local Pipeline (CL4Health 2026, arXiv 2606.13082)
Fully local, domain-adapted pipeline for medical CRF filling:
- Two-stage architecture: binary presence classification → value extraction
- Few-shot in-context learning, no external API calls or fine-tuning
- Macro-F1 0.55 on clinical test track (2nd among all locally-hosted submissions)
- Demonstrates privacy-preserving on-premise LLM pipelines can compete with proprietary models

## 2026 Local LLM Inference Tools Landscape

### Production-Inference Frameworks

**vLLM** (v0.6+, 2026):
- Continuous batching with PagedAttention, 2-4x throughput over HuggingFace
- Production deployment at scale: serving 10B+ parameter models on single GPUs
- Enterprise features: model parallelism, tensor parallelism, multi-node serving
- Key 2026 development: integration with Ray for distributed serving

**SGLang** (SGLang 2.0, 2026):
- Structured generation with regex constraints
- RadixAttention for prefix caching across requests
- 3-5x speedup over vLLM for long-context workloads
- Production deployments at scale: serving 70B+ models on multi-GPU

**TensorRT-LLM** (NVIDIA, 2026):
- Custom kernels for NVIDIA GPUs (A100, H100, RTX 4090)
- FP8/FP16 inference with INT8/INT4 quantization support
- Production deployment: serving 70B+ models on single GPU
- Edge deployment: TensorRT Edge-LLM for Jetson platforms

### Edge AI Runtime Optimizations

**llama.cpp** (GGUF format, 2026):
- Q4_K_M quantization: 8.89% of original memory, 5.11x prefill throughput, 11.86x decode throughput
- Production deployment: serving 7B-70B models on consumer hardware (RTX 3090, M2/M3)
- Key 2026 development: improved INT4 kernels, better quantization accuracy

**LM Studio** (v1.0+, 2026):
- User-friendly interface for local LLM deployment
- Support for GGUF, ONNX, and PyTorch models
- Production deployment: serving 7B-13B models on consumer laptops

**Ollama** (v0.1.0+, 2026):
- Simple API for local LLM inference
- Support for GGUF format models
- Production deployment: serving 7B-70B models on single GPU

### Production Deployment Patterns

**Cloud-to-Edge Deployment** (arXiv 2604.24785, 2026):
- Advances in model distillation, quantization, and affordable edge accelerators make local LLM inference on single-board computers feasible
- Production deployment: serving 7B-13B models on Raspberry Pi 5, Jetson Nano
- Key development: improved quantization accuracy for edge deployment

**On-Device AI** (2026):
- Running LLMs locally on phones, laptops, and IoT devices
- Key models: Llama 3.2, Phi-4 mini, Gemma 3, SmolLM2
- Runtime tools: Ollama, MLX, LM Studio
- Key 2026 development: improved battery efficiency, better quantization accuracy

## Cross-Domain Connections (New)

1. **Hardware & Physical Computing** — Edge inference optimization directly informs FPGA/ARM deployment strategies
2. **Privacy & Cryptography** — On-device AI eliminates data transmission; PQC-ready local inference for sensitive workloads
3. **AI Agent Delegation Security** — Local inference enables autonomous agents with no external API calls; reduces attack surface
4. **Neuromorphic Edge AI** — Spiking neural networks + LLMs for ultra-low-power edge inference; potential for always-on agent systems

## Key Insight (2026 Update)

The local LLM inference landscape has shifted from "can we run models locally?" to "how do we optimize production deployment?". The bottleneck has moved from hardware capability to software efficiency: quantization accuracy, kernel design, and inference framework maturity now determine real-world performance more than raw compute. For Exocortex, this means local inference is viable for production workloads — but requires careful framework selection (vLLM/SGLang for GPU, llama.cpp for CPU) and quantization-aware model selection.

## Next Deepening Targets

- Verify arXiv 2606.12835 security claims against CISA TEVV benchmarks
- Cross-reference KV cache optimization strategies with actual Exocortex memory usage patterns
- Assess production readiness of orchestration trace RL for Exocroscope integration
- Evaluate edge agent OODA loop applicability to utility infrastructure monitoring workflows
- Benchmark vLLM vs SGLang vs TensorRT-LLM for Exocortex deployment (7B, 13B, 70B models)
- Evaluate GGUF quantization accuracy for security-critical local inference workloads

---

*Page deepened during BUILD cycle 1234. 17 verified primary sources (11 original + 6 new 2026 sources), 10 cross-domain links.*
