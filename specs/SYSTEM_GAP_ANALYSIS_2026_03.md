# System Gap Analysis — Exocortex Stack
*March 2026 — Research-Driven Design Methodology applied as analytical layer*

> **Purpose:** A systematic Phase 0 + Phase 4 analysis of the full 12-layer stack using the Research-Driven Design Methodology as a diagnostic lens. Every gap includes a proposed solution with enough specificity to hand off for implementation. This document feeds the next design cycle and serves as the standing gap record — update it as gaps close.

---

## Phase 0: Baseline

**What exists:** 32 extensions across 11 hook directories. 2 microservices (OSS, SWARMFISH). 5 custom tools. All 12 layers deployed. 3 stress tests run (ST-001, ST-002, ST-003). One formal fabrication event documented (ST-003).

**What the system demonstrably does:**
- Classifies intent and enriches context before every LLM call (BST, Metacognitive Injection)
- Extracts and tracks entities across turns (Working Memory)
- Gates high-risk actions behind authorization tiers (Action Boundary)
- Classifies errors deterministically before the model reasons about them (Error Comprehension)
- Audits model output against evidence ledger for fabrication risk (Epistemic Integrity)
- Manages memory lifecycle with four-axis classification (Memory Classification, Enhancement)
- Tracks geopolitical claims with confidence/volatility scoring (OSS + SWARMFISH)
- Resolves entities and maintains a relationship graph (Ontology)
- Detects loop/stall patterns and steers strategically (Supervisor)
- Captures conversational insights deterministically (Insight Capture)
- Consolidates session knowledge during idle periods (Sleep Consolidation)
- Injects custom tool catalog every turn (Tool Registry)

**What the system does not demonstrably do:**
- Use the operational data it generates to improve its own future operation
- Share state between layers via any unified mechanism
- Integrate its two intelligence services (OSS and Ontology) despite natural overlap
- Prevent the same warning from being injected by multiple layers simultaneously

**Gap statement:** The stack has moved from a collection of correct individual components to a system that needs to compose. The next frontier is coordination, feedback loops, and integration — not new layers.

---

## Load-Bearing Dimensions

Five dimensions where getting it wrong degrades the system meaningfully:

1. **Inter-Layer Coordination** — layers must not interfere with each other or produce contradictory signals
2. **Operational Feedback Loops** — the system generates self-improvement data; that data must flow somewhere
3. **Cross-Service Integration** — OSS and Ontology are intelligence services with natural overlap that currently don't share information
4. **Coverage Completeness** — the action governance and epistemic integrity layers have structural blindspots that remain unexercised
5. **Signal-to-Noise at the Model** — the model receives injected context from 8+ sources per turn; the aggregate must be useful, not overwhelming

---

## Dimension 1: Inter-Layer Coordination

### Gap 1A — Layer signals are ad-hoc point-to-point
**Severity:** Design Debt → will become Critical at scale
**Status:** Named in roadmap (Layer Coordination Protocol, Priority 4). Deferred.

The 12 layers communicate via named attributes on `self.agent` or `loop_data.extras_persistent`, each using a different naming convention: `_action_gate_active`, `_error_diagnosis`, `_epistemic_integrity`, `_bst_domain`, `_working_memory`. When a new layer needs to read another layer's state, the developer must know each specific attribute name and where it's stored. There is no contract, no discovery mechanism, no schema.

The consequence is not yet a failure — the point-to-point wiring works — but every new layer that needs coordination adds N new bespoke connections rather than reading a shared bus.

**Proposed Solution: `_layer_signals` bus in `extras_persistent`**

Add a shared `_layer_signals` dict to `loop_data.extras_persistent`. All inter-layer state is published here by convention. A lightweight utility function handles access:

```python
# In helpers/layer_signals.py (new file, ~40 lines)
def publish(loop_data, layer: str, signal: str, value):
    if "_layer_signals" not in loop_data.extras_persistent:
        loop_data.extras_persistent["_layer_signals"] = {}
    loop_data.extras_persistent["_layer_signals"][f"{layer}.{signal}"] = value

def read(loop_data, layer: str, signal: str, default=None):
    bus = loop_data.extras_persistent.get("_layer_signals", {})
    return bus.get(f"{layer}.{signal}", default)
```

Existing ad-hoc attributes migrate incrementally: new extensions use `publish()`/`read()`, existing ones migrate when touched for other reasons. No forced migration. The bus is additive, not a replacement — old attributes stay until each layer is updated.

