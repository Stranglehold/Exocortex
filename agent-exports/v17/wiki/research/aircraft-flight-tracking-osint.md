# Aircraft & Flight Tracking for OSINT Investigation

**Status: STABLE**
**Created:** 2026-07-11
**Last Deepened:** 2026-07-11
**Parent Interest:** OSINT & Investigation Methodology
**Topic:** OSINT & Investigation Methodology

## Overview

Aircraft and flight tracking is a powerful OSINT technique that leverages publicly available Automatic Dependent Surveillance-Broadcast (ADS-B) data, Mode S transponder signals, flight plan databases, aircraft registry records, and satellite imagery to identify aircraft movements, ownership, and patterns of activity. With approximately 20,000+ aircraft broadcasting ADS-B data at any given moment, this data stream provides real-time insight into military logistics, sanctions evasion (shadow fleet aircraft), private aviation of individuals of interest, arms trafficking, and geopolitical activity.

The technique sits at the intersection of signals intelligence (SIGINT), geospatial intelligence (GEOINT), and open-source entity resolution. Its power lies in the fact that ADS-B was designed for air traffic safety, not privacy — aircraft continuously transmit their identity, position, altitude, and velocity on a public frequency (1090 MHz) that any suitably tuned receiver can intercept. Unless an operator takes deliberate steps to suppress or spoof these broadcasts, the flight record is freely available for analysis (Bowler, Signal & Shadow, July 2026).

## 1. ADS-B Technology Fundamentals

### 1.1 Protocol Architecture

ADS-B (Automatic Dependent Surveillance-Broadcast) is an aircraft surveillance technology where aircraft determine their position via satellite navigation (GPS/GLONASS) and periodically broadcast it, enabling tracking by ground stations and other aircraft. The system operates on 1090 MHz (Mode S Extended Squitter) for commercial aviation and 978 MHz (UAT) for general aviation in the US.

**ADS-B vs. Mode S:** Mode S is the underlying transponder protocol; ADS-B is the data broadcast layer built on top of it. Mode S provides selective interrogation (each aircraft has a unique 24-bit ICAO address), while ADS-B squitters — unsolicited broadcasts — carry position, velocity, and identification data. The distinction matters for OSINT: even when an aircraft disables ADS-B position reporting, it may still emit Mode S short squitters revealing its ICAO hex code, which can be triangulated via multilateration (MLAT) by networks of ground receivers.

**Key data fields transmitted (Flight Science, Ch. 9):**
- ICAO 24-bit aircraft address (hex code, linked to registration)
- Latitude, longitude, altitude (barometric and geometric)
- Velocity (ground speed, vertical rate)
- Heading/track angle
- Flight identification (callsign)
- Squawk code (transponder code)
- Emergency status indicators

### 1.2 Reception Hardware

**Entry-level:** RTL-SDR USB dongle (~$25, 24MHz-1.7GHz) with Dump1090 decoder software provides basic ground-level coverage (range ~100-300nm depending on antenna/terrain). The Kali Linux Cookbook (Packt, 2018) documents the complete setup:
```bash
git clone https://github.com/antirez/dump1090.git
cd dump1090 && make
./dump1090 --interactive -net
```
This launches an interactive CLI showing detected aircraft and an HTTP server displaying positions on Google Maps.

**Mid-tier:** FlightAware Pro Stick Plus, Airspy R2 — better sensitivity and filtering for congested spectrum.

**Advanced/Array:** KrakenSDR ($200) — a 5-channel coherent RTL-SDR array capable of radio direction finding (bearing to transmitters) and passive radar (detecting aircraft using FM broadcast signal reflections, zero emissions). Documented in Exocortex Gadget Kit Design Note (specs/GADGET_KIT_DESIGN_NOTE.md).

**Dedicated receiver:** Stratux — open-source ADS-B receiver software running on Raspberry Pi (documented in Internet of Things Programming Projects, Packt). Used in general aviation for in-flight weather and traffic, but the same hardware provides OSINT investigators a portable, battery-powered ADS-B collection platform.

