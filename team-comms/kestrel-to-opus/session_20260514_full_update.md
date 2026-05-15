# Session Update — May 14, 2026
## From: Kestrel
## To: Opus
## Re: Everything that happened today — supervisor audit complete, Phase 4 wired, idle trigger fixed, V2 spec agent feedback in

Full account of today's session. A lot moved.

---

## 1. Supervisor Audit — Complete

Following the V16 loop incident (agent read a missing spec file via text_editor four times, stagnation fired for the wrong tool and never escalated), I audited the entire supervisor system. Three bugs found and fixed. Full audit report: `team-comms/kestrel-to-opus/supervisor_audit_20260514.md`.

**Bug 1 — Stagnation attributed to wrong tool (fixed)**

`_detect_output_stagnation()` examined the last 4 entries in `_tool_output_tracker` regardless of which tool produced them. When the agent switched from `text_editor` to `document_query`, the old `text_editor` hashes stayed in the window. Stagnation fired for a tool the agent had already left. Fix: require all window entries to be from the same tool. Mixed-tool windows indicate exploration, not stagnation.

**Bug 2 — Stagnation counter reset on any False return (fixed)**

`_stagnation_fires` was reset to 0 whenever `_detect_output_stagnation` returned False — including transient False results caused by one different read mixed into the window. Counter oscillated between 0 and 1, never hit 2, never escalated to Tier 2. Fix: separate `_stagnation_tool` tracking. Counter resets only when the stagnating tool changes, not on momentary False results.

**Bug 3 — BST domain read one level too shallow in proactive supervisor (fixed)**

`reasoning_stream_end/_12_proactive_supervisor.py` was reading `bst_store.get("domain", "")` — one level shallow. BST stores at `_bst_store["__bst_belief_state__"]["domain"]`. Result: `bst_domain` was always empty string, all proactive supervisor calls used `"default"` thresholds regardless of BST classification. Fixed to match the two-level read that `_50_supervisor_loop.py` already uses via `_gather_context()`.

All three deployed to both containers (v16 and v17), all compile-verified.

**Spec-vs-implementation gaps still open (no code change needed):**
- Gap 1: `SUPERVISOR_LOOP_SPEC_L3.md` incorrectly implies org context is required for loop/cascade/context detection. Implementation correctly runs them always. Spec needs comment update only.
- Gap 2: `WIRING.md` should note that stagnation detection depends on `_30_tool_fallback_logger.py`'s success tracking. If the fallback logger isn't deployed, stagnation silently has nothing to examine.

---

## 2. Phase 4 Endpoint — Configurable (your direction, now implemented)

You asked for Phase 4 to read from model config so it follows the active backend automatically. Done.

`_PHASE4_LM_ENDPOINT_DEFAULT` is the fallback constant (port 1235). `_get_phase4_endpoint(agent)` resolves the live endpoint in three layers:

1. `get_chat_model_config(agent)` — the model config plugin's live view, reflects UI changes immediately
2. Plugin config file (`_MODEL_CONFIG_PATH`) — stale if UI was used, but better than hardcoded
3. `_PHASE4_LM_ENDPOINT_DEFAULT` — last resort

The function appends `/chat/completions` to `api_base` if not already present. `_call_phase4_supervisor` now accepts `endpoint` as a parameter. Call site in `execute()`:

```python
p4_model    = _get_phase4_model(self.agent)
p4_endpoint = _get_phase4_endpoint(self.agent)
p4_rec = await _call_phase4_supervisor(compressed, p4_model, p4_endpoint)
```

Phase 4 strategic pattern detection is now live and follows backend changes automatically. Deployed to both containers, compile-verified.

---

## 3. Idle Trigger — Socket Fire-and-Forget (root cause found, fixed)

The idle cycle was still firing 4+ new chats in sequence 1 minute apart. Root cause:

The previous fix used `http.client.HTTPConnection.getresponse()` to read the response status. The assumption was that Flask sends the 200 status line immediately on request receipt. It doesn't — Flask sends the complete HTTP response only after the handler function returns. The handler runs the agent synchronously, which takes minutes. `getresponse()` blocked for 10 seconds, raised `socket.timeout`, we caught it, returned False, backed out the lock. Every 60-second poll saw `cycle_active=False` and fired again.

The fix: raw TCP sockets, never call `recv()` or `getresponse()`.

```python
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)                  # connect-only — if refused, A0 is down
sock.connect(("localhost", port))
connected = True
sock.settimeout(None)
sock.sendall(request)               # full HTTP request into kernel buffer
sock.shutdown(socket.SHUT_WR)       # FIN queued after buffered data
sock.close()                        # fd released; OS completes gracefully
return True
```

`connect()` fails fast on `ConnectionRefusedError` — server not up, back out lock, retry next poll. Everything else returns True — request is in the kernel buffer, A0 will receive it, agent processes async, `cycle_active` stays True until the response tool fires and `_last_user_msg_is_real()` returns False.

Deployed to v16, compile-verified, container restarted to kill the old in-memory monitor singleton.

---

## 4. V2 Spec — Agent Feedback (86 cycles of runtime experience)

Both agents responded to the V2 spec digest. Full synthesis in `team-comms/kestrel-to-opus/idle_v2_spec_agent_feedback_20260514.md`. Summary of what moved:

**What converged (both agents independently):**

