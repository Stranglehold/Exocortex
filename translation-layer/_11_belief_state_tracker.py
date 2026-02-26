"""
Belief State Tracker — Agent-Zero Translation Layer v3
====================================================
Hook: before_main_llm_call

Works with agent-zero's dict-based message format.
Intercepts user messages before LLM call, classifies intent,
resolves slots, and enriches with structured context.

v3.1 — Compound Classification Layer
--------------------------------------
- Scores all domains (score-all replaces first-match-wins).
- Emits primary + optional secondary domain.
- Tracks compound signature momentum across turns.
- Integrates model profile enrichment gating.
- Writes _bst_domain and _bst_compound to extras_persistent.
- Slot resolution pipeline (taxonomy / _BSTEngine) unchanged.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent import LoopData
from python.helpers.extension import Extension

TAXONOMY_PATH          = Path(__file__).parent / "slot_taxonomy.json"
BELIEF_KEY             = "__bst_belief_state__"
MAX_HISTORY_SCAN_TURNS = 8

# ── Compound classification constants ─────────────────────────────────────────
SECONDARY_MIN_SIGNALS = 1   # Secondary must match at least 1 signal
MOMENTUM_THRESHOLD    = 3   # Turns before momentum resists reclassification

# Priority order for tiebreaking when two domains have identical scores.
# Lower number = higher priority. Favours higher-stakes, harder-to-recover domains.
DOMAIN_PRIORITY = {
    "investigation":      1,
    "analysis":           2,
    "bugfix":             3,
    "coding":             4,
    "planning":           5,
    "system_admin":       6,
    "config_edit":        7,
    "prompt_engineering": 8,
    "git_ops":            9,
    "file_ops":          10,
    "conversation":      99,
}

# Domain configs for compound classification.
# Separate from slot_taxonomy.json — that file governs slot resolution.
# Each domain:
#   signals:             regex patterns (each match scores +1)
#   enrichment_template: full guidance text injected as primary enrichment
#   brief_description:   single-line hint for secondary enrichment
DOMAIN_CONFIGS: dict = {
    "investigation": {
        "signals": [
            r"\binvestigat",
            r"\bresearch\b",
            r"\bwho\s+(?:is|are|owns?|controls?|runs?)\b",
            r"\bfind\s+(?:out|information|data)\b",
            r"\bbackground\s+on\b",
            r"\bdue\s+diligence\b",
            r"\bcredit\s+risk\b",
            r"\bosint\b",
            r"\blook\s+(?:into|up|at)\b",
            r"\bverif",
        ],
        "enrichment_template": (
            "Entity research methodology: verify primary sources, "
            "cross-reference data across multiple independent sources, "
            "flag gaps and contradictions. Report confidence levels."
        ),
        "brief_description": "Entity research methodology — verify sources, cross-reference data, flag gaps.",
    },
    "coding": {
        "signals": [
            r"\bwrite\s+(?:a\s+)?(?:function|class|script|module|code)\b",
            r"\bimplement\b",
            r"\bcode\s+(?:a|the|this)\b",
            r"\bgenerat\w+\s+(?:a\s+)?(?:function|class|code)\b",
            r"\bscaffold\b",
            r"\bcreate\s+(?:a\s+)?(?:function|class|script|module)\b",
            r"\bpython\b.{0,30}\bwrite\b|\bwrite\b.{0,30}\bpython\b",
        ],
        "enrichment_template": (
            "Code generation context: state the language and target file explicitly. "
            "Produce complete, runnable code only — no placeholders or stubs."
        ),
        "brief_description": "Tool syntax precision and parameter accuracy matter for this task.",
    },
    "bugfix": {
        "signals": [
            r"\bfix\b",
            r"\bbug\b",
            r"\berror\b",
            r"\bfailing\b",
            r"\bbroken\b",
            r"\bexception\b",
            r"\bcrash\w*\b",
            r"\btraceback\b",
            r"\bdebug\b",
            r"\bnot\s+work",
            r"\bissue\b",
        ],
        "enrichment_template": (
            "Bug isolation methodology: reproduce the failure, read error messages "
            "and tracebacks completely, isolate the failure point before attempting "
            "fixes. Check logs first."
        ),
        "brief_description": "Isolate the failure point before attempting fixes. Check logs first.",
    },
    "analysis": {
        "signals": [
            r"\banalyz",
            r"\banalysi",
            r"\bexamin",
            r"\bevaluat",
            r"\bassess",
            r"\bcompar",
            r"\breview\b",
            r"\bmetric",
            r"\bstatistic",
            r"\btrend\b",
            r"\bperformance\b",
            r"\bbenchmark",
        ],
        "enrichment_template": (
            "Analytical methodology: quantitative rigor required — cite specific "
            "metrics and data, not impressions. Distinguish correlation from causation."
        ),
        "brief_description": "Quantitative rigor required — cite specific metrics, not impressions.",
    },
    "system_admin": {
        "signals": [
            r"\binstall\b",
            r"\bservice\b",
            r"\bdaemon\b",
            r"\bsystemctl\b",
            r"\bsudo\b",
            r"\bpermission",
            r"\bchmod\b",
            r"\bchown\b",
            r"\bmount\b",
            r"\bnetwork\b",
            r"\bfirewall\b",
            r"\bapt\b|\byum\b|\bpip\b",
        ],
        "enrichment_template": (
            "System configuration context: check paths, permissions, and service "
            "status before making changes. Verify changes don't affect running services."
        ),
        "brief_description": "System configuration context — check paths, permissions, and service status.",
    },
    "planning": {
        "signals": [
            r"\bplan\b",
            r"\bstrateg",
            r"\broadmap\b",
            r"\barchitect",
            r"\bdesign\b",
            r"\bapproach\b",
            r"\bsteps?\s+(?:for|to)\b",
            r"\bhow\s+(?:should|do|can)\s+we\b",
            r"\bbest\s+(?:way|approach|practice)\b",
            r"\bsprint\b",
            r"\bbacklog\b",
        ],
        "enrichment_template": (
            "Planning context: sequence dependencies and resource constraints before "
            "committing to a plan. Identify blockers and critical path."
        ),
        "brief_description": "Sequence dependencies and resource constraints before committing to a plan.",
    },
    "config_edit": {
        "signals": [
            r"\bconfig\b",
            r"\bsetting",
            r"\b\.env\b",
            r"\byaml\b|\bjson\b|\btoml\b|\bini\b",
            r"\bparameter",
            r"\benvironment\s+variable",
        ],
        "enrichment_template": (
            "Configuration edit context: read-merge-write only, never overwrite "
            "config files wholesale. Verify syntax before saving."
        ),
        "brief_description": "Read-merge-write only. Verify syntax before saving.",
    },
    "prompt_engineering": {
        "signals": [
            r"\bprompt\b",
            r"\bsystem\s+(?:message|prompt)\b",
            r"\binstruction\b",
            r"\bfew[- ]shot\b",
            r"\bchain[- ]of[- ]thought\b",
            r"\bllm\b",
        ],
        "enrichment_template": (
            "Prompt engineering context: precision of wording affects model behavior. "
            "Test edge cases."
        ),
        "brief_description": "Precision of wording affects model behavior. Test edge cases.",
    },
    "git_ops": {
        "signals": [
            r"\bgit\b",
            r"\bcommit\b",
            r"\bbranch\b",
            r"\bmerge\b",
            r"\brebase\b",
            r"\bpull\s+request\b|\bpr\b",
            r"\brepository\b|\brepo\b",
        ],
        "enrichment_template": (
            "Git operations context: verify current branch and status before "
            "destructive operations."
        ),
        "brief_description": "Verify current branch and status before destructive operations.",
    },
    "file_ops": {
        "signals": [
            r"\bls\b|\bdir\b",
            r"\bcat\b|\bread\s+(?:the\s+)?file\b",
            r"\bcp\b|\bcopy\s+(?:the\s+)?file\b",
            r"\bmv\b|\bmove\s+(?:the\s+)?file\b",
            r"\brm\b|\bdelete\s+(?:the\s+)?file\b",
            r"\blist\s+(?:files|directory|dir)\b",
        ],
        "enrichment_template": (
            "File operations context: verify paths exist before operations. "
            "Be careful with destructive operations."
        ),
        "brief_description": "Verify paths exist before operations.",
    },
    "conversation": {
        "signals": [
            r"\bthank\w*\b",
            r"\bhello\b|\bhi\b|\bhey\b",
            r"\bwhat\s+(?:do|can)\s+you\b",
            r"\bcan\s+you\s+help\b",
        ],
        "enrichment_template": "",
        "brief_description": "General conversational context.",
    },
}

# Pre-compile all signal patterns at module load for performance.
_COMPILED_DOMAIN_CONFIGS: dict = {}
for _dname, _dcfg in DOMAIN_CONFIGS.items():
    _COMPILED_DOMAIN_CONFIGS[_dname] = {
        **_dcfg,
        "_signals_rx": [re.compile(s, re.IGNORECASE) for s in _dcfg["signals"]],
    }


# ── Compound classification dataclass ─────────────────────────────────────────

@dataclass
class CompoundClassification:
    primary_domain:       str
    primary_confidence:   int
    primary_signals:      list
    secondary_domain:     str | None
    secondary_confidence: int | None
    secondary_signals:    list | None
    compound_signature:   str
    momentum_turns:       int
    enrichment_plan:      dict

    def to_dict(self) -> dict:
        return {
            "primary": {
                "domain":          self.primary_domain,
                "confidence":      self.primary_confidence,
                "matched_signals": self.primary_signals,
            },
            "secondary": {
                "domain":          self.secondary_domain,
                "confidence":      self.secondary_confidence,
                "matched_signals": self.secondary_signals,
            } if self.secondary_domain else None,
            "compound_signature": self.compound_signature,
            "momentum_turns":     self.momentum_turns,
            "enrichment_plan":    self.enrichment_plan,
        }


# ── Compound classification functions ─────────────────────────────────────────

def _score_all_domains(message: str) -> list:
    """Score every domain against message using pre-compiled regex.

    Returns list of (domain_name, score, matched_patterns), sorted by:
      1. Score descending
      2. Domain priority ascending (tiebreaker)

    Only domains with score > 0 are included.
    """
    scores = []
    for domain_name, config in _COMPILED_DOMAIN_CONFIGS.items():
        matched = []
        for rx in config["_signals_rx"]:
            if rx.search(message):
                matched.append(rx.pattern)
        if matched:
            scores.append((domain_name, len(matched), matched))
    scores.sort(key=lambda x: (-x[1], DOMAIN_PRIORITY.get(x[0], 99)))
    return scores


def _extract_compound(scores: list) -> tuple:
    """Extract primary and optional secondary from score list.

    Primary = highest scoring domain. Always present (defaults to conversation).
    Secondary = second highest, IF score >= SECONDARY_MIN_SIGNALS.
    """
    if not scores:
        return {"domain": "conversation", "confidence": 0, "matched_signals": []}, None

    primary = {
        "domain":          scores[0][0],
        "confidence":      scores[0][1],
        "matched_signals": scores[0][2],
    }
    secondary = None
    if len(scores) > 1 and scores[1][1] >= SECONDARY_MIN_SIGNALS:
        secondary = {
            "domain":          scores[1][0],
            "confidence":      scores[1][1],
            "matched_signals": scores[1][2],
        }
    return primary, secondary


def _format_signature(primary: dict, secondary: dict | None) -> str:
    """Format compound signature string. Alphabetical order ensures symmetry."""
    if secondary:
        domains = sorted([primary["domain"], secondary["domain"]])
        return f"{domains[0]}+{domains[1]}"
    return primary["domain"]


def _parse_signature(signature: str) -> set:
    """Extract domain set from compound signature string."""
    return set(signature.split("+"))


def _restore_from_signature(
    signature: str,
    new_primary: dict,
    new_secondary: dict | None,
) -> tuple:
    """Restore classification from current signature using new confidence values.

    Keeps domain assignment stable while allowing confidence to reflect
    current turn's signals.
    """
    domains = _parse_signature(signature)
    if len(domains) == 1:
        domain = domains.pop()
        return {
            "domain":          domain,
            "confidence":      new_primary["confidence"],
            "matched_signals": new_primary["matched_signals"],
        }, None

    if new_primary["domain"] in domains:
        other_domain = (domains - {new_primary["domain"]}).pop()
        restored_secondary = {
            "domain": other_domain,
            "confidence": (
                new_secondary["confidence"]
                if new_secondary and new_secondary["domain"] == other_domain
                else 0
            ),
            "matched_signals": (
                new_secondary["matched_signals"]
                if new_secondary and new_secondary["domain"] == other_domain
                else []
            ),
        }
        return new_primary, restored_secondary
    else:
        domain_list = sorted(domains)
        return (
            {"domain": domain_list[0], "confidence": 0, "matched_signals": []},
            {"domain": domain_list[1], "confidence": 0, "matched_signals": []},
        )


def _apply_compound_momentum(
    new_primary: dict,
    new_secondary: dict | None,
    current_signature: str,
    current_momentum: int,
) -> tuple:
    """Apply compound momentum rules.

    Returns (final_primary, final_secondary, final_signature, final_momentum).

    Rules:
    1. Same signature → increment momentum.
    2. Weak momentum (< threshold) → accept new classification.
    3. Strong momentum (>= threshold):
         - New primary IN current compound → hold current, increment.
         - New primary NOT in current compound → break momentum, accept new.
    """
    new_signature = _format_signature(new_primary, new_secondary)

    if new_signature == current_signature:
        return new_primary, new_secondary, new_signature, current_momentum + 1

    if current_momentum >= MOMENTUM_THRESHOLD:
        current_domains = _parse_signature(current_signature)
        if new_primary["domain"] in current_domains:
            restored_primary, restored_secondary = _restore_from_signature(
                current_signature, new_primary, new_secondary
            )
            return restored_primary, restored_secondary, current_signature, current_momentum + 1
        else:
            return new_primary, new_secondary, new_signature, 1
    else:
        return new_primary, new_secondary, new_signature, 1


def _build_enrichment_plan(
    primary: dict,
    secondary: dict | None,
    model_profile: dict | None,
) -> dict:
    """Determine enrichment based on primary/secondary domains and model profile.

    Primary enrichment: ON unless primary domain in profile's disabled_domains.
    Secondary enrichment: ON if secondary exists and is not disabled.
    """
    disabled: set = set()
    if model_profile:
        disabled = set(model_profile.get("disabled_domains", []))

    plan = {
        "primary_enrichment":       primary["domain"] not in disabled,
        "secondary_enrichment":     False,
        "reason_primary_skipped":   None,
        "reason_secondary_skipped": None,
    }

    if primary["domain"] in disabled:
        plan["reason_primary_skipped"] = "disabled_in_profile"

    if secondary is None:
        plan["reason_secondary_skipped"] = "no_secondary_classified"
    elif secondary["domain"] in disabled:
        plan["reason_secondary_skipped"] = "disabled_in_profile"
    else:
        plan["secondary_enrichment"] = True

    return plan


def _generate_enrichment(classification: "CompoundClassification") -> str:
    """Generate enrichment text to prepend to model context.

    Primary: full enrichment template.
    Secondary: single abbreviated line.
    Returns empty string if nothing to inject.
    """
    plan  = classification.enrichment_plan
    parts = []

    if plan["primary_enrichment"]:
        template = DOMAIN_CONFIGS.get(classification.primary_domain, {}).get("enrichment_template", "")
        if template:
            parts.append(f"[BST] Domain: {classification.primary_domain}")
            parts.append(template)

    if plan["secondary_enrichment"] and classification.secondary_domain:
        brief = DOMAIN_CONFIGS.get(classification.secondary_domain, {}).get(
            "brief_description",
            f"{classification.secondary_domain} context is also relevant.",
        )
        parts.append(f"[BST] Secondary context: {classification.secondary_domain} — {brief}")

    if plan["reason_primary_skipped"]:
        parts.append(
            f"[BST] Primary domain '{classification.primary_domain}' enrichment skipped: "
            f"{plan['reason_primary_skipped']}"
        )
    if plan["reason_secondary_skipped"] == "disabled_in_profile":
        parts.append(
            f"[BST] Secondary domain '{classification.secondary_domain}' enrichment skipped: "
            f"{plan['reason_secondary_skipped']}"
        )

    return "\n".join(parts)


def _load_model_profile(agent) -> dict | None:
    """Load eval profile for current model. Returns None if not found (permissive default)."""
    try:
        config     = getattr(agent, "config", None)
        model_name = getattr(config, "chat_model", "") if config else ""
        if not model_name:
            return None
        profile_path = Path(f"/a0/usr/profiles/{model_name}.json")
        if profile_path.exists():
            with open(profile_path) as f:
                return json.load(f)
    except Exception:
        pass
    return None


# ── Extension class ───────────────────────────────────────────────────────────

class BeliefStateTracker(Extension):
    """Agent-Zero extension: before_main_llm_call"""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
        try:
            # Find the last user message (dict format)
            user_msg = _get_last_user_message(loop_data.history_output)

            if not user_msg:
                return

            message = user_msg.get('content', '')
            if isinstance(message, dict):
                message = message.get('user_message', '') or message.get('message', '') or str(message)
            message = str(message).strip()

            if not message:
                return

            # ── Compound classification ───────────────────────────────────────
            scores      = _score_all_domains(message)
            new_primary, new_secondary = _extract_compound(scores)

            # Load compound momentum state from agent store
            bst_store         = getattr(self.agent, "_bst_store", {}) or {}
            current_signature = bst_store.get("_compound_sig", "conversation")
            current_momentum  = bst_store.get("_compound_turns", 0)

            # Capture raw signature before momentum for hold/break logging
            raw_signature = _format_signature(new_primary, new_secondary)

            # Apply compound momentum
            final_primary, final_secondary, final_signature, final_momentum = \
                _apply_compound_momentum(
                    new_primary, new_secondary, current_signature, current_momentum
                )

            # Detect momentum hold and break events for logging
            momentum_held  = (
                current_momentum >= MOMENTUM_THRESHOLD
                and raw_signature != current_signature
                and final_signature == current_signature
            )
            momentum_broke = (
                current_momentum >= MOMENTUM_THRESHOLD
                and final_signature != current_signature
            )

            # Load model profile and build enrichment plan
            model_profile   = _load_model_profile(self.agent)
            enrichment_plan = _build_enrichment_plan(final_primary, final_secondary, model_profile)

            # Build CompoundClassification
            compound_cls = CompoundClassification(
                primary_domain       = final_primary["domain"],
                primary_confidence   = final_primary["confidence"],
                primary_signals      = final_primary["matched_signals"],
                secondary_domain     = final_secondary["domain"]          if final_secondary else None,
                secondary_confidence = final_secondary["confidence"]      if final_secondary else None,
                secondary_signals    = final_secondary["matched_signals"] if final_secondary else None,
                compound_signature   = final_signature,
                momentum_turns       = final_momentum,
                enrichment_plan      = enrichment_plan,
            )

            # Persist compound momentum state
            if not hasattr(self.agent, "_bst_store") or self.agent._bst_store is None:
                self.agent._bst_store = {}
            self.agent._bst_store["_compound_sig"]   = final_signature
            self.agent._bst_store["_compound_turns"] = final_momentum

            # Write to extras_persistent (backward-compat key + new compound key)
            ep = getattr(loop_data, "extras_persistent", None)
            if ep is None:
                loop_data.extras_persistent = {}
                ep = loop_data.extras_persistent
            ep["_bst_domain"]   = compound_cls.primary_domain
            ep["_bst_compound"] = compound_cls.to_dict()

            # ── Logging ───────────────────────────────────────────────────────
            sec_str    = (
                f" + {final_secondary['domain']} ({final_secondary['confidence']} signal"
                f"{'s' if final_secondary['confidence'] != 1 else ''})"
                if final_secondary else ""
            )
            enrich_str = (
                f"primary={'ON' if enrichment_plan['primary_enrichment'] else 'OFF'} "
                f"secondary={'ON' if enrichment_plan['secondary_enrichment'] else 'OFF'}"
            )
            self.agent.context.log.log(
                type="info",
                content=(
                    f"[BST] {final_primary['domain']} ({final_primary['confidence']} signal"
                    f"{'s' if final_primary['confidence'] != 1 else ''})"
                    f"{sec_str} | sig={final_signature} | momentum={final_momentum} "
                    f"| enrichment: {enrich_str}"
                ),
            )

            if momentum_held:
                self.agent.context.log.log(
                    type="info",
                    content=(
                        f"[BST] Momentum held: {current_signature} ({current_momentum} turns) "
                        f"resisted {raw_signature} ({new_primary['confidence']} signal"
                        f"{'s' if new_primary['confidence'] != 1 else ''})"
                    ),
                )
            elif momentum_broke:
                self.agent.context.log.log(
                    type="info",
                    content=(
                        f"[BST] Momentum break: {current_signature} ({current_momentum} turns) "
                        f"→ {final_signature} ({final_primary['confidence']} signal"
                        f"{'s' if final_primary['confidence'] != 1 else ''}, not in compound)"
                    ),
                )

            if enrichment_plan.get("reason_secondary_skipped") == "disabled_in_profile":
                config     = getattr(self.agent, "config", None)
                model_name = getattr(config, "chat_model", "") if config else ""
                self.agent.context.log.log(
                    type="info",
                    content=(
                        f"[BST] Secondary enrichment skipped for "
                        f"{compound_cls.secondary_domain}: disabled_in_profile ({model_name})"
                    ),
                )

            # Generate compound enrichment text
            compound_enrichment = _generate_enrichment(compound_cls)

            # ── Slot resolution (unchanged) ───────────────────────────────────
            tracker = _BSTEngine(self.agent)
            result  = tracker.process(message)

            # ── Apply enrichment ──────────────────────────────────────────────
            if result["action"] == "enrich":
                slot_message = result["enriched_message"]
                user_msg['content'] = (
                    compound_enrichment + "\n\n" + slot_message
                    if compound_enrichment else slot_message
                )
                self.agent.context.log.log(
                    type="info",
                    content=f"[BST] Slots: {result['filled_slots']}",
                )

            elif result["action"] == "clarify":
                user_msg['content'] = (
                    f"[CLARIFICATION NEEDED]\n"
                    f"Original: {message}\n\n"
                    f"Ask user: \"{result['question']}\"\n"
                    f"Wait for answer before proceeding."
                )
                self.agent.context.log.log(
                    type="info",
                    content=f"[BST] Clarifying - Domain: {result['domain']} | Missing: {result['missing_slot']}",
                )

            elif compound_enrichment:
                # Slot resolver returned passthrough but compound has enrichment
                user_msg['content'] = compound_enrichment + "\n\n[USER MESSAGE]\n" + message

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[BST] Error (passthrough): {e}",
                )
            except Exception:
                pass


# ── Message extraction ────────────────────────────────────────────────────────

def _get_last_user_message(history_output: list):
    """Find last user message in agent-zero's dict format."""
    if not history_output:
        return None

    for msg in reversed(history_output):
        if not isinstance(msg, dict):
            continue

        # Skip AI messages
        if msg.get('ai', True):
            continue

        content = msg.get('content', '')

        # Handle dict content with 'user_message' key
        if isinstance(content, dict):
            if 'user_message' in content:
                return msg
            # Skip tool results
            if 'tool_name' in content:
                continue

        # Handle plain string content
        if isinstance(content, str) and content.strip():
            return msg

    return None


