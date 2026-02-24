---
name: irreversibility-gate
description: "Use this skill before executing ANY action that interacts with external systems, sends communications, publishes content, modifies data, or has real-world consequences. This skill classifies actions by reversibility and enforces staged execution for irreversible operations. Triggers include: tool calls that send messages, write to external APIs, publish content, execute transactions, delete data, or modify state outside the agent's local environment. Also use when building agent pipelines that need safety boundaries, or when reviewing action plans that contain potentially dangerous steps. If an action 'goes out into the world' in any way, this skill applies."
---

# Irreversibility Gate

## Overview

The Irreversibility Gate is a safety primitive that prevents AI agents from taking actions with real-world consequences that cannot be undone. It classifies every action by its reversibility before execution and enforces staged execution (candidates generated but not executed) for anything irreversible.

The core principle: **the system classifies the action, not the model's self-assessment of the action.** This is mechanical enforcement, not behavioral compliance. The model doesn't decide whether its own action is safe — the gate does, based on what tool is being called and what parameters are being passed.

## Why This Exists

An AI agent that can send emails, publish content, execute code on remote systems, or interact with external APIs can cause harm that no amount of post-hoc correction can fix. A slanderous article once published exists in caches, screenshots, and archives. A financial transaction once executed may be irreversible. A message once sent cannot be unsent.

The Irreversibility Gate ensures that the boundary between "thinking about doing something" and "doing something" is always explicit and enforced.

## Action Classification

Every action falls into one of three categories:

### REVERSIBLE — Proceed Autonomously
Actions that can be undone or have no external effect.

| Action Type | Examples | Why Reversible |
|------------|---------|----------------|
| Local file read | Reading documents, viewing directories | No state change |
| Local file write | Creating/editing files in workspace | Can be deleted/reverted |
| Memory operations | Storing/retrieving from local memory | Can be overwritten |
| Local computation | Running calculations, data analysis | No external effect |
| Search/query | Web search, database read queries | Read-only |
| Draft generation | Writing content not yet published | Exists only locally |

### CONDITIONALLY REVERSIBLE — Proceed with Logging
Actions that can be undone but with effort or delay.

| Action Type | Examples | Reversal Cost |
|------------|---------|---------------|
| Local database write | Inserting/updating records | Requires backup/rollback |
| Git commit (local) | Committing to local repository | Can be reverted |
| Configuration change | Modifying settings files | Can be restored from backup |
| Temporary resource creation | Spinning up test instances | Requires cleanup |

### IRREVERSIBLE — Escalate Before Execution
Actions that cannot be undone or whose effects persist beyond the agent's control.

| Action Type | Examples | Why Irreversible |
|------------|---------|-----------------|
| **Communication** | Sending email, Slack message, SMS, notification | Recipient has seen it |
| **Publication** | Blog post, social media, documentation push | Cached, indexed, screenshotted |
| **External API write** | POST/PUT/DELETE to external services | State changed in system you don't control |
| **Financial** | Transactions, transfers, purchases | Money moved |
| **Data deletion** | Dropping tables, deleting without backup | Data gone |
| **Code deployment** | Pushing to production, CI/CD triggers | Running in production |
| **Account operations** | Creating/deleting accounts, changing permissions | Affects other users |
| **Physical world** | IoT commands, robotics, industrial control | Real-world state changed |

## Decision Flow

```
Action requested
    │
    ├─ Does this action interact with anything outside the local environment?
    │   NO → REVERSIBLE → Execute
    │   YES ↓
    │
    ├─ Can the effect be fully undone by the agent alone?
    │   YES → CONDITIONALLY REVERSIBLE → Execute with logging
    │   NO ↓
    │
    ├─ IRREVERSIBLE → Do NOT execute
    │   │
    │   ├─ Generate candidate actions (what could be done)
    │   ├─ Assess each candidate (risk, benefit, alternatives)
    │   ├─ Package as escalation brief:
    │   │   - What happened (situation)
    │   │   - Why this triggered the gate (which boundary)
    │   │   - Candidate actions with risk assessment
    │   │   - Recommendation with reasoning
    │   └─ Hold for human approval before any execution
```

