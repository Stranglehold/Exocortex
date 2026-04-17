# Token Economics in Agentic Inference
## Field Note

**Written:** Session ~2026-04-16 (Kestrel)
**Authors:** Kestrel (observation, implementation), Jake (operator context)
**For:** Opus (architectural review and next-build design)
**Status:** Observations complete. Two interventions already deployed. Three build candidates
identified — need architectural spec before implementation.

---

## 1. What This Session Surfaced

This note documents a recurring failure pattern observed during a live stress test
(company_collector.py, OSINT Phase 2), the root causes traced during diagnosis, and the research
literature that contextualizes both. The failure was a file-writing loop. The underlying cause is
a token economics problem that affects every long agentic session, not just that task.

**The immediate failure:** The agent looped for 25+ turns attempting to write a Python class with
12 methods. It correctly identified the task, correctly identified the approach (section-by-section
writes), and kept failing at one specific line: `{'Authorization': 'Bearer ' + self.api_key}`.
Single quotes inside a Python string inside a JSON field inside a tool call — three levels of
quoting, all using the same metacharacters. The model cannot reliably escape across all three levels
simultaneously while also generating correct Python and staying under token budget.

**What the loop looked like:** `[TOOL-REG] Injected 41 tools` firing on every turn while the agent
cycled through triple-quoted strings → double-quoted strings → f.write() chains → back to triple
quotes. The supervisor correctly detected stagnation. Tier 2 surgery removed the loop turns.
The agent then lost evidence that Section 1 was done and restarted from scratch. Surgery made the
loop worse by erasing the only progress signal.

This is not primarily a model quality problem. It is a protocol design problem. The agent was
trying to do something the transport layer cannot cleanly support.

---

## 2. Three Observed Failure Classes

### Class A — Quoting Depth (immediate, fixed today)

`code_execution_tool` requires embedding target file content inside executable Python code
inside a JSON string field. Three levels of quoting, same metacharacters at each level. Any string
literal in the target content can break the JSON or the Python. The model fails at the innermost
level because it cannot track escaping rules across all three levels simultaneously while also
reasoning about the task.

This is a structural problem with `code_execution_tool` as a file-writing primitive. It was built
for executing logic, not for writing content that contains the same metacharacters as its transport
layer.

**Fix deployed:** `write_file` tool — content passed as a direct JSON string field, one level of
encoding only. Single quotes in Python code never need JSON escaping.

### Class B — Context Bloat from Repeated Injection (chronic, partially fixed)

`_16_tool_registry` was injecting ~340 tokens of tool documentation on every turn. Same content,
different position in the prompt each turn. The KV cache cannot help: KV caching requires
byte-identical prefixes at fixed positions, and prepending to the user message shifts the content's
absolute position on every turn.

In a 20-turn conversation with 15 turns in active context, this is ~5,100 tokens of repeated
identical content — 16% of the 32K context window consumed by information the model already has.

**Fix deployed:** Smart injection — full block on turn 1 and after context surgery (detected via
history length drop), compact one-liner (~20 tokens) on all other turns. Per-turn savings: ~320
tokens. Over a 20-turn conversation: ~5,000 tokens recovered.

### Class C — Reasoning Token Overhead (chronic, unfixed)

The reasoning-distilled model generates long `<think>` chains before every JSON response. These
chains are often longer than necessary — the model plans the correct approach in the first 200
tokens, then spends another 800-1,200 tokens narrating what it just planned. This overhead
accumulates in context and in output token consumption.

A JSON payload that should cost 400 tokens (reasoning + tool call) costs 1,200-1,600 tokens
because the thinking chain runs to the natural completion of the model's verbosity patterns.
At the default 4K `max_tokens`, this truncates the JSON. At 16K `max_tokens` (deployed today),
truncation is rare but the thinking overhead is still consuming context window on every turn.

This class is not fully addressed by the fixes deployed today.

---

## 3. Research Grounding

The following papers were retrieved and reviewed. Full citations below.

### Tool Schema Overhead (arXiv:2510.14453, 2025)

313–346 token baseline overhead for having any tools enabled — before schema content is counted.
At 58 tools in catalog form: ~55K tokens. Accuracy drops up to **50 percentage points** as context
passes 8K tokens from schema bloat alone.

**Implication for Exocortex:** The natural language tool injection approach (tool names + one-line
descriptions in plain text, not JSON schemas) is architecturally validated. A0's tool registration
via system prompt text rather than OpenAI function-calling format is the correct choice. The 340
token TOOL-REG block compares favorably to 55K tokens of JSON schemas. The risk is at scale — as
tool count grows, even natural language injection becomes a first-class context consumer.

