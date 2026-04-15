-- 011_narrative_stability.sql
-- Adds narrative stability signal classification to retcon detection.
-- Spec: specs/NARRATIVE_STABILITY_SPEC_L3.md
-- Design note: specs/NARRATIVE_STABILITY_DESIGN_NOTE.md

BEGIN;

-- --------------------------------------------------------------------
-- claims: add modality field tagged at claim-extraction time.
-- Default 'unknown' keeps all 10k existing rows safe.
-- --------------------------------------------------------------------

ALTER TABLE claims
    ADD COLUMN IF NOT EXISTS modality text DEFAULT 'unknown';

-- Backfill any NULLs that somehow exist (defensive) before adding check
UPDATE claims SET modality = 'unknown' WHERE modality IS NULL;

-- Add check constraint separately so the ADD COLUMN doesn't fail on
-- concurrent writers mid-migration.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'claims_modality_check'
    ) THEN
        ALTER TABLE claims
            ADD CONSTRAINT claims_modality_check
            CHECK (modality IN ('fact', 'speculation', 'opinion', 'framing', 'unknown'));
    END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_claims_modality ON claims(modality);

-- --------------------------------------------------------------------
-- contradictions: add 5 new columns for signal classification.
-- All NULLable — historical rows predate the classifier and will be
-- backfilled by a dedicated script or left as 'uncategorized'.
-- --------------------------------------------------------------------

ALTER TABLE contradictions
    ADD COLUMN IF NOT EXISTS modality_a   text,
    ADD COLUMN IF NOT EXISTS modality_b   text,
    ADD COLUMN IF NOT EXISTS volatility   text,
    ADD COLUMN IF NOT EXISTS signal_class text,
    ADD COLUMN IF NOT EXISTS signal_score double precision;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'contradictions_signal_class_check'
    ) THEN
        ALTER TABLE contradictions
            ADD CONSTRAINT contradictions_signal_class_check
            CHECK (signal_class IS NULL OR signal_class IN (
                'reality_update', 'honest_correction', 'healthy_update',
                'silent_error', 'narrative_rewrite', 'editorial_drift',
                'uncategorized'
            ));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'contradictions_signal_score_check'
    ) THEN
        ALTER TABLE contradictions
            ADD CONSTRAINT contradictions_signal_score_check
            CHECK (signal_score IS NULL OR (signal_score >= 0.0 AND signal_score <= 1.0));
    END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_contradictions_signal_class ON contradictions(signal_class);
CREATE INDEX IF NOT EXISTS idx_contradictions_signal_score ON contradictions(signal_score);

COMMIT;
