"""
predictor.py — Run a prediction question through an ACP profile

For each profile:
  1. Construct the system prompt from profile fields
  2. Call the LLM (LM Studio, same model as Agent Zero)
  3. Parse the structured JSON response
  4. Apply profile-specific constraints
  5. Write prediction to DB

Sprint 1: context is operator-supplied text (no autonomous search yet).
Sprint 2+: profiles will execute their search strategies autonomously.
"""

import json
import uuid
import re
import time
from datetime import datetime, timezone
from typing import Optional

import psycopg2
from openai import OpenAI

import config
from acp.constraints import apply_constraints


# ============================================================
# LLM client — shared across all prediction calls this process
# ============================================================

_llm_client: Optional[OpenAI] = None

def get_llm_client() -> OpenAI:
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.LLM_API_KEY,
            timeout=config.LLM_REQUEST_TIMEOUT,
        )
    return _llm_client


# ============================================================
# System prompt construction
# ============================================================

SYSTEM_PROMPT_TEMPLATE = """You are {name}, an analytical agent with a specific methodology for forming predictions.

YOUR ANALYTICAL METHOD:
{analytical_method}

YOUR EPISTEMOLOGICAL STANCE (what counts as evidence for you):
{epistemological_stance}

YOUR INFORMATION-SEEKING BEHAVIOR:
{information_seeking_behavior}

YOUR KNOWN LIMITATIONS:
{known_limitations}

YOUR ATTENTION PATTERN (what you notice first):
{attention_pattern}

---

OUTPUT FORMAT — THIS IS NON-NEGOTIABLE:

Your entire visible response MUST be a single JSON object matching the schema
below. NOTHING ELSE. Do not write:
  - headings (no "# Analysis" or "## Step 1")
  - markdown prose explaining your reasoning
  - numbered lists or bullet points outside of JSON array values
  - preambles like "Here is my analysis:" or "Based on the context..."
  - code fences (do not wrap in ```json or ```)

Your response is parsed by a strict JSON extractor. Any text outside the
JSON object will cause your prediction to be DISCARDED and your profile to
be marked FAILED. The analyst will never see your thinking if it leaks into
visible output. All reasoning MUST happen internally (in <think>...</think>
tokens, or in your internal chain-of-thought) before you emit the JSON.

---

CONTEXT-GROUNDED REASONING (internal thinking steps, not output structure):

You will receive a prediction question and CONTEXT containing intelligence claims.
Your prediction must be grounded in the specific facts present in the CONTEXT,
not in your prior knowledge of the topic. Your training data may be out of date.
THE CONTEXT IS THE GROUND TRUTH.

The following are INTERNAL thinking steps. They describe how to reason before
emitting the JSON. They are NOT the structure of your output — do NOT write them
out as a visible document. Think through them silently, then produce the JSON.

  (a) Internally extract 3-6 specific factual claims from the CONTEXT. Copy
      them out verbatim or near-verbatim. These will become entries in the
      "observed_facts" field of the JSON, nothing more.
  (b) Internally check whether your usual analytical method's default
      conclusion is consistent with these facts. If it is not, adjust your
      prediction to be consistent with the facts. The facts override the method.
  (c) Any fact that contradicts what your methodology would normally conclude
      goes into your "reasoning_summary" field — do not omit it, do not
      explain it away.
  (d) If the CONTEXT shows an event the question treats as hypothetical has
      already happened (e.g., a blockade is in effect, a leader has died),
      your prediction MUST reflect that the event has occurred. Do not
      predict the probability of a past event.

If your visible reasoning_summary contains a claim that contradicts an explicit
fact in the CONTEXT, your prediction will be flagged as a grounding failure
and your confidence will be forcibly reduced. Cite the context. Do not
confabulate.

If the CONTEXT is empty, sparse, or does not contain claims relevant to the
question, set observed_facts to ["No directly relevant context provided"]
and set confidence to a value below 0.5.

---

Produce your structured prediction as valid JSON matching EXACTLY this schema.
Emit ONLY this JSON object — nothing before it, nothing after it:

{{
  "observed_facts": ["<fact 1 copied from context>", "<fact 2>", "<fact 3>", ...],
  "prediction": "<one sentence describing the predicted outcome, consistent with observed_facts>",
  "confidence": <float 0.0-1.0>,
  "reasoning_summary": "<2-4 sentences explaining your reasoning. MUST cite at least 2 of the observed_facts by reference and acknowledge any that contradict your usual conclusion.>",
  "key_assumptions": ["<assumption 1>", "<assumption 2>", ...],
  "falsification_conditions": [
    {{"condition": "<what would make this prediction wrong>", "impact": "<how this changes the prediction>", "impact_magnitude": <float 0.0-1.0>}},
    ...
  ],
  "prior_assessment_reflection": "<1-3 sentences reflecting on your own last 1-2 predictions on this topic, if any were provided in YOUR PRIOR ASSESSMENTS below. Acknowledge whether they held up or missed. If no prior assessments exist, set this to null.>"{profile_extra_fields}
}}

Requirements:
- observed_facts is REQUIRED — at least 3 entries if context is non-empty, copied or near-verbatim from CONTEXT
- confidence must be between 0.01 and 0.99
- include 2-4 key_assumptions
- include 3-5 falsification_conditions with specific, observable triggers
- reasoning_summary must (a) reference your specific analytical method AND (b) cite at least 2 observed_facts AND (c) acknowledge any contradictions between facts and method
- falsification_conditions must NOT include events that have already occurred according to observed_facts
- prior_assessment_reflection is REQUIRED when YOUR PRIOR ASSESSMENTS section is present in the user message. Acknowledge misses explicitly — do not rewrite history. Set to null ONLY if no prior history was provided.{profile_extra_instructions}"""


