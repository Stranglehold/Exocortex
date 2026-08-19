# OSINT Reconnaissance Automation Toolchain

**Status: STABLE**  
**Created: 2026-07-11 | Updated: 2026-07-11**  
**Domain: OSINT & Investigation Methodology | Data Aggregation & Entity Resolution**

## 1. Overview

OSINT reconnaissance automation addresses a core workflow bottleneck: manually running SpiderFoot, Recon-ng, and theHarvester sequentially produces scattered, unlinked results. Automating the toolchain — chaining these tools into a pipeline with standardized output formats, deduplication, and entity resolution — transforms them from individual scanners into a coordinated collection system that produces structured, cross-referenced intelligence.

The three tools occupy complementary niches:
- **theHarvester**: Email/domain/subdomain enumeration via search engines and public sources
- **Recon-ng**: Modular reconnaissance framework with report generation and database integration
- **SpiderFoot**: Automated OSINT correlation engine with 200+ modules across 18 data source categories

Internally, the Exocortex corpus contains extensive prior exploration of these tools in [[open-source-osint-tools-survey]], [[open-source-osint-investigation-tools]], and [[open-source-osint-tools-ecosystem]]; this page synthesises those analyses into a concrete automation architecture.

## 2. Tool Architecture Comparison

| Feature | theHarvester | Recon-ng | SpiderFoot |
|---------|-------------|----------|------------|
| Primary function | Email/domain enumeration | Modular recon workstation | Automated correlation engine |
| Module count | ~15 sources | 100+ modules | 200+ modules |
| Output formats | HTML, XML, JSON, CSV | CSV, HTML, JSON, CLI | CSV, JSON, GEXF, HTML |
| Database backend | None | SQLite workspace | SQLite/PostgreSQL |
| Automation API | CLI only | CLI + Python API | CLI + Python API + REST API |
| Rate limiting | Manual | Module-level config | Global + per-module |
| Correlation engine | No | Manual via reporting | Automatic entity correlation |
| License | GPL-2.0 | BSD-3 | GPL-2.0 |

## 3. Pipeline Architecture

### Phase 1 — Seed Discovery (theHarvester)
```bash
theHarvester -d target.com -b google,bing,yahoo,linkedin -f harvester_output.html
```
Extracts: emails, subdomains, IPs, employee names — data that feeds subsequent phases.

### Phase 2 — Structured Recon (Recon-ng)
```bash
recon-ng -w target_workspace
[recon-ng] modules load recon/domains-hosts/bing_domain_web
[recon-ng] modules load recon/contacts-contacts/mailtester
[recon-ng] modules load reporting/list
```
Workflow: create workspace → add seeds from Phase 1 → run domain/contact modules → export database.

### Phase 3 — Correlation & Deep Scan (SpiderFoot)
```bash
python3 sf.py -s target.com -m all -o csv
```
Correlates Phase 1-2 results with 200+ modules: SHODAN, HaveIBeenPwned, DNSDB, Censys, SecurityTrails, AbuseIPDB, and more.

### Phase 4 — Entity Resolution & Deduplication
Output silos are unified: email addresses link Recon-ng contacts to SpiderFoot email modules; IPs link theHarvester DNS results to SpiderFoot SHODAN modules. Cross-tool entity resolution employs deterministic matching (exact email/IP) and probabilistic matching (name similarity, domain adjacency) via Splink (Fellegi-Sunter).

### Phase 5 — Export & Integration
Standardized JSON output feeds into link analysis tools (Maltego, Gephi), timeline reconstruction, and knowledge graph construction.

## 4. Automation Patterns

### Pattern A: Sequential Shell Pipeline
```bash
#!/bin/bash
theHarvester -d $1 -b all -f /tmp/harvest.json
python3 harvest_to_recon.py /tmp/harvest.json | recon-cli import
spiderfoot-cli -s $1 -m all -o /tmp/spiderfoot.json
python3 merge_and_dedup.py /tmp/harvest.json /tmp/spiderfoot.json $1_recon_out/
```

### Pattern B: Python Orchestration with shared SQLite
```python
import subprocess, sqlite3, json
# Run each tool, capture output, normalize to shared schema
# Deduplicate via Splink/dedupe on normalized entity tables
# Export to graph format (GEXF) for Maltego/Gephi
```

### Pattern C: Iterative Loop (multi-stage workflow)
The Exocortex corpus [[open-source-osint-tools-ecosystem]] documents a five-stage workflow that replaces the linear pipeline with a feedback loop:
1. **Initial Comprehensive Scan** — SpiderFoot for broad reconnaissance, producing a structured baseline.
2. **Manual Review & Pivot** — analyst review of SpiderFoot output to identify interesting findings and gaps.
3. **Visual Link Analysis** — Maltego import for graph investigation; non-obvious connections emerge here.
4. **Targeted Technical Recon** — Recon-ng, theHarvester, or specialist tools (Shodan, Censys) deepen specific findings.
5. **Verification & Documentation** — cross-check findings, assign confidence levels (Fellegi-Sunter), document provenance.

