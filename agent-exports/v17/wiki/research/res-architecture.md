# RES Architecture: O(1) Context Window Agentic Design
**Created:** 2026-04-28T05:37Z
**Status**: Research paper summary — arXiv:2603.22367
**Category**: Scalable context management.
## Abstract Summary
Reasoner-Executor-Synthesizer (RES) three-layer architecture strictly separates intent parsing (Reasoner), deterministic data retrieval/aggregation (Executor zero LLM tokens), and narrative generation (Synthesizer). Executor passes only fixed-size statistical summaries to Synthesizer achieving O(1) token complexity regardless of dataset size. Validated on ScholarSearch with 130M+ articles: mean cost 1,574 tokens whether processing 42K or 16.3M records. Eliminates data hallucination by construction — LLM never sees raw records.
## Key Findings
- O(1) token complexity proven formally and validated empirically across 100 benchmark runs with dataset sizes spanning four orders of magnitude (42K → 16.3M articles)
- Hallucination eliminated not reduced because deterministic executor layer prevents LLM from fabricating data it never directly observes
- Fixed-size statistical summaries replace full document injection reducing per-query overhead by ~95% vs standard RAG approaches
## System Design Implications for Exocortex
1. **Executor as Layer B** — tool registry and memory recall could operate in zero-cost deterministic mode before any LLM invocation; only structured summaries reach generation phase not raw retrieved content
2. **Summary size budgeting** — fixed-size summary constraint means each Executor output bounded to predictable token count enabling precise injection budget planning per turn
3. **Hallucination prevention architecture** — separating data access from narrative generation prevents fabrication at architectural level not just detection post-hoc
## Connection to Other Concepts
- [[karpathy-wiki]] RES maps directly to three-layer wiki: L1=Reasoner (intent parsing) L2=Executor (deterministic retrieval zero tokens) L3=Synthesizer (narrative generation)
- [[context-pruner]] upstream prevention of context bloat by design not reactive compression after accumulation
- [[stateful-injection]] fixed-size summaries enable clean delta protocol because baseline format never changes across turns
## References
- arXiv:2603.22367 (RES Architecture)
\n## Verification Status\nLast verified: 2026-05-02. Verification status block added per program.md Rule 1 improvement cycle.
