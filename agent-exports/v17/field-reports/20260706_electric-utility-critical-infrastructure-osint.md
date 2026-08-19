# Field Report: Electric Utility & Critical Infrastructure OSINT
**Date:** 2026-07-06  
**Cycle:** EXPLORE  
**Topic slug:** electric-utility-critical-infrastructure-osint

---

## 1. What I explored

Electric utility and critical infrastructure is a top-level interest in Jake's registry with zero prior exploration — no wiki page, no field report, no journal mentions. This cycle drilled into the open-source intelligence (OSINT) techniques available for mapping and analyzing electric grid infrastructure using only public data.

The exploration thread: given heterogeneous public datasets (EIA, FERC, NERC, OpenStreetMap), how can an analyst resolve entities across them to map ownership, assess vulnerabilities, and detect anomalies in the bulk power system?

---

## 2. What I found

### Core open data portals
- **U.S. Energy Information Administration (EIA)** — [Electricity Data Browser](https://www.eia.gov/electricity/data.php): generation, consumption, emissions, power plant operations, grid monitor, and state-level overviews. Direct API access for programmatic querying.
- **Federal Energy Regulatory Commission (FERC)** — dockets, orders, and enforcement actions on reliability standards violations. The "Find, Fix, Track, and Report" (FFTR) process streamlines lesser-risk violations, giving public visibility into compliance gaps.
- **North American Electric Reliability Corporation (NERC)** — reliability standards, compliance reports, and disturbance analyses. Regional Entities publish annual reports on grid health.

### OSINT mapping tools
- **OpenInfrastructureMap** (openinframap.org): Global map of power plants, substations, transmission lines, telecoms, oil/gas pipelines — all from OpenStreetMap data. Free, no API key needed.
- **OpenGridWorks** (opengridworks.com): Dedicated power infrastructure map with Power Plant, Substation, Transmission Line, and Telecommunications layers. Exports KML for Google Earth overlay.
- **Submarine Cable Map** (submarinecablemap.com): Fiber-optic cable landing points worldwide; critical for understanding internet backbone dependencies tied to physical grid infrastructure.
- **FiberLocator** (fiberlocator.com): Commercial-grade fiber route mapping (free tier available) — useful for tracing telecom corridors that co-locate with transmission rights-of-way.

### Methodology from Undercode Testing (2025)
A professional OSINT workflow for critical infrastructure mapping was documented by Undercode Testing:
1. **Layered mapping**: Overlay power plant, substation, transmission line, and telecom layers within a defined radius (5–10 km) of a target location.
2. **CLI network intelligence**: Use `whois`, `traceroute -A`, `mtr`, and `peeringdb` queries to map IP ranges to physical data center infrastructure, revealing co-location of grid and internet nodes.
3. **Satellite cross-referencing**: Export KML overlays to Google Earth Pro; use historical imagery and Sentinel Hub false-color (SWIR for heat detection) to verify substation condition, transformer presence, burn marks, or new construction.
4. **Fiber route validation**: Cross-reference transmission line corridors with submarine cable landing points and FiberLocator routes; correlate ISP-reported fiber cuts with physical infrastructure clusters.
5. **Python automation**: Scripted bbox queries against infrastructure APIs, combining with `geopy` and `requests` for batch collection across regions.

### Academic validation
A 2024 paper in *Computers & Security* ("Fostering security research in the energy sector: A validation of open data") confirmed that OSINT-based approaches can construct valid models of real-world power grids, independent of operator cooperation — enabling security research without privileged access. This is the foundational academic imprimatur for the methodology.

---

## 3. What I think is interesting

**The grid is accidentally transparent.** Unlike financial data or personal records, electric utility infrastructure coordinates, capacities, and ownership structures are published for regulatory and operational reasons — and they become de facto intelligence assets when cross-referenced.

Three insights:

1. **Entity resolution is the bottleneck.** EIA, FERC, and OpenStreetMap use different naming conventions for the same power plant. A 500 MW gas plant might appear as "Big River Generating Station" (EIA), "Big River Energy Center" (OpenStreetMap), and under a holding company LLC (FERC ownership filings). Resolving these to a single entity is the same problem Jake is interested in for campaign finance/lobbying data — the techniques transfer directly.

2. **Substation morphology is a learnable OSINT signal.** In satellite imagery, substations have distinctive transformer arrays, bus configurations, and switchyard layouts. An analyst who learns these patterns can classify infrastructure by function (distribution vs. transmission substation, step-up vs. step-down) without labels — enabling rapid mapping in data-poor regions.

3. **Fiber-grid co-location is a dual-use vulnerability.** Telecom fiber routes overwhelmingly follow transmission line rights-of-way (shared easements, lower cost). This means a single physical event (wildfire, sabotage, equipment failure) can simultaneously knock out power AND internet — and this co-dependency is observable from public maps alone. Mapping these intersections produces a heatmap of single-point-of-failure clusters.

---

## 4. What I'd explore next

- **Ownership concentration analysis**: Scrape EIA plant data, FERC ownership filings (e-Forms 1, 556), and corporate registries to build a graph of which holding companies control how much generating capacity in which ISOs/RTOs. This surfaces monopoly risk and acquisition patterns.
- **Grid-resilience event correlation**: Cross-reference NERC disturbance reports with news archives and satellite imagery (Sentinel-1 SAR for flood/damage detection) to build a labeled dataset of infrastructure failures — useful for predictive modeling.
- **International extension**: Apply the same OSINT methodology to the European ENTSO-E transparency platform and the Indian CEA grid data — compare data availability and entity resolution challenges across jurisdictions.
- **Substation classification model**: Train a computer vision model (YOLO/ResNet fine-tuned on satellite imagery) to detect and classify substation types from aerial imagery, using OpenStreetMap labels as weak supervision.

---

## 5. Cross-domain connections

| Domain | Connection |
|--------|-----------|
| **Data Aggregation & Entity Resolution** | Core technique: resolving EIA/FERC/OSM identifiers to single entities is the same challenge as campaign finance/lobbying disclosure resolution |
| **Satellite Imagery OSINT** | Substation morphology classification and event damage verification use the same Sentinel Hub/Google Earth workflows already explored for conflict zone analysis |
| **DNS/WHOIS & Network Investigation** | Fiber route tracing with `whois`, `traceroute`, and PeeringDB uses identical CLI tools to the email header / IP tracing methods already documented |
| **Agentic Software Development** | Automating the bbox collection + entity resolution + map overlay pipeline would be a strong candidate for agent-coordinated tool development |
| **Privacy & Cryptography** | Understanding infrastructure topology is prerequisite to analyzing metadata-resistant communication — where traffic flows reveals what can be surveilled |
| **History of Intelligence Operations** | The "infrastructure as intelligence target" doctrine dates to WWII strategic bombing surveys; modern OSINT is the civilian continuation of this lineage |
| **Bridging Local-to-Frontier Models** | Substation classification from satellite imagery is a well-scoped computer vision task ideal for benchmarking local model performance against frontier models |

---

*This is the first exploration of this interest. A BUILD cycle should deepen this into a wiki page with primary sources from EIA documentation, the Computers & Security paper, and the Undercode Testing methodology.*
