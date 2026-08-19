---
name: multi-agent-patterns
description: Design, implement, and debug multi-agent architectures using Agent Zero's call_subordinate mechanism. Covers pattern selection, coordination protocols, fault tolerance, and anti-pattern avoidance.
version: '2.0'
author: Agent Zero Contributors
tags:
  - multi-agent
  - orchestration
  - delegation
  - supervisor-pattern
  - parallelism
  - fault-isolation
trigger_patterns:
  - "design multi-agent system"
  - "implement supervisor pattern"
  - "create swarm architecture"
  - "coordinate multiple agents"
  - "parallel agent execution"
  - "agent handoff protocol"
  - "subordinate orchestration"
  - "fan-out fan-in pattern"
---

# Multi-Agent Patterns

Production-ready patterns for designing, implementing, and debugging multi-agent systems within Agent Zero's `call_subordinate` framework.

## 1. Multi-Agent Architecture: Why Multiple Agents

Single-agent systems hit fundamental limits: context window saturation, sequential bottleneck, single-point failure, and inability to specialize across domains. Multi-agent architectures address these through four mechanisms.

| Mechanism | Benefit | Agent Zero Implementation |
|-----------|---------|--------------------------|
| **Specialization** | Each agent optimizes for a narrow domain, improving output quality | Profile selection via `call_subordinate(profile="researcher")` |
| **Parallelism** | Independent subtasks execute concurrently, reducing wall-clock time | Multiple subordinate calls with independent objectives |
| **Fault Isolation** | Failure in one agent does not corrupt the entire pipeline | Per-subordinate error handling and retry logic |
| **Scalability** | Add agents for additional capacity without redesigning core logic | Dynamic subordinate spawning based on task decomposition |

### When to Use Multi-Agent

Use multi-agent when the task exhibits at least two of these properties:

1. **Decomposable**: The task breaks into independent or weakly-coupled subtasks
2. **Heterogeneous**: Subtasks require different expertise (research, coding, analysis)
3. **Parallelizable**: Subtasks can execute without strict sequential dependency
4. **Fault-tolerant**: Partial results from failed subtasks are acceptable
5. **Context-heavy**: Individual subtasks exceed practical context window limits

Do not use multi-agent for simple tasks, tightly-coupled operations requiring shared mutable state, or when communication overhead exceeds computation cost.

## 2. Pattern Catalog

### Supervisor-Worker

A central coordinator delegates tasks to specialized workers and aggregates results.

**Structure**: One supervisor N workers
**Communication**: Supervisor sends tasks, workers return results
**Best for**: Complex tasks with clear decomposition into specialized subtasks

```json
{
  "thoughts": ["Decomposing task into 3 specialized subtasks"],
  "tool_name": "call_subordinate",
  "tool_args": {
    "profile": "researcher",
    "message": "Research component A: [specific objective]",
    "reset": true
  }
}
```

**Agent Zero implementation**: The supervisor (current agent) maintains task state, dispatches via `call_subordinate`, and synthesizes results. Workers are stateless — they receive complete context in the message and return complete results.

### Pipeline

Sequential chain where each agent's output becomes the next agent's input.

**Structure**: Agent 1 → Agent 2 → Agent 3 → ... → Agent N
**Communication**: Output of stage N feeds input of stage N+1
**Best for**: Multi-stage processing (extract → transform → analyze → report)

```python
# Pipeline execution pattern
stage1_result = call_subordinate(profile="developer", message="Extract data from...")
stage2_result = call_subordinate(profile="researcher", message=f"Analyze: {stage1_result}")
stage3_result = call_subordinate(profile="default", message=f"Synthesize report from: {stage2_result}")
```

**Critical constraint**: Each stage must produce output in a format the next stage can consume. Define serialization contracts explicitly.

### Fan-Out/Fan-In

Parallel execution of independent subtasks with result aggregation.

**Structure**: One dispatcher → N parallel workers → One aggregator
**Communication**: Dispatcher broadcasts tasks, aggregator collects results
**Best for**: Embarrassingly parallel workloads (multiple searches, parallel analyses)

```json
{
  "thoughts": ["Fan-out: 4 parallel research queries"],
  "tool_name": "call_subordinate",
  "tool_args": {
    "profile": "researcher",
    "message": "Query 1/4: Research market trends in sector A",
    "reset": true
  }
}
```

**Agent Zero constraint**: Sequential tool calls mean fan-out is logical, not truly concurrent. The framework processes calls sequentially, but each subordinate operates independently. Design for logical parallelism: independent objectives, no cross-dependencies.

