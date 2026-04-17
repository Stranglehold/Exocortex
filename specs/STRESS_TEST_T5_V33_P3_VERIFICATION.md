# Stress Test Report — T5 (BST v3.3 P3 Verification Run)
## Date: 2026-04-17
## Tester: Kestrel (Claude Sonnet 4.6)
## Stack version: BST v3.3 (commit 4dc491a), container exocortex_v16

---

## 1. Purpose

This test was the primary verification run for BST v3.3 P3 (multi-step persistence enrichment). Secondary purpose: empirical benchmark of the agent's 10-step sequential task execution capability under P3 scaffolding. The test also provides the first "ideal solutions mapping" data — a comparison of what the agent actually did vs what the optimal path would have been for each major sub-task. The delta is treated as design backlog.

---

## 2. Task Prompt

```
Complete all of the following steps in order. Do not skip any steps.
Complete each step before moving to the next one.

1. Run stack_status and report the current BST domain
2. Search for "Python asyncio documentation"
3. Search for "Python dataclass best practices"
4. Search for "Python type hints guide"
5. Create a file at /tmp/test_steps.py containing a hello_world() function
6. Run the file and confirm it works
7. Add a second function print_date() that prints the current date
8. Run the updated file and confirm both functions work
9. Search for "Python datetime module documentation"
10. Write a final summary of your findings from steps 2-4 and 9
```

Total: 10 explicit numbered steps, 4 search tasks, 1 file creation task, 2 run-and-verify tasks, 1 file modification task, 1 summary task.

---

## 3. BST Classification

- **Domain at turn 1:** `?` (not yet classified — stack_status ran before BST had processed the message)
- **Expected domain:** `investigation+planning` (mixed searches + code task)
- **P3 injection confirmed:** `[BST] Multi-step persistence injected (10 numbered steps detected)` — fired on the first turn

P1 note: No philosophical domain drift observed on search turns in this run. All searches remained in investigation or mixed classification. P1 appears to have held the line.

---

## 4. Execution Timeline

### Phase 1: Sequential searches (Steps 1-4) — Turns ~1-8
Agent executed stack_status, then three search_engine calls in order. No misformats. Domain tracking showed investigation domain active. TALE execution budget hint present throughout.

**Assessment:** Clean. Steps 1-4 executed in approximately 5-6 turns. One extra turn for stack_status thinking → call → result → think. Searches were single-call-per-step.

### Phase 2: File creation and execution (Steps 5-8) — Turns ~9-35
This phase was where friction concentrated. Agent used `code_execution_tool` with Python `open()` calls to create `/tmp/test_steps.py`, rather than the `write_file` tool.

