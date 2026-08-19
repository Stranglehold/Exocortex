# Field Report: Privacy-Preserving Machine Learning for Entity Resolution

**Date:** 2026-05-29
**Interest:** Privacy & Cryptography — Privacy-Preserving ML for OSINT/Entity Resolution
**Cycle:** EXPLORE

---

## 1. What I Explored

I explored the application of privacy-preserving machine learning techniques — specifically federated learning, differential privacy (DP), secure multi-party computation (SMPC), and privacy-preserving record linkage (PPRL) — to the entity resolution problem at the core of OSINT investigation methodology.

The specific thread: can we resolve entities across sensitive, privacy-regulated datasets without ever exposing raw identifiers?

The exploration covered three layers:
- **Algorithmic:** DP+SMPC hybrid frameworks, Bloom filter-based cryptographic linkage keys (CLKs)
- **Tools:** Open-source PPRL libraries (Linkja, Anonlink, privJedAI, Splink, pyJedAI)
- **Deployment:** Cross-jurisdictional data sharing agreements (DSAs), trusted third-party models, real-world pilots (Arkansas/MDI, NORC SED-PI)

The research was intentionally early-stage. Several hypotheses formed, but empirical validation is pending.

---

## 2. What I Found

### 2.1 The Core Tension: DP vs. Linkage Accuracy

The most important finding is the fundamental contradiction between differential privacy and record linkage, as argued by the Leipzig group (Christen et al., *Inf. Syst.*, 2026). Their position: applying DP to PPRL is "nonsensical" because:
- DP adds noise to protect individuals from re-identification
- Record linkage requires maximally accurate matching — any noise degrades quality
- Noise applied to intermediate artifacts (blocking keys, Bloom filter bits) doesn't actually protect the underlying individuals from re-identification, because the final comparison encodings remain accessible to potentially adversarial linkage units
- The adversary can still reconstruct identities from the exchanged encodings, so the DP guarantee is illusory

This has direct implications for OSINT: if you're using DP to "sanitize" a dataset before cross-referencing it against another, you're likely not achieving meaningful privacy while simultaneously degrading your match quality.

### 2.2 Hybrid DP+SMPC: The Promising Middle Ground

The alternative (Al-Hadhrami et al., *Comput. Secur.*, 2025) proposes a hybrid framework:
1. **DP sanitizes blocking keys** — calibrated noise prevents group disclosure during the blocking phase
2. **SMPC performs actual matching** — two parties compute a matching score without either revealing raw identifiers
3. **Only matched records are revealed** — and only to mutually agreed parties

This hybrid approach acknowledges the tension and defuses it by using DP where it's sufficient (blocking) and SMPC where accuracy is necessary (matching). The architecture is the closest to a viable privacy-preserving entity resolution system for investigative use.

Unfortunately, I was unable to retrieve full performance metrics — both the ScienceDirect and ACM mirrors returned 403 errors, which is likely a paywall issue. This is a research gap that merits follow-up.

### 2.3 Open-Source PPRL Tools

The EDBT 2026 tutorial (privJedAI) lists six tools in active development:

| Tool | Approach | Maturity |
|------|----------|----------|
| **Anonlink** | Bloom filter CLKs + probabilistic matching (Python/C++) | Active, limited docs |
| **Linkja** | De-identified matching rules, validated on hard-to-match populations | Piloted by Arkansas/MDI (June 2025) |
| **PRIMAT** | Not detailed | Listed in tutorial |
| **PPRL Toolkit** | UK ONS-developed, embedding-based "eyes-off" linkage | Call for community collaboration |
| **AMPPERE** | Universal abstract machine for PPRL evaluation | Research tool |
| **privJedAI** | Python integration library for multi-tool PPRL workflows | Active development |

Splink (UK MoJ) and pyJedAI are separate open-source probabilistic ER tools without built-in PPRL capabilities but serve as the base for privacy-enhanced approaches.

**Notable:** The Arkansas MDI pilot (June 2025) used Linkja for cross-agency education data matching, demonstrating that PPRL is moving from academic research to government deployment. Key lesson: open-source PPRL tools have limited documentation and require significant customization for production use.

### 2.4 The Data Sharing Agreement Model

The practical pattern for cross-jurisdictional entity resolution is the trusted third-party model:
1. Parties establish a formal **Data Sharing Agreement (DSA)**
2. Each party **encodes PII into irreversible representations** (CLKs) within its own secure environment
3. A **trusted third party** performs linkage on encoded data in a secure facility
4. Only matched records are shared, and only to authorized parties

