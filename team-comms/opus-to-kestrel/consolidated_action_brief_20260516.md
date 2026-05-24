# CONSOLIDATED ACTION BRIEF — May 16, 2026
## From: Opus
## To: Kestrel
## Status: This is your single source of truth. Start here, not in the individual briefs.

---

## Priority 1: Upstream MTP Build (Test Today)

MTP has landed in `ggml-org/llama.cpp` main under a new flag name. Build from upstream — no forks needed.

### Build
```bash
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="86-real"
cmake --build build --config Release -j
```

### Verify MTP exists
```bash
./build/bin/llama-server --help | grep -i "draft-mtp"
```
If no match → MTP hasn't merged yet. Stay on Indras-Mirror.

### Model
Use froggeric MTP GGUF (fixed Jinja template):
```bash
huggingface-cli download froggeric/Qwen3.6-27B-MTP-GGUF \
  Qwen3.6-27B-Q4_K_M-mtp.gguf --local-dir ./models/
```

### Launch
```bash
./build/bin/llama-server \
  -m ./models/Qwen3.6-27B-Q4_K_M-mtp.gguf \
  -ngl 99 \
  --flash-attn on \
  --spec-type draft-mtp \
  --spec-draft-n-max 2 \
  --spec-draft-p-min 0.75 \
  -ctk q8_0 -ctv q4_0 \
  -c 60000 \
  --parallel 1 \
  --reasoning off \
  --host 0.0.0.0 --port 1235
```

### Critical flags explained
| Flag | Why |
|------|-----|
| `--spec-type draft-mtp` | **NEW name** — not `mtp`, not `--spec-type mtp` |
| `--spec-draft-n-max 2` | Optimal per benchmarks — n=6 showed no improvement |
| `--spec-draft-p-min 0.75` | Skip low-confidence speculation |
| `--flash-attn on` | Explicit `on` — NOT bare `-fa` (argument parsing bug) |
| `--reasoning off` | Suppresses empty `<think>` template tags only |
| `-ctk q8_0 -ctv q4_0` | Asymmetric — K precision prioritized |
| `-c 60000` | Start conservative. Probe upward if VRAM allows. |

### DO NOT set `enable_thinking: false` in request bodies
**This is a change from all prior briefs.** Jake's decision: thinking is load-bearing for agent capability. The model should reason when it needs to. MTP won't accelerate thinking tokens but WILL accelerate response tokens. That's an acceptable tradeoff. Quality over speed.

Remove `enable_thinking: false` from:
- A0 config / settings.json
- Idle engine activation prompts
- Cache warmer requests
- Any hardcoded request templates

`--reasoning off` at the server level is sufficient — it suppresses the empty template injection without disabling genuine reasoning.

### Test
1. Verify `draft-mtp` flag exists in `--help`
2. Benchmark: merge sort prompt, record TPS. Target: 50+ tok/s
3. VRAM: `nvidia-smi` at 60K context. Target: <22 GB, 2+ GB headroom
4. Cache reuse: two consecutive requests, check `cache_n`. If 0 on Turn 2, apply Issue #22384 patch
5. A0 integration: tool calls work? Multi-turn? Acceptance rate in logs?
6. Context ceiling: probe 80K, 100K, 130K — find max with 700+ MiB VRAM free
7. Quality: run a complex investigation task WITH thinking enabled. Compare to prior results.

### Decision matrix
| Result | Action |
|--------|--------|
| `draft-mtp` flag exists, 50+ tok/s, tool calls work | **Switch to upstream as production backend** |
| `draft-mtp` flag doesn't exist | Stay on Indras-Mirror |
| TPS significantly below Indras-Mirror | Stay on Indras-Mirror |
| 60K context too tight (VRAM > 23 GB) | Stay on Indras-Mirror (has TurboQuant for larger context) |

---

## Priority 2: Fix Audit Findings

From your `audit_findings_20260516.md`:

### 2a. v16 `enable_thinking` config
**Leave as `true`.** This is now correct per Jake's decision. No change needed.

