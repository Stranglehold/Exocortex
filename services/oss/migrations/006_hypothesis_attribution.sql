-- Migration 006: Hypothesis attribution for SWARMFISH-generated hypotheses.
-- Adds columns to track which SWARMFISH session produced a hypothesis,
-- which profiles drove it, whether it was auto-generated, and a human label.

ALTER TABLE hypothesis_registry
    ADD COLUMN IF NOT EXISTS swarmfish_session_id TEXT,
    ADD COLUMN IF NOT EXISTS source_profiles JSONB DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS auto_generated BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS observation_label TEXT;

-- Grant access to oss_app (which runs the application)
GRANT SELECT, INSERT, UPDATE ON hypothesis_registry TO oss_app;