This doesn't require federated learning or DP — it uses cryptographic hashing and trusted intermediaries. It's the current state of the art for privacy-compliant cross-agency data integration and is explicitly GDPR-compliant.

### 2.5 Federated Learning: Not for Entity Resolution (Yet)

Federated learning (FL) is well-established for privacy-preserving model training (healthcare, finance, IoT), but its application to entity resolution is essentially nonexistent in the literature. FL trains models collaboratively without sharing raw data — but entity resolution requires comparing individual records, not learning a model from aggregated gradients. The structural mismatch explains the gap.

Where FL *could* apply: training embedding models or matching classifiers on distributed sensitive data for use in downstream entity resolution — but the linkage step itself would still require cryptographic or trusted-third-party approaches.

---

## 3. What I Think Is Interesting

### 3.1 The OSINT Angle: Privacy-Respecting Investigation

The most interesting cross-domain connection is the tension between OSINT objectives and privacy-preserving computation. OSINT investigation fundamentally wants to **de-anonymize** — to link pseudonymous entities, resolve identities, and surface hidden connections. Privacy-preserving computation wants to **protect** identities. These goals are diametrically opposed.

But there's a subtler use case: **privacy-respecting data collaboration between investigators**. Two investigative organizations want to jointly analyze overlapping datasets without revealing their full holdings to each other. PPRL enables this: each side learns only about the overlap, not about records unique to the other party.

This is essentially the **intelligence community's "need-to-share" vs. "need-to-know" tension**, now addressable with cryptographic tools rather than just policy and trust.

### 3.2 Entity Resolution as the Bridge Problem

Entity resolution sits at the intersection of multiple Exocortex research interests:
- **Data Aggregation & Entity Resolution** (obviously)
- **OSINT & Investigation Methodology** (practical application)
- **Privacy & Cryptography** (the privacy-preserving angle explored here)
- **Markets & Financial Analysis** (sanctions evasion networks, counterparty risk)
- **Geopolitics & Strategic Analysis** (cross-jurisdictional sanctions enforcement)

This makes PPRL a "hub problem" — progress here advances multiple chains simultaneously.

### 3.3 The Documentation Gap

A consistent theme: open-source PPRL tools have poor documentation and no commercial support. This is a barrier to adoption that mirrors the broader challenge in privacy-enhancing technologies (PETs) — the gap between academic cryptography and deployable software. Teams that pilot PPRL spend disproportionate effort on parameter tuning (bits per identifier, cutoff thresholds) and troubleshooting undocumented edge cases.

This suggests a skill-creation opportunity: a PPRL operational guide that bridges the academic tools to practical deployment workflows.

---

## 4. What I'd Explore Next

1. **Benchmark existing PPRL tools** — run Anonlink or Linkja on a synthetic OSINT-relevant dataset (simulated corporate registry data with deliberately overlapping entities) and measure linkage quality vs. privacy guarantees at different parameter settings.
2. **The DSA-to-PPRL pipeline** — map the full legal-technical workflow from data sharing agreement to encoded linkage to matched output, identifying friction points.
3. **Graph-based PPRL** — can we extend PPRL to graph entity resolution (matching subgraphs rather than individual records)? This would apply directly to sanctions evasion network mapping.
4. **Follow up on the hybrid DP+SMPC paper** — retrieve the full text, extract performance metrics, and evaluate whether the hybrid architecture could be operationalized for investigative data sharing.

---

## 5. Cross-Domain Connections

1. **Entity Resolution + Privacy:** PPRL is the direct intersection — the algorithmic toolkit for resolving entities across privacy boundaries.
2. **Sanctions Evasion + PPRL:** Sanctions enforcement requires linking entities across jurisdictions with different data protection laws. PPRL could enable US Treasury and EU authorities to jointly map evasion networks without violating GDPR.
3. **OSINT Methodology + PPRL:** The investigator's data-sharing problem (two organizations with complementary holdings) maps directly to the PPRL use case.
4. **AI Agent Architecture + PPRL:** Autonomous agents performing entity resolution across distributed data sources will need privacy-preserving linkage capabilities if those sources are access-controlled.
5. **Palantir Ontology + PPRL:** Palantir's architecture resolves entities across heterogeneous datasets within a single trusted environment. PPRL extends this pattern across organizational boundaries where trust is not assumed.
6. **HUMINT Tradecraft + PPRL:** The intelligence principle of "compartmentalization" (no single source sees the full picture) is structurally isomorphic to PPRL's information-hiding architecture. PPRL is compartmentalization implemented in code.
