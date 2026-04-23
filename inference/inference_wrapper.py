"""
Exocortex Inference Wrapper — Layer B
=====================================
FastAPI wrapper around llama-cpp-python that serves as the permanent
inference intelligence layer for the Exocortex.

Layer A (Agent Zero extensions): pre/post-processing (BST, context pruner, EI)
Layer B (this wrapper): inference-level intelligence (entropy monitoring,
    future: SRGen, SleepGate, Cache Processor, Knowledge Packs)

Drop-in replacement for LM Studio. Agent Zero's HTTP client needs zero changes.

Usage:
    pip install llama-cpp-python[server] fastapi uvicorn
    python inference_wrapper.py --config inference_config.json

    Or with GPU support:
    CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python[server]
"""

import argparse
import json
import logging
import math
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncGenerator, Optional

import subprocess

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

# ──────────────────────────────────────────────────────────────────────
# Live generation state — updated by streaming/sync response generators
# ──────────────────────────────────────────────────────────────────────

_generation_state: dict = {
    "active": False,
    "request_id": None,
    "tokens_generated": 0,
    "started_at": None,
    "elapsed_s": 0.0,
    "tokens_per_second": 0.0,
}

# ──────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────

@dataclass
class ModelConfig:
    model_path: str = ""
    chat_format: str = "qwen"
    n_ctx: int = 32768
    n_gpu_layers: int = -1
    n_threads: int = 8
    n_batch: int = 512
    logits_all: bool = False
    verbose: bool = False
    type_k: int = None     # KV cache K type: None=default(f16), 2=q4_0, 8=q8_0
    type_v: int = None     # KV cache V type: None=default(f16), 2=q4_0, 8=q8_0

@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8080
    model_alias: str = "qwen3.5-27b"
    max_tokens_cap: int = 16384  # hard ceiling — prevents infinite <think> loops

@dataclass
class EntropyConfig:
    enabled: bool = True
    log_per_token: bool = False
    log_summary: bool = True
    log_file: str = "logs/entropy_trace.jsonl"

@dataclass
class KVSlotConfig:
    enabled: bool = False
    slot_directory: str = "kv_slots/"
    preload: list = field(default_factory=list)


def load_config(config_path: str) -> dict:
    with open(config_path, "r") as f:
        raw = json.load(f)
    return {
        "model": ModelConfig(**{k: v for k, v in raw.get("model", {}).items()}),
        "server": ServerConfig(**{k: v for k, v in raw.get("server", {}).items()}),
        "entropy": EntropyConfig(**{k: v for k, v in raw.get("entropy_monitoring", {}).items()}),
        "kv_slots": KVSlotConfig(**{k: v for k, v in raw.get("kv_slots", {}).items() if k != "preload"},
                                  preload=raw.get("kv_slots", {}).get("preload", [])),
    }


# ──────────────────────────────────────────────────────────────────────
# Entropy Monitor
# ──────────────────────────────────────────────────────────────────────

