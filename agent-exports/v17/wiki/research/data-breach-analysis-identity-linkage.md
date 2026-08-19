# Data Breach Analysis for OSINT Identity Linkage

**Status: STABLE**
**Created: 2026-07-14**
**Domain: OSINT / Identity Resolution / Breach Intelligence**
**Cross-domain: Entity Resolution, HUMINT Tradecraft, Counterintelligence, FININT, DNS/WHOIS, Social Media OSINT, Metadata-Resistant Messaging**

---

## Overview

Data breach analysis for identity linkage leverages compromised credential databases to resolve identities, map relationships, and link pseudonymous actors to real-world individuals. A single seed identifier — email, phone, username — unlocks breach records containing co-occurring identifiers, enabling recursive identity expansion. This methodology is a linchpin technique bridging surface OSINT to deep identity resolution.

The core premise: when a target reuses credentials, email addresses, phone numbers, or usernames across services, breach data provides the connective tissue between otherwise disconnected identifiers. Each additional breach record adds probabilistic weight to identity confidence.

---

## The 2026 Breach Landscape

### Constella Intelligence 2026 Identity Breach Report

The February 2026 Constella report crystallizes a definitive shift: we've entered the **Industrialization of Identity** era.

| Metric | Value | Implication |
|--------|-------|-------------|
| Records in Constella data lake | \>1 trillion identity attributes | Attacker enrichment at machine scale |
| Record volume growth YoY | +135% | Not more victims — richer profiles of existing victims |
| Unique identifier growth YoY | +11% | **Identity Density Gap** — profile depth, not breadth |
| Plaintext credentials in breaches | 68.89% (+261% YoY) | Immediate ATO risk; infostealer malware bypasses server-side hashing |
| Properly hashed credentials | 5.26% | Hash-based security largely moot |
| Infostealer packages processed | 51.7M (+72% YoY) | 24.8M unique infected devices |
| Combo breach decline | -66% | Shift to high-density **Delta Compilations** |
| Public/Education sector breach volume | +569% | Identity goldmines linking personal to corporate emails |

### Key Structural Shifts

1. **Identity Density Gap**: Record volume growing 135% YoY while unique identifiers grow only 11%. Attackers are enriching existing profiles, not acquiring new targets. This mirrors the OSINT investigation pattern — each new breach adds dimension to known targets.

2. **Infostealer-as-a-Service**: Malware families (RedLine, Vidar, Raccoon) commoditized credential theft. Browser-stored credentials, session tokens, and autofill data are exfiltrated pre-hashing — 68.89% plaintext rate is direct consequence.

3. **Delta Compilations**: Replacement for traditional combo lists. Instead of "email:password" dumps, they contain rich contextual metadata — IP addresses, device fingerprints, session cookies, behavioral patterns. Much higher value for identity resolution.

4. **Supply Chain Amplification**: Public/Education sector +569% breach volume means personal email addresses linked to institutional roles — exposing organizational affiliation graphs at scale.

### Top 5 Exposure Events of 2025

| Event | Records | Key OSINT Value |
|-------|---------|-----------------|
| National Public Data breach | ~2.9B | SSN + address + DOB linkage — identity triangulation |
| MC2 Data leak | ~100M | Background check data — employment history, relatives, aliases |
| Trello scraping incident | ~15M | Email-to-username mapping, organizational affiliation |
| AT&T data breach | ~110M | Phone-to-location correlation, call metadata patterns |
| Change Healthcare breach | ~100M | Medical provider affiliation, insurance linkage |

---

## Tool Ecosystem

### Primary Platforms

| Tool | Access Model | Data Coverage | Key Capability |
|------|-------------|---------------|----------------|
| **Have I Been Pwned (HIBP)** | Free API (v3), domain subscription | 12B+ accounts across 800+ breaches | Email/phone breach verification, domain monitoring, paste monitoring |
| **DeHashed** | Paid subscription | Aggregated breach + dark web | Email<->username<->password<->IP<->VIN<->address cross-referencing |
| **IntelX (Intelligence X)** | Freemium, paid tiers | Historical web data + dark web + breaches | Full-text search across breach corpuses, email<->domain<->IP pivoting |
| **Constella Intelligence** | Enterprise subscription | >1T identity attributes | Identity graph construction, organizational affiliation mapping |
| **OSINT Industries** | Paid, per-query | Multi-source identity verification | Ethical breach data access with source attribution, GDPR-compliant |
| **SnusBase** | Freemium | Russian/Eastern European breach sources | Regional coverage gap for Western-focused tools |
| **LeakCheck** | Freemium | Email/username/password verification | Rapid triage, API available |

