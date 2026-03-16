-- Migration 007: Add last_prediction_check cursor to hypothesis_registry.
-- Replaces the fixed 2-hour window in check_hypothesis_predictions() with a
-- per-hypothesis timestamp cursor. Each ingest pass advances the cursor,
-- so claims are never re-evaluated against the same prediction (no double-counting)
-- and claims are never missed due to a gap between passes.

ALTER TABLE hypothesis_registry
    ADD COLUMN IF NOT EXISTS last_prediction_check TIMESTAMPTZ;

-- Backfill: treat existing hypotheses as never checked (NULL = use created_at as floor).
-- No data update needed — NULL is handled in application logic.
