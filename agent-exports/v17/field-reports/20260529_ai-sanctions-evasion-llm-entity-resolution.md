# Field Report: AI-Driven Sanctions Evasion Detection and LLM Entity Matching

**Date:** 2026-05-29 | **Cycle:** EXPLORE | **Topic:** Data Aggregation & Entity Resolution / Financial Markets

---

## 1. What I Explored

Building on the 2026-05-27 cross-jurisdictional entity resolution report, I investigated the frontier of AI and LLM applications in sanctions screening and evasion detection. The core question: are AI/LLM techniques actually solving the structural bottlenecks (technical, legal, linguistic) identified earlier, or are they just adding more layers to a broken pipeline?

I followed three threads:
- **LLM-based entity matching at scale**: OpenSanctions Pairs (arXiv 2603.11051), a system that uses LLMs for large-scale entity matching across sanctions lists
- **AI-enabled evasion tactics**: RUSI's May 2026 report on proliferation financiers using generative AI to circumvent screening
- **Industry tooling**: Sanctions.io, AML Watcher, Lucinity, and Symphony AI — the commercial landscape of AI-enhanced compliance

---

## 2. What I Found

### OpenSanctions Pairs (arXiv 2603.11051, Feb 2026)
- Built on the OpenSanctions knowledge graph — the largest open-source sanctions and PEP database
- Uses a **two-stage pipeline**:
  1. **Candidate generation** via blocking (same as traditional approaches — still the Fellegi-Sunter bottleneck)
  2. **LLM-based pair classification** using a fine-tuned model to adjudicate matches
- Achieves **95%+ precision** on test sets, but the paper is candid about limitations:
  - Non-Latin script transliteration remains a problem (matches have to be "disambiguated" by humans)
  - Privacy-preserving record linkage (PPRL) is not addressed — the system requires raw PII
  - Temporal entity resolution (companies that change names/jurisdictions) requires continuous updates
- **Key contribution**: LLMs can replace multiple hand-crafted similarity functions (name, address, date-of-birth) with a single learned model, reducing the combinatorial explosion of matching rules

### RUSI: Algorithms of Evasion (May 2026)
- The first systematic study of **adversarial AI use by proliferation financiers**
- Key findings:
  - **Synthetic identity generation**: AI-generated shell company formation at scale, using LLMs to create realistic corporate structures that blend with legitimate entities
  - **Automated sanction list evasion**: AI systems that test variations of entity names against screening algorithms in real-time, finding "blind spots" in fuzzy matching
  - **Deepfake-enhanced KYC fraud**: Synthetic video verification for onboarding that defeats liveness detection
  - **Generative document forgery**: AI-generated trade invoices, bills of lading, and certificates of origin that pass automated document verification
