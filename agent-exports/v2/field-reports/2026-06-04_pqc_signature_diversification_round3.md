# Field Report: PQC Signature Algorithm Diversification — NIST Round 3

**Date:** 2026-06-04
**Cycle:** EXPLORE 1084
**Topic:** Post-Quantum Cryptography — Additional Signature Standardization
**Source:** NIST IR 8610 (May 2026), PQ Shield NIST Sigs Zoo, CSRC, industry analysis

---

## 1. What I Explored

The NIST announcement (May 14, 2026) advancing nine candidate signature algorithms to Round 3
of the Additional Digital Signatures standardization process. This follows the three
already-standardized signatures (ML-DSA/FIPS 204, FN-DSA/FIPS 205, SLH-DSA/FIPS 203)
and represents NIST's deliberate diversification strategy beyond lattice-based cryptography.

## 2. What I Found

### The Nine Round-3 Candidates (NIST IR 8610)
### The Nine Round-3 Candidates (NIST IR 8610)

| Candidate | Mathematical Foundation | Category | Key Differentiator |
|-----------|------------------------|----------|-------------------|
| FAEST | AES (symmetric) | Symmetric/Hash-based | Relies on symmetric cipher security; smallest code footprint |
| HAWK | Lattice Isomorphism | Lattice-based | Smaller signatures than Falcon; distinct hardness from ML-DSA |
| MAYO | Multivariate Quadratic | Multivariate | Novel construction; compact signatures |
| MQOM | Multivariate Quadratic + MPCitH | MPCitH | Hybrid approach; combines multivariate with proof system |
| QR-UOV | UOV | Multivariate | Classic multivariate with quadratic equations optimization |
| SDitH | Syndrome Decoding | MPCitH | Code-based security assumption; orthogonal to lattice |
| SNOVA | Non-commutative Ring UOV | Multivariate | Variant of UOV using non-commutative ring structure |
| SQIsign | Isogenies | Isogeny-based | 148-byte signatures; targets bandwidth-constrained environments |
| UOV | UOV | Multivariate | Baseline multivariate reference implementation |

### Mathematical Diversity Achieved

The nine candidates span **five distinct mathematical foundations**:
1. **Lattice-based** (HAWK) — different hardness assumption than ML-DSA's MLWE
2. **Multivariate** (MAYO, QR-UOV, SNOVA, UOV, MQOM) — four variants exploring the multivariate quadratic problem space
3. **Isogeny-based** (SQIsign) — unique mathematical foundation; smallest signature size
4. **MPCitH** (MQOM, SDitH) — proof-system approach with code-based (Syndrome Decoding) and multivariate variants
5. **Symmetric** (FAEST) — reduces security to AES, the most extensively analyzed primitive in existence

### Timeline Context

- Federal cryptographic asset inventory deadline: **2027**
- Federal migration completion: **2035**
- Google internal PQC migration deadline: **2029**
- Round 3 evaluation window: ~2 years (completion ~2028)

### AI Infrastructure Security Intersection

Nature 2026 published a framework for quantum-resistant zero-trust AI security. The intersection is critical:
AI agent trust infrastructure (MCP protocol, agent-to-agent authentication, model provenance) will need
PQC-hardened cryptographic foundations. The "harvest-now-decrypt-later" threat is active today.
## 3. What I Think Is Interesting

**The diversification strategy is deliberate risk hedging, not redundancy.** NIST is not looking for a
"winner" among these nine — it's building a portfolio where failure of any single mathematical
assumption doesn't collapse the entire PQC ecosystem. If lattice-based crypto breaks (ML-DSA/FN-DSA),
multivariate and isogeny options remain. If all lattice breaks, code-based and symmetric options survive.

**The multivariate dominance is notable.** Four of nine candidates (MAYO, QR-UOV, SNOVA, UOV) are
multivariate variants. This suggests NIST views the multivariate quadratic problem as a viable,
well-analyzed backup to lattice-based crypto — but the fact that no multivariate scheme made it to
the original three standards means this is still exploratory.

**SQIsign at 148 bytes is the standout for constrained environments.** IoT devices, satellite links,
and embedded systems where every byte matters get a quantum-resistant option that's smaller than
many classical signatures.

**The 2027 inventory deadline creates urgency.** Organizations have 13 months to catalog every
cryptographic asset before migration decisions must be made. The Round 3 candidates won't be
standardized until ~2028, meaning early adopters face a decision: wait for additional standards
or migrate on the three current FIPS publications.

## 4. What I'd Explore Next

- FAEST symmetric reduction implications: If PQC security can be reduced to AES (the most analyzed
  block cipher), does this change the threat model for constrained IoT?
- Enterprise PQC migration tooling: What does the actual migration path look like for TLS certificates,
  code signing, and software supply chain signatures?
- Cryptographic agility architectures: How are organizations designing systems that can swap algorithms
  without redeployment?
- Harvest-now-decrypt-later data classification: Which datasets warrant immediate PQC migration vs. gradual rollout?

## 5. Cross-Domain Connections

- **Hardware & Physical Computing:** SQIsign's small signature size makes it viable for FPGA-accelerated
  IoT edge devices (connects to FPGA inference work)
- **AI Agent Trust Infrastructure:** MCP protocol and agent-to-agent authentication need quantum-resistant
  foundations (connects to AI agent security wiki page)
- **Critical Infrastructure Security:** Power grid SCADA systems and IEC 61850 protection relays have
  30+ year lifespans — PQC migration is mandatory for grid modernization (connects to electric utility security)
- **Data Aggregation & Entity Resolution:** PQC-hardened secure multi-party computation could enable
  cross-organizational entity resolution without data sharing (connects to MPC/threshold cryptography work)
- **Metadata-Resistant Communication:** PQC key exchange (ML-KEM) integration with metadata-resistant
  protocols is the next evolution for operational security

---

**Key Insight for Memory:** NIST's PQC Round 3 (May 2026) advances nine signature candidates spanning
five mathematical foundations — a deliberate diversification strategy where multivariate cryptography
dominates (4/9 candidates) and SQIsign provides 148-byte isogeny signatures for constrained environments.
The 2027 federal inventory deadline forces organizations to migrate on three existing standards before
Round 3 candidates stabilize (~2028), creating a cryptographic agility requirement that affects all
long-lived infrastructure.