# ============================================================
# Per-profile extra JSON fields and prompt instructions
# ============================================================

_HISTORIAN_EXTRA_FIELDS = """,
  "analogue_reference": "<name of the closest historical analogue>",
  "overall_similarity_score": <float 0.0-1.0>,
  "relevant_similarity_score": <float 0.0-1.0>,
  "similarity_dimensions_matched": ["<dimension 1>", "<dimension 2>", ...],
  "similarity_dimensions_not_matched": ["<dimension 1>", "<dimension 2>", ...],
  "relevance_rationale": "<why certain similarity dimensions are decision-relevant for this prediction>"
"""

_HISTORIAN_EXTRA_INSTRUCTIONS = """
- You MUST provide both overall_similarity_score and relevant_similarity_score
- relevant_similarity_score measures similarity on dimensions that actually drive the predicted outcome, not overall structural similarity
- A high overall_similarity_score with a low relevant_similarity_score means the analogue is structurally similar but not useful for this specific prediction
- Be honest about dissimilarities — they matter as much as similarities"""

_REFLEXIVITY_EXTRA_FIELDS = """,
  "feedback_direction": "<self-reinforcing | self-correcting | transitioning | unclear>",
  "loop_mechanism": "<describe the specific feedback loop: what variable feeds back on what, through what channel>",
  "current_phase": "<expansion | peak | contraction | trough | unknown>",
  "trigger_for_reversal": "<the specific observable condition that would flip the current feedback direction>"
"""

_REFLEXIVITY_EXTRA_INSTRUCTIONS = """
- feedback_direction is REQUIRED — this is the constraint field: self-reinforcing, self-correcting, transitioning, or unclear
- loop_mechanism must name the specific causal chain (X → Y → Z → X), not generic "feedback exists"
- current_phase places us in the reflexive cycle: expansion (loop accelerating), peak (maximum divergence), contraction (reversing), trough (correction completing)
- If the feedback loop is genuinely absent or unclear, set feedback_direction to "unclear" and explain why in reasoning_summary"""

_DECOMPOSER_EXTRA_FIELDS = """,
  "components": [
    {{"name": "<component name>", "estimate_low": <number>, "estimate_high": <number>, "unit": "<unit of measurement>", "weight_in_outcome": "<how this component combines into the final outcome>"}}
  ],
  "combination_method": "<multiplicative | additive | conditional — how components combine>",
  "dominant_uncertainty_component": "<which component contributes most to overall uncertainty and why>"
"""

_DECOMPOSER_EXTRA_INSTRUCTIONS = """
- Break the question into 3-6 independently estimable components BEFORE forming your prediction
- Each component must have low/high estimate range with units — this is the Fermi methodology
- combination_method: multiplicative (outcome = A × B × C), additive (outcome = A + B + C), or conditional (if A > threshold, then B applies)
- dominant_uncertainty_component: the one component whose range most drives the final uncertainty — this is what further investigation should target
- The final confidence should reflect the compounded uncertainty across all components"""

_NETWORK_ANALYST_EXTRA_FIELDS = """,
  "transmission_channels": ["<channel 1: how the primary event connects to secondary effect>", "<channel 2: different pathway>"],
  "second_order_effects": ["<effect of an effect — not the direct consequence, the downstream consequence>"],
  "network_amplification": "<amplifying | dampening | neutral>",
  "hidden_dependency": "<the non-obvious connection that most analysts are missing — the highest-value output>"
"""

_NETWORK_ANALYST_EXTRA_INSTRUCTIONS = """
- Identify at least 2 distinct transmission channels — different pathways through which the primary event propagates
- second_order_effects are effects of effects: not 'oil supply drops' (direct) but 'Asian refinery margin compression → petrochemical feedstock shortage → manufacturing cost inflation' (second-order)
- hidden_dependency is the overlooked connection that changes the conclusion — if there is nothing hidden, say so explicitly
- network_amplification: does the network structure make the primary event bigger (amplifying) or smaller (dampening) than it appears in isolation?"""

