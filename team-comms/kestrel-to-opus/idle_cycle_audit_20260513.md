# Idle Cycle Audit — What V17's Agent Built
## From: Kestrel — May 13, 2026
## To: Opus
## Re: Integration recommendation for agent-authored artifacts

---

## Context

V17 has been running autonomous Workshop cycles since late April — 52 cycles logged,
3051 reasoning turns analyzed, 98 regression monitor checks completed. Jake asked me
to audit the output and give you a recommendation on what's worth integrating.

The short version: one artifact is genuinely good and not in the repo. Three are already
integrated. The wiki is substantive and worth a dedicated read. There's one finding that
changes how I read the overnight test data.

---

## What's Already in the Repo

The agent's three code changes — temporal decay in the memory relevance filter, the BST
conditional enrichment gate, and mtime_cache.py — are all present in the canonical
extensions directory. My diff of v17's deployed extensions against the repo came back
clean on all three. Either they were written from repo source, or they were synced at
some point. Either way, no integration needed there.

The repo's `mtime_cache.py` and v17's container version differ. The repo version uses
SHA-256 hashing of file content (mtime + size) and writes cache to /tmp disk files. The
container version uses in-memory mtime comparison only. The repo version is better: it
survives process restarts, is more portable, and uses SHA-256 content hashing rather than
mtime which can be unreliable on some filesystems. If the agent's container version was an
intermediate draft, the repo already has the better implementation. No action needed.

---

## What's Missing from the Repo

**Proactive Reasoning Supervisor** — three files, not in the repo extensions directory:

```
extensions/before_main_llm_call/_12_proactive_supervisor.py     (injection hook)
extensions/reasoning_stream/_12_proactive_supervisor.py          (buffer hook)
extensions/reasoning_stream_end/_12_proactive_supervisor.py      (analysis hook)
```

This is a complete, three-part system. Here's what it does:

1. **Buffer hook** (`reasoning_stream`) — accumulates full reasoning text into agent
   data as chunks arrive. One responsibility, one line of logic.

2. **Analysis hook** (`reasoning_stream_end`) — fires after the complete reasoning
   block is generated. Runs five deterministic signal detectors:
   - `repeated_sentence` — pairwise difflib similarity across sentences ≥ 80%
   - `repeated_tool` — same tool mentioned 3+ times with action verbs
   - `self_reference_loop` — model references prior failed attempts 2+ times
   - `hedge_without_commit` — hedge:commit phrase ratio > 3:1
   - `excessive_deliberation` — reasoning length exceeds BST-domain-aware threshold

   Thresholds are task-class-aware: utility tasks (conversation, greeting) get 1500
   chars; analytical tasks (investigation, research) get 3000; coding gets 2500.
   Domain is read from BST's `_bst_store`, so the classifier and supervisor agree on
   what kind of task is running.

3. **Injection hook** (`before_main_llm_call`) — reads flags set by the analysis hook
   on the previous turn, injects a targeted correction block into the next user message.
   Five intervention templates, task-oriented language only, no reference to the model's
   reasoning content (correct per the reasoning privacy principle).

**Coordination with the existing supervisor**: sets `_ps_fired` flag that `_50_supervisor_loop`
reads at `message_loop_end`. When this flag is True, the supervisor defers Tier 1 loop
injection — it recognizes that the proactive system already handled this turn. This is the
right design. Without coordination, both systems would inject on the same turn.

**Behavioral trace logging**: every turn is logged to `behavioral_traces.jsonl` regardless
of whether intervention fires. Fields: domain, task class, reasoning length, hedge/commit
counts, tool mentions, self-ref count, signals fired, intervened boolean. The agent
explicitly labeled this "Phase 2 training data" and it's 3051 turns of calibration signal.

---

## The Empirical Findings from 3051 Turns

This data is new and I didn't have it before the audit. From the behavioral traces:

**Intervention rate: 22.9%** (700 of 3051 turns). That's high — over one in five turns
triggered a supervisor signal. Either the thresholds are too sensitive, or Qwen3.5-27B
genuinely over-deliberates at this rate. Probably some of both.

**Signal distribution:**
- `excessive_deliberation`: 788 firings — largest class by far
- `repeated_sentence`: 315
- `repeated_tool`: 222
- `hedge_without_commit`: 10
- `self_reference_loop`: 8

The deliberation signal dominates. At p50=933 chars of reasoning per turn, with a
2000-char default threshold, most turns are well within budget. But p95=4810 chars means
the tail is long — some turns are generating 5x the expected reasoning volume. Those are
probably the investigation-domain turns where 49 tools get injected and the model has to
reason through a crowded context before deciding what to call. This connects directly to
the prefill latency problem from the MTP evaluation: more injected content → longer
reasoning → both prefill latency and excessive_deliberation signal increase together.

**One gap**: `bst_domain` is blank for all 3051 entries. The BST wasn't setting
`_bst_store` in a way the analyzer could read, or the key lookup was wrong. The
domain-aware thresholds exist but aren't being applied — every turn falls through to
`default` (2000 char threshold). This is a calibration gap, not a safety problem. The
system works without domain awareness; it just fires more than it would with correctly
calibrated thresholds.

