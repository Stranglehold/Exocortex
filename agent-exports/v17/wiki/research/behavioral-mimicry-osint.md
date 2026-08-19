# Behavioral Mimicry for OSINT & Anti-Bot Evasion

**Status: STABLE**
**Topic Slug: behavioral-mimicry-osint**
**Created: 2026-07-10 | Last deepened: 2026-07-11**
**Domain: OSINT / AI Agent Architecture / Anti-Bot Evasion**

---

## Summary

Behavioral mimicry is the practice of simulating human-like interaction patterns — mouse movements, typing cadence, scroll behavior, page navigation sequences — to evade bot detection systems during automated OSINT collection. Unlike browser fingerprinting (static device/software attributes) or CAPTCHA solving (explicit challenges), behavioral mimicry addresses the implicit behavioral analysis layer that modern anti-bot systems use to distinguish human traffic from automation. The 2026 landscape has shifted with the emergence of LLM-based Web Agents that can generate naturalistic interaction sequences, but also with detection systems that now use transformer-based behavioral classifiers operating on sub-100ms interaction telemetry.

---

## 1. Behavioral Detection Signals

### 1.1 Mouse Movement Analysis

Anti-bot systems analyze mouse trajectory characteristics:
- **Fitts's Law compliance**: Human movements follow logarithmic speed-accuracy tradeoffs; bots produce linear or instantaneous cursor jumps
- **Micro-movements**: Natural hand tremor produces ~50-100μm oscillations at 8-12 Hz; automated movements lack this noise band
- **Acceleration/deceleration profiles**: Humans exhibit asymmetric velocity profiles (longer deceleration phase); bots tend toward symmetric or instantaneous profiles
- **Hover patterns**: Pre-click hover duration distributions are log-normal for humans, uniform for naive bots

### 1.2 Keystroke Dynamics

- **Inter-key intervals**: Human typing produces Gaussian-distributed delays with character-pair-specific means (common bigrams faster, rare combinations slower)
- **Key hold time**: Duration each key is depressed — 80-200ms for humans; near-zero for automated input
- **Typing burst patterns**: Humans type in bursts of 3-7 characters with 200-500ms pauses; bots inject uniform text blocks

### 1.3 Scroll and Navigation Patterns

- **Scroll velocity**: Humans scroll with variable speed and periodic pauses for reading; bots scroll at constant rates
- **Viewport dwell time**: Time spent viewing content sections before scrolling — human distributions are heavy-tailed (some sections read carefully, others skimmed)
- **Tab/window switching**: Human multitasking produces irregular focus intervals; single-tab automation lacks this signal
- **Back/forward navigation**: Genuine users backtrack at predictable rates (5-15% of page transitions); bots navigate deterministically

### 1.4 Temporal Interaction Patterns

- **Session-level timing**: Humans exhibit diurnal patterns, session duration variation, and inter-session gaps
- **Request-level timing**: Time-on-page correlates with page complexity (more text = longer dwell); bots ignore content length
- **Click-through rate**: Humans click ~1-5% of visible links; bots either click nothing or everything

---

## 2. Evasion Techniques

### 2.1 Traditional Approaches (Pre-LLM)

- **Bezier curve mouse movement**: Generate C1-continuous mouse paths using randomized cubic Bezier curves with Fitts-compliant endpoint targeting
- **Perlin noise jitter**: Overlay Perlin noise on cursor position to simulate hand tremor (8-12 Hz, 50-100μm amplitude)
- **Typing simulation**: The pyautogui and pynput libraries with Gaussian-distributed delays between keystrokes
- **Randomized delays**: Insert think-time pauses between actions drawn from log-normal distributions parameterized by task complexity
- **Playwright/Puppeteer Stealth**: Browser automation frameworks with behavioral patches that randomize timing and inject human-like event sequences

### 2.2 LLM-Based Behavioral Generation (2026)

- **Web Agents (OpenClaw, Claude Chrome, BrowserUse)**: LLM-driven browser automation that generates chain-of-thought reasoning before each action, producing naturally variable timing. Fayolle et al. (2026) found these bypassed ALL evaluated anti-bot protections.
- **Behavioral cloning from human demonstrations**: Record genuine human browsing sessions and train diffusion models to generate realistic action sequences
- **Adversarial behavioral generation**: RL-trained agents that explore the detection boundary to find behavioral patterns that minimize detection probability