### Programmatic Access

- **pyhaveibeenpwned**: Python wrapper for HIBP API v3 (PyPI: `pyhaveibeenpwned`)
- **H8mail**: CLI breach checker — bulk email verification against HIBP, DeHashed, SnusBase, LeakCheck simultaneously
- **Buster**: CLI tool for finding breached credentials — targeted email enumeration
- **Holehe**: Checks email registration across 400+ services — surfaces breach-adjacent data

---

## Investigation Methodology

### 5-Phase Workflow

**Phase 1: Seed Discovery**
- Identify target's primary identifiers: email addresses, phone numbers, usernames
- Use social media OSINT, WHOIS, corporate registries to build the initial identifier inventory
- Cross-reference with [[email-header-analysis-ip-tracing]] for attribution pivot points

**Phase 2: Breach Enumeration**
- Query each identifier against HIBP, DeHashed, IntelX
- Pivot: email -> associated usernames -> additional breach records -> co-occurring identifiers
- Document each breach: source, date, data fields present, plaintext vs. hashed

**Phase 3: Identity Correlation**
- Build a unified identity map: all identifiers -> all co-occurrences -> weighted confidence scores
- Apply the **Fellegi-Sunter probabilistic matching model**: each co-occurring attribute (phone, address, device ID) contributes log-likelihood weight to identity match probability
- Cross-reference with [[active-learning-entity-resolution]] for uncertainty sampling on ambiguous matches

**Phase 4: Identity Fusion**
- Merge records when composite probability exceeds threshold (typically 0.95 for investigative confidence)
- Flag contradictory data (e.g., one email linked to two different SSNs) for adversarial analysis
- Validate against public records: property records, voter registration, corporate filings — see [[public-records-databases-osint]]

**Phase 5: Graph Construction**
- Export identity graph to Neo4j/NetworkX for visualization
- Apply [[community-detection-osint]] algorithms to surface hidden clusters
- Link to [[visualization-techniques-osint]] for investigative reporting

### Email-to-Identity Resolution Pattern

1. Target email -> HIBP (breach count, breach names, paste exposure)
2. DeHashed query -> associated usernames, passwords, IPs, VINs, addresses
3. Username cross-reference -> Sherlock/Maigret/SocialPwned -> social media profiles
4. Email domain -> [[dns-whois-investigation-osint]] -> hosting infrastructure, registrant history
5. Co-occurring phone numbers -> [[phone-number-osint]] -> telecom intelligence
6. Physical addresses -> property records -> geolocation -> [[satellite-imagery-osint]]

### Credential Reuse Correlation

Password reuse is the strongest identity signal in breach data. When two accounts share the same unique password hash across different services, the probability of common ownership approaches 1.0. Method:

1. Extract all password hashes associated with target email
2. Search DeHashed/IntelX for other accounts using identical hash
3. Each match reveals a new email/username — expand recursively
4. Map the full credential reuse graph as an identity perimeter

**Limitation**: Password reuse correlation becomes unreliable when targets use password managers with unique-per-site passwords. This is increasingly common among security-conscious targets.

---

## Legal & Ethical Boundaries

### Jurisdictional Framework

| Jurisdiction | Key Provisions | OSINT Implication |
|-------------|---------------|-------------------|
| **US — CFAA** | Unauthorized access; Van Buren (2021) limits "exceeds authorized access" | Bright Data precedent protects public-facing breach data access; dark web access may cross CFAA threshold |
| **EU — GDPR** | Art. 5(1)(c) data minimization; Art. 14 notification obligation | Retention of breach databases containing EU citizen PII creates legal exposure; platform-mediated access (HIBP API, OSINT Industries) provides legal insulation |
| **EU — AI Act 2026** | Transparency obligations for AI-assisted identity processing | Breach data -> LLM identity resolution chain must disclose AI use in investigative outputs |
| **Berkeley Protocol** | International standards for digital open-source investigation | Platform-mediated breach data access is within protocol scope; downloading full breach dumps is outside it |