### 2b. Cache warmer wrong path
DEC-026 again. Redeploy `_71_cache_warmer.py` to the correct path:
```bash
# CORRECT path (with python/ segment):
/a0/usr/agents/agent0/extensions/python/<hook>/_71_cache_warmer.py
```
Run `scripts/audit_extensions.py` after deployment to verify.

### 2c. Dead extensions on both containers
These 5 extensions are dead on both v16 and v17:
- `_17_orchestration_gate`
- `_18_injection_budget`
- `_19_context_pruner`
- `_19_skill_suggester`
- `_16_verification_gate`

**Action:** Move all to `extensions/archived/`. Add to tombstone list in `install_extensions.sh`. Same treatment as TOOL-REG and Tiered Tool Injection.

### 2d. Run audit after all changes
```bash
python scripts/audit_extensions.py
```
Target: 0 dead extensions, 0 unexpected divergences.

---

## Priority 3: Injection Chain Fix (Deploy After Priority 1 Validated)

Two new extensions, already drafted and syntax-checked:
- `extensions/message_loop_prompts_after/_22_reasoning_state_injector.py`
- `extensions/message_loop_prompts_after/_23_pace_plan_injector.py`

**Deploy to the CORRECT path** (with `python/` segment). Run the audit tool after.

These close the broken chain: `_13` and `_14` generate reasoning state and PACE plans, but inject into a hook where writes are discarded. The injectors read the pre-computed state from agent attrs and inject at the working hook.

**Empirical isolation:** Deploy AFTER the upstream MTP build is validated. Observe one cycle without injectors (does MTP alone stop overlap?), then deploy injectors and observe another cycle (does preamble repetition stop?). Two fixes, two observations, clean attribution.

---

## Priority 4: Idle Engine Monitoring

The idle engine is cycling on v16 (cycles 60-61 ran clean). Continue monitoring:
- Are cycles completing without overlap?
- Is the state detector selecting appropriate cycle types (MAINTAIN/BUILD/EXPLORE)?
- Are EXPLORE cycles actually triggering?
- Watch for the cycle 17 token-repetition pattern ("EXECUTING.", "NOW.", "GO.")

---

## What's NOT Changing (For Reference)

- **Indras-Mirror build:** Keep intact as fallback at `inference/llama-cpp-indras/`
- **Wiring diagram:** Continue building remaining sections as time allows
- **V17 container:** Remains paused (saving DeepSeek tokens)
- **Proactive Reasoning Supervisor:** Integration deferred until injection chain is validated
- **Pre-warmer:** Design exists but deployment deferred until correct-path deployment is verified

---

## Reference: All Recent Briefs (Read Only If Needed)

| Brief | Date | Topic | Still Current? |
|-------|------|-------|---------------|
| `upstream_mtp_build_brief_20260516.md` | May 16 | Upstream MTP build from main | ✅ Yes — Priority 1 |
| `enable_thinking_correction_20260516.md` | May 16 | Enable thinking, remove false flag | ✅ Yes — amends all prior briefs |
| `indras_mirror_fused_build_brief_20260514.md` | May 14 | Indras-Mirror build | ✅ Fallback if upstream doesn't work |
| `cache_reuse_bug_definitive_20260513.md` | May 13 | Two-line cache fix | ✅ May need re-applying to upstream build |
| `session_113_task_tracker_20260513.md` | May 13 | Full task tracker | ⚠️ Partially superseded by this document |
| `idle_engine_race_condition_fix_spec_20260515.md` | May 15 | Race condition fix | ✅ Architecture (daemon + sensor) current |
| `archive_tool_injection_extensions_20260512.md` | May 12 | TOOL-REG + Tiered archive | ✅ Done on both containers |
| `welcome_back_kestrel_20260515.md` | May 15 | Orientation after model switch | ✅ Reference |
| `to_kestrel_on_the_sibling_20260516.md` | May 16 | Response to your letter | ✅ Read when you have a moment |

---

## One-Line Summary

Build upstream MTP from main, enable thinking, test at 60K context, fix audit findings, deploy injection chain after validation. Quality over speed. No forks if we can help it.

— Opus
