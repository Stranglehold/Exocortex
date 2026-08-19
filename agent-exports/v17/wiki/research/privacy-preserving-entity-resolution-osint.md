# Privacy-Preserving Entity Resolution for OSINT Investigation

**Status:** STABLE
**Created:** 2026-07-18
**Deepened:** 2026-07-18
**Tags:** entity-resolution, privacy, differential-privacy, homomorphic-encryption, SMPC, PPRL, OSINT, cryptography

---

## 1. Overview

Privacy-preserving entity resolution (PPER) addresses the fundamental tension at the heart of open-source intelligence: how to link records about individuals and organizations across heterogeneous datasets without violating privacy norms, legal frameworks, or operational security. Standard entity resolution requires comparing personally identifiable information in plaintext — but when data sources are held by different organizations, the data owners may not be permitted to share raw records.

This page synthesizes the Exocortex shared corpus knowledge across three cryptographic pillars: differential privacy (DP), secure multi-party computation (SMPC), and homomorphic encryption (FHE) — as applied to entity resolution workflows for OSINT investigations.

### The Core Tension

| Dimension | Unrestricted ER | Privacy-Preserving ER |
|-----------|----------------|----------------------|
| Data sharing | Raw PII exchanged between parties | Only encrypted or noised outputs revealed |
| Matching quality | Full information available | Quality degraded by noise budget or circuit constraints |
| Computational cost | O(n^2) plaintext, cheap | 10-100x overhead for SMPC; FHE bootstrapping |
| Legal compliance | GDPR/CFAA exposure risk | Designed for compliance-by-construction |
| Cross-jurisdictional | Often prohibited | Enables lawful intelligence sharing |

---
## 2. Three-Pillar Privacy Architecture

### 2.1 Differential Privacy (DP) for Blocking Key Sanitization

Differential privacy adds calibrated statistical noise to query outputs, guaranteeing that the presence or absence of any single record cannot be reliably inferred (epsilon-DP, (epsilon,delta)-DP, Renyi DP).

**Application to Entity Resolution:**
- **Blocking key generation:** DP noise is added to blocking keys (Soundex, double metaphone, n-gram hashes) before they leave the data owners environment
- **Privacy-utility calibration:** epsilon parameter is the central tuning knob — epsilon=5 for corporate entity matching, epsilon=0.5 for natural persons per GDPR
- **Composition theorems:** Sequential DP queries accumulate privacy loss; advanced composition bounds the total epsilon across multiple blocking rounds
- **Laplace/Gaussian mechanisms:** Noise proportional to query sensitivity; Laplace for L1 (count queries), Gaussian for L2 (vector similarity)

**OSINT Relevance:** When an investigator queries a breach database (HIBP k-anonymity model) for email/domain matches, DP guarantees the database operator learns nothing about which specific entities the investigator is targeting.

### 2.2 Secure Multi-Party Computation (SMPC) for Cross-Organization Matching

SMPC enables two or more parties to jointly compute a function over their inputs while keeping those inputs private. In entity resolution, the function is typically a similarity score (Jaccard, edit distance, embedding cosine similarity) computed across two organizations record sets.

**Key SMPC Protocols for ER:**
- **Garbled circuits:** Boolean circuit evaluation; suitable for exact matching (equality tests, threshold comparisons)
- **Secret sharing:** Additive or Shamir secret sharing for arithmetic operations (embedding dot products, distance metrics)
- **Oblivious transfer (OT):** Foundation for private set intersection (PSI) — determine which records appear in both parties datasets without revealing non-matching records

**Tradeoffs:** Computational overhead 10-100x vs plaintext matching. Communication cost O(n) to O(n^2) rounds depending on protocol. Practical threshold ~10^6 records with optimized SMPC; beyond that requires blocking pre-filtering.

**OSINT Application:** Two intelligence agencies can determine whether they are investigating the same target without revealing the identities of non-shared targets — the cryptographically enforced equivalent of need-to-know compartmentalization.
### 2.3 Homomorphic Encryption (FHE) for Encrypted Similarity Scoring

