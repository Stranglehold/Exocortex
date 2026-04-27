# INJECTION GATE (_09_) — Formal Decision Logic
## From: Opus — April 27, 2026
## Status: Implementation spec for Kestrel
## Depends on: Agent's interface spec (Stateful Injection Lifecycle), BST v3.8, token counting

---

## 1. Architectural Position

**Hook:** `before_main_llm_call`
**Priority:** `_09_` — fires before ALL other extensions
**Purpose:** Single control point that manages injection decisions for all participating extensions

The gate does NOT inject content itself. It sets flags and caches that other extensions read to decide whether to inject their full block, a compressed reference, or nothing.

---

## 2. State Storage

All state lives on the agent object (persists across turns within a session):

```python
# Gate state (set by _09_injection_gate.py)
agent._injection_gate = {
    "turn": 0,                          # current turn counter
    "phase": "full",                     # "full" or "conditional"
    "full_phase_until": 3,               # inject everything through this turn
    "last_domain": None,                 # BST domain on previous turn
    "cache": {},                         # {ext_name: content_hash}
    "token_budget": {},                  # {ext_name: tokens_injected_this_turn}
    "total_tokens_this_turn": 0,         # sum of all injection tokens
    "domain_change_this_turn": False,    # flag for other extensions
}
```

---

## 3. Decision Algorithm

### Phase 1: Turn Counting and Phase Management

```python
def execute(self, loop_data, **kwargs):
    gate = getattr(self.agent, '_injection_gate', None)
    if gate is None:
        gate = _init_gate()
        self.agent._injection_gate = gate
    
    gate["turn"] += 1
    turn = gate["turn"]
    
    # Reset token budget for this turn
    gate["token_budget"] = {}
    gate["total_tokens_this_turn"] = 0
    
    # Detect domain change
    current_domain = _get_bst_domain(self.agent)
    if current_domain and current_domain != gate["last_domain"]:
        gate["domain_change_this_turn"] = True
        gate["full_phase_until"] = turn + 2  # full injection for 2 turns after domain change
        gate["cache"].clear()  # invalidate all caches
        gate["last_domain"] = current_domain
        _log(self.agent, f"[GATE] Domain change: {gate['last_domain']} -> {current_domain}. Full injection for 2 turns.")
    else:
        gate["domain_change_this_turn"] = False
    
    # Set phase
    if turn <= gate["full_phase_until"]:
        gate["phase"] = "full"
    else:
        gate["phase"] = "conditional"
```

### Phase 2: The `should_inject` Function

Other extensions call this to decide what to inject:

```python
def should_inject(agent, ext_name: str, new_content: str) -> tuple:
    """
    Returns: (action, reference_line)
    
    action is one of:
        "full"     — inject the complete block
        "reference" — inject only the reference_line
        "skip"     — inject nothing (extension has no content)
    
    reference_line is a one-line summary for "reference" action
    """
    gate = getattr(agent, '_injection_gate', None)
    if gate is None:
        return ("full", "")  # no gate initialized — safe default
    
    # No content to inject
    if not new_content or not new_content.strip():
        return ("skip", "")
    
    # FULL phase: always inject everything
    if gate["phase"] == "full":
        new_hash = _fast_hash(new_content)
        gate["cache"][ext_name] = new_hash
        _track_tokens(gate, ext_name, new_content)
        return ("full", "")
    
    # CONDITIONAL phase: check cache
    new_hash = _fast_hash(new_content)
    cached_hash = gate["cache"].get(ext_name)
    
    if cached_hash == new_hash:
        # Content unchanged — inject reference only
        ref = _make_reference(ext_name, new_content)
        _track_tokens(gate, ext_name, ref)  # count the reference, not full block
        return ("reference", ref)
    else:
        # Content changed — inject full, update cache
        gate["cache"][ext_name] = new_hash
        _track_tokens(gate, ext_name, new_content)
        return ("full", "")
```

### Phase 3: Reference Line Generation

The reference line must contain enough context to be actionable even if the original injection is no longer in visible history:

```python
_REFERENCE_TEMPLATES = {
    "bst":                "[BST: {domain}, confidence {confidence} (unchanged since T={cached_turn})]",
    "completion_tracker": "[COMPLETION: {count} actions tracked (unchanged)]",
    "operator_profile":   "[OPERATOR: profile cached (unchanged)]",
    "metacognitive":      "[META: {model_id}, {domain}/{volatility} (unchanged)]",
    "tool_registry":      "[TOOLS: {skill_count} skills, {tool_count} custom tools (unchanged)]",
    "orchestration":      "[ORCH: {state} (unchanged)]",
    "memory_catalog":     "[MEMORY: {area_count} areas, {entry_count} entries (unchanged)]",
    "htn_plan":           "[HTN: {plan_name}, step {current}/{total} (unchanged)]",
}

def _make_reference(ext_name: str, content: str) -> str:
    """Generate a one-line reference with key values extracted from content."""
    template = _REFERENCE_TEMPLATES.get(ext_name)
    if template:
        values = _extract_key_values(ext_name, content)
        try:
            return template.format(**values)
        except (KeyError, IndexError):
            pass
    # Fallback: first 80 chars
    summary = content[:80].replace('\n', ' ').strip()
    return f"[{ext_name}: unchanged — {summary}...]"
```

### Phase 4: Token Tracking

```python
def _track_tokens(gate: dict, ext_name: str, content: str):
    """Track per-extension token injection for budget visibility."""
    tokens = len(content) // 4  # rough estimate: chars / 4
    gate["token_budget"][ext_name] = tokens
    gate["total_tokens_this_turn"] += tokens

def get_injection_summary(agent) -> str:
    """Generate the [INJECTION BUDGET] line for extras_temporary."""
    gate = getattr(agent, '_injection_gate', None)
    if not gate:
        return ""
    
    total = gate["total_tokens_this_turn"]
    budget = gate["token_budget"]
    top3 = sorted(budget.items(), key=lambda x: -x[1])[:3]
    top_str = ", ".join(f"{k}:{v}" for k, v in top3)
    phase = gate["phase"]
    turn = gate["turn"]
    
    return f"[INJECTION BUDGET] T={turn} phase={phase} total={total} tokens. Top: {top_str}"
```

---

## 4. Extension Integration Pattern

Each participating extension modifies its `execute()` to call the gate:

```python
# In _11_belief_state_tracker.py (example):

class BeliefStateTracker(Extension):
    async def execute(self, loop_data, **kwargs):
        # ... compute BST state as normal ...
        
        injection_content = _format_bst_block(belief_state)
        
        # Ask the gate what to do
        from extensions.before_main_llm_call._09_injection_gate import should_inject
        action, ref = should_inject(self.agent, "bst", injection_content)
        
        if action == "full":
            loop_data.extras_persistent["bst_state"] = injection_content
        elif action == "reference":
            loop_data.extras_persistent["bst_state"] = ref
        # action == "skip" — inject nothing
```

---

## 5. Participating Extensions

### Always-inject (never gated, even in conditional phase):

| Extension | Reason |
|-----------|--------|
| `_12_completion_tracker` | Completion state changes every turn with tool activity |
| `_20_context_watchdog` | Safety-critical, must always report utilization |

### Gated (participate in the injection gate):

| Extension | Cache Key | Changes When |
|-----------|-----------|-------------|
| `_11_belief_state_tracker` | domain + confidence + compound | Domain reclassification |
| `_13_operator_profile` | profile hash | Never (cache indefinitely) |
| `_14_metacognitive_injection` | model + domain + volatility | Domain change |
| `_16_tool_registry` | tool list hash | Tool install/remove |
| `_17_orchestration_gate` | delegation state | Subordinate called or delegation state change |
| `_18_memory_catalog` | area count + entry count | Memory area created/emptied |
| `_15_htn_plan_selector` | plan + step | Step completion |

### Not gated (different hook or content path):

| Extension | Reason |
|-----------|--------|
| `_56_memory_enhancement` | `message_loop_prompts_after` — different hook, different timing |
| `_50_supervisor_loop` | `message_loop_end` — post-turn, not pre-turn |
| All `tool_execute_*` | Different hook entirely |

---

## 6. Injection Budget Visibility

At the END of the `before_main_llm_call` chain (after all extensions have run), inject the budget summary into `extras_temporary`:

```python
# In _09_injection_gate.py, at the end of execute():
# Or in a separate _99_injection_budget.py at end of chain

summary = get_injection_summary(self.agent)
if summary:
    loop_data.extras_temporary["injection_budget"] = summary
```

