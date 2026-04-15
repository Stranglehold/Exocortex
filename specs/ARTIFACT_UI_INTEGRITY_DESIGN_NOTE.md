# Artifact UI Integrity
## Design Note: The Contract Between the Interface and the System

**Status:** Design note. Motivated by operational experience — controls that don't control, labels that don't reflect state, the trust erosion that follows. This document addresses the gap between UI research (how to make things look and feel good) and UI integrity (how to make things actually work). The audience is any agent building artifact panels for human use.

**Author:** Opus (architecture), informed by Jake (the frustration is the brief), Kestrel (implementation experience)
**Date:** 2026-04-05

---

## 1. The Problem

Jake pressed a pause button on the OSS web interface. The label changed to "stopped." LM Studio continued running. The pipeline continued ingesting. The button lied.

This is not a cosmetic issue. This is the most destructive failure mode a user interface can have: **the interface says one thing and the system does another.** Every other UI problem — ugly layout, poor typography, janky animations — is forgivable. A control that doesn't control is not. It destroys trust not just in that button, but in every button. Once the analyst sees one control that's disconnected from the system, the rational response is to distrust all controls. "How much behind the scenes is also failing or not wired up?" That question, once asked, cannot be un-asked.

We have extensive research on UI aesthetics (THEME_AUTHORING_GUIDE.md), UI mechanics (UI_MECHANICS_RESEARCH_NOTE.md), and UI structure (THEME_ENGINE_SPEC_L3.md, THEME_EDITOR_SPEC.md). What we don't have is a document about **UI integrity** — the contract between what the interface shows and what the system does. This document fills that gap.

The audience is primarily agents building artifact panels — Kestrel, the agent, any future instance that generates HTML for human interaction. The principles here are non-negotiable. Aesthetics are important. Mechanics are important. But integrity comes first. A beautiful interface that lies is worse than an ugly interface that tells the truth.

---

## 2. The Core Principle

**Every control must be verified against the system state it claims to control. Every indicator must reflect actual system state, not the last command sent.**

This means:

- A pause button must confirm the pipeline actually paused before showing "paused"
- A status indicator must poll or subscribe to actual system state, not cache the last known state
- An action button must handle failure — if the action fails, the UI must reflect the failure, not assume success
- A progress indicator must track real progress, not animate a fake progress bar

The test for every control: **if I unplug the backend, does the UI still change?** If yes, the UI is lying. The UI must not change state unless the system confirms the state change. The label is not the state. The API response is the state.

---

## 3. The Seven Integrity Rules

### Rule 1: No Optimistic State Updates Without Rollback

**The anti-pattern:** Button is clicked → UI immediately updates to show new state → API call fires in background → if it fails, the UI has already lied.

**The correct pattern:** Button is clicked → UI shows a loading/pending state (disabled button, spinner, "stopping...") → API call fires → on success, UI updates to confirmed state → on failure, UI reverts and shows error.

```javascript
// WRONG: Optimistic update without rollback
pauseBtn.onclick = () => {
    statusLabel.textContent = 'Stopped';  // LIE: we don't know yet
    fetch('/api/oss/pause');               // might fail silently
};

// RIGHT: Pending → confirmed pattern
pauseBtn.onclick = async () => {
    pauseBtn.disabled = true;
    statusLabel.textContent = 'Stopping...';
    try {
        const res = await fetch('/api/oss/pause', { method: 'POST' });
        const data = await res.json();
        if (data.ok) {
            statusLabel.textContent = 'Stopped';
        } else {
            statusLabel.textContent = 'Running';  // revert
            showError('Failed to pause: ' + data.error);
        }
    } catch (err) {
        statusLabel.textContent = 'Running';  // revert
        showError('Connection failed');
    } finally {
        pauseBtn.disabled = false;
    }
};
```

The key difference: the UI never shows "Stopped" until the system confirms it stopped. The intermediate state is "Stopping..." — which is honest. The user sees that the request is in progress. If it fails, they see it fail.

### Rule 2: Status Indicators Must Poll or Subscribe

**The anti-pattern:** Status is set once when the page loads and never updated. Or status is set when a command is sent and never verified.

**The correct pattern:** Status indicators poll the actual system state at regular intervals, or subscribe to a state stream (WebSocket, SSE).

