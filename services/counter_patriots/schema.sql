-- Counter-Patriots Schema
-- Append-only claims store with comparative completeness infrastructure.
-- Never UPDATE the claims table. New information = new row.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Sources: one row per outlet
CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL CHECK (source_type IN ('official', 'wire', 'outlet', 'social')),
    cluster TEXT NOT NULL CHECK (cluster IN ('left', 'center', 'right', 'wire', 'official', 'independent', 'international')),
    confidence_score FLOAT DEFAULT 0.7 CHECK (confidence_score BETWEEN 0.0 AND 1.0),
    acknowledged_retcon_count INT DEFAULT 0,
    silent_retcon_count INT DEFAULT 0,
    total_claims INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Claims: append-only, never updated
-- topic_tag is the primary grouping key for all downstream analysis
CREATE TABLE claims (
    id SERIAL PRIMARY KEY,
    source_id INT REFERENCES sources(id) ON DELETE RESTRICT,
    raw_text TEXT NOT NULL,
    claim_text TEXT NOT NULL,
    article_url TEXT NOT NULL,
    article_title TEXT,
    topic_tags TEXT[] DEFAULT '{}',       -- array: a claim can belong to multiple topics
    technique_class TEXT CHECK (
        technique_class IN ('presuasion', 'fracture', 'emergent', 'direct', 'none', NULL)
    ),
    extracted_at TIMESTAMP DEFAULT NOW(),
    published_at TIMESTAMP,
    faiss_id INT,
    embedding_model TEXT DEFAULT 'all-MiniLM-L6-v2'
);

CREATE INDEX idx_claims_source ON claims(source_id);
CREATE INDEX idx_claims_topic ON claims USING GIN(topic_tags);
CREATE INDEX idx_claims_published ON claims(published_at);
CREATE INDEX idx_claims_extracted ON claims(extracted_at);

-- Contradictions: pairs with relationship classification
-- source_acknowledged distinguishes journalism from silent retcon
CREATE TABLE contradictions (
    id SERIAL PRIMARY KEY,
    claim_a_id INT REFERENCES claims(id) ON DELETE RESTRICT,
    claim_b_id INT REFERENCES claims(id) ON DELETE RESTRICT,
    relationship TEXT NOT NULL CHECK (
        relationship IN ('contradiction', 'retcon_silent', 'retcon_acknowledged', 'elaboration')
    ),
    confidence FLOAT NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),
    source_acknowledged BOOLEAN DEFAULT FALSE,
    analyst_reviewed BOOLEAN DEFAULT FALSE,
    technique_class TEXT,
    flagged_at TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    CONSTRAINT no_self_contradiction CHECK (claim_a_id != claim_b_id)
);

CREATE INDEX idx_contradictions_claim_a ON contradictions(claim_a_id);
CREATE INDEX idx_contradictions_claim_b ON contradictions(claim_b_id);
CREATE INDEX idx_contradictions_relationship ON contradictions(relationship);

-- Silence flags: comparative completeness
-- An element present in some source clusters but absent from others
CREATE TABLE silence_flags (
    id SERIAL PRIMARY KEY,
    topic_tag TEXT NOT NULL,
    element TEXT NOT NULL,
    element_embedding_json TEXT,          -- JSON float array for semantic dedup
    present_in_sources INT[],
    absent_from_sources INT[],
    present_in_clusters TEXT[],           -- cluster names where element appears
    absent_from_clusters TEXT[],          -- cluster names where element is missing
    first_detected TIMESTAMP DEFAULT NOW(),
    detection_method TEXT NOT NULL CHECK (
        detection_method IN ('comparative', 'template', 'pattern')
    ),
    analyst_reviewed BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_silence_topic ON silence_flags(topic_tag);
CREATE INDEX idx_silence_detected ON silence_flags(first_detected);

-- Activation patterns: narrative spikes across ideologically distinct clusters
-- The emergent context management signature
CREATE TABLE activation_patterns (
    id SERIAL PRIMARY KEY,
    topic_tag TEXT NOT NULL,
    claim_pattern TEXT NOT NULL,          -- canonical form of the narrative being tracked
    source_ids INT[],
    cluster_spread INT NOT NULL,          -- count of distinct clusters where pattern appeared
    clusters_present TEXT[],             -- which cluster names
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    window_minutes INT,                   -- time window of appearance
    claim_count INT DEFAULT 0,           -- number of claims matching the pattern
    flagged_at TIMESTAMP DEFAULT NOW(),
    technique_class TEXT DEFAULT 'emergent'
);

CREATE INDEX idx_activation_topic ON activation_patterns(topic_tag);
CREATE INDEX idx_activation_flagged ON activation_patterns(flagged_at);
CREATE INDEX idx_activation_spread ON activation_patterns(cluster_spread);

-- Topics: registry of tracked topic tags with metadata
-- Prevents topic_tag proliferation and ensures consistent granularity
CREATE TABLE topics (
    tag TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT,
    parent_tag TEXT REFERENCES topics(tag),   -- hierarchical: 'iran' parent of 'iran-hormuz'
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW(),
    claim_count INT DEFAULT 0,
    active BOOLEAN DEFAULT TRUE
);

-- Seed with founding topic thread
INSERT INTO topics (tag, display_name, description)
VALUES ('iran-hormuz', 'Iran / Strait of Hormuz', 'Coverage of Iran-related Hormuz attribution and military posture');

INSERT INTO topics (tag, display_name, description, parent_tag)
VALUES ('iran', 'Iran (general)', 'General Iran coverage', NULL);

-- Seed source list (cluster taxonomy includes 'independent' and 'international'
-- beyond the original 5 in the spec — see architecture note)
INSERT INTO sources (name, url, source_type, cluster) VALUES
    ('Reuters',           'https://feeds.reuters.com/reuters/topNews',        'wire',    'wire'),
    ('AP',                'https://rsshub.app/ap/topics/apf-intlnews',        'wire',    'wire'),
    ('BBC',               'https://feeds.bbci.co.uk/news/world/rss.xml',      'outlet',  'international'),
    ('The Guardian',      'https://www.theguardian.com/world/rss',            'outlet',  'left'),
    ('NPR',               'https://feeds.npr.org/1001/rss.xml',               'outlet',  'center'),
    ('ABC News',          'https://feeds.abcnews.com/abcnews/internationalheadlines', 'outlet', 'center'),
    ('Fox News',          'https://moxie.foxnews.com/google-publisher/world.xml', 'outlet', 'right'),
    ('NYT',               'https://rss.nytimes.com/services/xml/rss/nyt/World.xml', 'outlet', 'center'),
    ('Wall Street Journal', 'https://feeds.a.dj.com/rss/RSSWorldNews.xml',   'outlet',  'right'),
    ('Al Jazeera',        'https://www.aljazeera.com/xml/rss/all.xml',        'outlet',  'international'),
    ('State Dept',        'https://www.state.gov/rss-feeds/',                  'official','official'),
    ('The Intercept',     'https://theintercept.com/feed/?lang=en',           'outlet',  'independent'),
    ('Moon of Alabama',   'https://www.moonofalabama.org/atom.xml',           'outlet',  'independent');
