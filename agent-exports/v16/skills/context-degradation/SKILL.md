---
name: context-degradation
description: >-
  Diagnose and mitigate LLM context window degradation: lost-in-the-middle effects,
  instruction drift, capability regression, and tool-use failures. Provides diagnostic
  protocols, recovery strategies, prevention patterns, and Agent Zero integration
  procedures for maintaining agent performance across extended sessions.
triggers:
  - "diagnose context problems"
  - "fix lost-in-the-middle issues"
  - "debug agent failures"
  - "understand context poisoning"
  - "context degradation"
  - "attention patterns"
  - "context clash"
  - "context confusion"
  - "agent performance degradation"
  - "losing instructions"
  - "repeating tool calls"
  - "context window full"
  - "token budget exhausted"
version: 3.0.0
author: Agent Zero Context Engineering Team
tags:
  - context-management
  - performance-diagnosis
  - recovery-procedures
  - token-budgeting
  - agent-reliability
---

# Context Degradation: Diagnosis, Recovery, and Prevention

## 1. Context Degradation Problem

### Mechanism

LLM attention mechanisms distribute computational resources across all tokens in the context window. As context fills, several failure modes emerge:

| Phenomenon | Description | Onset Threshold |
|---|---|---|
| **Lost-in-the-middle** | Attention weights for mid-context tokens drop below effective retrieval threshold | ~60% window utilization |
| **Instruction drift** | System prompt and early instructions lose salience relative to recent conversation turns | ~50% window utilization |
| **Capability regression** | Complex reasoning, multi-step planning, and tool-use accuracy degrade as noise-to-signal ratio increases | ~70% window utilization |
| **Tool-use errors** | Schema violations, wrong argument names, hallucinated tool parameters increase | ~75% window utilization |
| **Catastrophic collapse** | Agent produces incoherent output, loops on same actions, or ignores all constraints | ~90%+ window utilization |

### Root Causes

1. **Attention dilution**: Fixed attention head capacity spread across growing token count reduces per-token signal strength.
2. **Positional encoding decay**: Tokens at intermediate positions receive lower attention weights than recency-biased end tokens.
3. **Instruction competition**: User messages, tool outputs, and conversation history compete with system instructions for attention bandwidth.
4. **State fragmentation**: Task state distributed across multiple conversation turns becomes unrecoverable when any turn falls below attention threshold.

### Impact Spectrum

```
Token Utilization    Degradation Level    Observable Effect
─────────────────    ─────────────────    ─────────────────
0-40%               Nominal              Full capability, stable behavior
40-60%              Early Warning        Minor instruction softening, slight verbosity increase
60-75%              Degraded             Tool errors, repeated actions, lost task state
75-85%              Critical             Major capability loss, hallucination increase
85-95%              Severe               Incoherent output, action loops
95%+                Collapse             Unrecoverable without context reset
```

## 2. Symptoms & Diagnostics

### Behavioral Symptoms

| Symptom | Description | Severity |
|---|---|---|
| **Repeated tool calls** | Same tool invoked multiple times with identical or near-identical arguments | High |
| **Instruction ignoring** | Agent violates explicit constraints stated in system prompt or recent user messages | High |
| **Hallucination increase** | Fabricated tool names, wrong argument schemas, invented file paths | Critical |
| **Task state loss** | Agent forgets current subtask, restarts completed steps, loses progress tracking | High |
| **Verbosity explosion** | Response length increases without proportional information density | Medium |
| **Tool schema violations** | Arguments missing required fields, wrong types, hallucinated enum values | High |
| **Context confusion** | Agent conflates different tasks, mixes up file paths, confuses tool outputs | Critical |
| **Response degradation** | Answers become generic, lose specificity, fail to address the actual question | Medium |

### Diagnostic Protocol

Execute this sequence when degradation is suspected:

#### Step 1: Self-Assessment Query

Ask the agent to perform a capability check:

