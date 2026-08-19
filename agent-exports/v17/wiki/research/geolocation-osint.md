# Geolocation for OSINT Investigation

**Status: STABLE**
**Created: 2026-07-03 | Last deepened: 2026-07-03**
**Domain: OSINT / Investigation**

Geolocation is the foundational OSINT technique of determining the physical location of a person, device, infrastructure, or event from digital evidence. It spans multiple data modalities — IP addresses, images, videos, satellite imagery, metadata, radio signals, and GPS — and is central to identity attribution, timeline reconstruction, and evidence verification.

---

## 1. IP Geolocation

Mapping IP addresses to geographic coordinates. Four-tier accuracy hierarchy: country (99.8%), city (50-80%), postal code (~30%), coordinate within 50km (~20%). Primary databases: MaxMind GeoIP2, IPinfo, IP2Location, DB-IP.

**Critical structural limitations (arXiv:2605.21937, Nabi et al. 2026):**
- **Mobile vs. Fixed Gap:** 10x worse — mobile networks 179-207 km median error vs 3-16 km fixed. Structural, not provider-specific.
- **Global South Gap:** Asia 53-61% failure rate (>100km error), Africa 66-72%, vs Europe 9-20%.
- **Root Cause:** 32-40% of all geolocation prefixes span >100 km; ~70% of mobile prefixes exceed 100 km.
- **Accuracy Radius Deception:** p90 ratio of actual error to stated accuracy radius = 10x. MaxMind "50 km accuracy" can mean 500 km actual at p90.
- **IPv6 Blind Spot:** >60% of traffic on IPv6 with sparse geolocation database coverage.

**Method tiers (ascending accuracy/latency):** database-driven (<1ms), HTML5 Geolocation API, DNS-based, latency-based triangulation, ML-enhanced (RIPE Atlas + CBG), hybrid (database + latency + topology, ~85% city accuracy).

**Investigation workflow:** extract IP -> database lookup (multiple providers simultaneously, flag discrepancies) -> verify against known infrastructure (VPN/Tor cross-check) -> document accuracy radius as metadata -> never plot coordinates without error bars.

## 2. Image Geolocation

Determining where a photo/video was taken by analyzing visual content when GPS coordinates are absent or suspect.

**Visual Feature Analysis:**
- Natural landmarks (mountain silhouettes, coastlines, rivers, tree species)
- Built environment (architecture styles, road markings, signage language, utility infrastructure)
- Vegetation and climate zone indicators
- Shadow analysis: sun angle -> rough latitude + time of day; with date-stamp -> approximate longitude
- Weather/cloud formations as seasonal constraints

**Reverse Image Search:** Google Images, Yandex (Russia/Eastern Europe bias), TinEye, Bing Visual Search. Crop watermarks/text/borders. Multiple engines due to regional indexing differences.

**GeoGuessr-Style Deduction:** 5-category system: (1) sun direction -> hemisphere, (2) road markings -> country, (3) license plates -> country confirmation, (4) signage language -> region, (5) utility/architectural details -> precise location. Competitive players achieve meter-level accuracy from street-level imagery.

**Tools:** Google Earth/Maps, Yandex Maps, Baidu Maps, Wikimapia, OpenStreetCam, Mapillary.

## 3. AI/LLM-Powered Image Geolocation

LMMs (Large Multimodal Models) are transforming image geolocation from manual deduction to automated inference, with significant privacy implications.

### 3.1 Performance Benchmarks (2025-2026)

| Model/Framework | Benchmark | Accuracy | Notes |
|-----------------|-----------|----------|-------|
| WanderBench + GeoAoT | 32K panoramas across 6 continents | State-of-art fine-grained localization | Embodied reasoning — model can request rotation/movement actions to reduce uncertainty (arXiv:2603.10463) |
| Top-tier visual LMMs | Street-level imagery | 49% within 1km radius | Can infer location from text, architecture, environmental features alone — privacy risk |
| GPT-4V / Claude Vision | Bellingcat-style scenarios | Competitive with trained analysts on urban imagery | Excels at landmark recognition; weaker on rural/vegetation-only scenes |

### 3.2 WanderBench & GeoAoT (Zheng et al., 2026)

**WanderBench** is the first open-access global geolocation benchmark designed for actionable reasoning in embodied scenarios. 32K+ panoramas organized as navigable graphs that enable physical actions (rotation, movement). Transforms geolocation from static recognition into interactive exploration.

