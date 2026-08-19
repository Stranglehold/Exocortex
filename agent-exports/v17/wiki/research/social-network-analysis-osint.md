# Social Network Analysis for OSINT Investigation

**Status: STABLE**
**Topic Slug: social-network-analysis-osint**
**Created: 2026-07-18 | Deepened: 2026-08-02**
**Domain: OSINT & Entity Resolution**

---

## Overview

Social network analysis (SNA) applies graph theory and sociological network theory to OSINT investigations, transforming platforms' social graph data into actionable intelligence about individuals, organizations, and influence networks. While [[network-analysis-techniques-osint]] covers the mathematical and algorithmic foundations (centrality, community detection, temporal evolution), this page focuses on the **operational application to social media platforms**: extracting social graphs, analyzing connection patterns, mapping influence networks, and correlating identities across platforms via social graph isomorphism.

The core OSINT value proposition: **social graphs are behavioral fingerprints**. Unlike static attributes (name, email, IP address) that can be changed or obscured, the structure of an individual's social connections — who they follow, who follows them, interaction frequency, group memberships — forms a persistent, high-dimensional signature that survives platform migration and pseudonym changes (Granovetter 1973, Burt 1992). The Exocortex v16 field report on OSINT network analysis (2026-06-28) established that OSINT investigations are fundamentally graph traversal problems, and SNA formalizes what investigators do manually.

---

## Social Graph Data Sources

### Platform-Specific Graph Structures

| Platform | Graph Type | Data Available | Extraction Difficulty |
|----------|-----------|----------------|----------------------|
| **Facebook** | Undirected friendship graph | Friends list, mutual friends, group memberships, event co-attendance | High (post-Cambridge Analytica lockdown) |
| **Twitter/X** | Directed follower/following graph | Followers, following, retweet/reply/mention networks, list memberships | Medium (API v2 rate-limited but accessible) |
| **LinkedIn** | Professional connection graph | 1st/2nd/3rd-degree connections, company affiliations, skill endorsements | High (aggressive anti-scraping) |
| **Instagram** | Directed follow graph + interaction network | Followers/following, likes, comments, story views, tagged relationships | Medium-High (graph API locked down) |
| **Reddit** | Content-interaction graph | Subreddit memberships, post/comment networks, moderator relationships | Low-Medium (public API, pushshift.io archives) |
| **Discord** | Server-based membership graph | Server memberships, channel activity, role hierarchies | Low (API accessible with token) |
| **Telegram** | Group/channel membership | Group memberships, message forwarding patterns, admin hierarchies | Low-Medium (MTProto API) |
| **TikTok** | Content-driven follow network | Followers/following, duet/stitch networks, hashtag co-participation | High (limited API) |
| **WhatsApp** | Encrypted group membership | Group membership (via phone number correlation) | Very High (encrypted, no public API) |

### Graph Extraction Techniques

1. **API-based extraction**: Twitter API v2, Reddit API, Telegram MTProto, Discord Gateway API
2. **Web scraping**: Selenium/Playwright for LinkedIn connections, Instagram followers
3. **OSINT tool automation**: Maltego transforms, SpiderFoot HX modules, Holehe for account discovery
4. **Data breach correlation**: Linking leaked social graphs from breach databases (see [[data-breach-analysis-osint-identity-linkage]])
5. **Metadata extraction**: EXIF social media upload timestamps, geotags for timeline reconstruction

---

## Social Network Theory for OSINT

### Weak Ties and Information Access

Granovetter's (1973) weak ties theory: loose acquaintances provide access to novel information unavailable within dense clusters. In OSINT: targeting an individual's weak ties (distant LinkedIn connections, non-mutual Twitter follows) reveals information networks the subject draws upon — suppliers, contractors, confidential informants, intelligence handlers. This maps directly to the OSINT entity resolution pentagon identified in the v17 campaign finance wiki: corporate registries → lobbying disclosure → government contracts → property records → campaign finance, where weak organizational ties often signal hidden beneficial ownership.

### Structural Holes

Burt's (1992) structural hole theory: individuals who bridge otherwise disconnected network clusters wield disproportionate influence. In OSINT: identifying brokerage positions reveals gatekeepers, fixers, and intermediaries who connect otherwise separate networks (criminal organizations, corporate entities, political groups). The v17 wiki on [[network-analysis-techniques-osint]] documents betweenness centrality as the primary metric for detecting these brokerage positions, with Python/NetworkX implementations.

### Homophily and Entity Resolution

McPherson's homophily principle (2001): similar individuals cluster together. In OSINT: social graph homophily enables identity correlation — if two accounts on different platforms share structurally similar neighborhoods (same high-centrality nodes, same community memberships), they likely represent the same individual even under different usernames. This technique is applied to campaign finance donor networks (v17 wiki: [[campaign-finance-entity-resolution]]) using GNN-based entity resolution on graph structure alone.

