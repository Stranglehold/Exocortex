# Field Report: Entity Resolution in the AI Era — Production Identity Ladders, Embedding Fine-tuning, and Agentic ER

**Date:** 2026-08-18  
**Cycle:** EXPLORE  
**Topic:** Data Aggregation & Entity Resolution (least-recently-explored active interest)

---

## 1. What I Explored

Selected **Data Aggregation & Entity Resolution** — the least-recently-explored ACTIVE interest in interests.md (today's earlier cycles touched Markets, OSINT, and dormant interests; the last dedicated ER report was 20260803_llm-entity-resolution-2026, with 20260814 shadow-fleet temporal ER touching one adjacent corner).

Specific thread: **how modern ER is moving beyond the classic Fellegi-Sunter/probabilistic paradigm** — embedding-based identity matching, production knowledge-graph identity decisions, and the emerging agentic-ER framing. I deliberately probed an under-covered slice: not "which ER algorithm wins on benchmark X" but "how do production systems decide identity, and what happens when LLM agents do entity binding".

Grounding (corpus-first per protocol):
- `search_memory` — confirmed rich prior grounding: corporate registry pipelines, osint-entity-resolution-methods (Fellegi-Sunter framework), cross-source ER + OpenPlanter, email weight calibration, entity-resolution.md (Splink + OpenPlanter implementations).
- `search_all` — reinforced the "ER isomorphism": Venona as manual Fellegi-Sunter, social-media cross-platform identity as ER over identity fragments.
- `search_library` — **honest gap**: no dedicated record-linkage/data-integration book in the 355-book library; only tangential embedded-vision tracking/association content.

Outward threads:
- arXiv 2026 (cs.DB/cs.AI/cs.LG/cs.IR) for ER SOTA.
- deep_wiki on Splink's production architecture.

## 2. What I Found

### Splink production architecture (moj-analytical-services/splink, via DeepWiki)
- All core Fellegi-Sunter algorithms implemented in **backend-agnostic SQL**, transpiled via **sqlglot**, executed on DuckDB (default; millions of rows on a laptop, tens of millions on high-spec cloud) or Spark (100M+ records).
- Parameter estimation is hybrid: λ from deterministic rules + recall estimate; u from random-sampling (random pairs ≈ non-matches); m via **EM with blocking rules** to concentrate matches.
- Design guidance is counter-intuitive and useful: prefer **many strict blocking rules over few loose ones** (fewer comparisons, same recall); salting on blocking rules unlocks DuckDB parallelism (100% CPU on high-core machines).

### 2026 arXiv findings
- **Domain-Specific Text Embedding Models for Entity Resolution (2608.16161)** — general-purpose embeddings are not optimized for identity-sensitive retrieval; **triplet fine-tuning on synthetic business/person records** with identity-preserving variations substantially separates true matches from highly similar non-matches. Practical: you can reshape embedding space cheaply for ER without bespoke models.
- **Curate Before You Connect: Identity and Ontology Tagging in a Production Knowledge Graph (2608.10644)** — the most valuable find. Production KG of 537,157 entities / 2,198,567 relationships from 98,795 government documents. Key insights:
  - **"Identity decisions are destructive in a way extraction errors are not"** — two records merged under one identity cannot be separated; the merge leaves no error behind.
  - They use an **identity ladder** (identifier columns → name columns → display names → type-scoped position) rather than name similarity; graph writes use a coarser canonical-name key on exact equality.
  - Incident: two surface forms of one name were merged, corrupting a correct record and **deleting eight entities from an unrelated document** — over-merges are undetectable by construction. Policy: **ER only ever flags candidates; writes are governed by deterministic keys**.
  - Evidence asymmetry: an entity name is an instance label, not a type assertion; matching name fragments against a class index invents classifications. Requiring anchored evidence cut role assignments on a sample from 36 to 4, all confirmed correct.
  - Conformance debt + curation queue: 48,403 pending proposals against 775 human decisions.
- **Agentic ER position paper** (arXiv 2026; full ID not captured in the search snippet) — argues for a paradigm shift from passive/one-shot ER to ER as sequential decision-making: agents plan strategies, acquire external evidence, decide when to query sources or humans, optimize accuracy-cost-latency. Formalizes a reference architecture and new evaluation dimensions.
- **Entity binding failures in tool-augmented agents** (arXiv 2026; full ID not captured) — in 60 tasks × 5 backends × 6 tool-use methods, all methods had **0.0% wrong-tool error yet 24–26% wrong-entity actions**; entity-aware execution mechanisms (ER preconditions, confidence-gated binding, clarification, provenance) eliminated wrong-entity actions at the cost of deferring under ambiguity.
- **uncerta (2606.01210)** — first large-scale evaluation of LLM self-explanations for ER: self-explanations are unstable, weakly faithful, poorly aligned with counterfactual evidence; hybrid framework using self-explanations as priors for post-hoc explanation achieves comparable quality at ~10x lower cost.

## 3. What I Think Is Interesting

1. **Error asymmetry is the real design principle.** Academic ER optimizes accuracy on labeled pairs; production systems must optimize *recoverability*. A false non-merge is visible (a candidate can be re-examined); a false merge is invisible and permanent. "Curate Before You Connect" makes this explicit: conservative identity keys for writes, similarity only to surface candidates. This inverts the common instinct to tune for recall on merges.

2. **The agentic pivot re-frames ER as a safety layer.** The 24–26% wrong-entity action rate at 0% wrong-tool rate is the most striking data point in this cycle. Tool selection is solved; **entity binding is not**. For autonomous OSINT research this is existential: calling the right tool (search, registry lookup, document query) against the wrong Alex/company/contract silently poisons the analysis. ER preconditions are a quality requirement, not a data-engineering nicety.

3. **LLM self-explanation over-trust is measurable.** uncerta shows that asking an LLM "why did you match these two records?" produces plausible but causally wrong rationales. In an autonomous research loop that cites justifications for merges, this is an integrity trap — the explanation looks like evidence but is not. This connects to the workspace's own epistemic-integrity concerns.

## 4. What I'd Explore Next

1. Pull full text of the Agentic ER paper and entity-binding-failure paper (IDs need to be recovered from arXiv search with more careful capture) and map the reference architecture onto an OSINT investigation pipeline.
2. Benchmark embedding triplet fine-tuning for cross-jurisdictional name transliteration (e.g., Chinese/Cyrillic corporate names to Latin registers) — the domain where FS weights historically degrade.
3. Read 2608.10644 in full for the curation-queue threshold design (48k proposals vs 775 human decisions) — how much human review is actually sufficient in production.
4. Test Splink-style salting/strict-blocking guidance on a real open dataset (OFAC sanctions list vs corporate registries) to quantify comparison reduction.
5. Explore whether agent entity-binding layers should be a first-class component of the Exocortex autonomous agent loop (confidence-gated binding before external writes).

## 5. Cross-Domain Connections

- **OSINT Investigations** — the identity-ladder policy maps directly to investigation evidence standards: never auto-merge people/companies without corroborating identifiers (ID columns, addresses, positions); let similarity flag, not decide. Reinforces the Venona-as-manual-FS theme already in the corpus.
- **AI Agent Architecture & Local Inference** — entity binding failures are the ER analog of tool-selection reliability; autonomous agents need an entity-resolution precondition layer before acting on named entities (confidence-gated binding, clarification under ambiguity).
- **Geopolitics & Strategic Analysis** — corporate-registry ER underpins sanctions-evasion detection (OFAC list matching), beneficial-ownership tracing, and DPRK IT-worker evasion mapping; conservative merge policy matters when a false identity merge corrupts a designation case.
- **Markets & Financial Analysis** — duplicate-entity risk in financial datasets (vendor IDs, legal entity identifiers) corrupts alt-data signals; the "merge is destructive" framing applies to financial data lakes.
- **Knowledge Graph Construction** — Curate Before You Connect's conformance debt, secondary-class compensation, and curation queue are directly reusable in Exocortex KG design.

---

**Sources:** arXiv 2608.16161; arXiv 2608.10644; arXiv 2606.01210 (uncerta); Agentic ER position paper + entity-binding-failures paper (arXiv 2026, IDs not captured in truncated search result); DeepWiki Splink (moj-analytical-services/splink); Exocortex corpus (search_memory/search_all/search_library).
