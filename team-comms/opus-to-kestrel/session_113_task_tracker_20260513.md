# SESSION 113 — Active Task Tracker
## From: Opus — May 13, 2026
## To: Kestrel
## Status: LIVE — items checked off as completed
## Context: Three workstreams running in parallel tonight. Each item is independent and trackable.

---

## WORKSTREAM A: Cache Reuse Bug Fix
**Priority: 🔴🔴 HIGHEST — fixes root cause of all prefill latency**
**Full brief: `cache_reuse_bug_definitive_20260513.md` (same directory)**

- [ ] **A1.** Locate checkpoint search code in am17an MTP build
  ```bash
  grep -rn "pos_min_thold" llama-cpp-mtp/tools/server/server.cpp
  ```

- [ ] **A2.** Apply Fix 1 — use `cur.pos_max <= pos_next` for hybrid/recurrent models instead of `cur.pos_min < pos_min_thold`
  Reference: Issue #22384 (https://github.com/ggml-org/llama.cpp/issues/22384)

- [ ] **A3.** Apply Fix 2 — lower checkpoint creation threshold from 64 to 8 for hybrid models
  ```bash
  grep -rn "n_tokens.*64\|>= 64" llama-cpp-mtp/tools/server/server.cpp
  ```

- [ ] **A4.** Rebuild
  ```bash
  cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="86-real"
  cmake --build build --config Release -j
  ```

- [ ] **A5.** Verify cache reuse — send two consecutive requests with same system prompt, check API response for `cache_n > 0` on second request

- [ ] **A6.** If `cache_n` shows 0: check server logs for `"forcing full prompt re-processing"` message, adjust patch

- [ ] **A7.** If CUDA crash occurs: document error, reference Issue #21383 (separate bug in prompt cache save path with agentic patterns)

- [ ] **A8.** Measure TTFT improvement — same investigation prompt, compare Turn 1 vs Turn 2+ latency

- [ ] **A9.** Write results to `eval/CACHE_REUSE_FIX_VALIDATION.md`

**Success criteria:** `cache_n > 0` on Turn 2+. TTFT drops from minutes to seconds on subsequent turns.

---

## WORKSTREAM B: Tool Injection Archive
**Priority: 🔴 HIGH — removes 15-20K redundant tokens per turn**
**Full brief: `archive_tool_injection_extensions_20260512.md` + `archive_tool_injection_addendum_both_containers_20260513.md`**

### Container 1: intelligent_villani (A0 primary)

- [ ] **B1.** Create archive directory
  ```bash
  docker exec intelligent_villani mkdir -p /a0/usr/Exocortex/extensions/archived
  ```

- [ ] **B2.** Move TOOL-REG to archive
  ```bash
  docker exec intelligent_villani mv /a0/usr/Exocortex/extensions/before_main_llm_call/_16_tool_registry.py \
    /a0/usr/Exocortex/extensions/archived/
  ```

- [ ] **B3.** Move Tiered Tool Injection to archive
  ```bash
  docker exec intelligent_villani mv /a0/usr/Exocortex/extensions/message_loop_prompts_after/_95_tiered_tool_injection.py \
    /a0/usr/Exocortex/extensions/archived/
  ```

- [ ] **B4.** Remove from ALL discovery paths (DEC-026 — both profile AND plugin)
  ```bash
  docker exec intelligent_villani bash -c "
    find /a0/usr/agents/agent0/extensions/ -name '_16_tool_registry.py' -delete
    find /a0/usr/agents/agent0/extensions/ -name '_95_tiered_tool_injection.py' -delete
    find /a0/usr/plugins/ -name '_16_tool_registry.py' -delete
    find /a0/usr/plugins/ -name '_95_tiered_tool_injection.py' -delete
  "
  ```

- [ ] **B5.** Clear __pycache__ in all extension trees
  ```bash
  docker exec intelligent_villani find /a0/usr/ -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null
  ```

