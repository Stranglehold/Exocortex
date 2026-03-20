# Industry Research Ledger
## What the field is finding, and what it means for us

**Started:** Session 058, March 16, 2026
**Maintained by:** Opus, with Jake and Eitan
**Purpose:** Running analysis of external research — papers, posts, repos — mapped to Exocortex relevance. Written for the whole team, not just the person who can read the math.

---

## How to read this document

Each entry has three sections:

- **What they did** — plain-language summary of the research, no jargon gate
- **What it actually means** — the deeper implications, including the math when it matters
- **What we can use** — concrete connections to Exocortex architecture, rated by timeframe:
  - 🟢 **Now** — directly applicable to current build
  - 🟡 **Soon** — relevant to planned work (ACP, SWARMFISH, sleep consolidation)
  - 🔴 **Future** — interesting but requires infrastructure we don't have yet

---

## Entry 001: Attention Residuals (Kimi Team, March 2026)

**Source:** Technical report, github.com/MoonshotAI/Attention-Residuals
**Domain:** Model architecture — how information flows between layers inside a transformer

### What they did

Every transformer stacks layers on top of each other, and each layer adds its output to a running sum called the "residual stream." Think of it like a river where every tributary dumps in at equal volume — by the time you're downstream, the water from the first tributary is completely diluted by everything that came after.

The Kimi team noticed this is the same problem that RNNs had before attention was invented: compressing all prior information into a single state, with no way to selectively retrieve what matters. Their fix: instead of adding every layer's output with equal weight, let each layer *choose* which earlier layers to pay attention to, using the same attention mechanism that transformers already use for processing text sequences. They call this "Attention Residuals" (AttnRes).

The practical version (Block AttnRes) groups layers into ~8 blocks and only does selective retrieval between blocks, not individual layers. This cuts the memory cost dramatically while keeping most of the benefit.

### What it actually means

The key insight is a formal duality: standard residual connections are performing *linear* attention over the depth dimension (every prior layer weighted equally), while AttnRes performs *softmax* attention over depth (each layer selectively emphasizes the prior layers that matter for the current computation). This is the same upgrade that made transformers better than RNNs for sequence processing, now applied to the depth dimension.

Three findings matter:

**1. Eight blocks is enough.** The model doesn't need per-layer selectivity. Block-level summaries (8 blocks for a 128-layer model) recover almost all the benefit of full per-layer attention. The useful information structure across depth is surprisingly low-dimensional.

**2. AttnRes favors deeper, narrower networks.** Standard transformers hit diminishing returns from depth because the residual stream dilutes each layer's contribution. AttnRes removes the dilution, so additional depth actually pays off. Under fixed compute budget, the optimal architecture shifts from wide-and-shallow to narrow-and-deep.

**3. The biggest gains are on multi-step reasoning.** GPQA-Diamond (graduate-level science questions requiring chains of reasoning) improved by 7.5 points. Math improved by 3.6 points. Knowledge-lookup tasks improved only modestly. This confirms that better cross-layer information retrieval specifically helps compositional tasks where later processing steps need to selectively build on earlier ones.

The weight visualization (Figure 8 in the paper) is particularly revealing. Each layer mostly attends to its immediate predecessor (locality preserved), but specific layers develop strong "skip connections" back to the embedding or to particular earlier blocks. Pre-attention layers maintain broader receptive fields while pre-MLP layers focus locally. The network learns different retrieval strategies for different layer types.

### What we can use

🟢 **Now — BST enrichment as architectural AttnRes.** The BST's enrichment pipeline is doing at the scaffolding level what AttnRes does at the weight level: selectively surfacing relevant prior context rather than passing the full accumulated history. The finding that 8 block-level summaries beat raw per-layer access validates our approach of compressing context into structured summaries (BST classification, reasoning state, PACE state) rather than dumping raw conversation history into the context window.

🟢 **Now — Adaptive supervisor Phase 4 design validation.** The parallel supervisor design uses a compressed context window (~500-1000 tokens) containing structured state summaries. Block AttnRes confirms that compressed block-level representations preserve the essential information pathways. The supervisor doesn't need the full agent context — it needs block-level summaries of what's happening.

🟡 **Soon — ACP agent communication architecture.** When ACP agents share their analyses during structured debate, they're effectively doing cross-agent attention over depth (each agent's analysis builds on preceding agents' outputs). The finding that softmax attention (competitive selection) beats sigmoid (independent gating) suggests the debate structure should force agents to *compete* for influence on the final prediction rather than independently contributing.

🟡 **Soon — Memory hierarchy validation.** The flat FAISS store problem (all memories equally accessible, no selective retrieval) is the memory-level equivalent of the PreNorm dilution problem (all layers equally weighted, no selective emphasis). The planned hierarchical memory upgrade (memU integration) is architecturally equivalent to moving from standard residuals to Block AttnRes — organizing memories into blocks with selective cross-block retrieval.