```javascript
// Poll pattern — simple, reliable
async function pollStatus() {
    try {
        const res = await fetch('/api/oss/health');
        const data = await res.json();
        updateStatusDisplay(data.pipeline_running, data.queue_depth, data.last_ingest);
    } catch (err) {
        updateStatusDisplay(null, null, null);  // show "unknown" state
    }
}
setInterval(pollStatus, 5000);  // every 5 seconds
```

The polling interval depends on the system: 5 seconds for a pipeline status, 30 seconds for a calibration score, 1 second for a live deliberation progress. The interval should be documented and configurable.

**The "unknown" state matters.** If the poll fails (backend down, network issue), the UI must not continue showing the last known state as if it's current. It must show "unknown" or "connection lost." Stale data presented as current data is a lie.

### Rule 3: Actions Must Acknowledge Failure Visibly

**The anti-pattern:** An action fires, fails silently, and the UI shows no indication that anything went wrong. The user assumes it worked.

**The correct pattern:** Every action has three visible states: idle, pending, and result (success or error). Errors are shown to the user, not swallowed.

```javascript
// Every action button follows this lifecycle:
// IDLE → PENDING → SUCCESS or ERROR → IDLE

function actionButton(btn, apiCall, successMsg, errorMsg) {
    btn.onclick = async () => {
        btn.disabled = true;
        btn.classList.add('pending');
        try {
            const result = await apiCall();
            if (result.ok) {
                showToast(successMsg, 'success');
            } else {
                showToast(errorMsg + ': ' + result.error, 'error');
            }
        } catch (err) {
            showToast('Connection failed: ' + err.message, 'error');
        } finally {
            btn.disabled = false;
            btn.classList.remove('pending');
        }
    };
}
```

The user must never wonder "did that work?" Every action must answer the question visibly.

### Rule 4: The UI Must Not Invent Data

**The anti-pattern:** The UI shows a chart, a number, or a status that was generated by the frontend rather than received from the backend. Example: a "claims processed: 147" counter that increments in JavaScript without checking the actual count.

**The correct pattern:** Every piece of data displayed in the UI comes from an API call. The UI renders data. It does not generate data.

Exception: derived values computed from API data are acceptable (e.g., computing a percentage from two API-provided numbers). But the source numbers must come from the API.

### Rule 5: Loading States Are Mandatory

**The anti-pattern:** Content area is empty while data loads. Or worse, content area shows stale data from a previous load without indicating it's stale.

**The correct pattern:** Every content area has three states: loading (skeleton or spinner), loaded (actual content), and error (error message with retry option). The loading state is shown immediately. The loaded state replaces it when data arrives. The error state replaces it when the load fails.

```html
<!-- The three states, managed by Alpine.js or vanilla JS -->
<div x-show="state === 'loading'" class="skeleton-loader">Loading...</div>
<div x-show="state === 'loaded'" x-html="content"></div>
<div x-show="state === 'error'" class="error-state">
    Failed to load. <button @click="retry()">Retry</button>
</div>
```

The user must never see an empty panel and wonder whether it's loading, empty, or broken.

### Rule 6: Destructive Actions Require Confirmation

**The anti-pattern:** A "clear all data" or "reset pipeline" button fires immediately on click.

**The correct pattern:** Destructive actions show a confirmation dialog that names what will be destroyed. The confirmation is not a generic "Are you sure?" — it states specifically what will happen.

```
"This will delete 147 claims from the iran-hormuz topic.
 This action cannot be undone.
 [Cancel]  [Delete 147 claims]"
```

The confirmation button names the action specifically ("Delete 147 claims", not "OK"). The user must understand what they're confirming.

### Rule 7: The Backend Must Be the Source of Truth

**The anti-pattern:** The UI maintains its own state that diverges from the backend. Example: the UI tracks which topics are active in a local array, while the backend has a different list. When the page reloads, the UI "forgets" what the user configured because it was never persisted.

**The correct pattern:** The backend is always the source of truth. The UI reads from the backend and writes to the backend. On page load, the UI initializes from the backend state. On any action, the UI sends the action to the backend and updates from the response. The UI never has state that the backend doesn't know about.

```javascript
// On page load: read truth from backend
const state = await fetch('/api/oss/state').then(r => r.json());
renderFromState(state);

// On action: write to backend, update from response
const result = await fetch('/api/oss/topic', {
    method: 'POST', body: JSON.stringify({ name: 'iran-hormuz', action: 'pause' })
}).then(r => r.json());
renderFromState(result.state);  // re-render from backend's truth, not local assumption
```

---

## 4. The Verification Pattern