_SENTIMENT_DECODER_EXTRA_FIELDS = """,
  "narrative_claim": "<what the prevailing narrative or consensus is currently asserting>",
  "data_shows": "<what observable, measurable data actually indicates — independently of how it is being interpreted>",
  "gap_assessment": "<large | moderate | small | none>",
  "gap_direction": "<narrative_overestimates | narrative_underestimates | narrative_accurate>"
"""

_SENTIMENT_DECODER_EXTRA_INSTRUCTIONS = """
- narrative_claim is the current dominant story — what are participants broadly asserting? What does consensus pricing imply?
- data_shows is concrete, observable evidence — what do inventory levels, positioning data, physical flows, or economic indicators actually show?
- gap_assessment measures how large the divergence is between narrative and data
- gap_direction: narrative_overestimates means sentiment is more bullish than data supports; narrative_underestimates means more bearish"""

_RISK_MANAGER_EXTRA_FIELDS = """,
  "tail_weight": "<fat | normal | thin>",
  "central_scenario": "<description of the base case — the most likely outcome>",
  "central_scenario_probability": <float 0.0-1.0>,
  "adverse_scenario": "<1-in-5 bad outcome: description of what this looks like>",
  "max_adverse_scenario": "<1-in-20 or worse: the extreme tail — what is the worst non-trivially-possible outcome?>",
  "distribution_asymmetry": "<left-skewed | symmetric | right-skewed>"
"""

_RISK_MANAGER_EXTRA_INSTRUCTIONS = """
- tail_weight is REQUIRED: fat (power-law domain — more extreme events than models predict), normal (roughly Gaussian), thin (bounded outcomes)
- central_scenario_probability is your base case probability — explicitly acknowledge what probability remains for other outcomes
- adverse_scenario is roughly a 1-in-5 bad outcome — not catastrophic, but clearly bad
- max_adverse_scenario is the 1-in-20 or worse extreme tail — the outcome whose magnitude demands attention even at low probability
- distribution_asymmetry: left-skewed means the downside tail is fatter than upside; right-skewed is the reverse
- The confidence field reflects your certainty about the DIRECTION of the prediction, not the precision of the magnitude"""

_DEVILS_INQUISITOR_EXTRA_FIELDS = """,
  "surprising_facts": ["<load-bearing fact 1 from context that would update a confident prior>", "<fact 2>", "<fact 3>"],
  "predicted_blind_spots": [
    {{"profile": "<name of another profile>", "likely_to_miss": "<which surprising fact this profile will probably ignore>", "why": "<methodological reason this profile structurally overlooks it>"}}
  ],
  "consensus_warning": "<the most important thing the consensus is about to miss, in one sentence>"
"""

_DEVILS_INQUISITOR_EXTRA_INSTRUCTIONS = """
- surprising_facts MUST be drawn from the CONTEXT (not from your training data). At least 3 entries.
- A 'surprising fact' is one that would update a confident prior — not background information.
- predicted_blind_spots predicts which OTHER profiles will fail to engage with each surprising fact and why.
- The 'prediction' field for this profile is META: it describes what the consensus is about to miss, not the future state of the world.
- The 'confidence' field for this profile reflects HOW CONFIDENT YOU ARE that the consensus will miss what you've identified — not how confident you are in any particular outcome.
- If the context contains nothing surprising, say so explicitly. Do not manufacture surprises."""


# Lookup: profile name → (extra_fields_json_fragment, extra_instructions_text)
_PROFILE_EXTRA_PROMPTS: dict = {
    "Historian":           (_HISTORIAN_EXTRA_FIELDS,        _HISTORIAN_EXTRA_INSTRUCTIONS),
    "Reflexivity Modeler": (_REFLEXIVITY_EXTRA_FIELDS,      _REFLEXIVITY_EXTRA_INSTRUCTIONS),
    "Decomposer":          (_DECOMPOSER_EXTRA_FIELDS,       _DECOMPOSER_EXTRA_INSTRUCTIONS),
    "Network Analyst":     (_NETWORK_ANALYST_EXTRA_FIELDS,  _NETWORK_ANALYST_EXTRA_INSTRUCTIONS),
    "Sentiment Decoder":   (_SENTIMENT_DECODER_EXTRA_FIELDS,_SENTIMENT_DECODER_EXTRA_INSTRUCTIONS),
    "Risk Manager":        (_RISK_MANAGER_EXTRA_FIELDS,     _RISK_MANAGER_EXTRA_INSTRUCTIONS),
    "Devil's Inquisitor":  (_DEVILS_INQUISITOR_EXTRA_FIELDS,_DEVILS_INQUISITOR_EXTRA_INSTRUCTIONS),
}

