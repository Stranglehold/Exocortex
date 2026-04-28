# EXOCORTEX KNOWLEDGE WIKI — INDEX
## Last updated: April 27, 2026

---

## How to Use This Wiki
- Read `WIKI.md` for page templates and cross-reference rules
- Navigate by category below, or search for specific concepts
- Pages use [[wiki-links]] to cross-reference related content
- This wiki is maintained by the Exocortex team: Opus (concepts, research), Agent (components, incidents), Kestrel (technical validation), Jake (decision approval)

---

## Concepts

| Page | Status | Summary |
|------|--------|---------|
| [[proactive-interference]] | TODO | Memory degradation from competing information — the core problem both KV cache and DeltaNet share |
| [[entropy-as-signal]] | TODO | Five independent papers converge on entropy as the universal monitoring signal |
| [[deterministic-scaffolding]] | TODO | "Deterministic scaffolding beats probabilistic reasoning where reliability matters" |
| [[temporal-proprioception]] | TODO | The sense of elapsed processing time — architecturally absent from LLMs |
| [[confabulation]] | TODO | Two variants: quantitative (EI catches) and citation (EI doesn't catch) |
| [[build-the-environment]] | TODO | "You don't need a better model. You need a better harness." |
| [[initiation-bloat]] | TODO | Turns 1-3 consume massive context, then stabilize — scaffolding should phase |
| [[stateful-injection]] | TODO | Cache injections as state, only inject diffs — the agent's design |

## Components

| Page | Status | Summary |
|------|--------|---------|
| [[bst-classifier]] | TODO | Domain classification with phrase signals, momentum, anti-signals, compound detection |
| [[injection-gate]] | TODO | Three-phase context management: full → conditional → compressed |
| [[supervisor-loop]] | TODO | Graduated intervention with domain-aware thresholds and CUSUM canary |
| [[epistemic-integrity]] | TODO | Evidence ledger + volatility classification + confabulation detection |
| [[error-comprehension]] | TODO | Deterministic error classifier with anti-action principle |
| [[context-pruner]] | TODO | Stale output removal protecting both KV cache and DeltaNet state |
| [[backend-standby]] | TODO | Infrastructure failure detection with auto-recovery |
| [[stuck-delivery]] | TODO | Completion-communication gap detection with surgery suppression |
| [[inference-wrapper]] | TODO | FastAPI Layer B with entropy monitoring hooks |
| [[nerv-dashboard]] | TODO | Real-time GPU/generation monitoring |

## Research

| Page | Status | Summary |
|------|--------|---------|
| [[srgen]] | TODO | Token-level entropy intervention (2510.02919) |
| [[sleepgate]] | TODO | KV cache proactive interference management (2603.14517) |
| [[knowledge-packs]] | TODO | Zero-token KV cache injection (2604.03270) |
| [[can-llms-perceive-time]] | TODO | Temporal proprioception gap confirmed empirically (2604.00010) |
| [[bottlenecked-transformers]] | TODO | Step-level memory consolidation, ICLR 2026 (2505.16950) |
| [[thinking-optimal-scaling]] | TODO | Shortest correct response principle, NeurIPS 2025 (2502.18080) |
| [[streaming-hallucination]] | TODO | Trajectory contamination monitoring (2601.02170) |
| [[first-hallucination-tokens]] | TODO | One-token detection window (2507.20836) |
| [[hermes-agent]] | TODO | Nous Research self-improving agent with trajectory-to-skill |
| [[karpathy-wiki]] | TODO | LLM Knowledge Bases — three-layer wiki architecture |
| [[gepa]] | TODO | Reflective prompt evolution, ICLR 2026 Oral |
| [[autoresearch]] | TODO | Karpathy's autonomous experiment loop |

## Decisions

| Page | Status | Summary |
|------|--------|---------|
| [[dec-phrase-over-unigram]] | TODO | BST v3.8: lexically common words need phrase context |
| [[dec-disable-bugfix-enrichment]] | TODO | Qwen3.6: enrichment hurts bugfix (-14%) and config_edit (-25%) |
| [[dec-lower-supervisor-thresholds]] | TODO | Qwen3.6: recovery rate 33% requires earlier intervention |
| [[dec-conditional-injection]] | TODO | Skip injection when no signal, don't merge extensions |
| [[dec-upstream-pruning]] | TODO | Context pruner operates upstream of both memory systems |

## Incidents

| Page | Status | Summary |
|------|--------|---------|
| [[inc-oracle-fabrication]] | TODO | Agent fabricated complete credit risk report — motivated EI layer |
| [[inc-watchdog-blind]] | TODO | Hardcoded 100k window when actual was 65k — silent overflow |
| [[inc-bst-momentum-lock]] | TODO | BST locked coding+planning for 7+ turns during geopolitical research |
| [[inc-stuck-delivery-loop]] | TODO | Agent completed task but couldn't report results |
| [[inc-wrapper-killed]] | TODO | Wrapper killed during agent task — cascade without recovery |

---

## Ingestion Log

| Date | Source | Pages Created/Updated |
|------|--------|----------------------|
| (none yet — initial compilation pending) | | |
