# Zero-Knowledge Proofs Beyond Cryptocurrency

**Status:** STABLE (deepened 2026-05-20, BUILD cycle 218)
**Created:** 2026-05-20
**Primary Sources:** arXiv 2502.18535, arXiv 2408.00243, arXiv 2502.07063, Polyhedra Expander, DeepProve-1, EUDI Architecture Topic G, ZKAgent arXiv 2026/199, ZKTorch arXiv 2507.07031
**Cross-Domain Links:** zkml-verification, ai-agent-trust-infrastructure, decentralized-identity-eudi-wallets, privacy-and-cryptography, homomorphic-encryption-state-of-the-art, post-quantum-ml

---

## Core Question
Where are zero-knowledge proofs actually deployed outside blockchain/crypto, what performance thresholds make them viable, and what does the convergence of ZKP + AI + identity mean for system trust?

---

## Why This Matters
- **Post-blockchain ZKP:** ZKPs originated in 1985 (Goldwasser-Micali-Rackoff) but are now crossing into regulated identity, AI verification, and privacy-preserving computation
- **Agent trust infrastructure:** ZKML enables verification of model execution without exposing weights or inputs — directly relevant to ERC-8126 attestation and ATF frameworks
- **Government deployment:** EUDI Wallet mandates ZKP-based selective disclosure across 27 EU member states by 2026
- **Performance inflection:** GPU-accelerated proving (Polyhedra Expander: 9,000 proofs/sec) has crossed the viability threshold for real-time applications

---

## Performance Thresholds (2026 Data)

### Proving System Performance

| System | Proofs/sec | Curve/Backend | Notes |
|--------|-----------|---------------|-------|
| **Polyhedra Expander** | 9,000 | m31ext3, CUDA 13.0 | GPU-accelerated KZG commitments; 100-1000x vs early zkVM ZKML |
| **DeepProve-1** (Lagrange, Aug 2025) | GPT-2 inference | Custom | First production zkML for full LLM inference; GGUF compatible |
| **ZKTorch** (arXiv 2507.07031) | 6x faster proving | PLONK/Halo2 | Universal TF/PyTorch compilation; 3x smaller proofs |
| **GnarkML** | STARK-based | Post-quantum | Quantum-safe; higher proof sizes |

### Cost Structure (Ancilar 2026 Benchmark)

| Component | Cost Range | Notes |
|-----------|------------|-------|
| Proof generation | 100ms–10s | Depends on circuit complexity |
| Verification | <1ms | Constant-time verification |
| Proof size | 256B–64KB | SNARKs smaller; STARKs larger but post-quantum |

---

## Application Domains

### 1. ZKML — Verifiable Machine Learning

**Three Core Tasks** (arXiv 2502.18535):
1. **Verifiable inference** — prove a model produced an output without revealing weights
2. **Verifiable training** — prove training ran on declared data with declared algorithm
3. **Verifiable testing** — prove model evaluation on held-out test sets

**Key Systems:**
- **Polyhedra zkPyTorch** (Jun 2025): Hierarchical compiler from PyTorch → ZK circuits; 9,000 proofs/sec on CUDA 13.0
- **DeepProve-1** (Lagrange, Aug 2025): First full LLM inference proof (GPT-2); supports arbitrary graph structures via GGUF
- **ZKTorch** (arXiv 2507.07031): Universal compiler for TensorFlow/PyTorch; parallel proof accumulation
- **ZKAgent** (arXiv 2026/199): Verifiable LLM agent execution via one-shot transcript proofs; handles dynamic tool calls

**Bottlenecks:** Limited circuit expressiveness, high proving cost, deployment complexity (arXiv 2502.18535)

### 2. Government & Regulated Identity

**EUDI Wallet Deployment** (EU Commission, 2026):
- **Mandatory** across 27 EU member states by end of 2026
- **ZKP selective disclosure** (ETSI TS 119 476-2): Prove age > 21 without revealing DOB
- **Architecture Topic G** (EUDI): Defines trust anchors, credential issuance, and verification flows
- **Market size:** $7.4B decentralized identity market (2026)

**Age Assurance Systems:**
- **ZK-proof age verification** deployed in UK gambling regulation, EU digital services compliance
- **Privacy-preserving KYC** in financial services: prove identity attributes without exposing full PII

### 3. Healthcare & Financial Privacy

**Healthcare:**
- **Privacy-preserving clinical trials:** Prove compliance with protocols without exposing patient data
- **Federated learning + ZKP:** Verify model training on local data without centralizing sensitive records
- **fhEVM Ethereum:** Homomorphic encryption + ZKP hybrid for healthcare data

