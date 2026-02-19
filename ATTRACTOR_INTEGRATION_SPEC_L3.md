# Attractor Integration — Build Specification (Level 3)
## Organization Kernel · Phase 3: Graph Workflows

**Implementation note:** This spec defines intent, schemas, integration contracts, and
behavioral requirements. The implementing agent reads the Agent-Zero source and makes
all implementation decisions.

---

## Mission

Replace the linear step-sequence model in HTN Plan Templates with a directed graph
workflow engine. Plans become graphs where nodes are tasks, edges are conditional
transitions, and the engine traverses the graph deterministically based on verification
outcomes. This enables branching, retry loops, conditional paths, and escalation nodes
that linear plans cannot express.

The graph engine subsumes HTN — it's not a parallel system. The existing HTN plan
selector extension (`_15_`) is replaced by a graph-aware version that reads graph
definitions, tracks traversal state, and injects the current node's context into
the model's extras.

---

## Why This Matters

Linear plans fail on real tasks because:

1. **No branching.** "If reproduction fails, gather more context" can't be expressed.
   The plan either advances or stalls.

2. **No retry loops.** "Try the fix, test it, if it fails go back and try again" requires
   the plan to move backward. Linear plans only move forward or stall.

3. **No conditional paths.** "If the bug is in Python, use pytest. If it's in JS, use
   node test." The same task requires different tool chains based on runtime discovery.

4. **No escalation nodes.** "If stuck after 2 retries, escalate to XO" is a PACE concept
   that should be embedded in the workflow graph, not bolted on externally.

5. **No parallel potential.** In microcosm, graphs execute one node at a time. But the
   graph structure identifies which nodes are independent — meaning macrocosm mode can
   parallelize them across agents without any plan modification.

---

## Concepts

### Workflow Graph
A directed graph where:
- **Nodes** are tasks (tool execution, verification, decision points, escalation)
- **Edges** are transitions with optional conditions
- **The engine** traverses the graph from a start node, following edges based on
  verification outcomes, until it reaches an exit node or an escalation node

### Node Types

| Type | Shape | Purpose |
|------|-------|---------|
| `start` | Entry point | Every graph has exactly one. No action, just marks the beginning. |
| `task` | Work node | Has an action, tool hint, and verification. The model executes this. |
| `decision` | Branch point | Evaluates a condition and routes to different edges. No tool execution. |
| `escalate` | PACE trigger | Signals that the current approach has failed. Routes to supervisor or different role. |
| `exit` | Completion | Graph traversal complete. Task succeeded. |
| `checkpoint` | State save | Saves current progress. Enables resume after interruption. (Future use.) |

### Edge Conditions

Edges can be unconditional (always follow) or conditional (follow only if a condition is met).
Conditions are evaluated against the verification outcome of the source node.

| Condition | Meaning |
|-----------|---------|
| `on_success` | Previous node's verification passed |
| `on_fail` | Previous node's verification failed |
| `on_retry` | Previous node failed but retries remain |
| `on_exhaust` | Previous node failed and retries exhausted |
| `always` | Unconditional (default if no condition specified) |

### Traversal State
The graph engine maintains traversal state on the agent object, tracking:
- Which node is currently active
- Which nodes have been visited and their outcomes (pass/fail)
- Retry counts per node
- The full traversal path (for debugging and SALUTE reporting)

---

## Schema: Workflow Graph Definition

### File Location
Graphs are stored in the same plan library file, replacing the linear `steps` array
with a `graph` object. The library format is backward-compatible — plans with `steps`
continue to work as linear sequences. Plans with `graph` use the graph engine.

### Schema

