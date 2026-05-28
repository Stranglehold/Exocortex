"""
stack_status.py — Exocortex Stack Introspection Tool
=====================================================

Reports the live state of the Exocortex stack: which extensions are present
at the canonical profile path, and what runtime state the active layers have
accumulated.

Call this tool when:
  - Something isn't behaving as expected and you need to confirm which layers
    are actually running.
  - You want a snapshot of current classification state, EI verdicts, or
    supervisor anomaly counts.
  - After a deployment, to verify all extensions landed correctly.

No arguments required. No LLM calls. No external dependencies.
Output is deterministic: filesystem scan + agent attribute reads.

Updated 2026-05-27: AUTO-DISCOVER replaces the stale hardcoded EXTENSIONS dict.
  - A0 v1.18 loads extensions from /a0/usr/agents/agent0/extensions/python/<hook>/
    only (confirmed by extensions/install_extensions.sh:75 + runtime hook-tag
    evidence on nifty_panini v1.18). The prior version scanned the DIRECT path
    /a0/usr/agents/agent0/extensions/<hook>/ and missed 60+ loaded files while
    seeing 3 orphan-direct-path deploys, reporting a misleading "3/42 present."
  - Now scans python/<hook>/ as ground truth (auto-discovered, no stale list)
    and flags any files at the direct path as ORPHANS (deployed but not loaded).
  - BST reader now handles both dict-stored and object-stored belief states.
"""

import os
from datetime import datetime, timezone

from helpers.tool import Tool, Response

# A0 v1.18 extension loader paths.
EXT_ROOT       = "/a0/usr/agents/agent0/extensions"
CANONICAL_ROOT = f"{EXT_ROOT}/python"   # A0 ONLY loads from here. Direct EXT_ROOT/<hook>/ is orphan.


class StackStatus(Tool):
    """
    Report the live state of the Exocortex extension stack.

    Returns:
      - Per-hook inventory of extensions at the canonical profile path (loaded by A0).
      - Orphan deploys at the direct path (present but NOT loaded by A0 v1.18).
      - Runtime state accumulated by active layers this session.
    """

    async def execute(self, **kwargs) -> Response:
        try:
            report = _build_report(self.agent)
            print("[STACK] Status report generated.", flush=True)
            return Response(message=report, break_loop=False)
        except Exception as e:
            return Response(message=f"[STACK] Error generating report: {e}", break_loop=False)


# ---------------------------------------------------------------------------
# Deployment inventory — auto-discovered from the live filesystem
# ---------------------------------------------------------------------------

def _scan_deployment() -> dict:
    """Return {hook: {'loaded': [names], 'orphan': [names]}} for every hook
    that has any deploy at either path. `loaded` are .py files at the canonical
    python/<hook>/ path (A0 v1.18 will load these). `orphan` are .py files at
    the direct <hook>/ path that A0 does NOT load (a deploy-path bug)."""
    out: dict = {}

    # Canonical (loaded) — python/<hook>/<file>.py
    if os.path.isdir(CANONICAL_ROOT):
        for hook in sorted(os.listdir(CANONICAL_ROOT)):
            hp = os.path.join(CANONICAL_ROOT, hook)
            if not os.path.isdir(hp):
                continue
            loaded = sorted(
                f for f in os.listdir(hp)
                if f.endswith(".py") and not f.startswith("__")
            )
            out[hook] = {"loaded": loaded, "orphan": []}

    # Orphans — direct <hook>/<file>.py NOT also present at canonical.
    if os.path.isdir(EXT_ROOT):
        for hook in sorted(os.listdir(EXT_ROOT)):
            if hook == "python" or hook.startswith("."):
                continue
            hp = os.path.join(EXT_ROOT, hook)
            if not os.path.isdir(hp):
                continue
            direct = {
                f for f in os.listdir(hp)
                if f.endswith(".py") and not f.startswith("__")
            }
            loaded_set = set(out.get(hook, {}).get("loaded", []))
            orphans = sorted(direct - loaded_set)
            if orphans:
                out.setdefault(hook, {"loaded": [], "orphan": []})["orphan"] = orphans
    return out


def _short(name: str) -> str:
    """Strip .py for compact display."""
    return name[:-3] if name.endswith(".py") else name


