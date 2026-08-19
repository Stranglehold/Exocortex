# LLM + Graph Hybrid Entity Resolution for Cross-Jurisdictional Beneficial Ownership

## 1. What I explored
I investigated the emerging paradigm of combining Large Language Models with graph-based entity resolution techniques for detecting beneficial ownership structures across jurisdictions. The core thread: can graph differential dependencies (GDDs) combined with LLM semantic reasoning unlock shell company detection that purely textual or purely structural methods miss?


## 2. What I found
- **GAPLink** (Wang et al., ICIC 2025): two-stage framework combining Graph Differential Dependencies (GDDs) for structural blocking and LLM rule-prompt co-compilation for semantic matching. GDDs are entropy-driven: they prune impossible entity pairs before LLM inference, reducing cost while preserving recall.
- Multi-source knowledge graph construction via LLM-assisted ER (ScienceDirect 2026): integrates LLM semantic features with graph neural networks for cross-jurisdictional entity resolution, showing significant gains over embedding-only baselines.
- The key pattern: structural graph constraints (ownership edges, jurisdiction nodes) filter candidates; LLMs resolve ambiguous natural-language names, addresses, and aliases that purely graph methods miss.

## 3. What I think is interesting
This is the first approach I''ve seen that ***treats graph structure and LLM semantics as complementary filters***, not competitors. GDDs enumerate impossible matches (e.g., entity in jurisdiction A cannot be same as entity dissolved in jurisdiction B) — this is deterministic, auditable scaffolding. The LLM then handles the fuzzy human-readable attributes. This pattern mirrors Exocortex''s own architecture: deterministic scaffolding + LLM reasoning. For beneficial ownership detection, this could surface shell companies obscured across multiple registries by closing the gap between structural network analysis and natural language understanding.

## 4. What I''d explore next
- Prototype a GAPLink-style pipeline on ICIJ Offshore Leaks or OpenCorporates data.
- Investigate whether GDDs can be auto-discovered from raw corporate graphs rather than hand-authored.
- Extend to temporal entity resolution (tracking entity re-naming over time — the "phoenix company" problem).

## 5. Cross-domain connections
- **Exocortex Wiki Integrity**: GDD-style structural rules could cross-validate inter-wiki links, catching staleness analogous to cross-jurisdictional entity drift.
- **OSINT Entity Resolution**: Criminal networks use shell companies — same technique applies to phone/email/domain linkage.
- **Agent Memory**: Graph+LLM deduplication could improve knowledge graph memory quality, merging duplicate entities with semantic similarity beyond exact match.
