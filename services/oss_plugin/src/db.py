"""
db.py — OSS V2 SQLite database layer.

Consolidates the V1 PostgreSQL schema (schema.sql + 7 migrations) into a
single SQLite schema, adds V2 tables (active_questions, source_credibility,
rejection_ledger), and provides connection helpers used by all OSS modules.

SQLite translation notes vs. the original PostgreSQL schema:
  - SERIAL / BIGSERIAL      → INTEGER PRIMARY KEY AUTOINCREMENT
  - TEXT[] / JSONB          → TEXT (JSON stored as string, helpers below)
  - TIMESTAMPTZ / TIMESTAMP → TEXT (ISO-8601 strings)
  - BOOLEAN                 → INTEGER (0 / 1)
  - ILIKE                   → LIKE  (SQLite LIKE is case-insensitive on ASCII)
  - NOW()                   → datetime('now')
  - %s placeholders         → ? placeholders
  - CREATE EXTENSION / ROLE → removed
  - GIN indexes             → removed (not supported in SQLite)
  - autovacuum directives   → removed
"""

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from typing import Any, Optional

DB_PATH = os.environ.get("OSS_DB_PATH", "/a0/usr/oss/oss.db")

# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

def get_conn() -> sqlite3.Connection:
    """Open a WAL-mode connection with row_factory and FK support."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=15000")
    return conn


@contextmanager
def cursor(conn: Optional[sqlite3.Connection] = None):
    """Yield a cursor; auto-commit on clean exit."""
    owned = conn is None
    c = get_conn() if owned else conn
    try:
        cur = c.cursor()
        yield cur
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        if owned:
            c.close()


# ---------------------------------------------------------------------------
# Row / JSON helpers
# ---------------------------------------------------------------------------

def row_to_dict(row) -> dict:
    if row is None:
        return {}
    return dict(row)


def rows_to_dicts(rows) -> list:
    return [dict(r) for r in rows]


def jloads(s: Any, default=None):
    """Safe JSON parse for values stored as TEXT."""
    if s is None:
        return default
    if isinstance(s, (dict, list)):
        return s
    try:
        return json.loads(s)
    except Exception:
        return default


def jdumps(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, str):
        return v
    return json.dumps(v, ensure_ascii=False)


def new_id() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA = """
-- ── Sources ─────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS sources (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    name                     TEXT NOT NULL,
    url                      TEXT NOT NULL UNIQUE,
    source_type              TEXT NOT NULL CHECK (source_type IN ('official','wire','outlet','social')),
    cluster                  TEXT NOT NULL CHECK (cluster IN ('left','center','right','wire','official','independent','international')),
    confidence_score         REAL    DEFAULT 0.7 CHECK (confidence_score BETWEEN 0.0 AND 1.0),
    acknowledged_retcon_count INTEGER DEFAULT 0,
    silent_retcon_count       INTEGER DEFAULT 0,
    total_claims              INTEGER DEFAULT 0,
    irrelevance_count         INTEGER DEFAULT 0,
    scrape_weight             REAL    DEFAULT 1.0,
    created_at               TEXT    DEFAULT (datetime('now'))
);

-- ── Claims (append-only) ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS claims (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id             INTEGER REFERENCES sources(id) ON DELETE RESTRICT,
    raw_text              TEXT NOT NULL,
    claim_text            TEXT NOT NULL,
    article_url           TEXT NOT NULL,
    article_title         TEXT,
    topic_tags            TEXT    DEFAULT '[]',
    technique_class       TEXT    CHECK (technique_class IN ('presuasion','fracture','emergent','direct','none') OR technique_class IS NULL),
    extracted_at          TEXT    DEFAULT (datetime('now')),
    published_at          TEXT,
    faiss_id              INTEGER,
    embedding_model       TEXT    DEFAULT 'all-MiniLM-L6-v2',
    trust_level           TEXT    DEFAULT 'STAGED'
        CHECK (trust_level IN ('STAGED','PROMOTED','FALSIFIED','RETURNED_TO_STAGED','IRRELEVANT')),
    staging_confidence    REAL    DEFAULT 0.0,
    cui_bono              TEXT    DEFAULT '[]',
    emotional_salience_score REAL DEFAULT 0.0
);

CREATE INDEX IF NOT EXISTS idx_claims_source    ON claims(source_id);
CREATE INDEX IF NOT EXISTS idx_claims_published ON claims(published_at);
CREATE INDEX IF NOT EXISTS idx_claims_extracted ON claims(extracted_at);
CREATE INDEX IF NOT EXISTS idx_claims_trust     ON claims(trust_level);

-- ── Promotion snapshots (frozen at decision time) ───────────────────────────

