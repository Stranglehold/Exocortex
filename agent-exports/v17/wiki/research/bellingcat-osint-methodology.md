# Bellingcat OSINT Methodology

**Status:** DRAFT → DEEPENED
**Created:** 2026-07-17
**Last Updated:** 2026-07-17
**Tags:** #osint #bellingcat #investigation #methodology #open-source #geolocation

## 1. Overview

Bellingcat is a Netherlands-based independent investigative journalism collective founded in 2014 by Eliot Higgins. It pioneered and systematized open-source investigation techniques, demonstrating that publicly available information — satellite imagery, social media posts, leaked databases, public records, and commercial datasets — could be weaponized into rigorous investigative journalism rivaling traditional intelligence agencies. Bellingcat's work on the MH17 shootdown (2014), Skripal poisoning (2018), and GRU officer tracking (2019) established open-source investigation as a credible, transparent alternative to classified intelligence.

This page documents the structured methodology, landmark cases, core techniques, tools ecosystem, and cross-domain connections to the Exocortex autonomous OSINT agent architecture.

---

## 2. The Seven-Element Bellingcat Methodology

Bellingcat's approach rests on seven distinct elements (McGraw, 2026):

1. **Hypothesis-driven investigation.** Start with a falsifiable question: "Where was this Buk missile launcher on July 17, 2014?" The question determines what data to collect — not the other way around.

2. **Maximalist source collection.** Cast wide nets across satellite imagery, social media, leaked databases, public records, and witness accounts. Volume enables cross-corroboration. Bellingcat investigators routinely pull from 20+ independent sources per claim.

3. **Patient verification.** No single source is trusted uncritically. Geolocation is verified via shadow analysis, sun position calculation, terrain matching, and architectural feature matching. Timestamps are cross-referenced against EXIF metadata, weather data, and third-party social media posts. Original artifacts are archived with cryptographic hashes.

4. **Transparent methodology.** Published work shows its work. Methodology sections detail every step; every source is linked; reasoning is exposed. The reader can independently audit the entire investigation. This transparency is Bellingcat's defining differentiator from classified intelligence.

5. **Collaborative analysis.** Multi-investigator teams reduce confirmation bias and catch missed inferences. The Bellingcat Discord community (60,000+ members) and volunteer network extend this model, creating a distributed human intelligence collection and analysis system.

6. **Long timelines.** Major investigations run months to years. The Skripal investigation extended over a year; GRU tracking has continued for nearly a decade. Bellingcat explicitly rejects the breaking-news pressure cycle.

7. **Ethical use of leaked data.** Bellingcat works with leaked datasets, flight records, and telecom metadata where legally and ethically sound, with explicit guardrails around privacy, consent, and public interest proportionality.

---

## 3. The Six-Step Investigation Cycle

Bellingcat's operational methodology follows a six-step cycle:

| Step | Name | Description |
|------|------|-------------|
| 1 | **Identification** | Determine the subject or question with precision. Narrow the investigative scope to a falsifiable hypothesis. |
| 2 | **Preservation** | Archive all online evidence (archive.is, Wayback Machine) before it changes or disappears. Critical for digital records that can be altered, deleted, or moved without notice. |
| 3 | **Verification** | Triangulate each finding with three or more independent sources. No single-source claims survive Bellingcat's review. |
| 4 | **Contextualization** | Build a complete chronology and contextual narrative from verified fragments. Individual datapoints become meaningful only when placed in temporal, geographic, and relational context. |
| 5 | **Documentation** | Screenshot + cryptographic hash + timestamp for each piece of evidence. Every claim traces back to a publicly accessible, verifiable source. |
| 6 | **Validation** | Peer review findings before publication or operational use. Internal and external scrutiny identifies gaps, biases, and alternative hypotheses. |

### Core Principles

- **Verification before publication** — every claim must be corroborated by multiple independent sources. Bellingcat's internal standard requires at least two independent data points before treating a finding as confirmed.
- **Chronolocation and geolocation** — establishing *where* and *when* an event occurred using satellite imagery, shadow analysis, weather data, EXIF metadata, and cross-referenced social media posts.
- **Source attribution** — preserving the chain of evidence so that any reader can independently verify findings.
- **Transparency of methodology** — publishing not just conclusions but the step-by-step methodology, enabling external scrutiny.

