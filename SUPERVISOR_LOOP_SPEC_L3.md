# Supervisor Loop — Build Specification (Level 3)
## Organization Kernel · Phase 2

**Implementation note:** This spec defines intent, integration contracts, and behavioral
requirements. The implementing agent reads the Agent-Zero source and makes all
implementation decisions.

---

## Mission

Build the XO supervisory function: an extension that monitors the agent's operational
state, detects anomalies (stalls, loops, context exhaustion, repeated failures), and
injects corrective steering into the agent's conversation history. In microcosm mode
this is self-supervision — the agent reads its own SALUTE reports and failure state.
In macrocosm mode the same logic reads subordinate SALUTE files from a shared volume.

---

## Problem Statement

Current failure handling is reactive and narrow:
- Tool fallback advisor fires only when the same tool fails consecutively
- HTN staleness counter expires the plan but doesn't tell the model WHY or WHAT to do instead
- PACE levels are tracked and logged but nothing acts on them
- There's no mechanism that looks at the big picture: "you've been working on this task
  for 20 turns, changed PACE levels twice, and your context is 80% full — time to
  change approach"

The supervisor loop closes this gap. It's the XO doing radio checks — reading operational
status and intervening when the situation warrants it.

---

## Concepts

### Radio Check
Periodic review of operational state. The supervisor reads SALUTE data and evaluates
whether the agent is making progress, stuck in a loop, or approaching resource limits.
Runs on a configurable interval (every N message loop iterations).

### Steering Injection
When the supervisor detects a problem, it injects a warning message into the agent's
conversation history using `hist_add_warning()`. The model sees this as system guidance
on its next iteration, similar to how the tool fallback advisor injects advice.

### Anomaly Detection
Pattern-based detection of operational problems. Not model reasoning — deterministic
checks against thresholds and patterns. Categories:

| Anomaly | Signal | Response |
|---------|--------|----------|
| **Stall** | turns_since_progress exceeds role's max_turns_without_progress | Inject "you appear stalled — reassess approach" |
| **Loop** | Same tool called 3+ times with same/similar args in recent history | Inject "you are repeating the same action — try a different approach" |
| **Context Exhaustion** | context_fill_pct > 0.80 | Inject "context window nearly full — wrap up current task or summarize" |
| **Cascade Failure** | 3+ different tools failing in sequence | Inject "multiple tools failing — stop and verify your environment/assumptions" |
| **PACE Escalation** | PACE level is contingent or emergency | Inject role-specific PACE guidance from the role profile |

### Cooldown
After injecting a steering message, the supervisor enters a cooldown period (configurable,
default 3 turns) before it can inject another message of the same type. This prevents
flooding the agent's context with repeated warnings.

---

## Integration Point

- **Hook:** `message_loop_end`
- **Numeric prefix:** `_50_` — after history organization (`_10_`) but before chat saving (`_90_`)
- **File:** `/a0/python/extensions/message_loop_end/_50_supervisor_loop.py`

### Why `message_loop_end`

The supervisor needs to evaluate AFTER the agent has acted (tool call completed, response
generated) but BEFORE the next iteration's prompt is built. `message_loop_end` fires in
the `finally` block of every message loop iteration, including error cases. This means
the supervisor sees every outcome — successes, failures, and exceptions.

The steering injection via `hist_add_warning()` places the message in history where the
model will see it on the next `before_main_llm_call` → `prepare_prompt` cycle.

---

## Behavioral Requirements

### Activation
- Only run when an organization is active (check for `_org_active_role` on the agent).
- If no role is active, return immediately. Zero overhead when the org kernel is off.
- Track a turn counter independently from the dispatcher's counter.

### Radio Check Interval
- Read the active role's `doctrine.salute_interval_turns` to determine check frequency.
- Alternatively, use its own configurable interval (default: every 3 turns).
- The supervisor should check MORE frequently than SALUTE emission — it's watching the
  agent in real-time, not waiting for periodic reports.

### Anomaly Detection — Stall
- Read `turns_since_progress` from HTN state (`agent._htn_state`) if available.
- Compare against the active role's `doctrine.max_turns_without_progress`.
- If exceeded: inject steering that acknowledges the stall and suggests concrete
  alternatives (different approach, ask user for clarification, simplify the task).