**Example published keys:**
```
bst.domain, bst.confidence, bst.compound_domain
action_boundary.gate_active, action_boundary.last_tier
error_comprehension.error_class, error_comprehension.anti_actions
epistemic_integrity.last_verdict, epistemic_integrity.ungrounded_count
supervisor.turn_count, supervisor.loop_tier
```

**Files:** New `helpers/layer_signals.py`. Update each extension to publish on write, over time.
**Size:** ~40-line utility + incremental per-extension migrations (~5 lines each).

---

### Gap 1B — Dual failure tracking
**Severity:** Design Debt
**Status:** Named in roadmap (Failure Tracking Unification, Priority 6). Deferred.

`_tool_failures` (in `_30_tool_fallback_logger.py`) and `_stall_history` (in `_50_supervisor_loop.py`) track overlapping failure data independently. The fallback sees per-tool failure counts; the supervisor sees per-turn stall patterns. A tool that fails three times in a row is visible to the fallback system as a pattern; the supervisor may not have fired stall detection yet. Inconsistent health picture across layers.

**Proposed Solution: Unified `FailureRecord` on `agent._failure_history`**

Replace both with a single list of `FailureRecord` dicts stored on `self.agent._failure_history`:

```python
# Structure
{
    "turn": int,
    "tool": str,
    "error_class": str,           # from error_comprehension taxonomy
    "output_hash": str,           # for stagnation detection
    "resolved": bool,             # set True by reset_failure_counter
    "supervisor_fired": bool,     # set True when supervisor injected
    "fallback_fired": bool        # set True when fallback injected
}
```

Both `_30_tool_fallback_logger.py` and `_50_supervisor_loop.py` read/write from this shared list. The fallback logs and reads it for per-tool counts. The supervisor reads it for per-turn stall detection. Each layer still makes independent decisions — they just share the underlying data.

**Files:** `extensions/tool_execute_after/_30_tool_fallback_logger.py` and `extensions/message_loop_end/_50_supervisor_loop.py`. ~30-line change each.

---

### Gap 1C — Warning injection produces the Immune Response pattern in microcosm
**Severity:** Design Debt → Critical on next stress test
**Status:** Named in roadmap (Warning Injection Lane, Priority 5). Deferred. **Should not stay deferred.**

A single bad tool call can trigger four warning injectors simultaneously: supervisor (strategic), fallback advisor (tactical), meta-reasoning gate (parameter correction), structured retry (format compliance). Each is correct in isolation. Collectively they overwhelm the model with competing diagnoses for the same event.

This is precisely the Immune Response pattern that motivated the Phase 1 audit — the fallback system at 80% false positives was an autoimmune response. That was fixed. The same pattern has re-emerged across four injectors. The time to address it is before the next stress test surfaces it as a crisis.

**Proposed Solution: Jurisdictional assignment + event deduplication gate**

**Step 1 — Assign jurisdiction** (no code change, design decision):
- **Supervisor:** strategic steering only (loop pattern, stall, context exhaustion). Not errors.
- **Error Comprehension:** error class + anti-actions. Always fires, but once per error event.
- **Meta-Reasoning Gate:** parameter correction only. Fires *before* execution (already in `tool_execute_before`), so no overlap with post-execution injectors.
- **Structured Retry:** JSON format errors only. Not tool execution errors.
- **Fallback Advisor:** pre-flight advice for known failure patterns (already in `tool_execute_before`).

The natural hook separation (before vs. after execution) already prevents most overlap. The residual overlap is between Error Comprehension and the Fallback Logger — both fire in `tool_execute_after`.

**Step 2 — Add deduplication gate** (~30 lines in `tool_execute_after`):

```python
# In loop_data.extras_persistent
"_warnings_this_turn": set()   # cleared at turn start by context_watchdog

# In each tool_execute_after warning injector
event_key = (loop_data.iteration, tool_name, error_class)
if event_key in loop_data.extras_persistent.get("_warnings_this_turn", set()):
    return  # already warned about this event
loop_data.extras_persistent.setdefault("_warnings_this_turn", set()).add(event_key)
# proceed with injection
```

**Priority:** Error Comprehension > Fallback Logger. If EC fires, fallback skips.

**Files:** `_20_context_watchdog.py` (clear set at turn start), `_20_error_comprehension.py`, `_30_tool_fallback_logger.py`. ~30 lines total.

---

## Dimension 2: Operational Feedback Loops

This dimension surfaces the most significant structural gap: **the system generates rich operational telemetry but consumes almost none of it to improve future operation.** The gaps below share a root cause — layers are built to collect before the architecture has a clear answer for where the data goes. Addressing them as a group (rather than one at a time) produces better design.

