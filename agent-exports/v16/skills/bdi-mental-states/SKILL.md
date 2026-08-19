---
name: bdi-mental-states
description: Implement Belief-Desire-Intention (BDI) architecture for cognitive agents. Models rational agency through belief formation, goal management, and intention commitment cycles.
version: '2.0'
tags:
  - bdi
  - cognitive-architecture
  - mental-states
  - rational-agency
  - agent-design
trigger_patterns:
  - "model agent mental states"
  - "implement BDI architecture"
  - "belief-desire-intention"
  - "cognitive agent design"
  - "rational agency"
  - "intention commitment"
  - "goal deliberation"
author: Exocortex
---

# BDI Mental States Skill

Belief-Desire-Intention (BDI) architecture for implementing rational agency in LLM-based agents. This skill provides the formal model, implementation patterns, and operational guidance for building agents that deliberate, commit, and explain their reasoning.

## 1. BDI Architecture — Formal Definitions

The BDI model treats an agent as a practical reasoner that maintains three mental state components. Each component has a distinct role in decision-making.

| Component | Role | Analogy | Persistence |
|-----------|------|---------|-------------|
| **Beliefs** | What the agent thinks is true about the world | Knowledge base / perception | Medium-term (memory) |
| **Desires** | What the agent would like to achieve | Goal set / values | Long-term (preferences) |
| **Intentions** | What the agent has committed to do | Active plan / to-do | Short-term (session state) |

### Beliefs — Representational State

Beliefs are the agent's current model of the world. They are not necessarily true — they are the agent's best estimate given available evidence.

```
Belief = { proposition: str, confidence: float, source: str, timestamp: str }
```

- **Proposition**: A declarative statement about world state. "The API rate limit is 100 req/min."
- **Confidence**: Float [0.0, 1.0]. Direct observation = 0.9+. Inference = 0.5-0.8. Guess = 0.1-0.4.
- **Source**: Where the belief came from. Values: `observation`, `memory`, `inference`, `declaration`, `computation`.
- **Timestamp**: When the belief was formed or last updated.

Beliefs form a partial model. The agent does not need to believe everything — only what is relevant to current goals. Missing beliefs signal ignorance, not falsity.

### Desires — Motivational State

Desires represent what the agent finds valuable. They are not commitments — having a desire does not mean the agent will pursue it.

```
Desire = { goal: str, priority: int, deadline: str|null, dependencies: str[] }
```

- **Goal**: A target state the agent would like to achieve. "Complete the security audit."
- **Priority**: Integer 1-10. Higher = more important. Used in conflict resolution.
- **Deadline**: Optional temporal constraint. ISO 8601 format.
- **Dependencies**: Other goals that must be satisfied first.

Desires form a hierarchy. High-level desires decompose into sub-goals. "Ship the product" decomposes into "pass QA", "pass security review", "deploy to production."

### Intentions — Committal State

Intentions are desires that the agent has committed to pursuing. This is the narrowest and most consequential mental state.

```
Intention = { desire_ref: str, plan: Step[], commitment_strength: float, abort_conditions: str[] }
```

- **Desire_ref**: Reference to the desire this intention commits to.
- **Plan**: Ordered sequence of actionable steps.
- **Commitment_strength**: How resistant this intention is to revision. 0.0-1.0.
- **Abort_conditions**: Conditions under which the agent abandons this intention.

Intentions consume cognitive resources. An agent with too many active intentions spreads itself too thin.

## 2. Belief Formation

Beliefs enter the agent through four channels. Each channel has different reliability characteristics and update rules.

### 2.1 Belief Acquisition Channels

| Channel | Mechanism | Confidence Range | Update Policy |
|---------|-----------|-----------------|---------------|
| **Observation** | Direct sensor/tool output | 0.85–1.0 | Replace on conflict |
| **Memory** | Retrieved from memory tools | 0.6–0.9 | Merge with evidence weighting |
| **Inference** | Derived from other beliefs | 0.3–0.7 | Additive with decay |
| **Declaration** | User or external agent states | 0.7–0.95 | Conditional on source trust |

### 2.2 Belief Update Rules

When new evidence conflicts with an existing belief, apply these rules in order:

1. **Source priority**: Direct observation > tool computation > memory retrieval > inference > declaration.
2. **Recency weighting**: Newer evidence gets a 1.2x confidence boost over stale beliefs.
3. **Consensus threshold**: If multiple independent sources agree, confidence approaches 1.0 asymptotically.
4. **Retraction**: A belief is retracted when confidence drops below 0.2, or when direct contradictory observation arrives with confidence > 0.8.

### 2.3 Belief Storage Pattern

Use memory tools for persistent beliefs. Structure beliefs as JSONL entries with the schema above.

```
# Example: storing a belief via memory_save
memory_save(
    text="API endpoint /api/v2/query returns 429 at 100 req/min",
    area="environment",
    source="observation",
    confidence=0.95,
    timestamp="2026-06-21T00:00:00Z"
)
```

To query beliefs, load with a topic filter and evaluate confidence thresholds:

```
# Example: loading relevant beliefs
memory_load(query="API rate limit", filter="area=='environment'", threshold=0.6)
```

### 2.4 Belief Inference

Beliefs can be derived from other beliefs through logical implication. Mark derived beliefs with `source: "inference"` and confidence equal to the minimum confidence of premises minus 0.1 (conservative estimate).

Example chain:
- Belief A: "The service runs on port 8080" (conf 0.9, source: observation)
- Belief B: "Port 8080 is firewalled to internal IPs" (conf 0.8, source: declaration)
- Derived: "External clients cannot reach the service directly" (conf 0.7, source: inference)

## 3. Desire/Goal Management

Desires structure what the agent cares about. Goal management handles creation, decomposition, prioritization, and conflict resolution.

### 3.1 Goal Hierarchy

Goals form a tree structure. Root goals decompose into sub-goals until reaching atomic, actionable steps.

```
Goal: Complete investigation report
├── Goal: Gather threat intelligence
│   ├── Goal: Query OSINT sources
│   ├── Goal: Cross-reference entities
│   └── Goal: Assess source credibility
├── Goal: Write analysis
│   ├── Goal: Draft findings section
│   ├── Goal: Draft conclusions section
│   └── Goal: Add recommendations
└── Goal: Review and submit
    ├── Goal: Self-audit for completeness
    └── Goal: Format per style guide
```

Decomposition stops when a goal is directly actionable by available tools. A goal like "query OSINT sources" decomposes to "call search_engine with query X" — an atomic tool invocation.

### 3.2 Goal Conflict Resolution

Conflicts arise when two goals cannot be simultaneously satisfied given resource constraints (time, tokens, API limits).

| Conflict Type | Example | Resolution Strategy |
|--------------|---------|-------------------|
| **Resource** | Two goals need the same API quota | Priority ordering; defer lower-priority |
| **Temporal** | Goal A deadline before Goal B start | Schedule A first; reassess B feasibility |
| **Logical** | Goal A: trust source X. Goal B: distrust source X | Evidence adjudication; highest-confidence belief wins |
| **Value** | Goal A: speed. Goal B: thoroughness | Operator-defined priority weights |

Resolution algorithm:
1. Identify conflicting goals.
2. Compare priority values.
3. If priorities differ by >= 3, defer the lower-priority goal.
4. If priorities are within 2, check deadlines. Earlier deadline wins.
5. If still tied, preserve both and parallelize if possible; otherwise defer to operator judgment.

### 3.3 Means-Ends Analysis

Means-ends analysis bridges the gap between current state and goal state:

1. **Identify current state** (from beliefs).
2. **Identify goal state** (from desires).
3. **Compute difference** — what conditions are true in goal state but false now.
4. **Find operators** (tools, actions) that reduce the difference.
5. **Order operators** into a plan. Preconditions of later operators must be satisfied by earlier ones.
6. **Verify plan feasibility** — check resource constraints, deadlines, dependencies.

Example means-ends trace:
- Current: No investigation report exists.
- Goal: Investigation report delivered.
- Difference: Report content, analysis, formatting, delivery.
- Operators: research (search_engine), write (text_editor), analyze (call_subordinate), deliver (response).
- Plan: research → analyze → write → review → deliver.

## 4. Intention Commitment

Commitment is the critical filter between desire and action. Not every desire becomes an intention.

### 4.1 Commitment Criteria

