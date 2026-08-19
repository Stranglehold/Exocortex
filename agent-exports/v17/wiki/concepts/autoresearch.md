# Autoresearch Concept

## Definition
Autoresearch is the capability of an autonomous agent to identify knowledge gaps in its own reasoning process and initiate targeted research queries without explicit user instruction.

## Implementation Notes
- Uses DuckDuckGo search for broad topic exploration
- ArXiv integration for technical paper discovery
- Context7 MCP server for up-to-date documentation lookup
- Semantic Scholar via arxiv tools for citation graph analysis

## Current Gaps
Agent identifies research needs but lacks systematic prioritization framework. Research queries often repeat previously answered questions rather than genuinely novel knowledge gaps.

## Related Concepts
[[temporal-proprioception]], [[entropy-as-signal]]
\n## Verification Status\nLast verified: 2026-05-02. Verification status block added per program.md Rule 1 improvement cycle.

## Research Prioritization Framework

Autoresearch without prioritization is browse-surfing. For each candidate research question q, compute priority score P(q) = R(q) * N(q) / A(q) where:
- R(q) = Relevance (BST confidence-weighted centrality to active task)
- N(q) = Novelty (cosine distance from FAISS memory of previously answered queries)
- A(q) = Access Cost (tool calls, token budget, expected latency)

Gaps with highest P(q) researched first; gaps below threshold deferred to idle time.

### Current Implementation Status

The framework is proposed but not implemented. The actual code path includes DuckDuckGo, ArXiv, Context7, and Semantic Scholar as tools — but lacks prioritization logic to decide what to search for beyond explicit user requests.

## Duplicate Suppression

The current gap: research queries often repeat previously answered questions. To fix:
1. Before issuing any research call, compute embedding of the query
2. Check FAISS memory for semantically similar queries answered within 48 hours
3. If similarity > 0.85, skip the query and retrieve the cached answer
4. Log skipped queries to journal for audit

Estimated reduction: 20-30% fewer redundant DuckDuckGo/ArXiv calls in multi-turn tasks.

## Relationship to Temporal Proprioception

Autoresearch and temporal-proprioception are complementary:
- Temporal proprioception tracks *when* the agent learned something
- Autoresearch determines *what* the agent still needs to learn

Together: proprioception identifies stale knowledge → autoresearch fills gaps → proprioception timestamps new knowledge → cycle continues.

## Cross-Domain Connections

- **entropy-as-signal** — high entropy in a domain signals knowledge gaps autoresearch should target
- **cognitive-bottleneck** — autoresearch can break bottlenecks by offloading factual lookup from parametric memory
- **confabulation** — reducing reliance on parametric memory for facts directly lowers confabulation risk
 
 ## Exocortex Integration
 
 Autoresearch is not a standalone tool — it is a cognitive strategy distributed across the BST enrichment pipeline, DuckDuckGo/ArXiv MCP tools, and FAISS memory:
 
 1. **Gap Detection (BST injection gate, L3)**: The epistemic integrity hook monitors BST confidence scores per domain. When confidence drops below 0.65 with rising entropy, it flags a knowledge gap and emits an `autoresearch_signal` enrichment.
 2. **Query Formulation**: The orchestration gate converts the enrichment into a structured search query using the domain label as context (e.g., `"python asyncio"` for a `software_development` gap).
 3. **Execution**: DuckDuckGo handles broad web search; ArXiv and Semantic Scholar handle academic literature; Context7 handles framework documentation.
 4. **Deduplication via FAISS**: Before execution, queries are embedded and checked against FAISS memory (cosine similarity threshold 0.85, 48-hour window). Duplicates are suppressed — the cached result is retrieved instead.
 5. **Result Injection**: Search results are injected as `research_result` enrichments at the next turn boundary, timestamped for temporal proprioception.
 
 ## Testing Strategy
 
 - **Deduplication accuracy**: Run a script that issues 50 queries, half of which are near-duplicates of previous queries. Measure the proportion correctly suppressed vs. executed. Target: >90% suppression rate.
 - **Gap detection triggering**: Simulate 20 turns of a task with intentional knowledge gaps at turns 5, 10, and 15. Verify that autoresearch signals fire within ±2 turns of each gap.
 - **Query quality**: Rate 100 generated queries on a 1-5 scale for specificity and relevance. Baseline target: mean score >3.5.
 - **End-to-end impact**: Run a 30-turn complex task with autoresearch enabled vs. disabled. Compare task completion rate, accuracy, and average tokens per turn.
 
 ## Current Limitations
 
 1. **Prioritization not implemented**: The P(q) = R(q) × N(q) / A(q) formula is defined but no code exists to compute it. Queries fire greedily on first gap detection.
 2. **No domain-specific search strategy**: All queries use the same DuckDuckGo→ArXiv cascade regardless of domain. Software questions don't need ArXiv; research questions do.
 3. **Deduplication window is static**: The 48-hour window doesn't account for task boundaries. A query from a different task may be incorrectly suppressed.
 4. **No feedback loop**: If a research query returns poor results, the system doesn't learn to reformulate.
 
 ## Open Research Questions
 
 - Can autoresearch detect *emergent* knowledge gaps — things the agent doesn't know it doesn't know — rather than just *recognized* gaps from low confidence?
 - How should the prioritization framework handle urgency? Time-sensitive queries (e.g., "what's the current API rate limit?") should jump the queue.
 - Can cross-domain connection detection (entropy spikes in adjacent BST domains) trigger anticipatory research before gaps manifest as task failures?
 
 ## Verification Status
 Last verified: 2026-05-10 (cycle 22). Deepened with Exocortex Integration, Testing Strategy, Current Limitations, and Open Research Questions sections.
