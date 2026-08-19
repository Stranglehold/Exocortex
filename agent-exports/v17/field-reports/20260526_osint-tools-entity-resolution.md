# Field Report: Open-Source OSINT Tools for Entity Resolution

**Date:** 2026-05-26
**Cycle Type:** EXPLORE
**Topic:** Data Aggregation & Entity Resolution -> Open-source alternatives beyond OpenPlanter
**Interest Origin:** interests.md - Open-source alternatives: Maltego CE, SpiderFoot, Recon-ng, theHarvester

---

## 1. What I Explored

I investigated four open-source OSINT reconnaissance tools that serve as open-source alternatives to the (now abandoned) OpenPlanter platform for entity resolution and data aggregation. These tools represent the most widely adopted free/open-source options in the OSINT investigator toolkit for 2025-2026: Maltego Community Edition (CE), SpiderFoot, Recon-ng, and theHarvester. I examined their architectures, entity resolution capabilities, data source integrations, and suitability as OpenPlanter replacements.

## 2. What I Found

### Tool-by-Tool Analysis

**Maltego CE (Community Edition)**
- Type: Graph-based relationship mapping tool
- License: Free Community Edition with severe limitations; commercial XL at $1,999/instance
- Core capability: Transform-based data collection with automatic graph visualization
- Entity resolution: Built-in entity types (person, company, domain, email, IP, etc.) with automatic merging via transforms. The graph view visualizes relationships between resolved entities across data sources.
- Data sources: DNS records, WHOIS, search engines, social networks, Shodan, Criminal IP, and custom transforms via public APIs. CE version limited to 12 entities per graph and 10,000 entities total.
- Strengths: Best-in-class relationship visualization; automatic entity linking; mature ecosystem of transforms
- Weaknesses: CE version extremely limited (12 entity cap makes it nearly useless for real investigations); full version is expensive ($1,999+); closed-source core with open transform API
- Entity resolution capability: Excellent for small-to-medium investigations when combined with commercial licenses; CE limited to toy examples

**SpiderFoot**
- Type: Automated OSINT reconnaissance engine
- License: Open source (MIT), also a commercial HX version
- Core capability: Automated scanning across 200+ modules covering 30+ data source categories
- Entity resolution: SpiderFoot's internal data model tracks entities (IPs, domains, email addresses, names, etc.) and links them via relationships discovered by modules. It performs automatic entity deduplication and cross-referencing across data sources. The HX version adds correlation rules and risk scoring.
- Data sources: SHODAN, HaveIBeenPwned, AlienVault OTX, Censys, SecurityTrails, DNSDB, VirusTotal, Whois, and many more. Modules cover passive DNS, SSL certificates, social media, dark web, breach data, etc.
- Strengths: Most comprehensive data source coverage of any open-source OSINT tool; fully open-source core; automated scanning with minimal manual intervention; web UI for results exploration
- Weaknesses: Can be slow on large targets; overwhelming output without proper filtering; entity deduplication sometimes creates false merges
- Entity resolution capability: Strong for automated entity discovery and linking; less sophisticated graph visualization than Maltego but more comprehensive data coverage

**Recon-ng**
- Type: Modular reconnaissance framework with interactive console
- License: Open source (BSD)
- Core capability: Modules-based reconnaissance with database backend for storing and correlating results
- Entity resolution: Recon-ng stores all discovered data in a SQLite database with predefined tables for hosts, contacts, credentials, etc. Modules populate tables and can cross-reference results. The framework includes modules for contact harvesting, host discovery, and reporting that link entities across sources. However, entity resolution is manual — analysts must write queries to join tables and discover relationships.
- Data sources: Built-in modules for Shodan, HaveIBeenPwned, Whois, DNS, Bing, Google, LinkedIn, Twitter, GitHub, PGP key servers, and more. Modules are Python scripts that can be installed via the marketplace.
- Strengths: Familiar Metasploit-like console for penetration testers; database-driven with SQL query capability; extensible module marketplace; good for structured, repeatable reconnaissance workflows
- Weaknesses: No automatic entity resolution or graph visualization; requires manual SQL to connect entities; smaller module ecosystem than SpiderFoot; no web UI (terminal only)
- Entity resolution capability: Good data aggregation engine but resolution requires manual SQL analysis; best suited for technical users who want programmatic control

