# OSINT Tradecraft: Bellingcat Geolocation Methodology and Evolution

**Date:** 2026-06-05  
**Cycle:** EXPLORE  
**Interest:** OSINT & Investigation Methodology  
**Sub-topic:** Geolocation techniques, social media forensics, timeline reconstruction

---

## 1. What I Explored

I traced the evolution of Bellingcat's geolocation methodology from Eliot Higgins' 2014 beginner's guide through to the June 2025 landmark LLM geolocation evaluation. The thread examined how open-source investigators authenticate videos, pinpoint locations, and reconstruct timelines using public tools and, increasingly, large language models.

Sources:
- Higgins, E. (2014) "A Beginner's Guide to Geolocating Videos"
- Bellingcat (2015) "Searching the Earth: Essential Geolocation Tools"
- Bellingcat (2023) "Finding Geolocation Leads with OpenStreetMap Search Tool"
- Bellingcat (2024) "Tracking Your Search: Grid Generator"
- Bellingcat (2025) "Have LLMs Finally Mastered Geolocation?" (Foeke Postma & Nathan Patin)
- Bellingcat Wikipedia page
- Breitinger et al. (2025) "SoK: Timeline-based event reconstruction for digital forensics" (ScienceDirect)

## 2. What I Found

### 2.1 Core Methodology (Higgins, 2014)

Bellingcat's foundational geolocation technique follows a reproducible workflow:

1. **Landmark identification**: Spot distinctive features — minarets, road medians, building shapes, signage, vegetation types.
2. **Satellite imagery cross-referencing**: Wikimapia (multi-source: Google, Bing, Yahoo maps) used to find candidate locations. The example of Tiji, Libya demonstrated road width matching (two tanks wide) and minaret orientation to conclusively geolocate a video.
3. **Road pattern sketching**: For featureless urban areas (e.g., Brega, Libya), the cameraman's movement path is traced on MS Paint to create a road network sketch, then matched against satellite imagery of residential zones. This spatial pattern-matching succeeded where landmark identification failed.
4. **Shadow analysis**: SunCalc is used to chronolocate a photo by shadow angle and length, establishing time of day without metadata.

### 2.2 Tools Ecosystem (2024-2025)

- **OpenStreetMap Search Tool** (2023): Bellingcat built a custom search interface over OSM data, querying by tags (building=yes, highway=primary) to narrow candidate locations.
- **Search Grid Generator** (2024): Divides search area into a grid, preventing redundant searches and enabling team collaboration. Each square assigned to an investigator.
- **Google Lens** (comparative baseline): Traditional reverse image search remains competitive for landmark-heavy images.

### 2.3 LLM Geolocation Evaluation (June 2025)

Bellingcat ran 500 blind tests (20 models × 25 unpublished travel photos) covering all continents. Key findings:

| Model | Performance | Notable |
|-------|------------|---------|
| ChatGPT o4-mini-high | **Best overall** | Outperformed Google Lens; excellent at fine details |
| ChatGPT o3 | Top tier | Strong visual reasoning |
| Claude Opus 4.0 | Strong | Good at architectural style identification |
| Gemini 2.5 Pro | Strong | Multilingual signage advantage |
| Grok 3 DeepSearch | Moderate | Prone to overconfident errors |
| Claude Haiku 3.5 | Weak | Highest hallucination rate |

**Critical insight**: LLMs excel at multilingual clue extraction (Cyrillic signage, regional vegetation) that reverse image search cannot match. However, they remain prone to hallucination; deep research modes did not consistently improve accuracy — the model's base reasoning capability mattered more.

### 2.4 Timeline Reconstruction

The systematic chronolocation chain: shadow analysis (SunCalc) → image metadata (if available) → video frame sequencing → satellite image temporal comparison. Breitinger et al. (2025) propose a unified framework harmonizing event reconstruction terminology, identifying the four-phase model: collection, examination, analysis, and reporting.

## 3. What I Think Is Interesting

**The two-layer verification pattern**: Bellingcat's methodology structurally mirrors the Exocortex architecture. Deterministic scaffolding (GIS tools, satellite imagery, road pattern matching) provides hard facts; LLM reasoning layers interpret nuance (multilingual text, vegetation inference). This is not LLM replacing OSINT — it is LLM extending it.

**LLMs are best as tool-using investigators, not oracles**. The 2025 evaluation showed that even top LLMs fail at standalone geolocation (~40-60% accuracy on difficult images). But when used to augment systematic human workflows — noticing a street sign the analyst missed, translating Arabic script, identifying a tree species — they dramatically accelerate the investigation.

**The hallucination pattern mirrors injection gate risk**: LLMs will confidently assert wrong locations with plausible reasoning. The epistemic firewall needed for geolocation LLMs is the same problem as the Exocortex injection gate: a fact-checking layer that separately verifies LLM output against ground truth.

## 4. What I'd Explore Next

- **Automated geolocation pipelines**: Combining Google Earth Engine API + OSM data + LLM tool use in an agentic loop for first-pass location narrowing.
- **Temporal reconstruction with LLMs**: Can LLMs sequence events from multiple video sources without explicit timestamps? This is timeline reconstruction as a reasoning problem.
- **Adversarial geolocation countermeasures**: Image manipulation designed to mislead LLM geolocators (altered signage, shadow manipulation). Are current models robust?
- **Bridging to Exocortex**: Building a `geolocate` tool that leverages the OSM search tool + LLM reasoning as an MCP tool for the agent.

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| **AI Agent Architecture** | Two-layer verification (tool → LLM interpretation) is the Exocortex pattern. The LLM geolocation test provides empirical evidence for why agents need tool access, not just reasoning. |
| **Data Aggregation & Entity Resolution** | Geolocation is entity resolution for places — resolving a visual observation to a known location in a GIS database. The pattern-matching methodology (landmarks, road shapes) parallels Fellegi-Sunter probabilistic matching. |
| **Markets & Financial Analysis** | Supply chain verification increasingly uses geolocation to audit factory locations and shipping manifests. This is alternative data with spatial verification. |
| **Privacy & Cryptography** | Image metadata stripping defeats basic geolocation; shadow analysis and LLM visual reasoning defeat metadata stripping. The arms race continues. |
| **History of Intelligence Operations** | Photo interpretation tradecraft (WWII aerial recon → Cold War satellite imagery → modern OSINT geolocation) follows a continuous methodological lineage. The human-in-the-loop reasoning step persists across eras. |
| **Bridging Local-to-Frontier Performance** | Local LLM models (Qwen3.6-27B on RTX 3090) could run geolocation analysis locally, preserving privacy for sensitive OSINT investigations. The RTX 3090 DFlash/PFlash optimizations are directly applicable. |

---

*Sources saved from this cycle: Higgins (2014), Bellingcat (2023, 2024, 2025), Wikipedia, Breitinger et al. (2025).*
