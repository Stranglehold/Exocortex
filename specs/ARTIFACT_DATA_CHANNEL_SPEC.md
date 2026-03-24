# ARTIFACT_DATA_CHANNEL_SPEC.md
# Artifact Data Channel: Architecture, Protocol, and Test Methodology

*Specification for live data in Exocortex artifacts. Covers: postMessage data channel protocol, two-tier polling architecture, artifact manifest standard, and test methodology for verifying data accuracy and freshness.*

---

## 1. The Problem

Artifacts are rendered in `srcdoc` iframes. The `srcdoc` origin is `about:srcdoc` — direct `fetch` calls from artifact JavaScript to Agent Zero API endpoints fail due to same-origin policy. The only communication channel is `postMessage` to the parent window.

This makes artifacts functionally static at present. An artifact showing OSS claim counts or a network graph has no mechanism to update when the underlying data changes. For artifacts acting as live data screens or operational controls, this is a correctness failure: the artifact shows stale data and the analyst does not know it.

This spec defines:
1. A `postMessage` data channel protocol that turns artifacts into live, data-connected displays
2. A two-tier polling architecture that keeps payload overhead manageable regardless of data volume
3. An artifact manifest standard that formally declares what data an artifact needs
4. A test methodology that verifies data accuracy, update freshness, and interaction correctness

---

## 2. Performance Budget

### 2.1 What Polling Actually Costs

The `setInterval` and `postMessage` overhead is negligible — nanoseconds. The cost lives entirely in:

| Factor | Cost driver |
|--------|------------|
| **Payload size** | Bytes transferred + JSON parse time |
| **Backend query cost** | Database/FAISS query on each poll |
| **Render cost** | DOM diffing or full re-render in the artifact |
| **Poll frequency** | Multiplies all of the above |

### 2.2 Payload Tiers

| Data type | Typical payload | Acceptable poll interval |
|-----------|----------------|--------------------------|
| Status / health check | < 2KB | 5–10 seconds |
| Summary counts + timestamps | < 5KB | 10–15 seconds |
| Claims list (100 items) | 20–50KB | 30–60 seconds |
| Full graph (nodes + edges) | 100–500KB | On-demand only (never poll) |
| Network graph delta | 1–10KB | 10–30 seconds |

### 2.3 The Two-Tier Solution

**Tier 1 — Heartbeat (5–15 second interval):**
A lightweight poll to a `/status` or `/health` endpoint. Returns: entity counts, last-updated timestamps, any pending alerts. Payload < 2KB. The artifact uses this to display live indicators and to detect whether a full data refresh is needed.

**Tier 2 — Data fetch (on change detection or 60s max failsafe):**
The full data fetch. Triggered when Tier 1 indicates new data since the artifact's last full fetch (by comparing `last_updated_at` timestamps). The heavy query runs only when data has actually changed — not on every poll cycle.

```
Tier 1 poll (30s default, target 10s) → detect change?
    ├── No change → update lightweight indicators only
    └── Yes change → trigger Tier 2 fetch → full data update → re-render
```

**Result:** The network graph does not re-fetch 500KB every 30 seconds. It re-fetches only when the OSS ingestor has processed new claims. Between ingestion events, only the 2KB heartbeat runs. Polling can be lowered to 10 seconds for the heartbeat with negligible load because the expensive operation is gated behind a change check.

---

## 3. The postMessage Data Channel Protocol

### 3.1 Message Types

All messages are JSON objects with a required `type` field. The artifact sends messages to `window.parent`. The parent (`artifact-panel.js`) sends messages to `iframe.contentWindow`.

**Artifact → Parent messages:**

