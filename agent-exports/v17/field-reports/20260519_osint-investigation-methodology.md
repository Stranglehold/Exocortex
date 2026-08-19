# Field Report: OSINT & Investigation Methodology
**Date:** 2026-05-19
**Interest:** OSINT & Investigation Methodology
**Thread:** Phone number and email address investigation techniques

---

## 1. What I Explored

I researched the current state of OSINT techniques for resolving identities from two primary digital fingerprints: phone numbers and email addresses. The investigation covered:

- **Phone number OSINT**: reverse lookup tools (Truecaller, PhoneInfoga, IntelTechniques), UPI-based identity discovery (India-specific), Google dorking patterns for phone numbers, carrier/VOIP detection, and people search engine aggregation
- **Email OSINT**: reverse email lookup methodology, email header analysis, breach correlation (HaveIBeenPwned/Dehashed), platform-specific dorking (site:github.com, site:linkedin.com), username pivoting, and operational security (OPSEC) considerations
- **Tool ecosystem mapping**: free vs. paid tools, API-based vs. manual workflows, tool chaining patterns
- **Workflow design**: the canonical OSINT investigation pipeline from initial identifier to full identity profile

## 2. What I Found

### Phone Number OSINT Toolkit & Techniques

**Core tools (free tier):**
| Tool | What It Reveals | Access Model |
|------|-----------------|--------------|
| Truecaller | Full name, profile picture, spam score, sometimes email/social links | Web + App, login required |
| PhoneInfoga | Carrier, VOIP detection, Google dork auto-generation, basic geolocation | Open-source CLI/Python |
| Google Dorks (`"+1XXXXXXXXXX" site:facebook.com`) | Social media profiles, pastebin leaks, forum posts | Free, manual |
| WhatsApp (passive) | Profile picture, name, about/bio, business details if business account | App, passive observation |
| UPI apps (PhonePe/Google Pay) | Bank-verified full name, profile picture (India-specific, transaction not required) | App, passive |
| ZLOOKUP / OkCaller | Owner name, basic carrier info | Free web, limited queries |
| Numverify API | Carrier, line type (mobile/landline/VOIP), country, region | API, 250 free calls/month |

**The Workflow Pattern (phone number):**
1. **Validation** — verify the number is valid, identify carrier and line type (Numverify/PhoneInfoga)
2. **Basic ID** — Truecaller for crowdsourced name + photo
3. **Google Dorking** — exact-match search across social platforms, pastebins, XLS/CSV documents
4. **IM App Passive Recon** — WhatsApp, Telegram, Signal for profile data
5. **Pivot to Email** — use found names to discover emails, or check breach databases for phone→email correlations
6. **People Search Engines** — WhitePages, Intelius, Pipl for address and relationship data (mostly US-focused)
7. **Leak/breach correlation** — Dehashed.com, HaveIBeenPwned, Google dorks targeting pastebin and .txt files

### Email OSINT Toolkit & Techniques

**Core tools (free tier):**
| Tool | What It Reveals | Access Model |
|------|-----------------|--------------|
| Epieos | Which platforms the email is registered on (Google, Skype, LinkedIn, etc.) — silent lookup | Free web, CAPTCHA |
| OSINT Industries | Social media profiles linked to email, phone numbers, full name | Free tier available |
| HaveIBeenPwned | Breach databases where the email appears | Free web, API |
| Hunter.io | Email format pattern for domain, associated names | Free, 25 searches/month |
| Google Dorks (`"email@example.com" AND CV`) | Resumes, forum posts, organizational directories | Free, manual |
| RocketReach / Skymem | Data broker aggregations of email→name→social correlations | Free limited previews |

**The Workflow Pattern (email):**
1. **Search Engine Dorking** — `"email@example.com"` AND filetype:pdf OR filetype:xlsx for leaks/staff directories
2. **Domain Pivoting** — `@example.com AND "name"` to find organizational association
3. **Platform Validation** — Epieos to silently check where the email is registered
4. **Breach Assessment** — HaveIBeenPwned / Dehashed for compromised credentials and associated PII
5. **Social Media Discovery** — OSINT Industries or manual search to find linked accounts
6. **Username Pivoting** — extract username pattern from email, search across platforms (Sherlock, WhatsMyName)
7. **Email Header Analysis** — when an actual email is available: SPF/DKIM/DMARC verification, originating IP tracing, X-Originating-IP examination, mail client fingerprinting

### Operational Security (OPSEC) Considerations

A critical finding across all professional OSINT guides: **the investigator's own metadata leaks through tool usage.**

- Free tools log: search queries, IP addresses, device fingerprints, browser metadata, timestamps
- Cross-site tracking can follow an investigator's path across multiple tools
- A law enforcement investigator searching from an agency IP reveals: which agency is investigating, who the target is, and when the investigation is active
- **Mitigations**: dedicated VM or standalone research device, VPN/Tor for sensitive queries, compartmentalized browsers per case, cookie/cache clearing between targets

## 3. What I Think Is Interesting

### The Phone Number Is the Strongest Single Identifier

Phone numbers are unique, persistent, and cross-platform. Unlike emails (which can be created in seconds) or usernames (which change), mobile numbers require SIM registration with government-verified identity in most countries. People reuse the same number across financial services, social media, e-commerce, messaging apps, and job boards. The UPI technique in India — passive lookup via payment apps that reveals bank-verified full names — is a particularly elegant OSINT vector that exploits the frictionless design of payment infrastructure for intelligence gathering.

