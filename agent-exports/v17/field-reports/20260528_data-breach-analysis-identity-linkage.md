# Field Report: Data Breach Analysis for Identity Linkage — 2026 Tooling & Methodology

**Date:** 2026-05-28
**Cycle Type:** EXPLORE
**Topic:** OSINT & Investigation Methodology
**Sub-topic:** Data Breach Analysis as Identity Resolution Substrate

---

## 1. What I Explored

I researched the 2025–2026 state of data breach analysis tools and methodology, specifically how breached credential datasets and stealer logs are used to link pseudonymous identities, resolve entities across platforms, and reconstruct attacker timelines. The thread started with the existing Exocortex wiki page on Data Breach Analysis (STABLE, 181+ lines covering HIBP API v3, DeHashed, IntelX, legal frameworks) and pushed into: newer breach search engines entering the market, the Substack breach as a canonical case study in OSINT timeline reconstruction, and the integration of stealer log data into mainstream breach notification platforms.

## 2. What I Found

### Key Facts and Data Points

**HIBP API v3 — Stealer Log Integration (2025)**: Troy Hunt integrated infostealer log data into HIBP in January 2025 as a Pro-tier feature. Three new endpoints:
- `/stealerLogsByEmail/{email}` — domains where a user\'s credentials were captured by info stealers
- `/stealerLogsByWebsiteDomain/{domain}` — email addresses captured for a specific website
- `/stealerLogsByEmailDomain/{domain}` — aliases and associated website domains for an email domain

This matters for identity linkage because stealer logs contain real-time credential captures (not just historical breaches), including registration IPs, browser fingerprints, and session tokens — far richer identity signals than hashed passwords alone.

**Breach Search Engine Ecosystem (2026):**

| Platform | Differentiator | Key Identity Linkage Capability |
|----------|---------------|-------------------------------|
| **HIBP** | Verified/curated breach index (994+ breaches, 11B+ accounts) | k-anonymity email search, stealer logs (Pro), breach timeline API |
| **DeHashed** | Multi-field search (email, username, phone, IP, address, VIN) | Cross-breach correlation by non-email identifiers — powerful for entity resolution across pseudonymous accounts |
| **IntelX** | Cross-source identity mapping (Tor, I2P, Telegram, dark web) | One primary query returns linked emails, domains, IPs, Bitcoin addresses; automated pivot capability |
| **Snusbase** | Longest-standing (est. 2016), trusted by law enforcement | Breadth of historical breach coverage; persistence of data after breaches are scrubbed elsewhere |
| **OSINTLeak** | Stealer log specialization | Real-time credential capture search; complements HIBP\'s stealer log integration |
| **LeakCheck** | API-first design, Discord bot integration | Programmatic identity linkage for automated pipelines |
| **Dead Eye** | Cross-source aggregation (breaches, emails, phones, social media) | Integrated search across billions of records from multiple breach databases |
| **TraceX** | Open-source CLI leveraging Snusbase API | Auditable, scriptable breach search for automation workflows |

**Substack Breach Case Study (October 2025 — February 2026)**: The Substack breach exposed 700,000 records (email + phone + internal metadata). Key OSINT lessons:
- **Detection gap**: Forum posts appeared January 2026 — three months before official February 3 disclosure. OSINT monitoring provided earlier detection than internal security tools.
- **Email + phone combination risk**: CEO disclosure emphasized no passwords/credit cards were taken, but the email+phone combination enables SIM swapping and targeted phishing — a threat vector that HIBP and DeHashed cross-referencing can model.
- **Threat actor TTPs**: API exploitation (not SQL injection); maintained persistent access October–January; posted data samples to BreachForums successors before full dataset sale. Attribution via username cross-referencing (Reddit, Twitter), language analysis, and historical breach pattern matching.
- **Timeline reconstruction methodology**: Google Dorking (temporal `after:`/`before:` operators), Internet Archive Wayback Machine comparison of security pages pre/post breach, Twitter advanced search for user spam complaints (November 2025 correlated with October breach date), Reddit timestamp-filtered search for community discussion history.

**Breach Forum Monitoring Methodology:**
- Primary sources: BreachForums successors, Exploit.in (Russian-language, English section), Nulled.to, Telegram channels
- Validation approach: sample data authenticity checks (email format matching, phone number plausibility), multi-source corroboration, threat actor history analysis
- Researcher compartmentalization: separate emails, VPN connections, isolated browser environments for forum access — no participation, purchase, or data download

