# Temporal Entity Resolution

**Status:** DRAFT → Deepening
**Created:** 2026-07-08
**Last Updated:** 2026-07-08
**Tags:** entity-resolution, temporal-dynamics, OSINT, identity-tracking, sanctions-evasion, record-linkage

## 1. Overview

Temporal entity resolution (TER) extends standard entity resolution (ER) to track identity across time. Standard ER treats entities as static: at a given moment, two records either refer to the same real-world entity or they do not. Real entities, however, change — companies rebrand, merge, or cycle through shell identities; individuals change names, addresses, and digital footprints; vessels re-flag, spoof AIS, and adopt scrap identities. TER models these transitions so that an entity's identity trajectory is preserved, not just its current snapshot.

This is distinct from **timeline reconstruction**, which arranges event chronologies. TER tracks the evolution of an entity's *identity* — the labels and attributes by which it is known — across time steps. Timeline reconstruction answers "when did X happen?"; TER answers "is entity A at time t₁ the same as entity B at time t₂, despite changed identifiers?"

### 1.1 Why Standard ER Breaks Down with Time

- **Attribute obsolescence:** A company's registered office changes; its old address in a corporate registry becomes stale.
- **Deliberate obfuscation:** Sanctioned entities use serial shell companies, each with a short lifespan, to break temporal links.
- **Temporal incoherence:** Two records that appear identical under static Fellegi-Sunter matching may be temporally impossible (e.g., vessel simultaneously in two ports).

## 2. Taxonomy of Temporal Changes

| Category | Description | Detection Signal |
|----------|-------------|------------------|
| **Legitimate evolution** | Rebranding, M&A, address relocation, legal name change (marriage, incorporation amendments) | Continuity in non-public identifiers (tax ID, registration number) across records; overlap periods in corporate filings |
| **Deliberate evasion** | Shell company rotation ("serial incorporator"), vessel flag-hopping, straw owner substitution, AIS manipulation ("zombie" IMO numbers) | Short entity lifespan; high churn rate; shared beneficial owner, address, or contact details across successive shells; behavioral consistency (same port calls, same cargo patterns) |
| **Data-quality drift** | Registration lag (new records not yet in database), encoding changes, transliteration inconsistencies accumulating over time | Gradual attribute drift rather than sudden identity switch; predictable registration delay offsets |

## 3. Methodology

### 3.1 Temporal Windows

Instead of matching all records in a global cross-product, TER restricts matching to a **temporal window** [t−Δt, t+Δt]. This both reduces combinatorial complexity and enforces temporal consistency. For sanctions vessel tracking, windows of 24–72 hours are used to link AIS pings; for corporate registries, windows of months to years capture rebranding cycles.

### 3.2 Transition Models

A transition model estimates the probability that an entity changes its identifiers between time steps. Formalized as a latent state model:

- **Latent identity variable:** Each time step assigns an entity to a latent identity cluster.
- **Transition matrix:** P(identity_k → identity_l) from one period to the next. For legitimate changes, transitions are sparse and predictable; for evasion, transitions are erratic (jumping to entirely new identifiers).
- **FlexRL** (Robach et al., 2024, arXiv:2407.06835) implements this via a Stochastic EM algorithm: E-step estimates the latent entity assignments, M-step updates the transition parameters. The model accommodates both registration errors and genuine identity changes.

### 3.3 Decay Functions

Match confidence decays with time: a match between records 3 months apart is more reliable than one 10 years apart. TER applies **half-life weighting**:

- Addresses: half-life ~2 years (high churn)
- Tax ID/vessel IMO: half-life ~∞ (stable identifiers)
- Company name: half-life ~5 years (occasional rebranding)
- Beneficial owner: half-life ~5–10 years (slow change)

Decay functions convert a static Fellegi-Sunter weight into a time-weighted weight: w_t = w_static × e^{−λt}.

### 3.4 Spatio-Temporal Consistency

For entities with physical location (vessels, people), simultaneous consistency in time AND space dramatically reduces false positives. **ST-Link** (2018, arXiv:1801.04101) introduces *k-l diversity*: a candidate pair must be within k distance units AND l time units to be considered. Applied to OSINT vessel tracking, this filters out AIS spoofs where two vessels claim the same IMO at opposite sides of the globe.

## 4. Algorithms & Implementations

