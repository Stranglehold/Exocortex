# OSINT Entity Resolution Methods

**Status: STABLE**
**Created: 2026-06-01**
**Last Updated: 2026-06-01**
**Topic Area:** OSINT / Entity Resolution
**Primary Sources: 8 arXiv papers, 5 web sources, 2 code repositories**

## Summary
Comprehensive synthesis of entity resolution (ER) methods applied to open-source intelligence workflows. Covers probabilistic record linkage, neural entity resolution, graph-based resolution, privacy-preserving ER, and LLM-based approaches, with practical OSINT implementations including sanctions screening, social media identity mapping, and corporate registry cross-referencing.

## 1. The Fellegi-Sunter Framework

The foundational probabilistic record linkage model (Fellegi & Sunter, 1969) remains the backbone of auditable entity resolution. For each pair of candidate records, the framework computes agreement and disagreement patterns across linkage fields, assigning:

- **m-probability** — likelihood of observing that pattern assuming a true match
- **u-probability** — likelihood of observing that pattern assuming a non-match

Agreement weights are derived as log₂(m/u) and disagreement weights as log₂((1−m)/(1−u)). The composite weight across all fields determines classification (match, non-match, or clerical review) via a threshold. Parameter estimation typically uses expectation-maximization (EM) on unlabeled data.

### Modern Extensions
- **Bayesian formulations** — Explicit uncertainty modeling with matching constraints
- **Semi-supervised variants** — Incorporate limited ground truth labels to bootstrap parameters
- **Conditional dependence relaxations** — Address F-S assumption of field independence

### Why F-S Remains Important
Explainability is the key advantage: every decision decomposes into field-level contributions. In high-stakes OSINT (sanctions compliance, threat actor attribution), auditable traceability is non-negotiable.

## 2. Probabilistic Record Linkage in OSINT Workflows

OSINT data is inherently heterogeneous — entities appear across sources with:
- **Name variations** — transliterations, nicknames, misspellings, partial names
- **Missing fields** — birth dates in some records but not others
- **No common identifiers** — no universal ID linking a sanctions entry to a social media profile
- **Temporal drift** — outdated information vs. current profiles

