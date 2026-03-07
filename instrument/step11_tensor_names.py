#!/usr/bin/env python3
"""
Step 11 — Tensor name dump on Qwen3-0.6B.

Identifies the exact naming convention for layer output tensors.
Runs one inference pass with cb_eval, collects all unique tensor
names, highlights layer boundary candidates.

Key question: are layer outputs named "l_out-N", "l_out+N",
"blk.N.ffn_out", or something else entirely?
"""
import sys
import io
import ctypes
import re

# Force UTF-8 stdout to handle any Cyrillic/Unicode in tensor names
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

MODEL_PATH = "D:/LMStudio/Models/lmstudio-community/Qwen3-0.6B-GGUF/Qwen3-0.6B-Q8_0.gguf"

import llama_cpp.llama_cpp as llama_module

print("=" * 60)
print("Step 11: Tensor name dump — Qwen3-0.6B")
print("=" * 60)

# ── Try to access underlying CDLL for ggml_get_name ──────────────
# llama_cpp.llama_cpp is a Python module. Internally it loads a CDLL
# (usually stored as module._lib). If accessible, we can call
# ggml_get_name directly without struct offset guessing.
internal_lib = getattr(llama_module, '_lib', None)
ggml_get_name_fn = None

print("\n[check] Internal lib access:")
if internal_lib is not None:
    print(f"  type: {type(internal_lib)}")
    if hasattr(internal_lib, 'ggml_get_name'):
        try:
            internal_lib.ggml_get_name.restype = ctypes.c_char_p
            internal_lib.ggml_get_name.argtypes = [ctypes.c_void_p]
            ggml_get_name_fn = internal_lib.ggml_get_name
            print("  [+] ggml_get_name wired via internal CDLL")
        except Exception as e:
            print(f"  [!] ggml_get_name setup failed: {e}")
    else:
        ggml_attrs = [x for x in dir(internal_lib) if 'ggml' in x.lower()]
        print(f"  [!] ggml_get_name not found ({len(ggml_attrs)} other ggml attrs)")
else:
    print("  [!] llama_module._lib not accessible")

if not ggml_get_name_fn:
    print("  Using struct offset scan fallback")

# ── Name validation ───────────────────────────────────────────────
# Valid tensor names look like: inp_tokens, l_out-0, Qcur, blk.0.attn_norm
NAME_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_\-+.\[\]/]*$')

def try_name_at(ptr, offset):
    """Read GGML_MAX_NAME (64) chars from ptr+offset, validate as tensor name."""
    try:
        raw = bytes((ctypes.c_char * 64).from_address(ptr + offset))
        null = raw.find(b'\x00')
        if null < 2:
            return None
        s = raw[:null].decode('ascii', errors='strict')
        if NAME_RE.match(s) and 2 <= len(s) <= 63:
            return s
    except Exception:
        pass
    return None

# ── Offsets to scan (name field estimated around 248-280 in struct) ──
# ggml_tensor layout (64-bit):
#   type(4) + pad(4) + buffer*(8) + ne[4](32) + nb[4](32) = 80
#   + op(4) + op_params[16](64) + flags(4) + pad(4) = 76  → total 156
#   + src[10]*(80) + view_src*(8) + view_offs(8) + data*(8) = 104 → total 260
#   + name[64] at ~260
OFFSETS_TO_TRY = list(range(160, 400, 8))

# ── Storage ───────────────────────────────────────────────────────
# Collect (offset → list_of_names) during first 50 callback calls for calibration
names_by_offset = {off: [] for off in OFFSETS_TO_TRY}
# Final confirmed names (one per tensor, in order)
names_confirmed = []
call_count = [0]
confirmed_offset = [None]  # set once calibration determines best offset

EVAL_CB = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_bool, ctypes.c_void_p)

@EVAL_CB
def cb(ptr, ask, _):
    if not ask and ptr:
        call_count[0] += 1
        c = call_count[0]

        if ggml_get_name_fn:
            # Clean path: use ggml_get_name
            try:
                raw = ggml_get_name_fn(ptr)
                name = raw.decode('utf-8', errors='replace') if raw else None
                names_confirmed.append(name or '(unnamed)')
            except Exception:
                names_confirmed.append('(cb_error)')

        else:
            # Offset scan path
            # Phase 1 (calls 1-50): scan all offsets to calibrate
            if c <= 50:
                for off in OFFSETS_TO_TRY:
                    n = try_name_at(ptr, off)
                    if n:
                        names_by_offset[off].append(n)

            # Commit to best offset after 20 calls
            if confirmed_offset[0] is None and c >= 20:
                best = max(OFFSETS_TO_TRY, key=lambda o: len(names_by_offset[o]))
                if len(names_by_offset[best]) >= 3:
                    confirmed_offset[0] = best
                else:
                    confirmed_offset[0] = -1  # give up

            # Phase 2: read name using confirmed offset
            if confirmed_offset[0] and confirmed_offset[0] > 0:
                name = try_name_at(ptr, confirmed_offset[0])
                names_confirmed.append(name or '(unnamed)')
            else:
                names_confirmed.append('(calibrating)')

    return True