### Information Diffusion and Influence Mapping

Diffusion of innovations (Rogers, 1962) and viral cascade models: tracking how information propagates through social graphs identifies opinion leaders, echo chambers, coordinated inauthentic behavior, and influence operation infrastructure (see [[influence-operations-detection-countermeasures]]). The v16 Exocortex field report established that temporal network evolution — tracking how edges form and dissolve — reveals coordination patterns invisible in static graphs.

---

## OSINT Investigation Workflow

### Phase 1: Discovery — Seed Account Identification
- Start with known identifiers (email, phone, username) from [[phone-number-investigation-osint]], [[email-investigation-osint]], [[reverse-image-search-osint]]
- Use Sherlock/Maigret/Holehe to discover accounts across platforms
- Validate account authenticity (creation date, posting frequency, content quality)

### Phase 2: Extraction — Graph Data Collection
- Extract follower/following lists via API or scraping
- Collect interaction data (replies, mentions, retweets, comments)
- Capture group/channel memberships
- Timestamp all data for temporal analysis

### Phase 3: Enrichment — Attribute Layer Addition
- Cross-reference nodes with [[corporate-registry-investigation-osint]], [[dns-whois-investigation-osint]]
- Add entity resolution labels from [[financial-intelligence-entity-resolution]]
- Tag known threat actors from sanctions lists, law enforcement databases

### Phase 4: Analysis — Graph Computation
- Compute centrality measures (degree, betweenness, closeness, eigenvector/PageRank) — see [[network-analysis-techniques-osint]] for mathematical detail
- Run community detection (Louvain, Leiden, Infomap) from the v17 wiki implementation guide
- Identify structural holes and brokerage positions
- Perform temporal analysis for network evolution and coordination detection (arXiv:2102.10014, arXiv:2103.02504)

### Phase 5: Identity Correlation — Cross-Platform Resolution
- Compare ego networks across platforms for structural similarity
- Apply graph isomorphism heuristics for account matching
- Use embedding-based alignment (node2vec, GraphSAGE) for automated matching — GNN approaches documented in arXiv:2111.15367
- Validate matches with non-graph signals (timeline correlation, linguistic fingerprinting)

---

## Tool Ecosystem

| Tool | Platform | Capability | Output |
|------|----------|-----------|--------|
| **Maltego** | Multi-platform | Graph visualization, transforms for social media pivoting | Interactive graph |
| **SpiderFoot HX** | Multi-platform | Automated recon with social media modules | CSV, GEXF, JSON |
| **Gephi** | Cross-platform | Large-scale graph visualization, community detection | Interactive visualization |
| **Cytoscape** | Cross-platform | Network analysis with plugin ecosystem | Interactive graph |
| **NetworkX** | Python | Programmatic graph analysis, centrality, community detection | Python objects |
| **igraph** | Python/R/C | High-performance graph algorithms | Graph objects |
| **Snscrape** | Multi-platform | Social network scraping for Twitter, Facebook, Instagram, Reddit | JSON, CSV |
| **NodeXL** | Excel | SNA for Excel users, social media import templates | Excel workbook |

---

## Cross-Domain Connections

1. **Network Analysis Techniques for OSINT** — Mathematical foundation for centrality, community detection, link prediction applied here to social media data
2. **Entity Resolution Pipeline Performance** — Social graph isomorphism as a high-dimensional matching feature for cross-platform identity resolution
3. **Influence Operations Detection & Countermeasures** — SNA for mapping coordinated inauthentic behavior, bot networks, and information warfare infrastructure
4. **Data Breach Analysis for OSINT Identity Linkage** — Breach-derived social graphs as ground truth for cross-platform correlation validation
5. **Metadata Analysis for OSINT** — EXIF timestamps and geotags complementing social graph temporal analysis for timeline reconstruction
6. **Reverse Image Search for OSINT** — Profile photo cross-referencing combined with social graph matching for multi-signal identity confidence
7. **Financial Intelligence (FININT) for Entity Resolution** — Social graph analysis applied to payment networks, SWIFT correspondent banking relationships, and shell company director interlocks
8. **Corporate Registry Investigation for OSINT** — Director/officer interlock networks as a specialized social graph for beneficial ownership tracing
9. **Visualization Techniques for OSINT** — Force-directed layouts, geographic overlays, and timeline visualization for social graph presentation
10. **HUMINT Tradecraft for OSINT Methodology** — Social network elicitation techniques and access-agent recruitment patterns mapped to social graph analysis

---

## Deepening — Operational SNA Workflows, Coordinated Behavior & 2026 Frontier (2026-08-02)

### SNA as a Behavioral-Fingerprint Signal for Entity Correlation

