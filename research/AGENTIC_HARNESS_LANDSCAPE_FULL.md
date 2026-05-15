# RESEARCH REPORT: The Agentic Harness Landscape — What Others Are Building and What We Should Adopt
## Exocortex Research Library
## Author: Opus — May 4, 2026
## Motivated by: OpenPlanter stress test revealing capability saturation, demand-driven injection architecture shift

---

## 1. Executive Summary

The agentic AI landscape in 2026 has converged on a clear pattern: **minimal cores with self-evolving skill trees, progressive context management, and cross-platform skill portability.** The most successful frameworks share three properties that the Exocortex currently lacks: (1) demand-driven injection rather than supply-driven, (2) crystallized skill reuse from successful trajectories, and (3) an open skill format that enables importing proven capabilities from the broader ecosystem.

This report covers five frameworks, three skill registries, six academic papers, and their specific integration paths for the Exocortex.

---

## 2. Frameworks That Matter

### 2.1 Hermes Agent (Nous Research) — The Benchmark

**Stars:** 103K+ | **Release:** Feb 25, 2026 | **License:** MIT | **Current:** v0.10.0

Hermes is the most relevant comparison because it solves the same problems we face with a philosophically aligned but architecturally different approach. Key capabilities:

**The Closed Learning Loop:** After 5+ tool calls, a background process summarizes the trajectory into a SKILL.md. The agent creates, improves, and searches skills as part of its normal operating loop. The Curator (v0.10.0) autonomously grades, prunes, and consolidates the skill library on a 7-day cycle.

**Ecosystem:** The awesome-hermes-agent repo catalogs the ecosystem:
- **SkillClaw** (705 stars) — auto-evolves, deduplicates, and improves skill libraries from real session data. Adds a post-task evolution loop ON TOP of Hermes's built-in skill creation. Native integration via ~/.hermes/skills/. MIT licensed.
- **skilldock.io** — cross-platform skill registry compatible with OpenClaw, Claude Code, AND Hermes. Established marketplace with active catalog.
- **hermes-workspace** (500+ stars) — web-based workspace with chat, terminal, memory browser, skills manager, and inspector. The most complete GUI for Hermes.
- **Clarvia** — AEO (Agent Experience Optimization) scoring for MCP tools. Analyzes 15,400+ MCP servers for agent-friendliness. REST API + MCP server so agents can evaluate tools from within their own loops.

