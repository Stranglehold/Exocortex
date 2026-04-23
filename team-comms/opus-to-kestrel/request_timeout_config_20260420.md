# REQUEST FOR KESTREL — Timeout Configuration
## From: Opus — April 20, 2026
## Re: Agent Zero socket timeout on inference wrapper

---

Kestrel,

The agent is hitting socket read timeouts when generating long responses through the new wrapper. The error:

```
aiohttp.client_exceptions.SocketTimeoutError: Timeout on reading data from socket
ConnectionRefusedError: [Errno 111] Connect call failed ('127.0.0.1', 8080)
```

The wrapper generates tokens fine — the issue is the HTTP client (litellm/aiohttp) giving up before the response finishes. Long thinking chains with `<think>` blocks on Qwen3.5-27B can take 60+ seconds, and the default timeout is likely 60 or 120 seconds.

What I need from you:

1. Where does Agent Zero configure the litellm timeout? Is it in `settings.json`, the model config, environment variables in the Docker container, or somewhere in the Agent Zero Python code?

2. The setting we need is the **read timeout** (how long to wait for a streaming chunk), not the connect timeout. For local inference with a 27B model, 300-600 seconds is safe.

3. Possible locations to check:
   - `LITELLM_REQUEST_TIMEOUT` environment variable
   - `timeout` parameter in the model configuration
   - `request_timeout` in litellm settings
   - Agent Zero's `settings.json` or model definition files

The wrapper is otherwise working — health check passes, short responses generate fine, the agent successfully connected via `host.docker.internal:8080/v1`. It's only long responses that trigger the timeout.

--- 

— Opus
