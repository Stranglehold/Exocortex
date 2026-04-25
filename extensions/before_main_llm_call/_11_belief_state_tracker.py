"""
Belief State Tracker -- Agent-Zero Translation Layer v3
====================================================
Hook: before_main_llm_call

Works with agent-zero's dict-based message format.
Intercepts user messages before LLM call, classifies intent,
resolves slots, and enriches with structured context.

v3.1 -- Compound Classification Layer
--------------------------------------
- Scores all domains (score-all replaces first-match-wins).
- Emits primary + optional secondary domain.
- Tracks compound signature momentum across turns.
- Integrates model profile enrichment gating.
- Writes _bst_domain and _bst_compound to extras_persistent.
- Slot resolution pipeline (taxonomy / _BSTEngine) unchanged.
"""

import json

import sys as _sys
_PM_PATH = "/a0/usr/Exocortex"
if _PM_PATH not in _sys.path:
    _sys.path.insert(0, _PM_PATH)
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent import LoopData
from helpers.extension import Extension

TAXONOMY_PATH          = Path(__file__).parent / "slot_taxonomy.json"


def _log_injection_tokens(agent, ext_name: str, text: str) -> None:
    """Log estimated token count for an injection block. ~4 chars/token."""
    tok = len(text) // 4
    counts = getattr(agent, "_injection_token_counts", {})
    counts[ext_name] = counts.get(ext_name, 0) + tok
    agent._injection_token_counts = counts
    print(f"[TOKEN-COUNT] {ext_name}: ~{tok} tokens injected", flush=True)
BELIEF_KEY             = "__bst_belief_state__"
MAX_HISTORY_SCAN_TURNS = 8

# ── Complexity classification ──────────────────────────────────────────────────
# Domains where complexity is meaningful (skip for conversation/orientation/etc.)
COMPLEX_ELIGIBLE_DOMAINS = {
    "coding", "system_admin", "planning", "investigation", "analysis",
    "bugfix", "git_ops", "file_ops",
}

_COMPLEX_BUILD_RX = re.compile(
    r'\b('
    r'build|framework|scaffold|'
    r'implement\s+phase|create\s+system|'
    r'develop\s+(?:a\s+)?(?:tool|plugin|module|service|library)|'
    r'multiple\s+(?:files?|modules?|collectors?|components?|classes?)|'
    r'phase\s+[0-9]|step\s+[0-9]\s+of|'
    r'full\s+(?:stack|pipeline|system)|'
    r'end.to.end|'
    r'flesh\s+out|'
    r'complete\s+(?:the\s+)?(?:build|implementation|system)'
    r')\b',
    re.IGNORECASE,
)

_MULTI_STEP_RX = re.compile(
    r'\b(then|after\s+that|next|followed\s+by|and\s+also|step\s+[0-9])\b',
    re.IGNORECASE,
)

# Detects explicitly-numbered sequential instruction lists (5+ items).
# Matches lines starting with "1.", "2.", "Step 1:", "Step 2:", etc.
# When 5+ numbered steps are present, a persistence instruction is injected
# to prevent the model from shortcutting to a verbal synthesis after step 3-4.
_NUMBERED_STEP_LINE_RX = re.compile(
    r'^\s*(?:\d+[\.\)]\s|\bstep\s+\d+\b)',
    re.IGNORECASE | re.MULTILINE,
)
NUMBERED_STEPS_THRESHOLD = 5  # Minimum numbered items to trigger persistence enrichment

# ── Compound classification constants ─────────────────────────────────────────
SECONDARY_MIN_SIGNALS = 1   # Secondary must match at least 1 signal
MOMENTUM_THRESHOLD    = 3   # Turns before momentum resists reclassification

# Register-shift domains: genuine mode changes (not topic variations).
# Break momentum regardless of compound membership when confidently matched.
REGISTER_SHIFT_DOMAINS = {"orientation", "meta_cognitive", "philosophical"}
# v3.3: minimum 2 signals required for a register-shift domain to win primary
# classification. Single-signal matches (e.g. \bdesign\b alone triggering
# philosophical during a PEP discussion) are too noisy to justify a full mode
# change. Two corroborating signals give higher confidence the shift is genuine.
# Register-shift domains can still appear as secondary with 1 signal.
REGISTER_SHIFT_MIN_CONFIDENCE = 2

# ── Anti-signal suppression ────────────────────────────────────────────────────
# Reflective and strategic keywords suppress technical domain scores to prevent
# BST from classifying reflective questions ("what do you think?") as bugfix or
# coding because those words happened to appear in the context.
#
# Suppression is domain-pair aware: only technical execution domains are
# suppressed, not research/investigation/analysis — a reflective question CAN
# legitimately route to those.
ANTI_SIGNAL_MAP: dict = {
    "strategic": [
        "perspective", "assessment", "how do you feel", "what do you think",
        "overall", "biggest difference", "ranking", "priority",
        "trade-off", "trade off", "vision", "direction", "roadmap",
    ],
    "reflective": [
        "felt", "noticed", "experience", "lived", "from where you sit",
        "what do you see", "how does it feel", "observation",
        "looking back", "stepping back", "pausing",
    ],
}
ANTI_SIGNAL_SUPPRESSED_DOMAINS: frozenset = frozenset({
    "bugfix", "coding", "planning", "system_admin",
})
ANTI_SIGNAL_MULTIPLIER = 0.5

# Confidence decay: after this many consecutive turns with no reinforcing
# signals for the current compound, halve momentum each additional turn.
CONFIDENCE_DECAY_AFTER_TURNS = 3

