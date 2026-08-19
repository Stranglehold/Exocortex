# Brand Protection OSINT

**Status:** STABLE
**Created:** 2026-08-07 (BUILD cycle)
**Topic slug:** brand-protection-osint

## Summary
Brand protection OSINT is the practice of monitoring the open internet for misuse of a company's name, logos, domains, and apps, then driving takedowns. It is, structurally, continuous entity resolution against a known legal-identity seed set: every lookalike domain, fake social profile, spoofed app, and counterfeit listing is an unverified entity that must be matched, scored, and escalated. The methodology generalizes to any named identity whose owner wants to distinguish genuine instances from impersonations at internet scale.

## Why it matters
- Brand abuse is a leading indicator: lookalike-domain registration and credential exposure typically precede phishing campaigns, account takeover, and executive fraud.
- Single compromised brand surface can cascade into reputational damage, customer loss, and supply-chain impersonation (fake vendors, fake support, fake invoices).
- The 2026 tooling landscape is mature: 37+ commercial solutions tracked by CybersecTools; Bitsight reports ~85% takedown rate for impersonation-monitoring platforms.

## Threat surface (four exposure surfaces, 2026)
1. **Lookalike/typosquatted domains** — homoglyph, missing-character, and novel-TLD variants of owned domains.
2. **Phishing pages & credential harvesting** — brand-fronted login pages, often on lookalike domains or free-hosting subdomains.
3. **Social media & app impersonation** — fake executive profiles, support accounts, and spoofed mobile apps in official stores.
4. **Counterfeit & gray-market listings** — unauthorized sellers on Amazon, eBay, TikTok Shop, and gray-market distributors.

Dark-web monitoring adds a fifth latent surface: leaked credentials for brand domains (stealer logs), executive credentials, and marketplace mentions that precede attacks.

## Core monitoring pipeline
### 1. Domain monitoring (typosquatting)
- Generate variant sets from the owned domain: character omission, substitution, transposition, homoglyph (Unicode), and new-TLD additions.
- Open-source detection: **DNSrazzle** (free CLI OSINT typosquatting tool) compares candidate domains against the original; commercial platforms (Bolster, MarqVision, WhiteIntel) automate lookalike discovery and blocklist watch.
- Verify with DNS/WHOIS pivots already covered in [[dns-whois-investigation-osint]]: registration dates near campaign windows, privacy-guard WHOIS, name-server reuse, certificate-transparency subdomain discovery.

### 2. Social & app impersonation
- Profile-similarity scoring: name, avatar, bio, follower ratios, and posting velocity vs. the genuine account (ties to [[social-media-profile-analysis-osint]]).
- Executive/VIP monitoring: track name variants and handle prefixes/suffixes.
- App-store monitoring: developer-name lookalikes, icon reuse, and permission red-flags.

### 3. Marketplace & counterfeit detection
- Continuous scrape + image similarity against registered brand assets; listing text matching for trademark phrases.
- Distinguish counterfeit from gray market: gray market is authentic but unauthorized; takedown authority differs (trademark vs. distribution contract).
- E-commerce takedown workflow: notice-and-takedown under platform policies, Amazon Brand Registry, eBay VeRO, marketplace-specific IP portals.

### 4. Dark web & credential exposure
- Stealer-log monitoring for *@brand-domain* addresses; leaked executive credentials.
- Threat actor attribution via the attribution stack from corpus: Admiralty A-F source scoring, Fellegi-Sunter entity matching for actor personas.

## Threat intelligence integration
- Brand-protection feeds identify the *earliest* misuse event (domain registration, credential exposure) — a leading indicator for phishing campaign and account-takeover waves.
- Feeds integrate with OSINT investigations by expanding suspicious-entity candidate sets and validating takedown claims (source reliability scoring per [[counterintelligence-analysis-frameworks]]).
- Constella adds brand protection on top of identity-continuity data — the same bridge-identifier logic as breach analysis, now applied to brand assets.

## Brand monitoring as alternative data
- Typosquat traffic volumes and new-lookalike registration frequency are forward signals for phishing campaigns targeting a firm and, in aggregate, for industry-wide abuse waves.
- Web-traffic drop on the canonical brand domain combined with a rise on lookalike domains is an early-warning isomorphic to the traffic-signal methods in [[web-traffic-analytics-alternative-data]].
- Executive impersonation volume tracks social-engineering campaign intensity, useful for sector-level threat assessments.

## Legal & takedown layers
- Trademark law (Lanham Act in the US) provides the legal hook for domain and marketplace takedowns; DMCA applies to content theft.
- Platform-specific IP regimes dominate practical takedowns: Amazon Brand Registry, eBay VeRO, Meta IP reporting, Google Safe Browsing/legal removal.
- EU DSA notice-and-action obligations and app-store enforcement create parallel channels.
- Evidence preservation for takedowns mirrors evidence standards in [[evidence-preservation-chain-of-custody-osint]]: screenshot, URL, WHOIS snapshot, hashed artifacts.

## Cross-domain connections
- [[entity-resolution-algorithms-2026]] — matching candidate brands against a known seed; Fellegi-Sunter m/u probability mapping.
- [[dns-whois-investigation-osint]] — domain pivots, WHOIS ownership, CT log discovery.
- [[social-media-profile-analysis-osint]] — fake profile detection, sockpuppet analysis.
- [[deepfake-synthetic-media-verification-osint]] — synthetic avatar/voice impersonation for executive-brand fraud.
- [[web-traffic-analytics-alternative-data]] — brand-drop/typosquat traffic as an alternative-data signal.
- [[honeypot-operations-digital-deception-osint-attribution]] — canary traps/watermarks to identify who scrapes brand content.
- [[data-breach-analysis-osint-identity-linkage]] — bridge identifiers for threat-actor persona resolution.
- [[counterintelligence-analysis-frameworks]] — deception detection and source reliability scoring for takedown claims.
- [[evidence-preservation-chain-of-custody-osint]] — preserving takedown evidence for legal escalation.
- [[real-time-osint-monitoring-alerting]] — scheduling, alerting, and feed-fitting for continuous brand monitoring.

## References
1. CybersecTools — Brand Protection Tools 2026 comparison (37 solutions).
2. Constella Intelligence — Brand Protection platform capabilities.
3. ThreatFusionAI — Brand protection in cyber threat intelligence.
4. Bitsight — Best Brand Protection & Impersonation Monitoring Platforms 2026 (~85% takedown rate claim).
5. Bolster — OSINT Typosquatting Comparison (DNSrazzle).
6. WhiteIntel — Brand Protection in 2026: dark web monitoring, lookalike domains, VIP monitoring.
7. Scrapewise — Counterfeit Detection Tools 2026 (counterfeit vs gray market).
8. MarqVision — 10 Best Brand Protection Tools 2026.
9. Breachsense — Best Typosquatting Checkers (Dec 2025).

## Honest gaps
- search_memory/search_library (exocortex_memory tools) are not exposed in this environment; grounding used memory_load + wiki greps + web search only.
- Takedown-rate and market-size numbers are vendor claims, not independently verified.
