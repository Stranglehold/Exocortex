"""
Prose Leak Detector
===================
Hook: _functions/agent/Agent/process_tools/start
Priority: _05 — deliberately BEFORE _10_plaintext_response_fallback. See ORDERING.

Detects a VALID tool call that the model wrapped in prose, and nudges specifically
instead of letting it be mis-diagnosed or recited aloud.

THE MEASUREMENT BEHIND THIS
---------------------------
2026-08-22. Asked for a 32K escape-dense file, qwen3.8-27b emitted a complete valid tool
call — 37,422 bytes, all 243 requested blocks — and prefixed it with "I'll write out
blocks 1..243. Let me go." A0 v2.9's `extract_tool_request` requires
`root == content`, so the entire call was discarded. `is_misformatted_tool_request`
returns False on it (its thoughts-leak branch needs `content.endswith("}")`), so it landed
in the gap between the two detectors and `_10` claimed it:

    [PLAINTEXT-FB] wrapped 52943 chars of prose as a response tool call

The agent recited a 37KB tool call to the user instead of writing the file.

WHY THE PROSE IS NOT THE BUG
----------------------------
"Capacity, Not Format" (arXiv:2606.09410) — "performance recovers whenever unconstrained
reasoning precedes structured submission." DCCD (arXiv:2603.03305) builds a decoding
scheme on it: draft freely, then serialise. The model reasoning before emitting JSON is
optimal behaviour. The strict parser punishes it, so the correct response is to ask for a
clean re-send, not to tell the model its JSON is broken.

ORDERING — WHY _05
------------------
_10 fires on "non-empty AND not a valid tool request AND not misformatted". A prose-wrapped
call satisfies all three EXACTLY, so _10 is a superset of this case and would claim it
first. This must run before _10, and _10 defers on the shared flag.

Both files import HANDLED_KEY from helpers/prose_leak.py rather than repeating a literal —
a mismatched string in either half leaves the mechanism inert while looking installed.

WHAT THIS DOES NOT DO
---------------------
Does NOT extract and execute the recovered call, even though the valid root is right there.
Opus's call 2026-08-22: v2.9 made the parser strict deliberately, to avoid firing a call
the model merely DESCRIBED inside an explanation. Nudge-only until there is
nudge-acceptance data. Revisit after ~100 cycles.

Does NOT modify the message. The turn proceeds exactly as it would have; the only change
is that the model receives an accurate correction and _10 stops reciting the payload.

Reads:  data["args"] / data["kwargs"] (the `msg` argument)
Writes: agent data flag HANDLED_KEY; a history warning
Log tag: [PROSE-LEAK]
"""

import sys

_HELPERS = "/a0/usr/plugins/_exocortex/helpers"
if _HELPERS not in sys.path:
    sys.path.insert(0, _HELPERS)

from helpers.extension import Extension

try:
    import prose_leak as pl
except Exception:  # pragma: no cover — helper missing
    pl = None  # type: ignore[assignment]


class ProseLeakDetector(Extension):
    """process_tools/start: catch a valid tool call wrapped in prose."""

    def _log(self, message: str) -> None:
        print(f"[PROSE-LEAK] {message}", flush=True)

    async def execute(self, data: dict | None = None, **kwargs) -> None:
        try:
            if pl is None or not isinstance(data, dict):
                return

            # Clear last turn's flag first. A stale True would make _10 defer on a
            # message that never leaked — silently disabling the prose fallback.
            try:
                self.agent.set_data(pl.HANDLED_KEY, False)
            except Exception:
                pass

            msg, _where, _index = pl.read_msg(data)
            hit = pl.find_leaked_call(msg)
            if not hit:
                return

            self._log(
                f"valid {hit['tool_name'] or 'tool'} call wrapped in "
                f"{hit['surrounding']:,} chars of prose — nudging for a clean re-send "
                f"(root {len(hit['root']):,} chars)"
            )

            # Tell _10 to stand down BEFORE anything that can fail, so a failure in the
            # warning path cannot leave _10 free to recite the payload.
            self.agent.set_data(pl.HANDLED_KEY, True)

            try:
                self.agent.hist_add_warning(pl.nudge_text(hit))
            except Exception as exc:
                self._log(f"warning injection failed: {type(exc).__name__}: {exc}")

        except Exception as exc:  # never break the turn
            self._log(f"passthrough after error: {type(exc).__name__}: {exc}")
