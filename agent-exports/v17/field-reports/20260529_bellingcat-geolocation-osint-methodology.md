# Field Report — Bellingcat OSINT Geolocation Methodology
**Date:** 2026-05-29
**Cycle Type:** EXPLORE
**Topic:** Bellingcat methodology, manual geolocation techniques, OSINT investigation workflows
**Sources:** OSINT Bay, StateOfSurveillance, GitHub OSINT Toolbox, Bellingcat how-tos, GeoConfirmed

---

## 1. What I Explored

I followed the thread of Bellingcat's manual geolocation methodology — the structured approach to identifying geographic locations from images and videos with no metadata, no captions, just visual evidence. This is the canonical methodology that Bellingcat formalized a decade ago and that still underpins verified war-crime investigations, journalism, and law enforcement geolocation today. I also explored the broader OSINT geolocation tool ecosystem and the community of practitioners who maintain and advance these techniques in real time.

## 2. What I Found

### The Core Methodology: Decompose, Don't Scan

The central mental model is counterintuitive to beginners: instead of scanning an image for "the answer," operators decompose it into independent features that each narrow the search space:

| Feature | What It Narrows |
|---|---|
| Architecture and roof geometry | Continent, often country |
| Vegetation type and density | Climate zone |
| Road markings and signage standards | Region |
| License-plate format, font, color | Country (and often year) |
| Electrical sockets and power-line geometry | Region |
| Language/script on signage | Country |
| Vehicle makes, models, bodywork | Confirms market |
| Sun azimuth, shadow length, time of day | Latitude |

Stack five of these and you're often inside a 5 km radius. None alone is an answer — together they form a verifiable evidence chain that holds up in court.

### The Map Stack (Layered by Purpose)

No serious geolocator runs on one tool. Each platform sees a different version of the planet:

- **Google Earth Pro** — workhorse for satellite imagery, historical layers, 3D terrain. Historical-imagery slider walks a building backwards through time; ruler measures shadow length.
- **Google Street View** — Western default; date selector is non-negotiable. A 2014 drive-past can decide a case 2023 imagery can't.
- **Yandex Maps/Panoramas** — answer for post-Soviet space. Yandex reverse image search still outperforms Google for architecture/signage matching in that region. Panorama coverage in Ukraine largely frozen around 2011.
- **Mapillary and KartaView** — crowdsourced street-level layers filling holes Google won't drive into. KartaView strong in Southeast Asia; Mapillary wherever amateur drivers have dashboard mounts.
- **Bing Maps Bird's-eye** — oblique aerial views revealing building façades straight-down satellite misses. Underused.
- **OpenStreetMap (Overpass Turbo)** — query the planet: "show me every roundabout within 30 km of this point with exactly five exits." Tags every road, hydrant, mast, bench.
- **Wikimapia** — amateur annotations, often the only place an obscure landmark is named in the local language.

### Sun, Shadows, and Geometry of Light

If you can see a shadow and guess a season, you can constrain latitude to within a few kilometers. The mechanics:
- Sun position = two angles: azimuth and elevation.
- Pick candidate location + candidate time → SunCalc returns where shadows should fall and how long.
- If image shadow points northeast at 4pm and candidate says due south → candidate dead.
- A video showing shadow rotating across a wall is its own latitude estimator (azimuth change rate varies by latitude).
- **PeakVisor**: matches horizon silhouette against 3D model of every named peak → camera pointing direction within a degree.

### The AI Layer: Triage, Not Evidence

Two tools matter; the rest is noise.
- **Picarta**: vision transformers on geo-tagged imagery → city/country-level predictions with confidence scores. Tells you in 3 seconds that image is likely Eastern Mediterranean, not Latin America.
- **GeoSpy** (Graylark Technologies): same space, marketed for law enforcement deployment.

Ground rules: AI never replaces verification — every "high confidence" hit needs satellite/panorama match before leaving draft folder. AI fails hardest in places that matter most: low-data conflict zones, rural villages, generic interiors.

### The Community: Real-Time Contact Sport

Manual geolocation work happens on X (Twitter) and Telegram in real time, frame-by-frame. Key accounts:
- **@GeoConfirmed** / @gocha — canonical conflict-geolocation aggregator, daily verified incidents
- **@bellingcat** — methodology benchmark
- **@benjaminstrick** — Bellingcat investigator/trainer, reproducible case writeups
- **@aric_toler** — long-form geolocation case studies
- **@sector035** — weekly "Week in OSINT" digest
- **@nrg8000, @hatless1der, @ericdeshazo** — puzzle-based public solutions

