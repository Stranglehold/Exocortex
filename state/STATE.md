# STATE.md — Operational Snapshot

**Purpose:** Where we are right now. Read after SOUL.md, before the journal. Updated every session end.  
**Last updated:** 2026-04-17 (Session 002 Audit)

---

## Current Technical Configuration

**Primary environment:** Agent-Zero in Docker on RTX 3090  
**Active container:** `exocortex_v16`  
**Chat model:** `qwen3.5-27b-claude-4.6-opus-reasoning-distilled@q4_k_m`  
**Utility model:** `qwen3.5-4b@q4_k_s` (util tasks; was GLM-4-Flash, updated ~Session 058)  
**Embedding model:** nomic-embed-text-v1.5 (768-dim, instrument) / all-MiniLM-L6-v2 (OSS)  
**Vector DB:** FAISS (Agent-Zero built-in)  
**Repo:** GitHub (private), `Stranglehold/Exocortex`  
**Extension path:** `/a0/usr/agents/agent0/extensions/python/` (DEC-030, migrated from `/a0/python/extensions/`, Session 061)  

**Frontier access:**
- Anthropic API active. Opus 4.6 / Sonnet 4.6 via Claude Code sessions.
- Prompt caching available.

---

## Extension Stack Status

| Layer | Status | Last Validated | Notes |
|-------|--------|---------------|-------|
| BST (Belief State Tracker) | ✅ Deployed | 2026-04-15 (ST-010) | **v3.2:** `investigation` demoted from tiebreak priority 1 → 11. `financial` domain added (15 signals). `analysis` narrowed. `_COMPLEX_BUILD_RX` fixed. 10/10 ST-010 tasks correctly classified. |
| Working Memory Buffer | ✅ Deployed | 2026-02-22 (ST-002) | 25 entities from README. Holds objectives across 20-step chains. |
| Personality Loader | ✅ Deployed | Stable | MajorZero persona. qwen35 profile added. |
| Tool Fallback Chain | ✅ Deployed | 2026-03-07 | Failure tracker resets on success. LOOP_ALTERNATIVES corrected. EC wired through `_gather_context()`. |
| Meta-Reasoning Gate | ✅ Deployed | Stable | V1.7: `colon_dispatch` flag added for `skills_tool:list/load` pattern. |
| Graph Workflow Engine | ✅ Deployed | 2026-04-17 (audit) | HTN plan library deployed (`htn_plan_library.json`). Compound domain matching fixed. Evidence of helping in specific compound-domain tasks; not load-bearing on single-domain turns. |
| Organization Kernel | ✅ Deployed | Stable | PACE inter-agent coordination. Role dispatch by BST domain. PACE task planning = separate proposal (not yet built). |
| Supervisor Loop | ✅ Deployed | 2026-04-15 (SFX-001) | **SFX-001:** Tier 1 made silent — native A0 repeat detector fires logged/monitored, prescriptive "LOOP DETECTED/call_subordinate" removed. `fmt_consecutive` decoupled from tier clock. ST-010: native detector 3× / 0 prescriptive injections. |
| Tiered Tool Injection | ✅ Deployed | 2026-03-07 | Seen-tools persistence + intent pre-injection. |
| Conversational Insight Capture | ✅ Deployed | 2026-03-07 | Deterministic regex capture at monologue_end. |
| Selective Memorizer | ✅ Deployed | Stable | LLM-based memory extraction. Signal-discriminating. |
| Memory Classification | ✅ Deployed | 2026-04-17 (audit) | Source-file guard deployed in `_57_memory_maintenance.py` — prevents chunk-as-conflict false deprecation cascade. |
| Memory Enhancement | ✅ Deployed | Stable | Query expansion, temporal decay, dedup, co-retrieval. |
| Ontology Layer | ✅ Deployed | 2026-03-07 | Working as designed. Needs real investigation task to activate. |
| Error Comprehension | ✅ Deployed | 2026-03-22 | `PRIORITY_ERROR_CLASSES` added: terminal early-exit/heredoc-never-executed pattern. |
| **Action Boundary** | ✅ **Deployed** | 2026-04-15 (V1.7) | **UPDATED from "Designed."** Tier 1-4 framework live. Three calibration gaps closed: Gap A (Python `open()` to system paths → T4), Gap B (quoted-string context detection), Gap C (V1.7: `/a0/usr/plugins/` path coverage + variable indirection bypass). `_action_gate_active` flag coordinates with Supervisor. |
| **Epistemic Integrity** | ✅ **Deployed** | Session 053 | **UPDATED from "Designed."** Evidence Ledger Recorder (`_25_evidence_ledger_recorder.py`, tool_execute_after) + EI analyzer (`_25_epistemic_integrity.py`, monologue_end). Provenance, volatility classification, staleness scoring, `hist_add_warning` on ungrounded high-volatility claims. |
| **Staging Tier** | ✅ **Deployed** | Session 060 | **NEW.** Six components: `_10_session_init.py`, `staging_note` tool, relational salience 5th axis, relational decay exemptions, Sleep Phase 0 (staging lifecycle), canary CUSUM buffer. |
| **Orientation Stack** | ✅ **Deployed** | Session 061 (ST-007) | **NEW.** Four components: (1) Task Completion Tracker — `[COMPLETION STATE]` injected pre-LLM-call; (2) Artifact Registry — `_49_reasoning_state_update.py` detects file writes, `_13_reasoning_state.py` bootstraps `[ARTIFACTS]`; (3) Reasoning State Persistence — compression-bootstrap sequence (`[REASON-STATE]`/`[REASON-INJ]`); (4) Tool Registry v3.2 — AST scan of `/a0/usr/plugins/`, `[CUSTOM TOOLS]` block + `[SUGGESTED SKILLS]`. Skill Suggester `_19_skill_suggester.py` fires once/session. ST-006 result: Type 1 loops 0 (vs 7+ baseline), supervisor firings 3 (vs 10+). |
| **Loop Recovery & Memory Surgery** | ✅ **Deployed** | Session 061 | **NEW.** Five coordinated changes: `_loop_active` flag, evidence ledger timeline, Sleep Phase 4 adjudication, false recovery detector (supervisor reasoning about own action history — first instance), loop-epoch memory isolation. |
| **Sleep Consolidation** | ✅ **Deployed** | 2026-04-17 (audit) | Phases 0-4 live. All phases producing real operational data (confirmed 2026-04-17): Phase 1 dedup+utility_init, Phase 2 episode chunking+anti-pattern, Phase 3 operator interaction modeling, Phase 4 loop-period adjudication (found 3 loop memories, adjudicated correctly). |
| Prosthetic Cortex | 🔬 In progress | 2026-03-06 | Steps 1-13 complete. Layer 18 optimal (separability 1.62). Centroids saved. Step 14 classifier pending. |
| Profile Loader | ❌ Not started | — | Model-specific behavioral profiles. |
| Progress Tracking | ❌ Not started | — | Instruction anchoring without progress awareness. |

