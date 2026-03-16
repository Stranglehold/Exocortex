"""
config.py — SWARMFISH / ACP configuration

LLM endpoint shared with Agent Zero: same LM Studio instance, same loaded model.
No JIT reload triggered when both systems use the same model name.
Update SWARMFISH_LLM_MODEL to match whatever model you have loaded in LM Studio.
"""

import os

# --- LLM ---------------------------------------------------------------
# Points at the same LM Studio endpoint as Agent Zero.
# OpenAI-compatible API; api_key is ignored by LM Studio but required by the client.
LLM_BASE_URL = os.getenv("SWARMFISH_LLM_URL", "http://host.docker.internal:1234/v1")
LLM_MODEL    = os.getenv("SWARMFISH_LLM_MODEL",
                          "qwen3.5-27b-claude-4.6-opus-reasoning-distilled@q4_k_m")
LLM_API_KEY  = os.getenv("SWARMFISH_LLM_API_KEY", "lm-studio")

# --- Database -----------------------------------------------------------
DB_URL = os.getenv(
    "SWARMFISH_DB_URL",
    "postgresql://swarmfish_app:swarmfish_app_dev_password@localhost:5435/swarmfish"
)

# --- Redis --------------------------------------------------------------
REDIS_URL = os.getenv("SWARMFISH_REDIS_URL", "redis://localhost:6380/0")

# --- Auth ---------------------------------------------------------------
ANALYST_TOKEN = os.getenv("SWARMFISH_ANALYST_TOKEN", "dev_analyst_token")

# --- LLM generation parameters -----------------------------------------
LLM_TEMPERATURE    = float(os.getenv("SWARMFISH_LLM_TEMPERATURE", "0.3"))
LLM_MAX_TOKENS     = int(os.getenv("SWARMFISH_LLM_MAX_TOKENS", "2048"))
LLM_REQUEST_TIMEOUT = int(os.getenv("SWARMFISH_LLM_TIMEOUT", "120"))

# --- OSS bridge --------------------------------------------------------
# OSS runs on port 7731. From inside the swarmfish container (separate
# compose network), reach it via host.docker.internal.
OSS_BASE_URL      = os.getenv("OSS_BASE_URL", "http://host.docker.internal:7731")
OSS_ANALYST_TOKEN = os.getenv("OSS_ANALYST_TOKEN", "dev_analyst_token")

# --- Calibration thresholds --------------------------------------------
# Minimum predictions before calibration data influences weights.
MIN_CALIBRATION_PREDICTIONS = int(os.getenv("MIN_CALIBRATION_PREDICTIONS", "10"))
# Rolling window: last N predictions used for calibration.
CALIBRATION_WINDOW = int(os.getenv("CALIBRATION_WINDOW", "50"))
