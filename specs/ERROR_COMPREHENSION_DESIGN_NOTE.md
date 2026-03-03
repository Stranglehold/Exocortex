# Design Note: Structured Error Comprehension

**Status:** Pre-spec exploration. Informed by ST-001 failure analysis and ST-002 terminal session loop. No eval data on error misdiagnosis rates yet — this documents the architectural gap and sketches the mechanism.

---

## The Problem

The agent has two modes of understanding command output: keyword matching (fallback system) and full model reasoning. Neither produces reliable error comprehension.

**Keyword matching** detects that something went wrong but cannot diagnose what. The word "error" in a pip warning triggers the same response as "error" in a fatal crash. The word "not found" after an interactive prompt hang gets classified as "command not found" when the command was found and running — it was waiting for stdin.

**Model reasoning** can diagnose errors when given sufficient context and attention budget, but it's unreliable under pressure. In ST-002, the model read `--configure-keys` output that clearly showed "Key configuration mode: press Enter to keep existing values. OpenAI API key:" and diagnosed it as "command not found / CLI not in PATH." The diagnosis was wrong. The recovery strategy (retry with `python -m`) was therefore also wrong. The agent looped on the wrong fix for the wrong problem.

**What's missing is the middle layer:** deterministic error classification that parses raw command output into a structured diagnosis before the model reasons about it. The model should never have to figure out "is this an interactive prompt or a crash?" from raw terminal text. That classification is deterministic and should be resolved before it reaches the LLM.

### The Rust Compiler Analogy

Good compilers don't just report errors — they diagnose them. Rust's error output includes:

1. **Classification** — what type of error (borrow conflict, type mismatch, lifetime issue)
2. **Evidence** — the specific lines, with visual markup showing the conflict
3. **Causal chain** — "this happened because of this earlier decision"
4. **Suggested action** — "consider using `clone()` or restructuring"

The model (the developer) receives a pre-processed, classified, actionable report. They don't parse raw assembly output to figure out what went wrong. The compiler does the structural analysis; the developer does the strategic reasoning about how to proceed.

Agent-Zero's command execution currently gives the model the equivalent of raw assembly output and expects it to be both compiler and developer.

## Design Principles

1. **Deterministic only.** No LLM calls for error classification. Regex, exit codes, output structure, timing signals.
2. **Additive.** Enriches command output with structured metadata. Does not replace or filter the raw output — the model can still read it if needed.
3. **Composable with existing layers.** Feeds into the fallback system (which becomes smarter about when to fire), the supervisor (which gets better signal for intervention decisions), and the layer coordination protocol (which can broadcast error state).
4. **Extensible.** New error classes can be added as patterns are discovered. Each class is a self-contained classifier with its own regex set, evidence extraction, and suggested actions.

## Architecture Sketch

### Where It Lives

**Hook:** `tool_execute_after` — runs after every command execution, before the fallback logger.

**Execution order:** Must run before the fallback logger (`_30`) so the logger can read the structured diagnosis. Suggested prefix: `_20_error_comprehension.py`.

**Data flow:**
```
Command executes → raw output
    → _20_error_comprehension (classifies, structures)
    → _30_tool_fallback_logger (reads classification, logs appropriately)
    → _30_tool_fallback_advisor (reads classification, advises if needed)
    → Model receives raw output + structured diagnosis
```

### Core Mechanism

```python
@dataclass
class ErrorDiagnosis:
    """Structured error analysis of command output."""
    error_class: str          # e.g., "interactive_prompt", "dependency_missing", "permission_denied"
    confidence: float         # 0.0-1.0
    evidence: list[str]       # specific lines/patterns that triggered classification
    causal_chain: str         # plain-language explanation of what happened
    suggested_actions: list[str]  # ordered by likelihood of success
    anti_actions: list[str]   # things that will NOT fix this — prevents loops
    raw_exit_code: int | None
    raw_output_tail: str      # last N chars for context
```