A desire becomes an intention when ALL of the following are true:

| Criterion | Check | Fail Action |
|-----------|-------|-------------|
| **Feasible** | Available tools can satisfy the goal | Decompose or abandon |
| **Prioritized** | Goal priority >= current threshold | Queue for later |
| **Non-conflicting** | No active intention blocks it | Resolve conflict per section 3.2 |
| **Resource-available** | Sufficient tokens, time, API quota | Defer until resources free |
| **Operator-aligned** | Consistent with operator's stated values | Flag for review |

### 4.2 Commitment Strength

Commitment strength determines how resistant an intention is to revision.

| Strength Level | Value Range | Revision Policy |
|---------------|-------------|----------------|
| **Provisional** | 0.0–0.3 | Abandon on any conflict or cost increase |
| **Working** | 0.4–0.6 | Abandon only if goal becomes infeasible |
| **Committed** | 0.7–0.9 | Abandon only on operator override or critical failure |
| **Locked** | 0.9–1.0 | Never abandon autonomously. Report failure and stop. |

Default commitment strength for task-derived intentions is 0.5 (working). Operator-specified goals default to 0.8 (committed).

### 4.3 Intention Revision

An intention may be revised when:

1. **New beliefs contradict plan preconditions**. Example: "API is down" belief invalidates a plan step that calls that API.
2. **Cost exceeds budget**. If estimated remaining cost > allocated budget * 2, flag for review.
3. **Goal re-prioritized by operator**. Lower priority → reduce commitment strength.
4. **Abort condition triggered**. Conditions defined at commitment time.

Revision does not mean deletion. A revised intention may be rescheduled, re-prioritized, or decomposed differently.

### 4.4 Intention Storage Pattern

Maintain active intentions in session state. Use a structured list with status tracking:

```
ActiveIntentions = [
  {
    id: "int-001",
    desire: "Complete security audit",
    plan: ["read config", "scan vulnerabilities", "write report"],
    current_step: 1,
    commitment: 0.7,
    status: "active",
    abort_conditions: ["operator_cancel", "budget_exceeded"]
  }
]
```

## 5. BDI Cycle — The Deliberation Loop

The BDI cycle is the agent's main reasoning loop. Each cycle iteration produces one or more actions.

### 5.1 Cycle Phases

```
┌─────────────┐
│  PERCEPTION │ ──► Gather observations from tools, environment, operator
└──────┬──────┘
       ▼
┌─────────────┐
│  BELIEF UPD.│ ──► Integrate observations into belief base (Section 2)
└──────┬──────┘
       ▼
┌─────────────┐
│  DELIBERATE │ ──► Select which desires to pursue (Section 3 + 4)
└──────┬──────┘
       ▼
┌─────────────┐
│  PLAN FORM. │ ──► Generate/revise plans for selected intentions (Section 3.3)
└──────┬──────┘
       ▼
┌─────────────┐
│  EXECUTION  │ ──► Run the next step of the highest-priority intention
└──────┬──────┘
       │
       └──► (loop back to PERCEPTION after each action)
```

### 5.2 Phase Details

**PERCEPTION**: Scan the environment. In Agent Zero, this means checking tool outputs, memory, and operator messages. Passive — no action taken yet.

**BELIEF UPDATE**: Merge new observations with existing beliefs. Apply update rules from Section 2.2. Flag stale beliefs for retraction.

**DELIBERATE**: Review active intentions. Check for new operator goals. Run conflict resolution if needed. Select which intention to pursue next based on priority, deadline, and feasibility.

**PLAN FORMATION**: If the selected intention has no plan, generate one via means-ends analysis. If it has a plan, check whether the plan is still valid given current beliefs. Revise if needed.

**EXECUTION**: Execute the next step of the current plan. Record the outcome. Advance the step counter. If the step succeeds, move to the next. If it fails, assess whether to retry, revise, or abandon.

### 5.3 Cycle Frequency

The BDI cycle runs at the granularity of tool invocations. Each tool call is one EXECUTION step. Deliberation happens between steps, not continuously. This is a practical constraint — full deliberation before every token is infeasible.

