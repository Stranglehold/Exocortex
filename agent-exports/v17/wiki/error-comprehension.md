# Error Comprehension

## Layer
L2: Error Classification & Recovery

## Hook
`tool_execute_after` — `_20_error_comprehension.py`

## What It Does
Error Comprehension intercepts every tool call result before the model sees it. It parses raw command output into structured diagnoses — error class, confidence, suggested actions, and critically, anti-actions that explicitly tell the model what NOT to do next. This prevents the single most common local model failure mode: re-executing a failed command with the same arguments and expecting a different result.

Without this layer, the model sees raw terminal output and must infer what went wrong — often incorrectly, leading to loop cycles. With it, the model receives pre-digested error intelligence that guides recovery.

## Mechanism

### Error Classifier
Parses tool output against a taxonomy of failure categories:

| Error Class | Detection Pattern | Confidence | Common Cause |
|------------|------------------|------------|--------------|
| `SYNTAX_ERROR` | `SyntaxError`, `bash: syntax error` | 0.95 | Malformed command/script |
| `PERMISSION_DENIED` | `Permission denied`, `EACCES` | 0.95 | Wrong user, missing chmod |
| `NOT_FOUND` | `command not found`, `No such file`, `ModuleNotFoundError` | 0.90 | Missing binary, wrong path |
| `TIMEOUT` | `timed out`, `Took too long` | 0.80 | Network, long-running process |
| `IMPORT_ERROR` | `ImportError`, `ModuleNotFoundError` | 0.97 | Missing Python package |
| `CONNECTION_ERROR` | `Connection refused`, `Name or service not known` | 0.90 | Network/service down |
| `MEMORY_ERROR` | `MemoryError`, `Cannot allocate memory` | 0.85 | RAM/swap exhausted |
| `EXIT_ZERO_SILENT` | Exit code 0, no output, but expected output absent | 0.60 | Heredoc never executed, command ran but work didn't happen |
| `UNKNOWN` | Doesn't match any pattern | 0.30 | Novel failure mode |

### Anti-Actions
For each error class, the layer returns an `anti_action` — a specific instruction injected into the model's context telling it what NOT to do:

| Error Class | Anti-Action |
|------------|-------------|
| `SYNTAX_ERROR` | "Do NOT retry the same command — it has a syntax error. Check the exact syntax first." |
| `NOT_FOUND` | "Do NOT retry the same command — the binary/file is not installed/present. Use an alternative or install." |
| `IMPORT_ERROR` | "Do NOT attempt to import this module again in the same session. Install with /opt/venv-a0/bin/pip install and restart." |
| `EXIT_ZERO_SILENT` | "The command exited 0 but produced no work. Do NOT treat this as success. Check for heredoc/multiline issues." |

### Suggested Actions
Positive guidance for recovery:
- `SYNTAX_ERROR` → Check quotes, parentheses, escaping
- `IMPORT_ERROR` → Provide exact pip install command with correct venv path
- `NOT_FOUND` → Suggest alternative tool or installation path

### SUCCESS_INDICATORS
Not all detection looks for failure. The layer also identifies successful patterns to prevent false positives and decay failure counters:
- Write operations that actually produced output
- Commands that returned expected data
- Package installations that confirmed "Successfully installed"

When SUCCESS_INDICATORS fire, the failure history decays rather than escalating.

## Integration Points
- **Supervisor Loop (L4)** — Error class and anti-actions are injected into stall and loop intervention messages. PRIORITY_ERROR_CLASSES (terminal early-exit, heredoc-never-executed) trigger immediate escalation.
- **Evidence Ledger (L8)** — Error classifications recorded with evidence quality scores
- **Failure Tracker (`_30_failure_tracker.py`, same hook)** — Tracks cumulative failure patterns; SUCCESS_INDICATORS cause decay
- **Injection Gate (L3)** — Error severity influences enrichment budget — severe errors get more context

## Key Design Decision
The anti-action mechanism was added after observing that recovery strategies alone were insufficient. The model would read a recovery suggestion, then re-execute the failed command anyway. Explicitly telling the model what NOT to do proved more effective at breaking loop cycles.

## File
`/a0/usr/Exocortex/extensions/tool_execute_after/_20_error_comprehension.py`

## Related
- [[supervisor-loop]]
- [[epistemic-integrity]]
- [[bst-classifier]]
