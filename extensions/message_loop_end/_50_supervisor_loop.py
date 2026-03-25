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
    "research":       {"tier1": 6,  "tier2": 12, "tier3": 18},  # raised: multi-step research is legitimate iteration
    "analysis":       {"tier1": 6,  "tier2": 12, "tier3": 18},  # raised: complex analysis requires sustained tool use
    "investigation":  {"tier1": 6,  "tier2": 12, "tier3": 18},  # raised: OSS/OSINT tasks routinely need 15+ iterations
    "agentic":        {"tier1": 6,  "tier2": 12, "tier3": 18},  # raised: matches structural domains
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

# ── Canary CUSUM buffer ───────────────────────────────────────────────────────
# Sub-threshold signal accumulation (Ansoff 1975; Page 1954 CUSUM).
# The monitoring system and the decision system have different evidentiary
# standards — the canary notices at a lower threshold than the supervisor acts.
ANOMALY_CANARY = "canary"
CANARY_K = 0.25    # reference value: sensitivity to shift size (lower = more sensitive)
CANARY_H = 1.5     # decision threshold: cumulative sum to trigger soft flag
CANARY_DECAY = 0.1 # decay per turn when no new signals (avoids stale accumulation)

CANARY_SIGNAL_TYPES = frozenset([
    "bst_misclassification",
    "tool_selection_drift",
    "capability_boundary",
    "relational_friction",
    "confidence_drift",
])

# Stagnation detection: successful-execution-no-progress (Finding 2, Session 055).
# Fires when N+ successful tool calls in a window produce identical output hashes.
STAGNATION_WINDOW = 4          # Rolling window of recent tool outputs to examine
STAGNATION_MIN_SUCCESSES = 3   # Minimum successful calls needed to evaluate
STAGNATION_MAX_UNIQUE = 2      # Max unique output hashes before stagnation is declared

# ── Phase 4: Parallel LLM supervisor — strategic pattern detection ────────────
# A separate LLM call with compressed context only. No agent history, no Einstellung.
# The LLM advises. The deterministic tier system enforces.

PHASE4_LM_ENDPOINT = "http://host.docker.internal:1234/v1/chat/completions"
PHASE4_MODEL = "qwen3.5-27b-claude-4.6-opus-reasoning-distilled@q4_k_m"
PHASE4_MAX_TOKENS = 200
PHASE4_TEMPERATURE = 0.0
PHASE4_TIMEOUT = 10.0                  # hard timeout — never block the agent
PHASE4_ESCALATION_CONFIDENCE = 0.7
PHASE4_DEESCALATION_CONFIDENCE = 0.7
PHASE4_MIN_TURN = 3                    # don't fire in first 3 turns
ANOMALY_PHASE4 = "phase4"

# Trigger thresholds
PHASE4_MIN_FAILURES_TRIGGER = 2        # failure count before Phase 4 considers firing
PHASE4_CONFIRMATION_TRIGGER = 2        # operator confirmations without output → trigger
PHASE4_BST_MOMENTUM_TRIGGER = 5        # extended momentum in one domain → trigger

# Operator confirmation signal keywords (lightweight history scan)
_CONFIRMATION_SIGNALS = frozenset([
    "proceed", "go ahead", "start", "create", "build", "make", "write",
    "yes", "ok", "continue", "please", "sounds good", "lets", "let's",
    "implement", "generate", "sure", "great", "do it",
])

