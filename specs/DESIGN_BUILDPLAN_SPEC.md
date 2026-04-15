# DESIGN_BUILDPLAN Skill Spec

**Type:** Agent Zero Skill (agent-callable procedural guide)
**Skill file:** `skills/design-buildplan/SKILL.md`
**Companion:** `EXECUTE_BUILDPLAN_SPEC.md`
**Date:** 2026-04-10

---

## Research Lineage

- **"MAST: Benchmarking Multi-Agent Systems on Challenging Tasks"** (Wang et al., 2024, arXiv:2407.01477) — Taxonomy of 14 failure modes across multi-agent systems. Key finding: step repetition (15.7%) and unaware of termination (12.4%) are the top two single-failure modes; verification failures constitute 23.5% of all failures. Planning-before-execution pattern directly addresses the unaware-of-termination class.

- **"An LLM Compiler for Parallel Function Calling"** (Kim et al., 2023, arXiv:2312.04511) — LLM Compiler's two-stage architecture (Planner → Executor) with `$idx` variable substitution for inter-step artifact passing. Topological-order parallel execution reduces wall time to the critical path length rather than the sum. Research fan-out in `design_buildplan` directly applies this pattern.

- **"SagaLLM: Reliable Long-Horizon Task Execution"** (2024) — GlobalValidationAgent pattern: independent verifier that never shares execution context with the executor it validates. Applied in `execute_buildplan`; the planning phase here supports it by defining explicit success criteria per step so the validator has something deterministic to check against.

- **BabyAGI failure analysis** (Nakajima, 2023, github.com/yoheinakajima/babyagi) — Dynamic task generation from task results creates unbounded semantic search loops. The core failure: tasks generate sub-tasks, sub-tasks generate sub-sub-tasks, no convergence. Fixed upfront plans with bounded replanning (max 3 amendments) are the countermeasure. `design_buildplan` produces the fixed plan; `execute_buildplan` enforces the amendment ceiling.

- **"On the Reliability of LLM-Generated Tests"** (arXiv:2602.07900, 2026) — Agent-written tests resolve only 2.6% more issues than no tests; 70-77% of agent-written "tests" are print statements, not assertions. Verification in `execute_buildplan` must use pre-existing tests or deterministic acceptance criteria defined in the plan, never ad-hoc agent-written tests.

- **LangGraph supervisor benchmarks** (LangChain, 2024) — Supervisor-passes-summaries architecture starts ~50% worse than direct-response architectures due to telephone game degradation. Filesystem coordination (plan file as single source of truth) is the countermeasure; sub-agents write outputs directly to the plan file rather than returning them through a supervisor.

- **SkillsBench** (Li, Chen et al., 2026) — Curated procedural knowledge improves agent performance by 16.2pp. Focused 2-3 module skills outperform comprehensive documentation. This spec deliberately limits scope: `design_buildplan` covers planning only; execution is a separate skill.

---

## Motivation

The agent handles straightforward tasks well but fails predictably on complex multi-step projects:

1. **Uncontrolled scope expansion.** Without a defined plan, the agent adds steps as it discovers complexity. Tasks grow unbounded.

2. **No grounding check.** The agent writes plans referencing tools, paths, and APIs it hasn't verified exist. Execution then fails at the first unverified assumption.

3. **Research and build conflated.** The agent starts building before it knows enough to build well. Mid-build discoveries force rework.

4. **No success criteria per step.** When no criteria exist, the agent either verifies nothing (missing failures) or loops verifying things that don't converge.

5. **Plan lives in context, degrades through compression.** Long tasks exceed context, supervisor summaries lose fidelity. A plan file on disk is not compressible.

`design_buildplan` addresses points 1-5 directly: it separates the planning phase from execution, forces research to precede design, defines success criteria per step, and produces a persistent artifact.

---

## Design Principles

- **Research before build.** No implementation steps in a plan until all blocking unknowns are resolved. The planning phase includes an explicit research gate.

- **Deterministic grounding check.** Before the plan is finalized, every tool name, path, and dependency is verified to exist using `code_execution_tool`. A plan that references a non-existent tool is rejected.

- **Parallel research fan-out.** Research questions are read-only and independent. They are dispatched in parallel using `call_subordinate` (max 5 at a time) and synthesized after all return.

- **Fixed plan, bounded replanning.** The plan is complete when written. Amendments are append-only and capped at 3. No dynamic task generation from execution results.

- **Criteria-first step definition.** Every step defines its success criteria before it defines its action. This is the requirement that makes independent verification possible during execution.

- **Filesystem over message-passing.** The plan artifact is the coordination mechanism. No inter-agent context passing through supervisor memory.

---

## Components

### 1. Task Analyzer

**Purpose:** Breaks the user's request into a structured task frame before any research or planning begins. Prevents scope creep by establishing explicit boundaries up front.

