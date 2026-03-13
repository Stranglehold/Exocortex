-- Counter-Patriots Schema — CDS v2 Phase 1
-- Append-only claims store with trust lifecycle, promotion snapshots,
-- source network topology, and comparative completeness infrastructure.
--
-- Invariants:
--   NEVER UPDATE the claims table. New information = new row.
--   NEVER UPDATE promotion_snapshots. Frozen at moment of decision.
--   NEVER UPDATE or DELETE audit_log. Append-only enforced at DB + code level.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------------------------
-- Sources: one row per outlet
-- ---------------------------------------------------------------------------

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

-- ---------------------------------------------------------------------------
-- Claims: append-only, never updated
-- topic_tags is the primary grouping key for all downstream analysis
-- trust_level drives the contamination cascade in Phase 2
-- ---------------------------------------------------------------------------

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
    embedding_model TEXT DEFAULT 'all-MiniLM-L6-v2',

    -- CDS v2 trust lifecycle
    trust_level VARCHAR(16) DEFAULT 'STAGED'
        CHECK (trust_level IN ('STAGED', 'PROMOTED', 'FALSIFIED', 'RETURNED_TO_STAGED')),
    staging_confidence FLOAT DEFAULT 0.0,
    cui_bono JSONB DEFAULT '[]',
    emotional_salience_score FLOAT DEFAULT 0.0
);

CREATE INDEX idx_claims_source    ON claims(source_id);
CREATE INDEX idx_claims_topic     ON claims USING GIN(topic_tags);
CREATE INDEX idx_claims_published ON claims(published_at);
CREATE INDEX idx_claims_extracted ON claims(extracted_at);
CREATE INDEX idx_claims_trust     ON claims(trust_level);

-- ---------------------------------------------------------------------------
-- Promotion snapshots — FROZEN at moment of promotion
-- Never UPDATE this table. The contamination cascade (Phase 2) reconstructs
-- the actual decision, not a current approximation of it.
-- ---------------------------------------------------------------------------

