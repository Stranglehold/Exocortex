"""
Supervisor Loop — Agent-Zero Cognitive Architecture
====================================================
Hook: message_loop_end (_50_)

XO supervisory function: monitors operational state, detects anomalies
(stalls, loops, context exhaustion, cascading failures), and injects
corrective steering via hist_add_warning().

Runs in the finally block of every message loop iteration, after history
organization (_10_). Read-only on all state except history injection.

Loop/cascade/context detection runs always. PACE and stall detection require
an active organization (they depend on HTN state and PACE level).
"""

from typing import Any

import sys as _sys
_PM_PATH = "/a0/usr/Exocortex"
if _PM_PATH not in _sys.path:
    _sys.path.insert(0, _PM_PATH)

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

# Graduated tier thresholds — defaults, used by DOMAIN_THRESHOLDS["default"]
WARN_THRESHOLD      = 3   # Tier 1: warn (existing behavior)
SUMMARIZE_THRESHOLD = 6   # Tier 2: context surgery
RESET_THRESHOLD     = 9   # Tier 3: circuit breaker — forced response

# Direction A: Domain-aware threshold profiles.
# Structural domains (codegen, debugging, system_admin) involve repeated failures
# by design — that's the mechanism of the work, not evidence of being stuck.
# Exploratory domains (research, analysis, investigation) should escalate faster.
# Compound domains (e.g. "codegen+debugging") use the most permissive profile.
DOMAIN_THRESHOLDS = {
    "codegen":        {"tier1": 6,  "tier2": 12, "tier3": 18},
    "debugging":      {"tier1": 6,  "tier2": 12, "tier3": 18},
    "system_admin":   {"tier1": 6,  "tier2": 12, "tier3": 18},
    "research":       {"tier1": 3,  "tier2": 6,  "tier3": 12},
    "analysis":       {"tier1": 3,  "tier2": 6,  "tier3": 12},
    "investigation":  {"tier1": 3,  "tier2": 6,  "tier3": 12},
    "agentic":        {"tier1": 4,  "tier2": 8,  "tier3": 15},
    "meta_cognitive": {"tier1": 4,  "tier2": 8,  "tier3": 15},
    "default":        {"tier1": 3,  "tier2": 6,  "tier3": 9},
}

# Direction B: Minimum unique error types required to suppress Tier 2+ escalation.
# If the agent is hitting 3+ distinct error types across consecutive failures,
# it is iterating (learning from each failure), not stuck in a loop.
# Genuine loops produce the same error repeatedly (1-2 unique types).
DIVERSITY_SUPPRESS_THRESHOLD = 3

# Loop episode state keys (stored in supervisor state dict)
LOOP_TIER_KEY         = "loop_tier"           # "none"|"warn"|"summarize"|"reset"
LOOP_TOOL_KEY         = "loop_failing_tool"   # str | None
LOOP_START_IDX_KEY    = "loop_start_msg_idx"  # int: topic.messages index at episode start
LOOP_SURGERY_DONE_KEY = "loop_surgery_done"   # bool: Tier 2 fired for this episode
LOOP_RESET_DONE_KEY   = "loop_reset_done"     # bool: Tier 3 fired for this episode

# Cascade detection: N different tools failing in last M history entries
CASCADE_TOOL_COUNT = 3
CASCADE_WINDOW = 5

# Anomaly types for cooldown tracking
ANOMALY_STALL = "stall"
ANOMALY_LOOP = "loop"
ANOMALY_CONTEXT = "context"
ANOMALY_CASCADE = "cascade"
ANOMALY_PACE = "pace"
ANOMALY_STAGNATION = "stagnation"

# Stagnation detection: successful-execution-no-progress (Finding 2, Session 055).
# Fires when N+ successful tool calls in a window produce identical output hashes.
STAGNATION_WINDOW = 4          # Rolling window of recent tool outputs to examine
STAGNATION_MIN_SUCCESSES = 3   # Minimum successful calls needed to evaluate
STAGNATION_MAX_UNIQUE = 2      # Max unique output hashes before stagnation is declared

