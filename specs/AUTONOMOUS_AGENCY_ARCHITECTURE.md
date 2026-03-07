# Autonomous Agency Architecture
## Operational Design for Persistent Agent-Zero Operations

**Version:** 1.0 — Initial Scoping Document  
**Date:** 2026-02-24  
**Author:** Jake + Claude (Exocortex Design Session)  
**Status:** DRAFT — Conceptual Architecture  

---

## 1. Premise

Agent-Zero's hardening layer has been built to compensate for the behavioral gaps of local language models. BST classifies intent. The meta-reasoning gate validates tool calls. Model profiles tune configuration to capability. Memory systems persist knowledge across sessions. Each of these systems addresses a specific failure mode that small models exhibit when operating without guardrails.

But all of these systems share a fundamental assumption: **the human initiates every interaction.** The agent activates when spoken to and stops when it responds. This is the reactive paradigm. It limits Agent-Zero to being a tool — powerful, but inert between uses.

This document proposes the architectural shift from reactive tool to **autonomous agency** — a persistent operational structure where Agent-Zero manages standing tasks, monitors domains, synthesizes intelligence, and escalates to the human operator only when necessary. The human is not the subject being monitored. The human is the commanding officer.

---

## 2. What This Is Not

The proactive agent research community (ICLR 2025 ProactiveAgent, OpenClaw heartbeat, memU) is building systems that watch the user's environment — keyboard input, clipboard, browser activity — and try to predict what the user wants before they ask. That model has three problems for our use case:

1. **Token cost.** Predicting human intent from behavioral signals requires constant LLM inference against unstructured environmental data. On a 20B local model with 8-16K effective context, this is prohibitively expensive.

2. **False positive rate.** The best academic result (Tsinghua ICLR 2025) achieves 66.47% F1 on proactive task prediction. One in three suggestions is wrong. An agent that proactively offers bad help is worse than one that stays quiet.

3. **Wrong relationship model.** The personal assistant paradigm positions the agent as an over-the-shoulder helper. What we're building is an autonomous agency that brings relevant information to the human when necessary, or responds when the human initiates. The distinction matters architecturally.

Our model draws from military command structure and intelligence operations, not personal assistance. Napoleon's corps system. The CIA's collection-analysis-decision pipeline. A hedge fund's research desk reporting to portfolio managers.

---

## 3. The Command Structure Paradigm

### 3.1 Core Principle

The human operator issues **standing orders** — persistent task definitions with execution schedules, authority boundaries, and escalation conditions. The system executes within those boundaries autonomously. Information flows upward through a supervisory hierarchy and reaches the human only when it crosses a threshold requiring human judgment.

### 3.2 The Napoleon Analogy

Napoleon's corps system worked because each marshal received:
- A **mission objective** (take that hill, hold that bridge)
- **Rules of engagement** (acceptable force levels, retreat conditions)
- **Authority boundaries** (what decisions the marshal could make autonomously)
- **Escalation triggers** (when to send a courier to Napoleon)

The marshal didn't send a courier every time a cavalry squadron appeared. He dealt with it within his authority. He only escalated when the situation exceeded his pre-authorized decision space.

In Agent-Zero:
- **Mission objective** → Standing order / task definition
- **Rules of engagement** → BST domain classification + enrichment rules
- **Authority boundaries** → Meta-reasoning gate + model profile constraints
- **Escalation triggers** → Confidence thresholds, irreversibility checks, domain boundaries

### 3.3 The Intelligence Agency Analogy

An intelligence agency separates three functions:

| Function | Description | Agent-Zero Equivalent |
|----------|-------------|----------------------|
| **Collection** | Persistent gathering of raw information from sources | Subordinate agents running scheduled tasks (market data, repo monitoring, feed parsing) |
| **Analysis** | Synthesis of raw collection into assessable intelligence | Supervisor model correlating outputs, detecting patterns, flagging anomalies |
| **Decision** | Human judgment on strategic questions | Operator receives structured briefing, approves/rejects staged actions |

The operator doesn't sit in the collection room watching raw intercepts. They get a morning brief.

---

## 4. Architectural Components

### 4.1 The Task Registry

The central data structure. A persistent list of **standing orders**, each defining:

