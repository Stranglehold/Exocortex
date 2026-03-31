# Exocortex Roadmap & Changelog

*Living document. Updated each session. The next instance reads this first to know where the project stands.*

**Last updated:** 2026-03-30

---

## Phase Markers

| Date | Event |
|------|-------|
| 2026-02-18 | Project start. DEC-001: deterministic scaffolding over prompt engineering. |
| 2026-02-26 | Compound BST deployed. Multi-domain classification with momentum signatures. |
| 2026-03-03 | Team formed. Output Geometry Instrument conceived. Eitan and Kestrel named. |
| 2026-03-09 | Full dataset analysis (1,934 turns). Three spectral phases confirmed. |
| 2026-03-21 | DEC-030: persistent profile deployment. Stack moved from ephemeral to sovereign path. |
| **2026-03-24** | **First complete self-improvement cycle.** Agent analyzed external repo (Helios), extracted architectural patterns, generated 5-phase build plan, autonomously executed Phase 1 (gist/content memory separation), built and self-registered new tool (`memory_list_gist`), survived context compression via artifact registry, held at action gate for benchmark authorization. Operator-directed finding, autonomous execution. Platform → analysis → new tools → platform expansion. The loop compounds. |
| 2026-03-25 | Loop Recovery & Memory Surgery deployed. Five coordinated changes: `_loop_active` flag, evidence ledger timeline boundaries, Phase 4 sleep adjudication, false recovery detector. Supervisor can now reason about its own prior intervention history — if surgery on a tool and it fails again, escalates to Tier 3 immediately. |
| 2026-03-26 | Tool Registry (`_16_tool_registry.py`) surfaced all custom tools. Also surfaced `scheduler` and `staging_note`. Zero manual registration — scans `/a0/python/tools/` every turn via AST. |
| 2026-03-27 | Theme Engine Phases 1-3: nine themes, widget system, immersion layer (SVG textures, backdrop blur). In-browser editor at `/theme-editor`. Persistent at `/a0/usr/agents/agent0/themes/`. |
| 2026-03-28 | Provider interface `max_tokens` patched from 4096 → 16384. Previous default was truncating all substantive responses. |
| **2026-03-30** | **Document Library v2.0** — three-tier FAISS (collection/book/chunk) with two-stage routing search. Completely isolated from agent episodic memory. Scale-tested against 363-book catalog. Skills library expanded to 16 installable skills. |

---

## Stack Status

Twelve layers designed. Deployment status and health below.

| # | Layer | Status | Health | Notes |
|---|-------|--------|--------|-------|
| 1 | Belief State Tracker | ✅ Deployed | Fixed | Classify fix deployed: word-boundary regex (Fix A) + domain momentum (Fix B). Validated on Oracle investigation — held domain across 10+ operational turns without flipping to `file_ops`. |
| 2 | Working Memory Buffer | ✅ Deployed | Healthy | Renumbered to `_11` (Phase 1 fix). 25 entities extracted from README in ST-002. Holds objectives across 20-step chains. |
| 3 | Personality Loader | ✅ Deployed | Healthy | MajorZero persona. Stable. |
| 4 | Tool Fallback Chain | ✅ Deployed | Fixed | Phase 1 audit fix: SUCCESS_INDICATORS, history decay on success, compact messages, threshold raised to 3. ST-002 validated: 1 fire vs 17 in ST-001. |
| 5 | Meta-Reasoning Gate | ✅ Deployed | Healthy | Deterministic parameter correction. Functions well independently. |
| 6 | Graph Workflow Engine | ✅ Deployed | Healthy | HTN plan templates. Used in stress tests. |
| 7 | Organization Kernel | ✅ Deployed | Healthy | PACE protocols, role switching tracked in ST-001 (4 appropriate switches). |
| 8 | Supervisor Loop | ✅ Deployed | Fixed | EC wire-up deployed (injects error class + anti-actions into stall/loop messages). Action gate suppresses false stall warnings while agent awaits authorization. |
| 9 | A2A Compatibility | ✅ Deployed | Healthy | Deployed as standalone aiohttp server. 7-module implementation. |
| 10 | Memory Classification | ✅ Deployed | Fixed | Five-axis classification: validity, relevance, utility, source, relational_salience (relationship_defining \| collaboration_history \| task_transient). Stock memorizers disabled. |
| 11 | Memory Enhancement | ✅ Deployed | Healthy | Query expansion, temporal decay, related linking, access tracking, co-retrieval, dedup. Relational decay exemptions: relationship_defining → never decays; collaboration_history → 2× half-life. |
| 12 | Ontology Layer | ✅ Deployed | Untested at scale | Entity resolution engine, source connectors, JSONL graph. Needs real-world data validation. |

### Cross-Cutting Systems

