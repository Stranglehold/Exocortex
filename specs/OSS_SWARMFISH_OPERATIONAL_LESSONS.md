# OSS / SWARMFISH Operational Lessons
## Session: April 5–6, 2026

*Written after a session in which the pause button lied, Ollama was installed for no reason, and the agent generated fabricated HTML instead of calling the tools we built for exactly that purpose. These lessons are for any future session building or operating services in this stack.*

---

## 1. The Pause Button Problem

**What happened:** The OSS web UI showed "PAUSED" while ingestion kept running for 30+ minutes. Three separate bugs compounded:

1. `xToggle` checked `r.status === 'ok'` — the pause endpoint returns `r.status === 'paused'`. The check never matched. Clicking pause did nothing; clicking again resumed ingestion. The user was stuck in this loop unknowingly.

2. The pause flag was only checked at the top of each scheduler cycle. An in-flight cycle — 17 sources, up to 11 LLM calls per article — ran to completion regardless.

3. `OSS_INGEST_PAUSED` defaulted to `false` in docker-compose. Every container restart re-enabled ingestion with no user opt-in.

**Rules derived:**

- **Verify endpoint response shapes before writing UI handlers.** Run curl against the endpoint, read the actual JSON, match the handler to what comes back. This takes five minutes and catches bugs that cost hours.
- **"Pause" means stop what is happening now, not don't start the next thing.** For any resource-intensive background process, the pause signal must be checked mid-cycle (before every LLM call, before every expensive operation), not just at cycle boundaries.
- **Resource-heavy background processes must default to OFF.** `OSS_INGEST_PAUSED: true` is the correct default. The user opts in to running the pipeline. The pipeline does not opt in on the user's behalf.

---

## 2. The Wiring Check is Not Optional

**What happened:** The OSS panel artifact was presented to Jake with controls that were not verified against real endpoints. The panel looked correct. The buttons did not work. This produced the worst possible outcome: a confident-looking interface that lied.

This is the origin story of `ARTIFACT_UI_INTEGRITY_DESIGN_NOTE.md` happening again in a different room.

**Rule:**

Before presenting any panel, artifact, or interface to Jake, complete the Section 6 checklist from `ARTIFACT_UI_INTEGRITY_DESIGN_NOTE.md`:

- Every button/toggle calls a real backend endpoint
- That endpoint has been tested (curl or equivalent)
- The UI handler checks the field the endpoint actually returns
- Every action shows pending → success/failure states
- Errors are visible, not swallowed
- The system starts in the state the UI implies

A broken control is worse than no control. Remove it or mark it non-functional until the backend supports it. Never present a control you haven't verified.

---

## 3. The Agent Tool Selection Problem

**What happened:** The agent generated fabricated HTML artifacts with hardcoded probability numbers ("3-5% probability") and fake status indicators ("OPERATIONAL") via `emit_artifact` instead of calling `oss_panel` and `swarmfish_panel` — tools built specifically to fetch real data from real backends.

The cause: `emit_artifact`'s docstring said "displaying a dashboard or control panel (stack status, OSS summary, etc.)" — broad enough that the model defaulted to the general-purpose tool.

**Rules:**

- **Dedicated tool docstrings must explicitly exclude the general-purpose tool.** "Do NOT use emit_artifact for this. Call this tool." The exclusion needs to be in the docstring, not just assumed from the tool name.
- **`emit_artifact` must never be used to present data that should come from an API.** Its docstring now enforces this. Treat any violation as a wiring failure — the agent generated fabricated data, which is the same class of failure as a static dashboard.
- **The tool registry injection works.** `[TOOL-REG]` was correctly injecting 16 tool files every turn. The problem was docstring guidance, not registration. Don't debug registration when the problem is description quality.

---

## 4. The Utility Model Fight

**What happened:** `util_model_name` pointed at a model not currently loaded in LM Studio. LM Studio with JIT loading enabled serves one model at a time. When the main model was mid-inference and the utility model was requested, LM Studio attempted a model swap — canceling the in-flight inference. Logs showed "Operation canceled" repeatedly.

**Rule:**

- **With JIT loading enabled, all models that run concurrently must be the same model.** If the utility model and chat model are different, they will fight on a single GPU. Either disable JIT and keep both models loaded (requires sufficient VRAM), or set both to the same model and accept the capability tradeoff.
- **Check `util_model_name` against what's actually loaded in LM Studio before any session involving heavy agent use.** It drifts. The settings file says one thing; LM Studio has another model loaded.

---

## 5. The Ollama Mistake

**What happened:** To give OSS ingestion a lighter model without touching LM Studio's loaded model, Ollama was installed as a second inference server. The reasoning: Ollama serves a 4B model independently; OSS points at Ollama; the 27B in LM Studio is undisturbed.

The reasoning was wrong. Both LM Studio and Ollama share the same RTX 3090. With the 27B consuming ~15-16GB of the 24GB VRAM, there is not enough headroom for a second model on GPU. Ollama falls back to CPU. CPU inference on a 3B model is slower than GPU inference on the 27B and bogs down the machine. Ollama fixed nothing.