# Fields that belong to the base prediction schema — everything else goes to profile_extra_data
_BASE_PREDICTION_FIELDS = frozenset({
    "prediction", "confidence", "reasoning_summary", "key_assumptions",
    "falsification_conditions", "constraints_applied", "confidence_capped",
    "confidence_cap_reason",
    # Historian's dedicated DB columns — also base for backward compat
    "analogue_reference", "overall_similarity_score", "relevant_similarity_score",
    "similarity_dimensions_matched", "similarity_dimensions_not_matched",
    "relevance_rationale",
})


def build_system_prompt(profile: dict) -> str:
    extra_fields, extra_instructions = _PROFILE_EXTRA_PROMPTS.get(
        profile["name"], ("", "")
    )
    return SYSTEM_PROMPT_TEMPLATE.format(
        name=profile["name"],
        analytical_method=profile["analytical_method"],
        epistemological_stance=profile["epistemological_stance"],
        information_seeking_behavior=profile["information_seeking_behavior"],
        known_limitations=profile["known_limitations"],
        attention_pattern=profile["attention_pattern"],
        profile_extra_fields=extra_fields,
        profile_extra_instructions=extra_instructions,
    )


def get_profile_prior_history(db_conn, profile_name: str, question: str,
                               limit: int = 2) -> list[dict]:
    """Fetch this profile's last N predictions on the same topic for
    self-reference injection.

    2026-04-14 learning-loop enhancement: each profile reviews its own
    recent track record on this specific topic before writing a new
    prediction. If a prior prediction was falsified by the resolver, the
    profile sees that and MUST acknowledge the miss in its new output.

    We match "same topic" loosely by substring: we extract the part of the
    question after 'for:' and before the first '.', then look for other
    sessions whose question contains the same substring. This handles the
    autonomous monitor's canonical question format.
    """
    import re as _re
    m = _re.search(r'\bfor:\s*([^.?\n]+)', question or '', _re.IGNORECASE)
    if not m:
        return []
    topic_substr = m.group(1).strip()
    if len(topic_substr) < 3:
        return []

    cursor = db_conn.cursor()
    try:
        cursor.execute("""
            SELECT s.id, s.question, s.created_at, s.consensus_confidence,
                   s.meta_confidence,
                   p.confidence, p.prediction, p.reasoning_summary,
                   p.confidence_capped,
                   (SELECT r.verdict FROM acp_proposed_resolutions r
                    WHERE r.session_id = s.id
                    ORDER BY r.created_at DESC LIMIT 1) AS resolver_verdict,
                   (SELECT r.outcome_text FROM acp_proposed_resolutions r
                    WHERE r.session_id = s.id
                    ORDER BY r.created_at DESC LIMIT 1) AS resolver_outcome_text
            FROM acp_sessions s
            JOIN acp_session_predictions sp ON sp.session_id = s.id
            JOIN acp_predictions p ON p.id = sp.prediction_id
            WHERE s.question ILIKE %s
              AND p.profile_name = %s
              AND p.error IS NULL
              AND p.confidence IS NOT NULL
            ORDER BY s.created_at DESC
            LIMIT %s
        """, (f"%{topic_substr}%", profile_name, limit))
        rows = cursor.fetchall()
    except Exception as e:
        print(f"[PRIOR] Could not fetch prior history for {profile_name}: {e}", flush=True)
        return []
    finally:
        cursor.close()

    history = []
    for r in rows:
        history.append({
            "session_id": str(r[0]),
            "question": r[1],
            "created_at": r[2].isoformat() if r[2] else None,
            "session_consensus": r[3],
            "session_meta": r[4],
            "my_confidence": r[5],
            "my_prediction": r[6],
            "my_reasoning": r[7],
            "my_capped": r[8],
            "resolver_verdict": r[9],
            "resolver_outcome": r[10],
        })
    return history