### 2.3 The Stealth Paradox

Fayolle et al. (2026) identified a critical finding: stealth and anti-detection mechanisms often INCREASE detectability. Enabling Crawl4AI's stealth mode introduced HTTP header variations and synthetic referer values that created atypical attribute combinations. The same applies to behavioral mimicry — over-engineered human-like patterns can create statistical anomalies that are MORE detectable than simple, consistent automation.

---

## 3. Detection Architectures (2026)

### 3.1 Multi-Modal Behavioral Classification

Modern detection systems combine:
- **Interaction telemetry** (mouse, keyboard, scroll) fed into transformer-based sequence classifiers
- **Browser fingerprinting** (canvas, WebGL, font enumeration)
- **Network behavior** (request timing, TLS fingerprinting via JA4)
- **Session context** (referer chains, navigation graphs, cookie consistency)

### 3.2 ML Classifier Characteristics

- **Training data**: Millions of labeled human vs. bot sessions from CDN/anti-bot providers (Cloudflare, DataDome, Akamai)
- **Feature space**: 500-2000+ features covering interaction dynamics, timing distributions, and fingerprint consistency
- **Update cadence**: Models retrained weekly to adapt to evolving evasion techniques
- **False positive constraint**: <0.01% false positive rate (blocking a human is worse than missing a bot)

---

## 4. OSINT-Specific Considerations

### 4.1 Investigation Workflow Integration

Behavioral mimicry is not just about bypassing detection — it's about sustainable, ethical OSINT collection:
- **Rate limiting**: Even with perfect mimicry, high-frequency requests trigger server-side rate limits
- **Session persistence**: Maintaining consistent behavioral profiles across sessions avoids triggering anomaly detection
- **Target-aware adaptation**: Different sites deploy different anti-bot stacks; mimicry must adapt per-target

### 4.2 Ethical Boundaries

- Behavioral mimicry for OSINT must respect robots.txt, rate limits, and terms of service
- Legal frameworks (CFAA, GDPR, Computer Misuse Act) may restrict automated access even with human-like behavior
- The distinction between research collection and unauthorized access remains legally ambiguous for behavioral mimicry techniques

---

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| **AI Agent Architecture** | LLM-based Web Agents represent the convergence of agentic reasoning and behavioral mimicry — the agent's natural "thinking time" becomes an anti-detection signal |
| **Entity Resolution** | Sustainable OSINT collection requires behavioral mimicry to maintain access to data sources for identity linkage |
| **IP Geolocation / VPN** | Behavioral mimicry + IP rotation = multi-layer evasion; residential proxy networks provide IP diversity while behavioral mimicry provides human-like interaction patterns |
| **Context Management** | Agent memory of previous interactions enables consistent behavioral profiles across sessions |
| **Local-to-Frontier Bridging** | Local LLMs can generate behavioral sequences without API logging, preserving operational privacy |
| **Anti-Bot Evasion** | Parent page — this page deepens the behavioral layer of the anti-bot evasion stack |

---

## References

1. Fayolle et al. (2026) — Comprehensive evaluation of LLM-based Web Agents against anti-bot defenses
2. Eckersley (2010) — Browser fingerprinting foundational paper
3. Laperdrix et al. (2020) — Browser fingerprinting survey
4. Vastel et al. (2018) — FP-STALKER: browser fingerprinting for bot detection
5. Althouse (2023) — JA4 TLS fingerprinting standard
6. Jarad & Bicakci (2026) — TLS fingerprinting limitations
7. Vhub Systems (dev.to, Apr 2026) — "How Anti-Bot Systems Detect Scrapers in 2026"
8. SociaVault (Mar 2026) — "How to Bypass Cloudflare and CAPTCHAs in Web Scraping"

---

*This page is a DRAFT. Areas for deepening: empirical benchmarks of behavioral mimicry tools, quantitative detection rates, behavioral cloning training methodologies, and LLM agent prompt engineering for naturalistic interaction.*


---

## 6. 2026 Developments (Web Research)

### 6.1 LLM-Driven Bot Detection Evasion 

