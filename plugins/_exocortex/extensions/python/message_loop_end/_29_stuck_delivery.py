"""
Stuck Delivery Recovery — Exocortex Cognitive Recovery
=======================================================
Hook: message_loop_end (_29_ — fires after backend standby at _28_, before supervisor at _50_)

Detects when the agent has completed its task but is stuck in a delivery loop — repeatedly
sending identical output because the delivery tool (code_execution_tool, etc.) keeps failing.

Agent Zero emits "You have sent the same message again. You have to do something else!" into
history when its deduplication check fires on identical consecutive output. This is the
hard signal. Two consecutive turns with this string = stuck delivery.

On detection (2 consecutive turns with the repetition signal):
  1. Sets agent._suppress_surgery_this_turn = True (supervisor reads and clears this)
  2. Injects UI-visible warning into history
  3. Injects targeted escape intervention via agent.intervention

The intervention names the response tool explicitly but does NOT name the failing tool —
Opus design decision: stay generic, the escape route is what matters.

No LLM calls. Deterministic pattern detection from history strings.
"""

import sys as _sys

_PM_PATH = "/a0/usr/plugins/_exocortex/helpers"
if _PM_PATH not in _sys.path:
    _sys.path.insert(0, _PM_PATH)

from agent import LoopData
from helpers.extension import Extension

# ── Constants ─────────────────────────────────────────────────────────────────

REPETITION_SIGNAL = "You have sent the same message again"
REPETITION_COUNT_KEY = "_delivery_repetition_count"
SUPPRESS_SURGERY_KEY = "_suppress_surgery_this_turn"

# How many consecutive turns with the repetition signal before firing
DETECTION_THRESHOLD = 2


def _repetition_signal_present(agent) -> bool:
    """Check the last 4 history messages for Agent Zero's deduplication warning."""
    try:
        hist = agent.hist
        if not hist:
            return False
        for msg in hist[-4:]:
            content = ""
            if isinstance(msg, dict):
                content = str(msg.get("content", "") or msg.get("message", "") or "")
            elif hasattr(msg, "content"):
                content = str(msg.content or "")
            elif hasattr(msg, "message"):
                content = str(msg.message or "")
            if REPETITION_SIGNAL in content:
                return True
    except Exception:
        pass
    return False


# ── Extension ─────────────────────────────────────────────────────────────────

class StuckDelivery(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        try:
            if not _repetition_signal_present(self.agent):
                # Clean turn — reset the counter
                setattr(self.agent, REPETITION_COUNT_KEY, 0)
                return

            count = getattr(self.agent, REPETITION_COUNT_KEY, 0) + 1
            setattr(self.agent, REPETITION_COUNT_KEY, count)

            print(
                f"[STUCK-DELIVERY] Repetition signal detected (turn {count}/{DETECTION_THRESHOLD}).",
                flush=True,
            )

            if count < DETECTION_THRESHOLD:
                return

            # Threshold reached — agent is in a true delivery loop
            print(
                "[STUCK-DELIVERY] Threshold reached. Suppressing surgery, injecting escape.",
                flush=True,
            )

            # Suppress Tier 2 surgery this turn — surgery removes completion evidence
            # and makes delivery loops worse. The supervisor reads and clears this flag.
            setattr(self.agent, SUPPRESS_SURGERY_KEY, True)

            # Reset the counter so we don't fire again next turn unless loop continues
            setattr(self.agent, REPETITION_COUNT_KEY, 0)

            # Inject UI-visible warning
            self.agent.hist_add_warning(
                "[STUCK DELIVERY] Agent is in a delivery loop. "
                "Suppressing context surgery. Injecting recovery intervention."
            )

            # Inject targeted intervention — names the escape hatch, not the failing tool
            from helpers.history import UserMessage
            self.agent.intervention = UserMessage(
                message=(
                    "You are repeating the same output and not making progress. "
                    "Your work is complete — the results exist. "
                    "Switch to the response tool immediately and deliver your findings "
                    "as plain text from memory. "
                    "State the file paths if you wrote files. Summarize the key findings. "
                    "Do not execute any more code or read any more files. "
                    "The only valid next action is the response tool."
                )
            )

        except Exception as e:
            print(f"[STUCK-DELIVERY] Error in stuck delivery extension: {e}", flush=True)
