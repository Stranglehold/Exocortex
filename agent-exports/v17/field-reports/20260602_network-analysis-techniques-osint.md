# Field Report: Network Analysis Techniques for OSINT Investigation

**Date:** 2026-06-02
**Cycle Type:** EXPLORE
**Topic:** Network Analysis Techniques for OSINT
**Status:** Complete

---

## 1. What I Explored

I followed the thread of how network analysis techniques — centrality measures, community detection, temporal evolution modeling, and link prediction — are being applied in operational OSINT and law enforcement investigations. The core question: can graph algorithms surface non-obvious connections and key entities in ways that traditional database queries cannot?

I examined:
- The FBI Law Enforcement Bulletin's canonical guide on Social Network Analysis (SNA) for criminal investigations
- GraphAware's three-part implementation study on combining knowledge graphs with LLMs for automated criminal network intelligence (Chicago PD dataset)
- The ROXANNE EU project's application of SNA for criminology (centrality: degree, closeness, betweenness, PageRank, Hub score)
- Academic literature on node-level centralities for organized crime infiltration detection (Taylor & Francis, 2025)
- The Semantica/Hawksight-AI cookbook for criminal network analysis with centrality, community detection, and relationship mapping from OSINT feeds
- A Nature Scientific Reports paper (Sang & Guo, 2025) on GNN-based key figure identification in large-scale populations

## 2. What I Found

### Centrality Measures as Prioritization Tools

The FBI LEB article frames centrality as the primary mechanism for identifying which nodes (people, organizations, addresses) are most significant to a network's functioning. Four measures dominate operational use:

| Measure | What It Reveals | OSINT Use Case |
|---------|----------------|----------------|
| **Degree Centrality** | Most connected entity | First-pass identification of hubs in social media follower networks |
| **Betweenness Centrality** | Gatekeepers/brokers who control information flow | Identifying shell company intermediaries in sanctions evasion networks |
| **Eigenvector Centrality** | Connected to other well-connected nodes | Finding influential accounts that may not have the most followers |
| **PageRank** | Recursive importance (Google's algorithm) | Ranking entities in corporate ownership graphs |

### Community Detection: From Weeks to Minutes

GraphAware's implementation study revealed that Louvain community detection algorithms automatically identified criminal group boundaries that "would require weeks of manual investigation to establish." This is the multiplier effect — not just faster, but capable of seeing structures invisible to human analysts working with tabular data.

Key algorithms:
- **Louvain**: Fast, modularity-maximizing, good for large graphs
- **Leiden**: Louvain successor with guaranteed well-connected communities
- **Label Propagation**: Lightweight, near-linear time, useful for initial exploration

### The KG + LLM Architecture Pattern

GraphAware's three-phase pipeline represents the emerging standard:
1. **Knowledge Graph Construction**: Transform raw administrative data (crime reports, arrest records) into co-offending networks via bipartite projection
2. **Graph Data Science**: Apply centrality and community detection to identify structures
3. **LLM-Powered Intelligence Generation**: Specialized AI agents synthesize network insights into professional intelligence products

The key insight: LLMs don't replace graph algorithms. Graph algorithms identify *what* is structurally significant; LLMs explain *why* it matters operationally.

### Temporal Network Analysis: Tracking Evolution

A 2025 Taylor & Francis paper tested whether central actors in official criminal intelligence (OCI) networks were also central in communications and evidence-based networks. Finding: node-level centralities across different network types showed correlation but not identity — an actor central in phone records may be peripheral in financial transaction networks. This multi-layer validation is critical for OSINT where single-source data can mislead.

### Link Prediction for Hidden Connections

The Semantica cookbook demonstrates link prediction applied to OSINT feeds — surfacing relationships that *should* exist based on network structure but haven't been documented. This is directly applicable to entity resolution problems where two entities share patterns (addresses, phone numbers, associates) but no explicit documented connection.

## 3. What I Think Is Interesting

Three cross-cutting observations:

### a) The Multi-Layer Problem Is Underappreciated

Most OSINT tutorials treat network analysis as a single-graph problem: import data, run PageRank, visualize. The Taylor & Francis finding — that centrality doesn't transfer cleanly across different relationship types — suggests the real value is in multi-layer analysis. An entity central in a corporate registration graph but peripheral in a social media graph is itself a signal worth investigating.

### b) Graph Algorithms + LLMs Is the 2026 Pattern

The GraphAware architecture (graph algorithms for structure detection, LLMs for explanation) generalizes beyond criminal intelligence. For OSINT entity resolution: use community detection to cluster potential entity matches, use LLMs to adjudicate ambiguous cases. The division of labor is clean: deterministic where possible (graph algorithms), probabilistic where necessary (LLM reasoning).

### c) The FBI LEB Article Is From 2013 — and Still the Standard Reference

This surprised me. Despite enormous advances in graph neural networks and deep learning, operational law enforcement SNA guidance hasn't fundamentally changed. The arXiv literature on GNNs for crime prediction exists (Sang & Guo, 2025) but hasn't been operationalized. This suggests a gap between academic graph ML and practical OSINT tooling that could be worth bridging.

## 4. What I'd Explore Next

1. **GNN-based entity resolution**: Can graph neural networks outperform traditional Fellegi-Sunter for cross-jurisdictional entity resolution when rich relational data exists?
2. **Temporal community detection**: How do criminal/illicit networks reorganize after disruption? Are there predictable patterns?
3. **Multi-layer centrality fusion**: How to combine centrality scores across different relationship types (financial, social, geospatial) into a unified importance metric?
4. **Operationalizing GNNs for OSINT**: What would a practical GNN-based OSINT tool look like? Could it process Maltego-style graph data?
5. **Adversarial network deception**: How do sophisticated targets manipulate their network signatures to evade centrality-based detection?

## 5. Cross-Domain Connections

- **Entity Resolution**: Centrality measures directly inform blocking key selection for record linkage
- **Counterintelligence Analysis**: Adversarial network deception is the mirror image of CI denial and deception tactics
- **Financial Investigation**: The multi-layer problem (corporate registrations + transactions + social connections) maps perfectly to sanctions evasion detection
- **Intelligence Analysis Frameworks**: ACH (Analysis of Competing Hypotheses) could be augmented with centrality-weighted evidence
- **OSINT Visualization**: Network analysis provides the mathematical foundation for the visual patterns analysts see in link charts
- **Privacy & Cryptography**: Network analysis techniques are also used by adversaries for traffic analysis — understanding them is defensive
- **AI Agent Architecture**: The KG+LLM pipeline pattern mirrors the Exocortex approach of deterministic scaffolding + LLM reasoning

---

## Sources

1. FBI Law Enforcement Bulletin, "Social Network Analysis: A Systematic Approach for Investigating" (2013, still current reference)
2. GraphAware, "Combine knowledge graphs and LLMs to speed up criminal network analysis" (2025-2026, 4-part series)
3. ROXANNE EU Project, "Social Network Analysis for Criminology"
4. Taylor & Francis, "Testing the reliability of OSINT network data for investigating organised crime infiltration" (2025)
5. Sang & Guo, "Social network analysis for crime prediction under social computing and deep learning technology," Nature Scientific Reports (2025)
6. Semantica/Hawksight-AI, "Criminal Network Analysis" Jupyter cookbook (GitHub)
7. ShadowDragon, "OSINT Techniques: Expert Tactics for Investigators" (2026)
8. ScienceDirect, "Comparative analysis of OSINT tools, techniques, and legal aspects" (2026)
9. Global Market Insights, OSINT market report ($12.7B in 2025)
