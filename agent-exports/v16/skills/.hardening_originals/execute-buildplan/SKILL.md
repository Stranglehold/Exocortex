---
name: "execute-buildplan"
description: "Use this skill to execute a build plan produced by the design-buildplan skill. Input is a plan_id (or plan file path). Executes each phase and step sequentially with independent verification, writes results to the plan file, and runs the test gate at completion. Do not use this without a plan file — use design-buildplan first. Triggers: 'execute the plan', 'run the build plan', 'execute buildplan', 'execute plan_id={id}', 'start the build'."
version: "1.0.0"
author: "Kestrel"
tags: ["execution", "build", "multi-step", "verification", "plan"]
trigger_patterns:
  - "execute the plan"
  - "execute buildplan"
  - "run the build plan"
  - "start the build"
  - "execute plan"
  - "run plan"
---

# Execute Buildplan

## Purpose

This skill executes a build plan created by `design-buildplan`. It runs each phase and step with independent verification, writes all outputs to the plan file, and stops cleanly when something fails rather than silently continuing with broken state.

**Do not start executing without a plan file.** If no plan file exists, use `design-buildplan` first.

## Before Starting

Retrieve the plan file path. The user will provide either a `plan_id` or the full path.

```python
# code_execution_tool
import os, glob

# If plan_id provided:
plan_path = f"/a0/usr/workdir/buildplans/{plan_id}.md"

# If no plan_id, list available plans:
plans = sorted(glob.glob("/a0/usr/workdir/buildplans/*.md"))
for p in plans:
    print(p)
```

If the plan file doesn't exist, stop and ask the user for the correct plan_id.

## Instructions

---

### Step 0: Validate the Plan

Read and validate the plan file before executing anything.

```python
# code_execution_tool
import re

with open(plan_path, 'r') as f:
    content = f.read()

# Extract frontmatter
fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
if not fm_match:
    print("ERROR: Plan file has no valid frontmatter")
    # Stop

import yaml
fm = yaml.safe_load(fm_match.group(1))

print(f"Plan ID: {fm['plan_id']}")
print(f"Task: {fm['task']}")
print(f"Status: {fm['status']}")
print(f"Amendments used: {fm['amendments']}/3")

# Check status
if fm['status'] == 'complete':
    print("WARNING: This plan is already marked complete. Confirm re-execution?")
    # Ask user before continuing
elif fm['status'] == 'abandoned':
    print("ERROR: Plan is marked abandoned. Requires human review.")
    # Stop
elif fm['status'] == 'needs_review':
    print("ERROR: Plan hit the amendment ceiling and needs human review.")
    # Stop

# Count unchecked steps
pending = len(re.findall(r'- \[ \]', content))
done = len(re.findall(r'- \[x\]', content))
print(f"Steps: {done} complete, {pending} pending")
```

Update the plan status to `active`:

```python
# code_execution_tool
updated = content.replace(
    f"status: {fm['status']}",
    "status: active"
)
with open(plan_path, 'w') as f:
    f.write(updated)
```

---

### Step 1: Read All Phases and Steps

Parse the plan to get the execution order.

```python
# code_execution_tool
import re

with open(plan_path, 'r') as f:
    content = f.read()

# Find all steps: pattern is "- [ ] **P{n}S{m}** — {label}: {action}"
step_pattern = r'- \[( |x)\] \*\*(P\dS\d+)\*\* — ([^\n]+)'
steps = re.findall(step_pattern, content)

# steps = [(status, id, "label: action..."), ...]
for status, step_id, label in steps:
    phase = int(step_id[1])
    print(f"Phase {phase} | {step_id} | {'done' if status == 'x' else 'pending'} | {label[:60]}")
```

Group steps by phase. Identify `depends_on` relationships by reading each step's block.

---

### Step 2: Execute Each Phase

For each phase (2 → 3 → 4, in order):

**Phase gate check** — Before starting a phase, confirm all steps in the preceding phase are `[x]`. If any are not, halt and report which step is blocking.

**Within each phase**, build execution batches in topological order:
- Steps with no `depends_on` can run in the first batch
- Steps whose `depends_on` are all `[x]` can be added to the next batch
- Maximum 5 steps per batch

For each step in a batch:

#### 2a. Execute the Step

Read the step's action and tool from the plan. Execute it.

```
Step P{n}S{m}: {label}
Action: {from plan}
Tool: {from plan}
```

Use the specified tool to execute the action. Do exactly what the plan says. Do not improvise or expand the scope of the step.

