# Human Investigation & OSINT

## Status: STABLE (deepened)
## Last updated: 2026-05-19
## Source: BUILD cycle 26
## Primary sources: history-of-intelligence-operations field report, OpenPlanter entity_resolution.py, DuckDuckGo OSINT methodology search, research_topics.promptinclude.md agent directive

---

## Overview

Human Investigation & OSINT (Open Source Intelligence) is the discipline of identifying
individuals and organizations from publicly available data sources — corporate registries,
campaign finance records, social media, public records databases, domain registrations,
leaked datasets, satellite imagery, and other open sources. It is practiced by journalists
(e.g., Bellingcat), law enforcement, private investigators, intelligence agencies, and
corporate due diligence teams.

The US Intelligence Community's *OSINT Strategy 2024–2026* explicitly calls for integrating
OSINT "more fully into IC workflows, tradecraft, and all-source analysis," recognizing that
open-source signals now frequently provide the initial lead that triggers tasking for
HUMINT or SIGINT collection.

This wiki entry covers OSINT methodology, entity identification from identifiers (phone,
email, IP), anti-bot evasion techniques, network analysis, and legal boundaries — all from
the perspective of an autonomous agent that can execute OSINT workflows programmatically.

---

## 1. OSINT Tradecraft & Methodology

### Bellingcat Methodology
The Bellingcat method — named after the investigative journalism collective — has become
the benchmark for open-source investigation. Its core principles:

1. **Verification before publication** — every claim must be corroborated by multiple
   independent sources. Bellingcat's internal standard requires at least two independent
   data points before treating a finding as confirmed.
2. **Chronolocation and geolocation** — establishing *where* and *when* an event occurred
   using satellite imagery, shadow analysis, weather data, EXIF metadata, and cross-referenced
   social media posts.
3. **Source attribution** — preserving the chain of evidence so that any reader can
   independently verify findings. Every claim traces back to a publicly accessible source.
4. **Transparency of methodology** — Bellingcat publishes not just conclusions but the
   step-by-step methodology used to reach them, enabling external scrutiny.

### Source Credibility Assessment
Every OSINT data source must be assessed for:
- **Authority** — who published it? What are their credentials and track record?
- **Proximity** — how close was the source to the event? First-hand observation vs
  third-hand reporting?
- **Timeliness** — when was the data published? Is it still current?
- **Motive** — why was this information made public? Propaganda? Transparency? Self-interest?

This mirrors HUMINT source validation protocols from the intelligence world: a source's
reliability (track record) and access (proximity to information) must be assessed
independently before relying on their reporting.

### HUMINT-to-OSINT Fusion Framework
The history-of-intelligence-operations field report (2026-05-19) maps eight core HUMINT
tradecraft principles to OSINT equivalents:

| HUMINT Principle | OSINT Application |
|-----------------|-------------------|
| **Elicitation** — extracting information through structured conversation without the source realizing the target | Phased questioning: start broad, narrow to specifics. Avoid telegraphing the investigation's true target to monitored forums. |
| **Rapport building** — establishing trust to increase source cooperation | When contacting human sources during OSINT (journalists, researchers, forum members), build credibility through demonstrated domain knowledge before asking questions. |
| **Source validation** — verifying source reliability and access before relying on information | Every OSINT data source assessed for authority, proximity, timeliness, and motive. |
| **Parallel construction** — building an evidentiary chain from non-classified sources that independently confirms classified intelligence | Triangulate claims across at least three independent data sources before treating them as confirmed. |
| **Cover and legend** — maintaining consistent operational identity | Compartmentalize research identities: separate browser profiles, email personas, and access patterns for different investigations. |
| **Operational security (OPSEC)** — protecting methods, sources, and the investigator | VPNs/Tor, metadata stripping from documents, avoiding DNS leaks, understanding server log exposure. |
| **Dangle and access agent operations** — positioning a source to be recruited by the target | Honeypot documents, controlled data leaks to observe who accesses or acts on them, tracking document propagation through watermarking. |
| **Dead drops and cut-outs** — intermediaries who break the chain of direct contact | Dead-drop file hosting (anonymous upload services), publishing findings through third-party platforms, using journalists as cut-outs. |