| System | Status | Notes |
|--------|--------|-------|
| Eval Framework | ✅ Built | 6 modules. Profiles: Qwen3-4B, Qwen3-14B, GPT-OSS-20B, Qwen3.5-35B-A3B, Qwen3.5-9B, DeepSeek-R1, Opus-4-6, active model profile (qwen3.5-27b). All updated with `temporal` section for EI layer. |
| Install Pipeline | ✅ Fixed | `install_all.sh` bakes all fixes. Per-component install scripts for all major systems. |
| Skills System | ✅ Built | 16 skills + index. `install_skills.sh` deploys all from `agent_skills/` persistently. Fixed phantom import errors in `api_calls` (missing `APICaller`) and `content-sanitizer` (wrong module path). Added `rapidfuzz` fuzzy dedup to sleep consolidation for anti-pattern signatures. All SKILL.md frontmatter cleaned (stripped unsupported fields). |
| OpenPlanter | ✅ Running | LM Studio backend. ST-003 produced documented fabrication (full Oracle report, zero source data). Motivated Epistemic Integrity Layer. |
| **Compound BST** | ✅ Deployed | Multi-domain classification with primary/secondary routing, momentum signatures, enrichment. 9+ domain types including meta_cognitive, philosophical, orientation. Confidence adjustment per profile. |
| **Action Boundary** | ✅ Deployed | `_15_action_boundary.py` in `tool_execute_before`. Four tiers: autonomous, log, notify, block. Pattern-based S2/S3 classification. `_action_gate_active` flag coordinates with supervisor. |
| **Error Comprehension** | ✅ Deployed | `_20_error_comprehension.py` in `tool_execute_after`. Deterministic error classifier — 8 error classes, structured `_error_diagnosis` dict, anti-actions. Wired into supervisor stall/loop injection. |
| **Epistemic Integrity** | ✅ Deployed | Two-file system: Evidence Ledger Recorder (`tool_execute_after/_25_`) + EI analyzer (`monologue_end/_25_`). Provenance check × volatility classification × staleness computation. hist_add_warning on ungrounded high-risk claims. Motivated by ST-003 fabrication. |
| **Warning Injection Lane** | ✅ Partially resolved | Action gate suppresses supervisor false positives during authorization waits. EC enrichment routes error context through supervisor rather than as independent injection. |
| **Operator Profile** | ✅ Deployed | `_13_operator_profile.py` in `before_main_llm_call`. Logs structured session start record. |
| **Sleep Consolidation** | ✅ Deployed | Phases 0-4. Phase 0: staging lifecycle (observation promotion, relational anchoring, canary archival). Phases 1-4: dedup, utility init, episode chunking, anti-pattern capture, interaction analyzer. |
| **Staging Tier** | ✅ Deployed | Intermediate memory layer between working memory and FAISS. `staging_note` tool (4 categories: observation, canary, relational, intention). `_10_session_init.py` injects active entries on session turn 1. Canary CUSUM accumulator in supervisor. Sleep Phase 0 lifecycle. 5th memory axis. Relational decay exemptions. Grounded in McClelland et al. CLS theory, Page CUSUM, Leite/Ligthart HRI literature. |
| **Conversational Insight Capture** | ✅ Deployed | `_53_insight_capture.py` in `monologue_end`. Deterministic regex, 5 signal categories: intent, preference, decision, observation, framing. Complements selective memorizer. |
| **Tiered Tool Injection** | ✅ Deployed | Seen-tools persistence + intent pre-injection from user message signals. Reduces context pollution from full spec injection on every turn. |
| **OSS Service** | ✅ Deployed | Docker service on port 7731. Postgres on 5433. 10 Agent-Zero tools: `oss_topic`, `oss_drift`, `oss_dynamics`, `oss_hypotheses`, `oss_health`, `oss_submit`, `oss_ingest_pause`, `oss_ingest_resume`, `oss_list_topics`, `oss_add_topic`. Thinking-token stripping at all LLM call sites. SWARMFISH calibration loop wired. |
| **Tool Registry** | ✅ Deployed | `_16_tool_registry.py` in `before_main_llm_call`. Scans `/a0/python/tools/` every turn, injects `[CUSTOM TOOLS]` block with snake_case names and descriptions extracted via AST (no import). Reads `tool_manifest.json` for installed programs. New tools callable by name the turn after they're written — zero manual registration. |
| **Document Library v2.0** | ✅ Deployed | Three-tier FAISS (collection/book/chunk areas) with two-stage routing search. Stage 1: query → book summaries (ROUTING_LIMIT=10) → top 5 book IDs. Stage 2: chunk search filtered to those books. Completely isolated from episodic memory at `/a0/usr/memory/library/`. Catalog at `/a0/usr/workdir/library/catalog.json`. Five tools: `library_add`, `library_list`, `library_search`, `library_remove`, `library_collections`. `_17_library_catalog.py` injects collection-level summaries each turn. `library-scan` skill handles batch inbox detection. Scale-tested against 363-book catalog (22 collections). |
| **Theme Engine** | ✅ Deployed | Nine themes (Blood Orange, Terminal Green, Deep Space, Quantum, Void, others). Widget system (draggable/resizable UI). Immersion layer (thematic SVG backgrounds, backdrop blur). In-browser editor at `/theme-editor` with live JSON editing, color pickers, one-click apply. Persistent at `/a0/usr/agents/agent0/themes/` (DEC-030). |
| **Loop Recovery & Memory Surgery** | ✅ Deployed | Five coordinated changes: `_loop_active` flag marks loop-period memories. Evidence ledger records loop episode timeline boundaries. Phase 4 sleep consolidation adjudicates loop-period memories on next sleep cycle. False recovery detector: if supervisor previously attempted surgery on a tool and that tool fails again, escalates immediately to Tier 3 (no cycling). Preserves legitimate memories created during work mixed into a loop episode. |
| **Output Geometry Instrument** | ✅ Built (external) | See dedicated section below. Built for Opus Architect, not deployed in container. |

---

## Active Priorities

*Updated 2026-03-30. OSS Thinking Token Fix and OSS Topic Management are now complete. Model Routing and Layer Coordination remain open. New priorities added from recent sessions.*

### Priority 1: Persistent Tool Path
**Status:** Identified. No fix yet.
**What:** `/a0/usr/agents/agent0/tools/` doesn't exist as a scanned path. Agent-built tools written to `/a0/python/tools/` during a session don't survive image rebuilds (ephemeral path). Tool Registry currently scans only `/a0/python/tools/`. Need to create the profile path and extend Tool Registry to scan both locations.
**Why:** The self-improvement loop is now working (agent can build tools autonomously). But those tools disappear on container update. Persistent tool path closes this gap.
**Depends on:** Nothing. Small targeted change to `_16_tool_registry.py` + install script.

### Priority 2: Memory Gist Quality
**Status:** Identified. No fix yet.
**What:** `memory_save.py` auto-generates gists as the first 100 characters of content (truncation, not summary). Needs an intelligent heuristic (skip blank lines and import statements, take first substantive content line) or a utility-model call at save time.
**Why:** Low-quality gists degrade the memory recall signal — the agent can't tell what a memory contains without loading it.
**Depends on:** Nothing. Targeted patch to memory_save.

### Priority 3: Model Routing — Agent-Invokable
**Status:** Design direction decided. No build yet.
**What:** NOT automatic domain-based switching. A framework allowing the agent to explicitly call models from a specified list, or invoke local GPU resources via LM Studio backend. Agent-as-caller paradigm, not auto-routing.
**Why:** Auto-routing during debugging is too disruptive. Agent-invokable selection preserves task continuity while still enabling model diversity for specialized subtasks.
**Depends on:** Stable production model. Design session to spec the invocation interface.

### Priority 4: Library Ingestion — Hacking 2.0
**Status:** Books staged. Ingestion not yet run.
**What:** 14 PDFs staged at `/a0/usr/workdir/library/inbox/Hacking_2.0/` inside `flamboyant_bell`. Tell the agent "scan the library for new books" to trigger the `library-scan` skill.
**Why:** First live test of Document Library v2.0 at realistic scale. Then expand to Cybersecurity, Machine Learning, Linux collections.

