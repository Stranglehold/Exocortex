# OSINT Methodology & Anti-Bot Evasion

**Status:** DRAFT → STABLE (pending index update)
**Created:** 2026-05-19
**Deepened:** 2026-05-19
**Interest Domain:** OSINT & Investigation Methodology

## Overview
Modern OSINT methodology requires understanding anti-bot detection systems, browser fingerprinting, and evasion techniques for systematic public data collection while maintaining legal and ethical boundaries.

## Anti-Bot Detection Landscape (2025-2026)

### Classic Browser Fingerprinting
- **Declining effectiveness**: hCaptcha (Jul 2024) confirms classic browser fingerprinting is no longer effective due to privacy-focused browsers and advanced evasion tactics
- **Canvas/WebGL/Audio**: Still used but increasingly unreliable as detection signals
- **GDPR compliance**: Fingerprinting faces regulatory pressure in EU

### Emerging Detection Methods
- **TLS Fingerprinting**: New approach (arXiv 2602.09606) - analyzes TLS handshake characteristics, harder to spoof than browser properties
- **FP-Inconsistency Detection**: UC Davis research (ACM 2025) - detects bots by comparing multiple fingerprint attributes for logical consistency
- **Behavioral Analysis**: Mouse movement, scroll patterns, timing analysis
- **JavaScript Execution**: Headless browser detection via DOM manipulation tests

### Evasion Techniques
- **Stealth Browsers**: Commercial products exist but are detectable through fingerprint inconsistency
- **puppeteer-extra-plugin-stealth**: Open-source solution for headless Chrome
- **Clean Proxies**: Essential for avoiding IP-based detection
- **Behavioral Mimicry**: Simulating human-like interaction patterns

## Toolchain Benchmark Evaluations (2026)

### Browser Fingerprint Realism Benchmarks
- **ScrapeOps Stealth Benchmark (Mar 2026)**: Most scraping APIs score below 35/100 on fingerprint realism, failing majority of signal categories
- **TLS Fingerprinting (arXiv 2602.09606)**: Protocol-layer TLS fingerprints are harder to spoof than browser properties; new detection frontier as classic fingerprinting fails
- **FP-Inconsistency Detection (UC Davis, ACM 2025)**: Detects bots by comparing multiple fingerprint attributes for logical consistency; stealth browsers fail here

### OSINT Toolchain Benchmarks
- **OSINTBench (ccmdi)**: 4-category LLM OSINT benchmark — Geolocation (spatial reasoning), Identification (info synthesis/breadth), Temporal (temporal reasoning), Analysis (general reasoning); rewards precise pinpoints not "right area"
- **GTPred (arXiv 2601.13207)**: MLLM geo-temporal prediction benchmark evaluating 8 proprietary + 7 open-source MLLMs for interpretable geo-localization and time prediction

### Legal & Ethical Framework
- **OWASP Six-Step Framework**: Target identification → Source gathering → Data aggregation → Processing → Analysis → Ethical boundaries
- **Legal Boundaries**: OSINT is legal when conducted using lawfully accessible sources without deception or unauthorized access (CFAA compliance)
- **Ethical Guidelines**: Proportionality, validation, accountability — avoid surveillance without cause or data misuse
- **GDPR Considerations**: EU regulations limit data processing even for public sources
- **Human-in-the-Loop**: Ethical OSINT requires human oversight of automated collection

## Cross-Domain Connections
- **Entity Resolution**: Core technique for linking disparate data sources
- **Privacy & Cryptography**: Metadata protection for OSINT collectors
- **AI Agent Architecture**: Automated OSINT collection workflows
- **Financial Crime Detection**: Similar investigation patterns

## References
- arXiv:2602.09606 - TLS fingerprinting for bot detection
- arXiv:2601.13207 - GTPred MLLM geo-temporal prediction benchmark
- ACM 2025 - FP-Inconsistent: Browser fingerprint inconsistency analysis
- hCaptcha blog - Why classic browser fingerprinting no longer stops bots
- ScienceDirect - Comparative analysis of OSINT tools, techniques, and legal aspects
- Group-IB Knowledge Hub - OSINT frameworks and cybersecurity applications
- OWASP - Six-step OSINT methodology framework

## Deepening Status
- [x] Initial research on anti-bot evasion landscape
- [x] Legal/ethical framework documentation
- [x] Cross-domain connection mapping
- [x] Reference compilation
- [x] OSINT toolchain benchmark evaluations (ScrapeOps 2026, OSINTBench, GTPred)
- [x] TLS fingerprinting analysis (arXiv 2602.09606)
- [x] LLM-based OSINT capability assessment
- [ ] Real-world case study analysis
