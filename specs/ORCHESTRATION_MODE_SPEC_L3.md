# Orchestration Mode — Spec L3

## Problem

The main agent attempts complex multi-phase tasks (framework builds, multi-file
implementations, phased analysis) by executing tool calls directly. It reaches for
`code_execution_tool` and `text_editor` because those are the lowest-friction paths
to "doing the thing." Delegation via `call_subordinate` requires decomposition
thinking the agent isn't scaffolded to do by default.

The failure mode is always the same: step count climbs past 20, context fills or
compresses, the agent loses its position in the task, and a verbatim-repeat loop
begins. The supervisor injection ("You sent the same message again") produces no
recovery — the model isn't processing tool output well enough to act on it.

An existing `_17_orchestration_gate.py` addresses this in `before_main_llm_call`.
It is correctly designed but in the wrong hook. In V1.7, `prepare_prompt()` assembles
the LLM prompt BEFORE `before_main_llm_call` fires — all `history_output` modifications
are silently discarded. The gate never reaches the model.

The fix requires three layers:

1. **BST complexity slot** — classify task complexity at first contact, proactively,
   before the agent starts executing anything
2. **`_57_orchestration_mode.py` in `message_loop_prompts_after`** — re-inject
   orchestration scaffolding every turn, with state-aware content that reflects
   current phase, using the hook that actually works in V1.7
3. **MetaGate enforcement** — block `code_execution_tool` and `text_editor` when
   orchestration mode is active, providing mechanical negative feedback on violations

Without Layer 3, the design is advisory. With it, violations produce explicit
`hist_add_warning` output that the model reads on the next turn. Three blocked
attempts reliably redirect behavior.

---

## What This Does NOT Do

- Does not replace or remove the existing `_17_orchestration_gate.py`. That file
  is dead code in V1.7 and should remain as a migration artifact until the full
  `before_main_llm_call` → `message_loop_prompts_after` migration is complete.
- Does not call any LLM. All classification is deterministic regex.
- Does not block `call_subordinate` or any meta-tool.
- Does not fire on simple or multi-step tasks — only on `complex_build` classification.
- Does not persist across container restarts (state lives on `agent._attr`).
- Does not manage the subordinate agents themselves — orchestration scaffolding only.

---

## Layer 1: BST Complexity Slot

**File:** `extensions/before_main_llm_call/_11_belief_state_tracker.py`

Add a `complexity` field to the BST output dict. Additive — does not modify any
existing field. Stored in `_bst_store[BELIEF_KEY]["complexity"]`.

### Values

| Value | Meaning |
|-------|---------|
| `simple` | Single action, one file, one-shot question |
| `multi_step` | 2–4 sequential actions, same domain |
| `complex_build` | Framework, phases, modules, multiple files |

### Detection (applied only when domain is in COMPLEX_ELIGIBLE_DOMAINS)

```python
COMPLEX_ELIGIBLE_DOMAINS = {
    "coding", "system_admin", "planning", "investigation", "analysis"
}

_COMPLEX_BUILD_RX = re.compile(
    r'\b('
    r'build|framework|scaffold|'
    r'implement\s+phase|create\s+system|'
    r'develop\s+(?:a\s+)?(?:tool|plugin|module|service|library)|'
    r'multiple\s+(?:files?|modules?|collectors?|components?|classes?)|'
    r'phase\s+[0-9]|step\s+[0-9]\s+of|'
    r'full\s+(?:stack|pipeline|system)|'
    r'end.to.end|'
    r'flesh\s+out|'
    r'complete\s+(?:the\s+)?(?:build|implementation|system)'
    r')\b',
    re.IGNORECASE,
)

_MULTI_STEP_RX = re.compile(
    r'\b(then|after\s+that|next|followed\s+by|and\s+also|step\s+[0-9])\b',
    re.IGNORECASE,
)
```

### Logic (append to BST execute(), after primary domain is determined)

```python
complexity = "simple"
if primary_domain in COMPLEX_ELIGIBLE_DOMAINS:
    user_text = _extract_user_text(loop_data)
    if _COMPLEX_BUILD_RX.search(user_text):
        complexity = "complex_build"
    elif _MULTI_STEP_RX.search(user_text):
        complexity = "multi_step"

belief_state["complexity"] = complexity
```