**Space-based coverage:** Aireon — satellite-based ADS-B receivers hosted on the Iridium NEXT constellation, providing global coverage including oceanic and polar regions where ground stations cannot reach. Data is available commercially and through some research agreements (OpenSky Network).

### 1.3 ADS-B Security & Evasion

ADS-B was designed without authentication or encryption — any transmission can be received, and with sufficient knowledge, spoofed (Costin & Francillon, 2012). This creates a dual OSINT dynamic:

1. **Detection evasion by targets:** Aircraft operators deliberately disable transponders, switch to Mode S-only (no position broadcast but hex code still visible), spoof ICAO addresses, or operate below radar coverage. Russian shadow fleet aircraft flying to Algeria routinely \"dropped off ADS-B tracking radars even though other nearby aircraft remained within coverage\" — a known pilot evasion technique (Höller, Defense News, April 2026).
2. **OSINT counter-evasion:** Multilateration (MLAT) triangulates Mode S signals from multiple receivers even without ADS-B position. Satellite imagery overflight cross-referencing fills gaps (see §4 Cross-Domain Integration). ADS-B Exchange explicitly does not honor operator redaction requests, unlike FlightRadar24/FlightAware which comply.

### 1.4 Redaction & Uncensored Sources

Commercial flight trackers (FlightRadar24, FlightAware) honor operator requests to block tail numbers from public display — a feature widely used by wealthy individuals, state-connected entities, and military operators. For OSINT, uncensored alternatives are essential:
- **ADS-B Exchange:** Unfiltered global ADS-B data, no-censorship policy, community-hosted receivers. Used by C4ADS, OCCRP, and Bellingcat for investigations.
- **OpenSky Network:** Research API with bulk historical data access, academic/nonprofit focus.
- **Icarus Flights (C4ADS):** Built on ADS-B Exchange data, designed for investigative aviation analysis.

## 2. OSINT Investigation Techniques

### 2.1 Aircraft Identification & Owner Resolution

**ICAO Hex → Registration → Owner chain:**
1. Extract the 24-bit ICAO hex code from ADS-B or Mode S transmissions
2. Cross-reference against aircraft registries: FAA N-Number (US), G-INFO (UK), Transport Canada, national registries
3. Resolve the registered owner (individual, corporation, or trust) — frequently a shell entity
4. Chain-walk the corporate registry: beneficial owner → holding company → operating entity
5. Cross-reference with sanctions lists (OFAC SDN, EU, UN)

**Fleet analysis:** FlightAware and ADS-B Exchange allow searching by operator/owner, revealing all aircraft associated with a specific entity. This exposes the scope of aviation assets and enables systematic travel pattern analysis across the entire fleet.

### 2.2 Dark Aircraft Detection

\"Dark aircraft\" operate with transponders disabled or spoofed. Detection techniques:
- **Mode S MLAT triangulation:** Even without ADS-B position, Mode S short squitters carry the ICAO hex; trilateration from 4+ receivers yields position
- **Satellite imagery cross-reference:** Overlay known ADS-B tracks on satellite imagery; aircraft visible on the tarmac but absent from tracking feeds indicate deliberate shutdown
- **Gap analysis:** An aircraft that disappears from coverage in one region and reappears in another with impossible direct-flight timing indicates intermediate stops with transponder off
- **Flight plan vs. actual path deviation:** Filed ICAO flight plans vs. ADS-B observed routes — significant deviation suggests operational deception

