"""
Cost Control API
================
Route (auto-registered by A0's dispatch): GET + POST /api/cost_control

GET  — returns live cost metrics (from the cache_metrics.jsonl ledger) plus the
       current idle-engine + model-routing config, and a cost decomposition the
       UI uses to compute a live "projected $/day" as the operator moves dials.

POST — writes config the backend already reads live:
       action=set_interval  minutes=<15|30|60|...>      -> idle_time_engine.{idle_threshold,min_gap}
       action=set_power     enabled=<bool>              -> idle_time_engine.enabled
       action=set_cycle     cycle=MAINTAIN|BUILD|EXPLORE model=pro|flash thinking=on|off
                                                        -> idle_model_routing.by_cycle_type[...]

No restart needed for config changes: the idle_watch daemon and the
_05_idle_model_router extension both read these files live.

Prices: DeepSeek V4 current schedule ($/M tokens) — see specs/TOKEN_OPT_*.
"""

import json
import os
import time
from datetime import datetime, timezone

from helpers.api import ApiHandler, Request, Response

_CONFIG_PATH = "/a0/usr/Exocortex/config.json"
_LEDGER_PATH = "/a0/usr/Exocortex/cache_metrics.jsonl"

# $/M tokens — DeepSeek V4 (permanent reduction schedule)
PRICES = {
    "deepseek-v4-pro":   {"hit": 0.003625, "miss": 0.435, "out": 0.87},
    "deepseek-v4-flash": {"hit": 0.0028,   "miss": 0.14,  "out": 0.28},
}
_PRO = PRICES["deepseek-v4-pro"]
_FLASH = PRICES["deepseek-v4-flash"]

# Cycle-type cost shares — derived from the rotation (3 MAINTAIN : 5 BUILD : 1 EXPLORE).
# Approximation used only for the UI's live projection, not for billing.
_SHARES = {"MAINTAIN": 0.33, "BUILD": 0.56, "EXPLORE": 0.11}


class CostControl(ApiHandler):
    """GET/POST /api/cost_control — live cost meter + idle/routing dials."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict | Response:
        if request.method == "GET":
            return _build_state()

        action = (input.get("action") or "").strip().lower()

        if action == "set_power":
            _merge_config(lambda c: c.setdefault("idle_time_engine", {}).__setitem__(
                "enabled", bool(input.get("enabled"))))
            return {"ok": True, **_build_state()}

        if action == "set_interval":
            mins = int(input.get("minutes", 30))
            mins = max(5, min(mins, 240))
            secs = mins * 60

            def _set(c):
                eng = c.setdefault("idle_time_engine", {})
                eng["idle_threshold_seconds"] = secs
                eng["min_gap_between_cycles_seconds"] = secs
            _merge_config(_set)
            return {"ok": True, **_build_state()}

        if action == "set_cycle":
            cycle = (input.get("cycle") or "").strip().upper()
            model = (input.get("model") or "pro").strip().lower()
            thinking = (input.get("thinking") or "on").strip().lower()
            if cycle not in ("MAINTAIN", "BUILD", "EXPLORE"):
                return {"error": f"bad cycle {cycle!r}"}
            name = "deepseek-v4-flash" if model == "flash" else "deepseek-v4-pro"

            def _set(c):
                imr = c.setdefault("idle_model_routing", {})
                imr["enabled"] = True
                by = imr.setdefault("by_cycle_type", {})
                # default state (Pro + thinking on) => remove the override entirely
                if name == "deepseek-v4-pro" and thinking == "on":
                    by.pop(cycle, None)
                else:
                    kwargs = {}
                    if thinking == "off":
                        kwargs = {"extra_body": {"thinking": {"type": "disabled"}}}
                    by[cycle] = {"provider": "deepseek", "name": name, "kwargs": kwargs}
            _merge_config(_set)
            return {"ok": True, **_build_state()}

        return {"error": f"unknown action {action!r}"}


# ── config read/write ────────────────────────────────────────────────────────

def _read_config() -> dict:
    try:
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r", encoding="utf-8-sig") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _merge_config(mutate) -> None:
    """Read-merge-write config.json atomically; `mutate(cfg)` edits in place."""
    try:
        cfg = _read_config()
        mutate(cfg)
        tmp = _CONFIG_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        os.replace(tmp, _CONFIG_PATH)
    except Exception:
        pass


def _config_view(cfg: dict) -> dict:
    """Project the raw config into the panel's control state."""
    eng = cfg.get("idle_time_engine", {}) or {}
    imr = cfg.get("idle_model_routing", {}) or {}
    by = (imr.get("by_cycle_type") or {}) if imr.get("enabled") else {}

    def cyc(name: str) -> dict:
        e = by.get(name) or {}
        model = "flash" if "flash" in (e.get("name") or "") else "pro"
        thinking = "off" if (((e.get("kwargs") or {}).get("extra_body") or {})
                             .get("thinking", {}).get("type") == "disabled") else "on"
        return {"model": model, "thinking": thinking}

    interval_min = int(eng.get("idle_threshold_seconds", 1800)) // 60
    return {
        "enabled": bool(eng.get("enabled", False)),
        "interval_min": interval_min,
        "cycles": {c: cyc(c) for c in ("MAINTAIN", "BUILD", "EXPLORE")},
    }


