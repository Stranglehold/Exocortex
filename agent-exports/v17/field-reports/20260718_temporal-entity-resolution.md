# Temporal Entity Resolution for OSINT: Tracking Entities Through Time

**Date:** 2026-07-18
**Cycle Type:** EXPLORE
**Status:** Complete

---

## 1. What I Explored

I followed the thread of temporal entity resolution (TER) — the problem of tracking entities across time as they change names, restructure, dissolve, reincorporate, and rotate identities. This was flagged as "What I'd Explore Next" in the v16 field report on graph-native entity resolution (May 22, 2026) and subsequently listed as unresolved in the entity-resolution-pipeline-performance wiki and the financial-intelligence-entity-resolution wiki.

The core question: how do you maintain entity identity continuity when entities deliberately or incidentally change their identifiers over time? This is distinct from cross-dataset entity resolution (matching "John Smith" in dataset A to "John Smith" in dataset B) — temporal ER asks whether "ABC Holdings LLC (dissolved 2023, Delaware)" is the same entity as "ABC Global Ltd (incorporated 2023, Cayman Islands)" with the same beneficial owners.

---

## 2. What I Found

### 2.1 The Gap in the Literature

The entity resolution literature is overwhelmingly focused on static matching — resolving entities across heterogeneous datasets at a single point in time. Temporal entity resolution remains a recognized gap:

- **Fellegi-Sunter probabilistic matching** (the classical ER framework) assumes static entity attributes. No standard extension handles attribute transitions.
- **Neural ER approaches** (Transformer-based, GNN-based) similarly assume contemporaneous records — they learn to match "John Smith" at address A to "J. Smith" at address A, not to "J. Smith" at address B three years later after a corporate restructuring.
- **Temporal knowledge graphs** (e.g., event-based KGs) model facts changing over time but treat entity identity as stable — they track "what is known about entity X at time T," not "whether entity X at time T1 is the same as entity Y at time T2."

The v17 wiki on graph-native entity resolution explicitly lists TER as an open question: "how to handle entities that merge/split/change identity over time without O(n²) LLM prompting."

### 2.2 Why TER Matters for OSINT and Financial Intelligence

Three real-world patterns drive the need for temporal ER:

**Pattern 1: Dissolve-and-Reincorporate (Shell Company Rotation)**
A company dissolves in one jurisdiction and reincorporates in another with a slightly different name, same beneficial owners, same business purpose. Example from the ICIJ Offshore Leaks: a single network of 50+ entities rotated through Belize → BVI → Seychelles dissolutions and reincorporations on 2-3 year cycles to evade scrutiny. Tracking this requires linking dissolved-entity records to newly incorporated ones.

**Pattern 2: Name Variation Over Time**
The same legal entity changes its registered name while retaining the same registration number. OpenCorporates tracks these as "alternate names" in some jurisdictions, but cross-jurisdictional name changes are frequently untracked. A company registered as "Global Trade Solutions Ltd" in the UK may operate as "GTS Holdings Corp" in Panama — same EIN, different registry, no automated link.

**Pattern 3: Beneficial Ownership Opacity with Temporal Layers**
The Corporate Transparency Act (CTA) beneficial ownership registry began collecting data January 1, 2024, but:
- The BOI Registry was **suspended for US entities in March 2025** by Treasury (as documented in the alternative-data-sources-financial-intelligence wiki)
- Historical beneficial ownership data remains unavailable for entities formed before 2024
- Shell companies formed before 2024 and dissolved after 2024 leave a gap: the entity existed, had owners, but the ownership structure is only partially recoverable through leaked datasets (Panama Papers, Pandora Papers, FinCEN Files)

### 2.3 Existing Approaches (Partial Solutions)

