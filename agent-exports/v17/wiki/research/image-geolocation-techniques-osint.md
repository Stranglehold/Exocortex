# Image Geolocation Techniques for OSINT Investigation

**Status:** STABLE
**Deepened:** 2026-07-10
**Domain:** OSINT & Investigation Methodology
**Interest:** OSINT tradecraft — Bellingcat methodology, geolocation techniques
**Lines:** ~220

---

## Overview

Image geolocation is the practice of determining where a photograph or video was captured by analyzing visual clues within the image itself — shadows, landmarks, vegetation, architectural styles, signage, infrastructure, and temporal indicators. Unlike IP-based geolocation (which locates the server) or EXIF metadata extraction (which can be stripped or falsified), content-based geolocation relies on the immutable physical world recorded in the frame.

The Bellingcat collective pioneered and systematized these techniques into a reproducible methodology that has been used to verify war crimes, identify execution sites, and track arms shipments. This page surveys the core techniques, tool ecosystem, and research frontiers including LLM-based automated geolocation.

---

## Core Methodology

### 1. Shadow Analysis & Solar Geometry

The most mathematically rigorous technique. A shadow in an image encodes three interconnected variables:
- **Azimuth angle** — compass direction of the sun
- **Elevation angle** — sun height above horizon
- **Time of day** — determined from angle + date + location

Using **SunCalc** (Bellingcat toolkit), an analyst can input any two of {azimuth, elevation, time} to solve for the third. Given the location and date, SunCalc tells you what time the photo was taken. Given location and time, it tells you the sun direction (narrowing compass orientation for landmark matching).

The technique requires at least one vertical reference object (building, pole, person) casting a shadow on a flat surface. Limitations: overcast days, interior shots, shadows falling on slopes.

### 2. Landmark Identification

Distinctive built or natural features:
- **Iconic landmarks**: Eiffel Tower, Burj Khalifa — trivial
- **Infrastructure**: bridges, water towers, cell towers, power lines, rail crossings
- **Religious/civic architecture**: church steeples, minarets, government building styles distinctive to regions
- **Terrain features**: mountain silhouettes (PeakVisor for horizon matching), coastlines, river meanders

Multiple landmarks in a single image enable triangulation — narrowing the location to the area where all would be simultaneously visible from the camera's perspective.

### 3. Architectural Style & Infrastructure

Regional building conventions are powerful geolocation signals when landmarks are absent:
- **Roof styles**: red tile roofs (Mediterranean), thatched roofs (rural UK, Africa), metal sheet roofing (developing regions), flat roofs (Middle East), steep pitched roofs (Alpine/Swiss)
- **Building materials**: brick vs. concrete vs. wood framing — regional and era-specific
- **Window/door styles**: shutter designs, mullion patterns, balcony types
- **Street infrastructure**: road markings (yellow center lines = Americas; white = Europe), sign shapes, bollard designs, curb styles
- **Utility infrastructure**: overhead vs. buried power lines, pole designs, transformer boxes

A single 2024 Bellingcat investigation geolocated a site in rural Ukraine using the specific design of a roadside bus shelter — a perfect example of infrastructure-as-geolocation-signal.

### 4. Vegetation & Climate Signatures

Plant species have geographic ranges:
- **Palm trees**: coconut palms (tropical coastal), date palms (arid Middle East/North Africa), fan palms (Mediterranean/California)
- **Conifers vs. deciduous**: latitude and elevation signals
- **Cacti/succulents**: Americas-only (outside cultivation)
- **Eucalyptus**: Australia, but widely planted globally — requires caution

Climate indicators in photos: snow on palm trees (rare and highly specific), dust/dryness, humidity haze, seasonal leaf state.

### 5. Signage, Writing Systems & License Plates

- **Script identification**: Latin, Cyrillic, Arabic, Chinese, Japanese, Hangul, Thai, Devanagari immediately narrow to specific regions
- **Language on signs**: bilingual street signs (Belgium, Canada, Switzerland, Hong Kong), metric vs. imperial units
- **License plates**: country-specific color schemes, EU blue band, state/province codes
- **Commercial branding**: chain stores, bank names, telecom logos known to specific countries
- **Phone numbers**: country codes on advertisements, store windows

### 6. Chronolocation (Time-from-Image)

Determining *when* an image was taken, which constrains *where*:
- **Shadow direction + length** → time of day → time zone → longitude band (SunCalc method)
- **Clock faces visible** in image (analog or digital) — but may be wrong
- **Seasonal indicators**: leaf cover, snow, clothing (weather-appropriate attire), public event dates
- **Construction state**: partially built buildings, cranes, scaffolding can be matched to construction timelines via satellite imagery history
- **Vehicle models** visible can establish a *terminus post quem* (earliest possible date)

### 7. Multi-Source Corroboration

No single technique is definitive. Bellingcat's standard requires at least two independent data points confirming a location before treating a finding as confirmed. Typical corroboration chain:
1. Shadow analysis narrows to lat/long band
2. Landmark/architectural features further narrow within band
3. Google Earth/Maps Street View verification confirms match
4. Satellite imagery from multiple providers cross-references

---

## The Bellingcat Map Stack

