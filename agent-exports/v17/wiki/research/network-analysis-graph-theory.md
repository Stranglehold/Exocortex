# Network Analysis & Graph Theory

**Status: STABLE**
**Created: 2026-05-20 | Last Deepened: 2026-05-20**
**Cross-domain: OSINT, Entity Resolution, Intelligence Analysis, Markets, Privacy, Infrastructure**

Cross-cutting methodology for analyzing relational data — social networks, financial flows, infrastructure dependencies, communication patterns, and supply chains. Graph theory provides the mathematical foundation; network analysis applies it to real-world relational systems.

---

## Centrality Measures

Centrality quantifies which nodes are most "important" in a network. Different measures capture different notions of importance — no single measure is universally optimal (Freeman 1979; Lawyer 2015, arXiv:1405.6707).

### Core Measures

**Degree Centrality** — simplest measure: number of direct connections. Identifies highly connected individuals but misses bridge roles and influence through well-connected neighbors.

**Closeness Centrality** (Bavelas 1950, Sabidussi 1966) — inverse of average shortest-path distance to all other nodes. Identifies nodes that can quickly reach the entire network. Variant: harmonic centrality (Rochat 2009) handles disconnected graphs. Evans & Chen (2022, *Communications Physics*, arXiv:2108.01149) established formal link between closeness and degree centrality.

**Betweenness Centrality** (Freeman 1977) — fraction of all shortest paths that pass through a node. Identifies bridge nodes and gatekeepers controlling information flow. Brandes (2001, *J. Math. Sociology*) provided the O(|V|·|E|) algorithm that made betweenness practical for large networks.

**Eigenvector Centrality** (Bonacich 1972, 1987) — a node's importance is proportional to the sum of its neighbors' importance. Captures recursive influence: being connected to well-connected nodes matters more than raw degree. Power iteration method used for computation.

**PageRank** (Page et al. 1998; Brin & Page 1998) — variant of eigenvector centrality with damping factor, originally for web ranking. Distinguished from eigenvector by handling directed graphs and incorporating a teleportation (random jump) probability that prevents rank sinks. Essential for directed networks: financial flows, citation networks, web linkages.

**Katz Centrality** (Katz 1953) — predecessor to both eigenvector and PageRank. Includes a baseline importance term so even nodes with no incoming links from important neighbors get non-zero scores.

### Advanced Measures

**Percolation Centrality** (Piraveenan, Prokopenko & Hossain 2013, *PLOS ONE*) — weights betweenness by node percolation state. Valuable for modeling information spread, disease propagation, and cascading failure in infrastructure networks where some nodes are already "infected" or "failed."

**Centrality Stability** (Ghoshal & Barabasi 2011, *Nature Communications*) — not all centrality rankings are robust to network perturbation. Identifies "super-stable" nodes whose rankings persist under noise, vs. fragile rankings that shift with small changes.

### Choosing a Centrality Measure

No single measure is universally correct. Selection depends on the question:
- **Who is most connected?** → Degree
- **Who can reach everyone fastest?** → Closeness
- **Who controls information flow?** → Betweenness
- **Who is connected to the influential?** → Eigenvector
- **Who ranks high in directed flows?** → PageRank
- **Whose removal cascades?** → Percolation

---

## Community Detection

Community detection partitions a network into densely connected subgroups with sparser between-group connections. Fundamental to understanding organizational structure, coordinated behavior, and hidden relationships.

### Classical Methods

**Girvan-Newman Algorithm** (Girvan & Newman 2002, *PNAS*; Newman & Girvan 2004, *Phys. Rev. E*) — divisive: iteratively removes edges with highest betweenness, progressively breaking the network into communities. Computational cost O(|V|·|E|²) limits scalability beyond thousands of nodes.

**Modularity Maximization** — modularity Q (Newman 2006) measures the fraction of edges within communities minus expected fraction in a random network. Maximizing Q is NP-hard; practical algorithms approximate it:

- **Louvain Algorithm** (Blondel et al. 2008, *J. Stat. Mech.*) — greedy agglomerative: iteratively moves nodes to neighboring communities to maximize modularity gain, then aggregates communities into super-nodes and repeats. O(N·log N) complexity makes it practical for million-node networks. Known limitation: can produce arbitrarily badly connected communities.

- **Leiden Algorithm** (Traag, Waltman & van Eck 2019, *Scientific Reports*) — addresses Louvain's connectedness problem with a three-phase approach: local movement, refinement, aggregation. Guarantees well-connected communities while matching Louvain's speed. **Current recommended default.**

