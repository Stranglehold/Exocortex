# Post-Quantum Cryptography for AI Agent Security

**Status:** STABLE
**Deepened:** 2026-06-05 (BUILD 1136)
**Created:** 2026-06-05
**Interest Domain:** AI Agent Architecture / Privacy & Cryptography

## Core Question
How do post-quantum cryptographic standards (NIST Round 3: ML-KEM, ML-DSA, SLH-DSA) integrate with AI agent communication protocols (MCP, A2A, OpenAPI) to secure autonomous agent interactions against quantum threats?

## NIST PQC Standards (Verified 2024 Finalization)

### FIPS 203 — ML-KEM (Module-Lattice-Based Key-Encapsulation Mechanism)
- **Origin:** CRYSTALS-Kyber, standardized Aug 2024
- **Purpose:** Key exchange for quantum-resistant secure channels
- **Security levels:** ML-KEM-512 (NIST SL1), ML-KEM-768 (SL3), ML-KEM-1024 (SL5)
- **Status:** Production-ready; hybrid TLS 1.3 deployment ongoing

### FIPS 204 — ML-DSA (Module-Lattice-Based Digital Signature Algorithm)
- **Origin:** CRYSTALS-Dilithium, standardized Aug 2024
- **Purpose:** Quantum-resistant digital signatures for agent authentication
- **Security levels:** ML-DSA-44/65/87 matching NIST SL1/3/5
- **Status:** Production-ready; enterprise migration phase 2025-2027

### FIPS 205 — SLH-DSA (Stateless Hash-Based Digital Signature Algorithm)
- **Origin:** SPHINCS+, standardized Aug 2024
- **Purpose:** Quantum-resistant backup signature scheme (hash-based, lattice-independent)
- **Key property:** Security based on hash function assumptions, provides cryptographic diversity
- **Status:** Production-ready; recommended as fallback for ML-DSA

## Enterprise PQC Migration (2026 State)
- **Harvest-now-decrypt-later threat:** Data encrypted today with RSA/ECDH is at risk from future quantum computers
- **Timeline:** NIST recommends hybrid deployment (classical + PQC) through 2030 minimum
- **Adoption:** Python PQC libraries (OQS) widely available; TLS 1.3 hybrid modes shipping in Q2 2026
- **Reference:** NIST CSRC PQC migration guide, programming-helper.com 2026 guide, cuilabs.io 2026 analysis

## AI Agent Protocol Security Gap (Mid-2026 Assessment)

### MCP (Model Context Protocol)
- **Current security model:** Transport-layer (TLS), no PQC-specific provisions
- **Risk:** MCP servers indexed on Glama registry (19,831+ servers) lack PQC key negotiation
- **Gap:** No PQC migration path documented in MCP 2026 roadmap

### A2A (Agent2Agent Protocol)
- **Current security model:** Apache 2.0 licensed; Linux Foundation hosted; 150+ supporting orgs as of Apr 2026
- **Risk:** Agent discovery and interaction negotiation lack quantum-resistant authentication
- **Gap:** A2A v1.0 (2026) does not specify PQC for agent identity verification

### Cross-Cutting Issues
- **Key management for distributed agents:** No standard for PQC key rotation in multi-agent systems
- **Agent delegation chains:** Capability tokens use classical crypto; vulnerable to harvest-now-decrypt-later
- **Scalability:** PQC key sizes (4-8KB for ML-KEM-768) increase agent handshake latency

## Production Readiness Assessment

| Component | PQC Readiness | Timeline |
|-----------|--------------|----------|
| TLS 1.3 hybrid (ML-KEM + X25519) | Shipping Q2 2026 | Now-2026 |
| MCP PQC transport | Not specified | Unknown |
| A2A PQC authentication | Not specified | Unknown |
| Agent delegation tokens | Classical only | 2027+ |
| Distributed key management | Research phase | 2028+ |

## Strategic Assessment
- **PQC is table-stakes for 2026 infrastructure** — NIST standards finalized, migration underway
- **AI agent protocols lag PQC adoption** — MCP and A2A lack PQC integration
- **Harvest-now-decrypt-later applies to agent communications** — sensitive agent interactions today could be decrypted tomorrow
- **Key management is the unsolved bottleneck** — not the crypto itself, but rotating keys across distributed agent fleets

## Cross-Domain Links
- [ai-agent-interoperability-protocols-draft](ai-agent-interoperability-protocols-draft.md) — MCP/A2A protocol specifications
- [ai-agent-delegation-security](ai-agent-delegation-security.md) — Capability tokens and delegation chains
- [post-quantum-ml](post-quantum-ml.md) — PQC for ML model protection
- [privacy-and-cryptography](privacy-and-cryptography.md) — Cryptographic primitives overview

## References
- [1] NIST CSRC Post-Quantum Cryptography: https://csrc.nist.gov/projects/post-quantum-cryptography
- [2] NIST FIPS 203/204/205 finalized Aug 2024
- [3] PQC 2026 Enterprise Guide: https://www.programming-helper.com/tech/post-quantum-cryptography-2026-nist-standards-migration
- [4] Cuilabs PQC 2026 Guide: https://www.cuilabs.io/articles/pqc-2026-guide
- [5] MCP 2026 Roadmap: https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/
- [6] A2A Protocol v1.0 (Linux Foundation, 2026)