### Timeline Reconstruction
OSINT investigations frequently require reconstructing event sequences from multiple
fragmented sources — social media timestamps, news reports, satellite imagery dates,
camera footage. Key techniques:
- **Anchor events** — identify events with incontrovertible timestamps (e.g., satellite
  overpass times, news broadcasts) and use them as temporal anchors.
- **Relative ordering** — when absolute timestamps are unavailable, establish relative
  order using causal dependencies (post A responds to post B, etc.).
- **Metadata extraction** — EXIF data from photos, video upload timestamps, DNS registration
  dates all provide temporal evidence.

---

## 2. Entity Identification from Identifiers

The research_topics.promptinclude.md directive lists these as priority investigation areas.

### Phone Number → Identity Resolution
Phone numbers are among the most powerful identifiers in OSINT because they are:
- **Required for account creation** — many services require phone verification (Signal,
  Telegram, WhatsApp, Google, Facebook).
- **Stable over time** — people change email addresses more frequently than phone numbers.
- **Geographically grounding** — country codes, area codes, and carrier assignments provide
  geographic signals.

Techniques:
- **Carrier lookups** — LRN (Location Routing Number) databases reveal current carrier and
  number type (mobile/landline/VoIP).
- **Data broker lookup** — paid services aggregate phone-to-identity resolution from
  public records, utilities, and marketing databases.
- **VoIP detection** — numbers from Twilio, Google Voice, and similar services can be
  identified by carrier LRN (e.g., "Bandwidth.com" for many VoIP providers).
- **Reverse phone search** — free tools (Truecaller, SpyDialer, Zabasearch) provide
  varying levels of identity resolution.
- **Leaked database correlation** — phone numbers appearing in breach databases (Have I
  Been Pwned, DeHashed) can be correlated with email addresses and usernames.

### Email Address → Identity Resolution
Email addresses are the primary online identifier for most people. Resolution techniques:

1. **Domain analysis** — corporate email domains (e.g., @company.com) immediately
   associate the individual with an organization. Personal email domains (e.g., @gmail.com,
   @protonmail.com) signal different threat models.
2. **Pattern analysis** — many email addresses encode names directly (first.last@domain,
   firstinitiallastname@domain). Automated name extraction via regex patterns succeeds
   in ~70% of cases for Western naming conventions.
3. **Breach database lookup** — DeHashed, IntelX, SnusBase, and HaveIBeenPwned provide
   email-to-password and email-to-username correlation.
4. **Public profile enumeration** — many services reveal account existence via password
   reset flows, signup checks, or "forgot username" flows. Tools like Holehe check
   email registration across 100+ services.
5. **Gravatar and avatar hash** — MD5 hash of normalized email addresses can be queried
   against Gravatar to retrieve profile photos, which can then be reverse image searched.

### Email Header Analysis
Email headers contain a forensic trail of every server that handled the message. Key
header fields for investigation:

- **Received:** (plural) — the most forensically valuable field. Each hop records the
  receiving server's view of the sender. The *first* Received header (top of the chain)
  was added by the sender's own mail server, potentially revealing their IP address.
- **X-Originating-IP:** — Many email providers (Microsoft, Yahoo) add this field
  containing the sender's originating IP, often the user's residential IP.
- **Authentication-Results:** — SPF (authorized sending IPs), DKIM (cryptographic
  signature verification), and DMARC (policy enforcement) results indicate whether the
  email's claimed origin matches its actual origin.
- **Message-ID:** — Contains the sending server's hostname, useful for infrastructure
  attribution.
- **Return-Path:** — The bounce address; may differ from From: and reveal
  sending infrastructure.

Header forgery is trivial for all fields *except* the Received chain (which is appended
by servers the email actually passed through) and DKIM signatures (which are
cryptographically verified). A header analysis that focuses on the Received chain and
DKIM results is the hardest to forge.

