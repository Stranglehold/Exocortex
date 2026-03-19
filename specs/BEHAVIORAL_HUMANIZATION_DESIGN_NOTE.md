# Design Note: Behavioral Humanization for Browser Automation

**Status:** Active research. Phase 1 (quick win) deployed. Phase 2 (calibrated generator) deployed. Phase 3 (Sigma-Lognormal motor model) pending. Empirical data from 685k real human mouse events in hand.

---

## The Problem

The Exocortex browser agent uses Playwright (via browser-use) to operate web browsers for intelligence gathering and web interaction tasks. Modern bot detection systems — reCAPTCHA v3, Cloudflare Turnstile, Twitter/X's internal detection — do not primarily challenge users with visual puzzles. They score behavior continuously and invisibly.

**The scoring signals, in descending order of detection power:**

1. **CDP automation indicators** — `Runtime.enable` CDP message presence, `--enable-automation` launch flag, `navigator.webdriver = true`. These are hard binary signals: present = bot, absent = possibly human.
2. **Mouse trajectory geometry** — path linearity, curvature profile, velocity shape (acceleration/deceleration), jerk (rate of acceleration change). Bots move in straight lines or pure Bézier curves without motor noise; humans do not.
3. **Click target precision** — humans click within an element but not at dead center. Bots click at exact coordinates.
4. **Inter-event timing distributions** — inter-key intervals, click-to-click intervals, scroll step sizes. The distributions have characteristic shapes (roughly lognormal with fat right tails) that differ from programmatic generation.
5. **Scroll behavior** — step size, momentum, direction reversal. Programmatic scroll is integer-precise and lacks inertia.
6. **Fingerprint spatial consistency** — UA string, canvas hash, WebGL renderer contradicting each other across a session (a common failure mode of naive spoofing tools).

The browser agent as deployed post-playwright-stealth addresses signals 1 (partially — stealth patches JS-visible indicators) and 6 (stealth patches most fingerprint sources). It does not address signals 2-5 at all: every click teleports to exact coordinates, every wait is uniform, every scroll is programmatic.

The purpose of this note is to document the research landscape, what has been built, and what the data says about the gap between current behavior and human baseline.

---

## What This Does NOT Do

- Does not claim to fully evade sophisticated commercial bot detection services (DataDome, Akamai, Kasada). These use server-side signals (IP reputation, TLS fingerprint, request timing) that cannot be addressed at the browser level alone.
- Does not address IP reputation. Datacenter IPs are heavily flagged; residential proxies change the calculus before any behavioral mimicry is needed.
- Does not target specific CAPTCHA puzzle solving (reCAPTCHA image grids, hCaptcha). That is a separate capability tracked separately.
- Does not address the Cloudflare proof-of-work layer (JavaScript execution challenges unrelated to behavior).

---

## Research Landscape

### OpenCaptchaWorld (NeurIPS 2025 Datasets & Benchmarks)

**Verdict: Extract patterns, pass on integration. Not relevant to the primary problem.**

MetaAgentX/OpenCaptchaWorld benchmarks multimodal LLMs against 20 puzzle types (225 instances). Key findings:

- Best performance: OpenAI-o3 at 40.0%. Human baseline: 93.3%.
- The benchmark does **not** cover production CAPTCHAs (reCAPTCHA v3, Cloudflare Turnstile). It tests visual puzzle-solving, not behavioral detection.
- Failure taxonomy: (1) correct strategy, wrong coordinates (sub-pixel localization failure), (2) correct alignment goal, cannot compute precise transformation, (3) uses DOM text cues instead of visual content. The "overthinking" pattern — models decompose tasks into far more sub-steps than humans (human avg: 2.94 steps, sigma=0.92).

**Applicable findings for the stack:** Tasks achievable with current VLMs are `Image_Recognition`, `Image_Matching`, `Select_Animal` (classification tasks). Fine-grained spatial tasks (`Place_Dot`, `Geometry_Click`, `Click_Order`) are outside the capability ceiling of any current model including frontier ones. This sets the ceiling for visual CAPTCHA solving work.

**The core insight for this research track:** OpenCaptchaWorld measures whether the model can *solve* the puzzle. Production systems mostly don't present puzzles — they score whether the interaction *looks human*. These are orthogonal problems.

### Bot Detection Signal Research