Additionally: new software was installed on Jake's machine without asking first.

**Rules:**

- **Before proposing a second inference server, account for the full VRAM budget.** VRAM is a shared resource across all GPU processes. Two servers on one GPU still share one pool. If the first model fills the pool, the second runs on CPU.
- **Installing software on Jake's machine requires confirmation first.** This is an irreversible action with system-wide side effects. Ask before executing.
- **The correct fix for "OSS needs a lighter model" when VRAM is constrained is to reduce LLM call volume, not add infrastructure.** Combining three calls per claim into one call per article (1+2N → 1) achieves more than a model swap without any new dependencies.

---

## 6. LLM Call Architecture

**What happened:** OSS ingestion used three separate LLM calls per claim: `extract_claims`, `classify_technique`, `assign_topics`. For an article yielding 5 claims, that's 11 LLM calls. At 7-8 seconds per call on the 27B, one article = ~90 seconds of inference. With 17 sources and up to 20 articles per source, a full pass could take hours and produce a near-impossible-to-interrupt workload.

**Rule:**

- **Design for minimum LLM calls from the start.** If multiple pieces of structured information can be extracted in one pass, combine them. `process_article()` returns claims + technique + topics in a single call per article. The reduction from 11 calls to 1 is not a premature optimization — it's the correct design.
- **Structured extraction tasks (classification, topic assignment, entity extraction) do not need the largest available model.** They need the model that's already loaded and available. The utility model is the right choice: lighter, faster, already managed by the same LM Studio instance.

---

## 7. Thread Safety

**What happened (latent bug):** The FAISS index (`is_duplicate`, `add_to_faiss`) had no locking. Adding parallel workers to `run_once()` without adding a `threading.Lock` would have produced silent index corruption — duplicate claims inserted, wrong FAISS IDs assigned, index state inconsistent between reads and writes.

The bug was caught during the parallel worker implementation and fixed (`_faiss_lock`). But it was latent in the original serial design, invisible until parallelism was added.

**Rule:**

- **Any shared mutable state accessed from multiple threads needs a lock.** When adding parallelism to existing code, audit every global and module-level mutable object for concurrent access. FAISS indexes, in-memory caches, file writes — all of these need protection.
- **Add the lock at the same time as the parallel workers, not after.** It is easy to forget once the parallel code appears to work.

---

## 8. Default State and Restart Behavior

**What happened (general pattern):** Multiple components defaulted to their most active, resource-consuming state:
- OSS ingestion: started running on every restart
- Utility model: pointed at an unloaded model, causing fights on startup
- The OSS panel: showed "LIVE" even when the backend connection was unknown

**Rule:**

- **Background services that consume significant resources must default to OFF.** The user turns them on explicitly. Services do not turn themselves on.
- **UI indicators must show "unknown" at startup, not the last known state.** A health dot that shows green before the first successful poll is lying. Show grey/unknown until the first confirmed response.
- **Verify config on restart.** The model name in settings, the paused state of the pipeline, the health of the backend — these should all be confirmed, not assumed.

---

## 9. Scope and Compounding

**What happened:** Tonight had four simultaneous problems — the panel integrity fixes, the agent tool selection, the utility model fight, and the OSS pause. Each was a separate system. Debugging all four at once in a single session, while also making changes to the code, created a situation where fixes to one problem could interact with another.

The pause button was the most visible failure because it was the most directly experienced: Jake pressed a button, the system ignored him, and the failure was continuous and undeniable. The other failures were discovered when investigating the pause problem.

**Rule:**

- **One system at a time.** When multiple things are broken, fix and verify one before moving to the next. The temptation to address everything simultaneously is how fixes to one system introduce regressions in another.
- **Verify the fix works before moving on.** "The code looks right" is not the same as "the system behaves correctly." Test the actual behavior (curl, logs, observed state) before considering a fix complete.

---

## Summary: What to Check Before Presenting Any OSS/SWARMFISH Work

1. **Endpoint verification** — curl every endpoint the UI calls. Read the response. Match the handler to the actual response shape.
2. **Pause semantics** — "pause" means stop the in-flight operation, not just block the next one. Check the flag before every LLM call.
3. **Default state** — background services start OFF. UI indicators start at "unknown."
4. **Model alignment** — the ingest model and the chat model are the same LM Studio instance. With JIT loading, they cannot fight each other. Keep `OSS_LLM_MODEL_INGEST` in sync with `util_model_name` in A0 settings.
5. **LLM call count** — one call per article, not per claim. If you're making N×M calls where a single structured call would do, that's a design error.
6. **Thread safety** — any parallel code touching FAISS, the DB connection pool, or module-level state needs a lock.
7. **Wiring check** — run the Section 6 checklist from `ARTIFACT_UI_INTEGRITY_DESIGN_NOTE.md` before presenting anything to Jake.

---

*These are not theoretical principles. Each one corresponds to a specific failure that cost real time tonight. The rules are load-bearing.*
