# Cryptocurrency On-Chain Analysis for OSINT Investigations

**Status:** STABLE
**Created:** 2026-06-08
**Last Updated:** 2026-06-08

## Summary

Cryptocurrency on-chain analysis for OSINT — techniques, tools, and methodologies for tracing blockchain transactions to identify individuals, organizations, and illicit financial networks using publicly available ledger data. Covers blockchain forensic foundations, entity attribution & clustering, tool landscape, Agentic Blockchain Forensics (ABF) paradigm, cross-domain structural isomorphisms, and integration with Exocortex entity resolution pipelines.

---

## 1. Blockchain Forensic Foundations

Public blockchains (Bitcoin, Ethereum, Solana, TRON) are inherently transparent ledgers where every transaction is recorded and verifiable. On-chain analysis operationalizes this transparency to:

- **Trace fund flows:** Follow UTXO chains (Bitcoin) or account-based transfers (Ethereum/EVM) through multiple hops to identify source/destination wallets.
- **Cluster addresses:** Group addresses controlled by the same entity using heuristics like shared input ownership (Bitcoin), deposit address reuse, and change address detection.
- **Entity attribution:** Map clustered addresses to known entities (exchanges, mixers, DeFi protocols, darknet markets, sanctions-listed addresses) via public tag databases and off-chain intelligence.

Key forensic primitives:
- **CoinJoin detection:** Identify equal-denomination outputs and transaction graph sub-structures indicating privacy-enhancing mixing (Wasabi, Samourai Whirlpool).
- **Peel chain analysis:** Trace sequential splitting of a large UTXO into smaller outputs, typically used for gradual fund movement.
- **Cross-chain tracing:** Follow assets across blockchain bridges and decentralized exchanges (DEXs) using centralized bridge custody addresses, wrapped token mint/burn events, and temporal correlation.

---

## 2. Entity Attribution & Clustering

**Heuristic-based clustering (Bitcoin):**
- **Multi-input heuristic (H1):** All input addresses in a single transaction are controlled by the same entity.
- **Change address detection (H2):** Identify the change output by script type matching, fresh address generation, and non-round output values.
- **Address reuse:** Repeated use of the same receiving address strongly indicates single ownership.

**Ethereum/EVM clustering:**
- **Deposit address reuse:** Exchanges and services often generate a single deposit address per user.
- **Gas payment analysis:** Fee-paying addresses linked across transactions.
- **Contract interaction graphs:** DeFi protocol usage patterns, MEV bot activity, and AMM LP concentration reveal operational clusters.

**Entity attribution sources:**
- OFAC SDN List (sanctioned addresses)
- Chainalysis, Elliptic, TRM Labs commercial tag databases
- Internet Archive / Wayback Machine for historical address mentions
- Open-source tag repositories (Etherscan labels, BitcoinAbuse, WalletExplorer)

**Fellegi-Sunter isomorphism:** The clustering problem — probabilistically linking blockchain addresses to real-world entities — is structurally isomorphic to entity resolution. Address clustering heuristics (H1, H2) function as blocking rules; temporal features (first/last activity, transaction frequency) serve as matching features; and LLM-assisted entity resolution (see [[llm-assisted-entity-resolution]]) can be applied to correlate on-chain names (ENS, Unstoppable Domains) with off-chain identities.

---

## 3. Tool Landscape

| Tool | Type | Key Capability |
|------|------|---------------|
| Chainalysis Reactor | Commercial | Investigative graph visualization, entity tagging |
| Elliptic Investigator | Commercial | Risk scoring, wallet screening, cross-chain tracing |
| TRM Forensics | Commercial | Cross-chain analytics, sanctions screening, threat intel |
| Breadcrumbs.app | Freemium | Tracking blockchain paths, risk scoring |
| OXT (oxt.me) | Free | Bitcoin-only graph exploration, privacy analysis |
| Maltego + Blockchain Transforms | OSINT | Entity graphing with crypto address integration |
| etherscan.io | Free | EVM block explorer with address labels |
| solscan.io | Free | Solana explorer with token/txn tracing |
| Arkham Intelligence | Freemium | Entity-based dashboard, address attribution |
| Bitquery / Dune Analytics | Freemium | SQL-based on-chain data querying |

**Open-source tools:**
- BlockSci: Bitcoin blockchain parser and analysis library (C++/Python)
- GraphSense: Open-source cryptocurrency analytics platform
- WalletExplorer (Bitcoin): Community-maintained address labels
- LOCARD (arXiv:2604.04211): Agentic Blockchain Forensics framework (see §4)

---

## 4. Agentic Blockchain Forensics (ABF)

The traditional blockchain forensics pipeline is static: query → cluster → attribute → report. The emerging ABF paradigm (Yu & Knottenbelt 2026, arXiv:2604.04211) models forensic investigation as a **sequential decision-making process** where an LLM-based agent iteratively selects actions (query new addresses, decode contract calls, trace cross-chain bridges) based on the evolving investigative state.