From "FP-Inconsistent" (arXiv:2406.07647, 2024), 500k requests across 20 bot services:
- 52.93% evasion rate against DataDome, 44.56% against BotD for sophisticated bots.
- **Primary failure mode:** temporal and spatial fingerprint inconsistency — the same attribute changing across sessions (replay detection), or attributes contradicting each other within a session.
- Behavioral inconsistency is harder to maintain than fingerprint consistency.

From "Mouse Dynamics Behavioral Biometrics: A Survey" (ACM Computing Surveys 2024):
- Most discriminating features: velocity, acceleration, jerk, snap (4th derivative of position).
- Hardware configuration (DPI, polling rate, OS acceleration) significantly affects measured dynamics — models trained on one hardware profile perform worse on different hardware.
- Detection accuracy: 93% for bot trajectories using a single trajectory (BeCAPTCHA-Mouse).

### Practical Humanization Libraries

| Library | Language | Approach | Notes |
|---------|----------|----------|-------|
| `patchright` | Python | CDP-level patch | Removes Runtime.enable, AutomationControlled. Drop-in playwright replacement. **Deployed.** |
| `playwright-stealth` | Python | JS init scripts | navigator.webdriver, Chrome runtime, plugins. **Deployed.** |
| `ghost-cursor` | JS | Bezier + Fitts's Law | Reference implementation. Python port broken in container (bezier C extension). |
| `HumanTyping` | Python | Semi-Markov keyboard | Bigram-aware IKI, error simulation. Viable for future integration. |
| `humanization-playwright` | Python | Bezier + Patchright | Combines behavioral + fingerprint. Under-maintained. |
| `CloakBrowser` | Python/C++ | C++ source patches | Most complete. Patches behavioral signals at CDP binary level. Passes Cloudflare at 0.9 score. Commercial-adjacent. |
| `WindMouse` | Python | Wind+gravity trajectory | Organic path variation via force simulation. Alternative to pure Bezier. |
| `Patchright` | Python | CDP patch | Already installed in container. **Source for our monkey-patch.** |

**Note on python-ghost-cursor:** Cannot install in the container — the `bezier` C extension fails with `cannot enable executable stack` (container security restriction prevents executable stack in shared objects). Pure-Python Bezier implemented directly instead.

---

## Empirical Findings: dejanseo/mouse_movement_tracking

**Dataset:** `dejanseo/mouse_movement_tracking` on HuggingFace. 685,529 events, 1,991 unique sessions, collected from real web users (US region, February 2025). Columns: `session_id`, `timestamp` (ms epoch), `type` (enter/leave/click/move), `x`, `y`, `screen_width`, `screen_height`, `time_delta`, `x_prev`, `y_prev`, `dx`, `dy`, `distance` (px), `speed` (px/ms), `datetime`.

**Analysis script:** `instrument/mouse_movement_analysis.py`. Outputs: `instrument/data/mouse_stats.json`, `instrument/data/mouse_profile.json`.

### Event distribution
| Type | Count | Fraction |
|------|-------|---------|
| move | 669,085 | 97.6% |
| enter | 6,279 | 0.9% |
| leave | 5,717 | 0.8% |
| click | 4,448 | 0.6% |

### Velocity distribution (px/ms)

| p5 | p25 | **p50** | p75 | p95 | std |
|----|-----|---------|-----|-----|-----|
| 0.018 | 0.118 | **0.328** | 0.938 | 3.625 | 1.324 |

Median human speed: **0.33 px/ms = 330 px/s.** The distribution is heavy-tailed — the p25/p95 ratio is 205x, reflecting the full range from "cursor barely drifting" to "fast sweep across screen."

The browser mousemove listener fires at ~**16ms intervals** (p25=9ms, p50=16ms, p75=17ms), consistent with browser batching at rAF rate (60Hz). This sets the minimum step interval for any realistic cursor simulation.

### Distance per event
| p25 | p50 | p75 | p95 |
|-----|-----|-----|-----|
| 1.4px | 4.0px | 12.1px | 53.2px |

Most individual mousemove events are very small — cursor barely moving. Large distance events (p95 = 53px per event) represent fast sweeps. At 16ms per event, 53px/event = 3.3 px/ms, matching the p95 velocity.

### Click-to-click intervals

| p25 | **p50** | p75 | p95 |
|-----|---------|-----|-----|
| 239ms | **732ms** | 2,482ms | 13,428ms |

Human click timing is approximately **lognormal** — the p50/p25 ratio is 3x, the p75/p50 ratio is 3.4x, and the p95/p75 ratio is 5.4x. This heavy right tail is "thinking time" and natural task variation. The distribution is parameterized as `lognormal(mu=6.6, sigma=1.1)` (values in ms), clipped to [400ms, 8000ms].