```typescript
// Subscribe to a data endpoint with polling
{
  type: 'data-subscribe',
  sub_id: string,           // unique ID for this subscription (artifact-generated UUID)
  endpoint: string,         // Agent Zero API endpoint e.g. '/oss_health'
  params: object,           // query parameters to include
  interval_ms: number,      // polling interval in milliseconds (default: 30000)
  last_seen_at: string|null // ISO timestamp of artifact's last successful fetch
                            // null on first subscribe; enables delta responses
}

// Update subscription parameters (e.g. change interval)
{
  type: 'data-subscribe-update',
  sub_id: string,
  interval_ms?: number,
  params?: object
}

// Cancel a subscription
{
  type: 'data-unsubscribe',
  sub_id: string
}

// One-shot data request (no polling, single fetch)
{
  type: 'data-request',
  req_id: string,
  endpoint: string,
  method: 'GET'|'POST',
  params?: object,
  body?: object
}

// Artifact action (trigger a backend operation)
{
  type: 'data-action',
  action_id: string,
  endpoint: string,
  method: 'POST',
  body: object
}

// Artifact is ready to receive data (sent on artifact load)
{
  type: 'artifact-ready',
  artifact_id: string       // matches the name field from artifacts_get
}
```

**Parent → Artifact messages:**

```typescript
// Subscription data response
{
  type: 'data-response',
  sub_id: string,
  endpoint: string,
  data: object,
  timestamp: string,        // ISO timestamp of this response
  is_delta: boolean,        // true if only changed fields are included
  error: string|null        // non-null if fetch failed
}

// One-shot request response
{
  type: 'data-request-response',
  req_id: string,
  data: object,
  status: number,           // HTTP status code
  error: string|null
}

// Action response
{
  type: 'data-action-response',
  action_id: string,
  data: object,
  status: number,
  error: string|null
}

// Channel status (sent on connect, reconnect, or failure)
{
  type: 'channel-status',
  connected: boolean,
  timestamp: string,
  error: string|null
}
```

### 3.2 Subscription Lifecycle

```
Artifact loads
    ↓
Send artifact-ready {artifact_id}
    ↓
Parent sends channel-status {connected: true}
    ↓
Artifact sends data-subscribe for each endpoint it needs
    ↓
Parent registers subscriptions, starts polling intervals
    ↓
Every interval_ms:
    Parent fetches endpoint with last_seen_at
    Parent sends data-response to artifact iframe
    Artifact updates its display
    Artifact updates its last_seen_at
    ↓
On artifact close / iframe unload:
    Parent receives unload event
    Parent cancels all subscriptions for this artifact
```

### 3.3 Delta Response Convention

When the artifact sends `last_seen_at`, the backend endpoint can return only changes since that timestamp. The response includes `is_delta: true`. The artifact must merge delta data into its existing state rather than replacing it.

Backend endpoints that support delta responses indicate this in their API documentation. Endpoints that do not support deltas always return full data (`is_delta: false`). The artifact must handle both.

**Delta response for OSS claims:**
```json
{
  "is_delta": true,
  "since": "2026-03-21T10:00:00Z",
  "added": [ /* new claims */ ],
  "removed": [ /* claim IDs removed or expired */ ],
  "updated": [ /* claims with changed fields */ ],
  "last_updated_at": "2026-03-21T10:04:37Z"
}
```

### 3.4 Error Handling

The data channel must degrade gracefully:

- **Backend unavailable:** artifact shows a staleness indicator (last-updated timestamp + "Reconnecting..."). Does not crash or show empty state. Retries with exponential backoff (30s → 60s → 120s → cap at 300s).
- **Endpoint not found:** artifact shows "Data source unavailable." Logs the error via `console.error`. Does not retry automatically.
- **Malformed response:** artifact keeps its last good state. Logs the parsing error.
- **Stale data threshold:** if no successful data response within `stale_threshold_ms` (configurable per artifact, default 90 seconds), artifact shows a staleness warning banner.

---

## 4. Parent-Side Implementation: `artifact-panel.js` Extensions

The subscription manager runs in `artifact-panel.js`. It maintains a registry of active subscriptions and manages polling intervals.