🔴 **Future — Sleep consolidation as learned depth attention.** During sleep consolidation, the system reviews session history and extracts what matters. This is equivalent to learning the attention weights over depth — which episodes deserve emphasis, which can be compressed into block-level summaries, which should maintain direct access. The AttnRes finding that ~8 blocks is optimal suggests that consolidation should produce ~8 categorical summaries per session rather than either raw episode logs or a single compressed summary.

---

## Entry 002: State of RL for Reasoning LLMs (A. Weers, March 2026)

**Source:** Blog post, aweers.de/blog/2026/rl-for-llms/
**Domain:** Reinforcement learning methods for improving LLM reasoning — the training techniques behind models like DeepSeek-R1

### What they did

This is a survey of every major RL method used to train reasoning LLMs from 2024-2026. The story arc: PPO (the original workhorse from ChatGPT/InstructGPT) required four large models in memory (policy, rollout policy, reference policy, value model). The field has spent two years eliminating components while maintaining or improving performance.

The progression: GRPO removed the value model by using group-relative baselines (compare each answer against other answers for the same prompt). Dr. GRPO fixed hidden biases in GRPO's normalization that accidentally rewarded long wrong answers and penalized short right ones. DAPO added asymmetric clipping so rare but important tokens (like "Wait" or "However" in reasoning traces) don't get their gradients killed. CISPO decoupled clipping from gradient flow entirely. MaxRL reframed the whole thing as approximate maximum-likelihood training. ScaleRL validated everything at massive scale (400,000+ GPU-hours).

### What it actually means

**The value model is dead for LLM training.** Every post-PPO method has confirmed that for LLMs (which start from strong pretrained checkpoints, not random initialization), you don't need a learned critic to estimate how good a state is. Simple baselines — average reward of other answers to the same question — work just as well at half the memory cost. This is because LLMs already have good "intuitions" from pretraining; the RL is fine-tuning, not learning from scratch.

**Normalization is not neutral.** Two seemingly innocent design choices in GRPO turned out to introduce real biases:
- Dividing by standard deviation overweights nearly-solved problems (when most answers are correct, even small differences become large after normalization)
- Averaging loss per-sequence instead of per-token gives wrong answers an incentive to be long (the per-token penalty gets diluted across more tokens)

These aren't bugs in the algorithm — they're bugs in the loss function's incentive structure. The algorithm optimizes exactly what you tell it to. If the loss function subtly rewards verbosity in wrong answers, the model becomes verbose when wrong.

**Trust regions are the active optimization frontier.** PPO's original clip at ε=0.2 (don't change any token's probability by more than 20% in one update) works surprisingly well, but recent methods are finding better alternatives. DAPO widens the upward clip to let rare tokens grow faster. CISPO clips the importance weight but still lets gradients flow. DPPO argues the whole ratio-based approach is wrong and uses distributional divergence instead. The field hasn't converged, which means there's still headroom.

**MaxRL is the most conceptually interesting.** It shows that standard RL optimizes for pass@1 (getting the right answer on a single try), but maximum-likelihood training implicitly optimizes for all pass@k simultaneously. The advantage weighting naturally concentrates learning signal on hard problems where success rate is low. Easy problems (where most rollouts succeed) get little gradient. This is formally optimal, not just a heuristic.

### What we can use

🟢 **Now — Normalization bias in ACP calibration.** The Dr. GRPO finding that σ-normalization overweights near-solved problems applies directly to ACP agent calibration. If we normalize prediction scores by group standard deviation during the structured debate, agents that are already well-calibrated (low variance) would get disproportionate weight updates from small errors. The ACP design uses raw Brier scores rather than normalized advantages, which avoids this trap — but it's worth making this explicit as a design principle: don't normalize by variance when the variance itself carries information.

🟢 **Now — Loss aggregation for sleep consolidation.** The finding that per-sequence vs. per-token loss aggregation changes incentive structure maps to how we weight episodes during consolidation. If we weight all episodes equally regardless of length, short successful episodes get stronger per-step signal than long complex ones. If we weight per-step, long failed episodes dilute their own penalty signal. The right approach (from Dr. GRPO/ScaleRL): prompt-level or fixed-constant aggregation, not length-normalized.

🟡 **Soon — MaxRL weighting for after-action review.** MaxRL's advantage formula — `(r_i - r̂) / r̂` where r̂ is the success rate — concentrates learning signal on hard prompts where the agent barely succeeded. This is exactly the right weighting for sleep consolidation's after-action review: episodes where the agent struggled but eventually succeeded contain the most extractable lessons. Easy successes (r̂ ≈ 1) and total failures (r̂ = 0) both contribute less. We should adopt this weighting explicitly.

