# Privacy-Preserving Federated Learning for Critical Infrastructure Monitoring

**Status:** STABLE
**Domain:** Privacy & Cryptography
**Last Updated:** 2026-06-06

## Problem Statement

Critical infrastructure operators (electric utilities, water systems, transportation) collect vast sensor data for anomaly detection but are reluctant to share it due to security, privacy, and regulatory concerns. Federated learning (FL) enables collaborative model training without sharing raw data. When combined with privacy-enhancing technologies (PETs) — homomorphic encryption (HE), differential privacy (DP), secure multi-party computation (SMPC) — FL can enable sector-wide anomaly detection, threat intelligence sharing, and predictive maintenance while preserving operational secrecy.

## Key Research Findings

### DyHFL: Dynamic Homomorphic Encryption Federated Learning (Apr 2026)

Kamali Poorazad, Benzaïd & Taleb (arXiv:2604.06101, April 2026) propose **DyHFL** — a novel HE-based dynamic buffered FL framework for privacy-preserving anomaly detection in IIoT/CPS environments. Key innovations:

1. **Homomorphic Encryption integration**: Paillier-based HE encrypts model parameters during transmission, preventing model inversion attacks while preserving model accuracy (DP alternatives degrade accuracy via noise injection).

2. **Dynamic Agent Selection (sliding window)**: A sliding window mechanism continuously monitors three IIoT-relevant metrics per agent — training time, communication time, and local data size — to compute weighted thresholds (WAM + EWA) that dynamically classify agents as fast/slow for buffer-based aggregation. This:
   - Eliminates straggler effects from traditional SyncFL
   - Avoids communication bottlenecks of AsyncFL
   - Ensures fairness — achieves 56.44% straggler selection rate (vs BFL's 29.62%)

3. **Two-phase architecture**: (1) Preliminary rounds (sliding window) estimate agent performance thresholds; (2) Subsequent rounds select agents below threshold for aggregation, dropping stragglers above threshold.

4. **Communication cost**: reduced via selective agent participation — formula: $(M \times SW \times N) + (M \times (T - SW) \times N_{sel})$

5. **Three industrial datasets validated**: Gas_Pipeline, WUSTL_IIoT, Edge_IIoT across identical, No-Label-Skew, and Dirichlet distributions. DyHFL converges 5-158× faster than baselines depending on dataset.

**Ablation study**: Dynamic agent selection is the dominant performance driver; HE adds privacy with negligible accuracy impact.

### FL for Smart Grid / SCADA

Multiple approaches apply FL to smart grid anomaly detection:

| Approach | Privacy Mechanism | Key Finding | Reference |
|----------|-------------------|-------------|-----------|
| HeteroFL | Heterogeneous FL | Privacy-preserving electricity theft detection in smart grids | ScienceDirect, Jan 2025 |
| Decentralized FL | k-anonymity, local training | IDS for decentralized power zones | arXiv:2407.15879 |
| DP-FLoTinyLLM | Differential Privacy + LoRA | TinyLLM fine-tuning with DP for log anomaly detection | arXiv:2604.19118, Apr 2026 |
| ACM FL+DP | DP + unsupervised FL | Anomaly detection on synthetic smart grid data | ACM 1145/3694860, 2024 |

### SecuFL-IoT (Nature, Jan 2026)

Adaptive privacy-preserving FL framework for IIoT anomaly detection, published in Scientific Reports (Nature). Tailored for critical IIoT infrastructures with low-latency requirements.

### CPS Federated Anomaly Detection Survey (Springer, 2026)

"Balancing the trilemma" — comprehensive survey of FL for cyber-physical system anomaly detection. Frames the problem as a three-way tradeoff between privacy, accuracy, and communication efficiency. The survey catalogs SyncFL, AsyncFL, buffered FL, and hybrid approaches.

## Architecture Patterns

### Three-Layer Hybrid Architecture

Emerging consensus from surveyed systems:

1. **Deterministic safety floor**: Local anomaly detection with hard-coded trip thresholds (SCADA/ICS requirement — cannot depend on probabilistic models for safety-critical decisions)

2. **FL-based anomaly detection layer**: Collaborative model training across substations/plants without raw data sharing, using HE or DP for gradient/model protection

3. **Human-in-the-loop escalation**: FL system flags anomalies; human operators verify and respond

This pattern is structurally isomorphic to the Exocortex architecture (deterministic scaffolding + probabilistic LLM + supervisor loop).

### DyHFL's Two-Phase Selection Pattern

The sliding-window preliminary phase followed by threshold-based selection is a generalizable pattern for any multi-agent system facing heterogeneous participant performance. Directly applicable to Exocortex's call_subordinate agent orchestration — where subordinate agents may have varying response times and output quality.

## Threat Models & Attack Surfaces

| Attack Surface | Description | Mitigation |
|---------------|-------------|------------|
| Model inversion | Adversary reconstructs training data from gradients | HE encryption of model updates |
| Gradient leakage | Interception of model parameters during transmission | Paillier HE + probabilistic encryption |
| Model poisoning | Malicious agent submits corrupted updates | Secure aggregation, Byzantine-resilient FL |
| Honest-but-curious server | Aggregator inspects updates | HE ensures server cannot decrypt individual updates |
| Communication bottlenecks | AsyncFL frequent individual updates | Buffered aggregation with dynamic selection |

## Practical Limitations

1. **Resource constraints in OT**: Paillier HE introduces ciphertext expansion (1024-bit integers), increasing per-round communication. Embedded controllers in RTUs/PLCs lack cryptographic coprocessors.

2. **Trusted Third Party dependency**: DyHFL requires TTP for key generation — a single point of failure in adversarial environments. Future work points toward Distributed Key Generation (DKG).

3. **Deterministic latency requirements**: IEC 61850 GOOSE messaging requires sub-4ms protection-class performance. HE encryption latency (~10ms per operation) is incompatible.

4. **Non-IID data**: Power grid data is inherently heterogeneous across substations (different topologies, load profiles). DyHFL's Dirichlet-distributed experiments partially address this.

## Cross-Domain Connections

| Connection | Domain | Insight |
|------------|--------|---------|
| Two-phase preliminary → subsequent selection | Multi-agent orchestration (see [[multi-agent-orchestration-patterns]]) | DyHFL's sliding window + dynamic selection generalizes to any heterogeneous agent pool — directly applicable to Exocortex's call_subordinate selection |
| Three-layer architecture isomorphism | AI agent architecture (see [[ai-agent-architecture-local-inference]]) | Deterministic safety floor + FL optimization + human escalation mirrors Exocortex's deterministic scaffolding + LLM + supervisor loop |
| HE for model security | Privacy & Cryptography (see [[homomorphic-encryption-practical-state]], [[zkml-verifiable-ai-inference]]) | FL with HE bridges operational security and ML privacy — same cryptographic primitives as zkML for inference verification |
| Straggler mitigation for agent systems | Context management (see [[context-management-ai-agent-frameworks]]) | DyHFL's buffer-based aggregation with timeout thresholds is structurally identical to context pruner's entropy-based early termination |
| Grid anomaly detection | Electric Utility (see [[scada-ics-security]], [[distribution-automation-self-healing-grids]], [[grid-forming-inverters-ibr-stability]]) | FL for smart grid IDS closes the gap between isolated utility security operations and sector-wide threat intelligence sharing |
| ICS/SCADA data sensitivity | OSINT (see [[osint-entity-resolution-methods]]) | The same data-sharing reluctance that motivates FL for grid operators mirrors the legal/boundary constraints in OSINT entity resolution — both need PETs to enable collaboration |
| Agentic federation | Bridging local-frontier (see [[bridging-local-frontier-model-performance]]) | FL's model-merging paradigm (train locally, aggregate globally) is homologous to ensemble methods for bridging local-to-frontier performance — multiple weak models collaboratively approach frontier quality |
| Straggler fairness as selection bias | Intelligence failure (see [[intelligence-failure-analysis]]) | DyHFL's straggler selection fairness metric (SRS) prevents systematic exclusion of slower data sources — structurally isomorphic to preventing BST momentum lock from excluding contradictory signals |

## References

1. Kamali Poorazad, S., Benzaïd, C., & Taleb, T. (2026). "Towards Securing IIoT: An Innovative Privacy-Preserving Anomaly Detector Based on Federated Learning." arXiv:2604.06101. University of Oulu / Ruhr University Bochum.

2. SecuFL-IoT: "An Adaptive Privacy-Preserving Federated Learning Framework for Anomaly Detection in Critical IIoT Infrastructures." Nature Scientific Reports, January 2026. PMC12858826.

3. "Balancing the Trilemma: A Survey of Federated Anomaly Detection for Cyber-Physical Systems." Springer Cybersecurity, 2026. DOI: 10.1186/s42400-026-00567-6.

4. "Decentralized Federated Anomaly Detection in Smart Grids." arXiv:2407.15879.

5. Alshamasi, M. & Ibrahim, A. "Federated Intelligence for Smart Grids: A Comprehensive Review." Semantic Scholar, 2025.

6. "DP-FLoTinyLLM: Differentially Private Federated Learning for Log Anomaly Detection." arXiv:2604.19118, April 2026.

7. "Integrating Federated Learning and Differential Privacy for Secure Anomaly Detection in Smart Grids." ACM, 2024. DOI: 10.1145/3694860.3694869.

8. Poorazad, S.K., Benzaïd, C., & Taleb, T. (2024). "A Novel Buffered Federated Learning Framework for Privacy-Driven Anomaly Detection in IIoT." IEEE Globecom 2024, Cape Town.

## Exocortex Architecture Implications

1. **call_subordinate orchestration**: DyHFL's dynamic agent selection with sliding-window performance metrics provides a template for selecting subordinate agents based on latency, output quality, and task complexity — rather than round-robin or static assignment.

2. **Knowledge graph enrichment**: FL's aggregation of encrypted model updates without raw data sharing maps to the knowledge graph's need to store entity relationships while preserving source confidentiality — HE-based privacy-preserving graph merging.

3. **Supervisor loop integration**: DyHFL's two-phase architecture (estimating agent performance → selective participation) mirrors the supervisor loop's escalation logic (monitoring entropy → triggering compression/summarization). Both patterns measure performance variance before acting.

4. **Memory consolidation**: FL distributes training across agents; Exocortex memory consolidation distributes knowledge across ChromaDB + graph layer. Same architectural pattern — local processing, global aggregation.