class EntropyMonitor:
    """Tracks per-token entropy during generation.
    
    This is the universal signal that connects all three intervention levels:
    - Level 1 (Token): SRGen-style entropy spike detection
    - Level 2 (Step): Prediction error at reasoning boundaries
    - Level 3 (Cache): Attention entropy for PI detection
    
    MVP: logs entropy values. Future: triggers interventions.
    """

    def __init__(self, config: EntropyConfig):
        self.config = config
        self.current_trace = []
        self.logger = logging.getLogger("entropy")

        if config.log_file:
            log_dir = Path(config.log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)

    def compute_entropy(self, logits: list[float]) -> float:
        """Compute Shannon entropy from logits (pre-softmax)."""
        # Stable softmax
        max_logit = max(logits)
        shifted = [l - max_logit for l in logits]
        exp_vals = [math.exp(l) for l in shifted]
        total = sum(exp_vals)
        probs = [e / total for e in exp_vals]

        entropy = 0.0
        for p in probs:
            if p > 1e-10:
                entropy -= p * math.log(p)
        return entropy

    def on_token(self, token_id: int, logits: Optional[list] = None):
        """Called for each generated token. Records entropy if logits available."""
        if logits is not None and self.config.enabled:
            entropy = self.compute_entropy(logits)
            self.current_trace.append({
                "token_id": token_id,
                "entropy": entropy,
                "timestamp": time.time(),
            })

            if self.config.log_per_token:
                self.logger.info(f"[ENTROPY] token={token_id} H={entropy:.4f}")

    def finalize(self, request_id: str) -> dict:
        """Called at end of generation. Returns summary and optionally logs."""
        trace = self.current_trace
        self.current_trace = []

        if not trace:
            return {"entropy_monitoring": "disabled_or_no_logits"}

        entropies = [t["entropy"] for t in trace]
        n = len(entropies)
        mean_h = sum(entropies) / n if n > 0 else 0
        max_h = max(entropies) if entropies else 0
        min_h = min(entropies) if entropies else 0

        # Detect spikes (tokens > mean + 2*std)
        if n > 1:
            variance = sum((h - mean_h) ** 2 for h in entropies) / n
            std_h = math.sqrt(variance)
            spike_threshold = mean_h + 2 * std_h
            spikes = [i for i, h in enumerate(entropies) if h > spike_threshold]
        else:
            std_h = 0
            spikes = []

        summary = {
            "request_id": request_id,
            "total_tokens": n,
            "mean_entropy": round(mean_h, 4),
            "max_entropy": round(max_h, 4),
            "min_entropy": round(min_h, 4),
            "std_entropy": round(std_h, 4),
            "spike_count": len(spikes),
            "spike_positions": spikes[:10],  # cap at 10 for log readability
        }

        if self.config.log_summary:
            self.logger.info(
                f"[ENTROPY-SUMMARY] req={request_id} tokens={n} "
                f"mean={mean_h:.4f} max={max_h:.4f} spikes={len(spikes)}"
            )

        # Write full trace to JSONL if configured
        if self.config.log_file:
            try:
                with open(self.config.log_file, "a") as f:
                    f.write(json.dumps({
                        "summary": summary,
                        "trace": trace if self.config.log_per_token else None,
                    }) + "\n")
            except Exception as e:
                self.logger.warning(f"Failed to write entropy trace: {e}")

        return summary


# ──────────────────────────────────────────────────────────────────────
# KV Slot Manager (future: Knowledge Packs)
# ──────────────────────────────────────────────────────────────────────

class KVSlotManager:
    """Manages pre-computed KV cache states for zero-token knowledge delivery.
    
    Future implementation. MVP: stub with save/load interface defined.
    
    When implemented:
    - Pre-compute KV cache for BST enrichment templates
    - Save to disk as named slots
    - Load before query to inject knowledge without spending tokens
    - Critical: chat template must be applied before pre-computing
    """

    def __init__(self, config: KVSlotConfig):
        self.config = config
        self.slots = {}
        self.logger = logging.getLogger("kv_slots")

        if config.enabled:
            slot_dir = Path(config.slot_directory)
            slot_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"[KV-SLOTS] Slot directory: {slot_dir}")

    def save_slot(self, name: str, state) -> bool:
        """Save a model state as a named slot. Returns True on success."""
        if not self.config.enabled:
            return False
        # Future: serialize state to disk
        self.logger.info(f"[KV-SLOTS] save_slot({name}) — not yet implemented")
        return False

    def load_slot(self, name: str):
        """Load a named slot. Returns state or None."""
        if not self.config.enabled:
            return None
        # Future: deserialize state from disk
        self.logger.info(f"[KV-SLOTS] load_slot({name}) — not yet implemented")
        return None

    def list_slots(self) -> list[str]:
        """List available slot names."""
        if not self.config.enabled:
            return []
        slot_dir = Path(self.config.slot_directory)
        return [f.stem for f in slot_dir.glob("*.kvslot")] if slot_dir.exists() else []