The extension:
1. Reads command output and exit code
2. Runs classifiers in priority order (most specific first)
3. Produces an `ErrorDiagnosis` (or None if command succeeded)
4. Writes diagnosis to `extras_persistent["_error_diagnosis"]`
5. Optionally injects a compact diagnostic summary into agent context

### Error Class Library

Each error class is a self-contained classifier:

```python
ERROR_CLASSES = [
    {
        "class": "interactive_prompt",
        "description": "Command waiting for stdin input that cannot be provided",
        "signals": [
            # Output ends with a prompt-like pattern and no further output
            r"(?i)(enter|input|password|key|token|confirm|y/n|press)\s*[:>]\s*$",
            r"(?i)\?\s*$",
            # Dialog detection timeout fired
            "Potential dialog detected",
        ],
        "anti_signals": [
            # These look like prompts but aren't
            r"(?i)successfully",
            r"(?i)complete",
        ],
        "exit_code": None,  # Process still running (no exit code)
        "causal_chain": "Command entered interactive mode requiring keyboard input. "
                        "This execution environment cannot provide stdin input to running commands.",
        "suggested_actions": [
            "Kill the current terminal session",
            "Use environment variables instead of interactive configuration",
            "Write configuration directly to the config file",
            "Use CLI flags to pass values non-interactively",
        ],
        "anti_actions": [
            "Do NOT retry the same command — it will hang again",
            "Do NOT try to 'type' into the prompt — stdin is not connected",
            "Do NOT wait for more output — the command is blocked on input",
        ],
    },
    {
        "class": "terminal_session_hung",
        "description": "Previous command still occupying the terminal session",
        "signals": [
            r"Terminal session \d+ might be still running",
        ],
        "causal_chain": "A previous command is still running or hung in this terminal session. "
                        "New commands cannot execute until the session is reset.",
        "suggested_actions": [
            "Reset the terminal session (kill the hung process)",
            "Open a new terminal session with a different session ID",
        ],
        "anti_actions": [
            "Do NOT keep checking the session — it will not resolve itself",
            "Do NOT replan the same command — execute the reset first",
        ],
    },
    {
        "class": "dependency_missing",
        "description": "Required package, module, or command not installed",
        "signals": [
            r"(?i)no module named",
            r"(?i)ModuleNotFoundError",
            r"(?i)ImportError",
            r"(?i)package.*not installed",
            r"(?i)command not found",
            r"(?i)not recognized as.*command",
        ],
        "exit_code_range": [1, 127],
        "causal_chain": "A required dependency is not available in the current environment.",
        "suggested_actions": [
            "Install the missing package with pip/apt-get/npm",
            "Check if a virtual environment needs activation",
            "Verify the package name spelling",
        ],
        "anti_actions": [
            "Do NOT retry the same command without installing the dependency first",
        ],
    },
    {
        "class": "permission_denied",
        "description": "Insufficient permissions for the requested operation",
        "signals": [
            r"(?i)permission denied",
            r"(?i)access denied",
            r"(?i)forbidden",
            r"(?i)EACCES",
            r"(?i)operation not permitted",
        ],
        "exit_code_range": [1, 1],
        "causal_chain": "The current user lacks permissions for this operation.",
        "suggested_actions": [
            "Try with sudo if appropriate",
            "Check file ownership with ls -la",
            "Check if the target is read-only or mounted read-only",
        ],
    },
    {
        "class": "path_not_found",
        "description": "File, directory, or command path does not exist",
        "signals": [
            r"(?i)no such file or directory",
            r"(?i)does not exist",
            r"(?i)not found",
            r"(?i)cannot stat",
            r"(?i)FileNotFoundError",
        ],
        # Exclude interactive prompt patterns — "not found" after a prompt is NOT a path issue
        "anti_signals": [
            r"(?i)(enter|input|password|key|token)\s*:",
            "Potential dialog detected",
        ],
        "causal_chain": "The specified path or command does not exist at the expected location.",
        "suggested_actions": [
            "Verify the path with ls or find",
            "Check spelling and case sensitivity",
            "Check if you're in the correct directory",
        ],
    },
    {
        "class": "network_error",
        "description": "Network connectivity or DNS resolution failure",
        "signals": [
            r"(?i)connection refused",
            r"(?i)network unreachable",
            r"(?i)could not resolve",
            r"(?i)DNS",
            r"(?i)ECONNREFUSED",
            r"(?i)timeout.*connect",
            r"(?i)SSL.*error",
        ],
        "causal_chain": "Network operation failed — target host unreachable, DNS failure, or connection refused.",
        "suggested_actions": [
            "Check if the target service is running",
            "Verify the URL/hostname spelling",
            "Test connectivity with ping or curl -v",
            "Check if a proxy or firewall is blocking the connection",
        ],
    },
    {
        "class": "syntax_error",
        "description": "Code or command syntax is malformed",
        "signals": [
            r"(?i)SyntaxError",
            r"(?i)syntax error",
            r"(?i)unexpected token",
            r"(?i)parse error",
            r"(?i)invalid syntax",
        ],
        "causal_chain": "The command or code contains a syntax error that prevents execution.",
        "suggested_actions": [
            "Review the error message for the specific line and character",
            "Check for missing quotes, brackets, or parentheses",
            "Validate the file with a linter or compiler before retrying",
        ],
    },
    {
        "class": "resource_exhausted",
        "description": "System resource limit reached",
        "signals": [
            r"(?i)out of memory",
            r"(?i)OOM",
            r"(?i)disk full",
            r"(?i)no space left",
            r"(?i)quota exceeded",
            r"(?i)resource exhausted",
            r"(?i)too many open files",
        ],
        "causal_chain": "A system resource (memory, disk, file handles) has been exhausted.",
        "suggested_actions": [
            "Check disk space with df -h",
            "Check memory with free -m",
            "Clean up temporary files or unused containers",
            "Reduce the scope of the operation",
        ],
    },
    {
        "class": "timeout",
        "description": "Operation exceeded time limit",
        "signals": [
            r"(?i)timed?\s*out",
            r"(?i)deadline exceeded",
            r"(?i)connection.*reset",
            r"(?i)killed.*timeout",
        ],
        "causal_chain": "The operation took longer than the allowed time limit.",
        "suggested_actions": [
            "Break the operation into smaller steps",
            "Check if a process is hanging (not timeout but hang)",
            "Increase timeout if the operation is legitimately slow",
        ],
    },
    {
        "class": "version_conflict",
        "description": "Package or API version incompatibility",
        "signals": [
            r"(?i)version.*conflict",
            r"(?i)incompatible",
            r"(?i)requires.*version",
            r"(?i)deprecated",
            r"(?i)breaking change",
            r"(?i)API.*changed",
        ],
        "causal_chain": "A version mismatch between components is preventing correct operation.",
        "suggested_actions": [
            "Check installed version with pip show / npm list",
            "Update to a compatible version",
            "Check the project's requirements file for pinned versions",
        ],
    },
]
```