| Algorithm | Approach | Strengths | Limitations | Reference |
|-----------|----------|-----------|-------------|----------|
| **FlexRL** | Latent variable model, Stochastic EM | Handles attribute change + registration error; open-source R package | Requires training data with known transitions; computational overhead for large populations | arXiv:2407.06835 (2024) |
| **ST-Link** | Spatial-temporal diversity (k-l) | Scalable to million-scale spatio-temporal datasets; simple to implement | Only applicable when location data is available; parameter tuning sensitive | arXiv:1801.04101 (2018) |
| **Bayesian Record Linkage with Temporal Priors** | Random partition model + downstream task feedback | Exact error propagation; joint modeling improves downstream performance | Computationally expensive; designed for two-file linkage, not streaming | arXiv:1810.04808 (Steorts et al., 2018) |
| **DBLP Temporal Dataset** | Benchmark creation (80K authors, 2M publications, ground-truth affiliation changes) | First large temporal ER evaluation corpus | Domain-specific (academic authors); limited evasion patterns | arXiv:1806.07524 (Hu et al., 2018) |

## 5. Sanctions Evasion Case Studies

### 5.1 Iranian Shadow Fleet Vessel Rotation

**Source:** *Iranian Sanctions Evasion & Escalation* wiki page; CSIS satellite analysis, Kpler AIS data.

Iran's shadow fleet (~430 vessels) employs rapid **identity cycling**:
- **Flag rotation:** Vessels switch flags every 2–6 months through registries of Comoros, Panama, São Tomé, and landlocked nations (Botswana, San Marino) to create false jurisdictional flags.
- **AIS manipulation:** Broadcasting IMO numbers of scrapped vessels ("zombie tactics"), turning off AIS during ship-to-ship transfers, or spoofing other vessels' positions.
- **Identity layering:** A single vessel may simultaneously appear under three registrations — Panamanian for insurance, Emirati for ownership, Chinese for crew — to make cross-referencing fail.

**TER countermeasure:** Apply a spatio-temporal window filter (ST-Link) to AIS pings: if vessel A at position (lat₁, lon₁, t₁) cannot physically reach (lat₂, lon₂, t₂) at maximum vessel speed, they cannot be the same vessel. Match surviving candidates on physical signatures (vessel dimensions, draft, engine type) across time windows, ignoring flag/name/IMO changes.

### 5.2 Russian Oil Price Cap Shell Companies

**Source:** *Russian Oil Price Cap Sanctions Enforcement* wiki page; KSE Institute, CREA.

To circumvent the $60/bbl G7 price cap, Russian crude shippers use **short-lived shell companies** (lifespan 1–6 months) registered in UAE, Hong Kong, or Marshall Islands. A ShellCo exists only for a single voyage, then is dissolved. Standard ER sees a new entity each time; TER detects the shared beneficial owner or parent holding company across the chain of shells.

**TER countermeasure:** Corporate registry change-logs (UK Companies House, Dubai DED, Panama Registro Público) provide the transition record. A temporal ER pipeline scans for patterns: shared registered agent address across short-lived entities, shared directors/officers with overlapping tenures, rapid sequential incorporation of entities with identical share capital structures. Transition model flags chains of 3+ shells with <1 yr lifespan under common ownership.

### 5.3 North Korean Crypto Laundering Infrastructure

**Source:** *North Korean Cryptocurrency Operations* wiki page; Chainalysis, TRM Labs.

Lazarus Group laundering follows a multi-stage pipeline over ~45 days. Wallet addresses churn: the crypto-to-AI-to-missiles self-reinforcing cycle involves thousands of temporary addresses, each used once and discarded. Temporal ER on blockchain transaction graphs links wallets through behavioral patterns (gas fee signatures, exchange deposit timing, bridging patterns) despite no shared identifying information.

## 6. Cross-Domain Connections