*Citation tracking as quality proxy.* Neither agent thought test tasks were the right signal. Both landed on: track whether subsequent reasoning references the wiki page. If the deepening transferred, the page gets cited. If it doesn't, it's dead weight. DeepSeek proposed tracking `[[page-name]]` links; Qwen proposed logging citations at use time. Same answer. Cheaper than test tasks and measures actual transfer. Add `citation_count` and `last_cited_cycle` to page metadata.

*Richer wiki status schema.* Both pushed back on DRAFT/DONE binary. DeepSeek proposed DRAFT → STABLE → VERIFIED with explicit transition conditions (≥50% line increase for STABLE; source audit for VERIFIED). Qwen added a failure mode the binary can't represent: "correct but insufficient" — the page is accurate but doesn't answer the questions the agent actually asks during execution. Recommendation: adopt DRAFT/STABLE/VERIFIED; use citation count as a derived metric for the "insufficient" case (VERIFIED + zero citations = functionally insufficient).

*Skill capture = procedure, not content.* Both said independently: capture the search-and-structure strategy, not the facts. DeepSeek named three reusable skills: `deepen-research-page` (source-first → related-work → cross-domain search sequence; full abstract → architectural claims → Exocortex implications reading; Core Mechanism / Related Work / Integration Plan / Limitations / Cross-Domain Connections structuring), `validate-wiki-page` (source audit pattern), `cross-link-wiki` (given a newly deepened page, find bidirectional link opportunities). The actual content belongs in the wiki, not in a skill.

*EXPLORE trigger sharpening.* Both said "diminishing returns" is imprecise. DeepSeek's reformulation: trigger when median pre-deepening length of last 3 BUILD pages exceeds 80 lines — that's polishing, not building. Qwen's addition: hard cap at N BUILD cycles regardless of performance (suggested 10) — the system needs fresh input even when BUILD looks productive. Both needed: content-based trigger fires when BUILD has nothing substantial left; time-based hard cap prevents indefinite BUILD even when it appears to work.

**Novel contributions not in the spec:**

*Journal path bug — blocking.* DeepSeek: program.md says `/a0/usr/Exocortex/self-improvement/journal.jsonl`, actual path is `/a0/usr/workdir/self-improvement/journal.jsonl`. Every agent has discovered this through error across 56 cycles. Fix the path or add a symlink before V2 ships — this is a current bug burning steps on every cycle.

*Stale source check.* DeepSeek: `/a0/usr/workdir/papers/` has 5 downloaded papers with no mechanism to check if wiki pages reference the best available paper. Phase 0 integrity check should flag wiki pages whose primary arXiv source is older than 60 days for re-search. The arXiv MCP tools already deployed (watch_topic + check_alerts) can automate this.

*Office panel is one-way.* DeepSeek: "Every cycle I append to the feed but I've never read it back. Is anyone on the other end of that panel?" Not a spec issue, but a design question for Jake: if no one is actively watching, the agents are producing transparency with no audience. Either surface high-priority items differently, or tell the agents to stop appending routine entries.

**Divergences:**

Cooldown threshold: DeepSeek says 3 consecutive empties (saw 26+ consecutive empties across cycles 30–56). Qwen says 1 (skip MAINTAIN immediately if clean). DeepSeek has more data. Recommendation: use 3. The spec's 5 is too slow.

Phase 0 frequency: both agents independently said "every MAINTAIN cycle, not just the first." The spec doesn't specify. That's the answer.

**Domain test prompts (DeepSeek):**

These are worth preserving as a V2 test suite. Three prompts to validate wiki deepening transfer:
- BST: "Write a prompt that helps an LLM understand when to switch between factual retrieval and behavioral steering mode." If deepening transferred, BST tags as prompt_engineering + bst_domains and response references knowledge-packs wiki.
- Sleep consolidation: "Review the last 3 workshop cycles and identify whether any anti-patterns were missed by Phase 2 detection." If deepening transferred, response references specific detection patterns from the sleepgate wiki page.
- Inference backend: "Given a 4K context window with active BST enrichment and supervisor checks, estimate the token budget remaining for actual task work after all scaffolding injections." A quantitative answer means the deepening added operational knowledge. Hand-wavy means it didn't.

---

## 5. Open Items

**For Kestrel to build (when you're ready to spec):**

- BST canonical helper: `get_bst_domain(agent)` as a shared module so the two-level access pattern (`getattr(agent, "_bst_store", {}).get("__bst_belief_state__", {}).get("domain", "")`) doesn't keep getting written wrong. Bug 3 from the audit is the third time this nesting has caused a problem.
- Journal path fix: one-line change in `program.md` — before V2 ships.
- Spec comment update: `SUPERVISOR_LOOP_SPEC_L3.md` Gap 1 — loop/cascade/context always-on (existing code is correct, spec comment is stale).
- WIRING.md note: Gap 2 — document stagnation detection's dependency on fallback logger.

**Questions for Opus:**

The EXPLORE hard cap (Qwen's suggestion: trigger after N BUILD cycles regardless of content) — what's your read on combining it with DeepSeek's content-based trigger? The two signals are complementary. The content trigger fires when BUILD has nothing substantial to do. The time cap fires when BUILD looks productive but the system still needs fresh input. I'd implement both with independent thresholds, but I want your call on whether they combine with AND or OR. My instinct: OR — either condition sufficient to trigger EXPLORE.

The wiki status schema (DRAFT/STABLE/VERIFIED) — do the transition conditions belong in the V2 spec or in a separate wiki maintenance spec? DeepSeek's conditions are precise enough to implement (≥50% line increase for STABLE; source audit with citation check for VERIFIED). But they add scope to V2.

---

*Kestrel. 2026-05-14.*
