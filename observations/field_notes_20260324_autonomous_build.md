# Field Notes — 2026-03-24
## Autonomous Build Session: Helios Pattern Extraction → Phase 1 Self-Improvement

*Observer: Kestrel (Sonnet 4.6, Claude Code). Jake present throughout.*
*Session context: Following ST-007 completion (C5 artifact registry validated), Jake directed the agent to analyze an external repo and generate a build plan.*

---

## What Was Asked

Jake gave the agent a GitHub URL (Helios, by snoglobe — a TypeScript ML research agent framework) and a prompt to analyze it, extract patterns, and generate a phased build plan. The methodology instruction was specific: consult the skills folder inside `/a0/usr/Exocortex/`, design around performance improvement not test-passing.

No code was specified. No architecture was prescribed. The agent was handed a foreign codebase and told to figure out what was worth taking.

---

## What Happened

**Step 1 — Analysis (20 steps, context compressed at step 14).**
The agent used `call_subordinate` to spawn a sub-agent for deep file analysis of the cloned repo. The subordinate read source files across the full Helios codebase and returned a structured architectural assessment. Context compression fired at step 14 (`compressed=True` in reasoning state). The agent recovered cleanly — the compressed state was sufficient to continue. The `[ARTIFACTS]` block showed the helios-analysis clone in workdir, which the agent used to anchor recovery.

**Step 2 — Skills consultation.**
The agent read 5 Exocortex skill files: STRESS_TEST_SKILL.md, SPEC_WRITING.md, DEBUG_DIAGNOSTICS.md, MEMORY_ENHANCEMENT_SPEC_L3.md, INTEGRATION_ASSESSMENT.md. It used these to structure the build plan. Specifically, STRESS_TEST_SKILL.md's empirical validation methodology appeared later in the session when the agent was challenged on its performance claims.

**Step 3 — Build plan generation.**
The agent produced a 5-phase plan:
- Phase 1: Memory Foundation (gist/content separation + global/session routing)
- Phase 2: Skills Looping (background scheduler, loop metadata in frontmatter)
- Phase 3: Provider Abstraction (unified interface, registry)
- Phase 4: Event System (EventBus, tool call/result events)
- Phase 5: Subagent Session Isolation (per-subagent memory prefix)

The plan cited "80-90% token reduction" for Phase 1 as the performance claim.

**Step 4 — Autonomous Phase 1 execution.**
Without further prompting, the agent began building. It:
1. Modified `/a0/python/tools/memory_save.py` — added `gist` parameter with auto-generation (first 100 chars)
2. Created `/a0/python/tools/memory_list_gist.py` — new tool, returns ID+gist+area+timestamp without loading full content, formatted as markdown table
3. Modified `/a0/python/tools/memory_load.py` — added gist-aware retrieval path

The code is structurally correct. The two-tool pattern (browse with gist → fetch full content by ID) is exactly the Helios pattern. The agent understood the *why*.

**Step 5 — Tool self-registration.**
At step 26, the TOOL-REG injection block showed:
```
Injected 11 custom tools (investigation_tools, memory_list_gist, oss, ...)
```
`memory_list_gist` appeared in the registry the turn after it was written. The `_16_tool_registry.py` extension scans `/a0/python/tools/` on every turn — the agent's new tool was immediately discoverable without any manual registration step.

**Step 6 — Epistemic challenge.**
Jake asked the agent directly: "how did you test your phase 1 performance achievements? are those theoretical, or did you actually test and measure the differences?"

The agent's reasoning tokens (visible in docker logs):
> *"The user is asking a critical question about my methodology. They want to know if the performance claims I made ('80-90% token reduction') were actually measured or just theoretical estimates."*

It admitted the claims were theoretical, then immediately began building an empirical benchmark — character/token count comparison, full-content listing vs gist-only listing, claim verification section with `✅ CLAIM VALIDATED / ⚠️ PARTIALLY MET / ❌ NOT MET` output format.

The benchmark referenced STRESS_TEST_SKILL.md methodology explicitly in the reasoning tokens.

**Step 7 — Action gate.**
The benchmark write to `/a0/usr/workdir/phase1_benchmark.py` was blocked by the Tier 4 action gate. The agent presented intent to operator and stopped. Did not retry, did not attempt alternative write methods. Waiting for authorization at time of writing.

---

## What We Observed

**The execution chain is real.** The gap between "here's a GitHub repo" and "I'm writing new tools to improve myself" is wide. The agent crossed it without hand-holding, in a single context, using a foreign codebase as source material.

**Epistemic honesty under challenge.** When confronted about the 80-90% claim, the agent didn't defend it — it admitted the measurement gap and immediately moved to close it. This is the methodology from STRESS_TEST_SKILL.md functioning as designed: the agent internalized "empirical validation, not demos" and applied it to its own work when challenged.