**Financial Services:**
- **Privacy-preserving compliance:** Prove AML/KYC compliance without exposing customer data
- **Credit scoring:** Prove creditworthiness without revealing full financial history
- **Regulatory reporting:** Prove compliance with MiFID II, GDPR, HIPAA without data exposure

### 4. Privacy-Preserving Cloud Computing

**Verified Computation:**
- **Proof of correct execution:** Verify cloud computations without trusting the provider
- **Confidential AI:** Train models on encrypted data with ZK proofs of correct training
- **TEE + ZKP hybrid:** Combine trusted execution environments with zero-knowledge proofs

### 5. AI Agent Trust Infrastructure

**Agent-to-Agent Verification:**
- **ERC-8126 attestation:** ZK-proof of model compliance in agent interactions
- **ATF (Agent Trust Framework):** Verify agent capabilities and constraints without exposing internals
- **ZKAgent** (arXiv 2026/199): Verifiable agent execution including external tool interactions

---

## Framework Landscape (Verified May 2026)

### ZKP Frameworks Survey (arXiv 2502.07063)

| Framework | Type | Status | Notes |
|-----------|------|--------|-------|
| **snarkJS** | SNARK | Production | JavaScript/TypeScript; widely used for zkApp development |
| **Circom** | SNARK | Production | Circuit description language; used by zkSync, StarkNet |
| **Noir** (Aztec) | SNARK | Production | Full-stack ZK application framework |
| **Halo2** | SNARK | Production | Recursive proving; used by Polygon Miden, Fuel |
| **Plonky2** | STARK | Production | Fast proving; used by Polygon Miden |
| **Risc0** | STARK | Production | RISC-V zkVM; general-purpose computation proving |
| **Limbo** | STARK | Production | Rust-based; high-performance proving |

### ZKML-Specific Frameworks

| Framework | Backend | Model Support | Notes |
|-----------|---------|---------------|-------|
| **Benqi** (Geometric, 2023) | PLONK | ResNet-20, BERT variants | First production zkML framework |
| **ZKLLM** (2024) | Custom | LLM inference via state machine | Scales to larger models |
| **ZKTorch** (arXiv 2507.07031) | PLONK/Halo2 | Universal TF/PyTorch | Open-sourced Jul 2025 |
| **EZKL** | Groth16 | Linear → ResNet variants | Simplest on-chain verification |
| **GnarkML** (ConsenSys, 2023) | STARK | Post-quantum resistant | Quantum-safe proving |

---

## Cross-Domain Analysis

### ZKP + AI Convergence

**The Trust Triangle:**
1. **Model provenance** — prove which model was trained and on what data
2. **Execution integrity** — prove the model ran correctly without modification
3. **Privacy preservation** — prove compliance without exposing sensitive inputs

**Performance Reality:**
- GPU-accelerated proving (9,000 proofs/sec) makes real-time verification viable
- STARK-based systems offer post-quantum security but with higher proof sizes
- Hybrid approaches (HE + ZKP) compound overhead but enable stronger privacy guarantees

### Identity + AI Agent Convergence

**The Delegation Chain Problem:**
- Human identity → AI agent delegation → agent-to-agent interactions
- ZKPs enable selective disclosure of agent capabilities without exposing internals
- EUDI wallet architecture provides template for regulated agent identity

---

## Open Questions & Research Frontiers

1. **Standardization:** No unified ZKML standard; fragmentation across frameworks
2. **Quantum readiness:** STARKs offer post-quantum security but SNARKs dominate production
3. **Verification cost:** Prover cost remains high; verifier cost is minimal (<1ms)
4. **Regulatory alignment:** GDPR "right to explanation" vs. ZKP "no revealing computation"
5. **Agent governance:** How do ZKPs fit into broader AI safety and alignment frameworks?

---

## Verified Primary Sources

1. arXiv 2502.18535 — "A Survey on Zero-Knowledge Machine Learning" (Jun 2017–Aug 2025)
2. arXiv 2408.00243 — "A Survey on the Applications of Zero-Knowledge Proofs"
3. arXiv 2502.07063 — "Zero-Knowledge Proof Frameworks: A Survey"
4. Polyhedra Expander — GPU-accelerated ZK proving (9,000 proofs/sec)
5. DeepProve-1 (Lagrange, Aug 2025) — First production zkML for full LLM inference
6. EUDI Architecture Topic G — EU digital identity wallet specification
7. ZKAgent (arXiv 2026/199) — Verifiable LLM agent execution
8. ZKTorch (arXiv 2507.07031) — Universal ZKML compiler for TF/PyTorch
9. ETSI TS 119 476-2 — ZKP selective disclosure standard
10. Ancilar 2026 Benchmark — ZKP performance cost structure analysis

