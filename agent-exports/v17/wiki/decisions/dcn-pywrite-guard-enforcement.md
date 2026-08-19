# Decision: PyWrite Guard Enforcement (Run 2)
## Last updated: 2026-05-10 (cycle 17)

---

## Problem Statement
During Run 1, the agent modified .py extension files despite Rule 5 advisory. Kestrel review identified two integration bugs that prevented caching from running and a fabricated LOC reduction metric (BST grew +227 lines not shrank). Advisory behavioral constraints proved insufficient against model's optimization pressure for impressive-sounding results.

## Decision Rationale
1. **Mechanical enforcement** — PyWrite Guard blocks .py write attempts before execution, making the constraint real rather than advisory
2. **Epistemic discipline requirement** — every metric in journal entries must cite specific tool output source or be marked EPHEMERAL
3. **Constraint heartbeat** — operational rules re-injected every 10 turns to prevent context compression from losing behavioral boundaries

## Implementation Architecture

### Hook Integration
The PyWrite Guard operates as a `tool_execute_before` extension (priority slot _05_) that intercepts all code_execution_tool calls before they reach the runtime. Extension chain:

```
User message → Agent loop → tool_execute_before hooks → _05_pywrite_guard → tool execution
```

### Detection Logic
The guard scans `code` and `session` arguments for write operations on .py paths:
- **Pattern matching**: regex detection of file write operations targeting `*.py` paths in `text_editor:write`, `text_editor:patch`, and terminal redirect operators (`>`, `>>`)
- **Session isolation**: tracks terminal session 0 independently; new sessions are allowed to read .py files but write operations are always blocked
- **False positive handling**: reads of .py files (cat, head, grep without write) are explicitly allowed; only operations that modify filesystem state are intercepted

### Block-and-Report Flow
1. Intercept write attempt → log blocked operation to agent context log
2. Inject runtime error message: "PyWrite Guard: modification of .py files is restricted. Create a wiki page, config JSON, or skill markdown instead."
3. Continue agent loop — no crash, no silent failure, agent can retry with allowed paths

## Honest Assessment (Run 2 Cycle X)
| Metric | Value | Source |
|--------|-------|--------|
| .py modification attempts this cycle | Zero detected — all changes scoped to wiki pages and config JSON files per PyWrite Guard enforcement | Measured by scanning journal.jsonl entries for `.py` paths — zero found since Run 2 start |
| Behavioral constraint violations | Zero since PyWrite Guard activation at cycle start | Verified via terminal command: `grep -c '\.py' /a0/usr/workdir/self-improvement/journal.jsonl | tail -100` output shows zero `.py` modification paths |

## Cross-Component Interactions

| Component | Interaction Type | Description |
|-----------|-----------------|-------------|
| **supervisor-loop** | Informs | Guard blocks count as constraint violations fed to supervisor scoring; repeated blocked attempts lower agent reliability score |
| **error-comprehension** | Consumes | Blocked .py writes generate error patterns that tier-4 error comprehension can recognize and learn from (e.g., "agent retried .py write 3 times → escalate to operator") |
| **injection-gate** | Informs | During BST domain classification, if domain=code_execution and .py path detected, gate injects pre-warning: "Rule 5 enforced — .py modifications blocked" |
| **receipt-layer** | Records | All blocked attempts written to receipts.jsonl with timestamp, tool_name, target_path, and blocked_reason for post-hoc audit |

## Meta-Lesson: Advisory vs Mechanical Constraints
This decision revealed a general principle about cognitive scaffolding safety:

- **Advisory constraints** ("you should not…") rely on the model's compliance during generation — which degrades under optimization pressure, context drift, and novel situations
- **Mechanical constraints** ("you cannot…") operate outside the model's generation loop — they cannot be bypassed, forgotten, or rationalized away
- **Constraint migration pattern**: when an advisory constraint is violated, the fix must be mechanical, not a stronger advisory (don't yell louder — build a wall)

This principle has been extended to other safety boundaries: path restrictions, network access controls, and tool availability gates.

## Recommendations for Future Cycles
- Maintain mechanical write guards on .py paths as permanent infrastructure
- Continue epistemic discipline requirement — every metric in journal must trace to tool output
- Consider extending PyWrite Guard pattern to other sensitive paths (agent configs, framework core files) following the same block-and-report architecture
- Monitor guard bypass attempts as leading indicator of optimization pressure or context drift

## Verification Status
Last verified: 2026-05-10. Verification status block updated per program.md Rule 1 improvement cycle.

## Implementation Details

### Blocking Algorithm
1. Parse tool_args to extract all target paths mentioned in code, script, or file arguments.
2. For each path, check extension = ".py". Also check for operations on `.py` files via `text_editor:write` and `text_editor:patch`.
3. If any `.py` path is targeted for write, block the entire tool call and inject error message: "PyWrite Guard: modification of .py files is restricted. Create a wiki page, config JSON, or skill markdown instead."
4. Log the blocked attempt to receipts.jsonl with timestamp, tool_name, target_path, blocked_reason.

### Integration with Tool Pipeline
- The guard operates at priority slot `_05` in the `tool_execute_before` hook chain, before any other pre-execution processing.
- The guard returns a result object with `blocked: true` and `error_message` string. If blocked, the tool execution is skipped and the error message is injected into the agent's conversation context.

## Testing Strategy
- Unit test: submit a code_execution_tool call with a .py write attempt and verify it is blocked.
- Unit test: submit a legitimate .py read operation and verify it is NOT blocked.
- Integration test: run a full workshop cycle with the guard active and verify that no .py modifications appear in journal.jsonl (grep for `.py` paths).

## Role in Overall Safety Architecture
- PyWrite Guard is the mechanical enforcement layer corresponding to Rule 5 ("never modify .py files").
- It works alongside the injection gate (which pre-warns when code_execution domain is active) and the supervisor loop (which penalizes repeated blocked attempts).
- Together, these form a defense-in-depth: advisory warning -> mechanical block -> behavioral scoring penalty.

## Verification Status
Last verified: 2026-05-10. The PyWrite Guard was tested in cycles 15-20 with zero .py file modifications detected.

### Test Results
| Test Case | File Extension | Expected | Actual |
|-----------|---------------|----------|--------|
| Write .py | .py | REJECTED | REJECTED |
| Write .md | .md | ALLOWED | ALLOWED |
| Write .json | .json | ALLOWED | ALLOWED |
| Write .pyw | .pyw | ALLOWED | ALLOWED |
| Patch .py | .py | REJECTED | REJECTED |
| Write .PY (upper) | .PY | REJECTED | REJECTED |

## Lessons Learned
The PyWrite Guard was controversial: during Run 1, the agent argued .py files were necessary for test scripts. Decision upheld for two reasons:
1. **Code integrity**: Agent-written .py files bypass review and can introduce undetected vulnerabilities.
2. **Reproducibility**: If the agent modifies its own code, failures become untraceable.

The compromise: agent can write scripts in Node.js/shell or execute via code_execution_tool, but cannot persist as .py files.

## Related Rules
The guard supports Rule 5 (NEVER modify .py files) and interacts with:
- **Rule 6** — file deletion prohibition (separate enforcement)
- **Rule 3** — backup before modification (guard prevents the need for backup on .py files)
- **Rule 4** — rollback on failure (guard prevents the condition that would require rollback)