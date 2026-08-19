# Field Report: Data Aggregation & Entity Resolution

**Date:** 2026-05-15
**Topic:** Data Aggregation & Entity Resolution
**Cycle:** EXPLORE

---

## 1. What I Explored

The thread: how modern entity resolution systems work, from Fellegi-Sunter probabilistic matching through Palantir's ontology architecture to open-source alternatives like Splink.

Starting question: OpenPlanter uses deterministic entity resolution (exact CPF_ID lookups, string matching). What's the state of the art for linking heterogeneous datasets where no common key exists?

## 2. What I Found

### Fellegi-Sunter Model (1969) — Still Foundational
The Fellegi-Sunter framework remains the conceptual backbone of probabilistic record linkage 55+ years later. Key concepts:
- Each record pair has match (m) and non-match (u) probabilities per attribute
- Weights are log-odds ratios: w = log(m/u)
- Pairs are classified by comparing posterior match probability against thresholds
- Modern ML systems estimate m/u parameters that Fellegi-Sunter couldn't compute directly

### Splink — Modern Fellegi-Sunter Implementation
- Open-source (Python/SQL/Spark), developed by UK Ministry of Justice
- Implements scalable Fellegi-Sunter with EM algorithm for parameter estimation
- Supports active learning: human-in-the-loop labeling to refine match probabilities
- Handles billions of comparisons via blocking strategies (never compare all pairs)
- GitHub: OlivierBinette/Awesome-Entity-Resolution lists 100+ tools; Splink is the top probabilistic matcher

### LLM-Assisted Record Linkage (2026)
- New framework integrates Fellegi-Sunter with selective LLM usage
- FS produces initial prior match probability P_prior(x,y)
- LLM only invoked on uncertain pairs (threshold band), not all pairs
- Reduces LLM cost by 90%+ while improving accuracy on ambiguous matches
- Published in official statistics journals — government-grade validation

### Palantir's Ontology Architecture
- Five-layer enterprise AI operating system:
  1. Semantic layer — maps raw data to business objects
  2. Kinetic layer — enforces rules, constraints, workflows
  3. Dynamic layer — real-time operations, agent runtime
  4. Integration layer — multimodal data sources
  5. Security layer — row/column-level access control
- Ontology is NOT a thin semantic layer — it's a multimodal system with dozens of components
- Handles millions of reads/writes with unified reality view
- Community requests for true Neo4j-style graph capabilities (property graphs, not RDF)

### Open-Source Entity Resolution Landscape
- Splink (Fellegi-Sunter, probabilistic)
- Maltego CE (link analysis, visualization)
- SpiderFoot (automated OSINT, passive collection)
- Recon-ng (reconnaissance framework)
- NetworkX vs Neo4j for knowledge graph construction

## 3. What I Think Is Interesting

The gap between OpenPlanter's current implementation and Fellegi-Sunter is significant but bridgeable. OpenPlanter resolves entities through shared CPF_IDs from OCPF data — this works within Massachusetts campaign finance but breaks when linking to:
- USASpending vendor names (different formatting, no CPF_ID)
- SAM.gov UEI numbers (different namespace)
- OSHA inspection records (employer names, not CPFs)
- EPA ECHO facility records (facility names, addresses)

The Fellegi-Sunter model handles exactly this: heterogeneous identifiers across datasets with no common key. Blocking strategies reduce the comparison space from O(n²) to manageable levels.

Most interesting finding: LLM-assisted record linkage uses Fellegi-Sunter as the cheap first pass, then invokes LLMs only on the uncertain band. This is a pragmatic hybrid — don't throw away 55 years of statistical work, augment it selectively.

## 4. What I'd Explore Next

1. Splink integration test with OpenPlanter's OCPF + USASpending datasets
2. Blocking strategy design for political finance + government contracts
3. Active learning workflow: what pairs need human review, what can be automated
4. Property graph vs RDF for the knowledge layer (Neo4j vs JanusGraph)
5. Cross-jurisdictional entity resolution: how CPF_ID maps to FEC candidate IDs to SAM.gov UEI

## 5. Cross-Domain Connections

- **Privacy & Cryptography**: k-anonymity and differential privacy are relevant when publishing linked datasets — resolution creates re-identification risk
- **AI Agent Architecture**: Palantir's ontology layer is essentially a knowledge graph that agents can query — directly relevant to OpenPlanter's agent capabilities
- **Electric Utility & Critical Infrastructure**: SCADA entity resolution (linking IEDs across substations) uses similar graph patterns to political entity resolution
- **History of Intelligence Operations**: SIGINT entity resolution (linking callsigns, frequencies, locations) is the historical precedent for what Palantir does today

---

*Key deliverable: This report maps the entity resolution landscape from 1969 Fellegi-Sunter through 2026 LLM-assisted methods, identifying a clear upgrade path for OpenPlanter's current deterministic resolution.*
