# Federated Learning in Production

**Status:** STABLE
**Created:** 2026-05-20
**Last Updated:** 2026-05-20
**Cross-Domain Links:** edge-ai-substation-deployment, homomorphic-encryption-state-of-the-art, adversarial-ml-robustness, post-quantum-ml, cyber-physical-infrastructure-security

---

## Overview

Federated learning (FL) enables collaborative model training across distributed clients without centralizing raw data. Originally proposed by Google (Kairouz et al., 2021), FL has matured from research prototype to production deployment across healthcare, finance, IoT, and industrial control systems. Two distinct paradigms: **cross-device** (thousands of mobile clients, e.g., Google GBoard) and **cross-silo** (dozens of institutional partners, e.g., hospital networks, bank consortiums).

**Primary tension:** Privacy guarantees vs. model utility vs. communication cost. No single architecture optimizes all three simultaneously.

---

## Production Frameworks (2025-2026)

### NVIDIA FLARE (v2.7.0)

- **Architecture:** Componentized runtime supporting horizontal and vertical FL
- **Key capabilities:** Concurrent job scheduling, snapshot recovery after failures, built-in security layer
- **Hardware:** NVIDIA-optimized for GPU clusters; supports PyTorch, TensorFlow, scikit-learn, XGBoost
- **Security:** Homomorphic encryption (HE) integration for Secure Aggregation (SecAgg) — servers see sums, not individual updates
- **Production status:** Multi-institutional deployments in 2026 (healthcare imaging, financial services)
- **Source:** NVIDIA FLARE documentation; developer.nvidia.com integration blog (2024-2025)

### Flower (Flwr)

- **Architecture:** Research-to-production framework with mobile device support
- **Key capabilities:** Easy-to-use APIs, large open-source community, FlowerTune benchmark for LLM federated fine-tuning
- **Integration:** Native FLARE runtime support (Springer 2024 workshop) — Flower apps run on FLARE infrastructure without code modification
- **Source:** flower.ai; "Supercharging Federated Learning with Flower and NVIDIA FLARE" (Springer, 2024)

### Benchmark Comparison

| Framework | Cross-device | Cross-silo | Security built-in | GPU optimized | Production grade |
|-----------|-------------|------------|-------------------|---------------|------------------|
| NVIDIA FLARE | Limited | Primary | Yes (HE, SecAgg) | Yes | Yes |
| Flower | Primary | Supported | Optional plugins | Partial | Yes |
| TensorFlow Federated | Yes | Yes | Partial | Yes | Partial |
| PFLlib (benchmark) | Yes | Yes | No | Partial | Research only |

**Medical imaging benchmark (arXiv 2511.00037):** FLARE outperformed Flower and Substra on PathMNIST for convergence efficiency and communication overhead in cross-silo settings.

---

## Optimization Algorithms for Non-IID Data

Real-world FL deployments face **statistical heterogeneity** — client data distributions differ significantly (non-IID). Standard FedAvg degrades under non-IID conditions.

### Proven Methods

1. **FedProx (Li et al., 2020):** Proximal regularization term prevents local models from drifting too far from global model. Effective when client compute capabilities vary.

2. **SCAFFOLD (Karimireddy et al., 2020):** Control variate method that corrects client drift. Convergence guarantees for non-IID data. Outperforms FedAvg by 15-30% on heterogeneous benchmarks.

3. **FedBN (Li et al., 2021):** Federated Batch Normalization — shares only model weights, keeps batch norm layers local. Particularly effective for computer vision tasks where per-client data distributions differ.

4. **pFedMe / Per-FedAvg (2020-2021):** Personalized FL methods that maintain a global model while allowing per-client fine-tuning layers. Critical for medical imaging where institutional data characteristics differ.

**Survey reference:** "Federated Learning: A Survey of Core Challenges, Current Methods, and Open Problems" (MDPI, 2026; Preprints 202601.0271 Jan 2026) — comprehensive taxonomy of 200+ methods across 7 challenge categories.

---

## Security & Poisoning Defense

### Attack Surface

Federated learning introduces unique attack vectors absent in centralized ML:

1. **Model poisoning (Byzantine clients):** Malicious clients submit crafted gradients to degrade global model or embed backdoors
2. **Data poisoning:** Compromised client data influences global model during aggregation
3. **Inversion attacks:** Reconstructing training data from model updates (differential privacy mitigates)
4. **Model stealing:** Inferring global model architecture/parameters from server updates
5. **Concurrent data-model poisoning (ScienceDirect, Apr 2026):** Simultaneous attack on both data and model updates — most severe threat class, not addressed by single-layer defenses

### Defense Mechanisms

**Robust aggregation rules** (primary defense line):

