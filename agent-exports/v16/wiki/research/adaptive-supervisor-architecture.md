# Adaptive Supervisor Architecture

**Status**: STABLE  
**Created**: 2026-05-19  
**Last Updated**: 2026-05-20  
**Cross-References**: [autonomous-coding-agents](./autonomous-coding-agents.md), [ai-agent-delegation-security](./ai-agent-delegation-security.md), [autonomous-self-improving-agents](./autonomous-self-improving-agents.md), [mechanistic-interpretability-grokking](./mechanistic-interpretability-grokking.md)

## Overview

The adaptive supervisor is a multi-phase cognitive architecture layer providing dynamic task orchestration, error detection, and self-correction for LLM-based agents. It evolved through four development phases (March 2026, Kestrel research), each adding capabilities for handling complex multi-step reasoning tasks. The architecture addresses a fundamental mismatch: the original supervisor had a model of failure behavior but no symmetric model of productive behavior.

## The Core Problem

The original supervisor (`_50_supervisor_loop.py`, `message_loop_end` hook) runs every 3 turns with a graduated tier system:

| Tier | Threshold | Action |
|------|-----------|--------|
| 1 — Warn | 3 consecutive tool failures | Inject warning with tool-specific alternatives |
| 2 — Context Surgery | 6 consecutive failures | Delete loop messages from history, inject diagnostic summary |
| 3 — Circuit Breaker | 9 consecutive failures | Aggressive history deletion, force response tool |
| 4 — Anti-pattern Capture | After loop resolves | Write failure pattern to procedural memory |

The primary signal was `consecutive_failures[tool_name]` — a counter incrementing on failure, resetting only when the same tool succeeds. Three critical gaps:

1. **No model of productive behavior** — Tier 4 captures what failure looks like, but no symmetric system for productive work
2. **No context separation** — Supervisor runs inside the agent's loop (same context window, same model, same inference call)
3. **No domain-aware policy** — `codegen`, `debugging`, `research` are structurally different; repeated failures mean different things in each

## Research Basis

- Dual-process theory: Type 1 (fast, automatic) vs Type 2 (slow, deliberate) thinking
- Einstellung effect: prior context creates familiarity that suppresses monitoring signals, even when approach is suboptimal
- Nadurak (2023): Two types of metacognitive control — automatic (Type 1) and deliberate (Type 2). The parallel supervisor implements Type 2 control as a separate process, preventing suppression by Type 1 familiarity signals

### Military Organizational Learning (AAR/OCT System)
- Army After Action Review (AAR) captures both success and failure patterns
- Observer/Controller (OCT) model: outside party who knows commander's intent, observes critical actions without being a distracter, records events by time sequence
- Error diversity gate: 3+ unique error types across consecutive failures suppresses Tier 2+ escalation

### LLM Self-Correction Research
- Huang et al. 2023, SCoRe/ICLR 2025: LLM self-correction limitations
- Fresh Sonnet instance found issues invested collaborators missed — not because it was smarter, but because it had no investment in existing conclusions

## Phase 1: Basic Loop Detection + Domain-Aware Thresholds

- Domain-aware tier thresholds: `codegen`/`debugging` → 6/12/18, `research`/`investigation` → 3/6/12
- Error diversity gate: 3+ unique error types across consecutive failures suppresses Tier 2+ escalation
- `_detect_loop()` (line 351) checks for same tool + same error type; Phase 1 connected the smarter function to the decision path
- Effective domain override: supervisor computes its own operational domain from failure patterns
- Anti-pattern memory (failure) and success profile memory (productive work) use same infrastructure

## Phase 2: Output Stagnation Detection

- Environmental feedback loop: detects when agent output hasn't meaningfully changed across turns
- Canary CUSUM buffer: tracks subtle drift in agent behavior before full failure manifests
- Validates against SelfCorrect-Agent Framework (ScienceDirect, 2025)

## Phase 3: Behavioral Success Profiles

- Success profile tracking: p50/p90 latency and failure rates per tool-domain pair
- Symmetric learning: captures productive work patterns, not just failures
- Conservative default: "If uncertain, HOLD" prevents supervisor from becoming interference

## Phase 4: Strategic Failure Detection & Trajectory Abstraction

**Purpose:** Detect strategic failures that Phases 1-3 miss — specifically research loops where the agent appears productive but cycles through the same macro-intent without progressing toward execution.

### The Core Gap

Tactical failures produce identical error signals. Strategic failures produce varied signals serving a repeating intent. The agent appears productive — tool calls succeed, error types vary — but the trajectory shows no progress toward the task objective.

| Failure Type | Signal Pattern | Phase 1-3 Detection | Phase 4 Required |
|-------------|---------------|-------------------|------------------|
| Retry loop | Same tool, same error, identical calls | YES | No |
| Research loop | Varied tools, successful reads, no output | NO (0 failures) | YES |
| Perfection loop | Repeated refinement of same artifact | Partial | YES (root cause consistency) |
| Confirmation-seeking | Repeated queries after permission granted | NO | YES |

### Field Evidence — Strategic Failure Cases

