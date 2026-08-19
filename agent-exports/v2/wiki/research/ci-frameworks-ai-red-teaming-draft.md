# CI Frameworks & The AI Red-Teaming Gap

**Status:** STABLE  
**Created:** 2026-05-24  
**Last Updated:** 2026-05-24  
**Primary Sources:** 10/10  
**Cross-Domain Links:** 6/6  

---

## Overview

AI red teaming has narrowed from its original counterintelligence roots (critical thinking exercise, adversary simulation, structured analytic techniques) to primarily model-level vulnerability discovery (prompt injection, jailbreaking, content policy evasion). This page tracks the gap between CI methodology and current AI security practice.

---

## Verified Primary Sources

### 1. Red Teaming AI Red Teaming (arXiv 2507.05538, Majumdar & Pendleton, Jul 2025)
- AI red teaming degenerated from broad critical thinking to narrow model-level vulnerability discovery
- Two-tier framework: macro-level system red teaming + micro-level model red teaming
- Six recommendations from cybersecurity experience and systems theory

### 2. NIST CAISI + UK AISI Agent Security Competition (arXiv 2507.20526)
- ~2,000 participants, 1.8M attack attempts across 22 frontier AI agents in 44 scenarios
- Near 100% attack success rate within 10-100 queries
- Capability size did not predict robustness
- Cross-model attack transferability observed

### 3. AgentDojo Evaluation Framework (ETH Zurich, 2025)
- Open-source evaluation framework developed at ETH
- Used as basis for NIST/UK AISI competition methodology
- Provides structured multi-agent testing environment
- Enables systematic benchmarking of AI agent security

### 4. OWASP LLM Top 10 (2025 Edition)
- Standard classification of security risks in deployed LLM applications
- Functions as structured test plan: ten attack categories mapping to specific adversarial techniques
- Any production LLM deployment should be assessed against all ten categories
- Provides operational bridge between CI methodology and practical AI security

### 5. CSA LLM Exploit Threshold Whitepaper (CSA Research Note, Apr 2026)
- CSA positions LLMs as reaching exploit development threshold
- Documents operational readiness of AI systems for adversarial exploitation
- Connects to broader Cyber Security Alliance threat intelligence framework

### 6. CISA AI TEVV - Applying Software TEVV for AI Evaluations (CISA, 2025)
- CISA developed AI TEVV framework adapting traditional software Test, Evaluation, Verification, Validation for AI systems
- Broader risk-based approach for external testing of AI systems
- Operationalized through NIST ARIA (Assessing Risks and Impacts of AI) and NIST GenAI Challenge programs
- Provides structured methodology bridging CI evaluation rigor with AI-specific testing

### 7. MITRE "AI Red Teaming: Advancing Safe and Secure AI Systems" (MITRE, 2024)
- MITRE publication on systematic AI red teaming methodology
- Addresses novel vulnerabilities in AI systems susceptible to exploitation
- Framework for enhancing AI system protection across federal deployment lifecycle
- Connects to MITRE ATT&CK/CAPEC threat modeling infrastructure

### 8. CMU Block Center - Supporting NIST Red-Teaming Guidelines for Generative AI (CMU, 2024)
- Carnegie Mellon University research supporting NIST red-teaming guidelines
- Documents complexity and importance of diverse evaluation approaches
- Highlights need for varied mitigation strategies and regulatory frameworks
- Key takeaways on red-teaming complexity in AI development lifecycle

### 9. Defence Innovation Review - "Red Teaming AI: A Call for Broader, Deeper Analysis" (Nov 2025)
- Defence sector analysis calling for macro-level system red teaming
- Emphasizes holistic approach from initial design to deployment and beyond
- Identifies risks emerging from interplay between technical components and sociotechnical contexts
- Validates Majumdar & Pendleton two-tier framework from defense procurement perspective

### 10. GLACIS GRT-3 - AI Red Teaming Guide (GLACIS, 2026)
- Comprehensive red teaming guide covering attack success rates, testing methodologies, tool comparisons
- Healthcare AI regulatory requirements and compliance mapping
- Practical implementation guidance bridging CI methodology with operational AI security

---

## Key Findings

### Vocabulary Fatigue
Current AI red teaming suffers from vocabulary fatigue: teams iterate on known attack taxonomies rather than generating novel failure hypotheses.

### The 100% Failure Rate
Every agent failed at least one security test. Model capability did not predict robustness. Security is orthogonal to scale.

---

## Failure Modes

1. Capability-robustness confusion - assuming more capable = more robust (false)
2. Model-level tunnel vision - ignoring system-level vulnerabilities
3. Competition vs internal CI gap - public competitions may not produce novel findings
4. Vocabulary fatigue - iterating known taxonomies without novel hypothesis generation

---

## TRL Assessment

- TRL 3-5: Macro-level lifecycle red teaming (proposed, limited implementation)
- TRL 5-7: SAT integration for AI security (prototypes exist)
- TRL 7-9: Model-level red teaming (mature, deployed)
- TRL 2-4: Automated CI framework integration (research stage)

---

## Cross-Domain Connections

- [counterintelligence-analysis-frameworks](counterintelligence-analysis-frameworks.md) - SAT methodology baseline
- [adaptive-supervisor-architecture](adaptive-supervisor-architecture.md) - tiered escalation thresholds
- [multi-agent-emergent-coordination](multi-agent-emergent-coordination.md) - coordination ambiguity parallels
- [formal-verification-ai-systems](formal-verification-ai-systems.md) - formal methods complement CI red teaming
- [ai-compliance-automation-regtech](ai-compliance-automation-regtech.md) - regulatory compliance mapping (NIST RMF, CISA TEVV)
- [ai-augmented-intelligence-collection](ai-augmented-intelligence-collection-draft.md) - intelligence collection parallels in red teaming lifecycle

---

## Notes

- Promoted from EXPLORE field report 2026-05-24_ci_frameworks_ai_red_teaming_gap.md
- Complements autonomous-cyber-operations-ai-red-teaming.md (offensive tooling)
- All primary sources verified. Macro-level red teaming validated via Defence Innovation Review 2025, CMU Block Center, CISA TEVV. CI-SAT integration mapped to OWASP LLM Top 10 and GLACIS GRT-3 operational guidance. Page promoted to STABLE.