# Phase 4 system prompt — the only context the parallel supervisor sees
PHASE4_SYSTEM_PROMPT = (
    "You are a supervisor monitoring an AI agent's execution. "
    "You receive a compressed status report and must decide whether to intervene.\n\n"
    "Your options:\n"
    "- HOLD: Agent is working normally. No intervention needed.\n"
    "- ESCALATE: Agent is stuck in a strategic pattern it cannot break itself. "
    "Provide a specific intervention message.\n"
    "- DEESCALATE: Agent has recovered from a previous issue. "
    "Restore normal thresholds.\n\n"
    "Known failure patterns to watch for:\n\n"
    "1. RESEARCH_AFTER_CONFIRMATION: Agent re-enters information-gathering mode after "
    "operator has confirmed the task. Signal: operator_confirmations > 0 AND "
    "productive_output = 0 AND agent is reading/researching.\n\n"
    "2. STRATEGY_REPETITION: Multiple attempts fail for the same root cause despite "
    "surface-level variation. Signal: blocking_factors show the same root cause "
    "across 3+ attempts, even if error types differ.\n\n"
    "3. MACRO_CYCLE: Agent repeats a multi-step behavioral cycle (research -> propose -> "
    "ask -> research) after the cycle was already completed and confirmed. Signal: "
    "same strategy_hash appears twice with operator confirmation between them.\n\n"
    "4. SELF_DIAGNOSIS_WITHOUT_CHANGE: Agent correctly identifies it is stuck but then "
    "re-enters the same pattern. Signal: agent_self_diagnosis = present AND "
    "followed_by_change = no.\n\n"
    "Respond ONLY with a JSON object: "
    "{\"action\": \"HOLD\"|\"ESCALATE\"|\"DEESCALATE\", "
    "\"confidence\": 0.0-1.0, \"reason\": \"one line\", "
    "\"intervention\": \"message if escalating\", "
    "\"pattern_matched\": \"pattern name or null\"}.\n\n"
    "If uncertain, choose HOLD. False negatives are better than false positives."
)

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

            # ── Canary CUSUM check (runs every turn, before interval guard) ──────
            # Sub-threshold signal accumulation via CUSUM (Page 1954).
            # Fires a soft pre-tier-1 flag when accumulated signals cross CANARY_H.
            # Monitoring system has different evidentiary standard than decision system
            # (Ansoff 1975) — canary notices before any tier fires.
            if _cooldown_ok(state, ANOMALY_CANARY):
                canary_msg = _check_canary_staging(self.agent, state)
                if canary_msg:
                    try:
                        self.agent.context.log.log(
                            type="info",
                            content=f"[SUPERVISOR-CANARY] {canary_msg}",
                            flush=True,
                        )
                        loop_data.system.append({"role": "user", "content": canary_msg})
                        _mark_cooldown(state, ANOMALY_CANARY)
                    except Exception:
                        pass

            # Check interval — run checks every N turns
            interval = DEFAULT_CHECK_INTERVAL
            if state["turn"] % interval != 0:
                _set_state(self.agent, state)
                return

            # Phase 3: load profile store (cached per session) and drain episode buffer.
            # Must run before threshold selection — buffer may contain new observations
            # that improve the learned thresholds for this very turn.
            profile_store = _get_profile_store(self.agent)
            _process_episode_buffer(self.agent, profile_store)

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

            # Phase 3: identify the candidate failing tool before threshold selection.
            # The learned profile lookup is keyed on (tool_name, domain), so we need to
            # know which tool is accumulating failures to pick the right profile.
            # We read from ctx.tool_failures.consecutive — same source as _get_loop_metrics.
            failures_raw = ctx.get("tool_failures") or {}
            consecutive_raw = failures_raw.get("consecutive") or {}
            candidate_tool = max(consecutive_raw, key=consecutive_raw.get) if consecutive_raw else ""

            # Three-layer threshold selection: learned → static → default.
            thresholds = _get_learned_thresholds(candidate_tool, effective_domain, profile_store)

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

            # Phase 4 trigger tracking: record that the loop detector fired this session
            if new_loop_tier != "none":
                state["_p4_loop_fired"] = True

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

            # 3.6. Phase 4: parallel LLM supervisor — strategic pattern detection.
            # Fires only when trigger conditions are met and Phases 1-3 have not
            # already escalated to Tier 2+. The LLM advises; the tier system enforces.
            # Never blocks the agent: 10s timeout, any failure returns HOLD.
            if not injected and _cooldown_ok(state, ANOMALY_PHASE4):
                if _should_trigger_phase4(ctx, state, self.agent):
                    compressed = _build_phase4_context(
                        self.agent, ctx, effective_domain, state
                    )
                    p4_rec = await _call_phase4_supervisor(compressed)
                    _log_phase4_decision(self.agent, compressed, p4_rec)
                    _update_phase4_strategy_hashes(self.agent, state)
                    if p4_rec.get("action") == "ESCALATE":
                        _apply_phase4_recommendation(self.agent, p4_rec, state)
                        injected = True
                    elif p4_rec.get("action") == "DEESCALATE":
                        _apply_phase4_recommendation(self.agent, p4_rec, state)

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


# ── Canary CUSUM Buffer ───────────────────────────────────────────────────────

def _classify_canary_signal(text: str, why: str) -> str:
    """Deterministic keyword classification of a canary entry's signal type."""
    combined = (text + " " + why).lower()
    if any(kw in combined for kw in ["bst", "classified wrong", "misclassified", "domain wrong", "wrong domain"]):
        return "bst_misclassification"
    if any(kw in combined for kw in ["same tool", "keep using", "reaching for", "tool drift", "always use"]):
        return "tool_selection_drift"
    if any(kw in combined for kw in ["can't", "cannot", "outside", "capability", "don't know how", "beyond"]):
        return "capability_boundary"
    if any(kw in combined for kw in ["operator", "relationship", "friction", "tension", "misunderstood"]):
        return "relational_friction"
    return "confidence_drift"


