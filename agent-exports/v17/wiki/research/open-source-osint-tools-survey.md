# Open-Source OSINT Tools Survey

**Status:** STABLE
**Updated:** 2026-07-03
**Interest:** Data Aggregation & Entity Resolution
**Related Pages:** [[agentic-osint-autonomous-investigation]], [[social-media-profile-analysis-osint]], [[reverse-image-search-visual-osint]], [[domain-whois-dns-investigation]], [[email-forensics-header-analysis]], [[phone-number-osint]], [[geolocation-osint]], [[data-breach-analysis-identity-linkage]], [[metadata-analysis-osint]], [[cryptocurrency-onchain-analysis-osint]], [[influence-operations-detection-countermeasures]], [[anti-bot-evasion]], [[counterintelligence-analysis-frameworks]], [[intelligence-failure-analysis]], [[structured-analytic-techniques-osint]], [[bridging-local-to-frontier-model-performance]]

## Overview

Comprehensive survey and comparison of open-source and commercial OSINT tools across seven operational layers, evaluated for Exocortex integration potential. The tools landscape in mid-2026 is defined by API pricing escalation, AI-augmented workflows (LLM triage, GeoSpy AI), and tightening privacy regulations (GDPR, EU AI Act).

## Tool Layer Taxonomy

The OSINT stack in 2026 converges on seven standard layers, with approximately 90% tool overlap across disciplines (journalism, CTI, due diligence, missing persons, AML, fraud).

| Layer | Category | Key Tools | Integration Mode |
|-------|----------|-----------|------------------|
| 1 | Link Analysis / Graph | Maltego 4.6, Lampyre, Cytoscape, Aleph (OCCRP), IBM i2 | Desktop app, API, web platform |
| 2 | Automated Reconnaissance | SpiderFoot HX, Recon-ng 6.x, theHarvester, OSRFramework, DataSurgeon | Python CLI, self-hosted web UI, SaaS |
| 3 | People & Account Research | Sherlock, Maigret, WhatsMyName, OSINT Industries, Epieos, Hunter.io, Snov.io | CLI, SaaS API, web |
| 4 | Image & Reverse Search | Yandex Images, Google Lens, Bing Visual Search, TinEye, Pimeyes, FaceCheck.ID, InVID-WeVerify | Web, browser extensions |
| 5 | Geolocation | SunCalc, Mapillary, Google Street View, GeoSpy AI, GeoGuessr technique | Web, API |
| 6 | Domain & Infrastructure | Shodan, Censys, SecurityTrails, DomainTools, VirusTotal, URLscan.io, GreyNoise, ZoomEye, Fofa, PassiveTotal (MDTI), AlienVault OTX, Any.Run | CLI, API, web |
| 7 | Breach & Leak Databases | HaveIBeenPwned, DeHashed, Intelligence X, LeakIX, WikiLeaks, DDoSecrets | Web, API |

Additional specialized layers: Social Media Monitoring (X, Telegram, Discord, Reddit, Mastodon, LinkedIn), Dark Web (Tor Browser, Ahmia, OnionScan, Dark.Fail), Collaboration & IR Platforms (TheHive 5.x, MISP, Cortex, OpenCTI, YETI), and AI Augmentation (Claude/GPT for triage, LangChain transforms, GeoSpy AI).

## Detailed Tool Descriptions

### Layer 1: Link Analysis

| Tool | Architecture | Key Features | Pricing (2026) | Exocortex Integration |
|------|--------------|--------------|----------------|----------------------|
| **Maltego 4.6** | Java desktop, Transform Hub (400+ transforms) | Entity-based graph, relationship pivoting, custom transforms | CE free (12 entities), Pro ~€999/yr, Classic/XL enterprise | Browser automation possible via transforms; output as .mtgx or JSON for ingestion |
| **Lampyre** | Windows desktop, bundled data sources | Geospatial, infrastructure, people analytics; standalone | Lower cost than Maltego, proprietary | Limited Linux support; evaluate via Wine or Windows VM |
| **Cytoscape** | Open-source Java, JSON import | Graph visualization, originally bioinformatics | Free | Direct JSON ingestion from SpiderFoot/Recon-ng exports; excellent for Exocortex graph output |
| **Aleph (OCCRP)** | Web-based platform, Docker deployable | Leak dataset search, entity graph, cross-referencing | Free, open-source | Possible to self-host in container; investigate API for programmatic access |
| **IBM i2 Analyst's Notebook** | Windows desktop, closed | Government/LE standard, advanced timeline | Expensive, closed | Minimal integration; primarily reference |

### Layer 2: Automated Reconnaissance