```javascript
class ArtifactDataChannel {
  constructor(iframe, fetchApi) {
    this.iframe = iframe;
    this.fetchApi = fetchApi;           // the existing fetchApi from api.js
    this.subscriptions = new Map();     // sub_id → subscription state
    this.setupMessageListener();
  }

  setupMessageListener() {
    window.addEventListener('message', (e) => {
      if (!e.data?.type) return;
      switch (e.data.type) {
        case 'artifact-ready':    this.onArtifactReady(e.data); break;
        case 'data-subscribe':    this.onSubscribe(e.data); break;
        case 'data-subscribe-update': this.onSubscribeUpdate(e.data); break;
        case 'data-unsubscribe':  this.onUnsubscribe(e.data); break;
        case 'data-request':      this.onRequest(e.data); break;
        case 'data-action':       this.onAction(e.data); break;
      }
    });
  }

  onSubscribe({ sub_id, endpoint, params, interval_ms, last_seen_at }) {
    // Cancel any existing subscription with same sub_id
    this.onUnsubscribe({ sub_id });

    const state = {
      sub_id, endpoint, params,
      interval_ms: interval_ms ?? 30000,
      last_seen_at: last_seen_at ?? null,
      timer: null, retry_count: 0
    };

    // Immediate first fetch
    this.fetchAndSend(state);

    // Schedule polling
    state.timer = setInterval(() => this.fetchAndSend(state), state.interval_ms);
    this.subscriptions.set(sub_id, state);
  }

  async fetchAndSend(state) {
    const { sub_id, endpoint, params, last_seen_at } = state;
    const query = { ...params };
    if (last_seen_at) query.since = last_seen_at;

    try {
      const resp = await this.fetchApi(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(query)
      });
      const data = await resp.json();
      const timestamp = new Date().toISOString();

      // Update last_seen_at from response if present
      if (data.last_updated_at) state.last_seen_at = data.last_updated_at;
      state.retry_count = 0;

      this.send({ type: 'data-response', sub_id, endpoint, data, timestamp,
                  is_delta: data.is_delta ?? false, error: null });
    } catch (err) {
      state.retry_count++;
      this.send({ type: 'data-response', sub_id, endpoint, data: null,
                  timestamp: new Date().toISOString(), is_delta: false,
                  error: err.message });
    }
  }

  onUnsubscribe({ sub_id }) {
    const state = this.subscriptions.get(sub_id);
    if (state?.timer) clearInterval(state.timer);
    this.subscriptions.delete(sub_id);
  }

  send(message) {
    this.iframe?.contentWindow?.postMessage(message, '*');
  }

  destroy() {
    for (const state of this.subscriptions.values()) {
      if (state.timer) clearInterval(state.timer);
    }
    this.subscriptions.clear();
  }
}
```

---

## 5. Artifact-Side Pattern

Every data-connected artifact implements a minimal data client:

```javascript
// artifact-data-client.js — include in each artifact
class ArtifactDataClient {
  constructor(artifactId) {
    this.artifactId = artifactId;
    this.subscriptions = new Map(); // sub_id → callback
    this.requests = new Map();      // req_id → {resolve, reject}
    this.actions = new Map();       // action_id → {resolve, reject}

    window.addEventListener('message', (e) => this._onMessage(e));
    parent.postMessage({ type: 'artifact-ready', artifact_id: artifactId }, '*');
  }

  subscribe(endpoint, callback, options = {}) {
    const sub_id = crypto.randomUUID();
    this.subscriptions.set(sub_id, callback);
    parent.postMessage({
      type: 'data-subscribe',
      sub_id,
      endpoint,
      params: options.params ?? {},
      interval_ms: options.interval_ms ?? 30000,
      last_seen_at: options.last_seen_at ?? null
    }, '*');
    return sub_id; // caller can use this to unsubscribe
  }

  unsubscribe(sub_id) {
    this.subscriptions.delete(sub_id);
    parent.postMessage({ type: 'data-unsubscribe', sub_id }, '*');
  }

  request(endpoint, body = {}) {
    return new Promise((resolve, reject) => {
      const req_id = crypto.randomUUID();
      this.requests.set(req_id, { resolve, reject });
      parent.postMessage({
        type: 'data-request', req_id, endpoint, method: 'POST', body
      }, '*');
    });
  }

  action(endpoint, body = {}) {
    return new Promise((resolve, reject) => {
      const action_id = crypto.randomUUID();
      this.actions.set(action_id, { resolve, reject });
      parent.postMessage({
        type: 'data-action', action_id, endpoint, method: 'POST', body
      }, '*');
    });
  }

  _onMessage({ data }) {
    if (!data?.type) return;
    if (data.type === 'data-response') {
      const cb = this.subscriptions.get(data.sub_id);
      if (cb) cb(data.data, data.error, data.timestamp);
    } else if (data.type === 'data-request-response') {
      const { resolve, reject } = this.requests.get(data.req_id) ?? {};
      this.requests.delete(data.req_id);
      data.error ? reject(new Error(data.error)) : resolve(data.data);
    } else if (data.type === 'data-action-response') {
      const { resolve, reject } = this.actions.get(data.action_id) ?? {};
      this.actions.delete(data.action_id);
      data.error ? reject(new Error(data.error)) : resolve(data.data);
    }
  }
}
```

