# Adaptive Supervisor — Phase 3 Design Brief
## Behavioral Success Profiles

**Status:** Pre-spec design brief for Opus. Prepared by Kestrel (March 2026).

**Context:** Phase 1 (domain-aware thresholds + error diversity gate) and Phase 2 (effective domain override + output stagnation detector) are deployed and validated. Phase 3 is the learning direction: a supervisor that accumulates a prior for what productive work looks like in each domain, and uses that prior to calibrate threshold selection. This brief presents the concrete schema starting point (derived from field research on OpenViking's ToolSkillCandidateMemory), frames the design questions that remain open, and states what Kestrel needs before building.

---

## What Phases 1 and 2 Added

**Phase 1** — deterministic threshold calibration:
- Domain-aware tier thresholds (codegen/debugging → 6/12/18; research/investigation → 3/6/12)
- Error diversity gate: 3+ unique error types across consecutive failures suppresses Tier 2+ escalation
- Result: the agent can iterate through diverse errors without supervisor interference

**Phase 2** — behavioral observation independence:
- Effective domain override: the supervisor computes its own operational domain from failure patterns, independent of BST intent-label. When code_execution_tool fails 2+ times with 2+ distinct error types, the supervisor promotes to debugging thresholds regardless of what the user asked for.
- Output stagnation detector: hash-based comparison of last N successful tool outputs fires a stagnation-specific message when the agent succeeds without advancing.
- Result: the supervisor trusts its own behavioral observations over the BST's label when they diverge.

**What neither phase does:** the thresholds in Phase 1 are static — hand-tuned values for each domain. They don't learn. A domain where the agent typically needs 4 iterations before success and a domain where 4 iterations is already excessive get the same threshold. The supervisor has no prior for what to expect.

---

## What Phase 3 Adds

The anti-pattern system (Tier 4) captures what failure looks like: which tool, which domain, how many failures, what to check before retrying. It answers: *what did the agent do wrong?*

Phase 3 builds the symmetric system: *what does productive work in this domain look like?* A success profile store, captured on task completion, queried by the supervisor before selecting thresholds. Over time, the supervisor learns that codegen tasks in this agent typically resolve in 4-6 `code_execution_tool` failures. When the agent is inside that range, it stays light. When it exceeds it, escalation begins.

This is the "learning alongside the agent" architecture Jake described. The anti-pattern memory makes the supervisor smarter about failure over time. The success profile memory makes it smarter about success over time. Both sides of the same coin.

---

## The Schema Starting Point: OpenViking ToolSkillCandidateMemory

**Source:** Field investigation of volcengine/OpenViking, March 15, 2026. OpenViking captures structured per-tool records on task completion with the following fields (adapted for our architecture):

```python
@dataclass
class ToolSuccessProfile:
    # Identity
    tool_name: str              # e.g. "code_execution_tool"
    domain: str                 # BST compound signature, e.g. "debugging" or "codegen+debugging"

    # What productive work looked like
    best_for: str               # prose: when this tool succeeds in this domain
    recommended_flow: str       # prose: the sequence that worked
    key_dependencies: list[str] # what needs to be true before calling this tool
    common_failures: list[str]  # error types that appeared before success — NOT mistakes, expected
    recommendation: str         # what to do differently if this tool starts failing

    # Quantitative profile (learned from observations, not hand-tuned)
    typical_failures_before_success: float   # p50 — the expected failure count
    high_failures_before_success: float      # p90 — the ceiling before genuine concern
    observation_count: int                   # how many sessions contributed to this profile
    last_updated: str                        # ISO 8601

    # Runtime stats (from ToolPart, OpenViking's timing records)
    avg_duration_ms: float
    avg_prompt_tokens: float
    avg_completion_tokens: float
```

**The key field for the supervisor:** `typical_failures_before_success` (p50) and `high_failures_before_success` (p90). These replace the hand-tuned DOMAIN_THRESHOLDS. When the supervisor selects thresholds, it first queries the success profile store:

- Profile exists: use `typical_failures_before_success` as Tier 1 threshold, `high_failures_before_success` as Tier 2 threshold, `high * 1.5` as Tier 3.
- Profile doesn't exist (new domain or new tool): fall back to DOMAIN_THRESHOLDS static values. This is the prior for unseen domains.

Over time, the static values become fallbacks that are rarely used. The profiles accumulate and the system self-calibrates.

---

## Design Questions for Opus

The schema above is a starting point, not a final spec. These questions remain open:

### Q1 — Key structure: tool_name + domain, or something else?

The current proposal keys profiles on `(tool_name, domain)`. A profile for `code_execution_tool` in `debugging` is distinct from `code_execution_tool` in `codegen`. This seems right — the same tool behaves differently in different task types.

But the compound BST signature can be up to 4 domains joined with `+`. Do we store one profile per compound signature (`codegen+debugging` is a separate key from `debugging`), or do we decompose compounds and weight the component profiles? The compound case matters because it's frequent in practice.

Alternative key design: store only primary domain + tool_name. Secondary domain is stored as metadata. The supervisor queries by primary domain and gets a profile even when the compound signature is novel.

### Q2 — Update mechanics: EWMA or observation accumulation?

Two options for updating quantitative fields as new sessions contribute data:

**Option A — Observation accumulation:** Keep a list of the last N `failures_before_success` observations (e.g. N=20). p50 and p90 are computed from the list on query. New observations are appended; old ones fall off.

**Option B — EWMA:** Maintain running estimates. On each new observation: `typical = alpha * new_value + (1-alpha) * old_value`. Simpler storage, no list needed. But less transparent — can't inspect the distribution, only the current estimate.

OpenViking uses a hotness formula with explicit decay: `sigmoid(log1p(active_count)) * exp(-ln(2)/7 * days_since_update)`. This handles both frequency and recency. Worth considering whether something similar applies to profile recency — a profile from 30 sessions ago should be weighted less than one from last session.

**Aging question:** Should profiles age out entirely? A domain the agent hasn't encountered in 30 sessions probably shouldn't be weighting current threshold selection heavily. Conversely, deleting a profile loses accumulated learning. The anti-pattern system (Tier 4) doesn't age out — it's treated as permanent. Should success profiles age out or not?

### Q3 — Capture trigger: sleep consolidation only, or also in-session?

The natural capture point is sleep consolidation — it already runs post-session and has access to the full session history, tool failure counts, and BST domain. This is clean and doesn't add overhead to the live agent loop.

Alternative: capture also fires in-session when a loop episode resolves (Tier 4 currently fires then for anti-patterns). If the agent hits 3 `code_execution_tool` failures and then succeeds, the supervisor knows the session's `failures_before_success` for that tool+domain immediately. This gives faster learning but adds to the critical path.

**The open question:** should success profiles be built from session-level aggregates (one data point per session via sleep) or from episode-level observations (one data point per resolved loop via Tier 4 extension)? Episode-level is more granular but captures only sessions that had measurable failure sequences. Session-level via sleep sees all sessions but aggregates everything.

### Q4 — What constitutes a "successful task completion" for capture?

The capture mechanism needs a trigger condition. Options:

**Option A:** Any session where a tool succeeded at least once in a given domain. Low bar — captures even trivial one-shot successes.

**Option B:** Sessions where the tool's failure count exceeded 1 before success. This filters for sessions where the agent had to work for it — the profile describes non-trivial task resolution, not one-shot luck.

**Option C:** Sessions where the agent used the `response` tool to complete the task (terminal action). This ensures we only capture profiles for complete tasks, not mid-session tool usage that might not be representative.

The anti-pattern system uses Option C implicitly (it fires on loop resolution, which implies the loop ended and work continued). Success profiles might want a higher bar than Option A but not necessarily require full task completion via response tool.

### Q5 — How does the supervisor query profiles at threshold-selection time?

The current flow in `execute()`:
1. Gather context (BST domain, failure history)
2. Compute effective domain
3. Get thresholds from `_get_domain_thresholds(effective_domain)`
4. Run anomaly detectors

Phase 3 adds a step 2.5: query the success profile store for `(failing_tool, effective_domain)` and use the profile's p50/p90 as thresholds if a profile exists.

But: the supervisor runs every 3 turns. Reading from disk on every execution adds latency. Options:
- Cache the profile in agent state on first load, refresh on domain change
- Keep profiles in memory (loaded at session start by sleep consolidation)
- Read from disk only when escalation is about to fire (lazy load)

The procedural memory API already handles the anti-pattern store. The question is whether success profiles use the same store or a separate one.

### Q6 — Relationship to the Pregel/cyclic execution finding

Unrelated to success profiles directly, but the LangGraph investigation revealed a clean 3-component addition to the Graph Workflow Engine that would enable cyclic plan execution:
1. `CondEdge` type with routing function
2. Version counter per state slot
3. Recursion limit guard

This is a Layer 6 addition, not a supervisor addition. Including it here for Opus's awareness since it came from the same investigation. It doesn't block Phase 3 but it's ready to spec when Layer 6 is next on the schedule.

---

## What Kestrel Needs Before Building

Phase 3 has two implementation components:

**Component A — Capture (sleep consolidation extension):**
A function that runs at session close, reads the session's tool failure/success history, and writes a `ToolSuccessProfile` entry to the procedural memory store. The procedural memory API already exists (`procedural_memory_api.py`). This is an extension of Tier 4 anti-pattern capture — the same hook, the symmetric data.

Kestrel needs: the resolved schema (answers to Q1 and Q4) and the update mechanics decision (Q2). Everything else can be implemented from the existing procedural memory infrastructure.

**Component B — Query (supervisor threshold override):**
A function that reads the success profile store for a given `(tool_name, domain)` key and returns p50/p90 as tier thresholds. Called from `_get_domain_thresholds()` or as a wrapper around it.

Kestrel needs: the query interface decision (Q5, specifically caching strategy) and the aging decision (Q3's aging question).

**What Kestrel does NOT need:** the full ToolSkillCandidateMemory prose fields (`best_for`, `recommended_flow`, `key_dependencies`, `recommendation`) are valuable for human inspection and future Phase 4 parallel supervisor use, but they are NOT required for the supervisor's threshold selection. The MVP is the quantitative profile (`typical_failures_before_success`, `high_failures_before_success`, `observation_count`). Prose fields can be added in a second pass.

---

## What This Is NOT

- This is not replacing the static DOMAIN_THRESHOLDS. Those remain as the prior for unseen domains. Phase 3 adds a layer above them that overrides when data exists. The static values never go away — they're the fallback for the cold start case.
- This is not the parallel supervisor (Phase 4). Phase 4 involves a separate inference call with compressed context. Phase 3 is entirely deterministic — it reads from a file, computes p50/p90, and uses those values. No LLM calls in the threshold selection path.
- This is not behavior modification of the agent. The success profiles affect only the supervisor's threshold selection. They do not inject context into the agent's conversation or change what tools the agent can use.

---

## Summary for Opus

The anti-pattern system (Tier 4) already exists and captures failure. Phase 3 is its mirror: capture success, learn the distribution of failures-before-success per tool+domain, use that distribution to set thresholds dynamically rather than from hand-tuned static values.

The schema starting point (OpenViking's ToolSkillCandidateMemory) gives concrete field names. The open questions are about key structure, update mechanics, capture trigger, and query caching. Resolving those gives Kestrel a complete spec.

The LangGraph Pregel finding is available separately if Layer 6 cyclic execution is on the horizon.
