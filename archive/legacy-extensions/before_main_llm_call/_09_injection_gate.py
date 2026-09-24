"""
Injection Gate — Context Budget Management
==========================================
Hook: before_main_llm_call (_09_)
Priority: Fires before ALL injecting extensions

Single control point that manages injection decisions for all participating
extensions. Does not inject content itself — sets phase/cache state that
other extensions read to decide whether to inject their full block, a
compressed reference, or nothing.

Two phases:
  FULL        — inject everything (turns 1-3, and 2 turns after any domain change)
  CONDITIONAL — inject only changed content; cache hits become reference lines

Emergency mode:
  COMPRESSED  — references only when context utilization > 85%

Extensions integrate by calling:
  from extensions.before_main_llm_call._09_injection_gate import should_inject
  action, ref = should_inject(agent, "ext_name", content)

  action == "full"      → inject the complete block
  action == "reference" → inject only the one-line reference
  action == "skip"      → no content, inject nothing

Graceful degradation: if the gate isn't initialized (import fails, first run),
should_inject() returns ("full", "") — safe default, no extension breaks.

Token tracking: writes to both gate["token_budget"] AND agent._injection_token_counts
so _18_injection_budget.py continues to work without modification.
"""

import hashlib
import re
from typing import Optional

from agent import LoopData
from helpers.extension import Extension


# ── Constants ──────────────────────────────────────────────────────────────────

_GATE_ATTR    = "_injection_gate"
_BST_STORE    = "_bst_store"
BELIEF_KEY    = "__bst_belief_state__"

# Turns at session start that always inject everything
_FULL_PHASE_TURNS = 3

# Extra full-injection turns after domain change
_DOMAIN_CHANGE_EXTRA = 2

# Context utilization threshold for compressed mode
_COMPRESS_THRESHOLD = 0.85

# Model config path (same as supervisor and phase4)
_MODEL_CONFIG_PATH = "/a0/usr/plugins/_model_config/config.json"


# ── Reference line templates ──────────────────────────────────────────────────

_REFERENCE_TEMPLATES = {
    "bst":              "[BST: {domain}, conf={confidence} — unchanged]",
    "operator_profile": "[OPERATOR PROFILE: cached — unchanged]",
    "metacognitive":    "[META: {model_id} | cutoff:{cutoff} | {domain} — unchanged]",
    "tool_registry":    "[TOOLS: {tool_count} custom tools — unchanged]",
    "orchestration":    "[ORCH: {state} — unchanged]",
    "memory_catalog":   "[MEMORY: {area_count} areas — unchanged]",
    "htn_plan":         "[HTN: {plan_name} step {step} — unchanged]",
}

# Per-extension key extractors for reference lines
_KEY_EXTRACTORS = {
    "bst":              lambda content, agent: {
        "domain":     _get_bst_domain_from_store(agent),
        "confidence": _get_bst_confidence_from_store(agent),
    },
    "operator_profile": lambda content, agent: {},
    "metacognitive":    lambda content, agent: _extract_meta_keys(content),
    "tool_registry":    lambda content, agent: {
        "tool_count": max(content.count("\n") - 1, 0),
    },
    "orchestration":    lambda content, agent: {
        "state": content[:40].replace("\n", " ").strip(),
    },
    "memory_catalog":   lambda content, agent: {
        "area_count": content.count("area:") + content.count("Area:") or "?",
    },
    "htn_plan":         lambda content, agent: _extract_htn_keys(content),
}


# ── Gate class ─────────────────────────────────────────────────────────────────