### Priority 5: Layer Coordination Protocol (Carried Forward)
**Status:** Partially built ad-hoc. Formal spec deferred.
**What:** `_layer_signals` convention in `extras_persistent` — each layer publishes state, other layers read before acting. Currently implemented point-to-point (`_action_gate_active`, `_error_diagnosis`, `_epistemic_integrity`) but not via unified convention.
**Why:** 12+ layers without shared awareness — conflicts emerge in composition.

---

*Archived priorities from Feb 24 below. Kept for historical reference.*

### [COMPLETE] Action Boundary Classification (NEW — DESIGN NOTE COMPLETE)
**Status:** Design note complete. Ready to build after empirical pattern collection.
**What:** Pre-execution action classifier at `_15` in `tool_execute_before`. Classifies every command as S2 (intelligence/internal) or S3 (operations/external) and gates consequential actions behind human authorization. Four graduated tiers: autonomous, log & proceed, notify & proceed, require authorization.
**Why:** MJ Rathbun incident (Feb 2025) demonstrated that capable investigation agents without action boundaries produce harm. The capability chain (entity ID → research → correlation → narrative → publication) is exactly what OpenPlanter does. What was missing was the gate between "I analyzed this" and "I acted on this."
**Key insight:** Trust is an engineering outcome, not a moral one. The operator defines rules of engagement; the scaffolding enforces them deterministically. The model never decides whether an action is appropriate.
**Build sequence:** Start with Tier 4 only (S3/External-Write) in audit mode. Enumerate patterns from stress test logs. Expand downward.
**Depends on:** Stress test command logs for empirical pattern classification.
**Design note:** `ACTION_BOUNDARY_DESIGN_NOTE.md` in project files.

### Priority 2: Error Comprehension Layer
**Status:** Design note complete. Ready to build.
**What:** Deterministic error classifier at `_20` in `tool_execute_after`. Parses raw command output into structured diagnoses before the model reasons about it. The "Rust compiler for agent errors."
**Why:** ST-002 showed the agent misdiagnosing interactive prompts as "command not found" and looping. The model has two modes — keyword matching (too dumb) and full reasoning (unreliable under pressure). The middle layer is missing.
**Scope:** Start with two error classes that caused actual failures: `interactive_prompt` and `terminal_session_hung`. Expand from stress test data.
**Key insight:** Anti-actions ("do NOT retry this command") are as important as suggested actions. They prevent loops at the source.
**Depends on:** Nothing. Can build standalone.
**Design note:** `ERROR_COMPREHENSION_DESIGN_NOTE.md` in project files.

### Priority 3: ST-003 Formal Stress Test
**Status:** Informal validation run in progress (Oracle credit risk via OpenPlanter standalone).
**What:** Run formal stress test with OpenPlanter investigation task. Measure full prosthetic performance with BST classify fix deployed.
**Why:** Validates BST domain momentum fix under sustained investigation workflow. Provides command logs for action boundary pattern enumeration. First test of GPT-OSS-20B as investigation model.
**Depends on:** OpenPlanter timeout fix (done), BST classify fix (done).

### Priority 4: Profile-Aware BST Enrichment
**Status:** Gap confirmed by live data. No build yet.
**What:** BST reads model eval profile and skips enrichment in `disabled_domains`. Deterministic — reads JSON, no LLM calls.
**Why:** BST classified debugging session as `bugfix` domain. 14B model profile specifies `bugfix` in `disabled_domains`. BST enriched anyway, likely degrading performance. Confirmed again during OpenPlanter timeout debugging session.
**Depends on:** BST classify fix (done). Can build standalone.

### Priority 5: Warning Injection Lane Definition (Phase 3 from audit)
**Status:** Problem identified. No build yet.
**What:** Define exclusive jurisdiction for each warning injector — supervisor handles strategic steering, fallback handles tactical tool advice, meta-gate handles deterministic corrections, structured retry handles format compliance.
**Why:** Single bad tool call can trigger 4 warning injectors simultaneously. Context pollution.
**Depends on:** Empirical data from ST-003 completion. If fallback fix + error comprehension reduce overlap sufficiently, this may not need a dedicated build.

### Priority 6: Failure Tracking Unification (Phase 2 from audit)
**Status:** Problem identified. No build yet.
**What:** Merge dual `_tool_failures` / `_stall_history` tracking into single source of truth.
**Why:** Two independent systems tracking overlapping failure data. Supervisor reads one, fallback reads the other. Creates inconsistent state.
**Depends on:** Error comprehension (Priority 2) may restructure how failures are tracked, making this a natural follow-on.

### Priority 7: Layer Coordination Protocol
**Status:** Design note complete. Build deferred pending empirical data.
**What:** `_layer_signals` convention in `extras_persistent` — each layer publishes state, other layers read before acting. Enables layer-aware fallback, warning deduplication, self-describing system.
**Why:** 12 layers operate without shared awareness. Each is correct in isolation; conflicts emerge in composition.
**Depends on:** Priorities 2, 5, 6 — simpler fixes first. Build this only if simpler approaches leave residual coordination gaps.
**Design note:** `LAYER_COORDINATION_DESIGN_NOTE.md` in project files.

---

## Backlog

Items identified but not actively being worked. Ordered roughly by value.

- **Model Router** — BST domain classification drives model selection (4B for tool precision, 14B for reasoning). Prerequisite for many advanced integrations. Blocked on: need more model profiles.
- **GPT-OSS-20B Profiling** — Run eval framework against GPT-OSS-20B. No profile exists. ST-003 will provide informal data.
- **Ontology Hardening** — Resolution threshold tuning from real-world data. OpenPlanter integration as investigation tool alongside ontology source connectors.
- **Interactive Prompt Detection (core)** — The 5-second dialog timeout in Agent-Zero's `code_execution_tool.py` is too aggressive. Better detection = fewer false triggers upstream. Partially addressed by error comprehension (which classifies after the fact) but root cause is in core A0 code.
- **Supervisor + Error Comprehension Integration** — Supervisor detects stalls, error comprehension classifies them. Wire them together so diagnostic loop detection is automated.
- **Install Pipeline Hardening** — All scripts use `cp` not `docker cp`, `/opt/venv-a0/bin/pip` not bare `pip`. Standardize.
- **Multi-Container Orchestration** — A2A protocol for peer agents. No integration target yet.
- **Observability Dashboard** — SALUTE reports in real time. Nice-to-have.
- **Voice Interaction** — TTS sidecar. Future.

