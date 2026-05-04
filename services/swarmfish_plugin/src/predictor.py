"""
predictor.py — SWARMFISH V2 prediction engine

V2 changes from V1:
  - SQLite storage (replaces psycopg2)
  - full_reasoning stored per assessment (Level 3 transparency)
  - async parallel dispatch via asyncio.to_thread()
  - configurable committee (subset of 8 profiles)
  - self-contained (no external config module)
"""

import asyncio
import json
import os
import re
import sqlite3
import time
import uuid
from typing import Optional

from openai import OpenAI

# ─────────────────────────────────────────────────────────────
# Config — reads env vars or defaults
# ─────────────────────────────────────────────────────────────

LLM_BASE_URL  = os.environ.get("SWARMFISH_LLM_URL",   "http://host.docker.internal:1234/v1")
LLM_API_KEY   = os.environ.get("SWARMFISH_LLM_API_KEY","lm-studio")

from llm_config import get_llm_model as _get_llm_model
LLM_MODEL     = _get_llm_model()
LLM_MAX_TOKENS = int(os.environ.get("SWARMFISH_LLM_MAX_TOKENS", "4096"))
LLM_TEMPERATURE = 0.1
LLM_TIMEOUT   = int(os.environ.get("SWARMFISH_LLM_TIMEOUT", "120"))

_llm_client: Optional[OpenAI] = None

def _get_client() -> OpenAI:
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY, timeout=LLM_TIMEOUT)
    return _llm_client


# ─────────────────────────────────────────────────────────────
# Prompt construction (identical to V1)
# ─────────────────────────────────────────────────────────────

_SYSTEM_TEMPLATE = """You are {name}, an analytical agent with a specific methodology for forming predictions.

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

You will be given a prediction question and optional context.
Apply your specific analytical method to produce a structured prediction.

You MUST respond with valid JSON in exactly this format — no prose outside the JSON:

{{
  "prediction": "<one sentence describing the predicted outcome>",
  "confidence": <float 0.0-1.0>,
  "reasoning_summary": "<2-4 sentences explaining your reasoning, citing your analytical method>",
  "key_assumptions": ["<assumption 1>", "<assumption 2>"],
  "falsification_conditions": [
    {{"condition": "<what would make this prediction wrong>", "impact": "<how this changes the prediction>", "impact_magnitude": <float 0.0-1.0>}}
  ]{profile_extra_fields}
}}

Requirements:
- confidence must be between 0.01 and 0.99
- include 2-4 key_assumptions
- include 3-5 falsification_conditions with specific, observable triggers
- reasoning_summary must reference your specific analytical method, not generic analysis{profile_extra_instructions}"""

_HISTORIAN_EXTRA_FIELDS = """,
  "analogue_reference": "<name of the closest historical analogue>",
  "overall_similarity_score": <float 0.0-1.0>,
  "relevant_similarity_score": <float 0.0-1.0>,
  "similarity_dimensions_matched": ["<dimension 1>"],
  "similarity_dimensions_not_matched": ["<dimension 1>"],
  "relevance_rationale": "<why certain similarity dimensions are decision-relevant>"
"""
_HISTORIAN_EXTRA_INSTRUCTIONS = """
- You MUST provide both overall_similarity_score and relevant_similarity_score
- relevant_similarity_score measures similarity on dimensions that drive the predicted outcome
- Be honest about dissimilarities — they matter as much as similarities"""

_REFLEXIVITY_EXTRA_FIELDS = """,
  "feedback_direction": "<self-reinforcing | self-correcting | transitioning | unclear>",
  "loop_mechanism": "<the specific feedback loop: what variable feeds back on what>",
  "current_phase": "<expansion | peak | contraction | trough | unknown>",
  "trigger_for_reversal": "<the specific observable condition that would flip the feedback direction>"
"""
_REFLEXIVITY_EXTRA_INSTRUCTIONS = """
- feedback_direction is REQUIRED: self-reinforcing, self-correcting, transitioning, or unclear
- loop_mechanism must name the specific causal chain (X → Y → Z → X)"""

