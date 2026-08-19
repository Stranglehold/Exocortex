# Field Report: Email Header Analysis & IP Tracing for Identity Investigation
**Date:** 2026-05-26
**Cycle:** EXPLORE
**Topic:** Human investigation — email header analysis and IP tracing

---

## 1. What I Explored

Thread: How email header metadata can be used for OSINT identity investigation, specifically tracing sender IP addresses, verifying sender authenticity via SPF/DKIM/DMARC, and linking email artifacts to real-world identities.

Sources:
- **IP Tracker Online** guide on email header analysis (iptrrackeronline.com, Feb 2026)
- **State of Surveillance** comprehensive email OSINT guide (2025)
- Various OSINT tool aggregator pages (Forensic OSINT, OSINT Cabal, Medium OSINT Team)
- DuckDuckGo search results for email forensics, IP geolocation tools, and breach-checking services

---

## 2. What I Found

### Technical Core: Email Header Anatomy
- **Received headers** are the chain of custody: each MTA prepends a `Received:` line. Read bottom-up to trace chronological path.
- **Authentication-Results:** header from receiving server shows SPF, DKIM, DMARC verdicts.
- **X-Originating-IP:** present in some providers (webmail), but most strip it.
- Critical headers for investigation: `Authentication-Results`, `Received-SPF`, `DKIM-Signature`, `ARC-Authentication-Results` (preserves forwarding chain), `Return-Path`, `Reply-To`.
- **89% of malicious emails pass SPF/DKIM/DMARC** (iptrrackeronline statistic), making header analysis still essential.

### IP Tracing vs. IP Stripping
- Many major providers strip sender client IP from headers after internal routing:
  - Gmail: strips client IP; only shows Google outbound IPs
  - Outlook.com: similar stripping
  - Yahoo: strips client IP
  - **Corporate email via Microsoft 365**: can retain originating client IP in internal Received headers (e.g., `Received: from [192.168.1.105] (73.42.118.203) by ... via Frontend Transport`)
- IP geolocation can identify VPN/proxy use, but attackers increasingly use relays and cloud infrastructure, making simple IP-to-location mapping insufficient.
- The **bottom-most `Received:` header** often shows the originating server, but for webmail providers this is the provider's outbound relay, not the sender's device IP.

### OSINT Tool Landscape for Email Investigation

| Tool | Function | Notes |
|------|----------|-------|
| Have I Been Pwned (HIBP) | Breach detection | API $3.50/mo, web interface free |
| DeHashed | Breach + phone/IP lookup | More flexible than HIBP |
| IntelX (Intelligence X) | Dark web archives, breach data | Free & paid tiers |
| Hunter.io | Professional email lookup by domain | Shows email patterns, verifies |
| Holehe | Checks email on 120+ websites | Social media, dating, forums |
| h8mail | CLI breach hunting tool | Queries Collection1, Breach Compilation |
| WhatBreach | Breach discovery + domain search | Can download breach databases |
| Epieos | Email-to-social linking | API-based |
| Emailrep.io | Email age, phishing association | Quick reputation check |
| Spiderfoot | Automated OSINT multi-module | Excellent for full investigations |
| Maltego | Professional investigation graphs | Visual relationship mapping |
| MXToolbox | Header analysis, spoofing detection | Free tool |
| Forensic OSINT Email Analyzer | Composite risk scoring, typosquatting detection, campaign analysis | Drag & drop .eml support |

### Investigation Workflow (Synthesized from Sources)
1. **Basic search** — Google dork the email in quotes, check LinkedIn, Twitter, GitHub, forums.
2. **Breach database checks** — HIBP, DeHashed, IntelX; reveals services used, password exposure, approximate account creation timeline.
3. **Social media discovery** — Holehe, Epieos, "forgot password" technique on major platforms.
4. **Professional email intel** — Hunter.io for corporate patterns, TheHarvester for CLI scraping.
5. **Email verification** — Confirm address exists before acting (Mailtester, CentralOps).
6. **Header analysis** — If an email is received: extract Received chain, verify authentication, geolocate IPs.

