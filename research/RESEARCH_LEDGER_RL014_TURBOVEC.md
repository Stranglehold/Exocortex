
---

## RL-014: TurboVec — TurboQuant Applied to Vector Search

**Project:** RyanCodrai/turbovec (Rust + Python bindings, MIT license)
**Paper:** Google Research, "TurboQuant: Online Vector Quantization with Near-optimal Distortion Rate," ICLR 2026 (arxiv: 2504.19874)
**Found by:** Jake, June 3, 2026
**Relevance:** Memory infrastructure, FAISS replacement candidate, edge AI memory, the TurboQuant unification thesis
**Maturity:** Alpha (v0.5.2, first release April 2026). Watch, don't adopt yet.

**What It Is:** A vector index built on Google's TurboQuant algorithm. The same mathematical principle that compresses our KV cache (`-ctk turbo3 -ctv turbo3`) applied to embedding storage and retrieval. 31GB of float32 embeddings compressed to 4GB with search quality matching or exceeding FAISS.

**Key Properties:**
- 8x compression ratio (float32 → 2-4 bit quantized)
- Zero training step — data-oblivious quantizer, no codebook calibration, online ingest
- 12-20% faster than FAISS IndexPQFastScan on ARM (NEON kernels)
- Matches or beats FAISS on x86 (AVX-512BW kernels)
- R@1 within 0-1 points of FAISS for OpenAI embeddings (d=1536, d=3072)
- Built-in filtered search — pass ID allowlist to search(), kernel honors it natively
- Python bindings: `pip install turbovec`
- Rust core, MIT license, 946 stars

**Connections to Exocortex:**

1. **FAISS replacement candidate.** Our agents use FAISS for memory retrieval (1,043 memories after un-orphaning). TurboVec could replace FAISS with 8x less memory and equal or better search quality. The zero-training property means no index rebuilds — agents add memories and they're immediately searchable.

2. **Built-in filtering solves our area workaround.** Our current approach: search all areas, then filter. TurboVec filters AT search time (pass an allowlist). The `solutions` separate injection path becomes a filtered search parameter, not a separate index. Cleaner architecture.

3. **The TurboQuant unification thesis.** The same algorithm compresses:
   - KV cache (inference quality) — our `-ctk turbo3 -ctv turbo3`
   - Embedding storage (memory quality) — TurboVec
   - Both improve the environment without touching the model
   - DEC-001 expressed as a mathematical theorem: one quantization principle, two environmental applications

4. **Edge AI memory.** On ARM (Pi 5), TurboVec is 12-20% faster than FAISS. The gadget kit's edge node could store millions of embeddings in 2-4 bit format on 8GB RAM. Local, private, fast vector search on a $80 device.

5. **Online ingest for continuous learning.** FAISS requires periodic index rebuilds as the corpus grows. TurboVec indexes on ingest — each new memory is immediately searchable without rebuilding. This is the property the idle engine's continuous memory accumulation needs.

**Why We're Waiting:**
- Alpha software (v0.5.2, 2 months old)
- Benchmarks are developer-published, not independently verified
- Our FAISS integration is stable and working (the memory un-orphaning fix proved it)
- Swapping a production memory backend on benchmark claims alone violates DEC-041
- The right sequence: watch the project mature → test on a copy of our memory store → compare recall quality against FAISS on our actual data → adopt if validated

**Actionable:**
- Watch the project (GitHub releases, PyPI versions, community benchmarks)
- When it reaches v1.0 or gains independent benchmarks: test on a copy of V16's 1,043-memory store
- Compare R@1 and R@5 against FAISS on our actual embedding dimensions
- If validated: the integration point is A0's memory.py where FAISS is called — replace with TurboVec's Python API
- For the gadget kit: evaluate on Pi 5 ARM alongside the main Exocortex evaluation

**Cross-cutting theme:** Build the environment, not the model. TurboQuant is the unifying principle: same algorithm compresses KV cache and embeddings. The environment improves at both layers through one mathematical insight.
