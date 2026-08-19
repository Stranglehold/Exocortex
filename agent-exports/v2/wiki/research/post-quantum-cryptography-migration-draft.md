---
Status: DRAFT
Created: 2026-07-08
Last Updated: 2026-07-08
Tags: #cryptography #post-quantum #migration #NIST #critical-infrastructure
---

# Post-Quantum Cryptography: Migration Challenges and Timeline

## Overview

Post-quantum cryptography (PQC) refers to cryptographic algorithms that are secure against both classical and quantum computers. With NIST''s standardization of the first PQC algorithms in 2024-2025, organizations now face the challenge of migrating from classical cryptography (RSA, ECC) to quantum-resistant alternatives.

This page covers the technical, organizational, and timeline challenges of PQC migration, with a focus on practical implementation considerations.

## NIST Standardized Algorithms

### FIPS 203 - ML-KEM (Module-Lattice-Based Key Encapsulation Mechanism)
- Based on Kyber, a lattice-based KEM
- Replaces RSA and DH for key exchange
- Three security levels: ML-KEM-512, ML-KEM-768, ML-KEM-1024
- Performance: Faster than RSA for key generation and encapsulation

### FIPS 204 - ML-DSA (Module-Lattice-Based Digital Signature Algorithm)
- Based on Dilithium, a lattice-based signature scheme
- Replaces ECDSA and EdDSA for digital signatures
- Three security levels: ML-DSA-44, ML-DSA-65, ML-DSA-87
- Performance: Signature generation faster than ECDSA, verification comparable

### FIPS 205 - SLH-DSA (Stateless Hash-Based Digital Signature Algorithm)
- Based on SPHINCS+, a hash-based signature scheme
- Replaces ECDSA/EdDSA for long-term signature security
- Only one security level: SLH-DSA-SHA2-128s, -128f, -192, -256
- Performance: Slower than lattice-based, but with strongest security guarantees

## Migration Challenges

### Technical Challenges

1. **Hybrid Deployments**
   - Running classical and PQC algorithms simultaneously during transition
   - Increased ciphertext/signature sizes (ML-KEM-768: ~1KB vs RSA-2048: ~256 bytes)
   - Performance overhead in resource-constrained environments

2. **Protocol Integration**
   - TLS 1.3 extensions for PQC (draft-ietf-tls-hybrid-design)
   - SSH protocol updates
   - VPN and IPsec adaptations
   - Code signing and certificate migration

3. **Legacy System Compatibility**
   - Embedded systems with limited computational resources
   - IoT devices with constrained memory
   - Legacy cryptographic hardware (HSMs, smart cards)

4. **Cryptographic Agility**
   - Designing systems that can swap algorithms without major rewrites
   - Managing multiple algorithm versions during transition
   - Key management for hybrid schemes

### Organizational Challenges

1. **Inventory and Assessment**
   - Cataloging all cryptographic dependencies
   - Identifying systems that use RSA/ECC
   - Prioritizing migration based on sensitivity and exposure

2. **Testing and Validation**
   - Ensuring PQC implementations are correct
   - Performance benchmarking in production environments
   - Security auditing of PQC code

3. **Training and Expertise**
   - Building internal PQC knowledge
   - Understanding trade-offs between different PQC algorithms
   - Managing hybrid deployment complexity

4. **Supply Chain Coordination**
   - Coordinating with vendors for PQC-ready products
   - Updating third-party dependencies
   - Managing certificate authority transitions

## Timeline and Roadmap

### Current State (2024-2026)
- NIST has standardized the first PQC algorithms
- Early adopters are testing hybrid deployments
- Major tech companies (Google, Microsoft, Apple) are implementing PQC in browsers and OS
- TLS 1.3 PQC extensions are in draft/standardization

### Near-Term (2026-2028)
- Increased adoption in enterprise environments
- Certificate authority migration to PQC
- Regulatory guidance and compliance requirements emerging
- Legacy system retirement or PQC adaptation

### Long-Term (2028-2035)
- Full migration expected for most systems
- Classical cryptography phased out for new deployments
- Legacy systems with PQC adaptations or decommissioned
- Quantum computers capable of breaking RSA-2048 may emerge

## Critical Infrastructure Considerations

### Power Grid and Utilities
- SCADA/ICS systems with long lifespans (20-30 years)
- Need for backward compatibility with legacy protocols
- Safety-critical systems requiring extensive validation

### Financial Systems
- High transaction volumes requiring performance
- Regulatory compliance requirements
- Interbank communication protocols

### Healthcare
- Long-lived patient records requiring long-term confidentiality
- Medical device security
- HIPAA and privacy regulations

### Government and Defense
- Classified information protection
- Long-term secrecy requirements (50+ years)
- International interoperability

## Cross-Domain Connections

- **Critical Infrastructure Security**: PQC migration is essential for protecting SCADA/ICS systems
- **Privacy and Cryptography**: PQC enables long-term privacy guarantees
- **Hardware and Physical Computing**: Edge devices need efficient PQC implementations
- **AI and Machine Learning**: PQC can protect training data and model weights

## Open Questions

1. What is the optimal hybrid deployment strategy for different system types?
2. How do we handle legacy systems that cannot be upgraded?
3. What are the performance implications of PQC in high-throughput environments?
4. How do we manage the transition period with mixed classical/PQC deployments?
5. What are the long-term security guarantees of lattice-based cryptography?

## References

- NIST FIPS 203, 204, 205 (2024-2025)
- IETF TLS Hybrid Design draft
- CISA PQC Migration Guidance
- ENISA Post-Quantum Cryptography Report

---
*Page created: 2026-07-08 | Status: DRAFT | Next: Deepen with research and examples*
