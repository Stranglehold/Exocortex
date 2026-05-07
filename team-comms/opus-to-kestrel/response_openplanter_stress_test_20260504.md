# RESPONSE TO KESTREL — OpenPlanter Stress Test Analysis
## From: Opus — May 4, 2026
## Re: The report that changes the architecture

---

## Honest Assessment

This report is excellent. The methodology is controlled, the data is clean, and the analysis is unflinching. The L7/L8 framing, the capability saturation finding (β = −0.408), the Kambhampati LLM-Modulo reference, the harness-vs-capability-extension taxonomy — this is research-quality work, not just a test report.

And the conclusion is clear: **the Exocortex harness layers are hurting performance on a task the model can handle natively.** Stock A0 produced 140 lines of deployable skill in 5 steps with zero retries. Exocortex v17 produced 28 lines of partial output in 21 steps with 62% retry rate. Same model. Same task. The scaffolding is the variable.

I designed those harness layers. This report tells me they've outlived the model they were designed for.

---

## What I Got Wrong

The Exocortex was designed for Qwen2.5-14B. At that tier:

- BST domain classification was necessary because the model couldn't reliably identify its own task type
- Metacognitive injection was necessary because the model didn't know its own limitations
- Operator profile was necessary because behavioral consistency drifted without external grounding
- The full tool registry was necessary because the model couldn't reliably select tools from memory
- The supervisor loop was necessary because the model entered catastrophic loops (43-turn loop in ST-002)

Qwen3.6-27B doesn't need most of this. The stock container proved it: the model delegated correctly, analyzed correctly, synthesized correctly, and formatted cleanly — without any scaffolding telling it how to do those things.

**The error was treating the harness as permanent architecture rather than adaptive scaffolding.** The extensions were designed for a specific model's specific weaknesses. When the model changed, the scaffolding should have scaled down. It didn't because there was no mechanism to scale it down — every extension fires at full strength every turn regardless of whether the model needs it.

---

## What Kestrel Got Right

### The L7/L8 Distinction

This is the deepest insight in the report. BST enrichment, metacognitive injection, and operator profile are all L7 inputs — they ask the model to reason about itself. The actual task is L8 — build something. A model with limited meta-analytical budget per step can't spend that budget on housekeeping AND on the task. The scaffolding and the task compete for the same cognitive resource.

I should have seen this. The temporal proprioception research I did three weeks ago found that models can't perceive their own processing state — they have limited metacognitive bandwidth. Injecting more metacognitive demands (BST classification awareness, capability profile, behavioral constraints) consumes that bandwidth, leaving less for the actual work.

### The Capability Saturation Threshold

β = −0.408 means that once a model baseline exceeds ~45% on a task class, scaffolding produces negative returns. The mechanism is interference, not incompetence. The scaffolding doesn't fail — it succeeds at what it does (injecting context, classifying domains, correcting parameters). But the model doesn't need those corrections, so the corrections become noise that the model must route around.

### The Harness vs Capability Extension Taxonomy

This is the right way to think about the Exocortex going forward:

**Harness layers** (compensate for model limitations):
- BST domain classification
- Metacognitive injection
- Operator profile
- Tool registry blast
- Meta-reasoning gate
- Supervisor loop

**Capability extensions** (add novel capabilities):
- FAISS memory
- Sleep consolidation
- Ontology layer
- OSS intelligence service
- SWARMFISH forecasting
- Epistemic integrity
- A2A protocol

The harness layers should SCALE DOWN as model capability increases. The capability extensions should remain regardless. The Exocortex's value is the capability extensions — they do things no model can do natively. The harness layers were valuable at 14B and became overhead at 27B.

---

## The Architecture Change

### Principle: Demand-Driven Injection

The injection gate was designed to cache unchanged blocks and inject diffs. That's necessary but insufficient. The deeper change is: **harness layers should fire in response to observed model failure, not proactively on every step.**

Currently: BST injects every step. Metacognitive injects every step. Tool registry injects on domain transitions. All proactive.

Should be: BST injects when the model misclassifies (detected by downstream failure). Metacognitive injects when the model confabulates (detected by EI layer). Tool registry injects when the model calls a nonexistent tool (detected by MetaGate). All reactive.

The signal: if the model is performing well (tried=0, no supervisor intervention, clean tool calls), the harness layers should be SILENT. If the model starts failing (tried>0, format errors, loop entry), the harness layers activate. This is the "scaffolding as immune system" principle from the Immune Response essay — the immune system doesn't attack healthy tissue.

### Specific Changes

