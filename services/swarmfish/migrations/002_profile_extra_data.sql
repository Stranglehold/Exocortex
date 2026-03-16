-- Migration 002: Generic profile extra data column
--
-- New profiles (Reflexivity Modeler, Decomposer, Network Analyst, Sentiment Decoder,
-- Risk Manager) produce structured extra fields beyond the standard prediction schema.
-- Rather than adding dedicated columns per profile (which would bloat the table),
-- a single JSONB column holds all profile-specific structured output.
--
-- The Historian's dedicated columns (analogue_reference, etc.) remain for backward
-- compatibility; its extra fields are also written to profile_extra_data for
-- consistency.

BEGIN;

ALTER TABLE acp_predictions
    ADD COLUMN IF NOT EXISTS profile_extra_data JSONB;

COMMIT;
