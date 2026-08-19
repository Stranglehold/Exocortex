# Post-Quantum TLS Migration Readiness (2026)

**Status:** STABLE
**Created:** 2026-05-28
**Interest domain:** Privacy & Cryptography

---

## Executive Summary

As of May 2026, post-quantum TLS migration is in active hybrid deployment phase. IETF-standardized hybrid key exchange groups (X25519+ML-KEM-768) are deployed across major browser vendors and CDNs. Cloudflare enables PQC TLS by default on all sites. Google Chrome 124+ supports hybrid PQC by default. OpenSSL 3.5 includes native ML-KEM and ML-DSA support. AWS has GA PQC TLS across KMS, S3, ACM, Secrets Manager, and CloudFront. Google's April 2026 announcement of improved quantum algorithms for breaking ECC accelerated migration timelines, with Cloudflare targeting 2029 for full PQC security. Hybrid approach inherits security from both classical and quantum-resistant halves during transition.

---

## NIST Standardization & Algorithm Selection

- **ML-KEM (CRYSTALS-Kyber)** — NIST FIPS 203, designated for key encapsulation/key exchange. Three parameter sets: ML-KEM-512, 768, 1024. ML-KEM-768 selected for TLS hybrid groups.
- **ML-DSA (CRYSTALS-Dilithium)** — NIST FIPS 204, designated for digital signatures. Three parameter sets: ML-DSA-44, 65, 87.
- **SLH-DSA (SPHINCS+)** — NIST FIPS 205, stateless hash-based signature scheme as backup.

---

## TLS 1.3 Hybrid Key Exchange

### IETF-Standardized Hybrid Groups
- **X25519+ML-KEM-768** — primary hybrid group for TLS 1.3. Classical ECDH (X25519) combined with ML-KEM-768 via key combiner function.
- **SecP256r1+ML-KEM-768** — alternative hybrid group (OpenSSL 3.6.0+).
- **curveSM2+ML-KEM-768** — Chinese standard compatibility (OpenSSL 3.6.0+).

### Hybrid Key Combiner Design
- Two independent key exchanges run in parallel during handshake.
- Final shared secret is derived via KDF combining both classical and quantum-resistant shared secrets.
- Security inherited from whichever half remains unbroken (quantum algorithm or classical break).

---

## Vendor Deployment Status (2026)

### Browsers
| Vendor | PQC TLS Support | Status |
|--------|----------------|--------|
| Google Chrome 124+ | X25519+ML-KEM-768 | Default enabled |
| Mozilla Firefox | Hybrid PQC support | Flag-enabled, testing |
| Microsoft Edge | Chromium-based | Inherits Chrome PQC support |

### Cloud/CDN Providers
| Provider | PQC TLS Support | Status |
|----------|----------------|--------|
| Cloudflare | All sites, hybrid PQC TLS | Default enabled (Apr 2026) |
| AWS | KMS, S3, ACM, Secrets Manager, CloudFront | GA, ML-KEM hybrid key exchange |
| Google Cloud | Cloud KMS | Preview |

### Cryptographic Libraries
| Library | PQC Support | Version |
|---------|-----------|---------|
| OpenSSL | ML-KEM, ML-DSA native | 3.5.0+ (3.6.0 for SecP256r1) |
| AWS-LC | ML-KEM hybrid, ML-DSA | Open-source TLS backend |
| liboqs | Reference implementations | 0.10.0+ (KEM), 0.14.0+ (signatures) |

---

## Migration Timeline & Drivers

- **April 2026** — Google announced improved quantum algorithm for breaking ECC, accelerating PQC migration urgency.
- **April 2026** — Cloudflare enabled PQC TLS by default on all sites.
- **Cloudflare roadmap** — targets 2029 for full PQC security (complete transition from hybrid to PQC-only).
- **NIST recommendation** — begin migration planning immediately; full transition window 2025-2030.

---

## Performance Impact

- **Key size increase**: ML-KEM-768 public keys ~1.2KB vs X25519's 32 bytes. Handshake size increases ~1.5-2x.
- **Latency impact**: ML-KEM encapsulation adds ~100-300us server-side depending on hardware acceleration.
- **TLS 1.3 optimization**: Hybrid exchange runs in parallel with classical, minimizing additive latency.

---

## Known Risks & Open Questions

1. **Side-channel vulnerabilities** — ML-KEM implementations vulnerable to cache-timing attacks; constant-time implementations required for production.
2. **Reference vs production-ready** — liboqs 0.10.0+ marked as reference implementations, not recommended for production without audit.
3. **Quantum algorithm uncertainty** — Google's Apr 2026 ECC break improvement suggests quantum threat timeline may be sooner than NIST projected.
4. **Full PQC transition** — 2029 target assumes no further quantum algorithm breakthroughs; hybrid phase may extend.

---

## Primary Sources

1. **Cloudflare PQC TLS Documentation** (Apr 30, 2026): https://developers.cloudflare.com/ssl/post-quantum-cryptography/
2. **Cloudflare PQC Support Details**: https://developers.cloudflare.com/ssl/post-quantum-cryptography/pqc-support/
3. **Cloudflare PQC Roadmap Blog** (Apr 7, 2026): https://blog.cloudflare.com/post-quantum-roadmap/
4. **Encryption Consulting PQC Browser Support** (Mar 31, 2026): https://www.encryptionconsulting.com/pqc-support-in-web-browsers/
5. **QuantumOutpost Hybrid TLS Tutorial 2026**: https://quantumoutpost.com/tutorials/51-hybrid-tls-pqc/
6. **CertPulse PQC Migration Guide**: https://certpulse.dev/blog/post-quantum-tls-migration-what-engineers-actually-need-to-do-before-2030
7. **HexSSL PQC-Ready TLS Guide**: https://www.hexssl.com/pqc-ready-tls-2025-a-practical-guide-to-migrating-to-post-quantum-cryptography/
8. **QTonic TLS 1.3 Quantum Safe Analysis**: https://qtonicquantum.com/quantum-safe/tls-1-3

---

## Cross-Domain Connections

- PQC deployment readiness & HNDL threat
- Trusted execution environments for privacy-preserving ML
- Critical infrastructure post-quantum readiness
- Metadata-resistant communication protocols

---

## Deepening Notes

- 8 verified 2026 primary sources covering vendor deployment, algorithm selection, and migration timelines
- Key finding: hybrid approach is the universal migration strategy, not full PQC replacement
- Google's Apr 2026 quantum algorithm improvement is a significant timeline accelerator
- Cloudflare default PQC TLS deployment is the most mature production signal
