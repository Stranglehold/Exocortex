"""
PACE Plan Generator — Per-Task Execution Blueprint
===================================================
Hook: before_main_llm_call (_14_)

Creates a locked PACE (Primary / Alternate / Contingency / Emergency) execution plan
for each new multi-step task before the first LLM call. The plan defines explicit
fallback actions at each execution step so the agent approaches failures with a
pre-committed decision tree rather than improvising under pressure.

Design principle (from Opus, 2026-04-17):
  The plan is made when the agent is thinking clearly — before execution pressure.
  When the Supervisor detects a loop or failure, it reads the current step's next
  tier and injects that specific action rather than generic steering. The agent
  doesn't improvise under stress; it executes a decision already made.

Storage:  agent._pace_plan (survives turn boundaries, locked after creation)
Injection: [PACE PLAN] block prepended to user message context (read-only)
Tier advancement: _pace_advance_tier flag (set by Supervisor on loop/stall)
New-task signal: _pace_new_task flag (set by Supervisor after Tier 3 reset)

The plan advances to the next tier when the Supervisor signals failure. When it
advances from primary → alternate, the agent executes the alternate action on the
SAME STEP — not a new step. Step advancement happens when a step is complete.
Emergency tier is always available and always means: acknowledge failure, preserve
partial work, do not fabricate.

No LLM calls. Fully deterministic. Template-based with task content from BST/WM.
Runs after BST (_11_) and Org Kernel (_12_) so domain and role are available.
Runs before HTN planner (_15_) so the workflow engine has PACE context.
"""

import hashlib
import re
import uuid
from typing import Optional

from agent import Agent, LoopData
from helpers.extension import Extension

CONFIG_KEY = "pace_plan_generator"

# Domains that warrant PACE planning
PACE_DOMAINS = {
    "investigation", "analysis", "research",
    "coding", "bugfix", "system_admin",
    "planning", "agentic",
}

# Tier escalation order
TIERS = ["primary", "alternate", "contingency", "emergency"]

# Map tier names to _org_pace_level values (Supervisor PACE gate)
TIER_TO_ORG_PACE = {
    "primary":     "primary",
    "alternate":   "alternate",
    "contingency": "contingent",
    "emergency":   "emergency",
}

# ── Domain Templates ──────────────────────────────────────────────────────────
# Three steps per domain: Prepare → Execute → Deliver
# Each step has P/A/C/E tiers. Content is generic but readable.