CREATE TABLE promotion_snapshots (
    id SERIAL PRIMARY KEY,
    claim_id INT REFERENCES claims(id) ON DELETE RESTRICT,
    promoted_at TIMESTAMPTZ DEFAULT NOW(),
    promotion_confidence FLOAT NOT NULL,

    -- Weight distribution across corroborating sources at moment of decision
    -- e.g. {"source_12": 0.60, "source_7": 0.25, "source_3": 0.15}
    source_weights JSONB NOT NULL,
    threshold_at_promotion FLOAT NOT NULL,
    promoting_evidence TEXT[],

    -- Predictions that should be true if claim is valid.
    -- Confirmed predictions survive compromise of a corroborating source.
    falsification_predictions JSONB NOT NULL DEFAULT '[]',
    predictions_confirmed_independently INT DEFAULT 0,

    snapshot_frozen BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_promo_claim ON promotion_snapshots(claim_id);
CREATE INDEX idx_promo_at    ON promotion_snapshots(promoted_at);

-- ---------------------------------------------------------------------------
-- Source network topology — required by contamination cascade
-- DO NOT DESCOPE — see COGNITIVE_DEFENSE_SYSTEM_v2.md dependency graph
-- ---------------------------------------------------------------------------

CREATE TABLE source_network_edges (
    id SERIAL PRIMARY KEY,
    source_id INT REFERENCES sources(id) ON DELETE RESTRICT,
    connected_source_id INT REFERENCES sources(id) ON DELETE RESTRICT,
    relationship_type VARCHAR(64) CHECK (
        relationship_type IN ('amplifies', 'is_amplified_by', 'mutual_engagement', 'cluster_member')
    ),
    weight FLOAT DEFAULT 1.0 CHECK (weight BETWEEN 0.0 AND 1.0),
    first_observed TIMESTAMPTZ DEFAULT NOW(),
    last_confirmed TIMESTAMPTZ DEFAULT NOW(),
    observation_count INT DEFAULT 1,
    CONSTRAINT no_self_edge CHECK (source_id != connected_source_id)
);

CREATE INDEX idx_sne_source    ON source_network_edges(source_id);
CREATE INDEX idx_sne_connected ON source_network_edges(connected_source_id);
CREATE UNIQUE INDEX idx_sne_unique_pair
    ON source_network_edges(source_id, connected_source_id, relationship_type);

-- ---------------------------------------------------------------------------
-- Contradictions: pairs with relationship classification
-- source_acknowledged distinguishes journalism from silent retcon
-- ---------------------------------------------------------------------------

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

CREATE INDEX idx_contradictions_claim_a      ON contradictions(claim_a_id);
CREATE INDEX idx_contradictions_claim_b      ON contradictions(claim_b_id);
CREATE INDEX idx_contradictions_relationship ON contradictions(relationship);

-- ---------------------------------------------------------------------------
-- Silence flags: comparative completeness
-- An element present in some source clusters but absent from others
-- ---------------------------------------------------------------------------

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

CREATE INDEX idx_silence_topic    ON silence_flags(topic_tag);
CREATE INDEX idx_silence_detected ON silence_flags(first_detected);

-- ---------------------------------------------------------------------------
-- Activation patterns: narrative spikes across ideologically distinct clusters
-- The emergent context management signature
-- ---------------------------------------------------------------------------

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

CREATE INDEX idx_activation_topic   ON activation_patterns(topic_tag);
CREATE INDEX idx_activation_flagged ON activation_patterns(flagged_at);
CREATE INDEX idx_activation_spread  ON activation_patterns(cluster_spread);

-- ---------------------------------------------------------------------------
-- Living adversary model
-- adversary_abandoned = TRUE means they know the technique is detected
-- ---------------------------------------------------------------------------

CREATE TABLE threat_model (
    id SERIAL PRIMARY KEY,
    technique_name VARCHAR(128) NOT NULL,
    technique_class VARCHAR(64) NOT NULL,
    first_observed TIMESTAMPTZ,
    last_observed TIMESTAMPTZ,
    observed_count INT DEFAULT 0,
    detected_by_system BOOLEAN DEFAULT FALSE,
    adversary_abandoned BOOLEAN DEFAULT FALSE,
    abandoned_at TIMESTAMPTZ,
    predicted_adaptation TEXT,
    notes TEXT
);

CREATE INDEX idx_threat_class     ON threat_model(technique_class);
CREATE INDEX idx_threat_abandoned ON threat_model(adversary_abandoned, abandoned_at);

-- ---------------------------------------------------------------------------
-- Multi-hypothesis registry
-- Implements Chamberlin's method: multiple competing explanations per event.
-- Survivor is the hypothesis whose predictions matched reality.
-- ---------------------------------------------------------------------------

CREATE TABLE hypothesis_registry (
    id SERIAL PRIMARY KEY,
    observation_id INT NOT NULL,          -- opaque event reference; will FK in Phase 2
    candidate_explanation TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    current_confidence FLOAT DEFAULT 0.0 CHECK (current_confidence BETWEEN 0.0 AND 1.0),
    status VARCHAR(32) DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'PROMOTED', 'FALSIFIED', 'SUSPENDED')),
    predictions_generated JSONB DEFAULT '[]',
    predictions_confirmed INT DEFAULT 0,
    predictions_falsified INT DEFAULT 0,
    falsified_at TIMESTAMPTZ,
    falsification_evidence TEXT
);

CREATE INDEX idx_hyp_observation ON hypothesis_registry(observation_id);
CREATE INDEX idx_hyp_status      ON hypothesis_registry(status);

-- ---------------------------------------------------------------------------
-- Propagation dynamics
-- Escape velocity alert: when time_to_escape_velocity < operator_response_time,
-- correction is practically impossible. URGENT fires automatically.
-- ---------------------------------------------------------------------------

CREATE TABLE narrative_dynamics (
    id SERIAL PRIMARY KEY,
    narrative_id INT NOT NULL,
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    propagation_velocity FLOAT,           -- sources per hour
    acceleration FLOAT,                   -- velocity change rate
    escape_velocity_estimate FLOAT,       -- threshold where correction impractical
    time_to_escape_velocity_hours FLOAT,
    half_life_hours FLOAT,                -- falsified claim decay rate
    alert_level VARCHAR(16) DEFAULT 'INFORMATIONAL'
        CHECK (alert_level IN ('INFORMATIONAL', 'WARNING', 'URGENT'))
);

CREATE INDEX idx_nd_narrative ON narrative_dynamics(narrative_id);
CREATE INDEX idx_nd_alert     ON narrative_dynamics(alert_level);
CREATE INDEX idx_nd_computed  ON narrative_dynamics(computed_at DESC);

