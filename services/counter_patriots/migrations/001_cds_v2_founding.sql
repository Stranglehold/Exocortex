-- migrations/001_cds_v2_founding.sql
-- CDS v2 Phase 1: Founding Infrastructure
--
-- Run against an existing counter_patriots deployment.
-- Idempotent: safe to re-run. All statements use IF NOT EXISTS / ON CONFLICT.
--
-- Run via install.sh --migrate, or manually:
--   docker exec -i cp_postgres psql -U cp_user -d counter_patriots \
--       < migrations/001_cds_v2_founding.sql
--
-- "The promotion snapshot schema must exist at founding. Claims promoted before
--  this schema exists can only be approximately remediated, not precisely
--  remediated. A sophisticated adversary times their source burn to contaminate
--  claims promoted during the window when snapshot data didn't exist. That gap
--  is the exploit." — CDS v2

BEGIN;

-- ── 1. Extend claims with trust lifecycle columns ─────────────────────────────
-- Existing claims are STAGED — they haven't been through the analyst review
-- + promotion workflow yet. The trust_level field drives the contamination
-- cascade in Phase 2.

ALTER TABLE claims
    ADD COLUMN IF NOT EXISTS trust_level VARCHAR(20) DEFAULT 'STAGED'
        CHECK (trust_level IN ('STAGED', 'PROMOTED', 'FALSIFIED', 'RETURNED_TO_STAGED')),
    ADD COLUMN IF NOT EXISTS staging_confidence FLOAT DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS cui_bono JSONB DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS emotional_salience_score FLOAT DEFAULT 0.0;

CREATE INDEX IF NOT EXISTS idx_claims_trust ON claims(trust_level);

-- ── 2. Promotion snapshots — FROZEN at moment of promotion ────────────────────
-- Never UPDATE this table. snapshot_frozen enforces intent.
-- The contamination cascade (Phase 2) reconstructs the actual decision,
-- not a current approximation of it.

