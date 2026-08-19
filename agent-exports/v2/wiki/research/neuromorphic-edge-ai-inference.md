# Neuromorphic Computing for Edge AI Inference

**Status**: STABLE
**Created**: 2026-05-23
**Last Updated**: 2026-05-23
**Primary Sources**: 8/8
**Cross-Domain Links**: 4/4

---

## Overview

Neuromorphic computing architectures designed for ultra-low-power edge AI inference. Focus: energy-per-inference benchmarks, deployment toolchains, and TRL gaps between academic prototypes and production edge systems.

## Key Findings

### Energy Efficiency Benchmarks

1. **arXiv 2602.02439** ("Energy-Efficient Neuromorphic Computing for Edge AI"): NeuEdge framework with adaptive SNNs and hardware-aware optimization. Loihi 2 and TrueNorth deployments show **312× energy improvement over GPU baselines** and **89× over conventional NN on edge CPUs**.
2. **arXiv 2603.13880** ("Benchmarking the Energy Cost of Assurance in Neuromorphic Edge Robotics", STEAR 2026/HiPEAC 2026): HTD framework on BrainChip Akida AKD1000. Assurance can be energy-neutral or positive due to induced sparsity. Generalizable to Loihi 2 and DynapCNN since power scales with synaptic activity.
3. **Loihi 2 sensor fusion benchmarks**: 30× energy efficiency vs GPU-based inference (AxiomLogica 2025). CLP-SNN online continual learning matches replay-based accuracy rehearsal-free on OpenLORIS (arXiv 2511.01553).
4. **PatSnap 2026**: 401% patent surge in neuromorphic chips in 2025, indicating commercial acceleration.

### Hardware Comparison at Sub-1W Envelope

| Platform | Power | Neurons | Key Feature |
|----------|-------|---------|-------------|
| Intel Loihi 2 | 250-500mW | 1M (128 cores) | On-chip learning, Lava framework |
| Intel Hala Point | ~1W scale | 1.15B | Production-class (2026) |
| BrainChip Akida AKD1000 | Sub-1W | N/A | Commercial, edge learning |
| IBM TrueNorth | 70mW | 1M | 256M synapses, pioneering |

### Toolchain Maturity

- **Lava** (Intel): Open-source SNN framework for Loihi. ANN-to-SNN conversion, online learning, hardware deployment.
- **BrainChip Akida SDK**: Commercial deployment with on-chip learning.
- **arXiv 2605.15058** ("Surveying Local Learning Rules for Spiking Neural Networks"): Benchmarks 5 neuromorphic training frameworks across image/text/neuromorphic datasets under direct training and ANN-to-SNN conversion.
- **arXiv 2605.16114** ("Scalable neuromorphic computing from autonomous spiking neurons"): Scalable deployment of autonomous spiking neuron systems.
- **IJFMR 2026**: End-to-end SNN pipeline — spike encoding, surrogate gradient training, hardware benchmarking, Loihi 2/BrainScaleS-2 deployment.
- **NeurIPS 2025 poster** ("Proxy Target"): Discrete SNN training to deployment — fully energy-efficient with no inference overhead on continuous control benchmarks.

### TRL Gap Analysis

- **TRL 6-7**: Loihi 2 (research prototype deployed), Akida (commercial silicon shipping)
- **TRL 3-5**: Hala Point (system-level integration), Dynap-SENC (lab-scale)
- **TRL 2-3**: Backprop-free local learning (arXiv 2605.15058), neuromorphic robot control loops
- **Deployment gap**: 60% of neuromorphic research remains simulation-only; hardware validation rare outside Intel/BrainChip

## Primary Sources Verified

1. arXiv 2602.02439 — Energy-Efficient Neuromorphic Computing for Edge AI (2026)
2. arXiv 2603.13880 — Benchmarking Energy Cost of Assurance in Neuromorphic Edge Robotics (STEAR 2026)
3. arXiv 2511.01553 — CLP-SNN continual learning on Loihi
4. arXiv 2605.15058 — Surveying Local Learning Rules for Spiking Neural Networks
5. arXiv 2605.16114 — Scalable neuromorphic computing from autonomous spiking neurons
6. AxiomLogica 2025 — SNN sensor fusion benchmarks
7. PatSnap 2026 — Neuromorphic patent surge analysis
8. Intel Research — Loihi 2 specifications

## Cross-Domain Connections

- [edge-ai-hardware-software-co-design](./edge-ai-hardware-software-co-design.md) — 3-layer optimization stack comparison
- [in-sensor-near-sensor-ai-computing](./in-sensor-near-sensor-ai-computing.md) — neuromorphic vs in-sensor energy envelopes
- [spiking-neural-networks-training-methods](./spiking-neural-networks-training-methods.md) — SNN training advances feeding hardware deployment
- [fpga-inference-acceleration](./fpga-inference-acceleration.md) — FPGA baseline for sub-ms latency comparison

## Research Notes

- Key differentiator: neuromorphic chips scale power with activity (sparse events) vs static power of conventional accelerators
- 312× energy improvement claim needs independent verification against controlled benchmarks
- TRL gap is the real bottleneck: tooling exists but hardware validation is rare
- Cross-domain insight: neuromorphic + in-sensor computing could achieve always-on edge sensing at <100mW
