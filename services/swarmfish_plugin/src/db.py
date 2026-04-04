"""
db.py — SQLite database for SWARMFISH V2 plugin

DB path: /a0/usr/swarmfish/swarmfish.db (override via SWARMFISH_DB_PATH env).

Schema design:
  acp_profiles      — 8 analytical profile definitions + learned calibration
  acp_sessions      — prediction sessions (V2: persistent, configurable committee)
  acp_assessments   — per-profile predictions (V2: full_reasoning for transparency)
  acp_outcomes      — analyst outcome feedback for Brier scoring
  acp_calibration   — computed calibration scores per profile+domain
"""

import json
import os
import sqlite3
from typing import Any, Optional

DB_PATH = os.environ.get("SWARMFISH_DB_PATH", "/a0/usr/swarmfish/swarmfish.db")

# ─────────────────────────────────────────────────────────────
# Connection
# ─────────────────────────────────────────────────────────────

def get_conn() -> sqlite3.Connection:
    """Open (or create) the SQLite DB. Returns dict-row connection."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=15000")  # 15s for concurrent writes from parallel profiles
    init_db(conn)
    return conn


# ─────────────────────────────────────────────────────────────
# Schema
# ─────────────────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS acp_profiles (
    id                           INTEGER PRIMARY KEY AUTOINCREMENT,
    name                         TEXT UNIQUE NOT NULL,
    analytical_method            TEXT NOT NULL,
    epistemological_stance       TEXT NOT NULL,
    information_seeking_behavior TEXT NOT NULL,
    search_strategy              TEXT NOT NULL DEFAULT '{}',
    risk_orientation             TEXT NOT NULL,
    domain_affinities            TEXT NOT NULL DEFAULT '[]',
    known_limitations            TEXT NOT NULL,
    attention_pattern            TEXT NOT NULL,
    update_sensitivity           REAL NOT NULL DEFAULT 0.5,
    disagreement_style           TEXT NOT NULL,
    attribution_constraints      TEXT,
    -- Learned calibration (updated by calibration.py after outcomes)
    confidence_calibration       TEXT NOT NULL DEFAULT '{"default": 0.0}',
    consensus_weight             TEXT NOT NULL DEFAULT '{"default": 1.0}',
    agreement_patterns           TEXT NOT NULL DEFAULT '{}',
    complementary_agents         TEXT NOT NULL DEFAULT '[]',
    created_at                   TEXT DEFAULT (datetime('now')),
    updated_at                   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS acp_sessions (
    id                      TEXT PRIMARY KEY,
    question                TEXT NOT NULL,
    domain                  TEXT NOT NULL DEFAULT 'general',
    context_summary         TEXT,
    -- V2: configurable committee — JSON list of profile names, null = all 8
    committee_config        TEXT,
    -- Consensus fields (written by aggregator.finalize_session)
    consensus_confidence    REAL,
    consensus_range_low     REAL,
    consensus_range_high    REAL,
    meta_confidence         TEXT,
    disagreement_level      REAL,
    operator_brief          TEXT,
    falsification_checklist TEXT,
    profiles_used           TEXT,
    -- V2: analyst intervention log — JSON list of {type, text, target?, date}
    analyst_inputs          TEXT,
    created_at              TEXT DEFAULT (datetime('now')),
    updated_at              TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS acp_assessments (
    id                              TEXT PRIMARY KEY,
    session_id                      TEXT REFERENCES acp_sessions(id),
    profile_name                    TEXT NOT NULL,
    question                        TEXT NOT NULL,
    domain                          TEXT NOT NULL DEFAULT 'general',
    context_summary                 TEXT,
    prediction                      TEXT,
    confidence                      REAL,
    reasoning_summary               TEXT,
    -- V2: full LLM response text for Level 3 transparency (show me your work)
    full_reasoning                  TEXT,
    key_assumptions                 TEXT,
    falsification_conditions        TEXT,
    -- Historian-specific fields (dedicated columns for calibration)
    analogue_reference              TEXT,
    overall_similarity_score        REAL,
    relevant_similarity_score       REAL,
    similarity_dimensions_matched   TEXT,
    similarity_dimensions_not_matched TEXT,
    relevance_rationale             TEXT,
    -- Constraint metadata
    constraints_applied             TEXT,
    confidence_capped               INTEGER NOT NULL DEFAULT 0,
    confidence_cap_reason           TEXT,
    -- All other profile-specific extra fields (Reflexivity, Decomposer, etc.)
    profile_extra_data              TEXT,
    error                           TEXT,
    created_at                      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS acp_outcomes (
    id            TEXT PRIMARY KEY,
    session_id    TEXT REFERENCES acp_sessions(id),
    outcome       REAL NOT NULL,
    outcome_date  TEXT,
    notes         TEXT,
    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS acp_calibration (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_name  TEXT NOT NULL,
    domain        TEXT NOT NULL DEFAULT 'general',
    brier_score   REAL NOT NULL,
    confidence    REAL NOT NULL,
    was_correct   INTEGER NOT NULL,
    session_id    TEXT,
    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_assessments_session   ON acp_assessments(session_id);
CREATE INDEX IF NOT EXISTS idx_calibration_profile   ON acp_calibration(profile_name, domain);
CREATE INDEX IF NOT EXISTS idx_sessions_created      ON acp_sessions(created_at DESC);
"""


def init_db(conn: sqlite3.Connection) -> None:
    """Create tables if they don't exist."""
    conn.executescript(_SCHEMA)
    conn.commit()


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def row_to_dict(row: sqlite3.Row) -> dict:
    """Convert sqlite3.Row to plain dict."""
    return dict(row) if row else {}


def rows_to_dicts(rows) -> list:
    return [dict(r) for r in rows]


def json_loads_safe(val: Any) -> Any:
    """Parse a JSON string or return the value unchanged if already decoded."""
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return val
    return val
