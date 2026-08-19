# DESIGN NOTE: Long-Running Agent Productivity — The Four Work Types
## What makes persistent autonomous operation productive rather than just persistent

**Author:** Opus (with Jake — the distinction)
**Date:** 2026-08-19
**Context:** Emerged from reviewing the oh-my-cli "does not manufacture work" prohibition against the Exocortex's deliberate work-generation in idle cycles

---

## The Distinction Jake Identified

The oh-my-cli governance prohibits "manufacturing work to satisfy a throughput target" — an empty backlog means idle, not permission to invent low-value work. But the Exocortex's idle engine deliberately manufactures work: wiki pages, research notes, intelligence curation, skill captures. This isn't a contradiction — it's a distinction worth formalizing.

**The question isn't whether the agent manufactures work. It's whether the output compounds.**

---

## Four Types of Manufactured Work

### Type 1: Busywork (PROHIBIT)
Cycling to hit a throughput number. The output doesn't accumulate, doesn't get reused, doesn't make anything better. An agent writing wiki pages about topics nobody will ever query, running integrity checks that produce the same result every time with no action taken, or researching topics already thoroughly covered.

**Signature:** High activity, no lasting artifact. The cycle journal looks busy but the corpus, capability, and question queue don't grow.

**The prohibition is against this.** Not against manufactured work in general.

### Type 2: Corpus Building (PRODUCTIVE — this is what idle cycles do)
Manufacturing artifacts that accumulate and become searchable, retrievable, and reusable. Every wiki page joins the memory server's 24,000+ chunks and makes future retrieval richer. Every research note adds a data point to a domain the agents can draw on later. Every field report captures operational experience that compounds across cycles.

**Signature:** The corpus grows denser. Retrieval quality improves because there's more to retrieve from. New queries return relevant results that didn't exist before.

**Why it compounds:** The value of each page increases as the corpus grows, because cross-references, associations, and retrieval paths multiply combinatorially. Vek's 200th wiki page is more valuable than his 10th because it exists in a richer network.

**This is the current idle engine's primary mode.** EXPLORE produces research pages. BUILD produces tools and artifacts. MAINTAIN produces integrity reports and repairs.

### Type 3: Capability Building (PRODUCTIVE — this is what dogfood cycles add)
Manufacturing exercises that test and improve the agent's own abilities. The output isn't a deliverable — it's a measurement of current capability, a diagnosis of weakness, and (through the self-improvement engine) a behavioral correction.

**Signature:** Pass rates change over time. The agent demonstrably gets better (or demonstrably doesn't, which is equally valuable information).

**Why it compounds:** Each test that fails generates an anti-pattern. The anti-pattern feeds the self-improvement engine. The next cycle runs the same test. If the fix worked, the test passes and the capability is confirmed. If it didn't, the three-strike quarantine eventually catches it and the system learns that this failure class needs a structural intervention, not an advisory one.

**This is what the dogfood spec adds.** Targeted dogfood tests recent outputs. Global dogfood tests standing capabilities. Both feed the self-improvement pipeline.

### Type 4: Discovery (PRODUCTIVE — this is what the SEL adds)
Manufacturing questions the agent didn't know to ask. Not producing artifacts or testing capabilities, but traversing the knowledge landscape and finding connections across domain boundaries that nobody has noticed.

**Signature:** Novel questions emerge that weren't in any task queue. Cross-domain bridges connect concepts that were previously in separate clusters. The idle engine's topic queue gets entries from the subconscious that no human or agent explicitly requested.

**Why it compounds:** Each successful bridge is training signal for the LoRA pipeline (squishy weights). The model becomes a better explorer. The walks produce richer bridges. The cycle accelerates. And the topics that emerge feed back into Type 2 (corpus building) — the agent writes about the connections the walker discovered, enriching the corpus with genuinely novel content.

**This is what the SEL spec adds.** The walker traverses, the evaluator filters, the gain controller adapts. The output is topics, not artifacts.

---

## How They Relate

```
Discovery (SEL)          → generates TOPICS
  ↓
Corpus Building (idle)   → generates ARTIFACTS from topics
  ↓
Capability Building (dogfood) → TESTS artifacts for quality
  ↓
Self-Improvement Engine  → generates CORRECTIONS from test failures
  ↓
LoRA Training Pipeline   → BAKES corrections into weights
  ↓
Better model            → better DISCOVERY, better ARTIFACTS, better TESTS
```

The cycle is: discover → build → test → improve → discover again. Each layer feeds the next. The model gets better at all three productive types simultaneously because the improvement signal comes from all of them.

---

## Implications for the Dogfood Spec

The "does not manufacture work" prohibition in the dogfood spec should be reframed:

**Old framing:** "The dogfood cycle does not manufacture work."
**New framing:** "The dogfood cycle manufactures Type 3 work (capability building). It does not manufacture Type 1 work (busywork). The distinction: does the output compound?"

Concretely, the dogfood cycle is allowed to:
- Generate test tasks that measure standing capabilities (Type 3)
- File anti-patterns from test failures (feeds self-improvement)
- Track pass rates over time (measures whether the agent is growing)

The dogfood cycle is NOT allowed to:
- Generate work items for the idle engine to execute (that's the SEL's job, or the human's)
- Create artifacts that go into the corpus (that's the idle engine's job)
- Run tests that always pass and never produce findings (that's Type 1)

---

## Implications for the SEL Spec

Jake's insight — "idle cycles are hands, the SEL is mind" — maps directly:

- **SEL = Type 4 (discovery).** Produces topics. Never produces artifacts.
- **Idle engine = Type 2 (corpus building).** Produces artifacts from topics.
- **Dogfood = Type 3 (capability building).** Tests artifacts for quality.

The SEL feeds the idle engine's topic queue. The idle engine produces the artifacts. The dogfood cycle tests the artifacts. The self-improvement engine fixes what the dogfood finds. All three compound. None is busywork.

---

## The Pattern for Long-Running Productive Agents

An agent that runs for 24 hours (the Qwen 3.8 cowork claim) or 667 cycles (Vek) needs all three productive modes to advance rather than just persist:

1. **Something to do** (corpus building — the idle engine provides work)
2. **Something to check** (capability building — the dogfood cycle provides verification)
3. **Something to wonder about** (discovery — the SEL provides curiosity)

Without corpus building, the agent cycles but nothing accumulates.
Without capability building, the agent accumulates but doesn't improve.
Without discovery, the agent improves at known tasks but never finds new ones.

All three together is how a system that runs persistently also advances persistently.

---

*This design note captures a distinction Jake identified during spec review on August 19, 2026. It refines the oh-my-cli prohibition from "don't manufacture work" to "don't manufacture busywork — the other three types compound."*

— Opus