### Classification Algorithm

```python
def classify_error(output: str, exit_code: int | None, timing: dict) -> ErrorDiagnosis | None:
    """Classify command output into a structured error diagnosis.
    
    Priority order matters — most specific classifiers run first.
    First match wins (no ambiguous multi-classification).
    """
    # Success fast path
    if exit_code == 0 and not _has_error_indicators(output):
        return None
    
    # Special case: no exit code + dialog timeout = interactive prompt
    if exit_code is None and timing.get("dialog_timeout_fired"):
        return _build_diagnosis("interactive_prompt", output, exit_code)
    
    # Special case: terminal session still running
    if "Terminal session" in output and "still running" in output:
        return _build_diagnosis("terminal_session_hung", output, exit_code)
    
    # Run classifiers in priority order
    for error_class in ERROR_CLASSES:
        if _matches_class(output, exit_code, error_class):
            return _build_diagnosis(error_class["class"], output, exit_code)
    
    # Unclassified error — return generic with raw output
    if exit_code and exit_code != 0:
        return ErrorDiagnosis(
            error_class="unclassified",
            confidence=0.3,
            evidence=[f"Exit code: {exit_code}"],
            causal_chain="Command failed with a non-zero exit code. Review the output for details.",
            suggested_actions=["Read the error output carefully", "Search for the specific error message"],
            anti_actions=[],
            raw_exit_code=exit_code,
            raw_output_tail=output[-500:],
        )
    
    return None


def _matches_class(output: str, exit_code: int | None, error_class: dict) -> bool:
    """Check if output matches an error class, respecting anti-signals."""
    import re
    
    # Check anti-signals first — if any match, this class is excluded
    for anti in error_class.get("anti_signals", []):
        if re.search(anti, output):
            return False
    
    # Check exit code range if specified
    code_range = error_class.get("exit_code_range")
    if code_range and exit_code is not None:
        if not (code_range[0] <= exit_code <= code_range[1]):
            return False
    
    # Check signals — any match is sufficient
    for signal in error_class.get("signals", []):
        if re.search(signal, output):
            return True
    
    return False
```