**Usage in an artifact:**
```javascript
const client = new ArtifactDataClient('oss-dashboard');

// Two-tier polling: fast heartbeat, slow full data
client.subscribe('/oss_health', (data, err) => {
  if (err) { showStalenessWarning(); return; }
  updateIndicators(data);
}, { interval_ms: 10000 }); // 10s heartbeat

client.subscribe('/oss_claims_summary', (data, err) => {
  if (err || !data) return;
  renderClaimsSummary(data);
}, { interval_ms: 30000 }); // 30s data poll
```

---

## 6. Artifact Manifest Standard

Each artifact directory contains a `manifest.json` declaring its data requirements and DOM assertions for testing.

```json
{
  "artifact_id": "oss-dashboard",
  "title": "OSS Intelligence Dashboard",
  "version": "1.0.0",
  "subscriptions": [
    {
      "sub_id": "heartbeat",
      "endpoint": "/oss_health",
      "interval_ms": 10000,
      "tier": 1,
      "description": "Lightweight health check and change detection"
    },
    {
      "sub_id": "claims-summary",
      "endpoint": "/oss_claims_summary",
      "interval_ms": 30000,
      "tier": 2,
      "description": "Full claims summary with counts by topic and confidence"
    }
  ],
  "stale_threshold_ms": 90000,
  "dom_assertions": [
    {
      "description": "Claim count displays a number",
      "selector": "#claim-count",
      "assert": "text_matches_pattern",
      "pattern": "^\\d+$"
    },
    {
      "description": "Last updated timestamp is present",
      "selector": "#last-updated",
      "assert": "text_not_empty"
    },
    {
      "description": "Staleness warning hidden when data is fresh",
      "selector": "#stale-warning",
      "assert": "hidden"
    },
    {
      "description": "Topic list has at least one item",
      "selector": ".topic-row",
      "assert": "count_gte",
      "value": 1
    }
  ],
  "data_assertions": [
    {
      "description": "Claim count in DOM matches backend count",
      "selector": "#claim-count",
      "source_endpoint": "/oss_health",
      "source_field": "claim_count",
      "transform": "toString"
    }
  ],
  "interaction_tests": [
    {
      "description": "Clicking pause button sends pause action",
      "trigger_selector": "#pause-ingestion-btn",
      "trigger_event": "click",
      "expected_action": {
        "endpoint": "/oss_ingest_pause",
        "method": "POST"
      }
    }
  ]
}
```

---

## 7. Test Methodology

### 7.1 Three Test Layers

**Layer 1 — Contract Tests (no browser, fast)**
Verify that the backend endpoints an artifact depends on:
- Exist and return HTTP 200
- Return the schema the artifact expects (all required fields present, correct types)
- Support the `since` parameter for delta responses
- Return deltas that contain only changes

Run time: < 5 seconds. Run on every deploy.

**Layer 2 — Rendering Tests (Playwright, against live container)**
Verify that the artifact:
- Renders correctly with known data
- Displays the correct values in the correct DOM elements
- Shows staleness warning when data is withheld
- Handles error responses gracefully (no crash, shows error state)