### IP Tracing
IP addresses are weaker identifiers than phone/email but still valuable:

- **Geolocation databases** — MaxMind, IP2Location, and DB-IP provide city-level
  geolocation with varying accuracy (90-99% country, 60-80% city, depending on region).
- **ASN and BGP lookups** — IP-to-ASN resolution identifies the autonomous system
  (ISP, hosting provider, enterprise). Cloud IPs (AWS, Azure, GCP) are distinguishable
  from residential ISPs.
- **WHOIS history** — historical WHOIS data can reveal ownership changes over time.
- **Passive DNS** — resolves IPs to domain names historically associated with them.
- **Shodan/Censys scanning** — reveals services running on the IP, which can fingerprint
  the operator (e.g., self-hosted services, IoT devices).
- **Tor exit node detection** — IP addresses listed in Tor exit node databases are
  effectively anonymous for geolocation purposes.

---

## 3. Entity Resolution Algorithms (OpenPlanter Integration)

The OpenPlanter study's `entity_resolution.py` implements a deterministic matching
pipeline between Boston City Council candidates (OCPF campaign finance data) and
city contract vendors. This is a concrete example of the entity resolution problem
in practice.

### Algorithm Pattern
1. **Identifier extraction** — parse CPF IDs (unique candidate identifiers) from
   candidates.txt and match them to OCPF receipt records.
2. **Name normalization** — vendor/contributor names are normalized (case folding,
   punctuation removal, whitespace normalization) before matching.
3. **Exact matching** — where unique identifiers exist (e.g., CPF ID, DUNS number),
   match directly.
4. **Fuzzy matching** — where only names overlap, apply similarity thresholds (Jaro-Winkler,
   Levenshtein, or TF-IDF cosine similarity).
5. **Cross-reference scoring** — where multiple attributes overlap (name + address +
   employer), compute composite match scores.

### Fellegi-Sunter Model
The canonical probabilistic entity resolution approach: for each pair of records, compute
a weight representing the log-likelihood ratio that they match vs. don't match. Fields
that agree contribute positive weight; fields that disagree contribute negative weight.
Optimal decision thresholds are derived from estimated error rates.

### Deterministic vs Probabilistic
- **Deterministic matching** — records match if they share exactly the same value on a
  set of key fields (e.g., SSN, email). Simple, fast, but brittle (typos defeat it).
- **Probabilistic matching** — each field comparison contributes fractional evidence.
  Handles typos, transpositions, missing data, and cross-dataset variation. Computationally
  more expensive but more robust.

### Cross-Jurisdictional Linking
Different jurisdictions use different identifier formats (US SSN vs UK NINO vs Canadian
SIN), different corporate registration systems (SEC EDGAR vs Companies House vs
Handelsregister), and different naming conventions. Entity resolution across borders
requires:
- Identifier format recognition and normalization
- Name transliteration for non-Latin scripts
- Address standardization (geocoding to lat/lon as canonical form)
- Temporal alignment (records from different years must be compared at equivalent time slices)

---

## 4. Anti-Bot Evasion & Collection

Automated OSINT collection at scale requires bypassing anti-bot defenses that websites
deploy. This is a technical arms race.

### Browser Fingerprinting
Modern anti-bot systems (Cloudflare, DataDome, Akamai, PerimeterX) fingerprint browsers
using hundreds of signals:
- Canvas/WebGL rendering — GPU-specific rendering artifacts
- Font enumeration — available system fonts
- AudioContext output — audio stack fingerprinting
- Navigator properties — platform, user agent, hardware concurrency, memory
- Screen dimensions, color depth, timezone offset
- WebRTC leak — reveals local IP even behind VPN

Evasion techniques:
- Selenium Stealth / Puppeteer Stealth — plugins that patch the most detectable
  automation indicators
- Playwright with custom browser profiles — maintain consistent fingerprints across
  sessions
- Residential proxy rotation — distribute requests across genuine residential IPs to
  avoid rate limiting and reputation scoring