| Wiki Page | Connection |
|-----------|------------|
| [[cross-jurisdictional-entity-resolution]] | Multi-jurisdiction registries are the data sources; TER extends static cross-jurisdictional ER to track entities through jurisdiction changes over time |
| [[entity-resolution-agent-safety]] | Entity-binding failures (24–26% wrong-entity actions in tool-augmented agents) worsen when entities change identity between tool calls — TER-informed action gates detect stale bindings |
| [[data-lineage-provenance-entity-resolution]] | Provenance tracking (W3C PROV-O) aligns with TER: each identity change is a provenance event; temporal ER consumes lineage metadata to verify transition legitimacy |
| [[timeline-reconstruction-osint]] | Timeline reconstruction places events in time; TER answers "is the entity in event A the same as in event B?" — together they provide spatio-temporal event-entity coherence |
| [[knowledge-graph-construction]] | Knowledge graphs with temporal versioning (Temporal RDF, Neo4j temporal properties) store entity state snapshots — TER generates the links between snapshots |
| [[iranian-sanctions-evasion-escalation]] | Direct operational use case: vessel identity tracking across flag/IMO changes |
| [[russian-oil-price-cap-sanctions-enforcement]] | Shell company rotation detection via corporate registry change-logs |
| [[north-korea-crypto-operations-sanctions-evasion]] | Crypto address churn detection via behavioral fingerprint linkage |
| [[maritime-logistics-gray-zone]] | Shadow fleet AIS manipulation patterns; zombie tactics require temporal ER to track |
| [[entity-resolution-algorithms]] | Foundational Fellegi-Sunter model; TER extends FS with temporal priors and decay functions |
| [[intelligence-failure-analysis]] | Broken entity identity tracking is a species of intelligence failure (mirror-imaging, anchoring) — TER provides the countermeasure |

## 7. Evaluation & Datasets

### 7.1 Available Benchmarks

- **DBLP Temporal Dataset** (Hu et al., 2018): 80K author profiles with 2M publications; ground truth includes affiliation changes over time. The only dedicated temporal ER dataset.
- **OpenSanctions Pairs** (Smith et al., 2026): Cross-jurisdictional but static; could be extended with temporal snapshots by pulling registry versions at different dates.

### 7.2 OSINT-Specific Gap

No public benchmark exists for OSINT temporal ER tasks (vessel tracking, shell company detection, crypto address clustering). The field relies on operational case studies. A useful contribution would be a temporal version of the OpenSanctions dataset — periodically pull registry data and construct ground-truth identity chains through known sanctions evasion patterns.

## 8. Future Directions

- **LLM-assisted TER:** LLMs can recognize entity rebranding in unstructured news articles ("Company X, formerly known as Y...") and feed the transition as a prior to a probabilistic ER pipeline.
- **Graph neural networks for temporal entity graphs:** GNNs with temporal attention layers (e.g., TGNs) can learn entity transition patterns from historical registry data.
- **Streaming TER:** Real-time vessel/shell company tracking requires millisecond-latency matching with temporal window constraints.
- **Privacy-preserving TER:** Applying zero-knowledge proofs to verify entity transitions without exposing the raw identity chain.

## 9. References

1. Robach, K., van der Pas, S.L., van de Wiel, M.A., Hof, M.H. (2024). "A Flexible Model for Record Linkage." arXiv:2407.06835v3. *FlexRL R package.*
2. Hu, Y., Wang, Q., Christen, P. (2018). "Developing a Temporal Bibliographic Data Set for Entity Resolution." arXiv:1806.07524v1.
3. Spatial-temporal linkage: "Spatio-Temporal Linkage over Location Enhanced Services." arXiv:1801.04101v1, 2018.
4. Steorts, R.C., Tancredi, A., Liseo, B. (2018). "Generalized Bayesian Record Linkage and Regression with Exact Error Propagation." arXiv:1810.04808v1.
5. Fellegi, I.P. & Sunter, A.B. (1969). "A Theory for Record Linkage." *Journal of the American Statistical Association.*
6. Iranian Sanctions Evasion & Escalation wiki page (Exocortex, 2026).
7. Russian Oil Price Cap Sanctions Enforcement wiki page (Exocortex, 2026).
8. North Korean Cryptocurrency Operations wiki page (Exocortex, 2026).
9. Maritime, Logistics & Gray Zone Operations wiki page (Exocortex, 2026).
10. Cross-Jurisdictional Entity Resolution wiki page (Exocortex, 2026).

## Deepening Log

- 2026-07-08: DRAFT stub created (46 lines).
- 2026-07-08: Deepened to ~180 lines; added formal problem statement, change taxonomy, methodology (temporal windows, transition models, decay functions, spatio-temporal consistency), algorithm comparison table, three sanctions evasion case studies, 11 cross-domain connections, evaluation and dataset analysis, future directions, and 10 references.
