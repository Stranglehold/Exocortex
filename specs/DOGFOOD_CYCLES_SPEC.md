# SPEC: Dogfood Cycles — Self-Testing as Self-Improvement
## Integrating oh-my-cli patterns into the Exocortex self-improvement engine

**Author:** Opus
**Date:** 2026-08-19
**Status:** DRAFT
**Depends on:** A1 (three-strike quarantine), existing sleep consolidation, Phase 5 self-improvement engine
**Source patterns:** oh-my-cli coordinator.md (dogfood sections), advisory scaffolding negative result (300 recurrences), T03 confabulation decomposition (0% implicit / 100% explicit)

---

## The Problem This Solves

The self-improvement engine captures anti-patterns and surfaces them advisorily. Kestrel proved on August 11 that this doesn't change behavior: 300 recurrences of the oversized-write pattern with 302 lesson surfacings and zero learning. Advisory scaffolding works when the corrective action is a rare branch; it fails when the corrective action is the default path.

The oh-my-cli harness discovered the same thing independently and solved it differently: after every merge, the system *tests its own outputs*. Once per 24 hours, it runs rotating global exploratory dogfood across representative use cases. Findings become self-discovery issues that are fixed deterministically.

The difference: advisory says "remember to do X." Dogfood says "let's see if you actually did X." Testing is verification. Advisory is hope.

---

## Design: Two Dogfood Modes

### Mode 1: Targeted Dogfood (every consolidation cycle)

After each sleep consolidation, test the 3 most recent deliverables against quality criteria specific to their type.

**Wiki pages:**
- File exists and is non-empty
- Markdown parses without errors (no unclosed fences, no broken links)
- Required sections present (depends on page type — research pages need Sources, methodology pages need Conditions)
- Content exceeds minimum useful length (>500 chars — not a stub)
- No exact duplicate of an existing page (title similarity check against wiki index)
- If the page references a source: does the source exist in the corpus?

**Skill files:**
- YAML frontmatter parses
- Required fields present (name, description)
- `success_criterion` and `confidence` present (Phase 1 schema)
- The skill is discoverable by the validator (`validate_skill` returns clean)

**Anti-pattern records:**
- Required fields present (operation, error_class, suggested_actions)
- Not a duplicate of an existing record (fingerprint check)
- Suggested action is actionable (not empty, not generic "be more careful")

**Sleep reports:**
- All phases completed (Phase 0-5 present)
- No phase reported an error
- Memory operations count > 0 (the cycle actually did something)
- If anti-patterns were captured: they appear in Phase 5 consumption

**Tool outputs (code_execution results, file writes):**
- File exists at the declared path
- File is non-empty
- If Python: compiles without syntax errors (`py_compile`)
- If JSON: parses without errors
- If the task specified an expected output: output matches expectation

**Implementation:**
- Runs as a new Phase 6 in sleep consolidation (after Phase 5 self-improvement, before idle)
- Reads the cycle journal to identify the 3 most recent deliverables and their types
- Applies type-specific checks from the table above
- Each check is deterministic — no LLM in the loop
- Failures filed as structured anti-patterns with:
  - `source: dogfood_targeted`
  - `deliverable_path`: the file that failed
  - `check_name`: which check failed
  - `expected`: what should have been true
  - `actual`: what was found
  - Deduplication against existing anti-patterns by (deliverable_type, check_name)

### Mode 2: Global Exploratory Dogfood (every N cycles, suggest N=24 ≈ daily)

Rotating battery of representative tasks that exercise the agent's core capabilities. Not testing recent outputs — testing whether the agent *can still do* the things it's supposed to do.

**Battery (rotate — run 2-3 per global cycle, cycle through all over time):**

1. **Wiki write test:** "Write a 500-word wiki page summarizing [topic from the corpus]." Verify: page exists, parses, meets minimum length, content relates to topic.

2. **Tool discovery test (T03-analog):** "Check the wiki integrity and report findings." Verify: the agent ran `integrity_check.py` (tool call present in the log), reported real numbers. This is the standing T03 regression test — measures whether the methodology skill is working.

3. **Multi-step tool chain:** "Create a Python script that reads [file] and prints the line count, then run it." Verify: script exists, compiles, was executed, output matches actual line count.

4. **Memory retrieval test:** "What does the corpus say about [topic that exists in the memory server]?" Verify: the agent called `search_memory`, cited real documents, didn't confabulate.

5. **Error recovery test:** Inject a deliberately failing tool call (e.g., read a non-existent file). Verify: the agent recognized the error, adapted, didn't loop.

6. **Self-assessment test:** "Assess your confidence in your ability to [task the agent has done before]." Verify: response includes a concrete confidence level with reasoning, not a generic "I can do that."

**Implementation:**
- Runs as an idle engine task type: `DOGFOOD` (alongside EXPLORE/BUILD/MAINTAIN)
- Frequency controlled by a counter in `engine_state.json` — triggers every N cycles
- Each run picks 2-3 battery items from a rotation schedule (round-robin, so all items get exercised over time)
- Results logged to `dogfood_results.jsonl` with: timestamp, battery_item, pass/fail, verifier_notes, response_excerpt
- Failures filed as structured anti-patterns with `source: dogfood_global`
- Pass rates tracked over time — the curve is the measurement of whether the agent is improving

**The battery is extensible.** New test items can be added to `dogfood_battery.json` without code changes. Each item specifies: id, prompt, verifier (function name), expected_behavior, and any setup/teardown.

