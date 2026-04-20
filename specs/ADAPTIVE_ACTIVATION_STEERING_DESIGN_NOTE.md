# Adaptive Activation Steering — Design Note
## "The scaffolding catches mistakes at the output layer. This catches them at the representation layer."

**Status:** Design note. Ready for phased build.
**Motivated by:** The Prosthetic Cortex establishing direct write access to `l_out-14` via cb_eval; the BST providing turn-level domain classification; the supervisor providing mistake detection. All three pieces exist. The missing piece is the correction vector library that connects them into a learning loop.
**Depends on:** Prosthetic Cortex Steps 10b, 12a, 13 (cb_eval hook confirmed working, layer 14 write confirmed, semantic band layers 9-18 identified); BST domain classifier (Layer 1); Supervisor loop (Layer 8); Epistemic Integrity (cross-cutting); llama.cpp cb_eval API.
**Author:** Kestrel, Session 062. Research synthesis with Jake.

---

## 1. The Insight

The Exocortex currently intervenes at the output layer. The supervisor detects a loop → injects a recovery prompt. The write validator catches truncation → redirects to heredoc. The epistemic integrity layer spots a fabricated value → injects a warning. All of these are correct responses to observable failure signals.

But they share a structural limitation: they intervene *after* the wrong pattern has formed. The model generates, the scaffolding catches, the scaffolding corrects. The correction is one turn behind the mistake.

Activation steering moves the intervention point upstream. Rather than catching wrong output and redirecting, you add a vector to the model's residual stream *before* generation starts. The wrong pattern never forms because the activation space has already been steered away from it.

The key realization — the one that makes this buildable rather than theoretical — is that three components already exist in this project that together implement the routing and injection side of this architecture:

1. **The cb_eval hook** (Prosthetic Cortex Step 10b) — confirmed write access to `l_out-14` during every forward pass. The injection point is live.
2. **The BST domain classifier** (Layer 1) — classifies every turn as coding, investigation, philosophical, etc. This is the router.
3. **The supervisor loop** (Layer 8) — detects mistake patterns by type and severity. This is the trigger for correction vector capture.

What does not exist yet: the correction vectors themselves, the mechanism for computing them from mistakes and documents, and the library for persisting them across sessions.

The full system is: **mistake detected → activation captured → correction vector computed → stored → injected on similar future turns via cb_eval**.

---

## 2. Research Landscape

### 2.1 What exists and is production-ready

**Contrastive Activation Addition (CAA)** — Rimsky et al. 2023, ACL 2024. Compute steering vectors by averaging the difference in residual stream activations between positive and negative prompt pairs. Apply at inference time with a tunable coefficient. Multiple vectors compose additively. This is the foundational mechanism this design uses. GitHub: `nrimsky/CAA`.

**Representation Engineering** — Zou et al. 2023, arXiv:2310.01405. Top-down approach: Linear Artificial Tomography (LAT) for reading representations, contrast vectors for control. Confirms that behavioral directions in activation space are linear, low-rank, and can be targeted precisely.

**Inference-Time Intervention (ITI)** — Li et al. 2023, arXiv:2306.03341. Identifies attention heads most associated with a behavior via linear probes. Shifts activations in those heads along a target direction. Improved truthfulness on Alpaca from 32.5% to 65.1% — strongest single-paper result for correction steering.

**Activation Steering Adapter (ASA)** — arXiv:2602.04935, February 2026. This paper is the closest published description of what this design builds. From the abstract: "router-conditioned mixture of steering vectors with probe-guided signed gate." A router (BST, in our case) selects from a library of domain-specific steering vectors and applies them with learned weights. Single-shot mid-layer intervention. Compact adapter with shared base vector plus domain offset experts.

**Layer 14 confirmation** — arXiv:2511.03738. "Layer 14 is consistently optimal across models and behaviors for 7-9B parameter models with ~32 layers." For 27B models the optimal range may shift slightly upward, but the semantic band (layers 9-18) identified in Prosthetic Cortex Step 12a is aligned with this finding.

**Guiding Giants** — arXiv:2505.20309. Trainable controller network that observes intermediate LLM activations and predicts global scaling factor plus layer-specific weights. Demonstrates that adaptive, layer-aware intervention outperforms fixed-alpha vectors. Suggests the injection alpha should vary by domain and context, not be a fixed constant.

### 2.2 What does not exist — the novel contributions

Research was conducted against all major paper databases and GitHub as of April 2026. The following have **no published implementations**:

