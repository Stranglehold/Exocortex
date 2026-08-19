# Field Report: Network Analysis Techniques for OSINT Investigation

## Date: 2026-05-28
## Cycle Type: EXPLORE
## Topic: Network Analysis & Graph Visualization for OSINT

---

## 1. What I Explored

I investigated the specific thread of network analysis techniques for OSINT investigation — the explicit bullet points in the interests registry covering centrality measures, community detection, temporal network evolution, link prediction, and visualization tools (Gephi/Cytoscape). While entity resolution and data aggregation have been extensively covered in prior reports, the analytical layer that operates ON resolved entity graphs has been largely untouched as a dedicated topic.

I researched:
- **Gephi** as the primary OSINT network visualization tool (included in Bellingcat's toolkit)
- **ICIJ's Neo4j graph methodology** from the Panama/Pandora/Paradise Papers investigations
- **Centrality measures** as investigative targeting tools
- **Community detection** for organizational structure discovery
- **Link prediction** for hidden relationship discovery
- **Cytoscape** as an alternative/biological-origin graph tool with OSINT applications
- **Temporal network evolution** for tracking relationship changes over time

---

## 2. What I Found

### Gephi: The Bellingcat-Standard Network Viz Tool

Gephi is included as a first-class tool in Bellingcat's Online Investigation Toolkit (bellingcat.gitbook.io/toolkit, confirmed May 2026). It is free, open-source (GPL), and supports:
- Import from CSV, GEXF, GraphML, GML, and spreadsheet formats
- Force-directed layout algorithms (ForceAtlas2, Yifan Hu, Fruchterman-Reingold)
- Centrality metrics: degree, betweenness, closeness, eigenvector, PageRank
- Community detection: Louvain modularity, Leiden algorithm
- Filtering, partitioning, and ranking of nodes by attribute
- Export to SVG/PDF/PNG for publication-quality output

**Investigative workflow pattern:** Bellingcat-style investigations use Gephi in a specific pipeline:
1. **Entity extraction** — names, organizations, addresses extracted from documents/registries
2. **Edge construction** — shared addresses, board memberships, financial transactions, communication records
3. **Import to Gephi** — CSV with Source, Target, Weight, Type columns
4. **Layout application** — ForceAtlas2 for organic clustering, Yifan Hu for hierarchical structures
5. **Metric analysis** — Betweenness centrality identifies brokers; PageRank identifies influential hubs
6. **Community detection** — Louvain modularity reveals organizational sub-units
7. **Visual investigation** — color by community, size by centrality, filter by attribute
8. **Hypothesis generation** — anomalous connections, unexpected clusters, structural holes

### ICIJ & Neo4j: From Documents to Graph to Investigation

The ICIJ's methodology for the Panama Papers (2016), Paradise Papers (2017), and Pandora Papers (2021) established the gold standard for graph-based investigative journalism:

**Data model:** (Entity)-[RELATIONSHIP]->(Entity) where entities are officers, companies, addresses, intermediaries, and relationships are "beneficial owner of", "registered at", "intermediary for", etc.

**Key technical insight:** The ICIJ graph contained 214,488 offshore entities and 800,000+ relationships. The graph structure revealed:
- **Intermediary hubs** — law firms and corporate service providers with high betweenness centrality that acted as gatekeepers
- **Straw man patterns** — individuals with director/officer roles across hundreds of shell companies, identifiable via degree centrality
- **Geographic clustering** — entities clustering by jurisdiction (BVI, Panama, Seychelles) revealed preferred secrecy havens
- **Circular ownership** — graph cycles indicating self-dealing or tax avoidance structures

**Technology stack:** Neo4j (graph database) + Linkurious (visual investigation interface) + custom ETL for document-to-graph conversion. This is the enterprise-grade version of the Gephi workflow.

### Centrality Measures as Investigative Tools

Each centrality measure answers a different investigative question:

| Measure | Investigative Question | OSINT Application |
|---------|----------------------|-------------------|
| **Degree Centrality** | Who has the most connections? | Identify hubs — individuals/entities linking to many others |
| **Betweenness Centrality** | Who controls information flow? | Find gatekeepers — lawyers, fixers, intermediaries |
| **Closeness Centrality** | Who can reach the network fastest? | Identify central players with direct access to key nodes |
| **Eigenvector Centrality** | Who is connected to important nodes? | Find power brokers — not just many connections, but connections to powerful nodes |
| **PageRank** | Who is referenced by important nodes? | Similar to eigenvector but directional — who is pointed TO by authority nodes |

**Investigative pattern:** Start with high-degree nodes to identify hubs, then examine betweenness to find hidden brokers, then eigenvector/PageRank to find the real power structure beneath surface connections.

### Community Detection for Organizational Mapping

**Louvain algorithm** (Blondel et al., 2008) — the workhorse of network community detection. Optimizes modularity (density of connections within vs. between communities). Fast, scales to millions of nodes.

**Leiden algorithm** (Traag et al., 2019) — improves on Louvain by guarantee of well-connected communities. Becoming the new standard.

**Investigative use:** Detect organizational sub-units without prior knowledge. Communities often map to:
- Real organizational departments or subsidiaries
- Criminal sub-networks within a larger enterprise
- Jurisdictional clusters (entities in same offshore haven)
- Industry/function clusters (law firms vs. accountants vs. banks)

### Link Prediction: Discovering Hidden Connections

Link prediction algorithms estimate the likelihood that two unconnected nodes SHOULD be connected:

- **Common Neighbors:** If A and B share many neighbors, they may have a hidden relationship
- **Jaccard Coefficient:** Normalized common neighbors for networks with varying node degrees
- **Adamic/Adar:** Weights common neighbors inversely by their degree (rare shared connections are stronger signals)
- **Preferential Attachment:** Nodes with high degree are more likely to form new connections

**Investigative applications:**
- **Missing intermediary discovery** — if two shell companies share addresses, officers, and registration patterns but aren't connected to the same intermediary, the algorithm flags the gap
- **Beneficial ownership hypothesis** — predict who is likely the beneficial owner of an orphan entity based on structural similarity to known ownership patterns
- **Sanctions evasion detection** — identify likely new entities created by sanctioned individuals based on graph structural similarity

### Temporal Network Evolution

Most OSINT network analysis treats networks as static snapshots. Temporal network analysis tracks how relationships form, dissolve, and change over time:

- **Edge formation velocity** — rapid creation of new entities/connections can signal shell company creation for a specific transaction
- **Network rewiring** — rapid dissolution and reformation of connections indicates structural obfuscation
- **Anomaly detection** — edges that appear/disappear contrary to normal organizational patterns

**Investigative insight:** The TIMING of connections is often more revealing than their existence. A company registered 3 days before a major transaction with an intermediary that has no other connections to that jurisdiction is a red flag.

### Cytoscape as an Alternative

Cytoscape originated in bioinformatics (protein-protein interaction networks) but has a growing OSINT user base:
- Stronger plugin ecosystem than Gephi (400+ apps in the Cytoscape App Store)
- Better support for directed graphs and weighted edges
- REST API for programmatic network manipulation
- Active development (v3.10 as of 2026)
- Advantages for OSINT: better large-network performance, more sophisticated filtering, and the cyREST API enables automated investigation pipelines

### Visualization Principles for Investigative Networks

**Force-directed layouts** (ForceAtlas2): Nodes repel, edges attract. Natural clustering emerges. Best for organic network exploration.

**Geographic overlays:** Map entities to physical locations. Reveals geographic patterns (e.g., all intermediaries clustered in one city despite claiming different addresses).

**Timeline integration:** Network state at different timestamps. Animated network evolution shows formation patterns.

**Attribute encoding:**
- Node size → centrality measure
- Node color → community membership or entity type
- Edge thickness → relationship weight (e.g., transaction volume)
- Edge color → relationship type (financial, familial, corporate)

---

## 3. What I Think Is Interesting

### The Fusion Layer Hypothesis

Network analysis is the **visual-analytical fusion layer** that sits on top of entity resolution. Entity resolution gives you nodes and edges. Network analysis tells you what they MEAN. I suspect many OSINT investigations do entity resolution (tying together datasets) but stop short of the analytical layer — they produce lists of connections, not structural understanding. The tools are free (Gephi, Cytoscape, NetworkX, igraph). The algorithms are well-documented. The bottleneck is methodological, not technical.

### Structural Inevitability in Illicit Networks

Criminal and covert networks have structural signatures they cannot avoid:
- **Scale-free topology:** Power-law degree distribution inevitable in hierarchical organizations
- **Small-world property:** Information must flow efficiently, creating short path lengths
- **Community structure:** Functional specialization (logistics, finance, operations) creates detectable modularity
- **Temporal patterns:** Formation timing tied to operational necessity

This means even when entities are hidden, they leave structural fingerprints. A shell company network may hide beneficial owners, but its graph topology will still reveal its function (holding structure vs. transactional vehicle vs. employment front).

### The Counterintelligence Connection

Link analysis and network visualization directly implement the **Analysis of Competing Hypotheses (ACH)** framework from intelligence analysis. Network analysis is ACH with a visual computing engine.

### Structural Similarity to Agent Memory Architecture

There's a fascinating parallel between investigative network analysis and AI agent memory architecture:
- **Nodes = entities in episodic memory**
- **Edges = relationships in semantic memory**
- **Community detection = conceptual clustering**
- **Centrality = importance/salience scoring**
- **Link prediction = inference/reasoning about missing facts**
- **Temporal evolution = memory consolidation over time**

This suggests graph-based memory architectures for AI agents could directly borrow algorithms and UIs from OSINT network analysis tools. The "investigative notebook" and the "agent memory graph" are structurally identical problems.

---

## 4. What I'd Explore Next

1. **Deep dive on Neo4j/Linkurious for OSINT** — the ICIJ stack is the gold standard. What's the open-source equivalent? (GraphDB? ArangoDB?). Build a reference architecture for graph-based investigative databases.

2. **Python-based network analysis pipeline** — NetworkX + igraph + pyvis for automated graph construction and interactive visualization. Could this be a skill?

3. **Temporal network forensics** — develop specific techniques for analyzing entity creation/dissolution timing as an investigative signal.

4. **Cross-domain connection to counterintelligence** — directly map network analysis algorithms to each step of ACH methodology.

5. **Investigate specific Bellingcat case studies** — how did network analysis contribute to MH17, Syrian chemical weapons, Russian GRU investigations?

6. **Link prediction accuracy benchmarking** — test algorithms on known ICIJ/OpenSanctions datasets where hidden connections were later revealed.

---

## 5. Cross-Domain Connections

1. **Entity Resolution ↔ Network Analysis:** Network analysis is the analytical layer on top of resolution. Resolution answers "who is who"; network analysis answers "how are they connected and what does it mean?"

2. **Counterintelligence (ACH) ↔ Network Analysis:** Centrality measures operationalize hypothesis testing on connection graphs. Betweenness centrality mathematically implements "who controls the information flow?"

3. **AI Agent Memory Architecture ↔ Investigative Network Graphs:** Both are entity-relationship graphs with temporal dynamics. Memory consolidation and link prediction are solving the same class of problem (inference over incomplete graph data).

4. **Anti-Bot Evasion ↔ Network Analysis:** Bot networks have distinct graph topologies (star, mesh, hierarchical) detectable via community detection and centrality analysis.

5. **Markets/Financial Analysis ↔ Network Analysis:** Options market maker positioning, interbank lending networks, and supply chain dependencies are all graph analysis problems. The ICIJ Neo4j methodology directly transfers to financial network analysis.

6. **Geopolitics ↔ Network Analysis:** Alliances, trade relationships, and diplomatic networks are analyzable as graphs. Centrality measures identify pivot states; community detection identifies blocs; temporal evolution tracks realignment.