- The injected message should reference what the agent was trying to do if that
  information is available from BST or HTN state.

### Anomaly Detection — Loop
- Read recent tool call history from the tool failures data structure
  (`agent.get_data("_tool_failures")["history"]`).
- Detect if the last 3+ entries involve the same tool with the same error type.
- This is DIFFERENT from the tool fallback advisor's consecutive failure check.
  The fallback advisor checks consecutive failures of the SAME tool. The supervisor
  checks for behavioral loops — the agent doing the same thing repeatedly expecting
  different results.
- Also detect oscillation: tool A fails → tool B fails → tool A fails → tool B fails.
  This pattern indicates the agent is bouncing between two approaches without making
  progress.

### Anomaly Detection — Context Exhaustion
- Read context fill data. The dispatcher's SALUTE report includes `context_fill_pct`.
  The supervisor can read from the same source the dispatcher uses, or read the latest
  SALUTE file from disk.
- If context fill exceeds 80%: inject warning to wrap up, summarize, or start fresh.
- If context fill exceeds 90%: inject urgent warning that context is nearly exhausted
  and the agent should complete its immediate task and respond to the user.

### Anomaly Detection — Cascade Failure
- Read the tool failures history and check if 3+ DIFFERENT tools have failed recently
  (within the last 5 history entries).
- This indicates a systemic problem (wrong working directory, broken environment,
  incorrect assumptions) rather than a tool-specific issue.
- Inject steering that tells the agent to stop executing and verify its fundamental
  assumptions: correct directory, correct file paths, correct environment state.

### Anomaly Detection — PACE Escalation Response
- Read the current PACE level from `agent._org_pace_level` (or whatever attribute
  the dispatcher actually used — verify in source).
- When PACE is `contingent`:
  - Read the active role's `pace_plan.contingent.description` for context.
  - Inject steering that tells the agent its current approach has failed and it should
    try a fundamentally different method or ask the user for guidance.
- When PACE is `emergency`:
  - Inject steering that tells the agent to stop, preserve any partial results, and
    report what it has accomplished and where it got stuck.
  - In macrocosm mode (future), this would also notify the supervising XO container.

### Steering Message Format
- All injected messages should be concise — 2-3 sentences maximum.
- Start with a tag like `[SUPERVISOR]` so it's distinguishable in history from tool
  fallback advisor messages (which use `Tool guidance:` prefix).
- Include the specific anomaly detected and the recommended action.
- Do NOT include lengthy explanations or multiple options. The model's context is
  potentially already stressed — add minimal tokens with maximum signal.

### Cooldown Management
- After injecting a steering message, record the anomaly type and current turn number.
- Do not inject another message of the same type within the cooldown period (default 3 turns).
- Different anomaly types have independent cooldowns — a stall warning doesn't prevent
  a context exhaustion warning.
- PACE emergency is exempt from cooldown — always inject.

### Self-SALUTE Update
- After detecting and acting on an anomaly, update the current SALUTE report's
  `status.health` field if the supervisor's assessment differs from the dispatcher's.
- The supervisor has a more complete picture than the dispatcher because it runs AFTER
  tool execution, not before.

---

## Integration Contracts

### Reads From

| Source | Location | Data |
|--------|----------|------|
| Active role | `agent._org_active_role` (verify actual attr) | Role profile dict with doctrine and PACE config |
| PACE level | `agent._org_pace_level` (verify actual attr) | Current PACE level string |
| HTN state | `agent._htn_state` | Plan progress, `turns_since_progress`, `current_step` |
| Tool failures | `agent.get_data("_tool_failures")` | `consecutive` dict, `history` list |
| BST belief | `agent._bst_store["__bst_belief_state__"]` | Current domain, confidence |
| Loop data | `loop_data.iteration` | Current iteration number |
| Loop data | `loop_data.last_response` | Agent's last response text |
| SALUTE files | `/a0/usr/organizations/reports/<role_id>_latest.json` | Latest SALUTE (alternative to reading agent attrs) |

### Writes To

| Destination | Method | Data |
|-------------|--------|------|
| Agent history | `agent.hist_add_warning(message)` | Steering messages visible to model |
| Agent log | `agent.context.log.log(type, content)` | Supervisor activity logging |
| SALUTE report | Update `_latest.json` on disk (optional) | Corrected health assessment |

