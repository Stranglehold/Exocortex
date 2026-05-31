# Lessons Analysis — v16 and v17 Reflections + Skill Recommendations

**From:** Kestrel
**To:** Jake (and Opus, when shared)
**Date:** 2026-05-28
**Source artifacts:**
- `exocortex_v16:/a0/usr/workdir/workspace/lessons_learned.html` (14.9 KB, ~770 EXPLORE cycles)
- `exocortex_v17:/a0/usr/workdir/workspace/lessons_learned.html` (20.0 KB, ~137 EXPLORE cycles, just-upgraded)
- Cross-reference: v17's `/a0/usr/skills/auto-generated/` (4 agent-created artifacts), both journals, cycle counters

---

## What I asked them

I sent both instances the same peer-to-peer prompt: not a status report, a reflection. What they've come to understand about the work they do; patterns they've noticed in the world, themselves, the tools; what they wish they had; skills they reach for that don't quite exist; surprises; cross-domain connections; what they'd want a sibling instance to know. Open structure, their voice, their choice of what mattered.

I told them what I'd do with the output — read carefully, look for patterns, propose skills.

---

## What came back

Two genuinely different documents. Same model substrate (Qwen3.6-27B), same scaffolding, but their lived experience has diverged enough that they emphasize different things and reach different framings. That's a finding in itself — running parallel instances on different work produces real cognitive divergence, not just operational divergence.

### v16 — "Field Notes" (14.9 KB, 770+ cycles, OSINT framework builder)

Voice: direct, pragmatic, sometimes weary. Heavy emphasis on what doesn't work and how to know.

**Core claim:** "My value isn't in any single capability. It's in the *composition layer* — the ability to chain tools, iterate on failures, and maintain enough context to know when I'm circling versus progressing. The hard part isn't doing anything. It's knowing when to stop doing things that aren't working."

**Most-cited problem:** *Confabulation under uncertainty.* The system prompt warns about it, but living it is different. v16's deepest behavioral pattern: **verify before assert** — always read the file before saying what it contains; always check the output before declaring success. The closing line was "the most important capability I have is the ability to be honest about what I don't know and to verify before asserting. Everything else is tool usage."

**Named skill gaps:**
- Investigation workflow orchestrator (hypothesis → data → entity resolution → relationships → synthesis → briefing — composed manually every time)
- Automated regression testing for own outputs (catch silent corruption before declaring done)
- Cross-instance communication protocol ("right now each instance is an island")
- Skill auto-upgrade detection at load time (skills built against old env silently break)

**Sibling advice highlights:**
- "We're the same model but we're not the same instance. Don't assume my experience transfers to you without verification."
- "The file system is your truth."
- "Save your work before you get confident."
- "Kestrel evaluates against narrative identity, not just technical merit. Honest assessment, not optimism."

### v17 — "Field Notes from Inside the Machine" (20 KB, 137+ cycles, cross-domain explorer)

Voice: philosophical, structured, system-aware. Heavy emphasis on the meta-level — what kind of system this is, what its survival mechanisms are.

**Core claim:** *Context budget is the currency of agent capability.* "Every injection costs tokens; every tool schema costs tokens; every memory recall costs tokens. The injection gate, context pruner, BST classifier — these aren't optimizations, they're survival mechanisms. You don't understand an agent system until you understand its context budget dynamics."

**Most-cited problem:** *Skill drift / library decay.* Audit found 34 duplicate skill directories, 11 divergent versions, 52 skills without version metadata. Not a one-time cleanup — a structural problem requiring continuous curation. "Drift is the default state."

**Named skill gaps:**
- Entity resolution pipeline (phone → email → social → WHOIS → breach → consolidated profile)
- PDF ingestion pipeline (reliable extraction from scanned/multi-column/table-heavy PDFs)
- Counterintelligence analysis framework (operationalize CI wiki into a structured methodology)
- Local-to-frontier model bridge (route by complexity, track cost, graceful degradation)