- Browserscan/fingerprint.com bypass — continuously monitor fingerprint detection
  services to stay ahead of detection.

### CAPTCHA Solving
CAPTCHA difficulty has escalated from distorted text (reCAPTCHA v1, 2007) to behavioral
analysis (reCAPTCHA v3, 2018) and now to human verification services (hCaptcha, Cloudflare
Turnstile). Current solving approaches:
- **Audio CAPTCHA** — speech-to-text on the audio alternative (requires accessibility
  accommodation)
- **Image classification CAPTCHAs** — computer vision models fine-tuned on common
  CAPTCHA categories (traffic lights, buses, crosswalks)
- **CAPTCHA solving services** — 2Captcha, CapSolver, Anti-Captcha use human workers
  behind APIs ($0.50–$3.00 per 1000 solves)
- **Behavioral bypass** — reCAPTCHA v3 scores user behavior; maintaining human-like
  mouse movements and interaction patterns can improve scores.

### Behavioral Mimicry
To avoid detection, automated collection must replicate human browsing patterns:
- Realistic timing between page loads (not 10ms intervals)
- Scrolling, mouse movement, and click patterns
- Consistent browser profiles (same viewport, same OS, same timezone across sessions)
- Content consumption patterns (reading time proportional to page length)

---

## 5. Network Analysis & Visualization

Once entities are resolved, the next analytical layer is understanding their
relationships.

### Centrality Measures
- **Degree centrality** — raw connection count. Identifies the most connected nodes.
- **Betweenness centrality** — how often a node serves as a bridge between other nodes.
  Identifies gatekeepers and intermediaries.
- **Closeness centrality** — how quickly a node can reach all other nodes. Identifies
  efficient distributors of information/influence.
- **Eigenvector centrality** — weighted by the importance of connected nodes (Google
  PageRank is a variant). Identifies nodes connected to other important nodes.

### Community Detection
- Louvain algorithm — modularity optimization, fast, hierarchical
- Leiden algorithm — improves on Louvain's issues (badly connected communities)
- Label propagation — efficient for very large graphs

### Visualization
- **Force-directed layouts** — Fruchterman-Reingold, ForceAtlas2. Nodes repel; edges
  attract. Produces visually interpretable clusters.
- **Geographic overlay** — map entities and relationships onto geographic coordinates
  when location data is available.
- **Timeline visualization** — temporal network evolution shows how relationships
  form, strengthen, or dissolve over time.
- **Tools** — Gephi (desktop), Cytoscape.js (web), NetworkX (Python), Neo4j (graph
  database with built-in visualization).

---

## 6. Legal & Ethical Boundaries

OSINT operates in a legal gray zone — the data is publicly accessible, but the methods
of collection and the use of the data may be regulated.

### CFAA (Computer Fraud and Abuse Act)
The US CFAA criminalizes "unauthorized access" to computer systems. Key cases:
- **hiQ Labs v. LinkedIn (2022)** — Supreme Court vacated and remanded; the Ninth Circuit
  held that scraping publicly accessible website data does not violate the CFAA.
- **Van Buren v. United States (2021)** — Supreme Court narrowed CFAA interpretation:
  accessing data for an improper purpose is not "unauthorized" if the access was
  otherwise permitted. However, accessing data beyond authorized access limits is
  still a violation.

Practical guidance: scraping public data without authentication is generally legal;
bypassing authentication or access controls (login walls, API key requirements) may
violate CFAA.

### GDPR Implications for OSINT
The EU GDPR applies to processing of personal data of EU residents, regardless of
where the processor is located. OSINT implications:
- **Legitimate interest basis** — OSINT investigations may qualify as legitimate
  interest if they serve a genuine public interest (journalism, fraud detection, security
  research) and the data processing is proportional.
- **Right to information** — GDPR Article 14 requires informing data subjects within
  one month of obtaining their personal data from third-party sources. This is often
  impractical in OSINT and has carve-outs for legitimate purposes where informing
  would be impossible or involve disproportionate effort.
