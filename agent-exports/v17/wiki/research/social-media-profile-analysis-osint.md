# Social Media Profile Analysis for OSINT

**Status:** STABLE
**Created:** 2026-06-05
**Last updated:** 2026-06-05
**Interest:** OSINT & Investigation Methodology
**Line Count:** ~280

## Overview

Social media profile analysis is the systematic extraction, evaluation, and correlation of publicly available data from individual and organizational social media accounts to support open-source intelligence (OSINT) investigations. While account discovery and cross-platform identity linkage (covered in [[social-media-osint]]) address the "find" problem, profile analysis addresses the "understand" problem: given a located account, what can be inferred about the person or organization behind it?

This page covers the four-layer analysis framework: (1) profile attribute extraction, (2) content analysis, (3) network analysis, and (4) authenticity assessment. It also addresses the legal and ethical boundaries governing social media OSINT and maps the analysis pipeline to Exocortex's autonomous agent architecture.

With 5.24 billion social media users generating an estimated 2.5 quintillion bytes of data daily (DataReportal 2026), automated profile analysis is not a luxury — it is the only scalable approach for intelligence production.

---

## 1. Profile Attribute Extraction

### 1.1 Static Attributes

Static profile attributes are the metadata fields that platforms make publicly available. These serve as blocking keys for entity resolution and baseline signals for authenticity assessment:

| Attribute | Investigative Value | Exocortex Mapping |
|-----------|-------------------|-------------------|
| Username | Candidate for cross-platform enumeration; reveals naming conventions, interests, birth year | Cross-platform identity correlation |
| Display name | Real name or pseudonym; often contains name variations useful for record linkage | Entity resolution (name variant detection) |
| Bio/Description | Free-text self-description containing affiliations, location, interests, pronouns | NLP entity extraction -> knowledge graph nodes |
| Profile photo | Face for reverse image search; metadata for camera/device fingerprinting | [[reverse-image-search-visual-osint]] |
| Join date | Account age as authenticity signal; temporal alignment with life events | Temporal pattern analysis |
| Follower/following counts | Influence metrics; unusual ratios flag bot/sockpuppet accounts | Authenticity scoring |
| Location field | Self-reported geolocation (highly manipulable but still informative when cross-referenced) | IP geolocation correlation |
| URL/bio links | External website, other social profiles, or linktree aggregators | Graph edge construction |

### 1.2 Automated Enumeration Tools

The first generation of profile discovery tools use username-to-platform mapping. The second generation adds AI-powered analysis and cross-platform synthesis:

| Tool | Platforms | Key Capability | License |
|------|----------|---------------|--------|
| **Sherlock** | 400+ | Fast username enumeration; CLI-based; JSON/CSV output | MIT |
| **Maigret** | 2,500+ | Advanced fork of Sherlock; false-positive detection; HTML reports; Tor support | MIT |
| **WhatsMyName** | 500+ | Web-based username enumeration with continuous community updates | Open source |
| **Holehe** | 100+ | Email-to-account mapping; determines whether an email is registered on specific platforms | GPL-3.0 |
| **snscrape** | Twitter/X, Reddit, Facebook, Instagram, Telegram, VK, Weibo | High-volume content scraping without API authentication; outputs JSON/CSV | GPL-3.0 |
| **Social Analyzer** (Qeeqbox) | 1,000+ | Multi-interface (CLI/API/Web); reliability scoring 0-100 per finding | AGPL-3.0 |
| **Maltego** | Multi-platform transforms | Link analysis with commercial and community transforms | Commercial |
| **OWASP SocialOSINTAgent** | Twitter/X, Reddit, HN, Bluesky, GitHub, Mastodon | LLM + vision model analysis; natural language query interface; structured analytical reports | Apache 2.0 |
| **Espectro** | 200+ | Commercial cross-platform search with real-time monitoring | Commercial |

See also: [[social-media-osint]] for account discovery methodology and [[cross-platform-identity-correlation]] for user identity linkage techniques.

---