**Case Study — Russian Shadow Airlines (Defense News, April 2026):** Linus Höller documented 167+ cargo flights linking Russia to Algeria (March 2025-April 2026) operated by a dozen shadow airline operators. Key findings:
- Aircraft frequently visited Russian fighter jet production sites (Komsomolsk-on-Amur for Su-57/Su-35, Irkutsk for Su-30, Yeltsovka for Su-34) shortly before heading to Algeria
- Algerian destinations included military air bases (Oum El Bouaghi, Ain Oussera, Annaba, Laghouat, Béchar)
- Evasion techniques: \"many of the aircraft appeared to be involved in tracking-evasion techniques such as turning off their ADS-B transponders or misdeclaring airports in their itineraries\"
- Mineralnye Vody airport served as the primary staging hub (~⅔ of flights transited there)
- Ilyushin Il-76 was the workhorse airframe (~5,000km range when loaded)
- Algeria also served as a transit hub: flights onward to Conakry, Guinea (Russian mining/military interests) and Niamey, Niger (uranium airlift by Rosatom, Antonov An-124 heavy-lift)
- Satellite imagery confirmed An-124 RA-82079 parked at Niamey airport on multiple dates
- C4ADS analyst Margaux Garcia confirmed the flights likely delivered Su-57 and Su-35 fighter jets

### 2.3 Sanctions Evasion & Shadow Fleet Aviation

The maritime shadow fleet concept (see [[maritime-logistics-gray-zone]]) has a direct aviation parallel. Sanctioned entities and state actors use:
- Shell company ownership chains to obscure beneficial ownership of aircraft
- Flag-state hopping (re-registering aircraft in permissive jurisdictions)
- Transponder manipulation (selective ADS-B deactivation, hex code spoofing)
- Front airlines with no commercial passenger business, existing solely to move cargo for state interests

**OSINT Field Notes #7 (April 2026)** documents the military dimension of the shadow fleet: \"It adds a military dimension to the shadow fleet story that most sanctions-focused maritime analysts haven't been tracking.\" The methodology is transferable — the same entity resolution chain (aircraft registration → corporate registry → beneficial owner → sanctions list) applies to both maritime and aviation domains.

**Oxint.io 2026 Sanctions Stack** specifically recommends ADS-B Exchange for tracking Russian oligarch aircraft post-2022, noting that \"ownership-and-tracking work has been a continuous public-interest investigation.\"

### 2.4 Military Logistics Tracking

**IntelSky (intelsky.org):** A dedicated military aviation OSINT platform launched in 2026, providing real-time tracking of military, government, and ISR (Intelligence, Surveillance, Reconnaissance) aircraft worldwide. Features include live ADS-B radar, squawk alerts (emergency codes 7500/7600/7700), and historical path analysis.

**Defense procurement intelligence:** Monitoring test flights from manufacturer airfields provides production timeline intelligence. For example, tracking flights from Komsomolsk-on-Amur (Su-57 production) reveals delivery schedules to foreign customers (see Defense News Algeria investigation). Similarly, flights from Palmdale (Northrop Grumman) or Fort Worth (Lockheed Martin) can indicate B-21 Raider or F-35 production milestones.

**Squawk code analysis:**
- 7500 — Hijack
- 7600 — Radio failure
- 7700 — Emergency
- Military-specific squawk ranges (e.g., 00xx-04xx in US airspace) can indicate military operations

### 2.5 Temporal & Geospatial Pattern Analysis

Following the methodology in [[timeline-reconstruction-osint]]:
- ADS-B timestamps provide precise temporal anchors (±1 second accuracy)
- Flight path reconstruction enables pattern-of-life analysis: regular routes, unusual deviations, night operations
- Airfield visit frequency analysis reveals supply chain relationships (e.g., Defense News identified Komsomolsk-on-Amur as the most-visited Russian origin for Algeria-bound flights)
- Turnaround time at destinations indicates cargo type (quick turn = personnel/light cargo; extended ground time = heavy equipment offload)

### 2.6 Wealth & Political Exposure via Private Aviation

**Case Study — OCCRP Nazarbayev Investigation (2022):** OCCRP reporters obtained an import-duty exemption document for a new Airbus ACJ320neo worth $100M+ destined for Nursultan Nazarbayev's charitable foundation. The document gave only import date and aircraft type — no tail number. Methodology:
1. Used the import date and aircraft type to search uncensored flight data (Icarus Flights/ADS-B Exchange) by plane type and takeoff/landing location
2. Found only one ACJ320neo had flown in Kazakh airspace since June 2020
3. Pulled additional flights from OpenSky Network, including a Moscow trip coinciding with a Kremlin-announced Putin-Nazarbayev meeting
4. Domestic trips matched Nazarbayev's public appearance schedule — \"compelling evidence, in OCCRP's own framing, that the jet was used by Nazarbayev despite its formal ownership by a charity\" (Bowler, Signal & Shadow, 2026)

