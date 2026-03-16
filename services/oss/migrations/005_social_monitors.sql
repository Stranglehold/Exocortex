-- Migration 005: Social media monitor configuration table
-- Stores scheduled X/Twitter search queries and their ingestion parameters.
-- Playwright scraper reads active rows and runs searches on interval.

CREATE TABLE IF NOT EXISTS social_monitors (
    id SERIAL PRIMARY KEY,
    platform TEXT NOT NULL DEFAULT 'x',
    display_name TEXT NOT NULL,
    query TEXT NOT NULL,
    monitor_type TEXT NOT NULL DEFAULT 'search'
        CHECK (monitor_type IN ('search', 'hashtag', 'user')),
    topic_tags TEXT[] DEFAULT '{}',
    active BOOLEAN DEFAULT TRUE,
    interval_minutes INT DEFAULT 60,
    last_run_at TIMESTAMP,
    result_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
