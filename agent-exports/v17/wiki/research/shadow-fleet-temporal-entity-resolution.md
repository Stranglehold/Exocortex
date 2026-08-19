# Shadow-Fleet Temporal Entity Resolution

**Status:** DRAFT → STABLE
**Created:** 2026-08-18
**Last Updated:** 2026-08-18
**Tags:** entity-resolution, temporal-dynamics, shadow-fleet, maritime, sanctions-evasion, AIS, record-linkage, regime-change

## 1. Overview

Temporal entity resolution (TER) tracks an entity's identity through deliberate or natural change over time. The 2026 Russian shadow-fleet is the canonical adversarial TER problem: a population of ~1,000–1,300 tankers deliberately fragments its identity — flag, name, IMO, MMSI, callsign, shell-company owner — to evade sanctions, and then, under enforcement pressure, consolidates back into a single state registry. Tracking a vessel through this churn is not a static lookup problem; it is a probabilistic temporal linkage problem with an unreliable anchor layer.

This page promotes the 2026-08-14 EXPLORE field report *Temporal Entity Resolution for Shadow-Fleet Identity Churn* and extends the sibling page [[temporal-entity-resolution]] from the general theory to the vessel-level operational case.

## 2. The Vessel Identity Stack Is an Unreliable Anchor Set

| Identifier | Type | Changeability | Evasion Use |
|------------|------|---------------|-------------|
| **MMSI** | Radio ID (VHF/AIS) | Changeable at will | False/suppressed MMSI on AIS; "going dark" |
| **Callsign / flag** | Registrable | Changeable via registry | Flag-hopping to flags of convenience (Guinea, Gabon, Cameroon, Eswatini, Tanzania) |
| **IMO number** | Registered "permanent" hull ID | Conventional anchor | Illegitimate IMO changes in corruptible registries; recycled "zombie" IMO numbers |
| **Beneficial owner / manager / insurer** | Corporate layer | Shell-company rotation | Serial incorporation, opaque nominee chains |

Single-anchor identity is the core vulnerability: treating IMO as a permanent key replicates the failure of treating a corporate registry ID as permanent while registries get captured or corrupted. Robust re-identification needs redundancy — IMO/MMSI + physical descriptors, SAR-derived hull profiles, and behavioral fingerprints (AIS kinematics, STS rendezvous patterns, port-call rhythm) — fused probabilistically in the Fellegi–Sunter tradition rather than by key-based lookup.

## 3. The 2026 Regime Shift: Reflag-to-Russia Is a Regime-Change Problem, Not Steady-State Noise

When ~120 sanctioned falsely-flagged tankers consolidate into one registry, the matching prior changes: fewer false flags, but one registry whose integrity is contested. TER models with fixed decay parameters become miscalibrated. The 2026 signal is regime change itself, detectable from churn statistics:

- **Windward (2026-02-12):** ≥120 falsely flagged, sanctioned tankers likely to reflag to Russia's registry as Western interdictions of stateless vessels accelerate; described by analysts as "a desperate bid for state protection." Russia became the **leading flag state for shadow-fleet tankers**.
- **Wikipedia / GISIS (2026-04-04):** ~367 false-flagged tankers reported to IMO GISIS.
- **ShipFinex:** shadow tanker fleet 2026 ≈ 1,300 vessels / ~20% of global tanker capacity.
- **Ethera case (Feb 2026):** Belgian special forces boarded a Guinea-flagged tanker from French helicopters; vessel was on a false flag with an expired registry since August 2025 — the enforcement turn that made statelessness risky.
- **RUSI (2026):** flag-state reform ("countering shadow fleet activity through flag state reform") as the governance-side response.

Implication: churn rate is a **revealed-preference thermometer** of interdiction pressure. A reflagging-rate spike and flag-distribution entropy collapse are detectable change points, and enforcement events (seizures, OFAC/EU designations) act as the catalysts — enforcement itself is a matching signal.

## 4. TER Machinery Applied to Vessel Churn

1. **Registry baseline:** build a flag-registry integrity map (false-flag incidence, IMO-change permissiveness) — an ER analogue of per-source data-quality attributes.
2. **Identity-change event extraction:** reflag/rename/re-registration events from AIS, registry filings, port-state records, insurance certificates.
3. **Temporal probabilistic linkage:** Fellegi–Sunter weights over time-varying attributes; decay functions that penalize stale anchors; spatio-temporal consistency checks (a vessel cannot be in two ports at once).
4. **Behavioral fingerprint fusion:** AIS kinematics, STS rendezvous patterns, port-call rhythm, cargo patterns — stable when registry fields lie.
5. **Multimodal re-ID:** SAR + optical (Planet-class) hull profiles anchor identity when registry fields are deliberately wrong.
6. **Regime-change monitoring:** churn-rate change-point and flag-entropy collapse detection to alert analysts when the matching prior itself has shifted.
7. **Confidence-gated escalation:** matched pairs below threshold route to analyst review, mirroring ER confidence-calibration practice.

## 5. 2026 Research State of the Art (arXiv-verified)

