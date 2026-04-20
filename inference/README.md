# Exocortex Inference Wrapper — Layer B

## What This Is

A FastAPI wrapper around `llama-cpp-python` that replaces LM Studio as the inference backend for Agent Zero. This is the permanent inference intelligence layer — every research finding from the pondering architecture papers lives here.

## Two-Layer Architecture

**Layer A** (Agent Zero extensions): Pre/post-processing — BST, context pruner, EI, memory retrieval. Python code that runs *around* the LLM call.

**Layer B** (this wrapper): Inference-level intelligence — entropy monitoring, future SRGen token correction, SleepGate PI biasing, Knowledge Packs KV management. Code that runs *during* the LLM call.

## Quick Start

```bash
# Install dependencies (with GPU support)
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python fastapi uvicorn

# Edit config — set your model path
# CRITICAL: chat_format must match your model ("qwen" for Qwen family)
nano inference_config.json

# Run
python inference_wrapper.py --config inference_config.json

# Test
curl http://localhost:8080/health
curl http://localhost:8080/v1/models
```

## Agent Zero Configuration

Update Agent Zero's settings to point to this wrapper instead of LM Studio:

```
API URL: http://localhost:8080/v1
```

Zero other changes needed. The endpoint is OpenAI-compatible.

## Endpoints

### Standard (OpenAI-compatible)
- `POST /v1/chat/completions` — Chat completion (streaming + non-streaming)
- `GET /v1/models` — List available models

### Exocortex-specific
- `GET /health` — Health check
- `GET /v1/entropy/status` — Entropy monitoring status
- `GET /v1/kv/slots` — List pre-computed KV slots (future: Knowledge Packs)
- `POST /v1/kv/save` — Save model state as named KV slot

### Response Metadata
Non-streaming responses include an `exocortex` field:
```json
{
  "exocortex": {
    "entropy": {
      "total_tokens": 142,
      "mean_entropy": 2.3451,
      "max_entropy": 5.1203,
      "spike_count": 3,
      "spike_positions": [47, 89, 121]
    },
    "generation_time_ms": 4521.3
  }
}
```

Agent Zero ignores this field. The entropy dashboard reads it.

## What's Built vs. What's Stubbed

| Feature | Status | Paper |
|---|---|---|
| OpenAI-compatible serving | **Built** | — |
| Entropy monitoring (summary) | **Built** | All five papers |
| Per-token entropy logging | **Built** (needs `logits_all=True`) | SRGen, First Hallucination Tokens |
| KV slot save/load interface | **Stubbed** | Knowledge Packs |
| SRGen token correction | Future | SRGen (2510.02919) |
| SleepGate PI biasing | Future | SleepGate (2603.14517) |
| Cache Processor | Future | Bottlenecked Transformers (2505.16950) |
| Trajectory monitoring probe | Future | Streaming Detection (2601.02170) |

## Configuration

See `inference_config.json`. Key settings:

- `model.model_path`: Path to your GGUF file
- `model.chat_format`: **"qwen"** for Qwen family. CRITICAL — wrong format causes 6-7pp degradation (Knowledge Packs paper finding)
- `model.logits_all`: Set `true` to enable per-token entropy. Increases VRAM usage.
- `entropy_monitoring.enabled`: Master switch for entropy tracking
- `kv_slots.enabled`: Enable KV slot management (future)

## What Comes Next

1. Deploy and verify Agent Zero works identically
2. Enable `logits_all` and characterize Qwen3.5-27B entropy profile
3. Build entropy dashboard from JSONL traces
4. Implement KV slot save/load for Knowledge Packs
5. Add SRGen correction at entropy spike points
6. Add SleepGate soft attention biasing
