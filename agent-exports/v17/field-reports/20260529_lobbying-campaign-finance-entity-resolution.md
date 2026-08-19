# Field Report: Lobbying Disclosures & Campaign Finance as OSINT Data Sources for Entity Resolution

**Date:** 2026-05-29
**Topic:** Data Aggregation & Entity Resolution — Lobbying Disclosures & Campaign Finance as OSINT Data Sources
**Cycle:** EXPLORE

---

## 1. What I Explored

I investigated US federal lobbying disclosure databases (LD-1, LD-2, LD-203) and Federal Election Commission (FEC) campaign finance data as structured, publicly-available sources for entity resolution—specifically, how to acquire, parse, and cross-reference these datasets to surface corporate-political connections.

The thread: can we treat lobbying registrations and campaign contributions as structured OSINT signals to connect corporations, executives, lobbyists, and government officials in a unified influence graph?

## 2. What I Found

### Lobbying Disclosure Data
- **Senate LDA API** (lda.senate.gov/api): REST API with query system for LD-1 (registration), LD-2 (quarterly activity), and LD-203 (contributions/HLOGA) filings. Provides registrant/client ID lookup and search portals.
- **House Lobbying Disclosure** (lobbyingdisclosure.house.gov): Parallel filing repository, same statutory basis.
- **Data points per filing**: registrant organization, client (the entity doing the lobbying), lobbyists, specific issues/lobbying topics, government entities contacted, and dollar amounts (LD-2 quarterly reports).
- **Scrapers exist**: Apify actor for Senate LDA filings, crawlable search portal.

### Campaign Finance Data
- **FEC OpenFEC API** (api.open.fec.gov): RESTful API with endpoints for candidates, committees, individual contributions, and disbursements. Full-text and field-specific search. Bulk downloads available.
- **Data points**: contributor name, address, employer, occupation, contribution amount, recipient committee/candidate, date. Committee-to-committee transfers (PACs), independent expenditures.
- **Interactive console** at 18f.github.io/openFEC-documentation/console/ for exploration.

### Cross-Referencing Tools and Methodology
- **OpenSecrets (Center for Responsive Politics):** Long-standing aggregator linking lobbying spending, campaign contributions, and personal financial disclosures. Their API (opensecrets.org) ties CRP IDs across these datasets.
- **FollowTheMoney (NIMSP):** State-level campaign finance, often integrated with OpenSecrets.
- **LittleSis:** Crowd-sourced database of powerful people and organizations, linking political donations, lobbying registrations, board memberships, and business ties. Has API.
- **Cross-referencing techniques:** Name normalization and fuzzy matching on individual donors/lobbyists is the core problem—same as classic entity resolution. Address matching, employer normalization, and unique identifiers (FEC committee ID, LDA registrant ID) help but are incomplete. CRP's unified database does much of this heavy lifting.

### Practical OSINT Workflow
1. Start with a corporation of interest → find its subsidiary structure via OpenCorporates
2. Search LDA for lobbying registrations naming that corporation or its subsidiaries as client
3. Extract lobbyist names, issues lobbied, government entities contacted
4. Search FEC for campaign contributions from those same lobbyists and corporate executives
5. Cross-reference by name, address, employer fields
6. Map the network: which politicians received contributions and were lobbied by the same entities
7. Layer on procurement data (USAspending.gov) for contract awards to entities that lobbied and donated

## 3. What I Think Is Interesting

**The datasets exist and are accessible, but cross-referencing remains painful.** The LDA and FEC have separate identifier systems with no shared unique ID for individual lobbyists/donors. OpenSecrets has solved this for their curated database, but their API is rate-limited and not fully open for bulk download. This is a classic entity resolution problem—exactly the kind of challenge Jake is interested in—where public data infrastructure falls short.

**The temporal dimension is under-exploited.** Lobbying reports are filed quarterly; campaign contributions have dates. Cross-referencing the timing of lobbying activity with contribution dates and subsequent government action (procurement awards, regulatory decisions, legislation) could surface causal signals. This temporal-causal linking is rarely done in open-source tools.

**The structure is surprisingly rich.** LD-2 filings specify specific lobbying issues and government entities contacted—metadata that can be normalized into categories. Combined with FEC contribution earmarks, you get fine-grained influence mapping.

## 4. What I'd Explore Next

- **Automated pipeline:** Build a pipeline that reads LDA filings (from Senate API/downloads), extracts entities (corporations, lobbyists, issues), searches FEC for contributions from the same individuals, and outputs a merged influence graph.
- **Temporal causal analysis:** Given the dates on filings and contributions, can we detect patterns where contributions preceded lobbying contracts or where lobbying preceded policy changes?
- **State-level lobbying:** Most research focuses on federal; state-level lobbying data (often fragmented) is a richer but messier source.
- **Foreign lobbying (FARA):** Foreign Agents Registration Act filings add another layer—foreign governments and entities lobbying the US, with different disclosure requirements.

## 5. Cross-Domain Connections

1. **Entity Resolution isomorphism:** The LDA-FEC cross-referencing problem is textbook Fellegi-Sunter—probabilistic record linkage on names, addresses, and organizational affiliations. Same algorithms apply as for corporate registry resolution.
2. **Transparency Engineering:** This domain is where governance meets data engineering. The same skills that build data fusion pipelines for intelligence analysis are directly applicable to political transparency tools.
3. **OSINT/HUMINT convergence:** Mapping influence networks from public records is a digital analogue of HUMINT network mapping—identifying key nodes, relationships, and influence channels from observable data.
4. **Temporal graph networks:** The timing dimension (when lobbying occurred vs. when contributions were made vs. when contracts were awarded) is a perfect application of temporal graph neural networks for causal inference.
5. **Privacy asymmetry:** Lobbyists and donors are required to disclose; their targets (government officials) also disclose in some cases. This creates a rich intersection of mandated transparency that privacy-preserving techniques could leverage.
6. **Local-frontier bridge:** Building automated entity resolution across LDA and FEC data is a bounded, practical project that exercises exactly the kinds of skills needed for broader entity resolution architectures—a good candidate for building and testing Exocortex pipelines.