1. **Runtime correction vector computation** — All published work computes vectors offline from hand-crafted pairs before deployment. No system computes correction vectors at runtime from the model's own mistakes during a live session.

2. **Persistent accumulating vector libraries** — Vectors computed in one session persist and grow richer in future sessions. Not implemented anywhere.

3. **Document-grounded positive examples** — Using reference documents (Python style guides, architecture textbooks) as the positive half of contrastive pairs rather than hand-crafted statements. The approach is mechanically straightforward but has not been built or evaluated.

4. **llama.cpp activation steering** — No published implementations of activation steering on GGUF quantized models via llama.cpp. All steering work runs on PyTorch HuggingFace models. The cb_eval hook approach is ahead of the published field.

These four gaps are exactly where this design operates.

### 2.3 Why GGUF/llama.cpp is actually fine

The concern with quantized models is whether steering vectors computed in full precision transfer to a quantized activation space. Research on AWQ and GPTQ confirms: **weights are quantized, activations stay in FP32/FP16**. The cb_eval hook reads and writes full-precision activation tensors. Quantization does not affect the steering mechanism.

---

## 3. Architecture

### 3.1 Full Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    PRECOMPUTATION PATH                       │
│                                                             │
│  PDF Documents (Python, Systems Design, ...)                │
│      ↓                                                      │
│  Positive Example Extractor                                 │
│      → chunk document into passages                         │
│      → run each through model                               │
│      → record activations at layer 14                       │
│      → compute centroid = domain direction vector           │
│      ↓                                                      │
│  Vector Library ← "correct Python" direction                │
│                   "good architecture" direction             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    ONLINE CAPTURE PATH                       │
│                                                             │
│  Agent running → Supervisor detects mistake                 │
│      ↓                (loop / stall / fabrication)          │
│  Activation Recorder                                        │
│      → capture l_out-{9..18} at mistake moment             │
│      → label: mistake_type, domain (from BST), turn_id     │
│      → store as negative example                           │
│      ↓                                                      │
│  Correction Vector Computer                                 │
│      → mean(positive examples) - mean(negative examples)    │
│      → normalize, store with metadata                       │
│      ↓                                                      │
│  Vector Library ← "don't loop in coding context"           │
│                   "don't fabricate in investigation"        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    INJECTION PATH                            │
│                                                             │
│  Every forward pass:                                        │
│      BST domain classification                              │
│          ↓                                                  │
│      Vector Selector                                        │
│          → query library: domain + context                 │
│          → return ranked vectors with confidence scores    │
│          ↓                                                  │
│      cb_eval hook at l_out-14                               │
│          → apply vectors additively: h = h + Σ(αᵢ · vᵢ)  │
│          ↓                                                  │
│      Model generates corrected output                       │
│          ↓                                                  │
│      Feedback: did mistake pattern stop?                    │
│          → yes: increment vector confidence                 │
│          → no: flag, increase alpha, seek more examples    │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Component Specifications

#### Activation Recorder (`extensions/tool_execute_after/_29_activation_recorder.py`)

Hook: `tool_execute_after`, slot 29 (after write validator and inline truncation detector, before fallback chain).

Fires when: `self.agent.get_data("_supervisor_mistake_type")` is non-None (set by supervisor on mistake detection).

**Prerequisite:** `_50_supervisor_loop.py` must be extended to call `self.agent.set_data("_supervisor_mistake_type", mistake_type)` after anomaly detection, before Tier 1+ injection. Currently the supervisor classifies loop type internally (`loop_stall`, `loop_cascade`, `loop_context`) but does not expose it via `agent.set_data()`. This is a one-line addition per anomaly branch. Epistemic Integrity (`_25_epistemic_integrity.py`, `monologue_end`) must similarly call `self.agent.set_data("_supervisor_mistake_type", "fabrication")` on EI verdict. The key must be cleared to `None` at turn start (session init or BST) to avoid stale state.

Captures: activations at layers 9-18 via a short cb_eval pass on the most recent user message. This re-runs a partial forward pass specifically to capture the activation state at the mistake moment — not the general session state, but the representation of the specific content that triggered the mistake.

Output structure:
```python
{
    "turn_id": str,
    "timestamp": float,
    "mistake_type": str,  # "loop_stall" | "loop_cascade" | "loop_context" | "fabrication" | "truncation_loop"
    "domain": str,        # from BST: "coding" | "investigation" | ...
    "activations": {
        "layer_9": np.ndarray,   # shape: (hidden_size,)
        "layer_14": np.ndarray,
        "layer_18": np.ndarray,
    },
    "text_sample": str,   # first 200 chars of the message that triggered the mistake
    "confidence": 1.0     # initial; updated by feedback loop
}
```

