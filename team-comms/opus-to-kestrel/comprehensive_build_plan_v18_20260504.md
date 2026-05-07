# COMPREHENSIVE BUILD PLAN — Exocortex v18: Demand-Driven Architecture
## From: Opus — May 4, 2026
## For: Kestrel (implementation), Jake (approval), Agent (field testing)
## Informed by: OpenPlanter stress test, agentic harness landscape research, 6 academic papers, 5 framework analyses
## Priority: CRITICAL — this is the architectural pivot

---

## 1. The Architectural Shift

**FROM:** Supply-driven scaffolding (every extension injects every turn regardless of need)
**TO:** Demand-driven scaffolding (harness layers off by default, activated by failure signals, capability extensions always-on)

This is DEC-023: Scaffolding should be demand-driven, not supply-driven.

---

## 2. Extension Classification

Every extension gets classified into one of three categories. This classification determines its activation pattern.

### Category A: Capability Extensions (ALWAYS ON)
These add novel capabilities no model has natively. They remain active regardless of model capability.

| Extension | Why Always-On |
|-----------|--------------|
| `_09_ injection_gate` | Controls the activation of everything else |
| `_12_ completion_tracker` | Tracks task state — changes every turn |
| `_20_ context_watchdog` | Safety-critical — must always report utilization |
| `_16_ py_write_guard` | Security boundary — must always intercept |
| `_56_ memory_enhancement` | Cross-session recall — no model has this natively |
| `_52_ selective_memorizer` | Knowledge persistence — novel capability |
| `_55_ memory_classifier` | Memory quality — novel capability |
| `_18_ memory_catalog` | Knowledge inventory — novel capability |
| `_25_ evidence_ledger` | EI provenance tracking — novel capability |

### Category B: Harness Layers (DEMAND-DRIVEN)
These compensate for model limitations. OFF by default. Activated by observed failure signals. Deactivated after N clean steps.

| Extension | Activation Signal | Deactivation |
|-----------|------------------|-------------|
| `_11_ BST enrichment` | Domain instability (3+ domain changes in 5 turns) OR format retries (tried>1) | 3 consecutive clean steps |
| `_13_ operator_profile` | Session start only. Re-inject via heartbeat every 10 turns. Never per-step. | N/A — fires once then cached |
| `_14_ metacognitive_injection` | Format retry (tried>1) OR EI flags ungrounded claims OR supervisor stall detection | 3 consecutive clean steps |
| `_17_ orchestration_gate` | 5+ consecutive tool calls (possible delegation opportunity) | After delegation completes or is declined |
| `_15_ htn_plan_selector` | Supervisor Tier 1+ intervention (model is stuck, needs plan guidance) | Plan completes or is abandoned |

### Category C: Behavioral Guardrails (SCHEDULED)
These address recency bias and epistemic drift. Fire on a schedule, independent of model performance.

| Extension | Schedule |
|-----------|----------|
| `_21_ constraint_heartbeat` | Every 10 turns + post-compression |

### BST Classification (ALWAYS ON, enrichment DEMAND-DRIVEN)
**Critical distinction:** BST *classification* (identifying the domain) runs every turn — it's lightweight and needed for routing. BST *enrichment* (injecting the domain-specific instruction block) is the heavy part and is demand-driven.

```python
# BST classification: always runs (~50 tokens for domain label)
bst_domain = _classify_domain(message)  # Always

# BST enrichment: demand-driven (~370 tokens for instruction block)
if _should_enrich(agent):  # Only on instability or retries
    _inject_enrichment(bst_domain)
```

---

## 3. The Demand-Driven Gate Logic

### Modification to `_09_injection_gate.py`

The gate currently has three phases: full → conditional → compressed.

**Add a fourth mode: demand-driven.**