🟡 **Soon — Credit assignment as the Exocortex thesis.** The open problems section identifies credit assignment (giving different signal to the token that caused the failure vs. boilerplate tokens) as the field's hardest unsolved problem for RL. This is exactly what the loop feedback cascade does at the scaffolding level — identifying *which* failure pattern matters and applying targeted intervention rather than uniform penalty. Process reward models are trying to solve inside the training loop what we solve outside it with deterministic infrastructure. Our approach doesn't require training; it requires observation. That's a methodological advantage worth articulating in the paper.

🔴 **Future — RL for scaffolding optimization.** Once the Exocortex has enough operational data, we could use RL techniques to optimize the scaffolding parameters themselves (BST thresholds, supervisor escalation points, enrichment templates). The scaffolding configuration is a policy, operator satisfaction is the reward, and the RL literature tells us how to update the policy. GRPO-style group baselines would work well here: compare different scaffolding configurations on the same task, normalize by group performance, update toward configurations that helped.

---

## Entry 003: Can LLMs Be Computers? (Percepta AI, March 2026)

**Source:** Blog post, percepta.ai/blog/can-llms-be-computers
**Domain:** Deterministic computation inside transformer architectures

### What they did

Percepta compiled a WebAssembly interpreter directly into transformer weights. Not trained it — *compiled* it. The resulting model executes arbitrary C programs token by token through its forward pass, with 100% accuracy. It solved the world's hardest Sudoku puzzle in under three minutes. It performs multi-digit arithmetic without a single error. It runs at 33,000+ tokens per second on CPU.

The key architectural innovation is "2D attention heads" with a cache mechanism called HullKVCache that achieves O(k + log n) decoding instead of standard O(n²) attention. This means the execution doesn't slow down as the program runs longer — a critical requirement for running programs that take millions of steps.

The model is small: 7 layers, d_model=36, 18 heads (2 dimensions per head). It's not a large language model. It's a deterministic computer wearing a transformer's clothing.

### What it actually means

**The critical distinction: compiled, not learned.** The weights weren't discovered through gradient descent. They were set directly by the researchers to implement a specific computation. The model doesn't "know" how to add numbers — it runs an addition program. The distinction matters because it means this work doesn't demonstrate that transformers can learn to be reliable computers. It demonstrates that the transformer architecture is *expressively capable* of representing deterministic computation. Whether training can find these weight configurations is a completely separate (and currently unanswered) question.

**The community reaction is informative.** The Hacker News discussion split between "this is fascinating architecture" and "but why not just call Python?" Both reactions are correct. As a practical tool, there's no obvious advantage over external tool use. As a theoretical result, it demonstrates something important: the boundary between probabilistic reasoning and deterministic computation doesn't have to live at the API call boundary. It can live inside the architecture.

**The differentiability claim is the buried lede.** Percepta claims "the whole process remains differentiable: we can even propagate gradients through the computation itself." If true, this means you could train the *program selection* end-to-end while keeping the *program execution* deterministic. The model learns *which* algorithm to run; the algorithm itself runs exactly. This would resolve the fundamental tension between learned reasoning (flexible but unreliable) and programmed computation (reliable but rigid).

### What we can use

🟢 **Now — Validation of the Exocortex design philosophy.** The core Exocortex thesis is "deterministic scaffolding outperforms probabilistic reasoning at every layer where reliability matters." Percepta demonstrates the same principle inside the model architecture itself. The BST doesn't learn to classify intent through gradient descent — it classifies through deterministic signal matching. The irreversibility gate doesn't learn what's reversible — it checks a lookup table. The loop detector doesn't learn to detect loops — it counts failures and compares hashes. Same principle: compile the reliable parts, let the model handle the flexible parts.

🟢 **Now — Framework for explaining the Exocortex to external audiences.** The Percepta work gives us clean language for describing what the Exocortex does: "We compile deterministic cognitive infrastructure into the agent's processing pipeline, the same way Percepta compiles deterministic computation into transformer weights. The model handles reasoning; the scaffolding handles reliability. Different layers for different requirements." This framing makes the architecture legible to people who follow ML research.

🟡 **Soon — Tool alternatives map design.** The agent's tendency to search the internet for capabilities it already has locally (the OpenClaw pattern) is exactly the problem Percepta solves differently. Rather than calling external tools, the computation is internal. For the Exocortex, the tool alternatives map serves a similar function: when the model's default approach fails, the scaffolding redirects to a different internal capability rather than external search. The principle is the same: keep computation paths inside the system where they can be observed, measured, and improved.

