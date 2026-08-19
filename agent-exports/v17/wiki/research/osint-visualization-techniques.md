# OSINT Visualization Techniques — Graph, Timeline, and Geospatial Analysis

**Status:** STABLE
**Original Created:** 2026-05-31 (Build Cycle 164)
**Updated:** 2026-05-31 (Build Cycle 171)

## Overview

Visualization is the synthesis layer of the OSINT stack — the point where collected, resolved, and enriched data becomes an analyst's working surface. Three primary modes dominate: **graph/link analysis** (force-directed graphs, centrality metrics), **timeline reconstruction** (temporal ordering of events, entity state tracking), and **geographic overlay mapping** (spatial correlation, movement tracing). The 2025-2026 trend is toward **integrated platforms** that combine all three into a single investigative workspace, reducing the friction of tool-switching that historically fragmented OSINT analysis.

A parallel trend is **web-based interactive visualization**, enabling live-updating dashboards (Cytoscape.js, vis.js, Sigma.js, deck.gl) that don't require desktop tool installation. AI-assisted graph interpretation is emerging as LLMs become capable of extracting entities from raw text and answering natural-language queries about graph structures.

## 1. Integrated Platforms

**PANO** (github.com/ALW1EZ/PANO, v8.2.8 — 2026) is the current open-source OSINT visualization state of the art. Built with Python 3.11+ and PySide6 (Qt), it combines graph visualization, timeline analysis, geospatial mapping, and AI entity extraction in a single application.

### 1.1 Architecture Components

| Component | Role |
|-----------|------|
| `MainWindow` | Application shell and dock management |
| `GraphManager` | Graph data model — nodes, edges, entity properties |
| `GraphView` | Interactive canvas with `NodeVisual` and `EdgeVisual` |
| `TimelineManager` | Chronological event display and synchronization |
| `MapManager` | Geographic coordinate plotting and map integration |
| `LayoutManager` | Layout algorithms: Circular, Hierarchical, Radial, Force-Directed |
| `StatusManager` | Application state and progress tracking |
| `GroupManager` | Entity grouping and organization |

### 1.2 Entity Types
Email, Username, Website, Image, Location, Event, Text — each with type-safe properties and transform pipelines.

### 1.3 Transform System
Async operations that take one entity type and discover related entities:
- Email → Google account → Calendar events → Location history
- Username → social media profiles → posts → tagged locations
- Image → EXIF metadata → GPS coordinates → geolocation

### 1.4 PANAI — AI Integration
Natural language assistant that:
- Extracts entities from unstructured text
- Maps relationships between entities
- Performs pattern recognition and anomaly detection
- Provides context-aware suggestions considering existing graph state and current time
- Outputs JSON operations to create or update entities and relationships

### 1.5 Other Platforms
- **Sentinel Visualizer** (commercial) — law-enforcement-grade link analysis
- **Wynyard Group** (commercial) — advanced crime analytics
- **i2 Analyst's Notebook** (IBM) — enterprise link analysis
- Open source alternatives are limited, making PANO strategically significant.

## 2. Graph & Network Visualization

### 2.1 Tool Landscape

| Tool | License | Key Capability | Deployment |
|------|---------|----------------|------------|
| Gephi | Open Source | Interactive network viz; sigma.js export | Desktop |
| Cytoscape | Open Source | Plugin ecosystem; general-purpose | Desktop/Java |
| Maltego | Commercial (CE free) | Entity discovery transforms | Desktop |
| Neo4j Bloom | Commercial | Graph DB viz; natural language search | Web/Desktop |
| Graphistry | Commercial (GPU) | GPU-accelerated; millions of edges | Web |
| yEd | Free | Manual graph editing; auto-layout | Desktop |
| Palladio | Open Source | Spreadsheet-to-graph; humanities | Web |
| Linkurious | Commercial | Graph viz for Neo4j; investigation oriented | Web |
| Cytoscape.js | Open Source (MIT) | Pure JS graph library; plugin ecosystem | Web (embedded) |
| vis.js | Open Source (MIT) | Network + timeline + 2D/3D in one library | Web |
| Sigma.js | Open Source (MIT) | WebGL-accelerated; lightweight; large graphs | Web |
| D3.js | Open Source | General-purpose; custom graph builds | Web |

### 2.2 Centrality Metrics for Investigation

| Metric | What It Measures | Investigative Significance |
|--------|------------------|---------------------------|
| **Degree Centrality** | Number of direct connections | Who is most connected? Often the most visible, not always the most important. |
| **Betweenness Centrality** | Fraction of shortest paths passing through node | Who is the gatekeeper? Low-degree but high-betweenness nodes are often the critical brokers connecting separate compartments. |
| **Closeness Centrality** | Average shortest path to all other nodes | Who can reach the entire network fastest? Information dissemination. |
| **Eigenvector Centrality** | Influence weighted by neighbor importance | Who is connected to important nodes? Power-by-association. |
| **PageRank** | Directed graph authority score | For directed graphs (e.g., website link networks, transaction flows). |

