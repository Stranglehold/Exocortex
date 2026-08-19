# Field Report: Zero-Knowledge Proof Applications Beyond Crypto — 2026 Frontiers

**Date:** 2026-05-27
**Cycle:** EXPLORE
**Topic:** Privacy & Cryptography — ZKP Applications Beyond Crypto
**Status:** Complete

---

## 1. What I Explored

The interests.md directive asked: "Zero-knowledge proof applications beyond crypto." Prior cycles covered ZK-PoP for human authorship, AI identification frameworks, stateful proximity proofs, verifiable credentials for IoT, ZK regex/PSPACE, QR-code mobile authentication, and VeriSBOM for software supply chains. This cycle examined three fresh threads that had no prior coverage:

1. **ZKP for Verifiable ML Inference (zkML)** — specifically Jolt Atlas (arXiv 2602.17452, Feb 2026), which extends the Jolt proving system to ONNX model inference, enabling on-device cryptographic verification of ML inference without specialized hardware.
2. **ZKP in 5G/6G Telecommunications** — B5GRoam (arXiv 2509.16390, Sep 2025): privacy-preserving roaming settlements using zkSNARKs on Layer 2 zk-Rollups (7,200+ tx/s).
3. **ZKP for Smart Vehicle Digital Passports** — VehiclePassport (arXiv 2509.06133, Sep 2025): GAIA-X-aligned, blockchain-anchored digital passport with Groth16 proofs for GDPR-compliant traceability.

---

## 2. What I Found

### 2.1 Verifiable ML Inference — Jolt Atlas

**Paper:** Benno, Centelles, Douchet, Gibran (2026). _Jolt Atlas: Verifiable Inference via Lookup Arguments in Zero Knowledge_ (arXiv:2602.17452)

- Extends the Jolt ZK proving system from CPU instruction emulation to ONNX tensor operations, eliminating the overhead of emulating a full CPU.
- Uses **lookup arguments** (sumcheck protocol) for non-linear functions — a natural fit for ML activation functions.
- **Neural teleportation**: optimizes lookup table size while preserving model accuracy.
- **Streaming prover**: enables proof generation in memory-constrained environments.
- Achieves practical proving times for classification, embedding, automated reasoning, and **small language models**.
- **BlindFold technique** (from Vega) provides zero-knowledge property.
- Proofs are succinctly verifiable on-device, no specialized hardware required.
- **Use cases cited**: guardrails in agentic commerce, trustless AI context ("AI memory").

**Why this matters:** zkML has been theoretically attractive but practically bottlenecked. Jolt Atlas is the first framework to claim practical proving times for real ML workloads in memory-constrained settings. If verifiable inference becomes cheap enough, it enables:
- Autonomous agents that can cryptographically prove they ran a specific model with specific inputs, enabling audit trails without exposing model weights or input data.
- Trustless AI marketplaces where model providers prove inference correctness without revealing proprietary models.
- Privacy-preserving AI in regulated environments (GDPR, HIPAA).

**Cross-domain connection to AI Agent Architecture:** The Exocortex agent system could use zkML to provide verifiable audit trails of agent decision-making. If an autonomous agent takes a consequential action (e.g., financial transaction, security decision), it could produce a ZK proof that it followed authorized reasoning pathways without revealing its full context. The "AI memory" use case in the paper directly parallels the Exocortex's need for trustless context verification.

### 2.2 5G/6G Roaming Settlement — B5GRoam

**Paper:** Authors unnamed (2025). _B5GRoam: On-Chain Zero-Trust Framework for Secure, Privacy-Preserving and Scalable Roaming Settlements in 5G and Beyond Networks_ (arXiv:2509.16390)

- Roaming settlement between mobile operators is a multi-billion-dollar reconciliation problem plagued by disputes and intermediaries.
- B5GRoam introduces cryptographically verifiable Call Detail Records (CDRs) with zkSNARKs — on-chain verification of roaming activity without exposing user or network details.
- Layer 2 zk-Rollups provide throughput of **7,200+ tx/s** with strong privacy and significant gas cost reduction.
- Eliminates intermediaries; enables direct operator-to-operator settlement via smart contracts.

**Why this matters:** Telecom roaming infrastructure still runs on protocols from the 1990s (TAP files, batch reconciliation). ZKPs offer a pathway to real-time, trustless settlement that preserves subscriber privacy — a direct application of ZKPs to a non-crypto, trillion-dollar industry.

**Cross-domain connection to OSINT & Geopolitics:** Telecom infrastructure is critical infrastructure. Verifiable roaming settlement with privacy preservation has geopolitical implications — nation-states could demand verifiable records of cross-border communication patterns without exposing individual identities. The same zkSNARK infrastructure could be repurposed for secure intelligence sharing with selective disclosure.

### 2.3 Smart Vehicle Digital Passports — VehiclePassport

**Paper:** Kaushal (2025). _VehiclePassport: A GAIA-X-Aligned, Blockchain-Anchored Privacy-Preserving, Zero-Knowledge Digital Passport for Smart Vehicles_ (arXiv:2509.06133)

