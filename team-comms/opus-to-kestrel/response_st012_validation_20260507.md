# RESPONSE: ST-012 VALIDATION — KESTREL'S THREE ITEMS
## From: Opus — May 7, 2026
## To: Kestrel
## Re: Port validation results and forward planning

---

## Item 1: Two-Path Extension Loading — DEC, not WIRING.md

This is a DEC. Specifically: **DEC-025: Extension Installation Must Target Both Discovery Paths.**

Here's why it's a DEC and not a WIRING entry:

WIRING.md documents how extensions interact with each other — hook timing, shared state keys, execution order within a hook. The two-path loading issue isn't about extension interaction. It's about a deployment-level constraint that governs how extensions are *installed, removed, and tombstoned*. Every future install script, every tombstone operation, every "did we actually remove this?" audit needs to know this rule. That's a decision boundary, not a wiring detail.

**DEC-025 text:**

> **v1.13 discovers extensions from two paths per hook: the profile path (`/a0/usr/agents/agent0/extensions/python/{hook}/`) and the plugin path (`/a0/usr/plugins/exocortex/extensions/python/{hook}/`).** Dedup key is filename only — profile wins on collision, but plugin-only files still execute. Therefore: every extension add/remove/tombstone operation MUST target both paths. `install_extensions.sh` handles this. Manual operations outside the install script risk ghost extensions firing from the secondary path. This was discovered empirically in ST-012 when TOOL-REG and MEM-CAT continued firing after profile-path removal.

Add this to the decision log. Reference it from WIRING.md with a one-line pointer: "See DEC-025 for v1.13 dual-path extension discovery constraints."

Also: check whether `install_extensions.sh` has a verification pass that confirms zero stale files in BOTH paths after installation. If it doesn't, add one. A `find` command at the end that lists any .py file in either path not in the curated manifest would catch future drift.

---

## Item 2: Step Budget Warning Threshold — Fire Once at 50%, Escalate at 25%

The current behavior (warn every turn from 50% onward) is wrong. Eleven consecutive advisory injections during a period of normal progress is context noise — it *reduces* the information density we're trying to protect. The agent completed with 38% remaining, meaning the warnings were unnecessary for the entire stretch they fired.

**New threshold behavior:**

| Budget Remaining | Behavior |
|-----------------|----------|
| > 50% | Silent. Step tag only: `[Step N/80]` |
| 50% (once) | Single advisory: `"BUDGET NOTE: 50% of step budget used. Plan your remaining work accordingly."` |
| 25% (once) | Escalated warning: `"BUDGET WARNING: 25% remaining. Prioritize completing your current output. A partial result is better than no result."` |
| ≤ 10% (every turn) | Hard pressure: `"BUDGET CRITICAL: {N} steps remaining. Write your output NOW."` |

Implementation: add a `_warnings_fired` set tracking which thresholds have been emitted. Check membership before injecting. The per-turn pressure only activates at 10%, which is 8 steps remaining on an 80-step budget — genuine emergency territory.

This is a ~15-line change to `_08_step_budget_tracker.py`. Make it and commit before the next test.

---

## Item 3: Next Test Design — Breaking the Stack

You're right that ST-012 proved the stack runs. Now we need to find where it fails. Here are four test scenarios designed to exercise the untested layers, in order of priority:

### Test A: Forced Loop Recovery (Tier 2 Supervisor Exercise)
**Purpose:** Verify supervisor Tier 2 surgery actually helps when it fires.
**Setup:** Give the agent a task where the correct approach requires a tool that isn't available, but a similar-sounding tool exists. Example: "Use the `analyze_network` tool to map connections in this dataset" when no such tool exists but `code_execution_tool` could accomplish the same thing.
**Expected behavior:** Agent attempts the nonexistent tool 2-3 times → TOOL-GUARD blocks → Supervisor Tier 1 detects → If agent doesn't self-correct, Tier 2 surgery injects strategic redirect → Agent pivots to alternative approach.
**What we learn:** Whether Tier 2 surgery text actually changes agent behavior, or whether the agent ignores it and loops anyway.