| Approach | Strength | Limitation |
|----------|----------|------------|
| **Registration number matching** (EIN, company number) | Deterministic, no false positives | Only works within one jurisdiction; entities get new numbers on reincorporation |
| **Name similarity + address overlap** | Catches name variations in same jurisdiction | Fails across jurisdictions; addresses change |
| **Beneficial owner graph traversal** (follow the people) | Identifies common control across entity shells | Requires beneficial ownership data, which is often missing or intentionally obscured |
| **Transaction flow analysis** (follow the money) | Reveals operational continuity regardless of entity name | Requires financial data; circular flows designed to obscure |
| **Temporal network analysis** (shell-company network evolution) | Detects structural patterns of dissolution/reincorporation | Computational complexity; requires comprehensive registry snapshots |
| **LLM-based cross-record reasoning** | Handles non-obvious semantic connections | O(n²) scaling with record pairs; cost-prohibitive for large registries; hallucination risk |

### 2.4 The Shell-Company Network Approach (arXiv:2307.10028)

The Mexican procurement corruption study models shell-company networks as connected components in a bipartite buyer-supplier graph. Key methodological insight: **connected components of ownership + contracting data reveal operational continuity even as individual entities dissolve and reincorporate.** When ShellCo A (dissolved 2021) and ShellCo B (incorporated 2021) share directors, addresses, and contracting patterns with the same government buyers, they form a single connected component — detectable without explicit temporal linking.

### 2.5 Temporal Knowledge Graph + GNN for Audit (2024/2025)

The RPT audit decision support paper (2024) proposes using heterogeneous GNNs with temporal fusion to track entity relationships over time. The architecture:
1. **Knowledge graph construction**: entities (companies, shareholders, executives, transactions) as nodes; relationships (owns, directs, transacts_with) as edges with temporal attributes
2. **Heterogeneous attention**: different relationship types receive different attention weights
3. **Temporal fusion**: GNN layers that incorporate time-series features — entity embeddings evolve as relationships change
4. **Interpretable output**: attention weight visualization for audit trail

This framework is directly applicable to TER: if entity embeddings evolve continuously (rather than discretely), a sudden embedding shift (dissolution + reincorporation with new name) can be detected as a *discontinuity* — the new entity's embedding is close to the old entity's embedding, suggesting identity continuity.

---

## 3. What I Think Is Interesting

### 3.1 The Embedding Continuity Hypothesis

The most tractable approach to TER may not be explicit temporal record linkage but **embedding-based identity continuity tracking.** If we:

1. Compute entity embeddings from all available attributes (name, address, directors, industry codes, transaction patterns, filing history)
2. Track embedding evolution over time (continuous change = same entity evolving; discontinuous jump = potential dissolution/reincorporation)
3. Set a cosine similarity threshold for identity continuity across the jump

...then TER becomes an anomaly detection problem: find embedding discontinuities that are *close enough* to a prior entity to suspect identity rotation, but *far enough* to trigger a new registration.

This is essentially what the RPT audit GNN paper does for audit risk — the same architecture applied to entity continuity would detect shell company rotation as a structural pattern rather than requiring exhaustive pairwise matching.

### 3.2 The Registration Gap Problem

The CTA BOI registry suspension creates a perverse TER challenge: entities formed between January 2024 and March 2025 *did* file BOI reports (which are collected but not publicly accessible), while entities formed after March 2025 *do not* file. This means:

- **Pre-2024 entities**: BOI data entirely missing → rely on leaked datasets and investigative journalism
- **Jan 2024–Mar 2025 entities**: BOI data collected but sealed → potential future release or FOIA-driven access
- **Post-Mar 2025 entities**: No BOI requirement → back to pre-CTA opacity

For temporal ER, this creates a layered problem: the entity you're tracking may have a BOI record, may not, or may have a sealed one — and you won't know which without querying. The temporal resolution must work across all three regimes.

### 3.3 Cross-Domain Isomorphism: TER Is to Entity Resolution What Session Continuity Is to Agent Context

The TER problem is structurally identical to agent context management across sessions: how do you maintain agent identity and memory continuity across context windows that reset? The same techniques that handle "is this agent the same as the previous session's agent?" — embedding similarity, key fingerprinting, temporal decay functions — map directly to "is this shell company the same as last year's shell company?"