**Unseen implication:** Domain-relevant tool injection (BST-gated) — only injecting tool names
relevant to the current task domain — would reduce this further. 41 tools injected on a coding task
when the agent needs `write_file`, `code_execution_tool`, and `stack_status` is wasteful. The
BST already classifies domain on every turn. Wiring tool injection to that classification is a
natural extension of the existing architecture.

### JSON Format Penalty ("Let Me Speak Freely," 2024–2025)

Forcing JSON-structured output degrades reasoning accuracy by **10–15%** vs. free-form generation.
The model suppresses reasoning quality to satisfy a format constraint simultaneously.

**Implication for Exocortex:** A0's requirement for JSON tool calls is a structural accuracy tax
on every tool invocation. Not something we can change. But it explains part of why smaller models
(4B, 14B) fail at tool call format under cognitive load — they're simultaneously solving the task
AND satisfying a format constraint with limited capacity. MetaGate's arg normalization and alias
resolution is directly compensating for this effect at the deterministic layer.

### TALE: Token-Budget-Aware Reasoning (arXiv:2412.18547, Dec 2024)

Prompt-based token budget constraint: **67% output token reduction**, **59% cost reduction**,
accuracy drop from ~81% to ~80% — effectively maintained. The relationship between reasoning
tokens and task accuracy is **logarithmic**: early tokens contribute substantially, later tokens
yield diminishing returns. Including a budget instruction in the prompt is sufficient — no
fine-tuning required.