**Critical investigative pattern**: a node with LOW degree centrality but HIGH betweenness centrality is often the most important finding — the "gatekeeper" who connects otherwise separate compartments of an organization. This is fundamentally different from influencer-style analysis that focuses on degree.

### 2.3 Community Detection

Algorithms that partition graphs into natural clusters (communities):

| Algorithm | Reference | Key Property |
|-----------|-----------|--------------|
| Louvain | Blondel et al. (2008) | Fast, modularity optimization; may produce disconnected communities |
| Leiden | Traag, Waltman & van Eck (2019) | Guarantees connected communities; improved modularity |
| Infomap | Rosvall & Bergstrom (2008) | Information-theoretic; flow-based |
| Walktrap | Pons & Latapy (2005) | Random walk-based; hierarchical |

**Investigative applications**:
- Surface organizational structures hidden in communication data
- Identify cliques and their interconnections
- Detect anomalies: nodes that bridge unusual communities
- Temporal community detection reveals how groups form, dissolve, or shift over time

### 2.4 Temporal Network Evolution

Dynamic graph visualization enables analysis of structural change:
- Animate force-directed layouts over time slices (e.g., monthly snapshots)
- Detect role shifts: a node moving from periphery to core
- Identify emergence/dissolution of clusters
- Track gatekeeper role changes (betweenness centrality over time)

Tools supporting temporal graph analysis: Gephi with Timeline plugin, Cytoscape with animation support, custom D3.js animations.

## 3. Geospatial Visualization

### 3.1 Tool Landscape

| Tool | Type | Key Capability |
|------|------|----------------|
| QGIS | Desktop (Open Source) | Full GIS suite; plugin ecosystem; raster/vector processing |
| Kepler.gl | Web (Open Source) | GPU-accelerated; millions of points; arc/heatmap/cluster layers |
| deck.gl | Web (Open Source) | GPU-powered layered data visualization framework |
| Leaflet | Web (Open Source) | Lightweight; mobile-friendly; tile layers |
| Mapbox GL JS | Web (Freemium) | Vector tiles; 3D terrain; custom styles |
| OpenLayers | Web (Open Source) | Full-featured; WMS/WFS support |
| Google Earth Engine | Web (Free) | Satellite imagery analysis; time-series |
| GeoServer | Server (Open Source) | OGC standards; WMS/WFS/WCS |
| PostGIS | Database (Open Source) | Spatial SQL; raster support |
| PANO MapVisual | Desktop (Open Source) | Integrated coordinate plotting and location analysis |

### 3.2 Bellingcat Map Stack Methodology

Influential geolocation investigation methodology:
1. **Google Earth** — 3D terrain, historical imagery
2. **Yandex Maps** — often has imagery not on Google for certain regions
3. **Bing Maps** — alternative aerial/satellite imagery
4. **Mapillary** — crowdsourced street-level imagery
5. **OpenStreetMap** — community-mapped detail (buildings, footpaths)
6. **Wikimapia** — user-annotated locations
7. **PeakVisor** — mountain/summit identification from horizon profiles

### 3.3 Spatial Analysis Techniques

| Technique | Application |
|-----------|-------------|
| Buffer Analysis | Identify entities within radius of a point (e.g., all companies within 1km of a POI) |
| Heatmaps (KDE) | Density visualization of events, addresses, or activity |
| Point Clustering | Aggregate nearby points at low zoom levels |
| Route Analysis | Movement tracing from GPS tracks or address sequences |
| Temporal Geospatial | Animated movement traces with timestamps (e.g., where was subject X on date Y?) |

## 4. Timeline Reconstruction

### 4.1 Tool Landscape

| Tool | Type | Key Capability |
|------|------|----------------|
| TimelineJS | Web | Spreadsheet-to-timeline; Knight Lab |
| TimeGraphics | Web | Gantt-chart style; multiple parallel tracks |
| Aeon Timeline | Desktop | Interactive timeline for legal/investigative |
| PANO Timeline | Desktop (integrated) | Timeline as entity state tracker |
| Maltego Timeline | Desktop (commercial) | Event-based entity timeline from transforms |
| Sutori | Web | Collaborative timeline storytelling |
| Preceden | Web | Multi-layer timeline builder |

### 4.2 Methodology

Timeline reconstruction maps entity state changes over time:
- Corporate registrations (incorporation dates, director changes, address changes)
- Domain WHOIS changes (registration, expiration, nameserver changes, contact updates)
- Social media activity (account creation, post timestamps, profile changes)
- Financial transactions (dates, amounts, counterparties)
- Travel records (immigration stamps, flight bookings)

**Integration with graph visualization**: bidirectional filtering allows:
- Select a timeframe → filter graph to show only nodes active during that period
- Select an entity → highlight all timeline events associated with that entity
- Overlay multiple entity timelines to detect co-occurrence patterns

## 5. Web-Based Interactive Visualization

### 5.1 The Shift to Browser-Based Tools

Web-based visualization libraries enable:
- Live-updating investigation dashboards without desktop tool installation
- Shared investigation workspaces (multiple analysts viewing same graph)
- Embedding interactive graphs in reports
- Integration with web-based data sources