If the step specifies `call_subordinate`: dispatch the action to a sub-agent with a focused context window. Provide only what that sub-agent needs.

#### 2b. Write Output to Plan File

Immediately after execution, write the output to the plan file under the step's `<!-- Output: -->` marker.

```python
# code_execution_tool
with open(plan_path, 'r') as f:
    content = f.read()

# Find the Output marker for this step and fill it
# Target: <!-- Output: --> ... <!-- /Output --> under step P{n}S{m}
step_output = """<!-- Output: -->
{concise description of what was done}
{path to any artifact produced, or key value if applicable}
<!-- /Output -->"""

# Replace the empty marker
content = content.replace(
    f"<!-- Output: -->\n",  # find the marker after this specific step
    step_output,
    1  # replace only the first occurrence after the step
)
with open(plan_path, 'w') as f:
    f.write(content)
```

**Write the output immediately after execution, before verification.** The verifier reads from the plan file.

#### 2c. Verify the Step Independently

Verification reads filesystem state, not execution context. Start fresh.

```
SUCCESS CRITERIA for this step: {criteria from plan}

For each criterion:
    - File existence: os.path.exists(path)
    - Syntax: python3 -m py_compile file.py || echo FAIL
    - Content: grep "expected_string" file.py
    - Behavior: run the artifact and check exit code or output
    - Service health: check expected log line or port

Write verification result:
    PASS: all criteria met — describe what was checked
    FAIL: which criteria were not met — describe the evidence
```

**Do NOT verify by asking "did I succeed?" Verify by checking the filesystem.**

#### 2d. On PASS: Mark the Step Done

```python
# code_execution_tool
with open(plan_path, 'r') as f:
    content = f.read()

# Mark step as done
content = content.replace(
    f"- [ ] **{step_id}**",
    f"- [x] **{step_id}**",
    1
)

# Add to Execution Log
from datetime import datetime
log_row = f"| {step_id} | complete | verified | {datetime.utcnow().isoformat()} |\n"
content = content.replace(
    "## Amendments\n",
    f"{log_row}## Amendments\n"
)

with open(plan_path, 'w') as f:
    f.write(content)

print(f"[EXECUTE] {step_id} — PASS. Marked complete.")
```

#### 2e. On FAIL: Apply Amendment

Read current amendment count from frontmatter.

**If amendments < 3:**
```python
# code_execution_tool
with open(plan_path, 'r') as f:
    content = f.read()

import yaml, re
fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
fm = yaml.safe_load(fm_match.group(1))
count = fm['amendments'] + 1

# Append amendment
amendment_text = f"""
### Amendment {count} — {step_id}
- Failed criteria: {failed_criteria_description}
- Evidence: {what_was_checked_and_found}
- Revision: {brief_description_of_change}
- Status: retrying
"""

content = content.replace(
    "*(append-only — max 3)*",
    f"*(append-only — max 3)*\n{amendment_text}"
)

# Increment amendment counter
content = content.replace(
    f"amendments: {fm['amendments']}",
    f"amendments: {count}"
)

with open(plan_path, 'w') as f:
    f.write(content)

print(f"[EXECUTE] {step_id} — FAIL. Amendment {count}/3 applied. Retrying.")
```

Then revise the step's action (keeping the original visible with a strikethrough or revision note) and re-execute from 2a.

**If amendments >= 3:**
```python
# code_execution_tool
with open(plan_path, 'r') as f:
    content = f.read()

content = content.replace("status: active", "status: needs_review")
with open(plan_path, 'w') as f:
    f.write(content)
```

Report to the user:
```
Build plan {plan_id} has reached the amendment ceiling at step {step_id}.

Failed criteria: {what never passed}
What was attempted:
  1. {first attempt}
  2. {second attempt}  
  3. {third attempt}

The plan requires human review. Options:
  a) Review the plan file at {plan_path} and modify the step approach
  b) Abandon this plan and start fresh with design-buildplan
  c) Manually complete the step and mark it [x] in the plan, then resume
```

**Stop execution. Do not continue to the next step or phase.**

---

### Step 3: Phase Gate

After all steps in a phase are complete (or before starting the next phase):

```python
# code_execution_tool
import re

with open(plan_path, 'r') as f:
    content = f.read()

# Check this phase's section
phase_section = re.search(rf'## Phase {current_phase}.*?## Phase {current_phase + 1}', content, re.DOTALL)
if phase_section:
    incomplete = re.findall(r'- \[ \] \*\*(P\dS\d+)\*\*', phase_section.group())
    if incomplete:
        print(f"Phase {current_phase} gate BLOCKED. Incomplete steps: {incomplete}")
        print("Cannot advance to next phase until all steps are verified.")
        # Stop
    else:
        print(f"Phase {current_phase} gate PASSED. All steps verified.")
```