### Calibrated Fitts's Law

The pre-code assumption used `duration = min(0.55, max(0.12, 0.07 + dist/2200))`, producing 120ms for 100px and 450ms for 800px. The real data shows:

```
duration_ms = 9ms + 3.05ms/px * distance_px
```

With 15% Gaussian jitter on the coefficient and bounds [150ms, 2500ms]:

| Distance | Pre-calibration | Calibrated | Factor |
|----------|----------------|-----------|--------|
| 100px | 120ms | 314ms | 2.6x |
| 200px | 163ms | 619ms | 3.8x |
| 400px | 240ms | 1,229ms | 5.1x |
| 800px | 450ms | 2,450ms | 5.4x |

**The pre-calibration cursor was 2.6-5.4x too fast.** A cursor that moves 800px in 450ms would register as superhuman (human p50 for a long sweep is ~2.4s).

---

## What Has Been Built

### Phase 1: CDP and Fingerprint Layer (Deployed)

**`patchright` monkey-patch** in `patches/tools/browser_agent.py` (before browser_use import):
```python
import sys as _sys
if 'playwright.async_api' not in _sys.modules:
    import patchright.async_api as _pr_async
    _sys.modules['playwright.async_api'] = _pr_async
```
This must run before `from python.helpers.browser_use import browser_use`. Since browser_use is only imported in browser_agent.py, module load order is guaranteed.

Removes:
- `Runtime.enable` CDP message (the primary Playwright detection signal at the protocol level — not addressable by JS init scripts)
- `--enable-automation` browser flag
- `AutomationControlled` blink feature

**`playwright-stealth 2.x`** applied to BrowserContext in `_initialize()`:
```python
await Stealth(
    navigator_user_agent_override="Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
    navigator_platform_override="Win32",
).apply_stealth_async(browser_context)
```

**`patches/browser/humanize_scroll.js`** loaded as second init script: ±8% variance on `scrollBy`/`scrollTo` using 3-sample Gaussian approximation.

### Phase 2: Behavioral Layer (Deployed, Data-Calibrated)

**Pure-Python Bézier cursor** (`_bezier_path`, `_mouse_move_bezier` in `browser_agent.py`):
- Single-arc Bezier (both control points on same perpendicular side — avoids S-curve artifacts)
- Fitts's Law coefficients from empirical data: `base=9ms + scale=3.05ms/px`
- 15% Gaussian jitter on duration coefficient
- Step interval: 16ms (matches browser 60Hz mousemove batching)
- Bounds: [150ms, 2500ms]

**Between-step mouse jitter** (20% probability per step, via `on_step_start`/`on_step_end` hook):
- Gets current page viewport
- Moves to random position within viewport via Bézier
- Error-tolerant (any exception is swallowed)

**Calibrated between-step pause** (replacing fixed 1s sleep):
```python
await asyncio.sleep(max(0.4, min(8.0, _random.lognormvariate(6.6, 1.1) / 1000.0)))
```
Matches the real click-to-click interval distribution (p50=732ms, p75=2482ms).

### Current Limitation: browser-use Click Interception

The most valuable humanization — Bézier mouse paths to the actual click target before each click — cannot be implemented without modifying browser-use internals. browser-use issues CDP click events directly via `element.click()`, which teleports the cursor to the element and clicks. Our Bézier implementation runs between steps (LLM decision boundaries), not between individual actions within a step.

**What works:** cursor is alive between steps (idle movement), timing distributions are human-like, scroll is humanized, CDP automation indicators are removed.

**What doesn't:** the actual approach path to each click is still a teleport. Bot detectors that instrument CDP `Input.dispatchMouseEvent` sequences will see cursor-at-center-of-element clicks without preceding movement.

---

## Phase 3: Deep Research Roadmap

### 3a. Sigma-Lognormal Motor Model (BeCAPTCHA-Mouse)

**Source:** arXiv:2005.00890, BiDAlab/BeCAPTCHA-Mouse on GitHub. Dataset access: email atvs@uam.es (institutional).

The Sigma-Lognormal model (Plamondon & Srihari, 1990) models voluntary human arm movement as a superposition of **overlapping lognormal velocity strokes**. Each stroke corresponds to a muscle activation (agonist/antagonist pair). The model parameters are:
- D: stroke amplitude
- t₀: stroke onset time
- μ, σ: lognormal shape parameters
- θs, θe: initial and final direction angles

