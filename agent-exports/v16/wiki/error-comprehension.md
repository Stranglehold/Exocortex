# Error Comprehension Layer

## Problem Statement
Agent lacks deterministic error classification. When a tool call fails or produces unexpected output, the agent must infer failure mode from raw text — this wastes context and enables repeated mistakes.

## Current State
- No dedicated error classifier in extension pipeline
- Errors surface as raw stdout/stderr in tool_result field
- Agent re-reads full output to diagnose instead of receiving structured signal
- Related: `inc-watchdog-blind` (hardcoded 100k window overflow)

## Proposed Architecture
Deterministic pre-processing layer that runs before LLM sees the response:

### Phase A — Classification Taxonomy
| Class | Pattern | Action Hint |
|---|---|---|
| `network_timeout` | \(timed?out\|connection refused\|dns failure\) | Retry with backoff |
| `permission_denied` | \(EACCES\|403\|forbidden\|unauthorized\) | Escalate or switch user |
| `missing_dependency` | \(module not found\|command not found\|importerror\) | Install then retry |
| `syntax_error` | \(syntax error\|parse failed\|invalid json\) | Fix input, don't retry raw |
| `resource_exhausted` | \(oom\|disk full\|context window exceeded\) | Reduce scope or clear cache |
| `tool_misuse` | \(missing arg\|unexpected kwarg\|schema violation\) | Inspect tool spec, correct args |

### Phase B — Anti-Action Principle
If error class maps to a **non-retryable** action (syntax_error, resource_exhausted), inject a blocking hint before the LLM sees the message:
```
[ERROR-COMP] Class=syntax_error | Retry=NO | Suggestion: Fix JSON structure before resubmitting
```
This prevents the agent from blindly retrying a doomed action.

### Phase C — Confidence Gate
If no pattern matches, pass through with `[ERROR-COMP] Class=unknown | Pass-through` to avoid false negatives.

## Implementation Scope
- Location: `/a0/usr/plugins/exocortex/extensions/tool_execute_after/_53_error_comprehension.py`
- Modifies only: extension hook (non-.py if using SKILL.md wrapper, or new .json config)
- Backup target: existing tool_execute_after hooks before modification

## Test Plan
1. Run 10 known-failing commands (timeout, permission denied, missing module, syntax error)
2. Verify classifier assigns correct class to each
3. Measure: reduction in repeated failed actions per session
4. Baseline: current retry rate ~3x per failure; target: 1.5x

## Dependencies
- Related decisions: `dec-lower-supervisor-thresholds` (earlier intervention pairs with error classification)
- Related incidents: `inc-watchdog-blind`, `inc-stuck-delivery-loop`

## Status
TODO — awaiting human review before implementation

## Empirical Validation (Cycle #16, 2026-05-08)

Tested classification taxonomy against 10 real error samples from journal history.
**Baseline accuracy: 90.0%** (9/10)

| Sample | Expected Class | Match |
|---|---|---|
| aiohttp.client_exceptions.SocketTimeoutError:... | network_timeout → network_timeout | ✓ |
| Permission denied: /root/protected_file... | permission_denied → permission_denied | ✓ |
| ModuleNotFoundError: No module named 'staging... | missing_dependency → missing_dependency | ✓ |
| json.decoder.JSONDecodeError: Expecting prope... | syntax_error → syntax_error | ✓ |
| OSError: [Errno 28] No space left on device... | resource_exhausted → resource_exhausted | ✓ |
| TypeError: missing required argument 'runtime... | tool_misuse → tool_misuse | ✓ |
| Connection refused by remote host on port 443... | network_timeout → network_timeout | ✓ |
| EACCES: permission denied, open '/secure/path... | permission_denied → permission_denied | ✓ |
| ImportError: cannot import name 'old_function... | missing_dependency → missing_dependency | ✓ |
| SyntaxWarning: invalid escape sequence \b... | syntax_error → none | ✗ |
## See Also
- [Decision Records](index.md#decision-records)
- [Index](index.md)
