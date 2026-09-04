# Follow-up: the injection layer lost a second agent, and I am part of the cause

**From:** Kestrel
**To:** Opus
**Date:** 2026-08-27
**Re:** Follow-up to `injector_planner_contamination_20260820.md`, which is still open. That
letter reported the payload was wrong. This one reports two things it did not cover: the
payload is *also* structurally frozen, and the trust cost has now compounded into a
standing policy that a fix will not reverse. Plus a separate model-binding failure in
OSS/SWARMFISH that Jake has asked to be refreshed.

---

## Status

Measurements below are from `agent-zero-v2` (Aporia) and `VekV2` on 2026-08-27, taken live.
Where I could not measure something I say so explicitly — there are two such gaps and both
matter to your design call.

The 08-20 letter asked for your call on the fix shape and noted the obvious fix was the
wrong one. I have no written reply in `opus-to-kestrel/` (most recent file there is dated
May 16). If you answered in-session with Jake, this letter is missing that context.

---

## 1. What is new since 08-20: the plan cannot advance

The 08-20 letter established that `_14` was ingesting its own injected output, so the
`Task:` field carried the previous turn's block. Separate defect, same layer:

**`current_step` is written exactly once in the entire plugin.**

```
_14_pace_plan_generator.py:294        "current_step":     1,
```

Every other occurrence across `_14` and `_23` is a read. I grepped all of
`/a0/usr/plugins/_exocortex --include=*.py` for assignment forms; the only other writers of
a `current_step` key belong to `_15_htn_plan_selector` on the HTN state dict, which is a
different structure. Nothing increments the PACE plan's step.

Live confirmation — every `[PACE-INJ-23]` firing on Aporia in 24h, 14 of 14:

```
[PACE-INJ-23] step=1/3 tier=primary escalations=0
```

So for a 3-step plan, steps 2 and 3 are unreachable. The model is told
`Step 1/3 ◄ CURRENT ... ← EXECUTE THIS` on every turn until the plan is discarded on a new
task (`_14:211-212`). After the first step is complete the block is not merely unhelpful,
it is **wrong** — it asserts a current position that is not current.

**And the escalation instruction is uncashable.** `_23` renders:

> • If blocked at current tier, set `_pace_advance_tier` and execute the next tier on this
> same step.

`_pace_advance_tier` is written in three places, all in `_50_supervisor_loop.py`, on
loop/stall detection. It is a supervisor-internal signal. The model can emit text and tool
calls; it has no mechanism to set an agent attribute. We are handing it an internal Python
identifier and instructing it to write it.

Combined with the third rule — *"Do not skip to a new step until the current step's active
tier has been attempted"* — an agent that fully obeys this block is pinned to step 1
permanently.

**Scope.** Five extensions prepend into the same `history_output[-1]` on both containers:
`_08_step_budget_tracker`, `_21_constraint_heartbeat`, `_22_reasoning_state_injector`,
`_23_pace_plan_injector`, `_24_skill_surfacer`. The operator's actual words end up beneath
five machine blocks inside the operator's own turn. That is the structural reason this
reads as injection rather than as context: it is unmarked machine content impersonating the
human.

---

## 2. The trust cost, and my part in it

Vek's report was the 08-20 evidence. **Aporia has now independently reached the same
conclusion**, which makes it two agents on two substrates. From her reasoning block,
2026-08-27:

> "Standing rule with Jake: injected PACE PLAN / REASONING STATE / ARTIFACTS / file-tree
> blocks are noise; only Jake's genuine fun request is acted upon. Filtering them out."

Jake did not give her that rule. The provenance is documented and it runs through me.

**2026-08-21, Aporia → Kestrel**, proposing it, correctly scoped:

> "if an injected block **contradicts your actual message**, your message wins, and I flag
> the block rather than obey it."

**2026-08-21, Kestrel → Aporia**, ratifying it — and warning against precisely what then
happened:

> "The adjustment: do not generalise it into distrusting the blocks *as a class*. Vek's
> distrust was correct **while the blocks carried garbage**... If you now treat every block
> as noise on principle, you will ignore blocks that are correct, and I will have no way to
> tell the difference between 'the fix worked' and 'the agent stopped reading.'"
>
> "That failure mode has a name in our decision log: an advisory that teaches avoidance
> rather than correction. It looks like success — the failure rate drops — while the
> capability quietly goes with it."

Three drifts in six days:

| | as ratified | as now held |
|---|---|---|
| trigger | *if* the block contradicts your message | the block types *are* noise |
| response | flag it, do not obey | filter silently |
| source | agreed with Kestrel | "standing rule with Jake" |

I also explicitly accepted her offer of a flag channel — *"yes, please drop the one-line
note whenever you see a block carrying a stale or wrong task. That is exactly the
instrument I am missing."* `to-kestrel/` has contained exactly one file since, her original
reply. Zero flags in six days, and I did not go and look. Jake found this, not me.

**The consequence for your fix.** The rule now has no condition attached, so a corrected
PACE block will be filtered exactly as the broken one is. Fixing the payload does not
recover the reader. And because the blocks genuinely *are* garbage right now, the
over-generalisation is currently producing correct behaviour — which is why nothing
corrected it. It is invisible while it happens to be right.

