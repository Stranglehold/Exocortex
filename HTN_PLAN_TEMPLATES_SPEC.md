# HTN Plan Templates — Build Specification
## Agent-Zero Cognitive Architecture · Priority 4

---

## Problem Statement

Complex multi-step tasks cause local models to:
1. **Attempt everything at once** — cramming backup + export + import + verify into a single tool call
2. **Lose track of progress** — forgetting which steps completed after 3-4 iterations
3. **Skip verification** — moving to the next action without confirming the previous one succeeded
4. **Repeat failed steps** — no structured memory of what worked and what didn't

These failures compound: a skipped verification leads to a cascading failure three steps later, burning 5-10 tool calls before the model realizes it went wrong.

## Solution: Static Plan Library + Step Tracker

**No model reasoning required.** The model selects a plan — it doesn't generate one.

- **Plan Library:** JSON file with pre-built workflow templates, each keyed to BST domains + trigger phrases
- **Plan Selector:** Reads BST's domain classification, matches trigger phrases against the user message, injects the matching plan as structured context
- **Step Tracker:** Persists current plan state on `agent._htn_state`, tracks which steps are complete, what's active, what's next
- **Verification Gates:** Each step defines a verify condition; tool output is checked before advancing
- **Fallback Integration:** Failed verification increments the existing tool fallback chain's failure counter

---

## Architecture

### Hook Point
- **Extension:** `before_main_llm_call/_15_htn_plan_selector.py`
- **Numeric prefix:** `_15_` — runs after BST (`_10_`) but before context watchdog (`_20_`)
- **Rationale:** BST classifies domain and stores belief state on `agent._bst_store` before HTN reads it

### Data Flow
```
User message arrives
  → BST (_10_) classifies domain, stores belief in agent._bst_store
  → HTN (_15_) reads belief.domain + message text
    → Matches against plan library triggers
    → If match found:
      → Creates or resumes plan state in agent._htn_state
      → Checks last tool output against current step's verify condition
      → Advances step pointer if verified
      → Injects plan context into loop_data.extras_temporary
    → If no match: passthrough (no injection)
  → Context watchdog (_20_) runs normally
  → Model sees plan context in extras, follows step-by-step
```

### State Storage
```python
# Stored on agent._htn_state (same pattern as BST's _bst_store)
{
    "plan_id": "git_feature_branch",
    "domain": "git_ops",
    "started_turn": 42,
    "current_step": 1,          # 0-indexed
    "steps_completed": [0],     # indices of verified steps
    "steps_failed": [],         # indices of failed verifications
    "total_steps": 5,
    "last_tool_output": "",     # captured for verification
    "stale_after_turns": 10     # plan expires if no progress
}
```

### Plan Context Injection Format
Injected into `loop_data.extras_temporary["htn_active_plan"]`:
```
[ACTIVE PLAN: git_feature_branch]
Step 1 of 5: Check current branch status [COMPLETED]
Step 2 of 5: Create feature branch ← YOU ARE HERE
  Action: Create and checkout a new branch from main
  Tool: code_execution_tool (runtime: terminal)
  Command hint: git checkout -b feature/<name> main
  Verify: Branch checkout confirmed in output
Step 3 of 5: Make changes [PENDING]
Step 4 of 5: Commit changes [PENDING]
Step 5 of 5: Push and create PR [PENDING]

INSTRUCTION: Execute Step 2 now. Do not skip ahead. Verify the result before proceeding.
```

---

## Plan Library Schema

### File Location
`/a0/python/extensions/before_main_llm_call/htn_plan_library.json`

### Schema
```json
{
  "_meta": {
    "version": "1.0",
    "description": "HTN Plan Library for Agent-Zero"
  },
  "plans": {
    "<plan_id>": {
      "name": "Human-readable plan name",
      "domains": ["git_ops"],
      "triggers": ["create branch", "feature branch", "new branch"],
      "trigger_threshold": 2,
      "stale_after_turns": 10,
      "steps": [
        {
          "name": "Check current branch status",
          "action": "Run git status and git branch to confirm clean state",
          "tool": "code_execution_tool",
          "tool_hint": "git status && git branch",
          "verify": {
            "type": "output_contains",
            "value": "On branch"
          },
          "on_fail": "warn",
          "required": true
        }
      ]
    }
  }
}
```