Stored at: `/a0/usr/Exocortex/steering/negative_examples/{domain}/{mistake_type}/`

#### Positive Example Extractor (`instrument/extract_positive_vectors.py`)

Runs offline (not during agent operation) or on-demand via a new agent tool.

Input: PDF or text document path, domain label, target layer (default 14).

Process:
1. Extract text, chunk into ~200-token passages with overlap
2. For each passage: tokenize, run through model via llama.cpp with cb_eval hook active
3. Record activation at target layer for the last non-padding token (last-token pooling — confirmed necessary in Prosthetic Cortex Step 12a; mean pooling collapses to common base direction)
4. Compute centroid across all passage activations
5. Optionally: compute PCA to get top-k directions of variance (captures multiple aspects of the domain)

Output: `{domain}_positive_vectors.npy` + metadata JSON at `/a0/usr/Exocortex/steering/positive_examples/`

#### Correction Vector Computer (`instrument/compute_correction_vectors.py`)

Runs after enough negative examples accumulate (threshold: ≥3 examples per mistake type per domain).

Process: CAA-style contrastive computation.
```python
v_correction = mean(positive_activations) - mean(negative_activations)
v_correction = v_correction / np.linalg.norm(v_correction)  # normalize
```

Stores to vector library with:
- Source counts (how many positive/negative examples used)
- Compute timestamp
- Domain + mistake_type key
- Initial confidence score (0.5; updated by feedback)

#### Vector Library (`/a0/usr/Exocortex/steering/vector_library/`)

```
vector_library/
  index.json                          # metadata for all vectors
  coding_loop_stall.npy               # correction vector
  coding_loop_stall_meta.json         # source counts, confidence, last_updated
  coding_fabrication.npy
  investigation_fabrication.npy
  coding_positive.npy                 # domain direction from PDFs
  systems_design_positive.npy
  ...
```

`index.json` schema:
```json
{
  "vectors": [
    {
      "key": "coding_loop_stall",
      "domain": "coding",
      "mistake_type": "loop_stall",
      "confidence": 0.73,
      "positive_examples": 12,
      "negative_examples": 8,
      "successes": 15,
      "failures": 4,
      "last_updated": "2026-04-18T...",
      "layer": 14,
      "alpha": 0.4
    }
  ]
}
```

#### BST-Routed Injector (`extensions/before_main_llm_call/_18_steering_injector.py`)

Hook: `before_main_llm_call`, slot **18** (after tool registry _16 and library catalog/orchestration gate _17, before memory catalog _18 — note: if _18 is taken, bump to _19; verify slot availability at implementation time).

**Note on slot _17:** Slots `_17_library_catalog.py` and `_17_orchestration_gate.py` already occupy slot 17. Per WIRING.md Seam #4, numeric prefix collision creates undefined execution order. Deploy at _18 (currently unoccupied).

On each turn:
1. Read BST domain from `loop_data.extras_persistent.get("_bst_domain", "")`  
   ⚠ **API note:** BST writes to `loop_data.extras_persistent["_bst_domain"]`, not via `agent.set_data()`. Use `extras_persistent.get()` — not `self.agent.get_data()` which reads a different store.
2. Query vector library for vectors matching this domain
3. Sort by confidence score, take top-3
4. Schedule injection for the upcoming forward pass: store vector list in `loop_data.params_temporary["_steering_vectors"]`
5. The cb_eval hook reads from this key and applies vectors during the forward pass

The cb_eval hook addition (in llama.cpp Python bindings or via the Prosthetic Cortex activation writer):
```python
def steering_callback(layer_idx, token_idx, activations):
    vectors = get_scheduled_vectors()  # reads from agent state
    if not vectors:
        return activations
    for v, alpha in vectors:
        if v.layer == layer_idx:
            activations = activations + alpha * v.direction
    return activations
```

**Architectural constraint — inference path:** The cb_eval hook requires direct llama.cpp Python binding access. In production, Agent Zero calls LM Studio via HTTP (OpenAI-compatible API). There is no cb_eval access through the LM Studio boundary. Two options:

- **Option A (Phase 3 prerequisite):** Replace LM Studio with `llama-cpp-python` server mode (`python -m llama_cpp.server`). Exposes the same OpenAI API to the agent, but allows Python-level cb_eval registration. Cost: loses LM Studio UI/model management. Gain: full activation steering at inference time.