**Infomap** (Rosvall & Bergstrom 2007, *PNAS*, arXiv:physics/0612035) — information-theoretic: finds the partition that minimizes the description length of a random walk on the network. Treats community detection as a compression problem. Excels at detecting flow-based communities where direction matters.

### Stochastic Block Models (SBM)

SBM is a generative model: given community assignments, edges exist with probability depending on community membership. Inverts via Bayesian inference to find the most likely partition.

- **Detectability threshold** (Decelle, Krzakala, Moore & Zdeborova 2011, *Phys. Rev. Lett.*, arXiv:1102.1182) — community structure is only detectable above a critical signal-to-noise ratio. Below this threshold, no algorithm can recover communities better than chance.

- **Degree-corrected SBM** (Karrer & Newman 2011; Yan et al. 2014, *J. Stat. Mech.*, arXiv:1207.3994) — accounts for heterogeneous degree distributions, preventing high-degree nodes from dominating inference.

- **Bayesian SBM with nested models** (Peixoto 2013, *Phys. Rev. Lett.*; Peixoto 2019, arXiv:1705.10225) — uses minimum description length principle to select both the number of blocks and hierarchical structure, avoiding overfitting.

### Overlapping Communities

Real-world networks exhibit overlapping community membership (individuals belong to multiple social circles). Key approaches:

- **Clique Percolation Method** (Palla, Derenyi, Farkas & Vicsek 2005, *Nature*) — finds overlapping communities as unions of k-cliques that share k-1 nodes.

- **Mixed Membership SBM** (Airoldi et al. 2008; Gopalan & Blei 2013, *PNAS*) — each node has a distribution over communities rather than a single assignment.

### Evaluation and Benchmarks

- **LFR Benchmark** (Lancichinetti, Fortunato & Radicchi 2008, *Phys. Rev. E.*, arXiv:0805.4770) — generates networks with known community structure, heterogeneous degree and community size distributions.

- **Normalized Mutual Information (NMI)** — standard metric comparing detected vs. ground-truth partitions.

### Graph Neural Networks for Community Detection

Since ~2020, deep learning has transformed community detection. GNNs combine structural topology with node attributes through message passing, enabling joint optimization over graph structure and feature space — a significant advance over purely structural classical methods.

**Graph Convolutional Networks (GCNs) for Community Detection** — early approaches trained GCNs to maximize modularity, but often converged to suboptimal solutions (Shehzad et al. 2025, IJCAI, arXiv:2505.10197). GCN-based methods integrate local structure and node attributes, incorporating various optimization strategies.

**GSEC Framework** (2025, *ScienceDirect*) — a hybrid-guided paradigm integrating sparse prior knowledge at both structural and objective levels, enabling accurate community detection without requiring the number of communities to be pre-specified.

**GNN Robustness** (2025, *Physical Review*) — GNN-based community detection faces perturbation vulnerabilities. Targeted attacks on node attributes can degrade community recovery quality, and robustness varies significantly across GNN architectures.

**Key Reference:** Frontiers in AI systematic review (2025) identifies GNNs, autoencoders, and CNNs as the most commonly used deep learning approaches for community detection in social networks.

### Graph Transformers

Graph transformers (Shehzad et al. 2024, arXiv:2407.09777) represent the frontier beyond GNNs, using self-attention mechanisms to capture global graph dependencies that local message-passing GNNs miss.

**Core innovation:** While GNNs aggregate information from local neighborhoods (k-hop), graph transformers can attend to any node pair directly, overcoming the "over-squashing" problem where information from distant nodes is compressed through narrow bottlenecks.

**Community-Aware Graph Transformer (CoGT)** (2025, *Springer*) — introduces a node-community-global hierarchical aggregation framework that preserves community-level semantics while reducing information volume. Addresses both over-squashing and over-smoothing problems simultaneously.

**Graph Transformer for Overlapping Community Detection** (2026, *ScienceDirect*) — jointly performs overlapping community detection and link prediction using graph transformers, handling dynamic complex networks where node memberships are fluid and multi-faceted.

**Integrated GNN-Transformer architecture** (2025, *IEEE*) — combines GNN local pattern extraction with transformer global attention for community detection, leveraging local and global information from complex social network structures.

### Scalable Community Detection for Billion-Node Graphs

Real-world OSINT datasets (social media follower graphs, financial transaction networks) routinely exceed millions of nodes. Classical algorithms break at this scale.

**Hierarchical approaches:**
- **Community-based coarsening** — cluster local neighborhoods into super-nodes, run community detection on the coarse graph, then refine within each super-community. Reduces effective node count by orders of magnitude.
- **Label propagation with pruning** — iterative label propagation with early stopping on stable nodes. Linear in number of edges, parallelizable.

