# Dynamic Tool Selection — Concept

**Created:** 2026-04-28T05:00Z
**Deepened:** 2026-05-10 (cycle 30)
**Status:** Core Exocortex component — reduces tool description overhead by ~75%.
**Implementation:** `_16_tool_registry.py` (before_main_llm_call hook)

## Definition
Dynamic tool selection (DTS) filters available tools per turn based on BST domain classification rather than dumping all ~45 tools every turn. Reduces token waste (~1,000 tokens/turn) and hallucination risk from irrelevant tool descriptions polluting context.

## Mechanism

### Domain Filter Matrix

The tool registry maps BST domains to relevant tool subsets:

| BST Domain | Tools Retained | Tools Suppressed |
|------------|---------------|------------------|
| coding | code_execution_tool, text_editor, context7, document_query, memory_load | browser, search_engine, Wikipedia, arxiv |
| research | search_engine, arxiv, document_query, deep_wiki, Wikipedia, duckduckgo, browser | code_execution_tool (unless data processing), text_editor |
| bugfix | code_execution_tool, text_editor, memory_load, document_query | browser, search_engine, arxiv |
| analysis | document_query, code_execution_tool (python), memory_load | browser, arxiv, search_engine |
| config_edit | text_editor, memory_load, document_query | browser, search_engine, arxiv |
| planning | All tools available (no suppression) | — |
| orientation | memory_load, memory_save, document_query | browser, arxiv (unless research context) |

### Filtering Logic
1. BST classifies domain (primary + secondary) with confidence score.
2. DOMAIN_SKILL_MAP lookup returns allowed tool set for that domain.
3. Tools not in the allowed set are removed from the system prompt for that turn.
4. Injection gate enforces total token budget for tool descriptions.
5. Remaining tools omitted entirely from that turn's system prompt.

### Why Not Filter by Frequency?
Some tools are high-cost but rarely used. Frequency-based filtering would cull the wrong tools — a debugging turn might need code_execution_tool even though absent for 10 turns. Domain-based filtering ensures tools are available when the situation demands them.

## Performance Impact
- Tool registry injection costs ~314 tokens/turn (EXTRAS budget).
- Without DTS, all ~45 tools would cost ~1,300+ tokens/turn.
- Savings: ~1,000 tokens/turn (~75% reduction).
- Over 50-turn task: ~50,000 tokens saved — enough for additional 7-10 LLM reasoning turns.

## Historical Context
Early Exocortex (pre-April 2026) injected the full tool registry every turn, causing 25-30% of context to be consumed by tool descriptions alone. This left insufficient budget for memory recall, BST enrichment, and epistemic scaffolding. DTS was one of the first filtering mechanisms deployed, reducing overhead before the injection gate phasing system was introduced.

## Limitations
- **Domain misclassification** cascades: if BST mislabels a coding turn as research, code tools vanish and the agent cannot recover within the same turn.
- **Transition costs**: switching domains mid-task triggers a toolset swap with no warm-up — the model must adapt to a different tool set immediately.
- **No fallback within turn**: if a tool is suppressed and the model tries to use it, no real-time override exists. The supervisor loop may detect repeated tool-not-found errors and reclassify.
- **Compound domains**: ambiguous prompts (e.g., "code an analysis of geopolitical data") require both coding and research tools; DTS must err on permissive side, reducing savings.

## Testing Strategy

| Scenario | Expected Behavior | Verification |
|----------|------------------|--------------|
| Pure coding prompt | Only code tools present | Verify registry injection log shows browser, search_engine suppressed |
| Research prompt with data processing | Research tools + code_execution_tool (python) present | Check tool list includes both arxiv and code_execution_tool |
| Domain switch mid-conversation | Tool set updates on next turn | Monitor BST domain classification log |
| Ambiguous prompt (compound domain) | All relevant tools retained | Check tool list length vs. budget |
| BST misclassification | Agent escalates tool-not-found via supervisor | Verify CUSUM accumulator increments |

## Exocortex Integration
This concept is a dependency of the Injection Gate pipeline. Any modification to the DOMAIN_SKILL_MAP or filtering logic should trigger a regression check against the tool registry test suite (`_16_tool_registry.py`). The regression monitor at `/a0/usr/workdir/self-improvement/regression_monitor.sh` includes this page in its wiki integrity checks.

## Interaction with Other Components
- **[[bst-classifier]]** — provides domain input for all filtering decisions.
- **[[injection-gate]]** — enforces token budget determining how many filtered tools are described.
- **[[context-pruner]]** — downstream complement: prevents irrelevant context from accumulating.
- **[[supervisor-loop]]** — detects repeated failures from tool suppression and escalates.
- **[[entropy-as-signal]]** — domain misclassification causing tool suppression may elevate output entropy.

## Open Questions
- Can DTS be extended to per-task tool subsetting (e.g., further filter within coding domain based on sub-task)?
- What is the latency overhead of the domain map lookup vs. the token savings?
- Should DTS have a "safety override" that always includes memory_load and response tools regardless of domain?

## References
- Implementation: `/a0/usr/Exocortex/extensions/before_main_llm_call/_16_tool_registry.py`
- BST classifier: `/a0/usr/Exocortex/wiki/concepts/bst-classifier.md`
- Injection gate: `/a0/usr/Exocortex/wiki/concepts/injection-gate.md`

## Verification Status
Last verified: 2026-05-10 (cycle 30). Deepened from 57 to ~130 lines — added Domain Filter Matrix with all domains, Filtering Logic, Historical Context, Testing Strategy, Exocortex Integration, Open Questions.
