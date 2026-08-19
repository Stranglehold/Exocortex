# OpenPlanter OSINT Framework Assessment

## Framework Maturity Score: 7.5/10

### Architecture Overview
- **Agent Engine**: Recursive LLM investigation with graph-based HTN workflow
- **Desktop App**: Tauri 2 with Cytoscape.js knowledge graph visualization
- **Collector Suite**: 12 specialized collectors (Phase 2-4) with shared BaseCollector
- **Wiki System**: 17 structured data source reference pages
- **Test Coverage**: 44+ tests across agent modules, tools, and collectors

### Strengths
1. **Modular collector design** — clean separation of concerns, easy to extend
2. **Knowledge graph integration** — real-time entity/relationship visualization
3. **Multi-provider LLM support** — OpenAI, Anthropic, OpenRouter, Cerebras, Ollama
4. **Comprehensive test suite** — covers core agent functionality
5. **Background wiki curator** — maintains documentation consistency

### Capability Gaps
1. **Real-time ingestion** — OSS V2 shows volume_anomaly, ingestion paused
2. **Entity resolution** — Partial implementation, needs cross-source deduplication
3. **Temporal analysis** — Limited time-series correlation across data sources
4. **Dark web monitoring** — No collectors for underground sources

### Comparison to Wiki Decisions
- **dec-upstream-pruning.md** — Proposed pruner layer NOT yet implemented
- **dec-conditional-injection.md** — Gate function NOT yet implemented
- Both decisions represent unimplemented architectural improvements

### Production Readiness Assessment
| Component | Status | Confidence |
|-----------|--------|------------|
| Data Collection | ✅ Mature | 0.85 |
| Entity Resolution | ⚠️ Partial | 0.60 |
| Real-time Ingestion | ❌ Degraded | 0.30 |
| Documentation | ✅ Complete | 0.90 |
| Test Coverage | ⚠️ Medium | 0.65 |

### Recommendations
1. Fix OSS V2 volume_anomaly to restore continuous ingestion
2. Implement upstream pruner (dec-upstream-pruning.md)
3. Implement conditional injection gate (dec-conditional-injection.md)
4. Add temporal correlation engine
5. Expand entity resolution cross-referencing

---
*Assessment generated during Workshop Cycle #21*

## See Also
- [Investigation Framework](index.md#current-projects)
- [Index](index.md)
