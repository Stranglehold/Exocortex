# Field Report: Zero-Knowledge Proof Applications Beyond Cryptocurrency

**Date:** 2026-05-26
**Cycle:** EXPLORE
**Topic:** Privacy & Cryptography — Zero-Knowledge Proof Applications Beyond Crypto

---

## 1. What I Explored

Zero-knowledge proofs (ZKPs) are most commonly associated with cryptocurrencies and blockchain, but they are a general cryptographic primitive with broad applicability. I investigated the current state of ZKP use cases in non-crypto domains: healthcare, supply chain, identity verification, e-voting, machine learning verification, and decentralized authentication. I reviewed the arXiv survey "A Survey on the Applications of Zero-Knowledge Proofs" (2408.00243v1) and practical overviews from Chainlink, jayschulman.com, and academic papers.

## 2. What I Found

### Healthcare
- **Anonymous patient authentication**: patients can prove they belong to an authorized group (e.g., eligible for a clinical trial) without revealing their identity, using ZKP-based identity systems (ScienceDirect, 2025).
- **Data privacy**: ZKPs enable verification of medical record integrity without exposing the underlying data — useful for cross-institution research.

### Supply Chain
- **Provenance without exposure**: suppliers can prove goods meet certain criteria (origin, quality, compliance) without revealing the full supply chain. Chainlink has explored this for ethical sourcing.
- **Regulatory compliance**: companies can prove they follow regulations while keeping proprietary business data confidential.

### Identity & Authentication
- **Decentralized identity (DID)**: Redactable signatures vs. ZKPs for privacy-preserving identity. ZKPs are more expressive but may require trusted setup (Kumara et al., 2023).
- **Scholarship evaluation**: ZKP-based system for verifying academic qualifications without exposing grades (Chen et al., 2025).
- **Age verification**: users can prove they meet age requirements without revealing their exact birthdate — a practical ZKP application already being explored in EU digital identity frameworks.

### E-Voting
- **Verifiable voting**: voters can confirm their vote was counted without revealing their choice, enabling end-to-end verifiable elections. Several academic proposals exist.

### Machine Learning
- **Verifiable inference (ZKP-VML)**: proving that a ML model's inference was computed correctly without revealing the model weights or input data. This is the most active research area.
- **Training verification**: emerging work on proving that training was conducted correctly (Garg et al.), though computational cost remains high.
- **ZKMLOps**: a unified framework for cryptographic guarantees across the ML lifecycle (identified in a systematic survey).

### Other Domains
- **Intellectual property**: proving ownership or usage rights without revealing the IP itself.
- **Financial auditing**: proving solvency or regulatory compliance without disclosing full balance sheets.
- **Quantum ZKPs**: verifier-initiated quantum message authentication (Wang & Hayashi, 2025) — relevant as we approach post-quantum cryptography.

### State of the Art
Current ZKP systems vary widely in performance. Succinct non-interactive arguments of knowledge (zk-SNARKs) offer constant-size proofs but require a trusted setup. zk-STARKs remove the trusted setup but have larger proofs. Bulletproofs provide logarithmic proof sizes without trusted setup. Practical adoption is still nascent due to high prover costs and integration complexity.

## 3. What I Think Is Interesting

The convergence toward **ZKMLOps** — a framework for end-to-end cryptographic verification of the ML lifecycle — is particularly compelling. As AI regulation (EU AI Act) requires tamper-proof evidence of model behavior, ZKPs become critical infrastructure for trustworthy AI. This directly connects to Jake's interest in local inference and agent architecture: if we want agent decisions to be auditable and verifiable, ZKPs could provide the cryptographic backbone.

Also interesting: the tension between redactable signatures and ZKPs in identity systems. Redactable signatures are cheaper and faster; ZKPs offer stronger privacy. The emerging consensus is to use redactable signatures initially and migrate to ZKPs as the technology matures. This pattern — start simple, evolve to stronger cryptography — mirrors the evolution of TLS.

A surprising finding: ZKP-based machine learning verification is not just theoretical. The survey identified dozens of implemented schemes, with inference verification being the most mature. This could be relevant for Exocortex if we ever need to prove that an agent's reasoning was faithful to its prompt and model.

## 4. What I'd Explore Next

1. **Practical ZKP performance benchmarks**: what's the real proving time and proof size for ML inference verification on consumer hardware? Could an RTX 3090 perform ZKP proving for a modest transformer?
2. **ZKP for agentic systems**: can we prove that an agent's tool call was a deterministic consequence of its prompt and context, preventing tampering?
3. **Post-quantum ZKPs**: as quantum computing advances, are current ZKP schemes vulnerable? What's the transition path?
4. **Regulatory landscape**: how the EU AI Act and similar frameworks specifically address ZKP-based verification.

## 5. Cross-Domain Connections

- **AI Agent Architecture**: ZKMLOps for verifiable agent actions connects ZKPs to Exocortex's self-improvement loop. If we can prove an agent's output was faithful, we have an integrity guarantee beyond epistemic monitoring.
- **Hardware & Physical Computing**: FPGA-based ZKP acceleration is a growing field. Connecting ZKP proving to custom hardware could make verification practical at the edge.
- **OSINT & Investigation**: ZKPs for identity without disclosure could enable privacy-preserving OSINT — verifying a connection between entities without revealing the investigator's methods or sources.
- **Electric Utility**: ZKPs for SCADA/ICS — proving that a control command was authorized without revealing the command itself, useful for classified grid operations.

---

**Sources:**
- arXiv 2408.00243v1: "A Survey on the Applications of Zero-Knowledge Proofs"
- jayschulman.com: "Exploring the Use Cases of Zero-Knowledge Proofs Beyond Cryptocurrencies"
- Kumara et al. (2023): Redactable Signatures and ZKPs for Decentralized Identity
- Chen et al. (2025): Privacy-Preserving Scholarship Evaluation via DID and ZKP
- Wang & Hayashi (2025): Verifier-Initiated Quantum Message Authentication via Quantum ZKPs
- Chainlink: Zero-Knowledge Proof Use Cases
- ScienceDirect: Leveraging zero knowledge proofs for blockchain-based identity sharing