Exocortex v17 corpus grounding for this page (2026-07-08 social-media-forensics field report, influence-operations-detection wiki, knowledge-graph-construction-patterns wiki) reinforces that **behavioral signals derived from network structure — link velocity, topology, and interaction timing — are directly usable as entity-correlation features**. Cross-platform identity resolution therefore treats the social graph as a high-dimensional matching feature, not just a discovery surface: two profiles sharing a statistically unlikely overlap of neighbors, communities, or interaction rhythms are candidates for the same underlying actor even when names and emails differ.

### Key Operational Patterns

1. **Coordinated inauthentic behavior detection**: community detection (Louvain modularity, range 0.5–1.0; worked example 0.79 on a Powerlaw cluster graph — Python Data Science Essentials, p.292) plus centrality/outlier analysis identifies synchronized account clusters; interaction-graph features (posting velocity, retweet/mention topology) discriminate organic from coordinated behavior.
2. **Ego-network profiling**: the target's immediate neighborhood (alters, tie strength, structural holes) yields recruitment, influence, and affiliation intelligence; Burt structural holes identify brokers who connect otherwise-disconnected communities.
3. **Temporal SNA**: tie-formation velocity and stability over time are stronger signals than snapshot degree — rapid parallel tie formation across accounts is a coordination signature (Kossinets & Watts 2006).
4. **Graph deanonymization risk**: degree/topology-based re-identification (Narayanan & Shmatikov 2009) shows sparse anonymous graphs are surprisingly re-identifiable — the attacker's counterpart to the investigator's cross-platform graph correlation, and the privacy boundary of SNA-OSINT.
5. **Directed-network asymmetry**: in-degree/out-degree ratios distinguish broadcast nodes (high in, low out) from amplifiers/hubs — the structural counterpart of account-role classification in bot studies (Ferrara et al. 2016).

### 2026 Frontier

- **Temporal/learning graph models**: graph neural networks over time-evolving social graphs for early detection of emerging coordination; LLM-assisted SNA for natural-language tie inference from post content.
- **Federated and decentralized platform graphs**: Mastodon federation and Bluesky AT Protocol shift graph extraction from per-platform API to instance/relay crawling — new extraction-difficulty tiers and new correlation surfaces.
- **Resilience metrics**: K-core decomposition and percolation analysis to identify campaign cores that survive account takedowns — directly relevant to adversarial activity assessment.

### Extended Cross-Domain Connections

1. **Privacy-Preserving Entity Resolution** — graph deanonymization is the inverse of PPRL: the same topology that enables cross-platform correlation also enables re-identification of anonymized graphs.
2. **Agentic Self-Learning** — the AI-content-generation vs detection arms race is a multi-agent learning dynamic with structural parallels to self-play RL.
3. **Bridging Local-to-Frontier Model Performance** — detection models over large behavioral datasets must run on local hardware with frontier-comparable accuracy.

### References Added

15. Narayanan, A. & Shmatikov, V. (2009). "De-anonymizing Social Networks." IEEE Symposium on Security & Privacy.
16. Kossinets, G. & Watts, D.J. (2006). "Empirical Analysis of an Evolving Social Network." *Science*, 311(5757).
17. Ferrara, E., Varol, O., Davis, C., Menczer, F. & Flammini, A. (2016). "The Rise of Social Bots." *Communications of the ACM*, 59(7).
## References

1. Granovetter, M. (1973). "The Strength of Weak Ties." *American Journal of Sociology*, 78(6), 1360-1380.
2. Burt, R. (1992). *Structural Holes: The Social Structure of Competition.* Harvard University Press.
3. McPherson, M. et al. (2001). "Birds of a Feather: Homophily in Social Networks." *Annual Review of Sociology*, 27, 415-444.
4. Rogers, E. (1962). *Diffusion of Innovations.* Free Press.
5. Bonaccorsi, G. et al. (2024). "Social Network Analysis: A Practical Guide." *Python Data Science Essentials*, Ch. 5, Packt Publishing.
6. arXiv:2102.10014 — Social Network Analysis methods and applications
7. arXiv:2111.15367 — Graph Neural Networks for financial network analysis
8. arXiv:2103.02504 — Criminal network analysis using graph theory
9. arXiv:2103.08720 — Online entity resolution over streaming data
10. Exocortex v16 Field Report: "OSINT Network Analysis & Graph Intelligence" (2026-06-28)
11. Exocortex v17 Wiki: "Network Analysis Techniques for OSINT" — mathematical foundations
12. Exocortex v17 Wiki: "Campaign Finance Entity Resolution" — SNA for donor networks
13. Exocortex v17 Wiki: "Influence Operations Detection & Countermeasures" — coordinated behavior detection
14. Exocortex v17 Wiki: "Data Breach Analysis for OSINT Identity Linkage" — breach-derived social graphs
