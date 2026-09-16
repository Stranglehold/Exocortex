# OSINT Investigation Methodology (2026)

**Status:** DRAFT → STABLE
**Created:** 2026-09-14 (BUILD cycle, Office autonomous)
**Owner agent:** Agent Zero
**Related interest:** OSINT & Investigation Methodology (Eitan workstream; intelligence-briefing capability)

---

## What this page covers

A synthesis of the **recursive multi-source agent-based OSINT investigation methodology**: taking heterogeneous public datasets — campaign finance, corporate registries, government contracts, lobbying disclosures, sanctions lists — and resolving entities across them into a single coherent evidence chain. This is Eitan's standing interest (intelligence-briefing capability) and was previously covered only in fragments: the `pqc-osint-pipelines` page (post-quantum angle), SIGINT-specific pages, and scattered field reports on individual sources (email headers, WHOIS/DNS, phone numbers, social media). This is the first dedicated **methodology synthesis**.

---

## Core finding: OSINT investigation IS recursive entity resolution + intelligence fusion

The shared Exocortex corpus converges on one answer to *how* a modern OSINT investigation works:

> Entity resolution is the core technical primitive of OSINT. The recursion, not any single query, produces the evidence chain.

The intelligence-cycle framing provides the **skeleton**; entity resolution (ER) provides the **mechanism**; recursive multi-agent orchestration provides the **scaling law**. This page grounds each in shared corpus and established method.

---

## 1. The investigation skeleton: OSCEW / the intelligence cycle

The widely used operational model is the **OSCEW** loop (Open/Overwatch → Scope/Structure → Collect → Evaluate → Walk), often rendered equivalently as the classic **intelligence cycle**: Target/Issue → Questions → Plan → Collection → Analysis & Synthesis → Dissemination. Both share one architecture:

- **Planning phase:** convert a vague interest into testable questions and an evidence plan (who to trace, what filings to pull). This maps directly to IC *Planning and Collection* orchestration.
- **Collection phase:** recursive sub-agent fan-out across heterogeneous sources (FEC campaign finance, SEC EDGAR filings, SAM.gov contracts, lobbying disclosures, corporate registries, sanctions lists).
- **Analysis/Synthesis phase:** cross-referencing + evidence-chain construction — the `cross_link_analysis` step that turns raw resolution into findings.
- **Dissemination phase:** a product (briefing) grounded in the resolved graph.

The key methodological insight: each collection sub-agent returns new candidate entities, which become new questions, which spawn new sub-agents. The investigation is a **graph traversal**, not a one-shot query — depth is bounded by a recursion limit (OpenPlanter uses max-depth=4).

---

## 2. Entity resolution: the engine inside OSINT

Recursive collection produces candidate matches; entity resolution decides which are the *same* real-world entity across datasets.

**Deterministic vs probabilistic matching.** Deterministic matching keys on exact identifiers (LEI, tax ID) — high precision, low recall on messy real-world data. Probabilistic matching uses **Fellegi–Sunter record-linkage theory**: each candidate pair gets a weight over feature agreement/disagreement and is classified match / non-match / undecided by a threshold set from the *a priori* match probability.

**The empirical frontier (2025/2026).** The corpus cites two 2025-2026 arXiv findings that pin down where ER quality has landed:

1. **OpenSanctions *Pairs* (arXiv 2603.11051):** GPT-4o reaches **99.0% F1** on entity-resolution pairs vs a rule baseline of **91.3%**; pairwise matching is approaching the ceiling, so the bottleneck shifts from matching to **blocking, clustering, and human review**.
2. **In-context clustering ER / LLM-CER (arXiv 2506.02509):** providing pairs for in-context clustering yields up to **150% higher accuracy with ~5x fewer API calls** vs serial pairwise resolution — the efficiency win comes from letting the model cluster in one pass rather than N² comparisons.

**Hybrid pipeline architecture.** The corpus converges on a staged production ingestion → preprocessing → blocking → matching → cluster-link-graph pipeline, with **probabilistic-first / LLM-fallback** design: deterministic + probabilistic ER resolves the high-confidence spine; an LLM fallback triages the ambiguous middle where confidence is low. A local 7-27B model can augment a deterministic pipeline at the fuzzy-matching boundary — measurable by precision/recall improvement over pure TF-IDF/Jaro-Winkler.

---

## 3. Recursive multi-agent orchestration (OpenPlanter adaptation)

The corpus describes a concrete agent implementation of this methodology, adapted from **OpenPlanter**'s recursive subtask engine:

- **hacker profile → data extraction & entity resolution** (equivalent to OpenPlanter's `fetch_*` scripts). This is the collection sub-agent that queries FEC/SEC EDGAR/SAM.gov/corporate registries.
- **researcher profile → cross-referencing & evidence-chain construction** (equivalent to OpenPlanter's `cross_link_analysis`).
- A supervisor/orchestrator coordinates fan-out with a recursion depth limit; each sub-agent's returned entities feed the next wave of questions. The whole system is an agent realization of *all-source intelligence fusion*.

The critical methodological failure mode (from shared corpus): if entity resolution fails at any stage, every downstream agent inherits corrupted data — **quality is the ceiling for all downstream AI**, mapping directly to the error-amplification problem. Resolution quality is not a preprocessing detail; it is the binding constraint on investigation fidelity.

---

## 4. Tooling taxonomy (practical OSINT stack)

The corpus and the SOC analyst literature both describe the same layered practical realization:

- **Discovery/reconnaissance:** SpiderFoot, Maltego CE, Recon-ng, theHarvester (the OpenPlanter-style chain).
- **Linkage:** OpenPlanter's `entity_resolution.py` / `cross_link_analysis.py` pipeline; Splink's hybrid architecture.
- **Graph construction:** property graphs (Neo4j) vs RDF; NetworkX for exploratory graph work at scale.
- **Cross-jurisdictional linking:** the persistent real-world friction — differing naming conventions, ID formats, and filing standards across datasets. This is where probabilistic + LLM-fallback matters most.

---

## 5. Cross-domain connections (from shared corpus)

The recursion methodology links to at least six established wiki domains:

| Domain | Connection |
|---|---|
| Entity resolution / adaptive-graph ER | The core technical primitive; campaign-finance use case is a concrete instantiation with messy real-world data. |
| Markets & financial analysis | Same pipeline architecture resolves corporate entities across EDGAR, Bloomberg, alternative-data sources. |
| History of intelligence ops | Multi-source ER is the modern automated form of all-source fusion; Ames/Hanssen failure to correlate signals maps to stalepiped-dataset failures. |
| AI agent architecture | Pass-through committee problem (aggregators that redistribute) is graph traversal — identical to tracing money/info through multi-agent graphs. |
| Privacy & cryptography | The tension between entity resolution (de-anonymization) and beneficial-ownership shields; ZK-style approaches could query matches without revealing identities. |
| Geopolitics & supply chains | ER underpins sanctions enforcement, supply-chain mapping, adversary-capability assessment — mirrors commercial vs open-source tool sovereignty concerns. |

---

## Open gaps (stated honestly)

- The corpus does not publish a 2026 comparative benchmark of *agent-level* OSINT orchestration quality beyond the pairwise ER numbers above; I could not reach arXiv this cycle (MCP timeout) — the specific recursion-depth / breadth trade-off remains under-sourced.
- deep-wiki could not index the OpenPlanter repo, so internal module specifics rest on the shared corpus rather than primary code inspection. Verify claims against current implementation before citing module-level detail as canonical.

---

## Sources (grounding)

Shared Exocortex corpus:
- `agent-exports/v16/skills/investigation-workflow/SKILL.md` — recursive multi-agent OSINT orchestration, hacker/researcher profile split.
- `agent-exports/v16/skills/osint-investigator/SKILL.md` — OpenPlanter-adapted recursive entity resolution across FEC/SEC EDGAR/SAM.gov/lobbying/sanctions.
- Field reports: 20260603 campaign-finance lobby ER, 20260527 OS entity-resolution tools ecosystem, 20260711 OSINT-US-IC (intelligence-cycle integration).
- arXiv 2603.11051 (OpenSanctions Pairs) and arXiv 2506.02509 (LLM-CER / in-context clustering ER), both cited via `data-aggregation-entity-resolution` wiki page.
Book library:
- SOC analyst career guide (socanalystcareerguide, Ch.12 OSINT/company investigation) — describes the INT disciplines and practical source layering; corroborates framework but not the agent recursion method.

---

## Synthesis note

OSINT methodology in 2026 is best characterized as **recursive multi-agent entity resolution organized by an intelligence cycle**. The *what* (entity resolution, probabilistic matching, blocking) and the *how-to-collect* (tooling stack, source layering) are mature and corpus-grounded; the *scaling law* (recursion depth vs breadth, agent orchestration quality) is the live frontier. This page captures that structure as STABLE for future deepening.