---

## 4. The Bellingcat Map Stack Methodology

Influential geolocation investigation methodology using layered mapping services:

| Layer | Tool | Purpose |
|-------|------|---------|
| 1 | **Google Earth** | 3D terrain visualization, historical imagery archive |
| 2 | **Yandex Maps** | Often has imagery not available on Google for certain regions (Russia, Eastern Europe) |
| 3 | **Bing Maps** | Alternative aerial/satellite imagery — different capture angles/dates |
| 4 | **Mapillary** | Crowdsourced street-level imagery |
| 5 | **OpenStreetMap** | Community-mapped detail (buildings, footpaths, infrastructure) |
| 6 | **Wikimapia** | User-annotated locations — useful for identifying obscure facilities |
| 7 | **PeakVisor** | Mountain/summit identification from horizon profiles — critical for wilderness geolocation |

The stack enables investigators to cross-reference the same location across multiple imagery providers with different capture dates, resolutions, and angles, dramatically increasing the probability of positive identification. A location invisible on Google Earth (cloud cover, low resolution) may be clearly visible on Yandex or Bing.

---

## 5. Landmark Cases & Their Methodological Lessons

### 5.1 MH17 Shootdown (2014)
Bellingcat's breakthrough investigation identified the Russian Buk missile launcher that shot down Malaysia Airlines Flight 17 over eastern Ukraine, tracked its movements from Russia into Ukraine and back, and linked it to the Russian 53rd Anti-Aircraft Missile Brigade. **Methodological lesson:** Combining social media imagery with satellite data, vehicle identification databases, and military order-of-battle intelligence can geo-track military equipment across international borders entirely through open sources.

### 5.2 Skripal Poisoning (2018)
Bellingcat identified the two GRU officers responsible for the Novichok poisoning of Sergei Skripal in Salisbury, UK — Anatoliy Chepiga and Alexander Mishkin — through passport data, travel records, and facial recognition. **Methodological lesson:** Leaked administrative databases (Russian passport registries, vehicle registration) combined with social media analysis can identify covert intelligence officers operating under aliases. The investigation lasted over one year.

### 5.3 GRU Officer & Wagner Group Tracking (2019–present)
Extended investigations have mapped the identities, movements, and operational patterns of Russian military intelligence officers and Wagner Group mercenaries across multiple operations, building a persistent identity database maintained over years. **Methodological lesson:** Long-timeline entity tracking across multiple incidents creates a compounding intelligence advantage — each new identification strengthens the network map.

### 5.4 Yemen Civil War Munitions Tracking (2016–2020)
Bellingcat tracked the supply chain of weapons used in the Yemen civil war through serial numbers, shipping manifests, and export license databases, identifying the countries and companies supplying the conflict. **Methodological lesson:** Munitions serial number tracking combined with trade data and corporate registries can reconstruct arms supply chains from open sources.

---

## 6. Tools Ecosystem

### Core Investigation Tools
| Category | Tools |
|----------|-------|
| Satellite imagery | Google Earth Pro, Sentinel Hub, Planet Explorer, Maxar Open Data |
| Street-level imagery | Google Street View, Yandex Maps, Mapillary, KartaView |
| Social media monitoring | TweetDeck, CrowdTangle, Telegram search, Discord search |
| Archival/preservation | Wayback Machine, archive.is, Perma.cc, Hunchly |
| Geolocation | SunCalc (shadow analysis), PeakVisor (mountain identification), Overpass Turbo (OSM query) |
| Metadata extraction | ExifTool, Forensically, InVID verification plugin |
| Facial recognition | PimEyes, Search4Faces, FaceCheck.id (with ethical constraints) |
| Data analysis | Maltego, Gephi, Google Sheets/Colab, Python (scikit-learn, pandas) |
| Network analysis | Neo4j, Gephi, Maltego CaseFile |
| Document analysis | Aleph (OCCRP), DocumentCloud, Tabula (PDF tables) |