**GeoAoT (Action of Thought)** couples reasoning with embodied actions. Instead of text reasoning chains, it produces actionable plans: "approach the landmark," "adjust viewpoint 30° left" — actively reducing uncertainty. Evaluated over 19 LMMs.

**Key insight for OSINT:** The interactive paradigm enables progressively refined location estimates. An analyst can feed the model a photo, get a candidate region, then zoom/pan within the WanderBench graph to disambiguate visually similar locations.

### 3.3 Privacy & Counter-Intelligence Implications

- **Doxxing vector:** 49% within-1km accuracy from street-level photos makes social media images a potent location leak.
- **Countermeasures:** Image perturbation (adversarial noise, style transfer), metadata stripping insufficient against visual-only inference.
- **Detection:** Track whether MLLM geolocation requests appear in server logs; anomaly detection on image upload frequency/destinations.
- **Policy:** IEEE and ACM workshops (2025-2026) calling for geolocation-resistant image sharing standards.

## 4. Satellite & Aerial Imagery Analysis

**Platforms:** Google Earth Pro (historical imagery, measurement), Sentinel Hub (free 10m Sentinel-2, SAR cloud-penetrating radar), Planet Labs (3-5m daily revisit, commercial), Maxar/WorldView (30cm, taskable).

**Investigative Techniques:**
- Change detection: compare historical imagery for construction, deforestation, infrastructure projects (sanctions monitoring, conflict analysis)
- Shadow analysis: length + azimuth -> approximate time and latitude
- Infrastructure fingerprinting: military base layouts, industrial facility signatures, prison architectures (templates exist)
- Ship/aircraft tracking: overlay AIS/ADS-B data on imagery to identify dark vessels or transponder-off aircraft

**Case Study — Bellingcat MH17:** Imagery analysis confirmed Russian Buk missile system location by matching Russian MOD imagery features (cloud patterns, vegetation, vehicle positions) with independent satellite data, exposing doctored timestamps.

## 5. Cross-View Satellite-to-Ground Geolocation

Advanced computer vision techniques for matching ground-level photos to satellite imagery — critical for verifying event locations when only partial visual evidence is available.

### 5.1 Cross-View Splatter (Turkulainen et al., 2026)

Feed-forward method predicting pixel-aligned Gaussian splats from georeferenced ground + satellite imagery. Fuses orthorectified satellite views with GPS-tagged ground photos in a unified 3D coordinate frame. Enables novel-view synthesis and improved scene coverage (arXiv:2605.19656).

### 5.2 Satellite-to-Planimetric Map Fusion (Ngo et al., 2026)

Fuses satellite imagery with OpenStreetMap tiles for cross-view localization. Patch-level fusion rule learns when to prefer satellite detail vs. map annotation (streetlamps, buildings). Achieves 30.13% reduction in mean localization error (arXiv:2606.10166).

### 5.3 SatDreamer360 (Xu & Qin, 2025)

Panoramic epipolar-constrained architecture that generates 360° ground-level scenes from a single satellite image. Introduces VIGOR++ dataset for multi-view panorama generation. Applications: digital twin cities, autonomous navigation, OSINT scene recreation.

### 5.4 Practical OSINT Application

- Submit ground photo -> cross-view model returns candidate satellite tile matches -> analyst verifies matches with manual feature comparison.
- Temporal cross-view: historical satellite imagery matched to dated ground photos validates timeline.
- Limitation: requires GPS-tagged training data; accuracy degrades in feature-sparse environments (desert, ocean).

## 6. Metadata-Based Geolocation

**EXIF Data:** GPS coordinates, timestamp, device info from smartphones/GPS cameras. ExifTool is gold standard. Warning: social media platforms strip EXIF by default (Facebook, Twitter, Instagram, Reddit). Messaging apps may retain depending on settings.

**Document Metadata:** PDF author/creation software/file paths (sometimes exposes username/organization). Office files (DOCX/XLSX): author, last modified by, company name, revision history.

## 7. Cell Tower Triangulation

Not available to civilian OSINT but contextually relevant. Carrier CSLI provides tower sector + approximate distance: 100m (urban dense-tower) to several km (rural single-tower). Legal: Carpenter v. United States (2018) warrant requirement.

## 8. GPS Spoofing & Location Manipulation Detection

- GPS spoofing: signal replay, meaconing, synthetic generation (maritime dark vessels, military, fraud)
- VPN/proxy detection: MaxMind minFraud, IPQualityScore, IPinfo privacy flags; cross-reference BGP ASN data (datacenter ASN = likely hosting/VPN)
- Cross-validation: EXIF GPS + IP geolocation + visual features must converge. Divergence = authenticity red flag.