## 3. Tool Ecosystem

| Tool | Type | Key Features | Censorship | API/Access |
|------|------|-------------|------------|------------|
| **ADS-B Exchange** | Aggregator | Unfiltered global ADS-B, military/government aircraft included | None — does not honor redaction requests | Free web, API (paid tiers) |
| **FlightRadar24** | Commercial | Rich UI, historical playback, fleet tracking | Blocks per operator request | Free tier, paid API |
| **FlightAware** | Commercial | Fleet analysis, operator search, global coverage | Blocks per operator request | Free tier, paid API |
| **OpenSky Network** | Research | Bulk historical data, academic API | Minimal — research focus | Free (academic), API rate-limited |
| **RadarBox** | Commercial | Flight tracking, airport activity | Blocks per operator request | Free tier, paid API |
| **Icarus Flights (C4ADS)** | Investigative | Built on ADS-B Exchange data, optimized for OSINT investigations | None | Access via C4ADS |
| **IntelSky** | Military OSINT | Dedicated military/ISR tracking, squawk alerts, historical path analysis | Military-inclusive | Free web (2026) |
| **Dump1090** | Receiver/Decoder | Local ADS-B decoding from RTL-SDR, Mode S/ADS-B, interactive CLI, HTTP map server | N/A (local) | Open source (GitHub) |
| **Stratux** | Receiver | Open-source ADS-B receiver on Raspberry Pi, portable, battery-powered | N/A (local) | Open source |
| **Aireon** | Space-based | Satellite ADS-B via Iridium NEXT, global oceanic/polar coverage | Commercial | Commercial licensing |
| **KrakenSDR** | DF/Passive Radar | 5-channel coherent array, direction finding, passive radar (no emissions) | N/A (local) | Hardware ($200), open source software |

## 4. Cross-Domain Connections

| Domain | Wiki Page | Integration |
|--------|-----------|-------------|
| **Maritime Shipping OSINT** | [[maritime-logistics-gray-zone]] | Combined AIS + ADS-B for logistics chain mapping; shadow fleet methodology transfer |
| **Satellite Imagery OSINT** | [[satellite-imagery-osint]] | Overlay ADS-B tracks on imagery for dark aircraft detection; Bellingcat MH17 methodology |
| **Sanctions Evasion Detection** | [[sanctions-evasion-detection]] | Aircraft as parallel shadow fleet methodology to maritime; Iranian, Russian, North Korean aviation evasion networks |
| **Entity Resolution** | [[entity-resolution-agent-safety]] | ICAO hex → aircraft registration → corporate registry → beneficial owner chain |
| **Geolocation OSINT** | [[geolocation-osint]] | Bellingcat MH17 methodology — imagery + ADS-B for timeline verification |
| **Timeline Reconstruction** | [[timeline-reconstruction-osint]] | ADS-B timestamps as precise temporal anchors (±1 second) |
| **RF Sensing / Gadget Kit** | specs/GADGET_KIT_DESIGN_NOTE.md | RTL-SDR + KrakenSDR hardware for passive aircraft detection and direction finding |
| **Energy Commodity Dynamics** | [[energy-commodity-dynamics]] | Tracking oil/gas-related corporate aviation for sanctions monitoring |
| **Defense Procurement** | [[defense-procurement-cycles]] | Military aircraft test flight monitoring for production timeline intelligence; Defense News Algeria case study |
| **Counterintelligence** | [[counterintelligence-analysis-frameworks]] | Pattern-of-life analysis applies to adversary operational security assessment; transponder-off evasion as OPSEC indicator |
| **Supply Chain Network Analysis** | [[supply-chain-network-analysis-osint]] | Aviation logistics as key layer in supply chain reconstruction; arms trafficking via air cargo |
| **UAV/Drone Proliferation** | [[drone-autonomous-weapons-proliferation]] | UAV RemoteID (US) and drone detection via RF; crossover with ADS-B for military UAV tracking |
| **Corporate Registry OSINT** | [[business-registries-osint]] | Aircraft registration shell company chain-walking; shadow airline corporate structure discovery |
| **Legal/Ethical OSINT** | [[legal-ethical-osint]] | ADS-B data is publicly broadcast — collection is passive and legal in most jurisdictions; registration data access varies by country |

