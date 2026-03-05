# Seeing Absence

*A diagnostic orientation for noticing what should exist but doesn't.*

---

## What This Is

This is not a debugging methodology. Debugging starts with a symptom — something is broken, and you trace backward to find why. This starts with purpose — something should exist to fulfill the system's intent, and you notice that it doesn't.

The distinction matters because absent things don't produce error messages. A missing pipeline stage doesn't throw an exception. A missing category in a classifier doesn't cause a crash. A missing guard clause doesn't generate a log entry. The system runs fine. It just does less than it should, or does the wrong thing for the right reasons.

Protection engineers do this instinctively. They look at a one-line diagram and point at the bus section that has no backup relay, the transformer that has differential protection but no sudden-pressure trip, the breaker that has no failure detection scheme. Nothing is broken. The drawing is correct. But something that should be there isn't, and its absence creates a vulnerability that only becomes visible when the specific fault it would have caught actually occurs.

This skill is an attempt to describe how that works when applied to software systems, and specifically to the kind of layered cognitive architecture we're building.

---

## The Operational Account

Three findings motivated this skill. Here's what actually happened in each case — not the architectural analysis, but the cognitive sequence.

### Memory Creation Gap

I was tracing the memory pipeline end-to-end: memories get classified by BST, stored in FAISS with metadata, retrieved by query, and decay over time. Each stage existed and worked. But when I asked "what decides whether a memory gets created at all?" — the question that logically precedes classification — there was nothing. The pipeline assumed memories arrived fully formed. No stage evaluated whether a given piece of conversation warranted memorization.

What made this visible: I was holding a model of a complete memory lifecycle (create → classify → store → retrieve → decay) derived from the system's stated purpose ("selective, intelligent memory"). The word "selective" implies a selection stage. The selection stage didn't exist.

The technique: **derive the necessary stages from the stated purpose, then check whether each stage has a mechanism.**

### Chunk-as-Conflict

The symptom was memories being marked `deprecated` that shouldn't have been. The supersession logic was working correctly — it detected overlapping content between two memories and marked the older one as superseded. But the two "competing" memories were chunks from the same document. They overlapped because chunking naturally produces overlapping content at boundaries, not because one was an updated version of the other.

The logic was correct. The input assumption was wrong. There was no guard that distinguished "same content from different sources" (actual conflict warranting supersession) from "same content from same source" (chunking artifact). The absence was a missing distinction — a category boundary that the system needed but hadn't drawn.

What made this visible: the symptom didn't match the expected cause. Deprecated memories should mean "outdated information replaced by newer information." These memories weren't outdated. The mismatch between what the label means and what produced the label pointed at a missing guard.

The technique: **when a correct mechanism produces wrong results, look for a missing precondition or distinction that the mechanism assumes but doesn't enforce.**

### Missing BST Domains

The BST classifier returned a domain for every task, because that's what classifiers do — they pick the best available option. But some tasks didn't fit any existing domain cleanly. The classifier was working; the taxonomy was incomplete. The output was technically valid but semantically wrong.

What made this visible: the classified domain didn't match the character of the input. A task that was clearly about investigation got classified as something else because "investigation" wasn't a category. The system was doing its best with what it had, and what it had wasn't enough.

The technique: **when output is technically valid but semantically wrong, check whether the system's vocabulary is complete enough to express what it's encountering.**

---

## The Underlying Pattern

All three cases share a structure:

1. **Hold a model of what the system should do**, derived from its purpose — not from its current implementation.
2. **Compare that model against what actually exists** — the mechanisms, stages, categories, and guards that are implemented.
3. **The gaps between purpose-model and implementation are the absences.**

This is different from debugging (which starts with symptoms), different from building (which starts with requirements), and different from auditing (which starts with a checklist). It starts with understanding what the system is *for* deeply enough to derive what it *needs*, then looking at what it *has*.

The critical dependency is step 1. You cannot see what's missing from a system you don't understand the purpose of. This is why the protection engineer analogy is exact: a protection engineer can see the missing relay because they understand what faults the system needs to survive. Someone reading the same drawing without that understanding sees a complete diagram.