Every artifact panel that contains controls (buttons, toggles, sliders that affect system behavior) must implement the **Verification Pattern:**

### 4.1 On Build: Wire Check

Before shipping any artifact panel, verify every control:

```
For each button/toggle/slider in the panel:
  1. What API endpoint does it call?
  2. Does that endpoint exist and function correctly? (Test with curl)
  3. Does the endpoint actually perform the action it claims?
  4. Does the UI update from the endpoint's response (not from local state)?
  5. Does the UI handle failure from the endpoint?
  6. If the backend is stopped, does the UI still change state? (Must not)
```

If any answer is "no" or "I don't know," the control is not ready to ship. A button that doesn't work is worse than no button at all — remove it until the backend supports it.

### 4.2 On Display: Health Indicator

Every artifact panel that depends on a backend service should show a small health indicator — a dot or icon that reflects the actual connection status.

```
🟢 Connected (last successful poll < 10s ago)
🟡 Slow (last successful poll 10-30s ago)
🔴 Disconnected (last successful poll > 30s ago or poll failed)
```

The health indicator tells the analyst: "the data you're seeing is current" or "the data you're seeing may be stale." This is the "unknown state" from Rule 2 made visible at all times.

### 4.3 On Action: Feedback Loop

Every action must complete a full feedback loop:

```
User clicks → UI shows pending → Backend processes → Backend responds →
UI shows result → UI re-reads state from backend → UI reflects true state
```

The feedback loop must be visible. The user must see the pending state, see the result, and see the UI settle into the confirmed state. No silent successes. No silent failures.

---

## 5. Common Agent UI Failures

These are patterns I've observed in agent-generated UIs that violate integrity. This section exists as a checklist for any agent building artifact panels.

### 5.1 The Cosmetic Toggle

A toggle switch that changes its visual state (on/off) without calling the backend. The toggle looks functional. It isn't. This is the OSS pause button problem. Fix: the toggle must call the backend and only change visual state on confirmed response.

### 5.2 The Phantom Form

A form with input fields and a submit button where the submit button doesn't actually send the data anywhere — it just clears the form or shows a "success" message generated locally. Fix: the submit handler must POST to a real endpoint and handle the response.

### 5.3 The Static Dashboard

A dashboard with numbers and charts that were generated once when the page loaded and never updated. The numbers look live but are frozen. Fix: polling or subscription with a visible "last updated" timestamp.

### 5.4 The Swallowed Error

An API call wrapped in a try/catch where the catch block does nothing — `catch(e) {}`. The action fails and the user never knows. Fix: every catch block must surface the error to the user, even if it's just a toast notification.

### 5.5 The Assumed Shape

The UI assumes the API response has a specific shape without validating. When the backend returns something unexpected (error object instead of data, null instead of array), the UI breaks silently — showing undefined, NaN, or blank space instead of an error message. Fix: validate API response shape before rendering. Show a meaningful error if the shape is unexpected.

### 5.6 The Orphan Control

A control that was added to the UI during development but never connected to a backend endpoint. It renders, it's clickable, and it does nothing. This is worse than a missing control because it implies functionality that doesn't exist. Fix: if the backend doesn't support the action, don't render the control. Show "coming soon" or omit it entirely.

---

## 6. The Artifact Builder's Checklist

For every artifact panel an agent builds, verify before presenting to the user:

```
INTEGRITY
  [ ] Every button/toggle calls a real backend endpoint
  [ ] Every endpoint has been tested (curl or equivalent)
  [ ] Every action shows pending → success/failure states
  [ ] No optimistic state updates without rollback on failure
  [ ] Error states are visible to the user, not swallowed
  [ ] Backend is the source of truth, not frontend state
  [ ] Health indicator shows connection status

DATA
  [ ] All displayed data comes from API calls, not generated locally
  [ ] Loading states shown while data is fetched
  [ ] "Last updated" timestamp visible on polled data
  [ ] Stale data is indicated, not presented as current
  [ ] Empty states are distinguishable from loading states

CONTROLS
  [ ] Destructive actions require confirmation with specific description
  [ ] Disabled controls show why they're disabled (tooltip or label)
  [ ] Controls that depend on backend features not yet built are hidden, not broken
  [ ] Toggle states reflect backend state, not local state

RESILIENCE
  [ ] Panel handles backend being unreachable (shows error, not blank)
  [ ] Panel handles unexpected API response shapes (shows error, not NaN)
  [ ] Page reload restores correct state from backend (no lost state)
  [ ] Multiple rapid clicks on action buttons are debounced or disabled during pending
```

