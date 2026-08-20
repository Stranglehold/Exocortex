"""
_32_failure_fingerprint.py — A1 three-strike quarantine, RECORDER half

Hook: tool_execute_after
Priority: _32 — after _20_error_comprehension (sets the diagnosis) and after
          _31_failure_lesson_capture (writes the lesson skill). This extension
          only reads what _20 produced; it never re-derives a diagnosis.

WHAT THIS IS
------------
Half of A1. The other half is the ENFORCER in
`tool_execute_before/_20_meta_reasoning_gate.py`. This half records; that half
refuses. Both import `helpers/failure_fingerprint.py` so they cannot disagree
about what "the same failure" means — see that module's header for why that
matters more than it looks.

WHY THE RECORDER IS NOT IN `_20_meta_reasoning_gate.py`
------------------------------------------------------
The A1 build order said to build the quarantine in `_20_meta_reasoning_gate.py`.
That file lives at `tool_execute_before`, which fires BEFORE a tool runs and
therefore never sees a failure. Verified against A0 v2.9 `agent.py` (~L1192):

    tool_execute_before  -> tool_args, tool_name
    tool_execute_after   -> response, tool_name        (no args)

So recording has to happen here, where the failure actually arrives, and
enforcement has to happen there, where a retry can still be refused. The gate
file is right for the enforcer and wrong for the recorder. This is the same
principle that killed the auto-route design: an intervention can only live where
the failure actually arrives.

Because `tool_execute_after` gets no args, the gate stashes the op signature on
the agent (`_op_signature`) during the same turn and this extension reads it back.

WHAT IT DOES NOT DO
-------------------
- Does not block, retry, or modify the response. Recording only.
- Does not call an LLM. Deterministic hashing and counters.
- Does not duplicate `_31`'s lesson capture. `_31` writes a human-readable skill;
  this writes a machine-queryable counter with a rolling window. `_31`'s
  `.memory.md` ledger is append-only forever and has no window, which is why it
  could record 300 recurrences without ever being able to act on them.
"""

import sys

from helpers.extension import Extension

_EXOCORTEX_HELPERS = "/a0/usr/plugins/_exocortex/helpers"
if _EXOCORTEX_HELPERS not in sys.path:
    sys.path.insert(0, _EXOCORTEX_HELPERS)

DIAGNOSIS_KEY = "_error_diagnosis"     # set by _20_error_comprehension


class FailureFingerprint(Extension):
    """tool_execute_after: accumulate strikes per failure fingerprint."""

    def _log(self, msg: str) -> None:
        print(f"[QUARANTINE] {msg}", flush=True)

    async def execute(self, response=None, **kwargs) -> None:
        try:
            import failure_fingerprint as ff

            conf = ff.cfg()
            if not conf.get("enabled", True):
                return

            diag = self.agent.get_data(DIAGNOSIS_KEY)
            if not isinstance(diag, dict) or not diag.get("error_class"):
                return          # no classified failure this call — nothing to record

            tool = kwargs.get("tool_name") or "tool"
            error_class = str(diag.get("error_class"))
            message = str(diag.get("raw_output_tail") or "")
            op_sig = self.agent.get_data(ff.OP_SIG_KEY) or ""

            result = ff.record_failure(
                tool=tool,
                error_class=error_class,
                message=message,
                op_sig=op_sig,
                evidence=diag,
            )

            if result.get("invalidated"):
                self._log("gating code or model config changed — strike counts reset")

            strikes = result["strikes"]
            fp = result["fingerprint"]

            if result["quarantined"] and strikes >= int(conf["strikes_to_quarantine"]):
                self._log(
                    f"STRIKE {strikes} — QUARANTINED {tool}/{error_class} fp={fp}. "
                    f"This attempt will be refused until the fingerprint is invalidated "
                    f"(gating code change, model profile change, or explicit release)."
                )
                try:
                    self.agent.context.log.log(
                        type="warning",
                        content=(f"[QUARANTINE] {tool}/{error_class} quarantined after "
                                 f"{strikes} identical failures. Try a different approach."),
                    )
                except Exception:
                    pass
                self._file_anti_pattern(tool, error_class, strikes, diag, fp)
            elif strikes >= 2:
                self._log(f"STRIKE {strikes} — {tool}/{error_class} fp={fp} (warn)")
            else:
                self._log(f"STRIKE {strikes} — {tool}/{error_class} fp={fp}")

        except Exception as e:
            # A diagnostic must never break a turn.
            try:
                self._log(f"skipped — {type(e).__name__}: {str(e)[:100]}")
            except Exception:
                pass

    def _file_anti_pattern(self, tool: str, error_class: str, strikes: int,
                           diag: dict, fp: str) -> None:
        """Emit the quarantine as an ANTI-PATTERN so Phase 5 consumes it.

        Deliberately NOT a second consumption path in Phase 5. Phase 5 already
        ingests `type == "ANTI-PATTERN"` entries exactly-once via the
        `engine_consumed` marker; writing into that proven channel means the
        quarantine reaches the self-improvement engine with zero changes to
        Phase 5 and inherits its idempotency. Adding a parallel reader would have
        been a second producer/consumer pair to keep in sync — the thing this
        whole build is trying to stop doing.

        The `quarantine` tag is what makes it high-priority downstream: unlike a
        loop capture, this failure survived three identical attempts AND is now
        actively blocked, so it is the strongest available signal about what not
        to try.
        """
        try:
            from procedural_memory_api import ProceduralMemory  # type: ignore

            domain = "general"
            try:
                bs = self.agent.get_data("__bst_belief_state__") or {}
                domain = (bs.get("primary_domain") or "general") if isinstance(bs, dict) else "general"
            except Exception:
                pass

            check = (
                f"Do not retry {tool} in the way that produced '{error_class}' — "
                f"it failed {strikes} times identically and is quarantined. "
                f"{(diag.get('causal_chain') or '')[:120]}"
            ).strip()

            ProceduralMemory().create_anti_pattern(
                failing_tool=tool,
                domain=domain,
                consecutive=strikes,
                pre_action_check=check,
                tags=["quarantine", "three-strike", f"fp:{fp}"],
            )
            self._log(f"anti-pattern filed for Phase 5 (fp={fp}, domain={domain})")
        except Exception as e:
            self._log(f"anti-pattern filing skipped — {type(e).__name__}: {str(e)[:80]}")