class InjectionGate(Extension):
    """
    Runs at _09_ — before all injecting extensions.
    Initializes per-session gate state and sets the injection phase.
    Extensions call should_inject() to receive their injection decision.
    """

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            gate = _get_or_init_gate(self.agent)

            gate["turn"] += 1
            turn = gate["turn"]

            # Reset per-turn token budget
            gate["token_budget"] = {}
            gate["total_tokens_this_turn"] = 0

            # Detect domain change (reads last turn's BST domain from store;
            # BST runs at _11_ so _bst_store has previous turn's classification)
            current_domain = _get_bst_domain_from_store(self.agent)
            last_domain    = gate.get("last_domain")
            domain_changed = bool(current_domain) and current_domain != last_domain

            if domain_changed:
                gate["domain_change_this_turn"] = True
                gate["full_phase_until"] = turn + _DOMAIN_CHANGE_EXTRA
                gate["cache"].clear()
                gate["last_domain"] = current_domain
                print(
                    f"[GATE] Domain change: {last_domain} → {current_domain}. "
                    f"Full injection until T={gate['full_phase_until']}.",
                    flush=True,
                )
            else:
                gate["domain_change_this_turn"] = False
                if current_domain:
                    gate["last_domain"] = current_domain

            # Set phase
            if turn <= gate["full_phase_until"]:
                gate["phase"] = "full"
            else:
                gate["phase"] = "conditional"

            # Emergency compressed mode (context watchdog sets context_utilization)
            utilization = _get_context_utilization(loop_data)
            if utilization > _COMPRESS_THRESHOLD and gate["phase"] == "conditional":
                gate["phase"] = "compressed"
                print(
                    f"[GATE] Context critical ({utilization:.0%}) — compressed mode.",
                    flush=True,
                )

            print(
                f"[GATE] T={turn} phase={gate['phase']} "
                f"domain={current_domain} changed={domain_changed}",
                flush=True,
            )

        except Exception as e:
            print(f"[GATE] Error (passthrough): {e}", flush=True)


# ── Public API — called by participating extensions ────────────────────────────

def should_inject(agent, ext_name: str, new_content: str) -> tuple:
    """
    Called by participating extensions before injecting their content block.

    Returns (action, reference_line):
      ("full",      "")   — inject the complete block
      ("reference", ref)  — inject only the one-line reference
      ("skip",      "")   — no content, inject nothing

    If the gate isn't initialized, returns ("full", "") — safe default.
    """
    if not new_content or not new_content.strip():
        return ("skip", "")

    gate = getattr(agent, _GATE_ATTR, None)
    if gate is None:
        # Gate not running — every extension injects fully (safe default)
        return ("full", "")

    phase = gate.get("phase", "full")

    # FULL phase — inject everything, update cache
    if phase == "full":
        _update_cache(gate, ext_name, new_content)
        _track_tokens(gate, agent, ext_name, new_content)
        return ("full", "")

    # COMPRESSED phase — reference lines only for all extensions
    if phase == "compressed":
        ref = _make_reference(ext_name, new_content, agent)
        _track_tokens(gate, agent, ext_name, ref)
        return ("reference", ref)

    # CONDITIONAL phase — cache check
    new_hash = _fast_hash(new_content)
    cached   = gate["cache"].get(ext_name, {})

    if cached.get("hash") == new_hash:
        # Content unchanged — inject reference
        ref = _make_reference(ext_name, new_content, agent)
        _track_tokens(gate, agent, ext_name, ref)
        return ("reference", ref)
    else:
        # Content changed — inject full and update cache
        _update_cache(gate, ext_name, new_content)
        _track_tokens(gate, agent, ext_name, new_content)
        return ("full", "")


# ── Internal helpers ────────────────────────────────────────────────────────────

def _get_or_init_gate(agent) -> dict:
    gate = getattr(agent, _GATE_ATTR, None)
    if gate is None:
        gate = {
            "turn":                   0,
            "phase":                  "full",
            "full_phase_until":       _FULL_PHASE_TURNS,
            "last_domain":            None,
            "cache":                  {},
            "token_budget":           {},
            "total_tokens_this_turn": 0,
            "domain_change_this_turn": False,
        }
        setattr(agent, _GATE_ATTR, gate)
    return gate


def _fast_hash(content: str) -> str:
    return hashlib.md5(content.encode("utf-8", errors="replace")).hexdigest()[:16]