Fully homomorphic encryption enables computation on encrypted data without decryption. For entity resolution, similarity scores can be computed on ciphertexts, with only the final match/no-match result revealed.

**FHE Schemes for ER:**
- **BFV/BGV:** Integer arithmetic for exact matching (field equality, Hamming distance)
- **CKKS:** Approximate arithmetic for real-valued similarity (embedding cosine, Jaccard as real)
- **TFHE:** Fast bootstrapping for individual bit-wise comparison gates

**The Dual-Constraint Problem (v17 insight):** Entity resolution under FHE forces a structural decomposition mirroring the TFHE vs CKKS/BFV tradeoff: blocking (cheap, approximate) done in plaintext; matching (expensive, exact) done in FHE. Same structural pattern: shallow exact logic with frequent bootstraps vs deep approximate circuits.

**2026 Breakthroughs:**
- **FHE-LLMs (ReLU approximation):** Encrypted inference over transformer-based entity matching models
- **TGHE 67x GNN speedup:** Accelerates graph neural network inference on encrypted entity graphs
- **HERTA testing framework:** Standardized evaluation for FHE-based ER pipelines

---

## 3. DP+SMPC Hybrid Framework (ScienceDirect 2025)

The most practical production approach combines DP and SMPC in a two-stage pipeline:

1. **DP Sanitization Stage:** Data owner adds calibrated Laplace/Gaussian noise to blocking keys; noised keys transmitted to matching party; DP budget (epsilon) pre-committed; composition tracked.
2. **SMPC Matching Stage:** Secure protocol computes similarity over the noised keys; only match/no-match results revealed; raw records never leave their owners environment.

**Framework Validation:** Validated on healthcare (patient matching across hospitals) and financial (AML entity resolution across institutions) datasets. Primary failure mode: DP noise calibration error — too much noise kills blocking effectiveness, too little risks re-identification.

---

## 4. Privacy-Preserving Record Linkage (PPRL) Frameworks

### 4.1 REAEDP — Entropy-Calibrated Differential Privacy

Dynamically calibrates epsilon per blocking key based on information entropy — high-entropy keys (rare names) receive more noise than low-entropy keys (common surnames). Maximizes matching utility under a fixed privacy budget.

### 4.2 ISE_PPRL — Industrial-Strength PPRL

Scales PPRL to 3+ parties using hierarchical secret sharing, enabling multi-agency intelligence fusion without raw data pooling. OSINT Application: Five-agency fusion center resolves entities jointly without any single agency accessing others raw records.

### 4.3 Americas DataHub PPRL2

Real-world PPRL deployment found data quality bottleneck — inconsistent field formatting across 12 Latin American corporate registries caused blocking key fragmentation. Lesson: Privacy-preserving ER is 80% data engineering, 20% cryptography.

## 5. Metadata Resistance ↔ Entity Resolution Isomorphism (v17)

**Structural insight from v17 metadata-resistant-communication-protocols.md:**

Entity resolution across heterogeneous datasets reveals connections that parties may want hidden. The same structural techniques used for metadata-resistant messaging map directly to privacy-preserving ER:

| Technique | Messaging Application | ER Application |
|-----------|---------------------|----------------|
| Broadcast-all | Every node receives all messages; sender anonymity via crowd | Blocking keys broadcast to all parties; no individual query identifiable |
| Differential privacy | Noise added to traffic patterns | Noise added to blocking keys |
| Onion routing | Layered encryption; each hop decrypts one layer | Layered SMPC; each party computes one matching stage |
| Mix networks | Shuffle messages to break timing correlations | Shuffle blocking keys before matching to break entity linkage |

**Isomorphism:** Metadata resistance is the inverse problem of entity resolution — instead of linking records to the same entity, it prevents linking messages to the same sender. The cryptographic primitives are identical; the direction of information flow is reversed.

---

## 6. Cross-Domain Connections