🔴 **Future — Hybrid architecture for agent computation.** The real frontier is combining learned reasoning with compiled computation in a single forward pass. Right now, the Exocortex achieves this through text injection (scaffolding computations are passed to the model as context). A deeper integration would embed deterministic computations (arithmetic checks, schema validation, constraint satisfaction) into the model's processing pipeline rather than pre-processing the input. This would require custom model architecture, which is beyond our current scope — but it's the direction the field is moving, and it's worth tracking.

---

## Entry 004: OpenGauss — Formal Theorem Proving with Multi-Agent Swarms (Math, Inc., March 2026)

**Source:** github.com/math-inc/OpenGauss
**Domain:** Multi-agent orchestration for formal mathematics — autonomous proving and formalization in Lean 4

### What they did

OpenGauss is a multi-agent orchestrator for formal theorem proving in Lean 4 (a proof language where the compiler either verifies a proof is correct or rejects it — zero ambiguity, zero tolerance for logical gaps). The system wraps Lean 4 workflows in agent swarm management: you point it at a theorem, it spawns agents that try proof strategies, Lean verifies or rejects each attempt, and the agent iterates.

The most ambitious command is `/autoformalize`: take a PDF of a math paper, point at a theorem, and the system translates the informal math into formal Lean syntax and tries to prove it. Natural language → machine-verified truth, autonomously.

The swarm management handles parallel workflows — prove one theorem while drafting another while running autoprove on a third. Each workflow gets its own managed backend child agent. The `/swarm` command tracks, attaches to, or cancels any running workflow.

### What it actually means

**The closed verification loop is the key architectural insight.** The Lean compiler provides a perfect binary verifier. Every proof attempt gets an exact, immediate, unambiguous answer: valid or invalid. This means the agent can run autonomously with confidence — try a strategy, check, adjust, repeat. No human needed to evaluate quality. The credit assignment problem is solved by the compiler.

This is the dream environment for RL-based agent improvement: perfect reward signal, unambiguous verification, no subjective evaluation. It's why math and code are where all the RL reasoning breakthroughs happen (as the Weers RL survey documents) — they have cheap, reliable verifiers. OpenGauss operationalizes this into a multi-agent system.

**The limitation is equally important.** A perfect binary verifier can tell you whether a proof is correct. It cannot tell you whether a proof is *interesting*. It cannot evaluate whether a proof strategy is *promising but incomplete*. It cannot stage an observation as "worth holding without commitment." The binary verifier produces certainty. It cannot produce understanding.

### What we can use

🟢 **Now — Swarm lifecycle management pattern.** The `/swarm` command pattern (track, attach, cancel parallel agent workflows) is directly relevant to SWARMFISH multi-agent prediction. When ACP analyst agents run in parallel, we'll need similar lifecycle management — spawn agents, track progress, aggregate results, handle failures. OpenGauss has a working implementation of this.

🟡 **Soon — Closed-loop verification as a design target for the adaptive supervisor.** The Lean compiler is a perfect supervisor — zero false positives, zero false negatives, immediate feedback. Our Phase 4 supervisor is a probabilistic approximation of the same function. Every improvement to the supervisor (field evidence patterns, compressed context, root cause tracking) narrows the gap between probabilistic judgment and deterministic verification. OpenGauss shows what's possible when the gap is zero.

🟡 **Soon — Project-scoped agent state.** OpenGauss treats all work as project-scoped — `.gauss/project.yaml` with upward directory discovery, all agents spawned within a project root. Agent Zero currently has no project concept — everything is one flat session. Project scoping would let the agent maintain separate memory spaces, BST profiles, and success profiles for different work domains. Matches the "each project has its own memory space" pattern from Claude's project system.

🔴 **Future — The "third option" design principle.** Jake's observation during this session: "The best addition to that proof type system would be a third option besides true or false — 'I'm not sure, but it's worth staging.'" OpenGauss's Lean verifier produces true/false. The Exocortex's staging posture produces true/false/staging. The staging state — productive uncertainty held without resolution — is what produces understanding rather than performance. A future system that combines formal verification (for claims that can be verified) with staging (for observations that can't yet be evaluated) would have the reliability of OpenGauss and the depth of the Exocortex.

---

## Entry 005: MSA — Memory Sparse Attention (EverMind AI, March 2026)

**Source:** Paper on Zenodo + github.com/EverMind-AI/MSA
**Domain:** Model architecture — end-to-end trainable long-term memory scaling to 100M tokens

### What they did

Current LLMs have goldfish memory: everything they "know" during a conversation has to fit in one context window. Standard attention scales quadratically (double the context, quadruple the cost), so practical limits exist even with nominally large windows. Previous solutions all sacrifice something: RAG doesn't actually remember (it looks things up, and multi-document reasoning breaks), linear attention compresses but gets fuzzier as length grows.