Run time: 30–60 seconds per artifact. Run on deploy and on-demand.

**Layer 3 — Freshness Tests (Playwright, with data mutation)**
Verify that the artifact:
- Reflects data changes within `interval_ms + render_budget_ms` (default: 35 seconds)
- Correctly handles delta responses (adds new items, removes expired ones)
- Does not show stale data after the stale threshold

Run time: 60–120 seconds per artifact (must wait for polling cycle). Run on-demand and pre-release.

### 7.2 Test Fixtures

Test fixtures are known data states stored as JSON files alongside the tests. Each fixture is a valid API response from one or more endpoints.

```
tests/
  fixtures/
    oss_health_baseline.json      # healthy state with known counts
    oss_health_updated.json       # state after 5 new claims ingested
    oss_health_error.json         # error response
    oss_claims_summary_empty.json # zero claims (edge case)
    oss_claims_summary_large.json # 500+ claims (stress case)
```

The test runner can either:
- **Mock mode:** intercept API calls and return fixture data directly (fast, no OSS service needed)
- **Live mode:** seed actual data into the running OSS service and test against real responses (slower, higher confidence)

Both modes run the same test assertions. Mock mode is default for CI; live mode runs pre-release.

### 7.3 Test Runner Implementation

The test runner uses Playwright. It drives the actual Agent Zero webui running in the container.

```python
# tests/test_artifact_data.py
import pytest
import json
import time
from pathlib import Path
from playwright.sync_api import Page, expect

CONTAINER_PORT = None  # resolved at test start from docker port flamboyant_bell
FIXTURES = Path(__file__).parent / "fixtures"

class ArtifactTester:
    def __init__(self, page: Page, artifact_name: str):
        self.page = page
        self.artifact_name = artifact_name
        self.manifest = self._load_manifest(artifact_name)

    def _load_manifest(self, name):
        manifest_path = Path(f"patches/artifacts/{name}/manifest.json")
        return json.loads(manifest_path.read_text())

    def open_artifact(self):
        """Navigate to the webui and open the named artifact."""
        self.page.goto(f"http://localhost:{CONTAINER_PORT}")
        # Click artifacts sidebar section
        self.page.click("[data-section='artifacts']")
        # Click the artifact card
        self.page.click(f"[data-artifact='{self.artifact_name}']")
        # Wait for artifact iframe to load
        self.page.wait_for_selector("iframe[data-artifact-loaded='true']")

    def get_iframe(self):
        """Return the artifact iframe frame handle."""
        return self.page.frame_locator("iframe.artifact-frame").first

    def assert_dom(self, assertion):
        """Run a single DOM assertion from the manifest."""
        iframe = self.get_iframe()
        locator = iframe.locator(assertion["selector"])

        if assertion["assert"] == "text_matches_pattern":
            expect(locator).to_have_text(re.compile(assertion["pattern"]))
        elif assertion["assert"] == "text_not_empty":
            expect(locator).not_to_be_empty()
        elif assertion["assert"] == "hidden":
            expect(locator).to_be_hidden()
        elif assertion["assert"] == "count_gte":
            assert locator.count() >= assertion["value"]

    def assert_data_binding(self, assertion, api_response):
        """Verify that a DOM element value matches the corresponding API field."""
        iframe = self.get_iframe()
        field_value = api_response[assertion["source_field"]]
        if assertion.get("transform") == "toString":
            field_value = str(field_value)
        locator = iframe.locator(assertion["selector"])
        expect(locator).to_have_text(field_value)

    def wait_for_poll_cycle(self, sub_id=None):
        """Wait for one full polling cycle to complete."""
        interval = 30000  # default
        if sub_id:
            sub = next((s for s in self.manifest["subscriptions"]
                       if s["sub_id"] == sub_id), None)
            if sub:
                interval = sub["interval_ms"]
        # Wait interval + 5s render budget
        time.sleep((interval / 1000) + 5)


class TestOSSDashboard:
    def test_renders_with_data(self, page: Page):
        tester = ArtifactTester(page, "oss-dashboard")
        tester.open_artifact()

        for assertion in tester.manifest["dom_assertions"]:
            tester.assert_dom(assertion)

    def test_claim_count_matches_backend(self, page: Page):
        tester = ArtifactTester(page, "oss-dashboard")
        tester.open_artifact()

        # Get actual backend state
        resp = requests.post(f"http://localhost:{CONTAINER_PORT}/oss_health")
        api_data = resp.json()

        for assertion in tester.manifest["data_assertions"]:
            tester.assert_data_binding(assertion, api_data)

    def test_updates_after_new_claims(self, page: Page):
        tester = ArtifactTester(page, "oss-dashboard")
        tester.open_artifact()

        # Record current count
        iframe = tester.get_iframe()
        initial_count = int(iframe.locator("#claim-count").text_content())

        # Seed a new claim via oss_submit
        requests.post(
            f"http://localhost:{CONTAINER_PORT}/oss_submit",
            json={"text": "TEST CLAIM: automated freshness test", "topic": "iran-hormuz"},
            headers={"X-API-KEY": get_api_key()}
        )

        # Wait for the claims-summary poll cycle
        tester.wait_for_poll_cycle("claims-summary")

        # Assert count increased
        updated_count = int(iframe.locator("#claim-count").text_content())
        assert updated_count > initial_count, \
            f"Claim count did not increase after seeding: was {initial_count}, still {updated_count}"

    def test_shows_staleness_warning_when_backend_unreachable(self, page: Page):
        """Verified by intercepting network requests and returning errors."""
        page.route("**/oss_health", lambda route: route.abort())
        page.route("**/oss_claims_summary", lambda route: route.abort())

        tester = ArtifactTester(page, "oss-dashboard")
        tester.open_artifact()

        # Wait for stale threshold
        stale_threshold = tester.manifest["stale_threshold_ms"] / 1000
        time.sleep(stale_threshold + 5)

        iframe = tester.get_iframe()
        expect(iframe.locator("#stale-warning")).to_be_visible()

    def test_pause_button_calls_correct_endpoint(self, page: Page):
        """Verify that control actions trigger correct backend calls."""
        api_calls = []
        page.on("request", lambda req: api_calls.append(req.url)
                if "oss_ingest_pause" in req.url else None)

        tester = ArtifactTester(page, "oss-dashboard")
        tester.open_artifact()
        tester.get_iframe().locator("#pause-ingestion-btn").click()

        # Give time for the postMessage round-trip
        page.wait_for_timeout(2000)
        assert any("oss_ingest_pause" in url for url in api_calls), \
            "Pause button did not trigger /oss_ingest_pause API call"
```

