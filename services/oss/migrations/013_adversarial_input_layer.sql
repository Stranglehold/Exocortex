-- 013_adversarial_input_layer.sql
-- Adds the adversarial input layer: scrutiny verdicts, escalation requests,
-- and claim-level surprise_score + scrutiny_status.
-- Spec: specs/ADVERSARIAL_INPUT_LAYER_SPEC_L3.md
-- Design note: specs/ADVERSARIAL_INPUT_LAYER_DESIGN_NOTE.md

BEGIN;

-- --------------------------------------------------------------------
-- claims: surprise_score + scrutiny_status fields
-- --------------------------------------------------------------------

ALTER TABLE claims
    ADD COLUMN IF NOT EXISTS surprise_score  double precision,
    ADD COLUMN IF NOT EXISTS scrutiny_status text DEFAULT 'pending';

UPDATE claims SET scrutiny_status = 'pending' WHERE scrutiny_status IS NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'claims_scrutiny_status_check'
    ) THEN
        ALTER TABLE claims
            ADD CONSTRAINT claims_scrutiny_status_check
            CHECK (scrutiny_status IN ('pending', 'clean', 'flagged', 'escalated'));
    END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_claims_scrutiny_status ON claims(scrutiny_status);
CREATE INDEX IF NOT EXISTS idx_claims_surprise_score  ON claims(surprise_score);

-- --------------------------------------------------------------------
-- scrutiny_verdicts: append-only log of per-claim scrutiny checks
-- --------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS scrutiny_verdicts (
    id              serial PRIMARY KEY,
    claim_id        int NOT NULL REFERENCES claims(id),
    check_name      text NOT NULL,
    timestamp       timestamptz NOT NULL DEFAULT NOW(),
    result          text NOT NULL,
    confidence      double precision,
    numeric_value   double precision,
    reasoning       text,
    escalated       boolean NOT NULL DEFAULT false,
    metadata        jsonb,
    supersedes      int REFERENCES scrutiny_verdicts(id)
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'scrutiny_verdicts_result_check'
    ) THEN
        ALTER TABLE scrutiny_verdicts
            ADD CONSTRAINT scrutiny_verdicts_result_check
            CHECK (result IN ('pass', 'fail', 'warn'));
    END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_sv_claim     ON scrutiny_verdicts(claim_id);
CREATE INDEX IF NOT EXISTS idx_sv_check     ON scrutiny_verdicts(check_name);
CREATE INDEX IF NOT EXISTS idx_sv_escalated ON scrutiny_verdicts(escalated) WHERE escalated = true;
CREATE INDEX IF NOT EXISTS idx_sv_timestamp ON scrutiny_verdicts(timestamp);

-- --------------------------------------------------------------------
-- escalation_requests: OSS→SWARMFISH escalation tracking
-- --------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS escalation_requests (
    id                      serial PRIMARY KEY,
    claim_id                int NOT NULL REFERENCES claims(id),
    triggered_by            text[] NOT NULL,
    topic                   text,
    request_timestamp       timestamptz NOT NULL DEFAULT NOW(),
    swarmfish_session_id    uuid,
    committee_decision      text,
    committee_decision_at   timestamptz
);

CREATE INDEX IF NOT EXISTS idx_er_claim     ON escalation_requests(claim_id);
CREATE INDEX IF NOT EXISTS idx_er_topic     ON escalation_requests(topic);
CREATE INDEX IF NOT EXISTS idx_er_timestamp ON escalation_requests(request_timestamp);

-- --------------------------------------------------------------------
-- Grants — oss_app needs full CRUD on all new tables
-- --------------------------------------------------------------------

GRANT SELECT, INSERT, UPDATE, DELETE ON scrutiny_verdicts     TO oss_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON escalation_requests   TO oss_app;
GRANT USAGE, SELECT ON SEQUENCE scrutiny_verdicts_id_seq      TO oss_app;
GRANT USAGE, SELECT ON SEQUENCE escalation_requests_id_seq    TO oss_app;

COMMIT;