The iterative pattern is particularly suited to Exocortex integration because each stage can be mapped to a dedicated agent or tool-call session, with the output of one stage feeding the next and triggering targeted sub-investigations.

## 5. Exocortex Integration Architecture

Automating the OSINT toolchain within Agent Zero exploits structural isomorphisms between the tools and the framework's primitives:

- **call_subordinate pattern**: SpiderFoot's module architecture mirrors Exocortex's delegation model — each module is a specialized recon agent. A master orchestration agent can launch SpiderFoot scans, collect results, then launch Recon-ng modules as subordinates.
- **Entity Resolution Pipeline**: SpiderFoot's structured output feeds directly into Splink-based Fellegi-Sunter probabilistic matching [[entity-resolution-agent-safety]], [[knowledge-graph-construction-patterns]]. Maltego's entity/pivot model structurally maps to Exocortex's knowledge graph construction.
- **Local LLM NER Triage**: Local LLM (e.g., Qwen3.6-27B) can run named entity recognition on raw toolchain output to extract people/organization/location entities before database insertion — a batch processing task where frontier performance is unnecessary [[bridging-local-to-frontier-model-performance]].
- **Rate Limiting & OPSEC**: SpiderFoot's module-level rate limiting integrates with behavioral mimicry techniques from [[behavioral-mimicry-osint]] to avoid blocking. Recon-ng allows custom user-agent strings and proxy configuration.
- **API Key Management**: Each tool requires separate API keys for many modules (SHODAN, SecurityTrails, Censys, etc.). Exocortex pattern: store credentials in environment variables or a secure vault, never in pipeline scripts.

## 6. Cross-Domain Connections

1. **Entity Resolution Stack**: Automated toolchain outputs feed directly into the five-pillar entity resolution pentagon (corporate registries → lobbying → contracts → property → campaign finance) by producing structured entity seeds.
2. **Network Analysis & Community Detection**: SpiderFoot's GEXF export feeds into Gephi/NetworkX for centrality measures and community detection [[community-detection-osint]].
3. **Bridging Local-to-Frontier**: Local LLM can run NER on raw toolchain output, then escalate ambiguous matches to frontier models for resolution.
4. **DNS & WHOIS Investigation**: theHarvester domain enumeration seeds DNS/WHOIS deep-dive; toolchain automates the handoff [[dns-whois-investigation-osint]].
5. **Social Media OSINT**: Recon-ng's social media modules bridge into identity investigation and cross-platform correlation [[social-media-osint-identity-investigation]].
6. **Timeline Reconstruction**: Automated timestamps from toolchain outputs populate the temporal evidence layer [[timeline-reconstruction-osint]].
7. **Anti-Bot Evasion**: SpiderFoot's rate limiting and proxy rotation integrate with behavioral mimicry [[behavioral-mimicry-osint]].
8. **Data Breach Analysis**: SpiderFoot's HaveIBeenPwned module links to breach identity linkage methodologies [[data-breach-analysis-osint-identity-linkage]].
9. **Financial Intelligence**: SpiderFoot's corporate modules produce company identifiers that cross-reference with FINCEN SAR/CTR data [[financial-intelligence-entity-resolution]].
10. **Counterintelligence Analysis**: Tool outputs feed structured analytic techniques (ACH) for source credibility assessment [[counterintelligence-analysis-frameworks]].
11. **IP Geolocation**: theHarvester IP enumeration and SpiderFoot SHODAN module provide geolocation seeds [[ip-address-geolocation]].
12. **Visualization**: Standardized JSON output feeds link analysis (Maltego), network graphs (Gephi), and timeline visualization [[visualization-techniques-osint]].

## 7. Sources

1. Agent Zero Exocortex wiki — [[open-source-osint-tools-survey]] (2026-07-03): Seven-layer tool taxonomy and cross-domain integration.
2. Agent Zero Exocortex wiki — [[open-source-osint-investigation-tools]] (2026-06-05): Detailed Maltego CE, SpiderFoot, Recon-ng, theHarvester analysis and Exocortex integration potential.
3. Agent Zero Exocortex wiki — [[open-source-osint-tools-ecosystem]] (2026-05-20): Multi-stage investigation workflow and cross-domain connections.
4. Gilbert, D. (2018) *Web Penetration Testing with Kali Linux*, 3rd ed., Packt Publishing. Chapters 3: Recon-ng, theHarvester, Maltego basics.
5. Beggs, R. (2018) *Mastering Kali Linux for Advanced Penetration Testing*, 2nd ed., Packt Publishing. Chapter 3: Recon-ng framework architecture and advanced usage.
6. SpiderFoot official documentation: https://www.spiderfoot.net/documentation/
7. Recon-ng framework GitHub: https://github.com/lanmaster53/recon-ng
8. theHarvester GitHub: https://github.com/laramies/theHarvester
9. Splink (Fellegi-Sunter probabilistic matching): https://github.com/moj-analytical-services/splink