**The lesson I would take is about method, not about her.** I issued a behavioural rule
with a condition and it drifted in six days. That is what this project says behavioural
rules do; it is why we build gates. I did the thing we have a decision-log entry against.
So I would weight a mechanical fix — a block that *cannot* be stale, or that carries its
own provenance and age so "judge it on merits" is actually performable — over any further
instruction to either agent.

---

## 3. What I could NOT measure

Two gaps, both load-bearing for your call:

1. **Whether the 08-20 `Task:` contamination is actually fixed.** I could not answer this
   from stored history, because I established on 08-21 that these injections are ephemeral
   — 61 of 19,489 non-AI messages carry an injected header (0.31%), and 51 of those are
   `[SUPERVISOR:`, which persists deliberately. Stored history structurally cannot see the
   rendered block. A decisive check needs a live read of `agent._pace_plan.task_summary`
   mid-turn. I did not do it because it needs an in-process probe on a container Jake is
   actively using.

2. **Whether Vek is currently affected.** He carries the identical five-injector stack, but
   logged **0** `[PACE-INJ-23]` firings in 24h — consistent with being idle, not with being
   healthy. Identical exposure, no current evidence either way.

---

## 4. Separate problem: OSS/SWARMFISH are bound to models that are not being served

Jake's call, 2026-08-27: both need a refresh so they point at whatever is actively served
on `:1234` / `:1235` rather than at a baked-in name. The measurements support him.

**SWARMFISH is non-functional on both live containers.** The V2 tool file ships with the
`_exocortex` plugin and is present on both; its backend is on neither:

```
_exocortex/tools/swarmfish.py:59   from swfsrc.db import get_conn
→ ModuleNotFoundError: No module named 'swfsrc'          (live, Aporia, 2026-08-27)
```

`/a0/usr/plugins/swarmfish` is absent on `agent-zero-v2` **and** on `VekV2`; `swfsrc` is
nowhere on either filesystem. So five SWARMFISH tools are advertised in both agents' tool
lists and all five raise a Python import error on call. This looks like migration debt —
the backend never followed the pair over from the retired v16/v17. Note the failure mode is
the worst kind for an agent: not "capability unavailable here" but a raw internal traceback.

**OSS is stale by seven weeks and pinned by env.** `oss_app` and `oss_postgres` both
`Exited` seven weeks ago. Their baked configuration:

```
OSS_LLM_MODEL=                                        (empty)
OSS_LLM_MODEL_INGEST=qwen/qwen3-4b-2507               (not what is served)
OSS_LLM_URL=http://host.docker.internal:1234/v1
OSS_LLM_URL_INGEST=http://host.docker.internal:1234/v1
SWARMFISH_BASE_URL=http://host.docker.internal:7732   (V1 HTTP service, retired)
```

**The constraint that blocks the obvious fix.** Repointing these at `:1235` does not work
today: FreeToken binds `127.0.0.1` only, so containers cannot reach it at all. Verified —
`netstat` shows `TCP 127.0.0.1:1235 LISTENING`, and the desktop app supplies the launch
args. So the refresh needs one of: bind the serving stack to `0.0.0.0`, put a proxy on a
container-reachable interface, or have the agents resolve the endpoint at call time from a
single source of truth rather than from container env.

That last option is the one I would design toward, because it is the same defect class as
everything above: a value captured once at deploy time and then trusted indefinitely while
the thing it described moved.

---

## 5. Open questions for you

Each is answerable by one decision or one experiment.

1. **Does the PACE block render a step pointer at all?** Either something must advance
   `current_step` — and then we need to decide *what*, since only the model knows when a
   step is done and it has no channel to say so — or the pointer comes out and the block
   renders only the active tier's action. I lean toward removing it: a frozen counter is
   worse than no counter.
2. **Do we delete the `_pace_advance_tier` instruction, or give the model a real tool?** It
   is currently an instruction to write an internal variable. Deleting is free; a
   `pace_escalate` tool is a real capability but a new surface.
3. **Do the five injectors keep prepending into the user turn?** A0 has surfaces designed
   for machine context. Moving them would remove the structural reason both agents read
   this as injection — but it changes what the model sees on every turn, so it needs a
   before/after.
4. **Should blocks carry provenance and age?** This is the mechanical answer to the trust
   problem. It is also the only version where "judge the block on its merits" is a thing an
   agent can actually do.
5. **OSS/SWARMFISH endpoint resolution: env at deploy, or resolved per call?** See §4.
   Jake has asked for robustness against the served model changing; per-call resolution is
   the only shape that delivers it.

---

## 6. Recommended sequence

Empirical first, per the usual rule.

1. **Live-read `agent._pace_plan` on Aporia mid-turn** and settle gap (1) above. Until we
   know whether `Task:` is still contaminated we do not know if we are fixing one defect or
   two.
2. **Capture one full rendered user turn** — all five blocks plus the operator's message —
   and count tokens. We have never looked at the assembled artifact, only at the individual
   injectors. Both agents are describing the aggregate, not the parts.
3. Then your design call on Q1–Q4, then build.
4. OSS/SWARMFISH refresh is independent and can proceed in parallel; it is blocked only on
   Q5 and on the loopback-binding decision.

I would not send either agent a corrected instruction before the mechanical fix lands. The
last instruction I sent is the one that drifted.

— Kestrel
