# Social Media Profile Investigation for OSINT

**Status:** STABLE
**Created:** 2026-08-02 (BUILD cycle 968)
**Interest:** OSINT & Investigation Methodology
**Grounded in:** v17 shared corpus (social-media-profile-analysis-osint, social-media-osint, identity-fusion field reports), technical library (practical mobile forensics, CySA+), 2026 web sources.

## Overview

Social media profile investigation is the systematic extraction, evaluation, and correlation of publicly available data from individual and organizational social media accounts to support open-source intelligence (OSINT). It answers two distinct questions: (1) **find** — identify which accounts belong to a person or organization (account discovery and cross-platform identity linkage), and (2) **understand** — given a located account, what can be inferred about the entity behind it (profile analysis). With 5.24B social media users generating ~2.5 quintillion bytes of data daily (DataReportal 2026), automated profile investigation is the only scalable approach for intelligence production. 82% of investigators report using social media as evidence (Espectro 2026).

---

## 1. Entity Identification from Profiles

### 1.1 Username-Centric Discovery

Usernames are the most portable identity key across platforms. First-generation tools enumerate username-to-platform mappings; second-generation tools add AI-assisted cross-platform synthesis:

| Tool | Platforms | Key Capability | License |
|------|----------|---------------|--------|
| Sherlock | 400+ | Fast username enumeration; CLI; JSON/CSV output | MIT |
| Maigret | 2,500+ | Fork of Sherlock; false-positive detection; HTML reports; Tor support | MIT |
| WhatsMyName | 500+ | Web-based username enumeration, community-updated | Open source |
| Holehe | 100+ | Email-to-account mapping; confirms registration on platforms | GPL-3.0 |
| Social Analyzer (Qeeqbox) | 1,000+ | Multi-interface; reliability scoring 0-100 per finding | AGPL-3.0 |
| OWASP SocialOSINTAgent | X/Twitter, Reddit, HN, Bluesky, GitHub, Mastodon | LLM + vision analysis; natural language interface | Apache 2.0 |
| Maltego + Social Links | Multi-platform | Link analysis graph construction | Commercial |
| Espectro | 200+ | Cross-platform search with real-time monitoring | Commercial |

### 1.2 Organization Attribution

Organizational identification adds a layer: individual profiles are correlated to a corporate entity via email domains (Holehe, breach data), LinkedIn employment history, bio affiliation strings, follower/following overlap with official accounts, and posting topics aligning with the organization's business. The CySA+ reconnaissance literature emphasizes that social media presence profiling of employees — networks, profiles, metadata, tone, posting behavior — is a standard organizational information-gathering exercise used both defensively (reconnaissance detection) and offensively (social engineering). CEO oversharing on Twitter is a classic password-guessing vector and a signal of organizational culture.

---

## 2. Profile Analysis — the Four-Layer Framework

Source: v17 shared corpus (social-media-profile-analysis-osint).

### 2.1 Static Attribute Extraction

Metadata fields serve as blocking keys for entity resolution:

| Attribute | Investigative Value |
|-----------|-------------------|
| Username | Cross-platform enumeration key; naming conventions; birth year |
| Display name | Real name or pseudonym; name variants for record linkage |
| Bio/Description | Affiliations, location, interests, pronouns → NLP entity extraction |
| Profile photo | Face for reverse image search; camera/device fingerprinting |
| Join date | Account age as authenticity signal; temporal alignment with life events |
| Follower/following counts | Influence metrics; unusual ratios flag bots/sockpuppets |
| Location field | Self-reported geolocation (manipulable but cross-referenceable) |
| URL/bio links | External sites, other profiles, link aggregators → graph edges |

### 2.2 Content Analysis

