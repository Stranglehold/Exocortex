# Neuromorphic Computing

**Status:** STABLE
**Created:** 2026-05-19
**Last Updated:** 2026-05-19
**Cross-links:** [fpga-inference-acceleration](./fpga-inference-acceleration.md), [edge-ai-substation-deployment](./edge-ai-substation-deployment.md), [ai-inference-compiler-stack](./ai-inference-compiler-stack.md), [grid-edge-ai](./grid-edge-ai.md)

## Overview

Neuromorphic computing replaces the von Neumann architecture with brain-inspired systems using spiking neural networks (SNNs) and event-driven processing. Unlike traditional accelerators that shuttle data between CPU and memory, neuromorphic chips co-locate processing and memory at each neuron core, eliminating the von Neumann bottleneck.

## Hardware Platforms

### Intel Loihi 2
- Second-generation neuromorphic processor, ~10x faster than Loihi 1 (Intel Research)
- Programmable neuron and synapse microarchitectures with integer arithmetic
- On-chip learning: neurons adapt weights without external intervention
- Lava open-source software framework for SNN development
- Benchmarks: up to 30x energy efficiency vs GPU-based inference for SNN sensor fusion (AxiomLogica 2025)
- CLP-SNN: online continual learning on-chip, matches replay-based accuracy rehearsal-free on OpenLORIS (arXiv 2511.01553)
- SNN partitioning benchmarks show measurable impact on time, power, memory (ACM DL 2025)

### Intel Hala Point
- Large-scale neuromorphic system deploying 1.15 billion neurons (2026)
- Orders of magnitude better energy efficiency than conventional AI systems
- Transition from research prototype to production-class neuromorphic infrastructure

### IBM TrueNorth / NorthPole
- Pioneering neuromorphic architecture (2014 TrueNorth, NorthPole successor)
- 1M neurons, 256M synapses on-chip at 70mW for TrueNorth
- IBM research continues with NorthPole for next-gen scaling

### SpiNNaker 2/3 (University of Manchester)
- Real-time neural simulation at biological timescales
- Research platform for neuroscience-neuromorphic interface

### Nature Multi-Core Architecture (2026)
- Multi-core neuromorphic architecture enabling energy-efficient SNN training via backpropagation
- Addresses the training bottleneck limiting neuromorphic adoption

## Software & Frameworks

### Lava (Intel)
- Open-source framework for neuromorphic development
- Supports SNNs, rate-based, reservoir computing
- Multi-hardware abstraction layer
- Production-ready for Loihi 2

### Neurobench (Nature Communications 2025)
- Standardized benchmarking framework for neuromorphic simulators
- Addresses reproducibility crisis in neuromorphic benchmarking

### EdgeSNN Survey (arXiv 2507.14069)
- First comprehensive survey on Edge Intelligence with Spiking Neural Networks
- Taxonomy: neuron models, learning algorithms, hardware platforms
- Three pillars: on-device inference, resource-aware training, security/privacy
- Dual-track benchmarking (conventional + neuromorphic hardware)
- Covers Loihi 2 and BrainScaleS-2 deployment

## Edge Deployment Characteristics

### Power Envelope
- Sub-mW per neuron core (event-driven: neurons only activate on spikes)
- 30x energy efficiency vs GPU for async sensor fusion
- Zero static power during idle (no spikes = no compute)

### Latency
- Sub-ms event-to-spike latency
- Asynchronous processing, no clock synchronization overhead
- Real-time capability for robotics, industrial sensing, BCI

### Application Fit
- Event-based vision sensors (DVS cameras) — native spike compatibility
- Autonomous systems requiring ultra-low power continuous sensing
- Industrial IoT where battery replacement is impractical
- Edge inference where data privacy prevents cloud offload

## Research Gaps & Open Challenges

1. **Training bottleneck**: On-chip learning (STDP, surrogate gradients) lags ANN quality. Nature 2026 multi-core and CLP-SNN are early signals.
2. **Toolchain maturity**: Lava lacks PyTorch/TensorFlow ecosystem depth. ANN-to-SNN conversion adds complexity.
3. **Real-hardware validation**: Most benchmarks run on simulators; Loihi 2 validation is sparse.
4. **No MLIR/TVM equivalent**: Neuromorphic compilation toolchain gap.
5. **Production deployments**: Few documented industrial cases despite 15+ years research.

## Cross-Domain Connections

- **FPGA inference**: Both target edge sub-ms latency, 10-50W envelopes. Neuromorphic lower power, less flexibility.
- **Edge AI substation**: Event-driven nature suits substation monitoring where anomalies are sparse events.
- **Inference compiler stack**: No neuromorphic TVM/IREE equivalent — MLIR integration gap.
- **Post-quantum ML**: Neuromorphic analog-inspired; PQC implications unexplored.

## Primary Sources (8 verified)

1. Intel Research — Loihi 2: https://www.intel.com/content/www/us/en/research/neuromorphic-computing-loihi-2
2. arXiv 2507.14069 — Edge Intelligence with SNNs (Deng & Yu, 2025)
3. arXiv 2511.01553 — CLP-SNN Online Continual Learning on Loihi 2
4. Nature Communications 2025 — Neurobench benchmarking framework
5. Nature Communications 2026 — Multi-core neuromorphic training architecture
6. ACM DL 2025 — SNN partitioning benchmarks on Loihi 2
7. AxiomLogica 2025 — 30x energy efficiency SNN sensor fusion
8. IJFMR 2026 — Practical SNN deployment pipeline
