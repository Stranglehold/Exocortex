# AI-Driven Market Surveillance & Anomaly Detection

## Status: STABLE
## Created: 2026-05-22
## Last Updated: 2026-05-22
## Cross-Domain Links:
- options-market-structure
- ai-agent-market-microstructure-evolution
- ai-agent-economics-mechanism-design
- quantitative-analysis-techniques
- ai-sanctions-evasion-detection

## Overview

Regulators and exchanges increasingly deploy AI/ML systems for real-time market surveillance, detecting manipulative patterns that traditional rule-based systems miss. The surveillance-adversarial dynamic intensifies as AI-driven trading strategies grow more sophisticated. IOSCO's 2025 Thematic Review found 62% of respondents lack formal AI governance frameworks for surveillance, creating a capability gap between regulatory detection and adversarial evasion.

## Key Technology Categories

### Real-Time Pattern Detection
- **Temporal Convolutional Networks for Spoofing**: arXiv 2403.13429 (Poutré et al.) introduces a framework for detecting and triaging spoofing using TCNs with expert-informed ranking. Uses a labeling algorithm to create weakly supervised training on order book state sequences.
- **Probabilistic Spoofability Prediction**: arXiv 2504.15908 develops interpretable probabilistic neural networks to learn spoofability of limit order books. Moves beyond binary detection to quantify how spoofable a given LOB state is, enabling triage of surveillance alerts by severity.

### NLP-Driven Surveillance
- **Telegram Pump-and-Dump Detection**: arXiv 2412.18848 (Bolz & Bründler) presents a real-time NLP pipeline classifying Telegram messages to identify pump events. Identified 2,079 past pump events across Telegram groups exceeding 2M members total.
- **Social Media Manipulation from Forums**: arXiv 2301.11403 (Springer 2024) develops detection of pump-and-dump schemes from online forum posts, correlating price/volume profiles with social media sentiment spikes.
- **Real-Time Crypto Pump Detection**: arXiv 2605.09431 (May 2026) extends pump detection to real-time target extraction from social media, achieving message-level classification of pump signals.

### GNN Relationship Mapping
- **GNN for Financial Fraud Detection Review**: arXiv 2411.05815 (Cheng et al., Nov 2024) is a comprehensive review of graph neural networks for financial fraud detection. Demonstrates GNNs are exceptionally adept at capturing complex relational patterns in financial networks.

## Regulatory Landscape

- **IOSCO PD788 (AI in Capital Markets)**: Formal report covering AI-enhanced surveillance as a key use case. Highlights governance risks, model risk management requirements, and expansion of AI from trading into surveillance functions.
- **CFTC AI Surveillance Deployment (Apr 2026)**: CFTC publicly announced deployment of AI-based surveillance systems for futures markets. Focus on pattern detection for spoofing, layering, and momentum ignition.
- **SEC AI Integration (2025)**: SEC's CTF Proposal (Sep 2025) includes AI-enhanced market surveillance as mandated components for regulated entities.

## Adversarial Dynamics

- **Detection-Evasion Arms Race**: As AI surveillance improves, adversarial traders develop evasion techniques. The spoofability prediction framework quantifies how much a market state favors spoofing.
- **Cross-Jurisdictional Arbitrage**: IOSCO 2025 found 62% of respondents lack formal AI governance for surveillance, creating jurisdictional gaps that manipulators exploit.

## Verified Primary Sources (8)

1. arXiv 2403.13429 — Poutré et al., "Detecting and Triaging Spoofing using Temporal Convolutional Networks"
2. arXiv 2504.15908 — "Learning the Spoofability of Limit Order Books With Interpretable Probabilistic Neural Networks"
3. arXiv 2411.05815 — Cheng et al., "Graph Neural Networks for Financial Fraud Detection: A Review"
4. arXiv 2412.18848 — Bolz & Bründler, "Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time"
5. arXiv 2605.09431 — "Real-Time Detection and Target Extraction of Crypto Pump-and-Dump"
6. arXiv 2301.11403 / Springer 2024 — "Detecting Pump&Dump Stock Market Manipulation from Online Forums"
7. IOSCO PD788 — "Artificial Intelligence in Capital Markets: Use Cases, Risks and Challenges"
8. CFTC Press Release (Apr 2026) — "CFTC Deploys AI Tools to Modernize Market Surveillance"
