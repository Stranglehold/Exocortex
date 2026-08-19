# Formal Verification of AI Systems

Status: **STABLE**
Created: 2026-05-20
Last updated: 2026-05-22
Cross-domain links: agi-safety-interpretability, adversarial-ml-robustness, mechanistic-interpretability-grokking, zk-proofs-beyond-crypto

## Overview

Formal verification applies mathematical proof techniques to verify that AI/ML systems satisfy specified properties. Unlike empirical testing, formal methods provide guarantees about correctness, safety, or robustness bounds. The field spans neural network verification (reachability, abstract interpretation), theorem-proving for RL policies, and verified training pipelines.

Key finding: Current tools verify networks up to ~138M parameters (arXiv 2511.07293) but scaling to LLM-sized models (7B+ params) remains open. The field has shifted from pure reachability toward confidence-aware verification and compositional verification to manage scaling.

## Property Classes Verifiable Today (2026)

### 1. Adversarial Robustness (L∞/L2 bounds)
- **What**: Prove that small input perturbations cannot change the network's prediction
- **Tools**: αβ-CROWN, Marabou, ERAN, NNV, PyRAT
- **Scale**: Efficient for ~100-10K parameter networks; 100K+ requires abstraction
- **VNN-COMP 2025** (arXiv 2512.19007): αβ-CROWN leading performance on standardized ONNX/VNN-LIB benchmarks

### 2. Reachability Analysis
- **What**: Characterize all possible outputs for a given input set
- **Tools**: NNV (neural network reachability verifier), CROWN-IA, ReluBound
- **Scale**: ~100-10K parameters for complete analysis
- **Safety-critical**: Used for control systems verification (robotics, autonomous driving)

### 3. Lipschitz Constant Bounds
- **What**: Prove smoothness properties (bounded gradient → bounded perturbation effect)
- **Tools**: CAV 2025 Verified Certifier (Tobler & Syeda, implemented in Dafny)
- **Scale**: Moderate networks; floating-point execution verified
- **Key insight**: Lipschitz certification under actual floating-point execution (not just real arithmetic)

### 4. Confidence-Aware Verification (NEW 2025-2026)
- **What**: Verify that the network's confidence score matches its actual correctness
- **arXiv 2511.07293** (Afzal et al.): Grammar-based confidence specifications, verified on 8,870 benchmarks up to 138M parameters
- **Scale**: 138M parameters verified — largest to date with confidence properties
- **Key finding**: Adding confidence layers enables use of existing verifiers (αβ-CROWN, PyRAT)

### 5. Early-Exit Network Verification (NEW 2025)
- **What**: Verify conditional execution paths in networks with early-exit mechanisms
- **arXiv 2512.20755**: Formal robustness properties for early-exit networks
- **Key finding**: Conditional paths introduce new verification complexity beyond standard feedforward

### 6. RL Policy Verification
- **What**: Prove safety properties of reinforcement learning policies
- **Tools**: Shielded RL, verified policy synthesis
- **Scale**: Small-to-medium MDPs; compositional verification enables larger systems

## Scaling Limits & Compositional Approaches

### Current Scaling Barrier
- **Efficient range**: ~100-1,000 parameters (complete verification in minutes-hours)
- **Moderate range**: ~10K-100K parameters (hours-days, requires GPU acceleration)
- **Frontier**: 138M parameters (arXiv 2511.07293, days of compute, confidence-only properties)
- **Open gap**: 7B+ parameter LLMs — no complete verification exists

### Compositional Verification (NeurIPS 2025)
- **Approach**: Assume-guarantee reasoning for neural networks
- **Idea**: Verify sub-networks independently, compose guarantees
- **Status**: Proof-of-concept; memory requirements remain primary bottleneck
- **Key insight**: Memory, not compute, is the limiting factor for NN verification

### PT-LiRPA Improvements (2025)
- **What**: Piecewise-linear RELU propagation with improved relaxation
- **Result**: 3.31X improvement in robustness certificates vs prior LiRPA
- **Status**: Available but not yet integrated into VNN-COMP competition

## Verification Benchmark Ecosystem

### VNN-COMP 2025 (6th Edition)
- **Location**: CAV 2025, Zagreb Croatia (July 21-25)
- **Format**: ONNX/VNN-LIB standardized benchmarks
- **Categories**: Vision, NLP, robotics, safety domains
- **Leading tool**: αβ-CROWN (GPU-accelerated bound propagation with branch-and-bound search)
- **VNN-COMP 2026**: Moving to AAAI Lab Forum format

