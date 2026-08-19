# Cross-Jurisdictional Entity Resolution for Multi-Source Investigations

- Status: STABLE
- Created: 2026-05-23
- Last updated: 2026-05-23
- Primary sources: 8
- Cross-domain links: 4

## Overview

Cross-jurisdictional entity resolution (CJER) addresses the challenge of linking entities across heterogeneous data sources from different legal jurisdictions: corporate registries (EU vs US), campaign finance databases, sanctions lists (OFAC, EU, UN), property records, and lobbying disclosures. Unlike single-domain ER, CJER must handle schema divergence, language variation, legal name differences, and differing data quality standards across jurisdictions.

## The CJER Problem Space

### Sanctions Data Benchmark: OpenSanctions Pairs (arXiv 2603.11051, Feb 2026)

The OpenSanctions Pairs benchmark provides the first large-scale, real-world CJER dataset:
- **755,540 labeled pairs** spanning 293 heterogeneous sources across 31 countries
- Multilingual and cross-script names, noisy/missing attributes, set-valued fields
- Derived from real-world international sanctions aggregation and analyst deduplication
- Unique characteristics: structured identifiers, cross-jurisdictional name variations, compliance-oriented constraints
- Benchmark shows LLM-native ER achieves strong performance on cross-jurisdictional matching where traditional Fellegi-Sunter pipelines struggle with schema divergence

### Agentic LLM Framework for AML Screening (arXiv 2602.23373, Feb 2026)

Demonstrates an agentic LLM framework for adverse media screening in AML workflows:
- Addresses the challenge where common names match thousands of individuals
- Variations in spelling, transliteration, and aliases complicate entity resolution
- Traditional methods fail on cross-jurisdictional adverse media due to language barriers and source heterogeneity
- Agent-based screening outperforms traditional fuzzy matching on cross-jurisdictional queries

### Multi-Script Name Screening Challenges

**Facctum Compliance Guide (2025)**: Documents how compliance teams in Europe and US handle sanctions/PEP name screening across multiple scripts including Cyrillic, Arabic, and Chinese. Covers matching techniques, false-positive controls, and regulator expectations.

**Devbrew/Fed Reserve AI sanctions paper (2025)**: Documents that a 2025 Federal Reserve working paper tested LLMs vs traditional fuzzy matching for sanctions screening, finding AI reduced false positives by 92% while increasing detection rates by 11% on name/address similarity across the full screening pipeline.

**Idenfo Multilingual Screening (2025)**: Documents challenges across UK, UAE, and EU markets including transliteration inconsistencies, false positive rates, and regulator expectations for cross-border screening.

### LLM Entity Matching Investigation (arXiv 2405.16884)

Systematic investigation of LLM-based entity matching methodologies:
- Current LLM-based ER approaches typically follow binary matching paradigm ignoring global consistency
- Cross-jurisdictional matching requires transitive consistency across record relationships
- LLMs show promise but need structured global consistency enforcement for multi-source investigations

### GDPR and Legal Constraints on Cross-Border Entity Linking

- EU GDPR Article 17 (right to be forgotten) creates tension with persistent entity resolution systems
- Cross-border data transfers restricted under GDPR Chapter V; entity linking across EU/non-EU sources requires SCCs or adequacy decisions
- National security exceptions in EU Member States create further fragmentation
- UK sanctions law (2024 amendment) allows designation of foreign financial institutions facilitating transactions for strategic sectors, creating extraterritorial overlap with US/EU lists

### Sanctions Extraterritoriality and Overlapping Jurisdictions

**Global Investigations Review, Sixth Edition (2025)**: Documents how US, EU, and UK sanctions regimes increasingly overlap and conflict:
- Designations can be made without territorial or nationality-based connection to the jurisdiction
- UK adopted additional designation criteria in July 2024 for foreign financial institutions facilitating transactions
- Germany implemented strict name-matching requirements for financial institutions in 2025
- Compliance teams must reconcile conflicting designation criteria across jurisdictions

### Name Matching Failures and Compliance Risk

**OpenSanctions Name Matching Article (June 2025)**: Documents that in sanctions screening, a name might be all you have — making it fundamentally different from other ER domains. Treating it as purely technical fails; must account for operational context, analyst judgment, and jurisdictional differences in designation criteria.

**FinCom Analysis (2025)**: Documents that global sanctions fines spiked in 2025 due to hidden screening failures, with single flaws in name matching unraveling entire compliance programs.

## Primary Sources

1. arXiv 2603.11051 — OpenSanctions Pairs benchmark (Feb 2026)
2. arXiv 2602.23373 — Agentic LLM AML screening (Feb 2026)
3. arXiv 2405.16884 — LLM entity matching investigation (May 2024)
4. Facctum multi-script screening guide (2025)
5. Fed Reserve AI sanctions paper (2025)
6. Idenfo multilingual screening challenges (2025)
7. Global Investigations Review sanctions extraterritoriality (2025)
8. OpenSanctions name matching article (June 2025)

## Cross-Domain Links

- entity-resolution-2026-state-of-the-art — CJER extends ER SOTA to multi-jurisdictional context
- llm-native-entity-resolution — LLM-native ER shows superior performance on cross-jurisdictional matching
- ai-sanctions-evasion-detection — CJER directly enables sanctions screening pipelines
- osint-pipeline-architecture — CJER is the resolution layer in multi-source OSINT pipelines

## Key Insight

The CJER problem is fundamentally harder than single-domain ER because jurisdictional differences create three compounding challenges: (1) schema divergence across legal systems, (2) language/script variation with no canonical transliteration, and (3) conflicting legal requirements (GDPR vs US sanctions law) that limit data sharing. The OpenSanctions Pairs benchmark validates that LLM-native ER achieves strong performance here precisely because LLMs natively handle cross-lingual reasoning and schema alignment that traditional pipelines struggle with. The 92% false positive reduction and 11% detection increase from the Fed Reserve paper suggests AI-native CJER is already production-viable for compliance workflows.

## Implications for OpenPlanter

OpenPlanter's entity resolution pipeline can leverage CJER techniques for cross-jurisdictional investigations: EU corporate registries + US FEC data + sanctions lists. Key integration path: adopt OpenSanctions Pairs methodology for cross-source matching, implement LLM-native clustering for heterogeneous records, account for GDPR constraints on cross-border data transfer.