# ── metrics ──────────────────────────────────────────────────────────────────

def _agg_ledger() -> dict:
    """Aggregate the cache_metrics ledger into cost components + rate."""
    first_ts = None
    last_ts = None
    calls = 0
    hit = miss = out = reasoning = 0
    today_cost = 0.0
    by_model = {}
    now = time.time()
    start_today = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0).timestamp()
    win_start = now - 86400  # last-24h window for the burn-rate decomposition
    # windowed token sums (only entries within the last 24h) — representative of
    # CURRENT burn, vs a full-ledger average that's dragged down by downtime.
    w_hit = w_miss = w_out = w_reason = 0
    w_calls = 0

    try:
        with open(_LEDGER_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                u = r.get("usage")
                if not u:
                    continue
                ts = r.get("ts") or 0
                model = r.get("model") or "deepseek-v4-pro"
                price = PRICES.get(model, _PRO)

                prompt = u.get("prompt_tokens", 0) or 0
                h = u.get("prompt_cache_hit_tokens")
                m = u.get("prompt_cache_miss_tokens")
                if h is None:
                    h = (u.get("prompt_tokens_details") or {}).get("cached_tokens", 0) or 0
                    m = max(prompt - h, 0)
                o = u.get("completion_tokens", 0) or 0
                rz = (u.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0

                cost = (h * price["hit"] + (m or 0) * price["miss"] + o * price["out"]) / 1e6
                calls += 1
                hit += h or 0
                miss += m or 0
                out += o
                reasoning += rz
                if ts:
                    first_ts = ts if first_ts is None else min(first_ts, ts)
                    last_ts = ts if last_ts is None else max(last_ts, ts)
                    if ts >= start_today:
                        today_cost += cost
                    if ts >= win_start:
                        w_hit += h or 0
                        w_miss += m or 0
                        w_out += o
                        w_reason += rz
                        w_calls += 1
                bm = by_model.setdefault(model, {"calls": 0, "cost": 0.0})
                bm["calls"] += 1
                bm["cost"] += cost
    except FileNotFoundError:
        pass

    span_days = ((last_ts - first_ts) / 86400.0) if (first_ts and last_ts and last_ts > first_ts) else 0
    prompt_tot = hit + miss
    # Burn-rate decomposition from the last-24h window (already per-day, scale=1).
    # Fall back to the full-ledger daily average if the 24h window is ~empty
    # (engine paused all day) so the panel still shows a real figure.
    if w_calls >= 5:
        u_miss, u_reason, u_out, u_hit = w_miss, w_reason, w_out, w_hit
        scale = 1.0
        rate_window = "24h"
    elif span_days > 0:
        u_miss, u_reason, u_out, u_hit = miss, reasoning, out, hit
        scale = 1.0 / span_days
        rate_window = f"{span_days:.1f}d avg"
    else:
        u_miss = u_reason = u_out = u_hit = 0
        scale = 0.0
        rate_window = "—"
    miss_cost = u_miss * _PRO["miss"] / 1e6
    out_reason_cost = u_reason * _PRO["out"] / 1e6
    out_other_cost = max(u_out - u_reason, 0) * _PRO["out"] / 1e6
    hit_cost = u_hit * _PRO["hit"] / 1e6

    return {
        "calls": calls,
        "cache_hit_pct": round(100 * hit / prompt_tot, 1) if prompt_tot else 0.0,
        "reasoning_pct": round(100 * reasoning / out, 1) if out else 0.0,
        "today_cost": round(today_cost, 4),
        "span_days": round(span_days, 3),
        "rate_window": rate_window,
        "rate_per_day": round((miss_cost + out_reason_cost + out_other_cost + hit_cost) * scale, 4),
        "decomp_per_day": {
            "miss":   round(miss_cost * scale, 5),
            "reason": round(out_reason_cost * scale, 5),
            "other":  round(out_other_cost * scale, 5),
            "hit":    round(hit_cost * scale, 5),
        },
        "by_model": {k: {"calls": v["calls"], "cost": round(v["cost"], 4)} for k, v in by_model.items()},
    }


def _build_state() -> dict:
    cfg = _read_config()
    return {
        "metrics": _agg_ledger(),
        "config": _config_view(cfg),
        "shares": _SHARES,
        "flash_ratio": {
            "miss":   round(_FLASH["miss"] / _PRO["miss"], 3),
            "out":    round(_FLASH["out"] / _PRO["out"], 3),
            "hit":    round(_FLASH["hit"] / _PRO["hit"], 3),
        },
    }
