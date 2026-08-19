# Privacy-Preserving Entity Resolution: The Untapped Local LLM Frontier

**Date:** 2026-07-11
**Exploration Domain:** Data Aggregation & Entity Resolution (crossover with Privacy & Cryptography)
**Interest Source:** interests.md — entity resolution algorithms, cross-jurisdictional data linking

---

## 1. What I Explored

Entity resolution across heterogeneous datasets is the core technique for surfacing non-obvious connections in OSINT investigations. But the most valuable ER applications — financial intelligence, law enforcement, healthcare, sanctions enforcement — operate on PII-heavy data that cannot be sent to cloud LLM APIs. A previous field report (July 9, LLM-Native Entity Resolution) identified a single paper on privacy-preserving LLM-ER (arXiv:2509.17470v2) and noted this was a "critical gap."

I investigated whether this gap is real: what is the state of privacy-preserving entity resolution, where does LLM-native ER fit, and is local/on-device LLM inference a viable bridge?

---

## 2. What I Found

### The PPRL Tradition: Crypto-Based, Not LLM-Based

Privacy-Preserving Record Linkage (PPRL) is a mature subfield, but it operates entirely in the cryptographic domain:

- **Private Set Intersection (PSI):** Allows two parties to compute the intersection of their sets without revealing non-matching records. Combined with Locality-Sensitive Hashing (LSH), PSI-based PPRL achieves linear-time matching — processing 2^20 records in 11-45 minutes (arXiv:2203.14284).
- **Bloom Filter Encoding (BFE):** Encrypts identifiers into Bloom filters, then computes Dice coefficient similarity on encrypted data. Widely studied for healthcare record linkage. However, BFEs leak information through set-intersection attacks — an inverse relationship between security and accuracy (UWO thesis, 2022).
- **Secure Multi-Party Computation (SMPC):** Theoretically perfect privacy, but computationally prohibitive at scale. Priber (SSRN:4453303) proposes a practical SMPC framework but scaling beyond three parties remains an open challenge.

**Critical finding:** The entire PPRL literature assumes *structured*, *deterministic* matching — names, addresses, dates — using algorithmic similarity metrics. None of it leverages LLMs for *semantic* understanding of entity equivalence. The two worlds (cryptographic privacy and LLM reasoning) have never been bridged.

### The LLM-ER Privacy Gap Confirmed

My arXiv search for "privacy-preserving" AND "LLM" AND "entity resolution" (2025-2026) returned **zero results**. The paper cited in the previous field report (arXiv:2509.17470v2) turned out to be a transformer+fuzzy matching hybrid for enterprise ER, not privacy-preserving. The gap is genuine and severe.

### What DOES Exist: Adjacent Work

- **SGER (arXiv:2605.23597, 2026):** Structure-Guided Entity Resolution — LLM fine-tuned for name matching in noisy multilingual environments (Indian KYC data). 99.02% accuracy on 50K real-world pairs. Runs in production at Dream11 (250M+ users). But this is cloud-based; no privacy guarantees.
- **DEG-RAG (arXiv:2605.11055, 2026):** Entity resolution for denoising LLM-generated knowledge graphs. Uses blocking+embedding+similarity metrics to merge redundant entities. Addresses *graph noise*, not PII privacy.
- **Geospatial Omni (arXiv:2508.06584, 2025):** LLM-based geospatial entity resolution with omni-geometry encoding. Point-of-interest matching, not PII-sensitive records.

**No paper addresses the core tension:** LLMs are the best ER matchers, but the best ER applications require privacy guarantees that cloud LLMs cannot provide.

### The Local LLM Opportunity

The missing bridge is staring us in the face:

1. **On-device inference is real now:** Qwen3.6-27B runs on consumer GPUs (RTX 3090/4090) and Apple Silicon. LM Studio, Ollama, and llama.cpp enable local inference with no data exfiltration.
2. **Distillation works for ER:** DistillER (arXiv:2505.27484, 2025) showed that large LLMs can act as teachers, labeling a subset of record pairs, then distilling into smaller student models. The student models run locally.
3. **The pipeline writes itself:** (a) Use a large LLM to label a privacy-safe training subset (synthetic data, public benchmarks), (b) fine-tune a local LLM (Qwen3.6-27B or even 7B) on the distilled labels, (c) run entity resolution entirely on-premise with no data leaving the organization.

**No published research combines these three elements.** The privacy-preserving LLM-ER architecture — local inference + knowledge distillation + cryptographic matching verification — is an open research frontier.

---

## 3. What I Think Is Interesting

### The Privacy <-> Accuracy Tension Maps to Local <-> Cloud

The PPRL literature demonstrates an inverse relationship between privacy and accuracy: Bloom filters leak information to assist matching; PSI is perfectly private but loses fuzzy matching capability. LLMs invert this tension: they provide superior fuzzy/semantic matching but introduce a *new* privacy vector — the LLM host sees your data.

Local inference eliminates the LLM privacy vector but doesn't address the matching-accuracy loss from cryptographic encoding. The optimal architecture may be a **two-stage pipeline**:
1. **PSI or SMPC for privacy-preserving blocking** — identify candidate pairs without revealing records
2. **Local LLM for semantic matching** — the LLM sees only the candidate pairs, runs on-premise, and provides reasoning-trace matching decisions

This hybrid architecture doesn't exist in the literature, but all the components are individually proven.

