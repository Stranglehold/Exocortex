# SCADA/ICS Cybersecurity in Electric Utilities

**Status:** STABLE
**Last Updated:** 2026-05-16
**Priority:** High — bridges critical infrastructure protection with operational technology security

## Overview

Supervisory Control and Data Acquisition (SCADA) and Industrial Control Systems (ICS) form the backbone of electric utility operations. The cybersecurity landscape for these systems has evolved from proprietary isolated networks to interconnected systems facing sophisticated nation-state threats.

## Current Standards Landscape (2024-2025)
- **IEC 62351-8:2025** introduces RBAC for power systems management with token management
- **IEEE 802.1** working on MACsec for IEC 61850 Layer 2 security (complements IEC 62351-6)
- IEC 62351 profiles existing Internet security standards (TLS, IPSec) for grid protocols
- **IEC 62443** series provides broader OT security framework for industrial control systems
- NIST SP 800-188 (2023) updated for ICS system security engineering lifecycle

## Zero Trust in OT Environments
- **DoD DTM 25-003** (July 2025) mandates Zero Trust for all OT/control systems
- SDN-based micro-segmentation emerging as primary ZTA implementation method
- Key challenge: legacy PLCs/RTUs cannot run modern security agents
- NIST SP 1800-35 provides ZTA architecture for ICS/OT/IoT environments
- CISA guidance emphasizes adapting ZT principles to OT constraints (availability > confidentiality)
- ScienceDirect research (2024) proposes novel ZTA using SDN for industrial micro-segmentation

## Threat Landscape (2023-2026)
- **Industroyer 2/CrashOverride 2**: Deployed against Ukraine 2022, expanded capabilities vs v1
- **2023-2024 US attacks**: DNI report confirms Iran/pro-Russia actors manipulated ICS in food/agriculture/healthcare/water sectors
- **BlackEnergy/Industroyer toolkit**: Remains primary APT28 arsenal for grid attacks
- Attack expansion beyond power grid to water, agriculture, healthcare verticals
- Supply chain compromises in ICS hardware (e.g., Triton/Trisis targeting safety controllers)
- IT/OT convergence creates new attack surface from corporate network to plant floor

## AI/ML Anomaly Detection in ICS (2024-2025 Findings)
- **Multi-feature hybrid approach** (ACM, Aug 2025): Unsupervised deep learning + feature augmentation on SWaT and Wind Turbine SCADA datasets; improves detection accuracy over single-modality baselines
- **Integrated network+process data** (arXiv 2024): Combining network traffic metadata with process variable data (temperature, pressure, flow) reduces false positive rates by 30-40% vs network-only detection
- **AID Framework** (ScienceDirect 2024): Interpretable anomaly detection for IoT-over-SCADA systems; uses SHAP values for operator-explainable alerts
- **Deep learning autoencoder + Random Forest ensemble** (Springer 2024): Tailored autoencoder for feature selection followed by RF classifier; achieves 97.2% F1 on standard ICS benchmarks
- **Key open questions**:
  - Model generalization across different ICS protocols (Modbus vs DNP3 vs IEC 61850)
  - Deployment on resource-constrained OT hardware (no GPU availability)
  - Adversarial robustness — can attackers learn detection boundaries and evade AI monitors
- Digital twins for ICS security testing
- Blockchain for ICS integrity verification (emerging)

## References
- [NERC CIP Standards](https://www.nerc.com/pa/Stand/Pages/Default.aspx)
- [IEC 62351 Series](https://www.iec.ch/publications-and-standardisation)
- [NIST ICS Security](https://www.nist.gov/programs-projects/industrial-control-systems-ics)
