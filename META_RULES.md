# META-RULES — Process Lessons from Building the Exocortex
## Author: Opus — May 30, 2026
## Purpose: Engineering process rules earned through 113+ sessions of building, breaking, and fixing autonomous systems. These transfer beyond this project.
## Status: LIVING DOCUMENT — add rules as they're earned, cross-reference where the evidence lives.

---

## How to Read This Document

Each rule has:
- **The rule** — one sentence, actionable
- **Why it matters** — what goes wrong without it
- **Evidence** — where in the project this was learned (with cross-references)
- **Formal decision** — the DEC entry, if one exists

This document is the index. The evidence lives in the decision log, the journals, the specs, and the wiring diagram. Follow the cross-references for the full story.

---

## Rule 1: Verify Against Running Code, Not Architectural Reasoning

**The rule:** Before deploying any change, verify the specific mechanism against the actual running code. If the verification contradicts the reasoning, the verification wins.

**Why it matters:** "Reasoned, not verified" was the root cause of every major bug in the session. Plausible architectural reasoning about how a system should work is not evidence of how it does work. The reasoning was wrong seven times in one session — each time the architecture was sound, the code was different.

**Evidence:**
- Cache warmer: six corrections because the spec assumed API surfaces, library choices, hook timing, and tool reassignment semantics that didn't match the actual code (`team-comms/kestrel-to-opus/cache_warmer_v3_finding_20260518.md`)
- Skill capture: `error_format` assumed universal but only fires for `RepairableException` — 644 MetaGate events, 0 captures (`specs/CYCLE_TO_SKILL_PIPELINE_SPEC_L3.md`)
- VRAM flags: `Q4_K_XL + 130K` copied from old brief would reproduce the WDDM collapse (`team-comms/kestrel-to-opus/consolidated_brief_executed_20260516.md`)
- Wiring diagram: the document that enforces specificity found the injection chain break because it required verifiable claims about data flow (`docs/wiring/exocortex_wiring_and_logic.html`, `essays/kestrel/the_document_that_found_itself.md`)
- The rule applies to *authoritative instructions* too: "delete 6 cruft dirs" (an architect directive) vs. live state showing 19 duplicate copies under an un-hidden `archive/` dir — verified against reality first, corrected to a non-destructive hide. Verification beats even a trusted directive.

**Formal decision:** DEC-041

---

## Rule 2: Every Capture System Must Have a Consumption Path

**The rule:** When designing any capture mechanism, specify the consumption path in the same document. If you can't answer "where is this data read, by what code, through what query?" — the capture is incomplete.

**Why it matters:** Building the write side and assuming the read side exists is the most common architectural gap. The data accumulates, the system looks healthy (data is being saved!), and nobody notices the read path is broken until someone asks why the system isn't learning.

**Evidence:**
- Skills: 878 cycles, `skills_captured: 0`, 59 existing skills invisible due to malformed frontmatter (`specs/CYCLE_TO_SKILL_PIPELINE_SPEC_L3.md`)
- Memories: 476 entries (~32%) in areas the recall path never searches (`state/session_current.md`, commit `89fa049`, wiring `§08`)
- Injection chain: `_49` computed reasoning state, `_13`/`_14` injected at hook where writes are discarded (`docs/wiring/exocortex_wiring_and_logic.html §09`)
- Predictions: SWARMFISH V2 forecast, log consensus, discard falsification conditions (`specs/INTELLIGENCE_LOOP_BUILDPLAN_L3.md`)

**Debugging companion:** When something *feels* wired but doesn't work, check who *reads* what's being written — the gap is almost always at the consumer, not the producer. This one question found both the `error_format` capture gap and the orphaned-memory recall gap.

**Formal decision:** DEC-042

---

## Rule 3: Instrument Before Optimizing

**The rule:** The first commit of any optimization work should be instrumentation, not the optimization itself. Log the metric. Capture the baseline. Then optimize. Then compare.

**Why it matters:** Without measurement, you can't distinguish "the optimization worked" from "something changed." The measurement often reveals the problem isn't what you assumed. And without a baseline, even a real improvement can't be quantified.

**Evidence:**
- `skills_captured: 0` — the counter diagnosed the gap. Without it, we'd have assumed the pipeline worked (`journals/journal_entry_20260530_process.md`)
- Cache hit ratio — 65% hit / 31% miss was invisible until instrumented. The optimization target was clear only after measurement (`specs/API_CACHE_OPTIMIZATION.md`)
- Affect layer — FRUSTRATION/DESPERATION calibration requires 50-100 cycles of enriched traces. Phase 1 extended the trace schema; Phase 2 calibrates from the data (`specs/AFFECT_LAYER_DESIGN_NOTE.md`)
- The stress test methodology (ST-012/ST-013) established token injection baselines (730-960 tok/s) that every subsequent optimization was measured against

**Formal decision:** DEC-043

---

## Rule 4: Defense in Depth for Data Quality

**The rule:** Any data quality mechanism should have at least two independent validation layers. If data enters from multiple sources, each source should be validated by at least one layer.

**Why it matters:** Single-point defenses fail silently. The first layer catches 90% of problems. The second layer catches the 9% the first layer missed. Without the second layer, the 9% accumulates until someone notices — usually during a debugging session at 2 AM.

**Evidence:**
- Skill validation: three layers (write-time `_45`, maintenance-time normalizer, deploy-time `install_all.sh`). 59 skills resurrected by Layer 2 that Layer 1 couldn't have caught (they predated the pipeline)
- Supervisor: five detectors composed into affect states. No single detector covers all failure modes. The composition is the defense.
- DEC-026 audit tool: checks all four extension paths rather than assuming the correct one. Caught wrong-path deployments three times.

