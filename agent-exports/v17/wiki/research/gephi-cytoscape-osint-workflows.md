# Gephi/Cytoscape Workflows for OSINT Visualization

**Status:** STABLE
**Created:** 2026-08-07
**Last Updated:** 2026-08-07

## Summary

This page deepens the tool-specific "Gephi/Cytoscape workflows" subsection of the parent page [[visualization-techniques-osint]] into a standalone workflow page, grounded in the 2026-08-06 field report (20260806_gephi-cytoscape-osint-workflows.md), the shared Exocortex corpus, and 2026 web sources. Gephi and Cytoscape remain the two dominant desktop graph-analysis workbenches in OSINT practice. The workflow layer matters because the investigative value is not in layout algorithms alone — it lives in import hygiene, evidence semantics (dated/sourced edges), and the merge/verify operations that keep a graph trustworthy across a long investigation.

## 1. Tool Landscape & When to Use Which

### 1.1 Gephi — exploratory first pass

- **Positioning:** the OSINT-standard first-pass tool for force-directed exploration of moderately sized networks (typically up to ~100K nodes comfortably; beyond that scale moves to specialized engines).
- **Default layout:** ForceAtlas2 (Jacomy et al., PLOS ONE 2014), designed so non-graph-theorists can explore networks as maps; continuous/live layout suits iterative investigative sense-making.
- **Importers:** CSV, GEXF, GraphML, GDF, Pajek — the Bellingcat OSINT toolkit lists exactly these, i.e., the mainstream playbook expects tabular scraped data to land directly in Gephi.
- **Automation:** Java desktop app; scripting via the Gephi Toolkit is awkward inside Python pipelines.

### 1.2 Cytoscape — evidence-grade, scriptable layer

- **Positioning:** originally a genomics tool, re-purposed for OSINT because of its scriptability, robust plugin ecosystem, and Cytoscape.js web export.
- **Key advantages for investigations:** deterministic styling/edge attributes, strong visual-encoding control, and the web-export path into Cytoscape.js — which is what local-first tools like Osintracker use for an "evidence ledger with a canvas".
- **Scripting:** py2cytoscape lets NetworkX graphs push into Cytoscape REST sessions; cyREST exposes the graph via HTTP — a strong fit for reproducible pipelines.

### 1.3 Comparison table

| Criterion | Gephi | Cytoscape |
|-----------|-------|-----------|
| Primary use | Exploratory layout & clustering | Evidence-grade analysis & web delivery |
| Default layouts | ForceAtlas2, Fruchterman-Reingold, Yifan Hu | Force-directed + curated layouts |
| Import formats | CSV/GEXF/GraphML/GDF/Pajek | CSV/SIF/XGMML/GraphML |
| Scripting | Java Toolkit only | py2cytoscape, cyREST, Cytoscape.js |
| OSINT precedent | Panama Papers, Bellingcat toolkit | Osintracker, intellyweave-style local tools |
| Scale | ~100K nodes comfortable | smaller, more controlled graphs |

## 2. Core Workflows

### 2.1 Import pipeline

1. **Schema fix first:** normalize node/edge tables before import (URLs, names, dates) to avoid duplicate identities.
2. **Choose the interchange format:** GEXF for Gephi (includes node/edge attributes and dynamics), GraphML for tool portability, CSV for quick tabs.
3. **Preserve evidence attributes:** keep source, date, confidence on edges from day one — retrofitting evidence metadata after layout is costly.
4. **Version the graph file** alongside the investigation case file (chain-of-custody practice from [[evidence-preservation-chain-of-custody-osint]]).

### 2.2 Layout selection

- **ForceAtlas2** — default for connected, medium graphs; tune *linlog*, *gravity*, *scaling*; avoid naive defaults on sparse graphs.
- **Fruchterman-Reingold** — deterministic reference, good for small graphs.
- **Yifan Hu multilevel** — large graphs, fast, good separation; preferred when community structure is the goal.
- **OpenOrd** — scales to millions of nodes, but sacrifices local detail and ignores edge weights (use only for a global cluster sketch).

### 2.3 Community detection & centrality

- **Leiden** is preferred over Louvain in modern pipelines (better connected partitions; per memory and the network-analysis corpus).
- **Gatekeeper pattern:** nodes with LOW degree but HIGH betweenness often reveal the most important connector between otherwise separate compartments — the core investigative reading, structurally isomorphic to entity resolution.

### 2.4 Export for evidence

- Export PNG/PDF for reporting, but also export the **graph file + attribute tables** as the machine-readable evidence set.
- For paper-trail claims, pair visual exports with the underlying query so the picture is reproducible.

