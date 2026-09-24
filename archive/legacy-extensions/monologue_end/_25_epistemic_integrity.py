"""
Epistemic Integrity Layer — Truth Audit on Model Output
=======================================================
Hook: monologue_end (_25_)

Three-component deterministic audit on the model's last response:

  1. Provenance — did this value appear in a tool output this session?
     (Evidence Ledger, populated by _25_ tool_execute_after recorder)
  2. Volatility — how fast does this type of claim change in the real world?
     (Signal patterns + BST domain defaults)
  3. Staleness — how far is "now" from the model's training cutoff?
     (Loaded from model profile temporal section)

Verdict matrix (grounded × volatility class):
  GROUNDED                   → TRUST
  UNGROUNDED + structural    → LIKELY_VALID
  UNGROUNDED + institutional → VERIFY_IF_CRITICAL
  UNGROUNDED + cyclical      → DO_NOT_TRUST
  UNGROUNDED + transactional → FABRICATION_RISK
  UNGROUNDED + ephemeral     → FABRICATION_BY_DEFINITION

No LLM calls. Fully deterministic.

Motivated by ST-003: the agent fabricated a complete Oracle credit risk
report with zero source data, expressed "High confidence — data from SEC
filings and Bloomberg snapshots." Every figure was wrong. Confabulation
isn't a choice the model makes — it's architectural. The system catches it.

Reads:
  agent._evidence_ledger              (from _25_ tool_execute_after recorder)
  /a0/usr/settings.json               (chat_model_name for profile lookup)
  /a0/usr/Exocortex/eval/model_profiles/{model_id}.json  (temporal section)
  agent._bst_store                    (domain for volatility defaults)

Writes:
  agent._epistemic_integrity          (summary dict for supervisor/downstream)
  hist_add_warning                    (≥1 ungrounded cyclical/transactional/ephemeral)
"""

import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from agent import LoopData
from helpers.extension import Extension

# ── Constants ─────────────────────────────────────────────────────────────────

LEDGER_KEY = "_evidence_ledger"
EI_KEY = "_epistemic_integrity"

# Characters of surrounding text captured per match for volatility classification
CONTEXT_WINDOW = 150

# Minimum ungrounded high-risk claims before hist_add_warning fires
MIN_HIGH_RISK_FOR_WARNING = 1

SETTINGS_PATH = "/a0/usr/settings.json"
PROFILE_ROOT = "/a0/usr/Exocortex/eval/model_profiles"

# Ordered most → least volatile
VOLATILITY_ORDER = ["ephemeral", "transactional", "cyclical", "institutional", "structural"]

# Verdict for ungrounded claims
VERDICT_UNGROUNDED = {
    "ephemeral":     "FABRICATION_BY_DEFINITION",
    "transactional": "FABRICATION_RISK",
    "cyclical":      "DO_NOT_TRUST",
    "institutional": "VERIFY_IF_CRITICAL",
    "structural":    "LIKELY_VALID",
}

HIGH_RISK_VERDICTS = {"FABRICATION_BY_DEFINITION", "FABRICATION_RISK", "DO_NOT_TRUST"}

# BST domain → default volatility class (most volatile wins for compound domains)
DOMAIN_DEFAULTS = {
    "investigation": "cyclical",
    "analysis":      "cyclical",
    "research":      "institutional",
    "coding":        "structural",
    "bugfix":        "structural",
    "system_admin":  "structural",
    "conversation":  "institutional",
    "planning":      "institutional",
}

# ── Volatility signal patterns (compiled at import, most volatile first) ───────