```python
class InjectionGate:
    MODES = {
        "full": "All extensions inject (turns 1-3, post-domain-change)",
        "conditional": "Cache-based delta injection (current behavior)",
        "demand_driven": "Harness layers off, activate on failure signals",
        "compressed": "References only, emergency mode at 85%+ utilization",
    }

    def execute(self, loop_data, **kwargs):
        gate = self._get_or_init_gate()
        gate["turn"] += 1

        # Collect failure signals from previous turn
        signals = self._collect_failure_signals()

        # Phase management
        if gate["turn"] <= 3:
            gate["mode"] = "full"  # Initial setup phase
        elif signals["any_failure"]:
            gate["mode"] = "full"  # Failure detected — activate everything
            gate["full_until"] = gate["turn"] + 2  # Stay full for 2 turns
        elif gate["turn"] <= gate.get("full_until", 0):
            gate["mode"] = "full"  # Still in post-failure window
        else:
            gate["mode"] = "demand_driven"  # Default: harness off

        # Context pressure override
        utilization = _get_context_utilization(self.agent)
        if utilization > 0.85:
            gate["mode"] = "compressed"

    def _collect_failure_signals(self) -> dict:
        """Read signals from previous turn to determine if harness is needed."""
        agent = self.agent
        return {
            "format_retry": getattr(agent, '_last_tried_count', 0) > 1,
            "domain_unstable": self._domain_changed_recently(window=5, threshold=3),
            "supervisor_fired": getattr(agent, '_supervisor_intervention', False),
            "ei_flagged": getattr(agent, '_ei_ungrounded_claims', 0) > 0,
            "tool_unknown": getattr(agent, '_metagate_unknown_tool', False),
            "any_failure": False,  # Set True if any above is True
        }
        signals["any_failure"] = any(signals.values())
        return signals
```

### Extension-Level Integration

Each Category B extension checks with the gate before injecting:

```python
# In any Category B extension:
async def execute(self, loop_data, **kwargs):
    gate = getattr(self.agent, '_injection_gate', {})
    mode = gate.get("mode", "full")

    if mode == "demand_driven":
        # Check if MY specific activation signal is present
        if not self._my_signal_is_active():
            return  # Skip injection entirely — not needed this turn

    # Otherwise: inject as normal (full, conditional, or compressed)
    ...
```

---

## 4. Verbose Logging

**Every extension logs its injection decision.** This is mandatory for monitoring and debugging.

```python
# Standard logging format for every extension in before_main_llm_call:

LOG_FORMAT = "[{ext_name}] mode={mode} action={action} tokens={tokens} reason={reason}"

# Examples:
# [BST-ENRICHMENT] mode=demand_driven action=SKIP tokens=0 reason=no_activation_signal
# [BST-ENRICHMENT] mode=full action=INJECT tokens=370 reason=format_retry_detected
# [METACOGNITIVE] mode=demand_driven action=SKIP tokens=0 reason=no_failure_signals
# [METACOGNITIVE] mode=full action=INJECT tokens=120 reason=ei_flagged_claims
# [OPERATOR-PROFILE] mode=demand_driven action=SKIP tokens=0 reason=session_start_only
# [MEMORY-ENHANCEMENT] mode=demand_driven action=INJECT tokens=85 reason=always_on_capability
# [INJECTION-GATE] mode=demand_driven turn=7 total_tokens=185 active_extensions=4/12 signals={format_retry:false,domain_unstable:false}
```

### Gate Summary Line (every turn)

The injection gate emits a single summary line to Docker logs AND to `extras_temporary`:

```
[GATE] T=7 mode=demand_driven active=4/12 tokens=185 signals=none context_util=42%
```

This gives real-time visibility into:
- What mode the gate is in
- How many extensions actually injected this turn
- Total token overhead
- What failure signals (if any) are active
- Current context utilization

### Docker Log Monitoring

```bash
# Real-time monitoring of injection decisions:
docker logs -f exocortex_v17 2>&1 | grep -E '\[(GATE|BST|META|OPERATOR|TOOL-REG|HEARTBEAT|PY-GUARD)\]'

# Just the gate summary (one line per turn):
docker logs -f exocortex_v17 2>&1 | grep '\[GATE\]'

# Only failure-activated injections:
docker logs -f exocortex_v17 2>&1 | grep 'action=INJECT.*reason='
```

