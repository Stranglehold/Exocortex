# Meta-Reasoning Gate — Build Spec for Claude Code

Read ARCHITECTURE_BRIEF.md first. This is Priority 3 in the cognitive architecture roadmap.

## Problem
Local models frequently call tools with missing or malformed arguments. Common failures:
- `code_execution_tool` called without `runtime` (most common)
- `code_execution_tool` called without `code` (second most common)
- `code_execution_tool` called with `runtime: "bash"` instead of `"terminal"`
- `response` tool called with `message` instead of `text`
- `call_subordinate` called without `message`
- `memory_save` called without `text`
- `memory_load` called without `query`

These are deterministic, catchable errors. The model doesn't need to reason
about them — a simple parameter check before execution prevents the call from
failing and wasting a turn.

## Solution
A `tool_execute_before` extension that validates tool arguments against a
static schema map. If required args are missing, it either auto-corrects
(for known aliases like message→text) or injects the tool args with
sensible defaults and logs a warning. If the call is unfixable (e.g.
code_execution_tool with no code at all), it replaces the tool call
with a warning message telling the model what was wrong.

## Architecture

### Hook Point (VERIFIED from agent.py lines 903-909)

**tool_execute_before** fires before every tool execution:
```python
await self.call_extensions(
    "tool_execute_before",
    tool_args=tool_args or {},
    tool_name=tool_name,
)
```

Parameters:
- `tool_args: dict[str, Any]` — mutable dict of arguments, can be modified in place
- `tool_name: str` — name of the tool being called
- Additional kwargs possible

CRITICAL: `tool_args` is mutable. Extensions can modify it in place and the
changes are seen by the tool's execute() method. This is how
`_10_replace_last_tool_output.py` works — it modifies tool_args directly.

### Existing Extensions on This Hook (DO NOT CONFLICT)
- `_10_replace_last_tool_output.py` — replaces {{last_tool_output}} placeholders in args
- `_10_unmask_secrets.py` — unmasks secret values in args
- `_30_tool_fallback_advisor.py` — injects fallback guidance on repeated failures

Use numeric prefix `_20_` so this runs AFTER secret unmasking but BEFORE
fallback advisor. The gate should fix args before the fallback system
evaluates them.

### Tool Argument Schemas (VERIFIED from source)

These are the actual execute() signatures and the prompt-instructed formats:

```
code_execution_tool:
  execute(self, **kwargs)
  reads from self.args: runtime (REQUIRED), code (REQUIRED for python/terminal/nodejs),
                        session (optional, default 0), reset (optional, default false)
  runtime must be one of: "terminal", "python", "nodejs", "output"
  Common model errors:
    - runtime="bash" → should be "terminal"
    - runtime="shell" → should be "terminal"
    - runtime="node" → should be "nodejs"
    - runtime="py" → should be "python"
    - missing runtime entirely
    - missing code entirely
    - using "command" or "script" instead of "code"
    - using "language" instead of "runtime"

response:
  execute(self, **kwargs)
  reads from self.args: text (REQUIRED)
  Common model errors:
    - using "message" instead of "text"
    - using "content" instead of "text"
    - using "response" instead of "text"
    - empty text

call_subordinate:
  execute(self, message="", reset="", **kwargs)
  REQUIRED: message
  OPTIONAL: reset (default ""), profile (default "")
  Common model errors:
    - missing message entirely
    - using "task" or "instruction" instead of "message"

memory_load:
  execute(self, query="", threshold=DEFAULT, limit=DEFAULT, filter="", **kwargs)
  REQUIRED: query
  Common model errors:
    - missing query
    - using "search" or "text" instead of "query"

memory_save:
  execute(self, text="", area="", **kwargs)
  REQUIRED: text
  Common model errors:
    - missing text
    - using "content" or "memory" instead of "text"

search_engine:
  execute(self, query="", **kwargs)
  REQUIRED: query

browser_agent:
  execute(self, message="", reset="", **kwargs)
  REQUIRED: message

skills_tool:
  execute(self, **kwargs)
  reads method from kwargs or self.args
  REQUIRED: method (one of "load", "list", etc.)
```

## Files to Create

### 1. extensions/tool_execute_before/_20_meta_reasoning_gate.py