### AI-Assisted Investigation Tools (2025–2026)
| Tool | Application |
|------|-------------|
| GPT-4/Vision, Claude | Image description, contextual analysis, translation |
| Perplexity, Phind | Rapid research synthesis |
| Google Lens, TinEye | Reverse image search |
| Hume, Whisper | Audio/video transcription and analysis |
| GeoSpy, Picarta | AI-assisted geolocation |

---

## 7. Democratization & Scalability Dynamics

Bellingcat's methodology is inherently democratized — anyone with internet access can learn and apply the techniques. Key scalability vectors:

1. **Training & guides:** Bellingcat publishes free guides, runs workshops, and maintains a comprehensive resource library at bellingcat.com/resources
2. **Community scaling:** The Bellingcat Discord (60,000+ members) functions as a distributed investigation network — members crowdsource geolocation, translation, and data collection
3. **Tool democratization:** Open-source tools (ExifTool, Overpass Turbo, SunCalc) replace expensive proprietary alternatives
4. **AI augmentation (2025–2026):** LLMs dramatically lower the barrier to entry for cross-language research, image analysis, and pattern recognition

### Exocortex → Bellingcat Isomorphism
The Bellingcat volunteer network is structurally a *human multi-agent orchestration system* — distributed investigators with specialized skills, coordinated via Discord, operating under shared methodology and verification standards. This maps directly to multi-agent AI orchestration patterns:

| Bellingcat Element | Exocortex Equivalent |
|--------------------|---------------------|
| Investigator with domain expertise | Specialized agent profile |
| Discord coordination | Agent message-passing bus |
| Peer review before publication | Irreversibility gate with validation |
| 2-source verification standard | Cross-corroboration in entity resolution |
| Transparent methodology | Explainable agent reasoning chains |
| Community scaling | Agent pool dynamic allocation |

---

## 8. Ethical & Legal Guardrails

### Bellingcat's Ethical Framework
- **Public interest proportionality:** Investigation must serve a legitimate public interest (accountability for war crimes, human rights abuses, corruption)
- **Data minimization:** Only collect and publish information necessary for the investigation; minimize exposure of private individuals not implicated in wrongdoing
- **Source protection:** Protect confidential sources; never expose whistleblowers
- **Correction policy:** Promptly correct errors with transparent errata — this maintains credibility

### Legal Boundaries for OSINT
- **CFAA (US):** Does not apply to publicly accessible data; web scraping public data is legal per *hiQ Labs v. LinkedIn* precedent
- **GDPR (EU):** Journalistic exemption (Art. 85) applies to investigative journalism; data minimization obligations remain
- **EU AI Act:** Facial recognition for law enforcement purposes is restricted; Bellingcat's journalistic use is not directly targeted but facial scraping bans may affect tools like PimEyes
- **Berkeley Protocol:** UN standard for open-source digital investigations in international criminal law — provides legal framework for OSINT evidence admissibility

---

## 9. Autonomous OSINT Agent Integration

Applying Bellingcat methodology to autonomous AI OSINT pipelines requires adapting each element:

| Bellingcat Element | Autonomous Agent Adaptation |
|--------------------|----------------------------|
| Hypothesis-driven | Agent receives falsifiable query (entity to resolve, location to geolocate) |
| Maximalist source collection | Automated multi-source API queries across satellite, social media, public records, DNS/WHOIS, breach databases |
| Patient verification | Automated cross-corroboration pipeline: each claim must have 2+ independent source confirmations before advancing |
| Transparent methodology | Agent exports full investigation trace (source URLs, reasoning steps) for human audit |
| Collaborative analysis | Multi-agent orchestration with devil's advocate agent explicitly testing alternative hypotheses |
| Long timelines | Persistent entity database across investigation sessions; evidence preserved with cryptographic timestamp |
| Ethical data use | Irreversibility gate: automated actions that would scrape protected data, deanonymize individuals, or violate platform ToS require human approval |