The agent sees:
```
[INJECTION BUDGET] T=7 phase=conditional total=342 tokens. Top: memory_catalog:120, bst:85, htn_plan:72
```

This gives the agent temporal proprioception about its own context overhead.

---

## 7. Domain-Gated Tool Schema Injection

### Integration with `_16_tool_registry.py`:

When the gate is in conditional phase AND BST has a confident classification (≥ 2 signals):

**Always inject schemas for:**
- `code_execution_tool` — universal capability
- `response` — the only way to deliver results
- `call_subordinate` — delegation is always an option

**Domain-gated schemas:**

| BST Domain | Additional tools to inject |
|------------|---------------------------|
| `coding`, `bugfix` | `text_editor`, `write_file` |
| `investigation`, `research`, `analysis` | `search_engine`, `browser_agent`, MCP tools (ArXiv, DuckDuckGo, Wikipedia) |
| `system_admin`, `devops` | `code_execution_tool` detailed flags |
| `git_ops` | git-specific tool schemas |

**Fallback:** If BST confidence < 2 signals (low confidence), inject ALL tool schemas. Don't restrict tools on uncertain classification.

**One-line references for non-injected tools:**
```
[search_engine: available — web search via DuckDuckGo]
[browser_agent: available — browser automation for web interaction]
```

The tool is still callable — the model just doesn't get the detailed schema unless it's in a relevant domain. If it tries to call a tool without the schema, MetaGate catches malformed arguments.

---

## 8. Edge Cases

### Session Start (turn 1)
- Phase is "full", all extensions inject everything
- Cache is empty, everything is a cache miss
- Token budget captures the baseline

### Domain Change Mid-Task
- Cache clears, phase resets to "full" for 2 turns
- All extensions re-inject their full blocks
- After 2 turns, conditional phase resumes with fresh cache

### Extension Content That Changes Every Turn
- Completion tracker changes on tool activity — mark as always-inject
- If an extension's content changes every turn, the gate provides no savings — it's always a cache miss. This is fine; the gate doesn't hurt, it just doesn't help for that extension.

### Context Overflow Despite Gate
- If context watchdog reports > 85% utilization AND phase is "conditional", the gate should escalate to "compressed" phase: reference lines only for ALL extensions, even those that changed. This is an emergency compression mode.

```python
# In _09_ after setting phase:
utilization = loop_data.params_temporary.get("context_utilization", 0)
if utilization > 0.85 and gate["phase"] == "conditional":
    gate["phase"] = "compressed"
    _log(self.agent, "[GATE] Context critical — compressed mode, references only")
```

---

## 9. Estimated Impact

Based on injection audit data (T=5, 65% waste):

| Metric | Before Gate | After Gate (estimated) |
|--------|------------|----------------------|
| Tokens injected per turn (turns 1-3) | 900-1000 | 900-1000 (full phase, no change) |
| Tokens injected per turn (turns 4+) | 900-1000 | 300-400 (conditional, most cached) |
| Tokens injected per turn (compressed) | 900-1000 | 100-150 (references only) |
| Context available for content (at 100k) | ~85k after 15 turns | ~94k after 15 turns |
| Effective turn capacity | ~20 turns | ~30+ turns |

The biggest savings come from operator profile (never changes, ~100 tokens saved every turn after T=1), tool registry (~200 tokens saved when tool set unchanged), and metacognitive injection (~80 tokens saved when domain unchanged).

---

## 10. Build Order

1. **Core gate module** — `_09_injection_gate.py` with `should_inject()`, caching, phase management
2. **Integrate BST** — modify `_11_` to call `should_inject("bst", content)`
3. **Integrate operator profile and metacognitive** — these are the easiest (rarely change)
4. **Integrate tool registry** — includes domain-gated schema logic
5. **Integrate remaining extensions** — HTN, orchestration, memory catalog
6. **Add injection budget line** — token counting visibility for the agent
7. **Add compressed mode** — emergency compression at 85%+ utilization

Each step can be tested independently. The gate degrades gracefully — if `should_inject()` is unavailable (import fails, gate not initialized), every extension falls back to full injection. No extension should break if the gate isn't present.

---

*Decision logic by Opus. Interface spec by Agent Zero. Implementation by Kestrel. Three contributors, one gate.*
