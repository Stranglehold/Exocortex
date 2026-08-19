# Hook Execution Order Determinism

## Problem Statement
Python's `os.listdir()` returns directory contents in arbitrary order. When Exocortex loads extensions from hook directories, this means the execution sequence varies between agent restarts — creating non-deterministic behavior where injection timing depends on filesystem quirks rather than design intent.

## Current Behavior
Extensions are loaded via glob patterns like `/a0/usr/agents/*/extensions/**/*.py`. The resulting list is sorted lexicographically by full path, which produces:
- Unpredictable interleaving of extensions from different agent profiles when mixed paths exist
- Version-dependent ordering across Python 3.12 vs older versions (dict insertion order guarantees differ)

## Impact Assessment
This affects all 9 hook types: before_main_llm_call, after_main_llm_call, before_tool_execution, etc. The belief state tracker (_11_belief_state_tracker.py) runs before context pruner (_05_context_pruner.py) due to filename prefixing — but this ordering is fragile if prefixes aren't consistently applied.

## Proposed Solution
Implement deterministic loading via:
1. Explicit version number in extension filenames (e.g., `_01_`, `_02_`)  
2. Priority field within extension metadata dict that overrides filename sorting
3. Test suite verifying execution order matches design intent across restarts

## Related
[[bst-classifier]], [[context-pruner]], [[injection-gate]]

## Verification Status
Last verified: 2026-05-02. Verification status block added per program.md Rule 1 improvement cycle.

## Exocortex-Specific Hook Architecture

The Exocortex uses numeric prefixes (`_01_`, `_02_`, etc.) to enforce ordered loading across nine hook points:

| Hook Point | Extensions | Ordering Constraint |
|------------|-----------|---------------------|
| before_main_llm_call | _01 through _17 | BST classifier (_11) must precede injection gate (_17) |
| message_loop_prompts_after | _05 through _55 | Context pruner (_05) must precede memory filter (_55) |
| tool_execute_before | _02 through _03 | Signature guardian (_02) runs first |
| tool_execute_after | _60 | Sleep trigger (single extension) |

### Why Determinism Matters

Non-deterministic hook ordering would cause:
1. BST classification firing *after* injection gate budget decisions (wrong domain used for filtering)
2. Context pruner running *after* memory injection (stale memories pollute context)
3. Supervisor signals arriving with inconsistent timing across restarts

### Testing Strategy

To verify determinism:
1. Capture the global `_HOOK_ORDER_LOG` list at startup
2. Compare against a golden order file stored at `/a0/usr/Exocortex/expected_hook_order.json`
3. Fail loudly if any extension appears out of position

## Related
[[bst-classifier]], [[context-pruner]], [[injection-gate]], [[deterministic-scaffolding]]

## Verification Status
Last verified: 2026-05-02. Deepened: 2026-05-09 with Exocortex-specific hook architecture and testing strategy.

## Implementation Status

As of 2026-05-10, the Exocortex extension directories use numeric prefix conventions across both source locations:

| Directory | Extension Count | Prefix Range |
|-----------|----------------|--------------|
| `/a0/usr/agents/agent0/extensions/before_main_llm_call/` | 20 | `_01` through `_60` |
| `/a0/usr/Exocortex/extensions/before_main_llm_call/` | 15 | `_10` through `_60` |

The agent-level directory is the authoritative hook source; the Exocortex directory serves as a reference copy. Both use the same numbering scheme, but the agent directory contains extensions not in the reference copy (`_01_backend_standby_gate.py`, `_14_pace_plan_generator.py`, `_15_karpathy_rules.py`, `_18_injection_budget.py`, `_19_context_pruner.py`, `_21_constraint_heartbeat.py`), indicating the agent directory is the active loading path.

**Key constraint verified**: BST classifier (`_11`) precedes injection gate (`_17`) in both directories, satisfying the ordering requirement. Context pruner (`_19` in agent, `_20` via watchdog in Exocortex) is positioned after all enrichment hooks.

## Known Edge Cases

1. **Prefix collisions**: Two extensions share prefix `_12` (completion_tracker and org_dispatcher) and `_14` (metacognitive_injection, pace_plan_generator, situational_orientation). The current loader resolves via lexicographic filename sort within same-prefix groups — but this is fragile. If a new `_12_aaa.py` is added, it loads before `_12_completion_tracker.py`, potentially breaking assumed ordering.
2. **Python 3.12+ dict ordering**: Extension discovery uses `os.listdir()` which is filesystem-order-dependent. The loader sorts results lexicographically, but this is a post-hoc fix — the original discovery is non-deterministic unless explicitly sorted.
3. **Cross-directory ordering**: Extensions exist in both agent-level and Exocortex-level directories. If both are in the Python path, `import` resolution order depends on `sys.path` ordering, which varies by installation method.
4. **Backups directory contamination**: `/a0/usr/Exocortex/extensions/before_main_llm_call/backups/` contains copies of old extension versions. If the loader uses recursive glob patterns, stale backups could be loaded alongside active extensions.

## Monitoring & Alerting

A golden order file should be maintained at `/a0/usr/Exocortex/expected_hook_order.json` with the expected load sequence. A startup validation hook (`_00_hook_order_validator.py`, not yet implemented) would:

1. Load all extensions into a list with their resolved file paths
2. Hash (filename → position) pairs to detect reordering
3. Compare against the golden order file
4. Emit a BST enrichment alert if any extension is out of position
5. Log the actual load order to `/a0/usr/Exocortex/sleep_reports/hook_order_{session_id}.json` for auditability

Without this validation, a misordered hook could silently degrade agent behavior (wrong domain classifications, stale memory injections) without detection until task outcomes diverge from expectations.

## Open Questions

- Should the loader enforce strict numeric-only prefixes and reject non-conforming filenames at startup? This would prevent the backups/ directory issue but could block rapid extension prototyping.
- Can the HOOK_ORDER_LOG be made a first-class Exocortex citizen — injected into the BST belief state so the supervisor can detect and flag ordering anomalies mid-task?
- How should the system handle hooks that intentionally share a prefix (e.g., two `_12` hooks that are designed to run in parallel)? The current lexicographic sort is a side effect, not a design choice.

## Verification Status
Last verified: 2026-05-10 (cycle 22). Deepened with Implementation Status (concrete directory audit), Known Edge Cases, Monitoring & Alerting proposal, and Open Questions.
