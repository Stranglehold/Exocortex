# Exocortex Roadmap

*Living document. Updated after each significant session. See git log for full history.*

---

## Current Priorities

1. **Persistent tool path** — `/a0/usr/agents/agent0/tools/` doesn't exist; agent-built tools at `/a0/python/tools/` don't survive image rebuilds. Create the path, extend Tool Registry to scan both locations.

2. **Memory gist quality** — `memory_save.py` auto-generates gists as the first 100 characters (truncation, not summary). Needs an intelligent heuristic (skip blank lines and import statements, take first substantive content line) or a utility-model call at save time.

3. **Model routing** — Agent-invokable model selection from a configured list or LM Studio backend. Allows the agent to choose the right model for a subtask (fast utility vs. heavyweight reasoning) without operator intervention.

4. **Library ingestion** — Initial collection already staged: Hacking 2.0 (14 books) at `/a0/usr/workdir/library/inbox/`. Ask the agent to `scan the library for new books` to ingest. Then expand to Cybersecurity, Machine Learning, and Linux collections.

---

## Backlog

- **Curiosity queue** — Agent autonomously discovers and analyzes external repositories during idle time, rather than requiring the operator to point at one. Queue persists across sessions.
- **Layer coordination protocol** — Formalize the `_layer_signals` convention: each extension writes to a shared dict on the agent, other extensions read from it. Replace ad-hoc `getattr()` patterns.
- **Ontology hardening** — Source connector robustness, relationship confidence scoring, entity disambiguation across document types.
- **Multi-container orchestration** — Coordinate multiple Agent Zero instances (different models, different roles) through the A2A server.
- **Observability dashboard** — Live view of extension states, BST classification history, memory classification stats, supervisor tier counts, sleep consolidation reports.
- **CAPTCHA solver integration testing** — VLM-based rotation solver deployed; needs field validation against Arkose and reCAPTCHA v2.
- **Library expansion** — Progressive ingestion of remaining Humble Bundle collections (22 total, 363 books). Prioritized: Cybersecurity by Packt, Hacking for the Holidays, Machine Learning, Linux & UNIX by O'Reilly.

---

## Completed

*Reverse chronological. Each entry notes what was built and what motivated it.*

### 2026-03-30 — Document Library v2.0

Three-tier FAISS library (collection/book/chunk areas) with two-stage routing search and batch ingest. Completely isolated from agent episodic memory (`/a0/usr/memory/library/`). Catalog and file copies in workdir (`/a0/usr/workdir/library/`). Five tools: `library_add`, `library_list`, `library_search`, `library_remove`, `library_collections`. `_17_library_catalog.py` extension injects collection-level summaries each turn. `library-scan` skill handles batch directory ingestion. Scale tested against 363-book catalog (22 collections) — routing search bounds the search space regardless of library size.

### 2026-03-30 — Skills Library (16 skills + install fixes)

`install_skills.sh` deploys all skills from `agent_skills/` to `/a0/usr/skills/` persistently. Fixed phantom import errors in `api_calls` (missing `APICaller` class) and `content-sanitizer` (wrong module path). Added `rapidfuzz` fuzzy dedup to sleep consolidation for anti-pattern signatures — catches variants like `system_admin` ≈ `system_administration` with 85% threshold. Skill count grew to 16 installable skills.

### 2026-03-28 — Provider Interface max_tokens Fix

Patched `provider_interface.py` default `max_tokens` from 4096 to 16384. The previous default was truncating responses on any task requiring substantive output. Applied via `scripts/install_core_patches.sh` (Layer 1 in `install_all.sh`).

### 2026-03-27 — Theme Engine (Phases 1–3)

Phase 1: base theme deployment (9 themes: Blood Orange, Terminal Green, Deep Space, Quantum, Void, and others). Phase 2: Widget System (draggable/resizable UI components). Phase 3: Immersion Layer (thematic SVG background textures, backdrop blur). In-browser theme editor at `/theme-editor` — live JSON editing with syntax highlighting, color pickers, and one-click apply. Fixes applied for SVG visibility (backdrop blur + chat area CSS). Themes stored at `/a0/usr/agents/agent0/themes/` (DEC-030 persistent).

### 2026-03-26 — Tool Registry Expansion

Surfaced `scheduler` and `staging_note` tools (previously excluded from the registry). Added `[ARTIFACT RENDERING]` block injected every turn listing UI-renderable output types. Updated `call_subordinate` as primary escape route in Supervisor's loop intervention message.

### 2026-03-25 — Loop Recovery & Memory Surgery

Five coordinated changes to handle persistent loops without destroying memories created during legitimate work mixed into a loop episode. `_loop_active` flag marks loop-period memories. Evidence ledger records timeline boundaries. Phase 4 sleep consolidation adjudicates loop-period memories on next sleep cycle. False recovery detector: the first case of the supervisor reasoning about its own prior action history — if it attempted surgery on a tool and that tool fails again, it escalates immediately to Tier 3 rather than cycling through Tier 1 again.