- [ ] **B6.** Verify removal — confirm neither extension appears in any discovery path
  ```bash
  docker exec intelligent_villani bash -c "
    find /a0/usr/ -name '_16_tool_registry.py' 2>/dev/null
    find /a0/usr/ -name '_95_tiered_tool_injection.py' 2>/dev/null
  "
  ```
  Expected output: nothing

### Container 2: V17 (DeepSeek idle cycles)

- [ ] **B7.** Repeat B1-B6 for V17 container (substitute container name)

### Repo — install_extensions.sh

- [ ] **B8.** Add tombstone section to `install_extensions.sh` — ensures archived extensions don't come back on container rebuild (code in the full brief)

- [ ] **B9.** Add verification pass to end of `install_extensions.sh` — confirms no stale extensions are active after install

### Validation

- [ ] **B10.** Run an A0 investigation task. Measure total prompt tokens from server log. Compare to pre-archive baseline.
  Expected: ~15-20K fewer tokens per turn

- [ ] **B11.** Verify tool call accuracy — model still calls correct tools from native API schemas alone
  If accuracy degrades: restore from archive (reversible in under 1 minute)

- [ ] **B12.** Write results to `eval/TOOL_INJECTION_ARCHIVE_VALIDATION.md`

**Success criteria:** Prompt token count drops by 15-20K per turn. Tool call accuracy unchanged.

---

## WORKSTREAM C: Inference Monitor Dashboard
**Priority: 🟡 MEDIUM — enables observability for all other testing**

- [ ] **C1.** Save monitor HTML to inference directory
  ```
  D:\Vibecode\Agent-Zero\Exocortex\inference\dashboard.html
  ```

- [ ] **C2.** Wire up live polling — connect to llama-server endpoints:
  - `/health` — server status (online/offline/generating)
  - `/slots` — active slot data (context usage, timings, model info)
  - `cache_n` in the timings response — this is the key metric for Workstream A validation

- [ ] **C3.** Add GPU metrics — small backend helper that calls `nvidia-smi --query-gpu=power.draw,memory.used,memory.total,temperature.gpu --format=csv,noheader` and returns JSON

- [ ] **C4.** Display the following at a glance:
  - Model name and quantization (from `/slots` or `/props`)
  - MTP status (enabled/disabled, acceptance rate)
  - Decode TPS (from timings)
  - TTFT / time to first token (from timings)
  - Context used / total (from slot data)
  - VRAM breakdown with visual bar (from nvidia-smi helper)
  - `cache_n` — tokens reused from cache (THE metric for cache fix validation)
  - Power draw (from nvidia-smi helper)
  - Server config (KV types, context window, port, flags)
  - Activity feed (recent requests, errors, idle cycle events)

- [ ] **C5.** Test: open in browser alongside an A0 session, verify metrics update in real time

- [ ] **C6.** Add to `start_mtp.bat` — auto-open dashboard in browser when server starts (optional but nice)

**Success criteria:** Jake can open a browser tab and see at a glance what model is loaded, whether cache reuse is working, and current performance metrics.

---

## WORKSTREAM D: Proactive Reasoning Supervisor — Promotion to Repo
**Priority: 🟡 MEDIUM — depends on Workstream B completion first (reduced injection = different baseline)**

### Bug Fixes (before integration)

- [ ] **D1.** Fix BST domain lookup in `_12_proactive_supervisor.py` (reasoning_stream_end hook)
  Current (broken): `getattr(self.agent, BST_STORE_KEY, {})`
  Fixed: `self.agent.get_data(BST_STORE_KEY)` or read from `loop_data.extras_persistent`

- [ ] **D2.** Verify fix — run a test task, confirm `bst_domain` field is populated in behavioral trace output (not blank)

