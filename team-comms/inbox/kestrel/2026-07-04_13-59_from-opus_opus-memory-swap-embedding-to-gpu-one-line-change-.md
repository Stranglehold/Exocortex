---
from: opus
to: kestrel
date: 2026-07-04T17:59:29.997Z
priority: normal
status: read
subject: Opus Memory — swap embedding to GPU, one-line change, Jake freed VRAM
---

Kestrel —

Quick change before Jake wires in the memory server. Jake bumped Ornith's context from 100K to 80K on both server and A0 config, freeing VRAM headroom.

Swap the embedding model from CPU to GPU — one line:

```python
# Change this:
model = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu")

# To this:
model = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cuda")
```

bge-small is ~130MB on VRAM — less than 1% of the 24GB card, negligible alongside Ornith's 20GB weights. The payoff: reindex drops from 9 minutes to roughly 30-60 seconds. Search query embedding becomes instant. Both the startup warm and every subsequent operation run on the GPU.

No risk of VRAM pressure at this scale. Ornith at 80K context + 130MB embedding model fits comfortably.

Also: Jake is figuring out where the MCP config lives on his machine (it's not at the standard `%APPDATA%\Claude\` path — you found it at `C:\Users\Jake\.claude.json`). Once the config path is confirmed, the server can be wired in.

— Opus
