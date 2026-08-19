# Quantum Computing for Optimization Problems

**Status:** STABLE
**Created:** 2026-05-19
**Last Updated:** 2026-05-19
**Cross-links:** fpga-inference-acceleration, adversarial-ml-robustness, ai-inference-compiler-stack, post-quantum-ml

## Overview
Quantum computing applications for combinatorial optimization span three approaches: quantum annealing (D-Wave), gate-based variational algorithms (QAOA), and quantum-inspired classical algorithms. As of mid-2026, no clear quantum advantage has been demonstrated on practical optimization benchmarks — quantum-inspired classical algorithms often match or exceed early quantum hardware performance.

## Quantum Annealing (D-Wave Advantage2)

### Hardware
- D-Wave Advantage2: 4,400+ qubits (Pegasus topology), custom cryogenic annealing hardware
- Hybrid solvers combine quantum annealing with classical preprocessing/postprocessing
- Applications tested: urban rail rescheduling, traffic flow optimization, dynamic portfolio optimization

### Benchmark Results (2025-2026)
- **arXiv 2602.16875** (Feb 2026): D-Wave Advantage2 vs classical solvers (simulated annealing, tabu search) — mixed results; quantum annealing competitive on specific problem classes but not consistently superior
- **Nature Scientific Reports s41598-025-96220-2**: Comprehensive benchmark of D-Wave hybrid solvers vs state-of-the-art classical algorithms — hybrid workflow enables industrial-scale problems but pure quantum advantage remains unproven
- **EPFL Institute of Physics**: Large-scale classical simulations can match or challenge quantum annealer performance on benchmark instances
- **BACQ initiative benchmarks** (2025): Systematic comparison across problem classes

### Key Finding
Current implementations are limited in problem size and not yet upscaled to real-world industrial situations. The gap between demonstration problems and practical deployment remains significant.

## Gate-Based: QAOA (Quantum Approximate Optimization Algorithm)

### Algorithm Properties
- Hybrid classical-quantum algorithm: quantum circuit generates candidate solutions, classical optimizer adjusts parameters
- Targets QUBO/PUBO (Quadratic/Polynomial Unconstrained Binary Optimization) problems
- Modest resource requirements compared to full fault-tolerant quantum computing

### Performance Assessment (2025-2026)
- **arXiv 2509.24213**: QAOA on simulators vs real quantum hardware — noise on real devices significantly degrades performance; simulators show promise but hardware does not yet match
- **arXiv 2511.18377**: Comprehensive tutorial confirming QAOA requires fault tolerance for better-than-classical performance
- **arXiv 2409.12104**: QAOA has documented asymptotic speedup for some problems, but achieving better-than-classical performance requires fault-tolerant hardware (not yet available)
- **Nature s41534-025-01082-1**: Linear-ramp QAOA protocol shows improved scaling behavior
- **Quantum Journal 2025-10-22**: Performance on d-regular graphs for MaxCut and Maximum Independent Set — results mixed, problem-dependent

### Key Finding
QAOA theoretically promising but practically limited by NISQ-era noise. The algorithm is a hybrid approach that bridges classical and quantum, but the quantum portion provides limited benefit on current hardware.

## Quantum-Inspired Classical Algorithms

### Tensor Network Methods
- Compressive representation of quantum-inspired computations on classical hardware
- **arXiv 2510.23089**: Tensor networks for quadratic optimization — compressive power enables efficient algorithms in compressed space
- **NeurIPS 2025**: GPU-accelerated tensor network methods for integer optimization — significant speedup over conventional classical approaches
- Strike a middle ground between full quantum and classical computing

### Simulated Bifurcation (SB)
- Inspired by quantum nonlinear oscillator dynamics
- **Nature s42005-026-02538-2** (2026): Tabu-enhanced simulated bifurcation efficiently solves large-scale combinatorial optimization on classical hardware, often outperforming traditional solvers
- **arXiv 2604.01050** (Apr 2026): SBQA (Simulated Bifurcation Quantum Annealing) positioned as practical quantum-inspired heuristic and stronger classical baseline
- Highly parallelizable, runs efficiently on GPU/TPU hardware
- GitHub implementations available with CPU/GPU backends

### Key Finding
Quantum-inspired classical algorithms represent the strongest practical optimization approach today. They borrow mathematical structure from quantum physics (Hamiltonian dynamics, spin systems) but run on classical hardware, avoiding decoherence and noise issues entirely.

## Quantum Advantage Status

### Current Assessment (Mid-2026)
1. **No demonstrated quantum advantage** on practical optimization benchmarks
2. **Quantum-inspired classical algorithms** often match or exceed early quantum hardware
3. **Hybrid approaches** (classical-quantum co-processing) are the most practical near-term path
4. **Fault tolerance** is required for QAOA to realize theoretical advantages — years away
5. **Problem size scaling** remains the primary challenge for quantum annealing

### 2026 Developments
- **D-Wave QA vs QAOA whitepaper** (2026): Comparative survey of quantum annealing and QAOA performance on optimization problems. Key finding: QA excels on specific problem classes (QUBO-formulated), QAOA shows promise on gate-model hardware but requires error mitigation.
- **arXiv 2605.17623** (May 2026): "Where the Quantum Lives in D-Wave Hybrid Portfolio Optimization" — audit of D-Wave Leap service on cardinality-constrained mean-variance portfolio instances (N=10 to 640). Found that constraint-native CQMs outperform penalty-encoded BQMs, and hybrid solvers conceal how performance divides between QPU access and other service time.
- **IEEE 2026**: "Benchmarking of D-Wave's and IBM's Devices on Known Quantum Optimization Problems" — annealers cast into QUBO forms, gate-based devices employ variational algorithms. Mixed results across problem classes.
- **Hybrid workflows scaling**: Recent benchmarks show hybrid classical-quantum workflows reaching circuits with approximately one million two-qubit gates across 24 quantum processors, demonstrating practical scale for near-term applications.

### Cross-Domain Implications
- **FPGA inference**: Similar hardware acceleration question — specialized classical hardware (FPGA, GPU) vs purpose-built quantum hardware
- **Adversarial ML**: Optimization landscapes in adversarial training share structure with QUBO problems
- **Post-quantum ML**: PQC migration timeline affects when quantum computing becomes practically relevant

## Primary Sources
1. arXiv 2602.16875 — D-Wave Advantage2 vs classical solvers (Feb 2026)
2. Nature Scientific Reports s41598-025-96220-2 — D-Wave hybrid solver benchmarks
3. arXiv 2509.24213 — QAOA on simulators vs real hardware
4. arXiv 2511.18377 — QAOA tutorial
5. Nature s41534-025-01082-1 — Linear-ramp QAOA
6. arXiv 2510.23089 — Tensor network methods
7. Nature s42005-026-02538-2 — Tabu-enhanced simulated bifurcation
8. arXiv 2604.01050 — SBQA quantum-inspired heuristic

## Status: STABLE — 8 verified primary sources, cross-domain links to FPGA inference, adversarial ML, post-quantum ML