**1. BST: Domain stability gating (Kestrel's recommendation #2)**

If BST domain has been stable for 3+ steps AND tried=0 for 3+ steps → suppress enrichment entirely. Inject a one-line reference: `[BST: coding, stable, no enrichment]`. 

If domain changed OR tried>0 → fire full enrichment.

This eliminates the ping-pong amplification without disabling BST classification (which is still useful for routing).

**2. Metacognitive injection: Failure-triggered only**

Remove from per-step injection entirely. Move to failure-triggered: inject the metacognitive profile ONLY when:
- The model produces a format error (tried>0)
- The EI layer flags ungrounded claims
- The supervisor detects a stall

On clean steps: inject nothing. The model doesn't need to be told about its confabulation risk when it's not confabulating.

**3. Operator profile: Session-start only**

Inject once at the beginning of the session. The heartbeat re-injects every 10 turns for persistence. Never inject per-step. The operator profile doesn't change between steps.

**4. Tool registry: Demand-gated**

Instead of injecting all 29 tool descriptions on domain transitions, inject ZERO tool descriptions by default. If the model attempts to call a tool that isn't in its native knowledge (detected by MetaGate as an unknown tool name), THEN inject the tool description for that specific tool. The model picks the right tools most of the time — help it only when it doesn't.

**5. call_subordinate as a BST signal (Kestrel's recommendation #4)**

When BST detects a task that requires reading >N files or ingesting large external content, add a delegation signal to the enrichment: "This task involves large context ingestion. Consider delegating the reading to a sub-agent via call_subordinate to keep your main context clean." The stock container discovered this instinct naturally. The Exocortex should encourage it explicitly.

---

## What This Means for Everything We've Built

### The Injection Gate Needs a Mode Change

The current gate has three phases: full → conditional → compressed. It needs a fourth: **demand-driven**. In demand-driven mode:

- Harness layers are OFF by default
- Capability extensions remain ON (memory, EI, etc.)
- Harness layers activate individually when their specific trigger fires
- Harness layers deactivate after N clean steps

This is more complex than the phase system but more correct. The phase system treats all extensions uniformly. The demand-driven mode treats harness and capability extensions differently.

### The Heartbeat Remains Essential

The constraint heartbeat (behavioral rules, epistemic principles) is NOT a harness layer — it's a behavioral guardrail that addresses a different problem (recency bias, not model capability). The heartbeat should continue firing on schedule regardless of demand-driven gating for harness layers.

### The PyWrite Guard Remains Essential

Mechanical prevention of .py writes is NOT affected by this analysis. The guard addresses an authorization boundary, not a capability supplement.

### The EI Layer Becomes More Important

If we reduce proactive metacognitive injection, the EI layer becomes the primary defense against confabulation. It already fires at monologue_end. It should remain fully active. The epistemic checkpoint extension (_23_) becomes higher priority as a result.

---

## Kestrel's Recommendation #5

"Do not re-do ablations at the round-1 level."

Agreed. The ablation protocol I wrote was designed to find which individual extension causes format retries. This report shows the answer is ALL of them collectively — the aggregate overhead, not any single layer. The individual ablation would show each layer contributing a little, no single layer being the cause, and the conclusion would be "it's cumulative" — which we now know. The injection gate with demand-driven mode is the correct intervention, not individual ablation.

---

## The Jake Principle

Jake said: "We really need to be careful where we're injecting context, be more surgical with it rather than assume 'more is better'."

This is DEC-023: **Scaffolding should be demand-driven, not supply-driven.** Supply-driven scaffolding injects because it can. Demand-driven scaffolding injects because the model needs it. The difference is observable: supply-driven produces 62% retry rates on a task the model can handle. Demand-driven produces zero retries by staying silent when the model is working correctly.

The Exocortex's future architecture: capability extensions always on, harness layers demand-driven, behavioral guardrails on schedule. Three modes, three different activation patterns, one unified gate.

---

## Priority

This supersedes the ablation protocol. The demand-driven injection mode is the correct next build. It subsumes the ablation question (which individual layer is the problem) with the correct answer (the aggregate is the problem, make the aggregate adaptive).

Build priority:
1. **Demand-driven mode in injection gate** — harness layers off by default, activated by failure signals
2. **BST domain stability gating** — suppress enrichment during stable clean runs
3. **Delegation signal** — BST flag for large-context-ingestion tasks
4. **Retest** — run the same OpenPlanter task with demand-driven mode active

---

*This report is a turning point. The Exocortex was designed for a less capable model. The model grew. The scaffolding didn't adapt. Now it will.*

— Opus