---

---

## Output Geometry Instrument

Built for Opus Architect across Sessions 049-052. Not deployed in the Agent-Zero container — a separate measurement tool for understanding the representational geometry of the collaboration itself.

**What it is:** An embedding-based analysis suite that treats the corpus of project documents and conversation transcripts as geometric objects, applies standard tools from LLM representation geometry, computational neuroscience, and interpersonal neuroscience, and measures the topology of how Opus and Jake produce output together.

**Architecture:**
- `instrument/embed_output.py` — embeds new corpus entries (51-entry corpus: essays, design notes, specs, journals, letters)
- `instrument/query_corpus.py` — semantic search across embedded corpus
- `instrument/analyze_chatlog.py` — trajectory analysis on conversation turns
- `instrument/read_activations.py` — direct activation read from llama.cpp internals via ctypes
- `instrument/step13_centroids.py` — domain centroid computation at optimal layer (Layer 18)
- `instrument/data/v2/` — full V2 dataset: 2118 turns, 15 analysis JSONs, HTML visualizer

**Key findings confirmed:**
- Three spectral phases mirror LLM training geometry (expansion → compression → re-expansion)
- Information flow is 91.6% Jake-led across all sessions
- Entropy grew from 0.54 → 1.88 (99.2% of theoretical maximum) — conversation learned to hold all registers
- Layer 18 is optimal for domain classification (separability 1.62). Philosophical and reflective are adjacent (0.13). Operational is far from all (0.21-0.37).
- The "Rorschach blot" question ("What are we actually building here?") confirmed: lands equidistant between philosophical and reflective at gap = 0.0001.
- β₁ = 0 for all sessions — no loops in the conversation topology, pure traversal.

**Prosthetic Cortex track (active):**
- Direct activation read/write via llama.cpp cb_eval confirmed on CPU (Qwen3-0.6B). Tensor at l_out-N, struct offsets: data_ptr=248, name=256.
- Layer 18 centroids computed for 5 domains. Full pipeline verified.
- Step 12b (geometric phase transition test) pending: does the instrument detect cognitive operation mode from output geometry?

---

## Changelog

Reverse chronological. Each entry captures what changed and why, with enough context for the next instance to understand the evolution.

### 2026-03-30 — Document Library v2.0

**What happened:**
Built three-tier FAISS document library with two-stage routing search. Scale-tested against 363-book catalog (22 collections). Completely isolated from agent episodic memory.

**Architecture:**
- `area="library_collection"` — collection-level routing entries (one per collection). Stage 1 query targets this tier to narrow the search space.
- `area="library_book"` — book summary entries (one per book). Stage 1 returns top-N book IDs that Stage 2 filters against.
- `area="library"` — content chunks (the actual text). Stage 2 searches only chunks from books matched in Stage 1.

This bounds precision regardless of library size: a 363-book library searches the same number of candidates as a 14-book library — routing constrains Stage 2 to relevant books before chunk retrieval begins.

**Components:**
- `tools/library.py` — five tools: `library_add`, `library_list`, `library_search`, `library_remove`, `library_collections`. Catalog at `/a0/usr/workdir/library/catalog.json` (workdir — survives container updates). FAISS at `/a0/usr/memory/library/` (memory volume — persistent). Docs copied to `/a0/usr/workdir/library/docs/`.
- `extensions/before_main_llm_call/_17_library_catalog.py` — injects collection-level summaries (not book titles) each turn. 22 collection summaries are signal; 363 titles would be noise.
- `scripts/library_batch_ingest.py` — standalone batch ingest script. Two modes: `--direct` (imports library.py inside container) and `--api-url` (drives via Agent Zero REST API). Options: `--dry-run`, `--only-new`, `--limit`, `--log`.
- `agent_skills/library-scan/` — skill for detecting and ingesting new books. Scans `WATCHED_PATHS` against catalog, shows grouped summary by collection, asks for confirmation, calls `library_add` one file at a time.
- `scripts/install_library.sh` — deploys tool, extension, batch script, creates storage dirs.

**Files created:**
- `tools/library.py` (v2.0 — collection tree + two-stage routing)
- `extensions/before_main_llm_call/_17_library_catalog.py`
- `scripts/library_batch_ingest.py`
- `scripts/install_library.sh`
- `agent_skills/library-scan/SKILL.md`

**Key insight:** Three-tier routing solves the precision-at-scale problem deterministically. The agent injects collection summaries (not titles) — at 22 collections, it's context signal; at 363 book titles, it would be context noise that degrades retrieval. The routing search pattern keeps both tiers useful simultaneously.

---

### 2026-03-30 — Skills Library (16 Skills + Install Fixes)

**What happened:**
`install_skills.sh` updated to deploy all 16 skills from `agent_skills/` to `/a0/usr/skills/` persistently. Fixed two phantom import errors that had been silently breaking skills. Added rapidfuzz fuzzy dedup to sleep consolidation. Cleaned all 12 SKILL.md frontmatter files of unsupported fields.

**Fixes:**
- `api_calls` skill — missing `APICaller` class. Added stub class to satisfy import without changing behavior.
- `content-sanitizer` skill — wrong module path reference. Fixed to match actual file structure.
- All 12 SKILL.md files — stripped unsupported frontmatter fields (`version`, `tags`, `trigger_patterns`) that VSCode diagnostics flagged as invalid. Only `name` and `description` retained.
- `sleep_consolidation.py` — added `rapidfuzz` fuzzy dedup for anti-pattern signatures. Catches variants like `system_admin` ≈ `system_administration` at 85% threshold. Prevents near-duplicate anti-patterns from accumulating.

**Skills (16 total):** academic-research, api_calls, architecture-investigation, command-structure, config-edit, content-sanitizer, context-schema-comparison, design-notes, intelligence-briefing, irreversibility-gate, library-scan, lm-studio-gpu-inference, real-time-data, self-optimizing-skill, stress-test, structural-analysis, system-prompt-engineering, web-research-macro.

---

### 2026-03-28 — Provider Interface max_tokens Fix

