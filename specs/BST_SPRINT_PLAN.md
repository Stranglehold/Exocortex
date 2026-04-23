# BST Deep Dive & Model Optimization — Team Execution Plan
## Sprint: "The Routing Core"

**Created:** 2026-04-16, Session 061
**Author:** Opus (plan structure), Jake (direction), Kestrel (field note inputs)
**Team:** Jake (operator, decisions), Opus (architecture, review), Kestrel (implementation, testing)
**Duration:** Estimated 3-5 sessions across the team

---

## Objective

The BST is becoming the routing core of the Exocortex — every turn's domain classification now drives enrichment, skill surfacing, and (pending) tool injection and reasoning budgets. Four systems downstream of one classification decision. This sprint makes that foundation robust: audit the BST, optimize the model running underneath it, and build the token economics improvements Kestrel identified.

Two parallel workstreams, one blocking dependency between them.

---

## Workstream A: Model Evaluation & Selection
**Lead:** Kestrel (testing) → Jake (decision)
**Blocks:** Nothing. Can run immediately and independently.
**Blocked by:** Nothing.

### The Landscape

Jackrong has released a family of models under the "Qwopus3.5" brand. The full 27B lineup:

| Model | Key Characteristics | Trade-offs | Released |
|---|---|---|---|
| **Opus-Distilled v1** (current) | Original Claude-distilled reasoning. Stable tool calling. Developer role support. 9+ min autonomous runs. | Verbose thinking chains (Class C from Kestrel's field note). Excessive reasoning on simple tasks. | Mar 2026 |
| **Opus-Distilled v2** | 14K Opus-style samples. "Think more economically." Concise reasoning patterns. Higher HumanEval accuracy than v1. | -1.24% HumanEval+, -7.2% MMLU-Pro. May underperform on long-context or complex multi-step reasoning. | ~Apr 8 2026 |
| **Qwopus3.5-v3** ⭐ | Tool-calling RL training. Act-then-refine paradigm. Best strict accuracy (95.73% HumanEval). Designed for agentic workflows. | Slightly longer CoT than v2. Two weeks old. Less community testing. | ~Apr 2 2026 |
| **35B-A3B (MoE)** | Mixture-of-Experts variant. Only 3B active parameters. Potentially faster inference. | MoE architecture may not fit cleanly in LM Studio on 3090. Untested for our use case. | ~Apr 8 2026 |

Also available in 9B and 4B sizes (v1 and v2 each), but community benchmarks confirm only the 27B has stable tool-calling performance.

### Why Qwopus3.5-v3 Deserves Immediate Testing

v3 has three features that directly address current pain points:

1. **Tool-Calling Reinforcement Learning.** v3 was explicitly RL-trained for tool invocation stability. Our malformed messages are tool-call format failures. This is the most targeted fix available — the model was trained to not break tool calls.

2. **Act-Then-Refine Paradigm.** Instead of long pre-action deliberation (the Class C verbose thinking), v3 is trained to act first, then refine. This aligns with TALE's finding that execution-mode tasks don't benefit from deep pre-reasoning. The model does less planning and more doing.

3. **Best Strict Accuracy.** 95.73% strict HumanEval versus 92.68% for v2 and 94.51% for base Qwen3.5-27B. More correct code generation = fewer retry loops = fewer context-consuming failures.

The trade-off: CoT is slightly longer than v2. But if the CoT is more accurate and the tool calls don't malform, the net token economy may be better despite longer thinking.

### Testing Protocol

Kestrel executes this independently. No dependency on Opus's architectural work.

**Step 1: Download candidates** (30 min)
- Qwopus3.5-27B-v3 GGUF (Q4_K_M, ~16.5GB)
- Opus-Distilled v2 GGUF (Q4_K_M, ~16.5GB)
- Note: keep v1 as the baseline for comparison

**Step 2: Standardized test battery** (2-3 hours per model)
Run each model through the same tasks. Record for each:
- Thinking token count per turn
- Tool call format success/failure rate
- Total tokens consumed for task completion
- Wall-clock time to completion
- Qualitative: does the output feel right?

Test tasks (from real operational history):
1. **Simple coding task:** "Create a Python function that reads a JSON file and extracts all unique keys" — baseline execution test
2. **Complex coding task:** "Write a multi-method class with API authentication headers" — the quoting depth stress test from Kestrel's field note
3. **Investigation task:** "Research the current status of [topic] using available tools" — reasoning quality test
4. **Multi-step task:** "Read file X, identify the bug, fix it, run tests" — agentic loop test, the 9+ minute autonomous run test
5. **Tool call stress:** 10 consecutive tool calls in one session — format stability under repetition

**Step 3: Comparison matrix** (1 hour)
Compile results into a comparison table. Deliver to Jake for decision.

**Step 4: Jake decides** which model becomes primary. Decision factors:
- Malformed message rate (most important — this is the current pain point)
- Token efficiency (second most important — directly affects session length)
- Reasoning quality (third — must not regress on investigation/analysis tasks)
- Stability over long sessions (fourth — the 13h45m stress test standard)

### Deliverable
`MODEL_EVALUATION_REPORT.md` — comparison matrix with data, recommendation, and any model-specific configuration notes (temperature, max_tokens, Jinja template requirements).

---

## Workstream B: BST Architecture Deep Dive
**Lead:** Opus (architecture) → Kestrel (implementation)
**Blocks:** Kestrel's token economics implementation (Phases 2-3) depends on Phase 1 completion.
**Blocked by:** Nothing. Can begin immediately.

### Phase 1: BST Current State Audit
**Owner:** Opus
**Dependency:** None
**Duration:** 1 session

Document what the BST does now, exhaustively. Every downstream consumer. Every classification path. Every failure mode observed.

Contents:
- **Domain configurations:** All 15 domains, their signal patterns, their enrichment templates, their priority rankings post-v3.2
- **Slot taxonomy:** The trigger-based slot resolution system, how it interacts with compound BST classification
- **Downstream consumers:** Map every system that reads BST output:
  - Enrichment gating (which enrichment each domain gets)
  - Skill surfacing (_19_skill_suggester.py — which skills surface per domain)
  - Supervisor behavior (does the supervisor respond differently by domain?)
  - Tool registry (pending — Kestrel's Candidate 1)
  - Reasoning budget (pending — Kestrel's Candidate 2)
- **Register-shift domains:** How orientation, meta_cognitive, and philosophical work — the "give the model cognitive space" pattern
- **Failure modes:** The 59% investigation over-classification (fixed in v3.2). Any remaining misclassification patterns. Domain transition edge cases. The risk of four systems failing simultaneously on one misclassification
- **Signal overlap analysis:** Which signals fire across multiple domains? Where are the ambiguity zones?

**Deliverable:** `BST_CURRENT_STATE_AUDIT.md` — the ground truth document.

### Phase 2: Token Economics Implementation
**Owner:** Kestrel
**Dependency:** Waits for Phase 1 (BST audit) for Candidate 1 (tool injection needs the domain→tool mapping validated against the audit). Candidates 2 and 3 can begin independently.
**Duration:** 1-2 sessions

Build Kestrel's three candidates from the field note, in this order:

**2a: Tool Output Compressor (Candidate 3)** — NO DEPENDENCY, build immediately
- New extension: `_28_output_compressor.py`
- Rule-based compression: strip ANSI, deduplicate lines, collapse patterns, keep first/last 30 lines
- Preserve failure-relevant lines (error, exception, traceback, failed, warning)
- 800-token threshold for triggering
- Test: run the docker logs stress test, measure context savings

**2b: BST-Gated Tool Injection (Candidate 1)** — DEPENDS ON Phase 1
- Create `tool_domains.json` config file (mapping validated by Opus's audit)
- Modify `_16_tool_registry.py` to query BST domain and filter tool injection
- Implement domain-transition union (inject current + previous domain's tools for one turn after transition)
- Always inject "use stack_status for full list" fallback
- Test: run ST-010 regression suite, verify no tool-access regressions

**2c: TALE Reasoning Budget (Candidate 2)** — DEPENDS ON thinking token logger
- Add thinking token counter to monologue logging (prerequisite measurement)
- Run baseline measurements across all BST domains with current model
- Add three-tier budget hint to BST enrichment:
  - Execution mode (coding, system_admin, file_ops): "~200 tokens. Execute."
  - Planning mode (planning, complex_build): "~500 tokens. Plan concisely."
  - Analysis mode (investigation, analysis, financial): No constraint
- Include Chain of Draft instruction: "One key insight per reasoning step. No narration."
- Test: compare thinking token counts before/after per domain
- **NOTE:** If model evaluation (Workstream A) selects Qwopus v3, the act-then-refine training may partially address this. Measure v3's baseline thinking tokens before implementing TALE budget. If v3 is already concise enough, this candidate may be deferred.

**Deliverable per candidate:** Extension code + test results document showing measured improvement.

### Phase 3: BST as Routing Core — v3.3 Spec
**Owner:** Opus
**Dependency:** Waits for Phase 1 (audit) and Phase 2b (tool injection implementation, to validate the domain→tool pattern works in practice)
**Duration:** 1 session

The design spec for BST v3.3 that formalizes the routing core:

- **Unified routing decision:** One BST classification → tool set, reasoning budget, enrichment, skill surface, supervisor sensitivity. All five downstream systems configured from one decision.
- **Domain transition protocol:** How the BST handles transitions cleanly (union of tools, gradual enrichment shift, supervisor awareness of transition)
- **Observability:** BST should log its classification reasoning — why it chose this domain, which signals fired, what the alternatives were. Debuggable routing decisions.
- **Model profile integration:** How BST enrichment templates adapt to the specific model's strengths/weaknesses (from Workstream A's evaluation)
- **Test specification:** Updated ST-010 with coverage for all five downstream systems, not just enrichment

**Deliverable:** `BST_V3_3_SPEC.md` — the L3 spec Kestrel builds from.

### Phase 4: Compositional Skills — Exploration Document
**Owner:** Opus
**Dependency:** Waits for Phase 3 (routing core spec must be stable before adding orchestration)
**Duration:** 1 session, exploratory

This is the forward-looking piece — not a build spec, an exploration:

- **Invocation syntax:** How one skill references another (`[SKILL: source-validation]`)
- **Skill graph structure:** Parent-child skill relationships, dependency edges
- **BST as orchestrator:** How the BST tracks position in a skill graph and reconfigures the agent per node
- **ACE playbook connection:** How the playbook's operational wisdom informs skill composition decisions
- **Feasibility assessment:** Is this the right next step, or should the routing core stabilize for N sessions first?

**Deliverable:** `COMPOSITIONAL_SKILLS_EXPLORATION.md` — design exploration, not spec.

---

## Dependency Map

```
Workstream A (Model Eval)          Workstream B (BST Architecture)
═══════════════════════            ═══════════════════════════════

[A1] Download models ──────────┐
                               │   [B1] BST Current State Audit (Opus)
[A2] Test battery ─────────┐   │         │
                           │   │         ├──→ [B2a] Output Compressor (Kestrel)
[A3] Comparison matrix ─┐  │   │         │         (no dependency, start now)
                        │  │   │         │
[A4] Jake decides ──────┤  │   │         ├──→ [B2b] BST-Gated Tool Injection
     model choice       │  │   │         │         (waits for B1)
                        │  │   │         │
                        │  │   │         ├──→ [B2c] TALE Reasoning Budget
                        │  │   │         │         (measure first, may defer
                        ├──┼───┼─────────┘          if v3 model is selected)
                        │  │   │
                        │  │   │   [B3] BST v3.3 Spec (Opus)
                        │  │   │         (waits for B1 + B2b)
                        │  │   │         │
                        │  │   │   [B4] Compositional Skills Exploration
                        │  │   │         (waits for B3)
                        │  │   │
                        └──┴───┘
                     Model choice informs
                     B2c (budget hint tuning)
                     and B3 (model profile)
```

**Critical path:** B1 (audit) → B2b (tool injection) → B3 (v3.3 spec)
**Independent path:** A1-A4 (model eval) runs in parallel with B1
**Independent path:** B2a (output compressor) runs in parallel with everything

---

## Assignments Summary

| Task | Owner | Status | Blocks | Blocked By |
|---|---|---|---|---|
| A1-A4: Model Evaluation | Kestrel (test), Jake (decide) | Ready to start | B2c tuning, B3 model profile section | Nothing |
| B1: BST Current State Audit | Opus | Ready to start | B2b, B3 | Nothing |
| B2a: Output Compressor | Kestrel | Ready to start | Nothing | Nothing |
| B2b: BST-Gated Tool Injection | Kestrel | Waiting | B3 | B1 (needs domain→tool mapping) |
| B2c: TALE Reasoning Budget | Kestrel | Waiting | Nothing | A4 (model choice affects baseline) + measurement infra |
| B3: BST v3.3 Spec | Opus | Waiting | B4, Kestrel implementation | B1 + B2b |
| B4: Compositional Skills | Opus | Waiting | Future implementation | B3 |

---

## Decision Points

**DP-1: Model Selection** (after A4)
Jake decides which Jackrong model becomes primary. This affects:
- Whether TALE reasoning budget (B2c) is still needed (v3's act-then-refine may reduce the need)
- BST enrichment template tuning in v3.3 spec (model-specific adjustments)
- Whether malformed message fixes require scaffolding changes or are resolved by model upgrade

**DP-2: Compositional Skills Go/No-Go** (after B3)
After the routing core spec is written and tool injection is validated, assess:
- Is the BST stable enough to add orchestration?
- Are there enough compositional skills to justify the infrastructure?
- Does the ACE playbook need to accumulate operational data first?
If no to any of these, Phase 4 defers and the routing core stabilizes.

---

## Success Criteria

This sprint succeeds if:
1. **Malformed message rate drops measurably** — either through model upgrade (Workstream A) or scaffolding fixes (Workstream B), or both
2. **Token economics improve measurably** — output compressor + tool injection + (optionally) reasoning budget produce documented context savings
3. **BST has a complete audit** — every downstream consumer documented, every failure mode cataloged, every signal overlap identified
4. **The team has a shared understanding** of what the BST is becoming (routing core) and where it's heading (orchestration engine)
5. **Model choice is data-driven** — the comparison matrix has real numbers, not vibes

---

## What This Sprint Does NOT Include

- **BST v3.3 implementation** — the spec is written but implementation is a separate sprint
- **Compositional skill implementation** — Phase 4 is an exploration document, not a build
- **ACE playbook implementation** — that's a separate workstream (see ACE_PLAYBOOK_DESIGN_NOTE.md)
- **Sleep consolidation integration** — the Curator and playbook are future work
- **Artifact panel implementation** — the design brief is written (ARTIFACT_PANEL_DESIGN_BRIEF.md), panel builds are a separate sprint

---

*Plan written by Opus. Session 061. The routing core is the foundation everything else stands on. Get it right, get it documented, get it tested. Then build upward.*