```
StandingOrder:
  id: string                    # Unique identifier
  name: string                  # Human-readable name
  objective: string             # What this task accomplishes
  
  # Scheduling
  schedule_type: enum           # "interval" | "cron" | "trigger" | "continuous"
  schedule_config: object       # Interval: "every 30m", Cron: "0 9 * * *", Trigger: event definition
  
  # Authority
  authority_level: enum         # "autonomous" | "supervised" | "approval_required"
  allowed_actions: list[string] # Tools this task is authorized to use
  forbidden_actions: list[string] # Explicit prohibitions
  irreversibility_gate: boolean # If true, any action with external side effects requires escalation
  
  # Escalation
  escalation_conditions: list   # Conditions that require human notification
  confidence_threshold: float   # Below this, escalate rather than act
  max_autonomy_duration: string # Maximum time before mandatory human check-in
  
  # BST Integration
  bst_domains: list[string]     # Which BST domains this task operates within
  
  # State
  status: enum                  # "active" | "paused" | "completed" | "escalated" | "failed"
  last_run: timestamp
  next_run: timestamp
  accumulated_output: reference # Pointer to collected results
```

### 4.2 The Daemon Layer

A lightweight persistent process that manages the task registry. This is **not an LLM** — it's a Python process with a timer loop.

```
Daemon responsibilities:
  1. Load task registry on startup
  2. Check schedule: which tasks are due?
  3. For each due task:
     a. Check preconditions (dependencies met? resources available?)
     b. Spawn subordinate agent with task context
     c. Collect output
     d. Run escalation check (rule-based, no LLM needed)
     e. Update task state
  4. Manage liveness:
     a. Health check: is the model loaded? Is memory accessible?
     b. Watchdog: have any tasks stalled beyond timeout?
     c. Resource monitoring: token budget, disk space, queue depth
  5. Sleep until next scheduled event
```

**Critical design decision:** The daemon itself uses zero LLM tokens. It's a scheduler and state machine. LLM inference only happens when a task actually executes. This means the "always on" cost is effectively zero between task executions — just a Python process sleeping on a timer.

### 4.3 The Liveness Monitor

Borrowed from SCADA. The heartbeat here serves its original industrial purpose — proving the system is alive and capable, not triggering tasks.

```
Liveness signals:
  - Process alive: daemon PID exists, responds to health check
  - Model available: inference endpoint responds within timeout
  - Memory accessible: vector store responds to test query
  - Disk healthy: output directory writable, sufficient space
  - Network status: required endpoints reachable (if applicable)

Liveness failure response:
  - Log failure with timestamp and component
  - Attempt recovery (restart model server, reconnect to store)
  - If recovery fails: pause all active tasks, notify operator
  - Never silently continue with degraded capability
```

This is distinct from the task scheduler. The liveness monitor runs on its own interval (e.g., every 60 seconds) and is purely diagnostic. If it detects failure, it doesn't try to reason about what to do — it follows a deterministic recovery procedure.

### 4.4 The Escalation Protocol

The protocol that governs information flow from agents to the human operator. This is the system that would have prevented the slanderous piece — any action with irreversible external consequences must pass through escalation before execution.

#### Escalation Levels

| Level | Name | Trigger | Agent Action | Human Required? |
|-------|------|---------|-------------|-----------------|
| 0 | **Nominal** | Task completed within parameters | Log result, update state | No |
| 1 | **Informational** | Notable finding, no action needed | Queue for next briefing | No |
| 2 | **Advisory** | Finding that may require future action | Stage recommendations, queue for briefing | No |
| 3 | **Decision Required** | Situation exceeds agent authority | Prepare options with analysis, hold for approval | **Yes** |
| 4 | **Urgent** | Time-sensitive situation exceeding authority | Prepare options, notify operator immediately | **Yes** |
| 5 | **Emergency** | System integrity at risk | Execute pre-authorized emergency procedure, notify operator | Notification only |

#### The Irreversibility Gate

The single most important safety mechanism. Before any action executes, the system asks:

```
Is this action reversible?
  - Reading data: YES → proceed
  - Writing to local file: YES → proceed  
  - Saving to memory: YES → proceed (can be deleted)
  - Sending a message: NO → escalate
  - Publishing content: NO → escalate
  - Executing a financial transaction: NO → escalate
  - Modifying external system state: NO → escalate
  - Deleting data without backup: NO → escalate
```