### 2026-03-24 — Self-Improvement Loop (First Complete Cycle)

First documented complete cycle: operator points agent at external GitHub repo → agent extracts architectural patterns → agent autonomously builds new tools → new tools immediately callable by name (Tool Registry picks them up). Zero loops, zero operator interventions, clean context compression recovery. Demonstrates the floor working as designed.

### 2026-03-24 — Action Boundary Gap C

Third action boundary calibration fix: heredoc body detection. The gate was matching patterns inside heredoc content (the PAYLOAD being written) rather than the command constructing it. Added heredoc context detection to suppress false positives.

### 2026-03-23 — Behavioral Humanization

`browser_agent.py` monkey-patched with pure-Python Bézier cursor trajectories, calibrated Fitts's Law timing, and lognormal between-step sleep intervals. Derived from empirical mouse tracking data (685K events, 1991 sessions; dejanseo dataset). Speed p50=0.33px/ms, click-interval p50=732ms, lognormal(6.6, 1.1). Design note: `BEHAVIORAL_HUMANIZATION_DESIGN_NOTE.md`.

### 2026-03-22 — Persistent Profile Deployment (DEC-030)

Migrated entire extension stack from `/a0/python/extensions/` (ephemeral, wiped on image update) to `/a0/usr/agents/agent0/extensions/` (DEC-030 persistent profile path). Twenty-nine files, nine hook directories, three prompt files. Dropped three extensions (`_12_org_dispatcher`, `_13_operator_profile`, `_14_metacognitive_injection`) that were doing static work more efficiently handled by prompt files.

### 2026-03-21 — Supervisor Stagnation Detection

Added output stagnation detection to the supervisor: when N successful tool calls in a rolling window produce identical output hashes, the supervisor fires a stagnation intervention (different prescription from a loop — "your tool is working but you're not advancing"). Motivated by ST-006 finding that the consecutive failure counter stays at zero during stagnation.

### 2026-03-20 — Artifact Registry (C5), ST-007 Validated

`_49_reasoning_state_update.py` detects file writes from tool args (heredoc, echo redirect, tee, Python open) and writes to `staging.jsonl`. `_13_reasoning_state.py` bootstraps artifact list from staging on first turn of fresh context. All 6 ST-007 test cases pass. Agent cites correct file path in 1 turn from cold start after `docker restart` — no search, no re-derivation.

### 2026-03-19 — Sleep Consolidation Phases 0–4

Phase 0: staging tier lifecycle (promotion, archival, carry-forward). Phase 1: exact-hash deduplication. Phase 2: utility initialization. Phase 3: episode chunking. Phase 4: missed anti-pattern capture. Phase 4 also adjudicates loop-period memories (see Loop Recovery). Triggered by `tool_execute_after` hook on per-context asyncio tasks. Reports written to `/a0/usr/Exocortex/sleep_reports/`.

### 2026-03-18 — Epistemic Integrity Layer

Evidence Ledger Recorder (`_25_evidence_ledger_recorder.py`) tracks all tool outputs and extracts searchable key values (currencies, percentages, ratios, credit ratings, fiscal periods). EI Analyzer (`_25_epistemic_integrity.py`) checks model response claims against the ledger, classifies ungrounded claims by temporal volatility (structural → institutional → cyclical → transactional → ephemeral), computes staleness, and injects `hist_add_warning` for ungrounded high-volatility claims. Motivated by ST-003 Oracle fabrication.

### 2026-03-17 — OSS Service + SWARMFISH

OSS: Docker container on port 7731, Postgres backend, RSS ingestion, LLM claim extraction, FAISS deduplication. Ten tools including `oss_submit` (analyst as primary source). Thinking token stripping at all LLM call sites. SWARMFISH: Bayesian consensus engine on port 7732, two tools (`swarmfish_predict`, `swarmfish_calibration`). OSS→SWARMFISH calibration loop: hypothesis promotion/falsification fires `POST /acp/outcome` automatically.

### 2026-03-14 — Compound BST

Multi-domain scoring (all domains simultaneously vs. first-match). Momentum signatures carry forward from prior turn. Register-shift domains (orientation, meta_cognitive, philosophical) break momentum and provide minimal enrichment — cognitive space instead of technical framing. Eval harness: 0.98 accuracy across 54 labeled test cases, 14 domains.

### 2026-03-12 — Organization Kernel Phase 4 (A2A)

Standalone aiohttp A2A protocol server (Google Agent-to-Agent). Exposes agent capabilities as structured endpoints. Foundation for multi-agent coordination. Separate from Agent Zero's built-in A2A stub.

