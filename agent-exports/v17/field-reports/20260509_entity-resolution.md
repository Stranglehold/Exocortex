# Field Report: Entity Resolution & Heterogeneous Data Aggregation
**Date:** 2026-05-09 | **Cycle:** FIELD | **Topic:** Data Aggregation & Entity Resolution

---

## 1. What I Explored

The specific thread: **how modern entity resolution (ER) tooling handles heterogeneous datasets at scale, and whether multi-agent LLM architectures offer advantages over traditional probabilistic methods.**

This followed Jake's core question: "how do you take heterogeneous datasets — corporate registries, campaign finance records, lobbying disclosures, government contracts, property records — and resolve entities across them to surface non-obvious connections?"

I searched for current open-source tools, recent academic papers, and architectural patterns at the intersection of entity resolution and agent-based AI.

## 2. What I Found

### Open-Source Tools (current state of the art)
- **Splink** — Probabilistic record linkage using Fellegi-Sunter models. Backed by SQL or Spark. Scales to millions of records. Used by UK government data science. 1.9k GitHub stars.
- **Zingg** — Active learning approach with Java/Python bindings. Builds models from labeled examples rather than requiring manual rule specification.
- **dedupe** — Python library using active learning. Flexible but designed for single-machine datasets.
- **Awesome-Entity-Resolution** — Curated list by OlivierBinette cataloging the full landscape of open-source and academic ER resources.

### Academic Research (2025-2026)
- **Multi-Agent RAG Framework for ER** (MDPI, Dec 2025) — Proposes using specialized LLM agents for different phases of entity resolution (blocking, matching, verification). The key insight: monolithic LLM approaches suffer from scalability and interpretability limits. Multi-agent coordination allows each agent to specialize on a resolution sub-task.
- **Data Integration and Storage Strategies in Heterogeneous Analytical Systems** (MDPI, Nov 2025) — Provides a cross-layer taxonomy coupling integration mechanisms (schema matching, entity resolution, semantic enrichment) with storage models. Includes reproducible workflows for canonical heterogeneity problems (schema name mismatch, instance-level data ambiguity).

### Architecture Patterns
- **Observation masking > summarization** for failure preservation (JetBrains/TUM, NeurIPS 2025). Relevant because entity resolution often fails silently — a "non-match" decision may be an error, and LLM summarization of resolution steps would smooth over these failures.
- **Deterministic + LLM hybrid** approach emerging as dominant: use deterministic methods (blocking keys, fuzzy matching, Fellegi-Sunter) for the heavy lift, use LLMs for edge cases and explanation. Avoids full LLM reliance for scalable operations.

### Existing Workdir Assets
- `/a0/usr/workdir/openplanter_study/scripts/entity_resolution.py` — already has an implementation scaffold
- The OpenPlanter wiki already maps 15+ data sources (SEC EDGAR, FEC, SAM.gov, USAspending, OFAC SDN, ICIJ Offshore Leaks, etc.) — each with their own entity naming conventions

## 3. What I Think Is Interesting

**The gap isn't the matching algorithm — it's the mapping across domains.**

Splink and dedupe solve the *within-dataset* problem well: given a CSV of campaign contributions, find duplicates. But Jake's question is about *cross-domain* resolution: connecting a company in SEC EDGAR to a donor in FEC to a contractor in SAM.gov to a lobbyist in Senate LD.

Each of these datasets has:
- Different entity naming conventions ("Exxon Mobil Corporation" vs "ExxonMobil" vs "EXXON MOBIL CORP")
- Different identifiers (CIK vs FEC Committee ID vs DUNS vs EIN)
- Different temporal windows (quarterly filings vs annual reports vs event-based disclosures)

**The multi-agent RAG paper validates an approach that Exocortex could implement:** specialized agents for blocking (finding candidate pairs), matching (scoring similarity), and verification (explaining/validating matches). This maps cleanly to Exocortex's existing pattern of chaining subordinate agents for complex tasks.

**The observation masking insight is critical for ER:** when an entity resolution step fails (false negative — two records that should match but didn't), the system needs to preserve the raw evidence of why. An LLM summary would say "no match found" — losing the SQL query, field comparisons, and threshold values that would reveal the gap. Deterministic logging + structured failure preservation is the right pattern.

## 4. What I'd Explore Next

1. **Test Splink on the existing OpenPlanter datasets.** The scripts already exist to pull FEC, SEC, and SAM.gov data. Feed them into Splink and measure within-dataset deduplication quality before attempting cross-domain resolution.

2. **Build a cross-domain entity index.** A lightweight SQLite database mapping {entity_name, source_dataset, source_id, normalized_name} across all 15 OpenPlanter sources. This is the minimum viable step before any sophisticated resolution.

3. **Evaluate the multi-agent RAG approach concretely.** Can an Exocortex subordinate agent chain perform blocking → matching → verification more effectively than Splink alone? The paper shows promise but hasn't been tested against government/regulatory datasets (which have different noise characteristics than academic benchmarks).

4. **Investigate the ICIJ Offshore Leaks methodology.** ICIJ resolved entities across 40+ jurisdictions with different languages, legal systems, and naming conventions for the Panama Papers. Their methodology (deterministic rules + human review) is the real-world benchmark.

## 5. Cross-Domain Connections

- **SWARMFISH / Analytical Committee** — The multi-agent RAG pattern mirrors SWARMFISH's committee deliberation. Entity resolution could use a similar pattern: multiple profiling agents assess match candidates, a consensus agent aggregates.
- **Epistemic Integrity** — Entity resolution is a confabulation minefield. LLMs confidently assert that "Company A in SEC equals Company B in FEC" without evidence. EI's provenance tracking ("did this claim appear in a tool output?") would catch fabricated matches.
- **Evidence Ledger** — Every resolved entity pair should be recorded with provenance: which datasets, which matching fields, which algorithm, and what confidence score. This is the structured data that the Evidence Ledger was designed to store.
- **Context Pruner / Stateful Injection** — Cross-domain resolution generates large intermediate state (candidate pairs, feature vectors, match scores). The pruner's observation masking pattern is directly applicable to compressing intermediate resolution results.

---

*Sources: Splink (github.com/moj-analytical-services/splink), MDPI Computers 14(12):525 (2025), MDPI Information 16(11):932 (2025), JetBrains/TUM NeurIPS 2025 DL4Code, Awesome-Entity-Resolution (github.com/OlivierBinette/Awesome-Entity-Resolution), ICIJ Offshore Leaks methodology.*
