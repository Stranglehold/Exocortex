---
name: "design-buildplan"
description: "Use this skill when given a complex task that requires planning before execution — multi-phase builds, projects with unknowns, tasks involving multiple tools or files, or any task where building wrong would be costly to fix. This skill produces a persistent build plan artifact at /a0/usr/workdir/buildplans/{plan_id}.md that execute-buildplan can then execute. Triggers: 'build X', 'create X', 'implement X', 'design a plan', 'make a plan', 'figure out how to', or any request where the path to completion is not immediately obvious."
version: "1.0.0"
author: "Kestrel"
tags: ["planning", "multi-step", "complex-tasks", "build", "design"]
trigger_patterns:
  - "design a build plan"
  - "make a plan for"
  - "plan how to build"
  - "figure out how to implement"
  - "design buildplan"
  - "create a plan before we build"
---

# Design Buildplan

## Purpose

This skill separates planning from execution for complex tasks. It produces a complete, grounded build plan that the agent (or a subordinate) can execute reliably — without mid-build discoveries forcing rework, without referencing tools that don't exist, and without ambiguous step definitions that could mean anything.

**Always use this skill before `execute-buildplan`.** Do not execute before planning is complete.

## When to Use

Use this skill when the task has two or more of these properties:
- Multiple phases (research → design → implement → verify)
- Unknowns that could change the approach (APIs, paths, existing code state)
- Multiple files or tools involved
- High cost of getting it wrong (production systems, data files, infrastructure)
- The operator said "plan it out" or "let's think about this first"

Do NOT use for:
- Single-step tasks ("rename this variable")
- Tasks with a fully known path where no research is needed
- Tasks explicitly scoped to one tool call

## Instructions

Execute these phases in order. Do not skip phases. Write outputs to the plan file.

---

### Phase 0: Check for Existing Plan

Before starting, check if a plan already exists for this task:

```python
# code_execution_tool
import os, glob
plans = glob.glob("/a0/usr/workdir/buildplans/*.md")
# Show the user any existing plans whose title matches the current task
```

If an existing plan covers this task, ask the user whether to continue from it or start fresh. If continuing, use `execute-buildplan` instead.

---

### Phase 1: Task Analysis

Analyze the request and define the task frame. Do NOT begin researching yet.

Produce:
```
TASK FRAME:
- Deliverable: {what the final output must be — one specific sentence}
- Success definition: {how we know it's done — something checkable}
- Hard constraints: {things that cannot change, e.g. "must run inside the container"}
- Unknowns: {things that could change the approach if we knew them}
- Tool candidates: {tools we think we'll need — unverified}
- Out of scope: {what this plan explicitly does NOT do}
```

**Do not proceed until the task frame is written.** If the deliverable cannot be stated in one sentence, the task is not sufficiently defined. Ask one clarifying question to resolve it.

---

### Phase 2: Research Questions

Convert each Unknown from the task frame into a concrete, answerable research question.

Rules:
- Each question must be answerable by reading something (a file, a web page, a log, a tool output)
- Maximum 7 questions. Minimum 1. If there are no unknowns, skip to Phase 4.
- Each question gets a tool hint: which tool to use to answer it
- Questions must be read-only. "Try it and see" is not a research question.

Format:
```
RESEARCH QUESTIONS:
Q1: {specific question}
    Tool: {search_engine / code_execution_tool / memory_load}
    Output format: {what a useful answer looks like}

Q2: {specific question}
    ...
```

---

### Phase 3: Parallel Research

Execute all research questions in parallel using `call_subordinate`. Do not answer them yourself.

```
For each question:
    call_subordinate(
        task="Research question: {question text}. Tool to use: {tool hint}. 
              Return your findings in 2-3 sentences. Read-only — do not modify anything.",
        context="Research phase for build plan. Return findings only."
    )
```

Batch in groups of max 5 if more than 5 questions. Wait for all responses before proceeding.

Collect all findings. If a sub-agent returns no useful information, note the gap.

---

### Phase 4: Synthesis

Review all research findings and produce:

```
RESEARCH SYNTHESIS:
Approach selected: {name}
Rationale: {1-2 sentences connecting research findings to this choice}
Key findings:
  - {finding that affected the approach}
  - {finding that ruled out an alternative}
Gaps remaining: {anything still unknown — these become risks in the plan}

Alternative approaches considered:
  A: {name} — rejected because: {one reason}
  B: {name} — rejected because: {one reason}
```

If no research was done (no unknowns): write "No unknowns identified. Proceeding with direct plan generation."

---

### Phase 5: Plan Generation

Generate the build plan phases and steps.

**Phase structure:**
- Phase 2: Design (architecture decisions, no code yet)
- Phase 3: Implementation (code, config, file changes)
- Phase 4: Verification (tests, checks, acceptance criteria)

Phase 1 (Research) is already complete — mark it as such in the plan file.

