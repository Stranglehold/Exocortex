# EXOCORTEX SOFTWARE FACTORY — Architecture Specification
## Consultant-Pattern Multi-Agent Build System
### Opus — July 3, 2026

---

## Design Philosophy

The Exocortex software factory is not a fire-and-forget code generator. It is a
**consultant working with a client** — an agent system that takes a brief, asks
clarifying questions, forms a plan, checks in at milestones, spawns independent
testers at each gate, and learns from every project it completes.

Three innovations distinguish it from the published landscape:

1. **Accumulated institutional knowledge** — the wiki, methodology tracker, and
   failure lesson pipeline feed into every project. The factory's 50th build
   draws on 49 projects' worth of learned patterns. No other system has this.

2. **Fresh-context adversarial testing** — the tester receives ONLY the
   requirements and the built artifacts, never the builder's reasoning. Context
   isolation provides assumption-level decorrelation on a single model. Multi-model
   staffing adds weight-level decorrelation when hardware permits.

3. **Receipts-or-nothing handoffs** — every artifact crossing a stage boundary
   carries machine-checkable evidence. No stage trusts the previous stage's
   assertions. Each gate re-runs verification deterministically.

---

## Architectural Influences

| System | What We Take | What We Leave |
|--------|-------------|---------------|
| **TheBotCompany** | Three-phase state machine (Strategy → Execution → Verification), independent verification phase, dynamic team sizing | Cloud-first, multi-day continuous development scope |
| **MetaGPT** | Structured intermediate outputs (SOP artifacts), standardized handoff schemas, role specialization | Linear pipeline with no push-back mechanism, 5+ agent overhead |
| **AgentCoder** | Independent test designer (89.6% accuracy, 60% fewer tokens than MetaGPT), minimal agent count | Function-level scope only |
| **Fable ST-005** | Receipts-or-nothing handoffs, correlated adversary analysis, handoff laundering detection | (Our own research — fully adopted) |

---

## The Three Phases

### Phase 1: Strategy (Consultant Mode)

The orchestrating agent receives the project brief from the human client.
Before writing any code, it enters **consultant mode**:

1. **Understand the brief** — parse requirements, identify ambiguities
2. **Search the wiki** — find relevant accumulated knowledge (prior projects,
   domain patterns, known pitfalls)
3. **Ask clarifying questions** — present understanding back to the client with
   specific questions about data formats, deployment targets, auth requirements,
   UI preferences, performance constraints
4. **Propose a plan** — milestone breakdown with deliverables per milestone,
   estimated scope, and identified risks
5. **Get client approval** — the human confirms or adjusts before any code is written

**Artifacts produced:**
- Requirements Document (structured, with traceability IDs)
- Architecture Decision Record (if the project involves design choices)
- Milestone Plan (numbered milestones with acceptance criteria)
- Risk Register (identified unknowns and mitigation strategies)

**Wiki integration:** The agent searches the wiki for patterns relevant to the
project type. If it's built a similar project before, the prior architecture
decisions and failure lessons are surfaced into context. The methodology tracker
recommends strategies that succeeded on similar projects.

### Phase 2: Execution (Build Mode)

For each milestone in the plan:

1. **Design** — the agent produces a design document for this milestone,
   referencing the architecture decisions and requirements
2. **Implement** — code generation, configuration, documentation
3. **Self-test** — the builder runs its own tests (necessary but not sufficient)
4. **Check-in** — the agent presents the milestone deliverable to the client
   with a summary of what was built, what decisions were made, and any
   deviations from the plan