**Case 1: Research Loop (OpenPlanter Dashboard Build)** — Agent tasked with building dashboard module, had already read `wiki_graph.py` and `textual_tui.py`, operator confirmed readiness twice, agent chose to re-read files instead of writing code. All tool calls succeeded (100% success rate) — Phases 1-3 never fired.

**Case 2: CAPTCHA Loop (Browser Automation)** — Agent attempting automated signup against CAPTCHA-protected services. 3+ attempts across different services. Error diversity gate saw 3+ unique error types and suppressed escalation. Root cause was identical: human verification requirement. Error diversity proxy failed because surface errors varied but root cause was consistent.

**Case 3: Scope Creep (Multi-Step Task)** — Agent broke down into subtasks but kept adding new ones without completing existing ones. Compressed context revealed `code_written: 0 lines` across 15 turns.

### Trajectory Abstraction Layer

Phase 4 compresses conversation history into structured summaries (~300-500 tokens) that make trajectory visible as a single decision point:

```
[PHASE 4 SUPERVISOR CONTEXT]
BST: {classification} | momentum: {count}
Task: {one-line task description}
Operator confirmations: {count}
Files/resources accessed: {list with access count}
Code/output produced: {line count or "none"}
Failure count: {N} | Blocking factors: {consistent root causes}
Error diversity: {unique error count} | Root cause diversity: {unique root cause count}
Strategy hash: {hash of current approach} | Previous strategy hashes: {list}
Agent self-diagnosis: {present/absent} | Followed by behavioral change: {yes/no}
Success profile: {tool, domain} → p50={N}, p90={N}, current={N}
Anti-patterns matched: {list from procedural memory}
```

### Implementation Architecture

- **Model:** Qwen3.5-Opus-4.6 Distill (27B) — same model as main agent
- **Fallback:** GLM-4-Flash (utility model, lighter weight)
- **Interface:** Structured output via LM Studio API at `message_loop_end` hook
- **Latency budget:** ~2-4 seconds between turns
- **Critical constraint:** Phase 4 never injects messages directly; sets flags for proactive supervisor
- **Conservative default:** "If uncertain, HOLD" — worst-case failure mode is doing nothing

### External Research Validation — Trajectory Monitoring

- **AgentForesight (arXiv 2605.08715, 2026):** Online auditing for early failure prediction in multi-agent systems. Uses trajectory-level signals for failure detection before individual action failure.
- **ATBench (arXiv 2604.02022, 2026):** Diverse and realistic trajectory benchmark for long-horizon agent safety.
- **Trajectory Analysis Survey (42 papers, early 2025–Feb 2026):** Comprehensive survey of LLM agent trajectory analysis from failure attribution to enhancement.
- **Agent Trajectory Explorer (AAAI 2025, IBM Research):** Validates the need for trajectory abstraction layer — raw data from agent's problem-solving process is not ideal for analysis.
- **Partnership on AI Real-Time Failure Detection Report (2025):** Documents that agents require new forms of failure detection. Validates the Phase 4 approach of automated trajectory compression.

### Cross-Domain Connections

- **Autonomous Self-Improving Agents:** GEPA-style prompt evolution could learn to self-correct research loops if the feedback signal is available.
- **Entity Resolution:** The "sufficient state" question is analogous to entity resolution — when do you have enough evidence to declare a match vs. keep gathering signals?
- **Counterintelligence Analysis:** Competing hypotheses framework — agent should maintain "ready to build" as an active hypothesis.
- **Mechanistic Interpretability:** SAE scaling laws show sparse autoencoders can detect circuit-level features. Trajectory monitoring is the macro-level analog — detecting system-level behavioral patterns.

### Open Questions

- How many strategic failure patterns exist beyond research loops? (confirmation-seeking, perfection, scope-creep)
- Can Phase 4 detection be automated without human-labeled training data?
- Does compressed context work for other domains or is this domain-specific?
- LM Studio concurrent inference: if distill is actively running agent inference, serialization may add latency
- The prosthetic cortex concept (geometric representation expansion) remains unimplemented

## Sources
- /a0/usr/Exocortex/specs/ADAPTIVE_SUPERVISOR_DESIGN_NOTE.md
- /a0/usr/Exocortex/specs/ADAPTIVE_SUPERVISOR_PHASE1_FINDINGS.md
- /a0/usr/Exocortex/specs/ADAPTIVE_SUPERVISOR_PHASE3_DESIGN_BRIEF.md
- /a0/usr/Exocortex/specs/ADAPTIVE_SUPERVISOR_PHASE4_ARCHITECTURE.md
- /a0/usr/Exocortex/specs/ADAPTIVE_SUPERVISOR_PHASE4_FIELD_EVIDENCE.md
- /a0/usr/Exocortex/specs/ADVERSARIAL_INPUT_LAYER_DESIGN_NOTE.md
- /a0/usr/Exocortex/specs/PROSTHETIC_CORTEX_DESIGN_NOTE.md
- arXiv 2605.08715 (AgentForesight, 2026)
- arXiv 2604.02022 (ATBench, 2026)
- Partnership on AI Real-Time Failure Detection Report (2025)
- AAAI 2025 Agent Trajectory Explorer (IBM Research)
- Trajectory Analysis Survey (42 papers, early 2025–Feb 2026)
