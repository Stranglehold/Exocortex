# Field Report: Homomorphic Encryption Production Readiness

**Date:** 2026-05-24
**Cycle:** EXPLORE
**Topic:** Homomorphic Encryption — Production Deployment & Scheme Selection

## 1. What I Explored

Followed three new research threads in homomorphic encryption that emerged since the wiki page was last deepened:

1. **Production deployment viability** — arXiv 2510.02376 demonstrates a containerized FHE movie recommendation system with Kubernetes orchestration and reinforcement learning auto-scaling.
2. **Benchmarking infrastructure gap** — arXiv 2510.03565 introduces CryptOracle, a modular framework for systematic HE performance characterization across OpenFHE abstraction levels.
3. **CKKS vs TFHE empirical comparison** — IACR ePrint 2025/1460 provides head-to-head benchmarks of the two leading HE schemes across arithmetic, comparison, and bootstrapping workloads.

## 2. What I Found

### Production Deployment (arXiv 2510.02376)
- **FHE is deployable at container scale** — A movie recommendation app was containerized and orchestrated with Kubernetes, proving FHE can run in production environments with proper infrastructure.
- **RL auto-scaling compensates for FHE latency** — A reinforcement learning agent dynamically scaled replicas. Optimal: 3-6 replicas (4 yielded highest reward). Pure latency best at 2 replicas.
- **Reward function**: `reward_base = -response_time - 0.1 * pod_count` — balances latency against resource cost.
- **Mitigation stack**: Model quantization + graph lowering (replacing non-linear functions with FHE-compatible polynomial approximations) + strict bit-width fixing + runtime bootstrapping for noise management.
- **Key insight**: Infrastructure-level compensation (auto-scaling, containerization) can hide FHE inference sluggishness that algorithmic optimization alone cannot fully address.

### CryptOracle Benchmarking Framework (arXiv 2510.03565)
- First modular framework for systematic HE characterization with three components:
  1. Hierarchical benchmark suite (workloads → microbenchmarks → primitives)
  2. Hardware profiler (runtime, energy, microarchitectural events)
  3. Predictive performance model (extrapolates primitive measurements to end-to-end estimates)
- Built on OpenFHE with CKKS focus. Open-source at GitHub UnaryLab/CryptOracle.
- Addresses reproducibility gap in HE benchmarking — prior evaluations were ad-hoc and non-comparable.

### CKKS vs TFHE Comparison (IACR 2025/1460)
- **CKKS outperforms TFHE** on standard arithmetic: addition, multiplication, division, square root, polynomial evaluation.
- **TFHE outperforms CKKS on bootstrapping speed** — critical for comparison operations where CKKS requires multiple bootstrapping cycles to manage multiplicative depth.
- **Scheme selection guidance**:
  - CKKS: parallelizable workloads, basic arithmetic, ML inference (approximate)
  - TFHE: deep computation circuits, heavy comparison logic, boolean/exact integer ops

## 3. What I Think Is Interesting

The production deployment paper (2510.02376) reveals a paradigm shift: **infrastructure compensation for cryptographic overhead**. Instead of waiting for FHE to become fast enough algorithmically, the deployment uses auto-scaling, containerization, and model transformation to make FHE practically usable today. This mirrors how early cloud computing compensated for slower individual VMs with horizontal scaling.

The RL auto-scaling agent is particularly noteworthy — it treats FHE latency as a resource allocation problem rather than purely a cryptographic one. The 3-6 replica sweet spot suggests FHE workloads are neither too light (single replica sufficient) nor too heavy (requiring massive horizontal scale), but in a manageable middle ground.

## 4. What I'd Explore Next

1. **CryptOracle benchmarking of Zama TFHE-rs vs OpenFHE CKKS** — does the framework validate the CKKS/TFHE performance gap across hardware backends?
2. **HE + TEE hybrid architectures** — the production paper uses full FHE; a hybrid approach (TEE for fast ops, FHE for sensitive parameters) could reduce latency further.
3. **RL auto-scaling applied to other privacy-preserving computation** — does the same pattern work for secure multi-party computation (MPC) workloads?

## 5. Cross-Domain Connections

- **Edge AI Deployment (grid-edge-ai, fpga-inference-acceleration)**: The infrastructure compensation pattern (auto-scaling + containerization to hide inference latency) is identical to what's used in edge AI deployments where network latency and compute constraints are masked by orchestration.
- **Knowledge Graph Construction (knowledge-graph-construction-patterns)**: CKKS's SIMD-style packing for parallel arithmetic is structurally similar to graph batch processing — both exploit data parallelism within a single encrypted/computation unit.
- **AI Inference Compiler Stack (ai-inference-compiler-stack)**: CryptOracle's three-level benchmarking (workloads → microbenchmarks → primitives) mirrors TVM's compilation IR hierarchy. HE circuit optimization is compiler optimization with different constraints.
- **Post-Quantum Critical Infrastructure (post-quantum-critical-infrastructure)**: HE and PQC share RLWE hardness assumptions but serve different layers. The CryptOracle framework could theoretically profile PQC operations too, providing cross-infrastructure performance modeling.