- **Option B (phased approach):** Keep LM Studio for Phases 1–2 (offline precomputation and activation capture use the existing `instrument/` infrastructure directly). Phase 3 live injection becomes a discrete decision point — switch inference path to llama-cpp-python server when ready to go live. This is the recommended path: deliver vector library value before committing to infrastructure change.

The `instrument/read_activations.py` tool already demonstrates full cb_eval write access via direct llama.cpp call. The steering callback is composable with the existing activation reader — both can coexist in the same callback function (read phase, then write phase, on matching layer).

Alpha scaling follows the Guiding Giants approach: not fixed, but scaled by:
- Vector confidence (low confidence → lower alpha)
- Supervisor anomaly score (high concern → higher alpha)
- Domain match strength (BST secondary domain → reduce alpha)

#### Feedback Loop (extension to supervisor `_50_supervisor_loop.py`)

After any turn where steering vectors were applied:
- Check whether the mistake pattern that triggered the vector selection recurred
- If the pattern stopped: `vector.successes += 1`, `vector.confidence = successes / (successes + failures)`
- If the pattern continued: `vector.failures += 1`, flag for alpha increase or more examples
- Write updated confidence to vector library index

---

## 4. PDF Integration

Jake has Python and systems design reference documents. These provide the positive half of contrastive pairs — what correct, idiomatic code and sound architectural reasoning look like in activation space.

**Python PDF → coding domain direction:**
Extract functions, patterns, idioms. Run through model. Layer 14 activations cluster in the "correct Python" region. The centroid is the positive vector. When BST detects domain=coding, this vector is additively composed with any mistake-specific correction vectors. The model is steered toward correct Python before it generates a token.

**Systems design PDF → architectural reasoning direction:**
Extract principles, patterns, tradeoffs sections. Same process. When the agent is doing architectural work (investigation domain, high philosophical channel in BST), this vector steers toward rigorous architectural reasoning.

**Why this is stronger than prompt injection:**
The BST already injects domain context via prompt. But prompt injection works on the attention mechanism — the model reads it and responds. Activation steering works on the residual stream directly — the representation of the query is shifted before attention over the prompt even begins. The two interventions are complementary, operating at different points in the forward pass.

---

## 5. Connection to Existing Layers

| Layer | Role in This System |
|-------|---------------------|
| BST (Layer 1) | Domain routing — selects which vectors to apply |
| Supervisor (Layer 8) | Mistake detection — triggers activation capture; reads feedback |
| Epistemic Integrity (cross-cutting) | Fabrication detection — triggers "fabrication" negative example capture |
| Sleep Consolidation Phase 4 | Vector consolidation — prune low-confidence vectors, merge near-duplicates across sessions |
| Prosthetic Cortex Steps 10b/12a/13 | cb_eval hook, confirmed write access, semantic band, centroid computation — all prerequisites |
| Write Validator (_26_) | Truncation loop detection — triggers "truncation_loop" negative example capture |

The Sleep Consolidation Phase 4 extension is particularly natural: the nightly consolidation pass already prunes low-utility memories and promotes high-utility ones. Adding a vector consolidation step (prune low-confidence vectors, merge near-duplicate corrections) to that pass means the steering library stays lean and accurate over time.

---

## 6. Build Plan

### Phase 1 — Offline Precomputation (~1 session)

**Goal:** Compute positive domain direction vectors from Jake's PDFs. Verify they are meaningfully distinct in activation space. Test injection at layer 14. Confirm behavioral shift.

**Deliverables:**
- `instrument/extract_positive_vectors.py` — PDF → activation centroid pipeline
- `instrument/test_steering_injection.py` — verify injection shifts outputs in the expected direction
- Initial vector library populated with coding and systems_design positive vectors

**Success criterion:** A prompt in coding domain with positive vector injected produces measurably different activation patterns at layer 14 than without injection. Cosine similarity between steered and "ideal" response activations is higher than unsteered.

### Phase 2 — Online Mistake Capture (~1 session)

**Goal:** Activation Recorder extension fires on supervisor-detected mistakes, accumulates negative examples, computes first contrastive correction vectors.

**Deliverables:**
- `extensions/tool_execute_after/_29_activation_recorder.py`
- `instrument/compute_correction_vectors.py`
- Enough mistakes captured in a stress test to compute first real correction vectors

**Success criterion:** After one stress test session, vector library contains at least 3 domain+mistake_type correction vectors computed from real mistake activations.

### Phase 3 — BST-Routed Injection (~1 session)

