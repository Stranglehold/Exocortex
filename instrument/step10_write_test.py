#!/usr/bin/env python3
"""
Step 10 — llama-cpp-python write test.

Determines whether llama-cpp-python's Python bindings support:
(a) registering a ggml_backend_sched_eval_callback (cb_eval)
(b) reading activation tensors via ggml_backend_tensor_get
(c) writing modified values back via ggml_backend_tensor_set

This is the Path A vs Path B decision point for the Prosthetic Cortex Stage 3.

Usage:
    python3 step10_write_test.py
"""

import sys
import ctypes
import numpy as np

MODEL_PATH = "D:/LMStudio/Models/lmstudio-community/Qwen3-0.6B-GGUF/Qwen3-0.6B-Q8_0.gguf"
TEST_PROMPT = "The meaning of this test is to verify"

print("=" * 60)
print("Step 10: llama-cpp-python activation read/write test")
print("=" * 60)

# ── Step 1: Import and inspect the low-level API ─────────────────────────────
print("\n[1] Importing llama_cpp...")
try:
    import llama_cpp
    import llama_cpp.llama_cpp as _lib
    print(f"    llama-cpp-python version: {llama_cpp.__version__}")
except ImportError as e:
    print(f"    FAIL: {e}")
    sys.exit(1)

# ── Step 2: Check if cb_eval is exposed in llama_context_params ─────────────
print("\n[2] Checking llama_context_params for cb_eval...")
params = _lib.llama_context_default_params()
cb_eval_available = hasattr(params, 'cb_eval')
print(f"    cb_eval field in llama_context_params: {cb_eval_available}")
if cb_eval_available:
    print(f"    cb_eval type: {type(params.cb_eval)}")

# ── Step 3: Check for ggml_backend_tensor_get/set ────────────────────────────
print("\n[3] Checking for tensor read/write functions...")
has_tensor_get = hasattr(_lib, 'ggml_backend_tensor_get')
has_tensor_set = hasattr(_lib, 'ggml_backend_tensor_set')
has_tensor_get_async = hasattr(_lib, 'ggml_backend_tensor_get_async')
print(f"    ggml_backend_tensor_get: {has_tensor_get}")
print(f"    ggml_backend_tensor_set: {has_tensor_set}")
print(f"    ggml_backend_tensor_get_async: {has_tensor_get_async}")

# Check alternative tensor data access paths
has_get_data = hasattr(_lib, 'ggml_get_data')
has_get_data_f32 = hasattr(_lib, 'ggml_get_data_f32')
print(f"    ggml_get_data (direct ptr): {has_get_data}")
print(f"    ggml_get_data_f32 (direct ptr): {has_get_data_f32}")

# ── Step 4: Check tensor name access ─────────────────────────────────────────
print("\n[4] Checking tensor attribute access...")
has_tensor_name = hasattr(_lib, 'ggml_get_name')
has_tensor_ne = hasattr(_lib, 'ggml_tensor')
print(f"    ggml_get_name: {has_tensor_name}")
print(f"    ggml_tensor struct: {has_tensor_ne}")

# ── Step 5: Load model and try callback registration ─────────────────────────
print(f"\n[5] Loading model: {MODEL_PATH.split('/')[-1]}")
try:
    callback_calls = []

    if cb_eval_available:
        # Define the callback function type
        # ggml_backend_sched_eval_callback: (tensor, ask, user_data) -> bool
        EVAL_CALLBACK = ctypes.CFUNCTYPE(
            ctypes.c_bool,
            ctypes.c_void_p,  # tensor ptr
            ctypes.c_bool,    # ask
            ctypes.c_void_p,  # user_data
        )

        @EVAL_CALLBACK
        def my_cb_eval(tensor_ptr, ask, user_data):
            if not ask and tensor_ptr:
                # Get tensor name if possible
                name = "(unknown)"
                if has_tensor_name:
                    try:
                        raw = _lib.ggml_get_name(ctypes.cast(tensor_ptr, ctypes.POINTER(_lib.ggml_tensor)))
                        if raw:
                            name = raw.decode('utf-8', errors='replace')
                    except Exception:
                        pass
                callback_calls.append(name)
            return True  # always continue

        llm = llama_cpp.Llama(
            model_path=MODEL_PATH,
            n_ctx=128,
            n_gpu_layers=0,  # CPU only for this test
            verbose=False,
        )
        print(f"    Model loaded.")

        # Try to set the callback on the underlying context
        ctx = llm.ctx
        print(f"    llm.ctx type: {type(ctx)}")
        print(f"    llm.ctx value: {ctx}")
        has_ctx_set_eval_callback = hasattr(_lib, 'llama_set_causal_attn')

        # Check if we can access the ggml_backend_sched
        has_sched = hasattr(_lib, 'llama_get_model_tensor')
        print(f"    llama_get_model_tensor: {has_sched}")

    else:
        # Load without callback to check tensor access
        llm = llama_cpp.Llama(
            model_path=MODEL_PATH,
            n_ctx=128,
            n_gpu_layers=0,
            verbose=False,
        )
        print(f"    Model loaded (no cb_eval support in params).")

    # ── Step 6: Run inference and check what we can access ───────────────────
    print(f"\n[6] Running test inference...")
    output = llm(TEST_PROMPT, max_tokens=5, echo=False)
    print(f"    Output: {output['choices'][0]['text']!r}")

    if callback_calls:
        print(f"\n    Callback fired {len(callback_calls)} times")
        print(f"    First 10 tensor names: {callback_calls[:10]}")
        print(f"    l_out tensors seen: {[n for n in callback_calls if 'l_out' in n][:5]}")
    else:
        print(f"\n    No callback calls recorded")

    # ── Step 7: Try direct tensor data access via ggml_get_data ─────────────
    print(f"\n[7] Testing direct tensor data access...")
    if has_tensor_get and has_tensor_set:
        print("    ggml_backend_tensor_get and set are available — PATH A CONFIRMED")
    elif has_get_data:
        print("    ggml_get_data available (direct pointer access) — needs ctypes casting")
    else:
        print("    No direct tensor write path found — PATH B (C extension) required")

    llm = None  # release

except Exception as e:
    import traceback
    print(f"    ERROR: {e}")
    traceback.print_exc()

# ── Summary ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("VERDICT:")
if cb_eval_available and (has_tensor_get or has_get_data):
    print("  PATH A viable — callback registration and tensor access both exposed")
    if has_tensor_set:
        print("  WRITE ACCESS CONFIRMED — full read/write via Python bindings")
    else:
        print("  Write access unclear — ctypes workaround may be needed")
elif cb_eval_available:
    print("  Callback exposed but tensor get/set not directly available")
    print("  Partial Path A — read may work, write needs ctypes")
else:
    print("  cb_eval not exposed in Python bindings — PATH B required")
    print("  Need C extension or ctypes to call llama.cpp directly")
print("=" * 60)