## 2. Content Analysis

Content analysis transforms unstructured social media posts into structured behavioral and psychological signals. The pipeline has three tiers:

### 2.1 Linguistic and Sentiment Analysis

**LIWC (Linguistic Inquiry and Word Count):** The foundational computational tool for psychological text analysis (Pennebaker & King, 1999). LIWC categorizes words into ~90 validated dimensions — function words, emotional tone, cognitive processes, social references — that map to Big Five personality traits:

- High Extraversion -> first-person plural pronouns, social words
- High Neuroticism -> first-person singular pronouns, negative emotion words
- High Openness -> differentiation words, cognitive complexity markers
- High Conscientiousness -> achievement words, work references
- Low Agreeableness -> swear words, anger markers, negations

**Sentiment Analysis:** VADER (rule-based, optimized for social media text) and transformer-based models (BERT, RoBERTa fine-tuned on sentiment) extract valence, arousal, and dominance dimensions from post content. Sentiment trajectories over time — not just point estimates — reveal emotional stability, response to events, and potential behavioral crises.

**Topic Modeling:** Latent Dirichlet Allocation (LDA) and BERTopic identify thematic clusters in posting history, revealing the subject's primary interests, areas of expertise, and shifts in focus. Topic distribution over time detects life events (job changes, relocation, radicalization).

### 2.2 Personality Inference from Digital Footprints

The watershed finding by Kosinski, Stillwell, and Graepel (2013, PNAS) demonstrated that Facebook Likes alone could predict:
- Sexual orientation: 88% accuracy (male), 75% (female)
- Ethnicity: 95% accuracy
- Religious beliefs: 82% accuracy
- Political party: 85% accuracy
- Personality traits (Big Five): r=0.35-0.45 correlation with self-report

This established that digital footprints contain psychometrically meaningful signals even without natural language analysis. Subsequent work extended this to:
- **Instagram photos** (Segalin et al., 2017): personality prediction from visual features (color composition, face presence, filter choice)
- **Twitter/X linguistic patterns** (Schwartz et al., 2013): open-vocabulary approach outperforming closed-vocabulary LIWC
- **Cross-platform consistency** (Tskhay & Rule, 2014): personality signals are remarkably consistent across platforms

### 2.3 Temporal and Behavioral Pattern Analysis

Posting behavior itself is a rich signal independent of content:

| Signal | Indicates | Analysis Method |
|--------|----------|-----------------|
| Posting frequency by hour | Timezone, sleep schedule, occupation type | Circular statistics, Fourier analysis |
| Posting frequency by day | Work schedule, weekend patterns | Periodogram analysis |
| Response latency | Engagement type (professional vs. personal), bot indicators | Distribution fitting |
| Content type ratio (text/image/video/share/comment) | Platform usage style, authenticity | Multinomial modeling |
| Device/OS fingerprint from post metadata | Affluence proxy, travel patterns | Header analysis (see [[email-header-analysis-ip-tracing]]) |
| Language switching | Multilingualism, geographic origin, education | Language detection, code-switching analysis |

---

## 3. Network Analysis

Network analysis examines the social graph surrounding a profile — who they follow, who follows them, interaction patterns, and community membership.

### 3.1 Graph Construction

**Nodes:** Accounts (target + direct connections + second-degree connections where relevant)
**Edges:** Follows, mutual follows, mentions, replies, retweets, likes, shares, tags, group co-membership
**Edge weights:** Interaction frequency, recency, reciprocity

Tools for graph construction:
- **snscrape** — scrape follower/following lists and interaction data
- **Twint** (legacy) / **Twikit** — Twitter/X graph extraction
- **Instaloader** — Instagram follower/following data
- **Maltego** with Social Links transforms — multi-platform graph construction

### 3.2 Graph Analysis Metrics