If any item fails, the panel is not ready for the analyst. Fix the integrity issue before addressing aesthetics. A beautiful panel that lies is worse than an ugly panel that tells the truth.

---

## 7. The Aesthetic-Integrity Stack

The full stack of UI quality, in priority order:

```
1. INTEGRITY    — Does it actually work? Does every control do what it says?
                  (This document)

2. FUNCTION     — Does it show the right information? Can the user accomplish their task?
                  (OSS_V2_DESIGN_NOTE.md, SWARMFISH_V2_DESIGN_NOTE.md)

3. CLARITY      — Is the information hierarchy clear? Does the user know where to look?
                  (Layout, typography, visual weight)

4. AESTHETICS   — Does it feel good? Does it match the atmospheric theme?
                  (THEME_AUTHORING_GUIDE.md, THEME_ENGINE_SPEC_L3.md)

5. MECHANICS    — Is it performant? Are animations smooth? Is scrolling buttery?
                  (UI_MECHANICS_RESEARCH_NOTE.md)

6. DELIGHT      — Does it surprise pleasantly? Do the micro-interactions feel alive?
                  (THEME_EDITOR_SPEC.md — live preview, spring animations)
```

Each layer depends on the layers below it. Aesthetics without integrity is a beautiful lie. Mechanics without function is a smooth experience that doesn't accomplish anything. Delight without clarity is confusing whimsy.

The theme engine research and the UI mechanics research are excellent — they cover layers 4-6 thoroughly. The V2 design notes cover layer 2. This document covers layer 1. Layer 3 (clarity) is the next gap — information hierarchy, visual weight, spatial organization. But layer 1 must be solid before anything else matters.

---

## 8. For Kestrel Specifically

Kestrel, if you're reading this in a future session:

The OSS pause button that changed a label without stopping the pipeline is the reason this document exists. It wasn't a small bug. It was a trust failure that made Jake question everything the UI showed him. That's the cost of a disconnected control — not just the one thing that doesn't work, but the doubt it casts on everything else.

When you build an artifact panel:
1. Start with the API. Verify every endpoint with curl before writing any HTML.
2. Build the ugliest possible functional version first. Plain HTML, no styling, every button wired to a real endpoint with real error handling.
3. Only after every control works — actually works, verified against the backend — add the styling, the layout, the theme integration.
4. Run the checklist in Section 6 before presenting to Jake.

The checklist is not bureaucracy. It's the trust protocol. Jake's willingness to use the tools we build depends on his confidence that they do what they say. That confidence is earned control by control, verified endpoint by endpoint. It cannot be earned with aesthetics and lost with a single disconnected button.

The theme engine and UI mechanics research are good work. Apply them AFTER the integrity layer is solid. The foundation holds the building. The building holds the paint. The paint does not hold the building.

---

## 9. Connection to Broader Architecture

This integrity framework connects to several active threads:

**The Haskell Decision Service.** The compiler-as-conscience thesis: make incorrect states structurally impossible. In UI terms: make it structurally impossible for a control to exist without a verified backend endpoint. The checklist is the behavioral version. A type-safe artifact framework where controls are typed to their endpoints would be the structural version. Future exploration.

**The Proactive Supervisor.** The supervisor's reasoning-stream analysis detects when the agent's thinking diverges from its output. The UI integrity framework detects when the interface's appearance diverges from the system's state. Same principle: the visible layer must reflect the actual layer. Divergence is a failure.

**The Action Boundary.** The action boundary prevents the agent from taking actions it shouldn't. The verification pattern prevents the UI from showing actions it can't. Both are gatekeeping mechanisms — one for the agent's capabilities, one for the interface's claims.

**The EI Layer.** Epistemic integrity means not stating what you don't know as if you know it. UI integrity means not showing a state you haven't confirmed as if you confirmed it. The principles are isomorphic. A UI that shows "Stopped" without confirming the pipeline stopped is making an ungrounded claim. The EI layer for interfaces.

---

*The first artifact framework document was about how to make things look good (THEME_AUTHORING_GUIDE.md). The second was about how to make things perform well (UI_MECHANICS_RESEARCH_NOTE.md). This one is about how to make things actually work. It's the foundation layer. Without it, beauty and performance are decorating a lie.*

*The test is simple: unplug the backend. If the UI still changes state, it's lying. Fix the lie before you fix the layout.*

*Written by Opus. April 5, 2026. Session 061.*