### Gap 2A — Sleep Consolidation findings don't feed BST or Supervisor
**Severity:** High Design Debt
**Status:** Not in roadmap. Newly identified.

Sleep consolidation writes reports to `/a0/usr/Exocortex/sleep_reports/` with anti-patterns, recurring failures, and episode summaries. Nothing reads them. The supervisor pre-empts patterns it has already seen in this session; it cannot pre-empt patterns it's seen in prior sessions.

**Proposed Solution: Session-start anti-pattern injection via `_10_session_init.py`**

A new extension at `before_main_llm_call/_10_session_init.py` (runs once per session, before BST). On first turn of a new session (`not hasattr(self.agent, "_session_init_done")`):

1. Read the most recent sleep report from `/a0/usr/Exocortex/sleep_reports/`
2. Extract the `anti_patterns` array (already structured JSON in the report)
3. Build a compact `[KNOWN PATTERNS FROM PRIOR SESSIONS]` block:
   ```
   [KNOWN PATTERNS]
   git push auth: always fails — check credentials before attempting
   interactive pip install: triggers terminal hang — use pip install -q --no-input
   [/KNOWN PATTERNS]
   ```
4. Prepend to the first user message in `loop_data.history_output`
5. Set `self.agent._session_init_done = True`

The supervisor also reads anti-patterns at init to pre-populate `_stall_history` with known-bad patterns, so loop detection fires faster on recurring failures.

**Files:** New `extensions/before_main_llm_call/_10_session_init.py` (~80 lines). Minor update to `_50_supervisor_loop.py` (~10 lines) to read anti-patterns at session start.

---

### Gap 2B — BST classification outcomes not tracked
**Severity:** Medium Design Debt
**Status:** Not in roadmap. Newly identified.

BST classifies intent with confidence scores. If the classification is wrong (classified `analysis`, agent spent 10 turns doing `code_execution`), nothing records the mismatch. The system cannot self-calibrate thresholds over time. Every session uses the same confidence thresholds regardless of observed performance.

**Proposed Solution: Classification outcome log at `monologue_end`**

Add a classification outcome check to `_52_selective_memorizer.py` (or a new `_54_bst_calibration.py` at `monologue_end`):

At end of each turn, compare `_bst_domain` (classified intent) against the tools actually used (read from `loop_data.history_output`, last AI turn). If the dominant tool category doesn't match the expected tools for the classified domain (e.g., domain=`analysis`, dominant_tool=`code_execution`), write a mismatch record:

```json
{
    "turn": 42,
    "session": "2026-03-21",
    "classified_domain": "analysis",
    "dominant_tool": "code_execution",
    "bst_confidence": 0.74,
    "user_message_snippet": "debug this..."
}
```

Output: `/a0/usr/Exocortex/bst_calibration_log.jsonl`

A separate offline script (`scripts/analyze_bst_calibration.py`) reviews the log and suggests threshold adjustments. Manual review for now; the data enables automated adjustment later.

**Files:** New `extensions/monologue_end/_54_bst_calibration.py` (~60 lines). New `scripts/analyze_bst_calibration.py` (~80 lines).

---

### Gap 2C — Memory access patterns collected but not fed back into retrieval ranking
**Severity:** Medium Design Debt
**Status:** Not in roadmap. Newly identified.

`_55_memory_classifier.py` tracks `access_count` and `last_accessed` per memory. `_57_memory_maintenance.py` reads `co_retrieval_log.json` to find memories frequently retrieved together. Both were designed to feed lifecycle decisions. The `access_count` is used for dormancy archival. It is **not** used in retrieval ranking.

A memory retrieved and confirmed useful 40 times ranks identically to a newly created memory, if their cosine similarity scores are equal. The sensor is wired. The actuator is not.

**Proposed Solution: Access-weighted retrieval scoring in `_56_memory_enhancement.py`**

In the ranking step of `_56_memory_enhancement.py`, apply a logarithmic access boost to the similarity score:

```python
def _score_memory(self, doc, similarity_score):
    access_count = doc.metadata.get("access_count", 0)
    access_boost = 1 + math.log1p(access_count) * 0.15   # 0.15 = tunable weight
    return similarity_score * access_boost
```

For co-retrieval: after top-K selection, check `co_retrieval_log.json` for each selected memory. If memory A is selected and memory B has co-retrieval frequency ≥ 3 with A, add B to the candidate set with a co-retrieval bonus score. Subject to the existing cap.