# ──────────────────────────────────────────────────────────────────────
# FastAPI Application
# ──────────────────────────────────────────────────────────────────────

def create_app(config: dict) -> FastAPI:
    """Create the FastAPI application with the Llama model loaded."""

    app = FastAPI(
        title="Exocortex Inference Wrapper",
        description="Layer B — Inference intelligence layer for the Exocortex",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Model Loading ─────────────────────────────────────────────
    model_cfg: ModelConfig = config["model"]
    server_cfg: ServerConfig = config["server"]
    entropy_cfg: EntropyConfig = config["entropy"]
    kv_cfg: KVSlotConfig = config["kv_slots"]

    logger = logging.getLogger("inference")
    logger.info(f"Loading model: {model_cfg.model_path}")
    logger.info(f"Chat format: {model_cfg.chat_format}")
    logger.info(f"Context: {model_cfg.n_ctx}")

    from llama_cpp import Llama

    # Model state management for VRAM safety
    model_state = {"loaded": False, "llm": None}

    def load_model():
        """Load the model into VRAM."""
        logger.info(f"Loading model: {model_cfg.model_path}")
        logger.info(f"KV cache: type_k={model_cfg.type_k} type_v={model_cfg.type_v}")
        kwargs = dict(
            model_path=model_cfg.model_path,
            chat_format=model_cfg.chat_format,
            n_ctx=model_cfg.n_ctx,
            n_gpu_layers=model_cfg.n_gpu_layers,
            n_threads=model_cfg.n_threads,
            n_batch=model_cfg.n_batch,
            logits_all=model_cfg.logits_all,
            verbose=model_cfg.verbose,
        )
        if model_cfg.type_k is not None:
            kwargs["type_k"] = model_cfg.type_k
        if model_cfg.type_v is not None:
            kwargs["type_v"] = model_cfg.type_v
        model_state["llm"] = Llama(**kwargs)
        model_state["loaded"] = True
        logger.info("Model loaded.")

    def unload_model():
        """Unload the model to free VRAM."""
        if model_state["llm"] is not None:
            del model_state["llm"]
            model_state["llm"] = None
            model_state["loaded"] = False
            # Force garbage collection to release VRAM
            import gc
            gc.collect()
            try:
                import torch
                torch.cuda.empty_cache()
            except ImportError:
                pass
            logger.info("Model unloaded. VRAM freed.")

    def get_llm():
        """Get the model, raising 503 if unloaded."""
        if not model_state["loaded"] or model_state["llm"] is None:
            raise HTTPException(
                status_code=503,
                detail="Model not loaded. POST /v1/model/load to reload."
            )
        return model_state["llm"]

    # Initial load
    load_model()

    entropy_monitor = EntropyMonitor(entropy_cfg)
    kv_manager = KVSlotManager(kv_cfg)

    # Activity tracking for live dashboard
    activity = {
        "state": "idle",          # idle, generating, error
        "current_request_id": None,
        "requests_total": 0,
        "tokens_generated": 0,
        "active_since": None,
        "last_request_time": None,
        "last_gen_time_ms": 0,
        "last_prompt_tokens": 0,
        "last_completion_tokens": 0,
        "errors_total": 0,
        "last_error": None,
    }

    logger.info(f"Model loaded. Serving on {server_cfg.host}:{server_cfg.port}")
    logger.info(f"Entropy monitoring: {'enabled' if entropy_cfg.enabled else 'disabled'}")
    logger.info(f"KV slots: {'enabled' if kv_cfg.enabled else 'disabled'}")

    # ── Endpoints ─────────────────────────────────────────────────

    @app.get("/v1/models")
    async def list_models():
        """OpenAI-compatible model listing."""
        return {
            "object": "list",
            "data": [
                {
                    "id": server_cfg.model_alias,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "exocortex",
                }
            ],
        }

    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request):
        """OpenAI-compatible chat completion endpoint.
        
        Drop-in replacement for LM Studio's endpoint.
        Agent Zero's HTTP client needs zero changes.
        """
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")

        messages = body.get("messages", [])
        if not messages:
            raise HTTPException(status_code=400, detail="messages is required")

        # Extract parameters with OpenAI-compatible defaults
        temperature = body.get("temperature", 0.7)
        top_p = body.get("top_p", 0.95)
        max_tokens = min(body.get("max_tokens", 4096), server_cfg.max_tokens_cap)
        stream = body.get("stream", False)
        stop = body.get("stop", None)
        presence_penalty = body.get("presence_penalty", 0.0)
        frequency_penalty = body.get("frequency_penalty", 0.0)

        request_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

        llm = get_llm()

        # Pre-check context window before committing to a streaming response.
        # Once StreamingResponse is returned the HTTP 200 is sent and we can't
        # return a 4xx — the connection just crashes, which looks like a backend-
        # down failure to the agent.  Check here instead.
        ctx_size = llm.n_ctx()
        prompt_tokens = sum(
            len(llm.tokenize((m.get("content", "") or "").encode())) + 8
            for m in messages
        ) + 16  # global template overhead
        if prompt_tokens > ctx_size - 256:
            print(
                f"[WRAPPER] Context window pre-check failed: ~{prompt_tokens} prompt tokens, "
                f"context is {ctx_size}. Returning 400.",
                flush=True,
            )
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "message": (
                            f"Prompt too long: ~{prompt_tokens} tokens exceeds "
                            f"context window of {ctx_size}. "
                            "Agent Zero should compress history before retrying."
                        ),
                        "type": "context_length_exceeded",
                        "code": "context_length_exceeded",
                        "param": "messages",
                    }
                },
            )

        activity["state"] = "generating"
        activity["current_request_id"] = request_id
        activity["active_since"] = time.time()

        try:
            if stream:
                return StreamingResponse(
                    _stream_response(
                        llm, messages, temperature, top_p, max_tokens,
                        stop, presence_penalty, frequency_penalty,
                        request_id, server_cfg.model_alias, entropy_monitor
                    ),
                    media_type="text/event-stream",
                )
            else:
                result = _sync_response(
                    llm, messages, temperature, top_p, max_tokens,
                    stop, presence_penalty, frequency_penalty,
                    request_id, server_cfg.model_alias, entropy_monitor
                )
                activity["requests_total"] += 1
                activity["last_request_time"] = time.time()
                activity["state"] = "idle"
                return result
        except Exception as e:
            activity["state"] = "error"
            activity["errors_total"] += 1
            activity["last_error"] = str(e)[:200]
            raise

    @app.get("/v1/entropy/status")
    async def entropy_status():
        """Check entropy monitoring status. Exocortex-specific endpoint."""
        return {
            "enabled": entropy_cfg.enabled,
            "log_per_token": entropy_cfg.log_per_token,
            "log_file": entropy_cfg.log_file,
        }

    @app.get("/v1/kv/slots")
    async def list_kv_slots():
        """List available KV slots. Exocortex-specific endpoint."""
        return {
            "enabled": kv_cfg.enabled,
            "slots": kv_manager.list_slots(),
        }

    @app.post("/v1/kv/save")
    async def save_kv_slot(request: Request):
        """Save current model state as a named KV slot. Exocortex-specific."""
        body = await request.json()
        name = body.get("name")
        if not name:
            raise HTTPException(status_code=400, detail="name is required")
        
        state = get_llm().save_state()
        success = kv_manager.save_slot(name, state)
        return {"success": success, "name": name}

    @app.get("/health")
    async def health():
        return {
            "status": "ok" if model_state["loaded"] else "model_unloaded",
            "model": server_cfg.model_alias,
            "model_loaded": model_state["loaded"],
        }

    @app.post("/v1/model/unload")
    async def model_unload():
        """Unload model to free VRAM. Use before gaming or other GPU tasks.
        
        The wrapper stays running and returns 503 on inference requests
        until the model is reloaded via POST /v1/model/load.
        """
        if not model_state["loaded"]:
            return {"status": "already_unloaded"}
        unload_model()
        return {"status": "unloaded", "message": "VRAM freed. POST /v1/model/load to reload."}

    @app.post("/v1/model/load")
    async def model_load():
        """Reload the model into VRAM after unloading."""
        if model_state["loaded"]:
            return {"status": "already_loaded"}
        try:
            load_model()
            return {"status": "loaded", "model": server_cfg.model_alias}
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "detail": str(e)}
            )

    @app.get("/v1/model/status")
    async def model_status():
        """Check model load status and VRAM state."""
        return {
            "loaded": model_state["loaded"],
            "model": server_cfg.model_alias,
            "kv_cache": {
                "type_k": model_cfg.type_k,
                "type_v": model_cfg.type_v,
            },
            "context_size": model_cfg.n_ctx,
        }

    @app.get("/v1/activity")
    async def get_activity():
        """Live activity status for the dashboard."""
        elapsed = None
        if activity["state"] == "generating" and activity["active_since"]:
            elapsed = round(time.time() - activity["active_since"], 1)
        return {
            "state": activity["state"],
            "model_loaded": model_state["loaded"],
            "current_request_id": activity["current_request_id"],
            "generating_for_seconds": elapsed,
            "requests_total": activity["requests_total"],
            "tokens_generated": activity["tokens_generated"],
            "last_gen_time_ms": activity["last_gen_time_ms"],
            "last_prompt_tokens": activity["last_prompt_tokens"],
            "last_completion_tokens": activity["last_completion_tokens"],
            "errors_total": activity["errors_total"],
            "last_error": activity["last_error"],
            "timestamp": time.time(),
        }

    @app.get("/v1/status")
    async def live_status():
        """Live generation status — poll this to see what the wrapper is doing."""
        gpu: dict = {}
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=utilization.gpu,utilization.memory,memory.used,memory.free,temperature.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True, text=True, timeout=3,
            )
            vals = [v.strip() for v in result.stdout.strip().split(",")]
            if len(vals) == 5:
                gpu = {
                    "utilization_pct": int(vals[0]),
                    "memory_utilization_pct": int(vals[1]),
                    "memory_used_mb": int(vals[2]),
                    "memory_free_mb": int(vals[3]),
                    "temperature_c": int(vals[4]),
                }
        except Exception as exc:
            gpu = {"error": str(exc)}

        state = dict(_generation_state)
        if state["active"] and state["started_at"]:
            elapsed = round(time.time() - state["started_at"], 1)
            state["elapsed_s"] = elapsed
            state["tokens_per_second"] = round(state["tokens_generated"] / elapsed, 1) if elapsed > 0 else 0.0

        return {
            "model": server_cfg.model_alias,
            "model_loaded": model_state["loaded"],
            "generation": state,
            "gpu": gpu,
        }

    return app