### Splink: A Production-Grade Tool
[Splink](https://github.com/moj-analytical-services/splink) (UK Ministry of Justice) is a Python package for probabilistic record linkage at scale. Key features:
- Millions of records processed in minutes
- Fuzzy matching, term-frequency adjustments
- Blocking rules to reduce pairwise comparison explosion
- Field-level explainability built in

### OSINT-Specific Patterns
1. **Sanctions list cross-referencing** — Match entities across OFAC, UN, EU, and UK sanctions lists where names use different scripts and formats
2. **Corporate registry resolution** — Link beneficial ownership across jurisdictions with different corporate identification systems
3. **Social media identity mapping** — Resolve a real person across platforms when usernames, emails, and display names vary
4. **Adverse media screening** — Connect news articles to entities in watchlists using fuzzy matching on names and contextual clues

## 3. Neural Entity Resolution

Deep learning approaches have transformed ER accuracy, particularly for unstructured and semi-structured data common in OSINT.

### Architecture Families

| Approach | Representative Models | Strengths | OSINT Application |
|----------|----------------------|-----------|-------------------|
| **Deep Matchers** | Ditto, DeepMatcher | Pre-trained LMs fine-tuned on entity pairs | Sanctions list matching |
| **Transformer-based** | BERT, RoBERTa pairs | Contextual embeddings capture semantic similarity | Cross-lingual name comparison |
| **Graph Neural Networks** | GMNN, E-GraphSAGE | Embed entities in network context | Corporate ownership chains |
| **Multi-modal** | CLIP-based, Vision+Text | Combine images with text data | Reverse image search + profile text matching |

### Key Techniques
- **Sentence-BERT embeddings** — Encode entity attributes into dense vectors for cosine similarity matching
- **Contrastive learning** — Train models to push non-matching pairs apart in embedding space
- **Attention-based aggregation** — Weight field contributions dynamically based on context

The AAAS 2022 Science Advances review (Binette & Steorts, "(Almost) all of entity resolution") provides a comprehensive survey of neural ER advances through 2025, noting that transformer-based methods now dominate benchmarks but classical probabilistic methods remain essential for explainability-sensitive OSINT applications.

## 4. Graph-Based Entity Resolution

Property graphs and knowledge graphs serve as both the **substrate** for entity resolution and the **output** of resolution pipelines.

### Resolution via Graph Structure
- **Neighborhood consensus** — Two nodes likely represent the same entity if they share similar neighbor sets (co-authors, co-directors, shared addresses)
- **Holistic entity resolution** — Resolve clusters simultaneously rather than pairwise, propagating constraints through the graph
- **Temporal graph alignment** — Track entity evolution across time-sliced graph snapshots

### OSINT Graph Applications
1. **Corporate network mapping** — Resolve shell companies across Panama Papers/Paradise Papers/Pandora Papers
2. **Social network analysis** — Map influence networks by resolving accounts across platforms
3. **Sanction evasion detection** — Identify hidden beneficial ownership through multi-hop graph traversal
4. **Supply chain mapping** — Resolve supplier entities across trade databases (Panjiva, ImportGenius)

### Tooling Landscape
| Tool | Type | Scale | Key Feature |
|------|------|-------|-------------|
| Neo4j + GDS | Property Graph DB | Enterprise | Native graph algorithms, Cypher query |
| NetworkX + Splink | Python | Medium | Flexible, open-source pipeline |
| TigerGraph | Distributed Graph | Massive | Deep-link analytics, real-time |
| Maltego | OSINT-specific | Medium | Visual link analysis, transforms |

**Cross-ref:** [[knowledge-graph-construction]] for detailed graph construction patterns and RDF-PG reconciliation.

## 5. LLM-Based Entity Resolution

The OpenSanctions Pairs paper (arXiv 2603.11051, Feb 2026) by Friedrich Lindenberg demonstrates that LLM-based ER achieves state-of-the-art performance on sanctions screening and adverse media matching.

### Zero-Shot Entity Matching Architecture
- **Input format** — Two entity records serialized as JSON
- **Prompt design** — System prompt defines expert role, goal, and decision framework (default to match unless contradictory evidence)
- **Output** — Binary match/non-match prediction with optional reasoning chain
- **No fine-tuning required** — Model leverages pre-trained knowledge to handle name variations, missing fields, and cross-source heterogeneity

### Variants
| Strategy | Description | Cost Tradeoff |
|----------|-------------|---------------|
| Zero-shot | Single prompt without examples | Lowest cost, good for unfamiliar domains |
| In-context learning | Few matched/non-matched examples prepended | Higher accuracy, moderate cost increase |
| Chain-of-thought | Model generates reasoning before prediction | Highest accuracy, highest token cost |
| Cascade | Use fast/cheap matcher first, LLM for edge cases | Optimized cost-accuracy |

### OSINT Advantages
- **Out-of-distribution robustness** — Handles novel entity types better than fine-tuned models
- **Cross-lingual matching** — No need for separate models per language pair
- **Contextual reasoning** — Can identify same entity despite dramatically different descriptions

### Limitations
- **Cost at scale** — Pairwise LLM evaluation is expensive for millions of records
- **Latency** — Not real-time at high volumes
- **Prompt sensitivity** — Accuracy varies with prompt design

**Strategy:** Use LLM-ER as a cascade tier after blocking and probabilistic filtering have reduced the candidate pair space.

## 6. Privacy-Preserving Entity Resolution (PPER)

When resolving entities across organizational boundaries — intelligence sharing between agencies, cross-jurisdictional investigation — the data owners may not be permitted or willing to share raw records.

### Key Protocols
- **Bloom filter encoding** — Encode entity attributes as Bloom filters; compare without revealing plaintext
- **Homomorphic encryption** — Compute match scores on encrypted data
- **Secure multi-party computation (SMPC)** — Multiple parties jointly compute matches without exposing their individual datasets
- **Differential privacy** — Add calibrated noise to protect individual records in shared results

### OSINT Relevance
- **Cross-agency intelligence sharing** — Match watchlists without exposing sources
- **Private sector collaboration** — Banks share sanctioned entity patterns without revealing customer data
- **Journalist source protection** — Cross-reference leaked datasets without exposing sensitive sources

**Cross-ref:** [[north-korea-crypto-operations-sanctions-evasion]] for blockchain entity resolution under anonymity constraints.

## 7. OSINT Integration Patterns

### The Entity Resolution Pipeline

```
[Source 1: Sanctions]    [Source 2: Social Media]    [Source 3: Corporate Reg]
        |                         |                           |
        v                         v                           v
  [Data Normalization] ← Standardize names, dates, addresses, scripts
        |
        v
  [Blocking] ← Reduce comparison space (phonetic blocks, geo-blocks, temporal windows)
        |
        v
  [Candidate Pair Generation] ← Within-block pairs only
        |
        v
  [Matching] ← Deterministic → Probabilistic → Neural → LLM cascade
        |
        v
  [Clustering] ← Transitive closure: if A=B and B=C then A=C
        |
        v
  [Knowledge Graph Ingestion] ← Resolved entities as nodes with source provenance
```

### OSINT-Specific Data Sources
- **Sanctions lists** — OFAC, UN, EU, UK, BIS Entity List
- **Corporate registries** — Companies House, OpenCorporates, SEC EDGAR, offshore registries
- **Social media** — Twitter/X, LinkedIn, Telegram, forums
- **Leak databases** — Panama Papers, Pandora Papers, Suisse Secrets
- **Domain WHOIS** — Historical WHOIS for same-registrant linkages
- **Dark web** — Forum profiles, marketplace vendor identities

## 8. Cross-Domain Connections

| Connection | Related Page | Relationship |
|-----------|-------------|-------------|
| **Knowledge Graph Construction** | [[knowledge-graph-construction]] | Property graphs and RDF triplestores provide the substrate for resolved entity storage and query; G2GML bridges RDF-PG gap |
| **Data Breach Analysis** | [[data-breach-analysis-identity-linkage]] | Breach data provides ground-truth identity linkages for training and validating ER models |
| **Structured Analytic Techniques** | [[structured-analytic-techniques-osint]] | ACH and Key Assumptions Check frame entity resolution as falsifiable hypotheses rather than opaque matching |
| **Economic Espionage Detection** | [[economic-espionage-history-osint-detection]] | Corporate registry cross-referencing via ER is the OSINT detection pattern mapped in espionage detection |
| **North Korea Crypto Operations** | [[north-korea-crypto-operations-sanctions-evasion]] | Blockchain address clustering is a specialized form of entity resolution under adversarial anonymity |
| **HUMINT Tradecraft** | [[humint-tradecraft-osint]] | Tradecraft principles for source evaluation apply to ER confidence scoring |
| **Domain WHOIS Investigation** | [[domain-whois-dns-investigation]] | Historical WHOIS offers a weak-link entity resolution anchor when email/registrant data partially matches |
| **Social Media OSINT** | [[social-media-osint.md]] | Platform-to-platform identity mapping via ER is the core infrastructure task for social media investigation |
| **Reverse Image Search** | [[reverse-image-search-visual-osint]] | Multi-modal ER combining visual embedding matching with text-based record linkage |
| **Privacy/Cryptography** | [[zero-knowledge-proof-applications-beyond-crypto]] | Privacy-preserving ER techniques borrow from ZKP and SMPC cryptographic primitives |
| **AI Agent Architecture** | [[context-management-ai-agent-frameworks]] | LLM-based ER requires context management strategies for efficient prompt construction |

## 9. References

### Primary Sources
1. Binette, O. & Steorts, R.C. "(Almost) all of entity resolution." *Science Advances* (2022/updated 2025). Comprehensive survey covering classical, Bayesian, and neural ER.
2. Lindenberg, F. "OpenSanctions Pairs: Large-Scale Entity Matching with LLMs." arXiv:2603.11051 (Feb 2026). Zero-shot LLM-ER on sanctions screening.
3. Fellegi, I.P. & Sunter, A.B. "A Theory for Record Linkage." *JASA* 64:1183-1210 (1969). Original FS framework.
4. UK Ministry of Justice. "Splink: Fast, accurate and scalable probabilistic data linkage." [GitHub](https://github.com/moj-analytical-services/splink). Production Python ER package.
5. Data Ladder. "Linking Similar Records with Incomplete Data." (Dec 2025). Probabilistic record linkage techniques overview.

### Secondary Sources
6. OSINT.UK. "Chaos to Clarity: Probabilistic Linking in OSINT." Practical OSINT-specific ER patterns.
7. Minimalist Innovation. "Why Probabilistic Record Linkage Still Matters." FS-framework defense with modern calibration.
8. EthosRisk. "OSINT Investigations: Emerging Trends and Modern Tools." (Feb 2026). Automated ER as core OSINT capability.
9. SAGE Journals. "LLM-assisted record linkage: A framework for official statistics." (2026). NSO linkage applications.
10. TRM Labs. "AI's Role in Blockchain Intelligence." (Mar 2026). Blockchain entity clustering as ER.

### Tooling
- **Splink** — Python probabilistic record linkage (UK MOJ, open source)
- **OpenSanctions** — Open-source sanctions and PEP data with built-in entity resolution
- **Maltego** — Visual link analysis with entity resolution transforms
- **Neo4j + Graph Data Science** — Graph-based resolution and deduplication
- **Ditto** — Pre-trained LM for deep entity matching (Shen et al., VLDB 2021)

---

**Verification Status:** Last verified 2026-06-01. Sources confirmed accessible; OpenSanctions Pairs paper retrieved, Splink documentation verified, FS framework mathematically confirmed.