**theHarvester**
- Type: Email, subdomain, and virtual host enumeration tool
- License: Open source (GPLv2)
- Core capability: Passive reconnaissance focused on email addresses, subdomains, IPs, and URLs
- Entity resolution: Minimal — theHarvester collects entities but does not resolve or link them. It outputs raw lists of emails, hosts, IPs, etc. Entity resolution must be done manually or by piping output into another tool (e.g., Maltego, custom scripts).
- Data sources: Google, Bing, Yahoo, Baidu, Shodan, LinkedIn, Twitter, DNSDumpster, ThreatCrowd, VirusTotal, AlienVault, Censys, and many more search engines and APIs.
- Strengths: Fast, lightweight, simple CLI; excellent for quick email/subdomain enumeration; broad search engine support
- Weaknesses: No entity resolution; output is raw lists; requires chaining with other tools for investigations
- Entity resolution capability: None — pure data collection tool

### Comparison Matrix

| Capability | Maltego CE | SpiderFoot | Recon-ng | theHarvester |
|------------|------------|------------|----------|--------------|
| Entity resolution | Built-in (graph auto-merge) | Module-based auto-link | Manual SQL | None |
| Graph visualization | Excellent (native) | Basic (web UI) | None | None |
| Data source breadth | Medium (transforms) | High (200+ modules) | Medium (modules) | Medium (search engines) |
| Automation | Semi-automated | Fully automated | Semi-automated (scriptable) | Manual (CLI) |
| Open source | Core closed, API open | Core open (MIT) | Core open (BSD) | Core open (GPLv2) |
| Free tier | CE (12 entities max) | Full functionality free | Full (no limits) | Full (no limits) |
| Learning curve | Low (GUI) | Low (web UI) | High (console + SQL) | Low (CLI) |
| Best for | Relationship mapping | Automated scanning | Structured recon | Quick enumeration |

### OpenPlanter Replacement Assessment

OpenPlanter aimed to be an open-source alternative to Palantir Gotham for entity resolution and link analysis. None of these tools individually replicate that vision. However, a *pipeline combination* approaches the capability:

1. **theHarvester** / **Recon-ng** — Initial data collection (emails, subdomains, social profiles)
2. **SpiderFoot** — Deep automated scanning to expand entity graph with cross-source data
3. **Maltego CE (or XL)** — Relationship visualization and manual link analysis
4. **Custom scripts** — Entity resolution algorithms (Fellegi-Sunter, Jaro-Winkler, ML-based) applied to the collected data

The gap remains at step 4: no open-source tool has built-in probabilistic entity resolution across heterogeneous datasets. This is exactly the OpenPlanter gap — and it remains unfilled in 2025-2026.

### Emerging Alternatives (2025-2026)

- **Photon** — Web intelligence crawler that extracts structured data (emails, social links, keys) from websites; newer but gaining traction
- **Babel X** — Commercial multilingual OSINT search tool with link analysis; not open source
- **SpiderFoot HX** — Commercial version with advanced correlation, risk scoring, and team collaboration features
- **Maltego Transform Hub** — Community marketplace with 50+ data integrations, growing ecosystem

## 3. What I Think Is Interesting

**The tool ecosystem reflects the entity resolution problem, not a solution.** Every tool collects data from different sources and stores it in a different schema. The entity resolution problem — linking "John Smith" in WHOIS to "jsmith@example.com" in breach data to "@jsmith" on Twitter — remains a manual step that analysts perform in their heads or in custom scripts. This is exactly the problem Fellegi-Sunter was designed to solve, and no OSINT tool has incorporated it as a built-in feature. The tools are excellent scouts but poor analysts.

**SpiderFoot's module architecture is the closest to an extensible entity resolution platform.** With 200+ modules and a unified internal data model (entities + relationships), SpiderFoot is architecturally closest to an open-source Palantir. If someone added a probabilistic matching engine on top of SpiderFoot's entity store, it would become a legitimate open-source alternative for basic entity resolution. The HX version already has some correlation rules — extending that to Fellegi-Sunter or ML-based matching would be transformative.