### Brainstorm/Refine

Divergent generation followed by convergent evaluation.

**Structure**: Generator agents → Evaluator agent → Synthesis
**Communication**: Generators produce candidates, evaluator scores and filters
**Best for**: Creative tasks, solution exploration, design alternatives

**Workflow**:
1. Spawn multiple generator subordinates with divergent prompts
2. Collect all proposals
3. Spawn evaluator subordinate with scoring criteria
4. Synthesize top candidates into final recommendation

### Debate/Converge

Multiple agents argue positions, then converge on consensus.

**Structure**: N position holders → Moderator → Consensus
**Communication**: Structured rounds of argument, counter-argument, synthesis
**Best for**: Complex decisions requiring multiple perspectives, risk assessment

**Workflow**:
1. Assign distinct perspectives to subordinates (optimist, pessimist, realist)
2. Each subordinate produces analysis from assigned perspective
3. Current agent synthesizes conflicting viewpoints
4. Identify areas of agreement and principled disagreement
5. Produce balanced conclusion with confidence intervals

### Hierarchical

Multi-level delegation with intermediate supervisors.

**Structure**: Root supervisor → Level-1 supervisors → Level-2 workers
**Communication**: Top-down task assignment, bottom-up result reporting
**Best for**: Very complex tasks requiring multiple levels of decomposition

**Agent Zero constraint**: Each `call_subordinate` is one level deep. For deeper hierarchies, the subordinate itself calls its own subordinates. This creates nested delegation chains.

### Peer-to-Peer

Agents communicate directly without central coordinator.

**Structure**: N agents with mutual awareness
**Communication**: Direct message passing between agents
**Best for**: Distributed problem solving, consensus algorithms

**Agent Zero limitation**: Agent Zero's architecture is inherently hierarchical — the current agent orchestrates subordinates. True peer-to-peer requires simulating direct communication through the orchestrator relaying messages.

### Market-Based

Agents bid on tasks based on capability and load.

**Structure**: Task pool → Bidding agents → Task assignment
**Communication**: Task announcements, capability declarations, result submissions
**Best for**: Dynamic workloads with heterogeneous agent capabilities

**Agent Zero implementation**: Simulate by evaluating task-agent fit before dispatching. Select profile based on task requirements rather than fixed assignment.

## 3. Agent Zero Implementation

### Profile Selection

Available profiles determine subordinate capabilities:

| Profile | Use Case | Strengths |
|---------|----------|----------|
| `default` | General tasks, synthesis | Balanced capabilities |
| `researcher` | Information gathering, analysis | Deep research, source validation |
| `developer` | Code generation, debugging | Software engineering, architecture |
| `hacker` | Security analysis, penetration testing | Vulnerability assessment, security auditing |

**Selection heuristic**: Match profile to primary task characteristic. Research-heavy → `researcher`. Code-heavy → `developer`. Security-focused → `hacker`. Mixed → `default` with explicit role definition in message.

### Message Formatting

Subordinate messages must be self-contained. The subordinate has no access to the parent's context window.

**Required message components**:
1. **Role definition**: "You are a [specialist role]"
2. **Objective**: Clear, measurable goal
3. **Context**: All information the subordinate needs
4. **Constraints**: Format requirements, scope boundaries
5. **Output specification**: Expected result structure

**Template**:
```
You are a [role]. Your task is to [objective].

Context: [relevant background information]

Constraints:
- [constraint 1]
- [constraint 2]

Output format: [specification]

Deliverable: [what constitutes completion]
```

### State Passing

Subordinates are stateless. All state must be explicit in the message or passed via file artifacts.

**File-based state passing**:
```python
# Parent writes state file
with open('/a0/usr/workdir/task_state.json', 'w') as f:
    json.dump({"phase": 2, "results": [...], "next_step": "analysis"}, f)

# Subordinate reads state file
# Message includes: "Read /a0/usr/workdir/task_state.json for current state"
```

**Result aggregation**:
```python
# Collect results from multiple subordinates
results = []
for query in queries:
    result = call_subordinate(profile="researcher", message=f"Research: {query}")
    results.append(result)

# Synthesize aggregated results
synthesis = call_subordinate(
    profile="default",
    message=f"Synthesize these findings: {json.dumps(results)}"
)
```

## 4. Communication Protocols

### Structured Handoffs

Define explicit input/output contracts between agents.