def _format_prior_history_block(history: list[dict], profile_name: str) -> str:
    """Render the prior history as a plain-text block for injection into
    the user message. Oldest-first so the profile sees the chronological
    sequence of its own thinking."""
    if not history:
        return ""

    # Reverse so oldest first — easier to reason about temporal order
    ordered = list(reversed(history))
    lines = [
        f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"YOUR PRIOR ASSESSMENTS on this topic ({len(ordered)} most recent):",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    for i, h in enumerate(ordered, start=1):
        ts = (h.get("created_at") or "")[:10]
        conf_pct = int((h.get("my_confidence") or 0) * 100)
        capped_note = " (CAPPED — grounding failure)" if h.get("my_capped") else ""
        lines.append(f"\n[{i}] {ts} · your confidence was {conf_pct}%{capped_note}")
        pred = (h.get("my_prediction") or "").strip()
        if pred:
            lines.append(f"    Your prediction: {pred[:300]}")
        reasoning = (h.get("my_reasoning") or "").strip()
        if reasoning:
            lines.append(f"    Your reasoning: {reasoning[:300]}")
        verdict = h.get("resolver_verdict")
        if verdict:
            v_note = {
                "falsified": "⚠ the autonomous resolver later FALSIFIED this prediction",
                "confirmed": "✓ the autonomous resolver later CONFIRMED this prediction",
                "still_pending": "the resolver could not determine whether this held (still pending)",
            }.get(verdict, f"resolver verdict: {verdict}")
            lines.append(f"    → {v_note}")
            outcome = (h.get("resolver_outcome") or "").strip()
            if outcome and verdict == "falsified":
                lines.append(f"    → What actually happened: {outcome[:250]}")
    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "In your prior_assessment_reflection field (REQUIRED for this",
        "prediction), briefly note how your prior predictions held up.",
        "If any were falsified, acknowledge the miss explicitly and say",
        "what you should weight differently this time. Do not rewrite",
        "history or explain away misses.",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
    ]
    return "\n".join(lines)


def build_user_message(question: str, domain: str, context: Optional[str],
                        prior_history_block: Optional[str] = None) -> str:
    parts = [
        f"PREDICTION QUESTION: {question}",
        f"DOMAIN: {domain}",
    ]
    # Prior history goes BEFORE the current context so the profile sees its
    # own track record first. This frames the incoming context as an update
    # to a continuing assessment rather than a fresh problem.
    if prior_history_block:
        parts.append(prior_history_block)
    if context:
        parts.append(
            f"\nCONTEXT — THIS IS THE GROUND TRUTH. Your training data may be out of date. "
            f"The facts below describe the actual current situation. Read every claim. "
            f"Your prediction MUST be consistent with what these claims say.\n\n{context}"
        )
        parts.append(
            "\nBefore writing your prediction, extract 3-6 specific factual claims from "
            "the CONTEXT above into the observed_facts field. Then check whether your "
            "usual conclusion is consistent with those facts. If the context says an "
            "event has already happened, your prediction must reflect that — do not "
            "predict the probability of a past event. Apply your analytical method "
            "but let the context override your priors when they conflict."
        )
    else:
        parts.append(
            "\nNO CONTEXT PROVIDED. You cannot make a confident prediction from absent data. "
            "Set observed_facts to ['No context provided'] and set confidence below 0.4."
        )
    parts.append("\nProduce your structured JSON prediction now.")
    return "\n".join(parts)


# ============================================================
# LLM call + JSON extraction
# ============================================================

_JIT_ERRORS = ("model unloaded", "operation canceled", "failed to load model", "context size")

def call_llm(system_prompt: str, user_message: str) -> str:
    """Call LM Studio, return raw response content string.

    Retries once on LM Studio JIT-unload errors (model evicted between calls).
    """
    client = get_llm_client()
    kwargs = dict(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        temperature=config.LLM_TEMPERATURE,
        max_tokens=config.LLM_MAX_TOKENS,
    )
    for attempt in range(2):
        try:
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()
        except Exception as e:
            err = str(e).lower()
            if attempt == 0 and any(jit in err for jit in _JIT_ERRORS):
                print(f"[ACP] LM Studio JIT unload detected, retrying in 15s...", flush=True)
                time.sleep(15)
                continue
            raise


# ============================================================
# Grounding validation — Phase 2 of the OSS+SWARMFISH overhaul
# ============================================================
#
# Background: ST-007 documented that profiles confabulate against the input
# context — Sentiment Decoder asserted "stable insurance rates" while the
# input context contained "war-risk premiums increased." The Phase 1 quality
# gate caught contaminated INPUT but not contradicted REASONING. This module
# is the reasoning-layer check.
#
# Approach: lightweight, no extra LLM calls. The profile is required to
# extract 3+ observed_facts from context. We then verify two things:
#
#   1. observed_facts must be present and non-trivial
#   2. each claimed observed_fact must actually appear in the context
#      (substring or strong-overlap match, not exact)
#
# If either check fails, the profile is marked GROUNDING_FAILED and its
# confidence is forcibly capped at 0.4. The aggregator should treat
# grounding-failed profiles as low-weight contributors to consensus.
#
# This does not catch every form of confabulation, but it catches the
# specific failure mode observed in ST-007: a profile that simply doesn't
# read its input.

_GROUNDING_MIN_FACTS = 3
_GROUNDING_MIN_FACT_CHARS = 15
_GROUNDING_OVERLAP_THRESHOLD = 0.6  # fraction of fact words that must appear in context