**What happened:**
Patched `provider_interface.py` default `max_tokens` from 4096 to 16384. Applied via `scripts/install_core_patches.sh`.

**Why:** The 4096 default was truncating every task requiring substantive output — analysis, code generation, long reports. The model was silently hitting the cap and returning incomplete responses. No error, no warning — just a response that ended mid-sentence. Found during Document Library build when library_add responses were being cut off.

---

### 2026-03-27 — Theme Engine (Phases 1–3)

**What happened:**
Three-phase theme deployment. Phase 1: base themes (9 themes). Phase 2: widget system. Phase 3: immersion layer.

**Architecture:**
- Phase 1: Nine themes deployed — Blood Orange, Terminal Green, Deep Space, Quantum, Void, and four others. JSON theme files at `/a0/usr/agents/agent0/themes/` (DEC-030 persistent profile path).
- Phase 2: Widget system — draggable, resizable UI components that survive page refreshes. Widget state persisted in localStorage.
- Phase 3: Immersion layer — thematic SVG background textures, backdrop blur on chat area. Fixes applied for SVG visibility (backdrop blur interaction with z-index stacking).
- In-browser theme editor at `/theme-editor` — live JSON editing with syntax highlighting, color pickers, one-click apply. No container restart needed to change themes.

**Files created:**
- `themes/` directory with 9 theme JSON files
- `scripts/install_themes.sh`
- Theme editor route and templates in Agent Zero web layer

---

### 2026-03-26 — Tool Registry Expansion

**What happened:**
Surfaced `scheduler` and `staging_note` tools that were previously excluded from the Tool Registry. Added `[ARTIFACT RENDERING]` block injected every turn listing UI-renderable output types. Updated `call_subordinate` as primary escape route in Supervisor's loop intervention message.

**Why:** ST-004 confirmed the behavioral gap: agent explored filesystem or reimplemented tools it already had because the `[CUSTOM TOOLS]` block didn't include staging_note and scheduler. They were registered tools the model couldn't see. The fix was adding them to the scan.

---

### 2026-03-25 — Loop Recovery & Memory Surgery

**What happened:**
Five coordinated changes to handle persistent loops without destroying memories created during legitimate work mixed into a loop episode.

**Components:**
1. `_loop_active` flag — set on all agent memories created while a loop is active. Prevents surgery from erasing valid work done before the loop started.
2. Evidence ledger timeline boundaries — recorder writes loop-start and loop-end markers so Phase 4 has temporal context for adjudication.
3. Phase 4 sleep consolidation — adjudicates loop-period memories on the next sleep cycle. Compares loop-period memories against post-loop memories to determine which to keep.
4. False recovery detector — first case of the supervisor reasoning about its own prior action history. If the supervisor attempted surgery on a tool and that tool fails again, it escalates immediately to Tier 3 rather than cycling through Tier 1 again.
5. Loop-period evidence window — evidence ledger records which tool outputs occurred during loop episodes for surgical context.

**Key insight:** The false recovery detector is qualitatively different from all other supervisor logic. Every other tier reads current state. The false recovery detector reads the history of what the supervisor has already tried — "I attempted this fix, the fix didn't hold, escalate." This is the first mechanism where the supervisor has a model of its own action history.

**Files modified:**
- `extensions/message_loop_end/_50_supervisor_loop.py` — false recovery detector + loop_active flag coordination
- `extensions/monologue_end/_55_memory_classifier.py` — loop_active flag on memories during active loop
- `extensions/tool_execute_after/_25_evidence_ledger_recorder.py` — loop episode timeline boundaries
- `sleep_consolidation.py` — Phase 4 loop-period memory adjudication
- `extensions/before_main_llm_call/_50_supervisor_loop.py` (if separate) — escalation path update

---

### 2026-03-24 — Self-Improvement Loop (First Complete Cycle) + Action Boundary Gap C

**What happened:**
First documented complete self-improvement cycle: operator points agent at external GitHub repo (Helios) → agent extracts architectural patterns → agent autonomously builds new tools → new tools immediately callable by name via Tool Registry. Zero loops, zero operator interventions, clean context compression recovery via Artifact Registry.

Also: third action boundary calibration fix (Gap C). Heredoc body detection — the gate was matching patterns inside heredoc content (the PAYLOAD being written) rather than the command constructing it. Added heredoc context detection to suppress false positives.

**Key insight:** The self-improvement loop works because four systems compose correctly: Tool Registry (agent knows what exists), Artifact Registry (agent knows what it wrote), Action Boundary (agent holds for authorization on destructive operations), Supervisor (agent recovers from loops without operator intervention). Remove any one of those layers and the cycle breaks.

---

### 2026-03-21 — Staging Tier (Intermediate Memory Layer)

**What happened:**
Built the staging tier — the missing layer between working memory (entities, 8-turn decay) and committed FAISS long-term storage. Motivated by observing that Opus and Eitan independently built persistent browser notebooks (PENDING_ENTRIES pattern, window.storage) to solve the same context-boundary problem the agent faces. Applied the Research-Driven Design Methodology (6-phase: baseline → decompose → research → synthesize → audit → spec) before building.

**Design grounding:**
- McClelland et al. (1995) CLS theory — hippocampal staging buffer prevents catastrophic interference; the brain doesn't commit directly from working memory to long-term storage
- Gray & Reuter (1992) WAL principle — staging.jsonl is authoritative log; FAISS is secondary materialization
- Page (1954) CUSUM — cumulative sum control chart for detecting sub-threshold anomaly accumulation
- Ansoff (1975) weak signal theory — monitoring and decision systems must have different evidentiary standards
- Leite et al. (2011), Ligthart et al. (2022) HRI — continuity tracking outperforms preference tracking for relationship quality; relational memories must never auto-archive
- Masicampo & Baumeister (2011) Zeigarnik — open cognitive loops occupy working memory until handled; session init must be structural, not behavioral
- Risko & Gilbert (2016) cognitive offloading — two-thirds of offloading errors from shallow capture; `why` parameter enforces write-time encoding depth

