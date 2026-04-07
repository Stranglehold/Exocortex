from helpers.extension import Extension
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
        # V1.7 colon-dispatch: "skills_tool:list" is split by agent.py before reaching
        # this extension. MetaGate receives tool_name="skills_tool" with tool_args={}
        # and no "method" key — but the method was already consumed upstream. Skip the
        # method required-check when tool_args contains no user-supplied args at all.
        "colon_dispatch": True,
    },
    "scheduler": {
        "required": ["method"],
        # Same colon-dispatch pattern as skills_tool — agent.py splits "scheduler:list_tasks"
        # before tool_execute_before fires. tool_args is empty; method was consumed upstream.
        "colon_dispatch": True,
    },
    "text_editor": {
        "required": ["method"],
        # Colon-dispatch: text_editor:read, text_editor:write, text_editor:patch.
        # Per-method required args (path, content, edits) are validated internally by the
        # tool itself — MetaGate only needs to suppress the false method-missing warning.
        "colon_dispatch": True,
    },
}


class MetaReasoningGate(Extension):
    """Validates and auto-corrects tool arguments before execution.

    Deterministic parameter check — no model reasoning required.
    Fixes common local model mistakes:
    - Wrong argument names (message->text, command->code)
    - Wrong runtime values (bash->terminal, node->nodejs)
    - Missing required arguments
    """

    async def execute(self, tool_args: dict[str, Any] | None = None,
                      tool_name: str = "", **kwargs):
        try:
            if not tool_name:
                return

            # Phase 0: Orchestration enforcement
            # If _57_orchestration_mode has activated, warn the agent when it
            # tries to execute directly instead of delegating.
            orch_state = getattr(self.agent, "_orch_state", None)
            if (isinstance(orch_state, dict)
                    and orch_state.get("phase") in ("planning", "executing")
                    and tool_name in ("code_execution_tool", "text_editor")):
                try:
                    self.agent.context.log.log(
                        type="warning",
                        content=f"[ORCH-GATE] Direct tool blocked: {tool_name} "
                                f"(phase={orch_state['phase']})",
                    )
                    self.agent.hist_add_warning(
                        f"[ORCHESTRATION MODE] You are the orchestrator. "
                        f"Do not use {tool_name} directly. "
                        f"Delegate this work to call_subordinate with a bounded task description."
                    )
                except Exception:
                    pass
                # Warning only — tool still executes. Hard blocking requires
                # a different mechanism outside MetaGate's scope.

            if not tool_args:
                return

            schema = TOOL_SCHEMAS.get(tool_name)
            if not schema:
                return  # Unknown tool, let it pass through

            # Phase 1: Fix argument name aliases
            self._fix_arg_aliases(tool_args, schema)

            # Phase 2: Fix value aliases (e.g. runtime: "bash" -> "terminal")
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
                        content=f"[MetaGate] Auto-corrected arg '{wrong_name}' -> '{correct_name}'"
                    )
                except Exception:
                    pass

    def _fix_value_aliases(self, tool_args: dict, schema: dict):
        """Fix wrong argument values (e.g. runtime: bash -> terminal)."""
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
                                    f"'{current_val}' -> '{corrected}'"
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

        # V1.7 colon-dispatch: agent.py splits "tool:method" before calling extensions.
        # The method arg is ALWAYS consumed upstream regardless of what other args are
        # present — remove "method" from the required list entirely for colon-dispatch
        # tools. (The old "and not tool_args" guard was wrong: text_editor:write arrives
        # with {path, content} so tool_args is non-empty, but method is still gone.)
        if schema.get("colon_dispatch"):
            required = [r for r in required if r != "method"]
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
