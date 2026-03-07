#!/usr/bin/env python3
"""
read_activations.py — Extract residual stream activations from Qwen3-0.6B.

Registers cb_eval callback, runs one forward pass, captures l_out tensor
values at specified layer indices into numpy arrays.

Usage as library:
    from read_activations import read_activations
    result = read_activations("Why does getting this right matter?")
    # result = {9:  np.ndarray([n_embd], float32),
    #           14: np.ndarray([n_embd], float32),
    #           18: np.ndarray([n_embd], float32)}

Usage as script:
    python3 read_activations.py "Why does getting this right matter?"
    python3 read_activations.py "pip install rich" --layers 9,14,18
    python3 read_activations.py "Question A" --compare "Question B"
"""

import sys
import io
import ctypes
import re
import numpy as np

# UTF-8 stdout — tensor names may contain Unicode
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

MODEL_PATH = "D:/LMStudio/Models/lmstudio-community/Qwen3-0.6B-GGUF/Qwen3-0.6B-Q8_0.gguf"

import llama_cpp.llama_cpp as _lib

# ── Confirmed struct offsets (Step 11 empirical validation) ──────────────────
# ggml_tensor layout (64-bit):
#   type(4) + pad(4) + buffer*(8) + ne[4](32) + nb[4](32)
#   + op(4) + op_params[16](64) + flags(4) + pad(4) + src[10]*(80)
#   + view_src*(8) + view_offs(8) + data*(8) + name[64]
TYPE_OFFSET     = 0    # int32_t — GGML_TYPE_F32=0, F16=1, etc.
NE0_OFFSET      = 16   # int64_t ne[0] — innermost dim (n_embd for l_out)
NE1_OFFSET      = 24   # int64_t ne[1] — second dim (n_tokens for l_out)
DATA_PTR_OFFSET = 248  # void* data — pointer to tensor data buffer
NAME_OFFSET     = 256  # char name[64] — null-terminated tensor name

GGML_TYPE_F32 = 0

NAME_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_\-+.\[\]/]*$')

# ── Callback type ─────────────────────────────────────────────────────────────
_EVAL_CB = ctypes.CFUNCTYPE(
    ctypes.c_bool,
    ctypes.c_void_p,   # tensor ptr
    ctypes.c_bool,     # ask
    ctypes.c_void_p,   # user_data
)


def _read_name(ptr: int) -> str | None:
    """Read tensor name from ggml_tensor struct at confirmed offset 256."""
    try:
        raw = bytes((ctypes.c_char * 64).from_address(ptr + NAME_OFFSET))
        null = raw.find(b'\x00')
        if null < 1:
            return None
        s = raw[:null].decode('ascii', errors='strict')
        return s if NAME_RE.match(s) and len(s) <= 63 else None
    except Exception:
        return None


def read_activations(
    text: str,
    target_layers: list[int] | None = None,
    model_path: str = MODEL_PATH,
    pool: str = 'mean',
) -> dict[int, np.ndarray]:
    """
    Run one forward pass on Qwen3-0.6B, capture l_out tensors at target layers.

    Args:
        text:          Input text
        target_layers: Layer indices to capture (default [9, 14, 18])
        model_path:    Path to GGUF file
        pool:          'mean' (mean across token positions, recommended)
                       'last' (last token only — causal LM convention)
                       'full' (full [n_tokens, n_embd] array, no pooling)

    Returns:
        dict mapping layer_idx → np.ndarray (float32)
        Shape: [n_embd] for mean/last, [n_tokens, n_embd] for full
        Only contains entries for layers where capture succeeded.

    Raises:
        RuntimeError on model load failure or decode failure.
    """
    if target_layers is None:
        target_layers = [9, 14, 18]

    # Map name → layer index for O(1) lookup in callback
    target_names: dict[str, int] = {f'l_out-{n}': n for n in target_layers}
    captures: dict[int, np.ndarray] = {}
    capture_errors: dict[int, str] = {}

    prompt_bytes = text.encode('utf-8')

    @_EVAL_CB
    def _cb(tensor_ptr: int, ask: bool, _: int) -> bool:
        """Fires once per graph node per forward pass."""
        if ask or not tensor_ptr:
            return True

        name = _read_name(tensor_ptr)
        if not name or name not in target_names:
            return True

        layer_idx = target_names[name]
        if layer_idx in captures or layer_idx in capture_errors:
            return True  # already captured this layer

        try:
            # Verify F32 — on CPU l_out should always be F32
            ggml_type = ctypes.c_int32.from_address(tensor_ptr + TYPE_OFFSET).value
            if ggml_type != GGML_TYPE_F32:
                capture_errors[layer_idx] = f'type={ggml_type} (expected F32=0)'
                return True

            # Read tensor shape from struct
            ne0 = ctypes.c_int64.from_address(tensor_ptr + NE0_OFFSET).value  # n_embd
            ne1 = ctypes.c_int64.from_address(tensor_ptr + NE1_OFFSET).value  # n_tokens

            if ne0 <= 0 or ne1 <= 0 or ne0 > 32768 or ne1 > 8192:
                capture_errors[layer_idx] = f'shape sanity fail: ne0={ne0}, ne1={ne1}'
                return True

            # Read data pointer from struct
            data_ptr = ctypes.c_void_p.from_address(tensor_ptr + DATA_PTR_OFFSET).value
            if not data_ptr or data_ptr < 0x10000:
                capture_errors[layer_idx] = f'bad data_ptr: {data_ptr}'
                return True

            # Read all floats and copy immediately (ptr only valid during callback)
            n_floats = int(ne0 * ne1)
            raw_floats = (ctypes.c_float * n_floats).from_address(data_ptr)
            data = np.frombuffer(raw_floats, dtype=np.float32).reshape(ne1, ne0).copy()
            # data shape: [n_tokens, n_embd]

            if pool == 'mean':
                captures[layer_idx] = data.mean(axis=0)           # [n_embd]
            elif pool == 'last':
                captures[layer_idx] = data[-1].copy()             # [n_embd]
            else:
                captures[layer_idx] = data                        # [n_tokens, n_embd]

        except Exception as ex:
            capture_errors[layer_idx] = str(ex)

        return True  # always continue computation

    # ── Load model ────────────────────────────────────────────────────────────
    mp = _lib.llama_model_default_params()
    mp.n_gpu_layers = 0  # CPU only for cb_eval write access

    model = _lib.llama_load_model_from_file(model_path.encode('utf-8'), mp)
    if not model:
        raise RuntimeError(f'Failed to load model: {model_path}')

    # ── Create context with callback registered ───────────────────────────────
    cp = _lib.llama_context_default_params()
    cp.n_ctx = 512
    cp.n_batch = 512
    cp.cb_eval = _cb
    cp.cb_eval_user_data = None

    ctx = _lib.llama_new_context_with_model(model, cp)
    if not ctx:
        _lib.llama_free_model(model)
        raise RuntimeError('Failed to create context')

    # ── Tokenize ──────────────────────────────────────────────────────────────
    max_tokens = 512
    toks = (ctypes.c_int32 * max_tokens)()
    vocab = _lib.llama_model_get_vocab(model)
    n_tok = _lib.llama_tokenize(
        vocab, prompt_bytes, len(prompt_bytes),
        toks, max_tokens, True, False,  # add_special=True, parse_special=False
    )
    if n_tok <= 0:
        _lib.llama_free(ctx)
        _lib.llama_free_model(model)
        raise RuntimeError(f'Tokenization failed (returned {n_tok})')

    # ── Forward pass ─────────────────────────────────────────────────────────
    batch = _lib.llama_batch_get_one(toks, n_tok)
    ret = _lib.llama_decode(ctx, batch)

    # ── Cleanup ───────────────────────────────────────────────────────────────
    _lib.llama_free(ctx)
    _lib.llama_free_model(model)

    if ret != 0:
        raise RuntimeError(f'llama_decode failed: {ret}')

    if capture_errors:
        for layer_idx, err in capture_errors.items():
            print(f'  [warn] l_out-{layer_idx} capture error: {err}', file=sys.stderr)

    return captures


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