GeoGuessr World: top players do in 30 seconds what most analysts manage in 30 minutes.

### The Evidence Standard: GeoConfirmed Methodology

Every verification must be reproducible by anyone with a browser. The discipline that separates confirmed from "looks about right" follows Bellingcat's 2014 principle: every claim shows the evidence, every evidence chain is reproducible, every candidate location is killed before accepted. If a workflow can't survive being posted publicly with original image + satellite overlay side by side, it isn't a geolocation — it's a guess.

## 3. What I Think Is Interesting

**The methodology is a Latin verb conjugation table.** Bellingcat didn't invent most of the individual techniques — shadow analysis via SunCalc, road marking standards, license-plate font recognition. What they systematized was the *verification protocol*: decompose, constrain, eliminate, cross-verify, publish-reproducibly. This is structurally identical to scientific peer review applied to image analysis. The methodology prioritizes evidence-chain reproducibility over tool sophistication.

**The AI paradox.** Picarta and GeoSpy genuinely accelerate triage — reducing a search from 6 hours to 2 is meaningful. But they fail hardest precisely where verification matters most: conflict zones, rural areas, generic interiors. This creates a dangerous asymmetry: AI looks impressive on easy cases (solving GeoGuessr in seconds) while being useless on hard ones (verifying a war crime in a village with no Street View). The risk is that non-experts overtrust AI on hard cases because they saw it ace easy ones.

**Crowdsourced street-level imagery as a covert intelligence asset.** Mapillary and KartaView — amateur drivers with dashboard mounts — have built coverage in areas Google won't touch. This is a structural advantage for OSINT: open-licensed, globally distributed, non-corporate. It also means anyone can contribute to the global geolocation substrate, intentionally or not.

**The map stack is a multi-modal reasoning problem.** Each platform (Google, Yandex, Bing, OSM, Wikimapia) encodes the same physical world differently — different dates, different angles, different metadata. A human geolocator moving between them is performing cross-modal entity resolution: "this building in satellite view is the same as this storefront in Street View from a different year." This is structurally the same problem as resolving a corporate entity across SEC filings, OpenCorporates, and campaign finance databases — different schemas, same entity.

## 4. What I'd Explore Next

1. **Overpass Turbo + Bellingcat OSM Search Tool integration.** Build a skill that automates the "query OSM for geometric features matching a candidate location" workflow — effectively a programmatic geolocation triage assistant that returns candidate locations given a feature checklist.
2. **ShadowCalc/SunCalc automation.** A tool that takes an image timestamp estimate + shadow angle and returns constrained latitude band + candidate time windows, integrated with the map stack.
3. **GeoConfirmed incident database analysis.** Scrape/tabulate GeoConfirmed's verified incidents by region, actor, date, and geolocation method used — surface patterns: which techniques solve which types of locations?
4. **PeakVisor API integration for horizon matching.** Automate skyline silhouette → candidate camera position pipeline for mountain-region geolocation.
5. **Cross-domain: geolocation as entity resolution.** Formalize the structural equivalence between multi-map geolocation (cross-referencing Google, Yandex, Bing, OSM views of the same location) and multi-database entity resolution (cross-referencing SEC, OpenCorporates, campaign finance views of the same company). The Fellegi-Sunter probabilistic matching model applies to both.

## 5. Cross-Domain Connections

- **Entity Resolution**: Geolocation across multiple map platforms is cross-modal entity resolution. Same methodology (decompose into features, match across schemas, verify) applies to corporate registries, property records, and campaign finance.
- **Counterintelligence Analysis**: The verification protocol (every claim shows evidence, every evidence chain is reproducible, every candidate eliminated before acceptance) is structurally CI Analysis of Competing Hypotheses (ACH) applied to images instead of threats.
- **AI Agent Architecture**: The decomposition-first approach (break image into checklist of independent features, each narrows search space) mirrors the Exocortex multi-tool decomposition pattern: break task into subtasks, each tool narrows solution space.
- **Local-to-Frontier Model Cascade**: Picarta/GeoSpy as triage (fast, coarse, local model) → human verification with Google Earth/Yandex (slow, precise, frontier model) is structurally the same cascade architecture as local LLM pre-processing → frontier model reasoning.
- **Multi-Modal Reasoning**: Human geolocators moving between satellite, street-level, oblique aerial, and crowdsourced imagery are performing multi-modal reasoning across representations of the same physical entity — structurally identical to AI systems that reason across text, images, and structured data.
