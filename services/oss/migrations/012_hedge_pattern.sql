-- 012_hedge_pattern.sql
-- Adds hedge pattern detection fields to claims plus the source_topic_signals table.
-- Spec: specs/HEDGE_PATTERN_SPEC_L3.md
-- Design note: specs/HEDGE_PATTERN_DESIGN_NOTE.md

BEGIN;

-- --------------------------------------------------------------------
-- claims: three new fields tagged at extraction time.
-- Default 'unknown' keeps existing rows safe.
-- --------------------------------------------------------------------

ALTER TABLE claims
    ADD COLUMN IF NOT EXISTS certainty       text DEFAULT 'unknown',
    ADD COLUMN IF NOT EXISTS attribution     text DEFAULT 'unknown',
    ADD COLUMN IF NOT EXISTS quoted_directly text DEFAULT 'unknown';

-- Defensive: any NULL → 'unknown' before constraint
UPDATE claims SET certainty       = 'unknown' WHERE certainty       IS NULL;
UPDATE claims SET attribution     = 'unknown' WHERE attribution     IS NULL;
UPDATE claims SET quoted_directly = 'unknown' WHERE quoted_directly IS NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'claims_certainty_check'
    ) THEN
        ALTER TABLE claims
            ADD CONSTRAINT claims_certainty_check
            CHECK (certainty IN ('committed', 'hedged', 'unknown'));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'claims_attribution_check'
    ) THEN
        ALTER TABLE claims
            ADD CONSTRAINT claims_attribution_check
            CHECK (attribution IN ('named', 'vague', 'absent', 'unknown'));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'claims_quoted_directly_check'
    ) THEN
        ALTER TABLE claims
            ADD CONSTRAINT claims_quoted_directly_check
            CHECK (quoted_directly IN ('true', 'false', 'n_a', 'unknown'));
    END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_claims_certainty       ON claims(certainty);
CREATE INDEX IF NOT EXISTS idx_claims_attribution     ON claims(attribution);
CREATE INDEX IF NOT EXISTS idx_claims_quoted_directly ON claims(quoted_directly);

-- Partial index on the insidious combination — speeds up aggregation query
CREATE INDEX IF NOT EXISTS idx_claims_hedge_pattern
    ON claims(source_id, certainty, attribution, quoted_directly)
    WHERE certainty = 'hedged' AND attribution = 'vague';

-- --------------------------------------------------------------------
-- contradictions: raw_signal_score captures pre-certainty-modifier value
-- --------------------------------------------------------------------

ALTER TABLE contradictions
    ADD COLUMN IF NOT EXISTS raw_signal_score double precision;

-- --------------------------------------------------------------------
-- source_topic_signals: per-(source, topic) aggregation results
-- --------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS source_topic_signals (
    id                  serial PRIMARY KEY,
    source_id           int NOT NULL REFERENCES sources(id),
    topic               text NOT NULL,
    source_type         text NOT NULL,
    claim_count         int NOT NULL,
    insidious_count     int NOT NULL,
    topic_rate          double precision NOT NULL,
    baseline_rate       double precision NOT NULL,
    deviation           double precision NOT NULL,
    signal_class        text,
    computed_at         timestamptz NOT NULL DEFAULT NOW(),
    window_days         int NOT NULL DEFAULT 7
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'source_topic_signals_signal_class_check'
    ) THEN
        ALTER TABLE source_topic_signals
            ADD CONSTRAINT source_topic_signals_signal_class_check
            CHECK (signal_class IS NULL OR signal_class IN (
                'narrative_campaign', 'unverifiable_stream', 'unclassified'
            ));
    END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_sts_source       ON source_topic_signals(source_id);
CREATE INDEX IF NOT EXISTS idx_sts_signal_class ON source_topic_signals(signal_class);
CREATE INDEX IF NOT EXISTS idx_sts_computed_at  ON source_topic_signals(computed_at);
CREATE UNIQUE INDEX IF NOT EXISTS uq_sts_current
    ON source_topic_signals(source_id, topic, window_days);

COMMIT;