**The free tier problem is real.** Maltego CE's 12-entity limit makes it unusable for serious investigation. SpiderFoot is fully functional but the web UI becomes slow with large datasets. Recon-ng is powerful but requires SQL expertise. theHarvester is fast but produces undigested data. The practical investigator must either pay (Maltego XL) or invest significant time learning the toolchain. The OpenPlanter vision of a single, free, capable platform remains aspirational.

**Tool composability mirrors agentic tool use.** The pipeline approach (theHarvester -> SpiderFoot -> custom resolution -> Maltego visualization) is structurally identical to an agentic workflow where specialized tools are chained via a reasoning loop. An LLM-based investigator could orchestrate these tools, parse their outputs, and perform entity resolution programmatically — essentially becoming the missing step 4. This is a cross-domain convergence between OSINT tooling and AI agent architecture.

## 4. What I'd Explore Next

1. **Build a proof-of-concept entity resolution layer for SpiderFoot** — Write a Python script that reads SpiderFoot's SQLite database, extracts entities and relationships, and applies Fellegi-Sunter probabilistic matching to deduplicate entities across sources.

2. **Compare SpiderFoot data model to Palantir ontology** — Map SpiderFoot's entity types and relationship types to Palantir's Object-Broker-Link model to identify what's missing.

3. **Evaluate Recon-ng as an LLM orchestration backend** — Recon-ng's SQLite database and Python module API make it ideal for programmatic control by an LLM agent. Test whether an LLM can write Recon-ng modules on the fly.

4. **Inventory all 200+ SpiderFoot modules for data fusion patterns** — Which modules produce overlapping entity types? Where could entity resolution improve deduplication? Quantify the false-merge rate.

5. **Survey the Maltego Transform Hub** — Catalog which transforms do entity resolution vs. data collection. Identify gaps that a custom transform could fill.

## 5. Cross-Domain Connections

| Connection | Domain A | Domain B | Insight |
|------------|----------|----------|---------|
| **Tool composability -> Agentic tool use** | OSINT tool pipeline | AI agent tool orchestration | The investigator's manual pipeline (collect, enrich, resolve, visualize) is exactly the reasoning loop of an AI agent with tool access. An LLM could automate the entire OSINT workflow. |
| **Entity resolution gap -> Fellegi-Sunter** | OSINT tools (no built-in resolution) | Entity resolution algorithms | The missing piece in the open-source OSINT toolkit is the same math Fellegi-Sunter solved in 1969. Bridging this gap is an engineering problem, not a research problem. |
| **SpiderFoot data model -> Knowledge graphs** | SpiderFoot entity store (SQLite) | Neo4j property graph | SpiderFoot's entity-relationship model is a de facto knowledge graph. Exporting to Neo4j would enable Cypher queries and graph algorithms (centrality, community detection) for link analysis. |
| **Free tier limitations -> Open-source sustainability** | Maltego CE (crippled) vs. SpiderFoot (open) | Open-source business models | The OSINT tool ecosystem demonstrates the open-core vs. fully-open tradeoff. SpiderFoot's fully-open model with a commercial HX version is more sustainable than Maltego's CE crippleware. |
| **Tool data silos -> Epistemic integrity** | Each tool has its own entity model | Exocortex epistemic integrity | Just as each OSINT tool has its own version of an entity, each AI system has its own version of a claim. Entity resolution across tools is the same problem as claim verification across systems. |

---

## Sources

1. CSO Online (2023, updated). "What is OSINT? 15 top open source intelligence tools." https://www.csoonline.com/article/567859/
2. SpiderFoot GitHub. https://github.com/smicallef/spiderfoot
3. Maltego official site. https://www.maltego.com/
4. Recon-ng GitHub. https://github.com/lanmaster53/recon-ng
5. theHarvester GitHub. https://github.com/laramies/theHarvester
6. OSINT Team Blog (2025). "10 Free Tools Every OSINT Investigator Should Know in 2025." https://osintteam.blog/