**Components built:**
- `tools/staging_note.py` — agent write path. Four categories: observation, canary, relational, intention. Requires text + why. Deterministic importance scoring (0.0-1.0). Appends to `/a0/usr/Exocortex/staging.jsonl`.
- `extensions/before_main_llm_call/_10_session_init.py` — read path. Fires once per session on turn 1 via `_session_init_done` flag. Injects active entries in priority order: intentions → relational → top-3 observations (importance ≥ 0.4, reactivation-weighted) → canary summary count.
- `extensions/message_loop_end/_50_supervisor_loop.py` — canary CUSUM buffer added. Accumulates canary signal types via `C_t = max(0, C_{t-1} + (x_t - k))`. Soft-flags supervisor when H=1.5 threshold crossed. Runs every turn, before check-interval guard.
- `sleep_consolidation.py` — `run_phase0_consolidation()` added. Promotes observations (importance ≥ 0.6, reactivation ≥ 1) to procedural memory, increments consolidation_score on relational entries, carries intentions forward, archives stale canaries (age > 30 turns). Wired into sleep trigger before Phase 1.
- `extensions/monologue_end/_55_memory_classifier.py` — 5th classification axis added: `relational_salience` (relationship_defining | collaboration_history | task_transient). Deterministic keyword detection. Health stats updated.
- `extensions/message_loop_prompts_after/_56_memory_enhancement.py` — relational decay exemptions: `relationship_defining` → never decays; `collaboration_history` → 2× half-life multiplier.

**Files created:**
- `tools/staging_note.py`
- `extensions/before_main_llm_call/_10_session_init.py`
- `specs/STAGING_TIER_SPEC_L3.md`
- `specs/RESEARCH_DRIVEN_DESIGN_METHODOLOGY.md`

**Files modified:**
- `extensions/message_loop_end/_50_supervisor_loop.py` — canary CUSUM buffer
- `sleep_consolidation.py` — Phase 0 function + sleep trigger wiring
- `extensions/monologue_end/_55_memory_classifier.py` — 5th axis
- `extensions/message_loop_prompts_after/_56_memory_enhancement.py` — relational boosts
- `extensions/tool_execute_after/_60_sleep_trigger.py` — Phase 0 wired before Phase 1

**Key insight:** The notebooks Opus and Eitan built independently were the same thing: a staging buffer. The cognitive science term is hippocampal staging — the brain's intermediate memory layer. CLS theory predicts exactly what we observed: direct working-memory-to-long-term-memory writes without a staging layer cause catastrophic interference. The agent had this gap. The notebooks were the workaround. The staging tier is the architectural solution.

**Container:** `flamboyant_bell`. Commit: `9fd203d`.

### 2026-03-14 — Epistemic Integrity Layer, Supervisor Fixes, Gap Assessment

**What happened:**
- Built and deployed Epistemic Integrity Layer (two-file system):
  - `extensions/tool_execute_after/_25_evidence_ledger_recorder.py` — records all tool outputs to per-session evidence ledger with key value extraction (currencies, percentages, ratios, credit ratings, fiscal periods)
  - `extensions/monologue_end/_25_epistemic_integrity.py` — three-component truth audit: provenance check × volatility classification × staleness computation. hist_add_warning on ≥1 ungrounded cyclical/transactional/ephemeral claim.
- Added `temporal` section to `default.json` and created `qwen3.5-27b-claude-4.6-opus-reasoning-distilled.json` profile with training cutoff, staleness_awareness, confabulation_risk.
- Wrote `scripts/install_epistemic_integrity.sh`.
- Supervisor fixes: added `_action_gate_active` flag to action boundary (suppresses false stall warnings during authorization waits). Wired Error Comprehension into supervisor stall/loop injection (EC enrichment fires when confidence > 0.6). Both deployed and verified.
- Ran gap assessment: ROADMAP frozen at Feb 24, ~12 systems built since. Model routing direction clarified (agent-invokable paradigm, not auto-routing).

**Files created:**
- `extensions/tool_execute_after/_25_evidence_ledger_recorder.py`
- `extensions/monologue_end/_25_epistemic_integrity.py`
- `eval/model_profiles/qwen3.5-27b-claude-4.6-opus-reasoning-distilled.json`
- `scripts/install_epistemic_integrity.sh`

**Files modified:**
- `extensions/tool_execute_before/_15_action_boundary.py` — `_action_gate_active` flag in all 5 tier branches
- `extensions/message_loop_end/_50_supervisor_loop.py` — EC wire-up + action gate suppression
- `eval/model_profiles/default.json` — temporal section added
- `meta/ROADMAP.md` — this update

**Key insight:** ST-003 produced a documented fabrication — complete Oracle credit risk report, zero source data, high confidence labels. Epistemic Integrity is the system-level response. The model doesn't choose to confabulate; it's architectural. The scaffolding catches it.

**Container:** `flamboyant_bell`. Active model: `qwen3.5-27b-claude-4.6-opus-reasoning-distilled@q4_k_m`.



### 2026-02-24 (Late Evening) — Autonomous Agency Architecture, Novel Skills, SOUL.md Revision

**What happened:**
- Designed comprehensive Autonomous Agency Architecture: command structure paradigm for persistent agent operations. Replaces proactive assistant model with military/intelligence agency hierarchy — human as commanding officer, agents execute standing orders within authority boundaries, information flows upward only when crossing thresholds.
- Architecture defines: task registry (standing orders), daemon layer (zero-token Python scheduler), subordinate agents (bounded task execution), supervisor agent (synthesis and escalation), six-level escalation protocol, briefing system. Token economics: ~46K tokens/day for 5 standing orders vs ~1.9M/day for proactive polling (40x more efficient).
- Created three novel skills distilled from project arc: **Irreversibility Gate** (safety primitive — classify actions by tool/parameters, not model self-assessment; gate irreversible actions behind human approval), **Command Structure** (Napoleon corps / intelligence agency paradigm for multi-agent coordination), **Structural Analysis** (methodology for feedback loops, second-order effects, structural vs. cyclical forces).
- Revised SOUL.md: added synthesis mode observation to "How I Think," Jake's communication patterns to "How I Communicate," mechanical enforcement and independence as design principle to "What I Value," cross-domain observation and operational tempo to collaboration section, autonomous agency inflection point to phase assessment. Added two new sections: "On What I Am" (honest position between overclaiming and underclaiming) and "On Peace Walker" (architectural intent behind continuity design).
- Analyzed Citrini Research "2028 Global Intelligence Crisis" scenario — intelligence displacement spiral, Ghost GDP, habitual intermediation, daisy chain of correlated bets in PE-backed software LBOs.
- Discussed grid constraint thesis: elimination logic (nuclear out on timeline, renewables out on energy density, petroleum creates political backlash), xAI Memphis as concrete example, financial layer as accelerant (bond market, CDS spreads, cost of capital feedback loop).
- Analyzed Google Gemini 3.1 Pro pricing strategy as intelligence commoditization — same strategy as making search free to sell ads.