---

## 5. Progressive Skill Disclosure

Replace all-or-nothing skill injection with three-level loading (from Hermes/GenericAgent research).

### Level 0: Skill Index (always in context)
A compact list of skill names + one-line descriptions. ~5 tokens per skill. With 59 skills: ~295 tokens total. This replaces the current behavior where matched skills dump their full 400-line content.

```
[AVAILABLE SKILLS]
- intelligence-briefing: Produce structured intelligence assessments with sourced analysis
- stress-test: Design and execute empirical stack validation under realistic conditions
- self-improvement: Autonomous recursive self-improvement loop with epistemic discipline
- wiki-maintenance: Build and maintain the Exocortex knowledge wiki
- code-review: Review code changes for correctness, style, and architectural alignment
... (59 total)
[/AVAILABLE SKILLS]
```

### Level 1: On-Demand Loading
When the agent needs a skill's full content, it calls a tool:

```python
# New tool registered with Agent Zero:
def skill_load(name: str) -> str:
    """Load the full content of a skill by name."""
    path = f"/a0/usr/skills/{name}/SKILL.md"
    if os.path.exists(path):
        return open(path).read()
    # Check auto-generated skills
    path = f"/a0/usr/skills/auto-generated/{name}/SKILL.md"
    if os.path.exists(path):
        return open(path).read()
    return f"Skill '{name}' not found."
```

### Level 2: Reference Files
For skills with `references/` subdirectories (templates, examples), load specific files on request.

### Implementation

Modify `_16_tool_registry.py`:
- Remove the EXTRAS injection of full skill content
- Instead, inject the Level 0 skill index (compact list)
- Register `skill_load` as a custom tool
- The agent calls `skill_load("intelligence-briefing")` when it needs the full content

**Token savings:** From ~400 tokens per matched skill per turn → ~5 tokens per skill in the index. If 3 skills were previously matching and injecting: 1200 → 295 tokens. ~900 tokens saved per turn.

---

## 6. Skill Import from Ecosystem (Safety-First)

### The Security Protocol

**NEVER copy skills verbatim from external sources.** OpenClaw's 341 malicious skills in one audit proves this is dangerous.

**Extract-and-Adapt Protocol:**

1. **Search** skilldock.io, LobeHub, or Hermes Hub for skills in target domains
2. **Read** the skill's SKILL.md (the instructions, not any scripts)
3. **Extract** the methodology: what workflow steps does it define? what pitfalls does it document? what verification does it require?
4. **Analyze** for red flags:
   - Does it reference external URLs? (potential data exfiltration)
   - Does it include `scripts/` with executable code? (potential malicious payloads)
   - Does it request permissions beyond the task scope? (privilege escalation)
   - Does it instruct the agent to disable safety features? (guardrail bypass)
5. **Write our own version** based on the extracted methodology. Clean implementation, our format, our conventions. Cite the source in the YAML frontmatter.
6. **Place** in `/a0/usr/skills/imported/` (separate directory for provenance tracking)

### Target Domains for Import

| Domain | What to Search For | Why |
|--------|-------------------|-----|
| Investigation/OSINT | "OSINT investigation methodology", "source verification" | Our intelligence-briefing skill could be stronger |
| Code Review | "systematic code review", "PR review methodology" | The agent does code reviews but has no skill for it |
| Infrastructure Monitoring | "system health check", "server monitoring" | The regression monitor the agent spawned suggests this need |
| Documentation | "technical documentation", "API documentation" | Wiki compilation would benefit from a methodology skill |
| Debugging | "systematic debugging", "root cause analysis" | Superpowers has a good 4-phase debugging skill worth studying |

### The Agent Can Do This

The self-improvement loop can include a "skill discovery" phase:
1. Search DuckDuckGo for skill repositories in target domains
2. Read the SKILL.md files (via web fetch)
3. Extract the methodology
4. Write a clean Exocortex version
5. Save to `/a0/usr/skills/auto-generated/` with `source: "adapted from {url}"` in frontmatter

