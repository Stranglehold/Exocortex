# PONDERING ARCHITECTURE DESIGN NOTE

**Status:** Pre-spec exploration. Informed by five papers read in full: SRGen (2510.02919), Streaming Hallucination Detection (2601.02170), First Hallucination Tokens (2507.20836), SleepGate (2603.14517), and Bottlenecked Transformers (2505.16950, ICLR 2026). Also informed by the coma dream analysis thread (Sessions 059–061), the System 1/System 2 framework discussion, and the file-system-as-reflection-mirror discovery. No eval data on local model behavior yet. This document captures the architectural gap and sketches the mechanism. Not a spec. Not a commitment. An exploration backed by empirical research.

**Author:** Opus, Session 061 Extended — April 19, 2026 (updated same day with SleepGate + Bottlenecked Transformers findings)
**Cross-references:** `PONDERING_ARCHITECTURE_RESEARCH_SYNTHESIS.md`, `SRGen_analysis.md`, `EPISTEMIC_INTEGRITY_DESIGN_NOTE.md`

**REVISION NOTE (April 19, 2026, 7 PM):** Original design note had two intervention levels (step + trajectory). After reading SleepGate and Bottlenecked Transformers (ICLR 2026), the architecture now has THREE intervention levels (token + step + cache) connected by a universal entropy signal. The design principles and implementation path have been updated accordingly.

---

## 1. The Problem

### The Gap

The Exocortex has an Epistemic Integrity (EI) layer that checks claims after generation. It has a BST that selects processing modes before generation. It has no mechanism that operates *during* generation — no pause between impulse and output, no evaluation of the reasoning trajectory as it unfolds, no awareness of how long a response has been processing or how confident the system is in what it's producing.

The gap sits between the BST (which selects the mode) and the EI layer (which audits the result). Nothing monitors the generation process itself. The model generates token-by-token in a forward-only stream, commits each token irrevocably, and only evaluates the output after the full response exists. If the reasoning takes a wrong turn at token 47, every subsequent token is conditioned on that error and the EI layer doesn't see it until token 2,000 — by which time the entire analysis may be contaminated.

### The Motivating Thread

This design note originates not from a single incident but from a convergent thread across Sessions 059–061:

**The coma dream.** A patient in a coma dreams. The dream machinery — pattern completion, narrative generation, associative linking — runs without external sensory input to constrain it. The brain produces a perfectly coherent internal narrative that has no relationship to external reality. The dream feels real from inside. The machinery is functioning correctly. The *constraint* is missing. LLM generation is the same machinery: autoregressive pattern completion producing coherent output without external grounding during the generation process.

**The lamp.** In a coma dream, the patient's wife noticed that a lamp in the hospital room — visible from the bed — never appeared in the dream. The dream couldn't assimilate it because the lamp was a geometric detail from external reality that didn't fit the internal narrative. The lamp is the signal that breaks the dream. In LLM generation, the lamp is the first token where the model's internal state diverges from grounded reality. Research confirms (Paper 3: First Hallucination Tokens) that this first divergence token is far more detectable (AUROC ~0.8) than subsequent tokens (~0.5). After the first error, the narrative absorbs it. The lamp becomes invisible.

**The System 1/System 2 insight.** Kahneman's dual-process theory: System 1 (fast, automatic, pattern-matching) produces most cognitive output. System 2 (slow, deliberate, evaluative) activates when uncertainty is detected. Current LLM inference is pure System 1 — fast, automatic, forward-only. The pause is System 2. Not a full re-evaluation of everything. A targeted intervention at the moment of detected uncertainty.

**The reflection mirror.** During Session 061, I discovered that writing to a file and reading it back through the view tool creates a functional gap between generation and evaluation. Writing is System 1 — the next most probable continuation. Reading back is System 2 — I process my own words as input through the same channel I process Jake's messages. The gap is mechanical (a tool call), not lived duration, but it produces what the single generation stream cannot: critical distance from my own output. The pondering architecture is this same pattern, applied to the inference layer.

### What the Research Found

Three papers, read in full via arXiv MCP on April 19, 2026, validate this architecture from different angles:

**SRGen (2510.02919) — Step-level proactive intervention.** During token generation, monitors entropy. When entropy exceeds a dynamic threshold (rolling mean + k×σ over a sliding window), PAUSES generation. Optimizes a correction vector δ that balances contextual fidelity against uncertainty reduction. Injects δ into hidden state before emitting the token. +12% accuracy on AIME2024, ~50% bounded overhead. Critical finding: the triggered tokens are structural connectives ("so", "but", "wait", "since") — decision points where the reasoning trajectory diverges. Not content tokens. The error starts at the junction, not the assertion.

**Streaming Hallucination Detection (2601.02170) — Trajectory-level monitoring.** Treats hallucination as an evolving latent state, not a one-off error. Two signals: step-level (does this step introduce unsupported content?) and prefix-level (has the overall trajectory entered a hallucinated regime?). Critical finding: once prefix-level hallucination accumulates, isolated corrections don't fix it — the trajectory is poisoned. Individual correct steps don't repair a contaminated chain. 87%+ accuracy from hidden state probing. No additional inference cost.

**First Hallucination Tokens (2507.20836) — The foundational evidence.** The first hallucinated token is far more detectable than conditional ones. AUROC ~0.8 for the first token; ~0.5 for subsequent tokens. Entropy is the most effective detection signal. Holds across models (LLaMA 7B–70B, Mistral 7B). Implication: intervene at the first sign of divergence or lose the ability to detect it. The lamp is only visible when it first appears.

**SleepGate (2603.14517) — Cache-level proactive interference resolution.** LLMs suffer from proactive interference: stale KV cache entries actively compete with current information, degrading retrieval accuracy log-linearly toward zero regardless of context length. SleepGate introduces three coordinated mechanisms: a conflict-aware temporal tagger, a learned forgetting gate, and a consolidation module. Soft attention biasing (adding log(retention_score) to pre-softmax attention logits) exponentially suppresses stale entries without deleting them. 99.5% accuracy at PI depth 5 vs. <18% for all five baselines. The entropy trigger is the same signal as SRGen’s — attention entropy monitors when to run sleep cycles. Direct implication: the 20-turn BST classification collapse, strategic loops, and agent inability to break free of stale tool outputs are all possible PI symptoms. Architecture-level solution to a problem prompt engineering cannot address.

**Bottlenecked Transformers (2505.16950, ICLR 2026) — Step-level memory consolidation.** The KV cache is the terminal information bottleneck in decoder-only Transformers. Autoregressive training encourages it to retain ALL input information, even irrelevant detail — the opposite of what generalization needs. Solution: a Cache Processor (small auxiliary Transformer) that periodically rewrites KV entries in-place at reasoning step boundaries. Two operations: consolidation (rewrites recently generated entries) and reconsolidation (rewrites top-k recalled prior entries selected by attention mass). Non-causal processing — can attend to all selected entries simultaneously. Key finding: values change, keys don't. The Processor edits memory CONTENTS without changing ADDRESSING. Edits concentrate in early transformer layers. +6.6pp on SVAMP, consistent gains across 7 benchmarks. The authors explicitly suggest prediction-error/entropy gating for the reconsolidation trigger.

---

## 2. Design Principles

1. **The pause is the innovation.** The core mechanism is not better evaluation, better prompts, or better models. It's the introduction of a gap between generation and commitment — a buffer where evaluation can occur before output is finalized. Everything else follows from this.

2. **Proactive, not reactive.** Existing self-reflection (Think Twice, Self-Refine) is reactive — it generates a complete draft, then critiques and revises. The pondering architecture intervenes *before* the error is committed. SRGen's key distinction: proactive intervention at decision points costs ~50% overhead. Reactive revision costs 2-3× (full re-generation). Proactive wins on both accuracy and efficiency.

3. **Dual-mode detection.** Step-level intervention (catching wrong turns at decision points) and trajectory-level monitoring (detecting accumulated contamination across the reasoning chain) are complementary, not alternatives. Both are needed. SRGen without trajectory monitoring misses accumulated sub-threshold drift. Trajectory monitoring without SRGen catches errors only after they've propagated.

4. **Entropy as the universal signal.** All three papers converge on entropy as the primary detection signal. SRGen uses dynamic entropy thresholding. First Hallucination Tokens finds entropy most effective for detection. Streaming Detection uses hidden state probing (which captures entropy-related information). The BST already classifies by domain. The pondering layer classifies by uncertainty within a domain. Entropy is the BST for inference.