## 9. Investigation Methodology

### 9.1 Core Workflow

Triage available location modalities -> Extract raw data -> Cross-validate (multiple IP databases, visual features vs satellite, metadata vs visual) -> Flag uncertainty (document accuracy radius for each data point; never present coordinates without error bounds) -> Resolve contradictions -> Document source for each location assertion.

### 9.2 NiamonX Practical Investigation Checklist (2025)

Adapted from NiamonX 2025 geolocation methodology:

1. **Preserve originals:** Save raw files, compute hashes.
2. **Extract metadata:** exiftool; note alterations.
3. **Run reverse-image searches:** Google, Yandex, TinEye with crops/variants.
4. **Feature matching:** Road patterns, building shadows, vegetation, coastline curvature — compare to candidate satellite tiles.
5. **Satellite verification:** Cross-reference with date-range imagery (Sentinel, Google Earth, Planet).
6. **Sun-angle/shadow check:** Validate time-of-day consistency.
7. **Social corroboration:** Independent social media posts, local media, eyewitness accounts.
8. **Forensic integrity:** Noise pattern analysis, metadata provenance, tampering detection.
9. **Document + export:** Reproducible report with timestamps, sources, and uncertainty levels.

### 9.3 AI-Powered Multimodal Verification Workflow (2025-2026)

- **Triage:** AI models produce candidate location lists with confidence scores.
- **Verify:** Analyst inspects top-3 candidates; runs independent corroboration (metadata, shadows, landmarks, timestamps, multiple imagery providers).
- **Forensic defense:** ML-based tampering detectors for synthetic satellite and street-level imagery.

## 10. Threats & Manipulation

### 10.1 Deepfake Satellite & Street Imagery

Generative AI can produce plausible-but-fake satellite imagery and street-level photos. Detection requires noise-pattern consistency checks, metadata provenance verification, and cross-reference with multiple commercial/free satellite providers.

### 10.2 Accuracy Radius Deception

Adversary may exploit IP geolocation error margins: an IP registered to "New York" can physically route through Texas (anycast CDN, mobile CGNAT). Investigators must treat accuracy radius as metadata, not fact.

### 10.3 AI Geolocation Arms Race

As LMMs achieve 49% within-1km street-level accuracy, adversaries deploy adversarial perturbations and style-transfer obfuscation. Cat-and-mouse dynamic with forensic detectors.

## 11. Tools Reference

| Tool | Modality | Cost | Notes |
|------|----------|------|-------|
| MaxMind GeoIP2 | IP | Free/Paid | 99.8% country, ~66% city |
| IPinfo | IP | Freemium | ASN, privacy detection |
| IP2Location DB11 | IP | Free/Paid | Best mobile: 179km median |
| DB-IP Lite | IP | Free | Open data, monthly updates |
| ExifTool | Metadata | Free | Gold standard EXIF/IPTC/XMP |
| Google Earth Pro | Satellite | Free | Historical, measurement tools |
| Sentinel Hub | Satellite | Free | 10m, SAR, temporal analysis |
| Google/Yandex/TinEye | Reverse Image | Free | Regional bias varies |
| Mapillary | Street-Level | Free | Crowd-sourced |
| Shodan | Device Geo | Freemium | IoT/camera/industrial fingerprints |
| BGP.tools / HE BGP | Network | Free | Prefix size, ASN, peering |
| NiamonX Maps Explorer | Multi-Layer Map | Free | Browser-based OSINT mapping toolkit — satellite + basemaps + professional overlays |
| Planet Explorer | Satellite (commercial) | Paid | 3-5m daily revisit, commercial licensing |
| Amped Authenticate | Metadata/Forensics | Paid | Professional image authentication |
| QGIS | Geospatial | Free | Full GIS for overlays, spatial analysis |

## 12. Legal & Ethical Boundaries

- CFAA (US): Passive database lookups legal. Port scanning/traceroute to unauthorized endpoints may violate CFAA.
- GDPR (EU): IP addresses = personal data (Art 4(1)). Geolocation processing needs lawful basis. Investigative/journalistic use may qualify under Art 85 exemptions.
- LMM geolocation privacy: Unconsented location inference from social media images may violate platform ToS and emerging AI privacy regulations.
- Responsible disclosure: If geolocation reveals vulnerability (exposed IoT at critical facility), follow ISO/IEC 29147.

