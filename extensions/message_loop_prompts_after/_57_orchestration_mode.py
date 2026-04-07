"""
Orchestration Mode — Per-Turn Delegation Scaffolding
=====================================================
Hook: message_loop_prompts_after (confirmed working in V1.7 — T4 2026-04-06)
Slot: _57_ (between memory enhancement _56_ and ontology query _58_)

Problem
-------
The main agent attempts complex multi-phase tasks by executing tool calls directly
instead of delegating to subordinate agents via call_subordinate. This causes
context to fill, compression to trigger, and verbatim-repeat loops at step 90+.

An existing _17_orchestration_gate.py in before_main_llm_call addresses this but
is in the wrong hook — V1.7 discards all history_output modifications made in
before_main_llm_call before prepare_prompt() fires. This extension supersedes it
using the correct hook.

What this does
--------------
1. Reads BST complexity from _bst_store["_complexity"] (set by _11_belief_state_tracker)
2. When complexity == "complex_build", activates orchestration mode
3. Injects a phase-aware block into the last user message every turn:
   - planning phase: full scaffolding with call_subordinate format
   - executing phase: short reminder with delegation count
4. Deactivates when response tool fires or task domain shifts

State lives on agent._orch_state (survives context compression).

No model calls. No config required. Deterministic.
Log tag: [ORCH-MODE]
"""

import json
import re
from typing import Optional

from agent import LoopData
from helpers.extension import Extension

# ── Constants ──────────────────────────────────────────────────────────────────

BST_STORE_KEY  = "_bst_store"
ORCH_STATE_KEY = "_orch_state"

# Step threshold: <= this means agent hasn't done real work yet → planning phase
# > this means already mid-task → go straight to executing (don't disrupt good work)
PLANNING_STEP_THRESHOLD = 2

# Number of recent AI messages to scan when detecting delegation/response
HISTORY_SCAN_WINDOW = 5

DEFAULT_STATE: dict = {
    "phase": "inactive",       # inactive | planning | executing
    "original_task": "",
    "turn_activated": 0,
    "delegation_count": 0,
}


# ── Extension ──────────────────────────────────────────────────────────────────