# Lenz's law: opposing approaches indexed by tool name.
# When a loop is detected, the injection names the closed strategy
# and provides the orthogonal alternative — not generic "try something else"
# but the specific complement to what failed.
LOOP_ALTERNATIVES = {
    "document_query": [
        "Use code_execution_tool to read the file directly (cat, head, less)",
        "Use search_engine with different query terms or broader scope",
        "Ask the user for the correct file path or location",
    ],
    "search_engine": [
        "Use document_query to search specific files by path",
        "Navigate directly to the file via code_execution_tool",
        "Reduce query scope or try different terminology",
    ],
    "code_execution_tool": [
        "Verify the path exists before executing",
        "Break the command into smaller steps and test each",
        "Check syntax and imports in isolation before running full code",
        "Test with a minimal example to isolate the failure",
        "Verify dependencies are installed (pip list, import check)",
        "Check permissions or environment state first",
    ],
    "call_subordinate": [
        "Handle the subtask directly rather than delegating",
        "Decompose the task differently before re-delegating",
        "Report current state to the user and ask for guidance",
    ],
    "response": [
        "Use a different tool to complete the underlying task first",
        "Report partial progress and ask the user how to proceed",
    ],
}

DEFAULT_ALTERNATIVES = [
    "try a fundamentally different tool for this task",
    "simplify the task into smaller verifiable steps",
    "report current progress and ask the user for guidance",
]

LOOP_ALTERNATIVES["response_format"] = [
    "Output ONLY a valid JSON object with thoughts, tool_name, and tool_args fields",
    "Use the response tool to report current progress if unsure what to do next",
    "Simplify the response — no markdown, no <analysis> tags, just the JSON object",
]