DOMAIN_TEMPLATES = {
    "investigation": [
        {
            "name": "Gather Intelligence",
            "primary":     "Use available tools (OSS, search_engine, document_query) to collect current data on the task objective",
            "alternate":   "Try different tools or query variations — if OSS unavailable, use search_engine with targeted queries",
            "contingency": "Load from memory_load to retrieve prior sessions on this topic; use as partial context",
            "emergency":   "Report what is known from context only. State data gap explicitly. Do NOT synthesize from training data.",
        },
        {
            "name": "Analyze Findings",
            "primary":     "Synthesize gathered data into structured findings; cite each claim's source",
            "alternate":   "Partial synthesis using highest-confidence data only; flag every gap explicitly",
            "contingency": "Present raw collected data with minimal synthesis; note all analytical limitations",
            "emergency":   "Report what data was collected. State that full analysis cannot proceed. Ask for guidance.",
        },
        {
            "name": "Report Results",
            "primary":     "Write structured output to the requested file or format",
            "alternate":   "Respond inline with findings if file write fails",
            "contingency": "Abbreviated bullet-point summary of key findings only",
            "emergency":   "State what was completed and what remains. Preserve all partial results. Stop here.",
        },
    ],
    "analysis": [
        {
            "name": "Load Context",
            "primary":     "Load all relevant context via tools, memory_load, and provided data",
            "alternate":   "Work with available context; explicitly flag what is missing",
            "contingency": "Proceed with known context only; note limitations at the top of the output",
            "emergency":   "Report context gaps. Ask for additional information before proceeding.",
        },
        {
            "name": "Perform Analysis",
            "primary":     "Deep analysis using all available data; cite sources for each claim",
            "alternate":   "Targeted analysis on highest-confidence data points only",
            "contingency": "Surface-level observations with explicit uncertainty flags on each claim",
            "emergency":   "State what analysis is possible and what cannot be determined. Do NOT fill gaps with assumptions.",
        },
        {
            "name": "Produce Output",
            "primary":     "Write structured report with findings, confidence levels, and recommendations",
            "alternate":   "Bulleted summary of key findings with confidence indicators",
            "contingency": "Single-paragraph summary with uncertainty flags",
            "emergency":   "Raw data plus statement of analytical limitations. Ask user how to proceed.",
        },
    ],
    "coding": [
        {
            "name": "Design",
            "primary":     "Plan the implementation: identify modules, functions, data flow, and edge cases",
            "alternate":   "Simplify scope — identify the minimum viable implementation that satisfies requirements",
            "contingency": "Write pseudocode/specification; verify with user before writing executable code",
            "emergency":   "Report design constraints and ask for clarification before writing any code",
        },
        {
            "name": "Implement",
            "primary":     "Write code section by section (<=50 lines each); verify each section executes before continuing",
            "alternate":   "Write smaller sections (<=30 lines); test each in isolation using code_execution_tool",
            "contingency": "Write core logic only; omit error handling and edge cases; note explicitly what is omitted",
            "emergency":   "Write a stub with TODO comments. File partial work. Report what is missing.",
        },
        {
            "name": "Verify and Deliver",
            "primary":     "Run code, verify output matches requirements, fix any failures",
            "alternate":   "Run the core execution path only; note which edge cases are untested",
            "contingency": "Code review only — describe what should work and what is untested; do not claim verified",
            "emergency":   "File the code as-is. Report it is unverified. Ask user to test before relying on it.",
        },
    ],
    "planning": [
        {
            "name": "Assess Requirements",
            "primary":     "Assess full requirements, constraints, and measurable success criteria",
            "alternate":   "Assess minimum requirements only; flag unknowns explicitly",
            "contingency": "State assumptions and proceed with best estimate; mark all assumptions clearly",
            "emergency":   "Request clarification on ambiguous requirements before proceeding",
        },
        {
            "name": "Build Plan",
            "primary":     "Create detailed multi-step plan with verification criteria at each step",
            "alternate":   "Create simplified plan with key milestones only",
            "contingency": "Create a single-phase plan for the immediate next action only",
            "emergency":   "Propose the smallest possible next step; ask for confirmation before doing anything",
        },
        {
            "name": "Validate",
            "primary":     "Verify plan against requirements; identify risks; finalize",
            "alternate":   "Identify top 3 risks; note unvalidated assumptions",
            "contingency": "Mark plan as draft; flag all unvalidated sections",
            "emergency":   "Present as rough draft requiring review. Do not execute until confirmed.",
        },
    ],
    "research": [
        {
            "name": "Define Scope",
            "primary":     "Identify key questions and required sources; confirm scope before searching",
            "alternate":   "Narrow scope to the most critical question only",
            "contingency": "Work from a single highest-priority question",
            "emergency":   "Confirm research scope with user before beginning any information gathering",
        },
        {
            "name": "Collect",
            "primary":     "Search multiple sources; cross-reference and verify findings",
            "alternate":   "Single primary source with noted limitations",
            "contingency": "Memory recall only — flag as potentially outdated",
            "emergency":   "Report what is already known; state what requires live data to answer",
        },
        {
            "name": "Synthesize",
            "primary":     "Synthesize findings with citations into structured output",
            "alternate":   "Key findings with confidence ratings; skip low-confidence items",
            "contingency": "Bullet list of collected facts; no synthesis — let user interpret",
            "emergency":   "Raw notes only. State that synthesis cannot be completed without more data.",
        },
    ],
}

# Compound domain resolution: pick highest-priority template
_TEMPLATE_PRIORITY = ["investigation", "coding", "analysis", "planning", "research"]
_DOMAIN_ALIAS = {
    "bugfix":        "coding",
    "system_admin":  "coding",
    "agentic":       "investigation",
}