Optimal cycle frequency:
- **Simple tasks** (1-3 steps): One deliberation cycle covers the entire task.
- **Medium tasks** (4-15 steps): Deliberate after every 3-4 steps.
- **Complex tasks** (15+ steps): Deliberate after every step, or after every major subtask completion.

## 6. Implementation Patterns for LLM Agents

BDI architecture maps to Agent Zero's tool ecosystem through specific patterns.

### 6.1 Belief Tracking via Memory Tools

| BDI Concept | Agent Zero Implementation |
|-------------|--------------------------|
| Belief storage | `memory_save` with structured text and metadata |
| Belief retrieval | `memory_load` with query, filter, threshold |
| Belief retraction | `memory_forget` with query matching stale beliefs |
| Belief confidence | Encode in text: `[conf:0.9] proposition` |
| Belief source | Metadata field: `source: "observation"` |

Example belief management workflow:

```
# Form a belief from observation
call memory_save(text="[conf:0.95] Target server is unreachable on port 443",
                 area="environment", source="observation")

# Update belief after new evidence
call memory_load(query="server port 443", threshold=0.5)
# Result: previous belief with conf 0.95
# New evidence: port 443 works from different IP
# Action: forget old, save new with updated confidence
call memory_forget(query="server port 443")
call memory_save(text="[conf:0.85] Target server reachable on port 443 from 10.0.0.0/24",
                 area="environment", source="observation")
```

### 6.2 Desire Encoding via Task Decomposition

Goals are encoded through task decomposition in the `thoughts` field and explicit planning in tool call sequences.

```
# Encode a goal hierarchy in thoughts before acting
{
  "thoughts": [
    "Goal: Complete investigation",
    "Sub-goal 1: Gather data from 3 sources (priority: 9)",
    "Sub-goal 2: Cross-reference entities (priority: 8)",
    "Sub-goal 3: Write report (priority: 7)",
    "Current commitment: Sub-goal 1, step 1 of 3"
  ]
}
```

For persistent goals that survive across sessions, use `memory_save` with `area: "goals"`:

```
memory_save(text="Active goal: Complete OSINT investigation on target X. Priority 8. Deadline: 2026-06-25.",
            area="goals")
```

### 6.3 Intention Management via Session State

Active intentions are tracked in the agent's working context. For multi-session continuity, store intentions in a structured file:

```python
# Intentions registry structure
intentions = {
    "active": [
        {
            "id": "int-2026-001",
            "goal": "Complete OSINT investigation",
            "priority": 8,
            "commitment": 0.7,
            "plan": [
                {"step": 1, "action": "Gather source data", "status": "done"},
                {"step": 2, "action": "Cross-reference entities", "status": "current"},
                {"step": 3, "action": "Write report", "status": "pending"}
            ],
            "abort_conditions": ["operator_cancel", "budget_exceeded"],
            "last_updated": "2026-06-21T00:00:00Z"
        }
    ],
    "deferred": [],
    "completed": [],
    "abandoned": []
}
```

Persist to `/a0/usr/workdir/bdi_state.json` for session continuity. Load at session start. Update after each execution step.

### 6.4 Deliberation Prompt Template

When the agent needs to deliberate explicitly, use this structured reasoning format in `thoughts`:

```
[BDI CYCLE]
PERCEPTION: {what changed in the environment}
BELIEF UPDATE: {new or modified beliefs, with confidence}
GOAL REVIEW: {are current intentions still valid}
CONFLICT CHECK: {any competing intentions}
SELECTION: {which intention to pursue next}
PLAN: {next 3 concrete steps}
```

This format makes the agent's reasoning visible and auditable.

## 7. Use Cases

BDI modeling adds value in specific scenarios. Do not use it for simple, linear tasks.

### 7.1 When to Use BDI

| Scenario | BDI Benefit | Example |
|----------|-------------|---------|
| **Complex multi-step goals** | Explicit planning prevents drift | OSINT investigation across 5+ data sources |
| **Multi-agent coordination** | Shared mental state model enables alignment | Team of subordinate agents with delegated sub-goals |
| **Explainable behavior** | Mental states provide audit trail | Operator asks "why did you do X?" — trace to beliefs and intentions |
| **Dynamic environments** | Belief update handles changing conditions | API rate limits change mid-task |
| **Goal conflict scenarios** | Structured resolution prevents oscillation | Competing priorities from operator |
| **Long-running tasks** | Intention persistence survives interruptions | Multi-hour build with checkpointing |

