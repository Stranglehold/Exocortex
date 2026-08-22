import sys

from helpers.extension import Extension
from typing import Any

# A1 three-strike quarantine — ENFORCER half. The RECORDER is
# tool_execute_after/_32_failure_fingerprint.py. Both import the same helper so
# they cannot disagree about what "the same attempt" means; a silent mismatch
# there would leave quarantine permanently inert while looking installed.
_EXOCORTEX_HELPERS = "/a0/usr/plugins/_exocortex/helpers"
if _EXOCORTEX_HELPERS not in sys.path:
    sys.path.insert(0, _EXOCORTEX_HELPERS)

_PLUGIN_CONFIG = "/a0/usr/plugins/_exocortex/config/config.json"

# Absolute last resort for the write limit, used only when write_threshold cannot be
# imported AND the plugin config cannot be read. Named rather than inlined so that
# grepping for the number finds a declaration instead of a magic literal buried in an
# except branch — which is how the previous 5000 stayed invisible while governing every
# write on every model.
_LAST_RESORT_WRITE_LIMIT = 5000


def _backstop_limit() -> tuple[int, str]:
    """(limit, source) for the degraded path. Never raises."""
    try:
        import json
        with open(_PLUGIN_CONFIG, encoding="utf-8") as fh:
            cfg = json.load(fh)
        val = cfg.get("meta_gate", {}).get("write_size", {}).get("base_limit")
        if isinstance(val, (int, float)) and val > 0:
            return int(val), "config"
    except Exception:
        pass
    return _LAST_RESORT_WRITE_LIMIT, "last-resort"


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
            "content": "code",   # 4B models often use "content" instead of "code"
            "source": "code",
            "language": "runtime",
            "lang": "runtime",
            "type": "runtime",
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
        # Strip any key not in this set — prevents system-prompt content
        # (e.g. datetime strings) from leaking into tool_args as garbage keys.
        "known_args": {"runtime", "code", "session", "reset", "allow_running"},
        "strip_unknown_args": True,
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
    "write_file": {
        "required": ["path", "content"],
        "arg_aliases": {
            "file": "path",
            "filename": "path",
            "filepath": "path",
            "file_path": "path",
            "text": "content",
            "data": "content",
            "body": "content",
            "code": "content",
        },
        "defaults": {
            "mode": "w",
        },
        "known_args": {"path", "content", "mode"},
        "strip_unknown_args": True,
    },
}