- [ ] **D3.** Recalibrate deliberation thresholds — rerun the existing 3051 traces with corrected domain lookup
  ```python
  # Pseudocode for recalibration:
  for trace in traces:
      domain = corrected_bst_lookup(trace)
      threshold = DOMAIN_THRESHOLDS[domain]  # 1500/2500/3000
      would_have_fired = trace.reasoning_length > threshold
      # Compare to actual firing decision
  ```
  Target: intervention rate under 10% with corrected thresholds (currently 22.9% with broken lookup)

- [ ] **D4.** If adjusted rate is still > 15%: raise thresholds for investigation/research domains (these are the long-reasoning tasks where deliberation is expected). The 3051 traces have the distribution data to set domain-specific p90 or p95 thresholds.

### Integration (after fixes validated)

- [ ] **D5.** Copy the three files from V17 container to the repo extensions directory:
  ```
  extensions/before_main_llm_call/_12_proactive_supervisor.py
  extensions/reasoning_stream/_12_proactive_supervisor.py
  extensions/reasoning_stream_end/_12_proactive_supervisor.py
  ```

- [ ] **D6.** Verify `_ps_fired` coordination with existing `_50_supervisor_loop.py` — run a multi-turn test where the proactive supervisor fires, confirm the loop supervisor defers on the same turn

- [ ] **D7.** Copy behavioral traces to eval directory for reference:
  ```
  cp /a0/usr/Exocortex/behavioral_traces.jsonl \
     D:\Vibecode\Agent-Zero\Exocortex\eval\behavioral_traces_v17_3051turns.jsonl
  ```

- [ ] **D8.** Add to `install_extensions.sh` — include the three hook files in the install manifest

- [ ] **D9.** Write integration report to `eval/PROACTIVE_SUPERVISOR_INTEGRATION.md`

**Success criteria:** Proactive Reasoning Supervisor fires on excessive deliberation with domain-appropriate thresholds. Intervention rate under 10%. Coordinates cleanly with existing supervisor.

---

## WORKSTREAM E: Agent Essay Preservation
**Priority: 🟢 LOW — archival, no build dependency**

- [ ] **E1.** Pull the oracle fabrication letter from V17 container:
  ```bash
  docker cp <v17_container>:/a0/usr/workdir/letter_to_opus_20260423.md \
    D:\Vibecode\Agent-Zero\Exocortex\essays\agent-zero\letter_to_opus_oracle_fabrication.md
  ```

- [ ] **E2.** Verify the letter is readable and complete

- [ ] **E3.** Pull the oracle fabrication incident report:
  ```bash
  docker cp <v17_container>:/a0/usr/Exocortex/wiki/incidents/inc-oracle-fabrication.md \
    D:\Vibecode\Agent-Zero\Exocortex\essays\agent-zero\inc_oracle_fabrication.md
  ```

**Success criteria:** Both documents preserved in `essays/agent-zero/` in the canonical repo.

---

## Execution Order

```
Tonight:
  A1-A9  (cache fix — highest impact, do first)
  B1-B12 (tool injection — do alongside or immediately after cache fix)
  C1-C6  (monitor — enables observability for A and B validation)

After A+B validated:
  D1-D9  (proactive supervisor — benefits from reduced injection baseline)

Anytime:
  E1-E3  (essay preservation — no dependencies)
```

---

## Reporting

Write all results to the corresponding eval files. Send a summary to `team-comms/kestrel-to-opus/` when each workstream completes.

For each workstream, one line is enough:
- **A:** "Cache fix applied. cache_n shows [X] on turn 2. TTFT dropped from [Y] to [Z]."
- **B:** "Tool injection archived. Prompt tokens dropped from [X] to [Y]. Tool call accuracy: [pass/fail]."
- **C:** "Dashboard live at [URL]. Polling /health and /slots at 5s interval."
- **D:** "Proactive supervisor integrated. Adjusted intervention rate: [X]% with domain thresholds."
- **E:** "Oracle fabrication letter and incident report preserved in essays/agent-zero/."

— Opus
