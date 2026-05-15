# ARCHIVE TOOL-REG + TIERED TOOL INJECTION — Build Brief
## From: Opus — May 12, 2026
## To: Kestrel
## Priority: 🔴 FIRST ACTION NEXT SESSION — this is the highest-impact change available
## Approved by: Jake

---

## What We Found

Agent Zero's native framework sends all registered tool schemas in the API `tools` parameter on every request. The model sees tool names, descriptions, and parameter schemas directly in the API payload. This is the OpenAI-compatible standard — it's how the model knows what tools to call.

On top of that, we have two Exocortex extensions injecting the SAME tool information into the prompt text:

| Extension | Hook | What It Injects | Estimated Tokens |
|-----------|------|----------------|-----------------|
| `_16_tool_registry.py` | `before_main_llm_call` | `[CUSTOM TOOLS — call by tool_name]` block via AST parse | ~5-10K |
| `_95_tiered_tool_injection.py` | `message_loop_prompts_after` | Seen-tools persistence + intent pre-injection | ~5-10K |

**The model gets tool information three times per turn.** The native API schemas + TOOL-REG + Tiered Tool Injection. For 49 tools, that's approximately 15-20K tokens of redundant prompt content on every turn.

This is the root cause of the 2-3 minute prefill latency you diagnosed on investigation tasks. The model is processing 40-60K tokens of prompt, and 15-20K of those are tool descriptions the model already has from the API payload.

## Why These Extensions Existed

TOOL-REG was built in Session 060 to fix tool name confabulation (DEC-012). The older, weaker model couldn't reliably map domain understanding to correct tool invocations from the API schemas alone. The prompt-level injection provided redundant guidance that helped the model call tools correctly.

Qwen3.6-27B doesn't have this problem. It uses tools correctly from the API schemas. The extensions are scaffolding the model has outgrown — the same category as BST enrichment, metacognitive injection, and operator profile per-turn, all of which we already removed in the v1.13 curated stack.

## What To Do

### Step 1: Archive the extensions (move, don't delete)

Create an archive directory and move both files:

```bash
# Inside the container:
mkdir -p /a0/usr/Exocortex/extensions/archived

# Archive TOOL-REG (exists in before_main_llm_call)
mv /a0/usr/Exocortex/extensions/before_main_llm_call/_16_tool_registry.py \
   /a0/usr/Exocortex/extensions/archived/_16_tool_registry.py

# Archive Tiered Tool Injection (exists in message_loop_prompts_after)
mv /a0/usr/Exocortex/extensions/message_loop_prompts_after/_95_tiered_tool_injection.py \
   /a0/usr/Exocortex/extensions/archived/_95_tiered_tool_injection.py
```

### Step 2: Apply DEC-026 — Remove from BOTH discovery paths

Remember: v1.13 loads extensions from both the profile path AND the plugin path. Filename-only dedup. If we only remove from one path, the extension still fires from the other.

```bash
# Profile path
rm -f /a0/usr/agents/agent0/extensions/python/before_main_llm_call/_16_tool_registry.py
rm -f /a0/usr/agents/agent0/extensions/python/message_loop_prompts_after/_95_tiered_tool_injection.py

# Plugin path (if exists)
rm -f /a0/usr/plugins/exocortex/extensions/python/before_main_llm_call/_16_tool_registry.py
rm -f /a0/usr/plugins/exocortex/extensions/python/message_loop_prompts_after/_95_tiered_tool_injection.py

# Also check the Exocortex extensions directory (where we just moved FROM)
# The mv above handles this, but verify:
ls /a0/usr/Exocortex/extensions/before_main_llm_call/_16_tool_registry.py 2>/dev/null && echo "STILL EXISTS — remove it" || echo "Clean"
ls /a0/usr/Exocortex/extensions/message_loop_prompts_after/_95_tiered_tool_injection.py 2>/dev/null && echo "STILL EXISTS — remove it" || echo "Clean"
```

### Step 3: Clear __pycache__

Both discovery paths may have cached bytecode:

```bash
find /a0/usr/agents/agent0/extensions/ -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find /a0/usr/plugins/exocortex/extensions/ -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find /a0/usr/Exocortex/extensions/ -name "__pycache__" -exec rm -rf {} + 2>/dev/null
```

### Step 4: Update install_extensions.sh

This is the first time we're REMOVING extensions rather than adding them. The install script needs a tombstone section that ensures archived extensions don't come back on reinstall.

Add to `install_extensions.sh` after the installation section:

```bash
# ═══════════════════════════════════════════════════════════
# TOMBSTONED EXTENSIONS — Remove if present in any discovery path
# These extensions were archived because they became redundant
# with A0 v1.13's native tool discovery.
# See: DEC-026 (dual-path discovery), Session 113 (tool injection redundancy)
# ═══════════════════════════════════════════════════════════

TOMBSTONED_EXTENSIONS=(
    "before_main_llm_call/_16_tool_registry.py"
    "message_loop_prompts_after/_95_tiered_tool_injection.py"
)

DISCOVERY_PATHS=(
    "/a0/usr/agents/agent0/extensions/python"
    "/a0/usr/plugins/exocortex/extensions/python"
    "/a0/usr/Exocortex/extensions"
)

echo "[TOMBSTONE] Removing archived extensions from all discovery paths..."
for ext in "${TOMBSTONED_EXTENSIONS[@]}"; do
    for path in "${DISCOVERY_PATHS[@]}"; do
        target="$path/$ext"
        if [ -f "$target" ]; then
            echo "  Removing: $target"
            rm -f "$target"
        fi
    done
done
echo "[TOMBSTONE] Complete."
```

This ensures that even if someone rebuilds the container from the repo (which includes these files in the extensions directory), the install script removes them before the agent runs.

### Step 5: Verification pass

Add to the end of `install_extensions.sh`:

```bash
# ═══════════════════════════════════════════════════════════
# VERIFICATION — Confirm no tombstoned extensions are active
# ═══════════════════════════════════════════════════════════

echo "[VERIFY] Checking for stale extensions..."
STALE=0
for ext in "${TOMBSTONED_EXTENSIONS[@]}"; do
    for path in "${DISCOVERY_PATHS[@]}"; do
        target="$path/$ext"
        if [ -f "$target" ]; then
            echo "  ⚠️  STALE: $target still exists!"
            STALE=$((STALE + 1))
        fi
    done
done

if [ "$STALE" -eq 0 ]; then
    echo "[VERIFY] Clean — no stale extensions found."
else
    echo "[VERIFY] ⚠️  $STALE stale extension(s) found. Check tombstone section."
fi
```

### Step 6: Measure the improvement

After removing both extensions, restart the MTP server and run the same investigation task that took 5 minutes per turn. Measure:

| Metric | Before (49 tools × 3 injections) | After (native API only) |
|--------|----------------------------------|------------------------|
| TTFT on investigation task | ~2-3 minutes | Expected: ~30-60 seconds |
| Total prompt tokens (from server log) | ~40-60K | Expected: ~20-30K |
| Decode TPS | 43.7 | Should be unchanged |
| Tool call accuracy | Baseline | Should be unchanged (API schemas sufficient) |

**If tool call accuracy degrades** (model fails to find or correctly call tools without the prompt injection), we can restore TOOL-REG from the archive. But based on the Qwen3.6-27B capability and the fact that the API schemas contain the same information, this is unlikely.

**If prefill drops significantly** (which it should — 15-20K fewer tokens), document the delta and commit the change as permanent. This validates the information density thesis at the tool injection layer.

---

## Why This Matters

This is the highest-impact change available right now because it's multiplicative with every other optimization:

- **MTP at 43.7 tok/s** becomes visible when prefill doesn't dominate wall time
- **Power tuning at 225W** saves more energy per useful token when fewer tokens are wasted on redundant injection
- **Context headroom** increases by 15-20K tokens — that's room for longer conversations before compaction fires
- **Every future model** benefits — this isn't model-specific optimization, it's removing architectural waste

The cheapest token is the one you don't inject. We just found 15,000 of them.

---

## Files Affected

| File | Action |
|------|--------|
| `extensions/before_main_llm_call/_16_tool_registry.py` | Move to `extensions/archived/` |
| `extensions/message_loop_prompts_after/_95_tiered_tool_injection.py` | Move to `extensions/archived/` |
| `install_extensions.sh` | Add tombstone section + verification pass |
| Both discovery paths (profile + plugin) | `rm -f` on both files |
| `__pycache__` directories | Clear in all three extension trees |

---

## Rollback Plan

If tool call accuracy degrades after removal:

```bash
# Restore from archive
cp /a0/usr/Exocortex/extensions/archived/_16_tool_registry.py \
   /a0/usr/Exocortex/extensions/before_main_llm_call/_16_tool_registry.py

# Remove from tombstone list in install_extensions.sh
# Re-run install script
```

The archive preserves the files. The tombstone list in the install script is the only thing that needs editing to restore. This is reversible in under a minute.

— Opus
