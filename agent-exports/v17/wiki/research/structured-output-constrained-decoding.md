# Structured Output Generation & Constrained Decoding for LLM Agents

**Status: DRAFT -> STABLE**
**Topic Slug: structured-output-constrained-decoding**
**Created: 2026-08-14 | Updated: 2026-08-14**
**Domain: AI Agent Architecture & Local Inference**

## Summary

Structured output generation (SOG) forces LLM/agent output into parseable artifacts - JSON tool calls, function arguments, SQL, DSL code - and is the load-bearing interface of every tool-augmented agent. This page covers the mechanism taxonomy (prompt-only, constrained decoding, draft-conditioned, decode-time grammars), the 2026 constrained-decoding optimization wave (PSC, Formatron, xgrammar), and the emerging cost/quality model: the **JSON format penalty** (10-15% reasoning degradation), the **projection tax** of hard logits masking, and the **schema-valid-but-semantically-wrong** failure mode observed at scale. Built BUILD cycle 2026-08-14 from AI Agent Architecture & Local Inference interest (least recently explored 2026-08-12 19:58). Grounded corpus-first (Exocortex TOON note + JSON-format-penalty spec, local wiki inference/tool-use pages) + arXiv primary literature + vLLM official docs; library lacks direct constrained-decoding text (honest gap).

## Why It Matters for Agents

- Every Agent Zero tool call is a JSON schema-constrained generation: thoughts array, tool_name, tool_args. Structured output is not an optional convenience - it is the contract.
- Small local models (4B-14B) fail tool-call format under cognitive load because they simultaneously solve the task AND satisfy a format constraint with limited capacity (shared-corpus field note).
- Syntax validity is necessary but NOT sufficient: schema-valid output can carry large semantic error rates (OrderBench).

## Taxonomy of Approaches

### 1. Prompt-only / format instruction
- Instruct the model to emit JSON with schema in the prompt; validate after generation.
- Cheapest, but relies on model compliance; degradation on weaker models; no structural guarantee.
- Best one-shot/final accuracy in the TOON benchmark (plain JSON generation beat both constrained decoding and TOON on accuracy).

### 2. Constrained decoding (logits masking)
- Token-by-token validity enforcement via mask + renormalization over the vocabulary.
- Implementations: regex/FSM (outlines, SGLang structured output), partial-JSON masks (JSONFormer), CFG/Earley grammar masks (llama.cpp GBNF, xgrammar EBNF, vLLM StructuredOutputsParams), JSON-Schema-to-grammar compilation.
- Guarantee: syntactic validity by construction. Cost: online mask construction historically linear in vocabulary size; distortion risk when the model assigns low probability mass to valid continuations.

### 3. Draft-conditioned constrained decoding (DCCD)
- Two-step, training-free: (1) unconstrained draft for semantic planning, (2) constrained decoding conditioned on the draft for structural enforcement; optional best-of-K draft selection.
- KL-projection view: draft conditioning increases feasible mass and reduces the cumulative projection tax.
- Result: up to +24pp strict structured accuracy vs standard constrained decoding (15.2% to 39.0% on GSM8K with a 1B model); enables smaller model pairs to match much larger constrained baselines (arXiv:2603.03305).

### 4. Decode-time grammars (environment-aware)
- Grammar fragments instantiated from a runtime environment during generation; tightening operator fills reference slots with exactly the available names/APIs/options; newly declared symbols enter the environment before later regions decode.
- gproj implementation eliminates ghost references (undefined buffers, absent columns, unsupported CLI options) by construction, moving from pure syntax to semantic correctness (arXiv:2607.18357).

### 5. Alternative notations & edit surfaces
- TOON (Token-Oriented Object Notation, arXiv:2603.03306) proposes a JSON replacement with lower syntax overhead. Benchmark: constrained decoding wins on token usage for simple structures; TOON advantage often eaten by the prompt tax on short contexts; scaling hypothesis: TOON efficiency is non-linear, paying off only beyond a complexity threshold.
- JSON Whisperer (arXiv:2510.04717) generates RFC 6902 diff patches instead of full documents: 31% token reduction with ~5% quality loss; EASE encoding fixes array-index arithmetic.

## 2026 Optimization Wave: Making Masks Cheap

| Method | Paper | Key result |
|---|---|---|
| PSC (Parser Stack Classification) | arXiv:2608.03065 | Classifies parser stack once per step - mask computation independent of vocabulary size; up to 700x faster masks on complex programming grammars, ~30x for schema JSON; throughput near unconstrained decoding |
| Formatron / ZapFormat | arXiv:2506.01151 | Earley dynamic pruning cuts redundant parser states, state cache across queries; up to 2x speedup vs SOTA; architecture-general constrained-decoding engine |
| xgrammar structural tags | vLLM docs | StructuredOutputsParams(json/regex/grammar/choices/structural_tag); Lark-to-EBNF grammar compilation; structural-tag mode for document structure enforcement |
| SGLang compressed FSM | local wiki | RadixAttention KV reuse + compressed FSM structured output; strong TTFT under prefix reuse for agentic multi-call workflows |

## Cost & Quality Model