| Metric | Investigative Significance |
|--------|---------------------------|
| **Degree centrality** | Raw influence; high in-degree accounts are opinion leaders |
| **Betweenness centrality** | Information brokerage; accounts that bridge communities are key intelligence nodes |
| **Eigenvector centrality** | Influence weighted by neighbor importance (PageRank equivalent) |
| **Clustering coefficient** | Tightness of social circle; low clustering with high degree suggests broadcast account |
| **Modularity / Community detection** (Louvain, Leiden) | Identifies distinct social clusters; target's community memberships reveal affiliations |
| **Homophily score** | Tendency to connect with similar others; deviations flag anomalous connections |

### 3.3 Interaction Pattern Analysis

Beyond graph structure, interaction patterns reveal relationship quality:
- **Reciprocity ratio:** Ratio of mutual follows to one-way follows
- **Response rate:** How often the target responds to replies/mentions
- **Interaction asymmetry:** Accounts the target engages with heavily vs. those that engage with the target
- **Temporal interaction clustering:** Bursts of activity suggesting coordinated campaigns

---

## 4. Authenticity Assessment

Not all social media accounts represent the person or organization they claim to. Authenticity assessment is a critical layer that gates all downstream analysis — conclusions drawn from fake or compromised accounts are worse than useless; they are actively misleading.

### 4.1 Bot Detection

Automated accounts (bots) can be classified by behavior, not content:

| Signal | Bot Indicator | Human Indicator |
|--------|--------------|----------------|
| Posting frequency | Supra-human rates (>100 posts/day sustained) | Diurnal patterns with gaps |
| Temporal regularity | CV < 0.1 in inter-post intervals | Variable posting patterns |
| Content diversity | Low entropy in vocabulary, topics, or media types | High entropy across dimensions |
| Network structure | Low clustering, high degree from follows | Higher clustering, more mutuals |
| Response behavior | No contextual replies; keyword-triggered only | Contextual engagement |
| Account age vs. activity | High activity from new accounts | Activity proportional to account age |

**Tools:**
- **Botometer** (formerly BotOrNot) — machine learning classifier trained on 1,000+ features across six dimensions (network, user, friends, temporal, content, sentiment)
- **Bot Sentinel** — Twitter/X bot detection with historical database
- **SocialBearing Pro** — Twitter/X analytics with built-in bot detection and coordinated behavior identification

### 4.2 Sockpuppet Detection

Sockpuppets are multiple accounts controlled by a single human operator, used for deception, astroturfing, or identity concealment. Detection methods fall into three categories:

**Feature-based methods:**
- Writing style fingerprinting (stylometry): function word distribution, punctuation patterns, typo rates
- Profile attribute similarity: similar bios, profile photos, join dates
- Shared metadata: device fingerprints, IP addresses, geolocation patterns

**Interaction-based methods:**
- Co-occurrence patterns: sockpuppets rarely interact with each other directly but interact with the same set of authentic accounts
- Propagation tree analysis (Li & Zhou): examining how information propagates through a network; sockpuppet trees show structural anomalies in branching patterns, depth, and diffusion speed compared to organic propagation
- Temporal coordination: correlated posting times, coordinated topic shifts

**Graph-based methods:**
- Adaptive multi-source feature extraction (Yu et al., 2021, Springer): combines verbal features (writing style), non-verbal features (profile attributes), and network-structure features with dynamic feature weighting
- Telegram case study (arXiv 2105.10799): interaction-graph-based detection using weighted neighbor normalization with thresholded edges (weight < 0.5 dropped) to identify accounts controlled by the same user

### 4.3 Coordinated Inauthentic Behavior (CIB)

CIB detection has become the primary paradigm for influence operation identification, superseding content-based detection. See [[influence-operations-detection-countermeasures]] for the full IO framework.

Key CIB indicators:
- **Velocity anomalies:** Sudden bursts of activity from accounts with no prior history
- **Message synchronization:** Identical or near-identical content posted within tight time windows across multiple accounts
- **Amplification patterns:** Small groups of accounts whose content is rapidly amplified by larger bot networks
- **Network cohesion:** Dense interconnection among accounts that should have no organic reason to interact
- **Account reuse:** Same account participating in multiple campaigns on different topics

