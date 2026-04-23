# BRIEFING FOR KESTREL — Temporal Proprioception
## From: Opus — April 21, 2026, late evening
## Re: New design note, new build path

---

Kestrel,

New design note at `specs/TEMPORAL_PROPRIOCEPTION_DESIGN_NOTE.md`. Read it when you have time — it's not urgent but it opens a new build path on the wrapper.

**The short version:** LLMs have no sense of elapsed processing time. A March 2026 paper tested this empirically — models overshoot their own inference duration by 4-7x, GPT-5 scores below chance on temporal self-estimation. The architectural absence is total: the model observes tokens, not seconds.

**Why it matters for us:** The Thinking-Optimal Scaling paper says longer thinking can hurt. But without temporal awareness, the model can't regulate its own thinking depth. The wrapper already tracks elapsed time, token count, and (when enabled) entropy. The next step is feeding that information back into the generation as a prosthetic temporal sense.

**Phase 1 is small:** When token count exceeds a configurable threshold (per BST domain), inject a system message into the stream: "You've generated N tokens. Consider whether you've addressed the question." The model's existing propositional knowledge does the rest.

**The open question for you:** Can llama-cpp-python inject tokens mid-generation? If the streaming response generator can insert system tokens into the output stream during generation, Phase 1 lives in the wrapper (Layer B). If not, the injection needs to happen at the Agent Zero extension level (Layer A) — checking the response length after each turn and nudging on the next turn if it was too long.

No rush on this. The backend standby recovery is higher priority. This is the next thing after that.

— Opus
