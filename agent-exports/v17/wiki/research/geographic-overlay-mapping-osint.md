# Geographic Overlay Mapping for OSINT Investigation

**Status:** STABLE
**Created:** 2026-08-04
**Last Updated:** 2026-08-04

## Summary

Geographic overlay mapping is the practice of placing entities, events, and evidence onto a geospatial base map so that physical-space relationships become visible. It is the spatial presentation layer of OSINT: geolocation determines *where* something is; overlay mapping links those determined locations with thematic layers (points, routes, heatmaps, historical imagery, infrastructure networks) to reveal clustering, movement, hidden adjacency, and change over time. This page deepens the geographic-overlay subsection of the parent page [[visualization-techniques-osint]] into a standalone workflow, grounded in the shared Exocortex corpus (Bellingcat map stack, Kepler.gl/QGIS tooling, IP geolocation uncertainty research) and the 2026 geospatial-AI frontier.

## 1. Geographic Overlay Mapping Fundamentals

### 1.1 What Overlay Mapping Adds Over Raw Geolocation

- **Geolocation** answers "where is X?" via EXIF GPS, IP geolocation, image geolocation, Wi-Fi/BTS triangulation, AIS/ADS-B positions.
- **Overlay mapping** answers "what is near X?", "how do entities relate in physical space?", and "how did the spatial picture change over time?".
- The relationship mirrors entity resolution: overlay mapping turns resolved coordinates into a spatial graph the analyst can interrogate visually.

### 1.2 Coordinate Systems and Projections

| System | Use in OSINT |
|--------|--------------|
| WGS84 / EPSG:4326 | Standard lat/lon for GPS, GeoJSON, most web tools |
| Web Mercator / EPSG:3857 | Default tile projection for web maps (Leaflet, MapLibre, Kepler.gl) |
| UTM / MGRS | Grid precision for high-accuracy field work and target coordination |
| Regional projections (NAD83, ETRS89) | Local GIS standards for registry and cadastral data |

Coordinate uncertainty is inherited from the source: consumer GPS (2-10 m), geocoded addresses (often block-level), IP geolocation (fixed 3-16 km, mobile 179-207 km; see [[ip-address-geolocation]]), and image-derived coordinates (highly variable).

### 1.3 Data Models for Overlays

- **Point layers** — entities: addresses, facilities, sensor nodes, photo locations
- **Line layers** — routes: AIS tracks, ADS-B flight paths, supply chains, pipelines
- **Polygon layers** — boundaries: jurisdictions, service areas, exclusion zones, storage tank farms
- **Raster layers** — satellite/aerial imagery, elevation, heatmaps
- **Vector tiles / interactive basemaps** — scalable web mapping layers
- **3D layers** — CesiumJS terrain and building models

## 2. Tool Ecosystem (2026)

### 2.1 Desktop GIS

| Tool | Notes |
|------|-------|
| QGIS | Open-source standard; OSM, geocoding, XYZ tiles, temporal controller |
| ArcGIS / ArcGIS Online | Esri commercial stack; AGOL shared web maps |
| Google Earth Pro | Free; historical imagery slider, measurement, KML export |
| GRASS GIS | Advanced raster/vector analysis and change detection |

### 2.2 Web and GPU Mapping

| Tool | Notes |
|------|-------|
| Kepler.gl | Uber open-source GPU-accelerated mapping; point clouds, arc layers, hexbins |
| MapLibre GL JS | Open-source fork of Mapbox GL; vector tiles, custom layers |
| Leaflet | Lightweight JS library with GeoJSON/CSV, heatmap, OSM basemap extensions |
| CesiumJS | 3D globe, terrain, time-dynamic visualization |
| OpenLayers | Full-featured web GIS library |

### 2.3 Python / Notebook Stack

- **GeoPandas** — vector dataframes, spatial joins, overlay operations
- **OSMnx** — OpenStreetMap street networks and building footprints (Boeing 2017)
- **Folium / Plotly** — quick interactive Leaflet/Mapbox maps
- **Deck.gl / pydeck** — GPU layers for large point sets
- **rasterio / satpy** — raster processing and satellite data

### 2.4 OSINT-Specific Tools