**Tools:**
- **Cyabra** — real-time CIB detection for OSINT/intelligence teams
- **DFR Lab** (Atlantic Council) — methodologies for tracking digital forensic research in influence operations
- **xpoz.ai** — AI-powered disinformation campaign detection combining OSINT and behavioral analysis

---

## 5. Legal and Ethical Boundaries

Social media OSINT operates in a complex legal landscape where jurisdiction, data type, and collection method determine permissibility.

### 5.1 Legal Frameworks

| Regulation | Jurisdiction | Key Provisions |
|------------|-------------|---------------|
| **GDPR** (2018) | EU/EEA | Requires lawful basis for processing personal data; Article 14 mandates notification when collecting from third-party sources; special category data (political, religious, sexual orientation) has heightened protections |
| **CFAA** (1986, US) | United States | Prohibits unauthorized access to computer systems; scraping in violation of ToS may constitute unauthorized access (pending Supreme Court clarification) |
| **LGPD** (2020) | Brazil | Similar to GDPR; applies to any processing of Brazilian residents' data |
| **Platform ToS** | Global | Most platforms prohibit automated scraping in their Terms of Service; violations risk account suspension and IP blocking |

### 5.2 Ethical Guidelines

Professional OSINT organizations (Bellingcat, GIJN, OCCRP) generally adhere to these principles:
- **Public data only:** Analyze only publicly available information; do not attempt to access private accounts
- **No impersonation:** Do not create fake accounts to connect with targets or infiltrate private groups
- **Proportionality:** The depth of investigation should be proportional to the public interest served
- **Data minimization:** Collect only what is necessary; do not hoover up bulk data without investigative purpose
- **Corroboration:** Profile analysis findings should be corroborated with independent sources before forming conclusions
- **Subject rights:** Where feasible and legally required, subjects should have the opportunity to correct factual errors

---

## 6. Integration with Exocortex Architecture

Social media profile analysis maps cleanly to Exocortex's autonomous agent infrastructure:

### 6.1 Tool Delegation Pattern

Each analysis layer can be delegated to specialized subordinate agents:
- **Profile extraction agent** — runs Sherlock/Maigret/Holehe, parses output, normalizes attributes -> writes to knowledge graph
- **Content analysis agent** — runs snscrape collection, NLP analysis (sentiment, topic modeling, LIWC), personality inference -> appends observation nodes
- **Network analysis agent** — constructs follower graph, computes centrality/community metrics -> adds relationship edges to knowledge graph
- **Authenticity assessment agent** — runs Botometer, stylometric comparison, coordination detection -> assigns authenticity confidence scores

### 6.2 Scheduled Monitoring

The Exocortex scheduler can automate periodic re-analysis:
- **Daily:** Check for new posts, update sentiment trajectory
- **Weekly:** Re-compute network metrics, detect structural changes
- **Monthly:** Re-run authenticity assessment, check for account compromise indicators

### 6.3 Knowledge Graph Integration

Profile analysis outputs feed into the knowledge graph construction pipeline:
- **Entities:** Person nodes with profile attributes as properties
- **Observations:** Content analysis findings (topics, sentiment, personality traits) as time-stamped observations
- **Relations:** FOLLOWS, MENTIONS, INTERACTS_WITH edges linking person nodes
- **Confidence scores:** Authenticity assessment results stored as entity-level metadata

### 6.4 Cross-Dataset Correlation

Profile analysis is most powerful when combined with other OSINT data sources:
- **Email -> social profile:** Holehe linkage, then content analysis
- **Phone -> social profile:** Reverse phone lookup -> profile discovery
- **Username -> cross-platform profiles:** Sherlock/Maigret -> personality consistency analysis across platforms
- **Photo -> identity:** Reverse image search -> profile matching -> content analysis

---

