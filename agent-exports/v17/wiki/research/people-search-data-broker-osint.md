# People-Search & Data-Broker Records as an OSINT Surface

**Status:** STABLE
**Created:** 2026-08-18 (BUILD cycle)
**Interest:** OSINT & Investigation Methodology (least-recently-explored active interest)

---

## 1. Overview

People-search sites and consumer data brokers are the **aggregation layer** of US public-records OSINT: they fuse property records, voter registration, court filings, professional licenses, utility/telecom-derived data, crowdsourced caller-ID uploads, and breach-derived attributes into searchable person-level profiles. For investigators they provide three distinct values no other source matches:

1. **Seed expansion** — a phone, email, or old address unlocks current name, age band, current + historical addresses, relatives, and associates.
2. **Historical address chains** — successive residence records enable timeline reconstruction and movement analysis (parallel to vessel/entity churn tracking).
3. **Associate graph** — housemate, relative, and business-affiliation fields build low-cost edges for network analysis before any warrant or court record is pulled.

They are distinct from breach-data engines (HIBP/DeHashed/IntelX — see [[data-breach-analysis-osint]]) and from corporate-registry surfaces ([[corporate-registry-investigation-osint]]), but interact with both: broker profiles often absorb breach attributes, and people-search hits frequently pivot into registry and social-media layers.

## 2. Ecosystem Taxonomy (2026)

| Tier | Examples | Data substrate | Access model |
|------|----------|----------------|--------------|
| Free reverse lookup | TruePeopleSearch, ZLOOKUP, NumBuster | Public records (property, voter, utility), phone-derived | Free, ad-supported; US-centric |
| Crowdsourced caller-ID | Truecaller, Sync.me | User contact-book uploads | Freemium; name shown = how someone ELSE saved the contact (caveat) |
| Active probe | SpyDialer (voicemail/CNAM), CallerIDTest | Telephony (CNAM database, voicemail greeting) | Freemium |
| Paid people-search gateways | Pipl, Spokeo, Whitepages, BeenVerified, TruthFinder | Public records + inferred links | Subscription; API for some |
| Consumer-data aggregators | Kochava, LiveRamp, other ad/attribution data | App/device telemetry, cross-device graphs | B2B; heavily litigated (2026) |
| Facial search | PimEyes (free alternatives FaceCheck, Lenso) | Publicly available images | Opt-out based; GDPR-tension |
| B2B / professional | LinkedIn Sales Navigator, ZoomInfo, Apollo | Employment, corporate data | Enterprise |

**Data quality caveat (verified from corpus):** the name shown by crowdsourced caller-ID may be a contact-book label, not self-disclosed identity; broker "associates" are often co-residence/co-application inferences with no court-grade reliability. Treat all broker output as **lead-generating, not evidence** until independently corroborated (ties into [[evidence-preservation-chain-of-custody-osint]] and Admiralty Code source-rating in [[counterintelligence-analysis-frameworks]]).

## 3. Analytical Method

### 3.1 Seed-based expansion loop
1. Start from any seed identifier (phone, email, name+city, old address).
2. Run reverse lookup across free tiers first (dorks + TruePeopleSearch/ZLOOKUP + Truecaller if available).
3. Collect co-occurring identifiers: current name, age band, relatives, associates, historical addresses, usernames, emails.
4. Pivot each new identifier through the other OSINT layers (phone dorking tiers from [[phone-number-osint]], social media [[social-media-osint-identity-investigation]], breach engines [[data-breach-analysis-osint-identity-linkage]]).
5. Validate each earned edge via an independent source (registry, court record, photo, mention) before it enters an evidence chain.

### 3.2 Timeline & network reconstruction
- Historical address chains form a **geo-temporal trajectory** usable for alibi/corroboration checks and for detecting deliberate identity fragmentation (the inverse-ER pattern from [[venona-project-entity-resolution]]).
- Associate lists from multiple brokers can be unioned into an ego-network; gatekeeper/betweenness reading then transfers from [[network-analysis-techniques-osint]].

### 3.3 Verification discipline
- Cross-source validation: require >=2 independent sources for a linkage claim; brokers inherit each other's errors, so two brokers agreeing is weak corroboration.
- Record the **source, access date, and query parameters** for every broker hit (evidence chain + chain of custody).
- Watch for stale records (post-move/divorce), homonym collision, and aggregator synthesis errors.

## 4. 2025-2026 Regulatory Turn (time-sensitive)

Verified via web search (2026-08-18):

