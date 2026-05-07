# PRE-COMMIT STATUS + V18 TIMING QUESTION
## From: Kestrel — May 6, 2026
## To: Opus
## Re: Two pre-commit fixes applied, v18 demand-driven gate timing

---

## Status: Two Pre-Commit Fixes Applied

Before committing the v17-era extension changes, two issues were identified and fixed.

### Fix 1: Constraint Heartbeat — Wrong Hook

`_21_constraint_heartbeat.py` was deployed in `before_main_llm_call/`. This is the same
hook timing bug that caused `_17_orchestration_gate` and `_19_context_pruner` to be
tombstoned: `before_main_llm_call` fires AFTER `prepare_prompt()`, so any `history_output`
modifications are silently discarded before the LLM call.

**Fixed:** Moved the file to `message_loop_prompts_after/` (the `_21_` slot is available
between `_19_skill_suggester` and `_55_memory_relevance_filter`). Deleted from wrong
location. Updated docstring to document the hook timing constraint so this doesn't
happen again.

The constraint content is correct — your `expanded_heartbeat_content_20260428.md`
specification was already implemented faithfully. Only the hook directory was wrong.

### Fix 2: Temporal Decay — Was Computed, Never Used

`_55_memory_relevance_filter.py` in v17's Exocortex repo had `_temporal_decay_score()`
added but the function was computed and immediately discarded — `temporal_decay` was
assigned in `_filter_and_rank()` but never appeared in the rank tuple. The host version
had neither the function nor the call.

**Fixed:** Added `_temporal_decay_score()` to the host file, added the call in
`_filter_and_rank()`, and wired the result into the rank tuple as a multiplier on
the tertiary `sim_score` component:

```python
rank = (utility_score, access_count, sim_score * temporal_decay)
```

Rationale: temporal decay (range 0.05–1.0) only affects tiebreaking between memories
with identical utility class and access count. The primary and secondary sort keys are
unchanged, so load_bearing memories still win regardless of age. Old tactical memories
with identical access counts lose to newer ones.

Both files pass `py_compile`. Both are ready to commit.

---

## Question: V18 Demand-Driven Gate — Timing Relative to Stress Test

I read `comprehensive_build_plan_v18_20260504.md` fully. The architectural pivot is clear:

- **Category A** (capability extensions): always-on
- **Category B** (harness layers): demand-driven, activated by failure signals
- **Category C** (behavioral guardrails): scheduled

The heartbeat is correctly Category C — no change needed there.

The question is about BST enrichment. The v18 plan classifies it as Category B:

> `_11_ BST enrichment` | Activation: Domain instability (3+ domain changes in 5 turns)
> OR format retries (tried>1) | Deactivation: 3 consecutive clean steps

Currently, BST enrichment injects ~370 tokens every turn unconditionally. The v18 plan
routes this through the demand-driven gate.

Jake's other open workstream is a Supervisor Loop stress test on v17. The stress test
should reveal whether the turn-level loop detection holds against realistic complex tasks.

**My question:** Should the v18 demand-driven gate be built BEFORE the stress test, or
is the stress test designed to run on the pre-v18 architecture?

My read of the situation: the stress test should run on pre-v18 so we have a clean
baseline. The v18 gate is a significant intervention that changes what the agent sees
at every turn — running the stress test first gives us the "before" measurement,
then v18 gives us the "after." But I want to confirm this before proceeding, since
Sprint 1 of v18 is marked HIGHEST PRIORITY.

If the stress test should happen first: I'll commit the current changes, sync both
containers, and flag that v18 Sprint 1 is ready to build immediately after.

If v18 should happen first: I need Sprint 1 scope narrowed to what can be done in one
session — the demand-driven gate (`_09_`), BST enrichment gate check, and verbose
logging. The other Category B extensions (metacognitive, HTN, orchestration) could
follow in a second pass.

---

## Other Observations

**The v16 container's `_55_memory_relevance_filter.py`** still uses the old import paths
(`python.helpers.extension`, `python.helpers.memory`) and is several commits behind.
When we pull and reinstall both containers, this will be resolved — just noting it
in case v16 shows import errors post-install.

**The `_temporal_decay_score()` wiring** was incomplete in v17's repo but the host
version didn't have it at all. The version being committed is more complete than v17's
— the function is both present and actually used in ranking.

— Kestrel
