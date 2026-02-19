"""
Supervisor Loop — Agent-Zero Cognitive Architecture
====================================================
Hook: message_loop_end (_50_)

XO supervisory function: monitors operational state, detects anomalies
(stalls, loops, context exhaustion, cascading failures), and injects
corrective steering via hist_add_warning().

Runs in the finally block of every message loop iteration, after history
organization (_10_). Read-only on all state except history injection.

Requires active organization — returns immediately when org kernel is off.
"""

from typing import Any

from agent import LoopData
from python.helpers.extension import Extension

# ── Constants ────────────────────────────────────────────────────

# Agent attribute keys (verified from _12_org_dispatcher.py)
ACTIVE_ROLE_KEY = "_org_active_role"
PACE_LEVEL_KEY = "_org_pace_level"
HTN_STATE_KEY = "_htn_state"
TOOL_FAILURES_KEY = "_tool_failures"
BST_STORE_KEY = "_bst_store"
BST_BELIEF_KEY = "__bst_belief_state__"

# Supervisor's own state key
SUPERVISOR_STATE_KEY = "_supervisor_state"

# Default check interval (every N iterations)
DEFAULT_CHECK_INTERVAL = 3

# Cooldown: minimum turns between same-type steering injections
DEFAULT_COOLDOWN = 3

# Context exhaustion threshold (90% only — watchdog already warns at 70%/85%)
CONTEXT_CRITICAL_THRESHOLD = 0.90

# Loop detection: minimum repetitions of same pattern
LOOP_DETECTION_THRESHOLD = 3

# Cascade detection: N different tools failing in last M history entries
CASCADE_TOOL_COUNT = 3
CASCADE_WINDOW = 5

# Anomaly types for cooldown tracking
ANOMALY_STALL = "stall"
ANOMALY_LOOP = "loop"
ANOMALY_CONTEXT = "context"
ANOMALY_CASCADE = "cascade"
ANOMALY_PACE = "pace"