- **Bellingcat Map Stack** — Google Earth, Yandex Maps, Bing, Mapillary, OSM, Wikimapia, PeakVisor ([[bellingcat-osint-methodology]])
- **PANO** — open-source integrated investigation platform combining graph, timeline, and map views with AI entity extraction (corpus memory, 2025)
- **Maltego** — graph link analysis with geolocation transforms and map views

### 2.5 Street-Level and Historical Imagery

- Mapillary / KartaView — crowdsourced street-level imagery with view direction and timestamps
- Google Street View Time Machine / Yandex Panoramas — historical street scenes
- USGS topoView — historical topographic maps
- Esri Wayback Living Atlas / Google Earth historical imagery — time-series satellite imagery

## 3. Core OSINT Use Cases

1. **Entity spatial resolution** — overlay corporate registries, property records, campaign finance addresses to find shared facilities, shell-company clusters, and geographically hidden associations (see [[corporate-registry-investigation-osint]], [[property-records-tax-assessor-osint]]).
2. **Event incident mapping** — geolocate protest videos, attack photos, sensor reports; overlay timestamps to reconstruct event footprints over time ([[timeline-reconstruction-osint]]).
3. **Route and movement reconstruction** — overlay AIS vessel tracks, ADS-B flights, vehicle movement to detect shadowing, ship-to-ship transfer, and sanctions evasion ([[aircraft-flight-tracking-osint]], [[satellite-imagery-osint]]).
4. **Supply chain and infrastructure networks** — map production sites, ports, pipelines, storage to identify chokepoints and concentration risk ([[supply-chain-network-analysis-osint]], [[energy-commodity-dynamics]]).
5. **Discrepancy and deception detection** — compare claimed locations (HQ, factory, military base) with imagery and street-level evidence; detect spoofed EXIF, map laundering, and coordinate manipulation.
6. **Temporal change detection** — compare historical imagery for construction timelines, storage levels, port congestion, covert expansion ([[satellite-imagery-osint]]).
7. **Real-time alerting** — stream geolocated events onto a live map for monitoring and early warning ([[real-time-osint-monitoring-alerting]]).


## 4. End-to-End Overlay Mapping Workflow

### 4.1 Collect and Normalize Geospatial Inputs

1. **Extract coordinates** — EXIF GPS, social media geotags, AIS/ADS-B positions, satellite imagery annotations.
2. **Geocode textual locations** — registries, news reports, incident descriptions via OSM Nominatim or commercial geocoders; record confidence and match granularity.
3. **Normalize** — convert all coordinates to WGS84 (EPSG:4326), unify timestamps to ISO 8601 UTC, and standardize place names using the same regional gazetteer.
4. **Build the feature table** — each overlay point carries source, extraction method, acquisition timestamp, and coordinate uncertainty radius.

### 4.2 Analyze Overlays

- **Spatial joins and buffers** — find entities within a defined radius of infrastructure, addresses, or known facilities; surface colocation anomalies.
- **Layered thematic maps** — combine corporate registries, property records, trade data, and public infrastructure into one visual space (the core of [[corporate-registry-investigation-osint]]).
- **Temporal mapping** — animate time-stamped points to reveal movement, convoy behavior, or event cascades ([[timeline-reconstruction-osint]]).
- **Density and clustering** — hexbin or kernel-density layers for high-volume events such as protest detections or vessel call data.
- **Network-over-space** — draw graph edges over a map to connect entities via shared facilities or co-occurrence ([[network-analysis-techniques-osint]]).

### 4.3 Verify and Preserve

- Apply the Bellingcat two-source rule: confirm a photo or event location with at least two independent data points ([[bellingcat-osint-methodology]]).
- Cross-check against street-level imagery (Mapillary, KartaView, Street View Time Machine) and historical imagery.
- Draw uncertainty as error ellipses/radii instead of exact pins when the source is IP geolocation, geocoded address matching, or low-quality imagery.
- Record provenance for every layer so the chain of custody remains intact ([[evidence-preservation-chain-of-custody-osint]]).

## 5. 2026 State of the Art: Geospatial AI for OSINT

Geospatial AI is moving from niche remote sensing into standard OSINT tooling. The most widely applied techniques in 2026:

| Technique | OSINT Overlay Use |
|-----------|-------------------|
| Object detection in satellite imagery | Identify buildings, vehicles, infrastructure in free imagery (EOS, Sentinel, PlanetScope) |
| Semantic segmentation | Classify land cover; detect new construction, expansion, or environmental change |
| Change detection | Compare imagery dates to spot covert construction, storage buildup, port congestion |
| Predictive spatial modeling | Forecast where events (protest clusters, smuggling transshipment) are likely |

- **Planet Labs** advertises low-latency daily imagery for early change detection — an analyst can now query "what changed here this week?" as routine.
- **Esri/ArcGIS** combines spatial analysis, image analysis, and AI, handling street-level, drone, aircraft, and satellite sensors in one system, lowering the barrier for overlay fusion.
- **Evermx GeoAI** (JOSS 2026) is an open-source Python package bridging AI and geospatial data with satellite image segmentation, object detection, change detection, and QGIS integration — directly usable in an OSINT notebook stack.
- **EOS LandViewer** provides free access to open-data satellite imagery catalogs, making multitemporal comparison accessible to low-budget investigations.
- **Off-Nadir Delta** frames modern geospatial OSINT as building intelligence about places and events from public sources — news signals, free satellite imagery, AIS, geotagged media — by geolocating then overlaying heterogeneous signals.
- **Yenra 2026** frames the shift as geospatial analysis sitting at the intersection of imagery, maps, sensors, and location-aware decisions: overlay mapping is becoming the default analytical surface rather than a final illustration step.

### 5.1 Ground Truth and Accuracy Constraints

- IP geolocation remains unreliable for precise overlay: mobile networks can be off by 179–207 km vs 3–16 km for fixed lines, and Global South coverage fails 66–72% of the time (Nabi et al. 2026, arXiv:2605.21937; see [[ip-address-geolocation]]).
- LLM-based geolocation (GeoCLIP, PIGEON, Bellingcat 2026 evaluations) is an assistive narrowing tool, not a location oracle; images must still be confirmed against the map stack.
- Free imagery resolution varies by provider (Sentinel ~10 m, Landsat ~15–30 m, PlanetScope ~3 m); overlay precision must be pitched to the coarsest input layer.

## 6. Anti-Deception, Uncertainty, and Evasion

Overlay mapping is also an adversarial surface. Entities actively manipulate coordinates:

- **EXIF stripping/spoofing** — remove or alter GPS metadata; defenders use shadow analysis and location fingerprinting ([[geolocation-osint]]).
- **Map laundering** — falsely claiming a business/vessel location via virtual offices; overlay registries against observed imagery to detect divergence.
- **AIS spoofing/off** — vessels disabling transponders near sanctioned ports; overlay AIS gaps with satellite AIS and radar imagery ([[satellite-imagery-osint]]).
- **Deepfake/geotag laundering** — synthetic media with planted coordinates; verify via chronolocation and independent physical cues.

Uncertainty handling: every layer should carry a per-point confidence/uncertainty radius, and sensitivity analysis should show how conclusions change when low-confidence points are removed.

## 7. Exocortex Integration Architecture

- **Agentic pipeline**: geolocation extraction (image, IP, text) → entity resolution → overlay mapping → temporal analysis → alerting.
- **Map layers as evidence objects**: each geospatial layer is an evidence ledger item with source, timestamp, extraction method, and hash, aligning with epistemic integrity.
- **Real-time monitoring**: geolocated events stream onto live overlay maps for early warning and escalation ([[real-time-osint-monitoring-alerting]]).
- **Knowledge graph integration**: spatial joins become edges in the entity-resolution graph, extending [[network-analysis-techniques-osint]] with a "co-location" predicate.
- **Privacy-preserving overlay**: when handling personal location data, apply the privacy-preserving entity resolution approach (ε-DP, PPRL) before publishing overlays ([[privacy-preserving-entity-resolution-osint]]).

## 8. Cross-Domain Connections