```json
{
  "name": "Bug Fix Workflow",
  "domains": ["bugfix"],
  "triggers": ["fix bug", "debug", "troubleshoot", "not working", "broken"],
  "trigger_threshold": 1,
  "stale_after_turns": 15,

  "graph": {
    "start": "reproduce",

    "nodes": {
      "reproduce": {
        "type": "task",
        "name": "Reproduce the issue",
        "action": "Run the failing code/command to confirm the bug exists and capture error output",
        "tool": "code_execution_tool",
        "tool_hint": "Run the command or script that triggers the bug",
        "verify": {"type": "any_output"},
        "max_retries": 0
      },
      "gather_context": {
        "type": "task",
        "name": "Gather additional context",
        "action": "Read related source files, check logs, examine the environment to understand the failure",
        "tool": "code_execution_tool",
        "tool_hint": "cat, grep, find — examine files related to the error",
        "verify": {"type": "any_output"},
        "max_retries": 0
      },
      "isolate": {
        "type": "task",
        "name": "Isolate the root cause",
        "action": "Examine error output and source code to identify the specific cause of the bug",
        "tool": "code_execution_tool",
        "tool_hint": "Read source files, check stack traces, add debug output if needed",
        "verify": {"type": "any_output"},
        "max_retries": 0
      },
      "decide_approach": {
        "type": "decision",
        "name": "Decide fix approach",
        "description": "Based on isolation results, determine if this is a simple fix or needs deeper work"
      },
      "fix": {
        "type": "task",
        "name": "Implement the fix",
        "action": "Make the minimal code change to fix the identified root cause",
        "tool": "code_execution_tool",
        "tool_hint": "Edit the file(s) with the fix",
        "verify": {"type": "any_output"},
        "max_retries": 2
      },
      "test": {
        "type": "task",
        "name": "Test the fix",
        "action": "Re-run the original failing command to confirm the bug is resolved",
        "tool": "code_execution_tool",
        "tool_hint": "Run the same command from the reproduce step",
        "verify": {"type": "output_not_contains", "value": "error"},
        "max_retries": 0
      },
      "verify_no_regression": {
        "type": "task",
        "name": "Check for regressions",
        "action": "Run related tests or commands to ensure nothing else broke",
        "tool": "code_execution_tool",
        "tool_hint": "Run test suite or check related functionality",
        "verify": {"type": "any_output"},
        "max_retries": 0
      },
      "escalate_stuck": {
        "type": "escalate",
        "name": "Escalate — unable to fix",
        "reason": "Fix attempts exhausted without passing tests",
        "pace_level": "contingent"
      },
      "done": {
        "type": "exit",
        "name": "Bug fix complete"
      }
    },

    "edges": [
      {"from": "reproduce", "to": "isolate", "condition": "on_success"},
      {"from": "reproduce", "to": "gather_context", "condition": "on_fail"},
      {"from": "gather_context", "to": "reproduce", "condition": "on_success"},
      {"from": "gather_context", "to": "escalate_stuck", "condition": "on_fail"},
      {"from": "isolate", "to": "fix", "condition": "always"},
      {"from": "fix", "to": "test", "condition": "on_success"},
      {"from": "fix", "to": "escalate_stuck", "condition": "on_exhaust"},
      {"from": "test", "to": "verify_no_regression", "condition": "on_success"},
      {"from": "test", "to": "fix", "condition": "on_fail"},
      {"from": "verify_no_regression", "to": "done", "condition": "always"}
    ]
  }
}
```

### Linear Backward Compatibility

Plans that use the old `steps` array format continue to work. The engine treats them
as a simple linear graph internally: step[0] → step[1] → step[2] → ... → exit.
Each step gets `on_success` edges to the next step and `on_fail` behavior from the
step's `on_fail` field.

The implementing agent should detect whether a plan has `graph` or `steps` and handle
both. No existing plan library entries need modification unless you want to upgrade
them to graph format.

---

## Graph Engine

### Integration Point
- **Replaces:** `/a0/python/extensions/before_main_llm_call/_15_htn_plan_selector.py`
- **New file:** Same location, same prefix `_15_`, same class pattern
- **The extension is a drop-in replacement.** Same hook, same position in execution order,
  same integration contracts with BST and the org dispatcher.