class OrchestrationMode(Extension):
    """Inject per-turn delegation scaffolding for complex multi-phase tasks."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            state = self._get_state()
            history = loop_data.history_output or []

            # ── Check for deactivation conditions ─────────────────────────
            if state["phase"] != "inactive":
                if _response_tool_fired(history, HISTORY_SCAN_WINDOW):
                    self._deactivate("response tool detected")
                    return
                # Domain no longer complex — deactivate quietly
                _, _, complexity = _get_bst(self.agent)
                if complexity == "simple":
                    self._deactivate("domain complexity dropped")
                    return

            # ── Track delegation count ─────────────────────────────────────
            if state["phase"] != "inactive":
                if _last_ai_used_tool(history, "call_subordinate"):
                    state["delegation_count"] += 1
                    self._save_state(state)

            # ── Phase transitions ──────────────────────────────────────────
            if state["phase"] == "inactive":
                domain, confidence, complexity = _get_bst(self.agent)
                if complexity != "complex_build":
                    return
                if confidence < 1:
                    return  # Need at least 1 matched signal

                step = _get_step(self.agent)
                if step <= PLANNING_STEP_THRESHOLD:
                    state["phase"] = "planning"
                else:
                    state["phase"] = "executing"

                state["original_task"] = _get_user_text(history)
                state["turn_activated"] = step
                state["delegation_count"] = 0
                self._save_state(state)
                print(
                    f"[ORCH-MODE] Activated: phase={state['phase']} "
                    f"domain={domain} complexity={complexity} step={step}",
                    flush=True,
                )

            elif state["phase"] == "planning":
                # Transition to executing once the agent has delegated anything
                if _delegation_in_window(history, HISTORY_SCAN_WINDOW):
                    state["phase"] = "executing"
                    self._save_state(state)
                    print("[ORCH-MODE] Transition: planning → executing", flush=True)

            # ── Build and inject block ─────────────────────────────────────
            block = _build_block(state)
            user_msg = _get_last_user_message(history)
            if not user_msg:
                return

            existing = user_msg.get("content", "")
            user_msg["content"] = block + "\n\n" + str(existing)

            print(
                f"[ORCH-MODE] Injected {state['phase']} block "
                f"(delegations={state['delegation_count']})",
                flush=True,
            )

        except Exception as e:
            print(f"[ORCH-MODE] error (passthrough): {e}", flush=True)

    # ── State management ──────────────────────────────────────────────────

    def _get_state(self) -> dict:
        state = getattr(self.agent, ORCH_STATE_KEY, None)
        if not isinstance(state, dict):
            state = dict(DEFAULT_STATE)
            setattr(self.agent, ORCH_STATE_KEY, state)
        return state

    def _save_state(self, state: dict) -> None:
        setattr(self.agent, ORCH_STATE_KEY, state)

    def _deactivate(self, reason: str) -> None:
        state = dict(DEFAULT_STATE)
        setattr(self.agent, ORCH_STATE_KEY, state)
        print(f"[ORCH-MODE] Deactivated: {reason}", flush=True)


# ── Block builder ──────────────────────────────────────────────────────────────

def _build_block(state: dict) -> str:
    phase = state["phase"]
    delegations = state["delegation_count"]

    if phase == "planning":
        return (
            "[ORCHESTRATION MODE — PLANNING]\n"
            "Task complexity: multi-phase build. Your role is ORCHESTRATION, not execution.\n"
            "\n"
            "Before writing any code or files:\n"
            "1. List all subtasks in your thoughts as a numbered sequence\n"
            "2. Delegate SUBTASK 1 immediately via call_subordinate:\n"
            '   tool_name: "call_subordinate"\n'
            '   message:   "<focused, bounded task for the subordinate>"\n'
            '   agent_name: "developer"\n'
            "3. After subordinate returns, delegate SUBTASK 2, then SUBTASK 3, etc.\n"
            "\n"
            "Do NOT use code_execution_tool or text_editor this turn.\n"
            "Subordinates handle execution. You handle sequencing.\n"
            "[/ORCHESTRATION MODE]"
        )
    else:  # executing
        if delegations == 0:
            reminder = "Call the first subtask via call_subordinate now."
        elif delegations == 1:
            reminder = f"1 subtask delegated. Call the next subtask via call_subordinate."
        else:
            reminder = f"{delegations} subtasks delegated. Continue with the next via call_subordinate."
        return (
            f"[ORCHESTRATION MODE — EXECUTING]\n"
            f"{reminder}\n"
            f"Do not implement directly — delegate to call_subordinate.\n"
            f"[/ORCHESTRATION MODE]"
        )


# ── BST reader ─────────────────────────────────────────────────────────────────

def _get_bst(agent) -> tuple[str, int, str]:
    """Return (domain, confidence, complexity) from BST store."""
    try:
        store = getattr(agent, BST_STORE_KEY, None) or {}
        domain     = store.get("_compound_sig", "conversation").split("+")[0]
        complexity = store.get("_complexity", "simple")
        # Read confidence from extras_persistent if available
        ep = {}
        try:
            # LoopData not available here — read compound from store via belief key
            belief_key = "__bst_belief_state__"
            belief = store.get(belief_key)
            if isinstance(belief, dict):
                primary = belief.get("primary") or {}
                domain      = primary.get("domain", domain)
                confidence  = int(primary.get("confidence") or 0)
                return domain, confidence, complexity
        except Exception:
            pass
        return domain, 1, complexity
    except Exception:
        return "conversation", 0, "simple"


# ── History helpers ────────────────────────────────────────────────────────────

def _get_last_user_message(history: list) -> Optional[dict]:
    for msg in reversed(history):
        if isinstance(msg, dict) and not msg.get("ai", True):
            content = msg.get("content", "")
            if content:
                return msg
    return None


def _get_user_text(history: list) -> str:
    msg = _get_last_user_message(history)
    if not msg:
        return ""
    content = msg.get("content", "")
    if isinstance(content, dict):
        return content.get("user_message", "") or str(content)
    return str(content)[:200]  # cap for storage


def _parse_tool_name(content) -> str:
    """Extract tool_name from AI message content."""
    if isinstance(content, dict):
        return content.get("tool_name", "")
    if isinstance(content, str) and "{" in content:
        try:
            data = json.loads(content.strip())
            if isinstance(data, dict):
                return data.get("tool_name", "")
        except Exception:
            pass
        m = re.search(r'"tool_name"\s*:\s*"([^"]+)"', content)
        if m:
            return m.group(1)
    return ""


def _last_ai_used_tool(history: list, tool_name: str) -> bool:
    """True if the most recent AI message used the given tool."""
    for msg in reversed(history):
        if isinstance(msg, dict) and msg.get("ai", True):
            if _parse_tool_name(msg.get("content", "")) == tool_name:
                return True
            break  # Only check most recent AI message
    return False


def _delegation_in_window(history: list, window: int) -> bool:
    """True if call_subordinate appears in recent AI messages."""
    ai_msgs = [m for m in history if isinstance(m, dict) and m.get("ai", True)]
    recent = ai_msgs[-window:] if len(ai_msgs) > window else ai_msgs
    for msg in recent:
        if _parse_tool_name(msg.get("content", "")) == "call_subordinate":
            return True
    return False


def _response_tool_fired(history: list, window: int) -> bool:
    """True if the response tool appears in recent AI messages."""
    ai_msgs = [m for m in history if isinstance(m, dict) and m.get("ai", True)]
    recent = ai_msgs[-window:] if len(ai_msgs) > window else ai_msgs
    for msg in recent:
        if _parse_tool_name(msg.get("content", "")) == "response":
            return True
    return False


def _get_step(agent) -> int:
    """Get current step count from agent attributes."""
    # Try common attribute names used by A0 for step tracking
    for attr in ("_step", "step", "_loop_step", "loop_step"):
        val = getattr(agent, attr, None)
        if isinstance(val, int):
            return val
    # Try agent data dict
    try:
        val = agent.get_data("_step")
        if isinstance(val, int):
            return val
    except Exception:
        pass
    return 0