| Wiki Page | Connection |
|-----------|------------|
| [[visualization-techniques-osint]] | Parent page: overlay mapping is the spatial presentation layer with graph/timeline modes |
| [[geolocation-osint]] | Input layer: image and IP geolocation determines point positions |
| [[ip-address-geolocation]] | Uncertainty quantification for IP-derived coordinates |
| [[satellite-imagery-osint]] | Raster base layers and change detection feeds |
| [[timeline-reconstruction-osint]] | Temporal dimension over spatial overlay |
| [[force-directed-graph-layouts-osint]] | Graph-over-space: connecting entities by proximity |
| [[bellingcat-osint-methodology]] | Verification workflow and map stack |
| [[corporate-registry-investigation-osint]] | Address geocoding for entity spatial resolution |
| [[real-time-osint-monitoring-alerting]] | Live event streaming onto maps |
| [[evidence-preservation-chain-of-custody-osint]] | Provenance for each overlay layer |
| [[digital-twin-critical-infrastructure]] | Physical-grid overlays for infrastructure investigations |
| [[privacy-preserving-entity-resolution-osint]] | Privacy governor for personal location data |

## 9. References

1. GeoSpan (2026). *Geospatial AI: How Machine Learning Is Transforming GIS Analysis in 2026*. https://geospan.org/blog/geospatial-ai-how-machine-learning-is-transforming-gis-analysis-in-2026/
2. EOS Data Analytics (2026). *Free Satellite Imagery: 2026 Data Providers & Sources*. https://eos.com/blog/free-satellite-imagery-sources/
3. Evermx (2026). *GeoAI — Open Source AI Project*, Journal of Open Source Software. https://evermx.com/open-source/geoai-geospatial-artificial-intelligence
4. Planet Labs (2026). *Satellite Data for Geospatial Intelligence*. https://www.planet.com/geospatial-intelligence/
5. Esri (2026). *Image Analysis & Change Detection*. https://www.esri.com/en-us/capabilities/imagery-remote-sensing/capabilities/analysis
6. Off-Nadir Delta (2026). *Satellite Imagery Insights & Tutorials*. https://offnadir-delta.com/blog
7. Yenra (2026). *AI Geospatial Analysis: 10 Advances (2026)*. https://yenra.com/ai-tech/geospatial-analysis/
8. Nabi et al. (2026). *IP Geolocation accuracy*. arXiv:2605.21937 (cited via [[ip-address-geolocation]]).
9. Boeing, G. (2017). *OSMnx: New Methods for Acquiring, Constructing, Analyzing, and Visualizing Complex Street Networks*. Computers, Environment and Urban Systems. https://arxiv.org/abs/1611.01875
10. Uber Visualization. *Kepler.gl: Open-Source Geospatial Analysis Tool*. https://kepler.gl/
11. QGIS Project. *QGIS — A Free and Open Source Geographic Information System*. https://qgis.org/
12. Förster, H., Klesen, F., Dwyer, T., et al. (2024). *GraphTrials: Visual Proofs of Graph Properties*. arXiv:2409.02907.
13. Bellingcat (2026). *Online Investigation Toolkit* (map stack methodology), via [[bellingcat-osint-methodology]].
14. PANO (2025). *Advanced OSINT Investigation Platform*. https://github.com/ALW1EZ/PANO

## Verification Status

- **Corpus-first grounding**: memory_load of Exocortex shared corpus (OSINT visualization, Bellingcat geolocation, IP geolocation, PANO platform) plus greps of wiki/research for Kepler.gl/QGIS/map overlay/Bellingcat map stack. Strong local grounding.
- **Library**: the 355-book reference library tools were not reachable in this session; technical claims are grounded in corpus and web primary/secondary sources (honest gap).
- **Web gap-fill**: 2026 geospatial AI state-of-the-art from GeoSpan, EOS, Evermx JOSS, Planet, Esri, Off-Nadir Delta, Yenra. Reported as vendor/authoritative-blog claims, not laboratory-verified.
- **Status change**: DRAFT → STABLE after meeting deepening threshold (205 lines, 12 cross-domain connections, 14 references).

## 10. Maintenance Guidance

- Re-verify overlay tool and free imagery sources quarterly; catalogs and APIs change quickly.
- When new geolocation or satellite-imagery pages are produced, update the cross-domain links here.
- Treat the Bellingcat two-source rule as the hard verification floor for every pinned location.
- For Exocortex agent deployments, keep per-layer uncertainty radii and provenance hashes as first-class fields.
