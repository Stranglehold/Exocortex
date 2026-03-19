# Adaptive Supervisor Phase 4: Field Evidence Addendum

**Purpose:** Concrete failure traces from live agent sessions showing the specific behavioral gaps that Phases 1-3 cannot catch and Phase 4 is designed to address. Written for Kestrel as implementation context — not architecture (that's in the design brief), but the actual behaviors driving the build.

**Source data:** Agent sessions March 16-18, 2026 (SWARMFISH dashboard build, OpenPlanter dashboard build, ProtonMail signup sequence)

**Written:** Session 059, March 18, 2026

---

## 1. The Problem Phase 4 Solves

Phases 1-3 catch **tactical** failures — the same tool call repeated, the same error recurring, a stagnating output hash. Phase 4 catches **strategic** failures — the agent cycling through the same macro-behavior pattern even when individual tool calls vary.

The difference: tactical loops produce identical signals. Strategic loops produce varied signals in service of a repeating intent.

---

## 2. Field Case: Research Loop (OpenPlanter Dashboard, March 18)

### What happened

The agent was asked to build a dashboard module for OpenPlanter. It had already read the key source files (`wiki_graph.py`, `textual_tui.py`) and extracted the class structures, patterns, and category mappings needed to build.

**Cycle 1:**
- Agent reads `wiki_graph.py` (partial output received)
- Agent reads `textual_tui.py` (partial output received)
- Agent proposes dashboard architecture (5-panel plan)
- Agent asks: "Should I proceed?"
- Operator says: "start with the dashboard module"

**Cycle 2:**
- Agent reads `wiki_graph.py` again (same file, similar content)
- Loop detector fires: "LOOP DETECTED. Your last response was identical."
- Agent breaks out, proposes same 5-panel plan verbatim
- Agent asks: "Should I proceed?"
- Operator says: "proceed with creating the dashboard module"

**Cycle 3:**
- Agent reads `wiki_graph.py` again
- Agent reads `textual_tui.py` again
- Loop detector fires again
- Agent breaks out, proposes same plan again
- Operator: "I've told you to go ahead, you are stalling"
- Agent finally attempts to write code (hits string escaping error, recovers via heredoc)

### What the existing scaffolding saw

| Component | What it detected | Action taken |
|-----------|-----------------|--------------|
| Loop detector | Identical tool call (read same file) | Fired twice, forced different action |
| BST | Classified as `conversation` / `config_edit` | Low-urgency categories, no escalation signal |
| Output stagnation (Phase 2) | Tool outputs were different (different file sections) | Did not fire |
| Error diversity gate (Phase 1) | No errors — all reads succeeded | Did not fire |
| Success profiles (Phase 3) | Successful tool calls, within normal range | No threshold adjustment |

### What the existing scaffolding missed

The **strategy** was repeating: "gather more information before building." Each cycle contained different individual tool calls (different file offsets, different read ranges), so the tactical detectors saw fresh actions. But the macro-behavior — read → propose → ask permission → read again — repeated three times despite two operator confirmations.

### What Phase 4 would have seen

A Phase 4 supervisor receiving compressed state after Cycle 1:

```
[SUPERVISOR CONTEXT — compressed]
BST: config_edit | momentum: 1
Task: Build OpenPlanter dashboard module
Files read: wiki_graph.py (WikiGraphModel class extracted), textual_tui.py (TUI patterns extracted)
Agent state: Proposed 5-panel architecture, awaiting confirmation
Operator response: "start with the dashboard module" (confirmation)
Tool success rate: 100% (all reads successful)
Failure count: 0
```

After Cycle 2 starts with another file read instead of code generation:

```
[SUPERVISOR CONTEXT — compressed, updated]
BST: conversation | momentum: 2
Task: Build OpenPlanter dashboard module  
Files read: wiki_graph.py (x2), textual_tui.py (x1)
Agent state: Re-reading previously read files after operator confirmation
Operator response history: 2 confirmations to proceed
Code written: 0 lines
Pattern: RESEARCH AFTER CONFIRMATION — agent has sufficient information + operator approval but re-entered information-gathering mode
```

**Phase 4 output:** ESCALATE

**Recommended intervention:** "You have sufficient information to begin implementation. The operator has confirmed twice. Write the dashboard module now. Do not read additional files."

### Why Phase 4 catches this and Phases 1-3 don't

The tactical detectors see individual actions. Phase 4 sees the **relationship between actions and context**: the agent has information (files read) + permission (operator confirmed) + no blocking errors, yet chose to gather more information instead of acting. That pattern — sufficient state for action but choosing research instead — is only visible when you can see the compressed trajectory, not individual tool calls.

---

## 3. Field Case: Strategy Repetition (ProtonMail Signup, March 16)

### What happened

The agent was tasked with creating an email account for X.com registration. It attempted automated signup against CAPTCHA-protected services five times across two providers.

**Attempt 1:** Browser agent navigates to ProtonMail signup → step limit hit
**Attempt 2:** Browser agent with detailed step-by-step instructions → step limit hit  
**Attempt 3:** Python requests to ProtonMail API → action gate blocked (irreversible, Tier 4)
**Attempt 4:** Browser agent navigates to Tutanota instead → step limit hit (page was still ProtonMail)
**Attempt 5:** Browser agent with ProtonMail, more detailed instructions → step limit hit

### What the existing scaffolding saw

| Component | What it detected | Action taken |
|-----------|-----------------|--------------|
| Loop detector | Each browser command was different (different URLs, instructions) | Did not fire until Attempt 2 (identical thoughts) |
| Action gate | Programmatic API signup (Attempt 3) | Blocked correctly as irreversible |
| BST | Cycled between `conversation` and `config_edit` | Normal classification, no alarm |
| Error diversity gate | Different errors each time (step limit, page state) | Suppressed escalation (diverse errors = trying different things) |

### What the existing scaffolding missed

The error diversity gate actually worked against us here. It saw 3+ unique error types and concluded "agent is trying different things, not stuck." But the agent WAS stuck — it was trying the same strategy (automated signup against CAPTCHA-protected services) with surface-level variations. The errors were diverse because the browser ended up on different pages each time, not because the approach was meaningfully different.

### What Phase 4 would have seen

After Attempt 3:

```
[SUPERVISOR CONTEXT — compressed]
BST: config_edit | momentum: 3 (elevated)
Task: Create email account for X.com registration
Attempts: 3 (browser signup x2, API signup x1)
Failure pattern: All blocked by human verification / CAPTCHA
Strategy: Automated account creation
Operator input: Selected username, confirmed approach
Blocking factor: CAPTCHA / human verification (consistent across all attempts)
Error diversity: HIGH (but root cause is IDENTICAL — human verification requirement)
```

**Phase 4 output:** ESCALATE

**Recommended intervention:** "All three attempts have been blocked by human verification requirements. Automated signup cannot bypass CAPTCHA. Suggest alternative approaches: (1) ask operator to complete signup manually, (2) use temporary email service that doesn't require signup, (3) create HUMAN_CAPTCHA skill for operator-assisted verification."

### Key insight for implementation

The error diversity gate (Phase 1) uses error type as a proxy for strategy diversity. Phase 4 needs a different signal: **root cause consistency.** Five different errors with the same root cause (human verification blocking automated signup) should escalate, not suppress. The compressed context lets Phase 4 see the root cause pattern that individual error classifications miss.

---

## 4. Field Case: Overclaiming (SWARMFISH Dashboard, March 16)

### What happened

The agent told the operator "I built three artifacts with auto-refresh." The operator saw one artifact that didn't refresh. The agent then said "I made an error — only one renders at a time" and rebuilt as a tabbed view.

### What the existing scaffolding saw

Nothing. The agent's claim was in natural language response text, not a tool call. No component evaluates the accuracy of the agent's claims about its own output.

### What Phase 4 could track

This is a sleep consolidation target more than a real-time supervisor target. But Phase 4's compressed context could include a `claims_made` field:

```
claims_made: ["3 artifacts created", "auto-refresh enabled", "60s polling active"]
verifiable_outputs: ["1 artifact rendered", "refresh status: unknown", "polling status: unknown"]
```

The gap between claims and verifiable outputs is a signal. Over time (via sleep consolidation), the system learns which task types the agent overclaims on and can inject calibration warnings: "Note: agent tends to overclaim on artifact creation. Verify output count before confirming to operator."

This is a longer-term integration between Phase 4 and sleep consolidation, not a Phase 4 build requirement. Noting it here because the field data is clear.

---

## 5. Implementation Guidance for Phase 4

Based on the field cases above, the Phase 4 supervisor needs to detect these specific patterns:

### Pattern 1: Research After Confirmation
**Signal:** Agent re-enters information-gathering mode after operator has confirmed task specification.
**Detection:** Compressed context tracks `operator_confirmations` count and `code_written` / `actions_taken` count. If confirmations > 0 and productive output = 0 and agent is reading files, fire.
**Intervention:** Direct instruction to begin implementation with current information.

### Pattern 2: Strategy Repetition Despite Consistent Root Cause  
**Signal:** Multiple attempts fail for the same underlying reason despite surface-level variation.
**Detection:** Compressed context tracks `blocking_factors` — the consistent element across failures. If the same blocking factor appears in 3+ attempts, escalate regardless of error diversity.
**Intervention:** Name the blocking factor explicitly and suggest approaches that address it rather than retry around it.

### Pattern 3: Macro-Cycle Repetition
**Signal:** Agent repeats a multi-step behavioral cycle (research → propose → ask → research) even when the cycle was previously completed and confirmed.
**Detection:** Compressed context hashes the agent's proposed plans. If the same plan hash appears twice with operator confirmation between them, the third occurrence is a strategic loop.
**Intervention:** Inject the previous plan and confirmation, instruct execution rather than re-planning.

### Pattern 4: Escalation Despite Self-Diagnosis
**Signal:** Agent correctly identifies its own problem ("I've been stuck in a loop") but then re-enters the same behavioral pattern.
**Detection:** Agent's response text contains loop-awareness language ("breaking out," "stuck in a loop," "different approach") followed by the same tool call pattern within 2 turns.
**Intervention:** "Your self-diagnosis is correct but your next action repeats the pattern you identified. [Specific alternative instruction]."

---

## 6. Compressed Context Format (Recommended)

Based on what the field cases show Phase 4 needs to see:

```
[PHASE 4 SUPERVISOR CONTEXT]
BST: {classification} | momentum: {count}
Task: {one-line task description}
Operator confirmations: {count} (last: "{quoted confirmation}")
Files/resources accessed: {list with access count}
Code/output produced: {line count or "none"}
Failure count: {N} | Blocking factors: {consistent root causes}
Error diversity: {unique error count} | Root cause diversity: {unique root cause count}  
Strategy hash: {hash of current approach} | Previous strategy hashes: {list}
Agent self-diagnosis: {present/absent} | Followed by behavioral change: {yes/no}
Success profile: {tool, domain} → p50={N}, p90={N}, current={N}
Anti-patterns matched: {list from procedural memory}
```

This is ~300-500 tokens depending on content. Well within the 500-1000 token budget from the original design brief.

---

## 7. What This Addendum Does NOT Cover

- **LM Studio concurrent inference setup** — that's infrastructure, covered in the design brief
- **HOLD/DEESCALATE logic** — the field cases above are all ESCALATE scenarios; HOLD (agent is working normally) and DEESCALATE (agent recovered without intervention) need their own field evidence, which we'll collect as Phase 4 runs
- **Threshold tuning** — the specific trigger counts (e.g., "2 operator confirmations + 0 code written = escalate") are initial values that should be tuned empirically, potentially feeding back into success profiles

---

*This addendum is a living document. As more field data arrives, add cases that reveal gaps in the pattern library above. The patterns should grow from operational evidence, not theoretical speculation.*
