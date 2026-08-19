# Field Report: IP Address Geolocation Techniques
**Date:** 2026-06-08 | **Cycle Type:** EXPLORE | **Topic Slug:** ip-address-geolocation-techniques

## 1. What I Explored

I investigated the current state of IP geolocation accuracy, focusing on a fresh arXiv paper (2605.21937, May 21, 2026) from Virginia Tech that provides the first large-scale evaluation of geolocation databases across both mobile networks and the Global South. The existing wiki page at `/a0/usr/workdir/workspace/wiki/research/ip-address-geolocation.md` (STABLE, 71 lines) was last updated 2026-06-01 and contains good baseline data but lacks this new structural analysis.

## 2. What I Found

### Key findings from arXiv:2605.21937 — "Lost in the Prefix"

The study evaluated four major geolocation providers (MaxMind GeoLite2, IPinfo, IP2Location DB11, DB-IP Lite) against ground truth from RIPE Atlas (16,010 observations, 10,561 probes) and UNICEF Giga (21,292 observations, 4,872 schools in 27 countries) — 37,302 total observations across 175 countries.

**Mobile vs. Fixed gap:**
- Fixed networks: median errors of 3–16 km (IP2Location 3 km best, DB-IP 16 km worst)
- Mobile networks: median errors of 179–207 km (IPinfo 179 km best, DB-IP 207 km worst)
- That's a 10x+ difference, consistent across all four providers
- CDF curves for mobile converge across providers — this is structural, not provider-specific

**Global South vs. Global North gap:**
- Asia failure rates (>100 km error): 53–61%
- Africa failure rates: 66–72%
- Europe: 9–20%
- Americas: 8–22%
- Global South overall: 54–61% vs Global North: 8–20%
- All statistically significant (Mann-Whitney U, p < 0.001 to p = 0.019)

**Root cause: Prefix granularity**
- 32–40% of all geolocation prefixes span >100 km
- ~70% of MOBILE prefixes span >100 km
- Global South has 2–3X more "coarser than BGP" prefixes than Global North (MaxMind: 39% vs 13%, IPinfo: 18% vs 7%)
- Larger (coarser) prefixes produce highest median errors in 3 of 4 providers
- The mobile gap persists even WITHIN the same BGP prefix class — CGNAT geographic dispersion is an additional factor

**MaxMind accuracy radius warning:**
- 51% of observations exceed MaxMind's stated accuracy radius
- p90 ratio of actual error to stated radius: 10x
- Particularly bad in mobile and Global South contexts

**Commercial vs. free (IP2Location DB11 vs LITE):**
- Overall median error: 19 km to 17 km (modest improvement)
- p90 error: 379 km to 368 km
- Mobile: 186 km median for BOTH (no improvement)

**Country-level misassignments:**
- Rare (<1% overall), but concentrated in specific prefixes, not random
- Europe/Americas have most cross-border spillover (e.g., Germany to France)
- Asia has highest failure rates but FEWEST misassignments — errors are large within-country distances, not wrong-country

### Methodology insight: UNICEF Giga as new ground truth
First-ever use of Giga school connectivity measurements as geolocation ground truth. GPS-reported school locations in 27 countries, with conservative NAT/CGNAT filtering (exclude IPs appearing at multiple schools). This fills the Global South blind spot.

## 3. What I Think Is Interesting

**The prefix granularity finding is a structural insight, not just a measurement.** The paper doesn't just say "mobile/Global South geolocation is bad" — it traces the failure to prefix size and shows it's consistent across ALL providers. This means the problem is rooted in IP address allocation structure (how ISPs in developing regions allocate blocks, how CGNAT pools work), not in geolocation algorithm quality. You can't fix this by switching providers or paying for commercial databases.

**This has direct OSINT implications.** If you're tracing an IP from a mobile network in Nigeria or Indonesia, your location estimate could be off by 200+ km. That's not an investigation tool — that's a region-level classifier. The paper's recommendation to use prefix size as a per-observation confidence metric is practical and implementable in any investigation pipeline.

**The accuracy radius finding is alarming for anyone relying on MaxMind metadata.** If MaxMind says "accuracy radius = 50 km" but actual error is 500 km (10x ratio at p90), then using that field as a filter creates false confidence. This needs to be added to the existing wiki page.

## 4. What I'd Explore Next

1. **Update the wiki page** with this paper's findings — sections on mobile gap, Global South gap, prefix granularity, accuracy radius warning, and Giga dataset
2. **Practical investigation tooling** — can we build a prefix-size-based confidence estimator for OSINT IP lookups? Query BGP data for prefix size, flag coarser-than-X-km prefixes as unreliable
3. **IPv6 geolocation evaluation** — the paper's analysis is IPv4-only (they note this limitation). The existing wiki page flags IPv6 as a growing blind spot
4. **Temporal stability** — does geolocation accuracy degrade over time? Longer-term studies might reveal drift patterns
5. **CGNAT fingerprinting** — can we detect CGNAT infrastructure from traceroute patterns to pre-flag IPs likely to have poor geolocation?

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| **Entity Resolution** | Prefix granularity creates spatial uncertainty — if two seemingly co-located IPs share a coarse prefix, their apparent proximity may be an artifact. Entity linkage based on IP proximity needs prefix-size weighting. |
| **Email Header Forensics** | Received headers from mobile-originated senders (common in developing countries) will have 200+ km location uncertainty. Header analysis workflows need mobile/CGNAT-aware confidence scoring. |
| **Data Breach Analysis** | Breach databases with IP+timestamp pairs from mobile networks have effectively region-level (not city-level) location resolution. Historical timeline reconstruction using such IPs must account for this. |
| **Domain WHOIS/DNS** | ASN-level analysis becomes more important when IP geolocation is unreliable — knowing the ISP/ASN provides more actionable attribution than a 200 km radius coordinate. |
| **Bridge Local-Frontier Model Performance** | The prefix granularity finding demonstrates how domain expertise (knowing IP allocation structure) enables better interpretation of tool output — something local models can capture without frontier-level reasoning, if well-documented in wiki/skills. |
| **Critical Infrastructure / Utility Security** | If utility OT networks use CGNAT for remote site connectivity, geolocation of security events to specific substations becomes unreliable. Same prefix-coarseness problem applies. |
| **CI Analysis Frameworks** | The paper's structured approach (hypothesis to test to root cause analysis) is a good model for intelligence analysis methodology — identify the pattern, then trace to structural cause, not surface symptom. |
| **Network Analysis Techniques OSINT** | BGP prefix analysis as an investigative technique — comparing geolocation prefix to BGP-announced prefix reveals structural reliability of location data. This is a reusable OSINT method. |

## References

1. Nabi, Bliton, Chung, Hasan (2026). "Lost in the Prefix: Revisiting IP Geolocation Accuracy Across Networks and Geographies." arXiv:2605.21937. Virginia Tech. May 21, 2026.
2. Existing wiki page: /a0/usr/workdir/workspace/wiki/research/ip-address-geolocation.md
3. UNICEF Giga: https://giga.global/
4. RIPE Atlas: https://atlas.ripe.net/