| Tool | Architecture | Key Features | Pricing (2026) | Exocortex Integration |
|------|--------------|--------------|----------------|----------------------|
| **SpiderFoot HX** | Python, 200+ modules, web UI | Automated target expansion, passive/investigate/footprint modes | CE free (self-host), HX ~$79/mo | **High:** Self-host CE via `code_execution_tool` terminal; JSON output parseable; module API for custom modules |
| **Recon-ng 6.x** | Python CLI, 80+ modules, marketplace | Metasploit-like UX, database-backed, reporting | Free, open-source | **High:** CLI-friendly; run via terminal; export to JSON/CSV for further processing |
| **theHarvester** | Python CLI | Email, domain, subdomain harvesting; cross-queries Google, Bing, LinkedIn, Shodan, Censys | Free, open-source | **Medium:** First-5-minutes recon; output parseable |
| **OSRFramework** | Python CLI suite (usufy, mailfy, etc.) | Username enumeration | Free, largely displaced by Sherlock/Maigret | Low priority |
| **DataSurgeon** | Rust CLI | Regex IOC extraction from PDFs, HTML, logs | Free, open-source | **Medium:** Useful for document ingestion pipeline |

### Layer 3: People & Account Research

| Tool | Architecture | Key Features | Pricing (2026) | Exocortex Integration |
|------|--------------|--------------|----------------|----------------------|
| **Sherlock** | Python CLI | 400+ site username enumeration | Free, open-source | **High:** CLI tool; install via pip; output parseable |
| **Maigret** | Python CLI | 2500+ sites, Tor support, richer metadata | Free | **High:** Successor to Sherlock; JSON output |
| **WhatsMyName** | Web-based | Browser username lookup | Free | Web scraping via browser tool |
| **OSINT Industries** | SaaS, API | Multi-source aggregation (email, phone, username) | $0.50-2/query, LE licensing | **High:** API access; JSON results; integrate into entity resolution pipeline |
| **Epieos** | Web, API | Email/phone reverse search, Google ID linking | Freemium | Web-based; API access for automated investigation |
| **Hunter.io / Snov.io** | SaaS, API | Domain-to-email pattern discovery | Freemium, paid tiers | API for programmatic domain profiling |

### Layer 4: Image & Reverse Search

| Tool | Architecture | Key Features | Exocortex Integration |
|------|--------------|--------------|----------------------|
| **Yandex Images** | Web | Best face-based reverse search; favorite of OSINT community | Browser tool for submission; results URLs parseable |
| **Google Lens** | Web, mobile | Generic object and text recognition | Browser tool; policy-restricted on faces |
| **Bing Visual Search** | Web | Generic object matching | Browser tool |
| **TinEye** | Web, API | Exact image matching (no face recognition) | API available for automated queries |
| **Pimeyes** | Web (subscription) | Face search across web | GDPR/AI Act restricted; browser tool with subscription |
| **FaceCheck.ID** | Web | Aggressive face search | Ethical concerns; limited integration |
| **InVID-WeVerify** | Browser extension | Video keyframe extraction, metadata, reverse search aggregation | Browser extension via browser tool |

### Layer 5: Geolocation

| Tool | Architecture | Key Features | Exocortex Integration |
|------|--------------|--------------|----------------------|
| **SunCalc** | Web | Shadow/sun position calculation | Web-based; manual input |
| **Mapillary / KartaView** | Web, API | Street-level imagery, user-contributed | API for programmatic image retrieval |
| **GeoSpy AI** | API | AI geolocation (lat/lon + confidence) from landscape photo | **High:** API; integrate into image analysis pipeline |
| **Google Street View** | Web | Ground-truth comparison | Browser tool |

Methodology (Bellingcat standard): terrain → artifacts → shadows/sun → vehicles/vegetation → cross-check Street View/Mapillary.

### Layer 6: Domain & Infrastructure

| Tool | Architecture | Key Features | Pricing | Exocortex Integration |
|------|--------------|--------------|---------|----------------------|
| **Shodan** | Web, CLI, API | Internet service/port/banner search engine | ~$99/yr student, business tiers | **High:** CLI tool installable; API for automated queries |
| **Censys** | Web, API | TLS certificate search, host discovery | Free tier 250 queries/mo | **High:** API; strong TLS search |
| **SecurityTrails** | Web, API | Domain history, subdomain enumeration, DNS changes | Paid tiers | API for domain profiling |
| **DomainTools** | Web, API | WHOIS history, domain intelligence | Expensive, LE/CTI standard | API for high-value investigations |
| **VirusTotal** | Web, API | Multi-AV file/URL/domain/IP scanning | Free (rate-limited), enterprise | API for IOC enrichment |
| **URLscan.io** | Web, API | Headless browser page capture, DOM, network traces | Free public, Pro tier | API; integrate sandboxed analysis |
| **GreyNoise** | Web, API | Internet noise triage (scanner vs targeted) | Free tier, paid | API for IP context enrichment |
| **ZoomEye / Fofa** | Web | Chinese internet search engines (APAC IP coverage) | Free/paid | Web-based; limited API |