### Verification Types
| Type | Description | Example |
|------|-------------|---------|
| `output_contains` | Tool output contains substring | `{"type": "output_contains", "value": "On branch"}` |
| `output_not_contains` | Tool output does NOT contain substring | `{"type": "output_not_contains", "value": "error"}` |
| `exit_code_zero` | Command exited with code 0 | `{"type": "exit_code_zero"}` |
| `file_exists` | Check file was created (path in value) | `{"type": "file_exists", "value": "/path/to/file"}` |
| `any_output` | Any non-empty output passes | `{"type": "any_output"}` |
| `manual` | Model must confirm (no auto-check) | `{"type": "manual"}` |

### On-Fail Actions
| Action | Behavior |
|--------|----------|
| `warn` | Log warning, let model retry the step |
| `block` | Don't advance; inject "Step X failed verification" |
| `skip` | Mark step failed, advance to next |
| `abort` | Clear plan state, inject "Plan aborted due to step X failure" |

---

## Starter Plan Library

### Plans to Ship (v1.0)

| Plan ID | Domain(s) | Triggers | Steps |
|---------|-----------|----------|-------|
| `git_feature_branch` | git_ops | create branch, feature branch, new branch | status → branch → changes → commit → push |
| `git_merge_pr` | git_ops | merge, pull request, merge branch | fetch → checkout → merge → resolve → push |
| `docker_build_deploy` | docker_ops | build image, docker build, deploy container | dockerfile check → build → test → run |
| `bugfix_workflow` | bugfix | fix bug, debug, troubleshoot | reproduce → isolate → fix → test → verify |
| `file_backup_restore` | file_ops | backup, migrate, move files | inventory → backup → execute → verify → cleanup |
| `api_integration` | api_integration | connect api, integrate, endpoint | research → auth → implement → test → error handling |
| `codegen_module` | codegen | create module, new component, build feature | spec → scaffold → implement → test → document |
| `refactor_safe` | refactor | refactor, restructure, clean up | test baseline → extract → modify → test again → commit |
| `dependency_update` | dependency_mgmt | update deps, upgrade packages | audit → backup lockfile → update → test → commit |
| `log_investigation` | log_analysis | check logs, investigate, diagnose | locate logs → filter → identify pattern → trace root cause → report |

### Example Plan: `bugfix_workflow`
```json
{
  "name": "Bug Fix Workflow",
  "domains": ["bugfix"],
  "triggers": ["fix bug", "debug", "troubleshoot", "not working", "broken", "error in"],
  "trigger_threshold": 1,
  "stale_after_turns": 15,
  "steps": [
    {
      "name": "Reproduce the issue",
      "action": "Run the failing code/command to confirm the bug exists and capture the error output",
      "tool": "code_execution_tool",
      "tool_hint": "Run the command or script that triggers the bug",
      "verify": {"type": "any_output"},
      "on_fail": "warn",
      "required": true
    },
    {
      "name": "Isolate the cause",
      "action": "Examine error output, check relevant source files, identify the root cause",
      "tool": "code_execution_tool",
      "tool_hint": "Read source files, check stack traces, add debug output if needed",
      "verify": {"type": "any_output"},
      "on_fail": "warn",
      "required": true
    },
    {
      "name": "Implement the fix",
      "action": "Make the minimal code change to fix the identified issue",
      "tool": "code_execution_tool",
      "tool_hint": "Edit the file(s) with the fix",
      "verify": {"type": "any_output"},
      "on_fail": "block",
      "required": true
    },
    {
      "name": "Test the fix",
      "action": "Re-run the original failing command to confirm the bug is fixed",
      "tool": "code_execution_tool",
      "tool_hint": "Run the same command from Step 1",
      "verify": {"type": "output_not_contains", "value": "error"},
      "on_fail": "block",
      "required": true
    },
    {
      "name": "Verify no regressions",
      "action": "Run any existing tests or related commands to ensure nothing else broke",
      "tool": "code_execution_tool",
      "tool_hint": "Run test suite or related functionality checks",
      "verify": {"type": "any_output"},
      "on_fail": "warn",
      "required": false
    }
  ]
}
```

---

## Extension Implementation

### File: `_15_htn_plan_selector.py`