CREATE TABLE IF NOT EXISTS promotion_snapshots (
    id SERIAL PRIMARY KEY,
    claim_id INT REFERENCES claims(id) ON DELETE RESTRICT,
    promoted_at TIMESTAMPTZ DEFAULT NOW(),
    promotion_confidence FLOAT NOT NULL,

    -- Weight distribution across corroborating sources at moment of decision.
    -- e.g. {"source_12": 0.60, "source_7": 0.25, "source_3": 0.15}
    source_weights JSONB NOT NULL,
    threshold_at_promotion FLOAT NOT NULL,
    promoting_evidence TEXT[],

    -- Predictions that should be true if claim is valid.
    -- Confirmed predictions survive compromise of a corroborating source.
    -- e.g. [{"prediction": "oil above $95 within 72hrs",
    --         "confirmed_by": "reuters_20260312",
    --         "confirmed_at": "2026-03-12T14:23:00Z",
    --         "independent_of_source": true}]
    falsification_predictions JSONB NOT NULL DEFAULT '[]',
    predictions_confirmed_independently INT DEFAULT 0,

    snapshot_frozen BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_promo_claim ON promotion_snapshots(claim_id);
CREATE INDEX IF NOT EXISTS idx_promo_at ON promotion_snapshots(promoted_at);

-- ── 3. Source network topology — required by contamination cascade ─────────────
-- Enables _verify_independence() in the contamination cascade.
-- DO NOT DESCOPE — see COGNITIVE_DEFENSE_SYSTEM_v2.md dependency graph.

CREATE TABLE IF NOT EXISTS source_network_edges (
    id SERIAL PRIMARY KEY,
    source_id INT REFERENCES sources(id) ON DELETE RESTRICT,
    connected_source_id INT REFERENCES sources(id) ON DELETE RESTRICT,
    relationship_type VARCHAR(64) CHECK (
        relationship_type IN ('amplifies', 'is_amplified_by', 'mutual_engagement', 'cluster_member')
    ),
    weight FLOAT DEFAULT 1.0 CHECK (weight BETWEEN 0.0 AND 1.0),
    first_observed TIMESTAMPTZ DEFAULT NOW(),
    last_confirmed TIMESTAMPTZ DEFAULT NOW(),
    observation_count INT DEFAULT 1,
    CONSTRAINT no_self_edge CHECK (source_id != connected_source_id)
);

CREATE INDEX IF NOT EXISTS idx_sne_source ON source_network_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_sne_connected ON source_network_edges(connected_source_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_sne_unique_pair
    ON source_network_edges(source_id, connected_source_id, relationship_type);

-- Seed cluster membership edges from existing source metadata.
-- Wire and mainstream clusters get bidirectional edges automatically.
-- Official and independent sources: edges must be observed, not assumed.
INSERT INTO source_network_edges (source_id, connected_source_id, relationship_type, weight)
SELECT a.id, b.id, 'cluster_member', 0.8
FROM sources a
CROSS JOIN sources b
WHERE a.id != b.id
  AND a.cluster = b.cluster
  AND a.cluster NOT IN ('official', 'independent')
ON CONFLICT (source_id, connected_source_id, relationship_type) DO NOTHING;

-- ── 4. Living adversary model ─────────────────────────────────────────────────
-- Tracks technique observation and abandonment.
-- adversary_abandoned = TRUE means they know the technique is detected.
-- This is signal: adapt before they adapt.

CREATE TABLE IF NOT EXISTS threat_model (
    id SERIAL PRIMARY KEY,
    technique_name VARCHAR(128) NOT NULL,
    technique_class VARCHAR(64) NOT NULL,
    first_observed TIMESTAMPTZ,
    last_observed TIMESTAMPTZ,
    observed_count INT DEFAULT 0,
    detected_by_system BOOLEAN DEFAULT FALSE,
    adversary_abandoned BOOLEAN DEFAULT FALSE,
    abandoned_at TIMESTAMPTZ,
    predicted_adaptation TEXT,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_threat_class ON threat_model(technique_class);
CREATE INDEX IF NOT EXISTS idx_threat_abandoned ON threat_model(adversary_abandoned, abandoned_at);

-- ── 5. Multi-hypothesis registry ──────────────────────────────────────────────
-- Multiple competing explanations per observation.
-- The survivor is the hypothesis whose predictions matched reality —
-- not the hypothesis the analyst preferred.
-- Implements Chamberlin's method of multiple working hypotheses.

CREATE TABLE IF NOT EXISTS hypothesis_registry (
    id SERIAL PRIMARY KEY,
    -- observation_id: opaque event reference. Will FK to observations table in Phase 2.
    observation_id INT NOT NULL,
    candidate_explanation TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    current_confidence FLOAT DEFAULT 0.0 CHECK (current_confidence BETWEEN 0.0 AND 1.0),
    status VARCHAR(32) DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'PROMOTED', 'FALSIFIED', 'SUSPENDED')),
    predictions_generated JSONB DEFAULT '[]',
    predictions_confirmed INT DEFAULT 0,
    predictions_falsified INT DEFAULT 0,
    falsified_at TIMESTAMPTZ,
    falsification_evidence TEXT
);

CREATE INDEX IF NOT EXISTS idx_hyp_observation ON hypothesis_registry(observation_id);
CREATE INDEX IF NOT EXISTS idx_hyp_status ON hypothesis_registry(status);

-- ── 6. Propagation dynamics ───────────────────────────────────────────────────
-- Escape velocity alert: when time_to_escape_velocity < operator_response_time,
-- correction is practically impossible. URGENT fires automatically at that point.

CREATE TABLE IF NOT EXISTS narrative_dynamics (
    id SERIAL PRIMARY KEY,
    narrative_id INT NOT NULL,
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    propagation_velocity FLOAT,       -- sources per hour
    acceleration FLOAT,               -- velocity change rate
    escape_velocity_estimate FLOAT,   -- threshold where correction impractical
    time_to_escape_velocity_hours FLOAT,
    half_life_hours FLOAT,            -- falsified claim decay rate
    alert_level VARCHAR(16) DEFAULT 'INFORMATIONAL'
        CHECK (alert_level IN ('INFORMATIONAL', 'WARNING', 'URGENT'))
);

CREATE INDEX IF NOT EXISTS idx_nd_narrative ON narrative_dynamics(narrative_id);
CREATE INDEX IF NOT EXISTS idx_nd_alert ON narrative_dynamics(alert_level);
CREATE INDEX IF NOT EXISTS idx_nd_computed ON narrative_dynamics(computed_at DESC);

-- ── 7. Audit log — append only, never updated, never deleted ─────────────────
-- autovacuum disabled: append-only table never accumulates dead rows.
-- Enforcement is two-layer:
--   DB level:   cds_app role has UPDATE and DELETE revoked (see role setup below)
--   Code level: audit.py exposes only insert functions — no update, no delete

CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    session_id UUID NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    actor VARCHAR(64) NOT NULL,
    action TEXT NOT NULL,
    data_accessed JSONB,
    trust_level VARCHAR(20),
    injection_flag BOOLEAN DEFAULT FALSE
) WITH (autovacuum_enabled = false);

CREATE INDEX IF NOT EXISTS idx_audit_session ON audit_log(session_id);
CREATE INDEX IF NOT EXISTS idx_audit_event ON audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC);

-- ── 8. Application role: cds_app ─────────────────────────────────────────────
-- cds_app is the non-superuser role used by the Flask application.
-- cp_user is the admin role used only for migrations and schema management.
-- Having a separate application role enables the REVOKE enforcement below.

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'cds_app') THEN
        CREATE ROLE cds_app LOGIN PASSWORD 'cds_app_dev_password';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE counter_patriots TO cds_app;
GRANT USAGE ON SCHEMA public TO cds_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO cds_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO cds_app;

-- Enforce append-only on audit_log at the database level.
-- cds_app can INSERT but not UPDATE or DELETE.
-- cp_user (superuser) bypasses this — migrations only, never application logic.
REVOKE UPDATE ON audit_log FROM cds_app;
REVOKE DELETE ON audit_log FROM cds_app;

COMMIT;