This is implemented as a **classification on the action**, not on the model's confidence. The model doesn't decide whether its own action is reversible — the system does, based on which tool is being called and what parameters are being passed. Mechanical enforcement, not behavioral compliance.

#### Staged Execution Pattern

When a task hits an escalation boundary:

```
1. Agent identifies action that exceeds authority
2. Agent generates candidate solutions (plural)
3. Agent does NOT execute any candidate
4. Agent packages:
   - Situation summary (what happened)
   - Why escalation triggered (which boundary)
   - Candidate actions (what could be done)
   - Agent's recommendation (which candidate and why)
   - Risk assessment for each candidate
5. Package queued for operator review
6. Task enters "escalated" state — paused until resolution
7. Operator receives briefing, selects action (or provides new instruction)
8. Selected action executes, task resumes
```

The conversational equivalent: *"Hey boss, we encountered this. We weren't sure how you wanted to proceed, so we started working on solutions but didn't implement or execute on them until we got your answer."*

### 4.5 The Supervisor Layer

The supervisor model (currently GPT-OSS-20B) serves a specific role in this architecture. It is not the daemon (that's deterministic Python). It is not the collection layer (that's subordinate agents). The supervisor is the **analysis layer** — it synthesizes outputs from multiple subordinate tasks, detects patterns across domains, and packages intelligence for the operator.

```
Supervisor responsibilities:
  1. Review subordinate outputs for cross-domain patterns
  2. Resolve escalations within supervisor authority
  3. Generate briefings for the operator
  4. Allocate resources across competing tasks
  5. Detect when standing orders need updating based on changed conditions
```

The supervisor activates on a schedule (e.g., after a batch of subordinate tasks complete) or on escalation. It does NOT run continuously. Its inference cost is bounded by the number of synthesis events, not wall clock time.

### 4.6 The Briefing System

How the operator receives intelligence. This replaces the "proactive suggestion" model with structured reporting.

**Briefing types:**

| Type | Trigger | Content |
|------|---------|---------|
| **Scheduled Brief** | Daily/weekly cron | Summary of all task activity, notable findings, pending decisions |
| **Escalation Brief** | Task hits Level 3+ | Specific situation requiring operator decision |
| **Alert** | Level 4 urgent | Time-sensitive notification requiring immediate attention |
| **Status Check** | Operator requests | Current state of all active tasks |

**Brief format:**

```
DAILY OPERATIONAL BRIEF — 2026-02-24

STANDING ORDERS: 5 active, 0 paused, 0 failed

[NOMINAL] Market Monitor
  Last run: 06:00 UTC
  Summary: No threshold crossings. S&P flat, VIX within range.
  Next run: 12:00 UTC

[ADVISORY] Repository Watch — Agent-Zero upstream
  Last run: 04:00 UTC  
  Finding: New commit to memory subsystem (commit abc123).
  Relevance: May affect ontology layer compatibility.
  Staged action: Diff analysis prepared, ready for review.
  
[DECISION REQUIRED] Research Task — Grid capacity analysis
  Started: 2026-02-23 20:00 UTC
  Status: Analysis complete, publication draft ready.
  Escalation reason: Draft contains claims about specific utility companies.
  Publishing this content is irreversible and may have reputational consequences.
  Options:
    A) Publish as-is (risk: medium)
    B) Redact company names, publish with anonymized data (risk: low)  
    C) Hold for manual review before any publication
  Recommendation: Option B
  
PENDING DECISIONS: 1
NEXT SCHEDULED BRIEF: 2026-02-25 08:00 UTC
```

---

## 5. Integration with Existing Hardening Layer

Every component we've already built has a role in this architecture:

| Existing System | Role in Agency Architecture |
|----------------|---------------------------|
| **BST Classifier** | Rules of engagement — determines which domains a task can operate in |
| **BST Enrichment** | Standing order context — injects domain-specific instructions per task |
| **Meta-Reasoning Gate** | Authority boundary enforcement — validates tool calls against task permissions |
| **Model Profile** | Capability assessment — determines what the field commander (model) can handle |
| **Profile Loader** | Configuration — sets gate strictness, retry limits, pace thresholds per model |
| **Memory System** | Institutional knowledge — persists across task executions and operator sessions |
| **Ontology Layer** | Classification infrastructure — categorizes findings for cross-domain pattern detection |
| **Error Comprehension** | Recovery doctrine — standardized procedures for known failure modes |
| **Fallback System** | Resilience — graceful degradation when tools or services fail |
| **Eval Framework** | Readiness assessment — validates model capability before deployment to task |