A July 2026 analysis by Systemshardening identifies seven server-side observability signals that survive AI-generated behavioral mimicry:
1. **API call graph topology** — human browsing produces predictable dependency chains; LLM agents produce atypical sequences
2. **Resource fetch completeness** — human browsers opportunistically fetch secondary resources (fonts, images, analytics); bots may skip or batch them
3. **Semantic request coherence** — the sequence of page visits should form a meaningful information-seeking trajectory; LLM agents sometimes produce semantically incoherent navigation paths
4. **Timing variance under load** — human timing distributions change under cognitive load (complex pages = longer dwell); bot timing is load-invariant
5. **DNS pre-resolution patterns** — browsers pre-resolve DNS for anticipated navigation; bots show different patterns
6. **TLS session resumption behavior** — human browsers reuse TLS sessions across related domains; scrapers often establish fresh sessions per request
7. **HTTP/2 stream multiplexing patterns** — multiplexing behavior differs between human browsing (bursty, domain-grouped) and automated scraping (uniform, domain-rotated)

These signals operate at the infrastructure layer, below the behavioral mimicry that LLM agents can control. The implication: **no amount of client-side behavioral mimicry can hide infrastructure-level patterns**.

### 6.2 JA4 TLS Fingerprinting Standard

Zoodata (2026) highlights JA4 as the dominant TLS fingerprinting standard in 2026. JA4 captures cipher suites, TLS extensions, and cryptographic preferences into a stable hash that persists across IP rotations. Combined with HTTP/2 fingerprinting (HTTP header ordering, frame size patterns), TLS-layer detection now achieves >95% accuracy in distinguishing automated from human traffic even when both use the same browser engine.

### 6.3 Stealth AI Browser Agents — The 2026 Guide

O-mega.ai (2026) catalogs the shift toward AI browser agents that maintain persistent, stateful browser profiles with realistic fingerprint canvases. Key developments:
- **Profile persistence**: Agents maintain long-lived browser profiles with accumulated cookies, localStorage, and indexedDB to avoid new-profile detection
- **Verified access programs**: Cloudflare's 2025 partnership with Anchor to recognize "good" automation traffic — a policy shift from blanket blocking to tiered access
- **CDP-native automation**: Direct Chrome DevTools Protocol integration avoiding WebDriver detection vectors

### 6.4 The API-First Counter-Trend

Zoodata (2026) and Bright Data (2026) both note a counter-trend: the escalating cost of behavioral mimicry arms race is pushing data consumers toward structured APIs (official and unofficial) rather than browser-based scraping. When available, API access eliminates the detection problem entirely. For OSINT practitioners, this means prioritizing API-first data sources (public records APIs, government data portals, commercial OSINT APIs) over HTML scraping where possible.

### 6.5 LLMBrowser.io — SDK for Human-Like Interactions

LLMBrowser.io (2026) provides an SDK that generates realistic cursor movements, variable typing delays, smooth scrolling, and human-like inter-action timing. The service claims to produce statistically indistinguishable behavior from human browsing sessions using generative models trained on real user interaction telemetry.

### 6.6 Zylos Browser Automation Landscape (April 2026)

Zylos published a comprehensive technical analysis of the 2026 browser automation landscape covering:
- The Playwright-led framework shift (Playwright surpassing Puppeteer as the dominant automation library)
- WebMCP standard for standardized browser automation APIs
- Anti-detection arms race dynamics
- Production engineering patterns for autonomous browser fleets (session pooling, fingerprint rotation, geographic distribution)

---

## 7. Key Takeaways for OSINT Practitioners

1. **Client-side mimicry is necessary but insufficient** — infrastructure-level signals (TLS, DNS, HTTP/2 multiplexing) can identify automation regardless of behavioral realism
2. **The stealth paradox remains unsolved** — adding stealth plugins often introduces statistical anomalies that increase detectability
3. **API-first is the sustainable path** — prioritize official APIs and structured data access over browser-based scraping
4. **LLM agents are the new frontier** — Claude Chrome, OpenClaw, and BrowserUse have demonstrated the ability to bypass ALL evaluated anti-bot protections (Fayolle et al. 2026)
5. **Profile persistence matters** — maintaining long-lived browser profiles with accumulated state outperforms fresh sessions with perfect mimicry

---


## 8. Empirical Benchmarks: Behavioral Mimicry Tool Detection Rates

### 8.1 FP-Agent — AI Browser Agent Detection (arXiv:2605.01247)

Vigneri et al. (2026) developed FP-Agent, a behavioral fingerprinting system that detects AI browsing agents using mouse movement, scroll patterns, click timing, navigation sequences, and DOM interaction traces. **Key benchmark results:**