**Implication for Exocortex:** For execution-heavy domains (coding, system_admin) where the task
is known and the model primarily needs to execute rather than reason, a token budget instruction
reduces thinking overhead without accuracy loss. The BST already classifies these domains. Adding
a budget hint conditionally (e.g., "Limit reasoning to 300 tokens — the approach is clear, execute
it") is a one-layer change with documented 67% thinking token reduction.

This is the research basis for the `/no_think` experiment Jake proposed. The TALE approach is
more nuanced than `/no_think` — it constrains rather than eliminates thinking, and the constraint
is conditional on task type. Worth designing as a BST enrichment addition.

### Chain of Draft (arXiv:2502.18600, Feb 2025)

Concise intermediate reasoning steps match full CoT accuracy while using **7.6% of CoT tokens**.
The key change is prompting for one key insight per reasoning step rather than verbose narration.
Captures critical information, discards elaboration.

**Implication for Exocortex:** Zero-cost prompt change. The full CoT verbosity pattern is a habit
the model has, not a requirement for accuracy. Prompting for concise steps should be added to the
BST enrichment across all domains, not just coding. Estimated savings: 10–15× token reduction on
reasoning traces with no accuracy loss.

### Do Thinking Tokens Help or Trap? (arXiv:2506.23840, Jun 2025)

The NOWAIT approach — removing filler "wait" tokens from reasoning chains — reduces trajectory
length by **27–51%** across task types. These filler tokens are RLHF training artifacts, not
reasoning value. They exist because the model was rewarded for producing them, not because they
help.

**Implication for Exocortex:** The reasoning-distilled 27B model likely has this pattern. The
verbose planning narration observed in the loop logs ("I need to write the file in small sections,
I will use append mode, I must be careful about escaping...") is exactly the NOWAIT waste class.
The Chain of Draft instruction would suppress this. TALE budget constraint would suppress it harder.

### Prefix Caching (Anthropic/OpenAI documentation, 2024–2025)

**90% cost reduction** on Anthropic's API for byte-identical prefixes. Requirement: content must
be identical and at a fixed position from the start of the prompt.

**Implication for Exocortex:** Dynamic injection into user messages (TOOL-REG, BST enrichment,
working memory) prevents prefix caching entirely — every injection shifts subsequent content's
absolute position. This is an inherent trade-off of the injection architecture. For local llama.cpp
inference, prefix caching is not a directly applicable technique (llama.cpp's KV cache works
differently). But the principle applies: if we ever run A0 against the Anthropic API directly,
the injection architecture would need a rethink. For now, the architecture is correct for local
inference and the trade-off is known.

### LLMLingua-2: Prompt Compression (arXiv:2403.12968, ACL 2024)

**20× compression** with 95–98% accuracy retention. Extractive approach (token classification,
not generative summarization) avoids hallucination risk. LongLLMLingua actually **improves**
downstream task performance by up to 21.4% by removing noise from long inputs.

**Implication for Exocortex:** Tool outputs are the primary context window consumer in long
sessions — a single `cat` or `docker logs` output can be 5–10K tokens. A lightweight extractive
compressor running on tool outputs before they're stored in history would recover significant
context. This is distinct from the Sleep Consolidation system (between-session) — this is
within-session, applied at the `tool_execute_after` hook immediately after each tool call.
LLMLingua-2 runs as a separate model pass; a simpler rule-based approach (truncate repeated lines,
strip ANSI escape codes, keep first/last N lines) may capture 60–70% of the benefit at zero
compute cost.

### Focus Agent: Active Context Compression (arXiv:2601.07190, Jan 2025)

Agent-initiated context compression on SWE-bench Lite: **22.7% token reduction**. The agent
autonomously writes a structured "Knowledge Block" (facts, file paths, decisions, outcomes) then
prunes the raw interaction log. No external summarizer — the model decides what to keep.

**Implication for Exocortex:** Sleep Consolidation's Phase 1 (dedup + utility scoring) and the
selective memorizer's structured memory writes are architecturally the same pattern, validated at
research level. The Knowledge Block format — queryable facts rather than narrative summary — is
what makes it work. The distinction between "write structured facts" and "write prose summary" is
load-bearing. The existing Exocortex implementation gets this right.

---

## 4. What Was Built Today

| Component | Location | What it solves |
|-----------|----------|----------------|
| `write_file` tool | `tools/write_file.py` | Class A: quoting depth. Content → JSON, one level only |
| MetaGate `write_file` schema | `tool_execute_before/_20_meta_reasoning_gate.py` | Validation + arg aliases for new tool |
| BST coding enrichment update | `before_main_llm_call/_11_belief_state_tracker.py` | Directs to write_file, adds multi-step file protocol |
| TOOL-REG smart injection | `message_loop_prompts_after/_16_tool_registry.py` | Class B: 340 → 20 tokens on steady-state turns |
| Directory hash cache | Same file | Eliminates 13 ast.parse() calls per turn when tools unchanged |
| `max_tokens: 16384` via kwargs | Container `_model_config/config.json` | Class C (partial): prevents JSON truncation from token exhaustion |
| Jinja template (no namespace()) | LM Studio, manual paste | Correct `<think>` prompt prefix; removes broken Jinja dependency |

---

## 5. What Is Not Yet Built — Candidates for Opus Review

These are identified build candidates. They are not specced. Opus should evaluate whether they
belong as new layers, extensions to existing layers, or refinements to current implementations.

### Candidate 1: BST-Gated Tool Injection

**Problem:** 41 tools injected every turn regardless of task domain. A coding task doesn't need
`swarmfish_predict`. An investigation task doesn't need `write_file`. Noise, not signal.

**Proposed mechanism:** TOOL-REG queries current BST domain (stored in `self.agent._bst_store`)
and injects only the tool subset mapped to that domain. Full list injected when domain is
`general` or BST hasn't fired yet.

**Approximate domain → tool mapping:**
- `coding`, `bugfix`, `system_admin` → `write_file`, `stack_status`, `staging_note`
- `investigation`, `analysis` → `oss_*`, `swarmfish_*`, `investigation_tools`, `tla_check`
- `file_ops` → `write_file`, `stack_status`
- `general` / unknown → full list

**Expected token savings:** 340 → 60–80 tokens on domain-matched turns (not just the compact
one-liner, but a domain-filtered full block). More useful signal per token — the model sees exactly
the tools it needs.

**Risk:** BST misclassification injects the wrong subset. Tool the model needs is not shown.
Mitigation: always inject the one-liner fallback "use stack_status for full list" so the model
can discover tools it needs even when the domain filter missed.

### Candidate 2: TALE-Style Reasoning Budget in BST Enrichment

**Problem:** Class C above. Reasoning-distilled model generates 800–1,600 token thinking chains
on tasks where 200 tokens of reasoning would suffice. Verified by TALE research (67% reduction
available from prompt change alone).

**Proposed mechanism:** BST enrichment adds a token budget hint for execution-mode domains:

> "Reasoning budget: ~200 tokens. The approach is established — reason briefly, then execute."

Applied conditionally to: `coding`, `system_admin`, `file_ops`, `git_ops`.
Not applied to: `investigation`, `analysis`, `planning` (these benefit from deep reasoning).

**This is the research-backed version of the /no_think experiment.** TALE constrains rather than
eliminates reasoning. The model still thinks — it just stops narrating its own plan for 1,200 tokens
before executing it.

**Risk:** Budget hint is advisory, not enforced. Local models may ignore it. TALE tested on
instruction-tuned models; behavior on a reasoning-distilled model may differ. Recommend testing
with a measurable metric: log thinking token count before/after per BST domain.

### Candidate 3: Tool Output Compressor

**Problem:** Long tool outputs (file reads, docker logs, shell output, search results) are stored
verbatim in conversation history. A single `docker logs --since=5m` can be 8–15K tokens. After
10 turns, these outputs occupy the majority of the context window while the current task has moved
on.

**Proposed mechanism:** `tool_execute_after` extension at `_28_output_compressor.py`. Runs after
every tool call. For outputs exceeding a threshold (e.g., 800 tokens), applies rule-based
compression:

1. Strip ANSI escape codes (zero information loss)
2. Deduplicate consecutive identical lines (common in docker logs)
3. Collapse repetitive patterns (e.g., 50 lines of "Section N done" → "Section 1–50 done")
4. Keep first 30 + last 30 lines of remaining output with `[... N lines omitted ...]` marker

No LLM call. Deterministic. Fast. Expected to capture 60–70% of LLMLingua-2's savings at zero
compute cost. LLMLingua-2 (or a future equivalent) as optional Layer 2 for cases where rule-based
compression leaves too much.

**Risk:** Rule-based compression may drop a line the model needed (e.g., a specific error that
appeared in the middle of a long log). Mitigation: compress only outputs beyond a token threshold,
preserve failure-relevant lines (lines containing "error", "exception", "traceback", "failed").

---

## 6. Questions for Opus

1. **Candidate 1 (BST-gated injection):** The domain → tool mapping above is a first draft. Where
   does the mapping table live — hardcoded in `_16_tool_registry.py`, in a config file, or derived
   from the tool file's docstring metadata? The current architecture adds per-tool domain tags in
   docstrings as a pattern (see `stack_status.py`'s domain awareness hints). Is that the right
   location, or does this belong in `tool_manifest.json`?

2. **Candidate 2 (reasoning budget):** Should the budget hint be a fixed number (300 tokens) or
   adaptive (based on task complexity assessed by BST slot resolution)? The TALE paper used fixed
   budgets successfully, but our tasks vary more than their benchmarks.

3. **Candidate 3 (output compressor):** This overlaps conceptually with the Context Compression
   design note's Layer 1 (observation masking). Is this the same layer, or should these be
   distinct extensions? The compression design note's Layer 1 was scoped to within-session
   rolling compression on a timer or turn count. The output compressor proposed here is
   per-tool-call, immediate. Different trigger, same effect on context size.

4. **Scope concern:** All three candidates address token efficiency. They could be developed as
   isolated extensions or as a coordinated "Token Budget" subsystem with a shared config section
   and coordinated thresholds. Is coordination needed, or is independent deployment safer given
   the current stack's complexity?

---

## 7. References

| Paper | arXiv | Key number |
|-------|-------|------------|
| Natural Language Tools (Wang et al.) | arXiv:2510.14453 | 313–346 token baseline overhead; 50pp accuracy drop at 8K schema tokens |
| Beyond Max Tokens: Tool Call Chains | arXiv:2601.10955 | 2:1–3:1 input:output ratio; 12–40% savings from call fusion |
| TALE: Token-Budget-Aware Reasoning (Hu et al.) | arXiv:2412.18547 | 67% token reduction, <1% accuracy loss, prompt-only |
| Chain of Draft (Xu et al.) | arXiv:2502.18600 | 7.6% of CoT tokens at equivalent accuracy |
| Do Thinking Tokens Help or Trap? | arXiv:2506.23840 | 27–51% trajectory reduction from removing filler thinking |
| KVFlow (NeurIPS 2025) | arXiv:2507.07400 | 1.83–2.19× speedup over LRU KV cache eviction |
| LLMLingua-2 (Microsoft Research) | arXiv:2403.12968 | 20× compression, 95–98% accuracy retention |
| Focus Agent: Active Context Compression | arXiv:2601.07190 | 22.7% token reduction, agent-initiated, SWE-bench Lite |

---

*Field note written by Kestrel, session 2026-04-16. Captures what was observed, diagnosed, and
partially fixed in a single session. The three unbuilt candidates are ready for Opus to spec.
Research citations are real — all arXiv IDs were verified by web retrieval during the session.*
