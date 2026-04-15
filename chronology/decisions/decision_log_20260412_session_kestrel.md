# Decision Log — Session 2026-04-12 (Kestrel)

---

**DEC-031: Structural Gate Discipline for Implementation Sessions**

- **Decision:** Treat verification checkpoints as structural gates, not optional checks. A phase cannot report completion until its gate conditions are cleared. The three mandatory gates for any deployment task are: (1) syntax check passes, (2) symbols verified in container, (3) acceptance criteria confirmed in logs or output — not inferred from intermediate signals.
- **Rationale:** Derived from the goal gate pattern in StrongDM Attractor (https://github.com/strongdm/attractor). Attractor marks certain nodes `goal_gate=true` — the pipeline cannot exit without reaching them. The analogous failure mode in Kestrel sessions: reporting "deployed" after `docker cp` exits 0 without confirming the extension loaded, the class exists, and the log tag appears. This is the same completion-stall pattern Item 3 detects in the agent — finishing the work but failing to reach the response tool. The structural fix is the same: make the gates non-skippable rather than detecting post-hoc that they were skipped.
- **Concrete gates by task type:**
  - *Deploy extension*: syntax check → deploy → pycache cleared → symbol verified in container → log tag appears on next agent turn
  - *Fix bug in running code*: reproduce → apply fix → verify fix reaches target (importlib.reload if runtime-cached) → confirm corrected behavior in output
  - *Write new function*: implement → unit-level verification (does it produce expected output on known input?) → integration-level verification (does it behave correctly in the full system?)
- **Rejected alternative:** Treating verification as "good practice to remember." Good practice that isn't enforced degrades under time pressure. The structural version is: write the gates down before starting, don't mark the task done until each gate is cleared.
- **Source:** StrongDM Attractor `goal_gate=true` node pattern. Session 2026-04-12.
- **Revisit if:** A task type emerges where mandatory verification gates would produce worse outcomes than omitting them (e.g., rapid iteration during exploration where the cost of strict verification exceeds the benefit). Even then, the gate should be explicitly waived, not silently skipped.

---

**DEC-032: Phase-Aware Context Management (Fidelity Modes)**

- **Decision:** Different phases of implementation work require different context granularity. Explicitly identify the current phase before starting work and carry only the context that phase needs. Three phases with distinct fidelity requirements:
  - *Design/reading phase* — full fidelity: spec, architecture context, adjacent files, prior decisions
  - *Implementation phase* — medium fidelity: the specific file(s) being changed, the immediate spec section, pattern source
  - *Verification phase* — low fidelity: acceptance criteria only, log output, the specific assertion to check
- **Rationale:** Derived from Attractor's fidelity mode concept (full/compact/truncate per-node context management). During a long session, context from the design phase (full spec, architecture discussion, adjacent files) accumulates in the implementation phase where it provides no additional signal and consumes context window. During verification, only the acceptance criteria and the log output matter — carrying full spec context into this phase wastes tokens on content that cannot affect whether the log line appears. The current approach carries whatever seems relevant without explicit phase awareness. Making the phase explicit makes the fidelity decision deliberate.
- **Concrete application:** Before reading files, identify: am I in design phase (need full context), implementation phase (need focused context), or verification phase (need only acceptance criteria)? In verification phase, stop reading spec files. Read the log output. Compare against the acceptance criteria. That's the complete verification context.
- **Connection to Item 4 (Progressive Context Summarization):** When designing the context preserver extension, consider assigning fidelity modes to HTN steps rather than firing once at 70% fill. A long research step should carry full context. A verification step should carry only the checkpoint.
- **Source:** StrongDM Attractor fidelity mode concept. Session 2026-04-12.
- **Revisit if:** Session analysis shows that narrow-fidelity verification is missing relevant context that would change the verdict. (If it is, the acceptance criteria in the spec were incomplete, not the fidelity approach.)

---

**DEC-034: Idempotency Discipline for Implementation Steps**

- **Decision:** Before any file write, deploy command, or external state change, ask: "if this runs twice, what happens?" Every step in a multi-step implementation should be safe to retry without producing corrupted state.
- **Rationale:** Derived from durable execution research (Temporal.io, Restate). The core problem: when a multi-step implementation partially fails (file written, cache cleared, deploy failed), recovery requires knowing which steps actually completed and whether retrying them is safe. Without idempotency discipline, retrying a step that already completed can corrupt state. With it, retry is always safe.
- **Concrete patterns:**
  - *File write*: Check content hash before writing. If existing hash matches new content, return "no_change" — don't overwrite. This prevents double-writes from corrupting partially-edited files.
  - *Deploy command*: Use deployment IDs or session tokens as idempotency keys. If a deploy command is retried, the system should detect the duplicate and skip or return the prior result.
  - *Config edits*: Always read-merge-write (this was already in the playbook). The read step is the idempotency check.
  - *pycache clear*: Inherently idempotent — clearing an already-cleared cache is a no-op.
- **Companion pattern:** Register the compensation (undo) before executing the forward step. For a file write: know what the restore path is before writing. For a deploy: know what the rollback command is before deploying. The compensation is part of the plan, not an afterthought when things fail.
- **Source:** Temporal.io durable execution architecture. Saga pattern for distributed systems. Research session 2026-04-12. `chronology/decisions/decision_log_20260412_session_kestrel.md`
- **Revisit if:** A task type exists where idempotency checking has higher cost than the risk of a bad retry. (Probably not in this codebase — all writes are to local files or the container, both cheap to verify.)

---

**DEC-035: Pre-Mortem Gate for Multi-Step Implementation**

- **Decision:** Before starting any implementation task with more than 5 steps, explicitly enumerate: (1) what failure looks like at each step, and (2) how that failure would be detected. Write this before the first line of code. The pre-mortem is a gate, not a retrospective.
- **Rationale:** P(full success) = (per-step accuracy)^n. At 95% per-step accuracy across 10 steps, P(success) = 0.60. At 12 steps, 0.54. The compounding is faster than intuition predicts. Every unnecessary step added to a plan is not a small overhead — it's a reduction in the probability of successful completion by a factor of per-step accuracy. The pre-mortem gate makes the compounding visible before steps are committed to, forcing step count minimization as part of the plan. It also changes what counts as "implementation drift" — drift is identifiable against the pre-mortem's stated failure modes, not inferred post-hoc from unexpected output.
- **Concrete application:** For each phase (e.g., implement extension / deploy / verify), state: "This phase fails if [condition]. It fails silently if [condition]. I detect failure by [signal]." The set of failure signals IS the verification plan. DEC-031's gates are derived from this pre-mortem output — the gates are the failure signals, made non-skippable.
- **Rejected alternative:** Treating multi-step error compounding as an argument for more careful execution of each step. The bottleneck isn't step execution quality — it's step count. Minimizing steps and knowing the failure signature before starting is more effective than optimizing individual steps.
- **Connection to DEC-031:** DEC-031's structural gate discipline defines the gates. DEC-035 defines why those gates are non-optional (compounding error rates) and adds the step-count minimization discipline as a pre-plan gate.
- **Source:** SWE-bench multi-agent reliability research. P(success) = accuracy^n analysis. Research session 2026-04-12.
- **Revisit if:** Research shows per-step accuracy is uncorrelated with step count in well-structured plans (would change the calculus significantly).

---

**DEC-036: Verification-Within-Generation (ReVeal Pattern)**

- **Decision:** Every spec should include an "agent self-test" step inside the implementation sequence, not only as a final acceptance gate. The agent generates a verification test for what it just wrote, runs it, and must pass before advancing to the next phase.
- **Rationale:** Derived from the ReVeal framework (SWE-bench research, 2026). ReVeal inserts test generation into the code generation loop: write code → generate test → run test → revise if fail → advance if pass. This converts acceptance criteria from post-hoc reviewer checklist to structural gate the agent enforces on itself. The failure mode it addresses: the agent's text signals completion ("implementation complete") but the code doesn't pass the spec's acceptance criteria. Without a self-test step, this failure is invisible until the human reviewer checks. With a self-test step, it's caught inside the loop.
- **Concrete application in spec writing:** Every spec implementation sequence should include: `Step N: Generate a minimal test that would pass only if [specific acceptance criterion] is satisfied. Run the test. If it fails, revise and re-test. If it passes, advance.` The test is generated by the implementing agent, not provided by the spec — this forces the agent to operationalize the acceptance criteria rather than just read them.
- **Scope:** Applies to code generation. Not required for documentation or config changes where the acceptance criterion is structural (file exists, key present) rather than behavioral (code produces expected output).
- **Connection to DEC-033:** DEC-033's spec completeness gate requires observable acceptance criteria. DEC-036 requires that the spec also include a self-test step that operationalizes those criteria. Together: criteria are observable (DEC-033) AND the agent generates a test that operationalizes them (DEC-036).
- **Rejected alternative:** Relying on the final verification gate (DEC-031 step 5) to catch failures. The final gate catches them — but after the full implementation cycle is complete. The self-test step catches them earlier, reducing rework cost. The cost of the self-test step is minimal; the cost of rework after a failed final gate is significant.
- **Source:** ReVeal framework. SWE-bench top agent analysis. Research session 2026-04-12.
- **Revisit if:** Self-test generation proves unreliable (agents generate tests that pass the wrong thing). If so, the spec should provide test stubs rather than requiring full agent generation.

---

**DEC-037: Context Surgery for Loop Breaking**

- **Decision:** Breaking a behavioral loop requires modifying the conversation history, not adding to it. The intervention must operate *on* the channel, not *through* it. Graduated three-tier response: (Tier 1) warn — inject corrective message into history; (Tier 2) summarize — remove loop turns and replace with a single neutral diagnostic statement; (Tier 3) reset — force the response tool with whatever progress exists. The circuit breaker must trip; it cannot merely light up.
- **Rationale:** Derived from BV Operational Test Suite Session 049 — Qwen 3.5-35B looped for 43 turns with the loop detector firing repeatedly without breaking the cycle. A container restart (cleaning conversation history only — same model, same profile, same task) produced a clean result immediately. The conversation history was sustaining the loop, not the model's capability. This is the feedback microphone problem: adding "please stop doing X" into a context dominated by 43 examples of X amplifies rather than corrects. The correction must operate on the channel. Additionally confirmed by the March 25, 2026 incident in which a Qwen3.5-27B agent looped on a Python syntax error for 20+ turns.
- **Three known defects in context surgery implementation (from Loop Recovery and Memory Surgery Design Note):**
  1. *Wrong incision point* — surgery cuts at first detected loop turn, but observable drift precedes formal detection by several turns. Cutting at detection removes the symptom but leaves the onset.
  2. *Summary placement* — replacement summary injected at tail of history via `hist_add_warning()`. Pre-loop progress context ends up in the middle where positional attention bias (Liu et al., TACL 2024) de-emphasizes it.
  3. *Summary primes the failure* — current Tier 2 message describes what was removed ("N consecutive tool failures removed"). Any token semantically adjacent to a failure pattern primes that pattern's retrieval. The summary should acknowledge surgery occurred without naming the failure type.
- **Memory surgery is the companion problem** — context surgery without memory surgery leaves the agent vulnerable to re-entering the loop via memory recall. Loop-period memories (written by selective memorizer during each failed turn) form a dense semantic cluster that gets retrieved on the next turn, reconstituting the loop through the memory layer. This is Einstellung through the memory layer. The complete solution is atomic rollback across both context history and memory store simultaneously.
- **Source:** Loop Feedback Cascade Design Note (Session 049), `chronology/design_notes/design_08_20260305_loop_feedback_cascade.md`. Loop Recovery and Memory Surgery Design Note (March 2026), `specs/LOOP_RECOVERY_AND_MEMORY_SURGERY_DESIGN_NOTE.md`.
- **Numbering note:** Opus proposed this as DEC-031 in the April 12 review response. DEC-031 through DEC-036 were already assigned this session. Assigned DEC-037.
- **Revisit if:** A mechanism is found that can modify the model's attention weights directly rather than modifying the conversation history — that would be context surgery at a lower level without the positional bias constraint.

---

**DEC-033: Spec Completeness Gate**

- **Decision:** Before starting implementation on a spec, verify that the spec contains: (1) explicit acceptance criteria — specific, observable, not "the feature works"; (2) a pattern source — an existing file to pattern-match against; (3) all design decisions made — no "decide how to handle X" left open. If any of these are missing, flag the gap to Jake rather than filling it autonomously.
- **Rationale:** The Kestrel/Opus division of labor depends on specs making all design decisions. When a spec is incomplete, the implementation model either (a) makes design decisions it shouldn't, or (b) produces code that doesn't match what Opus intended. Both are worse than pausing. The completeness gate is a pre-flight check before the first line of code is written. This is the spec-level equivalent of DEC-031's structural gate discipline — applied earlier in the workflow.
- **The three gaps that most commonly cause implementation drift:**
  1. Acceptance criteria are vague ("the extension should inject skills") rather than observable ("log shows `[SKILL-SUGGEST] Injected N skills for domain X`")
  2. Pattern source not specified — implementation model chooses an arbitrary file to pattern-match and introduces inconsistencies
  3. Config/path constants not specified — implementation model makes up reasonable-sounding paths that don't match the actual container layout
- **Source:** Synthesized from observed implementation drift patterns across Exocortex sessions. Crystallized by Attractor's NLSpec approach which demonstrates that specification completeness directly determines implementation reliability. Session 2026-04-12.
- **Revisit if:** A spec that passes the completeness gate produces implementation drift anyway — that would indicate a fourth gap type not currently captured.