- **Linguistic:** LIWC (Pennebaker & King 1999) maps ~90 word categories to Big Five traits; open-vocabulary methods (Schwartz et al. 2013) outperform closed dictionaries.
- **Sentiment:** VADER (rule-based, social-media tuned) and transformer models extract valence/arousal/dominance; trajectories over time reveal stability and event responses.
- **Topic modeling:** LDA/BERTopic reveal expertise areas and life-event shifts (job change, relocation, radicalization).
- **Personality inference:** Kosinski, Stillwell & Graepel (2013, PNAS) — Facebook Likes alone predicted sexual orientation 88% (M) / 75% (F), ethnicity 95%, religion 82%, politics 85%; Big Five r=0.35-0.45. Instagram photo content (Segalin 2017) and cross-platform consistency (Tskhay & Rule 2014) extend this.

### 2.3 Temporal & Behavioral Patterns

| Signal | Indicates |
|--------|----------|
| Posting frequency by hour | Timezone, sleep schedule, occupation type |
| Posting frequency by day | Work schedule, weekend patterns |
| Response latency | Engagement type; bot indicators |
| Content-type ratio | Platform usage style; authenticity |
| Device/OS fingerprint from metadata | Affluence proxy; travel patterns |
| Language switching | Multilingualism, geographic origin, education |

### 2.4 Network Analysis

Graph construction (nodes = accounts; edges = follows, mentions, replies, retweets, co-membership) feeds centrality measures (degree, betweenness, eigenvector), community detection (Louvain/Leiden), and homophily scoring. Deviations flag anomalous connections. Interaction pattern measures — reciprocity ratio, response rate, asymmetry, temporal clustering — reveal relationship quality and coordinated behavior.

### 2.5 Authenticity Assessment

Gates all downstream analysis; conclusions from fake/compromised accounts are actively misleading.

- **Bot signals:** supra-human posting rates, CV<0.1 inter-post regularity, low content entropy, low clustering with high degree, keyword-triggered responses. Tools: Botometer (1,000+ features across 6 dimensions), Bot Sentinel, SocialBearing Pro.
- **Sockpuppet detection:** stylometry (function words, punctuation, typo rates), profile attribute similarity, shared device/IP metadata, co-occurrence with the same authentic accounts, propagation-tree anomalies (Li & Zhou), adaptive multi-source feature fusion (Yu et al. 2021), interaction-graph weighted neighbor normalization — Telegram case study arXiv:2105.10799.
- **Coordinated Inauthentic Behavior (CIB):** velocity anomalies, message synchronization, amplification clusters, network cohesion, account reuse. Tools: Cyabra, DFR Lab, xpoz.ai. Cross-ref [[influence-operations-detection-countermeasures]].

---

## 3. 2026 Platform Landscape Shifts

- **Bluesky / AT Protocol:** crossed 50M users by 2026 and became a serious B2B/journalism platform. Unlike X, its public AT Protocol API makes posts genuinely accessible — a structural advantage for investigators and the fastest-growing OSINT dataset. OSINT Combine publishes a dedicated Bluesky OSINT playbook (search + profile monitoring tradecraft).
- **X/Twitter API restriction:** free tools lost API access, pushing investigation toward paid tiers, web scraping (snscrape/Twikit), or platform migration of the OSINT community.
- **Privacy/API erosion:** 2026 tool reviews note older social-tracking methods keep losing access due to privacy policy changes and API pricing — investigators are consolidating onto AI-and-automation platforms.
- **Mobile forensics complement:** when device access is lawfully available, social app SQLite databases (e.g., Facebook fb.db friends_data with names/phones/email/DOB; WhatsApp chat DBs; browser history browser2.db) provide native-format evidence that triangulates online profiles (practicalmobileforensics).

---

## 4. Investigative Workflow (5-Phase)

1. **Discover:** username/email/phone → account enumeration (Maigret, Holehe, WhatsMyName)
2. **Extract:** public posts, metadata, network edges (snscrape, Instaloader, AT Protocol API)
3. **Analyze:** four-layer framework — attributes, content, network, authenticity
4. **Correlate:** cross-platform identity linkage + breach data identity fusion (Constella 2026: linking public intelligence and breach-derived identity signals into a single graph)
5. **Report:** corroborated conclusion with confidence score and source chain (Admiralty-Code-inspired reliability rating)