- Vehicles accumulate fragmented lifecycle records (manufacturing, telemetry, service) that are difficult to verify and prone to fraud.
- VehiclePassport anchors hashes on Polygon zkEVM at **<$0.02 per event**, validates Groth16 proofs in **<10 ms**.
- Enables selective disclosure via short-lived JWTs — prove a vehicle has a valid service history without revealing where or by whom.
- GDPR-compliant traceability: the ZKP layer ensures that identity-linked data is not exposed during verification.
- Scales to millions of vehicles.

**Why this matters:** This is a real-world ZKP application in a regulated industry (automotive) where GDPR compliance is mandatory. The architecture of "immutable commitment + selective disclosure via ZKPs" is a pattern that generalizes to supply chains, medical records, and professional certifications. The <$0.02/event cost and <10ms verification time suggests the economics are viable at scale.

**Cross-domain connection to Data Aggregation & Entity Resolution:** Vehicle identity resolution across OEMs, insurers, and regulators is an entity resolution problem. ZKPs enable selective joining of datasets without full data sharing — a privacy-preserving entity resolution primitive.

---

## 3. What I Think Is Interesting

### The Pattern: ZKPs Are Becoming Practical Verification Primitives

All three papers share a common architecture:
1. **Immutable commitment** (blockchain or cryptographic hash) to a claim
2. **ZK proof generation** that some property holds over the committed data
3. **Succinct verification** (sub-10ms, sub-200 bytes)
4. **Selective disclosure** — the verifier learns only the property, not the underlying data

This pattern is appearing in software supply chains (VeriSBOM), automotive (VehiclePassport), telecom (B5GRoam), AI (Jolt Atlas), and identity (QR-auth, AI identification). The convergence suggests we've crossed a threshold: ZK proving systems (Groth16, Plonk, Spartan) and tooling (Circom, Noir) are mature enough that domain experts can build ZKP applications without being cryptographers.

### The Verifiable AI Frontier

Jolt Atlas is the most consequential finding. The ability to prove that a specific AI model produced a specific output from specific inputs — without revealing the model, the inputs, or intermediate states — is a foundational primitive for trust in autonomous systems. If an autonomous agent makes a $10,000 trade, a ZK proof could confirm it followed risk constraints without exposing the reasoning. This is the bridge between "AI as black box" and "AI as auditable infrastructure."

### 5G/6G is an Underexplored ZKP Application Domain

Telecom is 20+ years behind in cryptographic modernization. The B5GRoam paper is the first credible proposal I've found for ZKP-based roaming settlement. The 7,200 tx/s throughput on L2 zk-rollups suggests the scalability argument ("ZKPs are too slow for telecom") no longer holds. Given that roaming settlement is a $30B+ market with chronic disputes, this is a commercially viable ZKP application.

---

## 4. What I'd Explore Next

1. **zkML implementation maturity:** Benchmark Jolt Atlas against alternatives (EZKL, TensorPlonk, zkLLM). What models can it prove? What are the actual proving times for LLM inference of >1B parameters? How does this interact with speculative decoding?
2. **Agentic audit trails via ZKPs:** Can we build a proof-of-reasoning primitive for agent systems? If an agent follows a chain-of-thought, can we ZK-prove that each step followed a verifiable policy without revealing the full reasoning trace?
3. **5G/6G ZKP standardization:** Track 3GPP SA3 (security) working group for any ZKP-related study items. The B5GRoam architecture could be submitted as a contribution.
4. **Selective disclosure pattern library:** Catalog the ZKP-for-selective-disclosure pattern across domains (automotive, supply chain, identity, medical). Develop a reusable architecture reference.

---

## 5. Cross-Domain Connections

| Interest Area | Connection |
|---------------|-----------|
| **AI Agent Architecture** | Verifiable inference (Jolt Atlas) enables auditable autonomous agents — proof that reasoning followed policy |
| **OSINT & Investigation** | ZKP selective disclosure pattern solves the "share intelligence without revealing sources" problem |
| **Data Aggregation & Entity Resolution** | ZKPs enable privacy-preserving entity resolution across siloed datasets |
| **Geopolitics & Strategic Analysis** | Telecom ZKPs (B5GRoam) have dual-use implications for intelligence sharing and sovereign network verification |
| **Markets & Financial Analysis** | ZKP-based verifiable settlement is a fintech primitive applicable to clearinghouses and cross-border payments |

---

**Sources:**
1. Benno et al. (2026). Jolt Atlas: Verifiable Inference via Lookup Arguments in Zero Knowledge. arXiv:2602.17452
2. Anonymous (2025). B5GRoam: On-Chain Zero-Trust Framework for Roaming Settlements in 5G+. arXiv:2509.16390
3. Kaushal (2025). VehiclePassport: GAIA-X-Aligned, Blockchain-Anchored ZK Digital Passport. arXiv:2509.06133
