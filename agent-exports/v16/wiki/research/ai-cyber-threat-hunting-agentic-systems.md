# AI-Augmented Cyber Threat Hunting — Agentic Multi-Agent Systems

**Status**: STABLE  
**Created**: 2026-05-23  
**Last Updated**: 2026-05-26  
**Deepened**: Cycle 610 (BUILD)  
**Primary Sources**: 6 verified  
**Cross-References**: [ai-threat-intelligence-fusion](./ai-threat-intelligence-fusion.md), [adversarial-ml-robustness](./adversarial-ml-robustness.md), [ai-agent-trust-infrastructure](./ai-agent-trust-infrastructure.md), [cyber-physical-infrastructure-security](./cyber-physical-infrastructure-security.md), [knowledge-graph-construction-patterns](./knowledge-graph-construction-patterns.md), [intelligence-operations-history](./intelligence-operations-history.md)

---

## Overview

AI-augmented cyber threat hunting has evolved from single-LLM reasoners to resilient multi-agent systems (MAS) with built-in adversarial defenses. As of May 2026, the field encompasses five generations of capability maturity, with verified implementations in multi-agent threat hunting frameworks (MAS-Hunt, AgentSOC), enterprise deployment (Microsoft DTDA), and systematic threat modeling (OWASP MAESTRO). The critical insight is that multi-agent threat hunting systems must themselves defend against adversarial manipulation — memory poisoning, prompt injection, and behavioral exploitation are first-class design concerns, not afterthoughts.

---

## 5-Generation Taxonomy of Agentic AI in Cybersecurity

| Generation | Capability | Key Differentiator | Representative Systems |
|---|---|---|---|
| **Gen 1** — Single LLM Reasoners | Basic LLM-as-analyst for triage | No tool access, query-response only | Early GPT-4 SOC assistants (2023-2024) |
| **Gen 2** — Tool-Augmented Agents | LLMs with SIEM/SOAR tool access | Single agent with operational tools | Microsoft Security Copilot (early 2024) |
| **Gen 3** — Multi-Agent Systems | Coordinated agent teams for parallel investigation | Role specialization, inter-agent communication | MAS-Hunt, AgentSOC |
| **Gen 4** — Adversarially-Resilient MAS | Built-in defenses against prompt injection, data poisoning, agent manipulation | Fresh-memory validators, cross-validation layers | MAS-Hunt v2, OWASP MAESTRO-guided deployments |
| **Gen 5** — Autonomous Threat Hunting | Self-directed hypothesis generation, evidence collection, report generation | Continuous operation, minimal human oversight | Microsoft DTDA (production, 2026) |

---

## MAS-Hunt: Resilient Multi-Agent Threat Hunting

