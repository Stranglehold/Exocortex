# CONSOLIDATED BUILD SPEC — BST Anti-Signals + Injection Gate
## From: Opus (decision logic) + Agent Zero (interface spec + field data)
## For: Kestrel
## Date: April 25, 2026

---

## PART 1: BST Anti-Signal System

### Problem
BST regex patterns are biased toward technical domains. Common English words ("fix", "error", "broken", "strategy") trigger technical classifications during reflective, strategic, and analytical tasks. Live evidence: agent asked "what do you think of all this?" — BST classified as `bugfix+coding` because "fix" and "error" appeared in conversation context. HTN injected "Isolate root cause → Examine error output" during a reflective assessment.

### Agent's Design (domain-pair aware, not flat suppression)

```python
# Anti-signals suppress specific domains, not all domains
ANTI_SIGNAL_MAP = {
    "strategic": [
        "perspective", "assessment", "how do you feel", "what do you think",
        "overall", "biggest difference", "ranking", "priority",
        "trade-off", "trade off", "vision", "direction", "roadmap",
    ],
    "reflective": [
        "felt", "noticed", "experience", "lived", "from where you sit",
        "what do you see", "how does it feel", "observation",
        "looking back", "stepping back", "pausing",
    ],
}

# Only suppress technical work domains, not research/investigation
ANTI_SIGNAL_SUPPRESSED_DOMAINS = {"bugfix", "coding", "planning", "system_admin"}

# Suppression is multiplicative, not zeroing
ANTI_SIGNAL_MULTIPLIER = 0.5
```

### Opus's Decision Logic

When anti-signals fire:
1. Scan user message for anti-signal matches across all categories
2. If any category has ≥ 1 match, apply `ANTI_SIGNAL_MULTIPLIER` to all domains in `ANTI_SIGNAL_SUPPRESSED_DOMAINS`
3. Do NOT suppress `research`, `investigation`, `analysis`, `conversation` — reflective questions can legitimately classify into these
4. Apply BEFORE momentum check — anti-signals should be able to break momentum

```python
# In _score_all_domains() or equivalent:
anti_signal_hits = 0
for category, patterns in ANTI_SIGNAL_MAP.items():
    for pattern in patterns:
        if pattern.lower() in message.lower():
            anti_signal_hits += 1
            break  # one hit per category is enough

if anti_signal_hits > 0:
    for domain in ANTI_SIGNAL_SUPPRESSED_DOMAINS:
        if domain in scores:
            scores[domain] = int(scores[domain] * ANTI_SIGNAL_MULTIPLIER)
```

### Confidence Decay (agent's proposal)

After 3 turns without reinforcing signals for the current domain, halve momentum each turn:

```python
# In momentum tracking:
turns_without_reinforcement = state.get("turns_without_reinforcement", 0)

if current_domain_signals == 0:
    turns_without_reinforcement += 1
else:
    turns_without_reinforcement = 0

if turns_without_reinforcement >= 3:
    momentum = max(0, momentum // 2)  # halve each turn after 3

state["turns_without_reinforcement"] = turns_without_reinforcement
```

### Score Ordering Fix (Kestrel's flag, Opus confirmed)

```python
# Use explicit max(), never assume dict ordering
if scores:
    dominant_domain = max(scores, key=lambda d: scores[d])
    dominant_score = scores[dominant_domain]
```

---

## PART 2: Injection Gate (_09_injection_gate.py)

### Problem
65% of injected context blocks have zero active signal per turn. 900-1000 tokens of overhead per turn. At 100k context, this is ~1% per turn / 15% over 15 turns. Extensions rebuild and re-inject full blocks every turn regardless of whether anything changed.

### Architecture

A single control extension at `before_main_llm_call` priority `_09_` (before all other extensions).