CREATE TABLE IF NOT EXISTS promotion_snapshots (
    id                              INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id                        INTEGER REFERENCES claims(id) ON DELETE RESTRICT,
    promoted_at                     TEXT    DEFAULT (datetime('now')),
    promotion_confidence            REAL    NOT NULL,
    source_weights                  TEXT    NOT NULL,
    threshold_at_promotion          REAL    NOT NULL,
    promoting_evidence              TEXT    DEFAULT '[]',
    falsification_predictions       TEXT    DEFAULT '[]',
    predictions_confirmed_independently INTEGER DEFAULT 0,
    snapshot_frozen                 INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_promo_claim ON promotion_snapshots(claim_id);
CREATE INDEX IF NOT EXISTS idx_promo_at    ON promotion_snapshots(promoted_at);

-- ── Source network topology ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS source_network_edges (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id            INTEGER REFERENCES sources(id) ON DELETE RESTRICT,
    connected_source_id  INTEGER REFERENCES sources(id) ON DELETE RESTRICT,
    relationship_type    TEXT CHECK (relationship_type IN ('amplifies','is_amplified_by','mutual_engagement','cluster_member')),
    weight               REAL    DEFAULT 1.0 CHECK (weight BETWEEN 0.0 AND 1.0),
    first_observed       TEXT    DEFAULT (datetime('now')),
    last_confirmed       TEXT    DEFAULT (datetime('now')),
    observation_count    INTEGER DEFAULT 1,
    CONSTRAINT no_self_edge CHECK (source_id != connected_source_id),
    UNIQUE (source_id, connected_source_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_sne_source    ON source_network_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_sne_connected ON source_network_edges(connected_source_id);

-- ── Contradictions ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS contradictions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_a_id          INTEGER REFERENCES claims(id) ON DELETE RESTRICT,
    claim_b_id          INTEGER REFERENCES claims(id) ON DELETE RESTRICT,
    relationship        TEXT NOT NULL CHECK (relationship IN ('contradiction','retcon_silent','retcon_acknowledged','elaboration')),
    confidence          REAL NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),
    source_acknowledged INTEGER DEFAULT 0,
    analyst_reviewed    INTEGER DEFAULT 0,
    technique_class     TEXT,
    flagged_at          TEXT DEFAULT (datetime('now')),
    notes               TEXT,
    CONSTRAINT no_self_contradiction CHECK (claim_a_id != claim_b_id)
);

CREATE INDEX IF NOT EXISTS idx_contradictions_claim_a      ON contradictions(claim_a_id);
CREATE INDEX IF NOT EXISTS idx_contradictions_claim_b      ON contradictions(claim_b_id);
CREATE INDEX IF NOT EXISTS idx_contradictions_relationship ON contradictions(relationship);

-- ── Silence flags ───────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS silence_flags (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_tag             TEXT NOT NULL,
    element               TEXT NOT NULL,
    element_embedding_json TEXT,
    present_in_sources    TEXT DEFAULT '[]',
    absent_from_sources   TEXT DEFAULT '[]',
    present_in_clusters   TEXT DEFAULT '[]',
    absent_from_clusters  TEXT DEFAULT '[]',
    first_detected        TEXT DEFAULT (datetime('now')),
    detection_method      TEXT NOT NULL CHECK (detection_method IN ('comparative','template','pattern')),
    analyst_reviewed      INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_silence_topic    ON silence_flags(topic_tag);
CREATE INDEX IF NOT EXISTS idx_silence_detected ON silence_flags(first_detected);

-- ── Activation patterns ─────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS activation_patterns (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_tag      TEXT NOT NULL,
    claim_pattern  TEXT NOT NULL,
    source_ids     TEXT DEFAULT '[]',
    cluster_spread INTEGER NOT NULL,
    clusters_present TEXT DEFAULT '[]',
    first_seen     TEXT,
    last_seen      TEXT,
    window_minutes INTEGER,
    claim_count    INTEGER DEFAULT 0,
    flagged_at     TEXT DEFAULT (datetime('now')),
    technique_class TEXT DEFAULT 'emergent'
);

CREATE INDEX IF NOT EXISTS idx_activation_topic   ON activation_patterns(topic_tag);
CREATE INDEX IF NOT EXISTS idx_activation_flagged ON activation_patterns(flagged_at);
CREATE INDEX IF NOT EXISTS idx_activation_spread  ON activation_patterns(cluster_spread);

-- ── Threat model ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS threat_model (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    technique_name       TEXT NOT NULL,
    technique_class      TEXT NOT NULL,
    first_observed       TEXT,
    last_observed        TEXT,
    observed_count       INTEGER DEFAULT 0,
    detected_by_system   INTEGER DEFAULT 0,
    adversary_abandoned  INTEGER DEFAULT 0,
    abandoned_at         TEXT,
    predicted_adaptation TEXT,
    notes                TEXT
);

CREATE INDEX IF NOT EXISTS idx_threat_class     ON threat_model(technique_class);
CREATE INDEX IF NOT EXISTS idx_threat_abandoned ON threat_model(adversary_abandoned);

-- ── Hypothesis registry ─────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS hypothesis_registry (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_id           INTEGER NOT NULL,
    candidate_explanation    TEXT NOT NULL,
    created_at               TEXT DEFAULT (datetime('now')),
    current_confidence       REAL DEFAULT 0.0 CHECK (current_confidence BETWEEN 0.0 AND 1.0),
    status                   TEXT DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','PROMOTED','FALSIFIED','SUSPENDED')),
    predictions_generated    TEXT DEFAULT '[]',
    predictions_confirmed    INTEGER DEFAULT 0,
    predictions_falsified    INTEGER DEFAULT 0,
    falsified_at             TEXT,
    falsification_evidence   TEXT,
    swarmfish_session_id     TEXT,
    swarmfish_source         TEXT,
    prediction_check_cursor  INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_hyp_observation ON hypothesis_registry(observation_id);
CREATE INDEX IF NOT EXISTS idx_hyp_status      ON hypothesis_registry(status);

-- ── Narrative dynamics ──────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS narrative_dynamics (
    id                           INTEGER PRIMARY KEY AUTOINCREMENT,
    narrative_id                 INTEGER NOT NULL,
    topic_tag                    TEXT,
    computed_at                  TEXT DEFAULT (datetime('now')),
    propagation_velocity         REAL,
    acceleration                 REAL,
    escape_velocity_estimate     REAL,
    time_to_escape_velocity_hours REAL,
    half_life_hours              REAL,
    alert_level                  TEXT DEFAULT 'INFORMATIONAL'
        CHECK (alert_level IN ('INFORMATIONAL','WARNING','URGENT'))
);

CREATE INDEX IF NOT EXISTS idx_nd_narrative ON narrative_dynamics(narrative_id);
CREATE INDEX IF NOT EXISTS idx_nd_alert     ON narrative_dynamics(alert_level);
CREATE INDEX IF NOT EXISTS idx_nd_computed  ON narrative_dynamics(computed_at DESC);

-- ── Topics ──────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS topics (
    tag          TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description  TEXT,
    parent_tag   TEXT REFERENCES topics(tag),
    created_at   TEXT DEFAULT (datetime('now')),
    last_active  TEXT DEFAULT (datetime('now')),
    claim_count  INTEGER DEFAULT 0,
    active       INTEGER DEFAULT 1
);

-- ── Audit log (append-only) ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT    DEFAULT (datetime('now')),
    session_id      TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    actor           TEXT NOT NULL,
    action          TEXT NOT NULL,
    data_accessed   TEXT,
    trust_level     TEXT,
    injection_flag  INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_audit_session   ON audit_log(session_id);
CREATE INDEX IF NOT EXISTS idx_audit_event     ON audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);

-- ── Operator state ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS operator_state (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_level          TEXT NOT NULL DEFAULT 'NOMINAL'
        CHECK (alert_level IN ('NOMINAL','DEGRADED','IMPAIRED')),
    threshold_multiplier REAL NOT NULL DEFAULT 1.0,
    reason               TEXT,
    set_at               TEXT DEFAULT (datetime('now')),
    set_by               TEXT DEFAULT 'system'
);

-- ── Social monitors ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS social_monitors (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    monitor_type TEXT NOT NULL CHECK (monitor_type IN ('search','hashtag','user')),
    query        TEXT NOT NULL,
    topic_tags   TEXT DEFAULT '[]',
    enabled      INTEGER DEFAULT 1,
    created_at   TEXT DEFAULT (datetime('now')),
    last_run     TEXT,
    run_count    INTEGER DEFAULT 0
);

-- ── V2: Active questions ─────────────────────────────────────────────────────
-- Replaces static topic-oriented organization. The analyst's current question
-- is the organizing principle. Claims are relevant to the active question,
-- not just matching a keyword. Multiple questions can coexist.

CREATE TABLE IF NOT EXISTS active_questions (
    id               TEXT PRIMARY KEY,
    text             TEXT NOT NULL,
    evolved_from     TEXT DEFAULT '[]',
    attention_weights TEXT DEFAULT '{}',
    created_at       TEXT DEFAULT (datetime('now')),
    last_updated     TEXT DEFAULT (datetime('now')),
    active           INTEGER DEFAULT 1
);

-- ── V2: Source credibility (analyst ratings) ────────────────────────────────
-- Per-source credibility scores set by the analyst, with optional domain
-- conditioning. Flows through to claim weighting in synthesis.

CREATE TABLE IF NOT EXISTS source_credibility (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id        INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    overall          REAL    DEFAULT 0.7 CHECK (overall BETWEEN 0.0 AND 1.0),
    domain_overrides TEXT    DEFAULT '{}',
    set_by           TEXT    DEFAULT 'analyst',
    last_updated     TEXT    DEFAULT (datetime('now')),
    UNIQUE(source_id)
);

-- ── V2: Rejection ledger ─────────────────────────────────────────────────────
-- Claims rejected during ingestion (duplicate, low-confidence, off-topic).
-- The analyst can review rejections on demand — transparency at every stage.

CREATE TABLE IF NOT EXISTS rejection_ledger (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_text       TEXT NOT NULL,
    article_url      TEXT NOT NULL,
    article_title    TEXT,
    source_id        INTEGER REFERENCES sources(id),
    rejection_reason TEXT NOT NULL
        CHECK (rejection_reason IN ('duplicate','low_confidence','off_topic','source_rejected')),
    rejection_detail TEXT,
    rejected_at      TEXT DEFAULT (datetime('now')),
    similarity_score REAL,
    duplicate_of_id  INTEGER REFERENCES claims(id)
);

CREATE INDEX IF NOT EXISTS idx_rejection_source   ON rejection_ledger(source_id);
CREATE INDEX IF NOT EXISTS idx_rejection_reason   ON rejection_ledger(rejection_reason);
CREATE INDEX IF NOT EXISTS idx_rejection_rejected ON rejection_ledger(rejected_at);
"""

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

_SEED_TOPICS = [
    ("iran-hormuz", "Iran / Strait of Hormuz",
     "Coverage of Iran-related Hormuz attribution and military posture", None),
    ("iran", "Iran (general)", "General Iran coverage", None),
]

_SEED_SOURCES = [
    ("Reuters",             "https://feeds.reuters.com/reuters/topNews",               "wire",    "wire"),
    ("AP",                  "https://rsshub.app/ap/topics/apf-intlnews",               "wire",    "wire"),
    ("BBC",                 "https://feeds.bbci.co.uk/news/world/rss.xml",             "outlet",  "international"),
    ("The Guardian",        "https://www.theguardian.com/world/rss",                   "outlet",  "left"),
    ("NPR",                 "https://feeds.npr.org/1001/rss.xml",                      "outlet",  "center"),
    ("ABC News",            "https://feeds.abcnews.com/abcnews/internationalheadlines","outlet",  "center"),
    ("Fox News",            "https://moxie.foxnews.com/google-publisher/world.xml",    "outlet",  "right"),
    ("NYT",                 "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",  "outlet",  "center"),
    ("Wall Street Journal", "https://feeds.a.dj.com/rss/RSSWorldNews.xml",            "outlet",  "right"),
    ("Al Jazeera",          "https://www.aljazeera.com/xml/rss/all.xml",               "outlet",  "international"),
    ("State Dept",          "https://www.state.gov/rss-feeds/",                        "official","official"),
    ("The Intercept",       "https://theintercept.com/feed/?lang=en",                  "outlet",  "independent"),
    ("Moon of Alabama",     "https://www.moonofalabama.org/atom.xml",                  "outlet",  "independent"),
]


def init_db(conn: Optional[sqlite3.Connection] = None) -> sqlite3.Connection:
    """Create all tables if they don't exist, seed initial data."""
    owned = conn is None
    c = conn or get_conn()
    try:
        c.executescript(SCHEMA)
        c.commit()
        _seed(c)
        c.commit()
    finally:
        if owned:
            c.close()
    return c


def _seed(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    # Topics
    for tag, display, desc, parent in _SEED_TOPICS:
        cur.execute(
            "INSERT OR IGNORE INTO topics (tag, display_name, description, parent_tag) VALUES (?,?,?,?)",
            (tag, display, desc, parent),
        )

    # Sources
    for name, url, stype, cluster in _SEED_SOURCES:
        cur.execute(
            "INSERT OR IGNORE INTO sources (name, url, source_type, cluster) VALUES (?,?,?,?)",
            (name, url, stype, cluster),
        )

    # Cluster member edges — wire and mainstream clusters, bidirectional
    cur.execute("""
        INSERT OR IGNORE INTO source_network_edges
            (source_id, connected_source_id, relationship_type, weight)
        SELECT a.id, b.id, 'cluster_member', 0.8
        FROM sources a
        JOIN sources b ON a.id != b.id AND a.cluster = b.cluster
        WHERE a.cluster NOT IN ('official', 'independent')
    """)

    # Seed nominal operator state if empty
    cur.execute("SELECT COUNT(*) FROM operator_state")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO operator_state (alert_level, threshold_multiplier, set_by) VALUES ('NOMINAL', 1.0, 'seed')",
        )