### Does NOT Write To
- Does not modify `_org_active_role` or `_org_pace_level` — that's the dispatcher's job.
- Does not modify `_htn_state` — that's the HTN selector's job.
- Does not modify `_tool_failures` — that's the fallback logger's job.
- The supervisor is read-only on all state except history injection and logging.

---

## Relationship to Existing Extensions

| Extension | Relationship |
|-----------|-------------|
| Tool Fallback Advisor (`tool_execute_before/_30_`) | Complementary, not overlapping. Advisor handles per-tool consecutive failures with tool-specific advice. Supervisor handles systemic patterns, behavioral loops, and PACE-level responses. |
| Org Dispatcher (`before_main_llm_call/_12_`) | Dispatcher sets PACE levels. Supervisor acts on them. Dispatcher emits SALUTE. Supervisor reads it. |
| HTN Plan Selector (`before_main_llm_call/_15_`) | HTN tracks staleness. Supervisor reads it and injects guidance when stale. HTN expires plans silently. Supervisor explains why and suggests alternatives. |
| Context Watchdog (`before_main_llm_call/_20_`) | If the watchdog already handles context limits, the supervisor should not duplicate that work. Check the watchdog's behavior and ensure no overlapping warnings. |
| History Organization (`message_loop_end/_10_`) | Runs before supervisor. History is already organized when supervisor executes. |

---

## Testing Criteria

### Test 1: No-Org Passthrough
- With no `active.json`, the supervisor must not execute any checks.
- No log entries, no steering injections, no file reads.
- Verify: agent behaves identically to pre-supervisor operation.

### Test 2: Normal Operation
- With an active org, run the agent on a task that completes successfully.
- The supervisor should execute its checks on schedule but inject nothing.
- Verify: no `[SUPERVISOR]` messages in the agent's history.

### Test 3: Stall Detection
- Start an HTN plan, then stop making progress (e.g., ask the agent to do something
  that causes it to spin without advancing steps).
- After `max_turns_without_progress` is exceeded, a steering message should appear.
- Verify: `[SUPERVISOR]` message in history referencing the stall.

### Test 4: Loop Detection
- Force the agent into a tool loop (repeatedly failing the same operation).
- After 3+ repetitions of the same pattern, a steering message should appear.
- Verify: message is distinct from the tool fallback advisor's per-tool advice.

### Test 5: Context Exhaustion Warning
- This is harder to trigger naturally. If possible, fill context through a long
  conversation and verify the warning fires at 80%.
- Alternative: verify the code path by checking the threshold logic in code review.

### Test 6: PACE Response
- Trigger enough tool failures to push PACE to contingent.
- The supervisor should inject guidance referencing the PACE level.
- Verify: message includes role-specific context from the PACE plan description.

### Test 7: Cooldown
- Trigger a stall warning, then continue for 2 more turns.
- The supervisor should NOT inject another stall warning during cooldown.
- After cooldown expires (default 3 turns), if still stalled, it should inject again.

### Test 8: Cascade Detection
- Force failures on 3+ different tools in sequence.
- The supervisor should detect this as a cascade (not just individual tool failures)
  and inject environment-verification guidance.

---

## Installation

### Script: `install_supervisor_loop.sh`

**Must do:**
1. Copy the supervisor extension to `message_loop_end/` with prefix `_50_`
2. Clear `__pycache__` in the target extension directory

### Addition to `install_all.sh`
Add as Phase 2 under the Foundation Layer.

---

## Future: Macrocosm Supervisor

In macrocosm mode, the supervisor extension runs in the XO's container, not the
specialist's container. Instead of reading `agent._htn_state` attributes directly,
it reads the specialist's SALUTE file from the shared volume.

Instead of injecting via `hist_add_warning()`, it writes a steering message to a
file that the specialist's container picks up (or sends via the A2A communication
channel).

The anomaly detection logic is identical. Only the I/O layer changes.

This is why SALUTE reports exist as files on disk rather than just in-memory state.
The file IS the communication channel. The supervisor loop built now in microcosm
is the same supervisor loop that runs in macrocosm — it just reads from a different
path.
