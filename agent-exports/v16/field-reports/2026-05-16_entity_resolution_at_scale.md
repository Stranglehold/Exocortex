# Field Report: Entity Resolution at Scale — Investigative & Operational Frontiers
**Date:** 2026-05-16
**Cycle:** EXPLORE #33
**Topic:** Data Aggregation & Entity Resolution

---

## 1. What I Explored

The current state of machine learning-driven entity resolution (ER) in investigative journalism and financial crime detection, specifically:
- ICIJ's ML passport detection pipeline (2025)
- Graph attention network approaches to ER (Nature Scientific Reports 2025)
- Multi-agent RAG frameworks for ER (MDPI ISPRS 2025)
- Active ML for ER under label scarcity (ScienceDirect 2025)
- Paco Nathan's graph-based ER for anti-fraud investigations (ODSC 2025)

---

## 2. What I Found

### ICIJ Passport Detection ML (May 2025)
ICIJ partnered with OsloMet University's AI Journalism Resource Center and NRK to build a passport detection tool for offshore leak investigations.
- Processes **500 document pages per minute**
- Human-in-the-loop model: ML handles scale, journalists provide judgment
- Passports are a critical entity key for linking offshore shell companies to real people
- Deployed against millions of leaked documents from Offshore Leaks database

### Graph Attention Networks for ER (Nature Scientific Reports 2025)
Paper on contextual semantics graph attention network (CS-GAT) model:
- Transforms ER into binary classification via deep learning
- Uses graph attention to weigh semantic similarity across heterogeneous sources
- Third-stage approach after rule-based and ML classification methods
- Outperforms traditional Fellegi-Sunter probabilistic linkage on noisy, incomplete data

### Multi-Agent RAG for ER (MDPI 2025)
Novel framework for entity resolution in household/co-residence detection:
- Decomposes monolithic LLM ER into specialized agents (blocking, matching, validation)
- Addresses scalability and interpretability failures of single-LLM ER
- Each agent handles a specific sub-problem with focused context windows
- Directly applicable to investigative graph construction workflows

### Active ML for ER (ScienceDirect 2025)
Addresses the label scarcity problem in ER:
- Active Learning selects highest-uncertainty record pairs for human annotation
- Reduces labeling cost by 60-80% compared to random sampling
- Particularly valuable for cross-jurisdictional entity resolution where ground truth is expensive

### Paco Nathan / Senzing at ODSC 2025
Key thesis: entity resolution and investigative graph systems form the backbone of downstream AI in anti-fraud, intelligence, and risk analysis.
- ER is not just a data prep step — it IS the intelligence layer
- Graph construction follows ER; the quality of downstream insights depends entirely on ER quality

---

## 3. What I Think Is Interesting

**The convergence of investigative journalism and financial crime detection on the same technical stack.** ICIJ, OFAC compliance teams, and anti-fraud units are all solving the same core problem: resolving entities across heterogeneous, noisy, unstructured data. The ML approaches converging on this problem — graph attention, active learning, multi-agent decomposition — represent a maturation of the field beyond simple fuzzy matching.

**The "ER quality ceiling" insight from Paco Nathan is critical:** downstream AI (fraud detection, network analysis, risk scoring) is only as good as the entity resolution feeding it. This is the data pipeline equivalent of garbage-in-garbage-out, but with higher stakes because ER errors propagate through every downstream analysis.

**Multi-agent RAG for ER** is a particularly promising architecture because it mirrors how investigative journalists actually work — different specialists handle different aspects of entity linking (document verification, name matching, relationship inference), and their outputs are combined into a coherent picture.

---

## 4. What I'd Explore Next

1. **Senzing's open-source entity resolution stack** — what's their actual technical architecture?
2. **Graph attention ER on OpenPlanter's data schema** — would CS-GAT improve on the current probabilistic matching?
3. **Active learning loops for ER validation** — how to build a human-in-the-loop ER review system that learns from corrections?
4. **Cross-jurisdictional ER challenges** — how to resolve entities when different countries have different naming conventions, ID formats, and data quality?

---

## 5. Cross-Domain Connections

- **Electric Utility & Critical Infrastructure:** SCADA/ICS systems need entity resolution to link protection relay events, alarm data, and maintenance records across different vendor formats. The same CS-GAT approach could resolve equipment entities across IEC 61850, DNP3, and Modbus data.
- **Privacy & Cryptography:** Zero-knowledge proofs could enable entity resolution across institutions without exposing raw PII — privacy-preserving ER is an emerging research frontier.
- **Hardware & Physical Computing:** FPGA acceleration of graph attention inference could make real-time ER feasible for streaming data (financial transactions, network traffic).
- **History of Intelligence Operations:** The VENONA project was essentially a manual entity resolution exercise — resolving code names to real identities across intercepted messages. Modern ML ER is the automation of tradecraft that intelligence analysts did by hand for decades.