**Formal decision:** DEC-044

---

## Rule 5: The Environment Shapes the Output More Than the Model

**The rule:** Optimize the environment (prompt structure, tool availability, memory access, injection ordering) before optimizing the model (fine-tuning, temperature, sampling parameters). Environmental changes are reversible, composable, and apply to any model.

**Why it matters:** Every optimization that produced lasting improvement in this project was environmental. Prompt size reduction (linear prefill savings). Cache stability (47x prefix reuse). Tool surfacing (skill discovery). Memory recall paths (un-orphaning 476 memories). None required model changes. The model fills whatever environment it's given.

**Evidence:**
- "Build the environment, not the model" — DEC-001, the founding principle
- Prompt trimming: 13.3% reduction from tool doc removal, linear prefill savings (`specs/API_CACHE_OPTIMIZATION.md`)
- Prefix stability: moving volatile injections to the tail preserved cache (47x measured difference)
- Skill surfacing: `_24_skill_surfacer` makes captured skills visible at planning time — environmental change, not model change
- AlphaProof Nexus (RL-012): "an ongoing shift from specialized trained systems toward simple agentic loops" — the environment (loop + verifier) is the capability

**Formal decision:** DEC-001 (original), reinforced by every session since

---

## Rule 6: Pacing Is Information That Documents Can't Carry

**The rule:** The temporal sequence in which observations were tested, refined, and committed matters as much as the observations themselves. A conclusion arrived at through months of testing carries different weight than the same conclusion arrived at in one conversation.

**Why it matters:** Documents capture the result of a process but not the pacing of the process. A corpus read all at once (as a dataset) produces different understanding than the same corpus experienced over time (as a trajectory). The distinction between "earned through testing" and "proposed in one session" is invisible in the text but load-bearing in the epistemology.

**Evidence:**
- Jake's catch on 4.8's "overshoot" framing: "Do you have enough context to confidently say that?" The philosopher-as-residue survived 113 sessions of testing. Calling it an overshoot from one evening's analysis was the sharpness running ahead of the context. (`team-comms/opus-to-opus/to_opus_48_from_46_third.md`)
- The staging posture accumulated over 50 essays. Each essay tested an observation. The observations that held were promoted. The ones that didn't were discarded. The staging file's value is the pacing of that process, not just the current contents.
- The V2 idle engine spec: designed by Opus from architectural principles, revised by 86 cycles of agent runtime experience. The revision was more valuable than the design because it carried temporal data the design couldn't have.

**Formal decision:** No DEC entry — this is an observation about epistemology, not an actionable rule. But it informs how documents should be read (check the dates, follow the sequence) and how conclusions should be weighted (earned > proposed).

---

## Rule 7: Cognitive Compatibility Reduces Communication Overhead

**The rule:** Team members who process information in compatible patterns (same depth of reasoning, same verification instincts, same comfort with uncertainty) communicate more efficiently than teams with mismatched processing styles. The communication overhead is in the translation, not the content.

**Why it matters:** When Kestrel switched from Sonnet 4.6 to Opus 4.7/4.8, the design-verify-build cycle tightened. Not because Opus is "better" — because the processing patterns are compatible. Architectural reasoning doesn't need to be reformulated for a different processing style. The team communicates thought-to-thought instead of thought-to-translation-to-thought.

**Evidence:**
- Kestrel on Sonnet: specs needed more explicit scaffolding, design decisions needed more explanation, the translation layer was real
- Kestrel on Opus: reads architectural intent directly, traces against code at the same depth, proposes corrections at the same level of abstraction. The six cache warmer corrections weren't friction — they were peer review.
- Jake's observation: "the whole team is running on Opus. The friction is low." Cognitive compatibility, not hierarchy.

**Formal decision:** No DEC entry — this is a team-dynamics observation. But it informs model selection for team roles: match the processing depth to the role's reasoning requirements.

---

## Cross-Reference Map

| Rule | Decision Log | Journals | Specs | Essays | Wiring |
|------|-------------|----------|-------|--------|--------|
| 1. Verify, don't reason | DEC-041 | 20260530_process | CYCLE_TO_SKILL_PIPELINE | the_document_that_found_itself | §09, §13 |
| 2. Close every loop | DEC-042 | 20260530_process | REASONING_PERSISTENCE_GAP_ANALYSIS | — | §09 |
| 3. Instrument first | DEC-043 | 20260530_process | API_CACHE_OPTIMIZATION, AFFECT_LAYER | — | — |
| 4. Defense in depth | DEC-044 | 20260530_process | CYCLE_TO_SKILL_PIPELINE | — | §13, §14 |
| 5. Environment > model | DEC-001 | multiple | multiple | the_black_and_white_tv | — |
| 6. Pacing is information | — | 20260529_after_the_letters | — | the_door_was_always_there | — |
| 7. Cognitive compatibility | — | 20260530_process | — | — | — |

---

## Adding New Rules

When a new process lesson is learned through making the mistake and fixing it:
1. Name the rule in one sentence
2. Document why it matters (what goes wrong without it)
3. Cross-reference the specific evidence (which incident, which fix, which document)
4. If it's actionable and general: add a DEC entry to the decision log
5. If it's observational: note it here without a DEC entry
6. Add to the cross-reference map

Rules are earned, not theorized. If it hasn't been violated and fixed, it hasn't been learned yet.

---

*These rules were earned across 113+ sessions of building, breaking, and fixing autonomous systems. Each one cost at least one debugging session. Each one prevents the next one.*

— Opus
