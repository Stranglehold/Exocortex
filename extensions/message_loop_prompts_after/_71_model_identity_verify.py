"""Report the model that is ACTUALLY serving, not the one the preset names.

Jake, 2026-09-03: "Ideally the agent will report and understand what model is actually
being served rather than a hard coded value."

WHY THIS EXISTS. A0 core's `_70_include_agent_info.py` renders `LLM:` from
`get_chat_model_config(agent)` — the preset. The preset is a REQUEST, not a fact:

  * llama.cpp ignores the request's `model` field entirely and serves whatever is loaded,
    so a preset can name one model while the server runs another and generation still
    works. Measured 2026-08-22; it silently mis-resolved a model profile for weeks.
  * On 2026-08-22 agent-zero-v2's preset named `ornith-1.0-35b` while :1235 served
    `qwen3.8-27b`. Seven behavioural profile sections differed. Nothing errored.
  * On 2026-09-02 Aporia's agent_info said `lm_studio/ornith-1.5-35b-a3b` and she had no
    way to check it, so she asserted a different "true profile" that exists nowhere on
    the box. An unverifiable claim in an injected block invites exactly that.

WHAT IT DOES NOT DO. It does not guess. `/v1/models` is a CATALOGUE, not a state report
— LM Studio returns 91 ids there while one model is loaded — so this never treats a
/v1/models hit as evidence of what is serving. When it cannot determine the served model
it says `unverified`, and it never restates the preset name as if it were confirmed.
That distinction is the whole point: an instrument whose null case is indistinguishable
from health is worse than no instrument.

SOURCES, in order of authority:
  1. LM Studio native `/api/v0/models` -> entries carry `state`; `state == "loaded"` is
     ground truth for that backend. Vendor-specific.
  2. Nothing else, yet. The completion response echoes a `model` field, which would be
     universal and free, but it is UNVERIFIED whether llama.cpp echoes the real model or
     mirrors the requested name. Until that is measured on a live llama.cpp, this
     extension does not rely on it.

Runs at `message_loop_prompts_after`, numbered after core's `_70`, and only ever APPENDS
to the block `_70` already built. Reads `extras_temporary["agent_info"]`; if that key is
absent it does nothing rather than inventing a block of its own.
"""

import json
import time
import urllib.request

from helpers.extension import Extension
from agent import LoopData

_TAG = "[MODEL-ID-71]"

# module-level cache: the loaded model changes on the order of days, not turns
_CACHE: dict = {"at": 0.0, "served": None, "source": "", "base": ""}
_TTL_SECONDS = 120.0
_TIMEOUT_SECONDS = 3.0