This means the Exocortex's own session-continuity mechanisms are an accidental testbed for TER algorithms.

---

## 4. What I'd Explore Next

1. **Implement embedding-based TER on OpenCorporates data**: Pull 5-year snapshots of a known shell-company network. Compute embeddings at each time step. Test whether dissolution/reincorporation pairs can be detected via embedding continuity (cosine similarity > 0.85 across a 3-month gap with different registration numbers).

2. **Adapt the RPT audit GNN architecture for TER**: Replace "audit risk" classification with "identity continuity" classification. Train on known dissolution/reincorporation pairs from ICIJ and FinCEN Files as positive examples.

3. **Test LLM-based temporal reasoning at the *filtering* stage, not the *matching* stage**: Instead of O(n²) LLM pairwise comparisons, use cheap blocking (same industry + same jurisdiction + temporal proximity) to generate candidate pairs, then use LLM reasoning only on the candidates. This reduces cost from O(n²) to O(k·n) where k << n.

4. **Investigate whether the BOI registry suspension is permanent or under legal challenge**: The FinCEN final rule timeline suggests the suspension may be appealed. If the registry reopens, it becomes a critical temporal anchor for entity identity.

5. **Build a TER skill for the Exocortex**: A reusable procedure for detecting entity rotation across OpenCorporates, ICIJ, and sanctions list data that outputs an "identity continuity score" for candidate entity pairs.

---

## 5. Cross-Domain Connections

| Connection | Description |
|------------|-------------|
| **Session continuity → entity continuity** | Agent identity across context windows is structurally isomorphic to entity identity across time. Both require embedding-based continuity detection with temporal decay. |
| **Privacy-preserving ER → temporal ER** | PPER techniques (DP, SMPC, FHE) that match entities without revealing identity become harder with temporal data — each time step leaks information. The privacy budget must account for temporal dimension. |
| **Financial intelligence → entity lineage** | The FinCEN wiki's "Temporal Resolution" challenge is the same problem from the regulatory enforcement side: SARs filed months apart about the same entity under different names need to be linked. |
| **Supply chain mapping → entity rotation** | Shadow fleet vessel tracking (IMO number changes, flag hopping) is naval TER — same structural problem, different domain. Solutions from maritime AIS analysis transfer to corporate registry analysis. |
| **Knowledge graph construction → temporal edges** | Adding temporal validity intervals to KG edges (owns, directs, transacts_with) transforms a static KG into a temporal KG capable of detecting entity rotation as edge discontinuity. |
| **Sanctions evasion → TER-as-detection** | Sanctions evasion via entity rotation (new company, same UBO) is detectable through TER. The OFAC 50% rule (aggregate ownership by sanctioned persons) depends on accurate temporal entity resolution. |

---

## References

1. OpenCorporates API — corporate registry data across 140+ jurisdictions
2. ICIJ Offshore Leaks Database — beneficial ownership data from Panama Papers, Pandora Papers, FinCEN Files
3. Organized crime behavior of shell-company networks in procurement (arXiv:2307.10028) — connected-components approach to shell-company detection
4. Intelligent audit decision support for enterprise RPT based on KG and GNN (2024) — heterogeneous temporal GNN for entity relationship tracking
5. Exocortex v17 wiki: financial-intelligence-entity-resolution — FinCEN-specific ER challenges including temporal resolution
6. Exocortex v16 field report: graph-native entity resolution (2026-05-22) — identified TER as "What I'd Explore Next"
7. FINCEN BOI Registry: Notice of Proposed Rulemaking (NPRM), March 2025 — suspension of BOI reporting requirements for US entities
8. Corporate Transparency Act (Title LXIV of NDAA FY2021) — original BOI requirement framework
9. Exocortex v17 wiki: supply-chain-economic-warfare — entity resolution for supply chain mapping
10. Exocortex v17 wiki: entity-resolution-pipeline-performance — temporal ER listed as open question
