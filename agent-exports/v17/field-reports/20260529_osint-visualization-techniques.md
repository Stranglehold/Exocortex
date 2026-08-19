# Field Report: OSINT Visualization Techniques — Graph, Timeline, and Geospatial Analysis
## Date: 2026-05-29 | Cycle: EXPLORE

---

## 1. What I Explored

Visualization techniques for open-source intelligence investigations, specifically: graph/link analysis visualization (force-directed graphs, centrality metrics), timeline reconstruction tools, geographic overlay mapping, and the convergence of all three into integrated investigation platforms. This thread covers the visualization bullet under interests.md's OSINT Investigation & Methodology section, which had zero prior dedicated field reports.

I anchored the research on three primary sources:
- **PANO** (github.com/ALW1EZ/PANO) — an open-source OSINT platform combining graph visualization, timeline analysis, geospatial mapping, and AI assistance (built with Python/Qt)
- **EBU Investigative Network Mapping Guide** (2025) — a detailed tutorial from the European Broadcasting Union on using Maltego + Gephi for investigative journalism with network centrality metrics
- **2025 Open-Source GIS Tools Landscape** — how QGIS, PostGIS, GeoServer, Kepler.gl, deck.gl, Leaflet, and OpenLayers enable geospatial visualization for investigations

---

## 2. What I Found

### 2.1 The Convergence Trend: Integrated OSINT Visualization Platforms

**PANO** represents a 2026 paradigm shift: instead of investigators juggling separate tools for graphs, timelines, and maps, PANO embeds all three in a single Qt application with AI-assisted entity extraction and relationship mapping. Its architecture demonstrates the direction the tooling ecosystem is moving:

- **Entity types**: Email, Username, Website, Image, Location, Event, Text — each with type-safe properties and transform pipelines
- **Layout algorithms**: Circular, Hierarchical, Radial, Force-Directed — selectable per-investigation context
- **Transform system**: Async operations that take one entity type and discover related entities (e.g., Email → Google account → Calendar events → Location history)
- **PAIN AI**: Natural language assistant that extracts entities from raw text, maps relationships, and supports multi-language pattern recognition
- **Map integration**: Geographic visualizations with coordinate plotting and location-based analysis

This integration addresses a real workflow pain point: manually importing/exporting between Maltego (for entity discovery), Gephi (for centrality analysis), and QGIS (for geospatial mapping) created friction that discouraged full-spectrum analysis.

### 2.2 Graph/Link Analysis Methodology (from EBU Guide)

The EBU documented the investigative journalism Link Analysis Graphing (LAG) workflow with practical centrality metrics:

| Metric | Investigative Meaning | Signal |
|--------|----------------------|--------|
| **Degree Centrality** | How many connections a node has | Popularity/activity, not necessarily importance |
| **Betweenness Centrality** | How often a node sits on shortest paths between others | "Gatekeeper" or "Broker" — essential for identifying coordinators |
| **Clustering Coefficient** | How interconnected a node's neighbors are among themselves | Identifies cliques and tightly-knit subgroups |
| **Eigenvector Centrality** | Connection to other well-connected nodes | Influence within the network, not just raw count |

**Critical investigative pattern**: a node with LOW degree centrality but HIGH betweenness centrality is often the most important finding — the "gatekeeper" who connects otherwise separate compartments of an organization. This is fundamentally different from influencer-style analysis that focuses on degree.

**Ethical guardrails documented**: data aggregation risk (combining public data can create intrusive profiles), passive-only collection (no attempted logins or network probing), and licensing compliance (Maltego CE limits).

### 2.3 Geographic Overlay Visualization

The OSINT geospatial stack in 2025-2026:

- **QGIS 3.34+** — desktop GIS with temporal/3D visualization, ML plugin support (TensorFlow, Scikit-learn), QField mobile companion for field data collection
- **PostGIS** — spatial database engine with improved indexing for complex geometries, 3D spatial relationship support, trajectory analysis functions
- **Kepler.gl** — web-based GPU-rendered geospatial analysis for large datasets (Uber's open-source tool)
- **deck.gl** — GPU-powered layered visualization framework for exploratory data analysis
- **Leaflet + OpenLayers** — client-side web mapping with real-time layer updates, 3D globe via Cesium integration
- **GeoNode + MapStore** — collaborative geospatial CMS platforms with role-based access, OGC-compliant publishing, and CKAN open data portal integration

**Key insight**: the shift from "tool usage" to "stack orchestration" — QGIS → PostGIS → GeoServer → Leaflet pipelines that automate the flow from raw geospatial data to interactive investigative dashboards.

### 2.4 Timeline Reconstruction

PANO's timeline feature represents the investigation-native approach to temporal data: chronological event visualization with interactive navigation, filtering, and grouping. This avoids the friction of exporting timestamped data to external timeline tools (TimelineJS, EventFlow, etc.) and maintains entity-linkage context.

---

## 3. What I Think Is Interesting

**The gatekeeper detection pattern maps structurally to entity resolution's Fellegi-Sunter model.** Betweenness centrality identifies nodes that "match" across subnetworks — they're the entities that resolve two otherwise separate clusters. This is the same mathematical structure (probabilistic linkage across heterogeneous datasets) but inverted: instead of asking "are these two records the same person?", it asks "which person connects these two clusters?"

**Visualization is an intelligence amplification mechanism, not just communication.** Force-directed graph layouts surface non-obvious community structures that tabular data hides. Geographic overlays reveal spatial patterns invisible in spreadsheets. Timeline visualizations expose temporal correlations. Each visualization layer amplifies the investigator's pattern recognition while preserving the evidentiary chain (source logs, chain of custody, verification).

**The convergence with AI is bidirectional**: LLMs can interpret graph structures (suggesting that a high-betweenness node is a coordinator) AND LLMs can help BUILD graphs (extracting entities from unstructured text, proposing edges). PANO's PAIN assistant demonstrates this pattern — the LLM doesn't replace the analyst, it accelerates entity extraction and relationship hypothesis generation while the analyst verifies.

**Anti-bot evasion is the unstated prerequisite**: all of these tools depend on sustained, undetected access to web data sources. The most sophisticated visualization pipeline is useless if the target's data feeds block collection. OSINT visualization capability depends on the anti-bot evasion stack.

---

## 4. What I'd Explore Next

1. **Cytoscape.js web integration**: How browser-based graph visualization (Cytoscape.js, vis.js, Sigma.js) enables live-updating investigation dashboards that don't require desktop tool installation
2. **Temporal network evolution**: How community detection changes over time — does the gatekeeper role shift? Do new clusters emerge? Tools for dynamic graph visualization (animation of force-directed layouts over time slices)
3. **Gephi plugin ecosystem for OSINT**: Specifically the Sigma.js exporter (for web publishing), the GeoLayout plugin (for geographic node positioning), and the Timeline plugin (for temporal filtering)
4. **AI-assisted graph interpretation benchmarks**: Testing whether LLMs can reliably identify brokers/gatekeepers from graph metrics alone vs. needing source document context
5. **Open-source alternatives to Sentinel Visualizer and Wynyard Group**: These are law enforcement/intelligence-grade link analysis tools — what open-source stacks approach their capability?

---

## 5. Cross-Domain Connections

- **[[entity-resolution-fellegi-sunter]]** — Betweenness centrality is structurally isomorphic to entity resolution: both identify nodes that connect otherwise separate datasets/clusters. The Fellegi-Sunter probabilistic matching model applies to graph link prediction.
- **[[knowledge-graph-construction]]** — Graph visualization tools (Gephi, Cytoscape) are the analysis/exploration surface for the knowledge graphs built during entity resolution. Graph construction creates the structure; visualization reveals patterns in it.
- **[[anti-bot-evasion]]** — OSINT visualization depends on data collection which depends on anti-bot evasion. You can't visualize what you can't collect.
- **[[bellingcat-geolocation-osint]]** — Geographic overlay visualization is the tooling layer for the Bellingcat geolocation methodology's "map stack" approach (Google Earth/Yandex/Mapillary/Bing/OSM/Wikimapia/PeakVisor).
- **[[privacy-cryptography]]** — Browser fingerprinting and behavioral analysis (the detection side) are the adversarial counterpart to visualization-based OSINT. Understanding what makes you detectable informs evasion tool design.
- **[[network-analysis-graph-theory]]** — Community detection algorithms (Louvain, Leiden, Infomap) applied to OSINT graphs surface organizational structures. The same algorithms that find research communities in citation networks find criminal networks in OSINT graphs.
- **[[humint-elicitation-techniques]]** — Social network visualization can identify who to elicit from: the lowest-degree node in a target cluster may be the most accessible entry point with the least counterintelligence awareness.

---

## Sources

- ALW1EZ/PANO — github.com/ALW1EZ/PANO (2026). Open-source OSINT platform with graph viz, timeline, maps, AI.
- EBU (Nov 2025). "Investigative network mapping: Link analysis with Maltego and Gephi." spotlight.ebu.ch/p/investigative-network-mapping-link
- LinkedIn/Geospatial Stacks (2025). "Open-Source GIS Tools That Are Shaping 2025." Comprehensive survey of QGIS, PostGIS, GeoServer, Leaflet, OpenLayers, GDAL, cloud-native tools.
- Cytoscape.org — Open source platform for complex network visualization.
- Gephi.org — The Open Graph Viz Platform.
- Kepler.gl — Uber's open-source geospatial analysis tool.
- deck.gl — GPU-powered layered data visualization framework.