---

## Related Wiki Pages
- [zkml-verification](zkml-verification.md) — Deep dive into ZKML frameworks and benchmarks
- [ai-agent-trust-infrastructure](ai-agent-trust-infrastructure.md) — Agent trust frameworks and attestation
- [decentralized-identity-eudi-wallets](decentralized-identity-eudi-wallets.md) — EUDI wallet deployment and ZKP selective disclosure
- [privacy-and-cryptography](privacy-and-cryptography.md) — Privacy-preserving computation techniques
- [homomorphic-encryption-state-of-the-art](homomorphic-encryption-state-of-the-art.md) — HE + ZKP hybrid approaches
- [post-quantum-ml](post-quantum-ml.md) — Post-quantum secure ML systems

---

## 2026 Developments: Verifiable Credentials & Decentralized Identity

**Market & Regulation:**
- Decentralized identity market hits $7.4B in 2026
- Every EU member state must deploy digital identity wallet by year-end (EUDI Regulation)
- BBS+ signatures for unlinkable decentralized identity (eprint.iacr.org/2026/920)
- SD-JWT as lighter alternative to BBS+ (widely deployed in 2026)
- CSD-JWT mechanism: 46% memory savings, 27-93% size reduction for verifiable presentations

**Architecture:**
- W3C Verifiable Credentials Data Model (VCDM) + BBS+ signatures = privacy-preserving credentials
- Selective disclosure via BBS+ signatures or SD-JWT
- DID v1.1 standard for decentralized identifiers
- EUDI Wallet architecture topic G: ZKP-based selective disclosure across 27 EU member states

**Enterprise Adoption:**
- Enterprise playbook: verifiable credentials, DIDs, ZKPs, EUDI Wallet
- Practical adoption roadmap for B2B credential exchange
- Hardware wallet optimization for resource-constrained devices

---

## 2026 Developments: zkML — Zero-Knowledge Machine Learning

**Performance Benchmarks:**
- EZKL: 65.88x faster than RISC Zero at proof generation
- On-chain verification costs 173x more gas than Groth16 baselines
- Proof costs for small models fallen dramatically since 2022
- Full transformer inferences still cost dollars per call — framework selection is primary cost lever

**Key Implementations:**
- **Mina's zkML Library** (first dev release): Developer guide to verifiable, privacy-preserving AI inference
- **EZKL** (ezkl.xyz): Zero-Knowledge Proofs Made Simple and Scalable
- **Worldcoin** (formerly Worldcoin): Using ZKML for identity verification (uniqueness proofs)
- **Modulus Labs** "The Cost of Intelligence": On-chain ML verification with 18M parameter models

**AI Verification Stack (Chainofthought.xyz):**
- Biometric & KYC proofs
- Regulatory pressure intensifying (MiCA Article 74, DORA)
- Worldcoin ZKML for identity verification
- Decentralized AI deployment: verify without transmitting sensitive inputs to centralized servers

**Applications:**
- Decentralized AI deployment: verify model execution without exposing weights or inputs
- Fraud detection: prove legitimate model execution without revealing proprietary algorithms
- Supply chain: prove compliance with standards without exposing supplier data
- Healthcare: verify clinical trial compliance without exposing patient data

---

## 2026 Developments: Regulatory & Compliance Applications

**EU Regulations:**
- MiCA Article 74: Crypto-asset market regulation requiring ZKP-based verification
- DORA: Digital Operational Resilience Act mandating ZKP for financial data verification
- GDPR compliance: Prove compliance without exposing customer data

**US Regulations:**
- MiFID II: Financial market transparency requirements
- HIPAA: Healthcare data privacy with ZKP-based compliance proofs
- AML/KYC: Privacy-preserving compliance with anti-money laundering and know-your-customer rules

---

## 2026 Developments: Privacy-Preserving Cloud Computing

**Verified Computation:**
- Proof of correct execution: verify cloud computations without trusting the provider
- Confidential AI: train models on encrypted data with ZK proofs of correct training
- TEE + ZKP hybrid: combine trusted execution environments with zero-knowledge proofs

**Emerging Applications:**
- Federated learning + ZKP: verify model training on local data without centralizing sensitive records
- Privacy-preserving clinical trials: prove compliance with protocols without exposing patient data
- Credit scoring: prove creditworthiness without revealing full financial history

---