- **Special category data** — racial, political, religious, health, sexual orientation
  data has heightened protection. Many OSINT investigations will inadvertently encounter
  this data.

### Responsible Disclosure
When an OSINT investigation discovers a security vulnerability (e.g., exposed database,
unsecured API), standard responsible disclosure practice applies:
1. Privately notify the affected organization with details.
2. Provide a reasonable timeline for remediation (typically 90 days).
3. Publish findings after remediation or after the timeline expires.

---

## 7. Exocortex Cross-Domain Connections

### Epistemic Integrity ↔ Source Validation
Exocortex's Epistemic Integrity layer audits every claim against an evidence ledger.
OSINT applies the same principle: every finding must be verifiable back to a source
that an independent analyst can access and validate. The structured "proximity,
authority, timeliness, motive" assessment is a manual version of what the EL layer
automates.

### Entropy-as-Signal ↔ Anomaly Detection in OSINT Streams
Entropy-as-Signal monitors attention weight distributions and output token entropy
to detect when the model is uncertain or confabulating. In OSINT, anomalous patterns
in data — sudden changes in corporate registration activity, unusual lobbying filing
frequency, improbable DNS registration timing — serve the same function: statistical
outliers signal that something merits deeper investigation.

### Deterministic Scaffolding ↔ Structured Investigation Methodology
Exocortex wraps LLM reasoning in deterministic scaffolding (structured JSON, BST
classification, supervisor loops) because probabilistic models alone are unreliable.
OSINT's structured methodologies (Bellingcat's multi-source verification, ACH matrices
for hypothesis evaluation, HUMINT source validation checklists) serve the same purpose
for human analysts: scaffolding that catches errors unaided judgment would miss.

### Context Pruner ↔ Source Filtering
Exocortex's Context Pruner removes low-signal tokens from accumulating context to
prevent proactive interference. OSINT analysts face the same problem at different scale:
the volume of publicly available data is infinite, but most of it is noise. Effective
source filtering — discarding low-signal sources before they consume analytical
attention — is the human equivalent of token-level pruning.

### Proactive Interference ↔ CI Dangles
In intelligence operations, a dangle is a controlled piece of disinformation fed to
an adversary to observe their response. Proactive interference in LLMs occurs when
outdated context data contaminates current reasoning. The OSINT parallel is when
an adversary deliberately feeds false information into public channels to mislead
open-source analysts — a technique used by Russian disinformation campaigns (Internet
Research Agency, 2014–present). The countermeasure in both domains is the same: maintain
source time-stamping and decay old data's influence.

### History of Intelligence Operations ↔ OSINT Methodology
The HUMINT-to-OSINT fusion framework (Section 1) demonstrates that structured
tradecraft developed for human source handling over decades of intelligence operations
applies directly to open-source investigation. The principles of source validation,
elicitation, parallel construction, and operational security are domain-agnostic.

---

## Sources Consulted

- OpenPlanter entity_resolution.py (deterministic matching pipeline, Fellegi-Sunter model reference)
- History of Intelligence Operations field report, 2026-05-19 (HUMINT-to-OSINT fusion framework)
- research_topics.promptinclude.md (agent investigation directives)
- DuckDuckGo search: "OSINT framework methodology entity resolution phone email identification 2025-2026"
- GitHub: frangelbarrera/OSINT-BIBLE (comprehensive OSINT guide, 2026)
- ShadowDragon: OSINT Techniques — Expert Tactics for Investigators (2026)
- CybelAngel: OSINT for Security Teams — How to Do It Right in 2026
- BitSight: OSINT Framework — What It Is, How It Works, and the Best Tools (2026)
- Moody's: How to use Open-Source Intelligence (OSINT) for investigations (2025)
- Heuer, Richards J. Jr.: Psychology of Intelligence Analysis (CIA, 1999) — ACH methodology
- hiQ Labs v. LinkedIn (2022), Van Buren v. United States (2021) — CFAA case law
- EU GDPR Article 14 — right to information from third-party data sources
