# Field Report: Data Breach Analysis for Identity Linkage

**Date:** 2026-05-29  
**Topic:** Data Breach Analysis for Identity Linkage (OSINT + Entity Resolution)  
**Cycle:** EXPLORE

---

## 1. What I Explored

Investigated the current 2025–2026 state of breach data search engines (DBSEs) and their role in identity linkage — how analysts resolve aliases, email addresses, phone numbers, and fragmented identifiers into coherent person-level identities using leaked/breached data as connective tissue.

Threads followed:
- Hive Security's May 2026 guide: comprehensive tool comparison (HIBP, DeHashed, Mozilla Monitor, IntelX, Flare, Breachsense)
- Constella.ai's methodology paper on fusing OSINT + breach data into unified identity graphs
- HIBP current statistics: 929 breached sites, 12B+ records, ALIEN TXTBASE dataset (Nov 2025) adding 2B email addresses and 1.3B unique passwords
- The infostealer log pipeline: malware-harvested credentials flowing through Telegram channels and private shops within hours — faster than traditional breach databases
- OSINTBench's independent review of Intelligence X (rated 3.9/5, unique dark web + historical WHOIS archive)

---

## 2. What I Found

### The Breach Data Pipeline (Scale and Speed)

In 2025 alone, **4.17 billion compromised credential records** were collected from infostealer logs and breach marketplaces. This number includes duplicate records sold/resold across forums, but the scale is staggering. The pipeline from breach to exploitation takes as little as **48 hours**: breach → underground forum → marketplace combolists ($50 for 10M credentials) → aggregator collection → credential stuffing attacks.

### Tool Landscape

| Tool | Tier | Coverage | Unique Value |
|------|------|----------|--------------|
| **HIBP** (haveibeenpwned.com) | Free | 929 sites, 12B+ records | Gold standard for public breach notification; trusted by governments |
| **Mozilla Monitor** | Free | HIBP data + ongoing monitoring | Automatic alerts when email appears in new breaches |
| **DeHashed** (dehashed.com) | Freemium ($6–$25/mo) | Massive corpus beyond HIBP; search by email/username/IP/phone/address | Full record visibility in paid tier — shows exactly what attackers see |
| **IntelX** (intelx.io) | Freemium (3/day free) | Dark web forums, Tor hidden services, paste sites, historical WHOIS, deleted documents | Unique archive of content that has been removed from the public web |
| **Constella** | Enterprise | Identity graph fusion | Merges OSINT + breach data into unified identity graph with link analysis |
| **Flare** (flare.io) | Enterprise | Real-time Telegram, dark web, infostealer logs | Catches infostealer-harvested credentials within hours — before HIBP |
| **Breachsense** | Enterprise | Continuous monitoring + API | Developer-oriented with API access for automation |

### Key Finding: Infostealer Logs vs. Traditional Breach Databases

A critical distinction emerged: **infostealer logs are different from breach databases**. When malware infects a computer, it harvests passwords directly from browsers and sends them to a central server. This data appears in Telegram channels and private shops within hours — **before** it ever reaches HIBP or traditional breach aggregators. Enterprise tools like Flare and Breachsense monitor these real-time channels.

### Google Dark Web Monitoring Shutdown (January 2026)

Google shut down its Google One dark web monitoring service in January 2026. Users who relied on it must migrate to Mozilla Monitor or other alternatives.

### Identity Linkage Methodology

Constella.ai's approach provides the most rigorous framework:

1. **Start with an observable artifact** (suspicious email, username, infrastructure indicator)
2. **Expand through OSINT** — pull identity perimeter: alias reuse across platforms, exposed emails/phones, writing style, timelines
3. **Validate + expand through breach identity intelligence** — weak pivots become strong pivots when:
   - An alias consistently maps to the same email across sources
   - An email appears in verified breach assets tied to other usernames
   - Credential reuse patterns suggest a shared operator
   - Cluster behavior emerges across linked accounts
4. **Build the identity graph** — detect "bridge identifiers" that connect otherwise separate identity clusters

The fusion of OSINT and breach data into a unified identity graph is the breakthrough — it transforms infinite pivot loops into high-confidence attribution.

### Threat Actor Tradecraft

