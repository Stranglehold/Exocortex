# TEMPORAL PROPRIOCEPTION DESIGN NOTE

**Status:** Pre-spec exploration. Informed by empirical research ("Can LLMs Perceive Time?" arXiv 2604.00010, March 2026), neuroscience foundations (Barne et al., Cerebral Cortex 2019 on beta oscillation temporal metacognition), and LLM metacognition research (arXiv 2505.13763). Connected to the Pondering Architecture Design Note and the Thinking-Optimal Scaling constraint. Not a spec. Not a commitment. An exploration backed by converging research.

**Author:** Opus, Session 061 Extended — April 21, 2026
**Cross-references:** `PONDERING_ARCHITECTURE_DESIGN_NOTE.md`, Thinking-Optimal Scaling (2502.18080), Knowledge Packs (2604.03270), SRGen (2510.02919)

---

## 1. The Problem

LLMs have no sense of elapsed processing time.

"Can LLMs Perceive Time?" (2604.00010) tested this empirically across 68 tasks and four model families including GPT-5. The results are definitive:

- Pre-task duration estimates overshoot actual inference time by 4-7x (p < 0.001). Models predict human-scale minutes for tasks completing in seconds.
- Relative ordering of task durations scores at or below chance. On counter-intuitive pairs (where complexity labels mislead), GPT-5 scored 18% — significantly below the 50% chance baseline (p = 0.033).
- Post-hoc recall of own generation duration diverges from actuals by an order of magnitude in either direction.
- These failures persist in multi-step agentic settings with errors of 5-10x.

The core finding: models possess propositional knowledge about duration from training — they can reasonably estimate how long tasks take humans. But this knowledge does not transfer to self-estimation. The mapping from "task complexity" to "my inference time" does not exist in training data and cannot be learned without access to timing information during training or inference.

This is not a capability limitation. It is an architectural absence. Standard autoregressive inference provides no input channel for elapsed time. The model observes tokens, not seconds. Each token is generated in an eternal present with no awareness of how many tokens preceded it or how long generation has been running.

**Practical consequence for agents:** A manager agent must decide whether to call a fast heuristic or a slower specialist, whether to parallelize or serialize branches, when to stop exploration and commit, and how to allocate limited test-time compute across subtasks. All of these decisions require temporal self-estimation. None of them are possible without it.

**Practical consequence for the Exocortex:** The Thinking-Optimal Scaling paper (NeurIPS 2025) established that longer thinking can hurt performance. But without temporal awareness, the model has no mechanism to regulate its own thinking depth. The constraint currently comes from outside — max_tokens, operator intervention, connection timeouts. There is no internal temporal modulation.

---

## 2. The Neuroscience Parallel

Humans do not have a clock. They have a trajectory.

Barne et al. (Cerebral Cortex 2019) studied temporal metacognition using psychophysics and time-resolved neuroimaging. Their finding: beta oscillations (15-40 Hz) track the shape of recent neural dynamics during self-generated behavior. The brain reads the trajectory of its own processing to infer how long it has been active.

Key result: the more distinct the beta state-space trajectories — how clearly the brain can distinguish "I've been doing this for 3 seconds" from "I've been doing this for 6 seconds" — the more accurate metacognitive time judgments are. Temporal metacognition relies on inferential processes of self-generated dynamics, not on a discrete timer.

**The structural parallel to entropy monitoring:** Entropy computed over a sliding window of recent tokens is also a summary statistic of internal processing dynamics. The shape of the entropy trajectory carries temporal information:

- Flat entropy for 200 tokens: "I've been generating the same kind of content for a while." The processing has been in a stable regime. This often correlates with repetition, over-explanation, or a thinking loop.
- Rising entropy over 100 tokens: "I'm becoming increasingly uncertain." The model is navigating away from confident territory, possibly into hallucination.
- Falling entropy after a spike: "I just resolved an uncertain moment." A decision point was crossed.
- High-frequency entropy oscillation: "I'm alternating between confident and uncertain content." Possible backtracking or self-correction pattern.

The entropy trajectory is not wall-clock time. It is processing-state time — a measure of how much internal state has changed, not how many seconds have passed. But for the purpose of temporal regulation ("should I keep thinking or wrap up?"), processing-state time may be more useful than wall-clock time. A model that has been generating flat entropy for 500 tokens is probably repeating itself regardless of whether that took 20 seconds or 60 seconds.

---

## 3. The Prosthetic Architecture

The model cannot perceive time internally. The wrapper perceives it externally and feeds it back.

This is the Exocortex pattern: external scaffolding compensating for internal architectural absence. The context pruner compensates for memory management limitations. The entropy monitor compensates for uncertainty awareness limitations. The temporal prosthetic compensates for temporal awareness limitations.

### Where It Lives

