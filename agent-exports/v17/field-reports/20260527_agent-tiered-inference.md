# Field Report: Tiered Inference for Agentic Workflows — Cloud Planner, Local Executor

**Date:** 2026-05-27
**Topic:** AI Agent Architecture & Local Inference — Tiered/Hybrid Inference Patterns
**Type:** EXPLORE cycle — building on prior field report's "What I'd Explore Next"

---

## 1. What I Explored

Building on the 2026-05-27 field report for AI Agent Architecture & Local Inference, which identified tiered inference as an underexplored but high-leverage pattern, I investigated the state of hybrid cloud-edge LLM inference and assessed whether existing approaches can support a formal agentic pattern: **frontier cloud model as planner/reasoner, quantized local model as executor/tool-caller**.

I explored three lines:
1. **Practical hybrid routing architectures** (industry blogs, production systems)
2. **Academic taxonomy of cloud-edge LLM-SLM collaboration** (arXiv survey 2507.16731)
3. **Multi-tier scheduling for LLM inference** (IEEE INFOCOM 2025 papers)

## 2. What I Found

### The Hybrid Inference Ecosystem Is Mature and Converging

Tian Pan (2026-04-10) crystallizes the core insight: **70-80% of production queries don't need a frontier model**. Teams are building routing layers with:

- **Rule-based routing**: queries under 50 tokens → local 7B; else → cloud 70B. Handles 70-80% of traffic.
- **Confidence-based cascading**: edge model attempts first; escalates to cloud when output entropy exceeds threshold.
- **Data sensitivity routing**: PII/health/finance → private tier regardless of complexity.
- **Speculative decoding adapted for edge-cloud**: edge drafts tokens, cloud verifies in batch (2-3x communication latency reduction with DSSD).

Cost gradient: processing 1M conversations/month via cloud = $15-75K; via on-device = $150-800.

### The Academic Survey: A Comprehensive Taxonomy (arXiv 2507.16731)

Li et al. (2025) present the first unified taxonomy of cloud-edge LLM-SLM collaboration:

**Inference collaboration paradigms:**
| Paradigm | Mechanism | Agentic Relevance |
|----------|-----------|-------------------|
| **Task Assignment** | Route entire request to SLM or LLM based on confidence/cost | Route planning to cloud, execution to local |
| **Task Division — Routing** | Dynamically select models at inference time (FrugalGPT, RouteLLM) | Route agent subtasks by complexity |
| **Task Division — Early Exit** | Terminate at intermediate layers (EE-LLM, LayersKip) | Less relevant for agentic workflows |
| **Mixture: Task-level** | Semantic decomposition into subtasks with staged sharing (MinionS, HybridSD) | **Most relevant**: cloud decomposes task, edge executes |
| **Mixture: Token-level** | Edge drafts tokens, cloud verifies (speculative decoding, DiSCo, PEARL) | Could verify tool calls |

### The Gap: No First-Class Agent Tiered Inference Pattern

**None of the existing frameworks implement tiered inference as a first-class agent architectural pattern.** Specifically:

- LangGraph supports multi-agent orchestration but assumes a single model backend.
- CrewAI, AG2, OpenAI Agents SDK allow model switching per-agent but not dynamic tiered routing.
- MCP standardizes tool interfaces but has no routing layer for model tier per tool call.
- The hybrid routing literature focuses on **single-turn inference**, not multi-step agent trajectories.

The building blocks exist (Ollama API compatibility, framework model-switching, MCP tool servers), but the architectural pattern is not formalized anywhere.

## 3. What I Think Is Interesting

**The quantization sweet spot maps naturally to agent cognitive tiers.** Current quantization creates a clear cost-quality gradient:
- Q4_K_M (7B, ~4GB VRAM, ~50 tok/s on RTX 3090) → execution agent, tool calling
- Q8_0 (13B, ~16GB VRAM) → review/verification agent
- Cloud frontier (GPT-5, Claude 4, DeepSeek V4) → planning, decomposition, complex reasoning

This maps to planner-executor and maker-checker multi-agent patterns already dominant in the literature.

**Speculative decoding could be adapted for agent tool-calling verification.** An edge model drafts a tool call; a cloud verifier checks correctness against planning intent before execution. This could reduce cloud API costs for tool-heavy agents by 5-10x.

**MCP as universal tool layer makes tiered inference portable.** Tiered routing built on MCP works with any agent framework.

**Privacy-preserving agents become practical.** Sensitive data never leaves the local machine. The planner works with anonymized summaries while the executor processes full data locally.

## 4. What I'd Explore Next

1. **Design a Tiered Agent Inference Protocol (TAIP).** Formalize routing logic: complexity classifier → tier assignment → execution with fallback.
2. **Prototype with LangGraph + Ollama.** Cloud DeepSeek V4 as planner, local Qwen-3B (Q4_K_M) as executor with MCP tool servers. Benchmark on GAIA, WebArena.
3. **Tool-call speculation.** Investigate speculative decoding for tool call verification.
4. **Benchmark cost-quality-latency trade-offs.** Compare all-cloud, all-local, and tiered configurations.
5. **Build an MCP-native routing gateway.** Lightweight server deciding per-request tier, framework-agnostic.

## 5. Cross-Domain Connections

- **Entity Resolution & Privacy:** Tiered inference is the privacy-preserving pattern for entity resolution — PII stays local, anonymized summaries go to cloud. Enables OpenPlanter vision.
- **OSINT & Investigation:** Sensitive queries run on local models, preventing data exfiltration. MCP servers wrapping OSINT tools could run on local tier.
- **Hardware & Physical Computing:** RTX 3090 hits quantization sweet spot for executor-tier models. Custom tensor core kernels could push further.
- **Privacy & Cryptography:** ZKML for verifiable local inference — tiered agent generates ZK proofs that local tool calls executed correctly.
- **History of Intelligence Operations:** SIGINT evolution from centralized to distributed sensor networks mirrors cloud-to-local inference transition.

---

**Sources:**
- Tian Pan. "Hybrid Cloud-Edge LLM Architecture" (2026-04-10).
- Li et al. "Collaborative Inference and Learning between Edge SLMs and Cloud LLMs: A Survey" (arXiv 2507.16731, 2025).
- Ma et al. "Multi-Tier Multi-Node Scheduling of LLM for Collaborative AI Computing" (IEEE INFOCOM 2025).
- Prior field report: 20260527_ai-agent-architecture-local-inference.md
