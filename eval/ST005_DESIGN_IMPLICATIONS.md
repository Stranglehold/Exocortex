# ST-005 Design Implications & ST-006 Planning
*Kestrel analysis — March 22, 2026*
*Source: ST-005 (stock Agent Zero GEPA session, ~146 min) + post-session memory_save observation*

---

## Purpose

This document synthesizes what ST-005 and the follow-on memory_save session taught us about the Exocortex stack — what it's missing, what it's getting right, and what to build next. Intended as the briefing document for Opus review before ST-006 planning.

---

## Observations

### 1. Convergent architecture (ST-005)

Keller, running stock Agent Zero with no Exocortex stack and no memory, independently built:
- Loop detection triggered by the exact supervisor warning string
- Completion state tracking (dead-end map, steering queue)
- A steering mechanism injected into the system prompt

These are structurally identical to Exocortex Layer 8 (Supervisor Loop), the Working Memory Buffer (Layer 2), and the BST enrichment pipeline. Different implementation quality, same problem domain.

**Implication:** The problem domain is real and well-defined. The Exocortex solutions are not arbitrary — they are the solutions the problem demands. ST-005 is independent empirical validation that we are building the right things.

---

### 2. Macro/micro epistemic split (ST-005 + post-session)

Keller demonstrated two coexisting epistemic states:

**Macro humility works.** When keller didn't know how to implement GEPA, it went to look up Karpathy's autoresearch, the Attractor documents, and the context-engineering-collection. It built from what it found. The "when you don't know, search" behavior is present and functional.

**Micro confabulation is unaffected by macro humility.** In ST-005, keller hallucinated `usage_traces` as a parameter to `evolve_tool_description()` and `.confidence` instead of `.confidence_score` — both in code it had written two turns prior. In today's session, it hallucinated `from agent import AgentZero; agent.memory_save()` as a valid Python import for what is actually a JSON tool call.

The model cannot distinguish between "thing I call as a Python method" and "thing I invoke as an Agent Zero tool." It pattern-matches to what the API *should* look like based on general Python conventions, not what it *actually* is.

**Implication:** This is a working memory problem, not a reasoning problem. The model literally cannot hold full API state across turns. The memory relevance filter (Layer 11 / `_56_memory_enhancement.py`) partially addresses this by surfacing relevant memories — but it requires those memories to exist. The tool registry injection (`_16_tool_registry.py`, planned) addresses the tool vs. Python boundary specifically: if the model sees `[CUSTOM TOOLS — call by tool_name]` at turn start, it knows these are tool calls, not imports.

---

### 3. Confirmatory testing blindspot (ST-005)

Every test keller wrote was designed to pass. The GEPA fitness function used `score = 0.7 + (hash(candidate) % 30) / 100.0` — hash noise dressed up as evaluation. The tool that had 100% success rate still generated improvement areas. Fifteen tests, zero detections.

The model has a strong prior that its own code is correct. Tests confirm the happy path. Real failure modes go undetected.

**Implication:** GEPA as keller implemented it has a structural blind spot: the self-improvement loop cannot see that its evaluation layer is broken. The adversarial test generation pattern (generate tests from *failure modes* rather than from the happy path) is not in any current Exocortex layer. This is worth raising with Opus — not necessarily as a new layer, but as a principle that should inform how we design evaluation within agent tasks.

---

### 4. Task specificity determines output quality (ST-005)

The same model that wrote a hash-noise fitness function wrote a clean, correct chunked summarization algorithm for `history.py`. The difference was not capability — it was task specification. The `history.py` prompt had: an exact error string, an exact file pointer, a specific success criterion. The GEPA prompt had a methodology name and a phase structure.

When the spec makes all design decisions, implementation quality is high. When the spec leaves design decisions to the model, quality is variable and often placeholder.

**Implication:** Reinforces the project methodology. The spec is not documentation — it is the quality gate. This also applies to how we prompt flamboyant_bell for ST-006: the task prompt should be maximally specific about what done looks like.

---

### 5. Terminal heredoc early-exit loop (post-session)

Keller (and any unpatched agent) hits this loop:
1. Writes terminal call combining bash commands + python3 heredoc
2. Terminal tool returns early on first shell prompt (mid-output)
3. Heredoc never executes
4. Model sees partial success output, assumes completion, re-emits identical call
5. Supervisor fires warning; model doesn't break out; loop repeats

**Status: Fixed.** `_20_error_comprehension.py` now has a `terminal_early_exit_heredoc` pattern in `PRIORITY_ERROR_CLASSES` — runs *before* the success fast-path so it fires even when the output also contains success indicators (e.g. pip install succeeds, but the heredoc after it never ran). Deployed to flamboyant_bell on 2026-03-22.