def _build_report(agent) -> str:
    lines = ["[EXOCORTEX STACK STATUS]", ""]
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append(f"Generated: {ts}")
    lines.append(f"Loader path: {CANONICAL_ROOT}   (A0 loads only from python/<hook>/)")
    lines.append("")

    # ── Section 1: Deployment inventory ────────────────────────────────────
    scan = _scan_deployment()
    total_loaded = sum(len(d["loaded"]) for d in scan.values())
    total_orphan = sum(len(d["orphan"]) for d in scan.values())
    populated_hooks = sum(1 for d in scan.values() if d["loaded"])
    lines.append(f"Extensions loaded: {total_loaded} across {populated_hooks} hook dir(s)")
    if total_orphan:
        lines.append(f"  ⚠ Orphan deploys at direct path (NOT loaded): {total_orphan}  — see hooks marked ⚠ below")
    lines.append("")

    for hook in sorted(scan.keys()):
        loaded = scan[hook]["loaded"]
        orphan = scan[hook]["orphan"]
        if loaded:
            lines.append(f"  {hook:<28} ({len(loaded):>2}) {', '.join(_short(f) for f in loaded)}")
        elif orphan:
            lines.append(f"  {hook:<28} ( 0) (empty — see orphan list below)")
        if orphan:
            lines.append(f"    ⚠ orphan: {', '.join(_short(f) for f in orphan)}  (at {EXT_ROOT}/{hook}/, NOT loaded)")
    lines.append("")

    # ── Section 2: Runtime state ────────────────────────────────────────────
    lines.append("Runtime state (session-accumulated)")
    lines.append(f"  BST            {_read_bst(agent)}")
    lines.append(f"  Evidence       {_read_evidence(agent)}")
    lines.append(f"  EI             {_read_ei(agent)}")
    lines.append(f"  Action gate    {_read_action_gate(agent)}")
    lines.append(f"  Supervisor     {_read_supervisor(agent)}")
    lines.append(f"  Working mem    {_read_working_memory(agent)}")
    lines.append(f"  Operator       {_read_operator_profile(agent)}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Runtime state readers — all safe, return "not yet fired" on missing attr
# ---------------------------------------------------------------------------

def _get(obj, key, default=None):
    """Read `key` from obj whether it's a dict, an object, or neither. Centralises
    the dict-or-object ambiguity that caused the BST reader's pre-fix "domain=?"
    when belief was stored as a dict (getattr returns None for dicts)."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _read_bst(agent) -> str:
    try:
        store = getattr(agent, "_bst_store", None)
        if not store:
            return "not yet fired"
        belief = store.get("__bst_belief_state__")
        if not belief:
            # BST stored some context fields but never produced a belief state.
            sig = store.get("_compound_sig")
            return f"store present, belief empty (compound_sig={sig})" if sig else "store present, belief state empty"
        primary   = _get(belief, "primary_domain") or store.get("_bst_domain") or "?"
        secondary = _get(belief, "secondary_domain")
        confidence = _get(belief, "confidence")
        bits = [f"domain={primary}"]
        if secondary and secondary != primary:
            bits.append(f"secondary={secondary}")
        if confidence is not None:
            try: bits.append(f"conf={float(confidence):.2f}")
            except Exception: pass
        return " | ".join(bits)
    except Exception as e:
        return f"read error: {e}"


def _read_evidence(agent) -> str:
    try:
        ledger = None
        try:
            ledger = agent.get_data("_evidence_ledger")
        except Exception:
            pass
        if ledger is None:
            ledger = getattr(agent, "_evidence_ledger", None)
        if not ledger:
            return "not yet fired"
        entries = _get(ledger, "entries", []) or []
        kv      = _get(ledger, "key_values", []) or []
        return f"{len(entries)} entries | {len(kv)} key values this session"
    except Exception as e:
        return f"read error: {e}"


def _read_ei(agent) -> str:
    try:
        ei = None
        try:
            ei = agent.get_data("_epistemic_integrity")
        except Exception:
            pass
        if ei is None:
            ei = getattr(agent, "_epistemic_integrity", None)
        if not ei:
            return "not yet fired"
        total  = _get(ei, "total_claims", 0)
        high   = _get(ei, "high_risk_count", 0)
        claims = _get(ei, "claims", []) or []
        last_verdict = _get(claims[-1], "verdict", "?") if claims else "none"
        return f"{total} claims | {high} high-risk | last={last_verdict}"
    except Exception as e:
        return f"read error: {e}"


def _read_action_gate(agent) -> str:
    try:
        gate = None
        try:
            gate = agent.get_data("_action_gate_active")
        except Exception:
            pass
        if gate is None:
            gate = getattr(agent, "_action_gate_active", None)
        if gate is None:
            return "not yet fired"
        return "ACTIVE — awaiting authorization" if gate else "inactive"
    except Exception as e:
        return f"read error: {e}"


def _read_supervisor(agent) -> str:
    try:
        state = getattr(agent, "_supervisor_state", None)
        if not state:
            return "not yet fired"
        turn      = _get(state, "turn", 0)
        loop_tier = _get(state, "loop_tier", "none") or "none"
        cooldowns = _get(state, "cooldowns", {}) or {}
        fired = [k for k, v in cooldowns.items() if isinstance(v, int) and v > 0]
        return f"turn={turn} | loop_tier={loop_tier} | anomalies fired={', '.join(fired) if fired else 'none'}"
    except Exception as e:
        return f"read error: {e}"


def _read_working_memory(agent) -> str:
    try:
        wm = getattr(agent, "_working_memory", None)
        if not wm:
            return "not yet fired"
        entities = _get(wm, "entities", []) or []
        promoted = _get(wm, "promoted", {}) or {}
        return f"{len(entities)} entities ({len(promoted)} promoted)"
    except Exception as e:
        return f"read error: {e}"


def _read_operator_profile(agent) -> str:
    try:
        cache = getattr(agent, "_operator_profile_cache", None)
        if not cache:
            return "not loaded (no approved profile)"
        profile = _get(cache, "profile", {}) or {}
        if not profile:
            return "cache present, profile empty"
        comm    = _get(profile, "communication_patterns", {}) or {}
        avg_len = _get(comm, "avg_turn_length_chars", 0) or 0
        try:    return f"loaded (avg {float(avg_len):.0f} chars/turn)"
        except Exception: return "loaded"
    except Exception as e:
        return f"read error: {e}"
