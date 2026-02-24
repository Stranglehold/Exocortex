---
name: command-structure
description: "Use this skill when designing, building, or operating multi-agent AI systems where tasks need hierarchical coordination, authority boundaries, and structured information flow. Triggers include: any multi-agent architecture design, subordinate agent spawning, task delegation patterns, escalation protocol design, supervisor-subordinate communication, standing order / persistent task management, or briefing generation. Also use when the user describes wanting agents that 'work autonomously', 'report back', 'operate within boundaries', or 'escalate when uncertain'. This skill replaces flat swarm patterns with structured command hierarchy."
---

# Command Structure Architecture

## Overview

The Command Structure is an organizational paradigm for multi-agent AI systems drawn from military command hierarchy and intelligence operations. Instead of flat agent swarms where every agent has equal authority and communicates peer-to-peer, this pattern establishes clear chains of command, authority boundaries, and structured information flow.

The human is not a participant in the swarm. The human is the commanding officer. Information flows upward. Authority flows downward. The system only surfaces information that crosses a defined threshold requiring human judgment.

## Core Paradigm

### What This Replaces

| Flat Swarm Pattern | Command Structure Pattern |
|-------------------|--------------------------|
| All agents equal authority | Hierarchical authority levels |
| Peer-to-peer communication | Information flows upward through chain |
| Any agent can take any action | Actions bounded by authority level |
| Human monitors all agents | Human receives synthesized briefings |
| Agents decide when to involve human | Escalation triggers are mechanical, not behavioral |
| Every agent reasons about everything | Specialized roles with bounded scope |

### The Napoleon Corps Analogy

Napoleon's corps system succeeded because each marshal received:
- **Mission objective** — what to accomplish
- **Rules of engagement** — what actions are permitted
- **Authority boundaries** — what decisions the marshal can make autonomously
- **Escalation triggers** — when to send a courier to Napoleon

The marshal didn't report every contact with the enemy. He handled situations within his authority and escalated only when conditions exceeded his pre-authorized decision space.

### The Intelligence Agency Analogy

Intelligence operations separate three functions:

| Function | Description | Agent Equivalent |
|----------|-------------|-----------------|
| **Collection** | Persistent gathering of raw information | Subordinate agents running scheduled tasks |
| **Analysis** | Synthesis into assessable intelligence | Supervisor model correlating outputs, detecting patterns |
| **Decision** | Strategic judgment on what to do | Human operator receiving structured briefings |

The operator doesn't sit in the collection room. They get a morning brief.

## Organizational Layers

### Layer 1: The Daemon (Scheduler)

A lightweight process that manages task scheduling. **This is NOT an LLM.** It's a deterministic program that:
- Maintains the task registry (standing orders)
- Checks which tasks are due on each cycle
- Spawns subordinate agents with task context
- Collects outputs
- Runs rule-based escalation checks
- Updates task state

Token cost: **zero.** The daemon never reasons. It schedules.

### Layer 2: Subordinate Agents (Field Operatives)

Individual agents spawned to execute specific tasks. Each subordinate operates within:
- A defined **scope** (what information/tools it can access)
- Defined **authority** (what actions it can take autonomously)
- Defined **escalation triggers** (conditions requiring upward reporting)
- A defined **output format** (structured reporting for supervisor consumption)

Subordinates do NOT communicate with each other directly. All information flows through the supervisor. This prevents cascading errors and ensures supervisory oversight of cross-domain interactions.

### Layer 3: Supervisor Agent (Field Commander)

A more capable agent that:
- Reviews subordinate outputs for cross-domain patterns
- Resolves escalations within supervisor authority
- Generates briefings for the human operator
- Allocates resources across competing tasks
- Detects when standing orders need updating

The supervisor activates on schedule or on escalation — it does NOT run continuously.

### Layer 4: Human Operator (Commanding Officer)

The human who:
- Defines standing orders (mission objectives)
- Sets authority boundaries (rules of engagement)
- Reviews escalation briefs
- Approves or rejects staged irreversible actions
- Adjusts standing orders based on changing conditions

## Standing Orders

The fundamental unit of work. A standing order defines a persistent task with:

```
Standing Order Schema:
  id: unique identifier
  name: human-readable name
  objective: what this task accomplishes
  
  schedule:
    type: "interval" | "cron" | "trigger" | "continuous"
    config: schedule-specific parameters
  
  authority:
    level: "autonomous" | "supervised" | "approval_required"
    allowed_tools: [list of tools this task may use]
    forbidden_tools: [explicit prohibitions]
    irreversibility_gate: true/false
    confidence_threshold: 0.0-1.0
  
  escalation:
    conditions: [list of conditions requiring escalation]
    max_autonomy_duration: maximum time before mandatory check-in
  
  output:
    format: structured output template
    destination: where results are stored
    briefing_level: "nominal" | "informational" | "advisory"
  
  state:
    status: "active" | "paused" | "completed" | "escalated" | "failed"
    last_run: timestamp
    next_run: timestamp
    run_history: [references to past outputs]
```

### Example Standing Orders

**Market Monitor:**
```
name: "Daily Market Monitor"
objective: "Track key market indicators and flag threshold crossings"
schedule: { type: "cron", config: "0 6,12,18 * * *" }  # 6am, noon, 6pm
authority: { level: "autonomous", allowed_tools: ["web_search", "compute"], irreversibility_gate: false }
escalation: { conditions: ["VIX > 30", "S&P daily move > 3%", "yield curve inversion change"] }
output: { format: "market_summary", briefing_level: "informational" }
```