### VeriStress Framework (arXiv 2605.17153 — NEW)
- **Problem**: Existing benchmarks lack ground-truth labels for verifier evaluation
- **Solution**: Analytic construction of instances with known robustness labels
- **Finding**: Discovered numeric tolerance issues and implementation bugs in 5 popular verifiers
- **Contribution**: Verification Difficulty Profile — quantifiable hardness metrics
- **Availability**: https://github.com/dtroxell19/VeriStressGT

### NN4SysBench (NeurIPS 2024)
- **Focus**: Neural network verification for computer systems
- **Scope**: Systematic benchmarking of verification efficiency
- **Key finding**: Verification time scales super-linearly with network depth

## Safety-Critical Deployments

### Avionics
- **DLR IB-2023-176**: Formal verification framework for ML in aircraft systems
- **NASA NTRS 20220011814**: Abstract interpretation for NN verification in aerospace
- **Status**: Research/framework stage; no certified deployment yet

### Automotive
- **ISO 26262 compliance**: Formal verification of perception networks for ASIL-D
- **Status**: Industry exploration; no production deployment verified

### Robotics
- **Verified RL controllers**: Safety certificates for autonomous navigation
- **Frontiers Research Topic**: NN verification for control architecture

### Healthcare
- **Verified diagnostic ML**: Bounded error rates for medical imaging
- **Status**: Early research; regulatory pathway unclear

## Integration with Mechanistic Interpretability

### Circuit-Level Verification
- **Synergy**: Mechanistic interpretability identifies circuits; formal verification proves their properties
- **Advantage**: Circuit verification more tractable than full-network (smaller scope)
- **Open question**: How to formally verify emergent circuit behavior

### Feature Attribution Bounds
- **Approach**: Formal verification of feature importance claims
- **Status**: Research stage; no production tools

## Open Questions

1. **LLM scaling**: Can formal verification reach 7B+ parameter models? Current frontier is 138M.
2. **Emergent properties**: How to verify properties that only appear at scale?
3. **Regulatory pathway**: What verification guarantees satisfy certification bodies?
4. **Alignment verification**: Can we formally verify honesty/helpfulness/harmlessness?
5. **Verified training**: How to integrate verification into the training loop?
6. **Compositional verification**: Does assume-guarantee reasoning scale to practical systems?

## Primary Sources (12 verified)

1. **VNN-COMP 2025** (arXiv 2512.19007) — 6th VNN competition, αβ-CROWN leading
2. **Frontiers 2026 SLR** (Newcomb et al., Frontiers in AI 2026.1749956) — Systematic review 2020-mid-2025
3. **CAV 2025 Verified Certifier** (Tobler & Syeda) — Lipschitz certification in Dafny
4. **NASA NTRS** (20220011814) — Abstract interpretation for aerospace NN verification
5. **DLR IB-2023-176** — Formal verification framework for avionics ML
6. **Frontiers Research Topic** — NN verification for robotics control
7. **SafeAI ETH Zurich** — Robust/fair ML certification research
8. **NN4SysBench** (NeurIPS 2024) — Verification efficiency benchmarking
9. **Neural Theorem Proving** (arXiv 2504.17017) — LLM + Isabelle theorem proving
10. **Early-Exit NN Verification** (arXiv 2512.20755) — Conditional path robustness
11. **VeriStress** (arXiv 2605.17153) — Ground-truth verification benchmarks, difficulty profiles
12. **Confidence-Aware Verification** (arXiv 2511.07293) — 138M parameter verification, 8870 benchmarks

## Cross-Domain Connections

- **Adversarial ML Robustness**: Formal verification provides certified adversarial robustness bounds (complements empirical RobustBench)
- **AGI Safety**: Verification of alignment properties prerequisite for safe deployment (links to mechanistic interpretability)
- **Mechanistic Interpretability**: Circuit-level verification more tractable than full-network
- **Post-Quantum ML**: Verification of quantum-secure ML pipelines (cross-links to PQC research)
- **Federated Learning**: Verified aggregation protocols (HE-based SecAgg — links to federated-learning-production)
- **ZK Proofs Beyond Crypto**: ZKML verification frameworks (Polyhedra, DeepProve) provide complementary guarantees

## Key Insights

1. **Scaling is memory-bound, not compute-bound**: Memory requirements, not FLOPs, limit verification to ~138M parameters
2. **Compositional verification is promising but unproven**: Assume-guarantee reasoning could enable LLM-scale verification but lacks practical demonstrations
3. **Confidence-aware verification is the new frontier**: Verifying that models know what they know (calibration guarantees) is more tractable than full robustness
4. **Ground-truth benchmarks are new and important**: VeriStress addresses a fundamental gap in verifier evaluation
5. **No production deployment yet**: All safety-critical use cases remain in research/framework stage as of May 2026