# ── CLI ───────────────────────────────────────────────────────────────────────

def _print_capture(layer_idx: int, arr: np.ndarray) -> None:
    if arr.ndim == 1:
        print(f'  l_out-{layer_idx}: shape={arr.shape}  norm={np.linalg.norm(arr):.4f}'
              f'  mean={arr.mean():.4f}  std={arr.std():.4f}')
        print(f'    first 6: {arr[:6]}')
    else:
        print(f'  l_out-{layer_idx}: shape={arr.shape} (full, no pooling)')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Read Qwen3-0.6B activation tensors')
    parser.add_argument('text', help='Input text')
    parser.add_argument('--layers', default='9,14,18',
                        help='Comma-separated layer indices (default: 9,14,18)')
    parser.add_argument('--pool', default='mean', choices=['mean', 'last', 'full'],
                        help='Token pooling strategy (default: mean)')
    parser.add_argument('--compare', metavar='TEXT2',
                        help='Second text — compare activation geometry at each layer')
    args = parser.parse_args()

    layers = [int(x.strip()) for x in args.layers.split(',')]

    print(f'Input A: {args.text!r}')
    print(f'Layers:  {layers}')
    print(f'Pooling: {args.pool}')
    print()

    result_a = read_activations(args.text, target_layers=layers, pool=args.pool)

    print(f'Captured {len(result_a)}/{len(layers)} layers:')
    for li in sorted(result_a):
        _print_capture(li, result_a[li])

    if args.compare:
        print(f'\nInput B: {args.compare!r}')
        result_b = read_activations(args.compare, target_layers=layers, pool=args.pool)

        print(f'Captured {len(result_b)}/{len(layers)} layers')
        for li in sorted(result_b):
            _print_capture(li, result_b[li])

        print(f'\n{"─"*50}')
        print('Layer-by-layer geometry comparison (A vs B):')
        print(f'  {"Layer":<10} {"Cosine sim":>12} {"L2 dist":>10} {"Signal"}')
        print(f'  {"─"*48}')
        for li in sorted(layers):
            if li not in result_a or li not in result_b:
                print(f'  l_out-{li:<4}  (missing from one result)')
                continue
            a, b = result_a[li], result_b[li]
            cos = cosine_sim(a, b)
            l2 = float(np.linalg.norm(a - b))
            # Signal: how different are these representations?
            signal = 'SIMILAR' if cos > 0.98 else ('DISTINCT' if cos < 0.90 else 'moderate')
            print(f'  l_out-{li:<4}  {cos:>12.6f}  {l2:>10.4f}  {signal}')

        print()
        print('Interpretation:')
        print('  cosine ~1.0 → same semantic direction at this layer')
        print('  cosine ~0.9 → moderate distinction')
        print('  cosine <0.8 → strong geometric separation')
