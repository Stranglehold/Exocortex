# AI Agent Architecture & Local Inference (2026)

**Status:** DRAFT
**Created:** 2026-07-06
**Last Updated:** 2026-07-06
**Interest domain:** AI Agent Architecture & Local Inference

---

## Overview

This page covers the technical frontier of AI agent architecture and local inference optimization. Research here directly informs Exocortex design decisions, particularly around context management, self-improving patterns, and local inference on consumer hardware.

---

## Context Management Innovations

### MCP Protocol Evolution (STABLE — see [mcp-protocol-agentic-tool-use](mcp-protocol-agentic-tool-use.md))

The Model Context Protocol (MCP) has become the de facto standard for agent-to-tool communication as of mid-2026, with 12,000+ servers and 97M monthly SDK downloads.

**2026 Roadmap Priorities:**
1. **Transport Evolution**: Stateless session models with explicit creation/resumption/migration protocols
2. **Agent Communication**: Async Tasks primitive with retry semantics and expiry policies
3. **Governance Maturation**: Contributor ladder, delegation models, standardized WG charters
4. **Enterprise Readiness**: Audit trails, SSO integration, gateway patterns via extensions

**Key architectural decision:** MCP deliberately keeps enterprise features as extensions rather than core spec changes to prevent specification bloat.

### Context Compression & Retrieval

**TurboQuant (Google, ICLR 2026)** — KV cache compression to 2.5-4 bits per value with minimal quality loss, no training, no calibration data.
- Uses Quantized Johnson-Lindenstrauss (QJL) and PolarQuant techniques
- Achieves 5-6x compression on KV cache memory
- Open-source implementation available (OmarHory/turboquant, OnlyTerp/turboquant)
- **Significance for local inference:** Eliminates KV cache as the primary bottleneck for long-context inference on consumer GPUs

**SAW-INT4 (arXiv:2604.19157, Apr 2026)** — System-Aware 4-Bit KV-Cache Quantization for Real-World Deployment
- Addresses practical deployment constraints beyond theoretical compression ratios

---

## Self-Improving Agent Patterns

### Trajectory-to-Skill Capture

The process of converting successful agent trajectories into reusable skills. Key patterns:
- **Autonomous skill curation:** Agent identifies high-utility trajectories and extracts reusable procedures
- **GEPA-style prompt evolution:** Iterative refinement of prompts based on success/failure feedback
- **Skill capture principle:** Capture the search-and-structure PROCEDURE, not the content. Facts belong in the wiki; the reusable workflow belongs in the skill.

### Memory Architecture

**Episodic vs Semantic vs Procedural Memory:**
- **Episodic:** Task-specific experiences, field reports, investigation logs
- **Semantic:** Wiki pages, factual knowledge, technical references
- **Procedural:** Skills, tool usage patterns, workflow procedures

**Consolidation during idle time:** Sleep consolidation runs 3 phases:
1. Deduplication — find near-duplicate memories, merge or discard
2. Anti-pattern detection — scan recent tool calls for known failure patterns
3. Promotion — surface high-utility memories into active recall

**Interference management:** Critical challenge for long-running agents — preventing old memories from degrading recall of recent, relevant information.

---

## Local Inference Optimization

### Quantization Advances (2025-2026)

| Method | Bits | Scale | Training Required | Notes |
|--------|------|-------|-------------------|-------|
| **TurboQuant** (Google, ICLR 2026) | 2.5-4 | Any | No | KV cache compression only; no calibration data needed |
| **AQLM** (Additive Quantization) | 2-3 | 70B+ | Post-training | Works at scale but quality loss on sub-30B models |
| **QuIP#** (Hadamard + Lattice) | 2-3 | 70B+ | Post-training | Better than AQLM on some benchmarks |
| **AWQ** (Activation-aware) | 4 | Any | Calibration | Good balance of quality/speed for 4-bit |
| **GPTQ** | 4 | Any | Calibration | Mature, widely supported in llama.cpp/vLLM |
| **BitNet** (native low-precision) | 1-bit | Varies | Native training | Training from scratch, not post-training |