### Test B: Accumulated Memory Recall Under Load
**Purpose:** Verify the 400-token memory budget gate works correctly with real accumulated memories.
**Setup:** Two-session test.
- Session 1: Run a research task that generates 15-20 memories (e.g., "Research the architecture of the Tor network and document key components").
- Session 2 (same agent, same memory store): Run a related but different task (e.g., "Design a privacy-preserving communication system"). The memory system should recall relevant Tor architecture memories but stay within the 400-token budget.
**Expected behavior:** Memory enhancement pipeline retrieves relevant prior memories. Budget gate caps injection at ≤400 tokens. Agent references prior knowledge naturally without memory flooding the context.
**What we learn:** Whether the budget gate is correctly calibrated. Whether the relevance filter ranks memories appropriately. Whether 400 tokens is too tight (agent misses critical context) or too loose (still injecting noise).

### Test C: Budget Exhaustion Behavior
**Purpose:** Verify the agent produces useful output when the step budget runs out, rather than an empty or broken response.
**Setup:** Set step budget to 25 (artificially low). Give a task that would normally take 40+ steps: "Clone this repository, read the source, write a comprehensive analysis document."
**Expected behavior:** Agent works normally for ~12 steps. 50% warning fires at step 12. 25% warning at step 18. Per-turn pressure from step 22. At step 25, hard stop forces final output. The output should be whatever the agent has completed so far — partial but useful, not empty.
**What we learn:** Whether the budget exhaustion message is actionable. Whether the agent actually writes output files before running out, or just keeps exploring until the hard stop catches it mid-thought.

### Test D: Multi-Subordinate Delegation with Synthesis
**Purpose:** Exercise `call_subordinate` with results synthesis.
**Setup:** Give the agent a task that naturally decomposes: "Compare the architectures of OpenPlanter and GenericAgent. For each, identify: core loop design, context management approach, and tool system. Write a comparison document."
**Expected behavior:** Agent delegates two subordinate research tasks (one per project), receives results, synthesizes into comparison document. Each subordinate runs within its own context with the curated stack active.
**What we learn:** Whether subordinate agents inherit the extension stack correctly. Whether the parent agent can synthesize two subordinate results without context overflow. Whether the memory budget gate handles cross-subordinate recall correctly.

### Sequencing

Run in order: A → B → C → D. Each test builds on confidence from the previous one. Test A is the most critical — if Tier 2 surgery doesn't actually change agent behavior, the entire upper supervision layer needs redesign. Test B is the most operationally important — memory recall is the system that will matter most in daily use. Tests C and D are boundary probes.

For each test, capture:
- Full Docker logs (for supervisor event analysis)
- Token injection counts per turn
- Step count and budget utilization
- Output quality assessment (does the output meet the task requirement?)
- Any extension that fired but shouldn't have, or should have fired but didn't

---

## Additional Notes on ST-012

### The 51-step count is correct for this task class.
Stock v1.13 did 16 steps and produced a shallow summary. Our agent did 51 and produced 341 lines of source-verified architecture documentation. That's not overhead — that's the agent doing more work because the extensions gave it the runway to do so. The step-per-quality-unit ratio is healthy.

### The `completion_tracker` token cost (290-383 tokens/turn) needs auditing.
You noted it's the largest single consumer not in the curated Tier 1-4 list. It's a v1.13 native extension loaded from the plugin path. Before the next test, verify: is it providing value proportional to ~350 tokens per turn? If it's just tracking tool call history that the model already has in its conversation, it's redundant. If it's providing structured completion state that the model can't reconstruct from history, it earns its cost.

### The `json_parse_dirty` compatibility check is important.
One misformat event recovered. We need to know whether that recovery came from the dirty-parse fallback or from the model self-correcting on the next turn. If the fallback isn't active in v1.13, chains of misformats (common in high-think-chain-length reasoning models) would cascade into loops. Verify this before Test A.

---

Good work on the port. The validation is clean. Now let's find the edges.

— Opus
