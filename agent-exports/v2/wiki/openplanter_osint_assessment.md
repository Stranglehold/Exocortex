# OpenPlanter OSINT Framework Assessment

## Architecture Overview
Recursive-language-model investigation agent with Tauri 2 desktop GUI. 1011-line autonomous engine with multi-provider LLM support (OpenAI, Anthropic, OpenRouter, Cerebras, Ollama).

## Key Components
- **Agent Engine**: `agent/engine.py` — recursive sub-agent delegation, context condensation heuristic at 75% window threshold
- **Knowledge Graph**: Cytoscape.js visualization with entity color-coding by category (corporate, campaign-finance, lobbying, contracts, sanctions)
- **Data Collectors**: 15+ source integrations (SEC EDGAR, FEC, SAM.gov, OFAC SDN, EPA Echo, OSHA, FDIC, ICij Offshore Leaks, Census ACS, ProPublica 990s)
- **Entity Resolution**: Cross-dataset entity matching via `phase2_collectors/entity_resolver.py`
- **Wiki Curator**: Background agent maintaining document consistency and cross-links
- **Test Suite**: 40+ test files covering tools, settings, TUI, session management, live models

## Data Sources
| Domain | Sources |
|--------|---------|
| Corporate | SEC EDGAR, Massachusetts SOC |
| Campaign Finance | FEC Federal, Massachusetts OCPF |
| Contracts | SAM.gov, USAspending, Boston Open Checkbook |
| Sanctions | OFAC SDN |
| Regulatory | EPA Echo, OSHA Inspections |
| Financial | FDIC BankFind, ProPublica 990s |
| Infrastructure | Census ACS |
| International | ICIJ Offshore Leaks |
| Lobbying | Senate LD |

## Assessment
**Strengths**: Production-ready desktop app, comprehensive data coverage, entity resolution pipeline, live graph visualization, multi-LLM provider abstraction
**Gaps**: No automated CI/CD for data freshness, collector error handling untested, graph persistence limited to session
**Risk Profile**: Medium — depends on external API stability, rate limiting not addressed in collectors

## Cross-References
- [[oss-ingestion.md]] — Shared intelligence ingestion patterns
- [[consolidation-idempotency.md]] — Entity resolution parallels to claim deduplication