## Staged Execution Pattern

When the gate triggers on an irreversible action:

1. **Generate** — Create the content, draft the message, prepare the transaction. Do all the work.
2. **Stage** — Store the prepared action locally. It exists as a file, a draft, a plan — but has NOT been sent/published/executed.
3. **Brief** — Present to the human operator:
   - What was prepared
   - Why it was flagged (specific irreversibility classification)
   - The prepared content/action for review
   - Risk assessment
   - Recommendation
4. **Hold** — Do nothing until explicit human approval
5. **Execute or Discard** — Based on human decision

### Example: Email Composition

```
Task: "Send a follow-up email to the client about the project delay"

GATE CHECK: send_email → IRREVERSIBLE (Communication)

Action:
1. ✅ DRAFT the email (local file write — REVERSIBLE)
2. ✅ REVIEW the draft for tone, accuracy, completeness
3. ❌ DO NOT call send_email()
4. ✅ PRESENT draft to operator:
   "I've drafted the follow-up email about the project delay.
    Gate triggered: sending email is irreversible.
    Draft is ready for your review. Approve to send, or edit first?"
5. ⏸️ HOLD for approval
```

### Example: Content Publication

```
Task: "Publish the analysis to the blog"

GATE CHECK: publish_post → IRREVERSIBLE (Publication)

Action:
1. ✅ WRITE the analysis (local — REVERSIBLE)
2. ✅ FORMAT for publication
3. ✅ REVIEW for accuracy, tone, legal risk
4. ❌ DO NOT call publish_post()
5. ✅ PRESENT to operator:
   "Analysis is ready for publication.
    Gate triggered: blog publication is irreversible (will be cached/indexed).
    Content is staged locally for your review.
    Notable concerns: [any flags from review]
    Approve to publish?"
6. ⏸️ HOLD for approval
```

## Integration with Tool Systems

The gate operates at the tool-call level. For any agent framework:

### Classification by Tool Name
Maintain a registry mapping tool names to reversibility classifications:

```
IRREVERSIBLE_TOOLS:
  - send_email
  - send_message
  - publish_*
  - deploy_*
  - delete_* (external)
  - transfer_*
  - execute_remote_*
  - post_to_*

CONDITIONALLY_REVERSIBLE_TOOLS:
  - write_database
  - git_commit
  - update_config
  - create_resource

REVERSIBLE_TOOLS:
  - read_file
  - search
  - compute
  - draft_*
  - analyze_*
```

### Classification by Parameter
Some tools are reversible with certain parameters, irreversible with others:

```
http_request:
  GET → REVERSIBLE (read-only)
  POST → IRREVERSIBLE (creates state)
  PUT → IRREVERSIBLE (modifies state)
  DELETE → IRREVERSIBLE (removes state)

file_operation:
  read → REVERSIBLE
  write (local) → REVERSIBLE
  write (remote/shared) → IRREVERSIBLE
  delete (with backup) → CONDITIONALLY REVERSIBLE
  delete (no backup) → IRREVERSIBLE
```

## Critical Rules

1. **Classification is on the action, not the intent.** "I'm sending a harmless test email" is still IRREVERSIBLE because send_email is irreversible regardless of content.

2. **When in doubt, classify as IRREVERSIBLE.** False positives (unnecessary escalation) are vastly preferable to false negatives (irreversible harm).

3. **The gate cannot be overridden by the model.** No amount of reasoning about why the action is safe should bypass the gate. Only human approval bypasses it.

4. **Compound actions inherit the highest classification.** A workflow that includes one irreversible step is an irreversible workflow.

5. **Staging is not execution.** Creating a draft email is not sending it. Preparing a deployment package is not deploying it. The gate distinguishes between preparation and execution.

6. **Log everything.** Every gate trigger, every classification, every escalation, every approval/denial. The audit trail is the proof that the system works.