_DECOMPOSER_EXTRA_FIELDS = """,
  "components": [
    {{"name": "<component name>", "estimate_low": <number>, "estimate_high": <number>, "unit": "<unit>", "weight_in_outcome": "<how this combines into the final outcome>"}}
  ],
  "combination_method": "<multiplicative | additive | conditional>",
  "dominant_uncertainty_component": "<which component contributes most to overall uncertainty>"
"""
_DECOMPOSER_EXTRA_INSTRUCTIONS = """
- Break the question into 3-6 independently estimable components BEFORE forming your prediction
- Each component must have low/high estimate range with units"""

_NETWORK_ANALYST_EXTRA_FIELDS = """,
  "transmission_channels": ["<channel 1: how the primary event connects to secondary effect>"],
  "second_order_effects": ["<effect of an effect>"],
  "network_amplification": "<amplifying | dampening | neutral>",
  "hidden_dependency": "<the non-obvious connection most analysts are missing>"
"""
_NETWORK_ANALYST_EXTRA_INSTRUCTIONS = """
- Identify at least 2 distinct transmission channels
- second_order_effects are effects of effects, not direct consequences"""

_SENTIMENT_DECODER_EXTRA_FIELDS = """,
  "narrative_claim": "<what the prevailing narrative is currently asserting>",
  "data_shows": "<what observable data actually indicates>",
  "gap_assessment": "<large | moderate | small | none>",
  "gap_direction": "<narrative_overestimates | narrative_underestimates | narrative_accurate>"
"""
_SENTIMENT_DECODER_EXTRA_INSTRUCTIONS = """
- narrative_claim is the current dominant story — what are participants broadly asserting?
- data_shows is concrete, observable evidence"""

_RISK_MANAGER_EXTRA_FIELDS = """,
  "tail_weight": "<fat | normal | thin>",
  "central_scenario": "<description of the base case>",
  "central_scenario_probability": <float 0.0-1.0>,
  "adverse_scenario": "<1-in-5 bad outcome>",
  "max_adverse_scenario": "<1-in-20 or worse: the extreme tail>",
  "distribution_asymmetry": "<left-skewed | symmetric | right-skewed>"
"""
_RISK_MANAGER_EXTRA_INSTRUCTIONS = """
- tail_weight is REQUIRED: fat, normal, or thin
- central_scenario_probability is your base case probability
- adverse_scenario is roughly a 1-in-5 bad outcome"""

_PROFILE_EXTRA: dict = {
    "Historian":           (_HISTORIAN_EXTRA_FIELDS,        _HISTORIAN_EXTRA_INSTRUCTIONS),
    "Reflexivity Modeler": (_REFLEXIVITY_EXTRA_FIELDS,      _REFLEXIVITY_EXTRA_INSTRUCTIONS),
    "Decomposer":          (_DECOMPOSER_EXTRA_FIELDS,       _DECOMPOSER_EXTRA_INSTRUCTIONS),
    "Network Analyst":     (_NETWORK_ANALYST_EXTRA_FIELDS,  _NETWORK_ANALYST_EXTRA_INSTRUCTIONS),
    "Sentiment Decoder":   (_SENTIMENT_DECODER_EXTRA_FIELDS,_SENTIMENT_DECODER_EXTRA_INSTRUCTIONS),
    "Risk Manager":        (_RISK_MANAGER_EXTRA_FIELDS,     _RISK_MANAGER_EXTRA_INSTRUCTIONS),
}

_BASE_FIELDS = frozenset({
    "prediction", "confidence", "reasoning_summary", "key_assumptions",
    "falsification_conditions", "constraints_applied", "confidence_capped",
    "confidence_cap_reason",
    "analogue_reference", "overall_similarity_score", "relevant_similarity_score",
    "similarity_dimensions_matched", "similarity_dimensions_not_matched",
    "relevance_rationale",
})


def _build_system_prompt(profile: dict) -> str:
    extra_fields, extra_instructions = _PROFILE_EXTRA.get(profile["name"], ("", ""))
    return _SYSTEM_TEMPLATE.format(
        name=profile["name"],
        analytical_method=profile["analytical_method"],
        epistemological_stance=profile["epistemological_stance"],
        information_seeking_behavior=profile["information_seeking_behavior"],
        known_limitations=profile["known_limitations"],
        attention_pattern=profile["attention_pattern"],
        profile_extra_fields=extra_fields,
        profile_extra_instructions=extra_instructions,
    )