class SupervisorLoop(Extension):
    """XO supervisory loop — anomaly detection and steering injection."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
        try:
            # Org state — may be None. Loop/cascade/context run regardless.
            # PACE and stall require org context.
            role = getattr(self.agent, ACTIVE_ROLE_KEY, None)
            org_active = bool(role)

            # Get or initialize supervisor state
            state = _get_state(self.agent)
            state["turn"] = state.get("turn", 0) + 1

            # Check interval — run checks every N turns
            interval = DEFAULT_CHECK_INTERVAL
            if state["turn"] % interval != 0:
                _set_state(self.agent, state)
                return

            # Read operational context
            ctx = _gather_context(self.agent, role or {})

            # Direction A: select domain-aware thresholds from BST classification.
            # Direction A+: effective domain override from behavioral signals (Finding 1).
            # The supervisor maintains its own observation loop — when BST intent-label
            # diverges from actual execution pattern, trust the behavioral signal.
            bst_domain = ctx.get("bst_domain", "")
            effective_domain = _get_effective_domain(bst_domain, ctx.get("failure_history", []))
            if effective_domain != bst_domain and effective_domain:
                try:
                    self.agent.context.log.log(
                        type="info",
                        content=f"[SUPERVISOR] Effective domain override: BST={bst_domain or 'none'} → {effective_domain}",
                        flush=True,
                    )
                except Exception:
                    pass
            thresholds = _get_domain_thresholds(effective_domain)

            # Run anomaly detectors (order: most severe first)
            # ── Graduated loop tier detection ─────────────────────────────────────
            consecutive, failing_tool = _get_loop_metrics(ctx, thresholds)
            # Also detect response-format loops (misformat + repeat) — these bypass tool_failures
            fmt_consecutive = _get_format_failure_count(self.agent)
            if fmt_consecutive > consecutive:
                consecutive = fmt_consecutive
                failing_tool = "response_format"
            new_loop_tier, old_loop_tier = _update_loop_state(
                self.agent, state, consecutive, failing_tool, thresholds, ctx
            )
            _write_loop_signals(self.agent, state, consecutive, failing_tool)

            # Tier 4: capture anti-pattern on loop recovery
            if old_loop_tier != "none" and new_loop_tier == "none":
                try:
                    bst_store = getattr(self.agent, "_bst_store", {}) or {}
                    compound_sig = bst_store.get("_compound_sig", "unknown")
                    domain = compound_sig.split("+")[0]  # primary domain only
                    _capture_anti_pattern(self.agent, state, domain)
                except Exception:
                    pass

            injected = False

            # Tier 3 — circuit breaker (highest priority, no cooldown)
            if new_loop_tier == "reset" and not state.get(LOOP_RESET_DONE_KEY):
                _execute_tier3(self.agent, failing_tool, consecutive, state)
                state[LOOP_RESET_DONE_KEY] = True
                state[LOOP_SURGERY_DONE_KEY] = True  # Tier 3 subsumes Tier 2
                injected = True

            # Tier 2 — context surgery (second priority, no cooldown)
            elif new_loop_tier == "summarize" and not state.get(LOOP_SURGERY_DONE_KEY):
                _execute_tier2(self.agent, failing_tool, consecutive, state)
                state[LOOP_SURGERY_DONE_KEY] = True
                injected = True

            # 1. PACE escalation response (org-dependent, emergency exempt from cooldown)
            if org_active:
                if ctx["pace_level"] == "emergency":
                    _inject_pace_emergency(self.agent, role, ctx, state)
                    injected = True
                elif ctx["pace_level"] == "contingent":
                    if _cooldown_ok(state, ANOMALY_PACE):
                        _inject_pace_contingent(self.agent, role, ctx, state)
                        injected = True

            # 2. Cascade failure detection (always runs)
            if not injected and _cooldown_ok(state, ANOMALY_CASCADE):
                if _detect_cascade(ctx):
                    _inject_cascade(self.agent, state)
                    injected = True

            # 3. Context exhaustion (always runs — watchdog handles 70%/85%)
            if not injected and _cooldown_ok(state, ANOMALY_CONTEXT):
                if _detect_context_exhaustion(self.agent, ctx):
                    _inject_context_warning(self.agent, ctx, state)
                    injected = True

            # 3.5. Output stagnation detection (Finding 2, Session 055).
            # Fires when successful tool calls produce identical output — the agent is
            # working but not advancing. No failure count, no tier escalation. Different
            # signal, different message, different intervention from loop detection.
            if not injected and _cooldown_ok(state, ANOMALY_STAGNATION):
                stagnation = _detect_output_stagnation(ctx.get("tool_output_hashes", []))
                if stagnation.get("stagnating"):
                    _inject_stagnation(self.agent, stagnation, state)
                    injected = True

            # Read action gate — suppresses stall/loop-Tier1 when agent is pending authorization
            action_gate = False
            try:
                action_gate = bool(self.agent.get_data("_action_gate_active"))
            except Exception:
                pass

            # 4. Stall detection (org-dependent — requires HTN state)
            if not injected and org_active and not action_gate and _cooldown_ok(state, ANOMALY_STALL):
                if _detect_stall(ctx, role):
                    _inject_stall(self.agent, ctx, role, state)
                    injected = True

            # 5. Loop detection — Tier 1 (warn, respects cooldown)
            if not injected and not action_gate and new_loop_tier == "warn" and _cooldown_ok(state, ANOMALY_LOOP):
                _inject_loop(self.agent, ctx, state)
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
        "error_diagnosis": {},
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

    # Error diagnosis (from error comprehension layer)
    try:
        ctx["error_diagnosis"] = agent.get_data("_error_diagnosis") or {}
    except Exception:
        pass

    # Tool output hashes for stagnation detection (from fallback logger success tracking)
    try:
        ctx["tool_output_hashes"] = agent.get_data("_tool_output_tracker") or []
    except Exception:
        pass

    return ctx


# ── Anomaly Detection ───────────────────────────────────────────

def _get_domain_thresholds(bst_domain: str) -> dict:
    """
    Select tier threshold profile based on BST domain classification.

    Compound domains (e.g. "analysis+codegen") use the most permissive
    profile — an agent doing both things simultaneously needs at least as
    much latitude as either domain alone.

    Always returns values >= the defaults (3/6/9). The system becomes
    more permissive with domain knowledge, never more restrictive.
    """
    if not bst_domain:
        return DOMAIN_THRESHOLDS["default"]
    if "+" in bst_domain:
        parts = bst_domain.split("+")
        profiles = [DOMAIN_THRESHOLDS.get(p.strip(), DOMAIN_THRESHOLDS["default"]) for p in parts]
        return {
            "tier1": max(p["tier1"] for p in profiles),
            "tier2": max(p["tier2"] for p in profiles),
            "tier3": max(p["tier3"] for p in profiles),
        }
    return DOMAIN_THRESHOLDS.get(bst_domain, DOMAIN_THRESHOLDS["default"])


def _get_effective_domain(bst_domain: str, failure_history: list) -> str:
    """
    Compute the supervisor's operational domain from both BST classification
    and observed behavioral signals.

    Finding 1 (Session 055): The BST classifies from the user's message intent
    and maintains momentum. When the user says "run X" and X breaks, the BST
    stays in 'conversation' while the agent is actually debugging. The supervisor
    needs a signal that responds to what's ACTUALLY HAPPENING in the execution
    pattern — its own observation loop, not a dependency on the BST's label.

    The AAR OCT model: the OCT reads the operations order before the exercise
    (= BST classification) but also observes what's happening on the ground.
    When reality diverges from the plan, the OCT maintains its own operational
    picture — it does not rewrite the operations order.

    IMPORTANT: This override flows only to threshold selection. It does NOT
    modify the BST. The BST continues classifying for enrichment purposes.
    Two observation loops, two update cadences, same agent.
    """
    if not failure_history or len(failure_history) < 3:
        return bst_domain

    recent = failure_history[-10:]
    code_exec_failures = [e for e in recent if e.get("tool") == "code_execution_tool"]

    if len(code_exec_failures) >= 2:
        unique_errors = len(set(
            e.get("error_type", "") for e in code_exec_failures if e.get("error_type")
        ))
        if unique_errors >= 2:
            # Behavioral signal: iterative debugging on code_execution_tool
            # regardless of what the user asked for
            if "debugging" not in bst_domain and "codegen" not in bst_domain:
                if bst_domain in ("", "conversation", "default"):
                    return "debugging"
                else:
                    return bst_domain + "+debugging"

    return bst_domain


def _get_error_diversity(ctx: dict, consecutive: int) -> int:
    """
    Count unique error types across the last N failure history entries.

    The fallback logger classifies every tool failure into a structured
    error_type field (timeout, not_found, syntax, execution, etc.), using
    the EC diagnosis when available. Counting distinct types over the recent
    failure window distinguishes iteration (3+ unique types = learning) from
    fixation (1-2 unique types = same error repeated).
    """
    history = ctx.get("failure_history", [])
    if not history or consecutive < 1:
        return 0
    recent = history[-max(consecutive, 1):]
    types = set(e.get("error_type", "") for e in recent if e.get("error_type"))
    return len(types)


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



def _detect_output_stagnation(tool_output_hashes: list) -> dict:
    """
    Detect when tool executions succeed but produce identical output — the
    agent is working mechanically without advancing the task.

    Finding 2 (Session 055): The consecutive failure counter stays at zero
    during stagnation (all calls succeed). The supervisor has no failure-based
    signal. The loop detection message that fired came from Agent Zero's core
    duplicate response detector (syntactic), not from the supervisor tier system.

    A loop is: same action → same error → same action. Stuck on INPUT side.
    Stagnation is: different action → same result → different action. Stuck on
    OUTPUT side. Different diagnosis, different prescription.

    The intervention for stagnation is also different:
    - Loop: "Your tool is failing. Try a different tool."
    - Stagnation: "Your tool is working but you're not advancing. Reconsider
      whether you're done or whether the objective needs clarification."
    """
    if len(tool_output_hashes) < STAGNATION_WINDOW:
        return {"stagnating": False}

    recent = tool_output_hashes[-STAGNATION_WINDOW:]
    successful = [o for o in recent if o.get("status") == "success"]

    if len(successful) < STAGNATION_MIN_SUCCESSES:
        return {"stagnating": False}

    hashes = [o.get("output_hash") for o in successful if o.get("output_hash") is not None]
    unique_hashes = len(set(hashes))

    if unique_hashes <= STAGNATION_MAX_UNIQUE:
        return {
            "stagnating": True,
            "identical_count": len(successful),
            "unique_hashes": unique_hashes,
            "tool": successful[-1].get("tool", "unknown") if successful else "unknown",
        }

    return {"stagnating": False}


def _get_loop_metrics(ctx: dict, thresholds: dict) -> tuple:
    """
    Return (consecutive_failure_count, failing_tool) from the tool failure tracker.
    Uses the 'consecutive' dict maintained by the tool fallback chain — more reliable
    than scanning failure_history list length.
    Returns (0, None) if no loop condition is present.

    thresholds: domain-aware profile from _get_domain_thresholds(), so that
    a codegen task doesn't register as a loop until 6 failures rather than 3.
    """
    failures = ctx.get("tool_failures") or {}
    consecutive = failures.get("consecutive") or {}
    if not consecutive:
        return 0, None
    failing_tool = max(consecutive, key=consecutive.get)
    count = consecutive[failing_tool]
    if count < thresholds["tier1"]:
        return 0, None
    return count, failing_tool



def _get_format_failure_count(agent) -> int:
    """
    Count consecutive response-format failures at the end of current history.
    Detects fw.msg_misformat (not valid JSON) and fw.msg_repeat (identical response)
    warnings injected by the agent-zero core. These bypass tool_failures.consecutive
    so the graduated cascade wouldn't otherwise detect them.
    """
    MISFORMAT_SIGNAL = "Your last response was not valid JSON"
    REPEAT_SIGNAL = "LOOP DETECTED. Your last response was identical"
    try:
        msgs = agent.history.current.messages
        count = 0
        for msg in reversed(msgs):
            if getattr(msg, "ai", False):
                continue  # skip AI response messages, only check warnings
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            if MISFORMAT_SIGNAL in content or REPEAT_SIGNAL in content:
                count += 1
            else:
                break  # stop at first non-format-failure warning
        return count
    except Exception:
        return 0


def _update_loop_state(agent, state: dict, consecutive: int, failing_tool,
                       thresholds: dict, ctx: dict) -> tuple:
    """
    Update persistent loop episode state. Computes tier from consecutive count,
    tracks tier transitions, records message index at episode start.
    Returns (new_tier, old_tier) as strings.

    Direction A: thresholds are domain-aware (from _get_domain_thresholds).
    Direction B: Tier 2+ escalation is gated on error type consistency.
                 If the agent is producing diverse errors (DIVERSITY_SUPPRESS_THRESHOLD+
                 unique types), it is iterating — suppress surgery/circuit-breaker
                 and hold at Tier 1 warn only.
    """
    old_tier = state.get(LOOP_TIER_KEY, "none")

    if consecutive < thresholds["tier1"]:
        # Loop resolved -- clear episode state
        if old_tier != "none":
            state[LOOP_TIER_KEY] = "none"
            state[LOOP_TOOL_KEY] = None
            state.pop(LOOP_START_IDX_KEY, None)
            state.pop(LOOP_SURGERY_DONE_KEY, None)
            state.pop(LOOP_RESET_DONE_KEY, None)
        return "none", old_tier

    # Direction B: check error diversity before escalating past Tier 1
    error_diversity = _get_error_diversity(ctx, consecutive)
    diverse_errors = error_diversity >= DIVERSITY_SUPPRESS_THRESHOLD

    # Compute new tier — suppress surgery/reset when errors are diverse
    if consecutive >= thresholds["tier3"]:
        new_tier = "warn" if diverse_errors else "reset"
    elif consecutive >= thresholds["tier2"]:
        new_tier = "warn" if diverse_errors else "summarize"
    else:
        new_tier = "warn"

    if diverse_errors and consecutive >= thresholds["tier2"]:
        try:
            agent.context.log.log(
                type="info",
                content=(
                    f"[SUPERVISOR] Diversity gate: {consecutive} failures on '{failing_tool}' "
                    f"but {error_diversity} unique error types — agent is iterating, "
                    f"suppressing Tier 2+ escalation."
                ),
                flush=True
            )
        except Exception:
            pass

    # Record message index at start of episode (first time entering warn)
    if old_tier == "none" and new_tier == "warn":
        try:
            state[LOOP_START_IDX_KEY] = len(agent.history.current.messages)
        except Exception:
            pass

    state[LOOP_TIER_KEY] = new_tier
    state[LOOP_TOOL_KEY] = failing_tool
    # Track peak for anti-pattern capture (how bad did it get?)
    state["loop_peak_consecutive"] = max(state.get("loop_peak_consecutive", 0), consecutive)
    return new_tier, old_tier


def _execute_tier2(agent, failing_tool, consecutive: int, state: dict):
    """
    Tier 2: Context surgery. Remove loop messages from the current history topic,
    inject a diagnostic summary. Breaks the history feedback loop that sustains
    repetitive failures without requiring a container restart.
    """
    try:
        current_topic = agent.history.current
        loop_start_idx = state.get(
            LOOP_START_IDX_KEY,
            max(0, len(current_topic.messages) - consecutive * 2)
        )
        removed_count = max(0, len(current_topic.messages) - loop_start_idx)
        if removed_count > 0:
            del current_topic.messages[loop_start_idx:]

        summary = (
            f"[SUPERVISOR TIER 2 - LOOP SURGERY] {consecutive} consecutive tool failures "
            f"removed from context to break the feedback loop. "
        )
        if failing_tool:
            alternatives = LOOP_ALTERNATIVES.get(failing_tool, DEFAULT_ALTERNATIVES)
            alt_text = "; ".join(alternatives[:2])
            summary += f"Failing tool: '{failing_tool}'. Alternatives: {alt_text}. "
        summary += (
            "Do NOT retry the same approach. "
            "If no alternative is available, use the response tool to report your progress."
        )
        try:
            ec = agent.get_data("_error_diagnosis") or {}
            if ec.get("confidence", 0) > 0.6:
                error_class = ec.get("error_class", "")
                anti = ec.get("anti_actions", [])
                if error_class:
                    summary += f" Error class: {error_class}."
                if anti:
                    summary += f" Do NOT: {anti[0]}."
        except Exception:
            pass

        agent.hist_add_warning(summary)
        agent.context.log.log(
            type="info",
            content=f"[SUPERVISOR] Tier 2 surgery: removed {removed_count} messages, tool={failing_tool}, consecutive={consecutive}",
            flush=True
        )
    except Exception as e:
        agent.context.log.log(
            type="warning",
            content=f"[SUPERVISOR] Tier 2 surgery failed: {e}",
            flush=True
        )


def _execute_tier3(agent, failing_tool, consecutive: int, state: dict):
    """
    Tier 3: Circuit breaker. Aggressive surgery + mandatory response instruction.
    The model's next action MUST be the response tool.
    """
    try:
        current_topic = agent.history.current
        loop_start_idx = state.get(
            LOOP_START_IDX_KEY,
            max(0, len(current_topic.messages) - consecutive * 2)
        )
        removed_count = max(0, len(current_topic.messages) - loop_start_idx)
        if removed_count > 0:
            del current_topic.messages[loop_start_idx:]

        tool_name = failing_tool or "unknown"
        msg = (
            f"[SUPERVISOR TIER 3 - CIRCUIT BREAKER] {consecutive} consecutive failures on "
            f"'{tool_name}'. Loop context has been cleared.\n"
            f"YOU MUST USE THE RESPONSE TOOL NOW. No other tool call is acceptable.\n"
            f"Your next action must be:\n"
            f'{{"thoughts": "Task interrupted by supervisor circuit breaker after {consecutive} failures.", '
            f'"tool_name": "response", '
            f'"tool_args": {{"text": "Describe what was completed before the loop started and what is blocking progress."}}}}'
        )

        try:
            ec = agent.get_data("_error_diagnosis") or {}
            if ec.get("confidence", 0) > 0.6:
                error_class = ec.get("error_class", "")
                if error_class:
                    msg += f"\n[EC] Error class: {error_class}."
        except Exception:
            pass

        agent.hist_add_warning(msg)
        agent.context.log.log(
            type="warning",
            content=f"[SUPERVISOR] Tier 3 circuit breaker: {consecutive} failures on {tool_name}",
            flush=True
        )
    except Exception as e:
        agent.context.log.log(
            type="warning",
            content=f"[SUPERVISOR] Tier 3 failed: {e}",
            flush=True
        )


def _write_loop_signals(agent, state: dict, consecutive: int, failing_tool):
    """
    Write loop state to _layer_signals for BST and memorizer coordination.
    BST reads loop_active to break momentum lock.
    Memorizer reads loop_active to suppress writes during active loops.
    """
    try:
        signals = agent.get_data("_layer_signals") or {}
        signals["loop_active"]       = consecutive >= WARN_THRESHOLD
        signals["loop_tier"]         = state.get(LOOP_TIER_KEY, "none")
        signals["loop_consecutive"]  = consecutive
        signals["loop_failing_tool"] = failing_tool
        agent.set_data("_layer_signals", signals)
    except Exception:
        pass



def _capture_anti_pattern(agent, state: dict, domain: str):
    """
    Tier 4: Capture loop-and-recovery as an anti-pattern entry in procedural memory.
    Called when a loop episode resolves (consecutive failures drop below WARN_THRESHOLD).
    Writes to /a0/usr/Exocortex/procedural_memory/ for cross-session prevention.
    """
    try:
        from procedural_memory_api import ProceduralMemory
        failing_tool = state.get(LOOP_TOOL_KEY) or "unknown"
        consecutive = state.get("loop_peak_consecutive", 3)

        pre_action_check = (
            f"Before calling '{failing_tool}' for {domain} tasks: "
            f"verify the tool can handle the input in this context. "
        )
        alternatives = LOOP_ALTERNATIVES.get(failing_tool, DEFAULT_ALTERNATIVES)
        if alternatives:
            pre_action_check += f"If uncertain, use alternative: {alternatives[0]}"

        pm = ProceduralMemory()
        path = pm.create_anti_pattern(
            failing_tool=failing_tool,
            domain=domain,
            consecutive=consecutive,
            pre_action_check=pre_action_check,
        )
        agent.context.log.log(
            type="info",
            content=f"[SUPERVISOR] Tier 4 anti-pattern captured: {failing_tool} in {domain} -> {path}",
            flush=True
        )
    except Exception as e:
        try:
            agent.context.log.log(
                type="warning",
                content=f"[SUPERVISOR] Tier 4 capture failed: {e}",
                flush=True
            )
        except Exception:
            pass


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
    ec = ctx.get("error_diagnosis", {})
    if ec.get("confidence", 0) > 0.6:
        error_class = ec.get("error_class", "")
        suggested = ec.get("suggested_actions", [])
        if error_class:
            msg += f" [{error_class}]"
        if suggested:
            msg += f" Suggested: {suggested[0]}."
    _emit(agent, msg, ANOMALY_STALL, state)


def _inject_loop(agent, ctx: dict, state: dict):
    """Inject loop detection — names the closed strategy and the opposing approach."""
    history = ctx.get("failure_history", [])
    recent = history[-LOOP_DETECTION_THRESHOLD:] if len(history) >= LOOP_DETECTION_THRESHOLD else history

    if recent:
        tool = recent[-1].get("tool", "unknown")
        error_type = recent[-1].get("error_type", "unknown")
        n = len(recent)
        alternatives = LOOP_ALTERNATIVES.get(tool, DEFAULT_ALTERNATIVES)
        alt_list = "\n".join(f"  - {a}" for a in alternatives)
        msg = (
            f"[SUPERVISOR] LOOP DETECTED — {tool} has failed {n} times ({error_type}).\n"
            f"This strategy is closed. Do not retry {tool}.\n"
            f"Opposing approaches:\n{alt_list}"
        )
    else:
        msg = (
            "[SUPERVISOR] You are repeating the same failing action. "
            "Stop and try a fundamentally different approach — different tool, different path, or different strategy."
        )

    ec = ctx.get("error_diagnosis", {})
    if ec.get("confidence", 0) > 0.6:
        error_class = ec.get("error_class", "")
        anti = ec.get("anti_actions", [])
        if error_class or anti:
            extra = f"\n[EC] Error class: {error_class}." if error_class else ""
            if anti:
                extra += f" Do NOT: {'; '.join(anti[:2])}."
            msg += extra

    _emit(agent, msg, ANOMALY_LOOP, state)


def _inject_context_warning(agent, ctx: dict, state: dict):
    """Inject context exhaustion warning at 90%+."""
    pct = round(ctx["context_fill"] * 100)
    msg = (
        f"[SUPERVISOR] Context window is {pct}% full. "
        f"Complete your immediate task and respond to the user. Do not start new subtasks."
    )
    _emit(agent, msg, ANOMALY_CONTEXT, state)


def _inject_stagnation(agent, stagnation: dict, state: dict):
    """
    Inject stagnation warning — successful execution without forward progress.

    Distinct from loop detection: the tool is working, the agent is not stuck
    on a failing approach. The problem is that successful output is identical
    across multiple calls — the agent is succeeding mechanically without
    changing the state of the task.

    The prescription is different from a loop intervention:
    - Loop says: "Your tool failed N times, try X alternative instead."
    - Stagnation says: "Your tool worked but nothing changed. Reconsider
      whether you're done or whether the goal needs clarification."
    """
    count = stagnation.get("identical_count", 3)
    tool = stagnation.get("tool", "unknown")
    msg = (
        f"[SUPERVISOR] STAGNATION DETECTED — '{tool}' has produced identical output "
        f"across {count} consecutive successful calls. The method is working but the "
        f"task is not advancing.\n"
        f"Consider:\n"
        f"  1. Whether the current output already satisfies the task objective\n"
        f"  2. Whether the goal needs refinement (what specifically should change?)\n"
        f"  3. Using the response tool to report current results and ask for guidance\n"
        f"Do not re-run the same approach expecting a different result."
    )
    _emit(agent, msg, ANOMALY_STAGNATION, state)


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
    # Signal to fallback advisor that supervisor has fired strategic guidance.
    # Prevents duplicate "try a different approach" messages on the next turn.
    try:
        agent.set_data("_supervisor_warned", True)
    except Exception:
        pass