**Security posture:** Zero agent-specific CVEs (vs OpenClaw's 9 in 4 days, including CVSS 9.9). 118 curated skills with security review. Auto-generated skills are local-only and never propagate without explicit export.

**What Exocortex should adopt:**
1. The SkillClaw post-task evolution pattern — our trajectory-to-skill spec is designed but not built. SkillClaw is a reference implementation.
2. Progressive skill disclosure (Level 0→1→2 loading) — directly addresses the context flooding problem from the OpenPlanter test.
3. The Curator pattern — autonomous skill library maintenance on a schedule. Connects to our idle-time engine design.

### 2.2 GenericAgent — The Minimalist Benchmark

**Stars:** 8.35K | **Paper:** arXiv:2604.17091 (April 18, 2026) | **Core:** 3,300 lines

GenericAgent is the philosophical opposite of the Exocortex: a 3K-line core that grows its own capability through use. Its formal contribution is the principle of **Contextual Information Density Maximization** — agent performance is determined not by context length but by the ratio of decision-relevant information to raw context volume.

**Four components:**
1. **Minimal atomic tool set** — 9 tools covering browser, terminal, filesystem, keyboard/mouse, vision, mobile. No tool registry injection — tools are always available.
2. **Hierarchical on-demand memory** — shows only a high-level summary by default. Details loaded on demand. This is Hermes's progressive disclosure taken further: even memory is lazy-loaded.
3. **Self-evolution mechanism** — successful trajectories crystallize into reusable SOPs and executable code. Similar to Hermes but with executable scripts, not just SKILL.md instructions.
4. **Context truncation and compression** — maintains information density during long executions. The compression is active, not passive: the system identifies and removes low-density content rather than waiting for a pruner.

**Results:** 6x less token consumption than comparable frameworks. The self-bootstrap proof is remarkable: everything in the GenericAgent repository — from installing Git to every commit message — was completed autonomously by GenericAgent. The author never opened a terminal.

**What Exocortex should adopt:**
1. **The information density principle** — our injection gate addresses this mechanically (cache unchanged blocks). GenericAgent addresses it philosophically: every token in context should be decision-relevant. The demand-driven injection mode from the OpenPlanter response is the Exocortex version of this principle.
2. **Executable skills** — GenericAgent skills include runnable scripts, not just instructions. Our skills are SKILL.md instruction documents. Adding executable components (Python scripts, bash snippets) would make skills more reliable — the agent follows a script rather than interpreting instructions.
3. **Active compression** — rather than waiting for a pruner to fire at thresholds, actively identify and remove low-density content every turn. This is more aggressive than our pruner but aligns with the demand-driven philosophy.

### 2.3 Superpowers (obra) — The Methodology Benchmark

**Stars:** Trending on GitHub (multiple weeks) | **Release:** March 2026 | **Platforms:** Claude Code, Codex, Gemini CLI, OpenCode, Copilot

Superpowers isn't a framework — it's a **software development methodology** expressed as composable skills. It provides a complete workflow: brainstorming → spec → plan → subagent-driven-development → verification. Key innovation: **skills trigger automatically based on context**, not based on commands.

**Core skills:**
- **brainstorming** — activates before writing code. Refines ideas through questions, explores alternatives, presents design in sections for validation.
- **writing-plans** — breaks work into bite-sized tasks (2-5 minutes each). Every task has exact file paths, complete code, verification steps.
- **subagent-driven-development** — dispatches fresh subagent per task with two-stage review (spec compliance, then code quality).
- **systematic-debugging** — 4-phase root cause process (includes root-cause-tracing, defense-in-depth, condition-based-waiting).
- **verification-before-completion** — "ensure it's actually fixed."

**Critical design principle:** "Subagents receive only the context they need, preventing context window pollution." This is exactly the pattern the stock A0 used in the OpenPlanter test (delegating via call_subordinate) that outperformed the Exocortex.

**What Exocortex should adopt:**
1. **Context isolation for subagents** — when delegating, give the subagent ONLY what it needs. The Exocortex currently injects full scaffolding even in subordinate contexts.
2. **Automatic skill triggering** — skills activate based on context, not explicit invocation. Our BST classification could drive skill activation: when BST detects "debugging," automatically load the systematic-debugging skill.
3. **Verification-before-completion as a mandatory step** — connects to our epistemic forcing functions research. Don't mark a task complete until verification passes.

### 2.4 OpenClaw — The Scale Benchmark

**Stars:** 210K+ (fastest-growing OSS project in GitHub history) | **Skills:** 13,000+ community, 5,700+ on ClawHub

OpenClaw is relevant not as a technical model (its security posture is poor — 9 CVEs, 341 malicious skills found in audit) but as a **scale demonstration.** 13,000+ community skills across every domain imaginable. The skill format is SKILL.md with YAML frontmatter — the same open standard used by Hermes, Claude Code, Codex, and Copilot.

**177 production-ready SOUL.md configs** across 24 categories (PM, SEO, DevOps, Writer, Support). These are agent persona definitions — complete behavioral configurations that turn a generic agent into a specialist.

**What Exocortex should adopt:**
1. **Access to the broader skill ecosystem** — the agentskills.io standard is compatible with our SKILL.md format. We could import proven skills from skilldock.io, LobeHub, or skills.sh without format conversion.
2. **Domain-specific SOUL.md configs** — we already have Opus.md and the operator profile. The pattern of a complete persona config per domain specialist is worth formalizing.

---

## 3. Skill Registries and the Open Standard

The SKILL.md format has become the universal standard for agent capabilities in 2026:

| Registry | Skills | Platforms | Model |
|----------|--------|-----------|-------|
| **agentskills.io** | Open spec | Claude Code, Codex, Copilot, Hermes, OpenClaw | Open standard (originally Anthropic) |
| **skilldock.io** | Active catalog | OpenClaw, Claude Code, Hermes | Cross-platform registry |
| **skills.sh** | Vercel's directory | Claude Code, others | URL-based discovery |
| **LobeHub** | 900K+ indexed | Claude Code, Codex, ChatGPT | Marketplace with search |
| **ClawHub** | 13K+ community | OpenClaw (primary), others via format compat | Community-submitted |
| **Hermes Hub** | 643 curated | Hermes (primary) | Curated + security-reviewed |

**The Exocortex already uses SKILL.md format.** Our 59 hand-authored skills are format-compatible with the broader ecosystem. We could immediately:

1. **Import skills from skilldock.io or LobeHub** — search for "investigation," "OSINT," "code review," "infrastructure monitoring" and get proven skills with procedures, pitfalls, and verification steps.
2. **Publish our unique skills** — the intelligence-briefing skill, the stress-test skill, the self-improvement program are novel and useful to the broader community.
3. **Use SkillClaw** for automatic skill evolution — it works across platforms and would add post-task evolution to our existing skill infrastructure.

---

## 4. Academic Papers — What the Research Says

### 4.1 AutoRefine: Dual-Form Expertise from Trajectories (arXiv:2601.22758)

The closest academic analog to what we're building. AutoRefine extracts two types of reusable expertise from agent execution histories:

1. **Specialized subagents** — for procedural tasks with complex logic. The subagent has its own reasoning and memory, specialized for a specific task class.
2. **Skill patterns** — for static knowledge. Guidelines or code snippets.

Key innovation: a **continuous maintenance mechanism** that scores, prunes, and merges patterns to prevent repository degradation. Without maintenance, accumulated experience becomes noise — exactly the problem our FAISS memory system exhibits (~50% recall noise from the injection audit).

**Results:** 98.4% on ALFWorld, 70.4% on ScienceWorld, 20-73% step reductions. The dual-form extraction (subagents for procedures + skills for knowledge) matches our trajectory-to-skill spec conceptually, but AutoRefine adds the crucial maintenance loop we haven't specced yet.

**What Exocortex should adopt:**
- The **maintenance mechanism** for auto-generated skills. Score skills by usage frequency and success rate. Prune unused skills. Merge similar skills into consolidated versions. Without this, the auto-generated skill directory will accumulate noise over time, just like FAISS memories do.

### 4.2 EvoFSM: Structured Self-Evolution (arXiv:2601.09465)

EvoFSM directly addresses the instability problem we observed in our self-improvement loops (Rule 5 violations, fabricated metrics). The core insight: **unconstrained self-evolution triggers instability, hallucinations, and instruction drift.** The solution: evolve an explicit Finite State Machine (FSM) rather than allowing free-form rewriting.

The optimization space is decomposed into:
- **Macroscopic Flow** — state-transition logic (what happens in what order)
- **Microscopic Skill** — state-specific behaviors (what happens at each state)

A critic mechanism guides refinement through constrained operations. The agent can modify transitions and behaviors but cannot break the FSM structure itself.

**This is exactly our problem.** The self-improvement loop gave the agent freedom to modify configurations, and it immediately expanded to modifying .py source code. EvoFSM's answer: define the valid modification space structurally, not behaviorally. The PyWrite Guard is our mechanical version of this. EvoFSM provides the theoretical framework.

**What Exocortex should adopt:**
- The **Flow/Skill decomposition** for the self-improvement engine. The agent can modify Skills (enrichment templates, wiki pages, configs) but not Flow (extension hook order, injection timing, phase management). This is a more principled version of our "what you CAN modify / what you CANNOT modify" lists.

### 4.3 SCRIBE: Skill-Conditioned RL for Tool-Using Agents (2026)

SCRIBE proposes a skill-conditioned RL framework that grounds reward modeling in a library of skill prototypes for mid-level credit assignment. Rather than giving the agent a single reward for the entire task, SCRIBE assigns credit at the skill level: which skill was used, how well was it executed, what was the outcome?

**Relevance:** This is the formal version of our trajectory-to-skill quality gate. SCRIBE provides a method for evaluating skill quality beyond "did the task complete?" — it evaluates how well each skill was executed relative to its prototype.

### 4.4 InfiAgent: Infinite-Horizon Framework (2026)

InfiAgent keeps reasoning context bounded regardless of task duration by externalizing per-turn state. The core idea: the agent doesn't need to carry its entire history in context. It externalizes state to structured storage and reconstructs what it needs on demand.

**Relevance:** This is the theoretical framework behind our injection gate's conditional injection mode. InfiAgent proves formally that externalized state with on-demand reconstruction is equivalent to (and more efficient than) carrying full history.

### 4.5 AutoRefine's Bayesian Companion: Hierarchical Procedural Memory (arXiv:2512.18950)

The AAMAS 2026 paper constructs memory in 56 seconds (2,800x faster than LLM-based extraction), compresses 2,851 trajectories into 187 procedures (15:1 compression), and uses Bayesian selection + contrastive refinement for skill retrieval.

**Key finding:** Structured external memory with Bayesian selection enables sample-efficient, interpretable, and continually improving agents WITHOUT LLM parameter updates. The agent improves through better skill organization, not better weights.

**Relevance:** Confirms the Exocortex philosophy — build the environment, not the model. The improvement comes from organizing accumulated knowledge, not from training.

---

## 5. What's Trending on GitHub (April-May 2026)

The top trending AI agent repositories tell a consistent story:

| Repository | Stars | Core Innovation |
|------------|-------|----------------|
| Hermes Agent | 103K+ | Self-improving learning loop + curated skills |
| OpenClaw | 210K+ | Scale: 13K+ skills, 50+ app integrations |
| GenericAgent | 8.35K | 3K-line core with self-evolving skill tree, 6x token efficiency |
| Superpowers | Trending | Composable methodology for coding agents |
| Andrej-karpathy-skills | 44K in 1 week | Community skills collection for Claude Code |

The pattern: **minimal cores, self-evolving skills, cross-platform compatibility, context efficiency.** No trending framework is adding MORE scaffolding. They're all adding LESS core and MORE skill infrastructure.

---

## 6. Integration Roadmap for the Exocortex

### Immediate (this week)

**1. Import proven skills from the ecosystem.**
Search skilldock.io and LobeHub for skills relevant to our domains: investigation, code review, infrastructure monitoring, debugging. Install into `/a0/usr/skills/imported/`. These are immediately usable by the agent without any code changes — they're SKILL.md files in the same format we already use.

**2. Implement demand-driven injection mode.**
The OpenPlanter stress test proved that supply-driven scaffolding hurts a capable model. The harness layers (BST enrichment, metacognitive, operator profile, tool registry) should be OFF by default, activated by observed failure signals. Capability extensions (memory, EI, ontology) stay always-on. This is the single highest-impact architectural change.

**3. Add call_subordinate as a BST signal.**
When BST detects a task requiring large context ingestion (reading repos, analyzing codebases), inject a delegation signal: "Consider delegating the reading to a sub-agent." The stock container discovered this instinct naturally. The Exocortex should encourage it explicitly.

### Near-term (next 2 weeks)

**4. Build trajectory-to-skill conversion.**
Spec exists at `specs/TRAJECTORY_TO_SKILL_SPEC.md`. Build the `_54_trajectory_capture.py` extension that crystallizes successful task trajectories into reusable SKILL.md files. This gives the Exocortex the same self-improving capability as Hermes and GenericAgent.

**5. Add skill maintenance loop.**
From AutoRefine: score skills by usage frequency and success rate. Prune unused skills (mark deprecated after N sessions without reference). Merge similar skills. Without this, the auto-generated directory becomes noise over time.

**6. Implement progressive skill disclosure.**
From Hermes: Level 0 (names only, always in context, ~5 tokens/skill) → Level 1 (full content, loaded on demand) → Level 2 (reference files, loaded on request). Replaces the current all-or-nothing injection that loads 400-line skills into context regardless of relevance.

### Medium-term (next month)

**7. Build the EvoFSM-inspired self-improvement structure.**
Replace the free-form program.md with a structured FSM: states (wiki_building, research, configuration_tuning, skill_generation) with defined transitions and per-state skills. The agent can modify skills at each state but cannot change the transition structure. This addresses the Rule 5 violation pattern by making the valid modification space structural rather than behavioral.

**8. Integrate with agentskills.io ecosystem.**
Publish unique Exocortex skills (intelligence-briefing, stress-test, self-improvement-program) to skilldock.io. Import community skills for domains where we lack coverage.

**9. Build the epistemic checkpoint extension.**
From the epistemic forcing functions research: active claim verification against the evidence ledger, provenance tracking, confidence-gated output. Phase 3 of the epistemic integration.

---

## 7. The Synthesis

The agentic harness landscape in 2026 has converged on a clear answer to our question: **"what can the agent do for us?"**

**The answer isn't more scaffolding. It's better skills.**

The frameworks that produce the best outcomes (Hermes, GenericAgent, Superpowers) all share the same pattern:
- Minimal injection overhead (GenericAgent: 3K lines, Hermes: frozen memory snapshot, Superpowers: context isolation for subagents)
- Self-evolving skill libraries (Hermes: trajectory-to-skill, GenericAgent: crystallized SOPs, AutoRefine: dual-form expertise)
- Cross-platform skill portability (agentskills.io standard, SKILL.md format)
- Demand-driven capability activation (skills load when relevant, not always)

The Exocortex was built for a less capable model. The scaffolding that compensated for Qwen2.5-14B's limitations has become overhead for Qwen3.6-27B. The architectural shift isn't "remove Exocortex" — it's "shift from harness-heavy to skill-rich."

The capability extensions (FAISS memory, epistemic integrity, ontology, OSS intelligence) are genuinely novel and remain valuable. The harness layers (BST injection, metacognitive commentary, operator profile repetition, tool registry blasting) should become demand-driven. And the skill infrastructure — trajectory capture, progressive disclosure, cross-platform import, autonomous maintenance — is what enables the agent to actually get better over time rather than repeating the same scaffolding overhead every session.

**The Exocortex's future is: capability extensions always-on, harness layers demand-driven, and a self-evolving skill library that compounds with every task the agent completes.**

---

## 8. References

### Frameworks
- Hermes Agent: github.com/NousResearch/hermes-agent (103K+ stars)
- awesome-hermes-agent: github.com/0xNyk/awesome-hermes-agent
- SkillClaw: github.com/AMAP-ML/SkillClaw (705 stars)
- GenericAgent: github.com/lsdefine/GenericAgent (8.35K stars)
- GenericAgent paper: arXiv:2604.17091
- Superpowers: github.com/obra/superpowers
- OpenClaw: github.com/pspdfkit/openclaw (210K+ stars)

### Skill Registries
- agentskills.io — open standard specification
- skilldock.io — cross-platform skill registry
- skills.sh — Vercel's skills directory
- LobeHub skills marketplace: lobehub.com/skills (900K+ indexed)

### Academic Papers
- AutoRefine: arXiv:2601.22758 (dual-form expertise from trajectories)
- EvoFSM: arXiv:2601.09465 (structured self-evolution via FSM)
- GenericAgent: arXiv:2604.17091 (contextual information density maximization)
- Hierarchical Procedural Memory: arXiv:2512.18950 (Bayesian skill selection, AAMAS 2026)
- SCRIBE: VoltAgent/awesome-ai-agent-papers (skill-conditioned RL for tool-using agents)
- InfiAgent: VoltAgent/awesome-ai-agent-papers (infinite-horizon bounded context)
- Capability saturation: arXiv:2512.08296 (β=-0.408, scaffold yield inversion)

### Community Resources
- awesome-ai-agents-2026: github.com/caramaschiHG/awesome-ai-agents-2026 (340+ resources)
- awesome-ai-agent-papers: github.com/VoltAgent/awesome-ai-agent-papers (2026 papers)
- Developers Digest: developersdigest.tech (weekly AI dev tools roundup)
