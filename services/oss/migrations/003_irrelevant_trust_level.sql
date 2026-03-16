-- Migration 003: Add IRRELEVANT trust level to claims
-- Allows analysts to mark claims as not relevant to current monitoring scope.
-- IRRELEVANT claims are excluded from Feed and Staging views.

ALTER TABLE claims DROP CONSTRAINT IF EXISTS claims_trust_level_check;
ALTER TABLE claims ADD CONSTRAINT claims_trust_level_check
    CHECK (trust_level IN ('STAGED','PROMOTED','FALSIFIED','RETURNED_TO_STAGED','IRRELEVANT'));