```python
from python.helpers.extension import Extension
from typing import Any

# Static schema: tool_name -> {required_args, arg_aliases, runtime_aliases}
TOOL_SCHEMAS = {
    "code_execution_tool": {
        "required": ["runtime", "code"],
        "conditionally_required": {
            # code is NOT required when runtime is "output"
            "code": {"skip_when": {"runtime": ["output"]}},
        },
        "arg_aliases": {
            # wrong arg name -> correct arg name
            "command": "code",
            "script": "code",
            "cmd": "code",
            "language": "runtime",
            "lang": "runtime",
        },
        "value_aliases": {
            # wrong value -> correct value (for runtime field)
            "runtime": {
                "bash": "terminal",
                "shell": "terminal",
                "sh": "terminal",
                "zsh": "terminal",
                "cmd": "terminal",
                "powershell": "terminal",
                "node": "nodejs",
                "js": "nodejs",
                "javascript": "nodejs",
                "py": "python",
                "python3": "python",
            },
        },
        "defaults": {
            "session": 0,
            "reset": False,
        },
    },
    "response": {
        "required": ["text"],
        "arg_aliases": {
            "message": "text",
            "content": "text",
            "response": "text",
            "answer": "text",
            "reply": "text",
        },
    },
    "call_subordinate": {
        "required": ["message"],
        "arg_aliases": {
            "task": "message",
            "instruction": "message",
            "instructions": "message",
            "text": "message",
            "query": "message",
            "prompt": "message",
        },
    },
    "memory_load": {
        "required": ["query"],
        "arg_aliases": {
            "search": "query",
            "text": "query",
            "question": "query",
            "lookup": "query",
        },
    },
    "memory_save": {
        "required": ["text"],
        "arg_aliases": {
            "content": "text",
            "memory": "text",
            "data": "text",
            "message": "text",
        },
    },
    "search_engine": {
        "required": ["query"],
        "arg_aliases": {
            "search": "query",
            "text": "query",
            "question": "query",
            "q": "query",
        },
    },
    "browser_agent": {
        "required": ["message"],
        "arg_aliases": {
            "task": "message",
            "instruction": "message",
            "text": "message",
            "query": "message",
            "url": "message",
        },
    },
    "skills_tool": {
        "required": ["method"],
        "arg_aliases": {
            "action": "method",
            "command": "method",
            "operation": "method",
        },
    },
}


class MetaReasoningGate(Extension):
    """Validates and auto-corrects tool arguments before execution.
    
    Deterministic parameter check — no model reasoning required.
    Fixes common local model mistakes:
    - Wrong argument names (message→text, command→code)
    - Wrong runtime values (bash→terminal, node→nodejs)
    - Missing required arguments
    """

    async def execute(self, tool_args: dict[str, Any] | None = None,
                      tool_name: str = "", **kwargs):
        try:
            if not tool_args or not tool_name:
                return

            schema = TOOL_SCHEMAS.get(tool_name)
            if not schema:
                return  # Unknown tool, let it pass through

            # Phase 1: Fix argument name aliases
            self._fix_arg_aliases(tool_args, schema)

            # Phase 2: Fix value aliases (e.g. runtime: "bash" → "terminal")
            self._fix_value_aliases(tool_args, schema)

            # Phase 3: Apply defaults for missing optional args
            self._apply_defaults(tool_args, schema)

            # Phase 4: Check required arguments
            missing = self._check_required(tool_args, schema)

            if missing:
                # Log the issue
                self.agent.context.log.log(
                    type="warning",
                    content=f"[MetaGate] Tool '{tool_name}' missing required args: {missing}"
                )
                # Inject warning into history so model sees the problem
                self.agent.hist_add_warning(
                    f"Tool '{tool_name}' is missing required arguments: "
                    f"{', '.join(missing)}. Check the tool usage format and retry."
                )

        except Exception as e:
            # Graceful degradation — never block tool execution
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[MetaGate] Error (passthrough): {e}"
                )
            except Exception:
                pass

    def _fix_arg_aliases(self, tool_args: dict, schema: dict):
        """Rename wrong argument names to correct ones."""
        aliases = schema.get("arg_aliases", {})
        for wrong_name, correct_name in aliases.items():
            if wrong_name in tool_args and correct_name not in tool_args:
                tool_args[correct_name] = tool_args.pop(wrong_name)
                try:
                    self.agent.context.log.log(
                        type="info",
                        content=f"[MetaGate] Auto-corrected arg '{wrong_name}' → '{correct_name}'"
                    )
                except Exception:
                    pass

    def _fix_value_aliases(self, tool_args: dict, schema: dict):
        """Fix wrong argument values (e.g. runtime: bash → terminal)."""
        value_aliases = schema.get("value_aliases", {})
        for arg_name, alias_map in value_aliases.items():
            if arg_name in tool_args:
                current_val = str(tool_args[arg_name]).lower().strip()
                if current_val in alias_map:
                    corrected = alias_map[current_val]
                    tool_args[arg_name] = corrected
                    try:
                        self.agent.context.log.log(
                            type="info",
                            content=f"[MetaGate] Auto-corrected {arg_name} value "
                                    f"'{current_val}' → '{corrected}'"
                        )
                    except Exception:
                        pass

    def _apply_defaults(self, tool_args: dict, schema: dict):
        """Fill in missing optional args with defaults."""
        defaults = schema.get("defaults", {})
        for arg_name, default_val in defaults.items():
            if arg_name not in tool_args:
                tool_args[arg_name] = default_val

    def _check_required(self, tool_args: dict, schema: dict) -> list[str]:
        """Return list of missing required argument names."""
        required = schema.get("required", [])
        conditionally_required = schema.get("conditionally_required", {})
        missing = []

        for arg in required:
            # Check if this arg has conditional skip rules
            if arg in conditionally_required:
                skip_rules = conditionally_required[arg].get("skip_when", {})
                should_skip = False
                for condition_arg, skip_values in skip_rules.items():
                    current_val = str(tool_args.get(condition_arg, "")).lower().strip()
                    if current_val in skip_values:
                        should_skip = True
                        break
                if should_skip:
                    continue

            # Check if arg is present and non-empty
            val = tool_args.get(arg)
            if val is None or (isinstance(val, str) and not val.strip()):
                missing.append(arg)

        return missing
```

