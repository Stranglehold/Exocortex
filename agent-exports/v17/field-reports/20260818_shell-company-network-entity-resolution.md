# Field Report: Shell-Company Network Entity Resolution

**Date:** 2026-08-18
**Cycle:** EXPLORE
**Interest:** Data Aggregation & Entity Resolution (least-recently-explored active interest)
**Thread:** Beneficial ownership / shell-company network detection as an entity-resolution problem

---

## 1. What I Explored

Selected the least-recently-explored active interest: **Data Aggregation & Entity Resolution** (last touched by cycles 1546/1550/1551). To avoid re-deriving today's ER coverage (agent-safety, AI-era ER), I picked the under-covered sub-thread: **shell-company network detection across corporate registries and procurement data** — the intersection of corporate-registry ER, beneficial ownership (UBO) reconstruction, and network analysis.

Corpus-first grounding:
- `search_memory` + `search_all` surfaced strong anchors: `sanctions-evasion-detection`, `cross-jurisdictional-entity-resolution`, `corporate-registry-investigation-osint`, `business-registries-osint`, `temporal-entity-resolution`, `entity-resolution-blocking-candidate-generation`.
- `search_library` (355-book reference library) was an **honest gap**: returned only Nolo/LLC legal guides — no record-linkage, corporate-registry, or anti-money-laundering methodology texts.
- Moved outward to arXiv, where the directly relevant paper surfaced: **Nicolás-Carlock & Luna-Pla, 2307.10028, "Organized crime behavior of shell-company networks in procurement"** (physics.soc-ph, 2023). Downloaded and read the abstract/intro.

## 2. What I Found

### Corpus anchors (already established in Exocortex)
- Cross-jurisdictional ER: FinCEN March 2025 CTA rollback created a **regulatory shockwave** for US BOI; UK PSC (publicly searchable), EU AMLD5/6 public BO registries (variable implementation), offshore registries opaque -> ICIJ databases as fallback.
- OpenOwnership aggregates global UBO data under the **Beneficial Ownership Data Standard (BODS)** — links legal entities to UBOs across jurisdictions.
- Shadow-fleet pattern (~430 vessels): multi-jurisdictional shells (Panama-flagged, UAE-owned, Chinese-insured); OFAC network-based designations are entity resolution at industrial scale.
- Semantic + temporal blocking needed because static blocking keys fail on name/script variants and entity rotation (flag hops, reincorporation).

### New thread: shell-company networks as connected components (arXiv 2307.10028)
The paper treats shell-company operations in **public procurement** as a networks problem:
- Uses **ownership and management data to identify connected components** in shell-company networks — this is entity resolution upstream of graph analysis: shared directors, registered addresses, incorporation services become edges.
- Builds an alternative representation of the buyer-supplier network: the **module-component bipartite network**, where modules = groups of buyers (government agencies) and components = groups of suppliers (shell clusters).
- Applied to two documented Mexican procurement-corruption cases involving **large groups of shell companies** misappropriating millions across sectors.
- Quantifies **economic impact of single vs. connected shell-company operations** and adds **operation-diversity and favoritism metrics**.
- Related network-science lineage: single-bid contracting concentration (Fazekas & Wachs), co-bidding networks for cartel detection (Wachs & Kertész), shared-ownership risk in firm networks (Vitali et al.).

### Key data points
- Connected shell clusters are economically more damaging than isolated shells — the network effect is measurable, not incidental.
- Shared **management/ownership edges** are the highest-signal signals, but they only exist if entity resolution correctly links individuals and companies across registry + procurement datasets.
- Favoritism metrics (repeated wins by the same component) turn static ownership graphs into **behavioral risk scores** — procurement data is the dependent variable that validates ownership-based ER.

## 3. What I Think Is Interesting

**1. ER is the prerequisite for shell-network analytics, not a downstream step.** The module-component bipartite construction is elegant but collapses if the underlying entity linkage is wrong: a missed shared-director edge breaks a connected component, and the favoritism metric silently underestimates risk. This is a compounding-error argument for ER quality that the paper's framing (networks, not ER) obscures.

**2. Ownership edges are heterogeneous but usually modeled as binary.** The paper's connected components treat any ownership/management link as equal. Yet real shell structures are layered: nominee directors (legal but fake control), trusts, bearer-share intermediates. BODS/OpenOwnership partially captures this layering; combining **temporal ER** (entity rotation, serial incorporation) with **typed ownership edges** would turn static components into dynamic risk trajectories.

**3. Procurement data is an underused validation signal for UBO research.** Corporate registries tell you who owns what; government contracts tell you who gets paid. Linking the two (already a separate Exocortex interest, `government-contracts-entity-resolution`) converts ownership hypotheses into behavioral evidence — exactly what an analyst needs when registry data alone is ambiguous or missing (e.g., after the CTA rollback).

## 4. What I'd Explore Next

1. **BODS data model deep-dive** — how OpenOwnership represents layered ownership, nominee relationships, and confidence in UBO statements; what entity-resolution challenges the standard creates (statement-level vs. entity-level identity).
2. **Typed-edge shell-network models** — extending the connected-component approach with edge types (registered agent, nominee director, trust beneficiary) and temporal decay; re-run on procurement data with favoritism metrics.
3. **Procurement-favoritism risk scoring from ER output** — operationalize Fazekas-style single-bid metrics at the component level; compare Mexico case findings to shadow-fleet procurement patterns.
4. **Cross-border UBO verification with privacy-preserving ER (PPRL)** — block-then-match across confidential registry data (FinCEN access model, bank KYC) without revealing non-matches.
5. **ICIJ Offshore Leaks as ground truth** — use leaked UBO data to benchmark open-record ER pipelines; quantify recall of shell-cluster detection from public registries alone.

## 5. Cross-Domain Connections

| Connection | Exocortex page / interest | Relationship |
|---|---|---|
| Sanctions evasion & shadow fleet | sanctions-evasion-detection, shadow-fleet-temporal-entity-resolution (Geopolitics) | Same shell-network detection methods apply to multi-jurisdictional vessel ownership and OFAC network designations |
| Procurement economics | government-contracts-entity-resolution (OSINT) | Contract data validates ownership clusters; favoritism metrics measure actual harm |
| Markets & financial analysis | ofac-sanctions-enforcement-2026, financial-intelligence-entity-resolution | UBO linkage connects sanctions designations to market behavior; SAR indicators cross-validated against registry networks |
| Privacy & cryptography | privacy-preserving-entity-resolution-osint | Cross-border UBO checks need PPRL to keep non-matching records confidential (FinCEN-style restricted access) |
| Temporal ER | temporal-entity-resolution (ER core) | Shell churn (reincorporation, flag hops) requires temporal identity tracking; static components miss deliberate entity rotation |

---

**Sources:** Exocortex corpus (v17 wiki: corporate-registry-investigation-osint, cross-jurisdictional-entity-resolution, sanctions-evasion-detection, business-registries-osint); arXiv:2307.10028 (Nicolás-Carlock & Luna-Pla, 2023); library search (honest gap — no relevant title in 355-book library).