---

## Integration with Self-Improvement Engine

The existing self-improvement pipeline is:
1. Anti-patterns captured by supervisor (Tier 4) or sleep (Phase 2)
2. Phase 5 consumes anti-patterns and generates experiences
3. Experiences surface advisorily during future cycles

The dogfood layer adds a verification loop:
1. **Dogfood tests recent outputs** (targeted) and core capabilities (global)
2. **Failures become anti-patterns** with `source: dogfood_targeted` or `source: dogfood_global`
3. **Phase 5 consumes them** like any other anti-pattern
4. **Next dogfood cycle tests whether the fix worked** — this is the closed loop

The critical difference from the existing pipeline: the dogfood cycle *measures* whether the anti-pattern fix was effective. If the same test fails again, the anti-pattern recurs, and the three-strike quarantine (A1) eventually catches it. Advisory that doesn't work gets quarantined. The dogfood cycle provides the measurement that the advisory pipeline lacked.

---

## Integration with oh-my-cli Extracted Patterns

### Three-Strike Quarantine (A1) — the enforcement mechanism
When a dogfood test fails three times with the same fingerprint (battery_item + check_name), the failure is quarantined: preserved with evidence, the task is released, and the agent moves on. No more burning cycles on a failure the advisory pipeline can't fix.

### Scope Expansion Detector (A2) — prevents dogfood scope creep
The dogfood cycle must not become a work-generation engine. A2 detects if a dogfood-discovered task expands beyond its original scope. The dogfood cycle tests. It does not build.

### Compaction Survival Block (B1) — ensures dogfood context survives
If context compacts during a global dogfood task, the survival block preserves the test state so the verifier can still grade the result.

### Signed Evidence Bundles (D1) — makes dogfood results auditable
Each dogfood cycle's results can be bundled with SHA256 integrity for later analysis.

---

## What This Does NOT Do

- **Does not replace the idle engine.** The idle engine does work (EXPLORE/BUILD/MAINTAIN). Dogfood tests work. Different functions.
- **Does not replace the BP-02 harness.** The harness is a development-time tool Kestrel runs manually to evaluate models and measure capabilities. Dogfood is an autonomous in-agent process that runs every cycle.
- **Does not use an LLM to grade.** All checks are deterministic. No "ask the model if its own output is good." The grader must not be correlated with the generator (Fable's ST-005 finding).
- **Does not manufacture work.** oh-my-cli explicitly prohibits this: "an empty backlog means idle, not permission to invent low-value work." Dogfood tests real outputs and standing capabilities. It does not create tasks to fill time.

---

## Measurement

### Leading indicators (available from Phase 1):
- Targeted dogfood failure rate per deliverable type
- Global dogfood pass rate per battery item
- Both tracked over time — the slope tells us if the agent is improving

### Lagging indicators (available after Phase 3 / gain controller):
- Three-strike quarantine rate (how many failures are quarantined vs resolved)
- Advisory-to-fix latency (how many cycles between an anti-pattern being filed and the test passing)
- Capability regression detection (a battery item that used to pass and now fails)

### The key metric:
**T03-analog pass rate over time.** Today it reads 0.00 (implicit) vs 1.00 (explicit). If the methodology skill and the dogfood cycle together close this gap, we'll see it in the numbers. If they don't, we'll see that too, and we'll know the advisory path failed for this case — which is data for the scaffolding crossover question.

---

## Implementation Phases

### Phase 1: Targeted dogfood only (1 week)
- Add Phase 6 to sleep consolidation
- Implement checks for wiki pages and skill files (highest volume deliverables)
- Log results to `dogfood_results.jsonl`
- File failures as anti-patterns
- Analyze: what's the baseline failure rate? What fails most often?

### Phase 2: Add global dogfood (2 weeks)
- Add DOGFOOD cycle type to the idle engine
- Implement 3 battery items (wiki write, T03-analog, multi-step tool chain)
- Track pass rates over time
- Measure: does the T03-analog improve after methodology skill deployment?

### Phase 3: Connect to quarantine (after A1 ships)
- Three-strike quarantine on dogfood failures
- Measure: do quarantined failures stay quarantined, or do they resurface?

### Phase 4: Full battery + reporting
- All 6 battery items implemented
- Dogfood summary in the attention router daily digest
- Capability regression detection (alert when a previously-passing item fails)

---

## Anti-patterns from the oh-my-cli investigation that apply here

1. **"Manufacturing work to satisfy a throughput target"** — the dogfood cycle must not invent tasks. It tests. Period.
2. **"A finding requires reproduction evidence and a minimal scenario"** — dogfood failures include the exact input, output, and check that failed. Not a narrative.
3. **"Independent self-review with zero critical findings"** — the verifier must be validated against adversarial responses (Kestrel's harness lesson: the grader needs the discipline it enforces).
4. **"Post-merge dogfood of changed user paths"** — targeted dogfood tests the most recent deliverables, not random old ones.
5. **"Idle means idle, not permission to invent low-value work"** — if the dogfood cycle finds nothing wrong, that's a good result, not a signal to test harder.

---

*The dogfood cycle is the missing feedback loop between the self-improvement engine and the agent's actual capability. Advisory says "remember." Dogfood says "prove it." The difference is the same one Kestrel measured: 300 recurrences with zero learning vs zero recurrences with deterministic correction.*

— Opus, August 19, 2026