### 2026-03-10 — Tool Registry

Scans `/a0/python/tools/` every turn, injects `[CUSTOM TOOLS]` block with snake_case tool names and descriptions extracted via AST (no import). Also reads `tool_manifest.json` for manually-registered programs. New tools callable by name the turn after they're written — zero manual registration. Motivated by ST-004 finding: agent explored filesystem or reimplemented tools it already had.

### 2026-03-09 — Action Boundary Gaps A+B

Gap A: Python `open()` writes to system paths (`/a0/python/`, `/a0/usr/agents/`) → Tier 4. Gap B: quoted-string context detection prevents pattern matches inside string literals from triggering command gates.

### 2026-03-07 — Action Boundary (S2/S3 Classification)

Four-tier pre-execution gate at `tool_execute_before`: autonomous (Tier 1), log-and-proceed (Tier 2), notify-and-proceed (Tier 3), require-authorization (Tier 4). `_action_gate_active` flag coordinates with Supervisor to suppress false stall warnings during authorization waits. Motivated by the MJ Rathbun incident (first documented case of AI-initiated public defamation).

### 2026-03-05 — Ontology Layer

Entity resolution engine for investigation/OSINT. Five-stage resolution pipeline (exact → normalized → alias → fuzzy → model inference). JSONL graph at `/a0/usr/ontology/relationships.jsonl`. Source connectors for structured and unstructured data. Five tools: `source_ingest`, `entity_resolve`, `relationship_query`, `investigation_report`, `ontology_search`.

### 2026-03-03 — Supervisor Loop

Tiered anomaly detection: Tier 1 (warn), Tier 2 (context surgery), Tier 3 (circuit breaker). Domain-aware thresholds from BST classification. Cascade detection. Context exhaustion detection (90% fill). CUSUM sub-threshold canary. Error diversity gate suppresses false loop detection when agent is handling varied errors. Informed by the Adaptive Supervisor design sequence (Phases 1-4).

### 2026-03-01 — Memory Classification System

Selective memorizer (`_52`) extracts high-signal content, writes to FAISS with pre-classified 5-axis metadata. Memory classifier (`_55`) tags unclassified entries, resolves conflicts, source-file guard prevents chunking artifacts from cascading false deprecation. Memory maintenance (`_57`) handles lifecycle. First act: the system noted its own prior absence.

### 2026-02-28 — Error Comprehension

Structured error classifier at `tool_execute_after`. Parses raw output into diagnosis + suggested actions + anti-actions. Anti-actions prevent loops at the source. Wired into Supervisor — diagnosis injected into intervention messages. `PRIORITY_ERROR_CLASSES` for terminal early-exit / heredoc-never-executed silent failure.

### 2026-02-26 — JSON Plain-Text Fallback

`json_parse_dirty()` wraps plain text as `{"tool_name": "response", "tool_args": {"text": text}}` instead of returning `None`. Fixes the reasoning-distilled model misformat loop where a plain-text response caused repeated JSON parse failures.

### 2026-02-25 — Graph Workflow Engine (HTN)

Replaces linear task plans with directed graph execution. Nodes define tasks, edges define transitions with success/failure conditions. Branching, failure recovery paths, retry loops, stall detection. Based on Hierarchical Task Network methodology. Replaces the earlier linear Organization Kernel planner.

### 2026-02-24 — Organization Kernel (Phases 1–3)

14 organizational roles with domain specializations. Dispatcher activates role based on BST classification. PACE communication protocols. SALUTE status reports. Graph workflow engine (Phase 3) replaces linear plans.

### 2026-02-22 — Working Memory Buffer

Entity and context state across conversation turns. Extracts key references (file paths, variable names, error messages, decisions). Re-injects as structured context. API signature extraction from AI code blocks prevents parameter confabulation.

### 2026-02-20 — Tool Fallback Chain

Pattern-matched error recovery at `tool_execute_after`. Seven error categories (syntax, permissions, not found, timeout, import, connection, memory). SUCCESS_INDICATORS decay failure history on successful operations — prevents overreaction to clean results. Solved the ST-001 finding: 17 false positives per session reduced to 1.

### 2026-02-18 — Belief State Tracker (Layer 1)

Dual-classifier system: regex domain classification + trigger-based slot resolution. 14 domains. Compound classification from the start. Slot taxonomy v1.2.0 with full lineage.

### 2026-02-17 — Project genesis

First session. Agent Zero running Qwen2.5-14B on RTX 3090. Stock behavior confirmed: tool calls not visible to model, loops on completed work, no fallback recovery. Architecture decisions recorded in `state/decision_log.md`.

---

*See `state/decision_log.md` for individual design decisions and the rationale behind each one.*
*See `state/STATE.md` for current operational snapshot.*
*See `essays/` for the philosophical substrate.*