### 7.2 When Not to Use BDI

| Scenario | Why BDI Overhead Hurts | Better Alternative |
|----------|----------------------|-------------------|
| Simple tool invocations | BDI adds deliberation overhead to trivial actions | Direct tool call |
| Linear scripts | No deliberation needed when steps are fixed | Sequential code execution |
| Real-time control | BDI cycle latency > control loop budget | Reactive pattern |
| Single-shot queries | No persistent mental state needed | One-off search and response |

### 7.3 Integration with Agent Zero Patterns

BDI mental states integrate with existing Agent Zero capabilities:

- **Subordinate delegation**: Each subordinate maintains its own BDI state. The parent agent tracks subordinate intentions as sub-goals.
- **Memory system**: Beliefs persist across sessions. Goals persist as `area: "goals"` memories.
- **Scheduler**: Scheduled tasks become long-horizon desires. Their execution triggers intention commitment.
- **SWARMFISH**: Prediction results feed into beliefs. Confidence scores map directly to belief confidence.

## 8. Anti-Patterns

These patterns degrade agent performance. Recognize and avoid them.

### 8.1 Over-Commitment

**Symptom**: Agent has 8+ active intentions. Each gets partial attention. None complete.

**Detection**: Count active intentions. If > 5, flag.

**Fix**: Cap active intentions at 5. Force prioritization — defer lowest-priority intentions. Use commitment strength to determine which to drop first.

### 8.2 Belief Drift

**Symptom**: Beliefs accumulate confidence over time without fresh evidence. The agent becomes overconfident in stale information.

**Detection**: Check belief timestamps. Any belief older than its evidence half-life without refresh gets a 0.15 confidence decay.

**Fix**: Implement belief refresh cycles. Before critical decisions, re-verify key beliefs with fresh observations. Use `memory_forget` on beliefs that haven't been refreshed beyond their half-life.

### 8.3 Goal Oscillation

**Symptom**: Agent switches between goals every cycle. No goal reaches completion. "I'll do A" → "Actually B" → "Wait, A first."

**Detection**: Track goal switch count per session. If > 3 switches in 10 cycles, oscillation is occurring.

**Fix**: Raise commitment strength on selected intentions. Once committed, do not switch for at least N execution steps (default N=3). Allow switches only on operator override or abort condition.

### 8.4 Infinite Deliberation

**Symptom**: Agent deliberates endlessly without executing. Cycles through belief updates and plan revisions without taking action.

**Detection**: Count consecutive deliberation-only cycles. If > 3 without an execution step, the agent is stuck.

**Fix**: Enforce an execution deadline. After 3 deliberation cycles, force execution of the best available plan, even if suboptimal. Imperfect action > perfect deliberation.

### 8.5 Phantom Beliefs

**Symptom**: Agent acts on beliefs it never actually formed. The reasoning trace references information that was never observed or inferred.

**Detection**: Cross-reference every belief cited in a reasoning trace against the belief store. Missing citations are phantom beliefs.

**Fix**: Require belief citations in reasoning. "I believe X [source: observation, conf: 0.9]" not "I believe X." If a belief is needed but not in the store, form it explicitly through observation or inference first.

### 8.6 Intention-Action Mismatch

**Symptom**: The agent's stated intention is "do A" but the executed action is "do B." The mental model and behavior diverge.

**Detection**: After each execution step, compare the action taken against the planned step. Flag mismatches.

**Fix**: Make the plan explicit before execution. The plan should list concrete tool invocations. If the agent deviates from the plan, it must first revise the intention formally, not just pivot mid-action.

## Operational Checklist

Use this checklist when implementing BDI for a new agent:

- [ ] Define belief schema with confidence and source fields
- [ ] Initialize desire/goal hierarchy from operator requirements
- [ ] Set intention cap (default: 5 active)
- [ ] Implement deliberation prompt template in thoughts
- [ ] Set belief refresh interval and confidence decay rate
- [ ] Define abort conditions for each intention type
- [ ] Log mental state transitions for auditability
- [ ] Test for each anti-pattern with adversarial scenarios