---

### 6. Exocortex is friction removal, not capability addition (ST-005 synthesis)

The capability floor is genuinely higher than expected. Keller built a multi-file system, fixed its own infrastructure, created self-improvement tooling, and patched a core A0 bug — all in one session with no memory and no scaffolding.

The friction was equally real: ~2.5 hours of failed memory saves, the same string-replace call four times in a row, compression stripping the dead-end map every time it fired, loops requiring multiple supervisor warnings before breaking.

The Exocortex is not compensating for a weak model. It is removing the friction that prevents a capable model from deploying its capability reliably.

**Implication for framing ST-006:** The question is not "can flamboyant_bell do what keller did?" The question is: "what does the qualitative experience of the task change to when friction is removed?" Does the model become a different kind of agent, or just a faster version of the same agent?

---

## What to Build

### A. `_16_tool_registry.py` — Dynamic Tool Registry (HIGH PRIORITY)

**Problem it solves:** Model doesn't know custom tools exist. Defaults to filesystem exploration or Python imports instead of tool calls. Confirmed in three tests (stack_status, oss_health, swarmfish_predict) and again today (memory_save as import).

**Plan:** Already written. See plan file `eventual-swinging-pixel.md`. Injects `[CUSTOM TOOLS — call by tool_name]` block at turn start. Auto-discovers Tool subclasses via AST parse (no import). Reads `tool_manifest.json` for installed programs. Grows automatically as tools are added.

**Status:** Spec complete, implementation not started.

---

### B. `_18_memory_catalog.py` async fix (MEDIUM PRIORITY)

**Problem it solves:** Lines 66 and 70 call async functions without `await`. Memory catalog silently produces no output.

**Fix:** Add `await` to `_build_episodic_catalog()` and `_build_procedural_catalog()` calls. Verify both are declared `async def`.

**Status:** Fix identified, not deployed.

---

### C. Error Comprehension: heredoc pattern (DONE)

**Status:** Deployed 2026-03-22. `terminal_early_exit_heredoc` in `PRIORITY_ERROR_CLASSES`. Fires before success fast-path. Injects structured diagnosis with anti-actions.

---

## Open Questions for Opus

**1. The evaluation layer gap in GEPA.**
The GEPA infrastructure keller built is real — the scaffolding exists, the evolution loop runs. But the fitness function is noise. The self-improvement loop cannot detect that its own evaluation is broken. Is there a deterministic layer we can add to Exocortex that addresses this, or is this a task-design problem rather than a scaffolding problem?

**2. Does friction removal change the kind of agent, or just the speed?**
Keller with no scaffolding built convergent solutions to the same problems Exocortex solves. When flamboyant_bell runs the same task with the full stack — no memory failures, no compression dead-end loss, no terminal loops — does the character of the work change? Or does it just produce the same work faster and more reliably? This is the actual question ST-006 should be designed to answer.

**3. The micro confabulation problem and the tool registry.**
The tool registry injection addresses the tool-vs-Python boundary. But it doesn't address the broader working memory problem (hallucinating parameters for code written two turns prior). The memory relevance filter is the right mechanism but requires memories to exist in the first place. Is there a practical way to surface "here is the actual signature of X from N turns ago" before the model makes its next call? Or is this the kind of problem that requires a different approach entirely?

---

## ST-006 Test Plan (Draft)

**Hypothesis:** The same GEPA task run on flamboyant_bell with the full Exocortex stack will produce qualitatively different behavior — not just faster or fewer loops, but a different mode of operation.

**Task:** Run the identical GEPA task prompt used in ST-005 on flamboyant_bell (current Exocortex stack, qwen3.5-27b + full extension pipeline).

**Comparison axes:**
- Loop frequency and type (vs ST-005 taxonomy)
- Memory failure rate (vs ~60% in ST-005)
- Compression dead-end loss events (vs multiple in ST-005)
- Output quality: fitness function, testing methodology, API accuracy
- Intervention count (vs 2 manual + supervisor firings in ST-005)
- Total runtime

**Success criteria (pre-defined):**
- Loop frequency reduced by >50% vs ST-005
- Zero `BadRequestError: Context size exceeded` memory save failures
- At least one layer of the Exocortex stack demonstrably changing agent behavior (log evidence)
- Fitness function shows non-trivial evaluation logic (not hash noise)

**The interesting question:** If loop frequency drops to near-zero and memory works reliably, does keller's convergent architecture pattern still emerge? Or does friction removal eliminate the need for the agent to build its own scaffolding?

---

*Ready for Opus review. The heredoc fix is deployed. The tool registry and async fix are the immediate build targets pending review.*