### Real-World Headline
$2.77B lost to business email compromise in 2024 (FBI IC3), median loss $50,000 per incident — nearly all started with email that looked legitimate.

### Emerging Challenge
Modern attackers use VPNs, proxies, spoofed headers, forwarding services, and cloud-based infrastructure, making conventional tracing less effective. A 2026 IJSAT paper ("A Modern Approach to IP and Email Tracing for Cybercrime Investigations") explicitly addresses this.

---

## 3. What I Think Is Interesting

The **asymmetry** between email sender privacy and investigator capability is stark. Webmail providers (Gmail, Yahoo, Outlook) sanitize client IPs for privacy reasons, yet this same sanitization gives cover to malicious actors. Corporate email systems (especially on-prem Exchange and Microsoft 365 with direct client submissions) still leak originating IP in internal Received headers, creating a bifurcated landscape: consumer email is opaque, enterprise email is partially transparent.

The **89% authentication pass rate** for malicious emails is a surprising number. It means SPF/DKIM/DMARC are necessary but insufficient filters — attackers are increasingly compromising legitimate accounts and domains rather than spoofing from scratch. This shifts the investigation burden from authentication verification to behavioral analysis and cross-referencing.

The **tool ecosystem** is mature and surprisingly accessible: many free tiers exist (HIBP web interface, Holehe, Hunter.io 25 searches/month, MXToolbox). The barrier to entry for basic email OSINT is essentially zero. A competent investigator can link an email to social profiles, breach history, and professional footprint in under 15 minutes using free tools.

The **IJsat paper** suggests the problem is shifting from "can we trace this email" to "can we trace this email through obfuscation layers," requiring multi-source correlation rather than single-header analysis.

---

## 4. What I'd Explore Next

- **Deep dive into ARC (Authenticated Received Chain)** — how forwarding lists and relay services preserve authentication across hops, and how ARC headers differ from standard Authentication-Results.
- **h8mail CLI practical testing** — evaluate breach hit rates on sample target emails.
- **Cross-referencing email + phone + breach data** — the multi-attribute linking pipeline: given one email, how reliably can it be connected to phone numbers, usernames, password fragments, and physical addresses?
- **Enterprise email header patterns** — catalog which enterprise email systems retain client IP, which strip, and under what conditions (mobile vs desktop Outlook, webmail vs thick client).
- **VPN/proxy detection through IP metadata** — beyond geolocation: timezone mismatch with Date header, ASN rep (known VPN hosts), hop latency anomalies.

---

## 5. Cross-Domain Connections

- **OSINT Methodology:** Email investigation is the entry vector for broader identity resolution — from email → usernames → social profiles → phone numbers → physical addresses. This maps to the human-investigation OSINT track in Jake's research agenda.

- **Entity Resolution:** Email addresses are natural keys for entity linking across datasets (breach databases, social media, corporate registries). The challenge of resolving "[email protected]" to a real person across heterogeneous sources is structurally identical to the Fellegi-Sunter record linkage problem.

- **Data Breach Analysis:** Breach databases (HIBP, DeHashed) are the intersection point between email investigation and the data-breach-analysis interest track. Understanding breach coverage, recency, and reliability directly impacts investigation effectiveness.

- **Metadata-Resistant Protocols:** The fact that webmail providers strip client IPs is a privacy feature — and the same countermeasure that metadata-resistant communication protocols (Signal, Cwtch) aim to guarantee end-to-end. The tension between privacy and investigability is a through-line.

- **Counterintelligence Analysis Framework:** The multi-source correlation approach to resolving obfuscated email traces maps to ACH (Analysis of Competing Hypotheses) — listing possible explanations for an email's origin and evaluating them against evidence from headers, breach data, and social media.

---

**Conclusion:** Email header analysis remains a critical OSINT skill despite provider IP stripping and attacker obfuscation. The tool ecosystem is mature and free-tier accessible. The investigative frontier is multi-source correlation — combining header artifacts, breach data, social media linking, and behavioral inconsistency analysis to resolve identities in an increasingly obfuscated threat landscape.