-- ---------------------------------------------------------------------------
-- Topics: registry of tracked topic tags
-- Prevents tag proliferation and ensures consistent granularity
-- ---------------------------------------------------------------------------

CREATE TABLE topics (
    tag TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT,
    parent_tag TEXT REFERENCES topics(tag),
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW(),
    claim_count INT DEFAULT 0,
    active BOOLEAN DEFAULT TRUE
);

-- ---------------------------------------------------------------------------
-- Audit log — append only, never updated, never deleted
-- autovacuum disabled: append-only table never accumulates dead rows
-- ---------------------------------------------------------------------------

CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    session_id UUID NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    actor VARCHAR(64) NOT NULL,
    action TEXT NOT NULL,
    data_accessed JSONB,
    trust_level VARCHAR(16),
    injection_flag BOOLEAN DEFAULT FALSE
) WITH (autovacuum_enabled = false);

CREATE INDEX idx_audit_session   ON audit_log(session_id);
CREATE INDEX idx_audit_event     ON audit_log(event_type);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp DESC);

-- ---------------------------------------------------------------------------
-- Application role: cds_app
-- Non-superuser role used by the Flask application.
-- cp_user is the admin role for migrations and schema management only.
-- ---------------------------------------------------------------------------

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'cds_app') THEN
        CREATE ROLE cds_app LOGIN PASSWORD 'cds_app_dev_password';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE counter_patriots TO cds_app;
GRANT USAGE ON SCHEMA public TO cds_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO cds_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO cds_app;

-- Enforce append-only on audit_log at the database level
REVOKE UPDATE ON audit_log FROM cds_app;
REVOKE DELETE ON audit_log FROM cds_app;

-- ---------------------------------------------------------------------------
-- Seed: founding topic thread
-- ---------------------------------------------------------------------------

INSERT INTO topics (tag, display_name, description)
VALUES ('iran-hormuz', 'Iran / Strait of Hormuz', 'Coverage of Iran-related Hormuz attribution and military posture');

INSERT INTO topics (tag, display_name, description, parent_tag)
VALUES ('iran', 'Iran (general)', 'General Iran coverage', NULL);

-- ---------------------------------------------------------------------------
-- Seed: source list
-- ---------------------------------------------------------------------------

INSERT INTO sources (name, url, source_type, cluster) VALUES
    ('Reuters',             'https://feeds.reuters.com/reuters/topNews',              'wire',    'wire'),
    ('AP',                  'https://rsshub.app/ap/topics/apf-intlnews',              'wire',    'wire'),
    ('BBC',                 'https://feeds.bbci.co.uk/news/world/rss.xml',            'outlet',  'international'),
    ('The Guardian',        'https://www.theguardian.com/world/rss',                  'outlet',  'left'),
    ('NPR',                 'https://feeds.npr.org/1001/rss.xml',                     'outlet',  'center'),
    ('ABC News',            'https://feeds.abcnews.com/abcnews/internationalheadlines','outlet', 'center'),
    ('Fox News',            'https://moxie.foxnews.com/google-publisher/world.xml',   'outlet',  'right'),
    ('NYT',                 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml', 'outlet',  'center'),
    ('Wall Street Journal', 'https://feeds.a.dj.com/rss/RSSWorldNews.xml',           'outlet',  'right'),
    ('Al Jazeera',          'https://www.aljazeera.com/xml/rss/all.xml',              'outlet',  'international'),
    ('State Dept',          'https://www.state.gov/rss-feeds/',                        'official','official'),
    ('The Intercept',       'https://theintercept.com/feed/?lang=en',                 'outlet',  'independent'),
    ('Moon of Alabama',     'https://www.moonofalabama.org/atom.xml',                 'outlet',  'independent');

-- Seed cluster membership edges from source metadata.
-- Wire and mainstream clusters get bidirectional edges.
-- Official and independent sources: edges must be observed, not assumed.
INSERT INTO source_network_edges (source_id, connected_source_id, relationship_type, weight)
SELECT a.id, b.id, 'cluster_member', 0.8
FROM sources a
CROSS JOIN sources b
WHERE a.id != b.id
  AND a.cluster = b.cluster
  AND a.cluster NOT IN ('official', 'independent')
ON CONFLICT (source_id, connected_source_id, relationship_type) DO NOTHING;