class MetaReasoningGate(Extension):
    """Validates and auto-corrects tool arguments before execution.

    Deterministic parameter check — no model reasoning required.

    Two categories of checks (and the boundary between them matters):

    1. STRUCTURAL VALIDATION — is the tool call correctly formed?
       Wrong arg names, missing required fields, bad runtime values.
       These are always appropriate to check here.

    2. KNOWN-DETERMINISTIC INVISIBLE FAILURE MODES — the call is correctly
       formed but will fail silently in a way the model cannot observe or recover
       from. Only add these when: (a) the failure is deterministic above a known
       threshold (not probabilistic), AND (b) the model receives no actionable
       error from the failure (no tool output to reason about, just a retry loop).
       The text_editor:write content size check is this category — an oversized
       payload truncates and the model sees only a misformat warning with no
       information about why. As of A3 the limit is complexity-keyed and sourced
       from the active model profile (helpers/write_threshold.py) rather than a
       flat constant: complexity predicts truncation, length alone does not.

    NOT appropriate for MetaGate: runtime feasibility checks that depend on state
    (path existence, disk space, import availability). Those belong in the tool
    fallback chain or error comprehension layer, which have access to tool output.
    """

    async def execute(self, tool_args: dict[str, Any] | None = None,
                      tool_name: str = "", **kwargs):
        try:
            if not tool_name:
                return

            # ── A1: three-strike quarantine ──────────────────────────────────
            # Runs FIRST. Two jobs, in this order:
            #   1. Stash the op signature for _32. `tool_execute_after` receives no
            #      tool_args (verified against A0 v2.9 agent.py ~L1192), so the
            #      recorder cannot compute this itself — it has to be handed over.
            #      Stashed unconditionally, because a call that succeeds must still
            #      overwrite a stale signature from a previous call.
            #   2. Refuse an attempt already under quarantine.
            #
            # Refusing by raise deliberately short-circuits `tool_execute_after`,
            # so a blocked attempt does NOT reach _32 and does NOT add a strike.
            # Quarantine must not deepen itself by being enforced.
            self._quarantine_gate(tool_name, tool_args)

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

            # Phase 0.1: text_editor_remote redirect
            # text_editor_remote is a Claude Code CLI tool — it is NOT available inside
            # the Agent Zero container. When the model calls it, A0 returns
            # "no CLI client connected" in a loop. Intercept early and redirect.
            if tool_name == "text_editor_remote":
                path = (tool_args or {}).get("path", "OUTPUT_PATH")
                msg = (
                    f"text_editor_remote is not available — it requires the Claude Code CLI "
                    f"which is not connected to this context. "
                    f"To write a file, use code_execution_tool with runtime=python:\n"
                    f"  {{\"tool_name\": \"code_execution_tool\", "
                    f"\"tool_args\": {{\"runtime\": \"python\", "
                    f"\"code\": \"with open('{path}', 'w') as f: f.write(section1)\"}}}}\n"
                    f"Keep each write under 800 chars. Use 'a' mode for append sections."
                )
                try:
                    self.agent.context.log.log(
                        type="warning",
                        content=f"[MetaGate] Blocked text_editor_remote — redirecting to code_execution_tool",
                    )
                except Exception:
                    pass
                try:
                    self.agent.hist_add_warning(msg)
                except Exception:
                    pass
                raise ValueError(f"[MetaGate] {msg}")

            # Phase 0.5: text_editor:write content size guard
            # text_editor:write embeds file content inside a JSON string field.
            # When content exceeds the effective limit the response payload truncates
            # mid-string, producing malformed JSON that triggers a misformat loop.
            # Block early and route to Python open() which avoids this entirely.
            if tool_name in ("text_editor", "text_editor:write") and tool_args:
                content = tool_args.get("content", "")
                # A3: the limit is complexity-keyed and sourced from the active model
                # profile, replacing a hardcoded 5000 that applied to every model and
                # every kind of content. The surviving finding from the JSON-reliability
                # arc is that COMPLEXITY predicts truncation and LENGTH does not — a 20K
                # prose payload can pass where 12K with three code fences fails.
                # Complexity only ever LOWERS the limit, so plain prose behaves exactly
                # as before and nothing regresses on evidence we do not have.
                sig = self._write_limits(content)
                if isinstance(content, str) and sig["over"]:
                    path = tool_args.get("path", "OUTPUT_PATH")
                    msg = (
                        f"text_editor:write blocked — content is {len(content):,} chars, "
                        f"over the {sig['effective_limit']:,} char limit for this content "
                        f"(base {sig['base_limit']:,}, complexity {sig['score']}x from "
                        f"{sig['fenced_blocks']} fenced block(s) and "
                        f"{sig['escape_density']:.1%} escape density). It will truncate. "
                        f"Use code_execution_tool with Python open() instead:\n"
                        f"  path = '{path}'\n"
                        f"  with open(path, 'w') as f:\n"
                        f"      f.write(content)  # write full content as Python string\n"
                        f"For large content, write in sections using append mode:\n"
                        f"  with open(path, 'a') as f: f.write(next_section)"
                    )
                    # A block produced by a GLOBAL DEFAULT is a different event from a
                    # block produced by a measured per-model limit, and until now they
                    # were indistinguishable in the record. The old hardcoded 5,000
                    # manufactured 357 blocks across two agents precisely because nothing
                    # ever said "this number was a fallback, not a decision about you".
                    if not sig.get("profile_sourced", True):
                        msg += (
                            f"\n\nNOTE: this limit is NOT calibrated for this model — it "
                            f"came from '{sig.get('profile')}', a global default, because "
                            f"no profile supplies meta_gate.write_size.base_limit. The "
                            f"limit may be far more restrictive than the model warrants."
                        )
                    try:
                        self.agent.context.log.log(
                            type="warning",
                            content=f"[MetaGate-SIZE] Blocked text_editor:write "
                                    f"({len(content):,} chars > {sig['effective_limit']:,} limit, complexity {sig['score']}x, profile={sig['profile']})",
                        )
                    except Exception:
                        pass
                    try:
                        self.agent.hist_add_warning(msg)
                    except Exception:
                        pass
                    raise ValueError(f"[MetaGate-SIZE] {msg}")

            if not tool_args:
                return

            schema = TOOL_SCHEMAS.get(tool_name)
            if not schema:
                return  # Unknown tool, let it pass through

            # Phase 1: Fix argument name aliases
            self._fix_arg_aliases(tool_args, schema)

            # Phase 1b: Strip keys not in known_args (prevents system-prompt
            # content leaking into tool_args as garbage keys on local models)
            self._strip_unknown_args(tool_args, schema)

            # Phase 2: Fix value aliases (e.g. runtime: "bash" -> "terminal")
            self._fix_value_aliases(tool_args, schema)

            # Phase 3: Apply defaults for missing optional args
            self._apply_defaults(tool_args, schema)

            # Phase 4: Check required arguments
            missing = self._check_required(tool_args, schema)

            if missing:
                # For code_execution_tool with missing/empty 'code', inject truncation guidance.
                # The empty-code case is almost always a truncated JSON payload — DirtyJson
                # parses the cut-off code string as an empty value. The model needs to know to
                # use append-mode writes rather than retrying the same oversized payload.
                if tool_name == "code_execution_tool" and "code" in missing:
                    msg = (
                        f"Tool 'code_execution_tool' is missing the 'code' argument. "
                        f"If you were writing a large file, your JSON was truncated — "
                        f"the code string was too long for a single payload. "
                        f"FIX: write in sections using Python open() with append mode:\n"
                        f"  with open(path, 'w') as f: f.write(section1)  # max ~1000 chars\n"
                        f"  with open(path, 'a') as f: f.write(section2)  # repeat as needed\n"
                        f"Also ensure you use 'code' (not 'content' or 'script') as the arg name."
                    )
                else:
                    msg = (
                        f"Tool '{tool_name}' is missing required arguments: "
                        f"{', '.join(missing)}. Retry the tool call with all required args present."
                    )
                # Log the issue
                try:
                    self.agent.context.log.log(
                        type="warning",
                        content=f"[MetaGate] {msg}"
                    )
                except Exception:
                    pass
                # Inject warning into history so model sees the problem
                try:
                    self.agent.hist_add_warning(msg)
                except Exception:
                    pass
                # Raise to abort tool execution — prevents downstream KeyError crashes.
                # A0's exception handler will add this to the retry context.
                raise ValueError(f"[MetaGate] {msg}")

        except ValueError:
            # Re-raise MetaGate abort signals — do not swallow
            raise
        except Exception as e:
            # Graceful degradation for all other MetaGate errors
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[MetaGate] Error (passthrough): {e}"
                )
            except Exception:
                pass

    def _write_limits(self, content) -> dict:
        """A3 threshold for this content. Degrades without ever blocking on its own error.

        Any failure here must not block a write: a threshold helper that raises would
        turn a size guard into an outage. So on error we still produce a limit rather
        than "no limit", and the original protection survives the profile machinery.

        The degraded path deliberately does NOT carry its own copy of the number. It used
        to hardcode 5000 inline — a second literal beside the one in write_threshold,
        free to drift from it, which is the defect class this codebase produces most
        reliably. It now reads the operator-tunable plugin config, and only falls to a
        named module constant when even that file is unreadable. `profile` reports which
        of those actually happened, so a degraded block is never mistaken for a
        configured one.
        """
        try:
            import write_threshold as wt
            return wt.describe(content if isinstance(content, str) else "", self.agent)
        except Exception as e:
            n = len(content) if isinstance(content, str) else 0
            limit, src = _backstop_limit()
            try:
                print(f"[MetaGate-SIZE] threshold helper unavailable "
                      f"({type(e).__name__}); using {src} limit {limit:,}", flush=True)
            except Exception:
                pass
            return {"length": n, "base_limit": limit, "effective_limit": limit,
                    "score": 1.0, "fenced_blocks": 0, "escape_density": 0.0,
                    "profile": f"degraded:{src}", "profile_sourced": False,
                    "over": n > limit}

    def _quarantine_gate(self, tool_name: str, tool_args: dict | None) -> None:
        """A1 enforcer. Stash the op signature, then refuse quarantined attempts.

        Raises ValueError to block, matching this file's existing block mechanism.
        Any *internal* failure here is swallowed: a broken quarantine store must
        degrade to "no quarantine", never to "no tool calls". A gate that can wedge
        the agent is worse than the failure loop it exists to stop.
        """
        try:
            import failure_fingerprint as ff

            conf = ff.cfg()
            if not conf.get("enabled", True):
                return

            op_sig = ff.op_signature(tool_name, tool_args)
            self.agent.set_data(ff.OP_SIG_KEY, op_sig)

            entry = ff.find_quarantine(op_sig)
        except Exception as e:
            try:
                print(f"[QUARANTINE] gate skipped — {type(e).__name__}: {str(e)[:100]}",
                      flush=True)
            except Exception:
                pass
            return

        if not entry:
            return

        # Outside the try: this raise is the intended control flow and must not be
        # swallowed by the handler above.
        msg = (
            f"[MetaGate-QUARANTINE] This exact call is quarantined after "
            f"{entry.get('evidence', {}).get('strikes_at_quarantine', entry.get('strikes'))} "
            f"identical failures ({entry.get('tool')}/{entry.get('error_class')}). "
            f"Retrying it will fail the same way. Do something different: change the "
            f"approach, the tool, or the target — or move on to another task. "
            f"Released automatically when the gating code or model profile changes."
        )
        try:
            self.agent.context.log.log(type="warning", content=msg)
        except Exception:
            pass
        print(f"[QUARANTINE] BLOCKED {tool_name} fp={entry.get('fingerprint')}", flush=True)
        raise ValueError(msg)

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

    def _strip_unknown_args(self, tool_args: dict, schema: dict):
        """Remove keys not in known_args for tools with complete schemas.

        Defends against local models leaking system-prompt content (datetime
        strings, injected blocks, etc.) into tool_args as garbage keys.
        Only fires when schema has strip_unknown_args=True and known_args set.
        """
        if not schema.get("strip_unknown_args"):
            return
        known = schema.get("known_args")
        if not known:
            return
        garbage = [k for k in list(tool_args.keys()) if k not in known]
        for k in garbage:
            del tool_args[k]
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[MetaGate] Stripped unrecognized arg key: {repr(k)[:120]}"
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