### Behavioral Requirements

**Plan Matching (unchanged):**
- Same trigger matching logic as current HTN selector
- Reads BST domain from `agent._bst_store`
- Respects org kernel's HTN filter from `agent.get_data("_org_htn_allowed_plans")`
- If matched plan has `graph` field, use graph engine. If `steps` field, use linear engine.

**Graph Traversal:**
- On plan activation, create traversal state with the `start` node as current.
- On each `before_main_llm_call` invocation with an active graph:
  1. Read the last tool output from history (same as current HTN does)
  2. If there's tool output, run the current node's verification against it
  3. Based on verification outcome, select the outgoing edge to follow
  4. Move to the target node
  5. If target is `exit`: complete the plan, clear state, log completion
  6. If target is `escalate`: trigger PACE level change, log escalation, clear plan
  7. If target is `task` or `decision`: inject its context into `loop_data.extras_temporary`
- Edge selection priority when multiple edges match:
  1. `on_success` / `on_fail` (specific outcome)
  2. `on_retry` / `on_exhaust` (retry-aware)
  3. `always` (fallback)
- If no edge matches the current outcome, treat as a stall and log a warning.

**Retry Handling:**
- Each task node has a `max_retries` field (default 0 = no retries).
- Track retry count per node in traversal state.
- When a node fails verification:
  - If retries remain: follow `on_retry` edge (or stay on current node if no `on_retry` edge)
  - If retries exhausted: follow `on_exhaust` edge (or `on_fail` if no `on_exhaust` edge)

**Decision Nodes:**
- Decision nodes don't execute tools. They evaluate a condition based on the
  traversal state and recent history, then route along the appropriate edge.
- In microcosm mode with a single model, the "decision" is effectively:
  check the last tool output and follow the matching edge.
- The decision node's `description` field is injected into extras so the model
  understands why the routing happened.

**Escalation Nodes:**
- When traversal reaches an escalation node:
  1. Set `agent._org_pace_level` to the node's `pace_level` value
  2. Log the escalation with the node's `reason`
  3. Emit an immediate SALUTE report (if org kernel is active)
  4. Clear the graph traversal state
  5. Inject a message into extras telling the model the plan was escalated and why

**Context Injection Format:**
Injected into `loop_data.extras_temporary` (same key as current HTN uses).
The format should show:
- The graph name and current progress
- Which nodes are completed, failed, or pending
- The current node's full details (action, tool hint, verification criteria)
- The available paths forward (what happens on success vs failure)
- A clear instruction to execute the current node

Example:
```
[WORKFLOW: Bug Fix Workflow]
  reproduce [DONE] → isolate [DONE] → fix << CURRENT (attempt 2/3)
    Action: Make the minimal code change to fix the identified root cause
    Tool: code_execution_tool
    Hint: Edit the file(s) with the fix
    Verify: any non-empty output
    On success → test
    On fail (retries left) → retry fix
    On fail (exhausted) → escalate: unable to fix
  
Execute the current step. Do not skip ahead.
```

**Staleness (unchanged from HTN):**
- Track turns since last node transition.
- If exceeds `stale_after_turns` from the plan definition, expire the graph.
- Same behavior as current HTN staleness.

---

## Traversal State

Stored on `agent._htn_state` (same attribute as current HTN to maintain compatibility
with the supervisor loop and SALUTE reporting that read this attribute).

```json
{
  "plan_id": "bugfix_workflow",
  "plan_name": "Bug Fix Workflow",
  "mode": "graph",
  "current_node": "fix",
  "visited": {
    "reproduce": {"outcome": "success", "attempts": 1},
    "isolate": {"outcome": "success", "attempts": 1},
    "fix": {"outcome": "pending", "attempts": 2}
  },
  "path": ["reproduce", "isolate", "fix", "fix"],
  "total_nodes": 9,
  "completed_nodes": 2,
  "started_turn": 42,
  "turns_since_transition": 1,
  "stale_after_turns": 15
}
```