class PacePlanGenerator(Extension):
    """Generate and inject a per-task PACE execution plan before each LLM call."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            if self.agent.get_data(Agent.DATA_NAME_SUPERIOR) is not None:
                return  # subordinate context — skip PACE planning overhead (DEC-028)
            cfg = _load_config(self.agent)
            if not cfg.get("enabled", True):
                return

            domain = _get_bst_domain(loop_data, self.agent)
            if domain == "unknown":
                return
            if not any(d in domain for d in PACE_DOMAINS):
                return

            user_msg = _get_last_user_message(loop_data.history_output)
            if not user_msg:
                return

            msg_content = _extract_message_content(user_msg)
            msg_hash = _hash_message(msg_content)

            existing = getattr(self.agent, "_pace_plan", None)
            is_new = _is_new_task(existing, msg_hash, self.agent)

            if is_new:
                plan = _create_plan(domain, msg_content, msg_hash)
                setattr(self.agent, "_pace_plan", plan)
                print(
                    f"[PACE] New plan {plan['plan_id'][:8]} "
                    f"domain={domain} steps={len(plan['steps'])}",
                    flush=True,
                )
            else:
                plan = existing
                # Advance tier if Supervisor flagged a failure last turn
                advanced = _maybe_advance_tier(plan, self.agent)
                if advanced:
                    # Sync _org_pace_level so Supervisor PACE gate fires correctly
                    _sync_org_pace_level(plan, self.agent)
                    print(
                        f"[PACE] Tier → {plan['active_tier']} "
                        f"step={plan['current_step']} "
                        f"escalations={plan.get('tier_escalations', 0)}",
                        flush=True,
                    )

            # Inject into context (read-only view for the model)
            block = _build_injection_block(plan)
            existing_content = user_msg.get("content", "")
            user_msg["content"] = block + "\n\n" + str(existing_content)

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[PACE] Error (passthrough): {e}",
                )
            except Exception:
                pass


# ── Plan Creation ──────────────────────────────────────────────────────────────

def _create_plan(domain: str, task_summary: str, task_hash: str) -> dict:
    """Create a new locked PACE plan for this task."""
    template_key = _resolve_template_key(domain)
    steps = DOMAIN_TEMPLATES.get(template_key, DOMAIN_TEMPLATES["investigation"])

    return {
        "plan_id":          str(uuid.uuid4()),
        "task_hash":        task_hash,
        "task_summary":     task_summary[:200],
        "domain":           domain,
        "locked":           True,
        "completed":        False,
        "steps":            [
            {
                "step":        i + 1,
                "name":        s["name"],
                "primary":     s["primary"],
                "alternate":   s["alternate"],
                "contingency": s["contingency"],
                "emergency":   s["emergency"],
            }
            for i, s in enumerate(steps)
        ],
        "current_step":     1,
        "active_tier":      "primary",
        "tier_escalations": 0,
    }


def _resolve_template_key(domain: str) -> str:
    """Resolve domain string (possibly compound) to a template key."""
    if domain in _DOMAIN_ALIAS:
        return _DOMAIN_ALIAS[domain]
    if "+" in domain:
        parts = [p.strip() for p in domain.split("+")]
        for priority in _TEMPLATE_PRIORITY:
            if priority in parts:
                return priority
        # Alias resolution for compound parts
        for p in parts:
            aliased = _DOMAIN_ALIAS.get(p, p)
            if aliased in DOMAIN_TEMPLATES:
                return aliased
    return domain if domain in DOMAIN_TEMPLATES else "investigation"


def _is_new_task(existing: Optional[dict], msg_hash: str, agent) -> bool:
    """
    True if a new PACE plan should be created.
    Conditions: no plan, completed plan, changed task hash, or Supervisor reset flag.
    """
    if not existing:
        return True
    if existing.get("completed", False):
        return True
    if existing.get("task_hash") != msg_hash:
        return True
    try:
        if agent.get_data("_pace_new_task"):
            agent.set_data("_pace_new_task", False)
            return True
    except Exception:
        pass
    return False


def _maybe_advance_tier(plan: dict, agent) -> bool:
    """
    Advance active_tier if the Supervisor set _pace_advance_tier.
    Returns True if tier was advanced, False otherwise.
    """
    try:
        if not agent.get_data("_pace_advance_tier"):
            return False
        agent.set_data("_pace_advance_tier", False)

        current = plan.get("active_tier", "primary")
        idx = TIERS.index(current) if current in TIERS else 0
        if idx < len(TIERS) - 1:
            plan["active_tier"] = TIERS[idx + 1]
            plan["tier_escalations"] = plan.get("tier_escalations", 0) + 1
            return True
    except Exception:
        pass
    return False


def _sync_org_pace_level(plan: dict, agent):
    """
    Keep _org_pace_level in sync with the task-level active_tier so the
    Supervisor's PACE gate (_inject_pace_contingent / _inject_pace_emergency)
    fires when appropriate.
    """
    try:
        active_tier = plan.get("active_tier", "primary")
        org_level = TIER_TO_ORG_PACE.get(active_tier, "primary")
        setattr(agent, "_org_pace_level", org_level)
    except Exception:
        pass


# ── Block Construction ─────────────────────────────────────────────────────────

def _build_injection_block(plan: dict) -> str:
    """Build the [PACE PLAN] read-only context block."""
    current_step = plan.get("current_step", 1)
    active_tier  = plan.get("active_tier", "primary")
    steps        = plan.get("steps", [])
    total        = len(steps)
    escalations  = plan.get("tier_escalations", 0)
    esc_note     = f" | Escalations: {escalations}" if escalations > 0 else ""

    lines = [
        "[PACE PLAN — ACTIVE]",
        f"Task: {plan.get('task_summary', '')[:140]}",
        f"Domain: {plan.get('domain', '?')} | Step: {current_step}/{total} | "
        f"Active Tier: {active_tier.upper()}{esc_note}",
        "",
    ]

    for step in steps:
        n    = step["step"]
        name = step["name"]
        current_marker = " ◄ CURRENT" if n == current_step else ""
        lines.append(f"Step {n} — {name}{current_marker}")
        for tier in TIERS:
            label = f"  {'PACE'[TIERS.index(tier)]}({tier})"
            action = step.get(tier, "")
            if tier == active_tier and n == current_step:
                lines.append(f"{label}: {action}  ← EXECUTE THIS TIER")
            else:
                lines.append(f"{label}: {action}")
        lines.append("")

    lines += [
        "RULES:",
        "• If blocked at current tier, set _pace_advance_tier and execute the next tier on this same step.",
        "• Emergency is always available — acknowledge failure and preserve partial work. Never fabricate.",
        "• Do not skip to a new step until the current step's active tier has been attempted.",
        "[/PACE PLAN]",
    ]

    return "\n".join(lines)


# ── Helper Functions ───────────────────────────────────────────────────────────

def _get_bst_domain(loop_data: LoopData, agent) -> str:
    try:
        ep = getattr(loop_data, "extras_persistent", None) or {}
        domain = ep.get("_bst_domain")
        if domain:
            return str(domain)
    except Exception:
        pass
    try:
        store = getattr(agent, "_bst_store", None) or {}
        belief = store.get("__bst_belief_state__")
        if belief and hasattr(belief, "primary_domain"):
            return str(belief.primary_domain)
        if isinstance(belief, dict):
            return str(belief.get("domain", "unknown"))
    except Exception:
        pass
    return "unknown"


def _get_last_user_message(history_output: list) -> Optional[dict]:
    if not history_output:
        return None
    for msg in reversed(history_output):
        if not isinstance(msg, dict):
            continue
        if not msg.get("ai", True):
            content = msg.get("content", "")
            if isinstance(content, dict) and "user_message" in content:
                return msg
            if isinstance(content, str) and content:
                return msg
    return None


def _extract_message_content(msg: dict) -> str:
    content = msg.get("content", "")
    if isinstance(content, dict):
        return str(content.get("user_message", ""))
    return str(content)


def _hash_message(content: str) -> str:
    """Short hash of the task message for change detection. Strips injected blocks."""
    clean = re.sub(r"\[PACE PLAN.*?\[/PACE PLAN\]", "", content, flags=re.DOTALL)
    clean = re.sub(r"\[MODEL CONFIGURATION\].*?EI active.*?\n", "", clean, flags=re.DOTALL)
    clean = clean.strip()[:500]
    return hashlib.md5(clean.encode("utf-8", errors="replace")).hexdigest()[:12]


def _load_config(agent) -> dict:
    try:
        cfg = getattr(agent, "config", None)
        if cfg is None:
            return {}
        raw = cfg if isinstance(cfg, dict) else vars(cfg)
        return raw.get(CONFIG_KEY, {})
    except Exception:
        return {}


# ── Public API for Supervisor ──────────────────────────────────────────────────

def get_current_step_action(agent, tier: str) -> str:
    """
    Return the action string for the current step at the given tier.
    Called by the Supervisor to inject specific guidance instead of generic steering.
    Returns empty string if no plan or no action available.
    """
    plan = getattr(agent, "_pace_plan", None)
    if not plan or plan.get("completed"):
        return ""
    current_step = plan.get("current_step", 1)
    for step in plan.get("steps", []):
        if step["step"] == current_step:
            return step.get(tier, "")
    return ""


def get_plan_context(agent) -> dict:
    """Return a summary dict of the current PACE plan state for the Supervisor."""
    plan = getattr(agent, "_pace_plan", None)
    if not plan:
        return {}
    return {
        "plan_id":       plan.get("plan_id", "")[:8],
        "current_step":  plan.get("current_step", 1),
        "active_tier":   plan.get("active_tier", "primary"),
        "escalations":   plan.get("tier_escalations", 0),
        "domain":        plan.get("domain", ""),
        "total_steps":   len(plan.get("steps", [])),
    }