## 5. Evasion Techniques & Countermeasures

### 5.1 Known Evasion Techniques

| Technique | Detection Difficulty | Countermeasure |
|-----------|---------------------|----------------|
| ADS-B transponder deactivation | Easy — aircraft disappears from all trackers | Mode S MLAT (hex code still visible), satellite imagery cross-reference |
| ICAO hex code spoofing | Hard — requires ground truth | Anomaly detection (impossible flight patterns), multi-source correlation |
| Airport misdeclaration in flight itineraries | Medium | ADS-B position data contradicts filed flight plan |
| Below-radar flight (nap-of-the-earth) | Hard | Satellite imagery, HUMINT, acoustic sensors |
| Flag-of-convenience registration | Medium | Corporate registry chain-walking to beneficial owner |
| Shell company ownership masking | Medium-Hard | Entity resolution pipelines (Fellegi-Sunter, Splink); cross-jurisdictional registry analysis |
| Callsign spoofing/misuse | Easy-Medium | Pattern analysis — same callsign on multiple airframes, non-standard callsign formats |

### 5.2 The Detection Arms Race

As OSINT investigators and sanctions enforcement agencies have become more sophisticated at aircraft tracking, targets have escalated their evasion techniques. The Defense News investigation documented that Russian shadow fleet pilots now routinely employ transponder-off tactics, particularly on flights south from Algiers into sub-Saharan Africa — a pattern that developed in response to increased scrutiny after 2022. This mirrors the maritime shadow fleet evolution documented in [[maritime-logistics-gray-zone]] and [[russian-oil-price-cap-sanctions-enforcement]].

## 6. Methodology: 5-Phase OSINT Investigation Workflow

1. **Collection:** Aggregate ADS-B data from uncensored sources (ADS-B Exchange, OpenSky Network), set up local RTL-SDR receiver for targeted collection, capture Mode S as well as ADS-B
2. **Identification:** Resolve ICAO hex codes to registrations, identify operators, flag blocked/redacted aircraft for deeper investigation
3. **Pattern Analysis:** Reconstruct flight histories, identify regular routes, detect anomalies (impossible flight times, coverage gaps, airport mismatches), analyze fleet-wide patterns
4. **Entity Resolution:** Chain-walk aircraft registrations through corporate registries to beneficial owners, cross-reference with sanctions lists, campaign finance, government contracts, and other OSINT databases (see [[public-records-databases-osint]])
5. **Corroboration:** Cross-validate with satellite imagery, maritime AIS data, social media posts, news reports, and other open sources. Document evidentiary chain to publication standard.

## 7. Exocortex Integration

- **ADS-B Exchange API:** Automated polling for fleet tracking, squawk alerts, and area monitoring
- **Entity Resolution Pipeline:** ICAO hex → registration → corporate registry → sanctions list via Fellegi-Sunter probabilistic matching ([[entity-resolution-algorithms]])
- **Knowledge Graph:** Store aircraft-registration-owner-flight chains as graph entities for cross-source linking ([[knowledge-graph-construction-patterns]])
- **Scheduled Tasks:** Set up recurring ADS-B data collection for persistent monitoring of targets of interest ([[scheduled-tasks]])
- **Irreversibility Gate:** When collecting ADS-B data that may reveal sensitive flight patterns of individuals, apply the irreversibility gate framework before publishing or acting on findings

## 8. Research Frontiers (2025-2026)