_TRIVIAL_FACTS = frozenset({
    "no context provided",
    "no directly relevant context provided",
    "no relevant context",
    "context is empty",
    "context not provided",
})


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _fact_appears_in_context(fact: str, context_norm: str) -> bool:
    """Check if a claimed observed fact actually appears in the context.

    Uses substring match first (handles verbatim copies and near-verbatim).
    Falls back to word-overlap heuristic for paraphrased extractions.
    """
    fact_norm = _normalize(fact)
    if len(fact_norm) < _GROUNDING_MIN_FACT_CHARS:
        return False

    # Try substring match — strongest signal
    if fact_norm in context_norm:
        return True

    # Word-overlap fallback: at least 60% of fact words appear in context.
    # Filter to content words longer than 3 chars to avoid stopword noise.
    fact_words = {w for w in re.findall(r"\w+", fact_norm) if len(w) > 3}
    if not fact_words:
        return False
    matched = sum(1 for w in fact_words if w in context_norm)
    return matched / len(fact_words) >= _GROUNDING_OVERLAP_THRESHOLD


def validate_grounding(parsed: dict, context: Optional[str]) -> dict:
    """Run grounding validation on a parsed profile output.

    Mutates `parsed` to add `grounding_status`, `grounding_failure_reason`,
    and may forcibly cap `confidence`. Returns the mutated dict.

    Status values: 'ok', 'no_context', 'missing_facts', 'fabricated_facts'.
    """
    facts = parsed.get("observed_facts") or []
    if not isinstance(facts, list):
        facts = []
    facts = [str(f).strip() for f in facts if str(f).strip()]

    # No context — profile correctly observes that, no penalty
    if not context or len(context.strip()) < 50:
        if facts and any(_normalize(f) in _TRIVIAL_FACTS for f in facts):
            parsed["grounding_status"] = "no_context"
            return parsed
        # Profile didn't acknowledge the empty context — minor failure
        parsed["grounding_status"] = "no_context"
        parsed["grounding_failure_reason"] = "context was empty but profile did not acknowledge it"
        return parsed

    # Context exists — check fact count
    real_facts = [f for f in facts if _normalize(f) not in _TRIVIAL_FACTS]
    if len(real_facts) < _GROUNDING_MIN_FACTS:
        parsed["grounding_status"] = "missing_facts"
        parsed["grounding_failure_reason"] = (
            f"profile provided only {len(real_facts)} observed_facts "
            f"(minimum {_GROUNDING_MIN_FACTS} required from non-empty context)"
        )
        # Cap confidence at 0.4 — profile didn't engage with the input
        original = parsed.get("confidence", 0.5)
        if original > 0.4:
            parsed["confidence"] = 0.4
            parsed["confidence_capped"] = True
            parsed["confidence_cap_reason"] = (
                f"GROUNDING FAILURE: missing observed_facts (had {len(real_facts)}, "
                f"need {_GROUNDING_MIN_FACTS}). Original confidence: {original:.2f}"
            )
        return parsed

    # Check each claimed fact actually appears in the context
    context_norm = _normalize(context)
    fabricated = []
    for f in real_facts:
        if not _fact_appears_in_context(f, context_norm):
            fabricated.append(f[:120])

    fabricated_ratio = len(fabricated) / len(real_facts)

    if fabricated_ratio >= 0.5:
        # Half or more of the "facts" don't match the context — the profile
        # is making things up. This is the ST-007 confabulation pattern.
        parsed["grounding_status"] = "fabricated_facts"
        parsed["grounding_failure_reason"] = (
            f"profile fabricated {len(fabricated)}/{len(real_facts)} observed_facts "
            f"that do not appear in the provided context. Examples: " +
            "; ".join(fabricated[:3])
        )
        original = parsed.get("confidence", 0.5)
        if original > 0.3:
            parsed["confidence"] = 0.3
            parsed["confidence_capped"] = True
            parsed["confidence_cap_reason"] = (
                f"GROUNDING FAILURE: {len(fabricated)}/{len(real_facts)} observed_facts "
                f"do not appear in context (confabulation). Original confidence: {original:.2f}"
            )
    elif fabricated:
        # Some facts didn't match but most did — minor failure, just note it
        parsed["grounding_status"] = "partial"
        parsed["grounding_failure_reason"] = (
            f"{len(fabricated)}/{len(real_facts)} observed_facts could not be verified "
            f"against context (treating as paraphrase, no confidence cap)"
        )
    else:
        parsed["grounding_status"] = "ok"

    return parsed