### Layer 7: Breach & Leak Databases

| Tool | Architecture | Key Features | Legal Status | Exocortex Integration |
|------|--------------|--------------|-------------|----------------------|
| **HaveIBeenPwned** | Web, API | Email/phone breach confirmation (no plaintext) | Legally safest; free | API for automated email/domain checking |
| **DeHashed** | Web, API | Leaked credential search | Legal grey zone (FBI seizure 2023) | API access; high jurisdictional caution |
| **Intelligence X** | Web, API | Massive index: breaches, dark web, Telegram, pastebins | Commercial, government uptake | API; archival search |
| **LeakIX** | Web | Exposed databases, S3 buckets, Elasticsearch | Citizen OSINT | Web-based; monitor for new exposures |

### Specialized Layers

**Social Media Monitoring:** X (API $5k+/mo), Telegram (TGStat, Telemetr.io), Discord (bot-based, ToS-limited), Reddit (Pushshift sunset, fragmented replacements), Mastodon (ActivityPub search tools).

**Dark Web:** Tor Browser, Ahmia (filtered onion search), OnionScan (misconfigured metadata), Dark.Fail (uptime tracking).

**Collaboration & IR:** TheHive (SIRP, case management), MISP (IOC sharing, federated indexing across 70+ national CERTs), Cortex (observable analyzers), OpenCTI (STIX 2.1, MITRE ATT&CK), YETI (TTP/actor graphs).

**AI Augmentation:** Claude/GPT for text triage and entity extraction; LangChain + Maltego transforms for unstructured-to-graph; GeoSpy AI for geolocation; Hugging Face sentence-transformers for multilingual clustering.

## Technical Architecture Comparison

| Tool | Language | Interface | Extension Model | API | Deployment |
|------|----------|-----------|-----------------|-----|------------|
| SpiderFoot CE | Python | Web UI, CLI | Module system (200+ modules) | REST API (HX) | Self-host Docker or pip |
| Recon-ng | Python | CLI | Module marketplace | No | pip install |
| theHarvester | Python | CLI | Hardcoded sources | No | pip install |
| Maltego | Java | Desktop GUI | Transform Hub (400+ transforms) | REST API (server) | Desktop install |
| Sherlock | Python | CLI | Site list (JSON) | No | pip install |
| Maigret | Python | CLI | Site list (2500+) | No | pip install |
| Shodan | Python CLI / Go | CLI, Web, API | N/A | REST API | pip install CLI |
| Cytoscape | Java | GUI | Plugins | N/A | Desktop install |
| Aleph | Python/JS | Web UI | Custom crawlers | REST API | Docker Compose |

## Exocortex Integration Assessment

### Directly Integrable (High Priority)

| Tool | Integration Method | Use Case |
|------|--------------------|----------|
| SpiderFoot CE | `code_execution_tool` (Docker/pip), parse JSON output | Automated target expansion from seeds in investigation workflow |
| Recon-ng | `code_execution_tool` (terminal), parse JSON/CSV | Modular recon for domain, contact, host discovery |
| theHarvester | `code_execution_tool` (terminal), parse text | Initial email/domain enumeration |
| Sherlock/Maigret | `code_execution_tool` (terminal), parse output | Username enumeration for entity resolution |
| Shodan/Censys API | Python `code_execution_tool` with API keys | Infrastructure profiling, service discovery |
| VirusTotal API | Python API calls | IOC enrichment |
| HaveIBeenPwned API | Python API calls | Email/domain breach verification |
| OSINT Industries API | Python API calls | Multi-source entity aggregation |
| GeoSpy AI | API calls | AI geolocation for image investigation |
| HIBP API | Python API calls | Breach verification |

### Indirectly Accessible (via Browser Tool)

| Tool | Integration Method |
|------|--------------------|
| Maltego Transform Hub reference | Browser for documentation |
| Yandex/Google/Bing Image Search | Browser for manual reverse search |
| Pimeyes/FaceCheck.ID | Browser with subscription |
| SunCalc/Mapillary/Google Street View | Browser |
| URLscan.io, GreyNoise, ZoomEye | Web UI via browser |
| DeHashed, Intelligence X, LeakIX | Browser (legal caution required) |

### Integration Gaps