**Streaming and dynamic algorithms:**
- **Incremental Louvain** — when the graph changes (new edges, new nodes), recompute only affected communities rather than the full partition.
- **Sliding-window temporal community detection** — maintain communities over a fixed time window, dropping stale edges and incorporating new ones incrementally.

**Hardware-aware implementations:**
- GPU-accelerated Leiden (RAPIDS cuGraph) for million-node graphs at interactive speeds
- Graph-tool SBM inference with OpenMP parallelism scales to tens of millions of nodes on multi-core CPUs

---

## Temporal Network Evolution

Most real-world networks evolve over time. Static analysis captures snapshots; temporal analysis captures dynamics.

### Dynamic Graph Models

**Evolving Networks** (Dorogovtsev & Mendes 2003; Barrat, Barthelemy & Vespignani 2008) — networks grow via preferential attachment (Barabasi & Albert 1999), producing scale-free degree distributions. Real networks often exhibit more complex growth: aging of nodes, fitness-based competition, and edge rewiring.

**Temporal Networks** (Holme & Saramaki 2012, *Physics Reports*) — represent edges as timestamped events rather than static connections. Enables analysis of time-respecting paths, temporal motifs, and burstiness patterns.

### Temporal Centrality

Standard centrality assumes static topology. Temporal centrality extends measures to time-respecting paths:

- **Temporal betweenness** — fraction of time-respecting shortest paths passing through a node
- **Temporal closeness** — inverse of average temporal distance to all other nodes

Critical for OSINT: an intermediary who only appeared during a specific 48-hour window may be invisible to static analysis but crucial to understanding a transaction sequence.

### Change-Point Detection

Detecting when network structure changes — new communities emerging, existing communities merging, hubs shifting. Statistical methods based on edge-density comparisons between time windows. Connected to [[entropy-as-signal]]: entropy of community assignments over time as a regime-change signal.

---

## Layout & Visualization

Visualization is analysis, not decoration. Layout choices reveal or obscure network structure.

### Force-Directed Layouts

**Fruchterman-Reingold** (1991) — physically-inspired: nodes repel each other, edges act as springs pulling connected nodes together. Produces aesthetically pleasing layouts where community structure is visually apparent. O(N²) per iteration; practical for thousands of nodes.

**ForceAtlas2** (Jacomy et al. 2014, *PLOS ONE*) — variant designed for real-world networks with heterogeneous degree distributions. Addresses the "hairball" problem of Fruchterman-Reingold by using degree-dependent repulsion and gravity, preventing high-degree hubs from collapsing into the center.

**OpenOrd** (Martin et al. 2011) — designed for very large networks. Uses simulated annealing with an initially random layout that progressively freezes into community structure. Handles million-node networks.

### Geographic Overlay

For networks with spatial coordinates (IP geolocation, physical addresses, territory), geographic mapping reveals spatial patterns: operational regions, jurisdictional boundaries, physical accessibility constraints.

### Tool Ecosystem

| Tool | Strength | Scale Limit | Notes |
|------|----------|-------------|-------|
| **NetworkX** (Hagberg et al. 2008) | Python ecosystem; algorithm richness | ~100K nodes in-memory | Pure Python; scales to limits of RAM |
| **igraph** (Csardi & Nepusz 2006) | High-performance C core with R/Python/Mathematica bindings | Millions of nodes | Preferred for large-scale computation |
| **graph-tool** (Peixoto 2014) | Python; SBM inference built-in | Millions of nodes | C++ core with OpenMP parallelism |
| **Gephi** (Bastian et al. 2009) | Interactive exploration GUI | ~100K nodes interactive | ForceAtlas2 default layout; plugin ecosystem |
| **Cytoscape** (Shannon et al. 2003) | Biological network visualization; large plugin library | ~100K nodes | Extensible via apps |
| **Neo4j Bloom** | Graph database visualization | Database-backed | Query-visualize-analyze cycle; property graph native |

### Large-Scale Rendering

For networks exceeding visualization tool limits:
- **Edge bundling** (Holten 2006) — routes edges along similar paths, reducing visual clutter
- **Community-based coarsening** — visualize community-level graph first, drill into communities on demand
- **Matrix-based representations** — adjacency matrices avoid the hairball problem entirely for dense networks

---

## Network Analysis in OSINT

### Core Patterns

**Pivot Chains as Graph Traversal** — OSINT investigations naturally produce graphs: a phone number connects to an email, which connects to a social media profile, which connects to a domain registration. Each "pivot" is an edge; each entity is a node. Graph traversal formalizes what investigators do manually.