### 5.2 Key Libraries

| Library | Graph Type | Rendering | Notes |
|---------|-----------|-----------|-------|
| **Cytoscape.js** | Graph (nodes/edges) | Canvas/WebGL | Most mature; extensive plugin ecosystem (layouts, styles, algorithms); compound nodes |
| **vis.js** | Network + Timeline | Canvas | All-in-one library; network, timeline, and 2D/3D graph views |
| **Sigma.js** | Graph | WebGL | Lightweight; optimized for large graphs (thousands of nodes) |
| **D3.js** | General-purpose | SVG/Canvas | Maximum flexibility; steep learning curve; force simulations |
| **deck.gl** | Geospatial + Graph | WebGL | GPU-powered; layers for graph, arc, scatterplot, heatmap |
| **Leaflet** | Geospatial | CSS/Canvas | Lightweight; extensive tile provider support |

## 6. AI-Assisted Visualization

### 6.1 LLM-Driven Entity Extraction

LLMs can extract structured entities (people, organizations, locations, events) from unstructured text (reports, news articles, social media posts) and output them as graph nodes and edges. PANAI implements this pattern.

### 6.2 Natural Language Graph Queries

- Neo4j Bloom: "Show me all connections between company X and company Y"
- GraphRAG: Augmenting retrieval-augmented generation with graph-based context (Microsoft GraphRAG, 2024-2025)
- Investigative assistants: "Which entity has the highest betweenness centrality?"

### 6.3 Automated Pattern Detection

- Anomaly detection: nodes with unusual connection patterns (low degree, high betweenness)
- Clique detection: fully connected subgraphs indicating coordinated groups
- Temporal anomaly detection: sudden spikes in connectivity
- Community outlier detection: nodes that don't fit any community

## 7. Cross-Domain Connections

- **[[entity-resolution-fellegi-sunter]]** — Betweenness centrality is structurally isomorphic to entity resolution: both identify nodes connecting separate datasets. Probabilistic matching (Fellegi-Sunter) applies to graph link prediction.
- **[[knowledge-graph-construction]]** — Graph viz tools (Gephi, Cytoscape) are the analysis surface for knowledge graphs built during entity resolution.
- **[[anti-bot-evasion]]** — Collection depends on evasion; you can't visualize what you can't collect.
- **[[bellingcat-geolocation-osint]]** — Geographic overlay visualization is the tooling layer for the Bellingcat geolocation methodology's map stack approach.
- **[[network-analysis-graph-theory]]** — Community detection algorithms (Louvain, Leiden) applied to OSINT graphs surface organizational structures.
- **[[humint-tradecraft-osint]]** — Social network visualization identifies who to elicit from: lowest-degree node = most accessible entry point.
- **[[privacy-cryptography]]** — Browser fingerprinting (detection) is adversarial counterpart to visualization-based OSINT.
- **[[social-media-osint]]** — Social network diagrams map influence networks; bot detection via graph anomalies (clusters of low-content, high-frequency accounts).
- **[[phone-number-osint]]** — Call detail records (CDR) analysis produces communication graphs; centrality metrics identify coordinators.
- **[[domain-whois-dns-investigation]]** — WHOIS data generates organizational linkage graphs: domains sharing registrant emails or nameservers.
- **[[data-breach-analysis-identity-linkage]]** — Breached credentials link identities across platforms via shared email addresses, forming cross-platform identity graphs.
- **[[palantir-ontology-data-fusion]]** — Palantir's dynamic ontology approach is a reference architecture for graph-based investigation platforms.

## Sources

- ALW1EZ/PANO (2026) — github.com/ALW1EZ/PANO. Open-source OSINT platform v8.2.8: graph, timeline, maps, AI.
- EBU Investigative Network Mapping Guide (Nov 2025) — spotlight.ebu.ch/p/investigative-network-mapping-link
- Geospatial Stacks (2025) — Open-Source GIS Tools Survey
- Traag, Waltman & van Eck (2019) — Leiden Algorithm, *Scientific Reports*
- Cytoscape.org — Open source platform for complex network visualization
- Gephi.org — The Open Graph Viz Platform
- Kepler.gl — Uber's open-source geospatial analysis tool
- deck.gl — GPU-powered layered data visualization framework
- i-intelligence OSINT Toolkit (2025 Edition) — i-intelligence.eu/resources/osint-toolkit
- Social Links OSINT Landscape 2026 — sociallinks.io/osint-landscape-2026
- Cybrvault (2025) — 10 Best Free OSINT Tools for Investigators and Researchers
- Defcon Level (2026) — OSINT Tools Workflow Guide
- GEOINT AI (2025) — Essential OSINT Tools for GEOINT Professionals
- vis.js — visjs.org
- Sigma.js — sigmajs.org
- Cytoscape.js — js.cytoscape.org
- D3.js — d3js.org
- Blondel et al. (2008) — Louvain algorithm, *J. Stat. Mech.*
- Rosvall & Bergstrom (2008) — Infomap, *PNAS*
