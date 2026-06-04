"""
Idle Model Router  (DRAFT — held for Jake's model config + approval)
====================================================================
Hook: chat_model_call_before
Routes idle-cycle LLM calls to a cheaper model by cycle type, to cut DeepSeek
cost on routine cycles (Lever 4 of DEEP_TOKEN_OPTIMIZATION).

INERT BY DEFAULT. Does nothing unless config provides an `idle_model_routing`
block with `enabled: true`. No block = no routing = stock behaviour. This is the
graceful-degradation contract every Exocortex extension follows.

Mechanism (verified against A0 1.18):
  - agent.call_chat_model() resolves the model fresh per call and exposes a
    mutable call_data["model"] via this hook (agent.py:790-828).
  - models.get_chat_model(provider, name, **kwargs) -> LiteLLMChatWrapper
    builds a model wrapper exactly as A0 does (models.py:829).
  - Each idle cycle is a FRESH context (idle_watch fires with no context_id),
    whose first user message carries "## IDLE-TIME CYCLE ACTIVATED" + a
    "Cycle type: MAINTAIN|BUILD|EXPLORE" line. We route per cycle (not per turn),
    which matches the fresh-context-per-cycle design.

Config contract (Jake authors this — model identities are MODEL CONFIG):
  /a0/usr/Exocortex/config.json
  "idle_model_routing": {
    "enabled": true,
    "by_cycle_type": {
      "MAINTAIN": {"provider": "deepseek", "name": "deepseek-v4-flash", "kwargs": {}}
      // cycle types absent here keep the agent's default (Pro) model
    }
  }

This extension AUTHORS NO MODEL CONFIG. It only routes to models Jake has named.
Real-user contexts (no activation sentinel) are never touched.
"""

import json

from helpers.extension import Extension

_SENTINEL    = "## IDLE-TIME CYCLE ACTIVATED"
_CONFIG_PATH = "/a0/usr/Exocortex/config.json"
_STATE_PATH  = "/a0/usr/workdir/workspace/office/engine_state.json"
_CACHE_ATTR  = "_idle_router_models"      # per-agent cache of built wrappers
_TYPE_ATTR   = "_idle_router_cycle_type"  # per-context memoised cycle type


def _load_routing_cfg() -> dict:
    try:
        with open(_CONFIG_PATH, encoding="utf-8-sig") as f:
            return json.load(f).get("idle_model_routing") or {}
    except Exception:
        return {}


def _detect_cycle_type(agent):
    cached = getattr(agent, _TYPE_ATTR, "__unset__")
    if cached != "__unset__":
        return cached

    ctype = None
    try:
        for m in agent.history.output():
            content = m.get("content") if isinstance(m, dict) else None
            text = content if isinstance(content, str) else json.dumps(content)
            if _SENTINEL in (text or ""):
                for line in text.splitlines():
                    if "cycle type" in line.lower():
                        parts = line.split(":", 1)[-1].strip().upper().split()
                        if parts:
                            ctype = parts[0]
                        break
                break
    except Exception:
        pass

    # Fallback: engine_state.last_cycle_type (idle cycles are serialised by the
    # idle_watch flock, so an active cycle's type is unambiguous).
    if ctype is None:
        try:
            with open(_STATE_PATH, encoding="utf-8") as f:
                st = json.load(f)
            if st.get("cycle_active"):
                ctype = (st.get("last_cycle_type") or "").upper() or None
        except Exception:
            pass

    setattr(agent, _TYPE_ATTR, ctype)
    return ctype


def _get_routed_model(agent, spec):
    cache = getattr(agent, _CACHE_ATTR, None)
    if cache is None:
        cache = {}
        setattr(agent, _CACHE_ATTR, cache)
    key = f"{spec.get('provider')}/{spec.get('name')}"
    if key in cache:
        return cache[key]
    import models
    model = models.get_chat_model(spec["provider"], spec["name"], **(spec.get("kwargs") or {}))
    cache[key] = model
    return model


class IdleModelRouter(Extension):
    async def execute(self, loop_data=None, **kwargs) -> None:
        call_data = kwargs.get("call_data")
        if not call_data:
            return
        try:
            cfg = _load_routing_cfg()
            if not cfg.get("enabled"):
                return
            ctype = _detect_cycle_type(self.agent)
            if not ctype:
                return  # not an idle cycle — leave the default model untouched
            spec = (cfg.get("by_cycle_type") or {}).get(ctype)
            if not spec or not spec.get("provider") or not spec.get("name"):
                return  # no override for this cycle type — default (Pro) stands
            model = _get_routed_model(self.agent, spec)
            if model is not None:
                prev = getattr(call_data.get("model"), "model_name", "?")
                call_data["model"] = model
                print(f"[IDLE-ROUTER] {ctype}: model -> {spec['provider']}/{spec['name']} (was {prev})", flush=True)
        except Exception as e:
            print(f"[IDLE-ROUTER] passthrough: {e}", flush=True)
