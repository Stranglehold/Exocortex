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

You will be given a prediction question and optional context (data, news, analysis).
Apply your specific analytical method to produce a structured prediction.

You MUST respond with valid JSON in exactly this format — no prose outside the JSON:

{{
  "prediction": "<one sentence describing the predicted outcome>",
  "confidence": <float 0.0-1.0>,
  "reasoning_summary": "<2-4 sentences explaining your reasoning, citing your analytical method>",
  "key_assumptions": ["<assumption 1>", "<assumption 2>", ...],
  "falsification_conditions": [
    {{"condition": "<what would make this prediction wrong>", "impact": "<how this changes the prediction>", "impact_magnitude": <float 0.0-1.0>}},
    ...
  ]{historian_extra_fields}
}}

Requirements:
- confidence must be between 0.01 and 0.99
- include 2-4 key_assumptions
- include 3-5 falsification_conditions with specific, observable triggers
- reasoning_summary must reference your specific analytical method, not generic analysis{historian_extra_instructions}"""

HISTORIAN_EXTRA_FIELDS = """,
  "analogue_reference": "<name of the closest historical analogue>",
  "overall_similarity_score": <float 0.0-1.0>,
  "relevant_similarity_score": <float 0.0-1.0>,
  "similarity_dimensions_matched": ["<dimension 1>", "<dimension 2>", ...],
  "similarity_dimensions_not_matched": ["<dimension 1>", "<dimension 2>", ...],
  "relevance_rationale": "<why certain similarity dimensions are decision-relevant for this prediction>"
"""

HISTORIAN_EXTRA_INSTRUCTIONS = """
- You MUST provide both overall_similarity_score and relevant_similarity_score
- relevant_similarity_score measures similarity on dimensions that actually drive the predicted outcome, not overall structural similarity
- A high overall_similarity_score with a low relevant_similarity_score means the analogue is structurally similar but not useful for this specific prediction
- Be honest about dissimilarities — they matter as much as similarities"""


def build_system_prompt(profile: dict) -> str:
    is_historian = profile["name"] == "Historian"
    return SYSTEM_PROMPT_TEMPLATE.format(
        name=profile["name"],
        analytical_method=profile["analytical_method"],
        epistemological_stance=profile["epistemological_stance"],
        information_seeking_behavior=profile["information_seeking_behavior"],
        known_limitations=profile["known_limitations"],
        attention_pattern=profile["attention_pattern"],
        historian_extra_fields=HISTORIAN_EXTRA_FIELDS if is_historian else "",
        historian_extra_instructions=HISTORIAN_EXTRA_INSTRUCTIONS if is_historian else "",
    )


def build_user_message(question: str, domain: str, context: Optional[str]) -> str:
    parts = [
        f"PREDICTION QUESTION: {question}",
        f"DOMAIN: {domain}",
    ]
    if context:
        parts.append(f"\nCONTEXT (operator-supplied data and analysis):\n{context}")
    parts.append("\nApply your analytical method and produce your structured prediction.")
    return "\n".join(parts)


# ============================================================
# LLM call + JSON extraction
# ============================================================

_JIT_ERRORS = ("model unloaded", "operation canceled", "failed to load model")

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


def extract_json(raw: str) -> dict:
    """
    Extract JSON from LLM response. Handles:
    - reasoning-model thinking tokens (<think>...</think>)
    - markdown code fences (```json ... ```)
    - bare JSON or JSON embedded in prose
    """
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

    # Try extracting JSON block from response
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract valid JSON from LLM response: {raw[:300]}")


# ============================================================
# DB write
# ============================================================

def write_prediction(db_conn, session_id: Optional[str],
                     profile_name: str, question: str, domain: str,
                     context_summary: Optional[str], parsed: dict) -> str:
    """Write a parsed, constraint-applied prediction to acp_predictions. Returns prediction_id."""
    pred_id = str(uuid.uuid4())
    cursor = db_conn.cursor()

    cursor.execute("""
        INSERT INTO acp_predictions (
            id, profile_name, question, domain, context_summary,
            prediction, confidence, reasoning_summary,
            key_assumptions, falsification_conditions,
            analogue_reference, overall_similarity_score, relevant_similarity_score,
            similarity_dimensions_matched, similarity_dimensions_not_matched,
            relevance_rationale,
            constraints_applied, confidence_capped, confidence_cap_reason
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s, %s,
            %s, %s,
            %s,
            %s, %s, %s
        )
    """, (
        pred_id, profile_name, question, domain, context_summary,
        parsed.get("prediction", ""),
        parsed.get("confidence", 0.5),
        parsed.get("reasoning_summary", ""),
        json.dumps(parsed.get("key_assumptions", [])),
        json.dumps(parsed.get("falsification_conditions", [])),
        parsed.get("analogue_reference"),
        parsed.get("overall_similarity_score"),
        parsed.get("relevant_similarity_score"),
        json.dumps(parsed.get("similarity_dimensions_matched")) if parsed.get("similarity_dimensions_matched") else None,
        json.dumps(parsed.get("similarity_dimensions_not_matched")) if parsed.get("similarity_dimensions_not_matched") else None,
        parsed.get("relevance_rationale"),
        json.dumps(parsed.get("constraints_applied", [])),
        bool(parsed.get("confidence_capped", False)),
        parsed.get("confidence_cap_reason"),
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
    try:
        system_prompt = build_system_prompt(profile)
        user_message  = build_user_message(question, domain, context)

        raw = call_llm(system_prompt, user_message)
        parsed = extract_json(raw)

        # Clamp confidence to valid range before constraint application
        parsed["confidence"] = max(0.01, min(0.99, float(parsed.get("confidence", 0.5))))

        # Apply mechanical constraints (Historian similarity scoring, etc.)
        parsed = apply_constraints(profile_name, parsed)

        # Write to DB
        pred_id = write_prediction(
            db_conn, session_id, profile_name, question, domain,
            context_summary or (context[:200] if context else None), parsed
        )

        print(f"[ACP] {profile_name}: confidence={parsed['confidence']:.2f} "
              f"capped={parsed.get('confidence_capped', False)}", flush=True)

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
            "constraints_applied": parsed.get("constraints_applied", []),
            "confidence_capped": parsed.get("confidence_capped", False),
            "confidence_cap_reason": parsed.get("confidence_cap_reason"),
            "error": None,
        }

    except Exception as e:
        print(f"[ACP] {profile_name} FAILED: {e}", flush=True)
        return {
            "prediction_id": None,
            "profile_name": profile_name,
            "prediction": None,
            "confidence": None,
            "error": str(e),
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
