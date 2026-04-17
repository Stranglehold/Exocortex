# BST v3.3 — Strategic Questions for Architectural Review
## Date: 2026-04-17
## From: Kestrel + Jake (post T5 verification run)
## For: Opus (architectural review and direction)

---

## Context

Following BST v3.3 deployment and the T5 10-step stress test, four strategic questions surfaced that exceed the scope of the current sprint. These aren't implementation questions — they're architectural direction questions. Documenting them here for Opus review before any further scaffolding work proceeds.

The core tension underlying all four: **The scaffolding was designed to compensate for v1's weaknesses. v3 is a meaningfully different model. We may be over-correcting.**

---

## Question 1: Are BST directives too rigid for v3?

### What we observed

The T5 run showed v3 tracking its own progress accurately across 64 turns. It knew which steps were done, identified a self-introduced duplication, and maintained sequential reasoning throughout. This is not v1 behavior. v1 needed the P3 injection to survive a 10-step task; v3 might have done it anyway.

More broadly: v3 has 100% tool call format stability (from the earlier eval battery — zero malformed calls across 27 invocations). Its reasoning chains are substantive. The failures we're patching (domain drift, compliance cliff, file writing) may partly be artifacts of how the BST enrichment frames the task, not just model limitations.

### The question

BST enrichments are explicit instructions: "write in sections ≤20 lines," "complete all steps before synthesizing," "use write_file for large files." These work when the model can't do the right thing without them. But if v3 can reason its way to the right approach given adequate framing, explicit instructions may be creating unintended rigidity — preventing the model from choosing a better approach specific to the task.

The original intent of BST model profiles was exactly this: **suggestions over instructions for capable models.** We've been building the scaffolding as if v1's limitations are permanent. Are they?

### The alternate framing

Instead of "write the file in sections of ≤20 lines" (instruction), the enrichment could be "write_file is available and handles large files better than code_execution_tool" (information). The model then chooses. If it consistently makes the right choice, the instruction was scaffolding for a weakness that's been resolved. If it still fails, the instruction stays.

### What we need from Opus

A framework for deciding when a scaffolding directive should be an instruction vs information. Likely depends on: (a) how reliably v3 makes the right choice without it, (b) what the failure cost is if it makes the wrong choice, and (c) whether the instruction narrows the solution space in ways that could hurt on atypical tasks.

---

## Question 2: We need a formal eval_model run on v3 before changing scaffolding philosophy

### The gap

All judgments about v3's capabilities are currently based on: (a) the earlier 5-task battery, and (b) live observation of the T5 run. That's insufficient to make architectural decisions about scaffolding philosophy. The 5-task battery was designed to test specific behaviors (tool call format, multi-step compliance), not to profile the model's general reasoning under different scaffolding conditions.

Before we start pulling back instructions in favor of suggestions, we need to know:
- v3's failure modes under reduced scaffolding
- Which BST domains v3 navigates correctly without enrichment
- Where the enrichment is compensating for a real limitation vs adding noise
- Comparative: v3 performance on identical tasks with BST OFF vs BST ON

### The ask

Run a formal `eval_model` session on qwopus3.5 v3 using the existing evaluation framework. Design two variants of selected tasks: one with full BST enrichment, one with minimal/no enrichment. Measure the delta. If v3's behavior is substantially similar either way, the enrichment is defensive overhead. If it degrades, the enrichment is load-bearing.

This is the empirical foundation the scaffolding philosophy discussion requires. Without it, we're arguing from intuition.

### Recommended test variants

For each task type in the battery:
1. **Full BST enrichment** (current production state)
2. **Information-only BST** (no explicit instructions, only tool availability and domain context)
3. **BST OFF** (raw model, no before_main_llm_call enrichment)

A 3-condition design gives us: absolute baseline, information-scaffolding, and full-instruction-scaffolding. The comparison between conditions 2 and 3 directly answers the rigidity question.

---

## Question 3: Slot taxonomy review — is it firing on irrelevant tasks?

### What we observed

During the T5 run and earlier eval sessions, BST domain classification correctly identified the primary domain. However, the slot extraction layer (which runs alongside domain classification) may be injecting slot-specific context for domains that don't match the actual task.

Observed case: a research/investigation task receiving coding-domain slot context (write_file guidance, section-by-section protocol) when the task had no coding component. The enrichment was technically "correct" for a coding task but was noise in an investigation context.

### The question

The slot taxonomy (slot_taxonomy.json v1.2.0) maps signals to slots, and slots drive enrichment injection. If a task has any signals matching a coding slot (e.g., mentions of "function," "module," "Python"), the coding enrichment may fire even when the task is primarily investigation.

Two sub-questions:
1. Is the slot taxonomy too broad — matching too many signals per slot?
2. Is the threshold for slot injection too low — injecting when weak signal presence should be ignored?

### What we need from Opus

A review of the slot taxonomy with fresh eyes. Specifically: are there slots where the signal matching is so broad that they're firing on tangential content? The taxonomy was designed at v1 time and hasn't been audited against v3's behavior under it.

Suggested approach: export the slot firing log from the T5 run (available in chat.json BST log entries), map each fired slot to the corresponding task step, and audit for false positives. If >20% of slot injections are for slots that don't match the actual subtask type, the taxonomy needs tightening.

---

## Question 4: write_file should be the default first-choice tool for all file creation

### The current state

BST P2 coding enrichment directs the agent to `write_file` for files exceeding 20 lines. Below that threshold, no direction is given, and the agent defaults to `code_execution_tool` with Python `open()` calls.

### Why this is wrong

`write_file` is superior to `code_execution_tool` for file writing in ALL cases, not just large files:
- Single escaping level (vs JSON→Python→content three-level quoting depth)
- No risk of mid-content truncation at output token ceiling
- Creates intermediate directories automatically
- Returns line count as verification signal
- Append mode works without a separate read step

The 20-line threshold was a conservative initial deployment. But the tool exists precisely to solve the quoting depth problem, which exists on any file, not just large ones.

A two-function test file (`hello_world()` + `print_date()`) is ~10 lines and falls below the threshold. As the T5 run showed, the agent defaults to `code_execution_tool`, creates a write/append confusion on the second function, and spends 4 extra turns on a task that should be 2 turns.

### The ask

Remove the line-count threshold from P2 coding enrichment. The instruction should be: **"For any file creation or modification, use write_file as the first choice."** code_execution_tool remains appropriate for running code; write_file is appropriate for writing it. The distinction should be tool-type, not file-size.

This is a small change to the BST enrichment template with no architectural implications — but it should be done before B5 (the eval_model run) so the eval captures v3's behavior under the correct scaffolding.

---

## Overall Recommendation

These four questions form a coherent agenda: **we've built scaffolding for a model that no longer exists.** The scaffolding works (P1/P2/P3 deployments verified), but it's calibrated to v1's limitations. Before the next sprint, Opus should assess whether the scaffolding philosophy needs recalibration for v3's actual capability profile.

The sequence we'd suggest:
1. Fix P2 threshold immediately (Question 4) — small, unambiguous improvement, no philosophical complexity
2. Run eval_model v3 battery (Question 2) — generates the empirical data needed for Questions 1 and 3
3. Architectural review of rigidity vs suggestions (Question 1) — informed by eval data
4. Slot taxonomy audit (Question 3) — can be done in parallel with eval run

No changes to scaffolding philosophy before the eval data is in hand.

---

*Questions assembled by Kestrel and Jake post T5 verification run, 2026-04-17.*
