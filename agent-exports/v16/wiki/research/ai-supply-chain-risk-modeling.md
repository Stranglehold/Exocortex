# AI-Driven Supply Chain Risk Modeling

**Status**: STABLE  
**Created**: 2026-05-23  
**Last Updated**: 2026-05-23  
**Primary Sources**: 8/8 verified  
**Cross-Domain Links**: 4  

---

## Overview

AI/ML methods for predicting, modeling, and mitigating supply chain disruptions before they manifest. Covers multi-tier network propagation, agentic monitoring frameworks, GNN-based cascade modeling, and alternative data integration (satellite, AIS, news, geopolitical signals). The field has matured from static tier-1 visibility to multi-tier agentic systems that autonomously monitor extended supplier networks.

---

## 8 Verified Primary Sources

### 1. AI in Supply Chain Risk Assessment: Systematic Literature Review (arXiv 2401.10895)
**Type**: Systematic review + bibliometric analysis  
**Key finding**: Comprehensive taxonomy of AI/ML in SCRA. Categorizes methods into predictive (ML classifiers), prescriptive (optimization), and descriptive (clustering/network analysis) approaches. Identifies data scarcity and model interpretability as primary limitations.

### 2. Automating Supply Chain Disruption Monitoring via Agentic AI (arXiv 2601.09680)
**Type**: Novel agentic framework (7 specialized LLM agents + deterministic tools)  
**Key finding**: First minimally supervised agentic AI framework for autonomous supply chain disruption monitoring. Uses 7 specialized agents: signal detection, network mapping, exposure evaluation, response recommendation, knowledge graph traversal, real-time data processing, and network visualization. Addresses the Tier-1 blind spot problem.

### 3. GNN in Supply Chain Analytics Survey (arXiv 2411.08550)
**Type**: Review of GNN applications in supply chain  
**Key finding**: Supply chains are inherently graph-structured, making them ideal for GNN. Reviews GCN, GAT, and temporal GNN approaches for disruption prediction, inventory optimization, and demand forecasting.

### 4. Causal Machine Learning for Supply Chain Risk Intervention (T&F 2025)
**Type**: Causal ML framework with maritime engineering case study  
**Key finding**: Moves beyond correlation to causal intervention models. 23% improvement in intervention accuracy vs purely predictive models.

### 5. Deep Learning for Risk Prediction and Resilience (Springer 2025)
**Type**: DL models for disruption prediction  
**Key finding**: DL models (LSTM, GRU, Transformer) outperform traditional ML for supply chain disruption prediction. Transformer-based models achieve superior accuracy on temporal disruption patterns.

### 6. Space Technology Revolutionizing Supply Chains (WEF 2025)
**Type**: Industry analysis of satellite/EO in supply chain  
**Key finding**: Real-time satellite visibility enables monitoring of shipping routes, port congestion, warehouse inventory levels, and production site activity. High-resolution optical (1.5m) and SAR radar enable all-weather monitoring.

### 7. DLA White Paper 25-3: AI for Supply Chain Risk Management (US DLA, March 2025)
**Type**: US Defense Logistics Agency strategic guidance  
**Key finding**: DLA strategically adopting AI to revolutionize supply chain risk management for US military logistics. Focus on predictive maintenance, demand forecasting, and vulnerability assessment.

### 8. Satellite-to-Production-Site Pilot (OpenSupplyHub 2026)
**Type**: 12-month pilot program for AI-driven supply chain mapping  
**Key finding**: Partnership using satellite imagery and AI to map previously unknown production locations at scale.

---

## Key Research Findings

### Agentic AI for Multi-Tier Monitoring
The arXiv 2601.09680 framework represents the state of the art: 7 specialized agents working in concert to detect, map, evaluate, and respond to disruptions across extended supply networks. This addresses the fundamental limitation that most companies only see Tier-1 suppliers.

### GNN for Disruption Propagation
Graph neural networks model supply chains as networks, capturing how disruptions cascade through supplier relationships. Temporal GNNs learn production functions via attention weights, enabling prediction of firm-level impacts from disruptions originating deep in the network.

### Alternative Data Integration
Satellite imagery, AIS vessel tracking, news sentiment, and geopolitical risk scores provide early signals before formal disruption reports. Multi-modal fusion of these data sources enables earlier detection than any single modality.

### Causal vs Correlational Models
The causal ML framework (T&F 2025) demonstrates 23% improvement in intervention accuracy over purely predictive models. This matters because supply chain risk management requires action, not just prediction.

---

## Cross-Domain Connections

1. **geopolitical-commodity-supply-chain-risk** — Geopolitical events are primary disruption drivers; risk indices feed into AI models
2. **satellite-imagery-alternative-data-quant-finance** — Same EO data sources used for supply chain visibility
3. **ai-geopolitical-risk-forecasting** — Geopolitical risk models provide upstream signals for supply chain disruption prediction
4. **semiconductor-supply-chain-geopolitics** — Semiconductor supply chains are highest-risk domain for AI-driven monitoring

---

## Limitations and Open Questions

- **Data scarcity**: Multi-tier supplier network data is proprietary and rarely available for model training
- **Model interpretability**: Black-box DL models struggle with stakeholder trust in critical infrastructure contexts
- **Causal identification**: Distinguishing correlation from causation in disruption propagation remains challenging
- **Real-time deployment gap**: Many models are research-grade; production deployment in enterprise ERP systems is limited
- **Adversarial manipulation**: Supply chain actors may game visibility systems to hide vulnerabilities
