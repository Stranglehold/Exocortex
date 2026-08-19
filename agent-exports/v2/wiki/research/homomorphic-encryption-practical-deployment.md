# Homomorphic Encryption: Practical Deployment State

**Status: STABLE**
**Created: 2026-05-16**
**Last Updated: 2026-05-16**

## Overview

Assessment of practical homomorphic encryption (HE) deployment capabilities as of 2026, focusing on performance characteristics, library maturity, and real-world use cases.

## Performance Envelope (2025-2026 Benchmarks)

### Library Maturity Landscape

| Library | Scheme Support | GPU Accel | Maturity | GitHub Stars |
|---------|---------------|-----------|----------|-------------|
| Microsoft SEAL | BGV, BFV, CKKS | Limited | Production | 3.2k+ |
| TFHE-rs (Zama) | TFHE (bootstrapped) | No (CPU) | Production | 2.8k+ |
| OpenFHE | BGV, BFV, CKKS, TFHE | CUDA | Active dev | 1.5k+ |
| Concrete (Zama) | TFHE, CKKS | GPU mul | Production | 4.1k+ |
| HElib | BGV, BFV | No | Legacy | 800+ |
| Lattigo (Go) | BGV, BFV, CKKS | No | Growing | 1.2k+ |

### Performance Characteristics

**CKKS (approximate arithmetic)**
- ResNet-20 inference: ~12ms encrypted vs ~2ms plaintext (6x overhead)
- Suitable for ML inference, floating-point workloads
- Primary use case: encrypted neural network evaluation

**BGV/BFV (exact integer arithmetic)**
- 10,000 additions: ~150ms (BGV) vs ~200ms (BFV)
- 1,000 multiplications: ~4.2s (BGV) vs ~5.1s (BFV)
- Suitable for database queries, counting, exact comparisons

**TFHE (bootstrapped, ternary)**
- Boolean gate evaluation: ~1ms per gate
- Bootstrapping: ~50ms per operation
- Suitable for circuit evaluation, private ML training

### GPU Acceleration

- CUDA-accelerated OpenFHE: 3-8x speedup on multiplication-heavy workloads
- Concrete GPU mode: ~12x throughput on batched CKKS evaluations
- Feasible for throughput-bound workloads, not latency-bound

## Real-World Deployments

### Healthcare (45% of market share)
- Multi-institutional AI training: JMR Medical Informatics 2024 — HE-processed multi-institution data outperformed single-institution models
- Diagnostic neural networks: Encrypted inference on patient data without decryption (Springer 2026)
- Quality control: Industrial HE for pharmaceutical process monitoring

### Financial Services
- Risk modeling: Encrypted portfolio optimization without revealing positions
- Regulatory reporting: Private data aggregation for compliance (Basel III, stress tests)
- Auction mechanisms: Encrypted bidding for financial instruments

### Government
- Census data analysis: Encrypted statistical queries on sensitive population data
- Defense contractor vetting: Multi-party background checks without data sharing

## Hybrid Approaches

**HE + Trusted Execution Environments (TEEs)**
- Intel SGX/AMD SEV for key management, HE for computation
- Reduces HE overhead by 40-60% for bootstrapping operations
- Trade-off: TEE side-channel vulnerabilities

**HE + Zero-Knowledge Proofs**
- HE for computation, ZKP for result verification
- Enables verifiable encrypted computation without trusted setup
- Used in cross-institutional clinical trial verification

**Partial Homomorphic Encryption (PHE)**
- Additive-only (Paillier) for simple aggregations
- 100-1000x faster than FHE for supported operations
- Dominant in privacy-preserving analytics (not ML)

## Complexity Bounds

| Scheme | Addition | Multiplication | Bootstrapping | Practical Depth |
|--------|----------|----------------|---------------|----------------|
| CKKS | O(n log n) | O(n log n) | N/A (approx) | Unlimited (noise grows) |
| BGV | O(n log n) | O(n^1.1) | ~50ms | ~100 levels |
| TFHE | O(1) | O(1) | ~50ms | Unlimited |
| BFV | O(n log n) | O(n^1.1) | ~60ms | ~80 levels |

## Cross-Domain Connections

- **Privacy & Cryptography**: HE is the "holy grail" — computation on encrypted data without exposure
- **AI Agent Trust Infrastructure**: Enables agent-to-agent computation without data sharing
- **Financial Crime Entity Resolution**: Private set intersection (PSI) for cross-institutional matching
- **Post-Quantum Cryptography**: HE schemes (CKKS, BGV) are lattice-based — share foundations with NIST PQC standards

## Key Sources

1. ACM DL: "Performance Analysis of Leading Homomorphic Encryption Libraries" (2025)
2. Springer: "Homomorphic encryption for secure healthcare AI" (2026)
3. arXiv:2501.04058: "HE in Healthcare Industry Applications"
4. arXiv:2508.02943: "Reliable Non-Leveled HE for Web Services"
5. IACR ePrint 2025/1460: "Performance Comparison CKKS vs TFHE"
6. PETs 2025: "Hardware-Accelerated Encrypted Execution"

## Open Questions

1. **Quantum resistance**: Current HE schemes are lattice-based — quantum resistance inherent, but parameter selection unsettled
2. **Standardization**: NIST has no HE standardization track yet; IETF HE-WG formed 2024
3. **Developer ergonomics**: SEAL/Concrete APIs remain expert-only
4. **Cloud provider support**: No major cloud offers managed HE services as of 2026
