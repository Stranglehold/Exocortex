-- ============================================================
-- Migration 003: Autonomous Resolver — Proposed Resolutions
--
-- The resolver reads old sessions + new OSS claims and proposes
-- confirmed/falsified/still_pending verdicts with cited evidence.
-- These are ADVISORY by default — the operator accepts or overrides
-- before anything flows into acp_outcomes / calibration.
-- ============================================================

CREATE TABLE IF NOT EXISTS acp_proposed_resolutions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID NOT NULL REFERENCES acp_sessions(id),

    -- The verdict
    verdict         TEXT NOT NULL
                    CHECK (verdict IN ('confirmed', 'falsified', 'still_pending')),
    resolver_confidence FLOAT NOT NULL
                    CHECK (resolver_confidence >= 0 AND resolver_confidence <= 1),

    -- Draft outcome the operator can accept as-is or edit
    outcome_text    TEXT NOT NULL,
    reasoning       TEXT NOT NULL,

    -- Evidence the resolver used — array of {claim_id, source, date, text_excerpt}
    cited_claims    JSONB DEFAULT '[]'::jsonb,

    -- Provenance of the evidence window
    claims_considered_count INT DEFAULT 0,
    claims_since    TIMESTAMPTZ,

    -- Operator action — null while pending, set on review
    operator_action TEXT
                    CHECK (operator_action IS NULL OR operator_action IN ('accepted', 'overridden', 'deferred')),
    operator_action_at TIMESTAMPTZ,
    -- When operator accepts, the resulting outcome row in acp_outcomes
    final_outcome_id UUID REFERENCES acp_outcomes(id),
    -- If overridden, what the operator actually decided (for concordance tracking)
    operator_was_correct BOOLEAN,

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_proposed_session ON acp_proposed_resolutions(session_id);
CREATE INDEX IF NOT EXISTS idx_proposed_action  ON acp_proposed_resolutions(operator_action);
CREATE INDEX IF NOT EXISTS idx_proposed_created ON acp_proposed_resolutions(created_at DESC);

GRANT SELECT, INSERT, UPDATE ON acp_proposed_resolutions TO swarmfish_app;