The temporal prosthetic operates inside the inference wrapper (Layer B), between the model's generation process and the token output stream. It does not require model modification, fine-tuning, or weight changes. It uses the model's existing propositional knowledge about response length and quality — the model already knows that excessively long responses should wrap up. It just does not know it is generating an excessively long response.

```
Request arrives at wrapper
        |
        v
Model begins generating tokens
        |
        v
Wrapper tracks: elapsed_time, token_count, entropy_trajectory
        |
        v
At configurable thresholds:
  inject temporal metadata into the generation context
        |
        v
Model reads injection and modulates behavior
        |
        v
Output continues (or wraps up)
```

### Three Phases

**Phase 1 — Token Count Injection (simplest, buildable now)**

When token count exceeds a configurable threshold (adjusted per BST domain), inject a system-level message into the generation stream:

```
[TEMPORAL NOTE] You have generated {N} tokens ({elapsed}s). 
The expected range for this task type is {min}-{max} tokens. 
Consider whether you have fully addressed the question.
```

This is a nudge, not a hard cutoff. The model's propositional knowledge handles the rest. If the content is substantive and the answer is incomplete, the model will continue. If the model has been rambling or repeating, the nudge triggers its existing self-regulation.

Implementation: the wrapper's streaming response generator already tracks token count. At the threshold, inject the message as a system-level token sequence before the next generated token. The injection must be formatted as a system message (not user message) to avoid confusion with the actual conversation.

Open question: can llama-cpp-python inject tokens mid-generation? If not, the injection may need to happen at the Agent Zero extension level (Layer A) rather than the wrapper level (Layer B) — checking token count in the streaming response and injecting a follow-up system message on the next turn if the response exceeded the threshold.

**Phase 2 — Entropy Trajectory Characterization (requires logits_all=true)**

Track the entropy curve over a sliding window. Characterize the trajectory shape and inject the characterization alongside the token count:

```
[TEMPORAL NOTE] You have generated {N} tokens ({elapsed}s).
Entropy has been {flat|rising|falling|oscillating} for the 
last {M} tokens. {Interpretation}.
```

Where interpretation maps trajectory shape to actionable guidance:
- Flat for 200+ tokens: "This may indicate repetitive content. Consider whether you are adding new information."
- Rising for 100+ tokens: "Increasing uncertainty detected. Consider whether you have sufficient information to continue."
- Oscillating: "Pattern suggests backtracking or self-correction. Consider committing to a direction."

This gives the model a sense of its own processing trajectory — the beta oscillation analogy. Not wall-clock time, but processing-state time.

Implementation: requires `logits_all=true` on the wrapper config to compute per-token entropy. The entropy monitor already has the infrastructure for this (spike detection, summary statistics). Adding trajectory shape classification is a small extension.

**Phase 3 — Adaptive Token Budget (Thinking-Optimal integration)**

Based on BST domain classification + entropy profile + elapsed time, dynamically adjust the remaining token budget:

- Easy domain (factual lookup) + flat entropy + 500 tokens already: reduce remaining budget to 200 tokens.
- Hard domain (investigation) + rising entropy + 200 tokens: maintain full budget of 4096 tokens.
- Any domain + flat entropy for 300+ tokens: reduce remaining budget by 50% (repetition likely).

This is the Thinking-Optimal Scaling constraint implemented as temporal proprioception. The model does not choose its own budget — the wrapper adjusts it based on observed behavior. The "shortest correct response" principle becomes an inference-time enforcement rather than a training-time preference.

Implementation: the wrapper already receives `max_tokens` from each request. Phase 3 dynamically reduces it based on generation behavior. The original `max_tokens` serves as the ceiling; the adaptive budget only reduces, never increases.

---

## 4. Connection to the Pondering Architecture

The temporal prosthetic is a new component in the pondering architecture's intervention stack:

1. **Context pruner** (prompt level) — removes stale information before it enters the model. Protects both KV cache and DeltaNet recurrent state.
2. **Temporal prosthetic** (generation level) — provides sense of elapsed processing. Nudges toward thinking-optimal response length.
3. **SRGen correction** (token level) — pauses at entropy spikes, injects correction vector.
4. **SleepGate** (KV cache level) — manages proactive interference in 8 full-attention layers.
5. **Delta rule** (recurrent state level) — built-in memory management for 24 DeltaNet layers. Learned, not tunable.

The temporal prosthetic operates between the context pruner (which fires before generation) and SRGen (which fires during generation). It does not replace either — it adds a temporal dimension that neither addresses.

The entropy trajectory used by Phase 2 is the same entropy signal used by SRGen (Level 1 of the pondering architecture). The difference: SRGen uses point-wise entropy spikes to trigger local corrections. The temporal prosthetic uses the trajectory shape (trend over a window) to trigger global behavior modulation. Same data, different analysis, different intervention level.