**LOCARD Framework (arXiv:2604.04211):**
- **Tri-Core Cognitive Architecture:** Decouples strategic planning, operational execution, and evaluative validation.
- **Structured Belief State:** Maintains an explicit state of known/unknown addresses, hypothesized clusters, and confidence levels — enforcing forensic rigor rather than open-ended LLM reasoning.
- **Thor25 Benchmark:** 151k+ real-world cross-chain forensic records for evaluating Group-Transfer Tracing (Sybil cluster dismantling).
- **Empirical validation:** LOCARD achieves high-fidelity tracing on real laundering sub-flows from the Bybit hack.

**StealthLink (Che et al. 2025, arXiv:2505.09892):**
- Cross-task domain-invariant feature learning for correlating mixing service accounts.
- Transfers knowledge from blockchain anomaly detection to the data-scarce task of mixing transaction tracing via adversarial discrepancy minimization.
- **State-of-the-art:** 96.98% F1-score in 10-shot learning for Tornado Cash mixing correlation.
- MixFusion module constructs and encodes mixing subgraphs for local transactional pattern capture.

**Structural insight:** ABF maps directly to Exocortex autonomous investigation architecture — the agentic forensic loop (plan → execute → validate) mirrors the supervisor-tool-worker pattern. The Structured Belief State is analogous to BST (Belief State Tracker) domain classification; adversarial knowledge transfer in StealthLink parallels cross-domain generalization in entity resolution and intelligence analysis.

---

## 5. Investigation Patterns

- **The $X million hack → laundering trace:** Follow stolen funds through DEX swaps, cross-chain bridges, and mixer deposits to identify cash-out exchange addresses; combine with KYC requests to exchanges for identity attribution.
- **Ransomware payment tracking:** OFAC-listed ransomware addresses (Conti, LockBit, DarkSide) → trace ransom payments to identify payment infrastructure and potential exchanger relationships.
- **Sanctions evasion detection:** Monitor addresses interacting with OFAC-designated entities; use peel chain and mixer detection to identify layering; correlate with off-chain intelligence (shell companies, nominee directors) for entity resolution.
- **Darknet market takedown support:** Analyze vendor/customer deposit address clusters across markets to map operational infrastructure and identify administrators via shared payment addresses.

---

## 6. Cross-Domain Connections

- **Entity Resolution:** Address clustering is Fellegi-Sunter probabilistic record linkage applied to blockchain data — heuristics as blocking rules, temporal/spatial features as matching features. See [[entity-resolution-methods]].
- **Sanctions Effectiveness:** On-chain analysis is the primary detection mechanism for crypto-based sanctions evasion (Iranian exchange networks, North Korean DeFi laundering). Bridges to [[secondary-sanctions-extraterritorial-enforcement]] and [[supply-chain-economic-warfare]].
- **Network Analysis Techniques:** Blockchain transaction graphs are directed, weighted temporal graphs — community detection, centrality, and pathfinding techniques from [[network-analysis-techniques-osint]] apply directly.
- **Intelligence Failure Analysis:** Crypto forensic false negatives (missed laundering flows) map to intelligence failure cognitive closure patterns — see [[intelligence-failure-analysis]].
- **Knowledge Graph Construction:** On-chain entity attribution feeds into property graphs linking addresses → entities → KYC identities → shell companies → physical locations. See [[knowledge-graph-construction]].
- **Agent Architecture / Agentic Forensics:** LOCARD's Tri-Core architecture mirrors Exocortex supervisor loop; ABF structural belief state is isomorphic to BST domain classification. See [[ai-agent-architecture-local-inference]].
- **Anti-Bot Evasion:** Address privacy techniques (mixers, CoinJoin, privacy coins) are structurally analogous to browser fingerprinting evasion — a detection/evasion arms race. See [[anti-bot-evasion]].
- **OSINT Tradecraft:** On-chain analysis extends Bellingcat-style digital investigation methodology to cryptocurrency — combining ledger transparency with off-chain corroboration. See [[osint-tradecraft-bellingcat-methodology]].

---

## 7. References

1. Yu, X. & Knottenbelt, W. (2026). "LOCARD: An Agentic Framework for Blockchain Forensics." arXiv:2604.04211. Agentic Blockchain Forensics paradigm; Tri-Core Cognitive Architecture; Thor25 benchmark (151k cross-chain forensic records); validated against Bybit hack laundering sub-flows.
2. Che, Z., Li, T., Shen, M., Du, H., & Zhu, L. (2025). "Correlating Account on Ethereum Mixing Service via Domain-Invariant feature learning." arXiv:2505.09892. StealthLink framework; MixFusion module; 96.98% F1 score in 10-shot mixing correlation.
3. Chainalysis. (2026). "The 2026 Crypto Crime Report." Industry-standard reference for ransomware, sanctions, and darknet market volumes. chainalysis.com
4. Elliptic. (2025). "Typologies of Crypto-Based Financial Crime." Summary of layering techniques, cross-chain obfuscation, and entity attribution methods.
5. GraphSense Project. Open-source cryptocurrency analytics platform. github.com/GraphSense/graphsense
6. BitcoinAbuse.com — community-maintained database of reported scam and ransomware BTC addresses.
