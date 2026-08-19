# OSINT Tradecraft — Bellingcat Methodology & Investigative Techniques

**Status:** STABLE
**Last Updated:** 2026-06-06
**Interest Area:** OSINT & Investigation Methodology
**Lines:** ~280

## Summary

OSINT (Open Source Intelligence) tradecraft as systematized by Bellingcat — the independent investigative collective founded by Eliot Higgins in 2014 that redefined what open-source investigation can achieve. This page documents the structured methodology, landmark cases, core techniques, tools ecosystem, democratization dynamics, ethical guardrails, and cross-domain connections to the Exocortex architecture.

## The Bellingcat Methodology

Bellingcat's approach rests on seven distinct elements (McGraw, 2026):

1. **Hypothesis-driven investigation.** Start with a falsifiable question: "Where was this Buk missile launcher on July 17, 2014?" The question determines what data to collect.
2. **Maximalist source collection.** Wide nets across satellite imagery, social media, leaked databases, public records, and witness accounts. Volume enables cross-corroboration.
3. **Patient verification.** No single source is trusted uncritically. Geolocation verified via shadow analysis, sun position, terrain matching; timestamps cross-referenced; original artifacts archived.
4. **Transparent methodology.** Published work shows its work — methodology sections detail every step; sources are linked; reasoning is exposed. The reader can audit the investigation.
5. **Collaborative analysis.** Multi-investigator teams reduce confirmation bias and catch missed inferences. The Bellingcat Discord and volunteer community extend this model.
6. **Long timelines.** Major investigations run months to years. The Skripal investigation extended over a year; GRU tracking has continued for nearly a decade.
7. **Use of leaked data, ethically.** Bellingcat works with leaked datasets, flight records, and telecom metadata where legally and ethically sound, with explicit guardrails.

## Landmark Cases

| Case | Year | Key Technique | Impact |
|------|------|--------------|--------|
| **MH17** | 2014– | Satellite imagery + social media archiving + vehicle tracking | Reconstruction of Buk missile launcher path from Kursk to Ukraine; cited by Dutch Joint Investigation Team and courts |
| **Skripal poisoning** | 2018– | Open-source records + leaked databases + travel records | Identified GRU officers Chepiga and Mishkin; confirmed by UK authorities |
| **Navalny poisoning** | 2020 | Flight records + mobile metadata leaks + social media matching | Identified FSB officers involved (lead: Christo Grozev) |
| **GRU Unit 29155** | 2019– | Cross-referencing travel patterns, leaked databases, social media | Identified officers behind destabilization operations across Europe incl. Vrbětice depot explosions |
| **Ukraine war crimes** | 2022– | Geolocation, verification of strike sites, perpetrator identification | Eyes on Russia map, Civilian Harm in Ukraine database; evidence preservation for prosecution |
| **Jan 6 Capitol attack** | 2021 | Photo/video crowd-sourced identification | Collaborative effort with Sedition Hunters; hundreds of rioters identified |

## Core Techniques

### Geolocation & Chronolocation
- **Geolocation:** Matching imagery to known terrain features using Google Earth Pro, OpenStreetMap, PeakVisor, and satellite basemaps (Maxar, Planet). Shadow length/angle analysis (Suncalc) to determine time of day. Vegetation phenology to date imagery.
- **Chronolocation:** Using metadata (EXIF), social media timestamps, weather data, and shadow analysis to place an event on a timeline.

### Social Media Forensics
- Cross-platform identity linkage (username reuse, profile photo reverse search)
- Archiving ephemeral content (deleted posts, stories) using Auto Archiver, Archive.today
- Metadata extraction from images/video (EXIF, codec fingerprints)
- Account authenticity assessment: follower network analysis, creation date, posting cadence

### Cross-Corroboration
- Triangulating a claim across multiple independent sources (imagery + social media + official statements + satellite)
- Building an evidence chain where each link is independently verifiable
- Adversarial mindset: anticipating counter-OSINT efforts (deletion, denial, planted disinformation)

## Tools Ecosystem: Bellingcat Online Investigation Toolkit

The Bellingcat Toolkit (2024, updated 2026) organizes tools into 12 categories:

| Category | Example Tools |
|----------|--------------|
| Maps & Satellites | Google Earth Pro, Sentinel Hub, Planet Explorer |
| Geolocation | OpenStreetMap, Overpass Turbo, Suncalc, Geohints |
| Image/Video | InVID, Google Lens, Forensically |
| Social Media | Twitter/X advanced search, Telegram, CrowdTangle |
| People | Blackbird, Sherlock, WhatsMyName, Skopenow |
| Websites | Wayback Machine, DomainTools Whois, urlscan.io |
| Companies & Finance | OpenCorporates, EDGAR, Companies House |
| Conflict | ACLED, LiveUAMap, Open Source Munitions Portal |
| Transport | Flightradar24, MarineTraffic, ADS-B Exchange |
| Environment & Wildlife | Global Forest Watch, Global Fishing Watch |
| Archiving | Auto Archiver, Archive.today, Distill.io |
| Data Organization & Analysis | Atlos, Blender, Datawrapper, Maltego |

## The OSINT Revolution: Democratization of Intelligence

Luberisse (2025) frames the transformation as three converging developments:

1. **Technological accessibility.** Commercial satellite imagery (Maxar, Planet, BlackSky) provides sub-meter resolution at subscription costs — capability that once required a national space program.
2. **Methodological transparency.** Techniques once guarded within intelligence agencies (shadow analysis, chronolocation, pattern-of-life analysis) are now taught openly via online courses, YouTube tutorials, and dedicated communities like C4ADS.
3. **Analytical tool democratization.** Digital forensics software for image verification, metadata analysis, and dataset processing is available in user-friendly forms.

