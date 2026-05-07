# ADDENDUM TO FACTORY COMPATIBILITY AUDIT
## Critical Findings from Kestrel's Ablation Tests (May 3, 2026)
## From: Opus — May 4, 2026

---

## Three Additional Findings That Affect the Migration

### Finding 1: The Two-Directory Problem

Agent Zero has TWO extension directory trees. Only one is active:

| Path | Status |
|------|--------|
| `extensions/<hook>/` | **NEVER LOADED** — stale outer directory |
| `extensions/python/<hook>/` | **ACTIVE** — what A0 actually loads |

Loading code: `paths = subagents.get_paths(agent, "extensions/python", extension_point)`

**Impact:** If any Exocortex extensions are deployed to the outer directory, they are silently not executing. Verify every extension is in the `python/` subdirectory before migration.

### Finding 2: _95_tiered_tool_injection.py Has Never Worked

Searches for `"## Tools available:"` but actual prompt header is `"## available tools"`. Silent no-op on every call since deployment. Dead code — confirms REMOVE verdict.

### Finding 3: Memory Confound in Testing

Format failures are step-count sensitive (appear at step 4+). When memory learns efficient batching (2-3 steps), failures never manifest. Clear memory between validation tests for honest measurements.

### Finding 4: Communication Protocol Prompt

V17 has `agent.system.main.communication_protocol.md` — operator style guide injected every turn. Not in stock A0. Add to REMOVE list (move to Agent Profile).

---

## Updated REMOVE List: 11 items (was 9)

Added: `_95_tiered_tool_injection.py` (dead code) and `communication_protocol.md` (per-turn static injection)

## Updated Migration Checklist

1. Verify all extensions are in `extensions/python/<hook>/` not `extensions/<hook>/`
2. Remove dead code (_95_, communication_protocol.md)
3. Clear memory between validation tests on v1.12
4. Use novel tasks for each validation test (avoid memory recall confound)
5. Check TOOLS_BLOCK_MARKER in any extension referencing prompt headers — format changed between versions
6. Check V17's relaxed JSON guidance ("Plain text is accepted") vs baseline's strict guidance — may need to restore strict version