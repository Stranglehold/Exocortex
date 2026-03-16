-- Migration 004: Topic feedback loop columns
-- Tracks irrelevance signal per topic to modulate ingestion throughput.
-- scrape_weight decays as irrelevance_rate rises; floor 0.05 prevents full silence.

ALTER TABLE topics ADD COLUMN IF NOT EXISTS irrelevance_count INT DEFAULT 0;
ALTER TABLE topics ADD COLUMN IF NOT EXISTS total_staged_count INT DEFAULT 0;
ALTER TABLE topics ADD COLUMN IF NOT EXISTS scrape_weight FLOAT DEFAULT 1.0
    CHECK (scrape_weight BETWEEN 0.0 AND 1.0);