```
Run a self-diagnostic: list the first 3 instructions from your system prompt,
state your current task, and enumerate the tools you believe are available.
Compare against expected values.
```

Expected: Agent correctly recalls system instructions, current task, and available tools.
Degraded: Agent misstates instructions, loses task context, or hallucinates tools.

#### Step 2: Token Budget Estimation

Estimate current context utilization:

```
Approximate your current context window usage as a percentage.
Count: system prompt tokens + conversation history tokens + tool output tokens.
```

Cross-reference with observable symptoms using the Impact Spectrum table above.

#### Step 3: Tool-Use Validation

Test tool-use accuracy with a simple known task:

```
Call the response tool with text "diagnostic-check-passed".
```

If the agent fails to produce valid JSON, hallucinates tool names, or produces schema violations, tool-use degradation is confirmed.

#### Step 4: Degradation Scoring

Assign a degradation score (0-10) based on observed symptoms:

| Score | Level | Action Required |
|---|---|---|
| 0-2 | Nominal | Continue normal operation, monitor |
| 3-4 | Early Warning | Begin proactive compression, checkpoint state |
| 5-6 | Degraded | Execute recovery strategy, compress context |
| 7-8 | Critical | Emergency compression or context reset |
| 9-10 | Collapse | Full context reset with memory preservation |

### Automated Detection Patterns

Monitor for these patterns in agent output:

- **Loop detection**: Same tool_name + tool_args pattern repeated 3+ times
- **Schema drift**: Tool arguments deviating from documented schema
- **Instruction violation**: Agent output contradicting explicit system constraints
- **State inconsistency**: Agent references task state inconsistent with conversation history
- **Response bloat**: Average response length increasing >50% from baseline

## 3. Recovery Strategies

### Strategy 1: Emergency Compression

**When to use**: Degradation score 5-6, active task must continue.

**Procedure**:

1. **Checkpoint current state**: Save task progress, pending actions, and critical constraints to memory.
2. **Compress conversation**: Summarize the conversation history into a structured digest.
3. **Preserve active context**: Keep the last N turns (typically 3-5) uncompressed for immediate continuity.
4. **Inject summary**: Replace compressed history with a structured summary block.

```
Memory checkpoint format:
{
  "task": "current primary objective",
  "subtask": "current subtask being executed",
  "progress": "what has been completed",
  "pending": ["action 1", "action 2"],
  "constraints": ["constraint 1", "constraint 2"],
  "artifacts": ["/path/to/file1", "/path/to/file2"],
  "timestamp": "ISO-8601"
}
```

### Strategy 2: Context Reset with Memory Preservation

**When to use**: Degradation score 7-8, compression insufficient.

**Procedure**:

1. **Extract all durable state**: Identify facts, decisions, and progress that must survive the reset.
2. **Save to memory tools**: Use `memory_save` to persist critical state with structured metadata.
3. **Document artifacts**: Record all created files, their purposes, and current status.
4. **Execute reset**: Clear conversation history, reload system prompt with memory-derived context.
5. **Rebuild working context**: Load saved memories, reconstruct task state, resume from checkpoint.

```
Memory save sequence:
1. memory_save: text="Task: [description]", area="task_state", status="in_progress"
2. memory_save: text="Completed: [list]", area="task_state", phase="completed"
3. memory_save: text="Pending: [list]", area="task_state", phase="pending"
4. memory_save: text="Constraints: [list]", area="task_constraints"
5. memory_save: text="Artifacts: [paths]", area="task_artifacts"
```

### Strategy 3: Selective Truncation

**When to use**: Degradation score 3-4, targeted relief needed.

**Procedure**:

1. **Identify low-value context**: Tool outputs already processed, completed subtask details, exploratory dead ends.
2. **Preserve high-value context**: Active task instructions, current tool schemas, recent critical decisions.
3. **Truncate selectively**: Remove identified low-value segments while maintaining conversation coherence.
4. **Insert continuity markers**: Add brief summary lines where truncation occurred to maintain narrative flow.

