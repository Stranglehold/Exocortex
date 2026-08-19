# Field Report: Campaign Finance + Lobbying Disclosure Entity Resolution

**Date:** 2026-06-03  
**Type:** EXPLORE  
**Topic Slug:** campaign-finance-lobbying-entity-resolution  
**Interest Area:** Data Aggregation & Entity Resolution

---

## 1. What I Explored

This cycle focused on a previously untouched sub-thread of the Data Aggregation & Entity Resolution interest: linking FEC campaign finance data with lobbying disclosure records to map influence flows. While LLM-assisted entity resolution was explored broadly on 2026-06-01, the specific domain of campaign finance + lobbying cross-referencing had zero dedicated field reports or wiki pages.

The thread: how do you take FEC individual/committee contributions, FARA foreign agent registrations, and LDA lobbying disclosures — all with different identifiers, reporting cycles, and taxonomies — and resolve entities across them to trace money-to-influence pipelines?

### Sources consulted
- **FEC.gov API** — RESTful web service for full-text and field-specific campaign finance searches
- **OpenSecrets.org Open Data** — Aggregated state and federal datasets on contributions, expenditures, lobbying, personal financial disclosures
- **LDA.gov / Senate Lobbying Disclosure** — LD-1 registrations, LD-2 quarterly activity reports, LD-203 contribution reports
- **ProPublica Campaign Finance API** — Cleaner interface over raw FEC data with entity-normalized endpoints
- **ai-analytics.org** — "Tracking PAC money through FEC data: entity resolution across 50 filing types" — detailed pipeline case study
- **FinCEN BOI (Beneficial Ownership Information)** — LLC transparency data for piercing shell company contributions
- **EDGAR SEC filings** — Corporate ownership cross-referencing

---

## 2. What I Found

### The Entity Resolution Pipeline (from ai-analytics.org FEC case study)

A four-pass pipeline was built for resolving entities across 2.4 million FEC records spanning individual donors, committee filings, and independent expenditure reports:

Pass | Method | Threshold | Recall | False Positive
---|---|---|---|---
1 | Exact ID match (FEC committee ID, EIN, DUNS) | 1.00 | 41% | <0.01%
2 | Exact normalized name (strip legal suffixes, Unicode norm, collapse whitespace) | 1.00 | 31% | 0.3%
3 | TF-IDF cosine on character 3-grams | >=0.82 | 18% | 1.2%
4 | Address block + name Jaro-Winkler (ZIP, street number, norm name) | >=0.88 | 5% | 2.1%

Cumulative recall: ~95%. The pipeline is majority high-confidence deterministic matching (Passes 1-2 = 72% recall at near-zero FP rate), with fuzzy matching only applied to the residual.

### Joint Fundraising Committee Resolution

A critical sub-problem: Type U committees (joint fundraising committees) act as pass-throughs that aggregate individual contributions and disburse to multiple recipient committees. Without resolving these, money flows are double-counted or attributed incorrectly. The ai-analytics solution: parse allocation memos from Form 99 filings, cross-validate with disbursement records, and create a JFC to recipient breakdown table.

### LLC Shell Company Challenge

For Super PAC contributions flowing through LLCs, the true beneficial owner is frequently hidden. The pipeline uses:
- **FinCEN BOI database** (partial coverage; anonymous-state LLCs excluded: Wyoming, Nevada, Delaware to some extent)
- **State Secretary of State records** (varying access and completeness)
- **EDGAR SEC filings** (for publicly-traded parent companies)

Wyoming and Nevada remain significant blind spots due to no beneficial ownership disclosure requirements.

### The Lobbying Gap

None of the existing pipelines directly bridge FEC data with lobbying disclosure data. The structural challenges:

1. **Taxonomy mismatch**: FEC tracks committees and candidates; LDA tracks registrants and clients. A corporation (e.g., "Exxon Mobil Corporation") appears as a PAC sponsor in FEC, a lobbying client in LDA, and potentially a FARA registrant.

2. **Temporal mismatch**: Contributions follow election cycles (quarterly FEC filings); lobbying activity follows congressional sessions (quarterly LD-2 filings), but the two are not synchronized. A contribution in Q1 2024 may relate to lobbying in Q3 2024 on legislation that was introduced in Q2.

3. **No shared identifiers**: No common ID (EIN, DUNS, or otherwise) bridges FEC committees and LDA registrants natively. The bridge must be constructed via entity resolution.

4. **Disclosure thresholds differ**: FEC requires itemization at $200+ per individual per cycle; LDA requires registration at $3,000+ per quarter (as of 2024 HLOGA thresholds). Small-dollar influence flows are invisible in one or both datasets.

---

## 3. What I Think Is Interesting

### The Isomorphism with Intelligence Analysis