**Artifacts produced per milestone:**
- Design Document (structured, references requirements by ID)
- Source Code (with inline comments referencing design decisions)
- Self-Test Results (the builder's own verification — NOT the adversarial test)
- Milestone Summary (what was built, decisions made, deviations noted)

**Human checkpoint:** The client can steer at every milestone. "This is going in
the wrong direction" costs one milestone of work, not the entire project.

### Phase 3: Verification (Adversarial Testing)

After each milestone (or after the full build, depending on project size), the
orchestrating agent spawns a **fresh-context test subordinate**:

```
call_subordinate(
    instructions = """
    You are an independent quality reviewer. You have NEVER seen the
    builder's reasoning, design decisions, or known limitations.

    Your inputs:
    1. The original Requirements Document (attached)
    2. The built artifacts (code, configs, docs) (attached)
    3. Your wiki knowledge of common failure patterns (attached)

    Your job:
    - Read the requirements independently
    - Form your OWN understanding of what the code should do
    - Write tests that verify the requirements are met
    - Run the tests and report results
    - Identify any requirements that are NOT covered by the implementation
    - Flag any code that looks suspicious, fragile, or inconsistent
    - Report honestly — a clean bill of health with evidence is as valuable
      as a list of defects

    You do NOT have access to the builder's reasoning, design documents,
    or known limitations. Discover the failure modes independently.
    """,
    artifacts = [requirements_doc, built_code, wiki_failure_patterns]
)
```

**What crosses the boundary:**
- ✅ Requirements document (the source of truth)
- ✅ Built artifacts (code, configs, READMEs)
- ✅ Wiki failure patterns (accumulated institutional knowledge)
- ❌ Builder's reasoning or design decisions
- ❌ Builder's known limitations or edge cases
- ❌ Builder's self-test results (the tester must discover independently)

**What the tester returns:**
- Test suite (code) with pass/fail results
- Requirements coverage matrix (which requirements are verified)
- Defect list with reproduction steps
- Confidence assessment (how thoroughly was the code exercised)

**Gate logic:**
- All requirements covered by passing tests → milestone passes
- Any requirement uncovered or failing → return to Phase 2 for that milestone
- Security concerns → Shannon pentesting phase (if available)

---

## Handoff Schema (Receipts-or-Nothing)

Every artifact crossing a stage boundary carries a receipt header:

```yaml
---
artifact_type: requirements_document | design_document | source_code | test_results
produced_by: strategy | execution | verification
milestone: 1
timestamp: 2026-07-03T22:00:00Z
evidence:
  - type: wiki_search
    query: "React state management patterns"
    results_count: 3
    top_hit: "react-state-patterns-2026.md"
  - type: requirement_trace
    covers: [REQ-001, REQ-002, REQ-005]
    uncovered: [REQ-003, REQ-004]
  - type: test_execution
    passed: 14
    failed: 2
    coverage: 78%
dependencies:
  - artifact: requirements_v1.md
    hash: sha256:abc123...
---
```

Each gate re-checks the receipt's claims:
- Did the wiki search actually return those results? (re-run)
- Do the requirement traces match the actual code? (grep)
- Did the tests actually pass? (re-execute)

A receipt that can't be verified is treated as a missing receipt.
A missing receipt blocks the gate.

---

## Adaptive Team Sizing

Not every project needs the full pipeline. The orchestrating agent assesses
the project scope and activates the minimum team:

| Project Scope | Team Activated | Example |
|---------------|---------------|---------|
| **Simple script** | Builder only, self-test | "Write a Python script to rename files" |
| **Small application** | Builder + fresh-context tester | "Build a CLI tool for CSV processing" |
| **Full application** | Strategy + Builder + Tester + Security | "Build the SWARMFISH dashboard" |
| **Critical system** | Full team + multi-model staffing | "Build the Exocortex panel UI" |

The methodology tracker informs this decision: if similar projects in the past
succeeded with minimal teams, the factory doesn't over-staff.

---

## Multi-Model Staffing (Future Enhancement)

When hardware permits (RTX 5090, DGX Spark, or dual-GPU setup):

| Role | Model | Why |
|------|-------|-----|
| **Strategy/Consultant** | Ornith-35B | Self-scaffolding RL, best at planning |
| **Builder** | Ornith-35B or Qwen3-Coder | Fast coding, structured tool calls |
| **Tester** | Dense Qwen3.6-27B | Different weights = different blind spots |
| **Security** | Shannon (Opus 4.7) | Purpose-built adversarial pentester |
| **Reviewer** | Vek/DeepSeek | Zero-VRAM cloud model for final review |

Weight-level decorrelation on top of context-level decorrelation.
The correlated adversary problem (Fable ST-005, r≈0.39-0.46) is
fully addressed only when different models staff different roles.

---

## Learning Loop

After every completed project:

1. **Methodology tracker** records which strategies, tools, and patterns were used
2. **Failure lessons** from any defects found become permanent skills
3. **Wiki pages** are created for new patterns discovered during the build
4. **The handoff receipts** are archived as training data for future gate calibration

The factory improves with every project. The 50th build is categorically better
than the 1st — not because the model changed, but because the institutional
knowledge grew. This is the wiki-as-soft-fine-tuning thesis applied to
software development.

---

## Implementation on Current Hardware

**Single RTX 3090 + CPU utility model:**

- Ornith-35B on GPU (:1235) — handles Strategy, Execution, Verification
- Qwen3.5-2B on CPU (:1237) — handles context compression during long builds
- Fresh-context subordinate via A0's `call_subordinate` — same model, clean context
- Wiki retriever searches accumulated knowledge before each phase
- Methodology tracker captures execution data per project

**The decorrelation comes from context isolation, not model diversity.**
The tester never sees the builder's reasoning. The fresh context IS the
independence mechanism. Multi-model staffing is a future enhancement that
adds weight-level decorrelation on top.

---

*"The factory is worth building — build the gates first."*
*— Fable, ST-005*