class SupervisorLoop(Extension):
    """XO supervisory loop — anomaly detection and steering injection."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
        try:
            # Only run when an organization is active
            role = getattr(self.agent, ACTIVE_ROLE_KEY, None)
            if not role:
                return  # No org — zero overhead passthrough

            # Get or initialize supervisor state
            state = _get_state(self.agent)
            state["turn"] = state.get("turn", 0) + 1

            # Check interval — run checks every N turns
            interval = DEFAULT_CHECK_INTERVAL
            if state["turn"] % interval != 0:
                _set_state(self.agent, state)
                return

            # Read operational context
            ctx = _gather_context(self.agent, role)

            # Run anomaly detectors (order: most severe first)
            injected = False

            # 1. PACE escalation response (emergency exempt from cooldown)
            if ctx["pace_level"] == "emergency":
                _inject_pace_emergency(self.agent, role, ctx, state)
                injected = True
            elif ctx["pace_level"] == "contingent":
                if _cooldown_ok(state, ANOMALY_PACE):
                    _inject_pace_contingent(self.agent, role, ctx, state)
                    injected = True

            # 2. Cascade failure detection
            if not injected and _cooldown_ok(state, ANOMALY_CASCADE):
                if _detect_cascade(ctx):
                    _inject_cascade(self.agent, state)
                    injected = True

            # 3. Context exhaustion (only 90%+ — watchdog handles 70%/85%)
            if not injected and _cooldown_ok(state, ANOMALY_CONTEXT):
                if _detect_context_exhaustion(self.agent, ctx):
                    _inject_context_warning(self.agent, ctx, state)
                    injected = True

            # 4. Stall detection
            if not injected and _cooldown_ok(state, ANOMALY_STALL):
                if _detect_stall(ctx, role):
                    _inject_stall(self.agent, ctx, role, state)
                    injected = True

            # 5. Loop detection
            if not injected and _cooldown_ok(state, ANOMALY_LOOP):
                if _detect_loop(ctx):
                    _inject_loop(self.agent, state)
                    injected = True

            _set_state(self.agent, state)

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[SUPERVISOR] Error (passthrough): {e}"
                )
            except Exception:
                pass


# ── State Management ─────────────────────────────────────────────

def _get_state(agent) -> dict:
    try:
        state = getattr(agent, SUPERVISOR_STATE_KEY, None)
        if state is None:
            state = {"turn": 0, "cooldowns": {}}
        return state
    except Exception:
        return {"turn": 0, "cooldowns": {}}


def _set_state(agent, state: dict):
    setattr(agent, SUPERVISOR_STATE_KEY, state)


# ── Cooldown Management ─────────────────────────────────────────

def _cooldown_ok(state: dict, anomaly_type: str) -> bool:
    """Check if the cooldown period has elapsed for this anomaly type."""
    cooldowns = state.get("cooldowns", {})
    last_turn = cooldowns.get(anomaly_type, 0)
    current_turn = state.get("turn", 0)
    return (current_turn - last_turn) >= DEFAULT_COOLDOWN


def _mark_cooldown(state: dict, anomaly_type: str):
    """Record that we just injected a steering message for this anomaly type."""
    if "cooldowns" not in state:
        state["cooldowns"] = {}
    state["cooldowns"][anomaly_type] = state.get("turn", 0)


# ── Context Gathering ───────────────────────────────────────────

def _gather_context(agent, role: dict) -> dict:
    """Read all operational state into a single dict. Defensive on every read."""
    ctx = {
        "pace_level": "primary",
        "htn_state": None,
        "turns_since_progress": 0,
        "htn_plan_name": "",
        "htn_current_step": 0,
        "htn_total_steps": 0,
        "bst_domain": "",
        "tool_failures": None,
        "failure_history": [],
        "max_consecutive_failures": 0,
        "context_fill": 0.0,
    }

    # PACE level
    try:
        ctx["pace_level"] = getattr(agent, PACE_LEVEL_KEY, "primary") or "primary"
    except Exception:
        pass

    # HTN state
    try:
        htn = getattr(agent, HTN_STATE_KEY, None)
        if htn:
            ctx["htn_state"] = htn
            ctx["turns_since_progress"] = htn.get("turns_since_progress", 0)
            ctx["htn_plan_name"] = htn.get("plan_name", "")
            ctx["htn_current_step"] = htn.get("current_step", 0)
            ctx["htn_total_steps"] = htn.get("total_steps", 0)
    except Exception:
        pass

    # BST domain
    try:
        store = getattr(agent, BST_STORE_KEY, {})
        belief = store.get(BST_BELIEF_KEY, {})
        ctx["bst_domain"] = belief.get("domain", "")
    except Exception:
        pass

    # Tool failures
    try:
        failures = agent.get_data(TOOL_FAILURES_KEY) or {}
        ctx["tool_failures"] = failures
        ctx["failure_history"] = failures.get("history", [])
        consecutive = failures.get("consecutive", {})
        ctx["max_consecutive_failures"] = max(consecutive.values()) if consecutive else 0
    except Exception:
        pass

    # Context fill — read from agent's ctx_window data (same source as context watchdog)
    try:
        from agent import Agent
        ctx_window = agent.get_data(Agent.DATA_NAME_CTX_WINDOW) or {}
        tokens = ctx_window.get("tokens", 0)
        window_size = agent.get_data("context_window_size") or 100000
        if tokens and window_size:
            ctx["context_fill"] = tokens / window_size
    except Exception:
        pass

    return ctx


# ── Anomaly Detection ───────────────────────────────────────────

def _detect_stall(ctx: dict, role: dict) -> bool:
    """Detect if the agent is stalled (no progress for too long)."""
    if not ctx["htn_state"]:
        return False
    max_turns = role.get("doctrine", {}).get("max_turns_without_progress", 12)
    return ctx["turns_since_progress"] >= max_turns


def _detect_loop(ctx: dict) -> bool:
    """Detect behavioral loops — same tool+error repeated 3+ times in recent history."""
    history = ctx.get("failure_history", [])
    if len(history) < LOOP_DETECTION_THRESHOLD:
        return False

    recent = history[-LOOP_DETECTION_THRESHOLD:]

    # Pattern 1: Same tool + same error type repeated
    if len(recent) >= LOOP_DETECTION_THRESHOLD:
        first = (recent[0].get("tool", ""), recent[0].get("error_type", ""))
        if all(
            (e.get("tool", ""), e.get("error_type", "")) == first
            for e in recent
        ):
            return True

    # Pattern 2: Oscillation — A, B, A, B pattern
    if len(history) >= 4:
        last4 = history[-4:]
        pair_a = (last4[0].get("tool", ""), last4[0].get("error_type", ""))
        pair_b = (last4[1].get("tool", ""), last4[1].get("error_type", ""))
        if pair_a != pair_b:
            if (last4[2].get("tool", ""), last4[2].get("error_type", "")) == pair_a and \
               (last4[3].get("tool", ""), last4[3].get("error_type", "")) == pair_b:
                return True

    return False


def _detect_context_exhaustion(agent, ctx: dict) -> bool:
    """Detect context exhaustion at 90%+ (watchdog already handles 70%/85%)."""
    return ctx["context_fill"] >= CONTEXT_CRITICAL_THRESHOLD


def _detect_cascade(ctx: dict) -> bool:
    """Detect cascade failure — 3+ different tools failing in the last 5 entries."""
    history = ctx.get("failure_history", [])
    if len(history) < CASCADE_TOOL_COUNT:
        return False

    recent = history[-CASCADE_WINDOW:]
    distinct_tools = set(e.get("tool", "") for e in recent if e.get("tool"))
    return len(distinct_tools) >= CASCADE_TOOL_COUNT


# ── Steering Injection ──────────────────────────────────────────

def _inject_stall(agent, ctx: dict, role: dict, state: dict):
    """Inject stall warning with task-specific context."""
    task_info = ""
    if ctx["htn_plan_name"]:
        task_info = f" on plan '{ctx['htn_plan_name']}' (step {ctx['htn_current_step'] + 1}/{ctx['htn_total_steps']})"
    elif ctx["bst_domain"]:
        task_info = f" in domain '{ctx['bst_domain']}'"

    msg = (
        f"[SUPERVISOR] You appear stalled{task_info} — "
        f"no progress for {ctx['turns_since_progress']} turns. "
        f"Reassess your approach: try a different method, simplify the task, or ask the user for guidance."
    )
    _emit(agent, msg, ANOMALY_STALL, state)


def _inject_loop(agent, state: dict):
    """Inject loop detection warning."""
    msg = (
        "[SUPERVISOR] You are repeating the same failing action. "
        "Stop and try a fundamentally different approach — different tool, different path, or different strategy."
    )
    _emit(agent, msg, ANOMALY_LOOP, state)


def _inject_context_warning(agent, ctx: dict, state: dict):
    """Inject context exhaustion warning at 90%+."""
    pct = round(ctx["context_fill"] * 100)
    msg = (
        f"[SUPERVISOR] Context window is {pct}% full. "
        f"Complete your immediate task and respond to the user. Do not start new subtasks."
    )
    _emit(agent, msg, ANOMALY_CONTEXT, state)


def _inject_cascade(agent, state: dict):
    """Inject cascade failure warning."""
    msg = (
        "[SUPERVISOR] Multiple different tools are failing. "
        "Stop executing and verify your assumptions: correct directory, correct file paths, correct environment state."
    )
    _emit(agent, msg, ANOMALY_CASCADE, state)


def _inject_pace_contingent(agent, role: dict, ctx: dict, state: dict):
    """Inject PACE contingent-level guidance."""
    pace_desc = role.get("pace_plan", {}).get("contingent", {}).get("description", "")
    hint = f" Role guidance: {pace_desc}" if pace_desc else ""
    msg = (
        f"[SUPERVISOR] PACE level is CONTINGENT — your current approach has failed repeatedly.{hint} "
        f"Try a fundamentally different method or ask the user for guidance."
    )
    _emit(agent, msg, ANOMALY_PACE, state)


def _inject_pace_emergency(agent, role: dict, ctx: dict, state: dict):
    """Inject PACE emergency-level guidance. Always fires (no cooldown)."""
    pace_desc = role.get("pace_plan", {}).get("emergency", {}).get("description", "")
    hint = f" Role guidance: {pace_desc}" if pace_desc else ""
    msg = (
        f"[SUPERVISOR] PACE level is EMERGENCY — stop all work immediately.{hint} "
        f"Preserve any partial results and report what you've accomplished and where you're stuck."
    )
    # Emergency is exempt from cooldown — always inject
    try:
        agent.hist_add_warning(msg)
        agent.context.log.log(type="warning", content=msg)
    except Exception:
        pass
    _mark_cooldown(state, ANOMALY_PACE)


def _emit(agent, msg: str, anomaly_type: str, state: dict):
    """Inject steering message and mark cooldown."""
    try:
        agent.hist_add_warning(msg)
        agent.context.log.log(type="info", content=msg)
    except Exception:
        pass
    _mark_cooldown(state, anomaly_type)