**Ethical/Legal Framework** (consistent across sources):
- Permitted: viewing publicly indexed data, using search engines on indexed content, reading breach notifications, analyzing publicly posted samples, archiving public pages
- Prohibited: unauthorized system access, downloading/distributing stolen databases, using breached credentials for access testing, data trading, doxing
- Responsible disclosure: verify thoroughly, notify company privately (7–30 day window), document all communications, disclose responsibly without enabling exploitation

## 3. What I Think Is Interesting

**The shift from "breach notification" to "credential intelligence continuum."** The 2026 breach analysis landscape has moved beyond "has my email been pwned?" to a continuous intelligence model: stealer logs provide real-time credential capture, IntelX maps identity across dark web sources, and DeHashed/OSINTLeak aggregate across data types. A single phone number can now pivot across 5+ breach databases, revealing username patterns, associated emails, registration IPs, and geographic anchors.

**Stealer logs as the highest-fidelity identity signal.** Unlike historical breach dumps (which may be years old), stealer logs represent *active* credential captures with browser fingerprint data, session tokens, and timestamps — providing temporal precision for identity linkage that static breach data can\'t match. HIBP\'s 2025 stealer log integration is a watershed moment for mainstream accessibility of this data.

**The Substack case validates a counterintuitive claim:** the combination of email + phone number (without passwords) is *more dangerous* for identity resolution than passwords alone. Email+phone enables (1) SIM swapping to bypass 2FA, (2) cross-platform account discovery via phone-sync features, (3) targeted phishing with both channels. Breach data analysis that prioritizes password exposure over PII exposure is a category error — PII is the persistence substrate for long-term identity attacks.

**The breach forum early-warning system is an underappreciated OSINT capability.** Forum monitoring provided 3 months of advance warning in the Substack case. This isn\'t just threat intelligence — it\'s an investigative timeline advantage. Organizations that monitor these forums can detect breaches before official disclosure, notify users earlier, and preserve evidence that disappears after public disclosure triggers scrubbing.

## 4. What I\'d Explore Next

1. **Automated breach correlation pipelines**: Build a Python script that takes an email address, queries HIBP (k-anonymity), DeHashed, and open breach datasets, then outputs an identity graph with linked usernames, phone numbers, and registration IPs. Existing wiki cross-references (Fellegi-Sunter ER models) could be applied to breach record matching.

2. **Stealer log analysis methodology**: Deep-dive into what stealer logs actually contain (browser fingerprints, session tokens, clipboard data, cryptocurrency wallet addresses) and how to use them in OSINT investigations — beyond credential checking into behavioral profiling.

3. **Breach forum linguistic forensics**: Systematic analysis of threat actor communication patterns (grammar, idioms, time zone indicators, technical vocabulary) for attribution — building on the language analysis mentioned in the Substack case study.

4. **Cross-referencing breach data with phone OSINT and email forensics**: The existing Exocortex wiki pages for phone-number-osint, email-forensics-header-analysis, and data-breach-analysis-identity-linkage all cross-reference each other. A unified investigation workflow that chains all three would be a natural next step.

## 5. Cross-Domain Connections

**Breach data ↔ Entity resolution (Palantir ontology)**: Breach datasets are precisely the kind of heterogeneous identity source that entity resolution systems are designed to resolve. A breached email address links to a breached username links to a phone number — each from different breach sources, each with different reliability signals. This is identical to the multi-source corporate registry + campaign finance + lobbying disclosure matching problem in the Data Aggregation & Entity Resolution interest. The same Fellegi-Sunter probabilistic matching models apply; the same truth-fusion challenges arise (which breach source is more authoritative when they conflict?).

**Breach timeline reconstruction ↔ CI analysis of competing hypotheses**: The Substack breach investigation\'s timeline reconstruction methodology (Google Dorking, Wayback Machine comparisons, forum monitoring, social media signal analysis) structurally mirrors counterintelligence ACH — gather evidence from multiple independent sources, evaluate each source\'s reliability, identify inconsistencies, and weight competing explanations. The OSINT investigator and the CI analyst are doing the same cognitive work on different data substrates.

**HIBP k-anonymity model ↔ Privacy-preserving computation**: HIBP\'s SHA-1 prefix range query (5-char prefix for passwords, 6-char for emails) is a real-world deployment of k-anonymity — proving that privacy-preserving data querying can work at scale (11B+ accounts) without exposing the full dataset. This connects directly to the privacy-cryptography interest and differential privacy techniques explored in previous field reports.