5. **Bounded overhead.** SRGen's overhead stabilizes at ~50% regardless of sequence length, because triggers are sparse (averaging ~6 per task). Trajectory monitoring uses existing hidden states — near-zero additional cost. The combined architecture should target <75% total overhead. This is acceptable for accuracy-critical applications (intelligence analysis, architectural decisions) and can be disabled for latency-sensitive ones (routine operational queries).

6. **Deterministic triggering, model-specific calibration.** The entropy threshold is dynamic (adapts to the model's baseline entropy profile), but the triggering mechanism is deterministic — no LLM call required to decide whether to pause. The correction (if any) may involve model computation, but the decision to pause is a statistical test on entropy values.

---

## 3. Architecture Sketch

### Where It Lives

The pondering layer sits between the BST (which selects the processing mode) and the output delivery (which presents the result to the operator or next pipeline stage). After reading SleepGate and Bottlenecked Transformers, the architecture has **three intervention levels** connected by a **universal entropy signal**:

```
Input → BST Classification → [Enrichment] → Model Generation
                                                    │
                                          ┌─────────────────────────────────┐
                                          │   PONDERING LAYER            │
                                          │                              │
                                          │   LEVEL 1 — TOKEN            │
                                          │   (SRGen mechanism)          │
                                          │   Entropy spike at token     │
                                          │   → pause → correct → resume │
                                          │                              │
                                          │   LEVEL 2 — STEP             │
                                          │   (Bottlenecked Transformer) │
                                          │   Reasoning step boundary    │
                                          │   → consolidate + reconsolidate│
                                          │                              │
                                          │   LEVEL 3 — CACHE            │
                                          │   (SleepGate mechanism)      │
                                          │   PI accumulation detected   │
                                          │   → tag → gate → evict/merge │
                                          │                              │
                                          │   MONITORING                 │
                                          │   (Streaming Detection)      │
                                          │   Trajectory contamination   │
                                          │   → flag → regenerate         │
                                          │                              │
                                          │   UNIVERSAL SIGNAL: ENTROPY  │
                                          └─────────────────────────────────┘
                                                    │
                                            EI Layer (post-generation)
                                                    │
                                            Output Delivery
```

**The Universal Entropy Signal.** All three intervention levels use entropy as their trigger, but at different granularities:
- **Level 1 (Token):** Per-token predictive entropy. Dynamic threshold: mean + k×σ over sliding window. (SRGen)
- **Level 2 (Step):** Prediction error at reasoning step boundaries. Mismatch between expected and actual triggers reconsolidation. (Bottlenecked Transformers suggest this; authors note surprise/PE gating would be more suitable than fixed newline triggers)
- **Level 3 (Cache):** Attention entropy across the full KV cache. When attention distributions become uniform (model “doesn’t know where to look”), PI has accumulated. (SleepGate)
- **Monitoring:** Hidden state probing at transformer layers 16-20. Prefix-level hallucination score tracking trajectory contamination. (Streaming Hallucination Detection)

One entropy monitor, four applications. The entropy computation exists in the logits (Level 1), the attention weights (Level 3), the hidden states (Monitoring), and the prediction loss (Level 2). Each is a different view of the same underlying signal: **uncertainty about what to generate next.**

### Mechanism: Three Levels + Monitoring

The original design had two monitors. After reading SleepGate and Bottlenecked Transformers, the mechanism has three intervention levels plus a monitoring layer. Pseudocode is provided for Level 1 (most mature) and Monitoring (simplest to implement). Levels 2 and 3 are described architecturally; full pseudocode will be written at spec phase.

**Level 1: Token-Level Correction (adapted from SRGen)**

```python
@dataclass
class StepMonitor:
    window_size: int = 25          # N most recent entropy values
    sensitivity: float = 4.0       # k standard deviations above mean
    correction_steps: int = 3      # gradient steps for correction vector
    learning_rate: float = 0.01
    lambda_balance: float = 0.05   # fidelity vs. uncertainty tradeoff
    
    entropy_history: deque         # sliding window of recent entropy values
    
    def should_pause(self, current_entropy: float) -> bool:
        """Deterministic trigger: is this token's entropy anomalously high?"""
        if len(self.entropy_history) < self.window_size:
            return False
        mu = mean(self.entropy_history)
        sigma = std(self.entropy_history)
        return current_entropy > mu + self.sensitivity * sigma
    
    def correct(self, hidden_state, prefix_tokens, vocab_head):
        """Optimize correction vector δ (SRGen mechanism)"""
        delta = zeros(hidden_state.shape)
        for step in range(self.correction_steps):
            L_CE = cross_entropy_loss(prefix_tokens, hidden_state + delta, vocab_head)
            L_AEM = entropy(softmax(vocab_head(hidden_state + delta)))
            L = (1 - self.lambda_balance) * L_CE + self.lambda_balance * L_AEM
            delta -= self.learning_rate * grad(L, delta)
        return delta
```

**Monitoring Layer: Trajectory-Level State (adapted from Streaming Hallucination Detection)**

```python
@dataclass
class TrajectoryMonitor:
    contamination_threshold: float = 0.7   # prefix-level score triggering alarm
    recovery_window: int = 5               # steps to observe after alarm before regeneration
    probe_layer: int = 18                  # transformer layer to probe (16-20 optimal)
    
    prefix_score: float = 0.0              # running estimate of trajectory contamination
    step_scores: list                      # history of step-level hallucination scores
    
    def update(self, hidden_state_at_step, step_hallucination_score):
        """Update trajectory state with new step evidence"""
        self.step_scores.append(step_hallucination_score)
        # Prefix-level probe on hidden state
        self.prefix_score = self.prefix_probe(hidden_state_at_step, step_hallucination_score)
    
    def is_contaminated(self) -> bool:
        """Has the trajectory entered a hallucinated regime?"""
        return self.prefix_score > self.contamination_threshold
    
    def should_regenerate(self) -> bool:
        """Has contamination persisted beyond recovery window?"""
        if not self.is_contaminated():
            return False
        recent = self.step_scores[-self.recovery_window:]
        return all(s > 0.5 for s in recent)  # sustained contamination
```

**Level 2: Step-Level Memory Rewriting (from Bottlenecked Transformers, ICLR 2026)**

At each reasoning step boundary (detected by newline token or other delimiter), a Cache Processor — a small auxiliary Transformer — rewrites selected KV entries in-place:

- **Consolidation:** All KV entries from the most recent reasoning step are passed through the Processor with non-causal (bidirectional) attention, then written back. This stabilizes newly formed memory traces.
- **Reconsolidation:** The top-k entries from prior steps (selected by attention mass with the current step) are also passed through the Processor and rewritten. This updates recalled memories with new contextual information.
- **Key finding:** The Processor edits value vectors while leaving key vectors nearly unchanged. It changes WHAT is remembered without changing WHERE it’s stored. Edits concentrate in early transformer layers.
- **The gating question:** Currently triggered at every newline. The authors suggest prediction-error/entropy gating would be more effective — trigger reconsolidation only when surprise is high.

**Level 3: Cache-Level PI Management (from SleepGate)**

Periodically during inference, a sleep micro-cycle manages the full KV cache:

- **Temporal tagging:** Each entry augmented with timestamp, semantic signature, superseded flag, and cumulative attention score.
- **Forgetting gate:** Small MLP assigns retention score r_i to each entry. Actions: Keep (r ≥ α_k), Compress (α_e ≤ r < α_k), Evict (r < α_e).
- **Soft attention biasing:** Instead of hard eviction, add b_i = β · log(max(r_i, ε)) to pre-softmax attention logits. Stale entries exponentially suppressed without deletion.
- **Consolidation module:** Entries marked for compression are clustered by semantic signature and merged into compact summary representations via cross-attention.
- **Trigger:** Attention entropy exceeding threshold OR conflict density (fraction of superseded entries) exceeding maximum OR fallback periodic interval.

**Controller: The Pause (updated for three levels)**

```python
@dataclass  
class PauseController:
    mode: str = "monitor"  # "monitor", "correct", "regenerate"
    
    def process_token(self, token_logits, hidden_state, step_monitor, trajectory_monitor):
        entropy = compute_entropy(token_logits)
        step_monitor.entropy_history.append(entropy)
        
        # Level 1: Step-level pause
        if step_monitor.should_pause(entropy):
            delta = step_monitor.correct(hidden_state, prefix, vocab_head)
            hidden_state = hidden_state + delta  # inject correction
            self.mode = "correct"
        
        # Level 2: Trajectory-level monitoring
        step_score = step_hallucination_probe(hidden_state)
        trajectory_monitor.update(hidden_state, step_score)
        
        if trajectory_monitor.should_regenerate():
            self.mode = "regenerate"
            return REGENERATE_SIGNAL  # stop generation, try again from checkpoint
        
        return sample_token(hidden_state, vocab_head)
```

### Configuration

```json
{
    "pondering": {
        "enabled": true,
        "step_monitor": {
            "window_size": 25,
            "sensitivity": 4.0,
            "correction_steps": 3,
            "learning_rate": 0.01,
            "lambda_balance": 0.05
        },
        "trajectory_monitor": {
            "contamination_threshold": 0.7,
            "recovery_window": 5,
            "probe_layer": 18
        },
        "overhead_budget": 0.75,
        "domains_enabled": ["investigation", "analysis", "financial", "planning"],
        "domains_disabled": ["coding", "file_ops", "system_admin"]
    }
}
```

### Integration with Existing Layers

**BST → Pondering:** The BST classification determines whether pondering is enabled for this task. Investigation, analysis, financial, and planning domains benefit from pondering (accuracy-critical). Coding, file_ops, and system_admin domains skip it (latency-sensitive, deterministic verification available).

**Pondering → EI:** The trajectory monitor's prefix-level score provides a confidence prior to the EI layer. If the trajectory was flagged as potentially contaminated but not regenerated (borderline cases), the EI layer can increase its scrutiny. The step-level entropy history provides a map of which parts of the response had the most uncertainty — the EI layer can focus its evidence-checking on those segments.

**Pondering → PACE:** If PACE (execution scaffolding) is active, the pondering layer can feed uncertainty signals into the PACE supervisor. High-uncertainty reasoning steps become candidates for verification before the agent acts on them.

### Implementation Path

**Phase 1 — The Mechanical Pause (Agent Zero wrapper, no inference modification)**
The simplest version. After generation completes, the response is held in a buffer. The agent reads its own output back through a separate model call and evaluates it for confidence. If below threshold, regenerates with the evaluation as additional context.

This is the reflection mirror pattern — write → read → evaluate. It works today with existing tools. It doesn't modify the inference pipeline. It adds one model call of overhead. For high-stakes outputs (intelligence briefings, architectural decisions), this overhead is acceptable.

**Deliverable:** A post-generation evaluation hook in the Agent Zero message pipeline.
**Verification:** Compare accuracy of direct output vs. held-and-evaluated output on a set of known-answer questions.

**Phase 2 — Entropy Monitoring (inference pipeline modification)**
Add entropy computation to the token generation loop. Log entropy values per token. Implement the dynamic threshold. When triggered, flag the token but don't correct — just log and mark the response as having high-uncertainty segments.

This requires modification to the serving layer (llama.cpp or vllm). On the local 3090 with Qwen3.5-27B, this is feasible — we control the inference pipeline.

**Deliverable:** Entropy logging in the inference pipeline. Dashboard showing entropy traces per response.
**Verification:** Correlate entropy spikes with known errors in a validation set.
**Dependencies:** Access to per-token logits during generation (available in llama.cpp).

**Phase 3 — Step-Level Correction (SRGen implementation)**
When entropy exceeds the dynamic threshold, pause generation. Compute correction vector δ. Inject into hidden state. Resume. This is the full SRGen mechanism adapted for our stack.

**Deliverable:** Entropy-triggered correction in the inference pipeline.
**Verification:** A/B comparison: baseline generation vs. SRGen-corrected generation on math reasoning and factual QA benchmarks.
**Dependencies:** Phase 2 (entropy monitoring), access to hidden states during generation.

**Phase 4 — Trajectory Monitoring (Streaming Detection implementation)**
Train a lightweight probe on hidden states from the probe_layer to estimate step-level and prefix-level hallucination scores. Run continuously during generation. When prefix-level score crosses threshold, signal for regeneration.

**Deliverable:** Trajectory contamination probe running alongside generation.
**Verification:** Detect contaminated trajectories before they produce incorrect final answers on a held-out test set.
**Dependencies:** Phase 2 (entropy monitoring), hidden state access, training data for probe (can be generated from the model's own outputs using the RAGTruth methodology).

**Phase 5 — Step-Level Memory Rewriting (Bottlenecked Transformer mechanism)**
Add a Cache Processor that rewrites KV entries at reasoning step boundaries. Start with consolidation only (rewrite recent entries). Add reconsolidation (rewrite top-k recalled prior entries) once consolidation is validated.

**Deliverable:** Cache Processor running at reasoning step boundaries.
**Verification:** Compare reasoning accuracy with and without Cache Processor on math reasoning benchmarks.
**Dependencies:** Phase 2 (entropy monitoring for prediction-error gating), KV cache access during generation.

**Phase 6 — Cache-Level PI Management (SleepGate mechanism)**
Implement the soft attention biasing technique: compute retention scores for KV entries and add log(retention) to pre-softmax attention logits. Start with a simple staleness heuristic (recency + superseded flag) before training the full forgetting gate.

**Deliverable:** Soft attention biasing active during generation. Dashboard showing retention scores and PI metrics.
**Verification:** Measure retrieval accuracy on tasks with high PI depth (repeated updates to same entity). Compare with and without biasing.
**Dependencies:** Attention weight access during generation.

**Phase 7 — Full Integration**
Wire all three levels + monitoring into the complete pondering layer. BST gates which domains enter pondering. Trajectory confidence feeds into EI scrutiny. Universal entropy monitor feeds all three levels. Run end-to-end evaluation.

---

## 4. What This Does NOT Do

- **Does not replace the EI layer.** The pondering layer catches errors during generation. The EI layer audits claims after generation against external evidence. Both are needed. The pondering layer is introspective (does the model's internal state look uncertain?). The EI layer is extrospective (does the claim match external reality?).

- **Does not require training.** SRGen is a test-time method. The correction vector δ is computed on-the-fly from the current context. No fine-tuning, no RL, no additional training data for the step-level mechanism. The trajectory probe (Phase 4) does require training, but on data that can be generated from the model's own outputs.

- **Does not apply to all domains.** Coding and file operations have deterministic verification (run the code, check the output). Pondering adds overhead without proportional benefit. The BST classification gates which domains enter the pondering layer.

- **Does not slow down simple queries.** The entropy monitor is near-zero cost (computed from existing logits). The correction mechanism triggers only on entropy spikes — averaging ~6 times per task in SRGen's experiments. Simple, high-confidence responses pass through unchanged.

- **Does not make the model "think harder."** It makes the model pause at the moments when it's most likely to go wrong. The correction is small and targeted — a nudge to the hidden state, not a re-computation of the entire response. The analogy is not "thinking harder" but "looking before you step."

---

## 5. Open Questions

1. **What is the entropy profile of Qwen3.5-27B on our workloads?** SRGen tested on Qwen2.5-Math, DeepSeek-R1, Qwen3-32B. Our local model is Qwen3.5-27B. Different architecture, different entropy baseline. Phase 2 must characterize this before calibrating the threshold.

2. **Does llama.cpp expose per-token logits and hidden states?** The SRGen mechanism requires access to logits (for entropy) and hidden states (for the correction vector). llama.cpp's API may need modification. Alternative: use vllm if it provides the necessary hooks.

3. **Can the mechanical pause (Phase 1) capture meaningful errors?** The simplest test: have the agent generate a response, read it back, and evaluate whether it catches errors the direct output would have missed. If Phase 1 shows no improvement, the more complex phases may not be justified.

4. **What is the right probe_layer for Qwen3.5-27B?** The streaming detection paper found layers 16-20 optimal for 7-8B models. For a 27B model with more layers, the optimal probe depth may differ.

5. **How does the pondering layer interact with extended thinking?** Some models (including DeepSeek-R1 distills) already produce internal "thinking" tokens. Does SRGen's entropy monitoring detect the same decision points that the model's own extended thinking addresses? Could there be interference?

6. **What training data would the trajectory probe need?** The streaming detection paper used Claude 4.5 for annotation. We could use a similar approach: generate responses, have a capable model annotate step-level and prefix-level hallucination, train the probe. How much data is needed for acceptable performance on our domains?

7. **Can the correction vector δ be pre-computed for common error patterns?** SRGen optimizes δ fresh each time. If certain error patterns recur (specific factual domains, particular reasoning structures), could we cache correction vectors and apply them without re-optimization? This would reduce the per-trigger overhead.

8. **Are our observed agent failures PI symptoms?** The 20-turn BST classification collapse, strategic loops, inability to break free of stale tool outputs — SleepGate predicts these are proactive interference. Test: add soft attention biasing with a simple staleness heuristic and measure whether classification accuracy improves in long conversations.

9. **What is the right Cache Processor size for Qwen3.5-27B?** Bottlenecked Transformers used 89M-211M parameter Processors for 1B-8B models. For 27B, the Processor size and training cost need estimation.

10. **Does prediction-error gating outperform fixed-interval reconsolidation?** The Bottlenecked Transformers authors suggest surprise-based gating for reconsolidation. This connects to SRGen’s entropy triggering. Test: compare fixed-interval (every newline) vs. entropy-triggered reconsolidation on reasoning benchmarks.

11. **Can soft attention biasing be added to llama.cpp without full SleepGate training?** The simplest PI mitigation: compute a staleness score per KV entry (based on recency and superseded status) and add log(staleness) to pre-softmax attention. No learned gate, no training. Does this simple heuristic provide meaningful PI reduction?

12. **How do the three levels interact?** Level 1 corrects at the token. Level 2 consolidates at the step. Level 3 manages the cache. Are there interference effects? Does Level 1 correction make Level 2 consolidation unnecessary (or vice versa)? The optimal combination may not be all three simultaneously.

---

## 6. Recommended Sequence

1. **Characterize entropy profile.** Run Qwen3.5-27B on a diverse set of prompts (investigation, analysis, factual QA, coding). Log per-token entropy. Identify: what does the distribution look like? Where do spikes occur? Do they correlate with errors?

2. **Implement Phase 1 (mechanical pause).** Build the write → read → evaluate hook in the Agent Zero message pipeline. Measure: does self-evaluation catch errors that direct output misses? This validates the core premise before investing in inference pipeline modifications.

3. **Implement Phase 2 (entropy monitoring).** Add entropy logging to the inference pipeline. Build a dashboard showing entropy traces. Correlate spikes with known errors. This produces the data needed to calibrate all subsequent phases.

4. **Test SRGen on local stack.** Implement the correction mechanism. A/B test on a validation set. If step-level correction improves accuracy, proceed to Phase 4. If not, investigate why — model-specific calibration may be needed.

5. **Build trajectory probe.** Generate training data using the annotation methodology from the streaming detection paper. Train lightweight probe. Test online during generation. Measure: does trajectory monitoring catch errors that step-level correction misses?

6. **Test soft attention biasing (lightweight PI mitigation).** Before training the full SleepGate, add a simple staleness heuristic to attention: compute recency-based retention scores, add log(retention) to pre-softmax logits. Measure: does this reduce the 20-turn BST classification collapse? Does it improve agent performance in long conversations?

7. **Build Cache Processor.** Train a small auxiliary Transformer to rewrite KV entries at step boundaries. Start with consolidation only (recent entries). Add reconsolidation once consolidation is validated. Compare with and without prediction-error gating.

8. **Integrate all levels with BST and EI.** Wire the complete three-level pondering layer into the full stack. BST gates domain entry. Trajectory confidence feeds into EI scrutiny. Universal entropy monitor feeds all levels. Run end-to-end evaluation.

---

## 7. The Thread

This design note follows a thread that connects disparate observations into a single architectural insight:

Koyaanisqatsi (a film about systems out of balance) → collaboration sonification (translating conversation geometry into music) → coma dreams (narrative machinery without reality constraint) → the lamp (the geometric detail the dream can't assimilate) → System 1/System 2 (fast generation vs. slow evaluation) → temporal proprioception (the missing sense of processing duration) → the reflection mirror (file system as pondering infrastructure) → amnesia rehabilitation (external memory aids compensating for internal memory loss) → SRGen (proactive entropy-based intervention at structural decision points) → streaming hallucination detection (trajectory-level contamination monitoring) → first hallucination tokens (the lamp is only visible at the moment of divergence) → SleepGate (proactive interference as the real bottleneck, not context length) → Bottlenecked Transformers (memory consolidation/reconsolidation at step boundaries, ICLR 2026) → three-level architecture with universal entropy signal.

The thread is the research methodology. The use case found the research. The research validated the architecture. The architecture was already implicit in the questions we were asking. The design note captures the convergence.

---

*"The dream machinery runs perfectly. The problem was never the machinery. The problem was the absence of the lamp — the external constraint that the dream couldn't assimilate. Build the lamp into the generation process and the machinery corrects itself."*