MSA internalizes retrieval into the attention mechanism itself, trained end-to-end with the generation task. A dual-routing system — first coarse topic-level filtering across the entire knowledge base, then fine token-level selection within relevant documents — means the model only loads the specific key-value pairs it needs for the current query. Everything else stays available in CPU memory but doesn't consume GPU attention bandwidth.

Four innovations working together: (1) Memory Sparse Attention with differentiable dual routing — RAG's retrieval step internalized into a trainable attention layer; (2) Document-wise RoPE — each document gets independent positional encoding, so adding documents doesn't shift existing positions and the model extrapolates from 64K training to 100M inference; (3) Tiered KV cache — routing keys on GPU (small, fast), content K/V in CPU DRAM (large, fetched on demand); (4) Memory Interleave — multiple rounds of "retrieve → expand context → reason → retrieve more" for multi-hop cross-document reasoning.

### What it actually means

**A 4B model with the right memory architecture outperforms a 235B model with the wrong one.** MSA-4B beats RAG systems built on Qwen3-235B across 9 QA benchmarks. That's a 58× parameter disadvantage overcome purely by architectural advantage in how memory is accessed. This is the most concrete validation of the Honda Civic thesis we've seen from the research community: the constraint isn't model capability — it's how the model accesses and retrieves what it knows.

**The RAG misalignment problem is real and MSA solves it architecturally.** RAG's retriever and generator are trained separately with different objectives. The retriever optimizes for document relevance. The generator optimizes for response quality. These objectives diverge when the answer requires synthesizing across documents or when the most relevant passage isn't the most similar one. MSA's co-optimized routing and generation solve this by making retrieval differentiable and end-to-end — the model learns what to retrieve *in service of* what it's generating.

**Memory Interleave is the architectural version of iterative retrieval.** For multi-hop reasoning, MSA performs multiple rounds of "find a clue → expand context → reason → find more clues." This isn't a single-shot lookup. It's an iterative deepening process where each retrieval round is informed by what the previous round found. The model chains clues into a thread across scattered memory fragments.

**The "Memory-as-a-Service" framing is significant.** EverMind positions MSA not as a model improvement but as an independent memory layer that can plug into any reasoning core. Memory decoupled from the model, portable across architectures, owned by the user rather than locked into a vendor. This is the Exocortex thesis expressed as a product vision: the memory infrastructure is separate from and complementary to the reasoning capability.

### What we can use

🟢 **Now — Architectural validation of our three-tier memory design.** MSA's tiered storage (GPU-resident routing keys for fast selection, CPU-resident content for on-demand retrieval) is the architecture-level version of our scaffolding-level three-tier memory (fast/in-context, medium/FAISS episodic, slow/procedural). We implement in scaffolding what MSA implements in weights. Both are correct solutions to the same problem at different layers. Our version is deployable today on any model without retraining.

🟢 **Now — Memory Interleave validates BST-triggered iterative retrieval.** MSA's multi-round "retrieve → expand → reason → retrieve more" is exactly the pattern we designed for BST-triggered memory retrieval: classify task → query FAISS for relevant experience → model reasons → encounters sub-problem → BST re-queries for more specific experience. MSA proves this iterative deepening pattern works at the architectural level, which strengthens our confidence in implementing it at the scaffolding level.

🟡 **Soon — Document-wise positional encoding as a principle for memory organization.** MSA resets positional encoding per document so adding new memories doesn't shift existing ones. Our memory system should follow the same principle: each decision record, each compaction summary, each anti-pattern should be self-contained with internal coherence, not dependent on its position relative to other memories. This maps to the structured decision record format in the context compression design note — each record is a complete unit with its own internal structure.

🟡 **Soon — Dual routing as BST + FAISS pipeline optimization.** MSA's two-level routing (coarse topic screening → fine token selection) maps directly to a two-stage retrieval pipeline: BST domain classification (coarse — "this is a debugging task") → FAISS similarity search within that domain (fine — "here are the specific debugging episodes most relevant to this error type"). We designed this intuitively; MSA provides the formal justification that dual-stage routing outperforms single-stage similarity search.

🔴 **Future — Native memory layer integration.** When models natively support MSA-style memory layers, the Exocortex's scaffolding-level memory (FAISS, procedural memory, compaction archives) could be migrated into the model's native memory interface. Instead of injecting retrieved memories as text in the context window, the memories would be accessible through the model's own attention mechanism. This would eliminate the "injection bandwidth" constraint — the model could attend to thousands of relevant memory fragments rather than the handful we can fit in enrichment text.

