-- Migration 001: Allow error predictions in acp_predictions
--
-- The Historian profile has more required output fields than Base Rate Analyst
-- and Contrarian. With a reasoning model (thinking tokens) and LLM_MAX_TOKENS=2048,
-- the Historian response can be truncated before the JSON is complete, causing a
-- parse failure. The error currently produces no DB row, so GET /acp/session/<id>
-- returns only 2 predictions for a 3-profile session with no indication of failure.
--
-- This migration:
--   1. Makes prediction, confidence, reasoning_summary, key_assumptions, and
--      falsification_conditions nullable so error rows can be written.
--   2. Drops and re-adds the confidence check constraint to allow NULL.
--   3. Adds an error TEXT column to record the failure reason.

BEGIN;

-- 1. Drop inline NOT NULL constraints on fields that must be NULL for error rows
ALTER TABLE acp_predictions
    ALTER COLUMN prediction           DROP NOT NULL,
    ALTER COLUMN confidence           DROP NOT NULL,
    ALTER COLUMN reasoning_summary    DROP NOT NULL,
    ALTER COLUMN key_assumptions      DROP NOT NULL,
    ALTER COLUMN falsification_conditions DROP NOT NULL;

-- 2. Drop and re-add confidence check to allow NULL while still bounding valid values
ALTER TABLE acp_predictions
    DROP CONSTRAINT IF EXISTS acp_predictions_confidence_check;

ALTER TABLE acp_predictions
    ADD CONSTRAINT acp_predictions_confidence_check
    CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1));

-- 3. Add error column
ALTER TABLE acp_predictions
    ADD COLUMN IF NOT EXISTS error TEXT;

COMMIT;