`_extract_user_text()` already exists in BST as the message extraction utility.
Use whatever helper currently extracts the raw user string for signal matching.

---

## Layer 2: `_57_orchestration_mode.py`

**File:** `extensions/message_loop_prompts_after/_57_orchestration_mode.py`

**Hook:** `message_loop_prompts_after` — confirmed working in V1.7 (T4 verified)

**Slot:** `_57_` — between memory enhancement (`_56_`) and ontology query (`_58_`)

**Pattern source:** `_56_memory_enhancement.py` (same hook, user-message prepend pattern)

### State

Stored on `self.agent._orch_state` (persists on agent object, survives context
compression since compression only touches `agent.history`, not `agent` attributes).

```python
DEFAULT_STATE = {
    "phase": "inactive",       # inactive | planning | executing
    "original_task": "",       # user message that triggered activation
    "turn_activated": 0,       # agent turn count at activation
    "delegation_count": 0,     # number of call_subordinate calls observed
}
```

### Phase Transitions

```
inactive ──[complex_build detected, step <= 2]──► planning
inactive ──[complex_build detected, step > 2]───► executing  (already working)
planning ──[call_subordinate in recent history]──► executing
executing ──[response tool fired OR domain no longer complex]──► inactive
```

- **Step threshold:** read from `loop_data` via `getattr(self.agent, '_step', 0)` or
  equivalent. "Step <= 2" means the agent hasn't done real work yet — use planning
  phase. "Step > 2" means it's mid-task — go straight to executing to avoid
  disrupting in-flight work that's going well.
- **`response` tool detection:** scan last 3 AI messages in `loop_data.history_output`
  for `"tool_name": "response"`. If found, the task completed — deactivate.

### Injection Content

#### Planning phase (first 1-2 turns after activation)

```
[ORCHESTRATION MODE — PLANNING]
Task complexity: complex_build. This task requires multiple implementation steps.

Before writing any code or files:
1. List all subtasks in your thoughts as a numbered sequence
2. Delegate SUBTASK 1 immediately via call_subordinate
   Format: tool_name: "call_subordinate", message: "<bounded task for subordinate>", agent_name: "developer"
3. After subordinate returns, delegate SUBTASK 2, and so on

Do NOT use code_execution_tool or text_editor this turn.
Your role is orchestration. Subordinates handle execution.
[/ORCHESTRATION MODE]
```

#### Executing phase (subsequent turns)

```
[ORCHESTRATION MODE — EXECUTING]
You have delegated {delegation_count} subtask(s) so far.
Continue: call the next subtask via call_subordinate.
Do not implement directly — delegate.
[/ORCHESTRATION MODE]
```

Short in executing phase — just a reminder, not a full instruction block.
The model already has the pattern from planning phase.

### Injection Mechanism

Prepend to last user message in `loop_data.history_output` (same pattern as
`_56_memory_enhancement.py`). Do NOT use `extras_temporary` — under deep-loop
conditions extras are appended after history and get overwhelmed by prior context.

```python
def _get_last_user_message(history):
    for msg in reversed(history):
        if isinstance(msg, dict) and not msg.get("ai", True):
            return msg
    return None

user_msg = _get_last_user_message(loop_data.history_output)
if user_msg:
    existing = user_msg.get("content", "")
    user_msg["content"] = block + "\n\n" + str(existing)
```

### BST State Reader

```python
BST_STORE_KEY  = "_bst_store"
BST_BELIEF_KEY = "__bst_belief_state__"

def _get_bst(agent):
    store = getattr(agent, BST_STORE_KEY, None) or {}
    belief = store.get(BST_BELIEF_KEY)
    if not isinstance(belief, dict):
        return "conversation", 0.0, "simple"
    primary = belief.get("primary") or {}
    domain     = primary.get("domain", "conversation")
    confidence = float(primary.get("confidence") or 0.0)
    complexity = belief.get("complexity", "simple")
    return domain, confidence, complexity
```

### Delegation Counter

Increment `_orch_state["delegation_count"]` by scanning the last AI message in
`loop_data.history_output` for `"tool_name": "call_subordinate"` each turn.
Only increment once per turn (check the most recent AI message, not a window).

### Log tag: `[ORCH-MODE]`