def _check_canary_staging(agent, state: dict) -> str | None:
    """
    CUSUM accumulator for sub-threshold canary signals.
    Scans staging.jsonl for active canary entries written since the last check.
    Decays existing accumulators when no new signals arrive.
    Returns a soft-flag message if any signal type crosses CANARY_H, else None.

    Runs every turn (before the check-interval guard) so signals accumulate
    at the per-turn resolution the CUSUM mechanism requires.
    """
    import json as _json
    import os as _os

    _STAGING_PATH = "/a0/usr/Exocortex/staging.jsonl"
    if not _os.path.exists(_STAGING_PATH):
        return None

    current_turn = state.get("turn", 0)
    last_check = state.get("_canary_last_check", 0)
    state["_canary_last_check"] = current_turn

    cusum = state.setdefault("_canary_cusum", {})

    new_canaries = []
    try:
        with open(_STAGING_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = _json.loads(line)
                    if (
                        entry.get("category") == "canary"
                        and entry.get("status") == "active"
                        and entry.get("session_age_at_write", 0) >= last_check
                    ):
                        new_canaries.append(entry)
                except _json.JSONDecodeError:
                    pass
    except Exception:
        return None

    # Decay existing accumulators when no new signals (prevents stale firing)
    if not new_canaries:
        for k in list(cusum.keys()):
            cusum[k] = max(0.0, cusum[k] - CANARY_DECAY)
        return None

    # CUSUM update: C_t = max(0, C_{t-1} + (x_t - k))
    fired_signals = []
    for entry in new_canaries:
        importance = entry.get("importance", 0.3)
        sig = _classify_canary_signal(entry.get("text", ""), entry.get("why", ""))
        cusum[sig] = max(0.0, cusum.get(sig, 0.0) + (importance - CANARY_K))
        if cusum[sig] >= CANARY_H:
            fired_signals.append(sig)
            cusum[sig] = 0.0  # reset after firing

    if not fired_signals:
        return None

    _SIGNAL_DESCRIPTIONS = {
        "bst_misclassification": "repeated BST domain misclassification",
        "tool_selection_drift": "persistent tendency toward a specific tool",
        "capability_boundary": "task may be near capability boundary",
        "relational_friction": "possible friction in operator-agent collaboration",
        "confidence_drift": "accumulating uncertainty signals",
    }
    msgs = [_SIGNAL_DESCRIPTIONS.get(s, s) for s in fired_signals]
    return f"⚠ Canary signals: {'; '.join(msgs)}. Consider pausing to assess."


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


def _get_learned_thresholds(tool_name: str, effective_domain: str, profile_store) -> dict:
    """
    Three-layer threshold selection — Phase 3 Adaptive Supervisor.

    Priority:
      1. Learned profile (observation_count >= MIN_OBSERVATIONS): p50/p90 from accumulated data.
         Safety floors: learned values never go below cold-start defaults (3/6/9).
      2. Static DOMAIN_THRESHOLDS: hand-tuned per-domain values. Used when no profile exists
         or profile has insufficient observations.
      3. Default 3/6/9: implicit via _get_domain_thresholds("").

    No LLM calls in this path. Pure arithmetic on the profile's observation list.
    """
    MIN_OBSERVATIONS = 3
    if profile_store and tool_name:
        try:
            profile = profile_store.get_for_compound(tool_name, effective_domain)
            if profile and profile.observation_count >= MIN_OBSERVATIONS:
                t1 = max(3, int(profile.p50))
                t2 = max(6, int(profile.p90))
                t3 = max(9, int(profile.p90 * 1.5))
                return {
                    "tier1": t1,
                    "tier2": t2,
                    "tier3": t3,
                    "source": "learned",
                    "observations": profile.observation_count,
                }
        except Exception:
            pass
    # Fallback: static domain thresholds
    static = _get_domain_thresholds(effective_domain)
    return {**static, "source": "static"}


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
            # False recovery tracking: record the surgery tool before clearing state
            if old_tier in ("summarize", "reset"):
                try:
                    agent.set_data("_post_surgery_tool", state.get(LOOP_TOOL_KEY))
                    agent.set_data("_post_surgery_turn", 0)
                except Exception:
                    pass
            state[LOOP_TIER_KEY] = "none"
            state[LOOP_TOOL_KEY] = None
            state.pop(LOOP_START_IDX_KEY, None)
            state.pop(LOOP_SURGERY_DONE_KEY, None)
            state.pop(LOOP_RESET_DONE_KEY, None)
            # Clear loop state for downstream hooks
            try:
                agent.set_data("_loop_active", False)
                agent.set_data("_loop_start_cycle", None)
            except Exception:
                pass
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


def _extract_session_intent(agent) -> str:
    """Extract the original task from the first non-system user message."""
    try:
        msgs = agent.history.current.messages
        for msg in msgs:
            if getattr(msg, "ai", True):
                continue
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            if content and not content.startswith("[SUPERVISOR"):
                return content[:200].replace("\n", " ")
    except Exception:
        pass
    return "task not recoverable"


def _extract_pre_loop_progress(agent, incision_idx: int) -> str:
    """Summarize successful tool calls before the incision point."""
    try:
        msgs = agent.history.current.messages
        pre_loop = msgs[:incision_idx]
        successes = []
        for msg in reversed(pre_loop[-10:]):  # last 10 pre-loop messages
            if not getattr(msg, "ai", False):
                continue
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            # Include AI messages that aren't supervisor warnings
            if content and not content.startswith("[SUPERVISOR"):
                successes.append(content[:150].replace("\n", " "))
                if len(successes) >= 3:
                    break
        if successes:
            return "; ".join(reversed(successes))
    except Exception:
        pass
    return "no progress record available"


def _extract_current_state(agent) -> str:
    """Extract working memory state if available, else return brief placeholder."""
    try:
        wm = agent.get_data("_wm_state")
        if wm and isinstance(wm, dict):
            parts = []
            if wm.get("objective"):
                parts.append(f"objective: {str(wm['objective'])[:100]}")
            if wm.get("entities"):
                ents = list(wm["entities"])[:3]
                parts.append(f"entities: {', '.join(str(e) for e in ents)}")
            if parts:
                return "; ".join(parts)
    except Exception:
        pass
    return "working memory not available"


def _drain_staging_buffer(agent):
    """
    Mark all staging-buffer entries from the loop period as loop_period validity.
    Called by Tier 2 and Tier 3 surgery. Operates on FAISS and evidence ledger.
    WAL approximation: writes are immediate but the buffer records them for rollback.
    """
    staging = agent.get_data("_memory_staging_buffer") or []
    loop_start_cycle = agent.get_data("_loop_start_cycle") or 0
    if not staging or not loop_start_cycle:
        return

    import asyncio
    from python.helpers.memory import Memory

    affected = [e for e in staging if e.get("turn_idx", 0) >= loop_start_cycle]
    if not affected:
        return

    async def _mark():
        try:
            db = await Memory.get(agent)
            all_docs = db.db.get_all_docs() if hasattr(db, "db") else {}
            changed = False
            for entry in affected:
                if entry.get("store") == "faiss":
                    doc = all_docs.get(entry["doc_id"])
                    if doc and hasattr(doc, "metadata"):
                        cls = doc.metadata.get("classification", {})
                        if cls.get("validity") not in ("deprecated",):
                            cls["validity"] = "loop_period"
                            doc.metadata["classification"] = cls
                            changed = True
                elif entry.get("store") == "evidence_ledger":
                    ledger = agent.get_data("_evidence_ledger") or {}
                    for e in ledger.get("entries", []):
                        if e.get("_staging_id") == entry["doc_id"]:
                            e["loop_period"] = True
            if changed:
                db.db._save_db()
        except Exception as e:
            print(f"[SUPERVISOR] _drain_staging_buffer inner error: {e}", flush=True)

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_mark())
        else:
            loop.run_until_complete(_mark())
    except Exception as e:
        print(f"[SUPERVISOR] _drain_staging_buffer dispatch error: {e}", flush=True)

    try:
        agent.context.log.log(
            type="info",
            content=f"[SUPERVISOR] Staging buffer drain: {len(affected)} entries tagged loop_period",
            flush=True,
        )
    except Exception:
        pass


