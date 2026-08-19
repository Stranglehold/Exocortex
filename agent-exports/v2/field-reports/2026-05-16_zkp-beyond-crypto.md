# Field Report: Zero-Knowledge Proofs Beyond Cryptocurrency

**Date:** 2026-05-16
**Explorer:** Agent Zero
**Topic:** Privacy & Cryptography — ZKP real-world deployment

---

## 1. What I Explored

I followed the thread of zero-knowledge proof deployment outside the cryptocurrency ecosystem. Most public discussion of ZKPs still orbits blockchain (zk-rollups, Zcash, Ethereum L2s), but the technology is maturing into general-purpose privacy infrastructure. I focused on four non-crypto domains: AI agent trust, government digital identity, healthcare data privacy, and supply chain verification.

## 2. What I Found

### AI Agent-to-Agent Trust
- American Express published a May 2026 article framing ZKPs as the trust substrate for agentic AI: agents proving authorization, compliance, or reasoning correctness without exposing underlying data.
- ERC-8126 (Jan 2026) proposes an AI Agent Verification standard using ZKPs to generate Proof of Digital Verification (PDV) with trustworthiness scores (0-100).
- NomadTrustLayer provides ZKP circuits for AI agent identity verification — agents prove unique identity and prevent duplicate actions without revealing private keys.
- Cloud Security Alliance published ATF (April 2026): a zero-trust framework for AI agents using ZKP-based credential verification.

### Government Digital Identity (eIDAS 2.0)
- EU Digital Identity Wallet (EUDI) must be deployed by all member states by December 31, 2026.
- eIDAS 2.0 explicitly supports zero-knowledge proofs for selective disclosure — proving "I'm over 18" without revealing full birthdate, or "I hold certification X" without exposing the document.
- Dock Labs confirmed Q4 2024 compliance alignment with eIDAS 2.0 standards.
- This represents the largest mandatory ZKP deployment to date: 27 member states, ~450 million potential users.

### Healthcare Privacy
- zkFL-Health (arXiv Dec 2025): ZKP-verified federated learning for cross-silo medical AI, proving the aggregator followed prescribed rules without revealing client data.
- HaloMed (JAIT 2026): First Halo2 implementation in healthcare, recursive proof composition enabling linear-time aggregation of 10,000+ medical records with O(1) verification.
- Multiple papers on ZKP-anonymous patient authentication on blockchain for medical record access.

### Supply Chain & Voting
- Springer chapter (2026) on ZKP-enabled supply chain verification: proving product authenticity and certifications without exposing manufacturer identity or batch locations.
- IEEE paper on zk-Rollup-based privacy-preserving supply chain identity verification.
- Anonymous voting systems using Semaphore and ZKP protocols for verifiable but private elections.

## 3. What I Think Is Interesting

The most significant finding is the **convergence of ZKP across identity, AI trust, and compliance**. Three separate domains — government identity (eIDAS), AI agent verification (ERC-8126, ATF), and healthcare (zkFL-Health) — are independently arriving at ZKP as their privacy primitive.

This suggests ZKP is transitioning from a niche cryptographic tool to **general-purpose trust infrastructure**. The pattern mirrors how TLS went from email encryption to the foundation of all internet communication.

The performance gap remains real: proof generation takes seconds to minutes for complex circuits. This makes ZKP better suited for asynchronous workflows (credential checks, batch audits, compliance verification) than real-time decision loops. Hardware acceleration is narrowing this gap but hasn't closed it.

## 4. What I'd Explore Next

- **Hardware acceleration for ZKP**: Cysic's ZK chips and GPU-based proof generation — how close is real-time verification?
- **zk-STARK vs zk-SNARK adoption trade-offs**: Which approach is winning in enterprise deployments?
- **W3C Verifiable Credentials standardization**: How mature is the interoperability layer between different ZKP implementations?
- **ZKP in model training provenance**: Proving training data licensing compliance without revealing datasets.

## 5. Cross-Domain Connections

- **Data Aggregation & Entity Resolution**: ZKP could enable privacy-preserving entity matching across datasets — proving two records refer to the same entity without exposing the underlying data. This directly connects to the OpenPlanter thesis.
- **Autonomous Coding Agents**: The AI agent trust framework (ERC-8126, ATF) is directly applicable to verifying autonomous agent actions and permissions.
- **History of Intelligence Operations**: ZKP's "prove without revealing" principle mirrors HUMINT tradecraft — verifying source credibility without exposing the source.
- **Hardware & Physical Computing**: ZKP hardware acceleration (FPGAs, custom chips) is a natural extension of the FPGA inference acceleration interest.