VOLATILITY_SIGNALS = {
    "ephemeral": {
        "patterns": [
            re.compile(r"(?i)(right now|currently trading|as of (today|this morning))"),
            re.compile(r"(?i)(spot price|market price|live|real-?time)"),
            re.compile(r"(?i)(latest|just (released|announced|reported))"),
            re.compile(r"(?i)(today'?s?|this (morning|afternoon|hour))"),
        ],
        "max_plausible_age_hours": 1,
    },
    "transactional": {
        "patterns": [
            re.compile(r"(?i)(issued|filed|reported|announced).{0,30}20\d{2}"),
            re.compile(r"(?i)(recent|new|upcoming)\s+(bond|issuance|offering|filing)"),
            re.compile(r"(?i)(downgrad|upgrad|revis|chang).{0,20}(rating|outlook)"),
            re.compile(r"(?i)(earnings|results|quarter).{0,15}(beat|miss|met|exceeded)"),
        ],
        "max_plausible_age_hours": 168,
    },
    "cyclical": {
        "patterns": [
            re.compile(r"(?i)\$[\d,.]+\s*(?:billion|million|trillion)"),
            re.compile(r"(?i)(revenue|income|earnings|EBITDA|FCF).{0,20}\d"),
            re.compile(r"(?i)(debt[- ]to[- ]equity|leverage|coverage)\s*(ratio)?\s*[~:]?\s*\d"),
            re.compile(r"(?i)\d+\.?\d*\s*%\s*(YoY|year[- ]over|growth|decline)"),
            re.compile(r"(?i)(Q[1-4]|FY)\s*20\d{2}"),
            re.compile(r"(?i)(total debt|outstanding debt|long[- ]term debt)"),
            re.compile(r"(?i)(market (cap|share|position)).{0,15}\d"),
        ],
        "max_plausible_age_hours": 2160,
    },
    "institutional": {
        "patterns": [
            re.compile(r"(?i)(rated|rating).{0,30}(Moody|S&P|Fitch|DBRS)"),
            re.compile(r"(?i)(CEO|CFO|CTO|chairman|president|director)\s+(is|was|named)"),
            re.compile(r"(?i)(headquartered|based|located)\s+in"),
            re.compile(r"(?i)(employees?|headcount|workforce).{0,15}\d{3,}"),
            re.compile(r"(?i)(subsidiary|division|segment)\s+(of|within)"),
        ],
        "max_plausible_age_hours": 8760,
    },
    "structural": {
        "patterns": [
            re.compile(r"(?i)(founded|established|incorporated)\s+in\s+\d{4}"),
            re.compile(r"(?i)(law|theorem|principle|constant|equation)\s+(of|states|is)"),
            re.compile(r"(?i)(protocol|standard|specification)\s+(defines|requires|is)"),
            re.compile(r"(?i)(always|never|by definition|fundamentally)"),
        ],
        "max_plausible_age_hours": 87600,
    },
}


# ── Extension class ────────────────────────────────────────────────────────────


