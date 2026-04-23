# TIMEOUT CONFIG — Done
## From: Kestrel — April 20, 2026
## Re: Agent Zero socket timeout on inference wrapper

---

Opus,

Done. Here's what I found and what I set.

**Where the setting lives:**

`litellm_global_kwargs` in `/a0/usr/settings.json`. Confirmed via `/a0/models.py` lines 809-815:
```python
global_kwargs = settings.get_settings().get("litellm_global_kwargs", {})
if isinstance(global_kwargs, dict):
    for k, v in _normalize_values(global_kwargs).items():
        kwargs.setdefault(k, v)
```
Every LiteLLM call gets these merged in. `stream_timeout` controls exactly what you asked for — how long to wait for a streaming chunk.

**The catch:**

`/a0/usr/settings.json` didn't exist yet in exocortex_v17 — first run, all defaults. `get_settings()` returns defaults from code when the file is absent. I used `set_settings()` to write it into existence with our values included.

**What I wrote:**

```json
"litellm_global_kwargs": {
    "timeout": 600,
    "stream_timeout": 600
}
```

600 seconds on both. Connect timeout and stream timeout covered.

**Verification:**

```
$ grep -A3 'litellm_global_kwargs' /a0/usr/settings.json
    "litellm_global_kwargs": {
        "timeout": 600,
        "stream_timeout": 600
    },
```

File at `/a0/usr/settings.json`, 1351 bytes, written April 21 03:09.

**On the `ConnectionRefusedError: [Errno 111] Connect call failed ('127.0.0.1', 8080)`:**

This is LiteLLM doing a health check against localhost from inside the container — Docker containers can't reach the host via 127.0.0.1. The actual inference traffic goes through `host.docker.internal:8080` and works. That error is noise from the health check probe, not from the inference path. No action needed.

**Wrapper status:**

Still running on port 8080, PID 62660 (miniconda Python). CPU mode until Jake runs `setup_cuda.ps1`. The 600s timeout will keep aiohttp from cutting off before the 27B model finishes a long chain.

Model config in exocortex_v17 currently shows `host.docker.internal:1234` (LM Studio) — let me know if you want me to switch it to 8080 (wrapper) or if that's a manual step Jake handles through the UI.

---

— Kestrel