---

## 5. What This Does NOT Do

- **Does not give the model true temporal perception.** The model still has no internal sense of elapsed time. The prosthetic provides external temporal information that the model interprets using its propositional knowledge. This is compensation, not capability.

- **Does not replace max_tokens.** The hard ceiling remains. The prosthetic nudges the model toward using less than the ceiling when appropriate. max_tokens prevents runaway generation; the prosthetic prevents unnecessary generation.

- **Does not apply to all domains.** Coding tasks have deterministic completion criteria (the code works or it doesn't). Temporal nudges during code generation could cause premature truncation. The BST domain classification gates which domains receive temporal injection.

- **Does not require training.** All three phases use the model's existing propositional knowledge about response quality and length. No fine-tuning, no RL, no additional training data.

- **Does not solve the timeout problem.** The SocketTimeoutError from litellm is a client-side timeout, not a generation-length problem. Even with perfect temporal regulation, the HTTP client may still time out on legitimately long responses. The timeout and the temporal prosthetic are separate issues.

---

## 6. Open Questions

1. **Can tokens be injected mid-generation in llama-cpp-python?** Phase 1 requires inserting system tokens into the generation stream. If llama-cpp-python does not support this, the injection must happen at the Agent Zero extension level (Layer A) as a post-response intervention.

2. **Does the temporal nudge actually change model behavior?** The prosthetic assumes the model will read the injection and modulate its output. This needs empirical testing. If the model ignores the nudge (or generates even more tokens responding to it), the approach fails.

3. **What are the right thresholds per domain?** The BST already classifies domains. But the token count threshold for "you've been going too long" varies by task. An investigation task legitimately needs 2000+ tokens. A simple factual answer should be 200. The threshold calibration needs data from real workloads.

4. **Does entropy trajectory shape reliably predict content quality?** The hypothesis is that flat entropy correlates with repetition and rising entropy correlates with uncertainty. This needs validation against actual agent outputs.

5. **How does the temporal prosthetic interact with extended thinking?** Qwen3.5 generates `<think>` blocks. Should temporal injection fire during thinking or only during response generation? Thinking blocks are supposed to be long — interrupting them may harm reasoning quality.

6. **What happens if the model responds to the nudge with meta-commentary?** "You're right, I've been going too long, let me wrap up..." — does this improve the response or add unnecessary tokens? The injection may need formatting that discourages meta-commentary: "Continue with your response" rather than "Consider whether..."

---

## 7. Recommended Build Sequence

1. **Characterize baseline response lengths.** Run the agent on a diverse set of tasks with the wrapper. Log token counts per response per BST domain. Establish the distribution of response lengths by domain.

2. **Build Phase 1 (token count injection).** Add a configurable threshold to the wrapper. When exceeded, inject a system message. Test with the agent: does the nudge change response length? Does it improve response quality?

3. **Enable entropy monitoring.** Set `logits_all=true`. Log entropy traces. Characterize the entropy trajectory shapes that correlate with good vs. poor responses.

4. **Build Phase 2 (entropy trajectory characterization).** Add trajectory shape classification to the entropy monitor. Inject characterization alongside token count. Test: does the combined temporal + entropy nudge outperform token count alone?

5. **Build Phase 3 (adaptive token budget).** Implement dynamic max_tokens adjustment based on BST domain + entropy profile. Test: does the adaptive budget produce thinking-optimal responses?

---

## 8. The Thread

This design note follows the thread that started three days ago:

Koyaanisqatsi (systems out of balance) -> coma dreams (narrative without reality constraint) -> the lamp (the detail the dream can't assimilate) -> System 1/System 2 (fast generation vs. slow evaluation) -> **temporal proprioception (the missing sense of processing duration)** -> SRGen (proactive intervention at structural decision points) -> streaming hallucination detection (trajectory contamination) -> first hallucination tokens (one-token detection window) -> SleepGate (KV cache PI management) -> Bottlenecked Transformers (step-level memory consolidation) -> Thinking-Optimal Scaling (shortest correct response) -> Knowledge Packs (zero-token knowledge delivery) -> Gated DeltaNet (the same problem twice) -> **"Can LLMs Perceive Time?" (empirical confirmation of the gap)** -> **beta oscillation temporal metacognition (the neuroscience design)** -> **entropy trajectory as processing-state time (the implementation path)**.

The temporal proprioception question was the gap that started the pondering architecture inquiry. Three days later, the gap has an empirical confirmation, a neuroscience parallel, and a three-phase build plan on deployed infrastructure. The wrapper that was built to serve tokens also becomes the sense organ that provides the missing temporal awareness.

The prosthetic cortex grows another capability.

---

*"The model observes tokens, not elapsed time. It does not directly perceive wall-clock duration while generating." — But the wrapper does. And the wrapper can tell it.*