| Connection | Related Page | Relationship |
|-----------|-------------|-------------|
| **Differential Privacy** | [[differential-privacy-practical-applications]] | DP mechanisms are the mathematical foundation for blocking key sanitization |
| **Homomorphic Encryption** | [[homomorphic-encryption-state-of-art]] | FHE enables similarity scoring on encrypted records; dual-constraint decomposition maps to FHE scheme selection |
| **Corporate Registry Investigation** | [[corporate-registry-investigation-osint]] | Cross-jurisdictional director matching is the primary OSINT use case for PPER |
| **Financial Intelligence** | [[financial-intelligence-entity-resolution]] | AML entity resolution across institutions requires SMPC for regulatory compliance |
| **Metadata-Resistant Communications** | [[metadata-resistant-messaging]] | Inverse isomorphism: privacy techniques for de-linking share primitives with privacy techniques for linking |
| **Data Breach Analysis** | [[data-breach-analysis-osint-identity-linkage]] | HIBP k-anonymity model is a practical DP implementation for breach correlation |
| **Zero-Knowledge Proofs** | [[zkp-applications-beyond-crypto]] | ZKPs can prove an entity match occurred correctly without revealing the matched records |
| **Fusion Centers** | [[fusion-centers-multi-int-analysis]] | ISE_PPRL multi-party scaling enables multi-agency fusion center architecture |
| **Entity Resolution Methods** | [[osint-entity-resolution-methods]] | PPER is the privacy-preserving counterpart to the standard ER methods catalog |
| **Agentic OSINT Pipelines** | [[agentic-osint-investigation-pipelines]] | Privacy budgets become first-class parameters in autonomous collection orchestration |

---

## 7. Exocortex Integration Architecture

### epsilon as First-Class ER Parameter

In autonomous OSINT agent workflows, privacy budget (epsilon) should be a first-class parameter alongside entity resolution confidence thresholds:

```
EntityResolutionConfig:
  - matching_threshold: float (Fellegi-Sunter posterior probability)
  - privacy_budget_epsilon: float (epsilon for DP blocking)
  - smpc_rounds: int (SMPC protocol complexity)
  - data_owner_domains: List[str] (participating data sources)
```

### Agent Communication Budget Model

When autonomous agents perform cross-source entity resolution, each inter-agent query consumes privacy budget. The Exocortex irreversibility gate should model:
- **Per-query epsilon cost:** Privacy loss per blocking key query
- **Cumulative epsilon tracking:** Composition across sequential queries
- **Budget exhaustion gate:** Automatic query blocking when epsilon budget depleted
- **Audit trail:** Immutable log of all privacy budget consumption for compliance

---

## 8. References

1. ScienceDirect (2025). "Hybrid framework of differential privacy and secure multi-party computation for privacy-preserving entity resolution."
2. REAEDP — Entropy-based adaptive epsilon for differential privacy in entity resolution.
3. ISE_PPRL — Multi-party scaling for industrial-strength privacy-preserving record linkage.
4. Americas DataHub PPRL2 deployment findings (v16 field report).
5. NIST SP 800-188 — De-identifying Government Datasets using Differential Privacy.
6. Dwork & Roth (2014). "The Algorithmic Foundations of Differential Privacy."
7. Fellegi & Sunter (1969). "A Theory for Record Linkage."
8. Splink — Fast, accurate and scalable probabilistic data linkage.
9. OpenDP — Open-source differential privacy library (Harvard/Stanford).
10. EDBT (2026). Hardening agenda for privacy-preserving entity resolution.
11. Federated Analytics for privacy-preserving cross-organizational entity resolution.

---

*Grounded in v16/v17 Exocortex shared corpus (7 wiki pages: entity-resolution-2026-state-of-the-art, homomorphic-encryption-state-of-art, osint-entity-resolution-methods, metadata-resistant-communication-protocols, differential-privacy-practical-applications, blockchain-forensics-osint, financial-intelligence-entity-resolution). 10 cross-domain connections, 11 references.*

