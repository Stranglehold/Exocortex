"""
Graph Workflow Engine — Agent-Zero Cognitive Architecture
=========================================================
Hook: before_main_llm_call (_15_)

Drop-in replacement for the linear HTN Plan Selector.
Reads BST domain classification, matches plan templates,
and either:
  - Traverses a directed graph workflow (plans with `graph` field)
  - Runs the original linear step engine (plans with `steps` field)

Graph plans enable branching, retry loops, conditional paths,
and escalation nodes that linear plans cannot express.

Runs after BST (_10_) and org dispatcher (_12_), before context
watchdog (_20_). Zero model reasoning. Pure dict lookups and
string matching.
"""

import json
from pathlib import Path
from typing import Any

from agent import LoopData
from python.helpers.extension import Extension

PLAN_LIBRARY_PATH = Path(__file__).parent / "htn_plan_library.json"
HTN_STATE_KEY = "_htn_state"
BST_STORE_KEY = "_bst_store"
BST_BELIEF_KEY = "__bst_belief_state__"
PACE_LEVEL_KEY = "_org_pace_level"

# Event log cap
MAX_EVENTS = 50

# Maximum auto-route depth (prevents infinite loops through decision chains)
MAX_ROUTE_DEPTH = 15


class HTNPlanSelector(Extension):
    """Graph workflow engine with linear plan backward compatibility."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
        try:
            library = _load_library()
            if not library:
                return

            state = _get_state(self.agent)

            # Active plan — check progress
            if state:
                mode = state.get("mode", "linear")
                if mode == "graph":
                    _check_graph_progress(self.agent, state, loop_data, library)
                else:
                    _check_linear_progress(self.agent, state, loop_data, library)
                return

            # No active plan — try to match one
            domain = _get_bst_domain(self.agent)
            message = _get_user_message(loop_data)
            if not message:
                return

            plan_id, plan = _match_plan(library, domain, message, self.agent)
            if not plan_id or not plan:
                return

            if "graph" in plan:
                state = _create_graph_state(self.agent, plan_id, plan)
                _advance_from_start(self.agent, state, plan)
                _inject_graph_context(loop_data, state, plan)
                _set_state(self.agent, state)
                self.agent.context.log.log(
                    type="info",
                    content=f"[HTN] Graph plan activated: {plan.get('name', plan_id)} ({state['total_steps']} nodes)"
                )
            elif "steps" in plan:
                state = _create_linear_state(self.agent, plan_id, plan)
                _inject_linear_context(loop_data, state, library)
                self.agent.context.log.log(
                    type="info",
                    content=f"[HTN] Linear plan activated: {plan.get('name', plan_id)} ({len(plan['steps'])} steps)"
                )

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[HTN] Error (passthrough): {e}"
                )
            except Exception:
                pass


# ── Library Loading ──────────────────────────────────────────────

_library_cache = None

def _load_library() -> dict | None:
    global _library_cache
    if _library_cache is not None:
        return _library_cache
    try:
        with open(PLAN_LIBRARY_PATH, "r", encoding="utf-8") as f:
            _library_cache = json.load(f)
        return _library_cache
    except Exception:
        return None


# ── BST Integration ──────────────────────────────────────────────

def _get_bst_domain(agent) -> str:
    try:
        store = getattr(agent, BST_STORE_KEY, {})
        belief = store.get(BST_BELIEF_KEY, {})
        return belief.get("domain", "")
    except Exception:
        return ""


# ── User Message Extraction ─────────────────────────────────────

def _get_user_message(loop_data: LoopData) -> str:
    if not loop_data.history_output:
        return ""
    for msg in reversed(loop_data.history_output):
        if not isinstance(msg, dict):
            continue
        if msg.get("ai", True):
            continue
        content = msg.get("content", "")
        if isinstance(content, dict):
            content = content.get("user_message", "") or content.get("message", "")
        return str(content).strip().lower()
    return ""


# ── Plan Matching ────────────────────────────────────────────────

def _match_plan(library: dict, domain: str, message: str, agent=None) -> tuple:
    """Match message against plan library. Returns (plan_id, plan) or (None, None)."""
    plans = library.get("plans", {})
    best_id = None
    best_score = 0

    # Org kernel HTN filter
    allowed_plans = None
    if agent:
        try:
            allowed_plans = agent.get_data("_org_htn_allowed_plans")
        except Exception:
            pass

    for plan_id, plan in plans.items():
        if allowed_plans is not None and plan_id not in allowed_plans:
            continue

        plan_domains = plan.get("domains", [])
        domain_match = not plan_domains or domain in plan_domains

        triggers = plan.get("triggers", [])
        threshold = plan.get("trigger_threshold", 2)
        hits = sum(1 for t in triggers if t in message)

        if hits >= threshold and domain_match:
            score = hits + (1.0 if domain_match and plan_domains else 0)
            if score > best_score:
                best_score = score
                best_id = plan_id

    if best_id:
        return best_id, plans[best_id]
    return None, None


# ── State Management ─────────────────────────────────────────────

def _get_state(agent) -> dict | None:
    try:
        return getattr(agent, HTN_STATE_KEY, None)
    except Exception:
        return None

def _set_state(agent, state: dict):
    setattr(agent, HTN_STATE_KEY, state)

def _clear_state(agent):
    try:
        if hasattr(agent, HTN_STATE_KEY):
            delattr(agent, HTN_STATE_KEY)
    except Exception:
        pass


# ── Graph State Creation ────────────────────────────────────────

def _create_graph_state(agent, plan_id: str, plan: dict) -> dict:
    graph = plan["graph"]
    nodes = graph.get("nodes", {})
    # Count task nodes only (decision nodes are auto-routed, not counted for progress)
    task_count = sum(1 for n in nodes.values() if n.get("type") == "task")

    state = {
        "plan_id": plan_id,
        "plan_name": plan.get("name", plan_id),
        "mode": "graph",

        # Backward compat fields (supervisor + SALUTE read these)
        "current_step": 0,
        "total_steps": task_count,
        "turns_since_progress": 0,
        "steps_completed": [],
        "steps_failed": [],
        "stale_after_turns": plan.get("stale_after_turns", 15),
        "iteration_started": 0,

        # Graph-specific fields
        "current_node": graph.get("start", ""),
        "visited": {},
        "path": [graph.get("start", "")],
        "total_nodes": task_count,
        "completed_nodes": 0,
        "turns_since_transition": 0,

        # Event log
        "events": [],
    }
    _emit_event(state, "plan_activated", node=graph.get("start", ""), plan=plan_id)
    _set_state(agent, state)
    return state


# ── Linear State Creation ───────────────────────────────────────

def _create_linear_state(agent, plan_id: str, plan: dict) -> dict:
    state = {
        "plan_id": plan_id,
        "plan_name": plan.get("name", plan_id),
        "mode": "linear",
        "domain": plan.get("domains", [""])[0] if plan.get("domains") else "",
        "current_step": 0,
        "steps_completed": [],
        "steps_failed": [],
        "total_steps": len(plan.get("steps", [])),
        "stale_after_turns": plan.get("stale_after_turns", 10),
        "turns_since_progress": 0,
        "iteration_started": 0,
    }
    _set_state(agent, state)
    return state


# ── Tool Output Extraction ──────────────────────────────────────

def _get_last_tool_output(loop_data: LoopData) -> str | None:
    if not loop_data.history_output:
        return None
    for msg in reversed(loop_data.history_output):
        if not isinstance(msg, dict):
            continue
        content = msg.get("content", "")
        if isinstance(content, dict):
            if "tool_name" in content:
                return str(content.get("tool_result", content.get("output", content.get("result", ""))))
        if isinstance(content, str) and content.startswith("[tool_result"):
            return content
    return None


# ── Verification ─────────────────────────────────────────────────

def _verify_node(node: dict, output: str) -> bool:
    """Run verification check on tool output. Used by both linear and graph engines."""
    verify = node.get("verify")
    if not verify:
        return True

    vtype = verify.get("type", "any_output")
    value = verify.get("value", "")
    output_lower = output.lower()

    if vtype == "output_contains":
        return value.lower() in output_lower
    elif vtype == "output_not_contains":
        return value.lower() not in output_lower
    elif vtype == "exit_code_zero":
        return "error" not in output_lower and "exit code" not in output_lower
    elif vtype == "any_output":
        return bool(output.strip())
    elif vtype == "file_exists":
        return True
    elif vtype == "manual":
        return True
    return True


# ══════════════════════════════════════════════════════════════════
#  GRAPH WORKFLOW ENGINE
# ══════════════════════════════════════════════════════════════════

def _advance_from_start(agent, state: dict, plan: dict):
    """Advance past the start node on plan activation."""
    graph = plan["graph"]
    start_id = graph.get("start", "")
    _emit_event(state, "node_entered", node=start_id)

    # Follow the edge from start (should be 'always' or unconditional)
    target = _follow_edge(state, graph, start_id, "always")
    if target:
        _move_to_node(state, graph, start_id, target, "always")
        # Auto-route through decisions
        _auto_route(agent, state, plan)


def _check_graph_progress(agent, state: dict, loop_data: LoopData, library: dict):
    """Main graph traversal logic. Called on each before_main_llm_call with an active graph plan."""
    # Staleness check
    state["turns_since_transition"] = state.get("turns_since_transition", 0) + 1
    state["turns_since_progress"] = state.get("turns_since_progress", 0) + 1

    stale_limit = state.get("stale_after_turns", 15)
    if state["turns_since_transition"] > stale_limit:
        _emit_event(state, "plan_expired", node=state.get("current_node", ""))
        agent.context.log.log(
            type="info",
            content=f"[HTN] Graph plan '{state['plan_name']}' expired (no transition for {stale_limit} turns)"
        )
        _clear_state(agent)
        return

    plan = library.get("plans", {}).get(state["plan_id"])
    if not plan or "graph" not in plan:
        _clear_state(agent)
        return

    graph = plan["graph"]
    node_id = state.get("current_node", "")
    node = graph["nodes"].get(node_id)
    if not node:
        _clear_state(agent)
        return

    # Handle based on current node type
    ntype = node.get("type", "task")

    if ntype == "exit":
        _complete_graph(agent, state)
        return

    if ntype == "escalate":
        _escalate_graph(agent, state, node, loop_data)
        return

    if ntype == "start":
        _advance_from_start(agent, state, plan)
        _inject_graph_context(loop_data, state, plan)
        _set_state(agent, state)
        return

    if ntype == "task":
        last_output = _get_last_tool_output(loop_data)
        if last_output is not None:
            # Initialize visited entry if needed
            visited = state["visited"].setdefault(node_id, {"outcome": "pending", "attempts": 0})
            visited["attempts"] += 1
            verified = _verify_node(node, last_output)

            _emit_event(state, "node_verified", node=node_id,
                        outcome="success" if verified else "fail")

            if verified:
                visited["outcome"] = "success"
                # Only count unique node completions (handles loops)
                if node_id not in state["steps_completed"]:
                    state["completed_nodes"] = state.get("completed_nodes", 0) + 1
                    state["steps_completed"].append(node_id)
                    state["turns_since_progress"] = 0  # real progress: new node completed
                # Update compat fields
                state["current_step"] = state["completed_nodes"]

                target = _follow_edge(state, graph, node_id, "on_success", fallback="always")
                if target:
                    _move_to_node(state, graph, node_id, target, "on_success")
                    _auto_route(agent, state, plan)
                else:
                    agent.context.log.log(type="warning",
                                          content=f"[HTN] No edge from '{node_id}' on success — stalling")
            else:
                max_retries = node.get("max_retries", 0)
                if visited["attempts"] <= max_retries:
                    # Retries remain
                    _emit_event(state, "retry_triggered", node=node_id)
                    target = _follow_edge(state, graph, node_id, "on_retry")
                    if target:
                        _move_to_node(state, graph, node_id, target, "on_retry")
                        _auto_route(agent, state, plan)
                    # else: stay on current node (retry in place)
                else:
                    # Retries exhausted
                    visited["outcome"] = "fail"
                    if node_id not in state["steps_failed"]:
                        state["steps_failed"].append(node_id)
                    target = _follow_edge(state, graph, node_id, "on_exhaust",
                                          fallback="on_fail", fallback2="always")
                    if target:
                        _move_to_node(state, graph, node_id, target, "on_exhaust")
                        _auto_route(agent, state, plan)
                    else:
                        agent.context.log.log(type="warning",
                                              content=f"[HTN] No edge from '{node_id}' on exhaust — stalling")

    elif ntype == "decision":
        _auto_route(agent, state, plan)

    # Check if we've landed on a terminal node after routing
    final_node = graph["nodes"].get(state.get("current_node", ""))
    if final_node:
        if final_node["type"] == "exit":
            _complete_graph(agent, state)
            return
        if final_node["type"] == "escalate":
            _escalate_graph(agent, state, final_node, loop_data)
            return

    # Inject context for current node
    _inject_graph_context(loop_data, state, plan)
    _set_state(agent, state)


def _follow_edge(state: dict, graph: dict, from_node: str, condition: str,
                 fallback: str = "", fallback2: str = "") -> str | None:
    """Find the target node for the given edge condition from from_node."""
    edges = graph.get("edges", [])
    candidates = [e for e in edges if e.get("from") == from_node]

    # Try primary condition
    for e in candidates:
        if e.get("condition", "always") == condition:
            return e["to"]

    # Try fallback
    if fallback:
        for e in candidates:
            if e.get("condition", "always") == fallback:
                return e["to"]

    # Try second fallback
    if fallback2:
        for e in candidates:
            if e.get("condition", "always") == fallback2:
                return e["to"]

    # Try 'always' as last resort
    for e in candidates:
        if e.get("condition", "always") == "always":
            return e["to"]

    return None


def _move_to_node(state: dict, graph: dict, from_node: str, to_node: str, condition: str):
    """Move traversal to a new node. Resets transition counter."""
    state["current_node"] = to_node
    state["path"].append(to_node)
    state["turns_since_transition"] = 0
    # Note: turns_since_progress is only reset on NEW node completions, not every transition.
    # This lets the supervisor detect cycling without real progress.

    # Reset visited state for target node (handles loops: test → fix → test → fix)
    # Each visit to a node starts fresh with attempts=0
    if to_node in state.get("visited", {}):
        state["visited"][to_node] = {"outcome": "pending", "attempts": 0}

    _emit_event(state, "edge_followed", from_node=from_node, to_node=to_node, condition=condition)
    _emit_event(state, "node_entered", node=to_node)


def _auto_route(agent, state: dict, plan: dict, depth: int = 0):
    """Auto-route through decision/start/checkpoint nodes until we hit a task, exit, or escalate."""
    if depth >= MAX_ROUTE_DEPTH:
        return

    graph = plan["graph"]
    node_id = state.get("current_node", "")
    node = graph["nodes"].get(node_id)
    if not node:
        return

    ntype = node.get("type", "task")

    if ntype == "decision":
        # Route based on last outcome in the path
        last_outcome = _get_last_outcome(state)
        condition = f"on_{last_outcome}" if last_outcome else "always"
        target = _follow_edge(state, graph, node_id, condition, fallback="always")
        if target:
            _move_to_node(state, graph, node_id, target, condition)
            _auto_route(agent, state, plan, depth + 1)

    elif ntype == "start":
        target = _follow_edge(state, graph, node_id, "always")
        if target:
            _move_to_node(state, graph, node_id, target, "always")
            _auto_route(agent, state, plan, depth + 1)

    elif ntype == "checkpoint":
        # Reserved — treat as pass-through
        target = _follow_edge(state, graph, node_id, "always")
        if target:
            _move_to_node(state, graph, node_id, target, "always")
            _auto_route(agent, state, plan, depth + 1)

    # task, exit, escalate — stop routing, these need action or are terminal


def _get_last_outcome(state: dict) -> str:
    """Get the outcome of the last visited node for decision routing."""
    events = state.get("events", [])
    for event in reversed(events):
        if event.get("type") == "node_verified":
            return event.get("outcome", "success")
    return "success"


def _complete_graph(agent, state: dict):
    """Handle graph completion (exit node reached)."""
    _emit_event(state, "plan_completed", node=state.get("current_node", ""))
    agent.context.log.log(
        type="info",
        content=f"[HTN] Graph plan '{state['plan_name']}' completed! "
                f"({state.get('completed_nodes', 0)}/{state.get('total_nodes', 0)} nodes)"
    )
    _clear_state(agent)


def _escalate_graph(agent, state: dict, escalate_node: dict, loop_data: LoopData = None):
    """Handle escalation node — set PACE, log, inject message, clear plan."""
    pace_level = escalate_node.get("pace_level", "contingent")
    reason = escalate_node.get("reason", "Plan escalated")
    plan_name = state.get("plan_name", "")

    _emit_event(state, "plan_escalated", node=state.get("current_node", ""),
                reason=reason, pace_level=pace_level)

    # Set PACE level on agent
    try:
        setattr(agent, PACE_LEVEL_KEY, pace_level)
    except Exception:
        pass

    # Log escalation
    agent.context.log.log(
        type="warning",
        content=f"[HTN] Plan '{plan_name}' escalated to PACE {pace_level}: {reason}"
    )

    # Inject escalation message into extras so the model knows
    if loop_data:
        escalation_msg = (
            f"[WORKFLOW ESCALATED: {plan_name}]\n"
            f"  Reason: {reason}\n"
            f"  PACE level: {pace_level}\n"
            f"  Completed: {state.get('completed_nodes', 0)}/{state.get('total_nodes', 0)} nodes\n\n"
            f"The current approach has failed. Change strategy or ask the user for guidance."
        )
        loop_data.extras_temporary["htn_active_plan"] = escalation_msg

    _clear_state(agent)


# ── Graph Context Injection ─────────────────────────────────────

def _inject_graph_context(loop_data: LoopData, state: dict, plan: dict):
    """Build and inject graph workflow context into extras_temporary."""
    graph = plan.get("graph", {})
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", [])
    current_id = state.get("current_node", "")
    current_node = nodes.get(current_id, {})

    lines = [f"[WORKFLOW: {state.get('plan_name', '')}]"]

    # Build traversal summary: show completed path + current
    visited = state.get("visited", {})
    # Show path as compact summary
    path_parts = []
    seen = set()
    for nid in state.get("path", []):
        if nid in seen or nid not in nodes:
            continue
        seen.add(nid)
        n = nodes[nid]
        ntype = n.get("type", "")
        if ntype in ("start", "checkpoint"):
            continue
        name = n.get("name", nid)
        v = visited.get(nid, {})
        outcome = v.get("outcome", "")
        if nid == current_id:
            attempts = v.get("attempts", 0)
            max_r = n.get("max_retries", 0)
            attempt_str = f" (attempt {attempts + 1}/{max_r + 1})" if max_r > 0 else ""
            path_parts.append(f"{name} << CURRENT{attempt_str}")
        elif outcome == "success":
            path_parts.append(f"{name} [DONE]")
        elif outcome == "fail":
            path_parts.append(f"{name} [FAILED]")
        elif outcome == "pending":
            path_parts.append(f"{name} [...]")

    if path_parts:
        lines.append("  " + " → ".join(path_parts))

    # Show current node details
    if current_node.get("type") == "task":
        lines.append(f"    Action: {current_node.get('action', '')}")
        if current_node.get("tool"):
            lines.append(f"    Tool: {current_node['tool']}")
        if current_node.get("tool_hint"):
            lines.append(f"    Hint: {current_node['tool_hint']}")
        verify = current_node.get("verify", {})
        if verify.get("type") and verify["type"] != "manual":
            vdesc = verify.get("type", "")
            if verify.get("value"):
                vdesc += f": {verify['value']}"
            lines.append(f"    Verify: {vdesc}")

        # Show outgoing edges
        out_edges = [e for e in edges if e.get("from") == current_id]
        for e in out_edges:
            target_name = nodes.get(e["to"], {}).get("name", e["to"])
            target_type = nodes.get(e["to"], {}).get("type", "")
            cond = e.get("condition", "always")
            if target_type == "escalate":
                lines.append(f"    On {cond} → escalate: {target_name}")
            else:
                lines.append(f"    On {cond} → {target_name}")

    elif current_node.get("type") == "decision":
        lines.append(f"    Decision: {current_node.get('description', current_node.get('name', ''))}")

    lines.append("")
    lines.append("Execute the current step. Do not skip ahead.")

    loop_data.extras_temporary["htn_active_plan"] = "\n".join(lines)


# ── Event System ─────────────────────────────────────────────────

def _emit_event(state: dict, event_type: str, **fields):
    """Append an event to the traversal state event log."""
    events = state.setdefault("events", [])
    event = {"type": event_type, "turn": state.get("turns_since_transition", 0)}
    event.update(fields)
    events.append(event)
    # Trim to last MAX_EVENTS
    if len(events) > MAX_EVENTS:
        state["events"] = events[-MAX_EVENTS:]


# ══════════════════════════════════════════════════════════════════
#  LINEAR PLAN ENGINE (backward compatibility)
# ══════════════════════════════════════════════════════════════════

def _check_linear_progress(agent, state: dict, loop_data: LoopData, library: dict):
    """Original linear step-sequence engine. Unchanged behavior."""
    # Staleness check
    state["turns_since_progress"] = state.get("turns_since_progress", 0) + 1
    stale_limit = state.get("stale_after_turns", 10)
    if state["turns_since_progress"] > stale_limit:
        agent.context.log.log(
            type="info",
            content=f"[HTN] Plan '{state['plan_name']}' expired (no progress for {stale_limit} turns)"
        )
        _clear_state(agent)
        return

    # Plan complete check
    if state["current_step"] >= state["total_steps"]:
        agent.context.log.log(
            type="info",
            content=f"[HTN] Plan '{state['plan_name']}' completed!"
        )
        _clear_state(agent)
        return

    plan = library.get("plans", {}).get(state["plan_id"])
    if not plan or "steps" not in plan:
        _clear_state(agent)
        return

    current_idx = state["current_step"]
    step = plan["steps"][current_idx]

    last_output = _get_last_tool_output(loop_data)
    if last_output is not None:
        verified = _verify_node(step, last_output)
        if verified:
            state["steps_completed"].append(current_idx)
            state["current_step"] = current_idx + 1
            state["turns_since_progress"] = 0
            agent.context.log.log(
                type="info",
                content=f"[HTN] Step {current_idx + 1} verified: {step['name']}"
            )
            if state["current_step"] >= state["total_steps"]:
                agent.context.log.log(
                    type="info",
                    content=f"[HTN] Plan '{state['plan_name']}' completed!"
                )
                _clear_state(agent)
                return
        else:
            on_fail = step.get("on_fail", "warn")
            if on_fail == "skip":
                state["steps_failed"].append(current_idx)
                state["current_step"] = current_idx + 1
                state["turns_since_progress"] = 0
            elif on_fail == "abort":
                state["steps_failed"].append(current_idx)
                agent.context.log.log(
                    type="warning",
                    content=f"[HTN] Plan aborted: step '{step['name']}' failed verification"
                )
                _clear_state(agent)
                return

    # Inject context if plan still active
    if _get_state(agent) is None:
        return
    _inject_linear_context(loop_data, state, library)
    _set_state(agent, state)


def _inject_linear_context(loop_data: LoopData, state: dict, library: dict):
    """Build and inject linear plan context string into extras_temporary."""
    plan = library.get("plans", {}).get(state["plan_id"])
    if not plan:
        return

    lines = [f"[ACTIVE PLAN: {state['plan_name']}]"]

    for i, step in enumerate(plan.get("steps", [])):
        step_num = i + 1
        name = step.get("name", f"Step {step_num}")

        if i in state.get("steps_completed", []):
            lines.append(f"  Step {step_num}/{state['total_steps']}: {name} [DONE]")
        elif i in state.get("steps_failed", []):
            lines.append(f"  Step {step_num}/{state['total_steps']}: {name} [FAILED]")
        elif i == state["current_step"]:
            lines.append(f"  Step {step_num}/{state['total_steps']}: {name} << CURRENT")
            lines.append(f"    Action: {step.get('action', '')}")
            if step.get("tool"):
                lines.append(f"    Tool: {step['tool']}")
            if step.get("tool_hint"):
                lines.append(f"    Hint: {step['tool_hint']}")
            verify = step.get("verify", {})
            if verify.get("type") and verify["type"] != "manual":
                lines.append(f"    Verify: {verify.get('type')}: {verify.get('value', '')}")
        else:
            lines.append(f"  Step {step_num}/{state['total_steps']}: {name} [PENDING]")

    lines.append("")
    lines.append(f"Execute Step {state['current_step'] + 1} now. Do not skip ahead. Verify before proceeding.")

    loop_data.extras_temporary["htn_active_plan"] = "\n".join(lines)