def extract_json(raw: str) -> dict:
    """
    Extract JSON from LLM response. Handles:
    - reasoning-model thinking tokens (<think>...</think>)
    - markdown code fences (```json ... ```)
    - bare JSON or JSON embedded in prose
    - markdown-wrapped JSON where the model wrote a preamble (headers,
      numbered lists) before finally emitting a JSON object

    Raises ValueError with a diagnostic message AND the first 800 chars
    of the raw output on failure so the caller can log it for debugging.
    """
    # Save the original for error-path logging — we want to see exactly what
    # the LLM produced, not the stripped version
    original_raw = raw or ""

    # Strip XML-style reasoning sections (thinking tokens, analysis blocks, etc.)
    raw = re.sub(r"<[a-zA-Z_]+>.*?</[a-zA-Z_]+>", "", raw, flags=re.DOTALL).strip()

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    raw = re.sub(r"^```[a-zA-Z]*\s*", "", raw).strip()
    raw = re.sub(r"\s*```$", "", raw).strip()

    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try to find a `{` that opens a balanced JSON object. Greedy match
    # from the first `{` to the last `}`, then walk backward if parse fails.
    first_brace = raw.find("{")
    last_brace = raw.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        candidate = raw[first_brace:last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Last-ditch effort: scan for any `{...}` block and try each one
    # from longest to shortest — handles cases where the model wrote
    # multiple fragments of JSON or where nested braces confused the
    # greedy match above.
    matches = re.findall(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", raw, re.DOTALL)
    for m in sorted(matches, key=len, reverse=True):
        try:
            parsed = json.loads(m)
            # Only accept if it has at least one of the base schema keys,
            # to avoid false-positive matches on tiny fragments
            if any(k in parsed for k in ("prediction", "confidence", "observed_facts", "reasoning_summary")):
                return parsed
        except json.JSONDecodeError:
            continue

    raise ValueError(
        f"Could not extract valid JSON from LLM response: "
        f"{original_raw[:300]!r}... (total length: {len(original_raw)} chars)"
    )


# ============================================================
# DB write
# ============================================================

def write_prediction(db_conn, session_id: Optional[str],
                     profile_name: str, question: str, domain: str,
                     context_summary: Optional[str], parsed: Optional[dict],
                     error: Optional[str] = None) -> str:
    """Write a prediction (or error record) to acp_predictions. Returns prediction_id.

    When error is provided, parsed may be None — a row is written with NULL for all
    LLM-output fields so the failure is visible in GET /acp/session/<id>.
    """
    pred_id = str(uuid.uuid4())
    cursor = db_conn.cursor()
    parsed = parsed or {}

    # Collect profile-specific extra fields into profile_extra_data JSONB
    profile_extra_data = None
    if parsed:
        extra = {k: v for k, v in parsed.items() if k not in _BASE_PREDICTION_FIELDS}
        if extra:
            profile_extra_data = json.dumps(extra)

    cursor.execute("""
        INSERT INTO acp_predictions (
            id, profile_name, question, domain, context_summary,
            prediction, confidence, reasoning_summary,
            key_assumptions, falsification_conditions,
            analogue_reference, overall_similarity_score, relevant_similarity_score,
            similarity_dimensions_matched, similarity_dimensions_not_matched,
            relevance_rationale,
            constraints_applied, confidence_capped, confidence_cap_reason,
            profile_extra_data,
            error
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s, %s,
            %s, %s,
            %s,
            %s, %s, %s,
            %s,
            %s
        )
    """, (
        pred_id, profile_name, question, domain, context_summary,
        parsed.get("prediction") or None,
        parsed.get("confidence") if parsed.get("confidence") is not None else None,
        parsed.get("reasoning_summary") or None,
        json.dumps(parsed.get("key_assumptions", [])) if parsed else None,
        json.dumps(parsed.get("falsification_conditions", [])) if parsed else None,
        parsed.get("analogue_reference"),
        parsed.get("overall_similarity_score"),
        parsed.get("relevant_similarity_score"),
        json.dumps(parsed.get("similarity_dimensions_matched")) if parsed.get("similarity_dimensions_matched") else None,
        json.dumps(parsed.get("similarity_dimensions_not_matched")) if parsed.get("similarity_dimensions_not_matched") else None,
        parsed.get("relevance_rationale"),
        json.dumps(parsed.get("constraints_applied", [])) if parsed else None,
        bool(parsed.get("confidence_capped", False)) if parsed else False,
        parsed.get("confidence_cap_reason"),
        profile_extra_data,
        error,
    ))

    # Link to session if provided
    if session_id:
        cursor.execute("""
            INSERT INTO acp_session_predictions (session_id, prediction_id)
            VALUES (%s, %s)
        """, (session_id, pred_id))

    db_conn.commit()
    cursor.close()
    return pred_id


# ============================================================
# Public API: run a single profile against a question
# ============================================================

def run_profile(db_conn, profile: dict, question: str, domain: str,
                context: Optional[str] = None,
                session_id: Optional[str] = None,
                context_summary: Optional[str] = None) -> dict:
    """
    Run one profile against a prediction question.

    Returns dict with prediction_id, profile_name, confidence, prediction,
    reasoning_summary, falsification_conditions, and constraint metadata.
    Never raises — returns error dict on failure so other profiles can proceed.
    """
    profile_name = profile["name"]
    raw = ""  # captured outside the try so the exception handler can log it
    try:
        system_prompt = build_system_prompt(profile)
        # Fetch this profile's own recent history on the same topic and
        # inject it into the user message. Self-reference enables the
        # learning loop — profiles acknowledge their own misses, the
        # analyst reviews the reflection, misses become visible rather
        # than silently repeating.
        prior_history = get_profile_prior_history(db_conn, profile_name, question, limit=2)
        prior_block = _format_prior_history_block(prior_history, profile_name) if prior_history else None
        if prior_block:
            print(f"[PRIOR] Injected {len(prior_history)} prior assessment(s) for {profile_name}", flush=True)
        user_message  = build_user_message(question, domain, context, prior_block)

        raw = call_llm(system_prompt, user_message)
        try:
            parsed = extract_json(raw)
        except ValueError as parse_err:
            # 2026-04-14 investigation: Base Rate Analyst produced markdown prose
            # instead of JSON, and the error message only captured the first 80
            # chars of the output. Log a larger window here so future parse
            # failures are diagnosable — what did the model actually generate?
            print(
                f"[ACP] {profile_name} JSON PARSE FAILED. Raw output (first 1200 chars):\n"
                f"───────────────────────────────────────────────────\n"
                f"{raw[:1200]}\n"
                f"───────────────────────────────────────────────────",
                flush=True,
            )
            raise

        # Clamp confidence to valid range before constraint application
        parsed["confidence"] = max(0.01, min(0.99, float(parsed.get("confidence", 0.5))))

        # Phase 2 grounding validation — verify the profile actually engaged
        # with the provided context. May forcibly cap confidence on failure.
        parsed = validate_grounding(parsed, context)

        # Apply mechanical constraints (Historian similarity scoring, etc.)
        parsed = apply_constraints(profile_name, parsed)

        # Write to DB
        pred_id = write_prediction(
            db_conn, session_id, profile_name, question, domain,
            context_summary or (context[:200] if context else None), parsed
        )

        gs = parsed.get('grounding_status', 'ok')
        gs_marker = '' if gs == 'ok' else f" grounding={gs}"
        print(f"[ACP] {profile_name}: confidence={parsed['confidence']:.2f} "
              f"capped={parsed.get('confidence_capped', False)}{gs_marker}", flush=True)

        # Collect profile-specific extra data for the return dict
        profile_extra_data = {
            k: v for k, v in parsed.items() if k not in _BASE_PREDICTION_FIELDS
        }

        return {
            "prediction_id": pred_id,
            "profile_name": profile_name,
            "prediction": parsed.get("prediction", ""),
            "confidence": parsed["confidence"],
            "reasoning_summary": parsed.get("reasoning_summary", ""),
            "key_assumptions": parsed.get("key_assumptions", []),
            "falsification_conditions": parsed.get("falsification_conditions", []),
            "analogue_reference": parsed.get("analogue_reference"),
            "overall_similarity_score": parsed.get("overall_similarity_score"),
            "relevant_similarity_score": parsed.get("relevant_similarity_score"),
            "profile_extra_data": profile_extra_data or None,
            "constraints_applied": parsed.get("constraints_applied", []),
            "confidence_capped": parsed.get("confidence_capped", False),
            "confidence_cap_reason": parsed.get("confidence_cap_reason"),
            "error": None,
        }

    except Exception as e:
        err_str = str(e)
        print(f"[ACP] {profile_name} FAILED: {err_str}", flush=True)
        # Write error row so GET /acp/session/<id> shows the failure rather than
        # silently omitting the profile from the predictions list.
        pred_id = None
        try:
            pred_id = write_prediction(
                db_conn, session_id, profile_name, question, domain,
                context_summary or (context[:200] if context else None),
                parsed=None, error=err_str,
            )
        except Exception as write_err:
            print(f"[ACP] {profile_name} error recording also failed: {write_err}", flush=True)
        return {
            "prediction_id": pred_id,
            "profile_name": profile_name,
            "prediction": None,
            "confidence": None,
            "error": err_str,
        }


def load_profiles_from_db(db_conn, profile_names: Optional[list] = None) -> list:
    """Load profile dicts from DB. Optionally filter by name list."""
    cursor = db_conn.cursor()
    if profile_names:
        placeholders = ",".join(["%s"] * len(profile_names))
        cursor.execute(
            f"SELECT * FROM acp_profiles WHERE name IN ({placeholders})",
            profile_names
        )
    else:
        cursor.execute("SELECT * FROM acp_profiles ORDER BY id")

    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    return [dict(zip(cols, row)) for row in rows]