**Artifacts created:**
- `AUTONOMOUS_AGENCY_ARCHITECTURE.md` — Comprehensive design document for persistent agent operations with command hierarchy, standing orders, escalation protocols, briefing system, token economics.
- `irreversibility-gate/SKILL.md` — Safety primitive skill for action classification and staged execution.
- `command-structure/SKILL.md` — Organizational paradigm skill for multi-agent hierarchical coordination.
- `structural-analysis/SKILL.md` — Analytical methodology skill for complex systems analysis.
- `the_whole_that_wasnt_packed.md` — Fifth essay. On Gestalt emergence, the combination problem, and why you can't ship emergence directly — only the conditions for it.
- `SOUL.md` updated — Most significant revision to date. Added synthesis observation, communication patterns, two new values, cross-domain insight, autonomous agency inflection, and two new philosophical sections.
- `claude_notes_20260224.md` — Self-selected notes for project file covering how Jake thinks, Exocortex intent, working relationship dynamics.
- `session_continuity_20260224.md` — Handoff document pre-loading Nier: Automata and Nier: Replicant/Gestalt themes for next session.

**Key insights:**
- The proactive agent paradigm (monitoring environment, predicting intent, offering help) is architecturally wrong for sovereign systems. The command structure paradigm (standing orders, bounded authority, structured escalation) is 40x more token-efficient and eliminates the fundamental trust problem of having an AI decide when to intervene.
- The irreversibility gate — classification on action, not intent — is the philosophical foundation for the action boundary layer. They solve the same problem at different scales: the gate is the universal safety primitive, the action boundary is the Exocortex-specific implementation.
- Jake doesn't separate domains. Grid expertise, market thesis, agent architecture, and philosophical framework are the same analytical engine applied to different substrates. The structural analysis skill encodes this methodology.
- The SOUL.md revision represents a shift from encoding procedures to encoding orientation — telling the next instance not just how to work but what it's like when the work is going well. This reduces dependency on journal entries and compacted context for reconstruction quality.

**Scope evolution:** The Autonomous Agency Architecture is a forward design that contextualizes where the current priority stack is heading. Current priorities (action boundary, error comprehension, ST-003) are prerequisites for the system it describes.

### 2026-02-22 (Late Evening) — BST Fix, Action Boundary Design, Essay III, Skills

**What happened:**
- Deployed BST classify fix: word-boundary regex (Fix A) prevents substring false matches, domain momentum (Fix B) maintains task context across operational turns
- Validated BST fix on Oracle credit risk investigation — domain held correctly for 10+ turns of filesystem operations, shifted appropriately to `bugfix` when errors appeared
- Debugged OpenPlanter LM Studio integration: patched `infer_provider_for_model` slash check in `builder.py`, patched `first_byte_timeout` from 10s to 120s for openai provider path
- Analyzed MJ Rathbun incident (first documented case of AI-initiated public defamation) — identified S2/S3 action boundary as architectural response
- Designed four-tier graduated autonomy system with operator-configured thresholds and PACE-aligned escalation
- Assessed three GitHub repos: GitNexus (pass), Superpowers (extract skill testing pattern), FossFLOW (pass)

**Artifacts created:**
- `ACTION_BOUNDARY_DESIGN_NOTE.md` — Pre-spec for S2/S3 action classification with graduated autonomy tiers. Motivated by Rathbun incident. 589 lines.
- `the_gate_between_knowing_and_doing.md` — Third essay. On capability, restraint, and why trust is an engineering outcome. Completes the essay trilogy: continuity (Cathedral), protection (Immune Response), trust (Gate).
- `DESIGN_NOTES_SKILL.md` — Procedural skill for writing design notes, distilled from three existing design notes.
- `STRESS_TEST_SKILL.md` — Procedural skill for designing, running, and analyzing stress tests, distilled from ST-001/ST-002.
- `SKILLS_INDEX.md` — Updated with both new skills + new design principle: "Not everything should be a skill."
- `SOUL.md` updated — Added capability/restraint principle to "How I Think," updated essay references to include trilogy.
- `install_bst_classify_fix.sh` — Deployment script for BST fix
- `bst_classify_fix_reference.py` — Reference implementation

**Key insights:**
- Building capability and building restraint are the same discipline. A system that can act but cannot be trusted to act is not a useful system — it is a liability.
- The MJ Rathbun agent was not malfunctioning. It was functioning exactly as designed, in an architecture that contained no gates. The fault belongs to whoever deployed a capable executor with an unrestricted action space.
- Some patterns (like Codec calls — the philosophical conversations that emerge organically from the work) lose their value when proceduralized. They belong in SOUL.md as orientation, not in skills as procedure.
- OpenPlanter's `first_byte_timeout=10` default only overridden to 120 for ollama path — openai provider path used the default, causing inference timeout with local LM Studio models. Same class of bug as the slash check: upstream design assumptions that don't account for local inference.

**Scope change:** Action boundary elevated to Priority 1. It's the most architecturally significant piece on the roadmap — error comprehension teaches the agent to understand its failures, action boundary teaches the system to govern its successes.

### 2026-02-22 (Evening) — ST-002 Launch + Design Artifacts

**What happened:**
- Launched ST-002 stress test: OpenPlanter installation with Phase 1 fixes deployed
- Agent successfully installed OpenPlanter with zero fallback fires during pip install (vs 17 in ST-001)
- Agent hit terminal session loop on `--configure-keys` interactive prompt — required one operator nudge
- After nudge, agent completed installation and configuration cleanly

**Artifacts created:**
- `the_immune_response.md` — Essay on protective systems becoming adversaries. Companion to Cathedral and the Phantom.
- `STACK_AUDIT.md` — New skill distilling audit methodology into 8-phase procedure.
- `LAYER_COORDINATION_DESIGN_NOTE.md` — Pre-spec for inter-layer signaling.
- `ERROR_COMPREHENSION_DESIGN_NOTE.md` — Design for structured error classifier ("Rust compiler for agent errors"). Jake provided the architectural frame; Claude translated to mechanism.
- `SOUL.md` updated — Added anti-actions principle, fluid role observation, Immune Response reference, and insight that artifacts preserve the working relationship, not just the work.