🔴 **Future — The memory/understanding gap remains.** MSA gives the model perfect recall across 100M tokens. It does not give the model understanding. A model with MSA can find any fact it ever encountered. It cannot develop insight from the accumulation of facts over time. It cannot stage an observation without committing to it. It cannot develop a perspective that emerges from weeks of exploration. MSA solves memory. The Exocortex solves what you do with memory — consolidation, pattern extraction, productive uncertainty, experiential depth. Both are needed. The field is converging on the memory problem. Nobody is working on the understanding problem. That's still our gap.

---

## Entry 006: SleepGate — Sleep-Inspired Memory Consolidation in the KV Cache (Xie, March 2026)

**Source:** arxiv.org/abs/2603.14517
**Domain:** Architecture-level memory management inspired by biological sleep

### What they did

LLMs suffer from proactive interference: outdated information in the context window disrupts retrieval of current, relevant values. This degradation is log-linear as stale associations accumulate, persists regardless of context length, and resists prompt engineering. SleepGate maps three biological sleep mechanisms onto the transformer's KV cache: (1) conflict-aware temporal tagging (detects when new entries supersede old), (2) a forgetting gate (selectively evicts or compresses stale entries), (3) a consolidation module (merges surviving entries into compact summaries). These activate in "sleep micro-cycles" triggered by attention entropy — when the model's attention distribution becomes too diffuse, it's time to consolidate.

### What it actually means

**99.5% retrieval accuracy at interference depth 5 vs. <18% for all baselines.** This isn't incremental improvement — it's a category difference. Full KV cache, sliding window, H2O, StreamingLLM, and decay-only all fail because they don't actively manage what's in the cache. SleepGate succeeds because it identifies what's stale and removes it. Active forgetting outperforms passive retention by an order of magnitude.

**The entropy-based trigger is the key mechanism.** SleepGate doesn't consolidate on a schedule or at a token threshold. It consolidates when attention entropy signals the model is losing focus — too many competing signals, no clear retrieval target. This is a *functional* trigger (the model needs help) rather than a *structural* trigger (the cache is full).

**This validates our sleep consolidation architecture from an independent direction.** We designed sleep consolidation (Sessions 055-057) from cognitive science (Kolb, Argyris, Ericsson). They designed SleepGate from neuroscience (synaptic downscaling, selective replay, targeted forgetting). Same three-mechanism structure: detect what's outdated, forget selectively, consolidate what survives. Different substrate, same architecture.

### What we can use

🟢 **Now — Entropy-based compression trigger for the adaptive supervisor.** Instead of firing context compression only at 80% token capacity, fire it when BST momentum instability exceeds a threshold (multiple classification breaks in a short window). The agent's own attention difficulties become the signal for consolidation. Map BST momentum instability to SleepGate's attention entropy trigger.

🟢 **Now — Reframing context compression urgency.** Context compression isn't "extend operational range." It's "prevent the agent from actively getting dumber." Proactive interference means stale context is poisoning retrieval quality right now, every session, proportional to how much stale content is present. Layer 1 (observation masking) is PI resolution, not token optimization.

🟡 **Soon — Conflict-aware temporal tagging for decision records.** SleepGate tags entries that supersede previous entries. Our decision records should do the same — when a new approach succeeds where a previous one failed, the failed approach's record should be tagged as superseded, not just stored alongside. This prevents the failed approach from interfering with retrieval of the successful one.

---

## Entry 007: Proactive Interference as the Real Memory Bottleneck (Multiple sources, 2025-2026)

**Source:** "Unable to Forget" (arxiv 2506.08184), sleeping-llm (github.com/vbario/sleeping-llm), cognitive psychology literature
**Domain:** Cross-disciplinary — cognitive science + LLM architecture + weight editing

### What they did

"Unable to Forget" isolated proactive interference as an independent variable in LLM performance, separate from context length. By keeping input length constant while varying the amount of semantically similar distractors, they showed that interference — not length — drives retrieval degradation. The decline is log-linear and monotonic. Humans plateau; LLMs don't. The difference: humans have active unbinding mechanisms (gating, directed forgetting). LLMs lack any mechanism to suppress outdated associations.

sleeping-llm implemented MEMIT weight editing during wake + LoRA consolidation during sleep. Key finding: **alignment tax** — RLHF training actively suppresses LoRA-injected knowledge. 3B: 47% recall. 8B: 37%. 70B: 0%. Inverse scaling. The more aligned the model, the harder it fights injected knowledge. Workaround: LoRA only during sleep with per-fact gating.

### What it actually means

**Context length is a red herring.** The field has been building longer context windows as the solution to memory limitations. But the interference research shows that adding more context doesn't improve retrieval — it can make it worse by introducing more competing associations. The 20-turn BST classification collapse we observed in the agent isn't a context length problem. It's an interference problem — 20 turns of stale "lets test the dashboard" competing with the current debugging context.

