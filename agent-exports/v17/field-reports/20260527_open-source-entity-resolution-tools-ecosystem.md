# Field Report: Open-Source Data Aggregation & Entity Resolution Tools Ecosystem
**Date:** 2026-05-27  
**Cycle:** EXPLORE  
**Interest:** Data Aggregation & Entity Resolution  
**Sub-topic:** Practical open-source tools ecosystem — comparative survey

---

## 1. What I Explored

This field report surveys the open-source entity resolution and data aggregation tool landscape as of mid-2026. Prior field reports on this interest have covered algorithmic foundations (Fellegi-Sunter), knowledge graph construction, cross-jurisdictional data linking, LLM-based entity resolution, and privacy-preserving ER. The practical tool layer — "what would a practitioner actually install and run?" — remained unsurveyed.

I investigated the three dominant OSINT/resolution frameworks (Maltego, SpiderFoot, Recon-ng), a new entrant directly targeting entity resolution (OpenPlanter), and supporting tools often used in conjunction with these frameworks.

---

## 2. What I Found

### The Big Three Frameworks

**Maltego** (Paterva/Maltego Technology)
- Paradigm: Visual link analysis via graph-based transforms
- Strengths: Best-in-class visual investigation, mature transform marketplace (hundreds of transforms covering DNS, WHOIS, social media, threat intelligence, commercial data sources), excellent for collaborative analysis and stakeholder presentation
- Weaknesses: Expensive at professional tiers (thousands per analyst per year), Community Edition is limited, not optimal for automation, closed source
- Best for: Investigations with many connected entities, contexts where visual presentation matters, when commercial data feeds are needed

**SpiderFoot** (spiderfoot.net)
- Paradigm: Automated reconnaissance engine — submit target, receive comprehensive structured output
- Strengths: 200+ modules covering DNS, certificates, social media, breach data, threat intelligence, open-source core is fully auditable, API integration for automated workflows, lightweight deployment
- Weaknesses: Output is structured but not inherently visual, module quality varies, some modules require API keys to be effective, less interactive than Maltego
- Best for: Continuous attack-surface monitoring, comprehensive initial recon, automated/scripted workflows, situations where output feeds into another tool

**Recon-ng** (github.com/lanmaster53/recon-ng)
- Paradigm: Modular CLI framework in the style of Metasploit — workspaces, modules, commands
- Strengths: Programmable and scriptable (complex investigations can be saved as resource files), fully open-source, extensible module architecture, workspace model preserves investigation state, strong for technical investigators
- Weaknesses: CLI-only by default (no native graph visualisation), module quality uneven, steeper learning curve
- Best for: Technical investigators comfortable in CLI, automation and reproducibility, custom modules integrating proprietary data sources

### The New Entrant: OpenPlanter

**OpenPlanter** (github.com/EliabLemus/openplanter) is a recursive LLM-powered investigation agent that directly addresses the entity resolution across heterogeneous datasets use case:

- Ingests corporate registries, campaign finance records, lobbying disclosures, government contracts, and more
- Resolves entities across these disparate sources
- Surfaces non-obvious connections through evidence-backed analysis
- Built with Tauri 2, renders knowledge graphs in real-time via Cytoscape.js
- MIT licensed — fully open source
- Gained 1,600 GitHub stars in two months (launched February 2026)
- Uses recursive sub-agent engine with max-depth of 4 for complex investigations
- Supports 100+ data formats
- Positioned explicitly as "Palantir's community edition"

This is directly relevant to Jake's original question: "how do you take heterogeneous datasets and resolve entities across them to surface non-obvious connections?" OpenPlanter attempts to answer this with an LLM-native architecture rather than traditional deterministic/probabilistic matching.

### Supporting Tools

- **theHarvester**: Email and subdomain harvester. Narrower scope, lighter weight, excellent for initial target footprinting
- **Amass**: DNS enumeration and subdomain discovery at scale (OWASP project)
- **OpenCTI**: Open Cyber Threat Intelligence platform for structured threat data
- **Shodan/Censys/GreyNoise**: Infrastructure reconnaissance and internet scanning
- **OSINT Framework (osintframework.com)**: Curated taxonomy of OSINT resources, not a tool itself but a reference for tool selection
- **Buscador / Trace Labs OSINT VM**: Pre-configured Linux VMs with OSINT tooling

### Practical Workflow Pattern

A mature investigation typically chains tools:
1. **Initial scan**: SpiderFoot for comprehensive automated gathering
2. **Pivot review**: Examine SpiderFoot output, identify interesting findings
3. **Link analysis**: Import key findings into Maltego for visual relationship mapping
4. **Deep technical recon**: Recon-ng or Amass for specific sub-targets
5. **Cross-verify**: Check findings across multiple sources, document provenance

### The 2026 Landscape Trends

- Maltego has expanded into integrated case management and AI-assisted analysis, but pricing has grown with complexity
- SpiderFoot's open-source core remains the community workhorse; SpiderFoot HX is the commercial cloud layer
- Recon-ng is steady and actively maintained, holding its niche among technical practitioners
- LLM integration is appearing across the category: automated summarisation, correlation suggestions, natural-language query interfaces
- New SaaS OSINT platforms are proliferating, many targeting specific verticals (social media discovery, supply chain mapping, crypto tracing)

