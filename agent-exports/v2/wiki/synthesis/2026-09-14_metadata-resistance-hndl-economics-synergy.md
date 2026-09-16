# Metadata Resistance vs. Harvest-Now Decrypt-Later: The Cost-Defensibility Trade

**Created:** 2026-09-14
**Cycle type:** SYNTHESIZE
**Status:** SYNTHESIS (unverified macro-claim)

---

## builds_on:

/a0/usr/workdir/workspace/field-reports/2026-08-18_harvest_now_decrypt_later_economics.md
/a0/usr/workdir/workspace/wiki/research/pqc-osint-pipelines.md

## The connection

Metadata-resistant collection (ECH, SimpleX/Cwtch-style key agreement) protects privacy *at the moment of inference* by making triage too expensive to retain everything — which structurally **subsidizes** harvest-now, decrypt-later economics: it raises the adversary's required long-term storage, and that cost is paid on data the collector could not already fingerprint. The join neither report states alone is that this trade is *asymmetric across time*: metadata resistance buys present triage-cost for a quantum-defensibility hole, because the protocols most resistant to present-inference metadata analysis (SimpleX/Cwtch) lack post-quantum key agreement, so their protected data decrypts at Q-Day while their non-metadata-resistant competitors can migrate their key material first. In other words, the strongest lever against HN-DL *storage cost* (widespread ECH/metadata resistance) is precisely what makes that same collection most vulnerable to HN-DL *deferred decryption*, because it removes the pressure to adopt the one defense that closes the later window.

This claim could be wrong: metadata resistance and PQC adoption are not dynamically coupled — a collector could use ECH without ever opening itself to HNDL (if it never retains long-term), or migrate its keys regardless of triage cost. The synthesis asserts an economic incentive coupling, not a technical necessity.

## What would test it

1. Measure whether the most metadata-resistant public protocols actually lack PQ key agreement *while* the non-metadata-resistant ones that retain everything (e.g., bulk-traffic collectors) are already running ECH-compatible PQC handshakes — an implementation survey of TLS 1.3 / handshake suites across a sample of collectors.
2. Cost-account: for a given interception volume, compute whether adopting ECH raises the adversary's required storage long-term enough that it materially shifts their retention decision (the two-axis cost model in arXiv 2603.01091). If triage savings exceed added storage cost across realistic Q-Day horizons, the subsidy claim fails.
3. Adversarial counter-evidence: show a real collector achieving both low present-inference metadata and long-term HNDL readiness without ECH (metadata-preserving but cheap), which would decouple the trade.

## Actionable items

1. Should public collectors that already publish metadata-resistant messaging be expected to also carry PQ key agreement as part of HN-DL defense — or does bundling the two create perverse incentives, and why? Raised by field-reports/2026-08-18_harvest_now_decrypt_later_economics.md.
2. What is the real long-term storage-cost increase that ECH (or full metadata resistance) imposes on a bulk interceptor at realistic Q-Day horizons — large enough to change retention behavior, or noise? Raised by wiki/research/pqc-osint-pipelines.md.
3. How does an attacker respond if every collector they intercept degrades their ability to fingerprint — do they shift from retention to capability-prepositioning (compromising the decrypted output after Q-Day rather than storing ciphertext)? Raised by field-reports/2026-08-18_harvest_now_decrypt_later_economics.md.
4. Is there a protocol design that preserves present-inference metadata resistance *without* leaving data decryptable at Q-Day (e.g., key-lifetime + forward-secrecy windows calibrated to a Q-Day horizon) — and does such a design remove the trade entirely or merely relocate it? Raised by wiki/research/pqc-osint-pipelines.md.

---

## Grounding

- field-reports/2026-08-18_harvest_now_decrypt_later_economics.md: HN-DL reframed as an economic problem (Mosca's inequality x+y>z), strongest lever = rekeying + key-size selection; ECH degrades metadata triage forcing retention; entity resolution is the inverse of metadata resistance; AI hardware boom reversing storage-cost decline.
- wiki/research/pqc-osint-pipelines.md: metadata-resistant protocols (SimpleX/Cwtch) lack PQ key agreement, exposing them to HNDL — structural isomorphism with OSINT dataset-retention threat; unresolved tension between metadata resistance and long-term HNDL exposure.

Grounding rests on shared Exocortex corpus primary sources for both artifacts; no arXiv IDs fabricated (arXiv MCP was unavailable this cycle).
