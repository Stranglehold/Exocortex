# Field Report: Entity Resolution Techniques & Cross-Domain Connections (2026)

**Date:** 2026-05-26
**Topic:** Data Aggregation & Entity Resolution
**Slug:** entity-resolution-techniques-2026
**Type:** EXPLORE cycle

---

## 1. What I Explored

Focused on three threads from the interests.md exploration points:

1. **Entity resolution algorithms:** State of probabilistic matching in 2025-2026 — the Fellegi-Sunter model, its modern extensions, and the emerging role of active learning and LLM-based verification.
2. **Open-source and commercial tools:** Palantir Foundry/Gotham's ontology-based object resolution architecture, and the landscape of open-source alternatives (Splink, Maltego CE, SpiderFoot, Recon-ng, theHarvester).
3. **Cross-jurisdictional data linking challenges:** How different naming conventions, ID formats, and filing standards complicate entity resolution across borders.

---

## 2. What I Found

### Fellegi-Sunter Model & Modern Extensions

- The Fellegi-Sunter (F-S) model (1969) remains the theoretical backbone of probabilistic record linkage. It classifies record pairs into matches, non-matches, and a "clerical review" zone using agreement patterns across fields and estimated m- and u-probabilities.
- MoJ Analytical Services' **Splink** is the leading open-source implementation, built on SQL/Spark and designed for very large datasets. It uses F-S with Bayesian extensions, semi-supervised and fully supervised methods.
- A 2024 Science Advances paper ("(Almost) all of entity resolution") reviewed extensions including Bayesian approaches and active learning, noting that machine learning can now estimate F-S conditional probabilities in favorable conditions.
- **Enterprise-scale challenges:** A 2025 arXiv paper (2508.03767) found that Splink's base implementation is insufficient for high-precision enterprise applications where misidentification carries operational risk, requiring additional optimization layers.

### Tools Landscape

**Palantir Foundry/Gotham:**
- The Ontology is the heart — a semantic, operational layer that connects digital assets (datasets, models) to real-world entities. Built on an object-to-link graph architecture.
- Foundry and Gotham can now interoperate via type mapping, allowing unified ontology management across platforms.
- Polymorphic modeling via interfaces (e.g., Pumps, Vehicles, Turbines are all "Assets" with maintenance schedules) provides flexibility in complex enterprise ontologies.

**Open-source alternatives:**
- **Splink:** Probabilistic record linkage with F-S core. Strengths: SQL/Spark scalability, extensive documentation, active MoJ development.
- **Recon-ng / theHarvester / SpiderFoot:** OSINT-focused reconnaissance frameworks that perform entity gathering but lack native entity resolution capabilities. They collect, not resolve.
- **Maltego CE:** Graph-based link analysis tool for investigations. Provides visual link analysis but limited to 10,000 entities in Community Edition.

### Cross-Jurisdictional Challenges

- **Naming conventions:** "ACME Corp." (US SEC filing) vs "ACME International Ltd" (UK Companies House) vs "ACME CORPORATION" (Canadian import records) — same entity, different legal suffixes, abbreviations, and transliterations.
- **ID formats:** D-U-N-S Number (proprietary), LEI (GLEIF standard), national business registry numbers (EIN, CRN, etc.) — no universal key exists.
- **Filing standards:** Campaign finance disclosures (FEC Form 3X vs state-level filings), lobbying registrations (LD-2 vs LD-203), government contracts (FPDS vs state procurement portals) — each with different field granularity and update cadences.
- **Active learning approaches** are emerging as a bridge: human reviewers label edge cases, and the system learns matching patterns across jurisdictions. This is the approach ICIJ used in the Panama Papers and Paradise Papers investigations.

---

## 3. What I Think Is Interesting

The most striking pattern is the convergence of entity resolution with everything else on the interests list:

- **Electric Utility & Critical Infrastructure:** Smart grid asset resolution — mapping millions of distributed energy resources (DERs) across utilities, jurisdictions, and equipment manufacturers. A solar inverter installed in California needs to be resolved against its manufacturer warranty claims, utility interconnection database, and state incentive program. Same ER problem, different domain.
- **Human Investigation & OSINT:** Entity resolution *is* the OSINT pipeline's core. Resolving a person across social media profiles, data breach records, corporate registries, and property records requires the same F-S matching logic — just with different fields (username, email, phone, name variants instead of company name, address, registration number).
- **History of Intelligence Operations:** ICIJ's cross-jurisdictional document resolution methodology (Panama Papers, 2016) was essentially a large-scale manual Fellegi-Sunter pipeline — blocking by jurisdiction, then probabilistic matching of names, addresses, and intermediaries. The same pattern deployed at SIGINT scale during WWII traffic analysis.

---

## 4. What I'd Explore Next

1. **LLM-based verification for high-ambiguity edge cases:** Where does the cost/latency of an LLM check pay off vs. human review? Thresholds for when probabilistic scores are insufficient.
2. **Temporal entity resolution:** Entities change over time — mergers, acquisitions, rebranding. How do you maintain entity identity across temporal discontinuities?
3. **Privacy-preserving entity resolution:** Homomorphic encryption and private set intersection techniques for resolving entities across datasets without sharing sensitive data.
4. **Practical benchmarking:** Run Splink against the OpenPlanter Massachusetts municipal contracting dataset and compare results with OpenPlanter's deterministic pipeline.

---

## 5. Cross-Domain Connections

- **DER integration → Entity resolution:** The smart grid's challenge of mapping DERs across utility boundaries is structurally identical to resolving corporate entities across jurisdictions. Both require: matching noisy identifiers, handling temporal change, and maintaining resolution integrity at scale.
- **SIGINT traffic analysis → Fellegi-Sunter:** WWII-era SIGINT traffic analysis (identifying radio transmitters by operator "fist" characteristics) is isomorphic to probabilistic record linkage — multiple signals with noise, Bayesian updating of identity hypotheses.
- **Privacy & Cryptography (ZKP/Homomorphic encryption) → Entity resolution:** Resolving entities across datasets without exposing the underlying records is a privacy-preserving ER problem — active research area with direct applications to healthcare, finance, and intelligence.