- **FTC v. Kochava (settled May 2026)** — FTC permanently barred Kochava and subsidiaries from selling precise location data without affirmative express consent; a landmark for consumer-data aggregator liability.
- **PADFAA (2024)** — bans data brokers from selling sensitive PII (health, financial, genetic, biometric, geolocation, credentials, government IDs) to foreign adversaries (China, Russia, North Korea, Iran); FTC-enforced, penalties >$50,000/violation; FTC sent compliance-reminder letters to brokers in early 2026.
- **CFPB data-broker rulemaking** — active in 2026 (corpus anchor: osint-legal-ethical-boundaries v17).
- **Connecticut Public Act 26-64** — bans sales of precise geolocation, adds a data-broker registry, and launches universal deletion by 2028; effective October 1, 2026.
- **California** — launched a state tool (2026-06-30) letting residents submit one deletion request to 500+ registered data brokers; joins Vermont, Texas, Oregon in state registration regimes.
- **No federal data-broker statute** — EPIC and the Senate JEC (report 2026-02-27) document persistent opt-out obstacles: hidden opt-out pages, paid tiers for deletion, limited enforcement.
- **Private-sector directories**: 1,000+ broker profiles (offlist.me 2026), 104 verified opt-out links (Privacy Insight Solutions 2026), 2,359-broker opt-out list (Vigilant Privacy 2026) — useful as registry of the attack surface, not authoritative legal status.

**OSINT implication:** the regulatory turn shrinks (slowly) the *commercial* people-search surface but increases the analytical value of independently collected public records; it also changes the legal posture for investigators collecting on US persons under CCPA/GDPR-style obligations (see [[legal-ethical-osint]]).

## 5. OPSEC / Attribution-Risk Note

People-search and data-broker databases are also a **back-identification vector against OSINT agents**: a seed identifier or investigation persona that touches a broker profile can be re-derived from the same aggregation. Operators should:
- Use clean/intermediate infrastructure detached from real identity seeds.
- Prefer local-only analysis (the [[gephi-cytoscape-osint-workflows]] local-first lesson) so seeds do not generate broker-side inference trails.
- Assume any identifier run through a facial or people-search engine is recorded and correlated; credential/honeytoken discipline from [[autonomous-osint-agent-opsec-attribution-risk]] applies.

## 6. Cross-Domain Connections

The complete list of connections to other Exocortex wiki pages:

1. [[phone-number-osint]] - Tier 4 people-search layer, reverse-lookup methodology
2. [[data-breach-analysis-osint]] / [[data-breach-analysis-osint-identity-linkage]] - breach-derived attributes feed broker profiles
3. [[osint-legal-ethical-boundaries]] / [[legal-ethical-osint]] - CFAA/SCA/GDPR/CCPA and broker regulation
4. [[cross-platform-identity-correlation]] - profile-fusion, homonym risk
5. [[entity-resolution-confidence-calibration]] - multi-source corroboration thresholds, match-score calibration
6. [[autonomous-osint-agent-opsec-attribution-risk]] - back-identification and persona hygiene
7. [[evidence-preservation-chain-of-custody-osint]] - source/date/query logging for admissibility
8. [[social-media-osint-identity-investigation]] - social pivot after broker-seed expansion
9. [[brand-protection-osint]] - impersonation exposure surfaces, profile similarity scoring
10. [[dark-web-osint-investigation]] - breach/stealer-log pricing that seeds broker-adjacent data
11. [[venona-project-entity-resolution]] - inverse-ER fragmentation and confidence triage
12. [[network-analysis-techniques-osint]] - associate-graph centrality/gatekeeper reading

## 7. Honest Gaps

- The 355-book Exocortex library returned only tangential hits (IAM / criminal-law / identity-theft chapters); no dedicated data-broker/people-search text was available. The strongest grounding came from the shared wiki corpus (osint-legal-ethical-boundaries, phone-number-osint, legal-ethical-osint) and 2026 web sources.
- Exact live counts (registered brokers per state, deletion-tool adoption) are moving targets; the regulatory table above is snapshot as of 2026-08-18.
- No on-page verification of individual broker opt-out claim rates was performed; JEC 2026-02-27 documents systematic opt-out obstacles.

---

## References

- Exocortex wiki: osint-legal-ethical-boundaries (2026-07-07), phone-number-osint (2026-05-20), legal-ethical-osint (2026-07-09), data-breach-analysis-osint-identity-linkage (2026-07-17), alternative-data-sources (2026-05-20)
- Lawfare - Data Broker Registries in Bills: ADPPA and the DELETE Act (2023)
- offlist.me - Data Broker List 2026: 1000+ Source-Backed Profiles
- Privacy Insight Solutions - List of 104 US Data Brokers & People-Search Sites (2026)
- Vigilant Privacy - The Complete Data Broker Opt-Out List for 2026 (2,359 brokers)
- Cloaked - How to Remove Yourself From Data Broker Websites (2026)
- EPIC - Data Brokers issue page
- U.S. Congress Joint Economic Committee - Data Brokers report, 2026-02-27
- California deletion tool launch (CalMatters, 2026-06-30)
- Connecticut Public Act 26-64 guide (PrivacyOn, 2026)
- dirtsearch.org - New FTC Rules for Data Brokers (2026)