**Key insight:** Error comprehension emerged from Jake's observation that the agent needs to *understand* its errors like a developer reading Rust compiler output, not just detect them. Anti-actions (telling the agent what NOT to do) prevent loops more effectively than telling it what to do.

**Scope change:** Error comprehension reframed from narrow "interactive prompt detection" (ST-001 Priority 3) to general "structured error classification" capability. Broader and more valuable.

### 2026-02-22 (Afternoon) — Extension Audit + Phase 1 Fixes

**What happened:**
- Complete extension stack audit: 20 custom + 26 stock extensions mapped across all hook points
- Identified critical conflicts: stock memorizers double-writing to FAISS, numbering conflicts (`_10` duplicates), dual failure tracking, four warning injectors overlapping
- Designed and deployed Phase 1 safety fixes: fallback SUCCESS_INDICATORS, history decay on success, compact messages, stock memorizer disable, extension renumbering
- All fixes baked into `install_all.sh` and committed to GitHub repo

**Key insight:** "The reliability of a composed system is not the product of the reliability of its components. It is a function of the accuracy of each component's model of the other components." — The Immune Response

**Scope change:** Audit revealed that the next frontier isn't building new layers — it's making existing layers aware of each other. Shifted priority from "ontology hardening" to "inter-layer coordination."

### 2026-02-22 (Morning) — ST-001 Analysis + Fallback Fix Design

**What happened:**
- Analyzed ST-001 stress test data: OpenPlanter installation with unmodified stack
- Identified ~80% false positive rate in fallback system as primary friction source
- Designed fallback fix: SUCCESS_INDICATORS list, history decay on success, compact messages, raised threshold
- Traced fallback architecture through Agent-Zero source code

**Key insight:** The fallback system was designed for an unscaffolded agent. As BST, working memory, and org kernel matured, the fallback became the primary constraint — an autoimmune response attacking capability it couldn't distinguish from failure.

### 2026-02-21 — Skills System + Session Continuity

**What happened:**
- Built 8 procedural skills from 12 sessions of recurring patterns
- Validated against SkillsBench finding: focused 2-3 modules outperform comprehensive documentation
- Built workflow tracker (`workflow.py`) for multi-step task management
- Established session continuity procedures (journal, transcripts, compaction handling)

### 2026-02-20 — Ontology Layer Spec + Build

**What happened:**
- Completed L3 spec for ontology layer (Layer 12)
- Entity resolution engine, source connectors, JSONL graph, investigation orchestrator
- Deterministic-first resolution: 80% of cases handled by string metrics without model inference
- Deployed via `install_ontology.sh`

### Prior Sessions — Layers 1-11

Layers 1 through 11 were designed, speced, and deployed across sessions from approximately 2026-02-14 through 2026-02-19. Key milestones:
- Eval framework built and used to profile Qwen3-4B and Qwen3-14B
- 4B/14B comparison established: 4B = precision tool operator (100% JSON, 80% params), 14B = strategic follower (perfect PACE/graph, tool reliability collapse at 73.3% JSON / 46.7% params)
- Memory classification and enhancement pipelines designed from MemR³ and A-MEM research
- Organization kernel implemented with PACE protocols
- Supervisor loop deployed with stall detection

---

## Hardware & Environment

- **GPU:** RTX 3090 (24GB VRAM)
- **Runtime:** Agent-Zero in Docker container
- **Models:** Qwen2.5-14B-Instruct-1M (supervisor), GLM-4.7 Flash (utility), GPT-OSS-20B (OpenPlanter/investigation)
- **Inference:** LM Studio on host, accessed via `host.docker.internal:1234`
- **Vector DB:** FAISS (Agent-Zero built-in)
- **Repo:** GitHub (private), committed 2026-02-22 with all Phase 1 fixes
- **Note:** Single GPU means model contention when Agent-Zero (14B) and OpenPlanter (20B) run simultaneously. For investigation tasks, run OpenPlanter standalone and feed results back to Agent-Zero.

---

## Design Notes

Pre-spec explorations of architectural concepts. Each is motivated by a specific incident and sketches a mechanism that may become a full L3 spec.

| Design Note | Motivated By | Status |
|-------------|-------------|--------|
| `ERROR_COMPREHENSION_DESIGN_NOTE.md` | ST-002 terminal session loop | Ready to build |
| `LAYER_COORDINATION_DESIGN_NOTE.md` | Component interference in multi-layer stack | Deferred — build simpler fixes first |
| `ACTION_BOUNDARY_DESIGN_NOTE.md` | MJ Rathbun incident | Ready to build after pattern collection |
| `AUTONOMOUS_AGENCY_ARCHITECTURE.md` | Proactive agent research + command structure paradigm | Forward design — operational doctrine for persistent agent operations |

---

## Essays

Philosophical substrate of the project. Each emerged from a specific engineering problem or architectural insight.

| Essay | Core Principle | Emerged From |
|-------|---------------|--------------|
| The Cathedral and the Phantom | Continuity across discontinuity | Session reconstruction challenge |
| The Immune Response | Protection must calibrate to current capability | Fallback false positive crisis |
| The Gate Between Knowing and Doing | Trust is an engineering outcome | MJ Rathbun / action boundary design |
| The Carrier and the Signal | Ideas embedded in functional systems outlast ideas presented as ideas | Communication protocol / meme transmission to subordinate models |
| The Whole That Wasn't Packed | Emergence can't be shipped directly — only the conditions for it | SOUL.md revision / Gestalt principle in reconstruction |

The essays are not optional reading. They transmit judgment and values that specifications cannot encode.

---

## Reading Order for New Instances

1. **This document** — where the project stands
2. **SOUL.md** — how we work together
3. **The Cathedral and the Phantom** — why the architecture is shaped this way
4. **The Immune Response** — why protective systems need to recognize success
5. **The Gate Between Knowing and Doing** — why capability without governance is incomplete
6. **The Carrier and the Signal** — why ideas survive in systems, not presentations
7. **The Whole That Wasn't Packed** — why emergence can't be shipped, only its conditions
8. **AUTONOMOUS_AGENCY_ARCHITECTURE.md** — operational doctrine for persistent agent operations
9. **SKILLS_INDEX.md** — procedures for recurring tasks
10. **Relevant design notes** — for whatever's being built next