## 3. Landmark Precedent: ICIJ Panama Papers (2016)

- **Scale:** ~11.5M documents, 380+ journalists across ~80 countries.
- **Stack:** graph databases + Linkurious + Gephi; the graph layer was the collaboration substrate (Knowledge Center, Global I-Hub) letting reporters query across entities — not merely visualization.
- **Takeaway:** the tool-workflow layer is where multi-analyst coordination happens; Gephi is fine for sense-making, but the shared evidence substrate (graph DB + queryable layer) is what made the project scale.

## 4. 2026 Shifts: Local-First & LLM-Assisted Graph Construction

- **Local-first evidence tools:** Osintracker uses Cytoscape.js with IndexedDB-local storage and dated/sourced/rated/directed edges — an *evidence ledger with a canvas*, aligning with OPSEC (the analysis environment itself becomes a security boundary).
- **LLM edge extraction:** Obsidian Simple Graph Builder and intellyweave use GLiNER/LLM extractors to turn notes/documents into edges. This moves classical entity-resolution failure modes (co-reference errors, duplicate identities) into the visualization layer.
- **Consequence:** the next meaningful OSINT tool gap is not layout — it is **graph quality control**: confidence-scored edges and merge/verify workflows inside the canvas.

## 5. OSINT-Specific Workflow Patterns

1. **Evidence semantics on edges** — date, source, confidence, rating (Osintracker pattern).
2. **Gatekeeper hunt** — rank by betweenness; inspect low-degree/high-betweenness nodes first.
3. **Merge/verify cycle** — dedupe identities before layout; after layout, revisit candidate duplicate pairs.
4. **Cross-tool export chain** — Python collection → NetworkX → Gephi (layout) → Cytoscape.js (delivery/evidence).

## 6. Integration with Exocortex

- The Exocortex knowledge-graph layer should expose graph files in the same interchange formats (GEXF/GraphML) so agent-built graphs can be opened in Gephi/Cytoscape without conversion.
- Visualization is the presentation layer of entity resolution; the graph QC problem is the same entity-binding problem from [[entity-resolution-agent-safety]].
- The local-first/OPSEC alignment mirrors metadata-resistant preferences: local storage and no third-party network calls during analysis.

## 7. Risks & Limitations

- **Layout is not analysis:** a pretty force-directed picture can imply relationships that aren't evidenced; always show edge provenance.
- **Scale ceilings:** desktop tools choke beyond ~10^5–10^6 nodes; large-scale work belongs in graph engines (Neo4j, t-SNE/UMAP cluster preview).
- **Graph QC blind spot:** LLM-built graphs inherit co-reference errors; without confidence-scored edges, false links propagate into the write-up.
- **Tool availability:** Gephi and Cytoscape both require Java; headless/container pipelines should use the Python reimplementation (bhargavchippada/forceatlas2, claimed 10–100x speedup) for layout without a GUI.

## 8. Cross-Domain Connections

- [[network-analysis-techniques-osint]] — centrality/community algorithms under the hood.
- [[force-directed-graph-layouts-osint]] — layout math and tuning.
- [[visualization-techniques-osint]] — parent page.
- [[entity-resolution-agent-safety]] — edge QC/merge as entity binding.
- [[evidence-preservation-chain-of-custody-osint]] — provenance fields on edges.
- [[timeline-reconstruction-osint]] — temporal attributes in graph work.
- [[autonomous-osint-agent-opsec-attribution-risk]] — local-first/OPSEC alignment.
- [[privacy-preserving-entity-resolution-osint]] — cross-institution graphs without central data.

## 9. References

1. Jacomy et al., ForceAtlas2, PLOS ONE 2014.
2. bhargavchippada/forceatlas2 (GitHub) — Python/Cython reimplementation.
3. Bellingcat Online Investigation Toolkit — Gephi section.
4. Data Journalism Handbook — ICIJ Panama Papers collaboration account.
5. Neo4j — How ICIJ used Neo4j.
6. Osintracker (osintracker.com) — local-first Cytoscape.js graph.
7. Obsidian Simple Graph Builder (community.obsidian.md).
8. vericle/intellyweave (GitHub).
9. HackerNoon, "How a Small OSINT Team Turned the Epstein Files Dump Into Actionable Intelligence" (Feb 2026).
10. Exocortex corpus: visualization-techniques-osint.md, force-directed-graph-layouts-osint.md, network-analysis-techniques-osint.md, memory o60XFc4gUb.

*Honesty note: library search tools (search_library) were not exposed in this cycle's runtime; the 355-book library was not reachable. Corpus grounding used memory_load + direct wiki/field-report greps, plus 2026 web sources from the field report and this cycle's verification pass.*
