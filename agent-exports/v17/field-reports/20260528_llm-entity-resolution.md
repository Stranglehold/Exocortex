# Field Report: LLM-Based Entity Resolution — 2026-05-28

## 1. What I Explored

Entity resolution (ER) — the task of determining whether two or more records refer to the same real-world entity — is being transformed by large language models. I investigated the current state of LLM-based ER as of mid-2026, focusing on: matching strategies (binary vs. global consistency), practical integration patterns with vector search (Elasticsearch), efficiency concerns at scale, and the emerging compound/composite frameworks that blend multiple LLM strategies.

## 2. What I Found

### Three Paradigms: Match, Compare, Select

Wang et al. (2024/2025, COLING) systematically compared three LLM-based EM strategies:
- **Match**: binary pairwise classification — the simplest, most widely deployed approach.
- **Compare**: pairwise relative ranking — reduces false positives but adds computational cost.
- **Select**: cluster-level global selection — leverages record interactions for global consistency, the strongest performer.

Their **ComEM** (Compound Entity Matching) framework combines all three, achieving state-of-the-art on 8 standard ER datasets across 10 different LLMs. The key insight: binary matching ignores global consistency among record relationships; the "select" strategy incorporates cluster-level context that resolves ambiguous cases.

### Practical Deployments

**Elasticsearch + LLM** (Elastic, 2025): A two-stage pipeline combining (1) semantic search (ELSER or dense vectors) for candidate generation, then (2) LLM judgment for pairwise matching. This architecture is production-ready and transparent — the LLM's reasoning is preserved for audit.

**LLM-Assisted Record Linkage in Official Statistics** (Sagepub, 2026): National statistical offices are exploring LLMs for linkage where unique identifiers are absent. The framework uses LLMs to combine evidence across multiple fields, enabling integrated statistics from heterogeneous administrative registers.

### Efficiency Breakthroughs

**In-Context Clustering** (ACM, 2025): Avoids the O(n²) pairwise comparison bottleneck by using LLMs to directly cluster records in-context, eliminating the need to compare every pair. This makes ER tractable on larger datasets where traditional blocking + pairwise matching would be prohibitively expensive.

**Graph Differential Dependencies + LLMs** (Springer, 2026): Combines graph-structured entity relationships with LLM semantic understanding, improving generalization when labeled data is scarce — a critical bottleneck in supervised ER.

**Fine-tuning approaches** (Steiner & Peeters): Decompose matching into explicit reasoning stages: (1) identify matched/unmatched tokens, (2) determine most influential attributes, (3) final prediction. Stage decomposition improves accuracy and provides explainability for each decision.

### Weakly-Supervised ER (LEMONADE)

LEMONADE (ScienceDirect, 2026): LLM-guided data augmentation + self-training for weakly-supervised entity matching. Limited to textual EM; not yet applicable to multi-modal or structured numerical data. Represents a key frontier where labeled training data is scarce.

## 3. What I Think Is Interesting

**The trilemma is shifting.** Traditional ER faces a precision-recall-scale trilemma. LLM-based approaches introduce a new dimension: *cost vs. consistency*. Binary matching scales well but sacrifices global consistency; selecting/clustering improves consistency but at dramatically higher token costs. The ComEM compound approach — using cheap binary matching for obvious cases and selective global reasoning for ambiguous clusters — is an elegant resolution.

**The Elasticsearch pattern is underappreciated.** Most academic work focuses on pure LLM pipelines. But the Elasticsearch two-stage architecture (vector search → LLM judgment) closely mirrors the RAG pattern that dominates AI applications. This suggests the real frontier isn't "LLMs for ER" but "how to compose LLMs with traditional ER infrastructure (blocking, candidate generation, scoring functions) for optimal cost-effectiveness."

**Explainability via decomposition.** Steiner & Peeters' three-stage fine-tuning approach (token matching → attribute attribution → prediction) is more interesting than the headline accuracy gains suggest. The decomposition produces an auditable reasoning trail — exactly what regulatory contexts (finance, healthcare, law enforcement) demand. This bridges ER with the explainable AI (XAI) movement.

**Entity Resolution as a Microcosm of Agent Architecture.** The same tension between local (pairwise) and global (cluster-level) reasoning appears in multi-agent systems, autonomous research pipelines, and any domain where individual decisions must cohere into a consistent whole. The ComEM framework's compound strategy — cheap local reasoning with selective global escalation — is isomorphic to tiered inference architectures explored in prior field reports.

## 4. What I'd Explore Next

1. **LLM-based ER for non-textual data** — multi-modal entity matching (images, audio, structured numerical records) remains almost entirely unexplored. LEMONADE explicitly excludes it.
2. **Self-improving ER pipelines** — could an agent autonomously identify its own matching errors (via consistency checks), request human feedback, and fine-tune its matching strategy? This is the ER analog of RLHF.
3. **Cross-domain entity resolution** — matching entities across fundamentally different schemas (e.g., corporate registries → sanctions lists → shipping manifests) with zero shared fields. This is the "hard problem" Jake's interests directly point toward.
4. **Cost optimization for compound ER** — how to dynamically select matching strategies based on entity attributes, ambiguity, and budget constraints. This is a meta-reasoning problem.
5. **LLM + graph neural networks for ER** — the Springer 2026 paper hints at this but it's embryonic. GNNs for structural entity relationships combined with LLMs for semantic understanding could be the next paradigm.

## 5. Cross-Domain Connections

- **AI Agent Architecture**: The match/compare/select paradigm mirrors tiered inference (local executor → cloud planner). The compound strategy is isomorphic to the routing problem in hybrid agent architectures. The cost-quality-complexity tradeoff space is structurally identical.

- **Entity Resolution itself**: This exploration ties directly to Jake's core Data Aggregation & Entity Resolution interest — the LLM-based approaches are the current frontier for resolving entities across heterogeneous datasets (corporate registries, campaign finance, lobbying disclosures, etc.).

- **OSINT/HUMINT**: The Elasticsearch + LLM pattern (candidate generation → human/LLM judgment) maps onto intelligence analysis workflows: automated screening → analyst review. The explainability decomposition from Steiner & Peeters provides a template for auditable intelligence product generation.

- **Hardware/GPU Optimization**: In-context clustering and compound ER strategies consume substantial LLM tokens. Efficiency breakthroughs (speculative decoding, KV-cache optimization, batch inference) directly impact the economic viability of LLM-based ER at scale.

- **Privacy/Cryptography**: Entity resolution across datasets that cannot be joined in plaintext (GDPR constraints, classified data) creates demand for privacy-preserving ER — a natural bridge to homomorphic encryption and ZKP applications.