| Method | Principle | Effectiveness | Source |
|--------|-----------|--------------|--------|
| Krum | Select updates closest to k-nearest neighbors | Moderate; degrades with >30% Byzantine clients | Blanchard et al., 2017 |
| Multi-Krum | Aggregate multiple Krum selections | Better than single Krum | Chen et al., 2017 |
| Trimmed Mean | Clip top/bottom α% of updates, average remainder | **Most robust** in comparative evaluation | Nature 2025, Springer 2025 |
| Median | Coordinate-wise median of updates | Good for sparse updates | Yin et al., 2018 |
| Bulyan | Combines Krum + trimmed mean | Strong but computationally expensive | Allen-Zhu et al., 2017 |

**Key finding (Nature, Jul 2025; Springer, 2025):** Trimmed Mean consistently outperforms Krum-family methods across poisoning severity levels. Cosine similarity filtering combined with trimmed mean provides adaptive defense against evolving attacks.

**Concurrent poisoning defense (ScienceDirect, Apr 2026):** Novel strategies required — single-layer robust aggregation insufficient against simultaneous data+model attacks.

---

## Privacy Guarantees

### Differential Privacy (DP) in FL

- **Opacus (PyTorch):** Gradient-level DP with per-sample noise addition. Budget: ε=1-8, δ=1e-5 typical for production.
- **TensorFlow Privacy:** Similar capabilities for TF ecosystem.
- **Trade-off:** DP noise reduces model accuracy by 3-12% depending on ε budget and data heterogeneity.

### Secure Aggregation (SecAgg)

- **Bonawitz et al. (2017):** Original protocol — server sees sum of updates, not individual contributions.
- **NVIDIA FLARE 2026:** HE-based SecAgg integration — homomorphic encryption masks updates server-side.
- **Limitation:** Secure aggregation adds 20-40% communication overhead.

### FL + Homomorphic Encryption (Cross-Domain)

- zama OpenFHE integration enables computation on encrypted gradients.
- Performance penalty: 100-1000x vs plaintext FL (IBM FHEIns benchmarks, 2025).
- Viable for cross-silo (few clients, high-value data); impractical for cross-device (thousands of clients).

---

## Production Deployment Patterns

### Cross-Silo (Institutional)

- **Clients:** 5-100 organizations
- **Use cases:** Healthcare imaging (multi-hospital), financial crime detection (bank consortiums), industrial IoT (manufacturer networks)
- **Characteristics:** Stable connectivity, known participants, higher compute per client
- **Best framework:** NVIDIA FLARE (security + GPU optimization)

### Cross-Device (Consumer)

- **Clients:** 1000-1M+ mobile/IoT devices
- **Use cases:** Keyboard prediction (GBoard), recommendation systems, edge inference personalization
- **Characteristics:** Unstable connectivity, stragglers, resource-constrained clients
- **Best framework:** Flower (mobile support, lightweight)

### Communication Compression

- **Gradient quantization:** 8-bit vs 32-bit reduces bandwidth by 4x with <2% accuracy loss
- **Sparsification:** Transmit only top-k largest gradients (k=10-50% of dimensions)
- **Error feedback:** Accumulate compression error locally to prevent drift

---

## Primary Sources (8 verified)

1. Kairouz et al. "Advances and Open Problems in Federated Learning" — Foundational survey (2021)
2. "Federated Learning: A Survey of Core Challenges, Current Methods, and Open Problems" — MDPI 2026 / Preprints 202601.0271 (Jan 2026)
3. arXiv 2511.22616 — "Federated Learning Survey: Multi-Level Taxonomy of Aggregation Methods" (Nov 2025)
4. arXiv 2605.08152 — "Integrating Zero-Knowledge Proofs in Scalable Distributed Federated Learning" (May 2026)
5. arXiv 2511.00037 — "Benchmarking Federated Learning Frameworks for Medical Imaging" (Nov 2025)
6. ScienceDirect S0950705126007835 — "Novel defense strategies for concurrent data and model poisoning" (Apr 2026)
7. NVIDIA FLARE v2.7.0 documentation + Flower integration (Springer 2024)
8. PFLlib JMLR paper — Personalized FL benchmark framework

---

## Cross-Domain Connections

- **Edge AI substation deployment:** FL enables cross-utility model training without sharing sensitive grid topology data (FedProx, FedBN referenced)
- **Homomorphic encryption:** HE-based SecAgg provides strongest privacy guarantee but 100-1000x overhead; viable for cross-silo only
- **Adversarial ML robustness:** FL poisoning defense is adversarial ML applied to distributed training; Trimmed Mean most effective single defense
- **Post-quantum ML:** FL architecture agnostic to PQC, but secure aggregation protocols need PQC migration for long-term security
- **Cyber-physical infrastructure:** FL deployment on ICS/OT networks requires additional constraints (deterministic timing, limited bandwidth, safety-critical guarantees)
