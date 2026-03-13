-- Migration 002 — Phase 3: Propagation Dynamics + Operator State
-- Adds topic_tag to narrative_dynamics for queryable history.
-- Adds operator_state table for staged threshold elevation mechanism.
-- 2026-03-12

-- narrative_dynamics.topic_tag
-- narrative_id remains as stable hash of topic_tag (Phase 3).
-- Full FK to narratives table: Phase 4.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'narrative_dynamics' AND column_name = 'topic_tag'
    ) THEN
        ALTER TABLE narrative_dynamics ADD COLUMN topic_tag TEXT NOT NULL DEFAULT '';
        CREATE INDEX IF NOT EXISTS idx_nd_topic ON narrative_dynamics (topic_tag, computed_at DESC);
        RAISE NOTICE 'narrative_dynamics.topic_tag added';
    ELSE
        RAISE NOTICE 'narrative_dynamics.topic_tag already exists — skip';
    END IF;
END $$;

-- operator_state table
-- Tracks current operator alert level for mechanical threshold elevation.
-- Behavioral signal integration: Phase 4 (requires operator interface plumbing).
CREATE TABLE IF NOT EXISTS operator_state (
    id                   SERIAL PRIMARY KEY,
    set_at               TIMESTAMPTZ DEFAULT NOW(),
    alert_level          VARCHAR(16) NOT NULL DEFAULT 'NOMINAL',
    -- NOMINAL | DEGRADED | IMPAIRED
    threshold_multiplier FLOAT NOT NULL DEFAULT 1.0,
    -- Applied to staging confidence threshold when elevated.
    -- DEGRADED: 1.25x, IMPAIRED: 1.50x
    reason               TEXT,
    set_by               VARCHAR(64) NOT NULL DEFAULT 'analyst',
    override_active      BOOLEAN DEFAULT FALSE
    -- True when analyst manually overrides auto-detection.
    -- Cleared when alert_level returns to NOMINAL.
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints
        WHERE constraint_name = 'operator_state_alert_level_check'
    ) THEN
        ALTER TABLE operator_state
            ADD CONSTRAINT operator_state_alert_level_check
            CHECK (alert_level IN ('NOMINAL', 'DEGRADED', 'IMPAIRED'));
        RAISE NOTICE 'operator_state constraint added';
    ELSE
        RAISE NOTICE 'operator_state constraint already exists — skip';
    END IF;
END $$;

-- Seed initial NOMINAL state if table is empty
INSERT INTO operator_state (alert_level, threshold_multiplier, reason, set_by)
SELECT 'NOMINAL', 1.0, 'system_init', 'system'
WHERE NOT EXISTS (SELECT 1 FROM operator_state);

RAISE NOTICE 'Migration 002 complete';