---

## Cross-Cutting Systems Status

| System | Status | Notes |
|--------|--------|-------|
| OSS Service | ✅ Running | Container `oss_app` + `oss_postgres`. 10 Agent-Zero tools. Adversarial Input Layer (2026-04-15): Hedge Pattern (3-axis claim tagging), Narrative Stability (retcon detection), SWARMFISH prior injection. Topics: `iran`, `iran-hormuz`, `private-credit`. |
| SWARMFISH | ✅ Running (V2) | Plugin at `/a0/usr/plugins/swarmfish/`, SQLite at `/a0/usr/swarmfish/swarmfish.db`. 5 tools: `swarmfish_predict`, `swarmfish_session`, `swarmfish_sessions`, `swarmfish_calibration`, `swarmfish_outcome`. V1 HTTP containers stopped. |
| A2A Server | ✅ Deployed | `a2a_server/` (7 Python modules). Not actively exercised. |
| Document Library | ✅ Deployed | Three-tier FAISS (collection routing, book summaries, content chunks). 5 tools: `library_add/list/search/remove/collections`. `_17_library_catalog.py` injects collection summaries. |
| Theme Engine | ✅ Deployed | 9 themes. Widget System. Immersion Layer. In-browser editor at `/theme-editor`. |
| Skills System | ✅ Deployed | 20+ procedural skills. `install_skills.sh` to `/a0/usr/skills/`. Validated vs SkillsBench: +16.2pp. |
| Evaluation Framework | ✅ Deployed | 6 modules. Profiles: DeepSeek-R1, Qwen3.5-35B-A3B, Qwen3.5-9B, Qwen3.5-27B. BST eval harness: 0.98 accuracy, 54 labeled cases, 14 domains. |
| Output Geometry Instrument | 🔬 Active | 51 corpus + 2118 turns. V2 pipeline pending. See `instrument/`. |