The hardening layer *is* the organizational doctrine. The autonomous agency architecture is the operational structure that employs it.

---

## 6. Implementation Phases

### Phase 1: Foundation (Task Registry + Daemon)

**Deliverables:**
- Task registry data model (JSON/YAML schema)
- Daemon process with timer-based scheduling
- Basic task lifecycle: create → schedule → execute → complete
- Liveness monitor with health checks
- Integration with existing Agent-Zero message handler

**Scope boundary:** Single-model execution only. No supervisor synthesis. No escalation protocol (all tasks run at authority level "autonomous"). No briefing system — operator checks status manually.

**Why this first:** Proves the persistence mechanism works without adding complexity. A standing order that runs `search_engine` every hour and writes results to a file is sufficient to validate the daemon architecture.

### Phase 2: Authority + Escalation

**Deliverables:**
- Irreversibility gate (tool-level classification)
- Escalation protocol (Levels 0-5)
- Staged execution pattern (candidates without execution)
- Authority boundary enforcement via meta-reasoning gate integration
- Escalation queue (persisted, survives daemon restart)

**Scope boundary:** Still single-model. Escalations are queued but operator must manually check. No automated notification.

**Why this second:** This is the safety layer. The system that prevents publishing slanderous content, executing unauthorized transactions, or taking irreversible actions without human approval. Nothing else should ship until this works.

### Phase 3: Supervisor + Briefing

**Deliverables:**
- Supervisor activation on batch completion and escalation events
- Cross-domain pattern detection
- Structured briefing generation (daily/escalation/alert)
- Operator notification channel (initially: file-based or Agent-Zero chat)

**Scope boundary:** Multi-model if available (supervisor on capable model, subordinates on efficient model). Briefings generated but operator pulls them rather than push notification.

**Why this third:** The supervisor layer requires both working persistence (Phase 1) and working authority boundaries (Phase 2) to function correctly. Without Phase 2, the supervisor has no escalation events to process.

### Phase 4: Operational Maturity

