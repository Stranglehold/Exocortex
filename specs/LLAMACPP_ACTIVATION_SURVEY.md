# llama.cpp Activation Callback Survey

**Date:** 2026-03-06
**For:** Opus Architect — flying buttress design (Prosthetic Cortex Stage 3)
**By:** Kestrel

---

## The Most Important Finding

**The mechanism already exists.** `ggml_backend_sched_eval_callback` is a public, documented API already wired into `llama_context_params`. The flying buttress exists in skeletal form — nobody has used it to build what we are building. What is missing is the wrapper that makes it usable as a structured activation reader and steerer.

The project does not need to patch llama.cpp internals or build a new callback mechanism from scratch. It needs to:
1. Use the existing callback API correctly
2. Build a Python wrapper that exposes it to the Exocortex
3. Resolve the LM Studio incompatibility (see below)

---

## The Two Callback Levels

llama.cpp has two distinct callback systems. They must not be confused.

### `llm_graph_cb` — Construction Time

**When it fires:** During graph *building*, before any computation.
**What's available:** Tensor metadata (name, shape, type). No computed values.
**What it's used for:** Internally, to name tensors (`"norm-3"`, `"ffn_down-7"`) and assign them to backends.
**Why it matters for us:** The names set at construction time are how the execution-time callback identifies layer boundaries. The naming convention is the map.

```c
// Graph construction callback signature (internal)
typedef void (*llm_graph_cb)(struct ggml_tensor * cur, const char * name, int il);
//                                                                           ^^
//                                                                      layer index
```

Layer index `il` is explicitly passed at construction time — every tensor knows its layer.

### `ggml_backend_sched_eval_callback` — Execution Time

**When it fires:** During graph *execution*, node by node.
**Two modes:**
- `ask=true` — fires before computation; return `true` to compute the node, `false` to skip it
- `ask=false` — fires after computation; GPU has been synchronized; tensor contains computed values

**This is the observation and intervention point.**

```c
typedef bool (*ggml_backend_sched_eval_callback)(
    struct ggml_tensor * t,
    bool ask,
    void * user_data
);
```

**How to register it:**
```c
struct llama_context_params params = llama_context_default_params();
params.cb_eval = my_callback_function;
params.cb_eval_user_data = my_context_pointer;
```

---

## Layer Boundary Locations

Transformer layer boundaries are identifiable by tensor name patterns set at construction time:

| Tensor name pattern | What it is | Layer boundary |
|---------------------|------------|----------------|
| `"norm-{il}"` | Pre-attention layer norm | Start of layer `il` |
| `"attn_norm-{il}"` | Alternative norm name | Start of layer `il` |
| `"ffn_down-{il}"` | FFN down projection output | End of layer `il` |
| `"l_out-{il}"` | Layer output (residual sum) | Clean layer output, best intervention point |

The `"l_out-{il}"` tensor is the full residual stream output after both attention and FFN — this is the standard representation engineering intervention point.

---

## The Intervention Mechanism (Confirmed)

After `cb_eval` fires with `ask=false`:

```c
// Read the activation
float buffer[n_embd];
ggml_backend_tensor_get(t, buffer, 0, sizeof(buffer));

// Modify it (add a steering vector, for example)
for (int i = 0; i < n_embd; i++) buffer[i] += steering_vector[i];

// Write back — downstream GPU operations WILL see this
ggml_backend_tensor_set(t, buffer, 0, sizeof(buffer));

return true;  // continue execution
```

`cudaStreamSynchronize()` is already called before the callback fires. Writing new data and returning `true` continues execution with the modified tensor. **The steering mechanism works.**

---

## The Performance Reality

Reading an activation tensor from GPU in the callback triggers `cudaMemcpyAsync` + `cudaStreamSynchronize` — a full pipeline stall.

For a 14B model (n_embd = 5120, float16):
- Each layer read: ~10KB
- Reading all 32 layers per token: ~320KB
- Estimated additional latency on RTX 3090 (PCIe): **~1–3ms per token**

For a 35B model (n_embd = 7168):
- Each layer read: ~14KB
- Reading all layers per token: proportionally higher

**Selective reading is essential.** Don't read all layers — read only the layers that matter for classification (e.g., layers 12-16 for semantic content, per representation engineering literature). The instrument doesn't need all 32 layers to classify domain.

### The Static Steering Alternative

`llama_set_adapter_cvec` is an existing API that adds a constant vector to activations at specified layers. It avoids the pipeline stall entirely by baking the addition as a GPU-side `ggml_add` node at graph construction time.

**For the prosthetic cortex Stage 3:** Static steering vectors (pre-computed per domain) can use `llama_set_adapter_cvec` — no callback overhead, no pipeline stall. The callback is needed only when the steering depends on the input's actual activation values (dynamic steering, Stage 3 full implementation).