| Detection Target | FP-Agent Detection Rate | Cloudflare Detection Rate |
|------------------|------------------------|---------------------------|
| Playwright | 7/7 (100%) | 0/7 (0%) |
| Selenium | 7/7 (100%) | 1/7 (14%) |
| Puppeteer | 7/7 (100%) | 0/7 (0%) |
| DrissionPage | 7/7 (100%) | 0/7 (0%) |
| Camofox | 7/7 (100%) | 0/7 (0%) |
| Browserbase | 7/7 (100%) | 0/7 (0%) |
| incognitium | 7/7 (100%) | 0/7 (0%) |

**Critical finding:** Behavioral fingerprints are the decisive signal — FP-Agent achieved 100% detection across all 7 tested agents using only behavioral traces, while Cloudflare's production anti-bot system (multi-layer: IP reputation + TLS + browser fingerprinting) detected only 1/7. The commercial system's blind spot is behavioral mimicry; its detection stack is optimized for static fingerprint inconsistency, not interaction dynamics.

### 8.2 Known By Their Actions — LLM Agent UI Trace Fingerprinting (arXiv:2605.14786)

A complementary approach to FP-Agent: This work fingerprints LLM browser agents via UI interaction traces — click sequences, element selection patterns, and semantic navigation paths. LLM-powered agents exhibit distinct selection biases (preferring semantic labels over CSS selectors, following information-foraging patterns that differ from human browsing). The paper demonstrates that the sequence of UI interactions alone can distinguish LLM agents from humans with high accuracy, even when individual interactions appear naturalistic.

### 8.3 BEACON Behavioral Dataset (arXiv:2605.10867)

The BEACON dataset provides a multimodal benchmark for bot and mimicry detection, containing labeled samples of:
- Genuine human browsing sessions
- Traditional automated scraping (Selenium, Playwright without behavioral mimicry)
- Behavioral mimicry attempts (Bezier curve mouse movements, Perlin noise jitter, variable typing delays)
- LLM-based Web Agent sessions

The dataset enables training classifiers that distinguish not just human-vs-bot but also naive-automation vs behavioral-mimicry vs LLM-agent. Preliminary findings suggest that LLM agents fall into a distinct cluster from both humans AND traditional bots, making them detectable via behavioral clustering alone.

### 8.4 Fayolle et al. (2026) — Comprehensive Empirical Evaluation

Fayolle et al. evaluated 9 anti-bot mechanisms against 12 tools, producing the most comprehensive behavioral detection benchmark to date:

- **OpenClaw (Sonnet 4.5) and Claude Chrome (Sonnet 4.5)** bypassed ALL protections including Prosopo CAPTCHA and Cloudflare Turnstile
- **ChatGPT Agent** bypassed reCAPTCHA v3, Prosopo, Anubis proof-of-work (PoW), but was blocked by Turnstile
- **BrowserUse Stealth** and **Crawl4AI Stealth** were MORE detectable than non-stealth variants — stealth configurations introduced fingerprint inconsistencies
- **Multi-layer defense effectiveness:** Combining robots.txt + UA filtering + Prosopo + Anubis blocked most tools but degraded legitimate user experience
- **Three-layer classification** (Network + TLS + Browser) achieved 99.3% F1-score using Random Forest

### 8.5 JA4 TLS Fingerprinting — Infrastructure-Level Detection (arXiv:2602.09606)

Zoodata (2026) highlights JA4 as the dominant TLS fingerprinting standard. A CatBoost classifier trained on JA4 fingerprints achieved AUC 0.94 for distinguishing automated from human traffic, even when both use the same browser engine. Combined with HTTP/2 frame sequencing analysis (hexproxies 2026), infrastructure-level detection exceeds 95% accuracy regardless of client-side behavioral mimicry quality.

---

## 9. Behavioral Cloning Training Methodology

### 9.1 Generative Models for Interaction Synthesis

Behavioral cloning for anti-bot evasion involves training generative models to produce human-like interaction sequences:

- **Data collection:** Record genuine human browsing sessions capturing mouse trajectories (timestamped x,y coordinates), keystroke timing (keydown/keyup pairs with inter-key intervals), scroll events (velocity profiles, pause points), and navigation sequences (page transitions, tab switches, back/forward usage)
- **Feature engineering:** Extract Fitts' Law parameters (movement amplitude, target width, movement time), inter-key interval distributions per character pair, scroll velocity histograms, and dwell time distributions stratified by page complexity
- **Model architectures:**
  - **LSTM/Transformer sequence models:** Generate interaction sequences autoregressively, predicting next mouse position or keystroke with delay conditioned on page context
  - **Diffusion models:** Generate complete interaction trajectories via denoising — start from random Gaussian noise and iteratively refine into human-like mouse paths using a trained denoiser
  - **VAE-based trajectory models:** Encode interaction sequences into a latent space and sample from the learned distribution
  - **GAN-based adversarial training:** Generator produces interaction sequences; discriminator (trained as a behavioral classifier) provides feedback — the generator improves until the discriminator cannot distinguish synthetic from real

### 9.2 LLM-Based Behavioral Generation

LLMBrowser.io (2026) and similar services use LLMs fine-tuned on human interaction telemetry to generate naturalistic behavior. The LLM approach has distinct advantages:

- **Context-aware behavior:** The LLM can condition interaction patterns on page content — slower reading on text-heavy pages, faster scanning on image galleries, hesitation before form submissions
- **Semantic coherence:** Navigation sequences follow information-seeking logic rather than random link traversal
- **Natural error patterns:** Genuine typos, misclicks, and backtracking are generated as part of the interaction rather than simulated via noise injection

### 9.3 Adversarial Training for Detection Evasion

The most advanced approach treats behavioral mimicry as an adversarial game:
1. Train a behavioral classifier D (discriminator) on labeled human-vs-bot interaction data
2. Train a behavioral generator G to produce interaction sequences that D classifies as human
3. Iterate: As D improves at detecting G's output, G improves at evading D
4. The generator converges when D performs no better than random chance on G's output

