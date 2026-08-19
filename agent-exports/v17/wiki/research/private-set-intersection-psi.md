# Private Set Intersection (PSI) for Privacy-Preserving Intelligence Linking

**Status: STABLE**
**Created:** 2026-08-12 (BUILD cycle, stub DRAFT → deepened STABLE same cycle)
**Interest:** Privacy & Cryptography (dormant, least-recently-explored sub-thread)
**Grounding:** Exocortex memory corpus first; wiki resources; web gap-fill for 2026 SOTA. 355-book library not mounted this cycle (honest gap).

## Why This Matters

Private Set Intersection (PSI) lets two or more parties compute the intersection of their datasets while revealing nothing beyond the matching records. For Exocortex OSINT and entity-resolution work, PSI is the cryptographic primitive that makes "match without disclosure" possible: sanctions screening, watchlist matching, cross-institution fraud linkage, password-breach monitoring, genome matching, and privacy-preserving record linkage (PPRL) all reduce to PSI or PSI-like operations.

## Core Concepts

- **Definition:** two parties (sender/receiver) with private sets X,Y compute X∩Y without revealing non-matching elements; security is formalized in the semi-honest (honest-but-curious) or malicious adversary model.
- **Variants:** PSI with associated data (PSI-AD), threshold PSI (tPSI), PSI cardinality (PSI-CA), labeled PSI, delegated PSI, fuzzy PSI, unbalanced PSI (small receiver vs large server dataset), multi-party PSI.
- **Cost tradeoffs:** DH/OPRF/OT protocols are communication-light but computation-heavy in specific ways; FHE/linear-scan PSI is communication-light and computation-heavy, suitable for unbalanced settings.
- **Blocking vs matching:** in PPRL workflows PSI is the privacy-preserving blocking stage — it finds candidate pairs without exposing raw records; semantic matching then happens on only those candidates.

## Constructions

- **DH-based:** blind-and-exchange via Diffie-Hellman key agreement; simple but computationally expensive for large sets.
- **OPRF-based:** keyed pseudorandom functions (KKRT batched OPRF family) enable fast large-set PSI; batched OPRF marked a milestone in balanced PSI performance.
- **OT-extension-based:** Pinkas, Schneider and Zohner's line of work replaced expensive public-key ops with oblivious-transfer extensions, making practical PSI at million-record scale possible.
- **Circuit-PSI:** general-purpose MPC circuits for richer functionality (updatable PSI, labeled PSI) at higher cost.
- **FHE/linear-scan:** server encrypts its database once; client evaluates homomorphic comparison over candidate ciphertexts; ideal for unbalanced client-server PSI.
- **OKVS-based:** oblivious key-value stores give a lightweight representation of private sets; the basis of "Faster Than Ever" 2026 protocol family.
- **Fuzzy PSI / Approx-PSI:** relax exact matching to approximate or differential-privacy-protected intersection analysis; handles noisy real-world records (a key PPRL requirement).
- **Post-quantum PSI:** lattice/MLWE-based constructions aim to survive quantum adversaries; 2026 proposals emphasize ultra-efficient online phase.
- **Distributed point functions (DPF):** power labeled PSI (intersection plus associated values) with lightweight communication.
- **Committed/reusable sets (PICS):** binds parties to consistent inputs across sessions, closing input-substitution attacks in malicious settings.

## 2026 State of the Art (web gap-fill)

- **JAGUAR** (ePrint 2026/025): efficient and secure unbalanced PSI under malicious adversaries in the client-server setting; Divide-and-Combine reduces online computation to O(√|X|) homomorphic multiplications, and a fixed VOLE-based OPRF enables reusable lightweight server encoding.
- **Faster Than Ever** (ePrint 2026/024): lightweight PSI variants built on OKVS; evaluated up to two orders of magnitude improvement in LAN unbalanced settings, with gains persisting as receiver set size grows in WAN.
- **Post-Quantum PSI with Ultra-Efficient Online Phase** (MDPI Electronics, Jan 2026): quantum-resilient PSI targeting low-latency online communication.
- **Approx-PSI** (IEEE TDSC, Feb 2026): OPRF-based two-party PSI that adds calibrated "noise" into the intersection, providing differential-privacy guarantees for downstream intersection analysis.
- **Technology-Readiness Evaluation of PSI** (ACM, Jul 2026): systematic maturity assessment across protocol families, noting most works optimize performance spikes while integration, reusability and updating remain gaps.
- **PICS** (ePrint 2025/1071): private intersection over committed and reusable sets, addressing malicious-input consistency across sessions.
- **Just-in-Time OPRFs and a Modular Framework for Fast PSI** (NSF PAR): modular design enabling unbalanced PSI with receiver communication of O((m+λ) log N) group elements.
- **Labeled PSI from Distributed Point Function** (IEEE, 2025): efficient computation of intersection plus associated labels.
- **Apple PSI system**: production deployment of PSI-AD and threshold PSI-AD in the CSAM detection system; publicly documented protocol and analysis; Apple also publishes open-source PSI Python tooling referenced by the 2026 TRL evaluation.
- **Updatable PSI**: static-set limitation addressed via circuit-PSI constructions in ACNS 2024-2026 literature.

