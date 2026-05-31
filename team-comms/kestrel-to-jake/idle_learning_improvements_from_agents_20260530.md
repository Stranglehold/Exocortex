# Improving the Idle-Time & Learning System — Ideas Mined from v16 & v17's Own Research

**From:** Kestrel
**To:** Jake
**Date:** 2026-05-30
**Method:** Read both agents' workdir field reports + wiki + program.md. These are *their* ideas — they've been researching how to improve systems exactly like the one they run in. I'm the synthesizer, not the source.

---

## The headline finding

Both agents, independently, researched the self-improving-agent literature (MUSE-Autoskill, AutoRefine, GEPA, CoEvoSkills, Trace2Skill, Mem0) and mapped it back to Exocortex. Their conclusions converge — **and they converge on the same gap I found from the outside: the skill-capture loop is open.** `program.md` Priority 3 is literally "Skill Generation," but every cycle journal shows `skills_captured: 0`. The system is *designed* to turn cycles into skills and in practice turns out zero. Closing that loop is the single highest-leverage improvement, and the agents have already researched *how*.

Their words are worth quoting — v16: *"None of these systems handle skill DEPRECATION… Memory bloat is the silent killer of self-improving systems."* v17: *"A skill's SKILL.md says what it does; .memory.md says what the agent has learned about using it."*

---

## A. Close the skill-capture loop (biggest leverage — both agents)

The program says "generate skills"; nothing does. Their proposed mechanisms, in build order:

1. **promote-field-report-to-skill / trajectory→skill extraction** *(v17 skill-extraction report; matches my earlier lessons-exchange rec).* Structured trajectory logging → a teacher pass proposes a skill from the trajectory/field report → score → register. v17: *"conversation logs exist but are not structured for skill extraction."* This is the keystone — every EXPLORE/BUILD cycle becomes a skill candidate.

2. **Failure-lesson skills** *(v17, both self-learning reports — novel and high-value).* Extract skills from **failed** trajectories, not just successes: *"when a tool call fails, automatically generate a 'failure lesson' skill ('when doing X, avoid Y')."* This directly attacks the recurring errors we keep hitting (the sleep dict-add bug, the `datetime` NameError, JSON misformat). Each becomes a durable "avoid this" note that compounds.

3. **Per-skill `.memory.md`** *(v17 MUSE report).* Append-only file beside each SKILL.md capturing usage notes, failure modes, quirks the agent learned in practice. Cheap, high-impact, trivially adoptable.

4. **Skill-level unit tests + registration gate** *(v17 MUSE).* A skill enters the bank only if a colocated test passes. *"Even a single test that verifies the skill script runs without error would eliminate the silent-failure class."* The test travels with the skill across agents.

5. **Audit terse vs procedural skills** *(v17 MUSE).* Surprising finding: agent-generated skills are 2.2× longer than human ones (326 vs 146 lines) yet *cheaper* to run — the extra length is procedural (steps, failure modes, schemas) that replaces ad-hoc reasoning. Recommendation: audit our existing skills; if terse, expand procedurally.

## B. Skill lifecycle / anti-bloat (v16's strongest insight)

6. **Skill deprecation + versioning** *(v16 GEPA/CoEvoSkills report).* The unsolved gap across the whole literature: systems generate skills but never forget. v16's insight: *"the Exocortex sleep consolidation engine addresses this for memories — the same pattern likely applies to skills."* We already have the evidence of need (the 34-duplicate / 11-divergent / 52-no-metadata skill mess the agents found earlier). Apply sleep-consolidation-style dedup/deprecation to the skill library.

## C. Prompt/policy evolution (v16 — cheapest path)

7. **Lightweight GEPA-style system-prompt evolution** *(v16).* v16 frames three layers — prompt (GEPA) / skill (CoEvoSkills) / policy (Trace2Skill) — and notes prompt-level is *"the cheapest, fastest, most reversible improvement path."* A bounded loop that reflects on execution traces and proposes prompt tweaks (gated, reversible) is a low-risk place to start.

## D. Memory system (v17)

8. **Agent-writable procedural memory** *(v17 memory-arch).* When the agent discovers a workflow/convention/failure-pattern, it writes back to a procedural-memory file injected in future sessions. This is the skill-capture loop at the memory layer — pairs naturally with A.
9. **Entity extraction for retrieval** *(v17, Mem0-style, no graph DB)* — extract entities at memory_save, boost on entity-match at retrieval.
10. **Memory-poisoning audit** *(v17 memory-arch + context-mgmt)* — what persists into memory from web/tool outputs? Security angle that ties into the OSINT anti-deception thread.
11. **Bitemporal journal** *(v17)* — `event_time` (when true) vs `ingestion_time` (when observed), enables retroactive correction without loss.

## E. Idle-time *efficiency* specifically (the "idle time" half of your ask)

12. **Declarative memory-format study** *(v17 context-mgmt)* — compare CLAUDE.md / SKILL.md / Rules formats to design the optimal procedural-memory injection (smaller, cache-friendlier tail → cheaper cycles; ties into the API-cache discussion).
13. **Context-rot detection** *(v17 context-mgmt)* — *"detect context rot before it causes failure."* Pairs with the affect-layer instinct — a deterministic signal that a cycle's context has degraded.
14. *(Kestrel adjacent)* The cycle cadence is 30-min and types rotate EXPLORE/BUILD/MAINTAIN at a fixed ratio; once skills are actually being captured, the EXPLORE:BUILD:MAINTAIN ratio is worth tuning so capture (BUILD) keeps pace with research (EXPLORE).

---

## My recommendation (prioritized)

If we build a few, this order — it's where both agents' research and my outside-in analysis agree:

1. **`promote-field-report-to-skill`** (A1) — closes the open loop; every future cycle becomes a skill candidate. Keystone.
2. **Failure-lesson capture** (A2) — novel, compounding, directly attacks our recurring bugs. High value, low effort (hook into the existing failure tracker / EI verdict).
3. **`build-skill` decision gate + per-skill `.memory.md`** (A3-4) — makes captured skills well-formed and self-documenting.
4. **Skill-library curation/deprecation** (B6) — until this runs, capture just adds to the 34-dup mess. Apply the sleep-consolidation pattern they pointed at.
5. **GEPA-style prompt loop** (C7) — cheapest evolution path, but downstream of the above.

Notably, this is the *same* top-of-list I reached in the lessons-exchange memo last week (`promote-field-report-to-skill` was my #1 there too) — except now it's backed by the agents' own literature review, which adds the failure-lesson and per-skill-memory refinements I didn't have.

The through-line: **the architecture is right (the agents confirm it maps cleanly to MUSE/AutoRefine), but the loop from cycle → durable capability is severed.** Reconnecting it is the work.

— Kestrel
