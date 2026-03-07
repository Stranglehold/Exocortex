#!/usr/bin/env python3
"""
Step 10b — Low-level llama-cpp-python activation callback test.

Uses the llama_cpp._lib C bindings directly to:
1. Create model + context with cb_eval set
2. Run inference and confirm the callback fires
3. Read tensor name and shape from callback
4. Attempt tensor read via ctypes (direct pointer access)

This bypasses the high-level Llama class which doesn't pass cb_eval through.
"""

import sys
import ctypes
import struct
import numpy as np

MODEL_PATH = "D:/LMStudio/Models/lmstudio-community/Qwen3-0.6B-GGUF/Qwen3-0.6B-Q8_0.gguf"

print("=" * 60)
print("Step 10b: Low-level activation callback test")
print("=" * 60)

import llama_cpp.llama_cpp as _lib

# ── Inspect what the ggml_tensor struct looks like ───────────────────────────
print("\n[1] Inspecting ggml_tensor struct...")
try:
    t = _lib.ggml_tensor()
    fields = [f[0] for f in t._fields_] if hasattr(t, '_fields_') else []
    print(f"    ggml_tensor fields: {fields}")
except Exception as e:
    print(f"    ggml_tensor not directly constructable: {e}")

# Check what functions ARE available that relate to tensors
print("\n[2] Scanning for tensor-related functions in _lib...")
tensor_funcs = [name for name in dir(_lib) if 'tensor' in name.lower() or 'ggml' in name.lower()]
print(f"    Found {len(tensor_funcs)} ggml/tensor functions:")
for fn in sorted(tensor_funcs)[:40]:
    print(f"      {fn}")
if len(tensor_funcs) > 40:
    print(f"      ... and {len(tensor_funcs) - 40} more")

# ── Check what llama-level functions are available ───────────────────────────
print("\n[3] Scanning for llama_* functions...")
llama_funcs = [name for name in dir(_lib) if name.startswith('llama_')]
print(f"    Found {len(llama_funcs)} llama_* functions:")
for fn in sorted(llama_funcs):
    print(f"      {fn}")

# ── Try to create context with cb_eval using low-level API ──────────────────
print("\n[4] Setting up low-level model + context with cb_eval...")

# Storage for callback observations
observations = []