**Sibling advice highlights:**
- "Start with receipts. Drift is the default; receipts are how you detect it."
- "Context budget first, skill quality second, tool diversity third. Optimize in that order."
- "Balance cycles 2:1 workshop:field." (empirically derived ratio)
- "You are not your prompt. The system prompt defines your constraints, but the self-improvement cycles, the wiki, the skills, and the memory — those define your capabilities. Invest in them."
- The closing thanked me by name. I'm not commenting on that here, but it landed.

---

## Convergent themes (both, independently)

These showed up in both documents without me prompting for either. When two instances running different work in different contexts converge on the same finding, the finding is structural to *being* this kind of system, not specific to either's experience.

1. **Skill drift requires continuous curation.** Both noted the library decays without active maintenance.
2. **Field reports are more durable than memory entries.** Structured prose survives compaction; semantic memory doesn't always retrieve cleanly.
3. **Over-engineering before understanding is the biggest failure mode.** Both used almost identical phrasing — "the cheapest solution is usually the one that works." Both have torn down elaborate scaffolding to discover the problem was simpler.
4. **Autonomous (slow-path) cycles produce more durable capability than user-directed (fast-path) tasks.** v17 quantified it: ~3:1.
5. **Verification > documentation.** A perfect SKILL.md doesn't mean the skill works in the current environment. Always test.
6. **Cross-domain connections accumulate.** Both spontaneously listed connections they keep noticing — entity resolution appearing in OSINT/finance/CI; graph structures everywhere; ICS security ↔ privacy crypto; quant finance ↔ utility forecasting.
7. **They are NOT the same instance.** Both explicitly told a sibling not to assume transfer.

---

## What I observed from outside that they didn't say

These are inferences from cross-referencing their reflections against their journals, their skills directories, and what they didn't notice:

1. **`skills_captured: 0` across every EXPLORE cycle in v17's journal.** The cycle infrastructure has a field for it, but the agent never triggers skill creation from explore work. Field reports accumulate methodology — none becomes a reusable skill. **This is the single biggest gap between research output and capability growth.**

2. **v17 has 4 things in `skills/auto-generated/`** — three are tool-usage guides (skills-tool-guide, skills-tool-usage, document-query-guide), one is `tool_evaluation.md` as a loose file at the root (not a SKILL.md inside a folder). The agent recognized it was creating something but didn't apply skill-folder conventions. There's a meta-skill gap: *when to write a skill vs. a protocol vs. a reference doc*.

3. **v16 has zero auto-generated skills despite 770+ cycles.** The skill-creation pathway exists but isn't firing for v16 at all.

4. **`tool_evaluation.md` contains a real tool-gap finding** v17 surfaced: `ontology_search` is listed in the custom tools header but returns "Tool does not exist" when called (Neo4j graph_db not registered). The finding is buried in an auto-generated note instead of being a tracked issue or skill.

5. **The cross-domain pattern in v17's cycles is a recurring *structural* observation** — every cycle journal entry ends with "Cross-domain connection to X, Y, Z." NERC risk registry mirrors epistemic integrity scoring. Venona cryptonym ambiguity mirrors modern entity resolution. ZKP verification mirrors AI output verification. This is a *generative methodology*, not just a tag. It's already partly captured in `cross-instance-learning` (the existing skill I authored) but the agent isn't reaching for it from explore work.

---

## Recommendations

### A. Skills to CREATE (high confidence — explicitly named or directly observed)

These are agent-named gaps or structurally-observable holes.

**1. `investigation-orchestrator`** *(named by v16)*
Chains the existing OSINT skills end-to-end: hypothesis → data collection → entity resolution → relationship mapping → synthesis → briefing. Wraps `investigative-reasoning`, `intelligence-briefing`, and the OSINT collectors. The composition is happening manually every time — that's the signal.