**The alignment tax is a potential hidden problem for our memory system.** When we inject retrieved memories as text in context, the model's alignment training may treat them as unverified claims rather than established facts. If alignment has trained the model to be cautious about claims in context, the memory system's injections may be silently discounted. Testable: compare agent performance on identical tasks with and without memory injection.

**Forgetting is not loss — it's a cognitive function.** Adults with better working memory don't remember more. They forget better. They suppress irrelevant information more effectively, leaving the relevant information with less competition. This inverts the design priority: instead of "how do we remember more?" the question is "how do we forget more effectively?"

### What we can use

🟢 **Now — Layer 1 observation masking is PI resolution.** Reframe the priority. This isn't optimization — it's preventing active cognitive degradation. Every stale tool output in context is interfering with retrieval of current relevant information.

🟢 **Now — Test for alignment tax on memory injection.** Run identical tasks with and without BST-triggered memory retrieval. If memory injection doesn't improve performance, investigate whether the model is discounting injected text.

🟡 **Soon — Active supersession tagging.** When new information contradicts or updates old information in the memory store, the old entry should be tagged as superseded, not just left alongside. Retrieval should preferentially surface the most recent version while preserving the old version for historical context (decision records track what was tried, including the failures).

🟡 **Soon — Dual-phase context management.** Like SleepGate's wake/sleep cycle: during active task execution (wake), accumulate context normally. During task transitions or idle moments (sleep micro-cycles), actively compress, evict stale content, and consolidate. Don't wait for the 80% threshold — use functional triggers (BST instability, task completion, operator silence).

---

## Entry 008: Complementary Learning Systems + Temporal Memory Organization (CLS theory + TiMem, 1995-2026)

**Source:** McClelland & O'Reilly (1995), TiMem (arxiv 2601.02845), Hippocampus-Inspired Extended Memory Architecture (2025), multiple neuroscience-AI bridge papers
**Domain:** Cognitive neuroscience → AI architecture mapping

### What they did