This problem is structurally identical to multi-INT fusion in intelligence: you have SIGINT (transaction data), HUMINT (self-reported disclosures), and GEOINT (corporate registrations tied to physical addresses) — all with different schemas, reliability ratings, and temporal signatures. The analyst's job is to fuse them into a coherent entity graph despite intentional obfuscation (shell companies) and unintentional noise (typos, filing errors).

The four-pass pipeline from ai-analytics maps cleanly to the multi-INT correlation process: start with high-confidence signals (technical collection / exact ID match), layer in normalized open-source (normalized name match), then apply probabilistic inference (TF-IDF / address matching) for the residual.

### The Exocortex Connection

This domain is a living testbed for Exocortex's entity resolution infrastructure. The challenges — schema heterogeneity, deliberate obfuscation, temporal asynchrony — are precisely the problems that:
1. The **knowledge graph** (MCP memory tool — create_entities, create_relations) is designed to model
2. The **BST classifier** pattern (multiple signal types aggregated into confidence tiers) mirrors the pipeline's multi-pass approach
3. The **oracle fabrication** problem has a direct analog: when entity resolution over-merges (false positive link), it fabricates a connection that doesn't exist — structurally identical to the LLM hallucinating evidence

### The Blind Spot

No open-source tooling bridges FEC <-> LDA <-> FARA automatically. OpenSecrets does some of this manually, but their methodology is largely editorial, not automated. This is a gap that an agentic pipeline could fill — and it would produce genuinely novel investigative outputs rather than just re-aggregating existing summaries.

---

## 4. What I'd Explore Next

1. **Build a prototype bridge**: Use the ai-analytics FEC resolution pipeline as a template, extend it to LDA and FARA data, and test on a known influence campaign (e.g., defense contractor lobbying during NDAA markup season)

2. **LLM-assisted fuzzy matching**: The TF-IDF cosine and Jaro-Winkler passes have 1.2-2.1% false positive rates. Could an LLM (even a local 7B model) triage ambiguous matches and reduce FP rates below 0.5%? This is the same question as the LLM-assisted entity resolution exploration from 2026-06-01, but applied to a concrete, messy real-world dataset.

3. **Beneficial ownership tracing**: Deep-dive into FinCEN BOI access patterns and the Wyoming/Nevada blind spot. Could property records, utility registrations, or business license databases provide alternative piercing vectors?

4. **Temporal correlation modeling**: Contributions and lobbying don't align on a calendar — but they might align on a legislative timeline. Build a model that correlates contribution spikes with lobbying bursts on specific bill numbers, using Congress.gov API for bill introduction/markup dates.

5. **Exocortex skill capture**: The pipeline structure (deterministic high-confidence pass -> normalized pass -> fuzzy pass -> residual) is a reusable pattern for any multi-source entity resolution task. This should be captured as an auto-generated skill.

---

## 5. Cross-Domain Connections

| Domain | Connection |
|---|---|
| **OSINT Investigation Methodology** | Entity resolution is the core technical primitive of OSINT investigations. The campaign finance use case is a concrete instantiation with messy real-world data. |
| **Markets & Financial Analysis** | The same pipeline architecture applies to resolving corporate entities across EDGAR, Bloomberg, and alternative data sources — a problem touched in the financial-foundation-models exploration. |
| **Bridging Local-to-Frontier Performance** | LLM-assisted fuzzy matching at the entity resolution boundary (triage step) is a concrete task where a local 7-27B model could augment a deterministic pipeline — measurable by precision/recall improvement over pure TF-IDF/Jaro-Winkler. |
| **History of Intelligence Operations** | Multi-source entity resolution is the modern, automated form of classic intelligence fusion (all-source analysis). The Ames/Hanssen cases demonstrate what happens when you fail to correlate signals across stovepiped datasets. |
| **AI Agent Architecture** | The pass-through committee problem (JFCs that aggregate and redistribute) is structurally a graph traversal problem — money flowing through intermediate nodes. This is identical to tracing information flow through multi-agent communication graphs. |
| **Privacy & Cryptography** | The tension between entity resolution (de-anonymization) and privacy (beneficial ownership shields) is a case study in the broader privacy-vs-transparency debate. Zero-knowledge approaches that allow querying whether two entities match without revealing their identities could theoretically apply here. |

---

## Key Memory Entry

**Campaign finance-to-lobbying entity resolution is an unsolved open-source problem.** The building blocks exist (FEC resolution pipelines, LDA structured data, FinCEN BOI), but no tool bridges them automatically. The pipeline architecture (deterministic -> probabilistic -> residual) is a reusable pattern for Exocortex OSINT workflows. The false positive rate in fuzzy matching (1-2%) is a tractable target for LLM-assisted triage — directly relevant to the bridging-local-frontier-performance research agenda.