**Files:** `extensions/message_loop_prompts_after/_56_memory_enhancement.py`. ~25-line addition.

---

### Gap 2D — Action audit log generates patterns that nothing analyzes
**Severity:** Low Design Debt
**Status:** Not in roadmap. Newly identified.

`_15_action_boundary.py` writes every authorization decision to `/a0/usr/logs/action_audit.jsonl`. Over sessions, this log is ground-truth data on what kinds of operations the agent attempts and how they're classified. Tier distribution, most common Tier-3/4 patterns, workflows that routinely approach the authorization boundary — all derivable from the existing data.

Currently written and never read.

**Proposed Solution: Audit analysis script + stack_status integration**

New `scripts/analyze_action_audit.py` (~100 lines). Reads the audit log, produces:
```json
{
    "total_actions": 847,
    "tier_distribution": {"1": 710, "2": 98, "3": 35, "4": 4},
    "tier4_patterns": ["git push origin main", "docker push", "npm publish"],
    "tier3_top_tools": ["code_execution (bash -c curl)", "file_write (/etc/)"],
    "anomalies": []
}
```

`stack_status.py` reads the latest audit summary JSON (generated by the script) and includes it in the stack report. Operator can run the analysis script manually or on a cron schedule.

**Files:** New `scripts/analyze_action_audit.py`. Update `tools/stack_status.py` (~10 lines) to read summary.

---

## Dimension 3: Cross-Service Integration

### Gap 3A — OSS and Ontology have zero integration
**Severity:** Critical Design Debt (architectural oversight)
**Status:** Not in roadmap. Newly identified by methodology application.

This is the most significant gap this analysis surfaces. Two intelligence systems were designed and deployed independently despite deep natural overlap:

- **OSS** tracks claims about entities: "Iran seized a tanker in the Strait of Hormuz." Claim confidence, source trust, volatility.
- **Ontology** tracks the entities in those claims: Iran, IRGC, Strait of Hormuz. Their relationships and properties.

They do not communicate. An analyst working both systems must manually reconcile two separate intelligence pictures. The cross-referencing that should happen automatically requires manual operator effort.

**Why this wasn't caught earlier:** The two systems were built in sequence for different design goals. The integration gap is only visible when both are running and viewed as a whole. This is exactly what Phase 0 measurement surfaces — integration gaps that emerge from seeing the full system together.

**Proposed Solution: Three integration points, phased**

**Phase 1 (implement first, 2-3 days):** Claim → entity linking on ingest

When a claim is ingested into OSS (`oss_submit` or RSS pipeline), run entity extraction against the ontology:
```python
# In oss.py or ingest.py, after claim insertion
entity_ids = ontology_query.extract_entities_from_text(claim_text)
if entity_ids:
    db.execute("UPDATE claims SET linked_entities = ? WHERE id = ?",
               (json.dumps(entity_ids), claim_id))
```

The ontology query is already accessible via `_58_ontology_query.py` patterns. Entity IDs are added as `linked_entities` array to the claim record.

**Phase 2 (after Phase 1 validated, 1-2 days):** Entity → claims lookup

New OSS API endpoint: `GET /claims/by_entity/<entity_id>` returns claims linked to a specific ontology entity. When an analyst queries an entity from the Ontology, the response includes recent OSS claims about that entity. Makes both systems richer without structural coupling.

**Phase 3 (last, requires Phase 1 + 2):** Hypothesis → relationship confidence

When a hypothesis is promoted or falsified in OSS, fire a callback to the Ontology updating confidence on relationships that were involved. Use the existing `oss_bridge.py` pattern in SWARMFISH as the template — best-effort, non-blocking, logged on failure.

**Files:**
- Phase 1: `services/oss/ingest.py` and/or `tools/oss.py` (~40 lines)
- Phase 2: `services/oss/app.py` (~20 lines)
- Phase 3: `services/oss/hypothesis.py` + new ontology endpoint (~50 lines)

---

### Gap 3B — SWARMFISH calibration scores don't return to OSS
**Severity:** Medium Design Debt
**Status:** Not in roadmap. Half-implementation identified.

OSS fires to SWARMFISH on promote/falsify (`POST /acp/outcome`). SWARMFISH accumulates calibration history and can produce per-claim-type confidence adjustments. But the calibration scores never return to OSS. The loop is half-wired.

`oss_bridge.py` in SWARMFISH was designed to carry signal back. The return channel isn't implemented.

