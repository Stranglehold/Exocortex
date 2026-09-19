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

WHAT THIS NOW DOES (REVISED 2026-09-17, Opus)
----------------------------------------------
For UNAMBIGUOUS cases (one call, prose only before it): extracts the valid tool call root,
rewrites `msg` so `process_tools` sees clean JSON, and lets A0 execute it. The prose
preamble is stripped. This is the "Capacity, Not Format" pattern: reasoning followed by
structured output.

For AMBIGUOUS cases (prose after the call, or multiple calls): nudge only, as before.

History: Opus's original call (2026-08-22) was nudge-only for all cases, pending
nudge-acceptance data. Data now in: Ornith's nudge acceptance rate is near zero over
cycles 513–640+. Three turns in Jake's "Workspace Scripts" chat (2026-09-17) produced
valid tool calls that the nudge loop silently discarded, leaving empty responses. The
`unambiguous` field in `survey_leaked_calls` was designed for exactly this transition.

Does NOT modify the message for ambiguous cases. The nudge is accurate and _10 defers.

ATTENDEDNESS — WHY THERE IS NO GATE (Opus, 2026-09-17)
------------------------------------------------------
Extraction runs in both attended and unattended (idle cycle) turns. This looks inconsistent
with _07 (repair_unterminated_string), which refuses to execute a recovered call when
unattended. The distinction is deliberate: _07 RECONSTRUCTS a call from a damaged payload
(guessing the closing structure), where the risk is executing something the model did not
quite emit. _05 takes a call the model DEFINITELY emitted, verbatim, and strips surrounding
text. `unambiguous` is the safety gate — one call, prose only before it, whitespace only
after. Different risks, different gates. (Named by Kestrel, confirmed by Opus.)

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

            msg, where, index = pl.read_msg(data)

            survey = pl.survey_leaked_calls(msg)
            if not survey:
                return

            first = survey["calls"][0]
            tool_name = first.get("tool_name") or "tool"
            root = first["root"]
            surrounding = survey["surrounding"]

            # Tell _10 to stand down BEFORE anything that can fail, so a failure in the
            # extraction or warning path cannot leave _10 free to recite the payload.
            self.agent.set_data(pl.HANDLED_KEY, True)

            if survey["unambiguous"]:
                # SAFE TO EXTRACT: exactly one call, prose only before it. This is the
                # "Capacity, Not Format" pattern — reasoning then structured output.
                # Rewrite msg to just the valid root; process_tools sees clean JSON.
                self._log(
                    f"valid {tool_name} call with {surrounding:,} chars of preamble "
                    f"— extracting (root {len(root):,} chars)"
                )
                try:
                    pl.write_msg(data, where, index, root)
                except Exception as exc:
                    self._log(f"extraction write failed: {type(exc).__name__}: {exc}")
            else:
                # AMBIGUOUS: prose after the call, or multiple calls. Nudge only.
                self._log(
                    f"valid {tool_name} call wrapped in "
                    f"{surrounding:,} chars of prose — nudging for a clean re-send "
                    f"(root {len(root):,} chars)"
                )
                try:
                    hit = {"tool_name": tool_name, "surrounding": surrounding}
                    self.agent.hist_add_warning(pl.nudge_text(hit))
                except Exception as exc:
                    self._log(f"warning injection failed: {type(exc).__name__}: {exc}")

        except Exception as exc:  # never break the turn
            self._log(f"passthrough after error: {type(exc).__name__}: {exc}")