# ── Load model ────────────────────────────────────────────────────
mp = llama_module.llama_model_default_params()
mp.n_gpu_layers = 0
model = llama_module.llama_load_model_from_file(MODEL_PATH.encode(), mp)
if not model:
    print("\nERROR: Model failed to load")
    sys.exit(1)

cp = llama_module.llama_context_default_params()
cp.n_ctx = 128
cp.n_batch = 64
cp.cb_eval = cb
cp.cb_eval_user_data = None
ctx = llama_module.llama_new_context_with_model(model, cp)
if not ctx:
    print("\nERROR: Context creation failed")
    sys.exit(1)

# ── Tokenize + decode ─────────────────────────────────────────────
toks = (ctypes.c_int32 * 64)()
vocab = llama_module.llama_model_get_vocab(model)
n_tok = llama_module.llama_tokenize(vocab, b"Hello", 5, toks, 64, True, False)
batch = llama_module.llama_batch_get_one(toks, n_tok)
ret = llama_module.llama_decode(ctx, batch)

print(f"\nTokens: {n_tok}, decode: {ret} (0=OK), callbacks fired: {call_count[0]}")

# ── Report offset calibration ─────────────────────────────────────
if not ggml_get_name_fn:
    print(f"\nOffset calibration (top hits from first 50 calls):")
    scored = sorted(OFFSETS_TO_TRY, key=lambda o: len(names_by_offset[o]), reverse=True)
    for off in scored[:10]:
        cnt = len(names_by_offset[off])
        if cnt == 0:
            break
        examples = names_by_offset[off][:5]
        print(f"  offset {off:4d}: {cnt:3d} valid names — {examples}")
    print(f"\nConfirmed offset: {confirmed_offset[0]}")

# ── Unique names ──────────────────────────────────────────────────
valid = [n for n in names_confirmed if n not in ('(unnamed)', '(calibrating)', '(cb_error)')]
uncaptured = len(names_confirmed) - len(valid)
unique = sorted(set(valid))

print(f"\nAll unique tensor names ({len(unique)}) [{uncaptured} uncaptured]:")
for name in unique:
    print(f"  {name!r}")

# ── Layer output analysis ─────────────────────────────────────────
print("\n--- Layer output candidates ---")
layer_out = [n for n in unique if 'l_out' in n.lower()]
if layer_out:
    print(f"  l_out pattern found ({len(layer_out)} tensors):")
    for n in sorted(layer_out):
        print(f"    {n!r}")
else:
    print("  No 'l_out' tensors — checking numbered patterns:")
    numbered = [n for n in unique if re.search(r'[-_.+]\d+$', n)]
    for n in sorted(numbered):
        print(f"    {n!r}")

    print("\n  All tensors with digits (possible layer-indexed):")
    with_digits = [n for n in unique if any(c.isdigit() for c in n)]
    for n in sorted(with_digits):
        print(f"    {n!r}")

# ── Residual stream candidates ────────────────────────────────────
print("\n--- Residual stream candidates (post-layer add) ---")
residual_keywords = ['l_out', 'residual', 'ffn_out', 'attn_out', 'out_norm', 'add']
for kw in residual_keywords:
    matches = [n for n in unique if kw in n.lower()]
    if matches:
        print(f"  [{kw}]: {sorted(matches)}")

# Cleanup
llama_module.llama_free(ctx)
llama_module.llama_free_model(model)

print("\n" + "=" * 60)
print("VERDICT:")
if unique:
    print(f"  {len(unique)} unique tensor names captured")
    layer_names = [n for n in unique if 'l_out' in n.lower()]
    if layer_names:
        print(f"  Layer output naming: {layer_names[0]!r} pattern confirmed")
        print(f"  Layer range: {sorted(layer_names)[0]!r} to {sorted(layer_names)[-1]!r}")
    else:
        numbered_pattern = [n for n in unique if re.search(r'[-_.]\d+$', n)]
        print(f"  No 'l_out' tensors — check numbered patterns above for layer markers")
else:
    print("  No tensor names captured — offset scan failed or callback not firing")
print("=" * 60)