**Mechanism:**
```
task_frame = {
    "deliverable": "what the final output must be (one sentence)",
    "success_definition": "how we know it's done (measurable)",
    "constraints": ["hard constraints — things that cannot change"],
    "unknowns": ["things we don't know that would affect the build"],
    "tool_candidates": ["tools we think we'll need, unverified"],
    "out_of_scope": ["things explicitly excluded"]
}
```

Derived from the user's request by the planning agent. If the user's request is ambiguous on the deliverable or success definition, the agent asks one consolidated clarifying question before proceeding.

**Edge Cases:**
- If the user provides a vague goal ("make the agent smarter"), derive a specific deliverable from context or ask.
- If constraints conflict, surface the conflict to the user before proceeding.

---

### 2. Research Question Generator

**Purpose:** Converts the task frame's unknowns into concrete, answerable research questions. Each question must be (a) read-only, (b) answerable by a sub-agent with tool access, and (c) necessary to resolve before the plan can be written.

**Mechanism:**
```
For each unknown in task_frame.unknowns:
    Formulate as: "What is [specific factual question]?"
    Add tool hint: which tool to use to answer it
    Add output format: what the answer should look like

Max research questions: 7
Min research questions: 1 (don't add noise)
```

**Edge Cases:**
- If a question is answerable from existing context or memory, skip it — don't spawn a sub-agent for something already known.
- If a question requires write access (e.g., "try this approach and see if it works"), it is not a research question. Flag it as a build risk instead.

---

### 3. Parallel Research Executor

**Purpose:** Dispatches research questions as parallel sub-agent calls and collects results. Applies the LLM Compiler fan-out pattern.

**Mechanism:**
```
Batch questions into groups of max 5.
For each batch:
    For each question in batch:
        call_subordinate(
            task=question.text,
            tools=[question.tool_hint],
            context="Research only. Read-only. Return findings as text."
        )
    Await all returns.
    Collect responses.

If a sub-agent fails or returns nothing useful:
    Note the gap in synthesis.
    Do not retry more than once.
```

**Edge Cases:**
- If all research questions fail: abort plan generation, report what was learned and what remains unknown.
- If research returns contradictory findings: note the contradiction explicitly in the synthesis; do not resolve it silently.

---

### 4. Research Synthesizer

**Purpose:** Converts raw research outputs into a structured synthesis that answers: what approach should we take, and why? Produces 2-3 candidate approaches with trade-off scoring.

**Mechanism:**
```
For each candidate approach (2-3):
    approach = {
        "name": "short label",
        "description": "what this approach does",
        "research_backing": ["which research findings support it"],
        "risks": ["what could go wrong"],
        "complexity_estimate": "low / medium / high",
        "score": <0-10, higher = better fit for this task>
    }

Select the highest-scoring approach.
Write research_summary (50-100 words) capturing the decision and key findings.
```

**Edge Cases:**
- If only one viable approach exists, score it and document why others were rejected.
- If no approach scores above 5/10, flag the task as high-risk and surface to user before proceeding.

---

### 5. Plan Generator

**Purpose:** Converts the selected approach into a phased, step-by-step build plan with success criteria per step. Produces the plan artifact.

**Mechanism:**
```
phases = {
    "research": already complete from steps 3-4,
    "design": architecture decisions, no code yet,
    "implementation": code/config changes,
    "verification": tests, acceptance criteria checks
}

For each step in each phase:
    step = {
        "id": "P{phase_num}S{step_num}",   // e.g. P2S1
        "label": "short action verb phrase",
        "action": "what to do",
        "tool": "which tool to use",
        "success_criteria": "specific, checkable condition",
        "output_artifact": "what file/data is produced (if any)",
        "depends_on": ["step IDs this step requires"]
    }
```

**Edge Cases:**
- Maximum steps per phase: 10. If more are needed, split into sub-phases.
- If a step has no checkable success criteria, it must be rewritten or removed.
- If a step depends on an artifact from a previous step, the dependency must be explicit.

---

### 6. Grounding Check

**Purpose:** Deterministic verification that every tool name, file path, and external dependency referenced in the plan actually exists. Runs before the plan is written to disk.

**Mechanism:**
```python
# For each tool reference in the plan:
code_execution_tool: check if tool exists in A0's tool registry
    → list files in /a0/python/tools/ and /a0/usr/plugins/exocortex/tools/

# For each file path reference:
code_execution_tool: os.path.exists(path)

# For each external service/API reference:
code_execution_tool: check if relevant config/credentials exist

# Report:
{
    "verified": [list of confirmed references],
    "missing": [list of unverified references with suggestions],
    "pass": len(missing) == 0
}
```

If grounding check fails: remove or replace the failing step references before writing the plan. Do not write a plan that references non-existent tools.

---

### 7. Plan Writer

**Purpose:** Writes the finalized plan to disk as a persistent markdown artifact. The plan file is the coordination mechanism for the entire execution phase.

**Mechanism:**

Plan file path: `/a0/usr/workdir/buildplans/{plan_id}.md`