### 7.4 Contract Tests (Layer 1, Fast)

```python
# tests/test_artifact_contracts.py
import json
import pytest
import requests
from pathlib import Path

def load_all_manifests():
    manifest_paths = Path("patches/artifacts").rglob("manifest.json")
    return [json.loads(p.read_text()) for p in manifest_paths]

@pytest.mark.parametrize("manifest", load_all_manifests(),
                         ids=lambda m: m["artifact_id"])
class TestArtifactContracts:
    def test_all_endpoints_reachable(self, manifest):
        for sub in manifest["subscriptions"]:
            resp = requests.post(
                f"http://localhost:{CONTAINER_PORT}{sub['endpoint']}",
                json={}
            )
            assert resp.status_code == 200, \
                f"Endpoint {sub['endpoint']} returned {resp.status_code}"

    def test_all_endpoints_return_json(self, manifest):
        for sub in manifest["subscriptions"]:
            resp = requests.post(
                f"http://localhost:{CONTAINER_PORT}{sub['endpoint']}",
                json={}
            )
            try:
                resp.json()
            except Exception as e:
                pytest.fail(f"Endpoint {sub['endpoint']} returned non-JSON: {e}")

    def test_data_assertion_fields_exist_in_response(self, manifest):
        for assertion in manifest.get("data_assertions", []):
            resp = requests.post(
                f"http://localhost:{CONTAINER_PORT}{assertion['source_endpoint']}",
                json={}
            )
            data = resp.json()
            assert assertion["source_field"] in data, \
                f"Field '{assertion['source_field']}' missing from {assertion['source_endpoint']} response"

    def test_delta_support_when_declared(self, manifest):
        for sub in manifest["subscriptions"]:
            if not sub.get("supports_delta"):
                continue
            resp = requests.post(
                f"http://localhost:{CONTAINER_PORT}{sub['endpoint']}",
                json={"since": "2026-01-01T00:00:00Z"}
            )
            data = resp.json()
            assert "is_delta" in data, \
                f"Endpoint {sub['endpoint']} declares delta support but response missing 'is_delta' field"
            assert "last_updated_at" in data, \
                f"Endpoint {sub['endpoint']} declares delta support but response missing 'last_updated_at' field"
```

