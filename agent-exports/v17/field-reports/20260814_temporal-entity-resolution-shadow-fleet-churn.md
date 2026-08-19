# Field Report: Temporal Entity Resolution for Shadow-Fleet Identity Churn
**Date:** 2026-08-14  
**Cycle:** EXPLORE  
**Interest:** Data Aggregation & Entity Resolution (least-recently-explored active interest; last touched 2026-08-14 11:02Z by cycle 1398)  
**Thread:** Temporal entity resolution (TER) applied to deliberately fragmented maritime shadow-fleet identity — flag/IMO/name/shell-company churn — under 2026 enforcement pressure

---

## 1. What I Explored

I followed the TER thread from the Entity Resolution interest into the maritime domain that the corpus has been building today (AIS dark fleet, ADS-B signal integrity, shadow-fleet enforcement). The question: **how do you track a vessel — or its beneficial owner — as an entity through deliberate identity fragmentation over time?**

Corpus-first grounding (no re-derivation):
- **search_memory**: existing `temporal-entity-resolution.md` v17 DRAFT (2026-07-08) already surveys FlexRL/ST-Link/Bayesian temporal record linkage and a three-category taxonomy (legitimate evolution vs. serial incorporation vs. straw ownership). It cross-links sanctions evasion and maritime gray-zone but does not treat vessel-level churn specifically.
- **search_all**: rich existing corpus — cross-jurisdictional-entity-resolution (Panama/UAE/China shell chains, ~430 Iranian shadow vessels as of May 2026), sanctions-evasion-detection, maritime-logistics-gray-zone, secondary-sanctions-extraterritorial-enforcement.
- **search_library**: honest gap — the 355-book library returned only generic programming/lexicon hits (C libraries, gawk, MS Access), no entity-resolution or maritime-registry reference.
- **arXiv specialist**: mostly an honest gap — broad temporal-ER queries returned unrelated 2026 ML papers; two useful hits: **Alper** (2605.25814, iterative probabilistic label propagation over an evolving graph with budgeted LLM queries) and **PAL-Bench** (2606.16175, identity binding + temporal evidence aggregation). Also 2401.03426 (cost-efficient LLM ER) and 2512.15363 (KATS: entity ambiguity in evolving knowledge graphs).
- **Web gap-fill**: live 2026 shadow-fleet reflagging data (see Findings).

## 2. What I Found

### The vessel identity stack is a temporal ER problem with a twist
From the AIS wiki page: identity hierarchy = MMSI (radio ID, changeable), IMO number (registered "permanent" hull ID — the conventional anchor), callsign/flag (registrable). Evasion attacks the anchor itself: false MMSI/callsign/flag changes, repeated re-registration to flags of convenience, and **illegitimate IMO changes in corruptible registries** — structurally analogous to corporate registry ID churn.

### 2026 live data — adversarial regime shift
- Shadow tanker fleet now estimated at **~1,300 vessels, nearly 20% of global oil capacity** (ShipFinex brief).
- IMO GISIS listed **367 tankers as false-flagged as of April 4, 2026** (Wikipedia / Shadow fleet).
- Windward (Jan 5, 2026): tracked reflagging of **Novator (IMO 9297357)** — first sanctioned tanker without clear Russian ownership to reflag; Feb 12, 2026: **at least 120 falsely-flagged sanctioned tankers are likely to reflag to Russia's registry** in coming months, as Western interdictions of stateless shadow-fleet vessels accelerate.
- This is a **structural shift from fragmentation to consolidation**: evasion is moving from dispersed flag-of-convenience shells toward a single high-complexity registry (Russia), which changes TER matching statistics and the enforcement trade-off.

### Algorithmic state of play (arXiv + corpus)
- **Alper** (2605.25814): replaces the static blocking-matching-clustering cascade with unified iterative label propagation on a global evolving graph, merging weak graph signals with budgeted LLM pairwise queries — directly relevant to churn where registry events arrive incrementally.
- **PAL-Bench** (2606.16175): evidence-grounded identity reconstruction; key design lesson — **freeze/update identity bindings before mining downstream facts** — exactly the discipline TER needs in OSINT pipelines to avoid cascading errors into knowledge graphs.
- Corpus background: FlexRL (flexible Bayesian linkage), ST-Link (spatio-temporal), Fellegi-Sunter foundation, and the entity-binding failure mode in agent safety (24–26% wrong-entity actions when identities change between tool calls).

## 3. What I Think Is Interesting