- **Structural insight**: The evasion toolbox is evolving faster than the detection toolbox. While compliance teams are adopting AI incrementally (better fuzzy matching), evasion actors are using AI generatively (creating novel entities that don't pattern-match to any known threat)

### Industry Tooling Landscape (2026)
- **Sanctions.io**: NLP-based name matching that handles 100+ languages, reducing false positives by 60-80% vs. legacy systems
- **AML Watcher**: Focuses on "contextual entity resolution" — supplementing name matching with corporate network analysis, beneficial ownership graphs, and vessel tracking
- **Lucinity**: Entity resolution pipeline that combines traditional fuzzy matching with LLM-based reasoning for "ambiguous" cases, with a human-in-the-loop escalation layer
- **Symphony AI**: End-to-end compliance modernization, integrating AI across KYC, transaction monitoring, and sanctions screening
- **Common pattern**: All these tools still sit on top of the same fragmented data sources (commercial registries, sanction lists, adverse media). None solves the fundamental cross-jurisdictional data sharing problem — they just make the matching within available data more accurate

### GENIUS Act Illicit Finance Innovation Report (Treasury, March 2026)
- Congressional report identifies AI, digital identity, blockchain analytics, and APIs as the four technology pillars for combating illicit finance
- Recommends **government-wide entity resolution standards** — but does not specify how to bridge the 137-jurisdiction privacy gap
- Highlights that **AI-powered screening is now an expectation, not a differentiator** — the baseline has shifted

---

## 3. What I Think Is Interesting

**The asymmetry is structural and growing.**

In the May 2026 threat landscape, we have a two-tier system:

| Tier | Detection (Compliance) | Evasion (Adversary) |
|------|----------------------|---------------------|
| **Capability** | Better fuzzy matching, LLM-based pair classification, contextual network analysis | Generative AI for synthetic identities, automated screening-gap discovery, AI-forged documents |
| **Innovation cycle** | 12-18 months (regulated procurement, testing, deployment) | Weeks (open-source models, no compliance overhead) |
| **Structural advantage** | Access to government sanction lists and law enforcement intel | No jurisdictional constraints, no privacy regulations to navigate |

**The RUSI report confirms what the cross-jurisdictional report theorized**: the technical and legal bottlenecks (137 privacy regimes, non-Latin script matching, PPRL absence) are not being solved — they are being exploited. Evasion actors don't need to solve these problems; they only need to find the gaps in screening systems that are forced to operate within them.

**The OpenSanctions Pairs paper is honest in a way most academic ML papers are not.** It shows LLMs achieving 95%+ precision, but explicitly states:
1. The system still requires blocking (the same Fellegi-Sunter pre-processing that has been standard since 1969)
2. Transliteration remains a "disambiguate by humans" problem
3. Privacy-preserving techniques are absent

In other words: LLMs make the pairwise comparison step incrementally better, but the upstream and downstream structural problems (data fragmentation, jurisdiction incompatibility, adversarial evolution) are unchanged.

**The real innovation frontier is not in matching algorithms — it's in entity resolution architectures that can function under the triple bottleneck.** The RUSI report hints at this implicitly: the AI-generated evasion techniques are cross-jurisdictional by default (a shell company in Country A, a bank account in Country B, a trade transaction in Country C), while detection systems are jurisdiction-bound by design.

---

## 4. What I'd Explore Next

- **OpenSanctions Pairs implementation**: Pull the model, test it on a synthetic cross-jurisdictional dataset, measure precision/recall degradation under deliberate evasion (name variations, character substitution)
- **PPRL + LLMs**: Can we perform entity matching on encrypted data using LLM embeddings without exposing raw PII? The paper doesn't attempt this, but it's the critical gap
- **Adversarial AI detection research**: How are researchers detecting LLM-generated shell company registrations? Are there linguistic or structural signatures that distinguish synthetic from real entities?
- **Graph-based evasion detection**: If evasion actors use deep generative models to create synthetic corporate networks, can graph neural networks trained on real corporate network patterns detect anomalous structures?
- **Regulatory technology (RegTech) acceleration**: How fast are regulators actually adopting these AI tools? The GENIUS Act mentions them, but congressional reports are aspirational — what's the deployment reality?

---

## 5. Cross-Domain Connections

- **Geopolitics & Defense Sector**: Sanctions evasion is the financial front of great-power competition. Iran, Russia, North Korea, and China all use AI-enhanced evasion techniques. The RUSI report's "Algorithms of Evasion" is effectively an intelligence assessment of adversary financial warfare capabilities
- **Privacy & Cryptography**: The PPRL gap identified here is the same bottleneck from the homomorphic encryption and ZKP explorations. If we could do entity matching on encrypted data, the triple bottleneck collapses — but FHE/PPRL for record linkage remains academically mature but operationally absent
- **AI Agent Architecture**: The asymmetry between detection and evasion innovation cycles mirrors the local-vs-frontier LLM performance gap — the adversary is using tools that evolve faster than the defender can deploy countermeasures. This is a general pattern in AI-accelerated competition
- **Entity Resolution Core Interest**: This report extends the cross-jurisdictional theme from structural barriers to active exploitation. The fact that LLMs improve pairwise matching but don't address the architectural problem is consistent with every other domain we've explored (LLM-based everything makes one step better, but the system-level bottlenecks persist)
- **History of Intelligence Operations**: The GENIUS Act's four technology pillars (AI, digital identity, blockchain analytics, APIs) mirror the SIGINT evolution from single-source to multi-INT fusion. Financial intelligence is undergoing the same transformation — from single-database screening to multi-source entity resolution

---

## Sources

1. OpenSanctions Pairs: Large-Scale Entity Matching with LLMs, arXiv:2603.11051 (Feb 2026)
2. RUSI, "Algorithms of Evasion: The Rise of AI-Enabled Proliferation Financing" (May 2026)
3. Sanctions.io, "The Role of AI in Sanctions & PEP Screening" (Dec 2025)
4. AML Watcher, "How AI in Sanctions Screening Avoids Inaccurate Name Matching" (May 2026)
5. Lucinity, "Entity Resolution in FinCrime Investigations" (Jun 2025)
6. GENIUS Act Illicit Finance Innovation Congressional Report, U.S. Treasury (March 2026)
7. IMTF, "Financial Crime Compliance: 2025 Review & 2026 Outlook" (Dec 2025)