---

## Active Work Streams

### Stack Audit (Session 002, 2026-04-17)

Audit authored by Opus 4.7 (doc-first pass, 21 layers). Kestrel executed 9 test items from the audit matrix empirically. Summary of results:

| Test | Result | Key Finding |
|------|--------|-------------|
| TEST-MEM-002 | PASS | Source-file guard load-bearing — 2 chunks at 1.0000 cosine would have been falsely deprecated without it |
| TEST-MEM-003 | PASS | End-to-end pipeline confirmed. `CLS_KEY="classification"` (not "cls") is the correct key |
| TEST-GWE-001 | PASS w/ 2 fixes | Library not deployed (now fixed); compound domain matching broken (now fixed) |
| TEST-FB-001 | PASS | Fallback EC deferral guard implemented; no double-injection |
| TEST-SUP-002 | PASS | Supervisor active: ~280 loop events, ~223 T1 stalls, ~38 T4 blocks across 10 sessions |
| TEST-AB-002 | PASS | T4 gate blocks shell patterns correctly. Gap: `text_editor write` to system path not caught (command type stripped by `_extract_command`) |
| TEST-OS-002 | PASS | Compression→bootstrap sequence confirmed in live logs. ORIENT firing at phase boundaries |
| TEST-SLEEP-002 | PASS | All 5 phases producing real operational data |
| TEST-BST-001 | PASS | 1,356 domain-tool pairs. Domain-specific tools appearing correctly. Enrichment budget correctly assigned (coding/bugfix 99-100% budget=200; philosophical 90% budget=none) |
| TEST-CP-001 | COMPLETE | 67.6% "Strait remains open" was correct: PROMOTED hypothesis, 7/8 predictions confirmed. V1 SWARMFISH data accessible at `swarmfish_postgres` container. |

### Known Gaps (unresolved from audit)

| Gap | Severity | Description |
|-----|----------|-------------|
| `text_editor` T4 write gap | Low | `_extract_command` strips command type from text_editor args; system path T4 check doesn't fire for text_editor writes |
| GWE not load-bearing | Medium | HTN plans activate for compound domains but no evidence of changing execution outcomes. May be architectural dead weight outside compound tasks. |
| Adaptive supervisor | Medium | Designed (Session 058), not confirmed deployed. Compressed-context parallel monitoring. |
| PACE task planning | Medium | PACE inter-agent coordination deployed; PACE failure-tree task planning not built. |
| TEST-BST-002/003 | Low | Slot taxonomy false-positive audit + domain-list sync check not yet run. |

---

## Decisions — Committed

DEC-001 through DEC-030 (main decision log). Key recent decisions:

| DEC | Decision |
|-----|----------|
| DEC-028 | Supervisor SFX-001: Tier 1 silent — native A0 detector runs, prescriptive injection removed |
| DEC-029 | BST v3.2: `investigation` demoted to tiebreak-only position |
| DEC-030 | Extension path migration: `/a0/python/extensions/` → `/a0/usr/agents/agent0/extensions/python/` (persistence guarantee across A0 updates) |

---

## Hardware & Container Reference

| Resource | State |
|----------|-------|
| RTX 3090 (primary) | Active, LM Studio inference |
| Active A0 container | `exocortex_v16` |
| Secondary A0 container | `exocortex_v17` (backup/testing) |
| OSS containers | `oss_app`, `oss_postgres` (start on demand) |
| SWARMFISH V1 containers | `swarmfish_app/redis/postgres` (stopped, data preserved) |
| SWARMFISH V2 | Plugin in `exocortex_v16`, SQLite db |

---

## Documentation Status

| Document | Current? | Notes |
|----------|----------|-------|
| README.md | ✅ Current | Updated through Session 061. |
| STATE.md (this file) | ✅ Current | Updated 2026-04-17. |
| SOUL.md (team/Opus/) | ⚠️ Through Session 052 | soul_staging.md has sessions 053-061 observations. |
| journal_latest.md | ⚠️ Session 052 | Notebook supplements for later sessions. |
| decision_log.md | ⚠️ Through DEC-026 | DEC-027-030 in session notes only. |
| WIRING.md | ⚠️ Needs update | Pre-Orientation Stack, pre-Action Boundary deployment. |
| ROADMAP | ⚠️ Unknown | Check against current layer status. |

---

*Update at every session end. Read first when orient state is unclear.*