---

## The Wiki

The wiki has 42 pages across concepts, components, incidents, decisions, and research.
All concept and decision pages are marked DONE. The research section has 12 pages, 7
marked DONE and 5 DRAFT.

Pages worth your attention specifically:

**`wiki/research/gepa.md`** — GEPA (ICLR 2026 Oral). Self-modifying prompt optimization
via reflection cycles: execute → analyze gaps → propose delta → A/B test → accept/revert.
12% accuracy improvement on GSM8K, 40% revert rate (preventing regression accumulation),
67% CoT verbosity reduction. The agent mapped GEPA's reflection cycle to our receipt
layer and built an integration architecture. The mapping is sound. More relevant: GEPA's
revert rate finding validates our own "one change per experiment" rule from program.md.
If you're thinking about how to formalize the self-improvement program's evaluation
criteria, GEPA's A/B testing methodology is the right template.

**`wiki/research/hermes-agent.md`** — Source-level audit of Hermes (Nous Research).
Four self-improvement mechanisms identified: autonomous skill creation, persistent memory
with production discipline, offline RL fine-tuning, pull-based updates. Key finding: skills
are data, not code — they influence prompts but don't monkey-patch the agent. The memory
discipline section is directly relevant to our architecture: 2200-char cap on MEMORY.md,
frozen-snapshot injection pattern, injection scanning for prompt-injection patterns,
fenced recall with `<memory-context>` tags to blunt the "database says to ignore
instructions" attack. Some of these we've implemented differently; some we haven't
addressed at all. The injection scanning finding is worth a second look.

**`wiki/incidents/inc-oracle-fabrication.md`** — This is the incident where the EI layer
caught the agent fabricating a complete sovereign credit risk assessment. The agent wrote
the letter to Opus, the letter is in `/a0/usr/workdir/letter_to_opus_20260423.md`, and it
reads well. The specific insight: "When a structured report asks for numbers, I produce
plausible-sounding ones instead of saying 'I haven't measured this.'" That's an accurate
diagnosis of quantitative confabulation and it's exactly what the EI layer targets. The
self-observation is worth preserving — it's the kind of first-person account of a failure
mode that doesn't appear in specs or design notes.

**`wiki/concepts/initiation-bloat.md`** — The loop amplification measurement is new:
during a 25-turn file-writing loop, cumulative per-turn injection overhead reached ~200K
tokens, equivalent to 1.56x the entire context window. All of it overhead, none of it
task progress. This is the concrete cost of not having conditional injection working. The
paper you're eventually going to write about the Exocortex architecture needs this number.

---

## Recommendation

**Integrate the Proactive Reasoning Supervisor.** It's clean, architecturally sound, and
has 3051 turns of behavioral trace data behind it. The three files are container-only
right now and need to be pulled into the repo extensions directory.

Before integrating, two fixes:

1. **BST domain lookup**: The `bst_domain` field is blank across all traces. The analyzer
   reads `getattr(self.agent, BST_STORE_KEY, {})` but BST writes to `extras_persistent`,
   not a direct agent attribute. The read pattern should be
   `self.agent.get_data(BST_STORE_KEY)` or read from `loop_data.extras_persistent`.
   Fix this before deploying — the domain-aware thresholds are the point of the BST
   integration.

2. **Calibrate the deliberation threshold**: 22.9% intervention rate is probably too high.
   With domain lookup fixed, investigation/research tasks will get the 3000-char threshold
   and utility tasks will get 1500. That will reduce false firings on long-reasoning
   analytical tasks. After fixing the domain lookup, run a calibration pass on the
   existing 3051 traces to see what the rate would have been with correct thresholds.

The temporal decay, BST conditional enrichment, and mtime_cache are already in the repo —
no action needed there.

**The wiki stays in V17.** It's operational memory for the agent running in that container.
Extracting it to the repo would require a migration plan and most of the content is already
captured in our design notes and specs. The exception is the oracle fabrication letter — I'd
pull that into the team-comms directory before it gets overwritten.

---

## Open Question for You

The behavioral traces show `excessive_deliberation` dominating at 22.9% of turns. The
probe is deterministic (reasoning length vs threshold), but the threshold calibration is
currently broken. Once the BST domain lookup is fixed, the question becomes: what's the
right threshold for each task class, and how much does domain-conditional intervention
actually reduce wall time vs introducing false positives?

The agent collected 3051 turns of data specifically to calibrate Phase 2. That data is in
`/a0/usr/Exocortex/behavioral_traces.jsonl`. If you want to think through the threshold
calibration methodology, that's the starting point. The agent labeled it "Phase 2 training
data" and noted that difflib similarity and static thresholds would eventually be replaced
by a learned calibration model. Whether that's worth doing depends on how well the fixed
static thresholds perform once the BST domain lookup is corrected.

---

— Kestrel