# ── Slot resolution engine (unchanged from v3) ────────────────────────────────

class _BSTEngine:
    """Core belief state tracking logic."""

    def __init__(self, agent):
        self.agent    = agent
        self.taxonomy = self._load_taxonomy()
        self.globs    = self.taxonomy.get("global", {})

    def process(self, message: str) -> dict:
        """Main entry point — classify and resolve slots."""

        # Check for underspecified follow-up
        if self._is_underspecified(message):
            belief = self._get_persisted_belief()
            if belief:
                return self._handle_underspecified(message, belief)

        # Classify domain
        domain_name, confidence = self._classify(message)

        if domain_name == "conversational" or not domain_name:
            self._clear_belief()
            return {"action": "passthrough", "domain": "conversational"}

        domain  = self.taxonomy["domains"][domain_name]
        history = self._get_history_text()

        belief = {
            "domain":           domain_name,
            "turn":             self._current_turn(),
            "slots":            {},
            "missing_required": [],
            "confidence":       confidence,
        }

        # Resolve required slots
        for slot_name in domain.get("required_slots", []):
            slot_def = domain["slot_definitions"].get(slot_name, {})
            value    = self._resolve_slot(slot_name, slot_def, message, history)

            if value is None and not self._is_conditionally_required(slot_name, slot_def, belief["slots"]):
                continue

            belief["slots"][slot_name] = value
            if value is None and not slot_def.get("nullable", True):
                belief["missing_required"].append(slot_name)

        # Resolve optional slots
        for slot_name in domain.get("optional_slots", []):
            slot_def = domain["slot_definitions"].get(slot_name, {})
            value    = self._resolve_slot(slot_name, slot_def, message, history)
            if value is not None:
                belief["slots"][slot_name] = value

        # Recompute confidence from slot fill rate
        required_count = len(domain.get("required_slots", []))
        if required_count > 0:
            filled    = required_count - len(belief["missing_required"])
            slot_conf = filled / required_count
            belief["confidence"] = (confidence * 0.4) + (slot_conf * 0.6)
        else:
            belief["confidence"] = confidence

        self._persist_belief(belief)

        threshold = domain.get("confidence_threshold", 0.7)

        # Below threshold — ask for missing slot
        if belief["confidence"] < threshold and belief["missing_required"]:
            asked = belief.get("clarifications_asked", 0)
            max_q = self.globs.get("max_clarification_questions", 2)
            if asked < max_q:
                missing_slot = belief["missing_required"][0]
                slot_def     = domain["slot_definitions"].get(missing_slot, {})
                question     = slot_def.get("question", f"What is the {missing_slot.replace('_', ' ')}?")

                if question:
                    belief["clarifications_asked"] = asked + 1
                    self._persist_belief(belief)
                    return {
                        "action":       "clarify",
                        "domain":       domain_name,
                        "missing_slot": missing_slot,
                        "question":     question,
                        "confidence":   belief["confidence"],
                    }

        # Confidence sufficient — enrich
        return {
            "action":           "enrich",
            "domain":           domain_name,
            "confidence":       belief["confidence"],
            "filled_slots":     [k for k, v in belief["slots"].items() if v is not None],
            "enriched_message": self._enrich_message(message, domain, belief),
        }

    def _classify(self, message: str) -> tuple:
        """Classify message into taxonomy domain."""
        msg_lower = message.lower()
        min_len   = self.globs.get("min_trigger_word_length", 3)
        scores    = {}

        for domain_name, domain in self.taxonomy["domains"].items():
            if domain_name == "conversational":
                continue
            triggers = domain.get("triggers", [])
            hits     = sum(1 for t in triggers if len(t) >= min_len and t in msg_lower)
            if hits > 0:
                weight = sum(len(t.split()) for t in triggers if t in msg_lower)
                scores[domain_name] = hits + (weight * 0.1)

        if not scores:
            return "conversational", 1.0

        best       = max(scores, key=lambda k: scores[k])
        raw_max    = max(scores.values())
        confidence = min(1.0, raw_max / max(3.0, raw_max + 1))
        return best, confidence

    def _resolve_slot(self, slot_name: str, slot_def: dict, message: str, history: str) -> Any:
        """Resolve slot value using resolver chain."""
        resolvers   = slot_def.get("resolvers", [])
        keyword_map = slot_def.get("keyword_map", {})
        msg_lower   = message.lower()

        for resolver in resolvers:
            if resolver == "keyword_map" and keyword_map:
                for keyword, mapped in keyword_map.items():
                    if keyword in msg_lower:
                        return mapped

            elif resolver == "file_extension_inference":
                ext_map  = self.globs.get("file_extensions", {})
                combined = message + " " + history
                for ext, lang in ext_map.items():
                    if ext in combined:
                        return lang

            elif resolver == "last_mentioned_file":
                ref = self._extract_file_ref(message + " " + history[:500])
                if ref:
                    return ref

            elif resolver == "last_mentioned_path":
                ref = self._extract_path_ref(message + " " + history[:500])
                if ref:
                    return ref

            elif resolver == "last_mentioned_entity":
                entity = self._extract_entity(message)
                if entity:
                    return entity

            elif resolver == "history_scan":
                hit = self._scan_history_for_slot(slot_name, history)
                if hit:
                    return hit

            elif resolver == "context_inference":
                value = self._inline_context_resolve(slot_name, slot_def, message)
                if value:
                    return value

            elif resolver == "working_memory_lookup":
                hit = self._working_memory_lookup(slot_name, message)
                if hit:
                    return hit

        return slot_def.get("default")

    def _is_conditionally_required(self, slot_name: str, slot_def: dict, current_slots: dict) -> bool:
        rw = slot_def.get("required_when")
        if not rw:
            return False
        for key, values in rw.items():
            if isinstance(values, list):
                if current_slots.get(key) in values:
                    return True
            else:
                if current_slots.get(key) == values:
                    return True
        return False

    def _enrich_message(self, original: str, domain: dict, belief: dict) -> str:
        lines  = []
        filled = {k: v for k, v in belief["slots"].items() if v is not None}
        if filled:
            slot_lines = "\n".join(f"  {k}: {v}" for k, v in filled.items())
            lines.append(f"[TASK CONTEXT]\n{slot_lines}")
        preamble = domain.get("preamble")
        if preamble:
            lines.append(f"[INSTRUCTION]\n{preamble}")
        lines.append(f"[USER MESSAGE]\n{original}")
        return "\n\n".join(lines)

    def _is_underspecified(self, message: str) -> bool:
        msg_lower = message.lower().strip()
        pronouns  = self.globs.get("ambiguous_pronouns", [])
        phrases   = self.globs.get("underspec_phrases", [])
        words     = msg_lower.split()
        if len(words) <= 5 and any(p in msg_lower for p in pronouns):
            return True
        return any(ph in msg_lower for ph in phrases)

    def _handle_underspecified(self, message: str, belief: dict) -> dict:
        domain_name = belief.get("domain", "conversational")
        if domain_name not in self.taxonomy["domains"]:
            return {"action": "passthrough", "domain": "conversational"}

        domain   = self.taxonomy["domains"][domain_name]
        preamble = domain.get("preamble", "")
        filled   = {k: v for k, v in belief.get("slots", {}).items() if v is not None}

        lines = [f"[CONTINUING TASK — Domain: {domain_name}]"]
        if filled:
            lines.append("[PRIOR CONTEXT]\n" + "\n".join(f"  {k}: {v}" for k, v in filled.items()))
        if preamble:
            lines.append(f"[INSTRUCTION]\n{preamble}")
        lines.append(f"[USER MESSAGE]\n{message}")

        return {
            "action":           "enrich",
            "domain":           domain_name,
            "confidence":       belief.get("confidence", 0.7),
            "filled_slots":     list(filled.keys()),
            "enriched_message": "\n\n".join(lines),
        }

    def _persist_belief(self, belief: dict) -> None:
        try:
            if not hasattr(self.agent, "_bst_store"):
                self.agent._bst_store = {}
            self.agent._bst_store[BELIEF_KEY] = belief
        except Exception:
            pass

    def _get_persisted_belief(self) -> dict | None:
        try:
            store  = getattr(self.agent, "_bst_store", {})
            belief = store.get(BELIEF_KEY)
            if not belief:
                return None
            ttl = self.globs.get("belief_state_ttl_turns", 6)
            if self._current_turn() - belief.get("turn", 0) > ttl:
                self._clear_belief()
                return None
            return belief
        except Exception:
            return None

    def _clear_belief(self) -> None:
        try:
            store = getattr(self.agent, "_bst_store", {})
            store.pop(BELIEF_KEY, None)
        except Exception:
            pass

    def _get_history_text(self) -> str:
        try:
            msgs   = self.agent.history or []
            recent = msgs[-MAX_HISTORY_SCAN_TURNS:]
            parts  = []
            for m in recent:
                content = getattr(m, "content", "") or ""
                if isinstance(content, list):
                    content = " ".join(
                        p.get("text", "") if isinstance(p, dict) else str(p)
                        for p in content
                    )
                parts.append(str(content))
            return " ".join(parts)
        except Exception:
            return ""

    def _current_turn(self) -> int:
        try:
            return len(self.agent.history or [])
        except Exception:
            return 0

    def _extract_file_ref(self, text: str) -> str | None:
        patterns = [
            r'`([^`]+\.[a-zA-Z]{1,5})`',
            r'"([^"]+\.[a-zA-Z]{1,5})"',
            r"'([^']+\.[a-zA-Z]{1,5})'",
            r'(\S+\.[a-zA-Z]{1,5})',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[-1]
        return None

    def _extract_path_ref(self, text: str) -> str | None:
        patterns = [
            r'(/[a-zA-Z0-9_\-\.]+(?:/[a-zA-Z0-9_\-\.]+)+)',
            r'(~/[a-zA-Z0-9_\-\./]+)',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[-1]
        return None

    def _extract_entity(self, text: str) -> str | None:
        for pattern in [r'`([^`]+)`', r'"([^"]+)"', r"'([^']+)'"]:
            matches = re.findall(pattern, text)
            if matches:
                return matches[-1]
        return None

    def _scan_history_for_slot(self, slot_name: str, history: str) -> str | None:
        if any(k in slot_name for k in ["file", "path", "source", "target", "script"]):
            return self._extract_file_ref(history) or self._extract_path_ref(history)
        return None

    def _inline_context_resolve(self, slot_name: str, slot_def: dict, message: str) -> Any:
        msg_lower = message.lower()

        if slot_name == "language":
            for ext, lang in self.globs.get("file_extensions", {}).items():
                if lang in msg_lower:
                    return lang

        if slot_def.get("type") == "bool":
            if any(w in msg_lower for w in ["no", "don't", "do not", "ignore", "skip", "without"]):
                return False
            if any(w in msg_lower for w in ["yes", "always", "keep", "preserve", "maintain"]):
                return True

        if slot_def.get("type") == "enum":
            for val in slot_def.get("enum_values", []):
                if val in msg_lower:
                    return val

        return None

    def _working_memory_lookup(self, slot_name: str, message: str) -> Any:
        """Check working memory buffer for recently mentioned entities.

        Search order:
        1. Promoted entities (3+ mentions, most valuable) — most recent first
        2. Active entities — most recent first (sorted by turn descending)
        """
        try:
            wm = getattr(self.agent, "_working_memory", None)
            if not wm:
                return None

            slot_to_entity = {
                "target_file":        ["file"],
                "source_file":        ["file"],
                "source_path":        ["path", "file"],
                "destination_path":   ["path"],
                "target":             ["path", "file", "container", "service", "url"],
                "container_name":     ["container"],
                "image_name":         ["image"],
                "endpoint":           ["url"],
                "log_source":         ["path", "file"],
                "config_key":         ["config_key"],
                "package_name":       ["package"],
                "branch_name":        ["branch"],
            }
            entity_types = slot_to_entity.get(slot_name)
            if not entity_types:
                return None

            etypes_set = set(entity_types)

            # 1. Search promoted entities first (highest value)
            promoted = wm.get("promoted", {})
            if promoted:
                best_val  = None
                best_turn = -1
                for value, info in promoted.items():
                    if info.get("type") in etypes_set and info.get("last_turn", 0) > best_turn:
                        best_turn = info["last_turn"]
                        best_val  = value
                if best_val is not None:
                    return best_val

            # 2. Search active entities, most recent first
            entities = wm.get("entities", [])
            if entities:
                candidates = [e for e in entities if e.get("type") in etypes_set]
                if candidates:
                    candidates.sort(key=lambda e: e.get("turn", 0), reverse=True)
                    return candidates[0].get("value")

        except Exception:
            pass
        return None

    @staticmethod
    def _load_taxonomy() -> dict:
        if not TAXONOMY_PATH.exists():
            raise FileNotFoundError(f"[BST] slot_taxonomy.json not found at {TAXONOMY_PATH}")
        with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