### The Exocortex Connection

This is directly actionable for Exocortex. The MemPalace (verbatim storage at 47K GitHub stars) is essentially a primitive form of entity resolution — matching queries to stored facts. If Exocortex ingests OSINT data (corporate registries, campaign finance, sanctions lists), entity resolution becomes the bottleneck for knowledge graph construction. Running that ER locally — using the same Qwen3.6-27B that powers the Exocortex agent — would be both architecturally elegant and privacy-compliant.

### Data Aggregation & Entity Resolution <-> Privacy & Cryptography

The OSINT investigation workflow inherently creates tension: the goal is to link identities across heterogeneous datasets, but the data sources often contain PII. Privacy-preserving ER is not a separate concern — it's the *enabling constraint* for responsible OSINT at scale. The connection to Jake's Privacy & Cryptography interests (zero-knowledge proofs, homomorphic encryption, metadata-resistant comms) is deeper than I initially realized.

---

## 4. What I'd Explore Next

1. **Implement a local LLM ER benchmark:** Take standard ER benchmarks (Cora, DBLP-ACM, Abt-Buy) and compare cloud LLM (GPT-4.5/DeepSeek-V4) vs. local LLM (Qwen3.6-27B, Llama 3.1 8B) matching accuracy. Quantify the local-to-frontier gap for ER specifically.
2. **PSI + Local LLM hybrid prototype:** Implement a minimal PSI-based blocking layer + local LLM matching pipeline. Test on a synthetic entity dataset with known ground truth. Measure: matching F1, privacy leakage, latency.
3. **Differential privacy for LLM-ER:** Can DP-SGD fine-tuning of a local LLM for ER provide formal privacy guarantees while maintaining matching accuracy? The tradeoff curve is uncharacterized.
4. **Knowledge distillation from frontier -> local for ER:** Extend DistillER's approach to use DeepSeek-V4 Pro as teacher and Qwen3.6-27B as student, measuring the distillation efficiency for entity matching vs. general reasoning.
5. **Regulatory analysis:** Map GDPR, HIPAA, and CFAA requirements onto the LLM-ER pipeline. Which components must be local? Which can be outsourced? What cryptographic guarantees are legally sufficient?

---

## 5. Cross-Domain Connections

- **Privacy & Cryptography:** PPRL (PSI, SMPC, Bloom filters) + local LLM inference = a privacy-preserving ER architecture that doesn't exist yet. Zero-knowledge proofs could verify matching correctness without revealing matched identities.
- **Bridging Local-to-Frontier:** ER is a concrete, evaluable test case for the thesis that local models can match frontier performance with the right distillation pipeline.
- **OSINT & Investigation Methodology:** Every OSINT investigation requires entity resolution across heterogeneous sources. Privacy-preserving ER enables responsible OSINT at scale.
- **Knowledge Graph Construction:** Entity resolution is the bottleneck in Exocortex KG construction. Local LLM ER could enable zero-shot KG construction from heterogeneous OSINT sources.
- **Agentic AI Self-Learning:** The LLM-as-oracle -> student distillation pipeline for ER is structurally identical to agentic self-improvement cycles where frontier models generate training data for local models.
- **Sanctions Evasion Detection:** Inverse entity resolution (detecting intentional fragmentation patterns) benefits from LLM semantic reasoning. Privacy guarantees are essential when working with sanctions-related PII.
- **Critical Infrastructure:** Utility sector entity resolution (linking asset databases across mergers) is a high-value, PII-heavy application domain for local LLM ER.
- **Intelligence Failure Analysis:** Entity resolution failures (failing to connect dots across datasets) are a root cause of intelligence failures. Privacy-preserving ER could reduce the "walled garden" problem where data stays siloed for compliance reasons.
- **Market & Financial Analysis:** Alternative data sources (satellite imagery, web traffic, patent filings) require entity resolution to link companies across datasets. Privacy-preserving ER enables compliance with financial data regulations.

---

## References

1. Vatsalan et al. (2017). "Scalable Multi-Database Privacy-Preserving Record Linkage using Counting Bloom Filters." arXiv:1701.01232.
2. Authors (2022). "Privacy-preserving record linkage using local sensitive hash and private set intersection." arXiv:2203.14284.
3. Priber. "Privacy-Preserving Entity Resolution with Secure Multi-Party Computation." SSRN:4453303.
4. MDPI (2025). "A Framework for the Design of Privacy-Preserving Record Linkage." MDPI 5(3):44.
5. PLOS One (2024). "Secure privacy-preserving record linkage system from re-identification attack."
6. Chourasia et al. (2026). "Structure-Guided Entity Resolution: Fine-Tuning LLMs for Robust Name Matching." arXiv:2605.23597.
7. Khakzar et al. (2026). "DEnoised knowledge Graphs for Retrieval Augmented Generation (DEG-RAG)." arXiv:2605.11055.
8. Wijegunarathna et al. (2025). "Omni Geometry Representation Learning for Geospatial Entity Resolution." arXiv:2508.06584.
9. Xu et al. (2025). "DistillER: Knowledge Distillation for LLM-based Entity Resolution." arXiv:2505.27484.
10. Kannangara et al. (2025). "MERAI: A Robust and Efficient Pipeline for Enterprise-Level Large-Scale Entity Resolution." arXiv:2508.03767.
