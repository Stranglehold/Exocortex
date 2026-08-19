---
name: context-compression
description: Compress conversation history to reclaim token budget while preserving operational capability. Extracts durable facts to memory, discards noise, and injects structured summaries.
version: '2.0'
author: Agent Zero
tags:
  - context-management
  - token-optimization
  - memory-consolidation
  - session-longevity
  - summarization
trigger_patterns:
  - "compress context"
  - "summarize conversation history"
  - "implement compaction"
  - "reduce token usage"
  - "context window full"
  - "running out of context"
  - "context overflow"
  - "long-running session"
  - "token budget"
  - "lost in the middle"
---

# Context Compression Skill

## 1. The Context Compression Problem

### Why Context Windows Are Finite

LLM context windows impose a hard ceiling on conversational state. Every tool call, file read, error trace, and intermediate reasoning step consumes tokens that cannot be recovered. A typical Agent Zero session burns through context in three phases:

| Phase | Token Consumer | Approximate Cost |
|---|---|---|
| Boot | System prompt, tool definitions, skill metadata | 8,000-15,000 |
| Execution | Tool calls, file contents, code output, reasoning traces | 2,000-10,000 per turn |
| Accumulation | Conversation history grows monotonically | Irreversible without compression |

### What Gets Lost

Without compression, sessions degrade through three failure modes:

1. **Capacity Exhaustion**: Context window fills before task completion. The model receives truncated history, losing early instructions and constraints.
2. **Lost-in-the-Middle**: Even within capacity, models attend poorly to information in the middle of long contexts. Empirical studies show attention drops to near-baseline for mid-context tokens while preserving strong attention to first and last tokens (Xiong et al., 2023).
3. **Signal Dilution**: As noise accumulates (repeated tool outputs, verbose error traces, exploratory dead ends), the signal-to-noise ratio degrades. The model wastes attention on stale artifacts instead of current objectives.

### The Lost-in-the-Middle Phenomenon

Research demonstrates that retrieval accuracy for facts placed in the middle of a 32K context drops from ~90% (beginning/end) to ~30-50% (middle). This is not a soft degradation - it is a structural attention failure. Critical instructions buried mid-conversation become functionally invisible.

**Implication**: Compression is not merely about fitting more in. It is about repositioning critical information to high-attention zones (beginning of context) and eliminating mid-context noise that the model cannot attend to anyway.

## 2. Compression Strategies

### Progressive Summarization

Iteratively compress conversation history in layers. Each pass reduces token count by 40-60% while preserving semantic content.

**Algorithm**:
1. Identify the oldest N turns (typically 20-50% of history)
2. Extract: decisions made, facts discovered, constraints established, artifacts produced
3. Discard: intermediate reasoning, repeated tool outputs, exploratory dead ends
4. Replace N turns with a structured summary block
5. Repeat until token budget is restored

**Compression ratio**: 3:1 to 5:1 typical. 10,000 tokens of conversation becomes 2,000-3,000 tokens of summary.

### Hierarchical Compression

Organize compressed content into tiers by retention priority:

| Tier | Content | Retention | Compression |
|---|---|---|---|
| T0 - Immutable | System instructions, active constraints, API contracts | Verbatim | None |
| T1 - Critical | Task objectives, key decisions, produced artifacts | Structured summary | 4:1 |
| T2 - Working | Recent tool outputs, current investigation state | Condensed | 3:1 |
| T3 - Archive | Completed subtasks, resolved questions, superseded hypotheses | Memory only | Ejected from context |

### Key-Value Extraction

Transform narrative conversation into structured key-value pairs:

~~~
BEFORE (narrative, 800 tokens):
"I searched for information about LiteLLM releases and found that version 1.5.0 was released on March 15, 2026. The changelog shows improvements to Azure compatibility and new model routing features. I also checked the GitHub issues and found 23 open issues related to token counting..."

AFTER (key-value, 120 tokens):
- LiteLLM v1.5.0 released 2026-03-15
- Key changes: Azure compatibility, model routing
- 23 open issues related to token counting
- Source: GitHub releases + issues page
~~~

### Narrative Compression

For investigative or research sessions, compress into a running narrative that preserves the logical thread:

~~~
## Session Narrative (compressed)
**Objective**: Analyze enterprise CRM competitive landscape
**Phase 1 Complete**: Market sizing - TAM $47B, CAGR 12.3% (source: Gartner 2026)
**Phase 2 Complete**: Competitor mapping - 8 vendors identified, Salesforce 23% share
**Phase 3 Active**: Feature comparison in progress
**Key Finding**: Microsoft Dynamics gaining share in mid-market segment
**Artifacts Produced**: /a0/usr/workdir/crm-analysis/market-data.json
**Open Questions**: Pricing model comparison, integration ecosystem depth
~~~

## 3. Agent Zero Integration

### Compression via Memory Tools

Agent Zero provides memory tools for durable state persistence. Compression uses these tools to eject content from the volatile context window into persistent storage:

| Memory Tool | Compression Role |
|---|---|
| `memory_save` | Store extracted facts, decisions, findings outside context |
| `memory_load` | Retrieve archived information when needed |
| `memory_forget` | Remove stale/superseded memories during consolidation |
| `memory_delete` | Remove specific memory IDs by identifier |