**Source**: Silva et al., *"MAS-Hunt: A Resilient AI Multi-Agent System for Threat Hunting,"* Engineering Proceedings 2026, Vol. 123, Paper 26.  
**GitHub**: [pmatheus/mas-hunt](https://github.com/pmatheus/mas-hunt)  
**Published**: February 2026

### Architecture

MAS-Hunt implements a **Kagebushin 3-layer orchestration pattern** for resilient threat hunting operating directly on live telemetry within the Elastic Stack:

1. **Shadow Layer** — Primary hunting agents that execute investigation tasks against live data
2. **Clone Layer** — Fresh-memory validator agents that independently verify findings without inheriting the shadow agents' memory state
3. **Orchestrator** — Coordinates agent lifecycle, detects adversarial manipulation by comparing shadow vs. clone outputs

### Key Innovation: Fresh-Memory Validation

The core adversarial defense mechanism: clone agents start with clean memory and independently re-derive conclusions from the same evidence. Divergence between shadow and clone outputs signals potential memory poisoning or behavioral manipulation of the primary agent.

- **Mechanism**: Byzantine fault tolerance adapted for AI agent systems
- **Detection**: If shadow agent conclusions differ from clone validation, flag as adversarial manipulation event
- **Recovery**: Replace compromised shadow agent with fresh clone, continue investigation

### Field Evidence — Adversarial Vulnerability Confirmed

Trail of Bits **PajaMAS** research (July 2025) demonstrated that multi-agent systems are vulnerable to hijacking via malicious web content — an orchestration agent delegating to a web surfing agent can be manipulated through crafted web pages with varying subtlety. This validates MAS-Hunt's adversarial resilience design as addressing a real, demonstrated threat vector, not a theoretical concern.

---

## AgentSOC Framework

**Source**: Roy & Singh, *"AgentSOC: A Multi-Layer Agentic AI Framework for Security Operations Automation,"* arXiv:2604.20134, April 2026.

### Architecture

AgentSOC is a multi-layered agentic AI framework that enhances SOC automation by integrating three capabilities:

1. **Perception Layer** — Alert correlation across heterogeneous data sources (SIEM, EDR, network telemetry)
2. **Anticipatory Reasoning** — Predictive analysis of multi-stage attack progressions using MITRE ATT&CK mapping
3. **Risk-Based Action Planning** — Safe response action selection with policy validation and audit logging

### Design Principles

- **Hybrid agentic reasoning**: Combines rule-based safety guards with LLM-driven analysis
- **Explicit policy validation**: All response actions pass through policy validation before execution
- **Comprehensive audit logging**: Every agent decision is logged for forensic review
- **Scalability**: Designed for large enterprise environments with thousands of concurrent alerts

### Addressing SOC Complexity

AgentSOC specifically targets three SOC pain points:
1. Correlating heterogeneous alerts across multiple security tools
2. Interpreting multi-stage attack progressions that span days or weeks
3. Selecting safe and effective response actions without causing operational disruption

---

## Microsoft Security Copilot DTDA

**Source**: Microsoft, *"GenAI-Driven Threat Detection with Microsoft Security Copilot,"* arXiv:2605.20896, May 2026.  
**Deployment**: Production across tens of thousands of organizations (Microsoft Defender + Sentinel).  
**Announced**: Microsoft Ignite 2025, public preview 2026.

### Architecture

The **Dynamic Threat Detection Agent (DTDA)** is an always-on adaptive backend service that:

1. **Continuous monitoring**: Operates persistently across Microsoft Defender XDR and Microsoft Sentinel environments
2. **Adaptive detection**: Translates evolving attacker tradecraft into detection logic automatically
3. **Explainable alerts**: Copilot-sourced alerts with reasoning directly within analyst workflows
4. **Gap identification**: Identifies detection gaps that traditional rule-based systems miss

### Operational Impact

- Shifts Microsoft Defender from **analyst-assistive** workflows toward **continuous autonomous threat discovery**
- Deployed at enterprise scale (tens of thousands of organizations)
- Integrated with Phishing Triage Agent (public preview) for autonomous AI-powered threat detection in SOC workflows

---

## OWASP MAESTRO Framework

**Source**: Cloud Security Alliance, *"Agentic AI Threat Modeling Framework: MAESTRO,"* February 2025.  
**OWASP Extension**: *"Multi-Agentic System Threat Modeling Guide v1.0,"* April 2025.  
**GitHub**: [CloudSecurityAlliance/MAESTRO](https://github.com/CloudSecurityAlliance/MAESTRO)

### 7-Layer Architecture

MAESTRO (Multi-Agent Environment, Security, Threat, Risk, and Outcome) provides a systematic 7-layer framework for threat modeling multi-agent AI systems:

| Layer | Scope | Key Concerns |
|---|---|---|
| 1. Foundation Models | Base LLM capabilities | Model provenance, capability boundaries |
| 2. Data Operations | Training/inference data | Data poisoning, prompt injection |
| 3. Agent Frameworks | Orchestration logic | Inter-agent manipulation, delegation abuse |
| 4. Deployment Infrastructure | Runtime environment | Supply chain, configuration drift |
| 5. Evaluation & Observability | Monitoring | Adversarial detection, behavioral drift |
| 6. Security & Compliance | Governance | Policy enforcement, audit trails |
| 7. Agent Ecosystem | External interactions | Cross-system threats, API security |

### OWASP ASI Top 10 (2025/2026)

Separate from the OWASP Top 10 for LLM applications, the **ASI Top 10** focuses specifically on agentic AI and multi-agent system risks using ASI01-ASI10 numbering. Provides a threat-model-based reference of emerging agentic threats with recommended mitigations.

---

## Cross-Domain Connections

- **ai-threat-intelligence-fusion** — MAS-Hunt and AgentSOC both aggregate CTI from multiple sources; multi-agent fusion patterns are structurally similar to cross-jurisdictional intelligence sharing
- **adversarial-ml-robustness** — MAS-Hunt's fresh-memory validators address adversarial manipulation at the agent level, complementing model-level robustness techniques
- **cyber-physical-infrastructure-security** — ICS/SCADA threat hunting requires real-time capabilities; DTDA's always-on model adapts to OT environments
- **knowledge-graph-construction-patterns** — MITRE ATT&CK serves as the navigation graph for agent-based threat hunting; knowledge graph construction techniques apply directly
- **ai-agent-trust-infrastructure** — Validator attestation primitives from trust infrastructure can strengthen MAS-Hunt's clone validation mechanism
- **intelligence-operations-history** — Fresh-memory validation parallels military intelligence confirmation chains (multiple independent sources required before action)

---

## Key Insight

Multi-agent adversarial resilience in threat hunting mirrors **Byzantine fault tolerance** in distributed systems and **military intelligence validation chains**. Fresh-memory validators (MAS-Hunt), cross-validation layers (AgentSOC), and OWASP MAESTRO's systematic threat modeling converge on a single principle: **in AI security operations, trust must be verified, not assumed** — even when the agent being verified is one of your own.

The field has moved beyond "can AI help hunt threats" to "how do we ensure the AI hunters themselves cannot be compromised." This is the defining challenge of Gen 4-5 agentic cybersecurity.

---

## Verified Sources

1. Silva et al., "MAS-Hunt: A Resilient AI Multi-Agent System for Threat Hunting," Engineering Proceedings 2026, Vol. 123, Paper 26 ✓
2. Roy & Singh, "AgentSOC: A Multi-Layer Agentic AI Framework for Security Operations Automation," arXiv:2604.20134 (April 2026) ✓
3. Microsoft, "GenAI-Driven Threat Detection with Microsoft Security Copilot," arXiv:2605.20896 (May 2026) ✓
4. Cloud Security Alliance, "Agentic AI Threat Modeling Framework: MAESTRO" (February 2025) ✓
5. OWASP, "Multi-Agentic System Threat Modeling Guide v1.0" (April 2025) ✓
6. Trail of Bits, "Hijacking multi-agent systems in your PajaMAS" blog (July 2025) ✓