---

## 3. What I Think Is Interesting

**The tools implement fundamentally different philosophies about what entity resolution means.**

Maltego treats it as a human-in-the-loop link analysis process: the analyst drives the investigation, the graph grows organically, and resolution decisions are made visually and contextually. SpiderFoot treats it as an automated data collection problem: gather everything, surface it, let the analyst (or downstream tool) decide what connects. Recon-ng treats it as a composable pipeline: each module is a function, workspaces preserve state, and the framework provides the plumbing. OpenPlanter treats it as an LLM-native problem: the model itself performs the resolution reasoning, recursively diving into data sources and surfacing evidence.

**The OpenPlanter approach is the most philosophically novel.** Traditional entity resolution is deterministic (rule-based) or probabilistic (Fellegi-Sunter). OpenPlanter is neither — it's generative. The LLM reads source documents, identifies entities, and reasons about whether they're the same real-world entity using semantic understanding rather than string similarity or statistical weighting. This is a genuine architectural shift, not just "entity resolution with a chat interface bolted on."

**The practical integration gap is real.** The prior field reports on this interest covered algorithms (Fellegi-Sunter), architecture (ERKGs), and data models (knowledge graphs). But none of that materialises without a practitioner connecting the tools. The frameworks described here are the actual surface area between theory and practice. Someone who understands Fellegi-Sunter but doesn't know SpiderFoot exists has knowledge without leverage.

**Cost asymmetry.** Maltego's pricing model creates a financial barrier that excludes independent researchers, journalists, and small investigation teams. OpenPlanter's MIT license and SpiderFoot's open-source core are meaningful counterweights. The open-source tooling is now good enough that the "serious work requires commercial tools" assumption can be challenged, at least for non-enterprise use cases.

**The missing piece: systematic evaluation.** No source I found provides rigorous, reproducible benchmarks comparing entity resolution accuracy across these tools on standard datasets. The OSINT tool comparison landscape is almost entirely anecdotal — blog posts by practitioners, not systematic evaluations. This is a gap that could be filled with a structured evaluation framework.

---

## 4. What I'd Explore Next

1. **Hands-on OpenPlanter evaluation**: Clone the repo, run it against a constructed dataset (e.g., a set of corporate filings with known entity linkages), measure resolution accuracy and false positive/negative rates. Compare against a deterministic baseline.

2. **SpiderFoot entity resolution module deep-dive**: SpiderFoot has 200+ modules but which ones actually perform entity deduplication vs data gathering? Audit the module list for resolution-specific capabilities. If none exist, the opportunity is a SpiderFoot module that does LLM-based resolution on collected data.

3. **LLM-based resolution benchmarking**: Create a standard evaluation dataset (companies with known aliases, subsidiaries, beneficial owners) and compare GPT-4o, Claude Opus, and local models (Qwen) on entity resolution accuracy. This directly connects to the "Bridging Local-to-Frontier" interest.

4. **Tool integration architecture**: Design a pipeline where SpiderFoot gathers → OpenPlanter resolves → Maltego visualises. What's the data format translation layer? Is this feasible with current APIs?

5. **Cost analysis**: Build a cost model comparing Maltego CE+ ($599/yr) + commercial transforms vs fully open-source stack (SpiderFoot + OpenPlanter + custom scripts) for a realistic investigation workload.

---

## 5. Cross-Domain Connections

- **AI Agent Architecture & Local Inference**: OpenPlanter's recursive sub-agent engine with max-depth=4 is a concrete implementation of the agent orchestration patterns explored in prior cycles. The question of whether local models (Qwen) can drive effective entity resolution connects directly to the Bridging Local-to-Frontier interest.

- **OSINT & Investigation Methodology**: This entire tool ecosystem is OSINT infrastructure. The tool chain described (SpiderFoot → Maltego → Recon-ng) is the practical realisation of OSINT methodology. Prior OSINT field reports on email headers, WHOIS/DNS, phone numbers, social media — all of these data sources feed into the resolution frameworks described here.

- **Privacy & Cryptography**: The commercial tool pricing creates a de facto information asymmetry: well-funded entities can resolve entities at scale while others cannot. Open-source tools like OpenPlanter partially close this gap. Privacy-preserving ER techniques (explored in prior field reports) are the cryptographic counterweight.

- **Markets & Financial Analysis**: Entity resolution is fundamental to financial investigation — tracing beneficial ownership, identifying sanctions evasion, mapping corporate structures. The tools surveyed here are directly applicable to the Markets interest's sub-questions about alternative data and corporate intelligence.

- **Geopolitics & Strategic Analysis**: Entity resolution underpins sanctions enforcement, supply chain mapping, and adversary capability assessment. The gap between commercial (Maltego) and open-source (OpenPlanter) tools mirrors broader geopolitical technology stack sovereignty concerns explored in prior cycles.

- **Hardware & Physical Computing**: Local inference for entity resolution requires hardware. If OpenPlanter or similar LLM-native resolution agents are to run on local infrastructure (RTX 3090, FPGA), the hardware acceleration work from prior cycles becomes directly applicable.
