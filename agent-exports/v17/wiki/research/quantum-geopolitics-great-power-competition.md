# Quantum Geopolitics & Great Power Competition

**Status:** STABLE
**Created:** 2026-07-10
**Deepened:** 2026-07-10
**Source Integration:** Shared corpus (7 cross-reference pages), book library (2 crypto references), web (Belfer Center 2026, PostQuantum 2025, QSI 2025)

## Overview

Quantum computing has transitioned from a purely scientific pursuit to a domain of geopolitical competition. The race for quantum advantage—and eventual cryptographically relevant quantum computers (CRQCs)—mirrors the nuclear race of the 20th century: the first mover gains asymmetric advantages in cryptanalysis (harvest-now, decrypt-later), materials science, and defense sensing. Unlike nuclear weapons, quantum supremacy is not a binary threshold but a continuous spectrum of capabilities, with the competition spanning hardware modalities, software ecosystems, talent pipelines, and supply chain control.

Global government investment now exceeds $40 billion (PostQuantum 2025), with China and the United States each committing $15B+. The UN designated 2025 as the International Year of Quantum Science and Technology (IYQ), underscoring the technology's perceived strategic importance.

## Strategic Significance

### Cryptography & National Security

The most immediate geopolitical threat is the prospect of a fault-tolerant quantum computer running Shor's algorithm to break RSA and elliptic-curve cryptography—the foundation of modern digital infrastructure, military communications, banking, and e-commerce. The "Q-Day" scenario—where a CRQC emerges before post-quantum cryptography (PQC) is widely deployed—is framed as an existential threat to information security.

Key dynamics:
- **Harvest-now, decrypt-later (HNDL):** State actors are believed to be intercepting and storing encrypted traffic today for future quantum decryption, motivating accelerated PQC migration under NIST FIPS 203/204/205
- **Intelligence advantage:** A country that develops a CRQC first gains the ability to decrypt rivals' secret communications, giving it a profound intelligence and military advantage
- **PQC transition costs:** Estimated at tens of billions globally, with critical infrastructure (IEC 61850/62351, SCADA/ICS) facing the hardest migration due to constrained embedded devices

### Economic Competitiveness

Quantum computing promises to revolutionize drug discovery, materials science, logistics optimization, and AI. National leadership is expected to translate into outsized economic returns and high-tech market dominance. The quantum computing market is projected at $50-100B by 2035, with early leaders capturing disproportionate value.

### Defense & Military Applications

Beyond code-breaking, quantum technologies have direct military applications:
- **Quantum sensing:** Detection of submarines, stealth aircraft, and underground facilities via gravitational/magnetic anomaly detection
- **Quantum communications:** Quantum Key Distribution (QKD) for tamper-evident command-and-control links
- **Quantum-enhanced AI:** Acceleration of defense computations including wargaming simulation and target recognition

## Competitive Landscape

### Major State Actors

| Country/Bloc | Investment (Est.) | Hardware Strengths | Notable Infrastructure |
|-------------|-------------------|--------------------|------------------------|
| United States | $15B+ (NQI Act $3.7B + DARPA US2QC + DOE) | Superconducting (IBM, Google), trapped ion (IonQ, Quantinuum), neutral atom (Atom Computing) | IBM Quantum Network, Google Willow (105 qubits, 2024) |
| China | $15B+ (state-directed) | Superconducting (Origin Wukong 198 qubits, 2024), photonic (Jiuzhang), QKD (Micius satellite) | World's longest QKD network (4,600+ km), national quantum lab Hefei |
| EU | €1B+ (Quantum Flagship) | Trapped ions (AQT), neutral atoms (PASQAL), superconducting (IQM) | EuroQCI |
| UK | £2.5B (National Quantum Strategy) | Trapped ions (Oxford Quantum Circuits), photonics (ORCA) | NQCC |
| Japan | ¥300B+ (Moonshot R&D) | Superconducting (RIKEN, Fujitsu) | IBM Quantum System One at Tokyo |
| India | ₹8,000 crore (National Quantum Mission, 2023) | Broad-spectrum, satellite QKD emphasis | I-Hub Quantum Technology Foundation |
| Russia | ~$790M | Ion traps (Russian Quantum Center), superconducting | Sanctions-constrained indigenous development |

### Hardware Modality Race

Five physical qubit modalities compete, each with different geopolitical implications:

1. **Superconducting circuits** (IBM, Google, Origin Quantum): Most mature, requires ~10mK dilution refrigeration (helium-3 supply chain dependency)
2. **Trapped ions** (IonQ, Quantinuum, AQT): Higher fidelity, slower gate speeds, laser supply chain dependency
3. **Neutral atoms** (PASQAL, Atom Computing, QuEra): Rapidly scaling (1,000+ logical qubit roadmap), advantages in connectivity
4. **Photonic** (Xanadu, PsiQuantum): Room-temperature operation potential, silicon photonics manufacturing dependency
5. **Topological** (Microsoft): Still theoretical, would offer intrinsic error protection; Majorana fermion detection remains unconfirmed

## Supply Chain & Critical Materials

### Dilution Refrigeration & Helium-3

Superconducting qubits require cooling to ~10 millikelvin using dilution refrigerators that depend on helium-3, a rare isotope primarily produced as a byproduct of tritium decay in nuclear weapons stockpiles. The helium-3 supply chain is deeply intertwined with nuclear weapons programs—the US and Russia are the primary suppliers. China's helium-3 access is a strategic constraint.

### Specialty Components & Export Controls