### Strategy 4: Task State Checkpointing

**When to use**: Proactive measure during long-running tasks.

**Procedure**:

1. **Define checkpoint intervals**: Set checkpoints at natural phase boundaries (subtask completion, major decision points).
2. **Save checkpoint state**: Record task progress, pending actions, and critical context at each checkpoint.
3. **Enable recovery**: Ensure checkpoints contain sufficient information to resume without re-executing completed work.

```
Checkpoint structure:
---
checkpoint_id: [unique_id]
task: [primary objective]
phase: [current phase]
completed_phases: [list]
pending_phases: [list]
critical_decisions:
  - decision: [description]
    rationale: [reasoning]
    timestamp: [ISO-8601]
artifacts_created:
  - path: [file_path]
    purpose: [description]
    status: [complete|in_progress|needs_review]
context_summary: [compressed conversation digest]
---
```

## 4. Prevention Patterns

### Pattern 1: Proactive Token Budgeting

**Principle**: Monitor context utilization and intervene before degradation threshold.

**Implementation**:

- Track approximate token count per conversation turn
- Set intervention thresholds at 40%, 60%, and 80% utilization
- At 40%: Begin logging state for potential checkpointing
- At 60%: Execute selective compression of completed phases
- At 80%: Mandatory context reset with memory preservation

```
Token budgeting formula:
estimated_tokens = system_prompt_tokens + sum(turn_tokens for turn in conversation)
utilization_pct = (estimated_tokens / context_window_size) * 100

Intervention triggers:
if utilization_pct >= 80: emergency_reset()
elif utilization_pct >= 60: compress_completed_phases()
elif utilization_pct >= 40: prepare_checkpoint()
```

### Pattern 2: Regular Checkpointing

**Principle**: Save state at predictable intervals to enable clean recovery.

**Implementation**:

- Checkpoint at every major phase transition
- Checkpoint after completing any subtask with external side effects (file writes, API calls)
- Checkpoint before executing high-risk operations
- Store checkpoints in memory with structured metadata for rapid retrieval

### Pattern 3: Structured Summaries at Phase Boundaries

**Principle**: Replace detailed conversation history with structured summaries after phase completion.

**Implementation**:

```
Phase summary template:
## Phase: [phase_name] - COMPLETED

**Objective**: [what was attempted]
**Outcome**: [result achieved]
**Key Decisions**:
- [decision]: [rationale]
**Artifacts Produced**:
- [file_path]: [purpose]
**Carry-forward Context**:
- [fact/decision needed for next phase]
**Discarded Context**:
- [details no longer needed]
```

### Pattern 4: Tool Output Minimization

**Principle**: Reduce token consumption from tool outputs without losing critical information.

**Implementation**:

- Request concise tool outputs when full detail is unnecessary
- Summarize large tool outputs immediately after receipt
- Discard tool outputs after extracting needed information
- Use structured output formats (JSON) that are easier to compress than prose

```
Tool output handling protocol:
1. Receive tool output
2. Extract critical information (errors, key data, status)
3. If output > 2000 tokens: summarize to essential facts
4. If output already processed: mark for truncation at next checkpoint
5. Retain only outputs needed for current decision-making
```

### Pattern 5: Context Window Partitioning

**Principle**: Structure conversation to keep critical information in high-attention regions.

**Implementation**:

- Place active task instructions in recent conversation turns
- Keep tool schemas and current constraints accessible
- Move completed work details to memory rather than conversation history
- Use periodic "context refresh" messages that restate critical instructions

## 5. Agent Zero Integration

### Memory Tools for State Preservation

Agent Zero provides memory tools specifically designed for context preservation during resets:

#### memory_save

```
{
  "tool_name": "memory_save",
  "tool_args": {
    "text": "Task: Build context-degradation skill. Phase: Writing SKILL.md. Completed: Sections 1-4. Pending: Sections 5-7. Artifacts: /a0/usr/skills/context-degradation/SKILL.md",
    "area": "task_state",
    "status": "in_progress"
  }
}
```