### Compatibility with Supervisor and SALUTE

The supervisor loop reads `_htn_state` for:
- `turns_since_progress` — map to `turns_since_transition`
- `current_step` / `total_steps` — map to `completed_nodes` / `total_nodes`
- `plan_id` and `plan_name` — unchanged

The SALUTE report reads the same fields. As long as the traversal state includes
these fields (or equivalents the supervisor can find), no changes to the supervisor
or SALUTE emission logic are needed.

**Critical:** If the implementing agent changes the field names, update the supervisor
and dispatcher to read the new names. Or better: keep the same field names and add
graph-specific fields alongside them.

---

## Starter Graph Library

Convert the following existing linear plans to graph format. The graphs should add
meaningful branching that the linear versions lack:

### 1. `bugfix_workflow` (shown in full above)
Key additions over linear: reproduce → gather_context loop, fix → test → fix retry loop, escalation node.

### 2. `git_feature_branch`
```
start → check_status → [clean?] 
  → yes: create_branch → make_changes → commit → push → done
  → no: stash_or_commit → check_status (retry)
  → exhaust: escalate
```
Key addition: handles dirty working directory instead of failing on step 1.

### 3. `codegen_module`
```
start → spec_review → scaffold → implement → test 
  → [pass?] → yes: document → done
  → no: fix_implementation → test (retry max 2)
  → exhaust: escalate
```
Key addition: implement → test → fix loop with bounded retries.

### 4. `refactor_safe`
```
start → run_baseline_tests → [pass?]
  → yes: extract_changes → modify → run_tests_again → [pass?]
    → yes: commit → done
    → no: revert → escalate
  → no: escalate (can't refactor without passing baseline)
```
Key addition: revert path if refactored code breaks tests. Safety-first workflow.

### 5. `docker_build_deploy`
```
start → check_dockerfile → build → [success?]
  → yes: test_image → [pass?]
    → yes: deploy → verify_running → done
    → no: fix_image → build (retry max 2)
    → exhaust: escalate
  → no: fix_dockerfile → build (retry)
  → exhaust: escalate
```
Key addition: build → fix → rebuild loop.

### Remaining Plans
Convert the remaining 5 linear plans (`git_merge_pr`, `file_backup_restore`,
`api_integration`, `dependency_update`, `log_investigation`) to graph format with
appropriate branching, retry loops, and escalation nodes. Use the patterns above
as templates. If a plan genuinely doesn't need branching, keep it linear but express
it in graph format for consistency.

---

## Event System (Lightweight)

As a bridge toward full Attractor-style event-driven observability, add a simple
event log to the traversal state.

### Event Types
| Event | Emitted When |
|-------|-------------|
| `plan_activated` | Graph traversal begins |
| `node_entered` | Traversal moves to a new node |
| `node_verified` | Verification result determined (pass/fail) |
| `retry_triggered` | Node is being retried |
| `edge_followed` | Traversal follows a specific edge |
| `plan_completed` | Exit node reached |
| `plan_escalated` | Escalation node reached |
| `plan_expired` | Staleness limit exceeded |

### Storage
Events are appended to a list in the traversal state:
```json
{
  "events": [
    {"type": "plan_activated", "turn": 42, "node": "start", "plan": "bugfix_workflow"},
    {"type": "node_entered", "turn": 42, "node": "reproduce"},
    {"type": "node_verified", "turn": 43, "node": "reproduce", "outcome": "success"},
    {"type": "edge_followed", "turn": 43, "from": "reproduce", "to": "isolate", "condition": "on_success"}
  ]
}
```

Keep the last 50 events. Trim older entries.

### SALUTE Integration
The SALUTE report's `activity` section can include the last 3-5 events for the
supervisor's awareness. This gives the supervisor not just a snapshot ("agent is on
node X") but a recent trajectory ("agent went from reproduce → isolate → fix, is now
on attempt 2 of fix").