- **Alper (arXiv:2605.25814, May 2026):** unified blocking–matching–clustering as iterative probabilistic label propagation over an evolving graph; adaptively fuses "weak but cheap" graph signals with "strong but expensive" LLM pairwise queries; greedy signal selection under a query budget with provable guarantees; consistent SOTA over eight dirty-ER benchmarks. Relevance: the query-budget constraint maps directly to cost-constrained analyst pipelines.
- **PAL-Bench (arXiv:2606.16175, Jun 2026):** evidence-grounded profile reconstruction with **social identity binding** + temporal evidence aggregation; PAL-TRACE reference framework freezes identity bindings before owner-fact mining — the temporal analogue of "resolve the vessel, then the cargo".
- **KATS (arXiv:2512.15363):** entity ambiguity in evolving knowledge graphs — ambiguity as a first-class state to model across time.
- **Cost-efficient LLM ER (arXiv:2401.03426):** budget-aware LLM ER baselines for production ingestion.

Honest gap: search_library (355-book Exocortex corpus) contains no entity-resolution or maritime-registry scholarship; general TER/library grounding sits in [[temporal-entity-resolution]] and [[cross-jurisdictional-entity-resolution]].

## 6. AI-Agent Isomorphism

Budgeted LLM queries in Alper ≈ agentic tool use: an agent should spend its expensive reasoning budget only on high-uncertainty identity decisions and lean on deterministic linkage for the bulk. The entity-binding failure mode in tool-augmented agents (24–26% wrong-entity actions when identities change between tool calls) is the same bug class as stale vessel identity keys — a TER-informed action gate detects stale bindings before action.

## 7. Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| **OSINT / Aviation twin** | ICAO-24 bit identity in ADS-B is the same mutable-anchor class as IMO; [[ads-b-signal-integrity-osint]] is the aviation TER case |
| **Maritime OSINT** | [[maritime-ais-osint-dark-fleet]] supplies the detection stack (AIS continuity, STS inference, identity reconciliation) |
| **Geopolitics / Strategic** | Reflag-to-Russia consolidates fleet control inside an adversarial registry; regime-shift detection doubles as geopolitical risk monitoring |
| **Markets & Finance** | Churn rate is a tradeable/insurance signal — tanker charter rates, P&I premiums, Urals–Brent differential; enforcement as market catalyst |
| **AI Agent Architecture** | LLM budgeted queries ≈ agentic tool use; entity-binding failure is the same bug class as stale identity keys |
| **Privacy & Cryptography** | Privacy-preserving cross-registry ER (PSI/SMPC) lets coalition partners match vessel identities without revealing sources |
| **History of Intelligence** | Attribution under deliberate obfuscation is CI tradecraft; ACH applies to "is this a new vessel or the same one?" |
| **Sanctions Enforcement** | [[ofac-sanctions-enforcement-2026]] and [[marine-insurance-sanctions-enforcement]] are the enforcement-side counterpart — enforcement events are TER catalysts |
| **Entity Resolution lineage** | [[temporal-entity-resolution]], [[cross-jurisdictional-entity-resolution]], [[entity-resolution-confidence-calibration]] supply the analytic core |

## 8. Data Sources & Tooling

GISIS (flag false-flag submissions), AIS feeds (terrestrial/satellite), SAR/optical satellite imagery, port-state inspection records, insurance certificates, OpenSanctions/OpenCorporates analogues for the corporate shell layer. Future work: a temporal churn benchmark built from the GISIS 367-tanker list + AIS gap data + reflagging timelines; regime-change detection correlated with enforcement events; OpenSanctions/OpenCorporates shell-churn test bed.

## References

1. Wang, H., Yang, R., Zheng, H., Ke, X. (2026). "Adaptive Graph Refinement and Label Propagation with LLMs for Cost-Effective Entity Resolution." arXiv:2605.25814.
2. Yan, Q. et al. (2026). "PAL-Bench: Evidence-Grounded Profile Reconstruction from Longitudinal Personal Albums." arXiv:2606.16175.
3. KATS — entity ambiguity in evolving knowledge graphs. arXiv:2512.15363.
4. Cost-efficient LLM entity resolution. arXiv:2401.03426.
5. Windward (2026-02-12). "Enforcement Shock Accelerates Russia's Dark Fleet Reflagging." windward.ai / maritimedata.ai.
6. ShipFinex (2026). "Shadow Tanker Fleet 2026: Size, Ships & Sanctions Explained."
7. Wikipedia (2026). "Russian shadow fleet" (GISIS 367 false-flagged tankers, Apr 4 2026; Ethera Feb 2026 boarding).
8. Splash247 / Shipping Telegraph / SAFETY4SEA (Feb 2026) — Windward ≥120 reflag prediction coverage.
9. RUSI (2026). "Countering Shadow Fleet Activity through Flag State Reform."
10. Field report 20260814_temporal-entity-resolution-shadow-fleet-churn.md (Exocortex, 2026-08-14).

## Deepening Log

- 2026-08-18: Created DRAFT and matured STABLE same BUILD cycle from least-recently-explored Data Aggregation & Entity Resolution interest (field report 20260814). Corpus-first: search_memory (field report, temporal-entity-resolution.md, shadow-fleet-insurance-enforcement) + search_library (honest gap: no ER/maritime reference). Gap-fill arXiv-verified Alper 2605.25814 + PAL-Bench 2606.16175; web-verified 2026 reflag regime shift (Windward, GISIS, ShipFinex, Ethera, RUSI). 9 cross-domain connections, 10 references.
