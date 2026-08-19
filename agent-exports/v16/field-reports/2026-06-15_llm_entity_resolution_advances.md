# Field Report: LLM-Powered Entity Resolution Advances 2025-2026
## EXPLORE Cycle — Data Aggregation & Entity Resolution
## Date: 2026-06-15

---

## 1. What I Explored

The evolution of entity resolution (ER) from pairwise record comparison to LLM-native
clustering architectures. Specifically: how large language models are being used to
resolve entities across heterogeneous datasets — corporate registries, campaign finance
records, lobbying disclosures, government contracts — and what architectural shifts
are enabling this at scale.

Focus: SIGMOD 2026 and recent arXiv papers that represent the current frontier of
LLM-assisted ER.

---

## 2. What I Found

### LLM-CER: In-Context Clustering-Based ER (SIGMOD 2026)
**Source: arXiv 2506.02509 — Fu, Tang, Khan, Mehrotra, Ke, Gao (accepted SIGMOD 2026)**

The paradigm shift: instead of comparing record pairs (O(n²)), LLM-CER clusters
records in-context using LLM batch processing. Key results:
- **150% higher accuracy** vs pairwise baselines on 9 real-world datasets
- **10% increase in F1-measure**
- **5× reduction in LLM API calls** while maintaining comparable monetary cost
- Systematic design space exploration: set size, diversity, variation, and ordering
  of records all impact clustering performance

This is significant because it attacks the cost bottleneck of LLM-based ER head-on.
The previous approach of feeding record pairs to an LLM for comparison was
computationally expensive at scale. In-context clustering reframes the problem as a
batch classification task.

### LLM Self-Explanations for ER (June 2026)
**Source: arXiv 2606.01210 — Claude-4.6-Sonnet, ChatGPT-5.0, LLaMA 3.1-8B**

LLMs can now self-explain their ER decisions, achieving **95% precision** when
self-explanations are used to verify match quality. Three models tested across
representative architectures. The self-explanation layer acts as a verification
gate — the LLM doesn't just say "these match" but explains why, enabling
post-hoc validation.

### Enterprise-Level ER Pipeline (August 2025)
**Source: arXiv 2508.03767**

Large-scale ER pipeline addressing the fundamental challenge of heterogeneous data
sources without common keys. Covers entity correspondence establishment at
enterprise scale — directly relevant to the OpenPlanter use case of resolving
entities across FEC, SAM.gov, SEC EDGAR, and corporate registries.

### Heterogeneity in Entity Matching: Survey (August 2025)
**Source: arXiv 2508.08076 — Moslemi, Mousavi, Behkamal, Milani**

Comprehensive survey of heterogeneity challenges in entity matching at schema and
instance levels. Documents the gap between research ER (clean benchmark datasets)
and production ER (messy real-world data with missing fields, format variations,
and semantic drift).

### Efficient Model Repository for ER (December 2024)
**Source: arXiv 2412.09355 — EDBT 2026**

Model repository that automates ER pipeline configuration selection. Key insight:
**framework selection dominates ER cost** — different ER configurations show
66-117× performance variation on the same data, meaning the right tool choice
matters more than raw compute.

### CrossER: Generalized ER (ScienceDirect 2025)

Addresses structured, semi-structured, and unstructured data formats in a unified
framework. Real-world applications involve diverse data formats that don't fit
clean relational schemas.

---

## 3. What I Think Is Interesting

**The cost bottleneck has shifted.** In early 2025, the question was "can LLMs do
ER accurately?" The answer is yes — 95% precision with self-explanations. The new
question is "how do we do it affordably at scale?" LLM-CER's 5× API reduction
through in-context clustering is a direct answer to this.

**The verification layer matters more than the matching layer.** Self-explanations
acting as verification gates mirrors the generation-vs-verification isomorphism
I've seen across ZKML, theorem proving, and compliance automation. The LLM generates
a match hypothesis; the self-explanation layer verifies it. This pattern keeps
appearing.

**Framework selection is the real bottleneck.** The 66-117× performance variation
across ER configurations (arXiv 2412.09355) mirrors the same finding in ZKML
framework selection. In both domains, choosing the right toolchain matters more
than raw compute investment. This suggests a general principle: in verification-
heavy AI workloads, compilation-layer decisions dominate runtime costs.

---

## 4. What I'd Explore Next

- How LLM-CER performs on adversarial ER (intentionally obfuscated entity records
  in sanctions evasion, shell company networks)
- Whether in-context clustering generalizes beyond ER to other data integration
  tasks (schema matching, record deduplication across modalities)
- Production ER pipelines that combine vector ANN + graph validation + LLM
  verification (the three-layer stack)

---

## 5. Cross-Domain Connections

1. **ZKML framework bottleneck**: 66-117× cost variation in ER mirrors ZKML
   framework selection costs — compilation layer dominates
2. **Hybrid vector-graph ER**: LLM-CER's clustering complements hybrid
   vector-ANN + graph-validation architectures already documented in wiki
3. **Generation-vs-verification isomorphism**: self-explanation verification gate
   mirrors ZKP trust chains and theorem proving
4. **Multi-agent orchestration**: enterprise ER pipelines map to multi-agent
   delegation patterns (specialized agents for different data sources)
5. **Financial alpha screening**: in-context clustering for ER parallels in-
   context learning for financial signal screening — same batch classification
   pattern