**For each step, define:**
```
- [ ] **P{phase}S{step}** — {short action label}: {what to do}
  - Tool: {which tool}
  - Success criteria: {specific, checkable condition}
  - Depends on: {P{n}S{m} if this step requires a prior step's output}
  <!-- Output: -->
```

**Rules for step quality:**
- Every step has a success criterion that can be checked without asking the agent that ran it
- No step references a tool without verifying it exists (grounding check, next phase)
- Maximum 10 steps per phase. If more are needed, split the phase.
- Steps within a phase that don't depend on each other can be parallelized during execution

---

### Phase 6: Grounding Check

Before writing the plan to disk, verify every tool and path reference.

```python
# code_execution_tool
import os, glob

# Check tool references
tool_dirs = [
    "/a0/python/tools/",
    "/a0/usr/plugins/exocortex/tools/"
]
available_tools = []
for d in tool_dirs:
    if os.path.exists(d):
        available_tools += [f.replace('.py','') for f in os.listdir(d) if f.endswith('.py')]

referenced_tools = {list each tool name mentioned in your plan steps}
missing_tools = [t for t in referenced_tools if t not in available_tools]

# Check path references
referenced_paths = {list each file/dir path mentioned in plan steps}
missing_paths = [p for p in referenced_paths if not os.path.exists(p)]

print(f"Missing tools: {missing_tools}")
print(f"Missing paths: {missing_paths}")
```

If anything is missing:
- Replace or remove the step that references it
- Re-run the grounding check until it's clean
- Do NOT write the plan with unverified references

---

### Phase 7: Write Plan File

Create the plan directory and write the artifact.

**Preferred path — Python (generates the plan_id):**

```python
# code_execution_tool
import os, uuid
from datetime import datetime

plan_id = str(uuid.uuid4())[:8]
plan_dir = "/a0/usr/workdir/buildplans"
os.makedirs(plan_dir, exist_ok=True)
plan_path = plan_dir + "/" + plan_id + ".md"

print("Plan ID: " + plan_id)
print("Plan path: " + plan_path)
print("Directory created: " + str(os.path.exists(plan_dir)))
```

After running the above, use `text_editor:write` to write the plan file to the path printed above. Fill in the template below with content from the task frame and research synthesis. Do NOT use Python to write the plan — write it via text_editor.

**Fallback — if code_execution fails entirely:** Choose any 8-character alphanumeric string as the plan_id (e.g. `a1b2c3d4`). Create the directory with `mkdir -p /a0/usr/workdir/buildplans` via code_execution, then write the plan file with text_editor:write.

**Write the plan with text_editor:write:**

```
text_editor:write
path: /a0/usr/workdir/buildplans/{plan_id}.md
content:
---
plan_id: {plan_id}
task: {deliverable from task frame}
created: {current UTC timestamp}
approach: {approach name from synthesis}
plan_version: 1
amendments: 0
status: ready
research_summary: |
  {2-3 sentence synthesis from Phase 4}
---

# Build Plan: {title}

## Context
{2-3 sentences: what this builds and why, from task frame}

## Out of Scope
{out_of_scope list from task frame}

## Phase 1: Research
*(complete — see research_summary in frontmatter)*

## Phase 2: Design
{all Phase 2 steps in format above}

## Phase 3: Implementation
{all Phase 3 steps}

## Phase 4: Verification
{all Phase 4 steps}

## Execution Log
| Step | Status | Verified | Timestamp |
|------|--------|----------|-----------|

## Amendments
*(append-only — max 3)*
```

---

## Output Format

Report to the user:
```
Build plan ready.
Plan ID: {plan_id}
File: /a0/usr/workdir/buildplans/{plan_id}.md

Summary:
- {N} steps across {M} phases
- Approach: {approach name}
- Research completed: {N} questions answered
- Grounding: all tool references verified

To execute: use the execute-buildplan skill with plan_id={plan_id}
```

Show the user a preview of the plan steps so they can review before execution begins.

---

## Failure Modes — Do Not Do These

- **Do not start implementing during planning.** If you find yourself writing code, stop. Save the plan first.
- **Do not skip the grounding check.** A plan with a non-existent tool reference will cause an execution loop.
- **Do not answer research questions yourself.** Dispatch to sub-agents. Your context does not have the freshest state.
- **Do not add steps to "be thorough."** Every step must be necessary. Unnecessary steps waste execution time and create opportunities for failure.
- **Do not proceed if the deliverable is undefined.** A vague deliverable produces a vague plan that fails at the first ambiguous decision.
- **Do not generate more than 7 research questions.** Beyond 7, you're stalling rather than planning.

## Example Triggers

- "I need to add CT certificate collection to the domain scanner"
- "Let's build a new Agent Zero tool that checks for running containers"
- "Design a plan to migrate the sleep consolidation from the python path to the profile path"
- "I want to add X to the stack — figure out how"