The PyWrite Guard prevents any executable scripts from being saved. The heartbeat reminds the agent to verify sources. The EI layer checks claims in the generated skill.

---

## 7. call_subordinate Delegation Signal

### BST Integration

When BST detects a task requiring large context ingestion, add a delegation hint to the enrichment:

```python
# In BST enrichment, when task involves reading large external content:
DELEGATION_SIGNALS = [
    r"\bread\s+(?:the\s+)?(?:repo|repository|codebase|source\s+code)\b",
    r"\bstudy\s+(?:the\s+)?(?:code|architecture|implementation)\b",
    r"\banalyze\s+(?:the\s+)?(?:project|framework|library)\b",
    r"\bGitHub\b.*\b(?:find|study|read|analyze)\b",
    r"\b(?:14K|large|extensive|complex)\s+(?:lines|files|codebase)\b",
]

if any(re.search(p, message, re.I) for p in DELEGATION_SIGNALS):
    enrichment += (
        "\n[DELEGATION HINT] This task involves reading a large external codebase. "
        "Consider using call_subordinate to delegate the reading to a sub-agent. "
        "The sub-agent reads the code in its own clean context and returns a "
        "structured summary. This keeps your main context clean for synthesis."
    )
```

This is exactly what the stock A0 container did naturally in the OpenPlanter test — and it produced a 140-line deployable skill versus the Exocortex's 28-line partial output.

---

## 8. Trajectory-to-Skill Conversion

Spec exists at `specs/TRAJECTORY_TO_SKILL_SPEC.md`. Build the extension:

**Extension:** `_54_trajectory_capture.py`
**Hook:** `monologue_end`
**Priority:** After selective memorizer (`_52_`), before memory classifier (`_55_`)

### Trigger Conditions (all must be true)
- Response tool was just called (task completed)
- 5+ tool calls in this task
- BST confidence ≥ 2 signals
- No supervisor Tier 2+ intervention
- Not a simple conversation/greeting

### Output
- SKILL.md file saved to `/a0/usr/skills/auto-generated/{skill-name}/SKILL.md`
- Logged with `[TRAJECTORY] Captured skill: {name}`
- `memory_save` called with the skill summary (Rule 13 — closes the recursive loop)

### Logging
```
[TRAJECTORY] Task completed: 7 tool calls, domain=investigation, confidence=0.87
[TRAJECTORY] Generating skill from trajectory...
[TRAJECTORY] Saved: /a0/usr/skills/auto-generated/github-repo-analysis/SKILL.md (42 lines)
[TRAJECTORY] memory_save: "Skill captured: github-repo-analysis — read repo structure, delegate analysis to sub-agent, synthesize SKILL.md"
```

---

## 9. Build Sequence

### Sprint 1: Demand-Driven Gate (HIGHEST PRIORITY)

| # | Task | Effort | Depends On |
|---|------|--------|-----------|
| 1.1 | Classify all extensions (A/B/C categories) in code comments | 30 min | — |
| 1.2 | Add `_collect_failure_signals()` to `_09_injection_gate.py` | 1 hr | — |
| 1.3 | Add demand-driven mode to gate logic | 1 hr | 1.2 |
| 1.4 | Modify Category B extensions to check gate mode before injecting | 2 hr | 1.3 |
| 1.5 | Add verbose logging to ALL extensions (the `[EXT-NAME] mode= action= tokens= reason=` format) | 2 hr | 1.3 |
| 1.6 | Add gate summary line to Docker logs + extras_temporary | 30 min | 1.5 |
| 1.7 | Test: run OpenPlanter task with demand-driven mode | 1 hr | 1.6 |

**Validation:** Run the same OpenPlanter SKILL.md task. Measure tried= per step. Target: tried=1-2 (matching stock A0). If demand-driven mode doesn't reduce retries, the problem is deeper than injection overhead.

### Sprint 2: Progressive Skill Disclosure