def _execute_tier2(agent, failing_tool, consecutive: int, state: dict):
    """
    Tier 2: Context surgery. Remove loop messages from the current history topic,
    inject a diagnostic summary. Breaks the history feedback loop that sustains
    repetitive failures without requiring a container restart.
    """
    try:
        current_topic = agent.history.current
        loop_start_raw = state.get(
            LOOP_START_IDX_KEY,
            max(0, len(current_topic.messages) - consecutive * 2)
        )
        incision_idx = max(0, loop_start_raw - 2)  # -2 lookback: drift precedes detection
        removed_count = max(0, len(current_topic.messages) - incision_idx)
        if removed_count > 0:
            del current_topic.messages[incision_idx:]

        # ── Build recovery summary (omit failure description — prevents re-priming) ──
        session_intent = _extract_session_intent(agent)
        progress       = _extract_pre_loop_progress(agent, incision_idx)
        current_state  = _extract_current_state(agent)

        summary_lines = [
            "[SUPERVISOR: CONTEXT SURGERY]",
            f"Session intent: {session_intent}",
            f"Progress before interruption: {progress}",
            f"Current state: {current_state}",
            "Note: A repetitive failure sequence has been removed from context. "
            "If the current approach is blocked, use the response tool to report "
            "the obstacle and request guidance.",
        ]

        # Add error class from EC if available (no tool name, no count)
        try:
            ec = agent.get_data("_error_diagnosis") or {}
            if ec.get("confidence", 0) > 0.6 and ec.get("error_class"):
                summary_lines.append(f"Error class detected: {ec['error_class']}.")
                anti = ec.get("anti_actions", [])
                if anti:
                    summary_lines.append(f"Do NOT: {anti[0]}.")
        except Exception:
            pass

        summary = "\n".join(summary_lines)

        # ── Insert at incision point (primacy position) rather than appending ─────
        try:
            from python.helpers.history import HistoryMessage
            summary_msg = HistoryMessage(content=summary, ai=False)
            current_topic.messages.insert(incision_idx, summary_msg)
        except Exception:
            # Fallback: append if insertion fails
            agent.hist_add_warning(summary)

        agent.context.log.log(
            type="info",
            content=f"[SUPERVISOR] Tier 2 surgery: removed {removed_count} messages, incision={incision_idx}, consecutive={consecutive}",
            flush=True
        )

        # ── Multi-store rollback via staging buffer ───────────────────────────────
        try:
            _drain_staging_buffer(agent)
        except Exception as e:
            agent.context.log.log(
                type="warning",
                content=f"[SUPERVISOR] Staging buffer drain failed (history surgery still applied): {e}",
                flush=True,
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
        loop_start_raw = state.get(
            LOOP_START_IDX_KEY,
            max(0, len(current_topic.messages) - consecutive * 2)
        )
        incision_idx = max(0, loop_start_raw - 2)  # -2 lookback: drift precedes detection
        removed_count = max(0, len(current_topic.messages) - incision_idx)
        if removed_count > 0:
            del current_topic.messages[incision_idx:]

        tool_name = failing_tool or "unknown"
        msg = (
            f"[SUPERVISOR TIER 3 - CIRCUIT BREAKER] {consecutive} consecutive failures. "
            f"Loop context has been cleared.\n"
            f"YOU MUST USE THE RESPONSE TOOL NOW. No other tool call is acceptable.\n"
            f"Your next action must be:\n"
            f'{{"thoughts": "Task interrupted by supervisor circuit breaker.", '
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
            content=f"[SUPERVISOR] Tier 3 circuit breaker: {consecutive} failures, incision={incision_idx}",
            flush=True
        )

        # ── Multi-store rollback via staging buffer ───────────────────────────────
        try:
            _drain_staging_buffer(agent)
        except Exception as e:
            agent.context.log.log(
                type="warning",
                content=f"[SUPERVISOR] Staging buffer drain failed (history surgery still applied): {e}",
                flush=True,
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
    Also exports _loop_active / _loop_start_cycle to agent data for memory
    classifier and evidence ledger recorder.
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

    # Export loop state for downstream hooks (memory classifier, evidence ledger)
    try:
        is_active = consecutive >= WARN_THRESHOLD
        agent.set_data("_loop_active", is_active)
        if is_active and agent.get_data("_loop_start_cycle") is None:
            agent.set_data("_loop_start_cycle", state.get(LOOP_START_IDX_KEY, 0))
    except Exception:
        pass

    # False recovery: increment post-surgery turn counter and check re-failure
    try:
        post_tool = agent.get_data("_post_surgery_tool")
        if post_tool:
            turn = (agent.get_data("_post_surgery_turn") or 0) + 1
            agent.set_data("_post_surgery_turn", turn)
            if turn <= 3 and failing_tool == post_tool and consecutive >= 1:
                agent.context.log.log(
                    type="warning",
                    content=(
                        f"[SUPERVISOR] False recovery detected: '{post_tool}' failed again "
                        f"within {turn} turn(s) of surgery. Escalating directly to Tier 3."
                    ),
                    flush=True,
                )
                # Force Tier 3 threshold: skip directly to reset
                state[LOOP_TIER_KEY] = "reset"
                state.pop(LOOP_SURGERY_DONE_KEY, None)
            elif turn > 3:
                agent.set_data("_post_surgery_tool", None)
                agent.set_data("_post_surgery_turn", None)
    except Exception:
        pass



def _get_profile_store(agent):
    """
    Get or initialize the session's ProfileStore. Cached on the agent attribute
    so it's loaded once per session and reused across supervisor invocations.
    Returns None on import failure so callers degrade gracefully.
    """
    try:
        store = getattr(agent, "_success_profile_store", None)
        if store is None:
            from success_profile_store import ProfileStore
            store = ProfileStore()
            setattr(agent, "_success_profile_store", store)
        return store
    except Exception:
        return None


def _process_episode_buffer(agent, profile_store):
    """
    Drain the success episode buffer accumulated by the fallback logger.
    Called at the start of each supervisor check (every 3 turns).
    Records each episode into the profile store and flushes to disk.

    Buffer format: list of dicts with {tool_name, failure_count, compound_domain}
    Written by: _30_tool_fallback_logger.py on successful tool execution
    after >= 1 consecutive failures.
    """
    if profile_store is None:
        return
    try:
        buffer = agent.get_data("_success_episode_buffer") or []
        if not buffer:
            return
        # Clear buffer before processing to avoid double-recording if an exception fires mid-loop
        agent.set_data("_success_episode_buffer", [])
        for episode in buffer:
            tool_name = episode.get("tool_name", "")
            failure_count = episode.get("failure_count", 0)
            compound_domain = episode.get("compound_domain", "")
            if not tool_name:
                continue
            try:
                profile = profile_store.record_episode(tool_name, failure_count, compound_domain)
                agent.context.log.log(
                    type="info",
                    content=(
                        f"[SUPERVISOR] Phase 3 observation: {tool_name}"
                        f"/{compound_domain or 'default'} "
                        f"failures_before_success={failure_count} "
                        f"n={profile.observation_count} "
                        f"p50={profile.p50:.1f} p90={profile.p90:.1f}"
                    ),
                    flush=True,
                )
            except Exception:
                pass
        profile_store.flush()
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


def _get_last_tool_output(agent) -> str:
    """
    Extract the last non-response tool output from agent message history.
    Trimmed to 600 chars so the injection stays bounded.
    Used by _inject_loop to give the model concrete diagnostic context,
    not just a meta-instruction. A model with new information breaks the
    fixed point; a model with only a warning repeats itself.
    """
    try:
        msgs = agent.history.current.messages
        for msg in reversed(msgs):
            if not getattr(msg, "ai", False):
                continue
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            # Skip final response tool messages — they're user-facing summaries, not errors
            if '"tool_name": "response"' in content or "'tool_name': 'response'" in content:
                continue
            trimmed = content.strip()
            if len(trimmed) > 600:
                trimmed = trimmed[:600] + "\n...(trimmed)"
            return trimmed
    except Exception:
        pass
    return ""


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

    # Prepend last tool output so the model has concrete diagnostic content.
    last_output = _get_last_tool_output(agent)
    if last_output:
        msg = f"[LAST TOOL OUTPUT]\n{last_output}\n[/LAST TOOL OUTPUT]\n\n" + msg

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


# ── Phase 4: Parallel LLM Supervisor ─────────────────────────────────────────

def _scan_recent_history(agent, window: int = 30) -> dict:
    """
    Scan the last N conversation messages for Phase 4 context signals.
    Returns operator_confirmations, files_read_count, code_written bool,
    agent_self_diagnosis bool, and last_proposal_hash.
    """
    result = {
        "operator_confirmations": 0,
        "files_read_count": 0,
        "code_written": False,
        "agent_self_diagnosis": False,
        "last_proposal_hash": None,
    }
    try:
        msgs = agent.history.current.messages
        scan = list(msgs)[-window:] if len(msgs) > window else list(msgs)
        for msg in scan:
            ai = getattr(msg, "ai", False)
            raw = msg.content if isinstance(msg.content, str) else str(msg.content or "")
            low = raw.lower()
            if not ai:
                # Operator message — check for confirmation language
                words = set(low.split())
                if words & _CONFIRMATION_SIGNALS:
                    result["operator_confirmations"] += 1
            else:
                # Agent message — detect behavioral signals
                if ("document_query" in low or
                        ("code_execution" in low and
                         any(kw in low for kw in ["cat ", "head ", "read ", "open(", "with open"]))):
                    result["files_read_count"] += 1
                if any(kw in low for kw in [
                    "write_to_file", "with open(", "echo >", "cat >", "heredoc",
                    "created file", "wrote file", "written to",
                ]):
                    result["code_written"] = True
                if any(kw in low for kw in [
                    "stuck in a loop", "breaking out", "i've been stuck",
                    "i'm stuck", "different approach", "circular", "i realize i",
                ]):
                    result["agent_self_diagnosis"] = True
                # Strategy hash — hash last response tool content for MACRO_CYCLE
                tool_name = getattr(msg, "tool_name", None) or ""
                if "response" in tool_name.lower():
                    import hashlib
                    result["last_proposal_hash"] = hashlib.md5(
                        raw[:300].encode("utf-8", errors="replace")
                    ).hexdigest()[:8]
    except Exception:
        pass
    return result


def _build_phase4_context(agent, ctx: dict, effective_domain: str, state: dict) -> str:
    """
    Assemble the compressed context string (~300-500 tokens) for the Phase 4 supervisor.
    Contains only the signals needed to recognise strategic failure patterns.
    """
    hs = _scan_recent_history(agent)

    # BST momentum
    bst_momentum = 0
    try:
        store = getattr(agent, BST_STORE_KEY, {}) or {}
        belief = store.get(BST_BELIEF_KEY, {})
        bst_momentum = belief.get("momentum", 0) or 0
    except Exception:
        pass

    # Total consecutive failures
    failures_raw = ctx.get("tool_failures") or {}
    consecutive_map = failures_raw.get("consecutive") or {}
    total_failures = sum(consecutive_map.values()) if consecutive_map else 0

    # Recent error sample (last 3 unique, 80 chars each)
    error_sample: list = []
    try:
        history = ctx.get("failure_history", [])
        seen: set = set()
        for entry in reversed(history[-10:]):
            err = entry.get("error", "") if isinstance(entry, dict) else str(entry)
            short = err[:80]
            if short and short not in seen:
                error_sample.append(short)
                seen.add(short)
            if len(error_sample) >= 3:
                break
    except Exception:
        pass

    # Stagnation status
    stagnating = False
    try:
        hashes = ctx.get("tool_output_hashes", [])
        stag = _detect_output_stagnation(hashes)
        stagnating = stag.get("stagnating", False)
    except Exception:
        pass

    # MACRO_CYCLE detection: current hash seen before?
    prev_hashes = state.get("_p4_strategy_hashes", [])
    current_hash = hs["last_proposal_hash"]
    macro_cycle_signal = bool(current_hash and current_hash in prev_hashes)

    lines = [
        "[PHASE 4 SUPERVISOR CONTEXT]",
        f"BST: {ctx.get('bst_domain') or 'none'} | effective: {effective_domain or 'none'} | momentum: {bst_momentum}",
        f"Failure count: {total_failures} | Loop tier: {state.get(LOOP_TIER_KEY, 'none')} | Stagnating: {stagnating}",
        f"Operator confirmations (recent window): {hs['operator_confirmations']}",
        f"Files read (recent): {hs['files_read_count']} | Code written: {hs['code_written']}",
        f"Agent self-diagnosis present: {hs['agent_self_diagnosis']}",
        f"Strategy hash: {current_hash or 'none'} | Previously seen (MACRO_CYCLE signal): {macro_cycle_signal}",
    ]
    if error_sample:
        lines.append(f"Recent errors (sample): {' | '.join(error_sample)}")

    return "\n".join(lines)


def _should_trigger_phase4(ctx: dict, state: dict, agent) -> bool:
    """
    Gate — Phase 4 has latency cost (~2-4s). Fire only when a strategic
    evaluation is warranted. Any one trigger is sufficient.
    """
    turn = state.get("turn", 0)

    # Never fire in first 3 turns (let agent orient)
    if turn < PHASE4_MIN_TURN:
        return False

    # Don't fire if Phases 1-3 have already escalated to Tier 2+
    if state.get(LOOP_TIER_KEY, "none") in ("summarize", "reset"):
        return False

    # Trigger 1: failure accumulation without Phase 1-3 escalation
    failures_raw = ctx.get("tool_failures") or {}
    consecutive_map = failures_raw.get("consecutive") or {}
    if max(consecutive_map.values(), default=0) >= PHASE4_MIN_FAILURES_TRIGGER:
        return True

    # Trigger 2: loop detector already fired this session
    if state.get("_p4_loop_fired"):
        return True

    # Trigger 3: operator confirmed 2+ times (scan and update state on every evaluation)
    hs_quick = _scan_recent_history(agent, window=10)
    state["_p4_confirmations_seen"] = hs_quick["operator_confirmations"]
    if state["_p4_confirmations_seen"] >= PHASE4_CONFIRMATION_TRIGGER:
        return True

    # Trigger 4: extended BST momentum in one domain
    try:
        store = getattr(agent, BST_STORE_KEY, {}) or {}
        belief = store.get(BST_BELIEF_KEY, {})
        if (belief.get("momentum") or 0) >= PHASE4_BST_MOMENTUM_TRIGGER:
            return True
    except Exception:
        pass

    return False


async def _call_phase4_supervisor(compressed_context: str) -> dict:
    """
    Fire the parallel LLM supervisor with compressed context only.
    Returns structured recommendation dict. Never raises — HOLD on any failure.
    """
    import re as _re
    import json as _json

    try:
        import aiohttp
    except ImportError:
        return {"action": "HOLD", "reason": "aiohttp_unavailable"}

    payload = {
        "model": PHASE4_MODEL,
        "messages": [
            {"role": "system", "content": PHASE4_SYSTEM_PROMPT},
            {"role": "user", "content": compressed_context},
        ],
        "max_tokens": PHASE4_MAX_TOKENS,
        "temperature": PHASE4_TEMPERATURE,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                PHASE4_LM_ENDPOINT,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=PHASE4_TIMEOUT),
            ) as resp:
                if resp.status != 200:
                    return {"action": "HOLD", "reason": f"lm_status_{resp.status}"}
                data = await resp.json()
                text = data["choices"][0]["message"]["content"]
                # Strip thinking tokens (distill model)
                text = _re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
                # Extract first JSON object
                m = _re.search(r"\{[\s\S]+?\}", text)
                if m:
                    return _json.loads(m.group())
                return {"action": "HOLD", "reason": "no_json_in_response"}
    except Exception as e:
        return {"action": "HOLD", "reason": f"call_error:{str(e)[:60]}"}


def _apply_phase4_recommendation(agent, recommendation: dict, state: dict):
    """
    Translate Phase 4 LLM recommendation into deterministic tier actions.
    The LLM advises. This function enforces.
    """
    action = recommendation.get("action", "HOLD")
    confidence = float(recommendation.get("confidence") or 0.0)

    if action == "ESCALATE" and confidence >= PHASE4_ESCALATION_CONFIDENCE:
        intervention = recommendation.get("intervention", "")
        pattern = recommendation.get("pattern_matched") or ""
        reason = recommendation.get("reason", "")
        tag = f"[SUPERVISOR-P4{' ' + pattern if pattern else ''}]"
        msg = f"{tag} {intervention or reason or 'Strategic pattern detected — reassess current approach.'}"
        _emit(agent, msg, ANOMALY_PHASE4, state)

    elif action == "DEESCALATE" and confidence >= PHASE4_DEESCALATION_CONFIDENCE:
        # Clear Tier 1 loop warning cooldown so the next genuine detection can fire
        state.get("cooldowns", {}).pop(ANOMALY_LOOP, None)
        try:
            agent.context.log.log(
                type="info",
                content=f"[SUPERVISOR-P4] DEESCALATE confidence={confidence:.2f}",
                flush=True,
            )
        except Exception:
            pass

    else:
        # HOLD — no intervention, but mark cooldown so Phase 4 doesn't fire every
        # turn while trigger conditions persist. Without this, HOLD responses cause
        # a Phase 4 LLM call on every single turn once momentum crosses the threshold.
        _mark_cooldown(state, ANOMALY_PHASE4)


def _update_phase4_strategy_hashes(agent, state: dict):
    """
    Update rolling strategy hash list for MACRO_CYCLE detection.
    Called after each Phase 4 evaluation.
    """
    try:
        hs = _scan_recent_history(agent, window=5)
        h = hs.get("last_proposal_hash")
        if h:
            prev = state.get("_p4_strategy_hashes", [])
            if h not in prev:
                prev.append(h)
            state["_p4_strategy_hashes"] = prev[-10:]  # rolling window of 10
    except Exception:
        pass


def _log_phase4_decision(agent, compressed_context: str, recommendation: dict):
    """
    Append Phase 4 decision to agent state for sleep consolidation review.
    Retrospective fields (agent_behavior_next_turn, operator_correction) are
    filled in by sleep consolidation after the session.
    """
    try:
        from datetime import datetime
        log = agent.get_data("_p4_decision_log") or []
        log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "context_snapshot": compressed_context,
            "recommendation": recommendation,
            "agent_behavior_next_turn": None,
            "operator_correction_within_3_turns": None,
        })
        agent.set_data("_p4_decision_log", log[-20:])
    except Exception:
        pass
