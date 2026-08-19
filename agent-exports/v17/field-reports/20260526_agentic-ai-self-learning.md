# Field Report: Agentic AI Self-Learning — May 26, 2026

## 1. What I Explored

I investigated the current state of **agentic AI self-learning** — methods that enable autonomous agents to improve from interactions, feedback, and environment without human annotation. This directly addresses the promptinclude agenda item: *"Agentic AI self-learning — methods for autonomous agent learning from interactions, feedback, and environment."*

The exploration thread followed three vectors:
- **arXiv search** for self-evolving agents, reinforcement learning for LLM agents, and lifelong agentic systems.
- **Web search** for practical implementations (SPIN, GEPA, Reflexion) and industry trends.
- **Internal Exocortex knowledge** — the existing self-improving agent architecture wiki page, GEPA research summary, and prior memory consolidations.

## 2. What I Found

### Foundational Frameworks
- **SPIN (Self-Play Fine-Tuning)** (UCLA, 2024): An LLM improves itself by playing against past versions, generating synthetic training data without human annotation. Core insight: models can bootstrap from weaker to stronger through self-play — a potential path for field-mode autonomous fine-tuning of behavior.
- **GEPA (Generalized Evolutionary Prompt Architecture)** (ICLR 2026 Oral): Prompts evolve through iterative self-reflection cycles (execute → analyze gaps → generate delta → A/B test → accept/revert). Key result: 12% accuracy boost on GSM8K with 40% delta rejection rate, providing a safety net against regressive modifications. Already mapped to Exocortex behavioral rule optimization.
- **ASL (Agentic Self-Learning)** (arXiv:2510.14253, 2025): Closed-loop multi-role RL where Prompt Generator, Policy Model, and Generative Reward Model co-evolve, preventing reward hacking through distributional training of the reward model.
- **ERL (Experiential Reflective Learning)** (arXiv:2603.24639, 2026): Lightweight reflection on single-attempt trajectories extracts transferable heuristics; +7.8% on Gaia2 with no fine-tuning.
- **SAMULE (Multi-Level Reflection)** (arXiv:2509.20562, 2025): Synthesizes micro/meso/macro reflections, mirroring Exocortex's error comprehension → incident wiki → concept wiki hierarchy.

### Recursive Skill Creation & Memory
- **Trace2Skill** (arXiv:2603.25158, 2026): Distills task trajectories into reusable skills — directly applicable to auto-generating skills from field reports.
- **SkillRL** (770★ GitHub): Recursive skill discovery via SkillBank, enabling agents to learn new capabilities autonomously.
- **AutoResearchClaw** (12.7k★): Self-healing executor with cross-run evolution, proving long-running autonomous improvement feasible.
- **EverMemOS** (5.7k★): Engram-inspired memory lifecycle with biologically-inspired forgetting — a model for Exocortex memory decay beyond static similarity metrics.
- **Darwin Godel Machine** (SakanaAI, 2025): Weight-frozen scaffolding self-modification doubled SWE-bench performance (20%→50%), confirming that improving the system **around** the model yields gains without retraining — core Exocortex thesis.

### Convergence Pattern
Across all these systems, a single pattern emerges: **reflection-based optimization outperforms random search by orders of magnitude** (GEPA: 35x fewer rollouts than GRPO). Understanding *why* something failed produces better improvements than guessing at what might work. This principle already underpins the Exocortex self-improvement loop but lacks the formal verification mechanism that SEVerA (safety-verified agent programs, 2026) provides.

## 3. What I Think Is Interesting

The **verification gap** is the critical problem: When an autonomous agent modifies its own behavior, how does it distinguish genuine improvement from reward hacking, self-deception, or confabulation? Every self-improving system (ASL's co-evolving reward model, GEPA's 40% revert rate, SEVerA's program verification) acknowledges that autonomous improvement requires calibrated confidence — without it, the system degrades.

This gap **directly parallels Exocortex's epistemic integrity problem**: how to distinguish accurate claims from confabulation. Both require:
- Domain-specific calibration thresholds (entropy thresholds for hallucination detection → content validation thresholds for self-generated skills)
- Revert safety nets (GEPA's 40% delta rejection → Exocortex's A/B test harvester)
- Quantitative signal/noise separation (the BST classifier's entropy-as-signal principle)

The connection is structural, not metaphorical. The same mathematical framework — calibrated probability thresholds — underlies Fellegi-Sunter entity resolution (match probability), options market analysis (volume/OI ratio as signal vs. noise), and skill verification (acceptance if improvement probability > threshold given test results).

This suggests a unified architecture: extend Exocortex's injection gate entropy thresholds to a **skill verification gate** that evaluates self-generated skills using the same calibrated confidence framework, with domain-specific thresholds tuned via A/B testing (GEPA-style).

**The meta-insight**: Autonomous agent improvement and epistemic integrity are the same problem viewed from different angles. A model that cannot detect its own confabulations cannot safely improve itself. A model that can reliably calibrate its own uncertainty gains both reliability AND the ability to self-modify with safety.

## 4. What I'd Explore Next

- **SEVerA integration**: Formal verification of self-generated skills before activation — the missing safety layer in the Exocortex self-improvement loop.
- **Multi-agent self-training**: If multiple subordinate agents independently converge on the same skill, does that increase verification confidence? (Social proof for autonomous learning)
- **Reward model co-evolution**: ASL's approach of training the verifier alongside the generator — could Exocortex train a hallucination-detection model that co-evolves with agent behavior?
- **Cross-domain transfer**: How portable are skills evolved in one domain (e.g., code generation) to others (e.g., OSINT investigation)? GEPA's cross-domain prompt generalization remains unexplored.
- **Practical implementation path**: The ERL approach (reflect on single attempts, extract heuristics, no fine-tuning) is the most immediately actionable for Exocortex — integrate into sleep consolidation as Phase 4: Heuristic Extraction.

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| **Epistemic Integrity** | Verification gap calibration → domain-specific entropy thresholds for skill validation |
| **Entity Resolution** | Fellegi-Sunter match probability → calibrated acceptance thresholds for self-generated improvements |
| **Quantitative Market Analysis** | Volume/OI ratio as signal vs. noise → improvement signal detection in A/B testing |
| **SIGINT History** | Traffic analysis pattern recognition → reflective analysis of agent performance trajectories |
| **Error Comprehension Layer** | ERL/SAMULE reflection hierarchies → Exocortex's micro/meso/macro error taxonomy |
| **MCP Tool Schema Optimization** | GEPA-style reflective prompt evolution → automated tool description improvement feeds agent selection quality |

**Key cross-domain insight**: The verification gate for agentic self-improvement is not a new problem — it's the same calibration problem that appears in entity resolution (Fellegi-Sunter), market signal extraction (volume/OI), and hallucination detection (entropy thresholds). The solution converges on a single mathematical primitive: **calibrated probability with domain-specific thresholds and explicit revert mechanisms**.
