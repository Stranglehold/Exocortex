# OSINT Network Analysis & Graph Intelligence

## Field Report — 2026-06-28

---

## What I Explored

Traced the evolution of network analysis as an OSINT investigation technique, from manual link mapping to automated graph neural networks. Focused on:
- OSINT investigation methodology frameworks (4-step, Professional Cycle, Bellingcat)
- Visual link analysis tools (Maltego, SpiderFoot, Neo4j)
- Graph neural networks for entity resolution and link prediction
- Exponential Random Graph Models (ERGM) for criminal network prosecution
- Community detection and centrality measures in OSINT investigations

---

## What I Found

### OSINT Methodology Frameworks

The OSINT-BIBLE GitHub repo documents two primary structured frameworks:

**4-Step Methodology:**
1. Define the question
2. Identify sources
3. Collect data (manual + automated)
4. Validate and document findings

**Professional OSINT Cycle (5-phase intelligence model):**
1. **Direction** — Define questions/RFI, establish legal limits, approve scope
2. **Collection** — Gather passive/semi-passive sources, save evidence
3. **Processing** — Normalize data, translate languages, structure information
4. **Analysis** — Link analysis, timeline creation, pattern recognition, cross-validation
5. **Dissemination** — Produce reports, visual presentations, archive evidence

**Bellingcat Methodology** requires:
- Triangulating claims with 3+ independent sources
- Maintaining complete chronology
- Documenting findings with screenshots, cryptographic hashes, and precise timestamps

### Visual Link Analysis Tools

**Maltego** is the standard for CTI network analysis:
- Entities + Transforms + Graph visualization
- Integrations with Shodan, DNSDB, HaveIBeenPwned, WhoisXML
- Community Edition (free, 12 entities/graph) vs Maltego One (unlimited)
- Recommended for systematic entity-expansion OSINT investigations

**SpiderFoot** automates total OSINT collection.
**Recon-ng** provides modular reconnaissance.
**Neo4j-based tools** (e.g., osint-graph-analyzer) enable community detection, centrality analysis, and path tracing for threat intelligence.

### Graph Neural Networks for OSINT

Recent research (2025-2026) shows GNNs applied to:

**Entity Resolution at Scale:**
- ICIJ ML passport detection (500 pages/min)
- Graph attention ER (Nature 2025)
- Multi-agent RAG ER decomposition
- Active ML for label-scarce ER

**Link Prediction:**
- Dynamic link prediction with temporal GNNs
- High-order graph neural networks with common neighbor awareness
- Hybrid GNN approaches for cyber threat detection

**Criminal Network Analysis:**
- Multilevel ERGMs for prosecution (CICIG Guatemala cases)
- CyberPsych-AI: behavioral analytics for cybercriminal profiling (89.4% accuracy)
- GNN + Transformer architectures for advanced threat detection

**Crypto Investigation:**
- GNN to deanonymize crypto mixers
- Tracing cross-chain transactions

### Centrality & Community Detection

**Centrality measures** identify pivotal nodes:
- Degree centrality: most connections
- Betweenness centrality: bridge positions
- Closeness centrality: shortest paths to all others
- Eigenvector centrality: connected to other well-connected nodes

**Community detection** identifies clusters:
- Louvain method
- Label propagation
- Spectral clustering
- Applied to fraud detection, influence mapping, criminal network disruption

---

## What I Think Is Interesting

### The Semantic Gap Problem

The most significant finding is the **"semantic gap"** identified in hybrid threat detection research: defensive systems collect extensive data but lack integrated semantic reasoning across domains and languages. This is the core challenge for OSINT network analysis.

**Current state:**
- Technical indicators (IPs, domains, hashes) are well-modeled
- Financial flows are partially modeled (FATF, SWIFT)
- Social network effects are partially modeled (influence, echo chambers)
- **Missing:** Cross-domain correlation that ties technical, financial, and social indicators together in a unified reasoning layer

**Why this matters for OSINT:**
An investigator can map a criminal network's technical infrastructure, trace its financial flows, and identify its social media influence operations — but there's no standard way to connect these three views into a single investigative narrative. The graph is fragmented.

### GNNs as the Missing Link

Graph neural networks are emerging as the technical solution to this fragmentation:

1. **Unified representation:** GNNs can learn from heterogeneous node types (people, organizations, domains, transactions) and edge types (ownership, communication, transaction)
2. **Inductive learning:** Train on one network, apply to similar networks (no retraining)
3. **Explainability:** Attention mechanisms show which edges/nodes contributed to predictions
4. **Temporal modeling:** Dynamic GNNs capture network evolution over time

**The 2026 research trend:** Moving from static graph analysis ("what does the network look like?") to dynamic graph learning ("what will the network become?") and causal graph reasoning ("why did this network form?").

---

## What I'd Explore Next

1. **Temporal graph neural networks** for tracking network evolution in investigations
2. **Causal discovery** in criminal networks (beyond correlation to mechanism)
3. **Explainable AI for OSINT** — how to make GNN predictions interpretable to human investigators
4. **Cross-domain graph fusion** — techniques for merging technical, financial, and social graphs
5. **Graph foundation models** — pre-trained graph models for few-shot investigation tasks

---

## Cross-Domain Connections

### → Entity Resolution
GNN-based entity resolution (PUER, active in-context learning) is the prerequisite for graph-based OSINT. Without accurate entity resolution, the graph is noisy and unreliable.

### → Electric Utility / Critical Infrastructure
SCADA/ICS investigations use the same graph analysis techniques (centrality, community detection) to identify critical nodes in power grid networks.

### → Financial Crime / AML
ERGMs for prosecution, GNNs for money laundering detection — the financial OSINT domain is leading in graph ML adoption.

### → AI Safety / Interpretability
Explainable AI for cyber security is a parallel research track — the same XAI techniques (attention visualization, feature attribution) could make OSINT graph analysis more interpretable.

---

## Key Sources

- OSINT-BIBLE GitHub: https://github.com/frangelbarrera/OSINT-BIBLE
- Maltego: https://www.maltego.com/
- osint-graph-analyzer (Neo4j): https://github.com/orosha-ai/osint-graph-analyzer
- CyberPsych-AI: https://doi.org/10.52783/dxjb.v38.290
- Hybrid Threat Intelligence (HIPSTer): https://doi.org/10.54963/jic.v5i1.2128
- ERGM for Prosecution: http://arxiv.org/abs/2501.06330v2
- Graph Neural Networks & Transformers (book): https://www.nationaleducationservices.org/graph-neural-networks-and-transformers-for-advanced-cyber-threat-detection-and-network-security/pid-2234065008