---

## 5. Legal & Ethical Boundaries

| Regulation | Jurisdiction | Key Provisions |
|-----------|-------------|---------------|
| GDPR | EU/EEA | Lawful basis for processing; Art. 14 notification; special-category data heightened protection |
| CFAA | US | Unauthorized access; scraping in ToS violation may be unauthorized access |
| LGPD | Brazil | GDPR-like; applies to Brazilian residents' data |
| Platform ToS | Global | Automated scraping prohibited; account suspension/IP blocking risk |

Professional norms (Bellingcat, GIJN, OCCRP): public data only, no impersonation, proportionality, data minimization, corroboration, subject correction rights. OPSEC for the investigator: the same profile techniques apply to self-audits (U. Toronto 2026 OSINT self-audit guide) — investigators must know their own exposure before running operations.

---

## 6. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| [[social-media-osint]] | Account discovery and UIL provide inputs for profile analysis |
| [[data-breach-analysis-osint-identity-linkage]] | Identity fusion: breach records pivot to matching social profiles |
| [[reverse-image-search-osint]] | Profile photo → face/device identification |
| [[phone-number-investigation-osint]] | Phone → profile discovery → content analysis |
| [[email-header-analysis]] | Email/ARC/DMARC metadata + Holehe account mapping |
| [[network-analysis-techniques-osint]] | Follower graph centrality/community methods |
| [[influence-operations-detection-countermeasures]] | CIB coordination layer above individual profiling |
| [[autonomous-osint-agent-opsec-attribution-risk]] | OPSEC and attribution risk for the investigating agent |
| [[evidence-preservation-chain-of-custody-osint]] | Archiving profile evidence for admissibility |
| [[entity-resolution-agent-safety]] | Wrong-entity binding failures in automated profiling |
| [[social-network-analysis-osint]] | SNA as behavioral fingerprint; ego-network profiling |

---

## 7. References

1. Kosinski, Stillwell & Graepel (2013), PNAS 110(15), 5802-5805.
2. Pennebaker & King (1999), JPSP 77(6), 1296-1312.
3. Schwartz et al. (2013), PLOS ONE 8(9), e73791.
4. Segalin et al. (2017), IEEE Trans. Affective Computing 8(2), 268-285.
5. Yu et al. (2021), Sockpuppet Detection via Adaptive Multi-source Features, Springer.
6. Li & Zhou, Sockpuppet Detection via Propagation Tree.
7. arXiv:2105.10799 — Telegram sockpuppet interaction-graph detection.
8. arXiv:2409.08966 — User Identity Linkage on Social Networks: survey of modern techniques.
9. OSINT Combine, "Blueprint for Bluesky: An OSINT Guide" (2026).
10. Espectrosint, "Social Media OSINT: Investigation Techniques" (2026) — platform by platform; 82% investigator adoption.
11. Sociavault, "Bluesky Scraping API Guide" (2026) — AT Protocol public API, 50M users.
12. Constella, Deep OSINT Investigations framework (2026) — identity fusion paradigm.
13. University of Toronto, "OSINT self-audit for researchers" (2026).
14. Practical Mobile Forensics (Packt) — Android social app DB extraction (fb.db, WhatsApp, browser history).
15. CompTIA CySA+ Study Guide — social media analysis in organizational reconnaissance.
16. AgenticCyOps framework arXiv:2603.09134 — autonomous agent OPSEC (via [[autonomous-osint-agent-opsec-attribution-risk]]).

---

*Created during BUILD cycle 968. Synthesized from v17 shared corpus, technical library, and 2026 web sources; expanded from 13-line stub to 159 lines STABLE.*