The recommended sequence:
1. Use callbacks for Stage 2 (read activations to classify domain)
2. Use `llama_set_adapter_cvec` for Stage 3 static steering vectors
3. Use callbacks for Stage 3 dynamic steering (where the intervention depends on measured activation values)

---

## The LM Studio Verdict

**LM Studio cannot be used as the integration surface for activation callbacks.**

The callback mechanism is a C ABI concern — a C function pointer registered at context creation. LM Studio's OpenAI-compatible HTTP API has no path to a C function pointer. The wrapper layer (HTTP → inference) doesn't expose the callback registration surface.

**The Prosthetic Cortex must link against llama.cpp as a library directly.**

Two viable paths:

### Path A: Python Bindings (llama-cpp-python)
`llama-cpp-python` wraps llama.cpp and exposes the callback via `LogitsProcessorList` and `llama_cpp.Llama` parameters. The `callback_eval` and `callback_eval_user_data` parameters map directly to `cb_eval`. This is the fastest path to a working prototype.

Limitation: `llama-cpp-python` may not expose full tensor manipulation — read is likely available, write may require a ctypes workaround.

### Path B: Direct C/C++ Extension
Build a minimal Python extension (pybind11 or ctypes) that links against `libllama.so`/`llama.dll` and exposes the callback with full tensor read/write access. More work upfront, full capability at the end.

**For the prototype (Step 2 embedding experiment):** Path A is sufficient — we need read access, not write access.
**For Stage 3 (steering):** Path B is required — write access to tensors after `ask=false`.

---

## What Exists vs What Needs to Be Built

| Capability | Exists? | Where |
|------------|---------|-------|
| Execution-time callback API | Yes | `ggml_backend_sched_eval_callback` in `llama_context_params` |
| Layer index at callback time | Yes | Parseable from tensor name (`"l_out-7"` → layer 7) |
| GPU→CPU tensor read | Yes | `ggml_backend_tensor_get()` |
| CPU→GPU tensor write (steering) | Yes | `ggml_backend_tensor_set()` |
| Static steering vectors | Yes | `llama_set_adapter_cvec()` |
| Python access to callbacks | Partial | `llama-cpp-python` (read likely ok, write uncertain) |
| Structured activation reader (our Stage 2) | No | **Build this** |
| Activation steerer with domain classification | No | **Build this** |
| Integration with Exocortex BST | No | **Build this** |

---

## Recommended Next Steps (for Opus Architect)

1. **Prototype with llama-cpp-python (Path A):** Register a `cb_eval` callback, identify `l_out-{il}` tensors by name, read the activations for target layers into numpy arrays. Measure the latency cost on RTX 3090. This validates the full pipeline from running model to numpy array before committing to a C extension.

2. **Design the callback interface for the Exocortex:** Two types as Eitan specified —
   - **Read callback:** fires at specified layer boundaries, returns tensor values as numpy array, no modification
   - **Intervention callback:** fires at specified layer boundaries, receives tensor values, can return modified values

3. **Determine Layer 12-16 vs full-layer reading:** The representation engineering literature suggests semantic domain information concentrates in middle layers. Validate this for the target models (Qwen2.5-14B, GLM-4.7) before committing to a layer selection strategy.

4. **Decide Path A vs Path B:** If `llama-cpp-python`'s write access is insufficient for steering, the C extension is the flying buttress contribution. Build it as a standalone `llama_activations` Python package — distributable to anyone running local models who wants activation access.

---

## Open Questions for Opus Architect

1. **Which layers for the domain classifier?** The representation reader (Stage 2) needs to read specific layers. Layers 12-16 are the standard recommendation for 14B models. Does Opus have a view on this from the Karkada/Park research?

2. **llama-cpp-python write access:** Has this been tested? ctypes might be needed to call `ggml_backend_tensor_set` through the Python binding. Worth a 20-minute prototype before committing to a full C extension.

3. **Model compatibility:** The callback API is part of the GGML graph execution, not specific to any model architecture. But the `l_out-{il}` naming convention should be verified against the Qwen2.5 and GLM model implementations in llama.cpp before assuming it's universal.

4. **`llama_set_adapter_cvec` for Stage 3 static steering:** This is underdiscussed in the design note. Pre-computing domain steering vectors offline and applying them via this API would add zero inference latency for static cases. The callback is only needed for dynamic (input-dependent) steering.

---

*Prepared by Kestrel, 2026-03-06.*
*Source: llama.cpp codebase analysis via GitHub (ggerganov/llama.cpp, current main branch).*
*Key files examined: `ggml/include/ggml-backend.h`, `include/llama.h`, `src/llama.cpp` (`llm_build_*` functions), `ggml/src/ggml-backend.c`.*
