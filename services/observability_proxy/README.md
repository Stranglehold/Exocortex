# Agent Observability Proxy — Phase 1

Spec: `specs/AGENT_OBSERVABILITY_PROXY.md` (Opus, 2026-08-26)
Built: Kestrel, 2026-08-31. **Phase 1 only** (proxy core). Phases 2–5 not started.

A transparent OpenAI-compatible proxy. Point an agent at
`http://<host>:1240/v1/<agent>` instead of its real upstream; requests are
forwarded verbatim and a copy of each exchange lands in a bounded ring buffer.

## Run

```
python proxy.py --config config.yaml
```

## What Phase 1 does

| Deliverable (spec §8) | Status | Evidence |
|---|---|---|
| Transparent forwarding | done | non-streaming HTTP 200, body byte-identical |
| Streaming passthrough (tee, no buffering) | done | first_byte 7 ms vs total 1.45 s |
| Latency budget < 5 ms | done | median delta −0.61 ms over 12 samples = noise |
| Token counting | **partial** | see "The token-counting gap" below |
| Tool call extraction | done | captured `get_weather {"city":"Tokyo"}`, `finish_reason: tool_calls` |
| Tool schema cost | done | `tool_schema_bytes: 208` — the Alier-paper metric |
| Think-block extraction | done | `reasoning_content` captured into `thinking` |
| Ring buffer, bounded | done | capped on turns AND bytes AND age, all three enforced |

All figures above were measured against LM Studio on `:1234` serving
`ornith-1.5-35b-a3b`, 2026-08-31. They are measurements, not estimates.

## Observer endpoints (Phase 2 will add MCP on top)

- `GET /_obs/health`
- `GET /_obs/agents` — configured agents, last-seen, buffer stats
- `GET /_obs/turns/{agent}?n=10&include_thinking=true`
- `GET /_obs/metrics/{agent}` — scaffolding-paper metrics per agent

## The token-counting gap (read before trusting a number)

On the **streaming** path `prompt_tokens` and `completion_tokens` are **0**, and
that is truthful rather than broken. An OpenAI-compatible server only emits a
`usage` block mid-stream when the *caller* sets
`stream_options: {"include_usage": true}`. The agents do not.

We could inject that flag into the upstream request and get real counts. We do
not, because altering the agent's request breaks the transparency guarantee this
whole thing rests on — the agent must not be able to tell it is being observed.

So instead the streaming path records what can be honestly measured:

- `completion_deltas` — count of streamed delta events (NOT a token count)
- `prompt_chars` — summed characters of string message content (NOT tokens)

`/_obs/metrics/` reports `turns_with_usage` so any token sum can be read against
the number of turns that actually contributed one. **Do not present
`completion_deltas` as tokens.**

Resolving this properly is a Phase 5 question: either the observed agent opts
into `include_usage`, or we tokenize locally with the model's tokenizer.

## Deviations from the spec, and why

1. **Upstreams.** The spec puts all three agents on `http://localhost:1235/v1`.
   That was true on 2026-08-26 and is not true now. `:1235` (FreeToken) is down
   and binds loopback only; Aporia moved to `:1234` on 2026-08-28; Hermes moved
   to the Nous API on 2026-08-27. `config.yaml` reflects live state and says so.

2. **`listen_host` added.** The spec says bind `127.0.0.1` (§7.4, privacy).
   That is kept as the default — but it makes the proxy **unreachable from Vek
   and Aporia**, which reach the host as `host.docker.internal`. This is the
   identical failure that left Aporia's utility model dead on `:1235` for two
   days. Proxying a container requires `listen_host: 0.0.0.0`, which exposes the
   port to the LAN. That is a privacy call the spec already made, so it is
   surfaced as config plus this note rather than quietly changed.

3. **`vek` is `enabled: false`** with an empty upstream. His preset has an empty
   `api_base` and litellm supplies the DeepSeek default. That URL was not
   guessed.

## Not done

- Phase 2 MCP server (SSE) — `observe_live_stream`, `observe_recent_turns`, …
- Phase 3 correction detection
- Phase 4 workspace watching / multi-agent
- Phase 5 scaffolding measurement mode
- No agent is pointed at the proxy yet. Nothing is observed until one is, and
  that is a config change on a live agent — Jake's call, not made here.