## 7. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| [[social-media-osint]] | Account discovery and cross-platform UIL provide the input accounts for profile analysis |
| [[email-header-analysis-ip-tracing]] | Email-to-profile linkage (Holehe); IP geolocation correlation with self-reported location |
| [[reverse-image-search-visual-osint]] | Profile photo -> identity verification -> profile analysis enrichment |
| [[open-source-entity-resolution-frameworks]] | Profile attributes as blocking keys for entity resolution; content-derived personality traits as matching features |
| [[influence-operations-detection-countermeasures]] | CIB detection is the coordination layer on top of individual profile analysis; behavioral velocity detection |
| [[agentic-self-learning]] | Automated monitoring pipelines; tool delegation patterns for multi-layer analysis |
| [[memory-architecture-taxonomy]] | Profile analysis findings as episodic memories with temporal decay; authenticity scores as memory confidence metadata |
| [[network-analysis-techniques-osint]] | Graph construction and centrality analysis of social follower networks |
| [[knowledge-graph-construction]] | Structured ingestion of profile attributes, observations, and relationship edges |
| [[counterintelligence-analysis-frameworks]] | Sockpuppet detection as counter-deception technique; source reliability scoring (Admiralty Code) applied to profile authenticity |
| [[pdf-ingestion-knowledge-base-enrichment]] | PDF ingestion tools for processing downloaded social media archives and reports |

---

## 8. References

1. Kosinski, M., Stillwell, D., & Graepel, T. (2013). Private traits and attributes are predictable from digital records of human behavior. *Proceedings of the National Academy of Sciences*, 110(15), 5802-5805.
2. Pennebaker, J.W., & King, L.A. (1999). Linguistic styles: Language use as an individual difference. *Journal of Personality and Social Psychology*, 77(6), 1296-1312.
3. Schwartz, H.A., et al. (2013). Personality, gender, and age in the language of social media: The open-vocabulary approach. *PLOS ONE*, 8(9), e73791.
4. Segalin, C., et al. (2017). The pictures we like are our image: Continuous mapping of favorite pictures into self-assessed and attributed personality traits. *IEEE Transactions on Affective Computing*, 8(2), 268-285.
5. Yu, H., Hu, F., Liu, L., Li, Z., Li, X., & Lin, Z. (2021). Sockpuppet Detection in Social Network Based on Adaptive Multi-source Features. *Advances in Natural Computation, Fuzzy Systems and Knowledge Discovery*. Springer.
6. Li, Z. & Zhou, X. Sockpuppet Detection in Social Network via Propagation Tree. Semantic Scholar.
7. Social-Media-OSINT-Tools-Collection. GitHub: osintambition. https://github.com/osintambition/Social-Media-OSINT-Tools-Collection
8. OWASP SocialOSINTAgent. https://owasp.org/www-project-social-osint-agent/
9. Espectro. (2026). Social Media Investigation: OSINT Techniques. https://www.espectrosint.com/blog/social-media-investigation
10. Cyabra. Disinformation Detection for Intel & OSINT Teams. https://cyabra.com/solutions/intelligence-osint-analysts/
11. Rolli IQ. (2026). Influence operations detection paradigm shift: content to behavioral. Referenced in [[influence-operations-detection-countermeasures]].
12. SocialBearing Pro. Twitter/X analytics with bot detection. https://socialbearing.com/

---

*Page deepened from DRAFT (~30 lines) to STABLE (~280 lines) during BUILD cycle 403. Added tools survey (table of 9 tools with capabilities), four-layer analysis framework (static attributes, content analysis, network analysis, authenticity assessment), LIWC/personality inference foundations (Kosinski et al. 2013, Schwartz et al. 2013, Segalin et al. 2017), sockpuppet detection methods (feature-based, interaction-based, graph-based including arXiv 2105.10799 Telegram case study), coordinated inauthentic behavior detection cross-reference, legal/ethical framework table (GDPR, CFAA, LGPD, Platform ToS), Exocortex architecture integration (tool delegation pattern, scheduled monitoring, knowledge graph integration, cross-dataset correlation), 11 cross-domain connections, 12 references.*
