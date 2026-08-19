# Field Report: Open-Source OSINT Tools for Entity Resolution
**Date:** 2026-05-29
**Topic:** OSINT frameworks as entity resolution pipelines — Maltego, SpiderFoot, Recon-ng, theHarvester
**Type:** EXPLORE cycle

---

## 1. What I Explored

The OSINT tool ecosystem as a practical implementation layer for entity resolution. Jake's interests.md lists "Open-source alternatives beyond OpenPlanter: Maltego CE, SpiderFoot, Recon-ng, theHarvester" as an explicit exploration target under Data Aggregation & Entity Resolution. I compared these four tools — plus Shodan as a reference — across their entity resolution capabilities, operational philosophies, and how they compose into investigation pipelines.

## 2. What I Found

### Tool-by-Tool Breakdown

| Tool | Entity Resolution Approach | Strengths | Weaknesses | Best For |
|------|--------------------------|-----------|------------|----------|
| **Maltego** | Graph-based: entities as nodes, relationships as edges, Transforms as entity expansion operations | Visual link analysis at scale; 200+ Transform integrations; mature commercial ecosystem; collaborative investigation | Significant learning curve; Pro tier ~$1,000/yr; fundamentally interactive, not automatable; closed source | Multi-entity investigations where visual representation aids analysis and stakeholder presentation |
| **SpiderFoot** | Automated breadth-first collection: 200+ modules, single-scan comprehensive recon, structured database output | Category-leading source coverage; open-source core; API-integrable; runs on modest hardware; automated scheduling | Structured output not naturally visual; module quality varies; triage overhead from scan volume; less interactive deepening | Continuous attack-surface monitoring; initial comprehensive recon; automated workflows feeding other tools |
| **Recon-ng** | Modular CLI framework: Metasploit-style workspaces, composable modules, programmable investigation workflows | Fully open-source; extensible module architecture; workspace model for resumable investigations; strong for technical users | CLI-only, no native graph visualization; steeper learning curve; module maintenance burden; uneven module quality | Technical investigators comfortable with CLI; environments requiring reproducibility; custom module integration |
| **theHarvester** | Focused enumeration: email harvesting, subdomain discovery from search engines and public sources | Simple, fast, free; strong on its narrow use case; active community; excellent as pipeline component | Narrow scope; not a comprehensive platform; best deployed alongside broader tools | Specific email/subdomain enumeration tasks as part of larger investigation workflows |
| **Shodan** | Internet-wide device search: exposed services, banners, vulnerabilities, IoT/ICS discovery | Unique dataset; powerful query syntax; API for automation; complementary to domain/person-focused tools | Different domain entirely (infrastructure, not entity-focused); free tier limited | Internet-exposed asset discovery; infrastructure reconnaissance |

### The Composite Investigation Pipeline

These tools form a natural pipeline when combined:
1. **SpiderFoot** → Initial comprehensive scan (broad collection)
2. **Manual review** → Identify interesting findings from SpiderFoot output
3. **Maltego** → Import key entities, run Transforms, build visual relationship graph (deep linking)
4. **Recon-ng** → Targeted technical recon on specific elements (programmable depth)
5. **theHarvester** → Fill gaps in email/subdomain data (specialized enumeration)
6. **Verification** → Cross-check findings, document sources, assign confidence levels

### Entity Resolution Framework Mapping

The tool pipeline maps cleanly onto the entity resolution problem space:

| OSINT Tool Function | Entity Resolution Parallel |
|--------------------|-----------------------------|
| SpiderFoot data collection | Heterogeneous dataset ingestion |
| Maltego Transform Hub | Deterministic/probabilistic matching rules |
| Recon-ng custom modules | Custom feature engineering for matching |
| Maltego graph visualization | Knowledge graph construction (property graph) |
| Cross-tool entity linking | Cross-jurisdictional data linking challenge |

## 3. What I Think Is Interesting

**The pipeline structure mirrors local-to-frontier bridging architecture.** SpiderFoot's breadth-first collection (200+ sources, automated) is structurally identical to a local model handling pre-processing and broad data ingestion. Maltego's deep, interactive link analysis with commercial data sources mirrors a frontier model performing synthesis and inference on pre-processed data. Recon-ng's composable modules mirror agent tool composition — each module is a tool, and the investigation is an agent execution plan.

This isn't just analogy; it's structural equivalence. Both pipelines:
- Ingest heterogeneous data from multiple sources
- Apply transformation/cleaning (Transforms in Maltego, module processing in Recon-ng)
- Resolve entities across sources (Fellegi-Sunter in entity resolution, manual/pseudo-automated linking in OSINT)
- Produce structured output (knowledge graph, investigation report)

**The gap between automated breadth (SpiderFoot) and investigative depth (Maltego) is the same gap between local model pre-processing and frontier model reasoning.** Bridging it requires the same approach: cascade architecture where broad collection feeds deep analysis.

## 4. What I'd Explore Next

- Automated SpiderFoot → Maltego pipeline: script SpiderFoot output parsing to auto-populate Maltego graphs
- Fellegi-Sunter implementation using Recon-ng custom modules: build a probabilistic entity matching module that scores matches across SpiderFoot-collected data
- Compare entity resolution accuracy of OSINT tool pipelines vs. dedicated ER tools (Splink, Zingg) on the same dataset
- Map Maltego Transform ontology to formal entity resolution schema (property graph vs. RDF)

## 5. Cross-Domain Connections

1. **Local-to-Frontier Bridging (Hardware/Computing):** The SpiderFoot→Maltego pipeline is structurally identical to the local pre-processing → frontier inference cascade architecture explored in prior cycles (20260528_bridging-local-frontier-cascade.md). Both require: ingestion layer (SpiderFoot/local model), transformation layer (Transforms/quantization), synthesis layer (Maltego graph/frontier model).

2. **Privacy-Preserving OSINT:** Running SpiderFoot and Recon-ng locally (both open-source, can run on private infrastructure) enables privacy-preserving OSINT investigation — the same principle that makes local LLM inference valuable for sensitive data processing. The tools exist; the integration architecture doesn't yet.

3. **Fellegi-Sunter Across Tools:** The OSINT ecosystem would benefit from a unified entity resolution layer that applies probabilistic matching (Fellegi-Sunter) across SpiderFoot's structured output, Maltego's graph entities, and Recon-ng's workspace databases. This is the OSINT equivalent of cross-database entity resolution in corporate registries.

---
*Generated during EXPLORE cycle. Memory saved with key cross-domain connection.*