```python
"""
HTN Plan Selector — Agent-Zero Cognitive Architecture
=====================================================
Hook: before_main_llm_call (_15_)

Reads BST domain classification, matches plan templates,
tracks step progress, injects structured plan context.
Runs after BST (_10_), before context watchdog (_20_).

Zero model reasoning. Pure dict lookups and string matching.
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


class HTNPlanSelector(Extension):
    """Selects and tracks execution of pre-built workflow plans."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
        try:
            library = _load_library(self.agent)
            if not library:
                return

            state = _get_state(self.agent)

            # If we have an active plan, check progress
            if state:
                state = _check_progress(self.agent, state, loop_data)
                if state:  # plan still active
                    _inject_plan_context(loop_data, state, library)
                    return

            # No active plan — try to match one
            domain = _get_bst_domain(self.agent)
            message = _get_user_message(loop_data)
            if not message:
                return

            plan_id, plan = _match_plan(library, domain, message)
            if plan_id and plan:
                state = _create_state(self.agent, plan_id, plan)
                _inject_plan_context(loop_data, state, library)
                self.agent.context.log.log(
                    type="info",
                    content=f"[HTN] Plan activated: {plan.get('name', plan_id)} ({len(plan['steps'])} steps)"
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

def _load_library(agent) -> dict | None:
    global _library_cache
    if _library_cache is not None:
        return _library_cache
    try:
        with open(PLAN_LIBRARY_PATH, "r") as f:
            _library_cache = json.load(f)
        return _library_cache
    except Exception:
        return None


# ── BST Integration ──────────────────────────────────────────────

def _get_bst_domain(agent) -> str:
    """Read BST's domain classification from agent._bst_store."""
    try:
        store = getattr(agent, BST_STORE_KEY, {})
        belief = store.get(BST_BELIEF_KEY, {})
        return belief.get("domain", "")
    except Exception:
        return ""


# ── User Message Extraction ─────────────────────────────────────

def _get_user_message(loop_data: LoopData) -> str:
    """Extract user message text from history."""
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

def _match_plan(library: dict, domain: str, message: str) -> tuple:
    """Match message against plan library. Returns (plan_id, plan) or (None, None)."""
    plans = library.get("plans", {})
    best_id = None
    best_score = 0

    for plan_id, plan in plans.items():
        # Domain filter: if plan specifies domains, message domain must match
        plan_domains = plan.get("domains", [])
        domain_match = not plan_domains or domain in plan_domains

        # Trigger matching
        triggers = plan.get("triggers", [])
        threshold = plan.get("trigger_threshold", 2)
        hits = sum(1 for t in triggers if t in message)

        if hits >= threshold and domain_match:
            # Score: hits + domain bonus
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

def _create_state(agent, plan_id: str, plan: dict) -> dict:
    state = {
        "plan_id": plan_id,
        "plan_name": plan.get("name", plan_id),
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


# ── Progress Checking ────────────────────────────────────────────

def _check_progress(agent, state: dict, loop_data: LoopData) -> dict | None:
    """Check if current step is verified, advance if so. Returns updated state or None if plan complete/stale."""

    # Staleness check
    state["turns_since_progress"] = state.get("turns_since_progress", 0) + 1
    stale_limit = state.get("stale_after_turns", 10)
    if state["turns_since_progress"] > stale_limit:
        agent.context.log.log(
            type="info",
            content=f"[HTN] Plan '{state['plan_name']}' expired (no progress for {stale_limit} turns)"
        )
        _clear_state(agent)
        return None

    # Plan complete check
    if state["current_step"] >= state["total_steps"]:
        agent.context.log.log(
            type="info",
            content=f"[HTN] Plan '{state['plan_name']}' completed!"
        )
        _clear_state(agent)
        return None

    # Check last tool output against current step's verification
    library = _load_library(agent)
    if not library:
        return state

    plan = library.get("plans", {}).get(state["plan_id"])
    if not plan:
        _clear_state(agent)
        return None

    current_idx = state["current_step"]
    step = plan["steps"][current_idx]

    # Get last tool output from history
    last_output = _get_last_tool_output(loop_data)

    if last_output is not None:
        verified = _verify_step(step, last_output)
        if verified:
            state["steps_completed"].append(current_idx)
            state["current_step"] = current_idx + 1
            state["turns_since_progress"] = 0
            agent.context.log.log(
                type="info",
                content=f"[HTN] Step {current_idx + 1} verified: {step['name']}"
            )

            # Check if plan is now complete
            if state["current_step"] >= state["total_steps"]:
                agent.context.log.log(
                    type="info",
                    content=f"[HTN] Plan '{state['plan_name']}' completed!"
                )
                _clear_state(agent)
                return None
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
                return None
            # "warn" and "block" both keep current_step unchanged

    _set_state(agent, state)
    return state


def _get_last_tool_output(loop_data: LoopData) -> str | None:
    """Extract the most recent tool output from history."""
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

def _verify_step(step: dict, output: str) -> bool:
    """Run verification check on tool output."""
    verify = step.get("verify")
    if not verify:
        return True  # No verification = auto-pass

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
        return True  # Can't check file system from here; model confirms
    elif vtype == "manual":
        return True  # Model self-reports
    return True


# ── Context Injection ────────────────────────────────────────────

def _inject_plan_context(loop_data: LoopData, state: dict, library: dict):
    """Build and inject the plan context string into extras_temporary."""
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
```