---

## Testing Criteria

### Test 1: Linear Backward Compatibility
- Ensure any existing linear plan (with `steps` array) still works unchanged.
- Trigger a plan that hasn't been converted to graph format.
- Verify: same behavior as before — step advancement, verification, staleness.

### Test 2: Graph Activation
- Trigger the graph-based `bugfix_workflow` (e.g., "fix the bug in /tmp/test.py").
- Verify: log shows plan activation with graph mode.
- The context injection shows the graph structure, not a linear step list.

### Test 3: Branching on Failure
- Set up a scenario where the reproduce step fails (file doesn't exist).
- Verify: traversal follows the `on_fail` edge to `gather_context` instead of stalling.
- After gather_context, traversal should loop back to reproduce.

### Test 4: Retry Loop
- Set up a scenario where the fix step fails verification on first attempt.
- Verify: traversal retries the fix node (up to `max_retries`).
- On subsequent failure, verify: traversal follows `on_exhaust` edge to escalation.

### Test 5: Escalation Node
- Push a graph to its escalation node (exhaust retries on fix).
- Verify: PACE level changes to the escalation node's `pace_level`.
- The model receives context about why the plan was escalated.

### Test 6: Successful Completion
- Run a graph-based workflow that succeeds through all nodes to the exit.
- Verify: log shows plan completed, traversal state cleared.
- All intermediate nodes show as visited with success outcomes.

### Test 7: Event Log
- After any graph traversal, check the traversal state for the `events` list.
- Verify: events are present, correctly typed, and in chronological order.

### Test 8: Supervisor Compatibility
- Verify the supervisor loop still reads traversal state correctly.
- The supervisor should detect stalls, report progress, and fire PACE triggers
  using the graph traversal state just as it did with linear HTN state.

### Test 9: Org Kernel Integration
- With an active organization, verify that the graph plan respects the org dispatcher's
  HTN plan filter. If the active role doesn't list the matched plan in its capabilities,
  the plan should not activate.

---

## Installation

### Script: `install_graph_engine.sh`

**Must do:**
1. Replace `_15_htn_plan_selector.py` with the new graph-aware version
   (back up the original first)
2. Replace or update `htn_plan_library.json` with graph-format plans
   (back up the original first)
3. Clear `__pycache__`

**Must not do:**
- Break linear plan backward compatibility
- Modify the dispatcher, supervisor, or any other extension

### Addition to `install_all.sh`
Replace the HTN Plan Templates layer with the Graph Workflow Engine layer.

---

## Relationship to Attractor Framework

This implementation draws from StrongDM's Attractor specification:

**What we adopt:**
- Workflows as directed graphs (Attractor uses Graphviz DOT; we use JSON for consistency
  with the existing plan library)
- Nodes as typed tasks with verification
- Conditional edges based on outcomes
- Escalation as a first-class graph concept
- Event stream for observability

**What we defer:**
- DOT syntax as the definition format (JSON is more natural for Agent-Zero's extension
  system; DOT could be added as an alternative parser later)
- The full Interviewer interface for human-in-the-loop questions (our PACE escalation
  serves this role for now)
- Provider-aligned tool profiles per node (deferred to model evaluation framework)
- Checkpoint/resume from persistent storage (the `checkpoint` node type is reserved
  but not implemented)
- Parallel node execution (graph structure identifies parallelizable nodes but microcosm
  executes sequentially; macrocosm would parallelize)

**What we extend beyond Attractor:**
- PACE integration: escalation nodes trigger organizational PACE levels
- SALUTE reporting: traversal state feeds directly into the military reporting system
- Role-filtered plan activation: the org dispatcher gates which graphs a role can execute
- Retry loops with bounded attempts: Attractor doesn't specify retry semantics;
  we add max_retries per node with on_retry/on_exhaust edge conditions