Mark the phase header in the plan file as complete:
```python
content = content.replace(
    f"## Phase {current_phase}:",
    f"## Phase {current_phase}: *(complete)*",
    1
)
```

---

### Step 4: Test Gate (After Phase 4 Complete)

Run the test gate after all phases are verified.

**Find pre-existing tests:**
```python
# code_execution_tool
import os, glob
from datetime import datetime

# Get plan creation time
import yaml, re
with open(plan_path, 'r') as f:
    content = f.read()
fm = yaml.safe_load(re.match(r'^---\n(.*?)\n---', content, re.DOTALL).group(1))
plan_created = datetime.fromisoformat(fm['created'])

# Find test files that existed BEFORE the plan was created
test_files = glob.glob("/a0/usr/**/*test*.py", recursive=True) + \
             glob.glob("/a0/usr/**/test_*.py", recursive=True)

pre_existing = [
    f for f in test_files
    if datetime.fromtimestamp(os.path.getmtime(f)) < plan_created
]

print(f"Pre-existing test files: {pre_existing}")
```

**Run pre-existing tests:**
```
For each test file:
    code_execution_tool: /opt/venv-a0/bin/python3 -m pytest {test_file} -v
    Record: pass/fail and which assertions failed
```

**If no pre-existing tests exist**, check for deterministic acceptance criteria in Phase 4 steps. Run those checks directly.

**If neither exists:**
```
Report:
"Test gate: No pre-existing tests found and no deterministic acceptance criteria 
in Phase 4 steps. Build steps are complete. Manual verification required."
```

Do NOT write new test files to serve as the acceptance test for the current build.

---

### Step 5: Final Report

```python
# code_execution_tool
import re, yaml
from datetime import datetime

with open(plan_path, 'r') as f:
    content = f.read()

fm = yaml.safe_load(re.match(r'^---\n(.*?)\n---', content, re.DOTALL).group(1))

total_steps = len(re.findall(r'- \[.\] \*\*P\dS', content))
done_steps = len(re.findall(r'- \[x\] \*\*P\dS', content))

# Mark complete
content = content.replace("status: active", "status: complete")
with open(plan_path, 'w') as f:
    f.write(content)
```

Report to user:
```
Build plan {plan_id} — COMPLETE

Task: {task from frontmatter}
Steps: {done_steps}/{total_steps} executed and verified
Amendments used: {amendments}/3
Test gate: {PASS / FAIL / manual-required}

Plan file: {plan_path}
```

---

## Rules — Do Not Break These

1. **Never self-verify.** After executing a step, verify by reading the filesystem. Do not check your own confidence.

2. **Write output to the plan file before verifying.** The verifier reads from the plan file, not from your context.

3. **Never skip the phase gate.** Phase 3 (Implementation) does not begin until Phase 2 (Design) is fully verified.

4. **Stop at amendment ceiling 3.** Do not attempt a fourth revision. Escalate.

5. **Test gate uses pre-existing tests only.** Never write tests during execution and use them as the acceptance gate for the same execution.

6. **Never continue past a blocked phase gate.** A step that fails verification blocks its phase. Its phase blocks the next phase.

7. **Irreversibility check before external actions.** Any step that deploys to production, sends a message, or modifies shared state must pass the `irreversibility-gate` check before execution.

---

## Failure Modes — Do Not Do These

- **Do not declare success after execution without checking the filesystem.** "I wrote the file" is not verification. `os.path.exists()` is verification.
- **Do not continue building when a step has failed verification.** Failed verification means the foundation is broken. Building on it makes it worse.
- **Do not generate a test file and immediately use it as the acceptance test.** You wrote the test. You can make it pass. That proves nothing.
- **Do not rewrite the plan from scratch when a step fails.** Amendments only. Max 3.
- **Do not pass artifacts through your context.** Write them to files. Reference the file paths. Large artifacts in context degrade precision by Phase 4.
- **Do not parallelize phases.** Parallelize steps within a phase only.

## Example Triggers

- "Execute the build plan" (plan_id retrieved from prior design-buildplan run)
- "Run plan abc12345"
- "Start the build — plan is at /a0/usr/workdir/buildplans/abc12345.md"
- "Continue executing — we left off at step P3S2"
