-- SWARMFISH — Schema
-- Sprint 1: ACP (Analytical Cognitive Profiles) tables
-- Sprint 3+: Simulation tables (graph_nodes, graph_edges, agent_memories, audit_log) added later
--
-- pgvector extension required — provided by pgvector/pgvector:pg16 image.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- Application user (non-superuser, no DELETE on audit tables)
-- ============================================================

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'swarmfish_app') THEN
    CREATE ROLE swarmfish_app WITH LOGIN PASSWORD 'swarmfish_app_dev_password';
  END IF;
END$$;

GRANT CONNECT ON DATABASE swarmfish TO swarmfish_app;
GRANT USAGE ON SCHEMA public TO swarmfish_app;


-- ============================================================
-- ACP: Analytical Cognitive Profiles
-- ============================================================

CREATE TABLE IF NOT EXISTS acp_profiles (
    id            SERIAL PRIMARY KEY,
    name          TEXT UNIQUE NOT NULL,       -- "Base Rate Analyst", "Contrarian", "Historian"

    -- Identity layer (stable)
    analytical_method         TEXT NOT NULL,
    epistemological_stance    TEXT NOT NULL,
    information_seeking_behavior TEXT NOT NULL,
    search_strategy           JSONB NOT NULL DEFAULT '{}',
    risk_orientation          TEXT NOT NULL,
    domain_affinities         JSONB NOT NULL DEFAULT '[]',
    known_limitations         TEXT NOT NULL,

    -- Cognitive style layer (semi-stable)
    attention_pattern         TEXT NOT NULL,
    update_sensitivity        FLOAT NOT NULL DEFAULT 0.5,  -- 0.0=anchored, 1.0=responsive
    disagreement_style        TEXT NOT NULL,

    -- Profile-specific mechanical constraints (null if not applicable)
    -- See design note Step 2.5: only profiles that always produce an answer need these.
    attribution_constraints   JSONB,

    -- Interaction layer (learned, starts empty)
    confidence_calibration    JSONB NOT NULL DEFAULT '{"default": 0.0}',
    consensus_weight          JSONB NOT NULL DEFAULT '{"default": 1.0}',
    agreement_patterns        JSONB NOT NULL DEFAULT '{}',
    complementary_agents      JSONB NOT NULL DEFAULT '[]',

    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

GRANT SELECT, INSERT, UPDATE ON acp_profiles TO swarmfish_app;
GRANT USAGE, SELECT ON SEQUENCE acp_profiles_id_seq TO swarmfish_app;


-- ============================================================
-- ACP: Prediction log
-- ============================================================

CREATE TABLE IF NOT EXISTS acp_predictions (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_name  TEXT NOT NULL REFERENCES acp_profiles(name),

    question      TEXT NOT NULL,
    domain        TEXT NOT NULL DEFAULT 'general',
    -- Optional operator-supplied context (news, data, prior analysis).
    -- Not stored in full — summary only to keep rows lean.
    context_summary TEXT,

    -- The prediction
    prediction    TEXT NOT NULL,              -- "72% probability oil > $90 in 3 weeks"
    confidence    FLOAT NOT NULL              -- 0.0–1.0
                  CHECK (confidence >= 0 AND confidence <= 1),
    reasoning_summary TEXT NOT NULL,
    key_assumptions   JSONB NOT NULL DEFAULT '[]',

    -- Falsification conditions: list of {condition: str, impact: str, impact_magnitude: float}
    -- Compiled into the monitoring checklist by the aggregator.
    falsification_conditions JSONB NOT NULL DEFAULT '[]',

    -- Historian-specific fields (null for other profiles)
    -- Dual similarity scoring per Eitan's review: overall vs decision-relevant.
    analogue_reference        TEXT,           -- "1987 Tanker War", "2019 Strait tensions"
    overall_similarity_score  FLOAT,          -- informational: how similar on all dimensions
    relevant_similarity_score FLOAT,          -- load-bearing: how similar on decision-relevant dims
    similarity_dimensions_matched    JSONB,   -- which dimensions matched
    similarity_dimensions_not_matched JSONB,  -- which dimensions didn't match
    relevance_rationale       TEXT,           -- why certain dims are decision-relevant

    -- Constraint metadata
    constraints_applied       JSONB,          -- which constraints fired
    confidence_capped         BOOLEAN DEFAULT FALSE,
    confidence_cap_reason     TEXT,

    -- Scored flag — set when outcome is recorded
    scored                    BOOLEAN DEFAULT FALSE,

    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_predictions_profile ON acp_predictions(profile_name);
CREATE INDEX IF NOT EXISTS idx_predictions_domain ON acp_predictions(domain);
CREATE INDEX IF NOT EXISTS idx_predictions_scored ON acp_predictions(scored);
CREATE INDEX IF NOT EXISTS idx_predictions_created ON acp_predictions(created_at DESC);

GRANT SELECT, INSERT, UPDATE ON acp_predictions TO swarmfish_app;


-- ============================================================
-- ACP: Outcome log
-- ============================================================

CREATE TABLE IF NOT EXISTS acp_outcomes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prediction_id   UUID NOT NULL REFERENCES acp_predictions(id),

    outcome         TEXT NOT NULL,            -- Description of what actually happened
    was_correct     BOOLEAN NOT NULL,
    brier_score     FLOAT NOT NULL,           -- (confidence - correct)^2

    conditions_that_held   JSONB DEFAULT '[]',
    conditions_that_failed JSONB DEFAULT '[]',
    post_mortem_note       TEXT,

    scored_at       TIMESTAMPTZ DEFAULT NOW()
);

GRANT SELECT, INSERT ON acp_outcomes TO swarmfish_app;


-- ============================================================
-- ACP: Calibration history (rolling window — last 50 per profile/domain)
-- ============================================================

CREATE TABLE IF NOT EXISTS acp_calibration (
    id            BIGSERIAL PRIMARY KEY,
    profile_name  TEXT NOT NULL REFERENCES acp_profiles(name),
    domain        TEXT NOT NULL,

    brier_score   FLOAT NOT NULL,
    confidence    FLOAT NOT NULL,
    was_correct   BOOLEAN NOT NULL,

    -- Regime context: captures what market/event conditions looked like at prediction time.
    -- Used by regime change detector to flag when current conditions are out-of-distribution.
    regime_context JSONB DEFAULT '{}',

    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_calibration_profile_domain ON acp_calibration(profile_name, domain);
CREATE INDEX IF NOT EXISTS idx_calibration_created ON acp_calibration(created_at DESC);

GRANT SELECT, INSERT ON acp_calibration TO swarmfish_app;
GRANT USAGE, SELECT ON SEQUENCE acp_calibration_id_seq TO swarmfish_app;


-- ============================================================
-- ACP: Prediction sessions (groups individual predictions into a forecast round)
-- ============================================================

CREATE TABLE IF NOT EXISTS acp_sessions (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question      TEXT NOT NULL,
    domain        TEXT NOT NULL DEFAULT 'general',
    context_summary TEXT,
    profiles_used JSONB NOT NULL DEFAULT '[]',

    -- Aggregated output
    consensus_confidence      FLOAT,
    consensus_range_low       FLOAT,
    consensus_range_high      FLOAT,
    meta_confidence           TEXT,   -- HIGH / MEDIUM / LOW
    disagreement_level        FLOAT,
    operator_brief            TEXT,   -- Full formatted brief

    -- Monitoring
    falsification_checklist   JSONB DEFAULT '[]',  -- compiled from all profiles' conditions
    monitoring_active         BOOLEAN DEFAULT TRUE,

    created_at    TIMESTAMPTZ DEFAULT NOW(),
    closed_at     TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS acp_session_predictions (
    session_id      UUID NOT NULL REFERENCES acp_sessions(id),
    prediction_id   UUID NOT NULL REFERENCES acp_predictions(id),
    PRIMARY KEY (session_id, prediction_id)
);

GRANT SELECT, INSERT, UPDATE ON acp_sessions TO swarmfish_app;
GRANT SELECT, INSERT ON acp_session_predictions TO swarmfish_app;


-- ============================================================
-- SWARMFISH Phase 3+: Simulation infrastructure (stubs, not yet active)
-- Uncomment when Counter-Patriots social simulation use case is live.
-- ============================================================

-- CREATE TABLE IF NOT EXISTS projects ( ... );
-- CREATE TABLE IF NOT EXISTS graph_nodes ( ... embedding vector(1536) ... );
-- CREATE TABLE IF NOT EXISTS graph_edges ( ... );
-- CREATE TABLE IF NOT EXISTS agent_memories ( ... embedding vector(1536) ... );
-- CREATE TABLE IF NOT EXISTS simulation_traces ( ... );
--
-- Append-only audit log (REVOKE UPDATE, DELETE on this table):
-- CREATE TABLE IF NOT EXISTS audit_log ( ... );


-- ============================================================
-- Triggers: update acp_profiles.updated_at on change
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER acp_profiles_updated_at
    BEFORE UPDATE ON acp_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