# ──────────────────────────────────────────────────────────────────────
# Response Generators
# ──────────────────────────────────────────────────────────────────────

def _sync_response(
    llm, messages, temperature, top_p, max_tokens,
    stop, presence_penalty, frequency_penalty,
    request_id, model_alias, entropy_monitor
):
    """Generate a non-streaming response."""
    t_start = time.time()

    _generation_state.update({
        "active": True,
        "request_id": request_id,
        "tokens_generated": 0,
        "started_at": t_start,
        "elapsed_s": 0.0,
        "tokens_per_second": 0.0,
    })

    try:
        result = llm.create_chat_completion(
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            stop=stop,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            stream=False,
        )

        t_end = time.time()
        usage = result.get("usage", {})
        completion_tokens = usage.get("completion_tokens", 0)
        elapsed = t_end - t_start

        _generation_state["tokens_generated"] = completion_tokens
        _generation_state["elapsed_s"] = round(elapsed, 1)
        _generation_state["tokens_per_second"] = round(completion_tokens / elapsed, 1) if elapsed > 0 else 0.0

    finally:
        _generation_state["active"] = False

    # Extract the response
    choice = result["choices"][0] if result.get("choices") else {}
    message = choice.get("message", {})
    finish_reason = choice.get("finish_reason", "stop")

    entropy_summary = entropy_monitor.finalize(request_id)

    response = {
        "id": request_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model_alias,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": message.get("content", ""),
                },
                "finish_reason": finish_reason,
            }
        ],
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        },
        "exocortex": {
            "entropy": entropy_summary,
            "generation_time_ms": round((t_end - t_start) * 1000, 1),
        },
    }

    return JSONResponse(content=response)