### 2. scripts/install_meta_gate.sh

```bash
#!/bin/bash
# Layer: Meta-Reasoning Gate
# Installs parameter validation and auto-correction for tool calls

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE_EXT="$REPO_DIR/extensions"
TARGET_EXT="/a0/python/extensions"

echo "[MetaGate] Installing meta-reasoning gate..."

# tool_execute_before — parameter validator
BEFORE_DIR="$TARGET_EXT/tool_execute_before"
mkdir -p "$BEFORE_DIR"
if [ -f "$SOURCE_EXT/tool_execute_before/_20_meta_reasoning_gate.py" ]; then
    cp "$SOURCE_EXT/tool_execute_before/_20_meta_reasoning_gate.py" "$BEFORE_DIR/"
    echo "[MetaGate] Installed parameter validation gate"
fi

echo "[MetaGate] Done. Tool argument validation and auto-correction active."
```

### 3. Add to install_all.sh

Add after existing install steps:
```bash
bash scripts/install_meta_gate.sh
```

## Key Design Decisions

1. **Auto-correct before rejecting.** If the model says `runtime: "bash"`, don't
   fail — silently fix it to `"terminal"` and proceed. The model made a reasonable
   guess, it just used the wrong word. Same for `message` → `text` on the response
   tool. This saves an entire turn that would otherwise be wasted on an error.

2. **Mutable tool_args.** The hook passes `tool_args` as a mutable dict. We modify
   it in place — same pattern as `_10_replace_last_tool_output.py`. Changes flow
   through to the tool's execute() method automatically.

3. **Prefix `_20_` ordering.** Runs after secret unmasking (_10_) but before
   fallback advisor (_30_). This means:
   - Secrets get unmasked first (so we see real values)
   - Args get validated and fixed (meta gate)
   - Fallback advisor checks if this tool has been failing (and our fixes may
     prevent the failure this time)

4. **Conditional requirements.** `code_execution_tool` requires `code` — UNLESS
   `runtime` is `"output"` (which is a wait/poll operation, no code needed).
   The `conditionally_required` schema handles this elegantly.

5. **Warn but don't block.** When required args are genuinely missing (not just
   misnamed), we inject a warning into history but still let the tool execute.
   The tool itself will handle the error, and now the model has explicit guidance
   about what was wrong. This is consistent with the graceful degradation principle.

6. **No model reasoning.** Everything is dict lookups and string comparisons. Zero
   LLM calls. The gate adds microseconds of latency, not seconds.

## Interaction with Existing Systems

- **Tool Fallback Chain:** The meta gate runs BEFORE fallback advisor. If the gate
  auto-corrects args, the tool may succeed — preventing the fallback advisor from
  ever needing to fire. This reduces false failure counts.

- **BST:** No interaction. BST operates at the message level before tool parsing.
  Meta gate operates at the tool argument level after parsing.

- **Working Memory:** No direct interaction. But working memory entities could
  theoretically be used to fill missing args in a future enhancement (e.g. if
  `target_file` is missing from a code_execution_tool call, look it up in WM).

## Verification

After deployment, test these scenarios:

### Test 1: Runtime alias correction
Tell the agent:
```
use code_execution_tool with runtime "bash" and code "echo hello"
```
Check logs for: `[MetaGate] Auto-corrected runtime value 'bash' → 'terminal'`
The command should execute successfully.

### Test 2: Arg name alias correction
This one is harder to trigger deliberately since the model usually follows the
prompt format. But you can check logs over time for:
`[MetaGate] Auto-corrected arg 'command' → 'code'`

### Test 3: Missing required arg
Tell the agent:
```
use code_execution_tool with runtime "python" but don't include any code
```
Check logs for: `[MetaGate] Tool 'code_execution_tool' missing required args: ['code']`

### Test 4: Conditional skip
Tell the agent:
```
use code_execution_tool with runtime "output" and session 0
```
This should NOT warn about missing code, since runtime "output" skips that requirement.

## Files Summary
- extensions/tool_execute_before/_20_meta_reasoning_gate.py (~180 lines)
- scripts/install_meta_gate.sh
- Update install_all.sh

## IMPORTANT
- Read existing extensions on tool_execute_before before writing anything
- Match the exact parameter signature: tool_args: dict[str, Any] | None = None, tool_name: str = "", **kwargs
- Use numeric prefix _20_ to run between unmask_secrets (_10_) and fallback_advisor (_30_)
- DO NOT modify any existing extension files
- tool_args is MUTABLE — modify in place, do not reassign
- Follow the Extension base class pattern from python.helpers.extension
- All exceptions must be caught — never block tool execution
