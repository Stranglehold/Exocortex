# Adaptive Supervisor — Phase 1 Findings

**Status:** Post-deployment field observation. Prepared by Kestrel (March 2026).

**Context:** Phase 1 (Directions A + B) deployed March 15, 2026. Domain-aware thresholds and error diversity gate are live. This document reports what the first observed session revealed about what Phase 1 fixed and what it didn't.

---

## Phase 1 Deployment Status

**What was built:**
- `DOMAIN_THRESHOLDS` dict: structural domains (codegen/debugging/system_admin) use 6/12/18; exploratory domains (research/analysis/investigation) use 3/6/12; default stays 3/6/9
- `_get_domain_thresholds(bst_domain)`: reads BST compound signature (`"analysis+codegen"` → takes max tier per component)
- Error diversity gate in `_update_loop_state`: if 3+ unique error types in recent history, suppress Tier 2 (context surgery) and Tier 3 (circuit breaker), hold at Tier 1 warn

**Validation:** The GitHub trending skill that prompted the design work completed successfully on first post-deployment run, with no supervisor interference. The agent worked through multiple iterations to fix a scraping approach and produce findings. Phase 1 provided the designed headroom.

---

## Session 055 Observations

Jake asked the agent to run the GitHub trending scout skill. The skill file had a syntax error. The agent spent ~20 turns debugging and fixing it. Two distinct phases emerged.

### Phase 1 of the session — Iterative debugging (no supervisor interference, correct behavior)

The agent encountered a sequence of genuinely different errors:

1. `SyntaxError: unterminated string literal` — string on line 17 was truncated mid-value
2. `SyntaxError: '(' was never closed` — sed fix mangled the line further
3. `IndentationError: expected an indented block` — file was now only 17 lines; body was lost
4. File had to be recreated from scratch
5. After recreation: HTML parsing returned 0 results
6. BeautifulSoup targeting wrong elements → revised → found correct `article` elements → successfully parsed 15 repositories

Each iteration produced a different error type and demonstrably advanced the state. No supervisor interference was observed. **This is the case Phase 1 was designed to protect, and it worked.**

### Phase 2 of the session — Genuine loop (caught, correct behavior)

Once the agent found the working parsing approach (15 repositories extracted), it stalled. It ran the same code 8+ times, producing identical output, saying "I see the issue — I'm running the same code repeatedly" but failing to change its action. The `LOOP DETECTED` message fired and broke the cycle.

**This was a genuine loop.** Phase 1 was correctly not protecting it. The loop detection mechanism that fired was the tool execution layer's duplicate action detector, not the supervisor tier system.

---

## Finding 1 — BST Classification Lag

**What happened:** The user said "run the github trending scout skill." The BST classified this as `conversation` (0 signals). For the first 12 turns of debugging, the active threshold profile was `default` (3/6/9), not `debugging` (6/12/18).

The BST momentum break to `bugfix+config_edit` happened at turn 12, triggered by `[ERROR-DX] terminal_session_hung`. By then, most of the legitimate debugging was already complete.

**The gap:** Domain-aware thresholds only help when the BST classification is accurate. The BST classifies entry intent from the user message. Task type can drift during execution: user says "run X," X breaks, agent starts debugging. The BST doesn't see the drift unless an error signal is strong enough to trigger a re-classification.

**The consequence:** An agent debugging a skill that the user asked it to "run" gets `default` thresholds, not `debugging` thresholds. The user-facing label and the actual work type diverge. Phase 1 helps when both align; it can't help when they don't.

**Design question for Opus:** Should the supervisor's threshold selection be allowed to override the BST classification based on observed error patterns in the current session — independent of what the user asked? If the failure history shows 3+ different error types on `code_execution_tool`, that's a behavioral signal of debugging regardless of what the BST domain says. This might be a natural extension of the diversity gate: error diversity suppresses escalation AND shifts the effective threshold to the debugging profile.

Alternatively: should the BST be extended to re-classify based on observed tool failure patterns mid-session, not just from the user message?

---

## Finding 2 — Successful-Execution-No-Progress Loop

**What happened:** The agent's tool calls were succeeding (200 status, 15 repos found, output printed). There were no tool failures. The consecutive failure counter was not incrementing. The supervisor tier system had no signal to act on.

The loop was: `code runs → same output → agent says "let me add X" → runs same code → same output`. The error diversity gate is irrelevant here — there are no errors.

**The gap:** The supervisor's loop detection is built around failure signals. It doesn't have a signal for **successful execution that produces no forward progress**. This is a structurally different failure mode:

| Pattern | Supervisor signal | Current handling |
|---------|-------------------|-----------------|
| Same tool, same error | consecutive_failures++ | Tier 1→2→3 |
| Same tool, different errors | consecutive_failures++, diverse types | Phase 1: suppress Tier 2+ |
| Same tool, success, same output | consecutive_failures = 0 | Nothing |

The third row is what happened. The loop was caught by the tool execution layer's duplicate action detector (different system, detects syntactically identical tool calls). That's a reasonable safety net, but it's a different layer from the supervisor's strategic steering.

**Design question for Opus:** Should the supervisor track output similarity alongside failure counts? A hash or similarity score on the last N tool outputs would detect "running successfully in place." When output similarity exceeds a threshold across consecutive turns, that's a different kind of stuck — not failure-stuck, progress-stuck. The appropriate intervention is also different: not "your tool failed, try an alternative" but "your approach is working mechanically but not advancing — what needs to change about the goal?"

This is potentially Direction C territory (progress signal tracking), but the mechanism is output similarity rather than reasoning state. It doesn't require `_12_reasoning_state.py` — it only requires comparing tool outputs across turns, which is available in the failure history structure already.

---

## What This Is NOT

- This is not a Phase 1 failure. Phase 1 worked for its designed case and the first validation run confirmed it.
- This is not an argument against the tier system. The tiers are still the right escalation structure. What changes is the input signals.
- Finding 2 is not the same as the Einstellung effect analysis in the design note. Einstellung is the agent failing to see alternatives due to prior fixation. Finding 2 is the agent recognizing it's looping but lacking a mechanism to break out — different root cause.

---

## For Opus

Two concrete questions:

**On Finding 1 (BST lag):** Is the right fix behavioral (supervisor uses error diversity as a threshold-profile signal independent of BST domain) or architectural (BST re-classifies mid-session from observed failure patterns)? The behavioral fix is lower effort and stays within Phase 1's scope. The architectural fix is more correct but touches the BST.

**On Finding 2 (successful-execution-no-progress):** Is output similarity tracking the right signal, or is there a better proxy for "working but not advancing"? The tool execution duplicate detector already catches identical calls — but it catches them at the syntax level, not the semantic level. The agent could run slightly different code that produces the same output and not be caught. A semantic signal (output hash or embedding similarity) would be more robust. Where does this fit in the Phase roadmap — is it a Phase 2 addition to Direction C, or a separate direction?