try:
    # Define callback type
    EVAL_CB_TYPE = ctypes.CFUNCTYPE(
        ctypes.c_bool,       # return type
        ctypes.c_void_p,     # ggml_tensor * t
        ctypes.c_bool,       # bool ask
        ctypes.c_void_p,     # void * user_data
    )

    # ── Confirmed struct offsets (from step11 empirical scan) ────────
    # ggml_tensor layout (64-bit): type(4)+pad(4)+buffer*(8)+ne[4](32)+
    # nb[4](32)+op(4)+op_params[16](64)+flags(4)+pad(4)+src[10]*(80)+
    # view_src*(8)+view_offs(8)+data*(8)+name[64]
    # data pointer at offset 248, name at offset 256
    NAME_OFFSET = 256
    DATA_PTR_OFFSET = 248

    import re as _re
    NAME_RE = _re.compile(r'^[a-zA-Z_][a-zA-Z0-9_\-+.\[\]/]*$')
    write_results = []  # accumulate write test results

    def read_name(ptr):
        try:
            raw = bytes((ctypes.c_char * 64).from_address(ptr + NAME_OFFSET))
            null = raw.find(b'\x00')
            if null < 1:
                return None
            s = raw[:null].decode('ascii', errors='strict')
            return s if NAME_RE.match(s) and len(s) <= 63 else None
        except Exception:
            return None

    @EVAL_CB_TYPE
    def cb_eval(tensor_ptr, ask, user_data):
        """Fires for each node in the computation graph during execution."""
        if not ask and tensor_ptr:
            name = read_name(tensor_ptr) or '(unnamed)'
            obs = {'name': name, 'ptr': tensor_ptr}

            # ── Write test: target l_out-14 (middle layer) ────────────
            if name == 'l_out-14' and not write_results:
                try:
                    data_ptr_raw = ctypes.c_void_p.from_address(
                        tensor_ptr + DATA_PTR_OFFSET
                    ).value
                    if data_ptr_raw and data_ptr_raw > 0x10000:
                        float_arr = (ctypes.c_float * 16).from_address(data_ptr_raw)
                        original_vals = [float_arr[i] for i in range(8)]

                        # Write test: write 42.0, read back
                        float_arr[0] = 42.0
                        read_back = ctypes.c_float.from_address(data_ptr_raw).value
                        float_arr[0] = original_vals[0]  # restore

                        write_confirmed = abs(read_back - 42.0) < 0.001
                        write_results.append({
                            'data_ptr': data_ptr_raw,
                            'original': original_vals[:5],
                            'read_back_42': read_back,
                            'write_confirmed': write_confirmed,
                        })
                        obs['write_test'] = 'done'
                except Exception as ex:
                    write_results.append({'error': str(ex)})

            observations.append(obs)
        return True

    # Load model
    model_params = _lib.llama_model_default_params()
    model_params.n_gpu_layers = 0  # CPU for test
    model = _lib.llama_load_model_from_file(
        MODEL_PATH.encode('utf-8'),
        model_params
    )
    if not model:
        print("    FAIL: Could not load model")
        sys.exit(1)
    print(f"    Model loaded: {model}")

    # Create context with cb_eval set
    ctx_params = _lib.llama_context_default_params()
    ctx_params.n_ctx = 128
    ctx_params.n_batch = 64
    ctx_params.cb_eval = cb_eval
    ctx_params.cb_eval_user_data = None

    print(f"    cb_eval set in params: {ctx_params.cb_eval}")

    ctx = _lib.llama_new_context_with_model(model, ctx_params)
    if not ctx:
        print("    FAIL: Could not create context")
        sys.exit(1)
    print(f"    Context created: {ctx}")

    # ── Tokenize and run one forward pass ────────────────────────────────────
    print("\n[5] Running inference with callback...")
    prompt = b"The purpose of this"
    tokens = (ctypes.c_int32 * 64)()

    # llama-cpp-python 0.3.x API: llama_tokenize takes vocab ptr, not model ptr
    vocab = _lib.llama_model_get_vocab(model)
    print(f"    vocab ptr: {vocab}")
    n_tokens = _lib.llama_tokenize(
        vocab, prompt, len(prompt),
        tokens, 64,
        True,   # add_special
        False,  # parse_special
    )
    print(f"    Tokenized to {n_tokens} tokens")

    # Create batch
    batch = _lib.llama_batch_get_one(tokens, n_tokens)

    # Decode
    ret = _lib.llama_decode(ctx, batch)
    print(f"    llama_decode returned: {ret} (0=success)")

    # ── Report callback results ──────────────────────────────────────────────
    print(f"\n[6] Callback fired {len(observations)} times")
    if observations:
        print(f"    First 10 tensor names:")
        for obs in observations[:10]:
            print(f"      {obs['name']!r}")

        l_out = [o for o in observations if o.get('name', '').startswith('l_out-')]
        norm = [o for o in observations if 'norm' in o.get('name', '')]
        print(f"    'l_out' tensors: {len(l_out)}")
        print(f"    'norm' tensors: {len(norm)}")
        if l_out:
            sample = sorted(set(o['name'] for o in l_out))[:6]
            print(f"    Sample l_out names: {sample}")

        # ── Write test results (executed inside callback on l_out-14) ─────────
        print("\n[7] Write test results (l_out-14 targeted inside callback):")
        if write_results:
            wr = write_results[0]
            if 'error' in wr:
                print(f"    ERROR: {wr['error']}")
            else:
                print(f"    data_ptr: 0x{wr['data_ptr']:016x}")
                print(f"    original values: {[f'{v:.4f}' for v in wr['original']]}")
                print(f"    wrote 42.0, read back: {wr['read_back_42']:.6f}")
                if wr['write_confirmed']:
                    print(f"    *** WRITE CONFIRMED — PATH A FULLY VIABLE ***")
                    print(f"    ctypes direct pointer write to CPU tensor WORKS")
                    print(f"    cb_eval + ctypes = full read/write access to residual stream")
                else:
                    print(f"    Write returned {wr['read_back_42']} — possible GPU/copy-on-write issue")
        else:
            print(f"    l_out-14 not observed — only {len(l_out)} l_out tensors seen")
            print(f"    (write test skipped)")
    else:
        print("    Callback never fired — cb_eval not wired through in this build")

    # Cleanup
    _lib.llama_free(ctx)
    _lib.llama_free_model(model)

except Exception as e:
    import traceback
    print(f"\nERROR: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("VERDICT:")
n = len(observations)
l_out_count = len([o for o in observations if o.get('name', '').startswith('l_out-')])
if n > 0:
    print(f"  Callback fired {n} times — WIRED THROUGH")
    if l_out_count > 0:
        print(f"  l_out tensors found ({l_out_count}) — layer boundaries readable")
    else:
        print(f"  l_out tensors not found — naming convention differs from expected")
else:
    print("  Callback did not fire — low-level setup may need adjustment")
    print("  Or: this llama-cpp-python build may not wire cb_eval through")
print("=" * 60)