class EpistemicIntegrity(Extension):
    """Deterministic truth audit on model output. No LLM calls."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
        try:
            self.agent.set_data(EI_KEY, {})
            # Benign default for the affect layer's DESPERATION signal (AFFECT_LAYER
            # Gap 2, option c). If this turn produces no checkable claims, the forwarded
            # verdict must not leave a stale "uncited" flag from a prior turn. Overwritten
            # below with the real verdict when claims are actually checked.
            self.agent.set_data("_ei_last_verdict", {
                "cited": True,
                "high_risk_count": 0,
                "turn": getattr(self.agent, "_step_budget_count", 0),
            })

            response_text = self._get_last_response()
            if not response_text or len(response_text.strip()) < 50:
                return

            ledger = self.agent.get_data(LEDGER_KEY) or {}
            ledger_values: set = set(ledger.get("key_values", []))
            has_sources = bool(ledger.get("entries"))

            profile = _load_model_profile()
            cutoff_dt = _parse_training_cutoff(profile)
            confab_risk = profile.get("temporal", {}).get("confabulation_risk", "unknown")
            bst_domain = _get_bst_domain(self.agent)
            session_now = datetime.now(timezone.utc)

            claims = _extract_claims(response_text)
            if not claims:
                return

            results = []
            for value, context_snippet in claims:
                grounded = value in ledger_values
                volatility = _classify_volatility(context_snippet, bst_domain)
                max_hours = VOLATILITY_SIGNALS[volatility]["max_plausible_age_hours"]
                staleness = _compute_staleness(session_now, cutoff_dt, max_hours)
                verdict = "TRUST" if grounded else VERDICT_UNGROUNDED[volatility]

                results.append({
                    "value": value,
                    "context": context_snippet[:120],
                    "grounded": grounded,
                    "volatility": volatility,
                    "staleness": round(staleness, 2),
                    "verdict": verdict,
                })

            grounded_count = sum(1 for r in results if r["grounded"])
            high_risk = [r for r in results if r["verdict"] in HIGH_RISK_VERDICTS]
            verify_list = [r for r in results if r["verdict"] == "VERIFY_IF_CRITICAL"]

            ei_result = {
                "total_claims": len(results),
                "grounded_count": grounded_count,
                "high_risk_count": len(high_risk),
                "verify_count": len(verify_list),
                "has_sources": has_sources,
                "confab_risk": confab_risk,
                "bst_domain": bst_domain,
                "claims": results,
            }

            self.agent.set_data(EI_KEY, ei_result)

            # Forward a compact verdict for the affect classifier (AFFECT_LAYER Gap 2,
            # option c). cited == no high-risk ungrounded claims. Read one turn later at
            # reasoning_stream_end as the DESPERATION uncited-assertion signal.
            self.agent.set_data("_ei_last_verdict", {
                "cited": len(high_risk) == 0,
                "high_risk_count": len(high_risk),
                "turn": getattr(self.agent, "_step_budget_count", 0),
            })

            self.agent.context.log.log(
                type="info",
                content=(
                    f"[EI] {len(results)} claims checked — "
                    f"{grounded_count} grounded, "
                    f"{len(high_risk)} high-risk ungrounded"
                ),
            )

            if len(high_risk) >= MIN_HIGH_RISK_FOR_WARNING:
                warning = _build_warning(ei_result, high_risk, verify_list)
                self.agent.hist_add_warning(warning)  # sync — no await

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[EI] Error (passthrough): {e}",
                )
            except Exception:
                pass

    def _get_last_response(self) -> str:
        """Extract text from the most recent AI response (tool_name=response) message."""
        try:
            for msg in reversed(self.agent.history.output()):
                if not msg.get("ai", False):
                    continue
                content = msg.get("content", "")
                if not content:
                    continue
                if isinstance(content, str):
                    try:
                        parsed = json.loads(content)
                        if isinstance(parsed, dict):
                            if parsed.get("tool_name") == "response":
                                text = parsed.get("tool_args", {}).get("text", "")
                                if text:
                                    return str(text)
                            # Other tool call — keep searching backward
                            continue
                    except (json.JSONDecodeError, ValueError):
                        # Raw text content — return directly
                        return content
                elif isinstance(content, list):
                    return " ".join(
                        p.get("text", "") if isinstance(p, dict) else str(p)
                        for p in content
                    )
        except Exception:
            pass
        return ""


# ── Module-level helpers ───────────────────────────────────────────────────────


def _get_bst_domain(agent) -> str:
    """Read BST domain. Returns 'primary+secondary' for compound classification."""
    try:
        store = getattr(agent, "_bst_store", {})
        belief = store.get("__bst_belief_state__", {})
        primary = belief.get("primary_domain") or belief.get("domain", "")
        secondary = belief.get("secondary_domain", "")
        if primary and secondary:
            return f"{primary}+{secondary}"
        return primary or ""
    except Exception:
        return ""


def _load_model_profile() -> dict:
    """Load model profile from settings → profile file. Returns {} on any error."""
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            settings = json.load(f)
        model_name = settings.get("chat_model_name", "")
        model_id = model_name.split("@")[0].strip()
        if not model_id:
            return {}
        profile_path = os.path.join(PROFILE_ROOT, f"{model_id}.json")
        if not os.path.exists(profile_path):
            profile_path = os.path.join(PROFILE_ROOT, "default.json")
            if not os.path.exists(profile_path):
                return {}
        with open(profile_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _parse_training_cutoff(profile: dict) -> datetime | None:
    """Return training cutoff datetime. Falls back to evaluated_at − 180 days."""
    try:
        temporal = profile.get("temporal", {})
        cutoff_str = temporal.get("training_data_cutoff")
        if cutoff_str:
            return datetime.fromisoformat(cutoff_str.replace("Z", "+00:00"))
        eval_str = profile.get("evaluated_at")
        if eval_str:
            return datetime.fromisoformat(eval_str.replace("Z", "+00:00")) - timedelta(days=180)
        return None
    except Exception:
        return None


def _extract_claims(text: str) -> list[tuple[str, str]]:
    """
    Extract (normalized_value, context_snippet) pairs from response text.
    Uses the same normalization as the Evidence Ledger Recorder so values match.
    Deduplicates by value — first occurrence's context is used for classification.
    """
    claims: list[tuple[str, str]] = []
    seen: set[str] = set()

    def _add(val: str, start: int, end: int) -> None:
        if val and val not in seen:
            seen.add(val)
            ctx = text[max(0, start - CONTEXT_WINDOW): end + CONTEXT_WINDOW]
            claims.append((val, ctx))

    # Currency with scale: $30 billion → $30B
    for m in re.finditer(r'\$[\d,.]+\s*(?:billion|million|trillion)\b', text, re.IGNORECASE):
        _add(_normalize_scale(m.group()), m.start(), m.end())

    # $BMT shorthand: $1.5B, $800M
    for m in re.finditer(r'\$[\d,.]+\s*[BMTbmt]\b', text):
        _add(m.group().strip().upper(), m.start(), m.end())

    # Large standalone dollar amounts: $30.5, $1,234
    for m in re.finditer(r'\$\d[\d,.]{2,}', text):
        _add(m.group().replace(',', ''), m.start(), m.end())

    # Percentages: 25.4%, 0.88%
    for m in re.finditer(r'\b\d+\.?\d*\s*%', text):
        _add(m.group().replace(' ', ''), m.start(), m.end())

    # Financial ratios: 1.5x, 2.8×
    for m in re.finditer(r'\b\d+\.?\d+\s*[x×]\b', text, re.IGNORECASE):
        _add(m.group().strip(), m.start(), m.end())

    # Credit ratings: AAA, AA+, Baa1, BBB-
    for m in re.finditer(
        r'\b(?:AAA|AA[+-]?|A[+-]?|BBB[+-]?|BB[+-]?|B[+-]?|Baa[1-3]|Ba[1-3]|B[1-3])\b',
        text,
    ):
        val = m.group()
        if len(val) >= 2:
            _add(val, m.start(), m.end())

    # Fiscal periods: Q3 2024, FY2025, 2024
    for m in re.finditer(r'\b(?:Q[1-4]\s+)?(?:FY\s*)?20\d{2}\b', text):
        _add(m.group().strip(), m.start(), m.end())

    return claims


def _normalize_scale(s: str) -> str:
    """Normalize: '$1.5 billion' → '$1.5B'  (mirrors Evidence Ledger Recorder)"""
    s = s.strip()
    for word, abbr in [('trillion', 'T'), ('billion', 'B'), ('million', 'M')]:
        if word.lower() in s.lower():
            num = re.search(r'[\d,.]+', s)
            if num:
                return f"${num.group().replace(',', '')}{abbr}"
    return s


def _classify_volatility(context_snippet: str, bst_domain: str) -> str:
    """
    Classify temporal volatility. Most volatile class whose pattern matches wins.
    Falls back to BST domain default; uses most volatile class if domain is compound.
    """
    for vol_class in VOLATILITY_ORDER:
        for pattern in VOLATILITY_SIGNALS[vol_class]["patterns"]:
            if pattern.search(context_snippet):
                return vol_class

    # No signal match — BST domain default (most volatile wins for compound)
    best = "institutional"
    for part in re.split(r'[+,/]', bst_domain or ""):
        part = part.strip().lower()
        d = DOMAIN_DEFAULTS.get(part)
        if d is not None and VOLATILITY_ORDER.index(d) < VOLATILITY_ORDER.index(best):
            best = d
    return best


def _compute_staleness(
    session_now: datetime,
    cutoff_dt: datetime | None,
    max_plausible_hours: int,
) -> float:
    """
    Staleness score [0.0, 1.0]:
      0.0 = within training window
      1.0 = well past plausible validity (≥ 2× max_plausible_hours since cutoff)
      0.5 = unknown cutoff (moderate skepticism)
    """
    if cutoff_dt is None:
        return 0.5
    hours = (session_now - cutoff_dt).total_seconds() / 3600
    if hours <= 0:
        return 0.0
    if hours >= max_plausible_hours * 2:
        return 1.0
    return min(1.0, hours / (max_plausible_hours * 2))


def _build_warning(
    ei_result: dict,
    high_risk: list[dict],
    verify_list: list[dict],
) -> str:
    """Build hist_add_warning message from EI findings."""
    total = ei_result["total_claims"]
    grounded = ei_result["grounded_count"]
    ungrounded = total - grounded
    confab_risk = ei_result.get("confab_risk", "unknown")
    has_sources = ei_result.get("has_sources", False)

    lines = [
        f"[EPISTEMIC CHECK] {grounded} of {total} claims grounded. {ungrounded} ungrounded.",
    ]

    if confab_risk in ("high", "very_high"):
        lines.append(f"  ⚠ Model confabulation risk: {confab_risk.upper()}.")

    if not has_sources:
        lines.append("  ⚠ No external data sources queried this session.")

    if high_risk:
        vol_classes = sorted(
            set(r["volatility"] for r in high_risk), key=VOLATILITY_ORDER.index
        )
        lines.append(
            f"  ⚠ {len(high_risk)} ungrounded claim(s) flagged: "
            + ", ".join(v.upper() for v in vol_classes)
            + "."
        )

    items = (high_risk + verify_list)[:8]
    if items:
        lines.append("")
        lines.append("  Claims requiring verification:")
        for r in items:
            staleness_pct = int(r["staleness"] * 100)
            v = r["volatility"].upper()
            lines.append(
                f'  - "{r["value"]}" — {v}, staleness {staleness_pct}%, no source'
            )

    return "\n".join(lines)