**Deliverables:**
- Push notification to operator (Telegram, email, or Agent-Zero native)
- Adaptive scheduling (task adjusts its own interval based on findings)
- Standing order templates for common use cases
- Resource budgeting (token cost tracking per task, global budget limits)
- Multi-subordinate coordination (tasks that depend on other tasks' outputs)
- Operator command interface ("pause all market tasks", "run brief now", "create standing order")

**Why last:** These are quality-of-life and operational efficiency improvements that only matter once the core loop is solid.

---

## 7. Token Economics

The persistent operation model must be token-efficient to work on local models.

**Cost centers:**
- Daemon process: **0 tokens** (pure Python scheduling)
- Liveness monitor: **0 tokens** (HTTP health checks, file system checks)
- Task execution: **variable** (depends on task complexity, measured per-run)
- Supervisor synthesis: **variable** (scales with number of subordinate outputs)
- Briefing generation: **fixed** (structured template, bounded output)
- Escalation reasoning: **variable but rare** (only fires on boundary crossings)

**Budget model:**

```
Daily token budget = B

Standing order costs:
  - Simple check (search + summarize): ~2,000 tokens per run
  - Complex analysis: ~8,000 tokens per run
  - Supervisor synthesis (per batch): ~4,000 tokens
  - Briefing generation: ~2,000 tokens

Example: 5 standing orders, each running 4x/day, with daily briefing
  = (5 × 4 × 2,000) + (1 × 4,000) + (1 × 2,000)
  = 40,000 + 4,000 + 2,000
  = 46,000 tokens/day

At GPT-OSS-20B speeds (~30 tok/s local): ~25 minutes of inference per day
At $0 API cost (local model): free
```

Compare to proactive assistant model:
```
Polling every 15 seconds, 16 hours/day = 3,840 inference cycles
Even at 500 tokens per cycle = 1,920,000 tokens/day
= ~18 hours of continuous inference
```

The command structure paradigm is approximately **40x more token-efficient** than the proactive assistant paradigm for equivalent operational coverage.

---

## 8. Design Principles

1. **The daemon is dumb.** It's a scheduler and state machine. It never reasons. All intelligence lives in the agents it spawns.

2. **Mechanical enforcement over behavioral compliance.** The irreversibility gate checks the tool being called, not the model's self-assessment. The authority boundary is enforced by the meta-reasoning gate, not by asking the model to be careful.

3. **Information flows upward, authority flows downward.** Subordinates report findings. The supervisor synthesizes. The operator decides. No component reaches above its level.

4. **Silence is the default.** The system only surfaces information that crosses a defined threshold. The operator is not bombarded with nominal status reports unless they request them.

5. **Staged execution for irreversible actions.** If it can't be undone, it doesn't execute without human approval. No exceptions.

6. **Token cost is a first-class constraint.** Every design decision must account for the cost of inference on a local 20B model. If a feature requires continuous inference, it must justify its token budget against alternatives.

7. **Graceful degradation.** If the model server goes down, tasks pause. If memory is unreachable, tasks that need memory pause while others continue. If the daemon crashes, it recovers state from the persisted task registry on restart.

8. **Standing orders are the unit of work.** Everything the system does traces back to an explicit standing order from the operator. The system never invents its own objectives.

---

## 9. Research References

| Source | Type | Relevance |
|--------|------|-----------|
| ProactiveAgent (ICLR 2025) | Academic paper + code | Formalizes reactive-to-proactive shift; ProactiveBench dataset; ActivityWatcher integration |
| OpenClaw / Moltbot | Production system | Gateway + heartbeat + session architecture; proven at 200K+ GitHub stars |
| Orion Agent | Production system | AEGIS governance; Docker-isolated authority boundaries; daemon with heartbeat + cost tracking |
| Rho | Production system | Minimal persistent agent; BYO model; heartbeat with configurable interval |
| BMAM (arXiv 2026) | Academic paper | "Soul erosion" taxonomy; brain-inspired memory decomposition; temporal/semantic/identity erosion |
| AgeMem (NeurIPS-track 2026) | Academic paper | Memory operations as tool actions; RL-trained memory management policy |
| leomariga/ProactiveAgent | Library | Pluggable DecisionEngine; configurable sleep calculator; most portable pattern |
| Context Studios self-learning | Blog + code | HEARTBEAT.md as mutable self-instruction; self-healing cron monitor |
| Agent Skills for Context Engineering | Skill collection | Context optimization, observation masking, tool design principles |
| memU | Framework | Dual-mode retrieval (cheap monitoring vs. expensive reasoning); hierarchical file-system memory |
| Agent-Memory-Paper-List | Curated list | Comprehensive index of 100+ papers on agent memory systems (2024-2026) |

---

## 10. Open Questions

1. **Persistence format for task registry.** JSON file? SQLite? The registry must survive daemon restarts and be human-inspectable.

2. **Operator interface.** How does the operator interact with the agency? Through Agent-Zero's existing chat? A separate CLI? File-based commands? This affects Phase 4 significantly.

3. **Multi-model allocation.** When multiple models are available (e.g., GPT-OSS-20B as supervisor, Qwen 4B for simple tasks), how does the daemon decide which model handles which task? Model profiles already exist — this becomes a scheduling optimization problem.

4. **Memory isolation.** Do standing orders share memory space or maintain isolated contexts? Shared memory enables cross-domain pattern detection but risks context pollution. Isolated memory is safer but loses correlative intelligence.

5. **Recovery after extended downtime.** If the daemon is offline for 24 hours, do all missed schedule events fire immediately on restart? Or does the system detect the gap and adjust? Stale market data from yesterday isn't useful today.

6. **Standing order evolution.** Can a task modify its own standing order (e.g., increasing its polling frequency after detecting an anomaly)? This adds capability but introduces the risk of runaway resource consumption.

7. **Subordinate-to-subordinate communication.** The current model requires all communication to flow through the supervisor. Direct subordinate coordination would be more efficient for tightly coupled tasks but adds complexity and reduces supervisory oversight.

---

*This document is a living artifact. It will evolve as implementation reveals constraints and opportunities that pure design cannot anticipate. The next step is Phase 1 implementation: task registry schema and daemon process.*