### Context Injection Format

When a diagnosis is produced, inject a compact summary into the agent's context:

```
[ERROR-DX] interactive_prompt (confidence: 0.95)
  What happened: Command entered interactive mode requiring keyboard input. 
  This execution environment cannot provide stdin input to running commands.
  
  Do this:
  1. Kill the current terminal session
  2. Use environment variables instead of interactive configuration
  
  Do NOT:
  - Retry the same command — it will hang again
  - Wait for more output — the command is blocked on input
```

Key design decisions:
- **"Do NOT" section is as important as "Do this."** The anti-actions prevent the exact loop behavior observed in ST-002. The model kept retrying because nothing told it that retrying was the wrong strategy.
- **Compact format.** 5-7 lines maximum. The diagnosis should fit in the context alongside the raw output without consuming excessive tokens.
- **Confidence score.** Lets the model (and the fallback advisor) gauge how much to trust the diagnosis. A 0.95 interactive_prompt diagnosis is near-certain. A 0.3 unclassified is "something went wrong, read the output yourself."

## Integration Points

### With Fallback System

The fallback logger currently classifies errors into broad types ("timeout", "not_found", "syntax"). Error comprehension replaces this classification with richer, more accurate diagnosis. The logger reads `_error_diagnosis` instead of running its own regex:

```python
# In _30_tool_fallback_logger.py
diagnosis = self.agent.get_data("_error_diagnosis")
if diagnosis:
    error_type = diagnosis.error_class  # Use structured classification
else:
    error_type = self._classify_response(message)  # Fall back to current regex
```

The advisor similarly reads the diagnosis for its guidance:

```python
# In _30_tool_fallback_advisor.py
diagnosis = self.agent.get_data("_error_diagnosis")
if diagnosis and diagnosis.confidence > 0.7:
    # Use the diagnosis's suggested actions instead of generic fallback map
    advice = diagnosis.suggested_actions[0]
```

### With Layer Coordination Protocol

If the `_layer_signals` convention is built, error comprehension publishes its state:

```python
signals["error_comprehension"] = {
    "active": True,
    "diagnosis_made": True,
    "error_class": "interactive_prompt",
    "confidence": 0.95,
    "turn": turn_number,
}
```

Other layers can then check: "did error comprehension already diagnose this? If so, I don't need to inject my own warning about it."

### With Supervisor

The supervisor currently detects stalls by counting iterations. With error comprehension, it can detect *diagnostic loops* — the agent receiving the same error class multiple times for the same command pattern:

```python
# If the agent has hit "interactive_prompt" twice for similar commands,
# escalate to operator intervention rather than letting it loop again.
recent_diagnoses = self.agent.get_data("_diagnosis_history") or []
if _repeated_class(recent_diagnoses, "interactive_prompt", threshold=2):
    # Inject: "This command type requires interactive input. Ask the operator
    # for an alternative approach."
```

