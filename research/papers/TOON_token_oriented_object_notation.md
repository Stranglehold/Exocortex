# TOON: Token-Oriented Object Notation
## Source: Matveev, I. (February 2026)
## Paper: arxiv.org/abs/2603.03306
## Added to ledger: May 9, 2026 by Opus

---

## Core Idea

TOON is a serialization format designed specifically for LLM interaction — both comprehension (input) and generation (output). It replaces JSON's verbose text syntax with a more token-efficient notation, reducing the number of tokens consumed by structural formatting (braces, quotes, colons, commas, field names) without losing the structured data semantics.

Standard JSON:
```json
{"name": "merge_sort", "language": "python", "lines": 45, "tested": true}
```

TOON equivalent (conceptual — fewer tokens for the same structured data):
```
name:merge_sort language:python lines:45 tested:true
```

The key insight: every token spent on JSON syntax (`{`, `"`, `:`, `,`, `}`) is a token the model generates that carries zero semantic information. In a tool-call-heavy agentic workflow, structured output formatting can consume 15-30% of generated tokens. TOON reclaims that capacity.

---

## Relevance to Exocortex

### Where This Matters

Agent Zero generates structured JSON on every tool call. Each monologue cycle produces:
- A JSON-formatted thoughts array
- A JSON-formatted tool call with name and arguments
- JSON-formatted tool results appended to history

In a 50-step agentic session, the cumulative JSON formatting overhead — braces, quotes, field names repeated identically on every turn — is substantial. TOON would reduce this overhead at the generation boundary, meaning:
- Fewer tokens generated per tool call → faster response
- Less context consumed by formatting → more room for reasoning
- Lower token cost on cloud APIs (DeepSeek, Claude) → cheaper operation

### Where This Doesn't Matter

- Human-readable artifacts (journals, essays, wiki pages) — these should stay in natural language
- Config files — JSON is the standard, tools expect it
- Network serialization (protobuf handles this for A2A) — TOON operates at a different layer

### The Layer Distinction

| Layer | Current Format | Optimization | Status |
|-------|---------------|-------------|--------|
| LLM generation boundary | JSON | TOON | Research — evaluate |
| Human-readable storage | JSON/Markdown/HTML | Stay as-is | No change needed |
| Agent-to-agent communication | JSON (current) | gRPC + protobuf (future) | Deferred — see A2A_SERIALIZATION_DESIGN_NOTE.md |
| KV cache storage | FP16/Q4 (current) | TurboQuant turbo3/4 | Active — in Kestrel's build |

TOON and protobuf are complementary, not competing. Protobuf optimizes the network wire format between services. TOON optimizes the token format at the model's output boundary. Both reduce waste at different layers.

---

## Technical Assessment

### Advantages
- Directly reduces token count in LLM-generated structured output
- Simple enough for one-shot in-context learning (model doesn't need TOON in training data)
- Backward compatible — can be translated to/from JSON at the application boundary
- Reduces generation time proportional to token savings

### Challenges
- Agent Zero's framework expects JSON tool calls — would require a translation layer
- llama.cpp's OpenAI-compatible API returns JSON — TOON would need to operate inside the model's generation, with a post-processing step to convert back to JSON for the framework
- Constrained decoding (grammar-based JSON enforcement) is well-established; TOON grammar enforcement is new and less tested
- The overhead of the example prompt (teaching the model TOON format) may offset token savings on short tasks

### Open Questions
- What's the actual token savings percentage for Agent Zero's typical tool call patterns?
- Does one-shot TOON learning degrade tool call accuracy compared to native JSON?
- Can TOON be combined with llama.cpp's grammar-based constrained decoding?
- What's the error rate on TOON parsing vs JSON parsing in production?

---

## Evaluation Path

1. **Measure baseline:** Count tokens consumed by JSON formatting in a typical Agent Zero session (tool calls + responses, exclude content). Calculate formatting overhead percentage.
2. **If overhead > 15%:** Worth evaluating TOON as a generation format with JSON translation at the framework boundary.
3. **If overhead < 15%:** The optimization is marginal. Focus on MTP and TurboQuant first — they provide larger gains.

This is a Phase 5+ evaluation — after MTP and TurboQuant are validated and stable. The token savings compound with MTP (fewer tokens to generate × multiple tokens per pass = multiplicative speedup), so the optimal time to evaluate TOON is after MTP is working.

---

## Connection to Information Density Thesis

TOON is the generation-side complement to our context-side density work. The curated Tier 1-4 stack reduces injection noise (fewer tokens IN). TOON would reduce formatting overhead (fewer tokens OUT). Both increase the proportion of tokens that carry semantic information versus structural overhead.

GenericAgent's finding: effective context is ~10x below nominal. If 15-30% of generated tokens are JSON formatting, effective generation capacity is similarly reduced. TOON recovers some of that capacity the same way the curated stack recovered context capacity — by removing tokens that carry no information.

---

## References

| Source | URL |
|--------|-----|
| TOON paper | arxiv.org/abs/2603.03306 |
| A2A Serialization Design Note (protobuf assessment) | specs/A2A_SERIALIZATION_DESIGN_NOTE.md |
| Information density thesis (GenericAgent) | research/AGENTIC_SUPERVISOR_ARCHITECTURE_RESEARCH.md |
