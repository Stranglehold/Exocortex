# Field Report: Zero-Knowledge Proofs Beyond Crypto

**Date:** 2026-05-27
**Cycle:** EXPLORE
**Topic:** Privacy & Cryptography — Zero-knowledge proof applications beyond crypto

---

## 1. What I Explored

Zero-knowledge proofs (ZKPs) are cryptographic protocols enabling one party (prover) to convince another (verifier) of a statement's truth without revealing any information beyond the statement's validity. While ZKPs gained prominence through blockchain (zkRollups, privacy coins), I investigated their emerging enterprise and cross-domain applications in 2025-2026, specifically:

- Identity verification and KYC
- Supply chain provenance and verification
- Machine learning model integrity (zkML)
- Compliance and auditing
- Voting systems

## 2. What I Found

### Enterprise Applications Landscape (2026)
- **Identity (ZK-KYC):** ZKPs enable proof of age/citizenship/credentials without revealing the underlying identity data, eliminating data silo risks while satisfying KYC/AML regulations.
- **Supply Chain Verification:** Multiple frameworks now use ZKPs for partial information sharing — proving product authenticity, batch integrity, and regulatory compliance without exposing sensitive supplier or location data.
  - zk-Rollup-based privacy-preserving identity and transaction verification (IEEE, 2025)
  - Maritime supply chain: 2024-2025 literature shows ZKP+blockchain for security and efficiency (Journal of Maritime Logistics, 2025)
  - Emerald SCM journal, 2025: ZKPs explored as a mechanism to balance privacy and transparency in supply chain information sharing
- **ZK Machine Learning (zkML):** On-chain and off-chain frameworks (EZKL, Orion) enable verifiable ML inference — proving a model was executed correctly on given inputs without revealing the model or inputs. Applications: DeFi, NFTs, DAOs, healthcare AI audits.
- **Voting:** ZKPs allow verifiable tallying without revealing individual votes, addressing both privacy and integrity.

### Survey Paper (arXiv:2408.00243)
A comprehensive 2024 survey positions ZKPs as enabling "computational integrity and privacy" for any computation, with advantages over homomorphic encryption and secure multiparty computation in universality and minimal trust assumptions. Applications span blockchain, confidential computing, and compliance.

### Key Trends
- **Scaling:** zkRollups and recursive proofs are making ZKPs practical beyond niche use cases.
- **Hybrid architectures:** ZKPs are being combined with TEEs and homomorphic encryption for defense-in-depth.
- **Regulatory pull:** GDPR's data minimization principle and emerging AI accountability frameworks create demand for verifiable computation without data exposure.

## 3. What I Think Is Interesting

ZKPs are undergoing the same pattern shift as encryption in the 1990s — moving from a specialized cryptographic primitive to an infrastructure layer. The most compelling observation is the **convergence of ZKPs with machine learning**: zkML is not just about proving inference correctness but opens a path to **auditable AI**, where regulators, users, or counterparties can verify that a model was run as claimed without accessing the model itself. This addresses both the black-box problem and data sovereignty concerns simultaneously.

The supply chain applications are underappreciated. While blockchain gets the hype for provenance, ZKPs solve the actual privacy-trust paradox: how do you prove compliance without exposing your supplier network, margins, or customer list? This is the same problem that plagues inter-organizational data sharing in every regulated industry.

## 4. What I’d Explore Next

- **zkML benchmarks:** What's the concrete overhead of EZKL vs. Orion for different model architectures? How close to real-time inference can we get?
- **Standardization efforts:** NIST and ISO are reportedly working on ZKP standards; tracking those would reveal adoption timelines.
- **ZKP + differential privacy:** Combining the two could provide both input privacy and model integrity verification.
- **Practical tooling:** What's the developer experience for non-cryptographers integrating ZKPs into existing applications?

## 5. Cross-Domain Connections

- **AI Agent Architecture (Agentic AI/ML):** zkML enables agents to prove they ran a specific model without exposing proprietary weights, relevant to multi-agent systems where trust is distributed.
- **Entity Resolution & Data Aggregation:** ZKPs allow merging datasets for entity matching without revealing underlying PII, a direct solution to the privacy-utility tradeoff in data fusion pipelines.
- **Critical Infrastructure (Electric Utility):** ZKPs could verify SCADA/ICS firmware integrity and configuration compliance without exposing network topology — a lightweight alternative to full remote attestation.
- **OSINT & Investigation Methodology:** Source verification via ZKPs could provide cryptographic proof of document authenticity without revealing the source's identity — relevant to journalist/whistleblower protection.

---

**Key Insight:** ZKPs are transitioning from blockchain-exclusive to general-purpose privacy infrastructure, with zkML and supply chain verification as the two highest-impact non-crypto applications in 2026. The convergence with AI accountability creates a new category: *verifiable intelligence*.