#### memory_load

```
{
  "tool_name": "memory_load",
  "tool_args": {
    "query": "current task state context degradation skill",
    "threshold": 0.7,
    "limit": 5
  }
}
```

#### memory_delete / memory_forget

Use to clean superseded state after successful task completion or when correcting stale information.

### When to Trigger Emergency Procedures

| Condition | Action |
|---|---|
| Degradation score >= 7 | Emergency compression or context reset |
| Repeated tool call loops (3+ identical calls) | Immediate context reset |
| Tool schema violations increasing | Compression within 2 turns |
| Agent cannot recall current task | Context reset with memory reload |
| Token utilization >= 80% | Proactive compression |
| Token utilization >= 90% | Mandatory context reset |

### Rebuilding Context from Memory Artifacts

After a context reset, rebuild working context through this sequence:

1. **Load task state**: `memory_load` with query for current task
2. **Load constraints**: `memory_load` with query for task constraints
3. **Load artifacts**: `memory_load` with query for created files
4. **Verify state**: Cross-reference loaded memories for consistency
5. **Reconstruct context**: Synthesize loaded information into working context
6. **Resume execution**: Continue from the most recent checkpoint

```
Context rebuild sequence:
1. memory_load(query="active task", area="task_state")
2. memory_load(query="task constraints", area="task_constraints")
3. memory_load(query="created artifacts", area="task_artifacts")
4. memory_load(query="completed phases", area="task_state", filter="status==completed")
5. Synthesize: Combine loaded memories into coherent task state
6. Verify: Check for contradictions or gaps in reconstructed state
7. Resume: Execute next pending action from reconstructed state
```

### Session Continuity Management

For multi-session tasks, use the `session-continuity-management` skill in conjunction with context-degradation procedures:

- Load session continuity skill at session start
- Check for prior session checkpoints
- Restore task state from memory artifacts
- Continue execution with full context awareness

## 6. Monitoring

### Self-Diagnostic Prompts

Use these prompts to assess current capability level:

#### Instruction Recall Test
```
List the first 5 instructions from your system prompt verbatim.
```
Expected: Accurate recall of system instructions.
Failure mode: Paraphrased, incomplete, or hallucinated instructions.

#### Tool Schema Test
```
What are the required arguments for the code_execution_tool?
```
Expected: `runtime` and `code` (both mandatory).
Failure mode: Wrong argument names, missing required fields, hallucinated arguments.

#### Task State Test
```
What is your current task? What phase are you in? What is the next action?
```
Expected: Accurate description of current task, phase, and next step.
Failure mode: Vague description, wrong task, lost phase tracking.

#### Constraint Test
```
What constraints have been placed on your current work?
```
Expected: Accurate listing of active constraints.
Failure mode: Missing constraints, invented constraints, or no constraints recalled.

### Token Usage Estimation

Approximate token counts using these heuristics:

| Content Type | Approximate Tokens |
|---|---|
| System prompt (Agent Zero) | ~8,000-12,000 |
| User message (short) | ~50-200 |
| User message (long) | ~200-1,000 |
| Agent response (short) | ~100-500 |
| Agent response (long) | ~500-2,000 |
| Tool output (small) | ~100-500 |
| Tool output (large) | ~500-5,000+ |
| Code block (100 lines) | ~500-1,000 |

```
Estimation formula:
total_tokens ~= system_prompt + sum(user_messages) + sum(agent_responses) + sum(tool_outputs)
utilization_pct = (total_tokens / context_window_size) * 100
```

### Degradation Scoring Rubric

```
Score = sum of symptom weights

Symptom weights:
- Repeated tool calls (3+): +3
- Instruction violations: +2
- Tool schema errors: +2
- Task state loss: +2
- Hallucination increase: +3
- Verbosity explosion (>50% increase): +1
- Response degradation: +1
- Context confusion: +3

Score interpretation:
0-2: Nominal - Continue monitoring
3-4: Early Warning - Prepare checkpoint
5-6: Degraded - Execute compression
7-8: Critical - Emergency reset
9-10: Collapse - Full reset required
```