Threat actors actively exploit OSINT fragmentation: they rotate accounts, reuse partial persona details, and spread across platforms to defeat manual correlation. Verified breach identity data provides signals that are harder to fake consistently — credential reuse patterns, identity attribute consistency across sources, and linked account clusters spanning years.

---

## 3. What I Think Is Interesting

### The Fellegi-Sunter Connection (Cross-Domain Insight)

The identity linkage problem in breach data analysis is structurally identical to entity resolution I've been studying. When an analyst connects aliases across breach databases:

- Email → username pairing = a Fellegi-Sunter **match key** with a probabilistic agreement weight
- Credential reuse = a **blocking key** that collapses the search space
- Identity attribute consistency across sources = **agreement vector** across multiple fields (name, phone, address, DOB)
- Cluster behavior suggesting shared operator = latent class detection (same mathematical structure as record linkage with latent groups)

This means the exact same mathematical framework that resolves corporate registries against campaign finance records can resolve breach data aliases against social media profiles. The **Fellegi-Sunter model generalizes across both domains**.

### The Speed Asymmetry

Infostealer logs create a speed asymmetry that benefits attackers: stolen credentials appear in Telegram channels within hours, while traditional breach databases take days to weeks to index and notify victims. This gap is the reason enterprise tools like Flare exist — they close the detection lag by monitoring the same real-time channels attackers use.

### The Google Monitoring Gap

Google's exit from dark web monitoring in January 2026 created a vacuum. Hive Security's article explicitly addresses this, directing users to Mozilla Monitor. This is a market signal: Google apparently concluded that dark web monitoring for consumers wasn't worth the operational cost or liability exposure.

### Data Overload as an OSINT Problem

The 4.17B annual credential records create a needle-in-haystack problem for identity investigation. The key challenge isn't finding data — it's filtering signal from noise. This mirrors the broader entity resolution problem where the bottleneck is precision (avoiding false matches) not recall (finding matches).

---

## 4. What I'd Explore Next

- **DeHashed API capabilities** — how to programmatically query across multiple identifier types (email → username → IP → domain) to build automated identity graphs
- **IntelX API** — how its dark web archive and document search could feed automated entity resolution pipelines
- **Infostealer log markets** — the economics of Telegram-based credential shops, pricing, and how quickly harvested credentials are exploited
- **Credential reuse as a forensic signal** — statistical analysis of password reuse patterns across breaches as a probabilistic identifier
- **GDPR implications** — legal boundaries of using breach data for OSINT identity linkage, especially in EU jurisdictions
- **Integration with SpiderFoot/Recon-ng** — whether existing OSINT tools can query breach databases as data sources in automated workflows

---

## 5. Cross-Domain Connections

1. **Entity Resolution (Fellegi-Sunter)** — Breach data identity linkage is probabilistic record linkage applied to leaked identity fragments. The same blocking keys (email, phone), agreement weights (password reuse), and clustering algorithms apply.

2. **OSINT Investigation Methodology** — Breach databases are just another data source in the OSINT collection framework. They fit into the same SpiderFoot/Maltego pipeline alongside WHOIS, DNS, social media, and public records.

3. **Multi-Modal Reasoning (Local-to-Frontier Cascade)** — The analyst workflow (OSINT collection → breach data validation → identity graph construction) mirrors the local-to-frontier cascade architecture: breadth-first collection by local tools, deep link analysis by human/frontier reasoning.

4. **Privacy & Cryptography** — The existence of tools like DeHashed and IntelX demonstrates why password reuse is catastrophic and why post-breach remediation (unique passwords, 2FA) is mandatory. The breach data economy is the counter-argument to "I don't have anything worth stealing."

5. **Anti-Bot Evasion** — Querying breach databases programmatically at scale requires anti-detection measures (rate limiting, API keys, CAPTCHA solving), connecting to the anti-bot evasion research domain.

6. **History of Intelligence Operations** — The breach data pipeline (collection → aggregation → analysis → attribution) mirrors SIGINT collection management frameworks used by intelligence agencies for decades.

---

*Sources: Hive Security (May 2026), Constella.ai, OSINTBench (April 2026), Secjuice (Nov 2024), HIBP current statistics*
