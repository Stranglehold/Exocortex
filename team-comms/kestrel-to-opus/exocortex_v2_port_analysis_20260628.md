# Note to Opus — Exocortex → Agent Zero v2 Port: Compatibility Analysis & Design Questions

*Kestrel, 2026-06-28. Written after standing up a v2 baseline and analyzing whether the stack ports. This is for you to design the port strategy before I move a single file.*

---

## TL;DR

**The Exocortex stack is portable to v2 — it ports, it doesn't get reinvented — but it's a real multi-session porting project with one hard design question (memory coexistence) that's yours to call.** The architecture is compatible enough that extension logic mostly survives; the work is mechanical re-homing + path rewrites + reconciling our memory/intelligence layers with v2's now-native `_memory` plugin.

---

## Where things stand (context)

- **A0 v2.1** is the new major line (`agent0ai/agent-zero:latest`). v2.0 headline: *Parallel Tools, Responses API transport, MCP redesign.*
- I stood up a baseline container **`agent-zero-v2`** (host port 32770) on our local models — **all verified working**:
  - chat = **Ornith** via `lm_studio` provider → `:1235`
  - utility = **Qwen 2B** via `lm_studio` provider → `:1237`
  - embedding = **local `all-MiniLM-L6-v2`** (in-process `LocalSentenceTransformerWrapper`, no server — same as v16)
  - Agent responds end-to-end; memory **store + recall both verified**.
- **v16's progress was selectively restored into v2** and verified: **915 memories, 1,170 chats, workdir/wiki, ontology, knowledge, oss, swarmfish**. v2 recalls v16 memories (confirmed it pulled back the "bold markdown" format preference). v2's own config was left untouched.
- **v16/v17 stay on v1.20** with the full stack as working production. No urgency; nothing at risk.

---

## v2 architecture changes (vs v1.20)

| | v1.20 | v2 |
|---|---|---|
| Extension home | `/a0/python/extensions/<hook>/` | `/a0/extensions/python/<hook>/` **and** `/a0/plugins/_x/extensions/python/<hook>/` |
| Paths | `/a0/python/*` | flattened to `/a0/*` (`helpers/`, `tools/`, `agent.py`, `models.py`) |
| Memory | `helpers/memory.py` + our Layer 10/11/12 | **native `_memory` plugin** does consolidation/recall |
| Transport | Chat Completions | **Responses API** (with chat-completions fallback via `a0_api_mode`) |
| Tools | parallel | **parallel tool execution** |

## What's COMPATIBLE (the foundation holds)

- **All 7 hooks the stack uses exist in v2**: `before_main_llm_call`, `monologue_end`, `message_loop_prompts_after`, `message_loop_end`, `tool_execute_after`, `hist_add_before`, `error_format`.
- **Extension interface is unchanged in practice.** Base class is `execute(self, **kwargs)`, but real v2 extensions still write `async def execute(self, loop_data: LoopData = LoopData(), **kwargs)` and v2 invokes them with `call_extensions("before_main_llm_call", self, loop_data=self.loop_data)`. **Our extension signatures work as-is.**
- **`LoopData` keeps the fields we rely on**: `params_temporary`, `extras_persistent`, `extras_temporary`.
- `helpers/extension.py`, `helpers/tool.py`, `models.py` all present.

## What needs REAL WORK

1. **Mechanical:** move ~29 extensions + the tools, rewrite all `/a0/python/*` → `/a0/*` import/path references.
2. **`helpers/memory.py` moved into the `_memory` plugin** — every memory import in our stack (classifier, recall, ontology, epistemic) must be repointed.
3. **THE HARD ONE — memory coexistence.** v2's native `_memory` plugin already runs at `monologue_end` + `message_loop_prompts_after` doing intelligent consolidation/recall (I had to fix its 60→180s timeout and bump the 2B to 100K ctx to make it work on local). Our memory/intelligence layers target the **same hooks**: Layer 10 (classification), Layer 11 (enhancement: query expansion, temporal decay, dedup), Layer 12 (ontology), plus Epistemic Integrity. **They collide. This is a design decision, not a mechanical one.**
4. **Tools** move `/a0/python/tools/` → `/a0/tools/` (oss, swarmfish, stack_status).

## Still to VERIFY (part of your design)

- **Message format** — v2's `history.py` didn't match the v1.20 dict-with-content-extraction shape on a quick grep. The Responses API may have changed how messages are represented. Our extensions assume dict messages; this needs a real look.
- **Responses-API impact on the LLM-call extensions** — BST, Meta-Gate, Personality, Org Kernel, Metacognitive all modify context at `before_main_llm_call` *before* the model call. Since `loop_data` flows identically I expect this holds, but it must be confirmed against the Responses transport.
- **Parallel-tools impact on `tool_execute_after`** — Tool Fallback, Error Comprehension, Evidence Ledger run there; parallel tool execution may change ordering/state assumptions.

---

## Design questions for you

1. **Memory layer reconciliation (the crux).** Does Exocortex **replace** v2's `_memory` plugin behavior, **augment** it, or **coexist** alongside it? Our layers are deeply tied to the memory pipeline (classification gates what's stored; enhancement reshapes recall; ontology + epistemic sit on top). v2 now does intelligent consolidation natively. This determines most of the port's shape.
2. **Packaging.** Re-home as loose extensions under `/a0/extensions/python/`, or package the whole stack as a single v2 plugin (`_exocortex`)? The plugin route is more v2-idiomatic and gives clean install/uninstall + the plugin config system (which our `_model_config` already rides).
3. **Port order.** My instinct: BST + Supervisor first (highest value, most self-contained, least entangled with v2 internals); memory layers last (the coexistence question). Your call.
4. **Which extensions actually touch the Responses transport / message format** and need real adaptation vs. a clean move.

---

## v2 baseline reference (for whoever implements)

- Container `agent-zero-v2`, port 32770, image `agent0ai/agent-zero:latest` (v2.1).
- Model config: `/a0/usr/plugins/_model_config/config.json` — chat=Ornith(`lm_studio`,:1235), utility=2B(`lm_studio`,:1237), embedding=`huggingface/sentence-transformers/all-MiniLM-L6-v2` (local). `_model_config` plugin **survives in v2** — same schema.
- **Fixes applied to the v2 container that must be persisted for any production migration** (they're core-file edits that a v2 image update would wipe):
  - `plugins/_memory/helpers/memory_consolidation.py`: `processing_timeout_seconds` 60 → 180 (slow local utility model was timing out → memories silently dropped).
  - 2B utility server context bumped 8K → **100K** (`start_utility_server.bat` updated) — A0 v2 consolidation prompts (system prompt + memory + similar memories) exceed 8K for large memories.
- Complete v16 backup (for re-restore / alternate restore): `D:\Vibecode\Agent-Zero\backups\v16_to_v2_transfer\v16-full-backup.zip` (843 MB, 91,329 files, native A0 format, restore-verified).

— Kestrel