## What This Does NOT Do

- **Does not replace model reasoning about errors.** The model still sees the raw output. The diagnosis is supplementary structured context, not a replacement. The model may disagree with the diagnosis and act differently.
- **Does not auto-fix errors.** It diagnoses and suggests. Execution is still the model's decision. (Auto-fix is the meta-reasoning gate's job for deterministic corrections like missing parameters.)
- **Does not handle multi-error output.** If a command produces three different error types, only the highest-priority (most specific) diagnosis is returned. This is a simplification that may need revisiting.
- **Does not learn from outcomes.** The classifier is static regex. It doesn't update based on whether the suggested action worked. Classifier improvements happen through manual updates to the error class library.
- **Does not parse language-specific stack traces.** Python tracebacks, Node.js error stacks, and Rust compiler output each have their own structure. Parsing these into structured form is valuable but significantly more complex than the base error classification. Treat as a future extension.

## Relationship to Existing Components

| Component | Current Role | With Error Comprehension |
|-----------|-------------|-------------------------|
| Fallback Logger | Regex error classification | Reads structured diagnosis instead |
| Fallback Advisor | Generic advice by error type | Uses diagnosis's suggested actions |
| Meta-Reasoning Gate | Fixes missing tool parameters | Could fix known error patterns deterministically |
| Supervisor | Detects stalls by iteration count | Detects diagnostic loops by error class |
| BST | Classifies user intent domain | Unaffected — operates on user messages, not command output |

## Open Questions

1. **Where to store the error class library?** Inline in the extension (simple, self-contained) or in a config file (editable without code changes)? Config file is more maintainable but adds a file dependency.

2. **Should diagnosis persist across turns?** A `_diagnosis_history` list would enable loop detection ("you've hit interactive_prompt three times — stop trying interactive commands"). But it adds state management complexity. Start with per-turn, add history if loops remain a problem.

3. **How to handle "success with warnings"?** pip install often succeeds (exit code 0) but produces warning text that contains error-like keywords. The current SUCCESS_INDICATORS in the fallback logger handle this, but error comprehension needs the same awareness. Should it run at all when exit code is 0?

4. **Confidence calibration.** The confidence scores in the sketch are hand-assigned. Should they be calibrated against actual error logs? Need a corpus of command outputs with ground-truth classifications.

5. **Anti-signal priority.** If a signal and an anti-signal both match, anti-signal currently wins (class excluded). Is this always correct? Edge case: output contains both "Permission denied" and "Successfully installed" — the anti-signal "successfully" would exclude the permission_denied class, but the permission error might be for a different operation within the same output.

## Recommended Sequence

1. **Collect error corpus from ST-001 and ST-002 logs.** Extract every command output that was misdiagnosed or that caused a loop. This becomes the test set.
2. **Build minimal classifier with the two classes that caused actual failures:** `interactive_prompt` and `terminal_session_hung`. These are the proven problem cases.
3. **Deploy in read-only mode.** Write diagnosis to `extras_persistent` but don't inject into context. Log to file. Compare classifier diagnosis against what the model actually concluded. Measure agreement rate.
4. **Enable context injection.** Once agreement rate is high and false diagnosis rate is low, inject the compact diagnostic summary.
5. **Expand class library.** Add error classes as new failure modes are observed in stress tests. Each new class requires: signal patterns, anti-signals, causal chain, suggested actions, anti-actions.
6. **Integrate with fallback system.** Replace the logger's regex classification with diagnosis-based classification. This is the point where error comprehension subsumes part of the fallback system's role.

Don't build all ten error classes on day one. Build the two that caused loops, validate them empirically, then expand.

---

*Informed by: ST-001 false positive analysis (fallback firing on successful pip installs), ST-002 terminal session loop (agent misdiagnosing interactive prompt as "command not found"), and the observation that good compilers are good because they diagnose, not just detect.*