**Corporate Ownership Networks** — shareholders, subsidiaries, and beneficial owners form directed graphs. Centrality reveals control chains; community detection surfaces beneficial ownership clusters obscured by layered holding structures. This is the methodology behind ICIJ's Offshore Leaks and Pandora Papers investigations.

**Social Media Follower/Retweet Networks** — follower graphs can reveal coordinated inauthentic networks: clusters of accounts that share unusually similar follower sets. Retweet cascades reveal information diffusion patterns and coordinated amplification.

**Campaign Finance & Lobbying Networks** — donor-recipient bipartite graphs become influence networks when projected. Betweenness identifies intermediaries connecting donors to beneficiaries across multiple steps.

**Infrastructure Dependency Graphs** — critical infrastructure sectors depend on each other (power → telecommunications → financial → power). Graph analysis identifies single points of failure and cascading failure pathways. See [[electric-utility-critical-infrastructure]].

### Entity Resolution → Graph Construction

Entity resolution (deduplication across datasets) is the prerequisite for network construction. See [[knowledge-graph-construction]] for formal reconciliation of property graphs and RDF triplestores (Hartig 2014, arXiv:1409.3288; G2GML 2022), entity resolution algorithms (Fellegi-Sunter, neural ER), and ingestion patterns from heterogeneous sources.

### Analytical Workflow

1. **Data Acquisition** — source documents, databases, OSINT collection
2. **Entity Extraction & Resolution** — deduplicate entities across sources
3. **Graph Construction** — nodes for resolved entities, edges for relationships found
4. **Exploratory Analysis** — centrality ranking, community detection, degree distribution characterization
5. **Targeted Hypothesis Testing** — "Does X connect to Y within 3 hops?" "Which community does Z belong to?"
6. **Visualization & Reporting** — force-directed layouts for narrative illustration; metric tables for analytical rigor

---

## Exocortex Integration Patterns

### Graph Construction from Exocortex Memory

The Exocortex knowledge graph (shared persistent memory between team members) is itself a network. Community detection on entity co-occurrence graphs surfaces thematic clusters. Centrality analysis identifies high-connectivity concepts that serve as bridges between knowledge domains.

### Entropy-as-Signal for Regime Change Detection

Network community structure entropy over time is a regime-change signal (connected to [[entropy-as-signal]]). Phase transitions in community assignment entropy indicate structural shifts in the underlying network — new entities entering, existing entities changing roles, communities merging or splitting.

### Entity Resolution Pipeline Integration

OpenPlanter's entity_resolution.py (753 lines) implements Fellegi-Sunter Bayesian record linkage and cross_link_analysis.py (585 lines) for cross-jurisdictional data linking (see [[cross-jurisdictional-data-linking]]). Network analysis is the downstream consumer: resolved entities become graph nodes, probabilistic match scores become edge weights, and community detection surfaces non-obvious organizational structures obscured by layered entity aliases.

### Sanctions & Supply Chain Graph Analysis

Network analysis directly supports [[supply-chain-economic-warfare]] and [[geopolitics-strategic-analysis]] through:
- **Sanctions evasion detection** — community structure in corporate ownership graphs reveals clusters of related shell companies (see [[domain-whois-dns-investigation]] for WHOIS graph construction)
- **Supply chain dependency mapping** — graph centrality identifies single points of failure in critical supply chains (rare earth processing, semiconductor fabrication)
- **Financial flow tracing** — PageRank on directed transaction graphs surfaces key intermediaries in sanctions-circumvention networks

### Tool Integration

NetworkX is the primary Python library for graph construction and analysis within Exocortex. igraph provides high-performance alternatives for large-scale community detection. Neo4j serves as the persistent graph database backend, enabling Cypher queries over stored entity-relationship networks.

---

## Primary Sources

### Classical & Foundational
- Freeman, L.C. (1979). "Centrality in social networks: Conceptual clarification." *Social Networks* 1:215-239.
- Bonacich, P. (1987). "Power and centrality: A family of measures." *American J. Sociology* 92(5):1170-1182.
- Barabasi, A.-L. & Albert, R. (1999). "Emergence of scaling in random networks." *Science* 286:509-512.
- Girvan, M. & Newman, M.E.J. (2002). "Community structure in social and biological networks." *PNAS* 99(12):7821-7826.
- Blondel, V.D., Guillaume, J.-L., Lambiotte, R., & Lefebvre, E. (2008). "Fast unfolding of communities in large networks." *J. Stat. Mech.* P10008.
- Traag, V.A., Waltman, L., & van Eck, N.J. (2019). "From Louvain to Leiden: guaranteeing well-connected communities." *Scientific Reports* 9:5233.
- Rosvall, M. & Bergstrom, C.T. (2007). "An information-theoretic framework for resolving community structure in complex networks." *PNAS* 104(18):7327-7331. arXiv:physics/0612035.
- Holme, P. & Saramaki, J. (2012). "Temporal networks." *Physics Reports* 519(3):97-125.