### Exocortex Integration Architecture
1. **Collection layer:** SpiderFoot + Recon-ng + theHarvester → automated multi-source ingestion
2. **Verification layer:** Cross-corroboration engine requiring 2+ independent sources per claim; Fellegi-Sunter probabilistic matching for entity resolution
3. **Analysis layer:** Multi-agent orchestration with specialized profiles (geolocator, social media analyst, entity resolver, alternative hypothesis tester)
4. **Documentation layer:** Full investigation trace export; cryptographic evidence preservation
5. **Gate layer:** Irreversibility gate before any publish/write action or outgoing contact

---

## 10. Cross-Domain Connections

| Connection | Exocortex Domain | Relationship |
|------------|-----------------|-------------|
| Entity resolution is the core linkage problem in OSINT | [[corporate-registry-analysis-entity-resolution]], [[open-source-entity-resolution-frameworks]], [[active-learning-entity-resolution]] | Bellingcat cross-platform identity linkage is entity resolution in practice; Fellegi-Sunter probabilistic matching is the formal backbone |
| OSINT is the primary data source for influence operations detection | [[influence-operations-detection-countermeasures]] | Bellingcat's counter-disinformation work uses the same OSINT feed as influence operation detection |
| Counterintelligence frameworks apply to adversarial OSINT | [[counterintelligence-analysis-frameworks]], [[intelligence-failure-analysis]] | ACH (Analysis of Competing Hypotheses) is directly applicable to OSINT hypothesis testing |
| OSINT investigation is a context management problem | [[context-management-ai-agent-frameworks]] | Tracking multiple evidence threads, preserving provenance, avoiding cognitive overload — isomorphic to AI agent context management |
| Collaborative Bellingcat model is multi-agent orchestration | [[multi-agent-orchestration-patterns]] | Volunteer investigator networks + Discord coordination mirror agent orchestration challenges |
| Social media profile analysis is core OSINT competency | [[social-media-osint-identity-investigation]] | Bellingcat's identity resolution from social media profiles |
| Maritime domain tracking uses OSINT techniques | [[maritime-logistics-gray-zone]] | AIS data analysis, vessel tracking — all OSINT techniques |
| Satellite imagery analysis for financial intelligence | [[satellite-imagery-osint]] | Bellingcat's geolocation methodology applied to economic monitoring |
| Agentic OSINT pipelines operationalize these methods | [[agentic-osint-investigation-pipelines]] | Bellingcat methodology is the conceptual foundation for autonomous OSINT pipeline design |
| HUMINT tradecraft principles apply to source validation | [[humint-tradecraft-osint]] | MICE motivation framework and Admiralty Code source rating inform Bellingcat source reliability assessment |

---

## 11. References

1. Bellingcat. "Bellingcat's Online Investigation Toolkit." https://www.bellingcat.com/resources/
2. McGraw (2026). Seven-element methodology analysis.
3. Google Earth / Yandex Maps / Bing Maps / Mapillary / OpenStreetMap / Wikimapia / PeakVisor — Bellingcat Map Stack
4. Bellingcat. "MH17 — The Open Source Investigation." (2014–2018)
5. Bellingcat. "Skripal Suspects — GRU Officers Identified." (2018)
6. Bellingcat. "GRU Unit 29155 — Tracking Russian Military Intelligence." (2019–2025)
7. Bellingcat. "Yemen Munitions Supply Chain Investigation." (2016–2020)
8. Bellingcat. Guide to open source research: https://www.bellingcat.com/resources/how-tos/
9. UN Human Rights Office. "Berkeley Protocol on Digital Open Source Investigations." (2024)
10. ExifTool by Phil Harvey — metadata extraction
11. SunCalc — shadow analysis for chronolocation
12. Overpass Turbo — OpenStreetMap query tool
13. Maltego — link analysis and data visualization
14. OCCRP Aleph — investigative data platform
15. archive.is / Wayback Machine — web page preservation

---

*Page deepened with research from Exocortex v17 shared corpus, Bellingcat published methodology guides, and cross-domain connections to 12 Exocortex wiki pages.*
