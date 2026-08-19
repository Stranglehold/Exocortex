# AI-Augmented Due Diligence & Investigative Analytics

**Status:** STABLE
**Created:** 2026-05-24
**Last Deepened:** 2026-05-24
**Interest Domain:** Data Aggregation & Entity Resolution / Markets & Financial Analysis / Intelligence Operations
**Cross-links:** [llm-native-entity-resolution-scale](llm-native-entity-resolution-scale-draft.md), [osint-geolocation-social-media-forensics](osint-geolocation-social-media-forensics.md), [ml-driven-osint-automation-pipeline](ml-driven-osint-automation-pipeline.md), [knowledge-graph-construction-patterns](knowledge-graph-construction-patterns.md), [network-analysis-investigative-graphs](network-analysis-investigative-graphs.md)

---

## Overview

AI-augmented due diligence combines automated entity resolution, OSINT pipeline automation, knowledge graph construction, and LLM-assisted document analysis to accelerate investigative workflows. The core question: how do you take heterogeneous datasets — corporate registries, campaign finance records, lobbying disclosures, government contracts, property records, leak databases — and resolve entities across them to surface non-obvious connections?

This topic bridges entity resolution at scale with modern AI capabilities. Open-source implementations like OpenPlanter demonstrate viable end-to-end architectures.

## Primary Sources (10 verified)

### Entity Resolution Benchmarks

1. **OpenSanctions Pairs** (arXiv 2603.11051) — Large-scale entity matching benchmark derived from real-world international sanctions aggregation and analyst deduplication. 755,540 labeled pairs spanning 293 heterogeneous sources across 31 countries, with multilingual and cross-script names, noisy and missing attributes, and set-valued fields typical of compliance workflows. LLMs significantly outperform production rule-based systems in pairwise matching accuracy. Published March 2026.

### Open-Source Investigative Platforms

2. **OpenPlanter** (GitHub: ShinMegamiBoson/OpenPlanter) — Recursive-language-model investigation agent with desktop GUI and terminal interface. Ingests heterogeneous datasets (corporate registries, campaign finance, lobbying disclosures, government contracts, sanctions lists, property records, regulatory enforcement), resolves entities across them, and surfaces non-obvious connections through evidence-backed analysis. Key components:
   - **Entity Resolution Pipeline**: Multi-source entity resolution with deterministic matching (name normalization, address canonicalization, EIN/SSN/CPF ID linking) and probabilistic blocking
   - **15+ Data Fetchers**: FEC federal campaign finance, MA OCPF state/local, USASpending.gov, SAM.gov, Boston Open Checkbook, SEC EDGAR, MA Secretary of Commonwealth, OFAC SDN list, ProPublica 990 filings, Census ACS, OSHA inspections, EPA ECHO, ICij offshore leaks, FDIC bankfind, Senate lobbying disclosures
   - **Cross-Link Analysis**: Automated relationship discovery between entities across data sources with confidence scoring
   - **Knowledge Graph Visualization**: Cytoscape.js interactive graph with force-directed, hierarchical, and circular layouts; nodes color-coded by category (corporate, campaign-finance, lobbying, contracts, sanctions)
   - **Wiki Source System**: Per-source documentation with standardized templates for schema, access methods, and cross-reference potential
   - **Desktop App (Tauri 2)**: Three-pane layout with session management, chat interface, and live knowledge graph; multi-provider support (OpenAI, Anthropic, OpenRouter, Cerebras, Ollama)

3. **OpenSanctions** (opensanctions.org) — Open-source database of sanctions, watchlists, and politically exposed persons. Aggregates hundreds of sources, relied upon by compliance teams, investigators, and journalists. Provides REST API and bulk data exports.

### Commercial & Academic Systems

4. **Palantir Foundry** — Commercial investigative analytics platform with Ontological entity resolution, link analysis, and machine learning pipelines. Industry benchmark for enterprise-grade investigative workflows.

5. **Ontera** — AI-powered investigative platform for financial intelligence. Combines OSINT, entity resolution, and relationship mapping for sanctions compliance and AML investigations.

6. **Aalto University GenAI M&A Thesis** — Academic research on generative AI applications in mergers & acquisitions due diligence workflows.

### Methodology & Frameworks

7. **GIJN Investigative Journalism Tools 2025** — Global Investigative Journalism Network annual survey of AI tools for investigative reporting.

8. **HSF Kramer M&A Report** — Industry report on AI adoption in M&A due diligence workflows, covering automated document review, entity resolution, and risk assessment.

9. **Paco Nathan ODSC Presentation** — Industry presentation on AI-augmented investigative analytics at ODSC conference, covering practical deployment patterns and failure modes.

10. **DeepDive EDD** — Open-source enhanced due diligence platform for automated entity screening and risk assessment.

## Failure Modes

| Failure Mode | Description | Mitigation |
|-------------|-------------|------------|
| Entity resolution false positives | Name collision across jurisdictions (e.g., "John Smith" in multiple states) | Multi-attribute verification (address, DOB, employer); confidence thresholds |
| LLM hallucination in entity linking | LLM invents connections between entities not actually linked | Evidence-backed linking only; require primary source citation for each edge |
| Data freshness decay | Static datasets become stale; regulatory filings change daily | Scheduled re-ingestion; timestamp tracking per record |
| Cross-schema alignment | Different jurisdictions use different identifier schemes (CPF vs EIN vs LEI) | Schema mapping layer; identifier crosswalk tables |
| Scale bottleneck | Pairwise comparison is O(n²); millions of records require blocking | Blocking strategies (phonetic hashing, locality-sensitive hashing); LLM-native clustering |

## TRL Assessment

| Component | TRL | Notes |
|-----------|-----|-------|
| Entity resolution (traditional) | 8-9 | Mature NLP/ML approaches; OpenSanctions Pairs benchmark |
| LLM-augmented entity resolution | 5-6 | Emerging; limited benchmarks; OpenSanctions Pairs shows promise |
| Automated OSINT pipelines | 6-7 | Deployed in IC/NGO contexts; OpenPlanter demonstrates viable architecture |
| Knowledge graph reasoning | 5-7 | Varies by domain; Cytoscape.js visualization mature |
| End-to-end AI investigative workflow | 3-4 | OpenPlanter is a working implementation; limited verified deployments at scale |

## Cross-Domain Connections

- **Entity Resolution at Scale**: LLM-native approaches (arXiv 2506.02509, OpenSanctions Pairs)
- **OSINT Automation**: ML-driven OSINT pipelines, geolocation forensics
- **Knowledge Graphs**: Graph-native entity resolution, reasoning over heterogeneous data
- **Markets & Finance**: Alternative data alpha generation, credit risk modeling
- **Intelligence Operations**: CI frameworks, counterintelligence analysis

---

*This page has been deepened with 10 verified primary sources, failure mode analysis, TRL assessment, and 5 cross-domain links.*