### Advanced & Domain-Specific
- Decelle, A., Krzakala, F., Moore, C., & Zdeborova, L. (2011). "Inference and phase transitions in the detection of modules in sparse networks." *Phys. Rev. Lett.* 107:065701. arXiv:1102.1182.
- Peixoto, T.P. (2013). "Parsimonious module inference in large networks." *Phys. Rev. Lett.* 110:148701. arXiv:1212.4794.
- Peixoto, T.P. (2019). "Bayesian stochastic blockmodeling." In *Advances in Network Clustering and Blockmodeling*. arXiv:1705.10225.
- Piraveenan, M., Prokopenko, M., & Hossain, L. (2013). "Percolation centrality: Quantifying graph-theoretic impact of nodes during percolation in networks." *PLOS ONE* 8(1):e53095.
- Lawyer, G. (2015). "Understanding the spreading power of all nodes in a network: a continuous-time perspective." *Scientific Reports* 5:8665. arXiv:1405.6707.
- Jacomy, M., Venturini, T., Heymann, S., & Bastian, M. (2014). "ForceAtlas2, a continuous graph layout algorithm for handy network visualization." *PLOS ONE* 9(6):e98679.
- Palla, G., Derenyi, I., Farkas, I., & Vicsek, T. (2005). "Uncovering the overlapping community structure of complex networks in nature and society." *Nature* 435:814-818. arXiv:physics/0506133.
- Lancichinetti, A., Fortunato, S., & Radicchi, F. (2008). "Benchmark graphs for testing community detection algorithms." *Phys. Rev. E* 78:046110. arXiv:0805.4770.
- Clauset, A., Moore, C., & Newman, M.E.J. (2008). "Hierarchical structure and the prediction of missing links in networks." *Nature* 453:98-101. arXiv:0811.0484.
- Ghoshal, G. & Barabasi, A.-L. (2011). "Ranking stability and super-stable nodes in complex networks." *Nature Communications* 2:394.

### Graph Neural Networks & Transformers
- Shehzad, A., Xia, F., et al. (2024). "Graph Transformers: A Survey." arXiv:2407.09777.
- Shehzad, A., Xia, F., et al. (2025). "Advancing Community Detection with Graph Convolutional Neural Networks." *IJCAI 2025*. arXiv:2505.10197.
- GATFELPA: "Integrates graph attention networks and enhanced label propagation." *Nature Scientific Reports* (2025).
- "Community-Aware Graph Transformer (CoGT): Preserving Community Semantics." *Springer* (2025).
- "Graph Transformer-Based Overlapping Community Detection for Link Prediction." *ScienceDirect* (2026).
- IEEE: "Graph Integrated Transformers for Community Detection in Social Networks" (2025).
- Frontiers in AI: "A systematic review of deep learning methods for community detection" (2025).

---

## Cross-Domain Connections

- [[human-investigation-osint]] — OSINT pivot chains as graph traversal; phone/email pivot chains produce naturally graph-structured investigation data
- [[knowledge-graph-construction]] — entity resolution as the prerequisite for graph construction; property graphs vs. RDF; Neo4j vs. NetworkX scaling
- [[cross-jurisdictional-data-linking]] — OpenPlanter's entity resolution pipeline (753L entity_resolution.py) feeds resolved entities into graph construction
- [[markets-financial-analysis]] — supply chain networks, financial contagion propagation, transaction graph anomaly detection
- [[history-of-intelligence-operations]] — link analysis in intelligence tradecraft (Anacapa charts, association matrices); graph-based counterintelligence analysis of competing hypotheses
- [[privacy-cryptography]] — metadata graph analysis for de-anonymization; traffic analysis as graph traversal
- [[electric-utility-critical-infrastructure]] — infrastructure dependency graphs; SCADA network topology analysis; single-point-of-failure identification via centrality analysis
- [[geopolitics-strategic-analysis]] — supply chain and influence networks; sanctions enforcement via corporate ownership graph analysis
- [[supply-chain-economic-warfare]] — sanctions evasion detection through community detection on corporate ownership graphs; rare earth supply chain dependency mapping
- [[entropy-as-signal]] — community assignment entropy as regime-change signal for detecting structural shifts in monitored networks