**Handoff contract**:
```json
{
  "handoff_id": "task_001_phase_2",
  "from_agent": "researcher",
  "to_agent": "developer",
  "input_format": "structured_findings",
  "output_format": "implementation_plan",
  "validation_criteria": ["all_findings_addressed", "actionable_steps"]
}
```

### Shared Memory via File Artifacts

When subordinates need to share state:

1. **Write phase**: Parent agent writes shared state to `/a0/usr/workdir/shared/`
2. **Read phase**: Subordinate reads state file as first action
3. **Update phase**: Subordinate appends results to shared file
4. **Merge phase**: Parent reads and merges all subordinate outputs

**File naming convention**: `{task_id}_{agent_role}_{timestamp}.json`

### Result Serialization

Standardize result formats for reliable aggregation:

```json
{
  "task_id": "unique_identifier",
  "agent_profile": "researcher",
  "status": "success|partial|failed",
  "confidence": 0.85,
  "result": {
    "findings": [...],
    "sources": [...],
    "uncertainties": [...]
  },
  "metadata": {
    "execution_time_seconds": 45,
    "tokens_consumed": 12000
  }
}
```

### Conflict Resolution

When subordinates produce conflicting results:

1. **Source quality weighting**: Prefer results from higher-quality sources
2. **Consensus voting**: When N subordinates address the same question, majority wins
3. **Expert arbitration**: Spawn a specialist subordinate to adjudicate
4. **Explicit disagreement**: Document conflicts rather than forcing false consensus

## 5. Coordination & Synchronization

### Barrier Synchronization

Wait for all subordinates to complete before proceeding:

```python
# Barrier: collect all results before next phase
all_complete = False
results = []
while not all_complete:
    result = call_subordinate(profile="researcher", message=current_task)
    results.append(result)
    all_complete = len(results) == expected_count
```

### Result Collection

Pattern for collecting results from multiple subordinates:

```python
def collect_results(tasks, profile="default"):
    results = []
    for i, task in enumerate(tasks):
        result = call_subordinate(
            profile=profile,
            message=f"Task {i+1}/{len(tasks)}: {task}",
            reset=True
        )
        results.append({"task": task, "result": result, "index": i})
    return results
```

### Timeout Handling

Agent Zero tool calls have built-in timeouts. Design for partial completion:

1. **Idempotent tasks**: Subordinate work should be retryable
2. **Checkpoint files**: Subordinates write progress to files periodically
3. **Partial result acceptance**: Define minimum viable output for each subordinate

### Retry Logic

```python
max_retries = 3
for attempt in range(max_retries):
    try:
        result = call_subordinate(profile=profile, message=message)
        if validate_result(result):
            break
    except Exception as e:
        if attempt == max_retries - 1:
            handle_failure(task, e)
        continue
```

### Partial Failure Handling

When some subordinates fail:

1. **Assess criticality**: Is the failed task essential or supplementary?
2. **Partial synthesis**: Proceed with available results, noting gaps
3. **Compensating actions**: Spawn replacement subordinate with adjusted parameters
4. **Graceful degradation**: Reduce output quality rather than failing entirely

## 6. Orchestration Patterns

### Dynamic Agent Spawning

Spawn subordinates based on runtime analysis:

```python
def dynamic_dispatch(task):
    complexity = assess_complexity(task)
    if complexity > HIGH_THRESHOLD:
        # Decompose and spawn multiple subordinates
        subtasks = decompose(task)
        return [call_subordinate(message=st) for st in subtasks]
    else:
        # Single subordinate handles it
        return call_subordinate(message=task)
```

### Load Balancing

Distribute work across subordinates based on capability:

| Task Type | Optimal Profile | Rationale |
|-----------|----------------|----------|
| Literature review | `researcher` | Source validation expertise |
| Code generation | `developer` | Programming specialization |
| Security audit | `hacker` | Security domain knowledge |
| Synthesis | `default` | Balanced generalist |

### Adaptive Delegation

Adjust delegation depth based on task complexity:

```
Simple task (complexity < 3): Direct execution, no delegation
Moderate task (3 <= complexity < 7): Single subordinate
Complex task (7 <= complexity < 12): Multiple subordinates, fan-out
Very complex (complexity >= 12): Hierarchical delegation, multiple levels
```

## 7. Debugging Multi-Agent Systems

### Tracing Execution

Track subordinate execution for debugging:

1. **Task IDs**: Assign unique identifiers to each subordinate call
2. **Timestamp logging**: Record start/end times for each delegation
3. **Input/output capture**: Log messages sent and results received
4. **State snapshots**: Capture system state before/after each subordinate call

**Trace format**:
```json
{
  "trace_id": "trace_001",
  "parent_task": "market_analysis",
  "subordinate_calls": [
    {
      "call_id": "sub_001",
      "profile": "researcher",
      "message_hash": "abc123",
      "start_time": "2026-01-15T10:30:00Z",
      "end_time": "2026-01-15T10:32:15Z",
      "status": "success",
      "result_size_chars": 4500
    }
  ]
}
```

### Identifying Bottlenecks

Common bottlenecks:

1. **Context overflow**: Subordinate message exceeds practical limits → truncate or split
2. **Sequential dependency**: Pipeline stages waiting on previous stage → parallelize where possible
3. **Result aggregation**: Too many results to synthesize → pre-filter or summarize
4. **Profile mismatch**: Wrong profile for task → reassign with correct profile

### Diagnosing Communication Failures

1. **Missing context**: Subordinate lacks required information → enrich message
2. **Format mismatch**: Output format incompatible with consumer → standardize contracts
3. **Ambiguous instructions**: Subordinate misinterprets task → clarify objectives
4. **State inconsistency**: Subordinates working with stale state → refresh shared files

### State Consistency Checks

Verify state integrity across agents:

```python
def verify_consistency(results):
    # Check all results reference same data version
    versions = set(r.get("data_version") for r in results)
    if len(versions) > 1:
        log_warning(f"Version mismatch: {versions}")

    # Check temporal ordering
    timestamps = [r.get("timestamp") for r in results]
    if not all(timestamps[i] <= timestamps[i+1] for i in range(len(timestamps)-1)):
        log_warning("Temporal ordering violation")
```

## 8. Anti-Patterns

### Over-Delegation

**Symptom**: Simple tasks delegated to subordinates when direct execution is faster
**Detection**: Task complexity < 3, single tool call sufficient
**Fix**: Execute directly; reserve subordinates for tasks requiring specialization or parallelism

### Circular Delegation

**Symptom**: Agent A delegates to B, B delegates back to A with same task
**Detection**: Task ID appears in delegation chain more than once
**Fix**: Track delegation depth; enforce maximum chain length (recommended: 3 levels)

### State Inconsistency

**Symptom**: Subordinates produce conflicting results due to stale or divergent state
**Detection**: Results reference different data versions or timestamps
**Fix**: Centralize state management; use file-based state with versioning

### Runaway Fan-Out

**Symptom**: Excessive subordinate spawning without aggregation strategy
**Detection**: More than 10 parallel subordinates without intermediate aggregation
**Fix**: Implement hierarchical fan-out with intermediate supervisors

### Result Collision

**Symptom**: Multiple subordinates produce overlapping or duplicate results
**Detection**: High similarity between subordinate outputs
**Fix**: Define exclusive task boundaries; implement deduplication in aggregation

### Context Bloat

**Symptom**: Subordinate messages grow too large, exceeding practical limits
**Detection**: Message length > 8000 characters
**Fix**: Split into multiple focused subordinates; use file artifacts for large context

### Silent Failure

**Symptom**: Subordinate fails but parent continues without detection
**Detection**: Missing or empty results from expected subordinates
**Fix**: Validate every subordinate result; implement explicit error handling

## Quick Reference: Pattern Selection Matrix

| Task Characteristic | Recommended Pattern | Rationale |
|---------------------|-------------------|----------|
| Clear decomposition into specialties | Supervisor-Worker | Optimal profile matching |
| Multi-stage processing | Pipeline | Sequential dependency |
| Independent parallel tasks | Fan-Out/Fan-In | Maximum parallelism |
| Creative exploration | Brainstorm/Refine | Divergent then convergent |
| Complex decision making | Debate/Converge | Multiple perspectives |
| Very complex decomposition | Hierarchical | Multi-level specialization |
| Dynamic workload | Market-Based | Adaptive assignment |

## Implementation Checklist

Before deploying a multi-agent system:

- [ ] Task decomposition defined with clear boundaries
- [ ] Profile selection justified for each subordinate
- [ ] Message templates include all required context
- [ ] Result aggregation strategy defined
- [ ] Error handling for subordinate failures
- [ ] State management protocol established
- [ ] Delegation depth limited to prevent circular chains
- [ ] Result validation criteria specified
- [ ] Fallback strategy for partial failures
- [ ] Trace logging enabled for debugging
