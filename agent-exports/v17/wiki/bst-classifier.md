# Belmont State Tracker (BST) — Compound Classifier

## Layer
L6: Belief State Tracking

## Hook
`before_main_llm_call` — fires on every user message before the model sees it.

## What It Does
BST classifies every incoming user message into one or two domains using regex-based signal scoring. It then enriches the model's context with domain-specific guidance (enrichment templates) before the LLM generates a response.

This is the first deterministic layer that processes user intent. Every other extension sees the classification result via `_bst_domain` and `_bst_compound` in extras.

## Mechanism

### Compound Classification (v3.1)
BST evolved from first-match-wins to score-all classification:

1. **Signal matching** — Each domain has a set of regex patterns. Every match scores +1 for that domain.
2. **Score aggregation** — Signal counts are weighted by domain specificity. Narrow signals (e.g., `git push`) carry more weight than broad ones (e.g., `file`).
3. **Domain priority tiebreaking** — When scores tie, `DOMAIN_PRIORITY` resolves: bugfix > coding > planning > analysis > ... > conversation.
4. **Primary + secondary** — The highest-scoring domain is primary; the next-highest distinct domain is secondary (if confidence >= threshold).
5. **Compound signature** — `"bugfix+planning"` — persisted across turns with momentum tracking.

### Domain Definitions
| Domain | Priority | Example Signals |
|--------|----------|----------------|
| bugfix | 1 | `error`, `traceback`, `fix`, `broken` |
| coding | 2 | `implement`, `write`, `refactor`, `code` |
| testing | 2 | `test`, `assert`, `pytest`, `verify` |
| planning | 3 | `design`, `architecture`, `spec`, `plan` |
| analysis | 4 | `analyze`, `investigate`, `compare`, `assess` |
| system_admin | 5 | `install`, `deploy`, `restart`, `config` |
| config_edit | 6 | `settings`, `configure`, `.json`, `.yaml` |
| prompt_engineering| 7 | `system prompt`, `behavior`, `instruction` |
| git_ops | 8 | `commit`, `push`, `merge`, `repo` |
| file_ops | 9 | `read`, `create`, `delete`, `move` |
| investigation | 11 | `research`, `search`, `find`, `OSINT` |
| orientation | 0 | `hello`, `what are you`, `who are you` |
| meta_cognitive | 0 | `how do you`, `explain your`, `why did you` |
| philosophical | 0 | `consciousness`, `meaning`, `should` |
| conversation | 99 | Fallback — any message not caught above |

### Enrichment Pipeline
After classification:
1. **Primary enrichment** — Full guidance text from the domain's `enrichment_template` is injected into the model's context.
2. **Secondary enrichment** — A one-line hint from the secondary domain (if any) is appended.
3. **Extras persistence** — `_bst_domain` and `_bst_compound` are written to `extras_persistent` for downstream extensions.

## Integration Points
- **Injection Gate (L3)** — Reads BST classification to decide whether to gate the message
- **Supervisor Loop (L4)** — Reads `_bst_domain` to adjust stall/loop thresholds
- **Evidence Ledger (L8)** — Tags ledger entries with BST domain for later retrieval
- **Model Profiles** — Some domains route through profile enrichment gating (v3.2)

## File
`/a0/usr/Exocortex/extensions/before_main_llm_call/_11_belief_state_tracker.py` — 1702 lines

## Related
- [[injection-gate]]
- [[supervisor-loop]]
- [[epistemic-integrity]]
- [[error-comprehension]]

## Version History
- v3.0 — First-match-wins classification
- v3.1 — Compound classification + score-all + secondary domain
- v3.2 — Model profile enrichment gating