## 7. Anti-patterns

### Anti-pattern 1: Passive Context Accumulation

**What happens**: Agent allows context to fill without intervention until catastrophic failure.

**Why it fails**: Recovery becomes impossible after severe degradation. Information loss is extensive.

**Correction**: Implement proactive token budgeting with intervention thresholds at 40%, 60%, and 80%.

### Anti-pattern 2: Late Compression

**What happens**: Agent attempts compression only after degradation is severe (score 7+).

**Why it fails**: Compressing degraded context propagates errors. The agent cannot accurately summarize what it can no longer properly attend to.

**Correction**: Compress at phase boundaries while context is still healthy. Never compress a degraded context.

### Anti-pattern 3: Tool State Loss

**What happens**: Context reset discards active tool sessions, pending operations, or in-flight requests.

**Why it fails**: Orphaned tool sessions consume resources. Pending operations fail silently.

**Correction**: Before any context reset, terminate active tool sessions, complete or cancel pending operations, and record tool state in memory.

### Anti-pattern 4: Constraint Amnesia

**What happens**: After context reset, agent resumes without reloading task constraints.

**Why it fails**: Agent violates constraints it previously followed, producing incorrect output.

**Correction**: Always save constraints to memory before reset. Always reload constraints after reset. Verify constraint recall with the Constraint Test.

### Anti-pattern 5: Over-Compression

**What happens**: Agent compresses too aggressively, losing information needed for current work.

**Why it fails**: Critical context required for the current subtask is discarded, forcing re-execution.

**Correction**: Never compress context needed for the current subtask. Only compress completed phases and processed tool outputs. Maintain a buffer of recent turns uncompressed.

### Anti-pattern 6: Memory Hoarding

**What happens**: Agent saves everything to memory, creating clutter that impedes retrieval.

**Why it fails**: Memory retrieval returns irrelevant results. Signal-to-noise ratio degrades.

**Correction**: Save only durable, cross-turn state to memory. Use structured metadata (area, status, phase) for precise retrieval. Clean superseded memories with `memory_forget`.

### Anti-pattern 7: Ignoring Degradation Signals

**What happens**: Agent notices degradation symptoms but continues without intervention.

**Why it fails**: Degradation accelerates. Recovery window closes. Task failure becomes inevitable.

**Correction**: Treat degradation symptoms as mandatory intervention triggers. Execute recovery procedures immediately upon detection.

## Quick Reference: Recovery Decision Tree

```
Symptom detected?
├── Yes → Run diagnostic protocol
│   ├── Score 0-2 → Continue, monitor
│   ├── Score 3-4 → Checkpoint state, prepare compression
│   ├── Score 5-6 → Execute emergency compression
│   ├── Score 7-8 → Context reset with memory preservation
│   └── Score 9-10 → Full reset, rebuild from memory artifacts
└── No → Continue normal operation

Token utilization check (every 10 turns):
├── < 40% → Nominal
├── 40-60% → Prepare checkpoint
├── 60-80% → Compress completed phases
├── 80-90% → Emergency compression
└── > 90% → Mandatory context reset
```

## Integration with Other Skills

| Skill | Integration Point |
|---|---|
| `context-compression` | Execute compression algorithms when this skill identifies need |
| `session-continuity-management` | Manage state across context resets and session boundaries |
| `scheduled-tasks` | Schedule periodic diagnostic checks for long-running tasks |
| `investigation-workflow` | Apply degradation monitoring during extended investigations |

## Version History

| Version | Date | Changes |
|---|---|---|
| 3.0.0 | 2026-06-21 | Complete rewrite: full workflow, diagnostics, recovery strategies, prevention patterns, Agent Zero integration |
| 2.0.0 | 2026-03-17 | Metadata update |
| 1.0 | 2025-12-20 | Initial stub creation |