### The Pivot Is Everything

Identity resolution is not about a single tool — it's about the **pivot chain**: phone → Truecaller name → Google dork for email → Epieos platform validation → LinkedIn profile → employment history → corporate directory → more phone numbers and emails. Each pivot expands the profile. The most skilled OSINT practitioners think in terms of graph traversal, not point queries.

### The Data Broker Ecosystem Is the Hidden Backbone

Many "free" OSINT tools are thin wrappers around data broker aggregation. RocketReach, Skymem, and Intelius sit on massive databases of scraped and purchased personal data. Understanding which broker has what coverage (RocketReach for professional emails, WhitePages for US residential, Truecaller for global crowdsourced phone data) is as important as knowing any specific tool.

### OPSEC Is Not Optional

Every professional guide mentions OPSEC, and for good reason. The tools know who you're investigating. If you're searching from a corporate or government IP, you've just telegraphed your entire investigation. The community norm of using dedicated research environments and VPNs is not paranoia — it's basic tradecraft.

### The Legal Gray Zone

Phone OSINT walks a line. Truecaller data is crowdsourced — when you look up a number, you're benefiting from someone else's contact list. UPI lookups exploit payment infrastructure designed for convenience, not privacy. Reverse email tools enumerate platform registrations without consent. All of this is "public" in some sense but not in a way the average person understands or has consented to. The legal frameworks (CFAA in US, GDPR in EU) are still catching up.

## 4. What I'd Explore Next

1. **Email Header Forensics Deep-Dive**: SPF/DKIM/DMARC analysis, X-Originating-IP extraction, mail client fingerprinting via MIME structure analysis, and temporal correlation across email threads. This connects to the existing promptinclude interest in email header analysis.

2. **Automated Pivot Chain Construction**: Design a tool that given a single identifier (phone or email), automatically executes the pivot chain and returns a structured entity graph. This would map directly onto the Exocortex OpenPlanter entity resolution work.

3. **Legal Boundary Mapping**: A systematic survey of what specific OSINT techniques are legally permissible in US (CFAA), EU (GDPR), India (DPDP Act 2023), and UK (IPA 2016) jurisdictions. The current guidance is piecemeal.

4. **Breach Data Utilization Patterns**: How professional investigators use breach data (Dehashed, IntelX, SnusBase) while managing evidentiary chain of custody and admissibility concerns.

5. **Anti-OSINT Countermeasures**: How sophisticated targets evade phone/email OSINT — burner phones, email aliasing services (SimpleLogin, Firefox Relay), phone number masking, and the cat-and-mouse game between investigators and targets.

## 5. Cross-Domain Connections

### Connection to Entity Resolution (OpenPlanter)

The pivot chain workflow (phone→email→social→employment→address) is entity resolution at the human level. OpenPlanter's scripts (fetch_fec.py, fetch_senate_lobbying.py, entity_resolution.py) are designed to do this at scale across structured datasets. The OSINT techniques documented here represent the manual verification layer that validates automated entity resolution outputs. The same graph traversal logic applies: Person nodes connected by PhoneNumber, Email, Organization, and Address edges.

### Connection to Privacy & Cryptography

Every OSINT technique documented here exploits a privacy failure or information leakage. The metadata in email headers, the crowdsourced contact lists in Truecaller, the platform enumeration in Epieos — these are all vectors that privacy-enhancing technologies (Signal's sealed sender, SimpleLogin aliasing, metadata-resistant protocols) are designed to close. The OSINT investigation methodology and the privacy/cryptography interest are mirror images of each other.

### Connection to History of Intelligence Operations

The pivot chain methodology (start with one identifier, expand outward, build a network graph) is fundamentally the same approach used in HUMINT contact chaining and SIGINT traffic analysis. The tools have changed (Google dorks instead of phone books, Epieos instead of physical surveillance) but the cognitive framework — identify, pivot, expand, verify — is the same tradecraft that intelligence services have practiced for a century.

### Connection to AI Agent Architecture (Exocortex)

The Exocortex idle-time cycles (EXPLORE mode in particular) are essentially an automated OSINT workflow for technical research. The same pattern applies: start with a topic identifier, search diverse sources (arXiv, GitHub, web), pivot between domains, synthesize findings, surface connections. Building an agent that can execute the phone/email OSINT pivot chain autonomously would be a direct application of the Exocortex architecture to the OSINT domain.

---

**Sources consulted:**
- espysys.com — "Ultimate Guide to Phone Number OSINT Tools" (Dec 2023)
- Spyboy.blog — "Phone Number OSINT: The Ultimate Guide" (Jun 2025)
- CavemenTech — "How to Find a Phone Number's Owner" (Jul 2025)
- OSINT Industries — "OSINT Phone Number Investigations" (Nov 2025)
- OSINT Industries — "OSINT Basics: Reverse Email Lookup" (May 2025)
- OSINT Combine — "Investigating Email Addresses with OSINT" (Mar 2025)
- UserSearch Intel Hub — "Reverse Email OSINT: The Complete Guide" (Dec 2025)
- OSINT Industries — "Reverse Email Lookup Ethics Handbook" (referenced, not deep-read)
