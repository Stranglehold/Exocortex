# OSS — Open Source Signal

Cognitive defense platform. Monitors information ecosystems for narrative manipulation, coordinated inauthentic behavior, and silence. Returns records — the analyst holds the conclusions.

**Port:** 7731 · **Postgres:** 5433 · **Container:** `oss_app`

---

## Design Constraints

**Curtis Rule** — The following endpoints do not exist and will not be added:
- `/api/suggest_framing`
- `/api/truth_score`
- `/api/counter_narrative`

OSS surfaces what is in the information space. It does not direct the analyst toward any conclusion.

**Festinger Boundary** — Contradiction data, staging actions, and hypothesis management require `X-Analyst-Token`. No bulk export of contradiction data without authentication.

---

## Setup

```bash
cd services/oss

# First run — initialize schema and create oss_app role
./install.sh --migrate

# Start containers
docker compose up -d

# Subsequent migrations only
./install.sh --migrate
```

**Dependencies:** Docker, Docker Compose. LM Studio running on host with a compatible model.

---

## Configuration

All via environment variables (set in `docker-compose.yml` or `.env`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `OSS_DB_URL` | `postgresql://oss_app:...@postgres:5432/oss` | App DB connection (non-superuser) |
| `OSS_LLM_URL` | `http://host.docker.internal:1234/v1` | LM Studio API endpoint |
| `OSS_LLM_MODEL` | `qwen3.5-27b-...@q4_k_m` | Model for extraction and analysis |
| `OSS_ANALYST_TOKEN` | `dev_analyst_token` | Auth token for protected endpoints |
| `OSS_EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence embedding model |
| `OSS_INGEST_INTERVAL_MINUTES` | `30` | RSS ingestion frequency |
| `OSS_INGEST_PAUSED` | `true` | Start with ingestion paused |
| `SWARMFISH_BASE_URL` | `http://host.docker.internal:7732` | SWARMFISH service location |
| `SWARMFISH_ANALYST_TOKEN` | `dev_analyst_token` | SWARMFISH auth |
| `X_AUTH_TOKEN` | _(empty)_ | X/Twitter `auth_token` cookie |
| `X_CT0_TOKEN` | _(empty)_ | X/Twitter `ct0` cookie |

To get X credentials: log into x.com → DevTools → Application → Cookies → copy `auth_token` and `ct0`.

---

## API Reference

Auth header: `X-Analyst-Token: <token>` (required for all protected endpoints)

### Public Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Service status, claim counts, last ingestion time |
| `GET` | `/api/feed` | Recent claims (optional `?topic=` filter) |
| `GET` | `/api/topics` | All monitored topic tags with claim counts |
| `GET` | `/api/sources` | Registered sources with trust metadata |
| `GET` | `/api/operator_state` | Current operator alert level and threshold multiplier |
| `GET` | `/api/operator_state/history` | Operator state change history |

### Authenticated — Query

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/topic` | Claims for a topic (`{topic, since?, limit?}`) |
| `POST` | `/api/topic_drift` | Narrative framing shift detection (`{topic, window_hours?}`) |
| `POST` | `/api/propagation_dynamics` | Propagation velocity and escape analysis (`{topic, window_hours?}`) |
| `POST` | `/api/contradictions` | Contradiction ledger for a topic |
| `POST` | `/api/silence` | Silence detection scan results |
| `POST` | `/api/hypotheses` | List hypotheses (`{observation_id?, status?, limit?}`) |
| `POST` | `/api/staging` | Claims awaiting analyst review |
| `GET` | `/api/health/meta` | OSS system health signal (NOMINAL / DEGRADED / COMPROMISED) |

### Authenticated — Hypothesis Lifecycle

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/hypothesis/<id>/falsify` | Mark hypothesis FALSIFIED (`{evidence}`) — posts outcome to SWARMFISH |
| `POST` | `/api/hypothesis/<id>/promote` | Mark hypothesis PROMOTED — posts outcome to SWARMFISH |
| `POST` | `/api/hypothesis/<id>/confirm_prediction` | Confirm a specific prediction (`{prediction_idx}`) |
| `POST` | `/api/hypothesis/from_swarmfish` | Register a SWARMFISH-generated hypothesis |

### Admin

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/admin/promote_claim` | Promote a staged claim to PROMOTED |
| `POST` | `/admin/mark_irrelevant` | Mark a claim as analyst-reviewed irrelevant |
| `POST` | `/admin/submit_claim` | Inject a claim directly (analyst dictation, bypasses LLM) |
| `POST` | `/admin/add_topic` | Register new topic tag (`{tag, display_name?, description?}`) |
| `POST` | `/admin/add_source` | Register new RSS source |
| `POST` | `/admin/x_search` | Direct X/Twitter search and ingest (`{query, topic_tags?, count?}`) |
| `POST` | `/admin/ingest/pause` | Pause scheduled ingestion |
| `POST` | `/admin/ingest/resume` | Resume scheduled ingestion |
| `POST` | `/admin/ingest` | Trigger immediate ingestion pass |
| `GET` | `/admin/swarmfish/status` | SWARMFISH monitor connection status |
| `POST` | `/admin/swarmfish/monitor/toggle` | Enable / disable SWARMFISH autonomous monitor |
| `POST` | `/admin/swarmfish/monitor/run_now` | Force immediate SWARMFISH monitor cycle |

---

## Trust Lifecycle

Claims move through trust levels:

```
STAGED → PROMOTED       (analyst review, or auto-promotion tier rules)
STAGED → IRRELEVANT     (analyst marks not relevant)
PROMOTED → FALSIFIED    (evidence shows claim was false)
PROMOTED → RETURNED_TO_STAGED   (re-review needed)
```

**Auto-promotion tier rules** (run after each ingestion pass):

| Source type | Requires topic tags | Confidence factor |
|-------------|--------------------|--------------------|
| `wire`, `official` | No | 1.0× source confidence |
| `outlet` | Yes | 0.9× source confidence |
| `independent`, `social` | Yes | 0.75× source confidence |

---

## Hypothesis Registry

Implements Chamberlin's method of multiple competing hypotheses. Multiple candidate explanations can exist for the same `observation_id`. Each generates falsifiable predictions. The survivor (predictions matched reality) is promoted; defeated explanations are preserved with their falsification evidence.

When a hypothesis has a `swarmfish_session_id`, promoting or falsifying it automatically posts an outcome to SWARMFISH so profile calibration updates.

---

## Agent Zero Tools

`tools/oss.py` in the Exocortex repo provides 10 tools:

| Tool | Purpose |
|------|---------|
| `oss_topic` | Query claims for a topic |
| `oss_drift` | Narrative drift detection |
| `oss_dynamics` | Propagation velocity and alert level |
| `oss_hypotheses` | List competing hypotheses |
| `oss_health` | System health report |
| `oss_submit` | Dictate a claim directly to the ledger |
| `oss_list_topics` | List monitored topics |
| `oss_add_topic` | Register a new topic |
| `oss_ingest_pause` | Pause ingestion pipeline |
| `oss_ingest_resume` | Resume ingestion pipeline |

---

## Database

PostgreSQL 16 on port 5433. Schema initialized by `schema.sql`, updated by migrations in `migrations/`. App connects as `oss_app` (non-superuser). Migrations must be run as `oss_admin`.

FAISS index at `/app/data/faiss/claims.index` (persisted to `oss_faiss_data` volume). Used for semantic deduplication and prediction confirmation scoring.

---

## Source Files

| File | Purpose |
|------|---------|
| `app.py` | Flask application, all routes |
| `ingest.py` | RSS ingestion, LLM extraction, auto-promotion, prediction confirmation |
| `hypothesis.py` | Hypothesis registry CRUD |
| `contradict.py` | Contradiction detection across sources |
| `silence.py` | Silence (suppression) scan |
| `activation.py` | Cognitive activation pattern detection |
| `narrative_drift.py` | Framing shift detection |
| `propagation_dynamics.py` | Velocity, acceleration, escape analysis |
| `contamination_cascade.py` | False claim propagation chains |
| `threat_model.py` | MITRE ATT&CK-style technique tracking |
| `retcon_ledger.py` | Retroactive continuity tracking |
| `source_intel.py` | Source network topology |
| `operator_state.py` | Alert state machine |
| `social_ingest.py` | X/Twitter ingestion via cookie auth |
| `audit.py` | Append-only audit trail |
