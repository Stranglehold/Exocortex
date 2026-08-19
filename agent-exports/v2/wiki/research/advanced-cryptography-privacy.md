# Advanced Cryptography and Privacy (2026)

**Status:** STABLE
**Created:** 2026-07-25
**Interest Domain:** Advanced Cryptography and Privacy

---

## Overview

Three threads within privacy-preserving cryptography transitioning from academic research to production infrastructure in 2026:

1. **Zero-Knowledge Proofs for AI Verification (ZKML)** — proving model outputs without revealing inputs or weights
2. **Fully Homomorphic Encryption (FHE)** — computing on encrypted data with production deployments
3. **Metadata-Resistant Communication** — Signal, Briar, Cwtch, SimpleX architectures for privacy-preserving messaging

---

## Zero-Knowledge Proofs for AI Verification

**Current State (2026):**
- ZKML has shifted from theoretical to practical, with multiple production deployments
- Key frameworks: EZKL, ZKTorch, Lagrange DeepProve, DSperse
- Primary use cases: AI agent verification, secure ML inference, identity systems
- **Critical insight:** ZK proofs provide the cryptographic handshake for multi-agent markets where agents exchange services without data exfiltration risk

**Recent Developments (2026):**
- EU AI Act compliance driving adoption (fully applicable 2026)
- **DSperse Framework** (arXiv Jan 2025, published March 2026): Targeted verification in decentralized AI inference markets with slice-based proofs to reduce costs
- **ZKML Optimizing System** (ACM 2023, production 2026): First framework to produce ZK-SNARKs for realistic ML models including state-of-the-art vision models and distilled GPT-2
- **JOLT Atlas** (Kinic March 2025): Reaching for SOTA in zero-knowledge machine learning with optimized proving
- **zk-OPML** (Springer Feb 2026): Using zero-knowledge proofs to optimize OPML for better performance
- **A Separation Principle for Lookup-Based zkML** (IACR ePrint July 2026): Activation-function optimization reducing proof generation costs
- **Benchmarking CNN Components in EZKL** (ICAIIC 2026): Layer-level analysis for EVM deployment showing multi-dimensional tradeoffs between proof latency, bandwidth, and computational complexity

**Production Deployments (2026):**
- EZKL: Enterprise deployments for verifiable inference on encrypted data
- Lagrange DeepProve: Production system for AI model verification
- DSperse: Decentralized inference markets with targeted verification
- zk-OPML: Optimized proving for production workloads
- zkML survey (arXiv:2502.18535) consolidating design space for verifiable ML
- Proof systems now handle complex neural networks with acceptable overhead
- **ZKML 2026:** Production deployments accelerating — Polyhedra Network, Lagrange DeepProve, EZKL frameworks
- **Key frameworks:** Kudelski Security's ZKML compiler, Chainscore Labs deployment services
- **Tradeoffs:** Verification speed vs. model complexity vs. infrastructure costs remain active research area
- **DSperse Framework** (arXiv Jan 2025, published March 2026): Targeted verification in decentralized AI inference markets with slice-based proofs to reduce costs
- **ZKML Optimizing System** (ACM 2023, production 2026): First framework to produce ZK-SNARKs for realistic ML models including state-of-the-art vision models and distilled GPT-2
- **JOLT Atlas** (Kinic March 2025): Reaching for SOTA in zero-knowledge machine learning with optimized proving
- **zk-OPML** (Springer Feb 2026): Using zero-knowledge proofs to optimize OPML for better performance
- **A Separation Principle for Lookup-Based zkML** (IACR ePrint July 2026): Activation-function optimization reducing proof generation costs
- **Benchmarking CNN Components in EZKL** (ICAIIC 2026): Layer-level analysis for EVM deployment showing multi-dimensional tradeoffs between proof latency, bandwidth, and computational complexity

**Production Deployments:**
- EZKL: Enterprise deployments for verifiable inference on encrypted data
- Lagrange DeepProve: Production system for AI model verification
- DSperse: Decentralized inference markets with targeted verification
- zk-OPML: Optimized proving for production workloads
- zkML survey (arXiv:2502.18535) consolidating design space for verifiable ML
- Proof systems now handle complex neural networks with acceptable overhead
- **ZKML 2026:** Production deployments accelerating — Polyhedra Network, Lagrange DeepProve, EZKL frameworks
- **Key frameworks:** Kudelski Security's ZKML compiler, Chainscore Labs deployment services
- **Tradeoffs:** Verification speed vs. model complexity vs. infrastructure costs remain active research area

---

## Fully Homomorphic Encryption

**Current State (2026):**
- FHE has reached critical inflection point — no longer purely academic
- GPU acceleration is real and shipping: bootstrapping under 1ms on H100
- Production deployments in healthcare (HIPAA analytics), finance (fraud detection), and private ML inference
- **Key frameworks:** Microsoft SEAL, IBM HElib 3.10, TFHE-rs, Concrete ML, OpenFHE

**Performance Reality:**
- Still too slow for interactive applications (latency gap remains)
- Most production deployments use PHE or SHE rather than full FHE
- Applied to specific high-value workloads rather than general infrastructure
- ASIC and photonic speedup claims are projections, not available silicon

**Authenticated Encryption (AEAD):**
- Authenticated encryption with associated data (AEAD) provides integrity + confidentiality
- AEAD(K, P, A) = (C, T) where T is authentication tag, A is associated data (e.g., headers)
- Used in TLS, secure messaging protocols, database encryption

**Format-Preserving Encryption (FPE):**
- Creates ciphertexts with same format as plaintext (e.g., credit card numbers stay 16 digits)
- Required by database systems with strict schema constraints
- Useful for data anonymization in testing environments

**Library References:**
- "Serious Cryptography" (Aumasson) — authenticated encryption, format-preserving encryption, provable security
- "Cryptography Engineering" (Ferguson, Kohno, Schneier) — TLS, quantum/post-quantum cryptography

---

## Metadata-Resistant Communication

**Current State (2026):**
- Signal, Briar, Cwtch, SimpleX architectures for privacy-preserving messaging
- Focus on metadata resistance rather than just content encryption
- Trade-offs between usability, performance, and metadata leakage

**Key Architectures:**
- **Signal:** Metadata-minimizing improvements, but still leaks metadata to server
- **Briar:** Tor-based, offline messaging via Bluetooth/WiFi sync
- **Cwtch:** Pluggable transports, metadata-resistant by design
- **SimpleX:** No user IDs, decentralized, metadata-resistant

**Metadata Resistance Trade-offs:**
- **Signal:** Best UX, but server sees who talks to whom
- **Briar:** Stronger privacy, but requires Tor and sync events
- **Cwtch:** No central server, but slower and less polished
- **SimpleX:** Strongest metadata resistance, but limited ecosystem

**Use Cases:**
- Journalist-source communication (Signal + Briar)
- Activist organizing (Cwtch)
- High-threat individuals (SimpleX)
- Metadata-minimizing improvements for mainstream adoption

---

## Cross-Domain Connections

1. **AI Agent Trust Infrastructure** — ZKML enables trustless agent verification
2. **Decentralized AI Compute Markets** — FHE enables private computation on encrypted data
3. **Intelligence Operations** — Metadata-resistant communication for source protection
4. **Privacy and Data Protection** — FHE enables data analytics without data exposure

---

## Primary Sources

1. Field Report: 2026-07-13_advanced_cryptography_privacy.md
2. arXiv:2502.18535 — zkML survey
3. Microsoft SEAL documentation
4. Signal Foundation research
5. SimpleX chat architecture documentation