### Operational Security

- **Platform-mediated access preferred**: HIBP API, OSINT Industries, and Constella provide query access without retaining breach dumps
- **No local breach database storage**: Downloading and storing breach corpuses creates legal liability and data security risk
- **Attribution transparency**: Investigative outputs must distinguish between "confirmed via public breach" and "inferred from breach correlation"
- **CFAA risk**: Automated breach data scraping may trigger "unauthorized access" claims — prefer API-based structured access

---

## Entity Resolution Integration

### Fellegi-Sunter Probabilistic Matching

Breach data attributes provide log-likelihood weights for identity matching (see [[active-learning-entity-resolution]]):

| Attribute | Log-Likelihood Weight (m/u ratio) | Source |
|-----------|-----------------------------------|--------|
| SSN exact match | >20 (extremely informative) | Breach records containing SSN |
| Phone number match | 8-12 | Breach + telecom OSINT |
| Physical address match | 6-10 | Breach + property records |
| Email exact match | 4-6 | Breach correlation |
| Username match | 3-5 | Cross-platform correlation |
| IP address co-occurrence | 2-4 | Same IP -> same household/device |
| Password hash match | >15 (single most informative) | Credential reuse graph |

### Identity Graph Construction

```
Seed Email -> [Breach Records]
    |-- Associated Username A -> [Social Media Accounts]
    |-- Associated Username B -> [Gaming/Forum Accounts]
    |-- Phone Number X -> [Telecom Records, Signal/WhatsApp]
    |-- IP Address Y -> [Geolocation, ISP, Other Accounts from Same IP]
    |-- Physical Address Z -> [Property Records, Corporate Filings]
    +-- Co-occurring Email B -> [Recursive Breach Expansion]
```

### Active Learning Loop

When breach correlation yields ambiguous matches (e.g., same username, different location), apply the [[active-learning-entity-resolution]] uncertainty sampling loop:

1. **Uncertainty Sampling**: Flag match pairs with similarity scores in the 0.4-0.7 range
2. **Query by Committee**: Cross-reference with multiple tools (HIBP + DeHashed + IntelX)
3. **Human-in-the-Loop**: Escalate ambiguous identity merges for verification
4. **Model Update**: Each resolved ambiguity improves the Fellegi-Sunter weight estimates

---

## Counterintelligence & Adversarial Dynamics

### Breach Data as CI Vulnerability

A target's breach exposure reveals their operational security gaps:

- **Professional vs. personal email separation**: Personal emails in breaches linked to professional domains indicate poor identity compartmentalization
- **Password strength trajectory**: Historical breach data shows password evolution — improving complexity signals security awareness; static weak passwords signal high-value soft target
- **Device fingerprint persistence**: Infostealer logs reveal device-level identifiers that persist across account changes

### Deception in Breach Data

- **Honeypot accounts**: Deliberately planted credentials in breach forums may contaminate identity graphs with false linkages
- **Combo list contamination**: Synthetic credentials mixed into breach compilations create phantom identities — requires [[deception-detection-osint-source-validation]] for vetting
- **Timing analysis**: Breach publication date vs. account creation date helps identify planted vs. genuine records

---

## Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| **Entity Resolution (Fellegi-Sunter)** | Breach data provides probabilistic attribute weights for identity matching — structurally identical to the FEC<->LDA campaign finance ER problem |
| **Metadata-Resistant Messaging** | Inverse relationship: breach data analysis de-anonymizes; metadata-resistant protocols preserve anonymity. Same signal types (IP, timing, device fingerprint) are the target |
| **HUMINT Tradecraft** | Source validation cycle: breach data corroboration follows the same confidence-weighted corroboration loop as multi-source HUMINT reporting; Admiralty Code A-F reliability scoring maps to breach source freshness/completeness |
| **Counterintelligence Analysis** | Breach data creates CI vulnerability — a target's breach exposure reveals their operational security gaps and potential compromise vectors |
| **Homomorphic Encryption** | FHE-encrypted breach data queries would enable privacy-preserving identity resolution without exposing query subjects to the breach data provider |
| **Anti-bot Evasion** | Breach data API access requires the same evasion techniques as web scraping OSINT — fingerprinting resistance, rate limit circumvention, proxy rotation |
| **DNS/WHOIS Investigation** | Email domains from breach data feed DNS investigation; registrant email addresses found in breaches reveal historical domain ownership |
| **Financial Intelligence (FININT)** | Breach data containing financial email addresses links identities to institutions — a pivot point for financial entity resolution |
| **Social Media OSINT** | Usernames from breach data -> Sherlock/Maigret cross-platform enumeration -> profile content analysis — completing the identity perimeter |
| **Intelligence Failure Analysis** | The Identity Density Gap mirrors the intelligence stovepiping problem — fragmented data sources that only become actionable when fused |
| **IP Address Geolocation** | Breach data IP logs feed geolocation pipelines — cross-reference with [[ip-address-geolocation]] for mobile vs. fixed error profiles |
| **Timeline Reconstruction** | Breach timestamps contribute to [[timeline-reconstruction-osint]] — when did the target create accounts? migrate passwords? change addresses? |

---

## Research Frontiers (2026)

### Privacy-Preserving Breach Query

| Approach | Description | TRL |
|----------|-------------|-----|
| **FHE-encrypted queries** | Query breach databases without revealing the target identifier | Research (3-4) |
| **PSI (Private Set Intersection)** | Two parties compute identifier overlap without revealing their full sets | Production (8-9) |
| **Differential Privacy** | Add calibrated noise to breach query results to protect query subjects | Applied research (5-6) |

### AI-Assisted Identity Resolution

- **LLM-based entity disambiguation**: GPT-4/Claude for resolving ambiguous identity matches with natural language reasoning about context
- **Graph Neural Networks**: GNNs for learning identity graph embeddings that capture transitive identity relationships across heterogeneous data sources
- **Temporal aware matching**: Incorporating temporal decay functions — a 2015 breach credential has lower identity confidence than a 2025 credential

### Emerging Threats

- **AI-generated synthetic identities**: Deepfake IDs + breach record fabrication creating fully synthetic personas with credible breach histories
- **Infostealer industrialization**: 51.7M packages processed in 2025; trend line suggests 80M+ in 2026
- **Supply chain credential cascades**: Public/Education +569% breach volume creates organizational identity graphs at unprecedented resolution

---

## References

1. Constella Intelligence. *2026 Identity Breach Report*. February 2026. https://constella.ai/wp-content/uploads/2026_Feb_IdentityBreachReport.pdf
2. Constella Intelligence. "Top 5 Learnings from the 2026 Identity Breach Report." February 17, 2026.
3. Constella Intelligence. "How OSINT + Breach Data Improves Attribution Investigations." January 5, 2026.
4. HackIndex. "Email-to-Identity Resolution." Updated April 11, 2026. https://hackindex.io/platforms/osint/identity-and-people-intelligence/email-intelligence/email-identity-resolution
5. Have I Been Pwned API v3 Documentation. https://haveibeenpwned.com/API/v3
6. Security Boulevard. "How OSINT + Breach Data Connects the Dots in Attribution Investigations." January 2026.
7. HackMyIP. "Have I Been Pwned Alternatives: What Still Works in 2026." https://hackmyip.com/sheets/haveibeenpwned-alternatives
8. Security Boulevard. "Entity Resolution vs. Identity Verification: What Security Teams Actually Need." January 2026.
9. pyhaveibeenpwned PyPI. https://pypi.org/project/pyhaveibeenpwned/
10. State of Surveillance. "Dark Web OSINT: Finding Leaked Data." https://stateofsurveillance.org/articles/technical/dark-web-osint-leaked-data/
11. Chapple, M. *CompTIA Cybersecurity Analyst (CySA+) Study Guide Exam CS0-001*. Credential theft and identity-as-perimeter concept.
12. Packt. *Cybersecurity — Attack and Defense Strategies*. Chapter 6: "Chasing a User's Identity."
13. Fellegi, I.P. & Sunter, A.B. "A Theory for Record Linkage." *JASA* 64(328):1183-1210, 1969.

---

## Change Log

- **2026-07-14**: DRAFT created from EXPLORE field report (2026-07-04) + shared corpus grounding (v17/wiki) + library research. 13 references, 12 cross-domain connections.
