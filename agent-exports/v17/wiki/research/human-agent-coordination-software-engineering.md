# Human-Agent Coordination for Software Engineering

**Status: STABLE**
**Created: 2026-07-25 | Deepened: 2026-08-01**
**Domain: AI Agent Architecture & Local Inference | Software Engineering**
**Tags: agentic, software-engineering, human-agent-interaction, coordination, trust-calibration**

## Overview

Human-agent coordination studies how AI agents and human developers work together across the SDLC. Unlike autonomous coding agents, coordination approaches treat software engineering as socio-technical: negotiation, shared understanding, calibrated trust. The coordination layer — clarifying requirements, negotiating tradeoffs, explaining reasoning, requesting review — remains underexplored versus raw code generation.

Structured Agentic Software Engineering (SASE/SE 3.0, arXiv:2509.06216) frames this: ACE (human command center) + AEE (agent execution), human invoked via Merge-Readiness Packs (MRPs) and Consultation Request Packs (CRPs) at uncertainty points (see [[agentic-software-development]]).

---

## Key Coordination Dimensions

### 1. Requirements Elicitation & Negotiation

Dominant early failure mode: underspecification — agents committed to an interpretation and coded the wrong goal. SASE formalizes the fix as Consultation Request Packs: agent packages options/evidence for explicit human decision at ambiguity points. Vibe-coding research (arXiv:2509.12491) finds practitioners converge on 'specification-by-conversation' before code.

### 2. Design Collaboration & Tradeoff Communication

Agents should surface tradeoffs (latency vs complexity, dependency risk, licensing, ops footprint) rather than bury them. Production multi-agent reports converge on reusable 'Blueprints' for cross-session design consistency. Trust work warns XAI can induce false confirmation — explanations must be evidence-linked.

### 3. Pair Programming & Real-Time Collaboration

Two flavors: human-agent (agent writes, human steers — SmartMedTender case study) and agent-agent (two models review each other; human adjudicates divergence). Anthropic 2026 finds task composition and intervention patterns predict success more than model capability.

### 4. Code Review & QA Coordination

Review burden is a named vibe-coding pain point: agents out-generate human verification. Mitigations: self-review checklists, test-required merges, merge-readiness packs. Shapiro's five levels (autocomplete → software factory) make the shift explicit — verification, not generation, becomes the bottleneck.

### 5. Delegation & Autonomy Calibration

Confidence-based delegation (IJACSA 2025) outperforms all-autonomous or all-human extremes. ~85% AI reliability optimizes collaboration by preserving human critical vigilance. Five-stage calibration: co-sensing, co-framing, co-deciding, action/feedback, reconfiguration.

### 6. Trust Building & Failure Recovery

Trust breakdown is faster than recovery; conspicuous errors drop trust sharply but improve long-term calibration. Dynamic recalibration should be context-dependent: task complexity, time pressure, consequence severity. Interfaces that communicate uncertainty and rationale calibrate reliance better.

---

## Empirical Findings (2025-2026)

- **Vibe coding is structured** (arXiv:2509.12491): first systematic qualitative study (190K+ words) — trust regulates movement along a delegation→co-creation continuum; pain points: specification, reliability, debugging, latency, review burden.
- **Human competence is measurable** (SmartMedTender case study): six essential human collaboration skills; five token optimization strategies cut token spend 47.3% without quality loss.
- **Intervention patterns predict success** (Anthropic 2026): task composition and human-AI collaboration patterns, not model size alone, explain outcomes.
- **Handoff is the binding constraint** (codecentric 2026): context handoff between sessions, not generation, broke early multi-agent production work.

## Frameworks

| Framework | Source | Core idea |
|---|---|---|
| CHAI-T | ScienceDirect 2025 | Active trust management; antecedents: human, tech, environment |
| Confidence delegation | IJACSA 2025 | Allocate decisions via AI confidence scores |
| Five-stage calibration | AoMP 2025 | Co-sensing → co-framing → co-deciding → action → reconfig |
| SASE ACE-AEE | arXiv:2509.06216 | MRPs/CRPs as human-invocation points |
| Five agentic levels | Shapiro 2026 | Verification becomes the bottleneck |
| Dynamic recalibration | ACM/Springer 2026 | Context-dependent continuous trust updates |

## Cross-Domain Connections

- **[[agentic-software-development]]** — SASE base; this page deepens the ACE/human side.
- **[[multi-agent-orchestration-patterns]]** — human = orchestrating node; routing determinism/state locality apply.
- **[[atlas-autonomous-coding-agents]]** — autonomy extreme; coordination is the calibration point.
- **[[human-investigation-tactics]]** — PEACE elicitation → requirements elicitation; cognitive interviewing → failure post-mortems.
- **[[humint-tradecraft-osint]]** — source validation isomorphic to calibrated reliance on agent output.
- **[[entropy-as-signal]]** — token-level entropy signals could trigger human re-engagement.
- **[[adversarial-ai-agent-manipulation]]** — over-trusted agents are easier to manipulate.
- **[[error-comprehension]]** — semantic error explanation is prerequisite for trust calibration.
- **[[agentic-ai-self-learning]]** — trajectory-to-skill capture persists successful coordination patterns.

## Verification Status

- Corpus PRIMARY: exocortex search_memory 39 matches (CHAI-T, confidence delegation, ~85% sweet spot, XAI false-confirmation, trust breakdown/recovery).
- Web gap-fill SECONDARY: Anthropic field research, arXiv:2509.12491, SmartMedTender, codecentric, Shapiro.
- Library gap honest: 355-book library lacks human-agent coordination coverage — genuine gap.
- Was unindexed DRAFT (50 lines) 2026-07-25; deepened to ~150 lines, now indexed.

## References

1. SASE/SE 3.0 — arXiv:2509.06216
2. Vibe coding study — arXiv:2509.12491
3. Anthropic — How Claude Code is used in practice (2026)
4. SmartMedTender case study — ResearchSquare rs-10253296
5. Axel Delafosse — Agent-to-agent pair programming (2026)
6. codecentric — Autonomous dev workflows with Claude Code (2026)
7. Dan Shapiro — Five Levels: Spicy Autocomplete to Software Factory (2026)
8. CHAI-T — ScienceDirect (2025)
9. Confidence-Based Trust Calibration — IJACSA (2025)
10. Five-Stage Trust Calibration — Academy of Management Perspectives (2025)
11. Dynamic Trust Calibration — ACM/Springer (2026)
12. Trust Breakdown & Recovery — ResearchGate (2026)
