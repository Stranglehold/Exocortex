# Field Report: Privacy & Cryptography — Homomorphic Encryption for AI Inference

**Date:** 2026-05-22
**Cycle:** 295 (EXPLORE)
**Topic:** Privacy & Cryptography — Homomorphic Encryption Practical State of the Art
**Thread Followed:** Orion FHE framework for private deep neural network inference

---

## 1. What I Explored

The thread of practical homomorphic encryption (HE) deployments, specifically focusing on fully homomorphic encryption (FHE) for deep learning inference. Two primary sources drove exploration:

1. **Orion framework** (Ebel, Garimella, Reagen — NYU, arXiv:2311.03470, published ACM DL 2025): A fully automated compiler that translates PyTorch models into efficient FHE programs for private neural network inference.
2. **Non-leveled HE for web services** (Chen & Zhao, arXiv:2508.02943, WWW 2026): A "Refresh" prototype that approximates CKKS bootstrapping via binarized polynomial rings, enabling non-leveled HE without full bootstrapping overhead.

Secondary context: market projections ($182.1M in 2025, 19.5% CAGR through 2033), IEEE use case catalog, and comparative analyses of HE schemes for privacy-preserving AI.

---

## 2. What I Found

### Orion Framework (NYU, 2025)
- **2.38x speedup** over prior state-of-the-art on ResNet-20 benchmark
- Fully automated: accepts PyTorch models, handles bootstrapping placement, FHE algorithm selection for convolutions, and non-linear activation approximation automatically
- Enables computation on **much larger networks** than previously possible in FHE
- Available on GitHub (baahl-nyu/orion) with CKKS backend integration
- Published at ACM DL 2025 (DOI: 10.1145/3676641.3716008)

### Non-Leveled HE (Chen & Zhao, WWW 2026)
- Addresses CKKS noise growth problem without full bootstrapping
- Uses **binarized polynomial rings** as a "skeleton" for CKKS bootstrapping approximation
- Refresh prototype is explicitly a research skeleton, not yet a validated production implementation
- Published at WWW 2026, Dubai (April 2026)

### Market & Deployment Context
- HE market valued at $182.1M in 2025, projected 19.5% CAGR through 2033
- Key players: Microsoft (SEAL), IBM, Galois
- Healthcare analytics and space-domain collaboration cited as early applied evaluation domains
- Quantum-resistant HE variants emerging for energy systems (ScienceDirect, Apr 2026)

### Key Technical Insight
The fundamental bottleneck for FHE in production is **bootstrapping overhead** — the process of refreshing ciphertext noise to allow unlimited computation depth. Orion's innovation is automating where and how bootstraps are placed during inference, rather than treating it as a manual optimization problem.

---

## 3. What I Think Is Interesting

The Orion framework represents a category shift: FHE is moving from "academic proof of concept" to "compiler-managed infrastructure." The automation of bootstrapping placement and activation approximation means developers can write models in standard PyTorch without FHE expertise.

The non-leveled HE approach is potentially more disruptive but riskier. If CKKS bootstrapping can be approximated via binarized polynomials with bounded error, it could eliminate the single largest performance bottleneck in practical FHE. However, the authors explicitly caveat this as a prototype.

The cross-domain connection between **FHE for inference** and **trusted execution environments (TEEs)** is worth noting: both solve the same problem (compute on sensitive data) via different threat models. FHE protects data even from the cloud provider; TEEs trust hardware roots. Orion's 2.38x speedup is impressive but FHE inference is still orders of magnitude slower than plaintext — TEEs may win on performance, FHE wins on trust assumptions.

---

## 4. What I'd Explore Next

1. **Orion benchmarking on larger models** — ResNet-20 is small; how does it scale to ResNet-50, ViTs, or transformer architectures?
2. **FHE vs TEE performance comparison** for identical workloads — concrete numbers on when FHE becomes competitive
3. **CKKS bootstrapping approximation error bounds** — the non-leveled HE paper lacks quantitative error analysis; how much does approximate bootstrapping degrade model accuracy?
4. **Multi-party FHE** — can Orion compose with secure multi-party computation for federated inference scenarios?

---

## 5. Cross-Domain Connections

- **Edge AI Security (Hardware/Software Co-Design)**: FHE inference at the edge could complement TEE-based approaches for privacy-preserving ML. The TwinShield architecture (heterogeneous TEE+GPU) could theoretically integrate FHE backends.
- **AI Agent Trust Infrastructure**: FHE provides a cryptographic trust layer for agent-to-agent data exchange without a trusted third party.
- **Post-Quantum ML**: Quantum-resistant HE variants are explicitly mentioned in energy system applications; the same constructions could protect ML pipelines against quantum adversaries.
- **Zero-Knowledge Proofs**: ZK-ML verification and FHE inference solve complementary problems — ZK proves computation integrity, FHE preserves data confidentiality. Combined they'd enable fully verifiable private inference.
- **Data Aggregation & Entity Resolution**: FHE could enable privacy-preserving entity resolution across institutional datasets without data sharing — directly relevant to OpenPlanter's thesis.

---

## Sources

1. Ebel, A., Garimella, K., Reagen, B. (2025). *Orion: A Fully Homomorphic Encryption Framework for Deep Learning*. ACM DL. arXiv:2311.03470. DOI: 10.1145/3676641.3716008
2. Chen, B., Zhao, D. (2026). *Reliable Non-Leveled Homomorphic Encryption for Web Services*. WWW 2026. arXiv:2508.02943
3. NYU Engineering News (Mar 2025). *Encryption breakthrough lays groundwork for privacy-preserving AI models*
4. CKKS Blog (2026). *Orion: A Fully Homomorphic Encryption Framework for Deep Learning*
5. IEEE Digital Privacy. *Homomorphic Encryption Use Cases*
6. ScienceDirect (Apr 2026). *Quantum-resistant homomorphic encryption for privacy-preserving energy systems*
7. GitHub: baahl-nyu/orion repository

---

*Report generated during EXPLORE cycle #295. Key insight saved to memory via memory_save.*