Key chokepoints subject to export controls (US BIS, Wassenaar Arrangement):
- Cryogenic microwave components: amplifiers, circulators, filters at millikelvin temperatures
- High-speed digitizers and arbitrary waveform generators for qubit control and readout
- Low-noise lasers and optical components for trapped ion and neutral atom modalities
- Quantum-specific ASIC design tools and fabrication for cryo-CMOS control electronics

As of 2026, US export controls on quantum technologies have expanded alongside semiconductor controls, but face the "small yard, high fence" critique—the technology is still pre-commercial, making controls hard to calibrate (Belfer Center 2026).

### Rare Earth & Advanced Materials Intersection

The quantum supply chain intersects with the rare earth supply chain (88-90% Chinese processing) for permanent magnets used in dilution refrigerators, vacuum systems, and laser components—the same structural dependency pattern documented in rare-earth-supply-chains.md.

## Export Controls & Technology Transfer

### US-Led Controls
- BIS Entity List: Chinese quantum firms (Origin Quantum, Baidu Quantum) restricted from US-origin equipment
- EAR dual-use additions (2022-2025): Quantum computing hardware, cryogenic systems, and associated software
- Outbound investment screening (2024-2025): Restrictions on US investment in Chinese quantum companies
- CHIPS Act national security guardrails: Beneficiaries cannot expand quantum R&D in China

### Chinese Response
- Accelerated indigenization: Domestic dilution refrigerator manufacturing (Origin Quantum's "Benu" fridge), cryogenic microwave components, quantum control electronics
- Talent repatriation programs to bring overseas Chinese quantum scientists back to domestic institutions
- Centralized control: Most leading quantum firms are spinoffs from state research labs; private tech firms shuttered quantum labs under government pressure to centralize (USCC 2025)

### The Pre-Commercial Controls Paradox

As the Belfer Center (2026) notes, Chinese quantum professionals view US export controls as "puzzling at this stage of the field"—the technology is too immature for controls to have meaningful impact on military capability, and restrictions may actually accelerate Chinese self-reliance. This is structurally isomorphic to the semiconductor export control paradox documented in us-china-semiconductor-supply-chain.md.

## Cryptography & Critical Infrastructure Implications

### Q-Day Timeline

The timeline to a CRQC remains uncertain. Expert surveys suggest a 20-50% probability within 15 years, but hardware advances (Google Willow 2024, IBM Heron 2025) are compressing estimates. The structural challenge: PQC migration requires 10-15 years for full infrastructure transition, creating a "migration gap" where cryptographic infrastructure may be vulnerable before Q-Day arrives.

### Critical Infrastructure Vulnerability

Direct connection to post-quantum-cryptography-critical-infrastructure.md: SCADA/ICS protocols (IEC 61850 GOOSE, DNP3, Modbus) have 20-40 year deployment cycles, meaning quantum-vulnerable devices installed today will remain in service long into the CRQC era.

## Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| us-china-semiconductor-supply-chain | Structural isomorphism: same export control paradox (controls accelerate indigenization), similar supply chain chokepoint patterns |
| post-quantum-cryptography-critical-infrastructure | Direct dependency: PQC migration timeline is a function of CRQC arrival estimates; shared SCADA/ICS vulnerability surface |
| rare-earth-supply-chains | Supply chain convergence: dilution refrigerator magnets, laser components depend on REE processing dominated by China (88-90%) |
| sigint-evolution | Paradigm continuity: quantum cryptanalysis is the next SIGINT paradigm after WWII Enigma/Colossus and modern mass surveillance |
| bridging-local-frontier-model-performance | Isomorphic pattern: quantum computing's classical-to-fault-tolerant gap mirrors the local-to-frontier AI gap |
| scada-ics-security | Shared vulnerability: PQC migration for ICS/SCADA protocols (IEC 61850, DNP3) is both a quantum infrastructure and critical infrastructure challenge |
| defense-sector-consolidation | Emerging intersection: quantum sensing for submarine/stealth detection; DARPA US2QC program |
| privacy-cryptography | Foundation: quantum-safe cryptography bridges QKD, PQC, and ZK-proof evolution in the broader cryptographic landscape |

## References

1. Belfer Center for Science and International Affairs. "Another Technology Race: US-China Quantum Computing Landscape." 2026. https://www.belfercenter.org/research-analysis/another-technology-race-us-china-quantum-computing-landscape
2. PostQuantum. "Quantum Geopolitics: The Global Race for Quantum Computing." March 2025. https://postquantum.com/quantum-computing/quantum-geopolitics/
3. USCC. "Vying for Quantum Supremacy: U.S.-China Competition in Quantum Technologies." 2025. https://www.uscc.gov/research/vying-quantum-supremacy-us-china-competition-quantum-technologies
4. Quantum Strategy Institute. "Export Controls & Quantum Technologies." July 2025. https://quantumstrategyinstitute.com/wp-content/uploads/2025/07/Export-Controls-Quantum-Technologies.pdf
5. PMC/NIH. "Quantum Technologies and Geopolitics: Comparing Parliamentary Approaches." 2025. https://pmc.ncbi.nlm.nih.gov/articles/PMC12830432/
6. Mamun, S. M. "Quantum Computing 2025: State of Play across Geopolitical, Security, and Economic Paradigms." Academia.edu, 2025
7. NIST. "Post-Quantum Cryptography Standardization." FIPS 203/204/205, 2024
8. CIGI. "Global Quantum Governance: From Principles to Practice." CIGI Papers No. 222, Kop & Forrest