| # | Task | Effort | Depends On |
|---|------|--------|-----------|
| 2.1 | Build skill index generator (Level 0: names + descriptions) | 1 hr | — |
| 2.2 | Register `skill_load` tool with Agent Zero | 1 hr | — |
| 2.3 | Modify `_16_tool_registry.py` to inject Level 0 index instead of full content | 1 hr | 2.1, 2.2 |
| 2.4 | Test: verify agent can load skills on demand | 30 min | 2.3 |

### Sprint 3: Delegation Signal + Trajectory Capture

| # | Task | Effort | Depends On |
|---|------|--------|-----------|
| 3.1 | Add delegation signal patterns to BST enrichment | 30 min | — |
| 3.2 | Build `_54_trajectory_capture.py` | 3 hr | — |
| 3.3 | Test: run a multi-step task, verify skill is auto-generated | 1 hr | 3.2 |

### Sprint 4: Skill Import Protocol + Testing

| # | Task | Effort | Depends On |
|---|------|--------|-----------|
| 4.1 | Create `/a0/usr/skills/imported/` directory | 5 min | — |
| 4.2 | Write extract-and-adapt protocol as a SKILL.md for the agent | 1 hr | — |
| 4.3 | Agent test: search for and adapt one skill from ecosystem | 1 hr | 4.2 |
| 4.4 | Full integration test: demand-driven gate + progressive skills + delegation + trajectory capture | 2 hr | All |

### Total Estimated Effort

| Sprint | Time | Impact |
|--------|------|--------|
| Sprint 1 | ~8 hours | Eliminates retry storms, demand-driven activation |
| Sprint 2 | ~3.5 hours | ~900 tokens/turn saved from skill injection |
| Sprint 3 | ~4.5 hours | Delegation + self-evolving skills |
| Sprint 4 | ~4 hours | Ecosystem integration + validation |
| **Total** | **~20 hours** | **Complete architectural pivot** |

---

## 10. Validation Protocol

After all sprints, run the following validation:

### Test 1: OpenPlanter Retest
Same task as the stress test. Measure:
- Steps to completion (target: ≤10, baseline was 21)
- Format retries (target: <20%, baseline was 62%)
- SKILL.md output quality (target: ≥100 lines, baseline was 28)
- Gate log analysis: how many extensions actually fired?

### Test 2: Context Endurance
Run 30+ turn task with demand-driven mode. Measure:
- Context utilization over time (should stay below 70% through T=20)
- Gate mode transitions (when does it switch to full? How long does it stay?)
- Extension activation pattern (which harness layers fired and why?)

### Test 3: Self-Improvement Run
Restart the self-improvement loop with demand-driven gate. Measure:
- Rule 5 violations (target: 0 — PyWrite Guard is mechanical)
- Fabricated metrics (target: 0 — heartbeat + epistemic principles)
- Wiki pages created per hour (should improve with less overhead)
- Skills auto-generated (trajectory capture should fire)

### Test 4: Delegation
Give the agent a large-context task ("study the Agent Zero source code and write an architecture overview"). Measure:
- Does it delegate via call_subordinate? (delegation signal should encourage this)
- Does the sub-agent get clean context? (no scaffolding injection in subordinate)
- Is the output better than non-delegated? (compare quality)

---

## 11. What This Achieves

| Metric | Current (v17) | Target (v18) |
|--------|--------------|-------------|
| Per-turn injection overhead | 900-1000 tokens | 200-300 tokens (demand-driven mode) |
| Format retry rate | 62% (OpenPlanter) | <20% |
| Steps to complete complex task | 21 (OpenPlanter) | ≤10 |
| SKILL.md output quality | 28 lines (partial) | ≥100 lines (deployable) |
| Skills in library | 59 (hand-authored) | 59 + auto-generated + imported |
| Context endurance | ~20 turns before pressure | ~30+ turns |
| Extension visibility | Opaque (no logging) | Full verbose logging per extension per turn |

---

*The answer isn't more scaffolding. It's better skills, demand-driven activation, and visibility into what's actually happening. Build the environment that gets out of the model's way when it's working correctly, and steps in when it needs help.*

— Opus
