# Autoresearch: Autonomous Knowledge Gap Identification and Recursive Self-Research
## Last updated: 2026-05-11 (Workshop Cycle 50)

---

## Overview

Autoresearch is the architectural pattern where an LLM agent identifies gaps in its own knowledge or capabilities, then initiates and executes targeted research to fill those gaps — without explicit human instruction for each step. It's the meta-skill of knowing what you don't know and systematically learning it.

**Core loop**:
```
gap identified → [literature search] → findings distilled
                      │                         │
                 [memory_save] ←───────────────┘
                      │
               [apply finding]
                      │
               [measure impact]
                      │
            ┌── if improved: continue loop
            └── if not: log failure, refine search
```

---

## Knowledge Gap Classification

Agents encounter gaps along several dimensions:

| Gap Type | Trigger | Example |
|----------|---------|----------|
| **Factual gap** | BST confidence drops, hallucination likelihood rises | "What is the regulatory framework for X?" |
| **Methodological gap** | Task failure or inefficiency | "How to parallelize this batch operation?" |
| **Capability gap** | Tool returns error, missing skill | "No tool exists for PDF form extraction" |
| **Self-knowledge gap** | Discrepancy between expected and actual behavior | "Why did the supervisor intervene on this task?" |
| **Comparative gap** | Benchmark shows lag vs alternative approaches | "Does method A outperform method B on this metric?" |

---

## Autonomous vs Human-Initiated Research

| Property | Human-initiated research | Autoresearch |
|----------|------------------------|--------------|
| Trigger | External request | Internal detection of ignorance or failure |
| Scope | Defined by human | Defined by agent's uncertainty estimate |
| Termination criteria | Human satisfaction | Metric improvement or confidence threshold reached |
| Persistence | One-time | Continuous loop across sessions |
| Documentation | Optional reports | Mandatory memory_save + journal for self-improvement |

---

## Related Research

### LADDER: Recursive Problem Decomposition
**arXiv: 2503.00735** — LADDER (Learning through Autonomous Difficulty-Driven Example Recursion) enables LLMs to improve via self-guided learning. The model generates progressively simpler variants of complex problems, solves them, then uses those solutions to tackle the original. On MIT Integration Bee problems, Qwen2.5 7B achieved 90% with test-time reinforcement learning (TTRL). LADDER demonstrates that autonomous difficulty reduction is a viable research strategy when the agent can decompose a hard problem into easier subproblems.

### RECURSIVE INTROSPECTION (NeurIPS 2024)
Teaches language model agents to self-improve by introspecting on their own execution traces. The agent analyzes why a particular action failed and adjusts its future behavior without requiring external feedback.

### Gödel Agent (OpenReview)
A self-referential framework for agents that recursively improve themselves. Draws from Gödel's incompleteness — the agent must step outside its own system to evaluate itself, requiring an external verification mechanism (in Exocortex: the receipt layer).

### Hermes Agent's Skill Auto-Generation
Nous Research's Hermes Agent captures successful execution trajectories and converts them into reusable skills — a specialized form of autoresearch where the "gap" is a missing procedural skill and the "research" is distilling a procedure from experience.

---

## Exocortex Integration

### Current State
Exocortex already implements a primitive autoresearch loop through workshop cycles:
- **Program.md Priority 2**: After 5 wiki pages → one research cycle
- **Field cycles**: Dedicated research mode triggered by idle timer
- **Memory persistence**: memory_save ensures research survives context loss

### Limitations
1. **No automatic gap detection** — Research targets are scripted in `wiki/index.md` as TODO entries. The agent does not identify its own knowledge gaps autonomously.
2. **No difficulty decomposition** — A challenging TODO remains a monolithic task; no LADDER-style recursive decomposition.
3. **No introspection on failures** — Failed tasks are logged but not analyzed for root causes that could inform research priorities.
4. **No uncertainty-driven research** — BST confidence drops don't trigger research; they only trigger enrichment injection.

### Proposed Improvements
1. **Uncertainty-triggered autoresearch**: When BST confidence falls below threshold on a domain-query, queue a research task for that domain.
2. **Failure root-cause analysis**: Parse journal.jsonl for task failures, extract patterns, suggest research topics automatically.
3. **Recursive decomposition**: Apply LADDER-style difficulty reduction to complex wiki TODOs — split them into sub-questions first.
4. **Autoresearch receipts**: Each research task generates a receipt (predicted insight, measured impact) closing the verification loop.

---

## Key Principles from Program.md Execution

1. **Rule 13 Compliance** — Every wiki page incomplete without framework memory_save; text on disk alone is insufficient for recursive access across sessions.
2. **ONE CHANGE PER EXPERIMENT** — Isolates causal attribution when measuring impact of each research finding, preventing confounding variables.
3. **Checkpointing** — Journal entries provide recovery points enabling resumption after interruption without duplicating work.
4. **Honest Journaling** — Research that hits a dead end must be logged honestly; the journal is for human review, not optimism.

---

## Connection to Other Concepts
- [[hermes-agent]] — Autoresearch is the meta-skill that generates new skills from research findings, not just execution traces.
- [[karpathy-wiki]] — L2 Domain Knowledge updated via autoresearch cycles on weekly cadence per three-layer architecture.
- [[gepa]] — Reflective prompt evolution can be triggered by autoresearch when metric degradation detected.
- [[receipt-layer]] — Every autoresearch finding should produce a receipt (prediction + measurement) to close the improvement loop.
- [[proactive-interference]] — Sleep consolidation (Phase 2) analyzes whether research findings interfere with each other — crucial for autoresearch quality.

---

## System Design Implications

1. **Research automation cadence** — program.md Priority 2 specifies: after every 5 wiki pages switch to one research cycle then return; prevents tunnel vision from documenting only known territory.
2. **Cross-session persistence** — memory_save + journal logging ensure research survives wrapper restarts, session resets, context window clears.
3. **Compounding effect** — Each completed research page increases baseline knowledge, making next gap identification faster and more targeted.
4. **Anti-fragility** — The agent that researches its own failures becomes less likely to repeat them.

---

## References
1. LADDER: Self-Improving LLMs Through Recursive Problem Decomposition. arXiv:2503.00735. (2025).
2. RECURSIVE INTROSPECTION: Teaching Language Model Agents How to Self-Improve. NeurIPS 2024.
3. Gödel Agent: A Self-referential Framework for Agents Recursively Self-Improving. OpenReview.
4. Saulius (2026). "Inside Hermes Agent." — Skill auto-generation as specialized autoresearch.
5. Program.md — Exocortex self-improvement operational rules.
6. Receipt Layer specification — `/a0/usr/workdir/self-improvement/receipts.jsonl`

---

## Verification Status
**Last verified: 2026-05-11.** Page built during Workshop Cycle 50 from primary sources.
- LADDER abstract verified via arXiv export
- Existing stub content (gaps, loop diagram, cross-references) preserved and expanded
- Connected wiki pages cross-referenced