async def _stream_response(
    llm, messages, temperature, top_p, max_tokens,
    stop, presence_penalty, frequency_penalty,
    request_id, model_alias, entropy_monitor
) -> AsyncGenerator[str, None]:
    """Generate a streaming response (SSE format)."""

    t_start = time.time()
    token_count = 0

    _generation_state.update({
        "active": True,
        "request_id": request_id,
        "tokens_generated": 0,
        "started_at": t_start,
        "elapsed_s": 0.0,
        "tokens_per_second": 0.0,
    })

    try:
        stream = llm.create_chat_completion(
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            stop=stop,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            stream=True,
        )

        for chunk in stream:
            token_count += 1
            elapsed = time.time() - t_start
            _generation_state["tokens_generated"] = token_count
            _generation_state["elapsed_s"] = round(elapsed, 1)
            _generation_state["tokens_per_second"] = round(token_count / elapsed, 1) if elapsed > 0 else 0.0

            choice = chunk["choices"][0] if chunk.get("choices") else {}
            delta = choice.get("delta", {})
            finish_reason = choice.get("finish_reason")

            sse_data = {
                "id": request_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model_alias,
                "choices": [
                    {
                        "index": 0,
                        "delta": delta,
                        "finish_reason": finish_reason,
                    }
                ],
            }

            yield f"data: {json.dumps(sse_data)}\n\n"

        # Final entropy summary as a non-standard SSE event
        entropy_summary = entropy_monitor.finalize(request_id)
        if entropy_summary.get("total_tokens", 0) > 0:
            yield f"data: {json.dumps({'exocortex_entropy': entropy_summary})}\n\n"

        yield "data: [DONE]\n\n"

    finally:
        _generation_state["active"] = False


