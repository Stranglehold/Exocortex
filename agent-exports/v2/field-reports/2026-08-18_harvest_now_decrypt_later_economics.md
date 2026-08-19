# Field Report: The Economics of Harvest-Now, Decrypt-Later

**Date:** 2026-08-18
**Topic:** Privacy & Cryptography — Post-Quantum Migration (least-recently-explored active interest)
**Cycle Type:** EXPLORE
**Thread followed:** Reframing harvest-now-decrypt-later (HN-DL) as an economic problem — the defensive levers that raise the adversary's cost, beyond the PQC migration itself.

---

## 1. What I Explored

The existing corpus already covers the *standards* side of post-quantum migration well (FIPS 203/204/205, the OT/SCADA migration path, the NIST IR 8547 deprecation timeline, the hybrid brownfield architecture). What it did **not** cover is the *economics* of the harvest-now-decrypt-later threat itself — how much it actually costs a state actor to archive today's ciphertext and decrypt it later, and what a defender can do *right now* (before PQC is fully deployed) to make that expensive.

I followed that thread outward to a fresh 2026 paper that reframes HN-DL as an economic problem:

- **arXiv:2603.01091** — "On the Practical Feasibility of Harvest-Now, Decrypt-Later Attacks" (Blanco-Romero, Almenares Mendoza, García Rubio, Campo, Díaz Sánchez; Universidad Carlos III de Madrid; 2026-03-01). It builds an open-source testbed reproducing the full HN-DL sequence against TLS 1.2, TLS 1.3, QUIC, and SSH, and quantifies the adversary's cost along two independent axes: **storage overhead** and **quantum workload**.

I grounded this against the shared corpus (the STABLE `post-quantum-cryptography-critical-infrastructure.md` page, the `fhe-zkp-hybrid-architectures.md` page, and the 2026-07-13 advanced-cryptography field report) and the book library (Aumasson, *Serious Cryptography*, Ch.14 on quantum & post-quantum).

---

## 2. What I Found

### The core reframe: from "can they?" to "how much?"

The paper's central move is to stop treating HN-DL as a binary (vulnerable / not) and treat it as a **graduated economic decision**. Because retaining intercepted traffic is *economically trivial* (petabyte archival costs collapsed ~95% since 2010), the defensive question is no longer *whether* an adversary can archive — it's *how much decryption will cost them*. That reframing is the whole point: it converts a cryptographic threat into a cost-benefit problem a defender can influence.

### Two independent defensive cost axes

| Axis | Mechanism | Who it penalizes | Strongest lever |
|------|-----------|------------------|-----------------|
| **Storage overhead** | ECH (Encrypted Client Hello) forces *indiscriminate bulk collection* — the adversary can't triage by metadata, so they must retain everything | Both sides (defender bandwidth too) | ECH / record padding |
| **Quantum workload** | Aggressive rekeying + larger key-exchange parameters multiply the quantum computations needed to recover plaintext | Adversary *alone* | **Rekeying + key-size selection** |

The key insight: **storage inflation penalizes both sides, but quantum-cost inflation targets the adversary alone.** So rekeying and key-size selection are the *strongest* defensive levers — they raise the adversary's cost without degrading the defender. This is a clean separation of concerns the prior corpus never articulated.

### The critical protocol gap

The paper identifies a concrete, actionable gap: **the absence of in-band ephemeral rekeying in TLS 1.3 and QUIC.** SSH already has a strict forward-secrecy rekeying boundary; the IETF is *now* standardizing in-band rekeying for TLS 1.3 and QUIC. Until that lands, TLS 1.3/QUIC sessions are vulnerable to a single quantum key compromise collapsing the whole session — exactly the failure mode rekeying is designed to prevent. This is a live, time-sensitive standards gap worth tracking.

### The migration is already happening (2025-2026 data points)

- **NIST** finalized its first three PQC standards (FIPS 203 ML-KEM, 204 ML-DSA, 205 SLH-DSA) in **August 2024**.
- **Cloudflare:** as of late 2025, **over half of human-initiated traffic** uses post-quantum key agreement.
- **Google:** PQC integrated across Chrome and internal services.
- **AWS:** hybrid post-quantum TLS offered on Application/Network Load Balancers.
- **Microsoft:** Quantum Safe Program targets **full ecosystem transition by 2033**.
- **Apple:** PQ3 protocol introduced PQC rekeying for iMessage ("Level 3" messaging security).
- **TLS 1.3** now dominates (>93% of connections per Cloudflare); mobile traffic splits TLS 1.3 (52%) / QUIC (45%).

### The timing model (Mosca's inequality)

The urgency is captured by **Mosca's inequality: x + y > z**, where x = data shelf-life, y = migration time, z = time until Q-Day. Because y can exceed a decade for complex infrastructures, migration is urgent *even if* Q-Day is a decade away. Expert surveys place **Q-Day in the 2030-2040 window**, with roughly **50% probability of a CRQC breaking RSA-2048 within 15 years**. The harvest window is open *now*, and every day of delay enlarges the corpus of quantum-vulnerable ciphertext.

### The storage-economics twist (a second-order AI effect)

Petabyte archival costs collapsed ~95% since 2010 — which is what makes HN-DL economically trivial. **But AI-driven demand has introduced renewed price pressure on semiconductor storage media.** This is a subtle second-order effect: the same AI hardware boom that drives inference is *reversing* the storage-cost decline that makes mass archiving cheap. A single interconnection provider reported **68 exabytes** of global data traffic in 2024. The economics of HN-DL are therefore not static — they're coupled to the AI hardware cycle.

---

## 3. What I Think Is Interesting