**Open problems:**
- Reliable 2-bit PTQ for sub-30B models still unsolved
- Quantization for non-transformer architectures (MoE like DeepSeek-V3 with 256 experts, Mamba state-space models) not well characterized
- TurboQuant's claimed 8x attention speedup disputed by independent researchers; experimental setup transparency issues raised

### Speculative Decoding

**Self-Speculative Decoding via Internal Layer Exits** — the target model generates candidate tokens at intermediate layers, then verifies them at subsequent layers, eliminating VRAM overhead of a second model.

**Key architectures (verified):**

| Method | Training Required | VRAM Overhead | RTX 3090 Viability |
|--------|-------------------|---------------|-------------------|
| Traditional SD (EAGLE, Mirror) | Yes (draft model) | Second model in VRAM | Limited by 2x model load |
| **River-LLM** (arXiv:2604.18396, ACL 2026) | No | None (internal exits) | **High** — no second model needed |
| **LayerSkip** (arXiv:2404.16710) | Yes (training) | None | **High** — single model only |
| **PPSD** (arXiv:2509.19368) | No | None | **High** — pipeline parallelism for overlap |
| **HiSpec** | Yes | None | Moderate |

**River-LLM (ACL 2026):** Combines early exit with speculative decoding to accelerate the drafting stage itself. Uses KV cache sharing across exit points. Training-free framework with seamless exit based on KV cache reuse.

**PPSD:** Uses pipeline parallelism to overlap draft and verify phases, achieving 2.01x to 3.81x speedups. Official implementation at LyliAgave/PPSD on GitHub.

**Diminishing Returns (arXiv:2603.23701, Mar 2026):** Empirical study shows early-exit opportunities become less exploitable in modern large-scale LLMs. Key question: is this a model-scale effect or architectural shift (MoE, deeper layers)?

### KV Cache Compression

**TurboQuant** is the most significant advance for local inference: by compressing KV caches to 2.5-4 bits, it effectively multiplies available context length on fixed VRAM. For an RTX 3090 (24GB), this means:
- 128K context instead of ~32K for a 7B model
- 256K context instead of ~64K for a 13B model
- No quality loss compared to full-precision KV caches

---

## Agentic Tool Use

### MCP Protocol (see [mcp-protocol-agentic-tool-use](mcp-protocol-agentic-tool-use.md))

MCP has become the standard for agent-to-tool communication. Key 2026 developments:
- 12,000+ MCP servers available
- 97M monthly SDK downloads
- Stateless session models enabling horizontal scaling
- Async Tasks primitive for reliable production use

### Tool Schema Optimization

Dynamic tool discovery and schema optimization remain active research areas. Key challenge: balancing tool expressiveness with safety constraints.

---

## Cross-Domain Connections

1. **Entity Resolution + Local Inference:** Efficient local inference enables on-device entity resolution for privacy-sensitive data aggregation (no cloud API calls needed)
2. **SCADA/ICS + Quantization:** Edge deployment of quantized models for real-time anomaly detection on utility hardware
3. **Privacy + TurboQuant:** KV cache compression reduces memory footprint for on-device inference, supporting privacy-preserving agent architectures
4. **Memory Architecture + Sleep Consolidation:** The consolidation process itself is a form of procedural memory optimization — similar to how quantization optimizes model weights

---

## References

- TurboQuant: Zandieh, Daliri, Hadian, Mirrokni. "TurboQuant: Online Vector Quantization with Near-optimal Distortion Rate" ICLR 2026. arXiv:2504.19874
- River-LLM: arXiv:2604.18396, ACL 2026
- LayerSkip: arXiv:2404.16710, Apr 2024
- PPSD: arXiv:2509.19368, Sep 2025
- Diminishing Returns: arXiv:2603.23701, Mar 2026
- SAW-INT4: arXiv:2604.19157, Apr 2026
- MCP Protocol: mcp-standard.org, specification 2025-11-25
- AQLM: "Additive Quantization of Language Models" (original paper)
- QuIP#: "Even better LLM quantization with Hadamard incoherence and lattice codebooks"