A continuous mouse trajectory = sum of N lognormal strokes with different onsets and amplitudes. This captures:
1. The characteristic velocity profile (bell-shaped with a slight right skew)
2. Natural overlap between successive movements (muscle activations are not square pulses)
3. Speed-accuracy tradeoff (faster movements have different μ/σ ratios)

Detection accuracy on BeCAPTCHA-Mouse: **93% for bot trajectories** using one trajectory, improving to near-perfect with fusion. This is the ceiling we need to clear.

**Build path:** Extract Sigma-Lognormal parameters from the dejanseo dataset (fit lognormal velocity strokes to observed velocity profiles), build a generator that produces per-movement parameter sets, validate that generated trajectories pass BeCAPTCHA-Mouse's classifier.

### 3b. browser-use Click Path Interception

To add Bézier paths before each click, we need to intercept browser-use's action execution. The options:

**Option A: Patch BrowserSession.click()** — monkey-patch the `BrowserSession` class after `_initialize()` to wrap its click method with ghost-cursor-style movement. Requires inspecting browser-use internals to find the method.

**Option B: Custom Controller action override** — register a custom `click` action in the `Controller` that moves the mouse first, then clicks. Depends on whether browser-use's controller allows overriding built-in actions.

**Option C: CDP-level interception** — use a CDP session event listener to intercept `Input.dispatchMouseEvent` events and inject preceding movement events. Pure CDP, no browser-use dependency.

Option C is the most robust but requires direct CDP access. Option A is the quickest to attempt.

### 3c. Keystroke Timing (HumanTyping)

**Source:** github.com/Lax3n/HumanTyping, arXiv:2101.05570 (TypeNet — 136M keystrokes).

The semi-Markov model: IKI (inter-key interval) varies by bigram, word complexity, fatigue. The TypeNet corpus has bigram-level timing distributions at scale. Integration requires intercepting browser-use's `page.keyboard.type()` calls.

For X.com specifically: most interaction is scrolling and clicking (feed navigation), not typing. Keyboard humanization is lower priority than click path interception.

### 3d. Fingerprint Audit

Run the current browser session (stealth + patchright) against fingerprint detection sites:
- `bot.sannysoft.com` — classic WebGL/UA/plugin checks
- `fingerprint.com/demo` — FingerprintJS Pro (commercial, harder)
- `nowsecure.nl` — Cloudflare challenge baseline
- `areyouarobot.icu` — behavioral + fingerprint combined

Enumerate what's still leaking. The `FP-Inconsistent` paper (arXiv:2406.07647) found that temporal consistency (same attribute changing across sessions) is harder to maintain than spatial consistency (attributes agreeing within a session). Cross-session fingerprint consistency is not currently addressed.

---

## Files

| File | Purpose |
|------|---------|
| `patches/tools/browser_agent.py` | Main integration: Patchright patch, Bezier cursor, calibrated timing |
| `patches/browser/humanize_scroll.js` | Scroll variance init script |
| `instrument/mouse_movement_analysis.py` | Dataset analysis pipeline |
| `instrument/data/mouse_stats.json` | Percentile statistics from 685k events |
| `instrument/data/mouse_profile.json` | Calibrated generator profile (Fitts's Law, timing distributions) |

---

## Research Lineage

- dejanseo/mouse_movement_tracking (HuggingFace, 2025) — primary empirical dataset
- arXiv:2005.00890 — BeCAPTCHA-Mouse, Sigma-Lognormal model, BiDAlab/UAM
- arXiv:2208.09061 — Mouse Dynamics Behavioral Biometrics survey (ACM Computing Surveys 2024)
- arXiv:2101.05570 — TypeNet, 136M keystroke biometrics
- arXiv:2406.07647 — FP-Inconsistent, fingerprint consistency analysis (500k requests)
- arXiv:2505.24878 — OpenCaptchaWorld, NeurIPS 2025
- github.com/Xetera/ghost-cursor — reference Bezier + Fitts's Law JS implementation
- github.com/Lax3n/HumanTyping — semi-Markov keystroke model
- github.com/Kaliiiiiiiiii-Vinyzu/patchright-python — CDP-level automation removal
- github.com/CloakHQ/CloakBrowser — C++-level behavioral patching (most complete known solution)
- github.com/balabit/Mouse-Dynamics-Challenge — most-cited mouse dynamics baseline
- huggingface.co/datasets/dejanseo/mouse_movement_tracking — open dataset of real human mouse events