Examples:
```
[ORCH-MODE] Activated: phase=planning domain=coding complexity=complex_build step=1
[ORCH-MODE] Transition: planning → executing (delegation detected)
[ORCH-MODE] Injected planning block
[ORCH-MODE] Injected executing reminder (delegations=2)
[ORCH-MODE] Deactivated: response tool detected at step=12
```

---

## Layer 3: MetaGate Enforcement

**File:** `extensions/tool_execute_before/_20_meta_reasoning_gate.py`

Add an orchestration check in `execute()`, before the existing schema validation.

```python
# Phase 1a: Orchestration enforcement (before arg alias fixes)
orch_state = getattr(self.agent, "_orch_state", None)
if orch_state and orch_state.get("phase") in ("planning", "executing"):
    if tool_name in ("code_execution_tool", "text_editor"):
        self.agent.context.log.log(
            type="warning",
            content=f"[ORCH-GATE] Blocked {tool_name} — orchestration mode active"
        )
        self.agent.hist_add_warning(
            f"[ORCHESTRATION MODE] You are the orchestrator. "
            f"Do not use {tool_name} directly. "
            f"Delegate to call_subordinate with a bounded task description."
        )
        # Do NOT return — let the tool proceed (warning only, not hard block)
        # Hard block would require returning a synthetic tool response, which
        # is out of scope for MetaGate. Warning + hist injection is sufficient.
```

Note: MetaGate cannot hard-block tool execution (it has no mechanism to short-circuit
the tool call itself). The warning approach is correct — `hist_add_warning` injects
into the model's next turn context. After 2–3 violations, the model's own reasoning
redirects. If hard blocking is needed in future, it belongs in `tool_execute_before`
as a separate extension with a different return mechanism.

---

## Files

| File | Action |
|------|--------|
| `extensions/before_main_llm_call/_11_belief_state_tracker.py` | ADD complexity slot (~15 lines) |
| `extensions/message_loop_prompts_after/_57_orchestration_mode.py` | NEW (~180 lines) |
| `extensions/tool_execute_before/_20_meta_reasoning_gate.py` | ADD ~15 lines in execute() |

The existing `_17_orchestration_gate.py` in `before_main_llm_call` is NOT removed.
It is dead code in V1.7 but kept for reference during the eventual full hook migration.

---

## Deploy

```bash
# Copy files
docker cp extensions/before_main_llm_call/_11_belief_state_tracker.py \
  exocortex_v16:/a0/usr/agents/agent0/extensions/python/before_main_llm_call/_11_belief_state_tracker.py

docker cp extensions/message_loop_prompts_after/_57_orchestration_mode.py \
  exocortex_v16:/a0/usr/agents/agent0/extensions/python/message_loop_prompts_after/_57_orchestration_mode.py

docker cp extensions/tool_execute_before/_20_meta_reasoning_gate.py \
  exocortex_v16:/a0/usr/agents/agent0/extensions/python/tool_execute_before/_20_meta_reasoning_gate.py

# Restart to clear extension class cache (required for any extension change in V1.7)
docker restart exocortex_v16
```

---

## Verification

1. **Syntax:** `python -m py_compile` on all three files before deploy
2. **Activation:** Send "build a multi-phase OSINT framework with 3 collector modules"
   → logs show `[ORCH-MODE] Activated: phase=planning`
   → model outputs call_subordinate on first tool call, not code_execution_tool
3. **Enforcement:** Ask agent to write a file directly during orchestration mode
   → logs show `[ORCH-GATE] Blocked text_editor`
   → model's next response redirects to call_subordinate
4. **Deactivation:** After agent sends `response` tool
   → logs show `[ORCH-MODE] Deactivated`
   → next task starts fresh with `phase=inactive`
5. **Simple task guard:** Send "write a hello world function"
   → BST classifies `complexity=simple`
   → no `[ORCH-MODE]` log output, no injection

---

## Research Lineage

No external papers required. This is behavioral scaffolding informed by:
- Observed failure mode: step-95 verbatim-repeat loop during OSINT framework build
- V1.7 hook timing finding (T11, 2026-04-06): `before_main_llm_call` injections discarded
- T4 (2026-04-06): `message_loop_prompts_after` injections confirmed working
- Supervisor loop analysis: `hist_add_warning` is read on next turn regardless of
  context compression state