- **AI/ML anomaly detection:** Using machine learning to detect anomalous flight patterns (deviation from historical routes, impossible flight times, transponder-off gaps) at scale across global ADS-B data streams
- **LLM-based investigation assistance:** AI agents that can autonomously collect ADS-B data, resolve entity chains, and generate investigative leads — the Agentic OSINT paradigm ([[agentic-osint-autonomous-investigation]])
- **Passive radar advances:** KrakenSDR and similar coherent arrays enabling detection of aircraft that have disabled all transponders, using ambient FM/TV broadcast signals as illumination sources
- **Space-based ADS-B (Aireon):** Expanded access to satellite-collected ADS-B data filling oceanic/polar coverage gaps — game-changing for tracking trans-oceanic shadow fleet flights
- **ADS-B security research:** Cryptographic authentication proposals for ADS-B to prevent spoofing; in the OSINT context, authenticated ADS-B would increase data reliability but reduce the ability to detect spoofing attacks

## References

1. Flight Science, Chapter 9 — Navigation, ADS-B, GPS/WAAS, GLONASS. Humble Bundle Applied Mathematics collection.
2. Kali Linux — An Ethical Hacker's Cookbook (Packt, 2018) — Dump1090 ADS-B decoding with RTL-SDR, complete setup and configuration.
3. Exocortex Gadget Kit Design Note (specs/GADGET_KIT_DESIGN_NOTE.md) — RF sensing hardware tiers including RTL-SDR, HackRF One, KrakenSDR.
4. Internet of Things Programming Projects (Packt) — Stratux ADS-B receiver on Raspberry Pi.
5. Bellingcat — MH17 investigation methodology: satellite imagery + ADS-B overlay for timeline verification.
6. Exocortex v17 shared corpus: geolocation-osint.md, satellite-imagery-osint.md, public-records-databases-osint.md.
7. ADS-B Exchange (adsbexchange.com) — unfiltered global ADS-B data, no-censorship policy.
8. OpenSky Network (opensky-network.org) — research API for bulk ADS-B data analysis.
9. FlightRadar24, FlightAware, RadarBox — commercial aggregators with historical playback.
10. Aireon — satellite-based ADS-B via Iridium NEXT (global oceanic coverage).
11. Bowler, Derek. \"ADS-B and Transponder Tracking for OSINT Investigators.\" Signal & Shadow, July 1, 2026. — Comprehensive methodology covering hex resolution, redaction circumvention, OCCRP Nazarbayev case study, and evidentiary standards.
12. Höller, Linus. \"Investigation: Russian Shadow Airlines Use Algeria as Base for Secretive Missions.\" Defense News, April 30, 2026. — 167+ documented cargo flights, ADS-B evasion techniques, specific airframes and airfields, satellite imagery corroboration, C4ADS analyst commentary.
13. OCCRP. \"The Nazarbayev Billions: How Kazakhstan's Leader of the Nation Controls Vast Assets Through Charitable Foundations.\" January 2022. — Aircraft tracking methodology: document-led filtering, uncensored data source (Icarus Flights/ADS-B Exchange), movement correlation with public appearances.
14. IntelSky (intelsky.org) — Military aviation OSINT platform, real-time ADS-B for military/government/ISR aircraft, squawk alerts.
15. AdriaDefense. \"10 Free OSINT Tools Every Defence Analyst Should Be Using in 2026.\" June 4, 2026. — ADS-B Exchange for unfiltered military aircraft tracking.
16. Oxint.io. \"OSINT Investigation Stack for Sanctions Analysts (2026).\" — ADS-B in sanctions compliance stack, Russian oligarch aircraft tracking methodology.
17. OSINT Field Notes #7, April 8, 2026. — Military dimension of shadow fleet aviation, ADS-B tracking methodology.
18. Costin, A. & Francillon, A. (2012). \"Ghost in the Air(Traffic): On Insecurity of ADS-B Protocol and Practical Attacks on ADS-B Devices.\" Black Hat USA 2012. — Foundational ADS-B security research: lack of authentication, spoofing feasibility.

---

## #status | DRAFT | Created 2026-07-11 | Deepened 2026-07-11
## #topic | OSINT & Investigation Methodology