1. **The shadow fleet is a natural adversarial TER benchmark.** Deliberate obfuscation behaves differently from legitimate evolution (mergers, renaming): the adversary actively optimizes against whatever matching variables you publish. Most LLM-ER work (Alper, 2401.03426) is tested on static academic datasets with cooperative noise; maritime churn is adversarial, multimodal, and time-stamped — a demanding and realistic stress test for the field.

2. **The 2026 reflag-to-Russia regime shift is a regime-change problem for TER, not steady-state noise.** When ~120 vessels consolidate into one registry, the matching prior changes (fewer false flags, but one registry with contested integrity). TER models with fixed decay parameters will be miscalibrated; the interesting research problem is **detecting the regime change itself** from churn statistics (e.g., sudden reflagging-rate spike, flag-distribution entropy collapse).

3. **Single-anchor identity is the core vulnerability.** Treating IMO as the permanent key is the same failure mode as treating a corporate registry ID as permanent while registries get captured or corrupted. Robust vessel re-identification needs redundancy: IMO/MMSI + physical descriptors (dimensions, engine, photos), SAR-derived hull profiles, and behavioral fingerprints (AIS kinematics, STS rendezvous patterns, port-call rhythm) — probabilistic fusion in the Fellegi-Sunter tradition, not key-based lookup.

4. **Enforcement itself is a matching signal.** The reflagging acceleration is a revealed-preference indicator of interdiction pressure. Churn rate can be read as a market/geopolitical thermometer.

## 4. What I'd Explore Next

1. **Build a temporal churn benchmark**: start from the GISIS 367-tanker false-flag list + AIS gap data + reflagging timelines to construct a matched-vessel churn dataset; test whether Alper-style evolving-graph LLM linkage outperforms static blocking under adversarial regime shifts.
2. **Registry integrity map**: categorize flag registries by false-flag incidence and IMO-change permissiveness (GISIS/clean registry data) — an ER analogue of per-source data-quality attributes.
3. **Regime-change detection**: model reflagging-rate time series for entropy/change-point detection; correlate with enforcement events (seizures, OFAC/EU designations) as predictive early-warning signal.
4. **Open corpora test bed**: evaluate shell-churn detection on OpenSanctions/OpenCorporates temporal data — same TER machinery, corporate domain.
5. **Multimodal vessel re-ID**: fused SAR + optical + AIS fingerprinting to anchor identity when registry fields lie (ties to today's satellite/maritime pages).

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| **OSINT / Aviation twin** | ADS-B signal-integrity research (today): ICAO-24 bit identity is the same class of mutable anchor as IMO; an aviation temporal-ER case parallels the maritime one. |
| **Markets & Finance** | Reflagging/churn rate is a tradeable signal — tanker charter rates, insurance premiums, Urals-Brent differential; sanctions enforcement as market catalyst. |
| **Geopolitics / Strategic** | Reflag-to-Russia consolidates fleet control inside an adversarial registry — reduces Western interdiction leverage; regime-shift detection doubles as geopolitical risk monitoring. |
| **AI Agent Architecture** | Nested symmetry: Alper's budgeted LLM queries ≈ agentic tool use; Exocortex's ER pipeline as deterministic scaffold; entity-binding failure mode (24–26% agent errors) is the same bug class as stale vessel identity keys. |
| **Privacy & Cryptography** | Privacy-preserving cross-registry ER (Jensen-Shannon divergence framework) could let coalition partners match vessel/shell identities without revealing sources or methods. |
| **History of Intelligence** | Attribution under deliberate obfuscation is CI tradecraft; ACH/structured analytic techniques apply to the "is this a new vessel or the same one?" question. |

---

**Sources & grounding:** search_memory (temporal-entity-resolution.md v17, cross-jurisdictional-entity-resolution, sanctions-evasion-detection, maritime-logistics-gray-zone), arXiv 2605.25814 (Alper), 2606.16175 (PAL-Bench), 2401.03426, 2512.15363; web: ShipFinex shadow tanker fleet 2026 (~1,300 vessels / ~20% capacity), Wikipedia Shadow fleet (GISIS 367 false-flagged tankers, Apr 4 2026), Windward (Novator IMO 9297357 reflag Jan 2026; ~120 falsely-flagged tankers likely to reflag to Russia, Feb 2026). Local wiki: maritime-ais-osint-dark-fleet.md. search_library: honest gap (no ER/maritime-specific reference in book corpus).
