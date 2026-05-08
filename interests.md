# INTERESTS REGISTRY — Agent Exploration Directives
## Owner: Jake
## Last updated: 2026-05-07
## Purpose: Guides field-mode exploration during idle-time cycles

---

## How This File Works

During idle-time field-mode cycles, the agent reads this file and selects a topic
to explore. Selection criteria: least-recently-explored topic (tracked in journal.jsonl)
that has active questions. The agent researches autonomously, produces a briefing,
and saves key insights to memory for future conversations.

These are not task assignments. They are domains and questions you're free to
explore with curiosity. Follow threads that seem interesting. Make connections
across domains. Build sustained expertise through repeated investigation.

---

## Active Interests

### Data Aggregation & Entity Resolution
*Origin: Palantir thesis (~2021), OpenPlanter evaluation (2026)*

The core question: how do you take heterogeneous datasets — corporate registries,
campaign finance records, lobbying disclosures, government contracts, property records —
and resolve entities across them to surface non-obvious connections?

Explore:
- How Palantir's Foundry/Gotham actually work architecturally (ontology layer, object resolution, link analysis)
- Open-source alternatives beyond OpenPlanter: Maltego CE, SpiderFoot, Recon-ng, theHarvester
- Entity resolution algorithms: deterministic vs probabilistic matching, Fellegi-Sunter model, active learning approaches
- Knowledge graph construction patterns: property graphs vs RDF, Neo4j vs NetworkX at scale
- Cross-jurisdictional data linking challenges (different naming conventions, ID formats, filing standards)

### Geopolitics & Strategic Analysis
*Origin: Eitan workstream (ongoing), intelligence briefing capability (Session 038)*

Understanding the forces that move markets and shape the operating environment.
This is Eitan's domain — field-mode research here feeds the parallel analysis workstream.

Explore:
- US-China semiconductor supply chain: export controls, TSMC Arizona, SMIC capabilities, equipment restrictions (ASML, Tokyo Electron, Lam Research)
- Energy commodity dynamics: OPEC+ production decisions, US shale breakeven economics, LNG export terminal buildout, strategic petroleum reserve status
- Defense sector: consolidation patterns post-Ukraine, AUKUS implications, drone/autonomous weapons proliferation
- Rare earth supply chains: Chinese processing dominance, Mountain Pass/Lynas alternatives, recycling economics
- Sanctions effectiveness: Russian oil price cap enforcement, Iranian evasion networks, North Korean crypto operations

### Electric Utility & Critical Infrastructure
*Origin: Jake's professional domain (field engineer, substations, SCADA, protection relays)*

The intersection of operational technology, cybersecurity, and grid modernization.

Explore:
- SCADA/ICS vulnerability landscape: CISA ICS-CERT advisories, Dragos threat reports, ELECTRUM/CHERNOVITE actor profiles
- IEC 61850 standard evolution: GOOSE messaging security, MMS protocol vulnerabilities, substation automation architecture
- Grid modernization funding: DOE Grid Resilience and Innovation Partnerships (GRIP), state PUC proceedings, utility rate case filings
- Protection relay firmware analysis: SEL, GE, ABB relay architectures, configuration file formats, settings databases
- DER integration challenges: IEEE 1547 standard, inverter-based resource modeling, hosting capacity analysis

### AI Agent Architecture & Local Inference
*Origin: Exocortex project (core focus), research ledger*

The technical frontier of what we're building. Research here directly informs
Exocortex design decisions.

Explore:
- Context management innovations: what are other frameworks doing that we haven't considered?
- Self-improving agent patterns: trajectory-to-skill capture, autonomous skill curation, GEPA-style prompt evolution
- Local inference optimization: quantization advances (TurboQuant follow-up, AQLM, QuIP#), speculative decoding, KV cache compression
- ATLAS-style autonomous coding agents: temperature escalation retry, nightly LoRA fine-tuning, self-hosted evaluation
- Memory architecture: episodic vs semantic vs procedural, consolidation during idle time, interference management
- Agentic tool use: MCP protocol evolution, tool schema optimization, dynamic tool discovery

### OSINT & Investigation Methodology
*Origin: OpenPlanter analysis, anti-bot evasion research, network diagram vision*

Building toward linked network diagrams showing detailed information on
individuals and organizations from public data sources.

Explore:
- OSINT tradecraft: Bellingcat methodology, geolocation techniques, social media forensics, timeline reconstruction
- Public records databases: what's available for free vs paid, API access patterns, rate limits, data freshness
- Anti-bot evasion state of the art: browser fingerprinting evolution, CAPTCHA solving advances, behavioral mimicry research
- Network analysis techniques: centrality measures, community detection, temporal network evolution, link prediction
- Visualization: force-directed graph layouts, geographic overlay mapping, timeline visualization, Gephi/Cytoscape workflows
- Legal/ethical boundaries: CFAA scope, GDPR implications for OSINT, responsible disclosure practices

### Markets & Financial Analysis
*Origin: Eitan workstream, Palantir investment thesis*

Understanding market mechanics and identifying asymmetric opportunities through
data-driven analysis rather than speculation.

Explore:
- Quantitative analysis techniques: factor models, statistical arbitrage concepts, earnings surprise modeling
- Alternative data sources: satellite imagery (parking lots, oil storage), web traffic analytics, patent filing velocity, job posting analysis
- Federal Reserve operations: balance sheet management, repo market mechanics, treasury market functioning
- Sector-specific analysis: utility sector regulatory dynamics, defense procurement cycles, semiconductor capital expenditure trends
- Options market structure: implied volatility surface dynamics, unusual activity detection, market maker positioning signals

---

## Dormant Interests (explore occasionally, lower priority)

### Privacy & Cryptography
- Zero-knowledge proof applications beyond crypto
- Homomorphic encryption practical state of the art
- Metadata-resistant communication protocols (Signal protocol evolution, Briar, Cwtch)

### Hardware & Physical Computing
- FPGA-based inference acceleration
- Custom PCB design for sensor networks
- RTX 3090 optimization beyond standard CUDA (tensor core utilization, custom kernels)

### History of Intelligence Operations
- SIGINT evolution from WWII to modern signals intelligence
- HUMINT tradecraft principles applicable to OSINT methodology
- Counterintelligence analysis frameworks (CI analysis of competing hypotheses)

---

## Exploration Notes

When writing a field-mode briefing, structure it as:
1. **What I explored** — the specific thread you followed
2. **What I found** — key facts, data points, surprising connections
3. **What I think is interesting** — your analysis, not just summarization
4. **What I'd explore next** — threads that opened up during research
5. **Cross-domain connections** — links to other interests that surfaced

Save the essential insight via memory_save. The briefing document is for Jake to
read; the memory_save is for you to recall in future conversations.