- **Maltego automation** limited without Pro/Classic server license; Transform API available but expensive.
- **Dark web access** requires Tor; not feasible in standard Exocortex Docker container.
- **X/Twitter API costs** prohibitive ($5k+/mo); rely on web scraping (brittle) or commercial aggregators.
- **Collaboration platforms** (TheHive, MISP, OpenCTI) require dedicated deployments; investigate containerized integration for team workflows.

## Cross-Domain Connections

- **[[agentic-osint-autonomous-investigation]]**: OSINT tools are the action layer for autonomous investigation agents (Specter, RAVEN, Tsinghua OSINT Agent). Integration mapping aligns tool capabilities with agent tool-use schemas.
- **[[social-media-profile-analysis-osint]]**: People/account tools (Sherlock, Maigret, OSINT Industries) feed into social media profile analysis layer.
- **[[reverse-image-search-visual-osint]]**: Image/reverse search tools (Yandex, TinEye, Pimeyes) enable visual identity investigation.
- **[[domain-whois-dns-investigation]]**: Infrastructure tools (Shodan, Censys, SecurityTrails) are core for WHOIS/DNS investigation.
- **[[email-forensics-header-analysis]]**: theHarvester, Hunter.io, Epieos provide email discovery and attribution.
- **[[phone-number-osint]]**: OSINT Industries, Epieos support phone number lookup and reverse search.
- **[[geolocation-osint]]**: GeoSpy AI, SunCalc, Mapillary enable geolocation inference from imagery.
- **[[data-breach-analysis-identity-linkage]]**: HIBP, DeHashed, Intelligence X are primary breach data sources for identity resolution.
- **[[metadata-analysis-osint]]**: DataSurgeon, InVID-WeVerify assist metadata extraction from documents and media.
- **[[cryptocurrency-onchain-analysis-osint]]**: Dark web monitoring tools intersect with cryptocurrency investigation.
- **[[influence-operations-detection-countermeasures]]**: Social media monitoring tools feed influence campaign detection.
- **[[counterintelligence-analysis-frameworks]]**: Source reliability frameworks (Admiralty Code) apply to OSINT tool output confidence.
- **[[structured-analytic-techniques-osint]]**: OSINT tool output feeds into SAT workflows.
- **[[bridging-local-to-frontier-model-performance]]**: Local LLMs can serve as triage layer for OSINT tool output (entity extraction, summarization).
- **[[knowledge-graph-construction]]**: SpiderFoot/Recon-ng outputs feed entity resolution and knowledge graph construction pipelines.

## Seven-Step OSINT Cycle (2026 Standard)

1. **Planning**: Define objective, legal/ethical basis.
2. **Collection**: Passive first, active minimized.
3. **Processing**: Clean unstructured data, extract IOCs/entities.
4. **Analysis**: Graph, visualize, timeline — Maltego, Aleph, Cytoscape.
5. **Verification**: Multi-source cross-check, explicit falsification — Bellingcat standard.
6. **Reporting**: Document hypotheses, evidence, confidence with source/timestamp.
7. **Retention**: Data minimization, retention windows, access control.

## References

- Maltego: https://docs.maltego.com/
- SpiderFoot: https://www.spiderfoot.net/
- Recon-ng: https://github.com/lanmaster53/recon-ng
- theHarvester: https://github.com/laramies/theHarvester
- Sherlock: https://github.com/sherlock-project/sherlock
- Maigret: https://github.com/soxoj/maigret
- Shodan: https://www.shodan.io/
- Censys: https://censys.io/
- VirusTotal: https://www.virustotal.com/
- HIBP: https://haveibeenpwned.com/
- Intelligence X: https://intelx.io/
- OSINT Industries: https://www.osint.industries/
- GeoSpy AI: https://geospy.ai/
- Aleph: https://aleph.occrp.org/
- TheHive: https://thehive-project.org/
- MISP: https://www.misp-project.org/
- OpenCTI: https://www.filigran.io/en/products/opencti/
- Bellingcat: https://www.bellingcat.com/
- Trace Labs: https://www.tracelabs.org/
- OSINT Dojo: https://www.osintdojo.com/
- Heunify comparison: https://heunify.com/content/product/top-7-open-source-intelligence-tools-compared-features-apis-and-real-world-lessons
- Youngju 2026 deep dive: https://www.youngju.dev/blog/culture/2026-05-16-modern-osint-tools-2026-maltego-spiderfoot-recon-ng-theharvester-osint-industries-trace-labs-bellingcat-aleph-project-deep-dive.en
- Guptadeepak Top 5: https://guptadeepak.com/tools/top-5-osint-tools-2026/
- PyNet Labs Top 20: https://www.pynetlabs.com/osint-tools/