The canonical investigation map stack (Bellingcat methodology):
1. **Google Earth** — 3D terrain, historical imagery timeline
2. **Yandex Maps** — often has imagery not on Google for Russia/CIS regions
3. **Bing Maps** — alternative aerial/satellite, often different capture dates
4. **Mapillary** — crowdsourced street-level imagery, invaluable for rural roads
5. **OpenStreetMap** — community-mapped detail (buildings, footpaths, land use)
6. **Wikimapia** — user-annotated locations with local knowledge
7. **PeakVisor** — mountain/summit identification from horizon profiles

---

## LLM-Based Automated Geolocation

A 2024–2026 research frontier. The Global Investigative Journalism Network (GIJN) tested 24 LLMs on Bellingcat holiday photos — images with and without recognizable features such as roads, signage, mountains, or architecture.

**Key findings (from GIJN published test):**
- Frontier models (GPT-4o, Claude) can narrow to correct city/country on images with recognizable landmarks ~60-70% of the time
- Performance collapses on images without obvious geographic markers — highlighting the gap between pattern-recognition and true spatial reasoning
- Models are easily fooled by culturally transplanted architecture (e.g., Las Vegas replicas)

**Academic research milestones:**
- **PIGEON/PIGEOTTO** (Haas et al., 2023–2024): fine-tuned CLIP models achieving 92% country-level accuracy on Geoguessr dataset
- **GeoCLIP** (Cepeda et al., 2024): GPS-encoded image embeddings with 1,500-mile median error → 300-mile with fine-tuning
- **GeoEstimation** (RAPTOR dataset): estimates geographic coordinates from single images using hierarchical classification

**OSINT integration**: LLM geolocation is currently an assistive tool for human analysts, not a replacement. The best workflow is LLM → narrowing search area → human analyst verification via map stack.

---

## Tool Ecosystem

| Tool | Function | Access |
|------|----------|--------|
| SunCalc | Sun position & shadow analysis | Free, web |
| Google Earth Pro | 3D terrain, historical imagery | Free |
| PeakVisor | Mountain/horizon identification | Freemium |
| Mapillary | Crowdsourced street-level imagery | Free, API |
| GeoGuessr | Gamified geolocation training | Paid |
| Bellingcat Toolkit | Curated OSINT tool collection | Free, web |
| Overpass Turbo | OpenStreetMap query engine | Free |
| QGIS | GIS analysis platform | Free, open-source |
| Sentinel Hub | Satellite imagery (ESA Sentinel) | Free tier |
| Wikimapia | User-annotated locations | Free |

---

## Investigation Workflow

1. **Extract all visual information** — catalog every observable clue (shadows, vegetation, signs, architecture, vehicles, clothing, weather, visible infrastructure)
2. **Chronolocate if possible** — shadow analysis, seasonal indicators → time/day → time zone
3. **Narrow geographic band** — script identification, vegetation, climate, architecture, infrastructure standards → continent → region → country
4. **Identify candidate locations** — landmarks, terrain features, map stack scanning
5. **Match and verify** — Street View, satellite imagery, multiple map sources
6. **Corroborate** — at least two independent data points before concluding
7. **Document chain of evidence** — every claim traceable to publicly accessible source

---

## Cross-Domain Connections

- **[[timeline-reconstruction-osint]]** — chronolocation feeds into multi-source timelines
- **[[reverse-image-search-osint]]** — reverse image search as first-pass (image may already exist with location metadata)
- **[[satellite-imagery-osint]]** — satellite imagery for final verification of geolocated sites
- **[[ip-address-geolocation]]** — IP geolocation provides server location; image geolocation provides content location
- **[[metadata-analysis-osint]]** — EXIF GPS data, when present, is the gold standard; geolocation recovers location when EXIF is absent
- **[[social-media-forensics-osint]]** — social media posts often contain imagery with geolocatable clues
- **[[visualization-techniques-osint]]** — geographic overlay mapping, force-directed link charts
- **[[osint-data-fusion-evidence-chains]]** — geolocation as Tier 1 direct evidence in evidence chains
- **[[humint-tradecraft-osint]]** — verification methodology isomorphism (cross-checking, corroboration)

---

## References

1. Bellingcat Toolkit — SunCalc. https://bellingcat.gitbook.io/toolkit/more/all-tools/suncalc
2. Bellingcat. "Using the Sun and Shadows for Geolocating Photos and Videos." GIJN, 2020. https://gijn.org/stories/using-the-sun-and-shadows-for-geolocating-photos-and-videos/
3. Bellingcat. "Bellingcat Geolocation Toolkit: 10 Sources That Always Work." https://ransomnews.com/bellingcat-geolocation-toolkit-10-sources/
4. GIJN. "Updated Test of 24 LLMs for Geolocation." 2026. https://gijn.org/stories/updated-test-24-llms-ai-geolocation/
5. Haas, Lukas, et al. "PIGEON: Predicting Image Geolocations." arXiv:2307.05845, 2023.
6. Cepeda, Vicente Vivanco, et al. "GeoCLIP: Clip-Inspired Alignment between Locations and Images for Effective Worldwide Geo-localization." NeurIPS 2024.
7. Sector035. "Chronolocation Tutorial." https://sector035.nl
8. Bellingcat. "Bellingcat's Online Investigation Toolkit." https://bellingcat.gitbook.io/toolkit
9. Exocortex Wiki — reverse-image-search-visual-osint.md (Bellingcat Methodology section)
10. Waters, Nick. "How to Identify and Geolocate a Missile launcher." Bellingcat, 2024.