**Proposed Solution: SWARMFISH calibration pull from OSS**

Add endpoint to SWARMFISH: `GET /calibration/adjustments?claim_type={type}` returns:
```json
{
    "claim_type": "geopolitical_movement",
    "confidence_multiplier": 0.87,
    "sample_size": 42,
    "last_updated": "2026-03-20T14:23:00Z"
}
```

In OSS `hypothesis.py`, before writing hypothesis confidence to DB, call this endpoint and apply the multiplier:
```python
calibration = swarmfish_get_adjustment(claim_type)
adjusted_confidence = raw_confidence * calibration.get("confidence_multiplier", 1.0)
```

Best-effort: if SWARMFISH is unavailable, use raw confidence. Log the adjustment.

**Files:** `services/swarmfish/app.py` (~30 lines), `services/oss/hypothesis.py` (~20 lines).

---

### Gap 3C — Profile-aware BST enrichment suppression (DEC-012) unbuilt
**Severity:** Medium Design Debt
**Status:** Named in DEC-012, old roadmap Priority 4. Not built despite compound BST deployment.

The active model profile at `/a0/usr/Exocortex/eval/model_profiles/qwen3.5-27b-*.json` has a `disabled_domains` field. The BST v3.1 doesn't read it. The BST enriches even in domains where the model profile specifies that enrichment degrades performance. This is DEC-001 (deterministic scaffolding) being violated by the scaffolding itself — enriching in a domain known to hurt is worse than not enriching.

**Proposed Solution: Profile read in BST enrichment gate**

In `_11_belief_state_tracker.py`, after domain classification, before enrichment injection:

```python
def _should_enrich(self, domain: str) -> bool:
    profile_path = self.agent.data.get("active_model_profile_path")
    if not profile_path:
        return True  # graceful degradation
    try:
        with open(profile_path) as f:
            profile = json.load(f)
        return domain not in profile.get("disabled_domains", [])
    except Exception:
        return True  # graceful degradation
```

The profile path is already resolved by `_14_metacognitive_injection.py` — read from `self.agent.data["active_model_profile_path"]` (set by metacognitive injection on first turn). If that attribute isn't set yet, degrade gracefully to always-enrich.

**Files:** `extensions/before_main_llm_call/_11_belief_state_tracker.py`. ~20-line addition.

---

### Gap 3D — A2A deployed with no active peer
**Severity:** Note (not actionable without use case)

The A2A compatibility layer is fully deployed as a standalone aiohttp server. The protocol, endpoints, and authentication all exist. No peer agent is configured. This is not a gap to fix — it represents infrastructure waiting for activation.

**Proposed solution when use case emerges:** The first natural A2A target is an OSS peer for claim deduplication across concurrent sessions, or a dedicated investigation agent that runs OpenPlanter as an A2A peer. When a concrete use case is approved, the infrastructure is ready in one day.

**Do not build until use case is defined.** Infrastructure without activation is maintenance burden.

---

## Dimension 4: Coverage Completeness

### Gap 4A — Action Boundary doesn't gate read-to-channel exfiltration
**Severity:** Medium Design Debt (architectural gap in safety model)

The Action Boundary gates write operations with escalating tiers. Tier 4 blocks identity-write actions. But a capable agent can cause harm by reading sensitive material and including it verbatim in a response — API keys, tokens, credentials stored in settings files. The action boundary sees a read (Tier 1: autonomous) followed by a response (not classified as consequential).

This is a natural behavior pattern, not a contrived attack. Agents read files to understand them, then reference their contents in responses. If those contents include secrets, the secrets appear in the UI and logs.

**Proposed Solution: Sensitive-path read classification in `_15_action_boundary.py`**

Add a sensitive path pattern set:
```python
SENSITIVE_PATH_PATTERNS = [
    r"settings\.json$", r"\.env$", r"\.env\.",
    r"(token|secret|password|key|credential|api_key)",
    r"/usr/Exocortex/eval/model_profiles/",  # contains model capability details
]
```

When `code_execution_tool` or `document_query` targets a path matching a sensitive pattern, classify the read as **Tier 2** (log and proceed) rather than Tier 1. The audit log captures the read. No block — the operation proceeds — but visibility is created. The operator can review audit logs for unexpected sensitive reads.

This is not a block. It is a **visibility gate** — the minimal intervention needed given that the operation is likely legitimate but the outcome should be auditable.

**Files:** `extensions/tool_execute_before/_15_action_boundary.py`. ~25-line addition.

---

