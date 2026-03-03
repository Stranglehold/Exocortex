# Skill: Integration Assessment

## Trigger
User discovers an external project (GitHub repo, tool, framework, service) and asks whether it's useful for Exocortex or Agent-Zero. Keywords: "what do you think of," "could we use," "I found this project," "is this useful for us," "how would this integrate," "have you seen."

## Inputs Required
- **Project source** — GitHub link, documentation URL, or user description
- **Current Exocortex state** — which layers exist, what's on the roadmap
- **User's stated interest** — what caught their attention (may differ from what's most technically useful)

If the project isn't provided directly, search for it. Read the README, architecture docs, and VISION/ROADMAP if they exist. Prioritize understanding what the project actually does today vs. what it aspires to do.

## Procedure

### 1. Understand What It Actually Is
Separate current reality from vision:
- **What exists today** — shipping features, working code, real capabilities
- **What's aspirational** — roadmap items, VISION.md promises, planned features
- **What's the core mechanism** — the one thing it does that nothing else does the same way

Many projects describe their vision in the README as if it's implemented. Check release history, actual codebase, and issue tracker to ground the assessment. A project with a beautiful VISION.md and 3 weeks of commits is a prototype, not a platform.

### 2. Map to Exocortex Layers
For each capability the project provides, ask:
- **Does this map to an existing layer?** — If yes, is it better than what we have?
- **Does this map to a roadmap item?** — If yes, does it accelerate the build?
- **Does this fill a gap we haven't identified?** — If yes, what weakness does it address?
- **Does this duplicate something we already built?** — If yes, is the duplication worth the integration cost?

Use the 10-layer stack as the reference frame. Every external capability either extends a layer, replaces a layer, fills a gap between layers, or doesn't fit the architecture.

### 3. Assess the Architecture
Evaluate integration feasibility:

**Dependency analysis:**
- What does it require? (API keys, cloud services, specific models, GPU, databases)
- Does it conflict with local-first principles? If yes, can it be adapted?
- What's the runtime environment? (Docker, bare Python, Node, system service)
- Can it run alongside Agent-Zero in the same container, or does it need its own?

**Mechanism classification (per component):**
- **Deterministic** — rule-based, heuristic, algorithmic. Can integrate directly.
- **Model-dependent (local)** — requires LLM inference but can use local models. Assess against model profiles (4B precision vs 14B reasoning).
- **Model-dependent (cloud)** — requires cloud API. Evaluate hybrid approach: cloud for heavy lifting, local for orchestration and storage.
- **Training-dependent** — requires fine-tuning or RL. This is the path Exocortex deliberately avoids. Note as "approach we don't take" and extract any deterministic insights.

**Interface surface:**
- Does it expose an API, CLI, or SDK?
- Can Agent-Zero call it as a tool?
- Can it be wrapped in an A2A-compatible interface?
- Does it produce structured output that can be ingested into classified memory?

### 4. Recommend Integration Path
One of five verdicts:

**Integrate as Tool** — Run inside Agent-Zero's container. Agent calls it via tool chain. Tightest coupling, most benefit, highest integration effort. Use when the project's core capability directly serves Agent-Zero's task execution.

**Integrate as Peer (A2A)** — Run as separate service. Agent-Zero delegates tasks via A2A protocol. Loose coupling, independent lifecycle, protocol overhead. Use when the project is a complete system with its own orchestration that would conflict with Agent-Zero's.

**Extract Patterns** — Don't integrate the project itself. Extract architectural patterns, algorithms, or design decisions that inform an Exocortex-native build. Use when the project validates an approach but its implementation doesn't fit the stack.

**Hybrid** — Use cloud/external for heavy operations, ingest results into local Exocortex. Reduce dependency over time by building deterministic alternatives for the components that don't require model inference. Use when the project provides essential capability that can't run locally today but the results can be stored locally.

**Pass** — Doesn't fit the architecture, duplicates existing capability without improvement, or the integration cost exceeds the value. Note what was learned for future reference.

### 5. Identify Prosthetic Requirements
If the project requires model capabilities that local models lack:
- Which specific operations need model inference?
- What are the reliability requirements? (Tool calls need 4B precision. Analysis needs 14B reasoning.)
- Can deterministic preprocessing reduce the model's burden?
- Does the model router become a prerequisite?

If the project introduces tool-heavy operations, check against the 4B/14B profiles:
- Tool reliability: 4B at 100% JSON / 80% params vs 14B at 73.3% JSON / 46.7% params
- Strategic reasoning: 14B at perfect PACE/graph vs 4B limited
- Route accordingly: structured tool calls → 4B, analytical reasoning → 14B

### 6. Position Relative to Roadmap
State explicitly:
- What roadmap item does this accelerate, replace, or invalidate?
- Does this change the priority order of planned builds?
- Does this introduce a new roadmap item?
- Does this affect the Agent-Zero migration decision? (Projects requiring inter-layer communication that can't be expressed as hook-order execution push toward custom framework.)

## Output Format
Conversational analysis, not a spec. The output is a recommendation that informs whether to integrate, how to integrate, and what to build. If integration is warranted, the output should include enough architectural mapping to feed into the Spec Writing skill.

Structure:
- Project reality check (what exists vs. what's aspirational)
- Layer mapping (where it fits in the stack)
- Architecture assessment (dependencies, mechanisms, interfaces)
- Integration recommendation (tool / peer / extract / hybrid / pass)
- Prosthetic requirements (what scaffolding the agent needs to use it)
- Roadmap impact (what changes)

## Quality Checks
- [ ] Current vs. aspirational capabilities clearly separated
- [ ] Every capability mapped to a specific Exocortex layer or gap
- [ ] Dependency analysis includes runtime environment, API requirements, and local-first compatibility
- [ ] Each component classified as deterministic / model-dependent (local) / model-dependent (cloud) / training-dependent
- [ ] Integration path recommendation is one of the five defined verdicts with justification
- [ ] Prosthetic requirements reference specific model profile metrics
- [ ] Roadmap impact explicitly states what changes

## Anti-Patterns
- **Evaluating the vision instead of the code.** A VISION.md is a plan. The README and actual codebase are reality. Assess what exists, then note what's planned.
- **Defaulting to "integrate everything."** Some projects are better studied than integrated. Extracting patterns costs nothing. Integration creates maintenance burden. The bar for integration should be: "does this provide capability we can't build faster ourselves?"
- **Ignoring the local-first constraint.** A project that requires cloud APIs for core functionality isn't immediately compatible. Assess the hybrid path, but don't pretend cloud dependency doesn't exist.
- **Forgetting the model router prerequisite.** Many integrations need tool-reliable execution routed to 4B and analytical reasoning routed to 14B. If the model router doesn't exist yet and the integration requires it, that's a dependency, not a feature.
- **Assessing in isolation.** Every external project exists in the context of the current stack and roadmap. An amazing project that duplicates Layer 10's capability isn't useful. A mediocre project that fills the one gap blocking the next roadmap phase is invaluable.