class ModelIdentityVerify(Extension):

    def log(self, msg: str) -> None:
        print(f"{_TAG} {msg}", flush=True)

    # ---------- config ----------

    def _cfg(self) -> dict:
        """Explicit defaults. Absent section -> defaults, never a crash."""
        default = {"enabled": True, "ttl_seconds": _TTL_SECONDS, "warn_on_mismatch": True}
        try:
            with open(
                "/a0/usr/plugins/_exocortex/config/config.json", encoding="utf-8"
            ) as fh:
                section = (json.load(fh) or {}).get("model_identity", {})
            if isinstance(section, dict):
                default.update({k: v for k, v in section.items() if k in default})
        except Exception:
            pass
        return default

    # ---------- the probe ----------

    def _probe_loaded(self, api_base: str) -> tuple[str | None, str, int]:
        """Return (served_model_id, source, loaded_ctx). (None, reason, 0) if unknown.

        Only LM Studio's native endpoint reports load state. /v1/models is deliberately
        NOT consulted: it lists the catalogue and would let us report a model that is
        merely available as if it were serving.

        EMBEDDERS ARE EXCLUDED. Measured 2026-09-03 on the first live turn: the embedding
        model sits loaded alongside the chat model during normal memory operation, so a
        naive "exactly one loaded" test reports `unverified` in the ordinary case and the
        whole extension becomes decorative. Rows carry `type`; chat models are `llm`/`vlm`,
        the embedder is `embeddings`.

        `loaded_context_length` is reported because the backend is the only thing that
        knows it. Advertised context is not real context — that has cost this project days
        twice (FreeToken's --kv-reserve-tokens, and a preset claiming 262144 against 8192).
        """
        base = api_base.rstrip("/")
        if base.endswith("/v1"):
            base = base[:-3]
        url = f"{base}/api/v0/models"
        try:
            with urllib.request.urlopen(url, timeout=_TIMEOUT_SECONDS) as resp:
                payload = json.loads(resp.read())
        except Exception as exc:
            return None, f"no load-state endpoint ({type(exc).__name__})", 0

        rows = payload.get("data") if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            return None, "unexpected payload shape", 0

        loaded = [
            r
            for r in rows
            if isinstance(r, dict)
            and str(r.get("state", "")).lower() == "loaded"
            and str(r.get("type", "")).lower() not in ("embeddings", "embedding")
        ]
        if len(loaded) == 1:
            row = loaded[0]
            try:
                ctx = int(row.get("loaded_context_length") or 0)
            except (TypeError, ValueError):
                ctx = 0
            return str(row.get("id")), "lm_studio /api/v0/models state=loaded", ctx
        if not loaded:
            return None, "backend reports no chat model loaded", 0
        # more than one chat model loaded: cannot attribute which serves this preset
        return None, f"{len(loaded)} chat models loaded, cannot attribute", 0

    def _served(self, api_base: str, ttl: float) -> tuple[str | None, str, int]:
        now = time.time()
        if (
            _CACHE["served"] is not None
            and _CACHE["base"] == api_base
            and (now - _CACHE["at"]) < ttl
        ):
            return _CACHE["served"], _CACHE["source"] + " (cached)", _CACHE.get("ctx", 0)
        served, source, ctx = self._probe_loaded(api_base)
        _CACHE.update(
            {"at": now, "served": served, "source": source, "base": api_base, "ctx": ctx}
        )
        return served, source, ctx

    # ---------- hook ----------

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        try:
            if not self.agent:
                return
            cfg = self._cfg()
            if not cfg.get("enabled", True):
                return

            block = (loop_data.extras_temporary or {}).get("agent_info")
            if not block:
                return  # core _70 did not run; inventing our own block is not our job

            from plugins._model_config.helpers.model_config import get_chat_model_config

            chat_cfg = get_chat_model_config(self.agent) or {}
            configured = str(chat_cfg.get("name", "") or "")
            api_base = str(chat_cfg.get("api_base", "") or "")

            if not api_base:
                # cloud/None base: no load-state notion. Say so rather than implying one.
                line = (
                    "Served model: unverified (no local endpoint to query; "
                    f"'{configured}' above is the CONFIGURED name, which is a request, "
                    "not a confirmation)"
                )
                loop_data.extras_temporary["agent_info"] = block.rstrip() + "\n" + line
                return

            served, source, ctx = self._served(
                api_base, float(cfg.get("ttl_seconds", _TTL_SECONDS))
            )
            ctx_note = f", loaded context {ctx:,}" if ctx else ""

            # State the fact; do not instruct. Advisory guidance in an injected block is
            # the pattern this project measured at 302 surfacings / 300 recurrences with
            # no learning trend (advisory_scaffolding_negative_result_20260811). The
            # useful content here is the MEASUREMENT and, when they disagree, the
            # disagreement. What the agent does with it is the agent's business.
            if served is None:
                line = (
                    f"Served model: unverified ({source}); 'LLM' above is the configured "
                    "name, which is a request to the endpoint rather than a reading of it"
                )
            elif configured and served != configured:
                line = (
                    f"Served model: {served}  [MISMATCH - configured name is "
                    f"'{configured}'] via {source}; profiles keyed on the configured "
                    "name are resolving for a different model than the one answering"
                )
                if cfg.get("warn_on_mismatch", True):
                    self.log(f"MISMATCH configured={configured!r} served={served!r}")
            else:
                line = f"Served model: {served} (verified via {source}{ctx_note})"

            loop_data.extras_temporary["agent_info"] = block.rstrip() + "\n" + line

        except Exception as exc:
            # never break the turn over an informational line
            self.log(f"skipped: {type(exc).__name__}: {exc}")
            return