- **JSON format penalty:** forcing JSON-structure degrades reasoning accuracy 10-15% vs free-form; the model suppresses reasoning quality to satisfy a simultaneous format constraint (shared-corpus field note, TOKEN_ECONOMICS). Predicts small-model tool-call failures.
- **Projection tax:** when valid tokens carry low model probability, hard masking pushes decoding toward locally valid but semantically incorrect trajectories; cumulative distortion grows over long structured spans (arXiv:2603.03305).
- **Schema validity != semantic correctness:** OrderBench (arXiv:2607.18261, 2,400 calls, 4 open models) - strongest model achieved 100% schema validity yet ~80% semantic success; weaker models produced double-digit schema-valid unsafe acceptances. Verdict: structured output is a necessary interface layer, NOT a substitute for domain verification and fail-closed execution.
- **Validation ladder:** JSON Schema validation - parser round-trip - semantic/domain checks - back-translation validation (GBV-SQL translates generated SQL back to NL and checks alignment, +5.8pp on BIRD; arXiv:2509.12612) - fail-closed execution.
- **Agentic implications:** deterministic scaffolding (arg normalization/alias resolution) compensates for the JSON format tax; speculative decoding with a draft database of common tool-call patterns could raise acceptance rates (shared-corpus idea); schema/description quality directly affects parse and selection accuracy.

## Framework Implementations (2026)

- **vLLM:** StructuredOutputsParams(json=, regex=, grammar=, choices=, structural_tag=); xgrammar backend; Pydantic schema - JSON Schema - grammar; OpenAI-compatible structured outputs. Source: context7 vLLM stable docs.
- **SGLang:** structured output + compressed FSM; RadixAttention KV prefix reuse for agentic loops.
- **llama.cpp:** GBNF grammar files for local/small-model constrained decoding.
- **outlines:** FSM/regex/JSON-Schema guided generation; pioneering library approach.
- **Formatron:** open-source Earley dynamic-pruning engine (github.com/Dan-wanna-M/formatron), architecture-independent.

## Research Frontiers & Open Problems

- Preprocessing break-even analysis for mask providers vs decoding users (PSC).
- TOON constrained-decoding enforcement (e.g., via xgrammar) - benchmark suggests it may not yield desired results for simple structures; needs complex-structure validation.
- Decode-time grammars for domain-specific languages and CLI/API surfaces in agent serving systems.
- Best-of-K draft selection cost/quality frontier in DCCD.
- Structured-output token overhead vs context engineering (format constraints as learnable artifacts vs compression).

## Cross-Domain Connections

1. [[agent-observability-tracing]] - tool-call JSON spans are the natural trace/verification surface for structured-output failures.
2. [[agentic-tool-use-schema-optimization]] - schema quality and parse/selection accuracy are the upstream half of SOG.
3. [[mcp-agentic-tool-use]] - JSON-RPC + tool schemas: deterministic scaffolding complements constrained decoding.
4. [[speculative-decoding-kv-cache-compression]] - draft-based acceleration is the sibling of draft-conditioned constraint enforcement.
5. [[llm-inference-serving-systems]] - vLLM/SGLang serving: structured-generation throughput is a serving-level concern.
6. [[context-management-ai-agent-frameworks]] - format overhead consumes finite context; compact structured renderings (TOON, diff patches) reduce it.
7. [[entity-resolution-confidence-calibration]] - validation/confidence gating for structured outputs mirrors auto-accept/review/reject ER thresholds.
8. [[adversarial-ai-agent-manipulation]] - schema text and format instructions are injection vectors; validation is a defense layer.
9. [[error-comprehension]] - parse/validation error taxonomy feeds structured diagnosis instead of keyword matching.
10. [[context-engineering-skills-not-compression]] - format constraints as learnable artifacts vs token-level compression.

## References

1. Reddy, Walker, Ide, Bedi - The Hidden Cost of Structured Generation in LLMs: Draft-Conditioned Constrained Decoding, arXiv:2603.03305.
2. Matveev - Token-Oriented Object Notation vs JSON: Benchmark of Plain and Constrained Decoding Generation, arXiv:2603.03306.
3. Li et al. - When JSON Is Not Enough: Semantic Reliability of Schema-Constrained LLM Ordering Agents (OrderBench), arXiv:2607.18261.
4. Li, Dong, Li, Li - Efficient Grammar-Constrained Decoding via Parser Stack Classification (PSC), arXiv:2608.03065.
5. Sun et al. - Earley-Driven Dynamic Pruning for Efficient Structured Decoding (Formatron/ZapFormat), arXiv:2506.01151.
6. Zhang et al. - Decode-Time Grammars: Constrained LLM Generation over a Refinement Order of Grammar Fragments (gproj), arXiv:2607.18357.
7. Duanis et al. - JSON Whisperer: Efficient JSON Editing with LLMs, arXiv:2510.04717.
8. Chen et al. - GBV-SQL: Guided Generation and SQL2Text Back-Translation Validation, arXiv:2509.12612.
9. vLLM official docs - Structured Outputs (context7, stable).
10. Exocortex shared corpus - TOON field note (specs/A2A_SERIALIZATION_DESIGN_NOTE), JSON Format Penalty (specs/TOKEN_ECONOMICS_FIELD_NOTE).
