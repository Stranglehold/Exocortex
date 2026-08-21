"""
Include Alias Expander — make `§§include(path)` actually reach the executed tool
================================================================================
Hook: tool_execute_before
Priority: _03 (deliberately BEFORE _20_meta_reasoning_gate — see ORDERING)

THE BUG THIS CLOSES
-------------------
A0 advertises this feature to the model in its own system prompt,
`/a0/prompts/agent.system.response_tool_tips.md` line 1, verbatim:

    "for long existing text, use `§§include(path)` instead of rewriting"

The expansion never reaches the executed tool. Traced 2026-08-21:

  helpers/strings.py:162            replace_file_includes() — EXISTS and WORKS. Run
                                    against a real 20,374-char file it expanded correctly.
  response_stream/_15_replace_include_alias.py
                                    CORRECT — walks parsed["tool_args"] recursively.
  agent.py:1535 handle_response_stream()
                                    parses the stream into a LOCAL dict, hands it to the
                                    extension as `parsed`, and then DISCARDS it. The
                                    function returns nothing.
  agent.py:457                      caller does handle_response_stream(full) then
                                    `return full.strip()` — the ORIGINAL text.

So the substitution lands on a throwaway parse built for live display, while the tool
that actually executes re-parses the original text. Producer built, consumer never wired
— the same defect class as the PTY leak, the acceptor, and _49's reasoning state.

FOUND BY APORIA, not by instrumentation. Two `text_editor:write` calls produced 94-byte
files containing the literal directive:

    §§include(/a0/usr/workdir/workspace/team-comms/to-kestrel/write-cap-test/gt_prose_20000.txt)

No error, no warning — the file just silently contained the directive instead of the
content. She used a documented feature exactly as the prompt instructs.

WHY HERE AND NOT A CORE PATCH
-----------------------------
`tool_execute_before` receives the dict that IS executed: agent.py:1199 passes
`tool_args=tool_args or {}` by reference and agent.py:1203 does
`await tool.execute(**tool_args)` on that same object. Mutating it in place propagates —
the established pattern, already used by _02, _15 and _16 for `tool_args["code"]`.

That means no A0 core modification (DEC-030 sovereignty holds) and the fix survives
upstream updates.

Known limit: agent.py passes `tool_args or {}`, so for a FALSY tool_args a fresh dict is
substituted and mutations would not propagate. Irrelevant here — a call with no arguments
has no `§§include` to expand.

ORDERING — WHY _03
------------------
_20_meta_reasoning_gate measures write size at this same hook. Expansion MUST happen
first, so the gate judges what is ACTUALLY written rather than a 94-character directive.
Expanding after the gate would let an arbitrarily large payload through unmeasured — the
gate would approve 94 chars and the tool would write 20,000.

Uses A0's own `replace_file_includes` rather than reimplementing the pattern, so the
syntax cannot drift from what the prompt advertises.

No new capability is granted: the agent can already read any of these paths through
code_execution. This only makes a documented feature behave as documented.

Reads:  tool_args (any nested string)
Writes: tool_args, in place
Log tag: [INCLUDE-03]
"""

from typing import Any

from helpers.extension import Extension

MARKER = "§§include("
PATTERN = r"§§include\(([^)]+)\)"


class IncludeAliasExpander(Extension):
    """tool_execute_before: expand §§include(path) in tool args before execution."""

    async def execute(
        self,
        tool_args: dict[str, Any] | None = None,
        tool_name: str | None = None,
        **kwargs,
    ) -> Any:
        try:
            if not tool_args or not isinstance(tool_args, dict):
                return

            # Cheap gate first — the vast majority of calls carry no directive, and
            # walking every nested value on every tool call is not free.
            if MARKER not in _flatten_probe(tool_args):
                return

            try:
                # Import files first: helpers.strings imports helpers.files at module
                # scope, and helpers.files imports back from helpers.strings. Loading
                # strings first raises ImportError on a partially initialised module.
                from helpers import files as _files  # noqa: F401
                from helpers.strings import replace_file_includes
            except Exception as e:
                print(f"[INCLUDE-03] expander unavailable ({e}); leaving args untouched",
                      flush=True)
                return

            expanded: list[str] = []

            def walk(value: Any) -> Any:
                if isinstance(value, str):
                    if MARKER not in value:
                        return value
                    out = replace_file_includes(value, PATTERN)
                    if out != value:
                        expanded.append("%d->%d chars" % (len(value), len(out)))
                    else:
                        # replace_file_includes swallows read errors and returns the
                        # placeholder unchanged. Say so rather than let it look expanded.
                        print(f"[INCLUDE-03] directive present but NOT expanded "
                              f"(unreadable path?): {value[:90]!r}", flush=True)
                    return out
                if isinstance(value, dict):
                    return {k: walk(v) for k, v in value.items()}
                if isinstance(value, list):
                    return [walk(v) for v in value]
                if isinstance(value, tuple):
                    return tuple(walk(v) for v in value)
                return value

            for key in list(tool_args.keys()):
                tool_args[key] = walk(tool_args[key])

            if expanded:
                print(f"[INCLUDE-03] expanded {len(expanded)} include(s) for "
                      f"{tool_name or '?'}: {', '.join(expanded[:3])}", flush=True)

        except Exception as e:
            # Graceful degradation — never block a tool call over this.
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[INCLUDE-03] error (passthrough): {e}",
                )
            except Exception:
                pass


def _flatten_probe(value: Any, depth: int = 0) -> str:
    """Cheap membership probe. Bounded depth so a pathological structure cannot spin."""
    if depth > 6:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return "".join(_flatten_probe(v, depth + 1) for v in value.values())
    if isinstance(value, (list, tuple)):
        return "".join(_flatten_probe(v, depth + 1) for v in value)
    return ""
