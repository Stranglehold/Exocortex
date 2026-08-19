# AI-Driven Market Microstructure Analysis

**Status:** STABLE  
**Created:** 2026-05-24  
**Last Updated:** 2026-05-24  
**Primary Sources:** 10/10  
**Cross-Domain Links:** 5  

## Overview

Market microstructure studies how trading mechanisms, order types, and information flow affect price formation and execution quality. AI/ML methods are increasingly deployed to analyze order book dynamics, detect latent market structure, optimize execution strategies, and classify trading regimes.

## Core Research Areas

### 1. Limit Order Book Forecasting with Deep Learning

- **LiT (Limit Order Book Transformer)** — Xiao & Ventre, Frontiers in AI 2025. Transformer architecture for LOB data capturing spatial and temporal dependencies. Outperforms traditional ML and prior DL baselines on short-term price forecasting.
- **TLOB** — Berti & Kasneci, arXiv 2502.15757. Simplified MLP-based architecture adapted to LOB data surpasses SoTA transformer performance on price trend prediction, challenging complexity-is-better assumption.
- **Deep LOB Forecasting Microstructural Guide** — Briola & Bartolucci, Taylor & Francis 2025. High forecasting accuracy does not necessarily translate to actionable trading signals. Proposes operational evaluation framework.

### 2. Reinforcement Learning for Optimal Execution

- **arXiv 2411.06389** — RL-based optimal execution using LOB state features at high frequency, formulated as MDP.
- **SCML 2025** — Enhanced RL with reward shaping for execution cost expectation and variance.
- **ACM AAMAS 2026 (10.1145/3768292.3770405)** — Market simulation-based RL for execution strategy discovery.
- **Springer 2026 (10.1007/s00780-026-00589-5)** — Actor-critic RL for continuous-time optimal execution with entropy regularization, closed-form solution.
- **IEEE 11467851** — Multi-agent optimal execution with high-frequency LOB features.

### 3. Market Regime Detection

- **Springer 2025 (10.1007/s11009-025-10148-8)** — HMM-SVM/MKL generative-discriminative approach for high-frequency regime classification.
- **IEEE 11038776** — HMM-based regime detection with RL for portfolio management (FinRL, 30-stock Dow Jones).
- **PLoS ONE 2025** — Heteroskedasticity network combining HMM, ARMA-GARCH, and ML for early regime switching warning.

### 4. AI-Driven Market Making & Execution

- **ScienceDirect S3050700626000368** — Comprehensive survey of AI reshaping algorithmic trading, refining order-flow interpretation and short-horizon return forecasting.
- **CFA Institute RPC 2025** — Chapter 5 on deep learning: millisecond pricing, risk assessment, signal discovery.

## Key Findings

1. Architecture simplicity can win for LOB tasks (TLOB MLP beats transformer).
2. Forecasting accuracy does not equal trading profitability (Briola & Bartolucci).
3. RL execution maturing with closed-form solutions and multi-agent frameworks.
4. Regime detection remains HMM-dominant despite deep learning advances.

## Primary Sources (10 verified)

1. Xiao & Ventre, LiT: Limit Order Book Transformer, Frontiers in AI 2025 (10.3389/frai.2025.1616485)
2. Berti & Kasneci, TLOB, arXiv 2502.15757
3. Briola & Bartolucci, Deep LOB Forecasting Guide, Taylor & Francis 2025
4. arXiv 2411.06389, Optimal Execution with RL
5. SCML 2025, RL for Optimal Trade Execution
6. ACM AAMAS 2026, Market Simulation-based RL (10.1145/3768292.3770405)
7. Springer 2026, Actor-Critic RL Continuous-Time Execution (10.1007/s00780-026-00589-5)
8. Springer 2025, HMM-SVM/MKL Generative-Discriminative (10.1007/s11009-025-10148-8)
9. IEEE 11038776, HMM-Based Regime Detection with RL
10. ScienceDirect S3050700626000368, AI in Algorithmic Trading Survey

## Cross-Domain Connections

- [ai-agent-delegation-security](ai-agent-delegation-security.md) — Execution risk management
- [distributed-training-infrastructure](distributed-training-infrastructure.md) — HF data pipeline requirements
- [adaptive-supervisor-architecture](adaptive-supervisor-architecture.md) — Regime detection as agent state monitoring
- [ai-datacenter-power-crisis](ai-datacenter-power-crisis.md) — HFT colocation demands
- [ai-driven-materials-discovery](ai-driven-materials-discovery.md) — RL for sequential decision making