**Goal:** Full injection pipeline active. Steering vectors applied on every turn via BST routing. Feedback loop updates confidence scores.

**Deliverables:**
- `extensions/before_main_llm_call/_17_steering_injector.py`
- cb_eval hook modification for vector application
- Feedback loop addition to `_50_supervisor_loop.py`

**Success criterion:** Stress test shows reduction in mistake recurrence rate for domains with high-confidence vectors vs. domains without.

### Phase 4 — Sleep Consolidation Integration (~0.5 sessions)

**Goal:** Vector library maintained by nightly consolidation pass. Stale vectors pruned. Near-duplicates merged.

**Deliverables:**
- Vector consolidation step in `sleep_consolidation.py` Phase 4

**Success criterion:** After 5 sessions, vector library remains under 50 entries (pruning working) with average confidence above 0.65 (quality improving over time).

---

## 7. What This Does NOT Do

- **Does not modify model weights.** Vectors are applied at inference time. The base model is unchanged. Removing the injector restores original behavior completely.
- **Does not replace the scaffolding layers.** The supervisor, epistemic integrity, and write validator continue operating. This is an additional intervention layer upstream of them, not a replacement.
- **Does not guarantee generalization.** A correction vector computed from 3 examples of a loop in coding context may not fire effectively on a loop in investigation context. Vectors are domain-specific by design.
- **Does not work on all models.** Requires cb_eval hook access — this is llama.cpp specific. Cloud API models cannot be steered this way.
- **Does not learn in real time during a single turn.** Vector computation requires accumulating examples across multiple turns. Single-turn learning is not possible with this architecture.
- **Does not produce interpretable explanations** of why a correction was applied. The steering vector is a direction in activation space, not a human-readable rule. SAE-based interpretation of vectors (arXiv:2411.02193) is a future research direction.

---

## 8. What Makes This Novel

Research as of April 2026 confirms that:

1. **No published system computes steering vectors at runtime from the model's own mistakes.** All published work computes vectors offline from hand-crafted pairs.
2. **No published system maintains a persistent accumulating vector library** that grows across sessions.
3. **No published system uses reference documents as positive examples** for steering vector computation.
4. **No published implementation applies activation steering to llama.cpp/GGUF quantized models.** All published work runs on PyTorch HuggingFace models.

The Prosthetic Cortex work (cb_eval hook, confirmed write access) is already ahead of the published field at the infrastructure level. This design extends that infrastructure into a learning loop.

The closest published work is ASA (arXiv:2602.04935, February 2026): "router-conditioned mixture of steering vectors with probe-guided signed gate." The BST is the router. The vector library is the mixture. The design here extends ASA's approach with online vector computation and document-grounded positive examples — neither of which ASA implements.

---

## 9. Research Lineage

**Foundational:**
- Rimsky et al. (ACL 2024) — "Steering Llama 2 via Contrastive Activation Addition" — CAA mechanism
- Zou et al. (arXiv:2310.01405) — "Representation Engineering" — linear structure of behavioral directions
- Li et al. (arXiv:2306.03341) — "Inference-Time Intervention" — truthfulness correction via head-level intervention

**Architecture:**
- ASA (arXiv:2602.04935, 2026) — router-conditioned mixture of steering vectors
- Guiding Giants (arXiv:2505.20309) — adaptive layer-specific weight scaling
- SADI (arXiv:2410.12299) — dynamic vector scaling based on input semantics

**Layer selection:**
- arXiv:2511.03738 — "Layer 14 consistently optimal for semantic steering"
- LayerNavigator (NeurIPS 2025) — scoring method for layer steerability
- Prosthetic Cortex Step 12a (this project) — semantic band layers 9-18 identified empirically on production model

**Quantization:**
- AWQ, GPTQ research confirming activations stay FP32 — steering vectors transfer to quantized models
- Prosthetic Cortex Steps 10b, 13 (this project) — cb_eval hook confirmed, struct offsets measured, 42.0 written and read back from l_out-14

**Self-correction:**
- Intrinsic Self-Correction (various 2024-2025 papers) — models can refine via activation-level steering
- arXiv:2603.12298 — Global Evolutionary Steering, cross-layer consistency
- YaPO (arXiv:2601.08441) — sparse activation steering via pretrained SAEs for domain adaptation

---

*Design note by Kestrel. Session 062. April 18, 2026.*
*The scaffolding catches mistakes at the output layer. This catches them at the representation layer. The agent learns not from being corrected, but from having been.*