def _update_cache(gate: dict, ext_name: str, content: str) -> None:
    gate["cache"][ext_name] = {
        "hash": _fast_hash(content),
        "turn": gate["turn"],
    }


def _track_tokens(gate: dict, agent, ext_name: str, content: str) -> None:
    tokens = max(1, len(content) // 4)
    gate["token_budget"][ext_name]  = tokens
    gate["total_tokens_this_turn"] += tokens
    # Write to _injection_token_counts so _18_injection_budget.py still works
    counts = getattr(agent, "_injection_token_counts", None) or {}
    counts[ext_name] = tokens
    agent._injection_token_counts = counts


def _get_context_utilization(loop_data: LoopData) -> float:
    try:
        params = getattr(loop_data, "params_temporary", None) or {}
        return float(params.get("context_utilization", 0.0))
    except Exception:
        return 0.0


def _get_bst_domain_from_store(agent) -> str:
    """Read last turn's BST domain from the persistent store."""
    try:
        store = getattr(agent, _BST_STORE, None) or {}
        # Primary: BELIEF_KEY dict (set by _BSTEngine._persist_belief)
        belief = store.get(BELIEF_KEY)
        if isinstance(belief, dict):
            domain = belief.get("domain")
            if domain:
                return str(domain)
        # Fallback: dataclass with primary_domain attribute
        if belief is not None and hasattr(belief, "primary_domain"):
            return str(belief.primary_domain)
        # Fallback: compound signature (e.g. "coding+devops") — take first part
        sig = store.get("_compound_sig", "")
        if sig:
            return sig.split("+")[0].strip()
    except Exception:
        pass
    return ""


def _get_bst_confidence_from_store(agent) -> int:
    try:
        store  = getattr(agent, _BST_STORE, None) or {}
        belief = store.get(BELIEF_KEY)
        if isinstance(belief, dict):
            conf = belief.get("confidence")
            if conf is not None:
                return int(float(conf) * 10) if conf <= 1.0 else int(conf)
        if belief is not None and hasattr(belief, "primary_confidence"):
            return int(belief.primary_confidence)
    except Exception:
        pass
    return 0


def _make_reference(ext_name: str, content: str, agent) -> str:
    template  = _REFERENCE_TEMPLATES.get(ext_name)
    extractor = _KEY_EXTRACTORS.get(ext_name)
    if template and extractor:
        try:
            values = extractor(content, agent)
            return template.format(**values)
        except (KeyError, IndexError, TypeError):
            pass
    # Generic fallback: first 80 chars, newlines stripped
    summary = content[:80].replace("\n", " ").strip()
    return f"[{ext_name}: unchanged — {summary}...]"


# ── Key value extractors ────────────────────────────────────────────────────────

def _extract_meta_keys(content: str) -> dict:
    model_id = "unknown"
    cutoff   = "unknown"
    domain   = "unknown"
    for line in content.splitlines():
        if "|" in line and "cutoff" in line:
            parts = line.split("|")
            model_id = parts[0].replace("[MODEL CONFIGURATION]", "").strip() or model_id
            for p in parts:
                p = p.strip()
                if p.startswith("cutoff:"):
                    cutoff = p.replace("cutoff:", "").strip().split()[0]
        if line.startswith("Domain:"):
            domain = line.replace("Domain:", "").split("(")[0].strip() or domain
    return {"model_id": model_id, "cutoff": cutoff, "domain": domain}


def _extract_htn_keys(content: str) -> dict:
    plan_name = "?"
    step      = "?"
    for line in content.splitlines():
        ll = line.lower()
        if "plan:" in ll:
            plan_name = line.split(":", 1)[-1].strip()[:20]
        if "step" in ll:
            m = re.search(r"step\s*(\d+)", line, re.IGNORECASE)
            if m:
                step = m.group(1)
    return {"plan_name": plan_name, "step": step}