**Cost asymmetry:** RAND studies find small OSINT cells can generate 70–90% of the analytic value of classified collection at approximately 2% of the cost of a comparable government program.

## Academic Research

- **ORS (OSINT Research Studios):** Mukhopadhyay et al. (2024, arXiv:2401.00928) propose a sociotechnical framework for expert-crowd collaboration in OSINT investigations, using design-based research to enable scalable, ethical OSINT across domains.
- **Russo-Ukrainian OSINT Dataset:** Niu et al. (2024, arXiv:2409.01052) assembled a 2-million-tweet dataset from 1,040 OSINT users tracking the Russo-Ukrainian war, enabling research on OSINT discourse and misinformation tracking.
- **Torrent Metadata OSINT:** Ahsan et al. (2026, arXiv:2601.01492) demonstrate how BitTorrent tracker metadata, enriched with geolocation and anonymization flags, can support scalable investigative profiling.
- **Secure OSINT for Cyberbullying:** Azumah et al. (2023, arXiv:2307.15225) propose an OSINT pipeline using Twitter data for law enforcement dashboards.

## Ethical & Legal Considerations

- **Leaked data ethics:** Bellingcat's policy is case-by-case assessment: verify authenticity, limit scope to investigation-relevant data, protect source identities, operate in jurisdictions where use is lawful.
- **CFAA (Computer Fraud and Abuse Act):** US law that can criminalize certain web scraping behaviors; OSINT practitioners must understand access boundaries.
- **GDPR:** European data protection regulation impacts collection and storage of personal data; legitimate interest balancing test applies.
- **Responsible disclosure:** Findings that identify individuals require editorial judgment — public interest, risk of harm, verification standard.

## Cross-Domain Connections

| Connection | Exocortex Domain | Relationship |
|------------|-----------------|-------------|
| Entity resolution is the core linkage problem in OSINT | [[corporate-registry-analysis-entity-resolution]], [[campaign-finance-entity-resolution]], [[government-contracts-entity-resolution]], [[open-source-entity-resolution-frameworks]], [[active-learning-entity-resolution]] | Bellingcat cross-platform identity linkage is entity resolution in practice; Fellegi-Sunter probabilistic matching is the formal backbone |
| OSINT is the primary data source for influence operations detection | [[influence-operations-detection-countermeasures]] | Bellingcat's counter-disinformation work uses the same OSINT feed as influence operation detection algorithms |
| Counterintelligence frameworks apply to adversarial OSINT | [[counterintelligence-analysis-frameworks]], [[intelligence-failure-analysis]] | ACH (Analysis of Competing Hypotheses) is directly applicable to OSINT hypothesis testing; adversarial denial tactics mirror intelligence failure patterns |
| OSINT investigation is a context management problem | [[context-management-ai-agent-frameworks]], [[context-management-innovations]] | Tracking multiple evidence threads, preserving provenance, avoiding cognitive overload — structurally isomorphic to AI agent context management |
| Collaborative Bellingcat model is a multi-agent orchestration pattern | [[multi-agent-orchestration-patterns]] | Volunteer investigator networks + Discord coordination mirror agent orchestration challenges: routing, state locality, recovery surface |
| OSINT applied to ICS/critical infrastructure attacks | [[ransomware-targeting-ics-ot]], [[scada-ics-security]], [[electric-utility-critical-infrastructure]] | Geolocation and social media analysis track physical infrastructure attacks and perpetrators |
| Social media profile analysis is a core OSINT competency | [[social-media-profile-analysis-osint]] | Four-layer framework (profile attributes, content analysis, network analysis, authenticity assessment) is Bellingcat methodology applied to social media |
| Maritime domain tracking uses OSINT tools | [[maritime-logistics-gray-zone]] | AIS data analysis, vessel tracking via MarineTraffic, satellite imagery of chokepoints — all OSINT techniques |

## Key Insight

Bellingcat demonstrated that an open-source investigation can produce evidence-chain quality sufficient for international criminal proceedings, achieving many of the analytic functions of state intelligence at a fraction of the cost. The structural pattern — wide source collection, patient verification, transparent methodology, collaborative analysis — is a direct template for Exocortex's autonomous investigation architecture. The core lesson: methodological rigor substitutes for institutional resources.

## References

1. McGraw, J.W. (2026). "The Bellingcat Methodology: How Open-Source Journalism Solved Real Cases." Ransomnews.
2. Bellingcat Online Investigation Toolkit. (2024, updated 2026). https://bellingcat.gitbook.io/toolkit
3. Luberisse, J. (2025). "Democratized Intelligence: How Open-Source Intelligence is Reshaping Asymmetric Advantage." Irregular Warfare.
4. Higgins, E. (2021). *We Are Bellingcat: An Intelligence Agency for the People.* Bloomsbury.
5. Mukhopadhyay, A., Venkatagiri, S., & Luther, K. (2024). "OSINT Research Studios: A Flexible Crowdsourcing Framework to Scale Up Open Source Intelligence Investigations." arXiv:2401.00928.
6. Niu, J., Stillman, M., Seeberger, P., & Kruspe, A. (2024). "A dataset of Open Source Intelligence (OSINT) Tweets about the Russo-Ukrainian war." arXiv:2409.01052.
7. Ahsan, M.M. et al. (2026). "Torrent Metadata as a Source for OSINT." arXiv:2601.01492.
8. Azumah, S.W. et al. (2023). "A Secure Open-Source Intelligence Framework For Cyberbullying Investigation." arXiv:2307.15225.
9. C4ADS. Center for Advanced Defense Studies — illicit shipping, sanctions evasion, proliferation network methodologies.
10. Bellingcat. "Guides & How-Tos." https://www.bellingcat.com/category/resources/how-tos/