def _build_user_message(question: str, domain: str, context: Optional[str]) -> str:
    parts = [f"PREDICTION QUESTION: {question}", f"DOMAIN: {domain}"]
    if context:
        parts.append(f"\nCONTEXT (analyst-supplied data and analysis):\n{context}")
    parts.append("\nApply your analytical method and produce your structured prediction.")
    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────
# LLM call
# ─────────────────────────────────────────────────────────────

_JIT_ERRORS = ("model unloaded", "operation canceled", "failed to load model", "context size")


def _call_llm(system_prompt: str, user_message: str) -> str:
    """Call LM Studio. Retries once on JIT-unload errors."""
    client = _get_client()
    kwargs = dict(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
    )
    for attempt in range(2):
        try:
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()
        except Exception as e:
            err = str(e).lower()
            if attempt == 0 and any(jit in err for jit in _JIT_ERRORS):
                print(f"[SWARM] LM Studio JIT unload, retrying in 15s...", flush=True)
                time.sleep(15)
                continue
            raise


def _extract_json(raw: str) -> dict:
    """Extract JSON from LLM response, handling thinking tokens and code fences."""
    raw = re.sub(r"<[a-zA-Z_]+>.*?</[a-zA-Z_]+>", "", raw, flags=re.DOTALL).strip()
    raw = re.sub(r"^```[a-zA-Z]*\s*", "", raw).strip()
    raw = re.sub(r"\s*```$", "", raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not extract JSON from LLM response: {raw[:300]}")


# ─────────────────────────────────────────────────────────────
# Constraint application (historian confidence scaling)
# ─────────────────────────────────────────────────────────────

def _apply_constraints(profile_name: str, parsed: dict) -> dict:
    """Apply mechanical constraints per profile attribution_constraints."""
    parsed = dict(parsed)
    if profile_name == "Historian":
        rel_sim = parsed.get("relevant_similarity_score")
        if rel_sim is not None:
            try:
                rel_sim = float(rel_sim)
                if rel_sim < 0.40:
                    parsed["confidence_capped"] = True
                    parsed["confidence_cap_reason"] = (
                        f"Historian: relevant_similarity_score={rel_sim:.2f} < 0.40 minimum. "
                        "Confidence capped at 0.50 — analogue is too weak to support higher certainty."
                    )
                    parsed["confidence"] = min(parsed.get("confidence", 0.5), 0.50)
                else:
                    cap = 0.50 + (rel_sim - 0.40) * 0.75
                    if parsed.get("confidence", 0.5) > cap:
                        parsed["confidence_capped"] = True
                        parsed["confidence_cap_reason"] = (
                            f"Historian: confidence scaled to {cap:.2f} based on "
                            f"relevant_similarity_score={rel_sim:.2f}."
                        )
                        parsed["confidence"] = round(cap, 3)
            except (TypeError, ValueError):
                pass
    if profile_name == "Risk Manager":
        tail_weight = parsed.get("tail_weight", "").lower()
        if tail_weight == "fat":
            cap = 0.70
            if parsed.get("confidence", 0.5) > cap:
                parsed["confidence_capped"] = True
                parsed["confidence_cap_reason"] = (
                    f"Risk Manager: fat tail domain — confidence capped at {cap} "
                    "(extremistan distributions preclude high directional certainty)."
                )
                parsed["confidence"] = cap
    return parsed


# ─────────────────────────────────────────────────────────────
# DB write (SQLite)
# ─────────────────────────────────────────────────────────────

def _write_assessment(conn: sqlite3.Connection, session_id: str,
                      profile_name: str, question: str, domain: str,
                      context_summary: Optional[str],
                      parsed: Optional[dict],
                      full_reasoning: Optional[str],
                      error: Optional[str] = None) -> str:
    """Write a profile assessment to acp_assessments. Returns assessment_id."""
    assessment_id = str(uuid.uuid4())
    parsed = parsed or {}

    profile_extra_data = None
    if parsed:
        extra = {k: v for k, v in parsed.items() if k not in _BASE_FIELDS}
        if extra:
            profile_extra_data = json.dumps(extra)

    conn.execute("""
        INSERT INTO acp_assessments (
            id, session_id, profile_name, question, domain, context_summary,
            prediction, confidence, reasoning_summary, full_reasoning,
            key_assumptions, falsification_conditions,
            analogue_reference, overall_similarity_score, relevant_similarity_score,
            similarity_dimensions_matched, similarity_dimensions_not_matched,
            relevance_rationale,
            constraints_applied, confidence_capped, confidence_cap_reason,
            profile_extra_data, error
        ) VALUES (
            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
        )
    """, (
        assessment_id, session_id, profile_name, question, domain, context_summary,
        parsed.get("prediction"),
        parsed.get("confidence"),
        parsed.get("reasoning_summary"),
        full_reasoning,
        json.dumps(parsed.get("key_assumptions", [])) if parsed else None,
        json.dumps(parsed.get("falsification_conditions", [])) if parsed else None,
        parsed.get("analogue_reference"),
        parsed.get("overall_similarity_score"),
        parsed.get("relevant_similarity_score"),
        json.dumps(parsed.get("similarity_dimensions_matched")) if parsed.get("similarity_dimensions_matched") else None,
        json.dumps(parsed.get("similarity_dimensions_not_matched")) if parsed.get("similarity_dimensions_not_matched") else None,
        parsed.get("relevance_rationale"),
        json.dumps(parsed.get("constraints_applied", [])) if parsed else None,
        1 if parsed.get("confidence_capped") else 0,
        parsed.get("confidence_cap_reason"),
        profile_extra_data,
        error,
    ))
    conn.commit()
    return assessment_id


# ─────────────────────────────────────────────────────────────
# Single-profile runner (synchronous, called via asyncio.to_thread)
# ─────────────────────────────────────────────────────────────

def run_profile(conn: sqlite3.Connection, profile: dict, question: str,
                domain: str, context: Optional[str],
                session_id: str, context_summary: Optional[str]) -> dict:
    """
    Run one profile against a prediction question. Synchronous — designed to be
    called via asyncio.to_thread() for parallel execution.

    Never raises — returns error dict on failure so other profiles can proceed.
    """
    profile_name = profile["name"]
    try:
        system_prompt = _build_system_prompt(profile)
        user_message  = _build_user_message(question, domain, context)

        raw = _call_llm(system_prompt, user_message)
        parsed = _extract_json(raw)

        parsed["confidence"] = max(0.01, min(0.99, float(parsed.get("confidence", 0.5))))
        parsed = _apply_constraints(profile_name, parsed)

        assessment_id = _write_assessment(
            conn, session_id, profile_name, question, domain,
            context_summary, parsed, raw,  # raw = full_reasoning (V2 Level 3)
        )

        print(f"[SWARM] {profile_name}: conf={parsed['confidence']:.2f} "
              f"capped={parsed.get('confidence_capped', False)}", flush=True)

        profile_extra_data = {k: v for k, v in parsed.items() if k not in _BASE_FIELDS}

        return {
            "assessment_id": assessment_id,
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
        print(f"[SWARM] {profile_name} FAILED: {err_str}", flush=True)
        assessment_id = None
        try:
            assessment_id = _write_assessment(
                conn, session_id, profile_name, question, domain,
                context_summary, None, None, err_str,
            )
        except Exception as write_err:
            print(f"[SWARM] {profile_name} error record write failed: {write_err}", flush=True)
        return {
            "assessment_id": assessment_id,
            "profile_name": profile_name,
            "prediction": None,
            "confidence": None,
            "error": err_str,
        }


# ─────────────────────────────────────────────────────────────
# Parallel dispatch (V2: async, runs all profiles concurrently)
# ─────────────────────────────────────────────────────────────

async def run_all_profiles(conn: sqlite3.Connection, profiles: list,
                           question: str, domain: str,
                           context: Optional[str], session_id: str) -> list:
    """
    Run all profiles in parallel via asyncio.to_thread().
    Returns list of assessment dicts (one per profile, including errors).

    V2: configurable committee — pass only the subset of profiles to run.
    """
    context_summary = context[:200] if context else None

    tasks = [
        asyncio.to_thread(
            run_profile, conn, profile, question, domain,
            context, session_id, context_summary
        )
        for profile in profiles
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Convert any unexpected exceptions into error dicts
    assessments = []
    for profile, result in zip(profiles, results):
        if isinstance(result, Exception):
            assessments.append({
                "assessment_id": None,
                "profile_name": profile["name"],
                "prediction": None,
                "confidence": None,
                "error": str(result),
            })
        else:
            assessments.append(result)

    return assessments