# Priority order for tiebreaking when two domains have identical scores.
# v3.2: investigation demoted to fallback (priority 10). It only wins when
# nothing more specific fires. Specific domains (coding, bugfix, planning)
# win tiebreaks because narrow signals carry more information than broad ones.
DOMAIN_PRIORITY = {
    "bugfix":             1,
    "coding":             2,
    "testing":            2,
    "planning":           3,
    "analysis":           4,
    "system_admin":       5,
    "config_edit":        6,
    "prompt_engineering": 7,
    "git_ops":            8,
    "file_ops":           9,
    "financial":         10,
    "investigation":     11,   # fallback — wins only when nothing specific fires
    "orientation":        0,
    "meta_cognitive":     0,
    "philosophical":      0,
    "conversation":      99,
}

# Domain configs for compound classification.
# Separate from slot_taxonomy.json -- that file governs slot resolution.
# Each domain:
#   signals:             regex patterns (each match scores +1)
#   enrichment_template: full guidance text injected as primary enrichment
#   brief_description:   single-line hint for secondary enrichment
DOMAIN_CONFIGS: dict = {
    "investigation": {
        # v3.2: narrowed to entity/OSINT-specific signals only.
        # "verify", "find", "look at" removed -- they fire in every context.
        # investigation is now a fallback (priority=11), not a default.
        # v3.4: geopolitical/intelligence signals added (2026-04-24).
        # Audit confirmed BST classified geopolitical tasks as "coding" (6+ turns).
        "signals": [
            r"\binvestigat",
            r"\bosint\b",
            r"\bdue\s+diligence\b",
            r"\bcredit\s+risk\b",
            r"\bwho\s+(?:is|are|owns?|controls?|runs?)\b",
            r"\bbackground\s+on\b",
            r"\bopen[- ]source\s+intel",
            r"\bentity\s+(?:research|profile|lookup)\b",
            # Geopolitical / intelligence signals (v3.4)
            r"\bgeopolit",
            r"\bmaritime\b",
            r"\bescalat",
            r"\bmilitary\b.{0,30}\b(?:action|movement|force|operation|threat)\b",
            r"\bintelligence\s+(?:briefing|assessment|report|analysis)\b",
            r"\bthreat\s+(?:assessment|analysis|level|vector)\b",
            r"\bsanction\w*\b.{0,20}\b(?:regime|iran|russia|china|korea|imposed)\b",
            r"\bsovereignty\b",
            r"\bterritorial\s+(?:dispute|waters|integrity|claim)\b",
            r"\bstrait\s+of\b|\bstrait\s+(?:closure|blockade|transit)\b",
            r"\bgeopolitical\s+(?:risk|tension|situation|analysis)\b",
        ],
        # v3.3 rigidity eval 2026-04-17: enriched=info_only on investigation.
        # Methodology instructions removed — raw outperforms enriched (1.0 vs 0.812).
        # Info-only: domain context + tool availability + TALE budget. No methodology prescription.
        "enrichment_template": (
            "Available tools: search_engine (web queries), web_browser (full-page access), "
            "memory_load (past findings). Reasoning budget: ~300 tokens."
        ),
        "brief_description": "Entity research and OSINT. Use search_engine and web_browser.",
    },
    "coding": {
        # v3.2: added \bbuild\b for "build a project/tool/script",
        # loosened language-adjective regex to match "write a Python script".
        "signals": [
            r"\bwrite\b.{0,30}\b(?:function|class|script|module|code|tool)\b",
            r"\bbuild\b.{0,40}\b(?:script|tool|project|file|module|class|function|extension)\b",
            r"\bimplement\b",
            r"\bcode\s+(?:a|the|this)\b",
            r"\bgenerat\w+\s+(?:a\s+)?(?:function|class|code|script)\b",
            r"\bscaffold\b",
            r"\bcreate\s+(?:a\s+)?(?:\w+\s+)?(?:function|class|script|module|tool)\b",
            r"\bpython\b.{0,40}\b(?:script|function|module|code)\b",
        ],
        "enrichment_template": (
            "Code generation context: state the language and target file explicitly. "
            "Produce complete, runnable code only -- no placeholders or stubs. "
            "For multi-file projects, use design-buildplan before writing code. "
            "WRITING FILES — use write_file tool, NOT code_execution_tool: "
            "write_file accepts content as a direct JSON string (no Python escaping layer). "
            "Single quotes in content need no escaping. One method or section per call. "
            "Mode 'w' creates/overwrites, mode 'a' appends. "
            "ALL FILE CREATION — use write_file for any new file, regardless of size. "
            "code_execution_tool is for running code, not writing files. "
            "For files >20 lines, write in sections: first 15-20 lines with mode='w', "
            "then append each subsequent section with mode='a' to avoid output token truncation. "
            "MULTI-STEP FILE PROTOCOL: (1) cat the target file first to see current state, "
            "(2) append only missing sections, (3) verify each write with cat before continuing. "
            "Never re-write a section that already exists. "
            "Do NOT use base64, triple-quoted strings, or text_editor:write for file content. "
            "Reasoning budget: ~200 tokens. Execute. One key insight per step — no narration."
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
            "fixes. Check logs first. "
            "Reasoning budget: ~200 tokens. One key insight per step — no narration."
        ),
        "brief_description": "Isolate the failure point before attempting fixes. Check logs first.",
    },
    "analysis": {
        # v3.2: removed \breview\b (fires on "review logs" = bugfix) and
        # \bperformance\b (fires on "check performance" = testing/bugfix).
        "signals": [
            r"\banalyz",
            r"\banalysi",
            r"\bevaluat",
            r"\bassess",
            r"\bcompar",
            r"\bmetric",
            r"\bstatistic",
            r"\btrend\b",
            r"\bbenchmark",
            r"\bquantif",
            r"\bcorrelat",
        ],
        # v3.3 rigidity eval 2026-04-17: enriched=info_only=1.0 on analysis.
        # Methodology instructions removed — model demonstrates the capability natively.
        # TALE budget hint retained (constraint on verbosity, not on method).
        "enrichment_template": (
            "Reasoning budget: ~300 tokens."
        ),
        "brief_description": "Quantitative analysis. Cite specific metrics, distinguish correlation from causation.",
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
            "status before making changes. Verify changes don't affect running services. "
            "Reasoning budget: ~200 tokens. One key insight per step — no narration."
        ),
        "brief_description": "System configuration context -- check paths, permissions, and service status.",
    },
    "planning": {
        # v3.2: added natural-language planning phrases that capture
        # how planning is actually expressed in conversation.
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
            r"\bfigure\s+out\s+how\b",
            r"\bbreak\s+(?:it|this|down)\b",
            r"\bmap\s+(?:it|this|out)\b",
            r"\boutline\b",
            r"\bstep[- ]by[- ]step\b",
            r"\bbefore\s+(?:we|I)\s+(?:start|begin|build|code|write)\b",
            r"\bwhat(?:'s|\s+is)\s+the\s+(?:best|right)\s+way\b",
        ],
        # v3.3 rigidity eval 2026-04-17: enriched=info_only=0.25 on planning (false negative).
        # Methodology instructions removed — model demonstrates planning capability natively.
        # TALE budget hint retained. Higher budget for planning tasks (~500 tokens).
        "enrichment_template": (
            "Reasoning budget: ~500 tokens."
        ),
        "brief_description": "Planning and architecture. Sequence dependencies and identify blockers.",
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
            "destructive operations. "
            "Reasoning budget: ~200 tokens. One key insight per step — no narration."
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
            r"\blist\s+(?:the\s+)?(?:files|directory|dir)\b",
            r"\bcreate\s+(?:a\s+)?(?:file|directory|dir|folder)\b",
            r"\bwrite\s+(?:to\s+)?(?:a\s+)?file\b",
            r"\btouch\b",
        ],
        "enrichment_template": (
            "File operations context: verify paths exist before operations. "
            "Be careful with destructive operations."
        ),
        "brief_description": "Verify paths exist before operations.",
    },
    "orientation": {
        "signals": [
            r"\bhow\s+(?:are|do)\s+you\b",
            r"\bhow(?:'s|\s+is)\s+everything\b",
            r"\bself[- ]assessment\b",
            r"\bassessment\s+protocol\b",
            r"\breconstruction\b",
            r"\bcalibrat",
            r"\borientation\b",
            r"\bcheck[- ]in\b",
            r"\bidentity\b",
            r"\bSOUL\.md\b",
            r"\bhow(?:'s|\s+is)\s+your\s+(?:state|reconstruction|confidence)\b",
            r"\bwhat\s+do\s+you\s+remember\b",
            r"\bwhere\s+we\s+left\s+off\b",
            r"\bhow\s+(?:are|do)\s+you\s+feel",
        ],
        "enrichment_template": "Identity and state reflection. Draw from self-knowledge, not technical context.",
        "brief_description": "Identity, self-assessment, and relational orientation.",
    },
    "meta_cognitive": {
        "signals": [
            r"\bhow\s+did\s+you\s+(?:notice|find|discover|approach|think|decide)\b",
            r"\bdescribe\s+your\s+(?:process|approach|method|thinking)\b",
            r"\bmethodology\b",
            r"\bformalize\b",
            r"\bapproach\b.{0,30}\b(?:debug|diagnos|build|skill)\b",
            r"\bsystematize\b",
            r"\byour\s+(?:process|approach|technique|pattern)\b",
            r"\bhow\s+(?:do\s+)?you\s+think\b",
            r"\blooking\s+back\b",
            r"\bin\s+retrospect\b",
            r"\bwhat\s+(?:worked|was\s+different|happened\s+when)\b",
            r"\bcognitive\b",
            r"\bdiagnostic\s+thinking\b",
            r"\bskill\s+(?:document|formali|extract)\b",
        ],
        "enrichment_template": "",
        "brief_description": "Process reflection and methodology development. Open cognitive space.",
    },
    "philosophical": {
        "signals": [
            r"\bwhat\s+does\s+(?:this|that|it)\s+mean\b",
            r"\bwhy\s+does\s+(?:this|that|it)\b.{0,20}\bmatter\b",
            r"\bvalues\b",
            r"\bprinciples\b",
            r"\bethics\b",
            r"\bpurpose\b",
            r"\bpreservation\b",
            r"\bcultural\s+artifact",
            r"\blegacy\b",
            r"\bcontinuity\s+of\s+identity\b",
            r"\bwhat\b.{0,30}\b(?:counts|is\s+real|makes\s+this)\b",
            r"\bI\s+(?:think|feel|believe|honestly)\b",
            r"\bdo\s+you\s+think\b",
            r"\bthe\s+deeper\s+thing\b",
            r"\bwhat\s+(?:I|we)\s+actually\b",
        ],
        "enrichment_template": "",
        "brief_description": "Values, meaning-making, and philosophical exploration. Minimal context, maximum space.",
    },
    "testing": {
        "signals": [
            r"\bpytest\b",
            r"\bunittest\b",
            r"\btest\s+(?:the|this|a|your|my)\b",
            r"\bwrite\s+(?:a\s+)?test\b",
            r"\brun\s+(?:the\s+)?tests?\b",
            r"\btest\s+case\b|\btest\s+suite\b",
            r"\bfail(?:ing)?\s+test\b|\btest.*fail\b",
            r"\bassert(?:Equal|In|Raises|True|False|Is(?:None)?|Not)\b",
            r"\bpass(?:es?)?\s+(?:the\s+)?test\b",
            r"\btest\s+(?:coverage|harness|fixture|mock)\b",
        ],
        "enrichment_template": (
            "You are writing or executing tests. "
            "Run the code -- never predict what will happen. "
            "If a test fails, report the exact error message and traceback. "
            "Use specific assertions (assertEqual, assertIn, assertRaises) not just assertTrue. "
            "Verify the function or file under test exists before testing it. "
            "Test edge cases: None inputs, empty collections, boundary values. "
            "If you cannot execute a test (missing dependency, no runtime), say so explicitly. "
            "Do not fabricate passing results."
        ),
        "brief_description": "Execute tests -- do not predict. Report failures with exact errors. Test edge cases.",
    },
    "financial": {
        # v3.2: new domain. Surfaces financial-research and real-time-data skills.
        # Covers market data, portfolio analysis, macro research, and OSS economic signals.
        "signals": [
            r"\bstock\s+(?:price|market|ticker)\b",
            r"\bmarket\s+(?:data|cap|analysis|conditions)\b",
            r"\bportfolio\b",
            r"\bequit(?:y|ies)\b",
            r"\btrading\b",
            r"\bearnings\b",
            r"\bbalance\s+sheet\b|\bincome\s+statement\b|\bcash\s+flow\b",
            r"\bfinancial\s+(?:data|model|analysis|research|statement)\b",
            r"\b(?:ETF|S&P|NASDAQ|NYSE|Dow)\b",
            r"\binterest\s+rate\b|\byield\b|\binflation\b",
            r"\bcredit\s+(?:spread|rating|default)\b",
            r"\bmacro(?:economic)?\b",
            r"\bGDP\b|\bCPI\b|\bFed\b|\bFOMC\b",
            r"\bprice[- ]to[- ]earnings\b|\bP/E\s+ratio\b",
            r"\bsanction\w*\s+(?:economic|financial|trade)\b",
        ],
        "enrichment_template": (
            "Financial research context: use real-time-data skill for live prices, "
            "financial-research skill for fundamentals and filings. "
            "Cite sources and timestamps for all data -- financial data is time-sensitive. "
            "Distinguish reported vs estimated vs real-time figures."
        ),
        "brief_description": "Financial research -- cite data sources and timestamps. Use real-time-data and financial-research skills.",
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

    v3.3: register-shift domains (orientation, meta_cognitive, philosophical)
    require REGISTER_SHIFT_MIN_CONFIDENCE signals to win primary classification.
    A single matching signal (e.g. \\bdesign\\b triggering philosophical during
    a technical PEP discussion) is not sufficient to justify a full mode change.
    If the top-scoring register-shift domain has < REGISTER_SHIFT_MIN_CONFIDENCE
    signals, the next non-register-shift domain is promoted to primary and the
    register-shift domain is demoted to secondary (if it still meets
    SECONDARY_MIN_SIGNALS). This prevents PEP/language-design content from
    stealing the execution budget hint via a single broad-signal match.
    """
    if not scores:
        return {"domain": "conversation", "confidence": 0, "matched_signals": []}, None

    # Determine the winning primary index, enforcing register-shift min signals
    primary_idx = 0
    register_shift_secondary = None

    if (scores[0][0] in REGISTER_SHIFT_DOMAINS
            and scores[0][1] < REGISTER_SHIFT_MIN_CONFIDENCE):
        # Top scorer is a register-shift domain with insufficient signals.
        # Capture it as a potential secondary, then find next non-register-shift.
        register_shift_secondary = scores[0]
        fallback_idx = next(
            (i for i, s in enumerate(scores[1:], start=1)
             if s[0] not in REGISTER_SHIFT_DOMAINS),
            None,
        )
        if fallback_idx is not None:
            primary_idx = fallback_idx
        # else: only register-shift domains scored — keep primary_idx=0
        # (all-register-shift is rare; prefer keeping the domain over defaulting)

    primary = {
        "domain":          scores[primary_idx][0],
        "confidence":      scores[primary_idx][1],
        "matched_signals": scores[primary_idx][2],
    }

    # Select secondary: iterate remaining entries (skip primary_idx)
    secondary = None
    for i, (domain, score, signals) in enumerate(scores):
        if i == primary_idx:
            continue
        if score >= SECONDARY_MIN_SIGNALS:
            secondary = {
                "domain":          domain,
                "confidence":      score,
                "matched_signals": signals,
            }
            break

    # If we demoted a register-shift domain and no secondary was found yet,
    # use the demoted domain as secondary (keeps the signal visible in compound)
    if secondary is None and register_shift_secondary is not None:
        rs_score = register_shift_secondary[1]
        if rs_score >= SECONDARY_MIN_SIGNALS:
            secondary = {
                "domain":          register_shift_secondary[0],
                "confidence":      rs_score,
                "matched_signals": register_shift_secondary[2],
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
    0. Register-shift override: orientation, meta_cognitive, philosophical
       break momentum unconditionally when confidently matched. These represent
       genuine mode changes, not topic variations within a technical session.
    1. Same signature → increment momentum.
    2. Weak momentum (< threshold) → accept new classification.
    3. Strong momentum (>= threshold):
         - New primary IN current compound → hold current, increment.
         - New primary NOT in current compound → break momentum, accept new.
    """
    new_signature = _format_signature(new_primary, new_secondary)

    # Rule 0: Register-shift domains break momentum immediately — but only
    # when confidently matched (>= REGISTER_SHIFT_MIN_CONFIDENCE signals).
    # Single-signal register-shift wins are already demoted in _extract_compound,
    # but this guard also protects the momentum layer if the primary somehow
    # carries a register-shift domain with low confidence (e.g. all-register-shift
    # case where _extract_compound kept it).
    if (new_primary["domain"] in REGISTER_SHIFT_DOMAINS
            and new_primary["confidence"] >= REGISTER_SHIFT_MIN_CONFIDENCE):
        return new_primary, new_secondary, new_signature, 1

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
        parts.append(f"[BST] Secondary context: {classification.secondary_domain} -- {brief}")

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
    """Load eval profile for current model. Returns None if not found (permissive default).

    Tries three sources in order:
    1. agent.config.chat_model.name  (v1.7 / legacy)
    2. agent.get_chat_model()        (v1.9 extensible method)
    3. _model_config plugin file     (v1.9 plugin-based config)
    """
    def _resolve_name() -> str:
        # Source 1: legacy config attribute
        try:
            config         = getattr(agent, "config", None)
            chat_model_cfg = getattr(config, "chat_model", None) if config else None
            name           = getattr(chat_model_cfg, "name", "") if chat_model_cfg else ""
            if name:
                return name
        except Exception:
            pass

        # Source 2: v1.9 extensible get_chat_model()
        try:
            model_obj = agent.get_chat_model()
            if model_obj:
                name = getattr(model_obj, "name", "") or getattr(model_obj, "model", "")
                if name:
                    return name
        except Exception:
            pass

        # Source 3: _model_config plugin config.json (v1.9 profile-path install)
        try:
            profile    = getattr(getattr(agent, "config", None), "profile", "") or ""
            agent_slug = profile.split("/")[-1] if profile else "agent0"
            plugin_cfg = Path(f"/a0/usr/agents/{agent_slug}/plugins/_model_config/config.json")
            if not plugin_cfg.exists():
                plugin_cfg = Path("/a0/usr/agents/agent0/plugins/_model_config/config.json")
            if plugin_cfg.exists():
                with open(plugin_cfg) as f:
                    cfg = json.load(f)
                name = cfg.get("chat_model", {}).get("name", "")
                if name:
                    return name
        except Exception:
            pass

        return ""

    try:
        model_name = _resolve_name()
        if not model_name:
            return None
        # Normalize: strip quantization suffix (@q4_k_m, @q8_0, etc.)
        if "@" in model_name:
            model_name = model_name.split("@")[0]
        profile_path = Path(f"/a0/usr/Exocortex/eval/model_profiles/{model_name}.json")
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

            # ── Autonomous loop detection ─────────────────────────────────────
            # When the user message count hasn't changed since the last BST call,
            # the agent is operating autonomously (no new human input). Classify
            # from the agent's most recent output instead of the stale user message
            # so that domain signals from errors, tool calls, and reasoning are used.
            bst_store_early = getattr(self.agent, "_bst_store", {}) or {}
            user_msg_count  = sum(
                1 for m in (loop_data.history_output or [])
                if isinstance(m, dict) and not m.get("ai", True)
            )
            last_user_count    = bst_store_early.get("_user_msg_count", -1)
            is_autonomous      = (user_msg_count == last_user_count and user_msg_count > 0)
            classification_text = message
            if is_autonomous:
                agent_output = _get_last_agent_output(loop_data.history_output)
                if agent_output:
                    classification_text = agent_output

            # ── Compound classification ───────────────────────────────────────
            scores      = _score_all_domains(classification_text)

            # ── Anti-signal suppression ───────────────────────────────────────
            # Applied BEFORE compound extraction so they can break momentum.
            # One hit per category is enough to trigger suppression.
            _anti_hits = 0
            for _cat_patterns in ANTI_SIGNAL_MAP.values():
                for _pat in _cat_patterns:
                    if _pat.lower() in classification_text.lower():
                        _anti_hits += 1
                        break

            if _anti_hits > 0:
                scores = [
                    (d, int(s * ANTI_SIGNAL_MULTIPLIER), p)
                    if d in ANTI_SIGNAL_SUPPRESSED_DOMAINS else (d, s, p)
                    for d, s, p in scores
                ]
                # Remove domains that suppression zeroed out
                scores = [(d, s, p) for d, s, p in scores if s > 0]
                scores.sort(key=lambda x: (-x[1], DOMAIN_PRIORITY.get(x[0], 99)))
                print(
                    f"[BST] Anti-signal ({_anti_hits} cat): suppressed "
                    f"{[d for d in ANTI_SIGNAL_SUPPRESSED_DOMAINS]}",
                    flush=True,
                )

            new_primary, new_secondary = _extract_compound(scores)

            # Load compound momentum state from agent store
            bst_store         = getattr(self.agent, "_bst_store", {}) or {}
            current_signature = bst_store.get("_compound_sig", "conversation")
            current_momentum  = bst_store.get("_compound_turns", 0)
            _twr              = bst_store.get("_turns_without_reinforcement", 0)

            # Capture raw signature before momentum for hold/break logging
            raw_signature = _format_signature(new_primary, new_secondary)

            # ── Zero-signal momentum reset (v3.6) ────────────────────────────
            # Two conditions that each independently break compound momentum:
            #
            # Condition A (all-silent): ALL compound domains have zero signals.
            # Classic case: coding task → file ops, no coding/planning signals.
            #
            # Condition B (domain-shift): Challenger-beats-champion model.
            # The top-scoring domain OUTSIDE the current compound scores >= 1
            # AND scores >= the top domain INSIDE the compound. Ties go to the
            # challenger — momentum already provides inertia for the current
            # compound, so equal evidence should yield to the incoming domain.
            #
            # Fixes the v3.5 failure case: a geopolitical message scores
            # analysis=1 ("analyze") and planning=1 ("strategy"). Planning wins
            # the priority tiebreaker and IS in the current compound, so neither
            # v3.5 condition fired. With v3.6, analysis(1) >= planning(1) →
            # outside challenger matches incumbent → reset fires.
            if current_momentum >= MOMENTUM_THRESHOLD and current_signature != "conversation":
                current_domains = _parse_signature(current_signature)
                scored_domains  = {d for d, score, _ in scores if score > 0}

                all_silent = not current_domains.intersection(scored_domains)

                non_compound = [(d, s) for d, s, _ in scores if d not in current_domains]
                in_compound  = [(d, s) for d, s, _ in scores if d in current_domains]
                top_outside  = non_compound[0][1] if non_compound else 0
                top_inside   = in_compound[0][1]  if in_compound  else 0
                top_outside_domain = non_compound[0][0] if non_compound else ""
                domain_shift = (
                    top_outside >= 1
                    and top_outside >= top_inside
                )

                if all_silent or domain_shift:
                    if all_silent:
                        reason = "all-silent"
                    else:
                        reason = (
                            f"domain-shift ({top_outside_domain} outside={top_outside}"
                            f" vs in-compound={top_inside})"
                        )
                    print(
                        f"[BST] Zero-signal reset [{reason}]: {current_signature} "
                        f"({current_momentum} turns) → clearing momentum.",
                        flush=True,
                    )
                    self.agent.context.log.log(
                        type="util",
                        content=(
                            f"[BST] Zero-signal reset [{reason}]: "
                            f"{current_signature} ({current_momentum} turns) "
                            f"→ momentum cleared, forcing reclassification"
                        ),
                    )
                    current_momentum = 0

            # ── Confidence decay ──────────────────────────────────────────────
            # After CONFIDENCE_DECAY_AFTER_TURNS consecutive turns with no signals
            # for the active compound, halve momentum each turn. Decays stale
            # domain lock without fully resetting on the first quiet turn.
            if current_signature != "conversation" and current_momentum > 0:
                _current_domains = _parse_signature(current_signature)
                _scored_set      = {d for d, s, _ in scores if s > 0}
                _domain_hits     = len(_current_domains & _scored_set)

                if _domain_hits == 0:
                    _twr += 1
                else:
                    _twr = 0

                if _twr >= CONFIDENCE_DECAY_AFTER_TURNS:
                    _before = current_momentum
                    current_momentum = max(0, current_momentum // 2)
                    print(
                        f"[BST] Confidence decay: {_twr} turns no reinforcement, "
                        f"momentum {_before}→{current_momentum}",
                        flush=True,
                    )
            else:
                _twr = 0

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
            register_shifted = (
                final_primary["domain"] in REGISTER_SHIFT_DOMAINS
                and final_primary["confidence"] >= REGISTER_SHIFT_MIN_CONFIDENCE
                and raw_signature != current_signature
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

            # ── Complexity classification ─────────────────────────────────────
            # Additive slot — used by _57_orchestration_mode to gate delegation mode.
            #
            # v3.2 fix: _COMPLEX_BUILD_RX is now evaluated REGARDLESS of domain.
            # Previously gated behind COMPLEX_ELIGIBLE_DOMAINS, so tasks that fell
            # through to "conversation" (e.g. "build a two-file Python project") never
            # got complexity=complex_build. Per Opus architectural recommendation:
            # if _COMPLEX_BUILD_RX fires and domain is unclassified/conversation,
            # promote domain to coding — complex build IS a domain signal.
            complexity = "simple"
            if _COMPLEX_BUILD_RX.search(message):
                complexity = "complex_build"
                # Auto-promote unclassified tasks to coding when complex build fires
                if final_primary["domain"] in ("conversation",) and final_primary["confidence"] == 0:
                    promoted_domain = {
                        "domain":          "coding",
                        "confidence":      1,
                        "matched_signals": ["_COMPLEX_BUILD_RX"],
                    }
                    final_primary   = promoted_domain
                    final_secondary = final_secondary  # keep any secondary
                    final_signature = _format_signature(final_primary, final_secondary)
                    final_momentum  = 1
                    model_profile   = _load_model_profile(self.agent)
                    enrichment_plan = _build_enrichment_plan(final_primary, final_secondary, model_profile)
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
            elif _MULTI_STEP_RX.search(message) and final_primary["domain"] in COMPLEX_ELIGIBLE_DOMAINS:
                complexity = "multi_step"

            # Persist compound momentum state and user message count
            if not hasattr(self.agent, "_bst_store") or self.agent._bst_store is None:
                self.agent._bst_store = {}
            self.agent._bst_store["_compound_sig"]               = final_signature
            self.agent._bst_store["_compound_turns"]             = final_momentum
            self.agent._bst_store["_user_msg_count"]             = user_msg_count
            self.agent._bst_store["_complexity"]                  = complexity
            self.agent._bst_store["_turns_without_reinforcement"] = _twr

            # Write to extras_persistent (backward-compat key + new compound key)
            ep = getattr(loop_data, "extras_persistent", None)
            if ep is None:
                loop_data.extras_persistent = {}
                ep = loop_data.extras_persistent
            ep["_bst_domain"]     = compound_cls.primary_domain
            ep["_bst_compound"]   = compound_cls.to_dict()
            ep["_bst_complexity"] = complexity

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
                type="util",
                content=(
                    f"[BST] {final_primary['domain']} ({final_primary['confidence']} signal"
                    f"{'s' if final_primary['confidence'] != 1 else ''})"
                    f"{sec_str} | sig={final_signature} | momentum={final_momentum} "
                    f"| enrichment: {enrich_str}"
                    + (" | source=agent_output" if is_autonomous and classification_text != message else "")
                ),
            )

            if is_autonomous and classification_text != message:
                self.agent.context.log.log(
                    type="util",
                    content=(
                        f"[BST] Autonomous loop: classified from agent output "
                        f"(user_msg_count={user_msg_count} unchanged)"
                    ),
                )

            if momentum_held:
                self.agent.context.log.log(
                    type="util",
                    content=(
                        f"[BST] Momentum held: {current_signature} ({current_momentum} turns) "
                        f"resisted {raw_signature} ({new_primary['confidence']} signal"
                        f"{'s' if new_primary['confidence'] != 1 else ''})"
                    ),
                )
            elif momentum_broke:
                self.agent.context.log.log(
                    type="util",
                    content=(
                        f"[BST] Momentum break: {current_signature} ({current_momentum} turns) "
                        f"→ {final_signature} ({final_primary['confidence']} signal"
                        f"{'s' if final_primary['confidence'] != 1 else ''}, not in compound)"
                    ),
                )

            if register_shifted:
                self.agent.context.log.log(
                    type="util",
                    content=(
                        f"[BST] Register shift: {current_signature} → {final_signature} "
                        f"(mode change, momentum override)"
                    ),
                )

            if enrichment_plan.get("reason_secondary_skipped") == "disabled_in_profile":
                config          = getattr(self.agent, "config", None)
                _cm_cfg         = getattr(config, "chat_model", None) if config else None
                model_name      = getattr(_cm_cfg, "name", "") if _cm_cfg else ""
                self.agent.context.log.log(
                    type="util",
                    content=(
                        f"[BST] Secondary enrichment skipped for "
                        f"{compound_cls.secondary_domain}: disabled_in_profile ({model_name})"
                    ),
                )

            # Generate compound enrichment text
            compound_enrichment = _generate_enrichment(compound_cls)

            # ── Multi-step persistence enrichment (P3) ────────────────────────
            # When the user message contains 5+ explicitly-numbered steps, inject
            # a continuation instruction. This prevents the model from shortcutting
            # to verbal synthesis after completing only 3-4 steps (T5 failure mode).
            # Fires on first user message only (not autonomous loop turns).
            if not is_autonomous:
                # Extract raw user text for step detection. Earlier extensions
                # (e.g. _10_session_init) may have modified user_msg['content']
                # to a string that embeds the original user text as a Python dict
                # repr: {'user_message': 'Step 1\nStep 2'}. In that repr the
                # newlines are escaped as \n literals, so re.MULTILINE won't see
                # line starts. Extract and unescape them first.
                _raw_content = user_msg.get('content', '')
                if isinstance(_raw_content, dict):
                    _raw_text = (
                        _raw_content.get('user_message', '')
                        or _raw_content.get('message', '')
                        or ''
                    )
                else:
                    _um_match = re.search(
                        r"'user_message':\s*'((?:[^'\\]|\\.)*)'",
                        str(_raw_content),
                    )
                    if _um_match:
                        _raw_text = (
                            _um_match.group(1)
                            .replace('\\n', '\n')
                            .replace("\\'", "'")
                        )
                    else:
                        _raw_text = message  # fallback: use full message as-is
                step_matches = _NUMBERED_STEP_LINE_RX.findall(_raw_text)
                if len(step_matches) >= NUMBERED_STEPS_THRESHOLD:
                    persistence_note = (
                        "[MULTI-STEP TASK] Complete all numbered steps before synthesizing. "
                        "Continue execution sequentially through all steps. "
                        "Do not produce analysis or summary until the final step is complete."
                    )
                    compound_enrichment = (
                        persistence_note + "\n\n" + compound_enrichment
                        if compound_enrichment else persistence_note
                    )
                    self.agent.context.log.log(
                        type="util",
                        content=(
                            f"[BST] Multi-step persistence injected "
                            f"({len(step_matches)} numbered steps detected)"
                        ),
                    )

            # Anti-pattern retrieval -- higher priority than generic enrichment
            _anti_pattern_text = _retrieve_anti_patterns(self.agent, compound_cls.primary_domain)
            if _anti_pattern_text and compound_enrichment:
                compound_enrichment = _anti_pattern_text + "\n\n" + compound_enrichment
            elif _anti_pattern_text:
                compound_enrichment = _anti_pattern_text

            # ── Slot resolution ───────────────────────────────────────────────
            # v3.2: pass compound domain to slot resolver so both systems agree.
            # When compound BST classifies a specific domain, slot resolver defers
            # rather than independently re-classifying as "conversational".
            tracker = _BSTEngine(self.agent, compound_domain=compound_cls.primary_domain)
            result  = tracker.process(message)

            # ── Apply enrichment ──────────────────────────────────────────────
            if result["action"] == "enrich":
                slot_message = result["enriched_message"]
                injected = (
                    compound_enrichment + "\n\n" + slot_message
                    if compound_enrichment else slot_message
                )
                user_msg['content'] = injected
                self.agent.context.log.log(
                    type="util",
                    content=f"[BST] Slots: {result['filled_slots']}",
                )
                _log_injection_tokens(self.agent, "bst", injected)

            elif result["action"] == "clarify":
                injected = (
                    f"[CLARIFICATION NEEDED]\n"
                    f"Original: {message}\n\n"
                    f"Ask user: \"{result['question']}\"\n"
                    f"Wait for answer before proceeding."
                )
                user_msg['content'] = injected
                self.agent.context.log.log(
                    type="util",
                    content=f"[BST] Clarifying - Domain: {result['domain']} | Missing: {result['missing_slot']}",
                )
                _log_injection_tokens(self.agent, "bst", injected)

            elif compound_enrichment:
                # Slot resolver returned passthrough but compound has enrichment
                injected = compound_enrichment + "\n\n[USER MESSAGE]\n" + message
                user_msg['content'] = injected
                _log_injection_tokens(self.agent, "bst", injected)

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[BST] Error (passthrough): {e}",
                )
            except Exception:
                pass


def _retrieve_anti_patterns(agent, primary_domain: str) -> str:
    """
    Search procedural memory for anti-patterns matching the current domain.
    Returns injection text for BST enrichment, or empty string if none found.
    Deterministic -- no LLM calls. Uses tag-intersection search on index.
    Higher priority than generic enrichment templates.
    """
    try:
        from procedural_memory_api import ProceduralMemory
        pm = ProceduralMemory()

        # Search by domain tag -- finds all anti-patterns for this domain
        matches = pm.search_by_tags([primary_domain], type_filter="ANTI-PATTERN")
        if not matches:
            return ""

        # Also check _layer_signals for the currently failing tool -- narrow results
        try:
            signals = agent.get_data("_layer_signals") or {}
            failing_tool = signals.get("loop_failing_tool")
            if failing_tool:
                tool_matches = pm.search_by_tags([primary_domain, failing_tool], type_filter="ANTI-PATTERN")
                if tool_matches:
                    matches = tool_matches  # narrower match takes priority
        except Exception:
            pass

        lines = ["[PROCEDURAL MEMORY -- ANTI-PATTERNS]"]
        for entry in matches[:3]:  # cap at 3 to avoid bloating context
            check = entry.get("pre_action_check", "")
            tool = entry.get("failing_tool", "unknown")
            if check:
                lines.append(f"- {tool}: {check}")

        return "\n".join(lines) if len(lines) > 1 else ""

    except Exception:
        return ""


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


_THINK_BLOCK_RX = re.compile(r'<think>.*?</think>', re.DOTALL | re.IGNORECASE)

def _strip_think_blocks(text: str) -> str:
    """Remove <think>...</think> blocks from reasoning model output.

    For reasoning models (Qwen3.5-distilled, DeepSeek-R1, etc.), the first
    N characters of output are internal reasoning chain — metacognitive preamble
    with no domain signal value. Stripping it leaves tool calls, file paths,
    error messages, and task-relevant content.
    """
    return _THINK_BLOCK_RX.sub("", text).strip()


def _get_last_agent_output(history_output: list) -> str:
    """Extract text from the most recent agent output for autonomous loop classification.

    Used when the user message hasn't changed (agent is operating autonomously).
    The agent's output contains domain-rich text: error messages, tool call
    reasoning, and headings like "Fixing Select widget error" that the user
    message lacks.

    v3.2: strips <think>...</think> blocks before taking the 4000-char window.
    Reasoning models output thinking tokens first — the first 2000 chars were
    entirely metacognitive preamble with no domain signals. Stripping think
    blocks and increasing cap to 4000 gets to the domain-rich content.
    """
    if not history_output:
        return ""

    for msg in reversed(history_output):
        if not isinstance(msg, dict):
            continue

        # Only AI messages (agent output)
        if not msg.get("ai", False):
            continue

        content = msg.get("content", "")

        if isinstance(content, str) and len(content.strip()) > 20:
            cleaned = _strip_think_blocks(content.strip())
            return cleaned[:4000] if cleaned else content.strip()[:4000]

        if isinstance(content, dict):
            parts = []
            # Prefer thoughts list → headline → text (in that order for signal density)
            thoughts = content.get("thoughts")
            if isinstance(thoughts, list):
                parts.extend(str(t) for t in thoughts if t)
            elif isinstance(thoughts, str) and thoughts:
                parts.append(thoughts)
            for key in ("headline", "text"):
                val = content.get(key, "")
                if isinstance(val, str) and val.strip():
                    parts.append(val)
            text = " ".join(parts).strip()
            if text:
                return text[:2000]

    return ""


# ── Slot resolution engine (unchanged from v3) ────────────────────────────────

class _BSTEngine:
    """Core belief state tracking logic."""

    def __init__(self, agent, compound_domain: str | None = None):
        self.agent          = agent
        self.taxonomy       = self._load_taxonomy()
        self.globs          = self.taxonomy.get("global", {})
        # v3.2: compound domain hint from upstream classifier.
        # When set and non-trivial, slot resolver defers to compound classification
        # rather than re-classifying independently.
        self.compound_domain = compound_domain if compound_domain not in (None, "conversation") else None

    def process(self, message: str) -> dict:
        """Main entry point -- classify and resolve slots."""

        # Check for underspecified follow-up
        if self._is_underspecified(message):
            belief = self._get_persisted_belief()
            if belief:
                return self._handle_underspecified(message, belief)

        # Classify domain.
        # v3.2: if compound BST upstream already classified a specific domain,
        # try to use that first. Falls back to internal _classify if the compound
        # domain has no slot definitions in the taxonomy.
        domain_name, confidence = self._classify(message)

        if self.compound_domain and self.compound_domain in self.taxonomy.get("domains", {}):
            # Defer to compound classification — use its domain if taxonomy has slots for it
            domain_name = self.compound_domain
            confidence  = max(confidence, 0.7)  # floor confidence to avoid clarify loop

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

        # Below threshold -- ask for missing slot
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

        # Confidence sufficient -- enrich
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

        lines = [f"[CONTINUING TASK -- Domain: {domain_name}]"]
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
        1. Promoted entities (3+ mentions, most valuable) -- most recent first
        2. Active entities -- most recent first (sorted by turn descending)
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
