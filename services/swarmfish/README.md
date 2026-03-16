# SWARMFISH — Analytic Consensus Protocol

Prediction ensemble with calibration. Eight deep analytical frameworks each grounded in a different theory of how systems work — assess questions independently, disagree on the record, and get scored against outcomes. Profile weights adjust over time toward whoever has the better track record.

**Port:** 7732 · **Postgres:** 5435 · **Redis:** 6380 · **Container:** `swarmfish_app`

---

## The Eight Profiles

Each profile is structured around a real practitioner's methodology, not a shallow persona.

| Profile | Practitioner lineage | Methodology |
|---------|---------------------|-------------|
| **Base Rate Analyst** | Tetlock / Silver | Historical base rates, reference class forecasting, calibrated confidence intervals |
| **Contrarian** | Burry / Druckenmiller | Structural mispricing, crowd error identification, non-consensus positioning |
| **Historian** | Dalio / Allison | Analogical reasoning from historical precedent, dual similarity scoring, long-cycle dynamics |
| **Reflexivity Modeler** | Soros | Feedback loops between perception and reality; self-reinforcing vs. self-correcting dynamics |
| **Decomposer** | Fermi / Sherman Kent | Component-by-component estimation; breaks opaque judgments into independently estimable sub-questions |
| **Network Analyst** | Minsky / Kindleberger | Hidden leverage chains, second-order contagion, transmission channel mapping |
| **Sentiment Decoder** | Howard Marks / Shiller | Narrative-reality gap, pendulum model, crowd psychology positioning |
| **Risk Manager** | Taleb / Derman | Distribution shape, fat tails, Knightian uncertainty, model skepticism |

Profiles assess independently, then a consensus is aggregated. A profile is flagged as a **dissenter** when its confidence deviates more than 20 percentage points from consensus — that's signal, not noise.

Profile weights are updated via Brier scoring after each recorded outcome. The ensemble's track record is visible at `/acp/status`.

---

## Setup

```bash
cd services/swarmfish

# First run — initialize schema
./install.sh

# Start containers
docker compose up -d
```

**Dependencies:** Docker, Docker Compose. LM Studio running on host with a compatible model. OSS running on port 7731 (optional — used for context injection).

---

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `SWARMFISH_DB_URL` | `postgresql://swarmfish:...@postgres:5432/swarmfish` | Database connection |
| `SWARMFISH_LLM_URL` | `http://host.docker.internal:1234/v1` | LM Studio API endpoint |
| `SWARMFISH_LLM_MODEL` | _(model name)_ | Model for profile reasoning |
| `SWARMFISH_ANALYST_TOKEN` | `dev_analyst_token` | Auth token for all endpoints |
| `OSS_BASE_URL` | `http://host.docker.internal:7731` | OSS service for context injection |
| `OSS_ANALYST_TOKEN` | `dev_analyst_token` | OSS auth |
| `SWARMFISH_MONITOR_ENABLED` | `false` | Enable autonomous hypothesis generation loop |
| `SWARMFISH_MONITOR_INTERVAL_MINUTES` | `30` | How often the monitor cycle runs |
| `SWARMFISH_MONITOR_MIN_CLAIMS` | `1` | Minimum new promoted claims to trigger a cycle |

---

## API Reference

All endpoints require: `X-Analyst-Token: <token>`

### Prediction

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/acp/predict` | Run a question through the ensemble. Returns operator brief, per-profile breakdown, consensus, falsification checklist, and `session_id`. |
| `POST` | `/acp/predict/stream` | Same, but streams SSE events as each profile completes. Events: `session_created`, `profiles_loaded`, `profile_start`, `profile_done`, `done`. |

**Request body** (`/acp/predict`):
```json
{
  "question":      "string (required)",
  "domain":        "geopolitical_risk | economic | military | general",
  "context":       "optional operator-supplied data",
  "profile_names": ["optional", "subset", "of", "profiles"]
}
```

**Response** includes:
- `session_id` — reference for outcome feedback
- `operator_brief` — synthesized assessment for analyst consumption
- `consensus.consensus_confidence` — ensemble confidence (0.0–1.0)
- `individual_predictions` — per-profile with `confidence`, `rationale`, `key_factors`
- `falsification_checklist` — conditions that would invalidate the assessment

### Outcomes and Calibration

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/acp/outcome` | Record what actually happened and score the prediction |
| `GET` | `/acp/status` | Calibration summary + last 20 sessions |
| `GET` | `/acp/profiles` | All profiles with current calibration weights |
| `GET` | `/acp/session/<id>` | Full session detail including all profile outputs |