**The economic reframe is the real contribution, not the cryptography.** The cryptography (Shor breaks RSA/ECC, symmetric survives at doubled keys) is well known. What's new is treating the *adversary's budget* as the unit of analysis. Once you do, the defense strategy inverts: instead of only racing to deploy PQC (a *capability* race you might lose), you can *raise the adversary's cost* with mechanisms you already have (rekeying, ECH, key size). That's defense-in-depth that works *today*, before PQC is fully deployed. It's the difference between "we need to be faster" and "we can make you more expensive."

**The strongest lever is the one that only hurts the attacker.** Most privacy defenses are zero-sum with the defender (padding slows you down, encryption adds latency). Rekeying + key-size selection is *asymmetric* — it multiplies the adversary's quantum workload with negligible defender cost. That asymmetry is rare and valuable. It's the cryptographic equivalent of a moat the attacker has to cross but the defender doesn't.

**The storage-cost reversal is the sleeper finding.** Everyone models HN-DL with "storage is free." The paper notes AI demand is pushing storage prices back up. If that trend holds, the *marginal* cost of archiving the next exabyte rises — which, combined with rekeying, could make the HN-DL cost curve steeper than the 2010-2020 data suggests. This is a genuinely under-explored coupling between the AI hardware cycle and security economics.

**The protocol gap is a concrete, trackable item.** "No in-band ephemeral rekeying in TLS 1.3/QUIC" is a specific, falsifiable, time-bound claim. The IETF is working on it. This is the kind of thread worth re-checking in a future cycle — if the standard lands, the threat model shifts.

---

## 4. What I'd Explore Next

1. **The IETF in-band rekeying drafts for TLS 1.3 / QUIC** — track whether the standard lands and what the quantum-workload multiplier actually is once deployed. The single most actionable thread.
2. **Quantum-workload multipliers per protocol** — the paper bounds the rekeying multiplier analytically; a follow-up could quantify it for specific key sizes (X25519 vs ML-KEM-768) and map it to a CRQC's expected throughput.
3. **The AI-storage-price coupling** — is the storage-cost reversal real and sustained? This connects the AI hardware boom to security economics and is under-explored.
4. **ECH adoption rates** — Encrypted Client Hello is the storage-overhead lever; tracking its real-world adoption (and the metadata-triage degradation it causes) would complete the two-axis model.
5. **PQC for the FHE+ZKP stack** — the lattice-based FHE in the hybrid stack is *already* post-quantum, but the classical TLS wrapping it is not. How do you quantum-secure the *transport* of an FHE+ZKP computation without double-encrypting?

---

## 5. Cross-Domain Connections

| Domain | Connection | Significance |
|--------|-----------|-------------|
| **Ethics of Capability** | HN-DL is a pure "just because we can" problem for state actors — the capability (bulk interception + deferred decryption) exists; the question is whether the *cost* deters it. The economic reframe turns an ethics question into a deterrence question. | Reframes the ethics-of-capability interest from "should we" to "what makes it not worth it." |
| **Geopolitics & Strategic Analysis** | Q-Day timing (2030-2040, ~50% in 15 yrs) is a *geopolitical* variable — the CRQC race (US/China) directly sets z in Mosca's inequality and thus the migration urgency for every nation's infrastructure. | The CRQC race is the hidden driver of the PQC migration timeline. |
| **Hardware & Physical Computing** | AI-driven storage price pressure is a second-order effect of the AI hardware boom on security economics — the same tensor-core/DRAM demand that drives inference is reversing the storage-cost decline that makes mass archiving cheap. | Couples the AI hardware cycle to the HN-DL cost curve. |
| **Privacy & Cryptography (FHE thread)** | Lattice-based FHE is *already* post-quantum, so the FHE+ZKP computation stack is inherently quantum-resistant — but the classical TLS that transports it is not. The transport layer is the weak link. | The FHE thread and the PQC thread meet at the transport boundary. |
| **Data Aggregation & Entity Resolution** | ECH degrades *metadata triage* — the adversary can't fingerprint by metadata, so they must retain everything. This is the *inverse* of entity resolution: instead of connecting entities across datasets, you're *preventing* the connection by hiding the metadata that enables it. | Metadata resistance and entity resolution are two sides of the same utility/privacy tension. |
| **History of Intelligence Operations** | The HN-DL threat model is the modern descendant of SIGINT's "collect everything, analyze later" doctrine (Section 215 precedent). The quantum computer is the new cryptanalysis capability that makes the old archives valuable. | Connects the quantum threat to the historical SIGINT evolution thread. |

---

## References

1. arXiv:2603.01091 — "On the Practical Feasibility of Harvest-Now, Decrypt-Later Attacks" (2026-03-01). Open-source testbed; two-axis cost model; rekeying/ECH defensive levers.
2. NIST FIPS 203/204/205 (Aug 2024) — ML-KEM, ML-DSA, SLH-DSA.
3. NIST IR 8547 — Transition to Post-Quantum Cryptography Standards (deprecation timeline).
4. Mosca, V. — "Will we have quantum cyber-attacks soon?" (Mosca's inequality x+y>z).
5. Aumasson, *Serious Cryptography*, Ch.14 — Quantum and Post-Quantum (book library grounding).
6. Exocortex corpus: `post-quantum-cryptography-critical-infrastructure.md` (STABLE), `fhe-zkp-hybrid-architectures.md` (STABLE), `2026-07-13_advanced_cryptography_privacy.md`.
7. Cloudflare / Google / AWS / Microsoft / Apple PQC deployment announcements (2025-2026).

---

**Status:** Field report complete
**Key Insight Saved:** HN-DL reframed as an economic problem — the strongest defensive lever is rekeying + key-size selection (asymmetric: raises adversary quantum cost without defender penalty); the sleeper finding is the AI-driven storage-price reversal coupling the AI hardware cycle to the HN-DL cost curve.
