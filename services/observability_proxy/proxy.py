"""
Agent Observability Proxy — Phase 1 (proxy core)
=================================================
Spec: specs/AGENT_OBSERVABILITY_PROXY.md

A transparent OpenAI-compatible proxy. An agent points its LLM endpoint at
    http://127.0.0.1:1240/v1/<agent>
instead of the real upstream. We forward verbatim, tee a copy of the exchange
into a bounded ring buffer, and expose it for observers.

Design constraints taken from the spec, restated here because they are the
correctness conditions:

  * TRANSPARENT. The agent's bytes are not altered, reordered, or delayed.
    Streaming is passed through chunk-by-chunk as it arrives; capture happens
    on a copy. If capture raises, the agent still gets its tokens.
  * BOUNDED. Ring buffer is capped by turns AND bytes AND age.
  * LOCAL. Binds 127.0.0.1 only. Nothing leaves the machine.

Phase 1 scope: forwarding, token counting, tool-call extraction, ring buffer,
plus plain HTTP inspection endpoints under /_obs/ so this is verifiable before
the MCP layer (Phase 2) exists.

Run:  python proxy.py --config config.yaml
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

import httpx
import uvicorn
import yaml
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

# ── Think-block patterns, per model family ───────────────────────────────────
# Extraction is best-effort and never fatal: an unknown family just means the
# reasoning trace stays folded into content.
_THINK_PATTERNS = {
    "qwen3.8": r"<think>(.*?)</think>",
    "ornith": r"<think>(.*?)</think>",
    "deepseek": r"<think>(.*?)</think>",
    "_default": r"<think>(.*?)</think>",
}


def _extract_think(text: str, family: str) -> tuple[str, str]:
    """Return (visible_text, thinking). Never raises."""
    try:
        pat = _THINK_PATTERNS.get(family, _THINK_PATTERNS["_default"])
        blocks = re.findall(pat, text or "", flags=re.DOTALL)
        if not blocks:
            return text or "", ""
        visible = re.sub(pat, "", text or "", flags=re.DOTALL).strip()
        return visible, "\n\n".join(b.strip() for b in blocks)
    except Exception:
        return text or "", ""


@dataclass
class ToolCallRecord:
    name: str = ""
    arguments: str = ""
    call_id: str = ""


@dataclass
class Turn:
    agent: str
    ts: float
    model: str = ""
    stream: bool = False
    # request side
    n_messages: int = 0
    n_tools_offered: int = 0
    tool_schema_bytes: int = 0
    last_user_preview: str = ""
    # response side
    content: str = ""
    thinking: str = ""
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    finish_reason: str = ""
    # metrics
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = 0
    ttft_ms: Optional[float] = None
    total_ms: Optional[float] = None
    upstream_status: int = 0
    error: str = ""
    # Streaming upstreams omit `usage` unless the CALLER sets
    # stream_options.include_usage. We do not inject that (it would alter the
    # agent's request), so on the streaming path token counts arrive as 0.
    # These are the raw measurables we can honestly record instead. They are
    # NOT token counts and must never be presented as such.
    completion_deltas: int = 0
    prompt_chars: int = 0

    def approx_bytes(self) -> int:
        return len(self.content) + len(self.thinking) + 512

    def to_public(self, include_thinking: bool = True) -> dict:
        d = asdict(self)
        if not include_thinking:
            d.pop("thinking", None)
        return d


class RingBuffer:
    """Bounded by turn count, total bytes, and age. All three enforced."""

    def __init__(self, max_turns: int, max_memory_mb: int, max_age_hours: float):
        self.max_turns = max_turns
        self.max_bytes = max_memory_mb * 1024 * 1024
        self.max_age = max_age_hours * 3600
        self._turns: deque[Turn] = deque()
        self._bytes = 0
        self._lock = asyncio.Lock()

    async def add(self, turn: Turn) -> None:
        async with self._lock:
            self._turns.append(turn)
            self._bytes += turn.approx_bytes()
            self._evict()

    def _evict(self) -> None:
        now = time.time()
        while self._turns and (
            len(self._turns) > self.max_turns
            or self._bytes > self.max_bytes
            or (now - self._turns[0].ts) > self.max_age
        ):
            old = self._turns.popleft()
            self._bytes -= old.approx_bytes()

    def recent(self, agent: Optional[str], n: int) -> list[Turn]:
        items = [t for t in self._turns if agent is None or t.agent == agent]
        return items[-n:]

    def stats(self) -> dict:
        return {"turns_held": len(self._turns), "bytes_held": self._bytes}


class Capture:
    """Builds a Turn from a request/response pair. Never raises into the path."""

    def __init__(self, agent: str, family: str, body: dict):
        self.turn = Turn(agent=agent, ts=time.time())
        self.family = family
        self._t0 = time.perf_counter()
        self._chunks: list[str] = []
        try:
            self.turn.model = body.get("model", "") or ""
            self.turn.stream = bool(body.get("stream"))
            msgs = body.get("messages") or []
            self.turn.n_messages = len(msgs)
            tools = body.get("tools") or []
            self.turn.n_tools_offered = len(tools)
            self.turn.tool_schema_bytes = len(json.dumps(tools)) if tools else 0
            for m in reversed(msgs):
                if m.get("role") == "user":
                    c = m.get("content")
                    if isinstance(c, list):  # multimodal
                        c = " ".join(
                            p.get("text", "") for p in c if isinstance(p, dict)
                        )
                    self.turn.last_user_preview = (str(c or ""))[:300]
                    break
            for m in msgs:
                c = m.get("content")
                if isinstance(c, str):
                    self.turn.prompt_chars += len(c)
        except Exception as e:
            self.turn.error = f"request capture: {e!r}"

    def mark_first_token(self) -> None:
        if self.turn.ttft_ms is None:
            self.turn.ttft_ms = (time.perf_counter() - self._t0) * 1000

    def feed_sse_line(self, line: str) -> None:
        """Consume one raw SSE line from the upstream stream."""
        try:
            if not line.startswith("data:"):
                return
            payload = line[5:].strip()
            if not payload or payload == "[DONE]":
                return
            obj = json.loads(payload)
            for ch in obj.get("choices") or []:
                delta = ch.get("delta") or {}
                piece = delta.get("content")
                if piece:
                    self.mark_first_token()
                    self.turn.completion_deltas += 1
                    self._chunks.append(piece)
                rc = delta.get("reasoning_content")
                if rc:
                    self.mark_first_token()
                    self.turn.completion_deltas += 1
                    self.turn.thinking += rc
                for tc in delta.get("tool_calls") or []:
                    self._merge_tool_call(tc)
                if ch.get("finish_reason"):
                    self.turn.finish_reason = ch["finish_reason"]
            usage = obj.get("usage")
            if usage:
                self._apply_usage(usage)
        except Exception:
            pass  # capture must never break the stream

    def _merge_tool_call(self, tc: dict) -> None:
        idx = tc.get("index", 0)
        while len(self.turn.tool_calls) <= idx:
            self.turn.tool_calls.append(ToolCallRecord())
        rec = self.turn.tool_calls[idx]
        if tc.get("id"):
            rec.call_id = tc["id"]
        fn = tc.get("function") or {}
        if fn.get("name"):
            rec.name = fn["name"]
        if fn.get("arguments"):
            rec.arguments += fn["arguments"]

    def _apply_usage(self, usage: dict) -> None:
        self.turn.prompt_tokens = usage.get("prompt_tokens", 0) or 0
        self.turn.completion_tokens = usage.get("completion_tokens", 0) or 0
        details = usage.get("prompt_tokens_details") or {}
        self.turn.cached_tokens = details.get("cached_tokens", 0) or 0

    def absorb_non_streaming(self, obj: dict) -> None:
        try:
            for ch in obj.get("choices") or []:
                msg = ch.get("message") or {}
                self._chunks.append(msg.get("content") or "")
                if msg.get("reasoning_content"):
                    self.turn.thinking += msg["reasoning_content"]
                for tc in msg.get("tool_calls") or []:
                    fn = tc.get("function") or {}
                    self.turn.tool_calls.append(
                        ToolCallRecord(
                            name=fn.get("name", ""),
                            arguments=fn.get("arguments", "") or "",
                            call_id=tc.get("id", "") or "",
                        )
                    )
                if ch.get("finish_reason"):
                    self.turn.finish_reason = ch["finish_reason"]
            if obj.get("usage"):
                self._apply_usage(obj["usage"])
            self.mark_first_token()
        except Exception as e:
            self.turn.error = f"response capture: {e!r}"

    def finish(self) -> Turn:
        raw = "".join(self._chunks)
        visible, thinking = _extract_think(raw, self.family)
        self.turn.content = visible
        if thinking and not self.turn.thinking:
            self.turn.thinking = thinking
        self.turn.total_ms = (time.perf_counter() - self._t0) * 1000
        return self.turn


# ── App ──────────────────────────────────────────────────────────────────────

def build_app(cfg: dict) -> FastAPI:
    agents: dict[str, dict] = cfg.get("agents") or {}
    bcfg = cfg.get("buffer") or {}
    buf = RingBuffer(
        max_turns=int(bcfg.get("max_turns", 50)),
        max_memory_mb=int(bcfg.get("max_memory_mb", 100)),
        max_age_hours=float(bcfg.get("max_age_hours", 2)),
    )
    app = FastAPI(title="Agent Observability Proxy")
    app.state.buf = buf
    app.state.agents = agents
    app.state.started = time.time()
    client = httpx.AsyncClient(timeout=httpx.Timeout(None, connect=15.0))
    app.state.client = client

    @app.on_event("shutdown")
    async def _close() -> None:
        await client.aclose()

    # ── observer endpoints (Phase 2 replaces/augments these with MCP) ────────
    @app.get("/_obs/agents")
    async def obs_agents() -> JSONResponse:
        out = []
        for name, a in agents.items():
            turns = buf.recent(name, 1)
            out.append({
                "agent": name,
                "upstream": a.get("upstream"),
                "model_family": a.get("model_family"),
                "container": a.get("container"),
                "last_seen": turns[0].ts if turns else None,
                "turns_buffered": len(buf.recent(name, 10**6)),
            })
        return JSONResponse({
            "agents": out,
            "buffer": buf.stats(),
            "uptime_s": round(time.time() - app.state.started, 1),
        })

    @app.get("/_obs/turns/{agent}")
    async def obs_turns(agent: str, n: int = 10, include_thinking: bool = True):
        n = max(1, min(n, 50))
        turns = buf.recent(agent, n)
        return JSONResponse({
            "agent": agent,
            "count": len(turns),
            "turns": [t.to_public(include_thinking) for t in turns],
        })

    @app.get("/_obs/metrics/{agent}")
    async def obs_metrics(agent: str):
        """Scaffolding-paper metrics: what the scaffolding spends per turn."""
        turns = buf.recent(agent, 10**6)
        if not turns:
            return JSONResponse({"agent": agent, "turns": 0})
        n = len(turns)
        pt = [t.prompt_tokens for t in turns if t.prompt_tokens]
        ttft = [t.ttft_ms for t in turns if t.ttft_ms]
        return JSONResponse({
            "agent": agent,
            "turns": n,
            "median_input_tokens": sorted(pt)[len(pt) // 2] if pt else 0,
            "total_input_tokens": sum(pt),
            "total_output_tokens": sum(t.completion_tokens for t in turns),
            "total_cached_tokens": sum(t.cached_tokens for t in turns),
            "mean_tools_offered": round(sum(t.n_tools_offered for t in turns) / n, 1),
            "mean_tool_schema_bytes": round(
                sum(t.tool_schema_bytes for t in turns) / n, 1),
            "tool_calls_made": sum(len(t.tool_calls) for t in turns),
            "median_ttft_ms": round(sorted(ttft)[len(ttft) // 2], 1) if ttft else None,
            "errors": sum(1 for t in turns if t.error or t.upstream_status >= 400),
            # How many turns actually carried upstream usage. Streaming turns
            # usually do not; treat the token sums above as covering only these.
            "turns_with_usage": sum(1 for t in turns if t.prompt_tokens),
            "total_completion_deltas": sum(t.completion_deltas for t in turns),
            "total_prompt_chars": sum(t.prompt_chars for t in turns),
        })

    @app.get("/_obs/health")
    async def obs_health():
        return JSONResponse({"ok": True, "agents": list(agents)})

    # ── the transparent proxy ───────────────────────────────────────────────
    @app.api_route("/v1/{agent}/{path:path}",
                   methods=["GET", "POST", "PUT", "DELETE"])
    async def proxy(agent: str, path: str, request: Request):
        a = agents.get(agent)
        if not a:
            return JSONResponse(
                {"error": {"message": f"unknown agent {agent!r}",
                           "type": "invalid_request_error"}}, status_code=404)

        upstream = a["upstream"].rstrip("/") + "/" + path
        raw = await request.body()

        # Forward headers except hop-by-hop and Host.
        headers = {k: v for k, v in request.headers.items()
                   if k.lower() not in ("host", "content-length", "connection")}

        body: dict = {}
        if raw:
            try:
                body = json.loads(raw)
            except Exception:
                body = {}

        capturing = path.endswith("chat/completions") and isinstance(body, dict)
        cap = Capture(agent, a.get("model_family", "_default"), body) if capturing else None
        streaming = bool(body.get("stream")) if capturing else False

        if not streaming:
            try:
                r = await client.request(request.method, upstream,
                                         content=raw or None, headers=headers,
                                         params=request.query_params)
            except Exception as e:
                if cap:
                    cap.turn.error = repr(e)
                    await buf.add(cap.finish())
                return JSONResponse(
                    {"error": {"message": f"upstream unreachable: {e}",
                               "type": "api_connection_error"}}, status_code=502)

            if cap:
                cap.turn.upstream_status = r.status_code
                try:
                    cap.absorb_non_streaming(r.json())
                except Exception:
                    pass
                await buf.add(cap.finish())

            excluded = ("content-encoding", "transfer-encoding",
                        "content-length", "connection")
            return Response(
                content=r.content, status_code=r.status_code,
                headers={k: v for k, v in r.headers.items()
                         if k.lower() not in excluded},
                media_type=r.headers.get("content-type"))

        # Streaming: pass through chunk-by-chunk, tee into the capture.
        async def gen():
            pending = ""
            try:
                async with client.stream(request.method, upstream,
                                         content=raw or None, headers=headers,
                                         params=request.query_params) as r:
                    if cap:
                        cap.turn.upstream_status = r.status_code
                    async for chunk in r.aiter_raw():
                        yield chunk                       # agent first, always
                        if not cap:
                            continue
                        try:
                            pending += chunk.decode("utf-8", "ignore")
                            while "\n" in pending:
                                line, pending = pending.split("\n", 1)
                                cap.feed_sse_line(line.strip())
                        except Exception:
                            pass
            except Exception as e:
                if cap:
                    cap.turn.error = repr(e)
                raise
            finally:
                if cap:
                    try:
                        await buf.add(cap.finish())
                    except Exception:
                        pass

        return StreamingResponse(gen(), media_type="text/event-stream")

    return app


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--port", type=int, default=None)
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    port = args.port or int((cfg.get("proxy") or {}).get("listen_port", 1240))
    host = str((cfg.get("proxy") or {}).get("listen_host", "127.0.0.1"))
    app = build_app(cfg)
    print(f"[OBS-PROXY] agents: {', '.join((cfg.get('agents') or {}))}", flush=True)
    print(f"[OBS-PROXY] listening on {host}:{port}", flush=True)
    uvicorn.run(app, host=host, port=port, log_level="warning")
    return 0


if __name__ == "__main__":
    sys.exit(main())