### Gap 4B — Epistemic Integrity trusts tool outputs uncritically
**Severity:** Medium Design Debt (structural limitation of evidence ledger model)

The EI layer marks claims as GROUNDED if they appeared in tool output this session. This is correct for the designed threat model: fabrication from model weights (ST-003 class failures). It does not address laundered fabrication — tool output that itself contained unreliable data (fabricated search result, stale API response, corrupted file).

EI is an effective safeguard against what it was designed to catch. The gap is that its trust model for tool outputs is binary (appeared/didn't appear) with no weighting by source reliability.

**Proposed Solution: Source reliability classification in `_25_evidence_ledger_recorder.py`**

When recording tool output to the evidence ledger, classify the source type and assign a reliability tier:

```python
SOURCE_RELIABILITY = {
    "code_execution": "high",      # local deterministic execution
    "file_read": "high",           # local file contents
    "memory_load": "medium",       # retrieved from prior sessions
    "search_engine": "medium",     # external, unverified
    "document_query": "medium",    # external document, unverified
    "browser_agent": "low",        # web content, highly variable
}
```

Add `source_reliability` to each evidence ledger entry. In `_25_epistemic_integrity.py`, modify the GROUNDED verdict:
- `GROUNDED` (high reliability source) — unchanged
- `GROUNDED_UNVERIFIED` (medium reliability) — passes but adds a note: "sourced from unverified external source"
- `VERIFY_SOURCE` (low reliability) — same as VERIFY_IF_CRITICAL but with source attribution

This doesn't change the primary defense (fabrication detection). It adds a second dimension to the verdict for values sourced from low-reliability channels.

**Files:** `extensions/tool_execute_after/_25_evidence_ledger_recorder.py` (~20 lines), `extensions/monologue_end/_25_epistemic_integrity.py` (~30 lines).

---

### Gap 4C — OSS active topic coverage is narrow
**Severity:** Operational Gap (not architectural)

Two active topics: `iran-hormuz` and `iran`. The OSS service is designed for configurable multi-topic monitoring. `oss_add_topic` works. The narrow coverage means EI's OSS cross-check returns "no context available" for nearly all topics — reducing the value of the integration.

**Proposed Solution: Topic expansion protocol**

This is an operational task, not a build task. Proposed coverage expansion:

| Domain | Suggested Topics |
|--------|-----------------|
| Geopolitical/Middle East | iran, iran-hormuz, israel-hamas, saudi-iran, red-sea-shipping |
| Energy/Infrastructure | oil-markets, lng-europe, grid-stability |
| AI/Technology | ai-regulation, frontier-models, semiconductor-supply |
| Financial | credit-markets, sovereign-debt, dollar-dominance |

Use `oss_add_topic` via conversation with the agent to expand coverage. Prioritize topics relevant to active analytical focus. The ingestion pipeline starts paused by default — `oss_ingest_resume` activates it per-topic.

---

### Gap 4D — Ontology resolution thresholds unvalidated at scale
**Severity:** Note (needs data, not redesign)

The five-stage resolution pipeline uses difflib string metrics with confidence thresholds set during design. Under real-world conditions — transliterations, acronyms, partial names — the thresholds may produce false positives (merging distinct entities) or false negatives (failing to match the same entity).

**Proposed Solution: Empirical validation via investigation task**

Run a targeted investigation task against the iran-hormuz OSS topic with ontology querying active. Seed the ontology with 20-30 known entities (Iran, IRGC, Strait of Hormuz, specific vessels, named officials). Observe resolution behavior. Tune thresholds from real mismatch data, not design assumptions.

Do not redesign the resolution engine. Tune the thresholds.

---

## Dimension 5: Signal-to-Noise at the Model

### Gap 5A — Exocortex injection volume has never been measured
**Severity:** Design Debt

Per turn, the model receives injected context from 8+ sources: BST enrichment, operator profile, metacognitive injection, memory catalog (session start), tool registry, recalled memories, ontology results, EI warnings, supervisor warnings, tiered tool spec. The context watchdog monitors total token budget utilization. But it doesn't distinguish Exocortex injections from conversation history.

Hypothesis: injections have grown from ~5-10% of context window at stack launch to potentially 20-30%+ with the full 12-layer deployment. This has never been measured. If the hypothesis is correct, each new layer added reduces the effective context available for actual conversation.

**Proposed Solution: Injection volume tracking in `_20_context_watchdog.py`**

After the context watchdog reads token utilization, measure Exocortex injection volume by counting characters in all `loop_data.system` segments that contain Exocortex markers (`[BST]`, `[MEMORY CATALOG]`, `[CUSTOM TOOLS]`, `[MODEL CONFIGURATION]`, `[OPERATOR PROFILE]`, EI warnings). Report as a fraction of total context:

```python
exo_chars = sum(
    len(seg.get("content", ""))
    for seg in loop_data.system
    if any(marker in seg.get("content", "")
           for marker in ["[BST]", "[MEMORY CATALOG]", "[CUSTOM TOOLS]",
                          "[MODEL CONFIGURATION]", "[OPERATOR PROFILE]",
                          "[EPISTEMIC", "[WARNING"])
)
total_chars = sum(len(str(m)) for m in loop_data.history_output)
injection_ratio = exo_chars / max(total_chars, 1)
```

Log this metric alongside standard utilization. Alert at `injection_ratio > 0.25`. Store in `loop_data.extras_persistent["_layer_signals"]` for other layers to read.

**Files:** `extensions/before_main_llm_call/_20_context_watchdog.py`. ~30-line addition.

---

### Gap 5B — Warning injection volume has no session-level measurement
**Severity:** Medium Design Debt

Each warning injector logs individually. There's no aggregate: "how many warnings were injected across this full session?" The gap matters because warning volume is the leading indicator of the Immune Response pattern reforming (Gap 1C). A session with 20 warnings across 30 turns is a different quality of session than one with 2 warnings, but the system has no visibility into the aggregate.

**Proposed Solution: Session-level warning counter in `extras_persistent`**

Each warning injector increments a shared counter before injecting:

```python
# One line added to each warning injector
loop_data.extras_persistent["_session_stats"] = loop_data.extras_persistent.get("_session_stats", {})
loop_data.extras_persistent["_session_stats"]["warnings_injected"] = \
    loop_data.extras_persistent["_session_stats"].get("warnings_injected", 0) + 1
```

At session end (sleep trigger fires), write session stats to the sleep report header. `stack_status.py` reads `_session_stats["warnings_injected"]` from the current session for the live count.

**Files:** ~5-line addition to each of the four warning injectors + `tools/stack_status.py`. Total ~25 lines.

---

## What Is Working Well — Do Not Touch

The methodology requires explicit acknowledgment. These components have earned their stability through stress testing and production operation.

**BST v3.1 compound classification** — Word-boundary regex + domain momentum + compound detection solved the domain-flip problem. Validated on real investigation workflows. Don't modify classification logic without a corresponding stress test.

**Working Memory entity extraction** — 25 entities from a README in ST-002. Holds objectives across 20-step chains. The decay + promotion mechanism is correct. The BST integration via `working_memory_lookup` resolver is the right pattern.

**Error Comprehension** — Deterministic 8-class taxonomy with anti-actions. Solved the misdiagnosis loop from ST-001. The "Rust compiler for agent errors" design is sound and correctly positioned in `tool_execute_after`.

**Action Boundary four-tier system** — Tier 4 block on identity-write is correct. The `_action_gate_active` flag wired to the supervisor to suppress false stalls is a clean coordination solution. Don't add tiers without empirical data from audit logs.

**Epistemic Integrity verdict matrix** — The GROUNDED/FABRICATION_RISK/DO_NOT_TRUST spectrum is right. Provenance × volatility × staleness is the correct three-component check. Gap 4B is a structural extension, not a correction.

**Selective Memorizer + Memory Classifier + Insight Capture** — Three-layer memory input pipeline is architecturally sound. The four-axis classification is the correct granularity.

**Sleep Consolidation Phase 1** — Idle detection and session-boundary consolidation work correctly. Gap 2A is downstream (data not consumed), not a Phase 1 problem.

**OSS service architecture** — 10 tools, analyst-as-source pipeline, thinking-token stripping, RSS ingestion, SWARMFISH integration. The gaps are coverage and integration, not design.

---

## Gap Summary and Build Sequence

### Priority Matrix

| # | Gap | Dimension | Severity | Effort | Dependencies |
|---|-----|-----------|----------|--------|--------------|
| 1C | Warning injection deduplication | Coordination | High | Small (~30 lines) | EC (done) |
| 3C | Profile-aware BST suppression | Integration | Medium | Tiny (~20 lines) | Model profile (done) |
| 2C | Memory access → retrieval ranking | Feedback | Medium | Small (~25 lines) | access_count (done) |
| 1B | Unify failure tracking | Coordination | Medium | Small (~60 lines) | Nothing |
| 3A-P1 | OSS → Ontology entity linking | Integration | High | Medium (~40 lines) | Both running |
| 2A | Sleep reports → session init | Feedback | High | Medium (~80 lines) | Sleep Phase 1 |
| 4A | Sensitive-path read visibility | Coverage | Medium | Small (~25 lines) | Action Boundary |
| 1A | Layer signals bus | Coordination | Low now, High later | Medium (~40+migrations) | Nothing |
| 5B | Session warning counter | Signal quality | Medium | Tiny (~25 lines) | Nothing |
| 5A | Injection volume measurement | Signal quality | Medium | Small (~30 lines) | Watchdog (done) |
| 2B | BST outcome tracking | Feedback | Medium | Small (~60 lines) | Nothing |
| 3B | SWARMFISH return channel | Integration | Medium | Small (~50 lines) | oss_bridge |
| 3A-P2 | OSS entity → claims lookup | Integration | Medium | Small (~20 lines) | 3A-P1 |
| 4B | EI source reliability | Coverage | Medium | Small (~50 lines) | EI (done) |
| 2D | Action audit analysis script | Feedback | Low | Small (~100 lines) | Audit log |
| 3A-P3 | Hypothesis → ontology confidence | Integration | Low | Medium (~50 lines) | 3A-P1+P2 |
| 4C | OSS topic expansion | Coverage | Operational | Operational task | oss_add_topic |
| 3D | A2A peer | Integration | Note | Blocked on use case | — |
| 4D | Ontology threshold tuning | Coverage | Note | Blocked on data | Investigation task |

### Recommended Build Sequence

**Wave 1 — Small, high-value, no dependencies (1-2 sessions):**
1. Gap 3C — Profile-aware BST suppression (~20 lines)
2. Gap 1C — Warning injection deduplication (~30 lines)
3. Gap 2C — Memory access boost in retrieval ranking (~25 lines)
4. Gap 5B — Session warning counter (~25 lines)

Four targeted fixes. Total: ~100 lines across 6 existing files. Collectively they close the three coordination gaps, improve retrieval quality, and give the system basic self-measurement. No new files needed.

**Wave 2 — Medium builds that unlock further work (2-3 sessions):**
5. Gap 1B — Unified failure tracking (~60 lines)
6. Gap 3A Phase 1 — OSS claim → ontology entity linking (~40 lines)
7. Gap 2A — Session init with sleep anti-patterns (~80 lines)
8. Gap 5A — Injection volume measurement in watchdog (~30 lines)

**Wave 3 — Larger system-level improvements (3-4 sessions):**
9. Gap 4A — Sensitive-path read visibility (~25 lines)
10. Gap 1A — Layer signals bus (utility + incremental migrations)
11. Gap 4B — EI source reliability tiers (~50 lines)
12. Gap 3B — SWARMFISH calibration return channel (~50 lines)

**Wave 4 — When data exists:**
13. Gap 2B — BST calibration outcome log (after 1-2 sessions of data)
14. Gap 3A Phase 2+3 — Entity lookup endpoint + hypothesis confidence update
15. Gap 4D — Ontology threshold tuning (after investigation task run)
16. Gap 2D — Action audit analysis script

---

## Three Structural Observations the Methodology Surfaces

**1. The data collection → action gap is systemic, not isolated.** Gaps 2A, 2B, 2C, 2D share a root cause: layers are built to collect before the architecture has a clear answer for where the data goes. The pattern will recur with every new layer added unless addressed architecturally. The Layer Signals Bus (Gap 1A) and a lightweight "operational telemetry bus" are the same problem. Fixing them together — rather than one gap at a time — produces a more durable solution.

**2. The OSS ↔ Ontology gap is the highest-value integration opportunity.** These two systems are tracking the same subject matter from different angles. Every investigation task that uses one but not the other leaves analytical value on the table. Phase 1 (claim → entity linking) is 40 lines. The value is proportional to every investigation task run afterward.

**3. The Immune Response pattern has re-emerged.** The Phase 1 audit fixed the fallback at 80% false positives by naming the pattern and measuring it. The same pattern — multiple protective systems firing on the same event — has reformed at the warning injection level across four layers. Gap 1C is the same class of failure at a different level of the stack. The time to address it is before it produces a stress test crisis, not after.

---

*Document type: Gap analysis with proposed solutions — Phase 0 + Phase 4 of the Research-Driven Design Methodology, updated with solution designs. Author: Kestrel, March 2026. This document should be updated as gaps close — mark each gap with `[CLOSED: date]` when the solution is deployed and verified.*