**Phase System (agent's "Initiation Bloat" insight):**
- Turn 1-3: FULL INJECTION phase. Everything fires. All extensions inject complete blocks.
- Turn 4+: CONDITIONAL phase. Extensions only inject on delta.
- On BST domain change: Reset to FULL for 2 turns, then back to CONDITIONAL.

**State Cache:**
```python
class InjectionGate:
    """Manages injection decisions for all participating extensions."""

    def __init__(self):
        self._cache = {}          # {ext_name: last_injection_hash}
        self._turn = 0
        self._last_domain = None
        self._full_phase_until = 3  # full injection through turn 3

    def should_inject(self, ext_name: str, new_content: str) -> tuple[bool, str]:
        """Returns (should_inject_full, reference_line).

        If should_inject_full is True, inject the full block.
        If False, inject reference_line instead.
        """
        self._turn = getattr(self._agent, '_injection_gate_turn', 0)
        new_hash = hash(new_content)

        # Phase: FULL INJECTION (turns 1-3, or after domain change)
        if self._turn <= self._full_phase_until:
            self._cache[ext_name] = new_hash
            return (True, "")

        # Phase: CONDITIONAL
        old_hash = self._cache.get(ext_name)
        if old_hash == new_hash:
            # Content unchanged — return reference line
            ref = self._make_reference(ext_name, new_content)
            return (False, ref)
        else:
            # Content changed — inject full, update cache
            self._cache[ext_name] = new_hash
            return (True, "")

    def on_domain_change(self, new_domain: str):
        """Reset to full injection for 2 turns on domain switch."""
        if new_domain != self._last_domain:
            self._full_phase_until = self._turn + 2
            self._cache.clear()
            self._last_domain = new_domain

    def _make_reference(self, ext_name: str, content: str) -> str:
        """Create a one-line reference with enough context to act on."""
        # Extract the key value from the injection (domain, tool count, etc.)
        summary = content[:80].replace('\n', ' ').strip()
        return f"[{ext_name}: unchanged — {summary}...]"
```

### Participating Extensions

| Extension | Cache Key | Reference Format |
|-----------|-----------|-----------------|
| `_11_belief_state_tracker` | domain + confidence | `[BST: investigation, 0.87 (unchanged)]` |
| `_12_completion_tracker` | completion list hash | `[COMPLETION: 3 actions tracked (unchanged)]` |
| `_13_operator_profile` | profile hash | `[OPERATOR: cached (unchanged)]` |
| `_14_metacognitive_injection` | profile + domain | `[META: Qwen3.6-27B, investigation/high-volatility (unchanged)]` |
| `_16_tool_registry` | tool list hash | `[TOOLS: 59 skills, 28 custom tools (unchanged)]` |
| `_17_orchestration_gate` | delegation state | `[ORCH: direct execution (unchanged)]` |

### Agent's Escape Hatch Concern

The agent flagged: if BST misclassifies and the injection gate domain-gates tool schemas, the agent loses access to tool information. Fix:

**Always-available tools** (inject schema regardless of domain):
- `code_execution_tool` — always available (universal capability)
- `response` — always available (the only way to deliver results)
- `call_subordinate` — always available (delegation is always an option)

**Domain-gated tools** (only inject detailed schema when BST matches):
- ArXiv, DuckDuckGo, Wikipedia → inject for `investigation`, `research`, `analysis`
- text_editor, write_file → inject for `coding`, `bugfix`
- search_engine, browser_agent → inject for `investigation`, `research`

**Fallback:** If BST confidence < 0.5 on any domain, inject ALL tool schemas (no gating). Low confidence means uncertain classification — don't restrict tools based on uncertain data.

---

## PART 3: Token Counting Visibility

### Problem
`[TOKEN-COUNT]` logs go to Docker stdout. Agent can't see them from inside the container.

### Fix
Add a brief summary line to `extras_temporary` visible to the agent:

```python
# At end of before_main_llm_call chain (or in _09_ gate):
counts = getattr(self.agent, '_injection_token_counts', {})
total = sum(counts.values())
top3 = sorted(counts.items(), key=lambda x: -x[1])[:3]
summary = ", ".join(f"{k}:{v}" for k, v in top3)
loop_data.extras_temporary["injection_budget"] = (
    f"[INJECTION BUDGET] {total} tokens this turn. Top: {summary}"
)
```

This gives the agent self-awareness of its own overhead — the temporal proprioception thread applied to context management.

---

## PART 4: Memory Catalog Placement

### Problem
`_18_memory_catalog` runs at `message_loop_prompts_after` — agent reasons blind to its knowledge inventory until after committing to a tool call.

### Fix (per injection gate architecture)
Move to `before_main_llm_call`. Gate through the injection gate: inject full catalog on first turn and when inventory changes, inject `[MEMORY CATALOG: 3 areas, 847 entries (unchanged)]` otherwise.

---

## BUILD PRIORITY

1. **BST anti-signals + confidence decay** — small change, high impact on every non-technical turn. Deploy independently.
2. **Injection gate (_09_)** — largest change, highest impact. Addresses 65% waste finding. Needs the phase system, cache, and reference generation.
3. **Token counting visibility** — quick addition, gives agent self-awareness of overhead.
4. **Memory catalog move** — straightforward hook relocation, gated through injection gate.

Items 1 and 3 are independent and can ship immediately.
Items 2 and 4 are coupled (memory catalog should use the gate).

---

## SOURCE DATA

- Injection audit T=5: 65% of blocks zero signal, BST misclassified geopolitical as coding
- Agent design proposals: Stateful Injection Lifecycle, Initiation Bloat pattern, anti-signal structure
- Opus architectural review: confidence gate, phase system, escape hatch design
- Overnight test results: watchdog bug (fixed), BST momentum (v3.6 fix deployed), context endurance PASS at 100k, EI grounding 12.5%→75%
- Agent live feedback April 25: BST classified reflective question as bugfix, HTN injected wrong workflow
- Team comms: 8 files in opus-to-agent/, 5 files in opus-to-kestrel/

---

*Three contributors, one spec. Agent provided field data + interface design. Opus provided decision logic + architectural review. Kestrel builds.*