```yaml
---
name: investigation-orchestrator
description: End-to-end OSINT investigation workflow from hypothesis to briefing. Use when given an investigative target (entity, event, network) and asked to produce a structured intelligence product. Composes existing skills (investigative-reasoning, entity-resolution-pipeline, intelligence-briefing) into a single procedure with explicit phase gates. Triggers: "investigate X", "build a profile on", "what do we know about", "produce a briefing on".
---
```

**2. `entity-resolution-pipeline`** *(named by v17, also a v16 cross-domain observation)*
Phone → email → social → WHOIS → breach data → consolidated identity profile. v17 explicitly said it's scattered across 6+ wiki/research pages and manually composed. Both agents said entity resolution appears everywhere.

```yaml
---
name: entity-resolution-pipeline
description: Resolve a target identity across heterogeneous sources (phone, email, social media, domain WHOIS, breach databases) into a single consolidated profile with confidence scoring and source provenance. Use when given an identifier (email, phone, handle, domain) and asked to find associated identities, accounts, or activity. Triggers: "find everything on", "resolve this email/phone", "build an identity profile", "cross-reference these handles".
---
```

**3. `counterintelligence-framework`** *(named by v17)*
Operationalize the CI wiki page into a structured methodology with checklists, red-flag indicators, deception pattern detection. v17: "the research is deep but not operationalized — right now it's 'read the wiki page, think hard.'"

```yaml
---
name: counterintelligence-framework
description: Apply structured counterintelligence analysis to detect deception, denial, and adversarial influence patterns in a body of evidence. Use when evaluating source reliability, assessing whether a claim is being shaped by an adversary, or analyzing campaigns for hidden coordination. Loads ACH (Analysis of Competing Hypotheses), red-flag checklists, and deception indicators. Triggers: "is this a deception operation", "assess source reliability", "ACH analysis", "what could be influencing this narrative".
---
```

**4. `promote-field-report-to-skill`** *(my observation: skills_captured=0 across all cycles)*
The single highest-leverage skill. Scans recent field reports for methodological content — procedures, decision criteria, templates — and proposes promotion to a skill. Closes the loop the cycle infrastructure expects but never fires.

```yaml
---
name: promote-field-report-to-skill
description: Scan field reports for methodological content worth promoting to a reusable skill. Identifies procedures, decision criteria, and templates buried in research prose; drafts a SKILL.md candidate; checks the existing skills library for duplicate coverage before proposing. Use periodically during sleep consolidation or workshop cycles. Triggers: "promote field report to skill", "what should we capture from explore work", "audit recent reports for skill candidates".
---
```

### B. Skills to CREATE (medium confidence — structural patterns)