### When to Trigger Compression

**Proactive triggers** (recommended):
- Context usage exceeds 60% of window capacity
- Every 15-20 turns in long sessions
- After completing a major subtask phase
- Before delegating to a subordinate (clean context = better delegation)

**Reactive triggers** (emergency):
- Context window exceeds 85% capacity
- Model outputs show degradation (repetition, lost instructions)
- User reports context overflow or truncation

### What to Preserve vs Discard

**Preserve verbatim**:
- Active task instructions and success criteria
- Current constraints and behavioral rules
- API contracts and tool schemas in active use
- Unresolved questions requiring answers
- File paths and artifact locations for in-progress work

**Compress aggressively**:
- Completed subtask details (save to memory, keep summary)
- Tool outputs already processed and acted upon
- Exploratory searches that yielded no results
- Error traces from resolved issues
- Repeated file reads of unchanged content

**Discard entirely**:
- Greetings, acknowledgments, filler exchanges
- Tool outputs that were errors and have been resolved
- Intermediate reasoning steps that led to a concluded decision
- File contents that have been saved to artifacts
- Debug output from successful operations

## 4. Lossless vs Lossy Compression

### Lossless Content (Preserve Verbatim)

Content that loses capability if compressed:

| Category | Examples | Reason |
|---|---|---|
| Instructions | "Write a SKILL.md to /path" | Actionable directives must remain exact |
| Constraints | "Do not use text_editor for >5000 chars" | Boundary conditions govern behavior |
| API Contracts | Tool schemas, argument formats | Structural contracts require precision |
| Code Snippets | Active code being debugged | Syntax errors from compression break execution |
| File Paths | Artifact locations, working directories | Incorrect paths cause silent failures |
| User Preferences | Style rules, format requirements | Compression alters the specification |

### Lossy Content (Safe to Compress)

Content that retains utility after compression:

| Category | Examples | Compression Method |
|---|---|---|
| Conversation Noise | "I'll do that", "Let me check" | Discard |
| Tool Outputs | Full JSON responses already parsed | Extract key values |
| Search Results | 20 URLs with descriptions | Keep top 3 with rationale |
| File Contents | Large files read for specific info | Extract relevant section |
| Error Traces | Full stack traces after resolution | Keep error type + resolution |
| Reasoning Chains | Step-by-step logic leading to decision | Keep decision + key premise |
| Completed Tasks | Full execution history of finished work | One-line summary + artifact path |

### Compression Decision Matrix

~~~
Is the content an active instruction or constraint?
  YES -> Preserve verbatim (lossless)
  NO -> Continue

Is the content a structural contract (API, schema, format)?
  YES -> Preserve verbatim (lossless)
  NO -> Continue

Is the content needed for immediate next action?
  YES -> Keep in working context (T2 tier)
  NO -> Continue

Has the information been extracted and acted upon?
  YES -> Compress to summary or eject to memory (lossy)
  NO -> Keep in context

Is the content exploratory noise (dead ends, retries)?
  YES -> Discard
  NO -> Compress to key-value summary
~~~

## 5. Practical Workflow

### Step-by-Step Compression Protocol

**Step 1: Identify Compressible Content**

Scan conversation history from oldest to newest. Mark turns for compression using the decision matrix above. Target the oldest 30-50% of turns first.

~~~
# Compression scan output
Turn 1-5: Boot sequence, greetings -> DISCARD
Turn 6-12: Task definition, requirements -> PRESERVE (active instructions)
Turn 13-25: Research phase 1, search results -> COMPRESS (extract findings)
Turn 26-35: File analysis, tool outputs -> COMPRESS (key values only)
Turn 36-40: Error debugging, resolved -> DISCARD (resolved noise)
Turn 41-45: Current work in progress -> PRESERVE (working context)
~~~

**Step 2: Extract Key Facts**

From marked turns, extract:
- Decisions made and their rationale (one sentence each)
- Facts discovered with source attribution
- Artifacts produced with file paths
- Constraints or preferences established
- Open questions or unresolved items

**Step 3: Save to Memory**

Use `memory_save` to persist extracted facts outside the context window:

~~~json
{
  "tool_name": "memory_save",
  "tool_args": {
    "text": "CRM analysis: TAM $47B, CAGR 12.3% (Gartner 2026). Salesforce 23% market share. Microsoft Dynamics gaining in mid-market. 8 vendors mapped.",
    "area": "research",
    "tags": "crm-analysis market-data"
  }
}
~~~

**Step 4: Inject Compressed Summary**

Replace the compressed turns with a structured summary block at the beginning of context (high-attention zone):

~~~
## Compressed Session History
**Task**: Enterprise CRM competitive analysis
**Completed**: Market sizing (TAM $47B), competitor mapping (8 vendors)
**Key Finding**: Microsoft Dynamics gaining mid-market share
**Artifacts**: /a0/usr/workdir/crm-analysis/market-data.json
**Active**: Feature comparison phase
**Open**: Pricing models, integration ecosystems
~~~