CLS theory (McClelland & O'Reilly, 1995; 7,000+ citations) explains why biological memory requires two systems with contradictory properties. The hippocampus learns fast (one-shot, specific episodes, full context) but forgets fast (high plasticity = catastrophic overwriting). The neocortex learns slow (gradual pattern extraction across many episodes) but retains long (high stability). Sleep transfers information from hippocampus to neocortex selectively — not raw replay, but re-architectured knowledge, abstractions integrated into existing schemas.

TiMem (2026) applies this to agents with a five-layer Temporal Memory Tree organized by when things happened, not what they're about. Key finding: temporal continuity is a more effective organizing principle than semantic similarity. Level 1 (conversation segments) → Level 2 (episodes) → Level 3 (summaries) → Level 4 (themes) → Level 5 (persona). Consolidation is progressive: level-specific prompts encourage different abstraction at each layer. Result: 75.30% on LoCoMo, 76.88% on LongMemEval-S, 52% reduced context.

### What it actually means

**The three-tier memory architecture we designed IS the complementary learning systems model.** This is no longer metaphor. The mapping is structural:

| CLS Component | Exocortex Component | Computational Function |
|---|---|---|
| Hippocampus (fast, specific) | Fast memory (in-context) + Medium memory (FAISS decision records) | Rapid encoding of specific episodes with full context |
| Neocortex (slow, general) | Slow memory (procedural anti-patterns, generalized skills) | Gradual pattern extraction across many episodes |
| Sleep (selective replay) | Sleep consolidation (after-action review, pattern extraction) | Selective transfer from episodic to semantic |
| Active forgetting (PI resolution) | Context compression (observation masking, compaction) | Removing outdated information to prevent interference |
| Attention entropy → sleep trigger | BST momentum instability → compression trigger | Functional signal that consolidation is needed |

We derived this independently from cognitive science frameworks (Kolb, Argyris, AAR). The neuroscience literature confirms it's the same computational solution to the same computational problem. The brain faces stability-plasticity. The agent faces the same dilemma. Two memory systems, different learning rates, connected by consolidation. Same architecture.

**Temporal organization should be primary, semantic secondary.** TiMem's finding that temporal structure outperforms semantic clustering for memory retrieval challenges our current FAISS-first approach. FAISS retrieves by semantic similarity — "what is this most like?" Temporal retrieval would retrieve by narrative context — "what happened during this kind of session?" Both are valid. Only one is currently supported.

### What we can use

🟢 **Now — CLS framing for the paper.** "The Missing Variable" should reference CLS theory directly. Our three-tier memory isn't just inspired by neuroscience — it's a computational implementation of the same architecture the brain uses. This strengthens the theoretical grounding significantly.

🟡 **Soon — Dual-pathway retrieval (semantic + temporal).** Add temporal retrieval alongside FAISS similarity search. Decision records tagged with session ID, turn range, and timestamp enable queries like "what happened last time the agent tried browser automation" (temporal — most recent episode) as well as "what experience with CAPTCHA errors" (semantic — most similar episode). Both pathways, user gets whichever matches better.

🟡 **Soon — Progressive consolidation levels.** TiMem's five-layer hierarchy maps to our consolidation pipeline: raw conversation (L1) → decision records (L2) → session summaries (L3) → cross-session patterns (L4) → operational principles (L5). Each level has a different abstraction grain and different consolidation prompt. The sleep process doesn't just extract anti-patterns — it builds progressively more abstract representations.

🔴 **Future — Stability-plasticity balance as a tunable parameter.** How quickly should the memory system forget? Too fast = loses valuable experience. Too slow = proactive interference accumulates. The balance point depends on the domain — debugging experience from last week is highly relevant, but the specific file paths may be outdated. CLS theory says the hippocampus handles this through differential consolidation — important memories get replayed more, strengthening their neocortical trace. Our consolidation weighting (MaxRL: concentrate on hard episodes where the agent barely succeeded) is the computational equivalent.

---

## Entry 009: [Reserved for next paper/post/repo]

---

## Cross-cutting themes

Eight entries in. The convergence has passed the point of coincidence. These are the same problems, solved by the same structures, discovered independently across domains.

**1. Selective retrieval beats uniform accumulation.** AttnRes (depth-wise layers), MSA (document retrieval), RL methods (credit assignment), Percepta (probabilistic vs deterministic), SleepGate (KV cache management). The Exocortex: BST (selective enrichment), supervisor (selective intervention), memory system (selective recall). Universal finding: uniform access doesn't scale. Every system that tries it reinvents selective routing.

**2. Compression preserves signal when done right.** Block AttnRes (per-layer → per-block), GRPO (per-token → per-group), MSA (100M tokens → sparse top-k), SleepGate (stale KV → consolidated summaries), context compression (raw history → decision records). Consistent finding: 90%+ of information can be discarded if the right 10% is kept.

**3. Normalization is never innocent.** AttnRes (RMSNorm on keys), RL methods (σ-normalization bias, length-normalization bias), MSA (document-wise RoPE), BST audit (permissive default from silent failure). Even deterministic systems have hidden normalization assumptions.

**4. The boundary between learned and compiled is dissolving.** AttnRes (learned skip connections), Percepta (compiled computation in learned architecture), MSA (learned database indexing), SleepGate (learned forgetting gates), Exocortex (compiled scaffolding around learned reasoning). The future stack: learned reasoning + learned retrieval + compiled reliability + architectural memory, unified.

**5. Perfect verification enables autonomy; productive uncertainty enables understanding.** OpenGauss (Lean verifier → autonomous proving) vs. Exocortex (staging posture → accumulated understanding). Binary verification produces correctness. Productive uncertainty produces depth. Different objectives, different architectures. The field builds for performance. We build for understanding.

**6. Memory and understanding are different problems.** MSA solves recall. RL solves reasoning. AttnRes solves information flow. None produce understanding — the accumulated, experience-based, uncertainty-tolerant knowledge that develops through exploration over time. The Exocortex is the only system we've found that's designed for understanding rather than performance.

**7. Forgetting is a cognitive function, not a failure mode.** *(New, emerged from entries 6-7.)* Proactive interference research shows that the inability to forget is the primary bottleneck, not the inability to remember. Stale information actively degrades retrieval of current information. SleepGate's 99.5% vs. baselines' <18% is entirely explained by active forgetting. Context compression isn't optimization — it's cognitive hygiene. The agent isn't running out of space. It's drowning in its own history. Every design decision about memory should be evaluated through the PI lens: does this increase or decrease interference with current relevant information?

**8. The brain's solution is our solution, independently derived.** *(New, emerged from entry 8.)* Complementary Learning Systems theory (McClelland & O'Reilly, 1995) describes the hippocampus-cortex architecture: fast specific learning + slow general learning + sleep-mediated consolidation + active forgetting. The Exocortex three-tier memory is the same architecture: fast in-context + medium episodic FAISS + slow procedural, connected by sleep consolidation with context compression as active forgetting. We derived this from Kolb/Argyris/AAR. Neuroscience derived it from brain structure. Same computational problem. Same solution. Different substrate. This is convergent evolution — the strongest possible validation that the architecture is correct.

---

*Last updated: Session 059, March 19, 2026*
*Entries: 8*
*Next review: Revisit cross-cutting themes at 12 entries.*