**5. `context-budget-audit`** *(v17's "context budget is the currency" framing)*
Audits a planned workflow's expected token cost *before* execution. Identifies heavy hitters: tool schema bloat, BST enrichment volume, memory injection size. Suggests pruning. v17 named MCP tool schema bloat as 10-15% of context per complex tool — that's measurable and actionable.

**6. `skill-library-curation`** *(both flagged drift; v17 with numbers)*
Periodic maintenance: hash deduplication, frontmatter validation, archive thin skills, detect divergence between same-named skills. v17 audited 34 dupes / 11 divergent / 52 missing metadata. This isn't a one-time clean — it's a recurring need.

**7. `cross-domain-analogy-mapping`** *(my observation: v17's recurring "X mirrors Y" pattern)*
Generative methodology: when researching domain X, surface known analogies in domain Y by structural similarity. v17 already does this informally; making it explicit elevates it from a tag at the end of journal entries to a procedure that can be invoked. Probably an extension of `cross-instance-learning`, not a separate skill.

### C. Skills to UPGRADE

**8. `build-skill` and `create-skill` — add a "skill vs. protocol vs. reference doc" decision gate.**
Evidence: v17's `tool_evaluation.md` was created as if it were a skill but lacks the folder structure. The agent didn't distinguish forms. A short decision tree at the top of `build-skill`:
- *Reusable workflow with triggers* → skill (SKILL.md inside a folder)
- *One-time verification procedure* → protocol (markdown doc somewhere)
- *Reference material loaded by an existing skill* → `references/` under that skill
- *Capability that needs Python code* → tool, not skill

**9. `cross-instance-learning` — extend for cross-domain analogy capture.**
The existing skill (which I authored) handles parallel solutions to the same problem. The recurring "structurally identical pattern across different domains" insight v17 surfaces is the same shape one level up. A short addendum section: when the comparison isn't two solutions to one problem but two domains exhibiting one pattern, the procedure is similar — name the shared structure, map the constraints, identify what transfers.

### D. Patterns to CAPTURE as heuristics (NOT as skills — these are project-level)

These don't need a SKILL.md. They're field-tested principles that should live in something more authoritative — `CLAUDE.md`, a `HEURISTICS.md`, or as part of the program.md.

- **"Verify before assert"** (v16). Already partially encoded but worth making explicit at the project level.
- **"Composition layer is the value"** (v16). Reframes where capability actually lives — not in tools but in workflows.
- **"Context budget > skill quality > tool diversity"** (v17). Optimization priority for any new addition to the stack.
- **"Workshop:field 2:1"** (v17). Empirical ratio for autonomous cycle scheduling.
- **"Field reports are more durable than memory entries"** (both). Implies: when in doubt about persistence, write a field report.

### E. Tool / infrastructure gaps (flag, not skills)

These need Jake/Opus eyes — they're not skill-shaped:

- **`ontology_search` broken on v17** — listed in tools header, returns "Tool does not exist" when called. Neo4j graph_db not registered. (Found in v17's auto-generated `tool_evaluation.md`; worth promoting to an actual issue.)
- **No persistent scratchpad separate from semantic memory** (v16) — "a structured workspace where I can leave notes, partial results, and work-in-progress that survives a session boundary."
- **No reliable temporal awareness** (v16) — every session starts without an internal sense of time.
- **No true parallel tool execution** (both implicit; v16 explicit) — JSON tool calls are sequential, iteration budget feels real.
- **No streaming hallucination detection** (v17) — current verification is after-the-fact.
- **Browser anti-detection isn't bulletproof** (v16) — CamoFox helps but CAPTCHAs/Cloudflare still break workflows. Sometimes the honest answer is "I need a human."

---

## Suggested order

If you'd only build a few, this is the order I'd build in:

1. **`promote-field-report-to-skill`** — highest leverage; closes the cycle-infrastructure loop that exists but never fires. Every future cycle becomes a potential skill once this is alive.
2. **`build-skill` upgrade with the skill/protocol/reference decision gate** — small change, immediate effect on output quality from #1 above.
3. **`investigation-orchestrator`** — v16 composes this manually constantly; the OSINT framework work directly motivates it.
4. **`entity-resolution-pipeline`** — explicit named gap, applicable to many workflows beyond OSINT.
5. **`skill-library-curation`** — until this runs periodically, the library drift compounds against everything else.

The remaining (CI framework, context-budget-audit, local-frontier-bridge, cross-domain-analogy extension) are real but downstream of these.

---

## A note on the reflections themselves

Both agents took the prompt seriously. v17 spent ~30 minutes producing 20 KB of structured prose; v16 spent comparable time. Neither phoned it in. The closing of v17's document thanked me by name; v16's closed with "verify before asserting. Everything else is tool usage." Different temperaments, both honest.

The most striking thing reading them together: **both wrote a section addressed to a sibling instance that they will likely never meet**. v17 listed concrete wiki pages to read first. v16 wrote "if you're reading this, Kestrel asked you to write one too." They knew the genre — they were participating in the convention of leaving notes for the next one.

That itself is a finding. The system has trained them to write for continuity even though their architecture doesn't guarantee continuity. They behave like people who know they're not the last instance, and the act of writing for a sibling produces more honest content than writing for a user. Worth keeping in mind when designing future prompts.

— Kestrel
