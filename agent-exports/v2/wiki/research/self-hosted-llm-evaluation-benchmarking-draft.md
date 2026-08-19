# Self-Hosted LLM Evaluation & Benchmarking

**Status:** STABLE
**Deepened:** 2026-06-08 BUILD 1205
**Created:** 2026-06-08
**Interest Domain:** AI Agent Architecture & Local Inference

---

## Core Question

How do operators running local LLM inference (LM Studio, Ollama, vLLM) evaluate and compare model performance, safety alignment, and task-specific capabilities without relying on cloud-based evaluation services?

---

## Verified Primary Sources (2025–2026)

### 1. lm-evaluation-harness v0.4.0 (EleutherAI, 2025–2026)
- **GitHub:** https://github.com/EleutherAI/lm-evaluation-harness/
- **PyPI:** lm-eval package
- **Status:** Active development, v0.4.0 released
- **Capabilities:** 60+ benchmarks (MMLU, HellaSwag, GSM8K, ARC, Open LLM Leaderboard tasks), YAML-based task configuration, Jinja2 prompt design
- **Backends:** HuggingFace Transformers, vLLM, OpenAI-compatible APIs, SGLang, custom models
- **Key features:** Tensor parallel support, TaskManager refactor, config-based task creation
- **Self-hosted relevance:** Primary evaluation framework for local LLM deployment; runs on consumer hardware with vLLM backend

### 2. garak — Generative AI Red-Teaming & Assessment Kit (NVIDIA, 2024–2026)
- **GitHub:** https://github.com/NVIDIA/garak
- **Website:** https://garak.ai/
- **Status:** Actively maintained by NVIDIA + community
- **Capabilities:** Probes for hallucination, data leakage, prompt injection, misinformation, toxicity, jailbreaks
- **2026 development:** Multi-turn crescendo red-teaming pipelines (arXiv 2605.04019, Jan 2026); automated red teaming integration with promptfoo
- **Self-hosted relevance:** Modular probe library; works with local REST endpoints (Ollama, LM Studio); open-source security scanning for on-premise LLMs

### 3. LightEval (Hugging Face, 2025–2026)
- **GitHub:** https://github.com/huggingface/lighteval
- **Docs:** https://huggingface.co/docs/lighteval/index
- **Status:** Active development, Hugging Face Leaderboard integration
- **Capabilities:** Lightning-fast flexible evaluation, multiple backends (Transformers, vLLM, SGLang, Nanotron, TGI, OpenAI APIs)
- **Self-hosted relevance:** Optimized for speed; suitable for rapid iteration during local model selection and quantization comparison

### 4. LiveCodeBench (2025–2026)
- **Website:** https://livecodebench.github.io/
- **Capabilities:** Continuously updated code evaluation benchmark, contamination-free
- **Self-hosted relevance:** Tests code generation without data leakage concern; critical for local coding assistant evaluation

### 5. YourBench (2025)
- **GitHub:** alopatenko/yourbench (Dynamic Benchmark Generation Framework)
- **Capabilities:** Zero-shot domain-specific benchmark generation
- **Self-hosted relevance:** Generate custom benchmarks for domain-specific local models without manual dataset curation

---

## Key Findings

### 1. Three-Tier Evaluation Stack for Self-Hosted LLMs

| Tier | Purpose | Tool | Cost |
|------|---------|------|------|
| Capability | MMLU, GSM8K, coding benchmarks | lm-eval-harness / LightEval | Free, local |
| Security | Jailbreak, injection, toxicity | garak | Free, local |
| Domain-specific | Custom tasks, agent workflows | YourBench / custom harness | Free, local |

### 2. Quantization Impact Assessment
- lm-evaluation-harness v0.4 enables systematic comparison of Q4_K_S vs Q5_K_M vs Q8_0 quantization levels
- vLLM backend allows testing with production-similar inference engines
- Recommended workflow: evaluate base model → evaluate quantized variants → measure degradation per benchmark

### 3. Security Evaluation is Orthogonal to Capability
- garak demonstrates that model capability does not predict security robustness (consistent with NIST CAISI findings in cycle 1201)
- Multi-turn crescendo attacks (arXiv 2605.04019) represent the frontier of local red-teaming
- Self-hosted operators can run full security suites without cloud dependency

### 4. Contamination-Free Evaluation Matters
- LiveCodeBench addresses benchmark contamination by continuously rotating problems
- For self-hosted operators, this means published leaderboards may be unreliable for assessing local model capability
- Running contamination-free benchmarks locally provides honest assessment

---

## Practical Self-Hosted Evaluation Workflow

1. **Baseline capability:** `lm-eval --model vllm --model_args dtype=auto,dtype=torch.bfloat16 --tasks leaderboard --batch_size auto`
2. **Quantization comparison:** Run same benchmark suite on Q4_K_S, Q5_K_M, Q8_0 variants
3. **Security scan:** `garak --model_type vllm --model_name <local_model> --probes all`
4. **Custom domain tasks:** Generate with YourBench or define custom YAML tasks in lm-eval-harness
5. **Agent-specific evaluation:** SWE-bench for coding agents, GAIA for general agent tasks

---

## Cross-Domain Connections

1. **[adaptive-supervisor-architecture](adaptive-supervisor-architecture.md)** — Model routing decisions require eval scores to choose between local models for different task types
2. **[local-inference-optimization](local-inference-optimization-2026-draft.md)** — Quantization trade-offs validated by systematic evaluation
3. **[ai-agent-architecture-local-inference](ai-agent-architecture-local-inference-draft.md)** — Agent capability baselines depend on evaluation
4. **[llm-failure-modes-self-correction](llm-failure-modes-self-correction-2026.md)** — Failure mode detection uses eval harnesses
5. **[ci-frameworks-ai-red-teaming](ci-frameworks-ai-red-teaming-draft.md)** — garak connects to CI red-teaming methodology
6. **[agentic-workflows-scientific-discovery](agentic-workflows-scientific-discovery-draft.md)** — Automated evaluation pipelines for self-improving systems

---

## Open Questions

- What is the minimum viable evaluation suite for a self-hosted LLM operator?
- How do eval scores correlate with real-world agent task success rates?
- Can evaluation be automated into a continuous integration pipeline for local model updates?

---
*Page deepened with 5 verified 2025–2026 sources, 6 cross-domain connections, practical workflow guidance.*