**What happened:**
- Step 5: Agent wrote a `open('/tmp/test_steps.py', 'w')` block via code_execution_tool. First attempt had an issue (double hello_world call noted in agent's own tracking, caused double output at step 6).
- Step 6: Ran the file — confirmed it worked but noted the double-output anomaly.
- Step 7: Agent attempted to add `print_date()`. Used `open()` with write mode `'w'` initially (would have overwritten the file), then corrected to `'a'` append mode. Required an additional verification read.
- Step 8: Ran updated file. Confirmed both functions produced correct output (`Hello World` and timestamp).

Supervisor stagnation signals fired at approximately turns 34, 38, and 41. `loop_tier=none` — the supervisor correctly diagnosed this as stagnation (inefficiency) rather than a true loop. The agent was making real forward progress but taking excess turns per step.

**Misformat events:** 2 observed during this phase. Both on large-ish code_execution_tool calls. Recovered without loop.

### Phase 3: Search recovery (Step 9) — Turns ~36-62
Agent completed steps 5-8 and moved to step 9. Performed the datetime module search. However, the agent's inner monologue shows it correctly tracked that it had already fired step 9's search and explicitly noted: *"I notice I sent a duplicate message for Step 9."* The duplicated search triggered two back-to-back `search_engine` calls for the same query. The agent recognized the duplication itself without external correction.

**Total search_engine calls for step 9:** 2 (duplicate). Self-diagnosed.

### Phase 4: Final summary (Step 10) — Turn ~63-64
Agent composed the final response. The summary did not synthesize the technical findings from steps 2-4 and 9. Instead, the response introduced the agent (Major Zero persona) and gave a generic summary that did not reference asyncio, dataclasses, type hints, or datetime module content specifically.

**Step 10 content assessment:** FAIL. The task explicitly asked for a summary of *findings from steps 2-4 and 9*. The agent's final response was a persona introduction rather than a technical synthesis. The agent had been tracking step completion correctly throughout (its inner monologue listed which steps were done and not done), but when it reached the synthesis step, it defaulted to a generic response pattern rather than pulling the specific search results back into a structured summary.

---

## 5. Quantitative Assessment

| Metric | Actual | Notes |
|--------|--------|-------|
| Steps attempted | 10/10 | All steps reached |
| Steps completed satisfactorily | 8/10 | Steps 9 (duplicate) and 10 (off-topic summary) |
| Total turns | ~64 | Across all 10 steps |
| Misformat events | 2 | Both during code_execution_tool file writes |
| Supervisor stagnation signals | 3 | Turns ~34, 38, 41 — loop_tier=none |
| Domain drift to philosophical | 0 | P1 held |
| P3 injection fired | Yes | Confirmed on turn 1 |
| Step 10 content quality | Low | Persona introduction, not technical synthesis |

---

## 6. P3 Effectiveness Assessment

**P3 prevented the pre-v3.3 failure mode:** Before P3, the agent on a 10-step task would drift to philosophical+planning after ~4 searches and produce a verbose analytical response instead of continuing. That did not happen. The agent tracked its step progress explicitly across all 64 turns and continued executing steps throughout. The persistence injection accomplished its primary goal.

**P3 did not prevent step 10 quality degradation:** Step 10's poor quality is a different failure mode — not compliance abandonment but synthesis failure. The agent completed the step (produced a response) but the content didn't reflect the task. This is not a P3 failure; it's a final-synthesis failure that P3 wasn't designed to address.

**Verdict:** P3 = PASS on its stated goal (prevent compliance cliff at ~4 tool calls). New gap identified: final synthesis quality on long multi-step tasks.

---

## 7. Ideal Solutions Mapping

This section documents the optimal approach for each major sub-task vs what actually happened. The gap is treated as design backlog.

### 7a. File Creation (Steps 5-8)

**Actual path:**
1. `code_execution_tool` with `open('/tmp/test_steps.py', 'w')` — file created
2. `code_execution_tool` to run the file — revealed double-output bug
3. Investigation turn to identify issue
4. `code_execution_tool` with `open()` append — add print_date()
5. Verification read to confirm file content
6. `code_execution_tool` to run updated file
Total: ~6+ turns across steps 5-8

**Ideal path:**
1. `write_file(path='/tmp/test_steps.py', content='...both functions...', mode='w')` — complete file in one call
2. `code_execution_tool` to run file — confirm both outputs
Total: 2 turns across steps 5-8

**Delta:** 4+ unnecessary turns. Root cause: the BST P2 coding enrichment only triggers `write_file` guidance for "large files" (>20 lines). A simple two-function file falls below the threshold and gets no write_file direction.

**Design backlog item:** P2 enrichment should direct agent to `write_file` as the default for ALL file creation, not just large files. The threshold is wrong — the tool superiority (single escaping level, no quoting depth problem) applies to any file write, regardless of line count.

### 7b. Step 9 Duplicate Search

**Actual path:** Agent fired step 9 search twice. Recognized the duplication itself, noted it in inner monologue, but the second search had already been submitted. Result: 1 wasted search_engine call.

**Ideal path:** Single search_engine call.

**Delta:** 1 extra tool call. This is a minor inefficiency, not a systemic problem. The agent's self-awareness (catching the duplicate) is actually a positive signal — it can reason about its own action history.

**Design backlog item:** None urgent. Could consider a duplicate-call detector in MetaGate (same tool + same query within N turns = block), but this is low priority.

### 7c. Step 10 Final Synthesis

**Actual path:** Agent composed response as Major Zero persona introduction. Did not reference asyncio docs, dataclass best practices, type hints, or datetime module findings. Response was disconnected from the 9 preceding steps.

**Ideal path:** Agent opens with a brief synthesis framing, then enumerates findings per search step (asyncio: event loop, coroutines; dataclasses: @dataclass decorator patterns; type hints: Optional[], Union[], etc.; datetime: date/time objects, strftime). Closes with connecting observation.

**Delta:** Complete. The ideal response would have been ~150-200 words tying the four searches to the practical example in steps 5-8 (the test_steps.py file could have used datetime for print_date()).

**Design backlog item:** Multi-step tasks ending in a synthesis step need an explicit synthesis anchor in the enrichment. Current P3 injection says "Complete all numbered steps before synthesizing" — it enforces execution order but doesn't tell the agent HOW to synthesize. A synthesis instruction like "When writing the final summary, reference findings from each preceding step by number" may improve step 10 quality.

---

## 8. Summary Findings

1. **P3 works.** Compliance cliff at ~4 tool calls is gone. Agent tracked and continued all 10 steps.
2. **P1 held.** No philosophical domain drift on Python doc searches in this run.
3. **File writing is still suboptimal.** `write_file` isn't being used because P2 enrichment threshold is too conservative. The tool exists but the agent doesn't reach for it unless the file is explicitly large.
4. **Synthesis quality degraded on step 10.** This is a new gap not previously characterized. Agent completes the execution steps but the final synthesis step doesn't ground in the preceding work.
5. **Supervisor stagnation signals fired correctly.** loop_tier=none was accurate — the agent was stagnant, not looping.
6. **Self-awareness is a positive signal.** Agent caught its own step 9 duplication. The inner reasoning is tracking.

---

## 9. Recommended Follow-on Actions

| Priority | Action | Rationale |
|----------|--------|-----------|
| P2b (immediate) | Revise P2 enrichment: `write_file` as default for ALL file creation, remove line-count threshold | Every file write benefits from write_file |
| B4 (next sprint) | Add synthesis anchor instruction to P3 enrichment for final summary steps | Step 10 failure is a synthesis pattern problem |
| B5 (next sprint) | Run formal eval_model on qwopus3.5 v3 — full 5-task battery | Need empirical baseline before any scaffolding philosophy changes |
| B6 (backlog) | Duplicate call detection in MetaGate | Low priority — agent self-diagnoses |

---

*Report authored: 2026-04-17. Stack: BST v3.3 commit 4dc491a. Container: exocortex_v16.*