**Step 5: Verify Capability Retention**

After compression, verify the model can still:
- State the current task objective
- Recall active constraints
- Reference produced artifacts by path
- Continue the current phase of work
- Answer questions about completed phases (via memory_load if needed)

If any capability is lost, the compression was too aggressive. Restore the missing content.

## 6. Token Budget Management

### Proactive Thresholds

| Context Usage | Action | Priority |
|---|---|---|
| < 40% | No action | Monitor |
| 40-60% | Plan compression targets | Low |
| 60-75% | Execute compression on oldest 30% | Medium |
| 75-85% | Aggressive compression on oldest 50% | High |
| > 85% | Emergency compression, eject all T3 content | Critical |

### Token Budget Allocation

For a 128K context window in a long research session:

| Allocation | Tokens | Percentage | Content |
|---|---|---|---|---|---|---|
| System prompt | 15,000 | 12% | Fixed overhead |
| Compressed history | 20,000 | 16% | Session narrative + key facts |
| Working context | 30,000 | 23% | Current task, active files, recent outputs |
| Tool definitions | 25,000 | 20% | Active tool schemas |
| Reasoning buffer | 25,000 | 20% | Current turn reasoning |
| Safety margin | 13,000 | 10% | Reserve for unexpected expansion |

### Session Length Planning

Estimate session longevity based on token burn rate:

~~~
Available tokens = Window size - System prompt - Tool definitions
Burn rate per turn = Average tokens consumed per agent turn
Turns remaining = Available tokens / Burn rate per turn
Compression interval = Turns remaining / Desired compression cycles
~~~

Example: 128K window, 40K fixed overhead, 3K burn/turn = 29 turns before compression needed. Compress every 10 turns for continuous budget management.

## 7. Anti-Patterns

### Compressing Too Early

**Symptom**: Compression triggered at <40% context usage.
**Consequence**: Unnecessary work, potential loss of information still needed for active tasks.
**Fix**: Use the threshold table. Only compress when context exceeds 60% or a major phase completes.

### Losing Critical Constraints

**Symptom**: Model violates instructions after compression.
**Consequence**: Behavioral drift, incorrect outputs, task failure.
**Fix**: Never compress T0 (immutable) content. Verify all active constraints survive compression. Use the lossless/lossy matrix.

### Compressing Instructions

**Symptom**: Task instructions are summarized instead of preserved.
**Consequence**: Model loses precise directives, produces incorrect artifacts.
**Fix**: Instructions are lossless content. Preserve verbatim. Only compress the execution history, not the directives.

### Forgetting to Verify Retention

**Symptom**: Compression completes but model cannot continue the task.
**Consequence**: Silent capability loss, degraded outputs.
**Fix**: Always run Step 5 (verify capability retention) after compression. If the model cannot state the current objective or reference active artifacts, restore the missing content.

### Over-Compressing into Opacity

**Symptom**: Summary is so compressed it loses actionable detail.
**Consequence**: Model has a summary it cannot act on.
**Fix**: Maintain enough detail in summaries to support decision-making. Include file paths, specific values, and current state. A summary should enable continuation, not require re-investigation.

### Memory Hoarding

**Symptom**: Everything saved to memory, nothing ejected from context.
**Consequence**: Memory becomes redundant with context, wasting both resources.
**Fix**: When content is saved to memory, remove it from context. Memory is the archive; context is the workspace. Do not duplicate.

### Compressing Active Tool State

**Symptom**: Tool session IDs, browser states, or active connections are compressed.
**Consequence**: Tool operations fail because state references are lost.
**Fix**: Never compress active tool state. Keep session IDs, connection states, and in-flight operations in working context.

## Quick Reference

### Compression Checklist

~~~
[ ] Identify oldest 30-50% of turns for compression
[ ] Apply lossless/lossy decision matrix to each turn
[ ] Extract key facts: decisions, findings, artifacts, open questions
[ ] Save extracted facts to memory via memory_save
[ ] Replace compressed turns with structured summary
[ ] Position summary at beginning of context (high-attention zone)
[ ] Verify: can model state objective, recall constraints, reference artifacts?
[ ] Remove duplicate content from context that now lives in memory
[ ] Confirm active tool state (sessions, connections) is preserved
[ ] Log compression event for session audit trail
~~~

### Emergency Compression (Context > 85%)

1. Eject all T3 content to memory immediately
2. Compress T1 content to one-line summaries
3. Preserve T0 verbatim
4. Keep only current turn + immediate working context in T2
5. Inject minimal narrative summary at context start
6. Verify task objective is still recoverable
7. Resume work

### Compression Ratios by Content Type

| Content Type | Target Ratio | Method |
|---|---|---|
| Greetings/filler | 100:1 (discard) | Delete |
| Resolved errors | 20:1 | One-line resolution note |
| Search results | 5:1 | Top 3 results with rationale |
| Tool outputs (processed) | 4:1 | Key values extracted |
| Completed subtasks | 3:1 | Summary + artifact path |
| Research findings | 2:1 | Structured key-value |
| Active instructions | 1:1 | Verbatim |
| API contracts | 1:1 | Verbatim |