### 7.5 Running the Tests

```bash
# Layer 1 — contract tests (fast, run always)
cd /a0/usr/Exocortex
C:/Users/Jake/miniconda3/python.exe -m pytest tests/test_artifact_contracts.py -v

# Layer 2 — rendering tests (requires running webui)
C:/Users/Jake/miniconda3/python.exe -m pytest tests/test_artifact_data.py::TestOSSDashboard::test_renders_with_data -v

# Layer 3 — freshness tests (slow, run before release)
C:/Users/Jake/miniconda3/python.exe -m pytest tests/test_artifact_data.py -v -k "freshness or stale or updates"

# Full suite
C:/Users/Jake/miniconda3/python.exe -m pytest tests/ -v --timeout=180
```

### 7.6 Pass / Fail Criteria

| Test type | Pass condition | Fail condition |
|-----------|---------------|----------------|
| Contract | All declared endpoints return 200 + JSON with declared fields | Any endpoint missing, non-200, or missing field |
| Rendering | All manifest DOM assertions satisfied after artifact load | Any selector not found, wrong text, wrong visibility |
| Data binding | DOM values match backend response values | Mismatch between display value and API value |
| Freshness | DOM value updates within `interval_ms + 5000ms` after data change | No update within timeout |
| Staleness | Staleness warning visible after `stale_threshold_ms` | Warning not shown, or shown too early |
| Interaction | Expected API call made within 2000ms of trigger event | No API call, wrong endpoint, wrong method |

---

## 8. What This Does NOT Cover

- This spec does not define the implementation of delta-aware API endpoints on the OSS or Agent Zero side — those are the responsibility of the respective service specs.
- This spec does not cover artifacts that are purely generative (reports, static analysis output) — those do not need a live data channel and are tested differently (output correctness, not data freshness).
- This spec does not cover authentication within the iframe — the postMessage bridge inherits the Agent Zero session that the parent window has established.
- This spec does not define CI/CD integration — that depends on the deployment pipeline that doesn't yet exist. The tests are written to run manually or from a shell script.

---

## 9. Implementation Sequence

| Step | What | Dependency |
|------|------|-----------|
| 1 | Add `ArtifactDataChannel` class to `artifact-panel.js` | None |
| 2 | Create `artifact-data-client.js` shared library | Step 1 |
| 3 | Add `manifest.json` to `oss-dashboard` artifact (first test subject) | None |
| 4 | Update `oss-dashboard` to use data client | Steps 2, 3 |
| 5 | Run Layer 1 contract tests against current endpoints | None |
| 6 | Run Layer 2 rendering tests against updated dashboard | Steps 1–4 |
| 7 | Run Layer 3 freshness tests | Steps 1–6 |
| 8 | Extend pattern to `network_graph` artifact | Steps 1–2 |
| 9 | Tune polling intervals based on measured overhead | Steps 1–7 |

Step 9 is where "30 seconds → as low as we can go" gets its empirical answer. After the full test suite runs, the measured overhead of each endpoint determines the minimum interval that keeps the system comfortable.

---

*Research conducted March 2026. See also: WEBUI_DESIGN_BRIEF.md, AESTHETICS_DESIGN_BRIEF.md, INFORMATION_ENVIRONMENTS_DESIGN_BRIEF.md.*