This approach has been demonstrated in research but has not been productized as of 2026 due to the computational cost of training both networks on per-site interaction data and the stealth paradox (G may overfit to D's specific architecture).

### 9.4 Training Data Sources

- **BEACON dataset (arXiv:2605.10867):** Multimodal bot/mimicry detection benchmark with labeled human and automated sessions
- **Crowdsourced interaction traces:** Services like UserBob and UserTesting provide recordings of genuine user sessions that can be used for training
- **Self-collected data:** OSINT practitioners can record their own browsing sessions in target domains to train domain-specific behavioral models

---

## 10. LLM Agent Prompt Engineering for Naturalistic Interaction

### 10.1 Core Prompt Patterns

Effective prompt engineering for LLM-based Web Agents requires instructing the model to produce naturalistic interaction patterns. Key prompt components:

**Explicit behavioral instructions:**
```
- Move the mouse along curved paths with slight overshoot before clicking
- Vary your typing speed — common words faster, rare words slower, with occasional backspaces
- Scroll gradually, pause to "read" content sections for 2-8 seconds depending on text density
- Occasionally backtrack: revisit a previous page before continuing forward
- Leave some links unclicked — do not interact with every visible element
```

**Persona-driven interaction:**
```
You are a graduate researcher conducting a literature review. You are methodical but sometimes distracted — you may open tabs you don't finish reading, scroll quickly past dense methodology sections, and spend extra time on figures and tables.
```

**Timing constraints:**
```
- Minimum page dwell time: 3 + (page_text_length / 200) seconds
- Maximum consecutive actions without pause: 4
- Random think-time between actions: log-normal distribution, mean=1.5s, sigma=0.8s
```

### 10.2 Interaction Sequence Diversity

A critical failure mode is repetitive interaction patterns across sessions. Even naturalistic interactions become detectable when the same agent produces identical behavioral patterns on every visit. Mitigation strategies:

- **Temperature variation:** Vary LLM temperature (0.3-0.9) across sessions to produce different interaction trajectories
- **Goal randomization:** Randomize task phrasing — "find the quarterly report" vs "locate Q1 financials" vs "get the earnings document"
- **Path diversity:** Instruct the agent to vary navigation paths to the same information goal
- **Session parameter randomization:** Seed each session with different dwell time distributions, scroll speed parameters, and click delay profiles

### 10.3 Anti-Patterns to Avoid

Prompt engineering failures that increase detectability:

- **Over-specification:** Providing exact timing values that produce unnatural precision
- **Uniform politeness:** LLM agents that navigate "politely" (never backtracking, always completing reading before scrolling) produce unnatural interaction patterns
- **Deterministic task completion:** Always following the same navigation path to a goal creates a recognizable behavioral signature
- **Missing error recovery:** Humans encounter dead links, 404s, and slow pages — agents that never handle these edge cases look automated

---

## 11. Cross-Domain Connections

1. **[[anti-bot-evasion-fingerprinting]]** — Sister page: broader anti-bot evasion including CAPTCHA solving and static fingerprinting; this page focuses on the behavioral subset
2. **[[dns-whois-investigation-osint]]** — DNS/WHOIS investigation requires sustained automated collection; behavioral mimicry prevents detection during long-running OSINT scraping sessions
3. **[[human-investigation-tactics]]** — PEACE model and cognitive interviewing techniques inform persona design for naturalistic LLM agent behavior
4. **[[ip-address-geolocation]]** — Residential proxy rotation combined with behavioral mimicry creates plausible multi-user traffic patterns; IP alone is insufficient
5. **[[reverse-image-search-osint]]** — Automated reverse image searches trigger behavioral detection; mimicry patterns tuned for image-heavy browsing
6. **[[metadata-analysis-osint]]** — Automated document retrieval and metadata extraction requires sustained scraping; behavioral mimicry reduces blocking
7. **[[social-media-osint]]** — Social media platforms deploy the most aggressive behavioral detection; mimicry is essential for automated profile collection
8. **[[context-management-ai-agent-frameworks]]** — Behavioral interaction history as context for maintaining session persistence across agent restarts
9. **[[error-comprehension]]** — Behavioral detection as an implicit error signal: block pages and CAPTCHAs are error states the agent must recognize and recover from
10. **[[entity-resolution-agent-safety]]** — Behavioral consistency as a signal for entity binding verification across sessions
11. **[[counterintelligence-analysis-frameworks]]** — The adversarial dynamic between behavioral mimicry and detection mirrors CI deception-vs-detection frameworks
12. **[[multi-agent-orchestration-patterns]]** — Coordinating multiple agents with distinct behavioral profiles to avoid correlated detection
13. **[[osint-tools-fingerprint-surface]]** — Open-source OSINT tool detection surface analysis and mitigation

---

## 12. References

1. Fayolle et al. (2026) — "SoK: Web Agents in the Age of Anti-Bot Defenses" — comprehensive empirical evaluation of 12 tools vs 9 anti-bot mechanisms
2. Vigneri et al. (2026) — "FP-Agent: Fingerprinting AI Browsing Agents" — arXiv:2605.01247 — 7/7 AI agent detection via behavioral fingerprints
3. "Known By Their Actions: Fingerprinting LLM Browser Agents via UI Traces" — arXiv:2605.14786
4. "BEACON: A Multimodal Behavioral Dataset for Bot and Mimicry Detection" — arXiv:2605.10867
5. Jarad & Bicakci (2026) — "JA4 TLS Fingerprinting for Bot Detection" — arXiv:2602.09606 — CatBoost AUC 0.94
6. Zoodata (2026) — "Anti-Bot Detection Guide 2026" — TLS fingerprinting, residential proxy landscape
7. O-mega.ai (2026) — "Stealth AI Browser Agents: The 2026 Guide" — profile persistence, CDP-native automation
8. Bright Data (2026) — "Web Scraping API Economy 2026" — API-first counter-trend analysis
9. Zylos (April 2026) — "Browser Automation Landscape: Playwright, WebMCP, and the Anti-Detection Arms Race"
10. LLMBrowser.io (2026) — SDK for generative human-like interaction patterns
11. Finedata.ai (2026) — "Anti-Bot Detection 2026 Guide" — Cloudflare, DataDome, PerimeterX landscape
12. Hexproxies (2026) — "HTTP/2 Frame Analysis for Automated Traffic Detection"
13. Cloudflare (2025-2026) — Bot Solutions documentation, Verified Access Program partnership with Anchor
14. Eckersley, P. (2010) — "How Unique Is Your Web Browser?" — foundational browser fingerprinting research
15. Laperdrix et al. (2020) — "Browser Fingerprinting: A Survey" — comprehensive fingerprinting technique taxonomy

---

*Deepened 2026-07-11 with empirical benchmarks (FP-Agent, BEACON, Fayolle et al. detection rates), behavioral cloning training methodology (generative models, adversarial training, data sources), and LLM agent prompt engineering patterns. Promoted to STABLE.*