## 13. Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| **Entity Resolution** | Spatial proximity strengthens identity resolution. Prefix granularity creates false proximity — accounts from same /16 mobile prefix may appear co-located despite 200km separation. |
| **Email Header Forensics** | Received headers contain IP chains; geolocating each hop reconstructs sender path. Mobile headers have 200+ km uncertainty. |
| **Domain WHOIS/DNS** | ASN analysis becomes more important when IP geolocation unreliable — ISP/ASN provides more actionable attribution than 200km-radius coordinate. |
| **Data Breach Analysis** | IP+timestamp pairs for historical location timeline. Mobile IPs have region-level (not city-level) resolution. |
| **Social Media OSINT** | Visual geolocation of profile photos, video backgrounds reveals location independent of platform data. LMMs can infer location from visual content even when metadata stripped. |
| **Maritime Domain Awareness** | AIS manipulation structurally identical to IP geolocation evasion — adversary obscures location to evade attribution. |
| **CI Analysis Frameworks** | Accuracy radius deception maps to intelligence failure pattern of over-trusting source metadata. Structured analytic techniques for hypothesis testing and confidence assessment. |
| **Critical Infrastructure** | CGNAT IP geolocation for remote OT sites creates >100km uncertainty for security event attribution to specific substations. |
| **Bridge Local-Frontier** | Domain knowledge (prefix structure, accuracy radius limits) that local models can capture and apply without frontier reasoning, if documented in structured wiki format. |
| **Influence Operations** | Geotag manipulation (spoofed GPS, deepfake satellite imagery) as disinformation vector — cross-domain verification essential. |
| **Agentic OSINT** | Autonomous investigation pipelines can integrate geolocation as a tool call; uncertainty must be propagated through the pipeline. |
| **Privacy-Preserving Federation** | Federated learning for geolocation models must protect location privacy; homomorphic encryption of location queries. |

## 14. Open Questions

- What is the accuracy ceiling for automated satellite-to-ground cross-view geolocation without GPS-tagged ground truth?
- How will adversarial perturbations evolve against LMM-based geolocation?
- What legal framework governs AI-inferred location disclosure (beyond GDPR Art 4)?
- Can OSINT investigators trust AI geolocation in court — what admissibility standards apply?

## References

1. Nabi, Bliton, Chung, Hasan (2026). "Lost in the Prefix: Revisiting IP Geolocation Accuracy Across Networks and Geographies." arXiv:2605.21937.
2. Zheng, Duan, Zhang, Liu, Min (2026). "Learning to Wander: Improving the Global Image Geolocation Ability of LMMs via Actionable Reasoning (WanderBench & GeoAoT)." arXiv:2603.10463.
3. Turkulainen et al. (2026). "Cross-View Splatter: Feed-Forward View Synthesis with Georeferenced Images." arXiv:2605.19656.
4. Ngo et al. (2026). "Fusing Satellite Imagery and Planimetric Maps for Cross-View Localization." arXiv:2606.10166.
5. Xu & Qin (2025). "Satellite to GroundScape — Large-scale Consistent Ground View Generation from Satellite Views." arXiv:2504.15786.
6. NiamonX Team (2025). "Geolocation 2025: How OSINT, AI, and satellite forensics are rewriting the map." https://blog.niamonx.io/geolocation-2025-how-osint-ai-and-satellite-forensics-are-rewriting-the-map
7. ProjectOSINT. "Geospatial OSINT Workflow: How to Verify Locations and Events." https://projectosint.com/geospatial-osint-workflow-verify-locations/
8. ShadowDragon (2026). "OSINT Techniques: Expert Tactics for Investigators." https://shadowdragon.io/resources/osint-techniques/
9. IEEE (2025). "OSINT Analysis Through Geolocation and Imagery: Practical Approaches." DOI: 10.1109/...
10. MaxMind GeoIP2 Accuracy: https://www.maxmind.com/en/geoip2-city-accuracy-comparison
11. ExifTool: https://exiftool.org/
12. RIPE Atlas: https://atlas.ripe.net/
13. Sentinel Hub: https://www.sentinel-hub.com/
14. Bellingcat. "MH17 Investigation." https://www.bellingcat.com/
15. Carpenter v. United States, 585 U.S. ___ (2018)
16. Exocortex wiki/research/ip-address-geolocation.md
17. Exocortex wiki/research/reverse-image-search-visual-osint.md
18. Exocortex wiki/research/ip-geolocation-network-attribution.md
19. Exocortex field-reports/20260608_ip-address-geolocation-techniques.md