**Outcome body:**
```json
{
  "session_id":         "uuid (score all predictions in session)",
  "outcome":            "what actually happened",
  "was_correct":        true,
  "conditions_held":    ["optional list"],
  "conditions_failed":  ["optional list"],
  "post_mortem_note":   "optional"
}
```

Outcomes are posted automatically by OSS when an analyst promotes or falsifies a hypothesis that has a `swarmfish_session_id`. Manual outcome recording is also supported.

### Monitor

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/monitor/status` | Monitor state: active, running, interval, last run stats |
| `POST` | `/monitor/toggle` | Enable / disable the monitor at runtime (no restart needed) |
| `POST` | `/monitor/run_now` | Trigger one monitor cycle immediately in a background thread |

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | `{status, profiles}` — number of seeded profiles |

---

## Autonomous Monitor

When `SWARMFISH_MONITOR_ENABLED=true`, a background thread runs on `SWARMFISH_MONITOR_INTERVAL_MINUTES` cadence:

1. Fetch active topics from OSS `/api/topics`
2. For each topic, fetch promoted claims newer than `last_checked`
3. If new claim count ≥ `SWARMFISH_MONITOR_MIN_CLAIMS`:
   - Build a prediction question from the claim batch
   - Call `/acp/predict` internally
   - Extract falsification checklist and per-profile confidences
   - Flag dissenters (confidence deviation > 20% from consensus)
   - POST resulting hypothesis to OSS `/api/hypothesis/from_swarmfish`
4. Persist `last_checked` per topic to `/app/data/monitor_state.json`

The monitor can be toggled live via the OSS web UI (header buttons) or via `/monitor/toggle`. Current cycle state and last run stats are visible in `/monitor/status`.

---

## OSS Context Injection

Every `/acp/predict` call automatically queries OSS for relevant promoted claims and prepends them as context before the profiles reason. This grounds predictions in current evidence from the ledger rather than relying on the model's training data.

The bridge is in `oss_bridge.py` and queries `OSS_BASE_URL/api/feed` with the question domain as a filter. Context injection is silent — it does not change the API contract.

---

## Calibration Loop

The full feedback loop:

```
OSS auto-promotes claims
    ↓
Monitor detects new signal
    ↓
SWARMFISH runs ensemble prediction
    ↓
Hypothesis posted to OSS with session_id
    ↓
Analyst promotes or falsifies hypothesis
    ↓
OSS posts outcome to SWARMFISH /acp/outcome
    ↓
Brier scores computed, profile weights updated
```

Profiles that consistently overestimate or underestimate have their `consensus_weight` adjusted down. The ensemble self-corrects over time.

---

## Agent Zero Tools

`tools/swarmfish.py` in the Exocortex repo provides 2 tools:

| Tool | Purpose |
|------|---------|
| `swarmfish_predict` | Run a question through the ensemble. Returns operator brief, per-profile breakdown with dissenter flags, and falsification conditions. Timeout: 300s. |
| `swarmfish_calibration` | Profile calibration weights, Brier scores, and recent session history. |

---

## Source Files

| File | Purpose |
|------|---------|
| `app.py` | Flask application, all routes, startup seeding |
| `config.py` | Environment variable loading |
| `monitor.py` | Autonomous OSS polling and hypothesis generation loop |
| `oss_bridge.py` | Client for OSS context injection |
| `acp/profiles.py` | Profile definitions and DB seeding |
| `acp/predictor.py` | Per-profile LLM calls |
| `acp/aggregator.py` | Multi-profile consensus synthesis and operator brief generation |
| `acp/tracker.py` | Outcome recording, Brier scoring, weight updates |
| `acp/constraints.py` | Behavioral guardrails for profile outputs |