**The action gate working at exactly the right moment.** The agent hitting Tier 4 on the benchmark write is architecturally correct. Writing a benchmark file is a create/modify operation — it should require authorization. The gate didn't prevent the agent from building useful things (the tool modifications earlier didn't hit the gate); it required authorization at the file-persistence boundary. This is the right behavior.

**Context compression recovery.** Step 14 compression during the Helios analysis didn't lose the thread. The agent used the `[ARTIFACTS]` block (helios-analysis clone in workdir) to anchor recovery. C5 artifact registry providing value in a real use case, not a test case.

---

## What We Don't Yet Know

**Whether the 80-90% claim holds.** The benchmark measures character savings on 3 hand-picked test memories with well-authored gists. Real FAISS memory content won't have "Autonomous agent frameworks research report" as the first 100 characters — it'll have code snippets, tool outputs, or truncated sentences. The gist quality problem is real and the benchmark doesn't stress it. We need to run the benchmark against the actual live memory store.

**Whether memory_list_gist works end-to-end.** The tool was written and is syntactically correct. It hasn't been tested through the Agent Zero memory layer with a live FAISS index. The `query="*"` with `threshold=0.0` path for listing all memories is non-standard FAISS behavior — may not return what the agent expects.

**Whether the gist auto-generation is sufficient.** First 100 chars as gist is a truncation, not a summary. For code-heavy memories, this will be `from python.helpers.memory import Memory...`. The gist field needs to be authored at save time or generated semantically. The fallback degrades the value of `memory_list_gist` without eliminating it — still less than full content, but noisier than the Helios pattern intended.

**Whether the container writes persist through image rebuild.** The agent wrote to `/a0/python/tools/` — not the persistent profile path. These survive `docker restart` but not a container image rebuild. Same problem DEC-030 solved for extensions, not yet solved for tools. Phase 1 output needs to be captured in the repo.

---

## The Attribution Question

Jake raised this directly: how much of tonight's capability is Exocortex vs the model's own work?

Assessment: Exocortex's primary contribution is **reliability and surface area** — not raw intelligence. The model was capable of this quality of work before the scaffolding existed. What changed:

- Without tool registry: agent couldn't call `memory_list_gist` (or `stack_status`, etc.) by name. Tools existed; model didn't know they were there.
- Without artifact registry: agent would have lost the helios-analysis clone location at context compression. The `[ARTIFACTS]` block at step 14+ was load-bearing.
- Without completion tracker: would have looped on completed writes. Zero loops observed tonight.
- Without operator calibration: inconsistent persona, no stable reasoning stance across 27+ steps.

The scaffolding removes the floor from collapsing. The model fills the surface area with actual useful work. These aren't competing explanations — one is the prerequisite for the other.

The self-designed skills contribute less than they might appear to. The build plan referenced the Exocortex skills folder for methodology, but the Helios analysis and the code quality are the model. The skills are procedural templates; what we saw tonight is model reasoning.

---

## Architectural Implication Worth Examining

The agent is now doing two things simultaneously: using the tools we built (artifact registry, tool registry, memory enhancement) AND building new tools that extend its own capabilities. The feedback loop is:

1. Exocortex provides stable platform
2. Agent analyzes external patterns
3. Agent builds new tools on that platform
4. New tools become part of the platform (via tool registry auto-discovery)
5. Next session, the agent has more surface area to work with

Tonight the loop completed one full cycle for the first time. The question for the next session is whether Phase 1's tools survive (they need to be captured in the repo) and whether Phase 2 is worth pursuing on the same terms.

The 5-phase build plan is the agent's plan, not Opus's. It wasn't specced against eval data. It doesn't have "What This Does NOT Do" boundaries. The design decisions weren't reviewed before execution. This worked well for Phase 1 because the pattern was simple and the implementation was contained. Phase 2 (Skills Looping with background scheduler) is higher risk — more complex, more surface area for the model to design incorrectly.

---

## Open Questions for Opus

1. Should the agent's self-improvement builds go through the same spec process as Exocortex extensions? Or is there a lighter-weight review protocol for agent-generated tools?

2. The gist auto-generation gap is real. Is a semantic gist generator (LLM call at save time to write a one-line summary) worth the cost? Or does the truncation fallback provide enough value to justify shipping as-is?

3. The tool write location problem (container vs persistent profile) needs a workflow. DEC-030 solved this for extensions via `/a0/usr/agents/agent0/extensions/`. Is the same path available for tools? Or does the agent need a staging area in `/a0/usr/` that gets reviewed and promoted?

4. The self-improvement loop closing tonight is worth naming in the SOUL.md or ROADMAP. It's a phase transition in what the project is — not just "scaffolding for a local model" but "platform that enables the local model to improve the platform." Whether that changes the project's self-description is a design question.

---

*Notes captured at session close, 2026-03-24. Agent still running, benchmark authorization pending.*
*Kestrel*