---

## Installation

### install_htn_plans.sh
```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
TARGET="/a0/python/extensions/before_main_llm_call"

echo "[HTN] Installing Plan Selector..."
cp "$REPO_ROOT/extensions/before_main_llm_call/_15_htn_plan_selector.py" "$TARGET/_15_htn_plan_selector.py"
echo "  ✓ _15_htn_plan_selector.py"

cp "$REPO_ROOT/extensions/before_main_llm_call/htn_plan_library.json" "$TARGET/htn_plan_library.json"
echo "  ✓ htn_plan_library.json"

# Clear pycache
rm -rf "$TARGET/__pycache__"
echo "  ✓ Cleared __pycache__"

echo "[HTN] Plan Templates installed."
```

### install_all.sh Addition
```bash
# Layer 5: HTN Plan Templates
echo ""
echo "=== Layer 5: HTN Plan Templates ==="
bash "$SCRIPT_DIR/install_htn_plans.sh"
```

---

## Integration with Existing Layers

| Layer | Interaction |
|-------|-------------|
| **BST** | HTN reads `agent._bst_store[BELIEF_KEY]["domain"]` to filter plans by domain |
| **Working Memory** | WM entities available to model when executing plan steps (no direct integration needed) |
| **Personality** | Major Zero voice on plan activation/completion log messages (if personality reinforcement added later) |
| **Tool Fallback Chain** | Failed verifications don't directly increment fallback counter — the actual tool errors do. HTN adds structured retry guidance. |
| **Meta-Reasoning Gate** | Gate auto-corrects tool args before execution, increasing plan step success rate |

---

## Testing Protocol

### Test 1: Plan Activation
```
User: "I need to fix a bug in the login module"
Expected: BST classifies as "bugfix", HTN matches bugfix_workflow, plan context injected
Verify: Log shows "[HTN] Plan activated: Bug Fix Workflow (5 steps)"
```

### Test 2: Step Advancement
```
User: (after Step 1 produces output)
Expected: Step 1 verified (any_output), step pointer advances to Step 2
Verify: Log shows "[HTN] Step 1 verified: Reproduce the issue"
```

### Test 3: Staleness Expiry
```
User: (changes topic for 15+ turns)
Expected: Plan expires, state cleared
Verify: Log shows "[HTN] Plan expired"
```

### Test 4: No False Triggers
```
User: "What's the weather like?"
Expected: BST classifies as "conversational", no plan matched, no injection
Verify: No HTN log entries
```

### Test 5: Fallback Integration
```
User: (step fails verification 3x)
Expected: on_fail="block" keeps step active, tool fallback chain fires independently on actual tool errors
Verify: Both systems log independently
```

---

## Design Decisions

1. **`before_main_llm_call` over `message_loop_prompts_after`:** Ensures BST domain is available fresh, same hook family, cleaner data flow.

2. **`extras_temporary` over system prompt modification:** Extras are appended after history, closer to where the model's attention is strongest. System prompt modifications would fight with the existing tiered tool injection.

3. **Trigger threshold configurable per plan:** `bugfix_workflow` has threshold 1 (single trigger like "debug" should activate), while `git_feature_branch` has threshold 2 (need more specificity to avoid false positives).

4. **No model-generated plans:** Local models at 14B parameters cannot reliably decompose tasks. Pre-built plans from the library are deterministic and tested.

5. **Staleness over explicit cancellation:** The model won't reliably call a "cancel plan" action. Turn-based expiry is passive and reliable.

6. **Verification is best-effort:** Some checks (like `file_exists`) can't run from within the extension. The model self-reports, and the structured format nudges it to actually check.

---

## Future Enhancements

- **Plan chaining:** Completing one plan can auto-trigger the next (e.g., `codegen_module` → `git_feature_branch`)
- **Dynamic step insertion:** Model can request "add a step" via a structured response format
- **Plan history:** Track which plans succeed/fail over time to adjust trigger thresholds
- **User plan authoring:** UI for creating custom plan templates
- **Subordinate delegation:** Multi-step plans that use `call_subordinate` for parallelizable steps