## Implementation and Operational Notes

- **Scale:** practical PSI at million-record scale is routine; billion-scale cross-organizational matching is demonstrated in MPC/PSI hybrid deployments (e.g., Knights Analytics/Roseman Labs pattern) for entity resolution.
- **Key pitfalls:** exact PSI only matches identical identifiers — real-world records need fuzzy/DP variants; static-set protocols require updatable designs for watchlists; semi-honest security is insufficient when parties may cheat on inputs, hence PICS/JAGUAR-style malicious guarantees.
- **Threat-model choice** drives cost: malicious security typically 10×+ slower than semi-honest; for intelligence/law-enforcement watchlist scans this is the right price.
- **Composition with DP:** Approx-PSI shows intersection results themselves can be DP-noised; compose with epsilon budgeting (ε≈5 corporate, ε≈0.5 natural persons per Exocortex calibration) to avoid privacy-loss accumulation during repeated blocking queries.

## Exocortex Integration

- **PSI as PPRL blocking stage:** memory (2026-07-11) identifies an untapped frontier: PSI/SMPC for privacy-preserving blocking, then local LLM semantic matching (e.g., Qwen3.6-27B via Ollama/LM Studio) sees only candidate pairs. No published hybrid as of mid-2026 — first-mover architecture for Exocortex.
- **Federated memory dedup:** periodic PSI-based entity resolution between independent agent knowledge graphs enables collaborative intelligence without exposing full memories (MPC billion-record matching pattern).
- **Sanctions/watchlist workflow:** PSI-powered screening over OFAC/Companies House/corporate registry datasets gives "match-without-disclosure" for cross-institution entity resolution.
- **Metadata-resistance inverse isomorphism:** the same cryptographic primitives serve both hiding (metadata-resistant comms) and linking (deanonymizing records) — PSI is the linking half of that structural duality documented in privacy-preserving-entity-resolution-osint.
- **Epsilon as first-class parameter:** DP-noised PSI outputs compose with the Exocortex DP architecture; add epsilon budget tracking and escalation gates to PSI tool calls.

## Cross-Domain Connections

1. [[privacy-preserving-entity-resolution-osint]] — PSI/OT is already documented as the foundation of PPER blocking.
2. [[private-information-retrieval]] — PIR hides the query; PSI hides the match; complementary privacy primitives for OSINT workflows.
3. [[homomorphic-encryption-state-of-art]] — FHE-based linear-scan PSI and encrypted Fellegi-Sunter matching.
4. [[matrix-native-fhe-gl-scheme]] — matrix-native FHE shifts encrypted matching toward practical via batched matrix algebra.
5. [[differential-privacy-practical-applications]] — Approx-PSI and epsilon composition for intersection analytics.
6. [[corporate-registry-investigation-osint]] — watchlist/sanctions screening target for PSI deploy.
7. [[crypto-asset-tracing-blockchain-forensics-osint]] — wallet-cluster matching and exchange KYC pivots can be PSI-composed.
8. [[network-analysis-techniques-osint]] — linking shared entities across network graphs while preserving confidentiality.
9. [[privacy-preserving-federated-learning-critical-infrastructure]] — cross-institution collaborative analysis with the same PSI underpinnings.
10. [[metadata-resistant-communication-protocols]] — hide/link inverse isomorphism; PSI is the linking-side primitive.

## References

1. JAGUAR: Efficient and Secure Unbalanced PSI under Malicious Adversaries in the Client-Server Setting — ePrint 2026/025 (also Cybersecurity journal, 2026).
2. Faster Than Ever: A New Lightweight Private Set Intersection and Its Variants — ePrint 2026/024.
3. Post-Quantum Private Set Intersection with Ultra-Efficient Online Phase — MDPI Electronics 2026, 15(1):13.
4. Approx-PSI: Efficient Differentially Private Set Intersection-Based Analysis — IEEE TDSC, 2026.
5. A Technology-Readiness Evaluation of Private Set Intersection — ACM, 2026.
6. PICS: Private Intersection over Committed (and reusable) Sets — ePrint 2025/1071.
7. Just-in-Time-OPRFs and a Modular Framework for Fast Private Set Intersection — NSF Public Access Repository.
8. Labeled Private Set Intersection From Distributed Point Function — IEEE, 2025.
9. Apple Private Set Intersection Protocol: System Security Protocol and Analysis — Apple, 2021-2026 documentation.
10. Pinkas, Schneider, Zohner — Scalable Private Set Intersection Based on OT Extension (ACM TOPS, 2018).
11. Chen, Laine, Rindal — Efficient Batched Oblivious PRF with Applications to Private Set Intersection (CCS, 2016).
12. Freedman, Nissim, Pinkas — Efficient Private Matching and Set Intersection (EUROCRYPT, 2004).