# ──────────────────────────────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Exocortex Inference Wrapper — Layer B"
    )
    parser.add_argument(
        "--config", type=str, default="inference_config.json",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--host", type=str, default=None,
        help="Override server host"
    )
    parser.add_argument(
        "--port", type=int, default=None,
        help="Override server port"
    )
    args = parser.parse_args()

    # Logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("inference")

    # Load config
    config_path = args.config
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        logger.info("Create inference_config.json or specify --config path")
        sys.exit(1)

    config = load_config(config_path)

    # CLI overrides
    if args.host:
        config["server"].host = args.host
    if args.port:
        config["server"].port = args.port

    # Validate model path
    if not os.path.exists(config["model"].model_path):
        logger.error(f"Model file not found: {config['model'].model_path}")
        logger.info("Update model_path in inference_config.json")
        sys.exit(1)

    # Create and run
    app = create_app(config)

    logger.info("=" * 60)
    logger.info("  EXOCORTEX INFERENCE WRAPPER -- Layer B")
    logger.info(f"  Model: {config['model'].model_path}")
    logger.info(f"  Chat format: {config['model'].chat_format}")
    logger.info(f"  Context: {config['model'].n_ctx}")
    logger.info(f"  Endpoint: http://{config['server'].host}:{config['server'].port}/v1/chat/completions")
    logger.info(f"  KV cache: type_k={config['model'].type_k} type_v={config['model'].type_v}")
    logger.info(f"  Entropy: {'ON' if config['entropy'].enabled else 'OFF'}")
    logger.info(f"  KV Slots: {'ON' if config['kv_slots'].enabled else 'OFF'}")
    logger.info(f"  Model mgmt: /v1/model/unload | /v1/model/load")
    logger.info("=" * 60)

    uvicorn.run(
        app,
        host=config["server"].host,
        port=config["server"].port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
