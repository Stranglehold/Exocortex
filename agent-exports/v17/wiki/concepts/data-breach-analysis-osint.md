# Data Breach Analysis for OSINT Identity Linkage

**Status: STABLE**
**Created: 2026-07-06**
**Source: Field Report 2026-07-04 + Deepening**

## Overview

Data breach intelligence transforms OSINT identity investigation by moving from publicly declared identifiers to **verified identity linkages** through credential reuse patterns, breach correlation, and identity graph construction. Breach data provides a high-signal substrate for entity resolution: real-world identifiers (email addresses, phone numbers, usernames, passwords, IP addresses) linked through actual usage by the same person, rather than inferred relationships.

This page describes the 2026 breach analysis landscape, OSINT integration methodology, and cross-domain connections to the broader Exocortex wiki.

---

## The 2026 Breach Landscape

The Constella 2026 Identity Breach Report crystallizes a definitive shift: the **Industrialization of Identity**.

| Metric | Value | Implication |
|--------|-------|-------------|
| Records in Constella data lake | >1 trillion identity attributes | Attacker enrichment at machine scale |
| Record volume growth YoY | +135% | Profile depth, not victim count, is the growth vector |
| Unique identifier growth YoY | +11% | "Identity Density Gap" — richer profiles of existing victims |
| Plaintext credentials in breaches | 68.89% (+261% YoY) | Browser-scraping infostealers bypass server-side hashing |
| Properly hashed credentials | 5.26% | Hash-based security is effectively moot |
| Infostealer packages processed | 51.7M (+72% YoY) | 24.8M unique infected devices |
| Combo breach decline | -66% | Shift to high-density "Delta Compilations" |
| Public/Education sector breach volume | +569% | Identity goldmines linking personal to corporate emails |

**Key Insight:** The identity density gap means attackers are not widening their victim pool — they are deepening the profiles they already own, building richer identity graphs for targeted attacks.

---

## OSINT Integration: Methodology

### Phase 1: Subject Enumeration

Start with known identifiers from social media, corporate registries, or other OSINT sources. Extract:
- Email addresses (personal, corporate, throwaway)
- Phone numbers
- Usernames (Sherlock/Maigret cross-platform enumeration)
- Associated domains

### Phase 2: Breach Query & Correlation

Query breach databases (HIBP, DeHashed, IntelX, Constella) for each identifier. Methodological stages:

| Stage | Action | Tools |
|-------|--------|-------|
| **Breach discovery** | Query by email/username/domain | HIBP API, DeHashed, IntelX, Constella |
| **Credential reuse analysis** | Cross-reference passwords across breaches to confirm common identity | Custom scripts, breach analytics platforms |
| **Secondary identifier extraction** | Extract linked phone numbers, IP addresses, physical addresses from breach records | Python pandas, jq |
| **Identity fusion** | Construct identity graph linking all identifiers | Neo4j, NetworkX |
| **Confidence scoring** | Apply Fellegi-Sunter probabilistic matching to breach-derived attributes | Splink, custom Python |

### Phase 3: Confirmation & Extension

Validate breach-derived associations through:
- **Reverse lookup** on newly discovered identifiers (phone -> name, address -> property records)
- **Cross-reference with non-breach OSINT** (social media, corporate filings, DNS/WHOIS)
- **Temporal correlation** — do breach timestamps align with known activity periods?

### Phase 4: Negative-space analysis

The **absence** of a subject in expected breaches is itself a signal. A target with no breach presence may indicate:
- Sophisticated operational security (isolated identities, no reuse)
- Use of dedicated breach-monitoring services
- Freshly created identity (burner email/phone)

---

## Tool Ecosystem (2026)

| Tool | Type | Key Capability | Access |
|------|------|----------------|--------|
| **Have I Been Pwned** | Free/Paid API | Email/domain breach search; 12B+ records; API v3 with stealth mode | API key required for full access |
| **DeHashed** | Paid | Email, username, IP, phone, VIN, address search; API and web UI | Subscription ($) |
| **IntelX** | Paid | Dark web, data leaks, breach databases; advanced boolean search | Subscription ($$$) |
| **Constella Intelligence** | Paid | Identity graph across 1T+ attributes; "Dragonfly" graph visualization | Enterprise ($$$$) |
| **SpyCloud** | Paid | Infostealer malware session capture; compromised device tracking | Enterprise ($$$$) |
| **LeakCheck** | Freemium | Email/username/domain breach check; API available | Limited free tier |
| **SnusBase** | Free | Email/username/domain breach check; Tor-friendly | Free, anonymous access |
| **H8mail** | Open source | Email breach checker from command line; multiple API backends | GitHub |
| **pyhaveibeenpwned** | Open source | Python wrapper for HIBP API v3 | PyPI |

---

## Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| **Entity Resolution (Fellegi-Sunter)** | Breach data provides probabilistic attribute weights for identity matching — structurally identical to the FEC<->LDA campaign finance ER problem |
| **Metadata-Resistant Messaging** | Inverse relationship: breach data analysis de-anonymizes; metadata-resistant protocols (Signal, Briar, Cwtch, SimpleX) preserve anonymity. The same signal types (IP, timing, device fingerprint) are the target |
| **HUMINT Tradecraft** | Source validation cycle: breach data corroboration follows the same confidence-weighted corroboration loop as multi-source HUMINT reporting; Admiralty Code A-F reliability scoring maps directly to breach source freshness/completeness |
| **Counterintelligence Analysis** | Breach data creates CI vulnerability — a target's breach exposure reveals their operational security gaps and potential compromise vectors. Mirror-imaging: an analyst's own breach hygiene is part of the CI threat surface |
| **Homomorphic Encryption** | FHE-encrypted breach data queries would enable privacy-preserving identity resolution without exposing query subjects to the breach data provider |
| **DNS/WHOIS Investigation** | Email domains from breach data feed DNS investigation; registrant email addresses found in breaches reveal historical domain ownership |
| **Financial Intelligence (FININT)** | Breach data containing financial email addresses (e.g., @bloomberg.net, @gs.com) links identities to institutions — a pivot point for financial entity resolution |
| **Social Media Profile Analysis** | Usernames from breach data -> Sherlock/Maigret cross-platform enumeration -> profile content analysis — completing the identity perimeter |
| **Intelligence Failure Analysis** | The Identity Density Gap mirrors the intelligence stovepiping problem — fragmented data sources that only become actionable when fused |
| **Phone Number Investigation** | Phone numbers recovered from breach data provide high-confidence pivots to carrier lookups, registration records, and messaging app correlation (Signal, WhatsApp, Telegram) |

---

## Operational Security & Legal Boundaries

- **Querying breach data is legal** in most jurisdictions when using licensed services (HIBP, DeHashed, etc.) — the data is already public/available
- **CFAA boundaries:** Do not access or download full breach databases directly; use authorized APIs
- **GDPR considerations:** Querying European subjects' breach data for OSINT purposes falls under legitimate interest provisions, but consent and proportionality still apply
- **OPSEC:** Your queries to breach services are logged; use VPNs, burner accounts, or anonymous access (SnusBase, Tor) when necessary
- **Attribution:** Breach data alone is not conclusive — it requires corroboration through additional sources (principle of multi-source confirmation)

---

## Deepening: Methodological Extensions

### Graph-Based Identity Resolution

Breach data entities (email->username->phone->IP->physical address) form a natural graph. Community detection algorithms (Louvain, label propagation) can cluster identifiers into identity groups without supervised labels. The graph approach is detailed in [[network-analysis-techniques-osint]].

### Confidence Scoring Matrix

| Evidence Type | Weight | Affinity with Subject |
|--------------|--------|-----------------------|
| Email + password reused across breaches | High | High — same person reusing credentials |
| Email + IP address in same breach record | Medium-High | Medium — could be shared device |
| Username match + same breach site | Medium | Medium — username collision possible |
| Phone number + email in same breach | High | High — phone-email binding is rare |
| Physical address + email | High | Very High — confirms physical identity |


### Password Reuse Patterns (arXiv:1706.01939)

Wang et al. (2017) analyzed 28.8M users and 61.5M passwords across 107 services, finding **38% exact password reuse** and **20% modified versions** of existing passwords. The password modification patterns were highly consistent across demographics, enabling a training-based guessing algorithm that cracked 16M+ password pairs within 10 attempts (~30% of modified passwords and all reused). This empirical data underpins breach analysis confidence: a password reused across multiple breaches is a near-certain identity link, while a modified password still carries strong probabilistic weight given the high predictability of modification patterns.

### ML-Driven Password Guessability (arXiv:2311.13422)

Alkinoon et al. (2024) reviewed password guessers and attack vectors, noting that ML techniques can learn personal information patterns to predict password choices with high accuracy. This reinforces the breach data value: passwords are not random — they carry personal information (names, dates, patterns) that can be extracted and mapped to identity attributes, strengthening the entity resolution signal from breach data.

### Temporal Decay

Breach age degrades relevance. A credential found in a 2018 breach may no longer be in use. Apply temporal decay weighting:

<latex>w(t) = w_0 \cdot e^{-\lambda (t_{now} - t_{breach})}</latex>

where <latex>\lambda</latex> is the decay constant (~0.5/year for credentials, ~0.2/year for physical addresses).

### Negative-Space Quantification

Define a "Breach Expectation Score" — for a given identity profile (age of first known activity, number of online accounts, digital footprint size), calculate the expected number of breach appearances. A null result when expectation is >0 is a strong OPSEC signal.

---

## References

1. Constella Intelligence. *2026 Identity Breach Report*. February 2026.
2. Constella Intelligence. "Top 5 Learnings from the 2026 Identity Breach Report." February 17, 2026.
3. Constella Intelligence. "How OSINT + Breach Data Improves Attribution Investigations." January 5, 2026.
4. HackIndex. "Email-to-Identity Resolution." Updated April 11, 2026.
5. Have I Been Pwned API v3 Documentation.
6. Security Boulevard. "How OSINT + Breach Data Connects the Dots in Attribution Investigations." January 2026.
7. HackMyIP. "Have I Been Pwned Alternatives: What Still Works in 2026."
8. Security Boulevard. "Entity Resolution vs. Identity Verification: What Security Teams Actually Need." January 2026.
9. pyhaveibeenpwned PyPI.
10. State of Surveillance. "Dark Web OSINT: Finding Leaked Data."

---

*Page built from field report 2026-07-04. Deepened 2026-07-06 with graph methodology, temporal decay modeling, confidence scoring matrix, and expanded cross-domain connections.*