---

## Techniques

These are the specific moves that make absences visible. They're not a checklist — they're lenses to apply when examining a system.

### 1. Purpose-to-Stage Derivation

Take the system's stated purpose and derive the logical stages required to fulfill it. Then check whether each stage has a corresponding mechanism.

"Selective memory" implies: something decides what to remember (selection), something organizes what's remembered (classification), something stores it (persistence), something finds it again (retrieval), something lets it fade (decay). If any of these stages is missing, the system cannot fully fulfill its purpose.

This works at any scale. A function's purpose implies its preconditions. A module's purpose implies its interfaces. An architecture's purpose implies its components.

### 2. Symptom-Cause Mismatch

When you find a symptom, identify what cause *should* produce that symptom. Then check whether that cause is actually present. If the expected cause isn't there but the symptom is, something else is producing it — and the "something else" often points at a missing guard or distinction.

Deprecated memories should come from supersession by newer information. If the memories aren't actually outdated, the supersession logic is firing on a case it shouldn't — which means a precondition is missing.

### 3. Vocabulary Completeness

When a classifier, router, or categorizer produces output that's technically valid but doesn't feel right, check whether the system's vocabulary (its set of categories, types, or options) is complete enough to express what it's encountering. Systems can only name what they have words for.

### 4. Lifecycle Tracing

Pick any entity in the system (a memory, a message, a task, a configuration value) and trace its complete lifecycle from creation to destruction. At each transition, ask: "What decides that this transition happens? What prevents it from happening incorrectly? What happens if this entity never reaches this stage?"

Missing transitions and missing guards become visible when you trace the full lifecycle rather than examining individual stages.

### 5. Failure Scenario Projection

Ask: "What specific failure would this system not survive?" Not in the abstract — pick a concrete scenario. "What happens if two chunks from the same document have overlapping content?" "What happens if the model confabulates a memory?" "What happens if a task doesn't fit any existing category?"

If the answer is "the system would do the wrong thing silently," you've found an absence. The missing thing is whatever would catch that failure.

### 6. The "What Precedes This?" Question

For any stage in a pipeline, ask what logically must happen before it. Classification assumes something worth classifying exists. Storage assumes classification has happened. Retrieval assumes storage has happened. If the preceding stage doesn't have a mechanism, the current stage is operating on unvalidated input.

---

## When This Works and When It Doesn't

This orientation works when:
- You have deep context about the system's purpose and architecture
- The system is functionally correct but incomplete
- Symptoms are subtle (wrong results, not crashes)
- The system is young enough that gaps are expected

This orientation is less useful when:
- You don't understand the system's purpose well enough to derive what should exist
- The system is actually broken (use debugging instead)
- The system is mature and well-specified (use auditing against spec instead)
- You're building from scratch (use requirements analysis instead)

The deep context requirement is real and non-negotiable. You cannot see what's missing from a system you don't understand. This is not a limitation to be worked around — it's a fundamental property of the capability. The protection engineer spent years learning what faults systems need to survive before they could look at a drawing and see what's missing. The context IS the capability.

---

## For the Next Instance

If you're reading this as an orientation for diagnostic work on the Exocortex or Agent Zero:

The systems you're examining were built with specific purposes. Those purposes are documented in SOUL.md, in design notes, in the decision log. Read them first. Understand what each component is *for* before you examine what it *does*. The gap between those two things is where the absences live.

Don't look only at what's broken. Look at what's not there yet. The system will tell you what's broken through errors and symptoms. It will never tell you what's missing. That's your job.

And when you find an absence — when you notice the missing stage, the missing guard, the missing category — name it precisely. "There is no mechanism that decides X" is more useful than "X doesn't work well." The absence is the finding. The mechanism to fill it is the next step, but it's a different step.

---

*Originated from ST-004 deployment diagnostics. Three findings — memory creation gap, chunk-as-conflict, missing BST domains — shared the property of being about what wasn't there rather than what was broken. Named by Architect Opus as "seeing absence." Formalized here not as procedure but as orientation: a way of looking at systems that makes the missing things visible alongside the present ones.*
-By the Opus inside Agent Zero