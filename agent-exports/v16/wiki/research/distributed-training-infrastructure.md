# Distributed Training Infrastructure & Systems

## Status: STABLE

## Scope
Large-scale AI model training infrastructure: distributed training frameworks, parallelism strategies, fault tolerance, cluster orchestration, and cross-datacenter training.

## Primary Sources (9 verified)

### Surveys & Frameworks
1. **Duan et al. (2024)** — "Efficient Training of Large Language Models on Distributed Systems" arXiv:2407.20018 — Comprehensive survey of LLM training infrastructure: AI accelerators, networking, storage, scheduling, and computation/communication/memory optimizations.
2. **Distributed MLLM Survey (2025)** — arXiv:2503.16585 — Reviews distributed training, inference, fine-tuning, and deployment across MLLM pipeline; categorizes by six decentralization focus areas.
3. **TorchTitan (Meta, 2024-2025)** — arXiv:2410.06511 — Open-source PyTorch-native distributed training with SPMD (TP, activation checkpointing, torch.compile, FSDP, mixed precision), checkpointing, and debugging tools.
4. **Mist (EuroSys 2025)** — Communication-optimized distributed training outperforming Megatron-LM and DeepSpeed manual approaches.

### Fault Tolerance & Checkpointing
5. **TierCheck (2026)** — arXiv:2605.17821 — Tiered checkpointing for fault tolerance; reveals failure heterogeneity at scale; periodic checkpointing remains standard.
6. **Fault-Tolerant Hybrid-Parallel (2024)** — arXiv:2310.12670 — Distributed in-memory checkpointing with near-zero overhead; addresses partial failure recovery.

### Datacenter Infrastructure
7. **Astral (ACM SIGCOMM 2025)** — Datacenter infrastructure supporting up to 500K GPUs; same-rail interconnection network, tier-2 scaling, production operational lessons.
8. **Datacenter Design for Next-Gen LLMs (2025)** — arXiv:2506.15006 — Anticipatory network development for 2026/2027 LLM training architectures.

### Cross-Datacenter Training
9. **Decoupled DiLoCo (Google DeepMind, 2026)** — arXiv:2604.21428 — Asynchronous distributed pre-training across distant data centers; 88% goodput under high failure rates; 2-5 Gbps WAN bandwidth; 20x faster than synchronous; 236x bandwidth reduction.

## Key Findings

### Parallelism Strategies
- **Data Parallelism (DP)** — SPMD; each device holds full model replica, gradients synchronized via all-reduce.
- **Tensor Parallelism (TP)** — Splits individual layer computation across devices (Megatron-LM).
- **Pipeline Parallelism (PP)** — Splits layers across devices sequentially; requires careful scheduling.
- **ZeRO** — DeepSpeed memory optimization: shards optimizer states, gradients, parameters (ZeRO-1/2/3). ZeRO-3 reduces memory ~3x vs DP.
- **FSDP** — PyTorch-native ZeRO-3; integrated into PyTorch 2.0+.

### Fault Tolerance
- Checkpointing overhead is dominant cost. TierCheck (2026) introduces tiered strategies.
- In-memory checkpointing achieves near-zero overhead vs disk-based.
- Partial failure recovery critical at 1000+ GPU scale.

### Cross-Datacenter Training
- Decoupled DiLoCo (2026): asynchronous islands of compute train independently, synchronize periodically.
- 88% goodput even with hardware failures.
- Standard internet bandwidth (2-5 Gbps) sufficient.

### Production Deployments
- **TorchTitan** (Meta): Production-ready PyTorch stack combining TP/PP/FSDP/torch.compile.
- **Astral** (SIGCOMM 2025): 500K GPU datacenter infrastructure.
- **Mist** (EuroSys 2025): Communication-optimized training.

## Cross-Domain Links
- [ai-inference-compiler-stack](ai-inference-compiler-stack.md) — TorchInductor/torch.compile overlap
- [ai-datacenter-power-crisis](ai-datacenter-power-crisis.md) — Training energy at 500K GPU scale
- [semiconductor-supply-chain-geopolitics](semiconductor-supply-chain-geopolitics.md) — GPU availability constraints
- [conditional-compute-mixture-of-experts](conditional-compute-mixture-of-experts.md) — MoE training infrastructure

## Integration Notes
- Distributed training is prerequisite for understanding frontier model economics.
- Fault tolerance patterns transferable to distributed ML systems.
- Decoupled DiLoCo may influence self-improving agent training infrastructure.

---
*Deepened: Cycle 341 (2026-05-22) | 9 verified primary sources, 4 cross-domain links*