**Repository Watch:**
```
name: "Upstream Repo Monitor"
objective: "Watch for changes to monitored repositories that affect our systems"
schedule: { type: "interval", config: "every 4 hours" }
authority: { level: "autonomous", allowed_tools: ["web_search", "git_operations"], irreversibility_gate: false }
escalation: { conditions: ["breaking change detected", "security advisory", "API deprecation"] }
output: { format: "repo_diff_summary", briefing_level: "advisory" }
```

**Research Task (Bounded):**
```
name: "Grid Capacity Analysis"
objective: "Compile current datacenter power consumption data and project constraints"
schedule: { type: "trigger", config: "manual_start" }
authority: { level: "approval_required", irreversibility_gate: true }
escalation: { conditions: ["analysis complete", "confidence below 0.7", "contradictory sources"] }
output: { format: "research_brief", briefing_level: "advisory" }
```

## Escalation Protocol

### Escalation Levels

| Level | Name | Trigger | Agent Action | Human Required? |
|-------|------|---------|-------------|-----------------|
| 0 | **Nominal** | Task completed within parameters | Log result, update state | No |
| 1 | **Informational** | Notable finding, no action needed | Queue for next briefing | No |
| 2 | **Advisory** | Finding may require future action | Stage recommendations, queue | No |
| 3 | **Decision Required** | Situation exceeds agent authority | Prepare options, hold for approval | **Yes** |
| 4 | **Urgent** | Time-sensitive, exceeds authority | Prepare options, notify immediately | **Yes** |
| 5 | **Emergency** | System integrity at risk | Execute pre-authorized procedure, notify | Notification only |

### Escalation Brief Format

When a subordinate or supervisor escalates to the next level:

```
ESCALATION BRIEF
  Level: [0-5]
  Source: [which standing order / agent]
  Timestamp: [when]
  
  SITUATION: [what happened — factual, concise]
  
  BOUNDARY: [which authority boundary was crossed]
  
  CANDIDATES: [possible actions, each with:]
    - Action description
    - Risk assessment (low/medium/high)
    - Reversibility (reversible/conditional/irreversible)
    - Resource cost estimate
  
  RECOMMENDATION: [which candidate and why]
  
  HOLD STATUS: [what is paused pending resolution]
```

### The Conversational Equivalent

Level 3 escalation, expressed naturally:

> "Hey boss, we encountered [situation]. We weren't sure how you wanted to proceed, so we started working on solutions but didn't implement or execute on them until we got your answer. Here are the options we prepared: [A, B, C]. We recommend [B] because [reasoning]. Standing order [X] is paused until you decide."

## Briefing System

### Briefing Types

| Type | Trigger | Content |
|------|---------|---------|
| **Scheduled Brief** | Cron (daily/weekly) | Summary of all task activity, findings, pending decisions |
| **Escalation Brief** | Task hits Level 3+ | Specific situation requiring operator decision |
| **Alert** | Level 4 urgent | Time-sensitive notification |
| **Status Check** | Operator requests | Current state of all active tasks |

### Scheduled Brief Template

```
OPERATIONAL BRIEF — [date]

STANDING ORDERS: [N] active, [N] paused, [N] failed

[For each completed task since last brief:]
  [LEVEL_TAG] [Task Name]
    Last run: [timestamp]
    Summary: [1-2 sentence finding]
    [If advisory+:] Staged action: [what was prepared]

PENDING DECISIONS: [count]
[List any Level 3+ escalations awaiting response]

NEXT SCHEDULED BRIEF: [date/time]
```

## Token Economics

The command structure paradigm is dramatically more efficient than proactive monitoring:

| Component | Token Cost | Frequency |
|-----------|-----------|-----------|
| Daemon scheduling | 0 | Continuous |
| Liveness checks | 0 | Every 60s |
| Simple subordinate task | ~2,000 tokens | Per execution |
| Complex analysis task | ~8,000 tokens | Per execution |
| Supervisor synthesis | ~4,000 tokens | Per batch |
| Briefing generation | ~2,000 tokens | Per brief |

**Example budget:** 5 standing orders × 4 runs/day + daily synthesis + daily brief = ~46,000 tokens/day

**Compare to proactive monitoring:** Polling every 15 seconds × 16 hours = ~1,920,000 tokens/day

The command structure is approximately **40x more token-efficient** because:
- The daemon uses zero tokens (pure scheduling)
- Tasks only fire when scheduled (not continuously polling)
- Subordinates have bounded scope (don't reason about everything)
- Supervisor only activates on batch completion or escalation

## Design Principles

1. **The daemon is dumb.** It schedules. It never reasons.
2. **Information flows upward, authority flows downward.** Never reversed.
3. **Silence is the default.** Only threshold-crossing findings surface.
4. **Mechanical enforcement over behavioral compliance.** Authority boundaries are enforced by the system, not by asking the model to be careful.
5. **Standing orders are the unit of work.** The system never invents its own objectives.
6. **Staged execution for irreversible actions.** See: Irreversibility Gate skill.
7. **Graceful degradation.** Component failure pauses affected tasks, not the whole system.
8. **Token cost is a first-class constraint.** Every design decision accounts for inference cost.