Plan file format:
```markdown
---
plan_id: {uuid4[:8]}
task: {one-line description}
created: {ISO timestamp}
approach: {selected approach name}
plan_version: 1
amendments: 0
status: ready
research_summary: |
  {50-100 word synthesis}
---

# Build Plan: {Title}

## Context
{2-3 sentences: what this is building and why}

## Phase 1: Research
*[complete — see research_summary in frontmatter]*

## Phase 2: Design
- [ ] **P2S1** — {label}: {action}
  - Tool: {tool}
  - Success criteria: {criteria}
  <!-- Output: -->

## Phase 3: Implementation
- [ ] **P3S1** — {label}: {action}
  - Tool: {tool}
  - Success criteria: {criteria}
  - Depends on: P2S1
  <!-- Output: -->

## Phase 4: Verification
- [ ] **P4S1** — {label}: {action}
  - Tool: {tool}
  - Success criteria: {criteria}
  <!-- Output: -->

## Execution Log
| Step | Status | Verified | Timestamp |
|------|--------|----------|-----------|

## Amendments
*(append-only — max 3)*
```

---

## Pipeline Flow Diagram

```
User task request
        │
        ▼
[1] Task Analyzer
    → deliverable, constraints, unknowns, out_of_scope
        │
        ▼
[2] Research Question Generator
    → 1-7 read-only questions with tool hints
        │
        ▼
[3] Parallel Research Executor (call_subordinate × N, max 5/batch)
    → raw findings per question
        │
        ▼
[4] Research Synthesizer
    → 2-3 scored approaches, selected approach, research_summary
        │
        ▼
[5] Plan Generator
    → phases × steps × success_criteria
        │
        ▼
[6] Grounding Check (code_execution_tool, deterministic)
    → verified / missing
    If missing: revise steps → re-check
        │
        ▼
[7] Plan Writer (code_execution_tool)
    → /a0/usr/workdir/buildplans/{plan_id}.md
        │
        ▼
Report plan_id to user. Ready for execute_buildplan.
```

---

## File Inventory

| File | Location | Action | Purpose |
|------|----------|--------|---------|
| `SKILL.md` | `skills/design-buildplan/SKILL.md` | CREATE | Agent-callable skill |
| Plan artifact | `/a0/usr/workdir/buildplans/` | CREATE (at runtime) | Persistent plan file per task |

**Files NOT modified:**
- Any extension file
- Any config file
- Any existing tool
- Agent Zero core (`/a0/python/`)

---

## Testing Criteria

1. **Task analyzer produces a non-empty out_of_scope list.** A plan that scopes everything in is a plan that scopes nothing out. Every test invocation should produce at least one explicit exclusion.

2. **Research fan-out fires in parallel, not sequentially.** Verify via log timestamps: 3 research questions should complete in approximately the time of the slowest single question, not 3× that time.

3. **Grounding check rejects a plan with a non-existent tool.** Test: include a step referencing `tool_that_does_not_exist`. Grounding check must flag it; plan writer must not write the plan until it's corrected.

4. **Plan artifact is complete and parseable.** Every `<!-- Output: -->` marker is present. YAML frontmatter validates. All step IDs are unique. All `depends_on` references resolve to real step IDs.

5. **Research synthesis documents contradictions explicitly.** Feed two sub-agents contradictory findings. The synthesis must name the contradiction and state how the selected approach handles it, not silently pick one side.

---

## Dependency Map

```
User request
    │
    └─► design-buildplan SKILL.md (read by agent)
            │
            ├─► call_subordinate (research sub-agents)
            │       └─► search_engine / code_execution_tool / memory_load
            │
            └─► code_execution_tool (grounding check + plan write)
                    └─► /a0/usr/workdir/buildplans/{plan_id}.md  ←── consumed by execute_buildplan
```

---

## What This Does NOT Do

- Does NOT execute any build steps. Planning only.
- Does NOT write any code, configuration, or data files other than the plan artifact.
- Does NOT call the agent's text_editor or make any modification to existing files.
- Does NOT call external APIs or services during planning (research sub-agents use search_engine for web lookups, nothing more).
- Does NOT generate test code. Success criteria in the plan are descriptions, not code.
- Does NOT manage multiple concurrent plans. One plan per invocation.
- Does NOT interact with docker, containers, or deployment tooling. Those steps appear in the plan as actions to be executed later.

---

## Further Reading

- **"ReAct: Synergizing Reasoning and Acting in Language Models"** (Yao et al., 2022, arXiv:2210.03629) — Interleaved reasoning and acting. The `design_buildplan` pattern separates them: all reasoning (planning) before any acting (execution). Useful background for understanding why the separation improves reliability.

- **"TaskBench: Benchmarking Large Language Models for Task Automation"** (Shen et al., 2023, arXiv:2311.18760) — Structured task decomposition benchmarks. Relevant for understanding what makes step definitions unambiguous.

- **"HumanEval-v2 on Agentic Code Generation"** (2025) — Finds that pre-execution planning reduces hallucinated API calls by ~40% on code generation tasks. Supports the grounding check step.
