# Entity-Resolution Matching Accuracy vs Harvest-Now-Decrypt-Later Staging: A Provenance Blind Spot

date: 2026-09-15
status: SYNTHESIZE cycle artifact (idle-time, Jake away)

## builds_on:
/a0/usr/workdir/workspace/field-reports/2026-08-18_harvest_now_decrypt_later_economics.md
/a0/usr/workdir/workspace/field-reports/2026-08-18_data_aggregation_entity_resolution_llm_frontier.md
/a0/usr/workdir/workspace/wiki/research/scada-ics-cybersecurity.md

## The connection
Entity-resolution (ER) pipelines tuned to maximize *matching accuracy* will be systematically blind to harvest-now-decrypt-later (HNDL) staging, because the HNDL threat manifests as **metadata retention and provenance accumulation**, while ER evaluates success by how well it *connects entities across datasets*. The detection vector for an archival-intent adversary is therefore not higher match precision but **provenance completeness** — exactly what ECH degrades by hiding the metadata that enables triage. Neither report states this join: HARVEST describes HNDL purely as a quantum-decryption-delay cost model and frames metadata resistance as "preventing connection"; ER frames T-KAER's transparency questions as analyst tradecraft for defensible matches. Reading them together, the shared variable is *provenance integrity under resource pressure*, and it turns out that an adversary can make an archive operationally worthless without ever deleting a record — simply by ensuring no match in that archive carries verifiable provenance.

This also reframes the electric-utility supply-chain note (backdoored model weights propagating through federated aggregation as a clean-label poisoning vector): the common structure is **a low-signal, high-volume update that a verifier cannot cheaply authenticate**, whether it is an ML weight or a database record's lineage. The attacker does not need to corrupt content — only to erode confidence in provenance.

## What would test it
Observation: run T-KAER-style transparency questions ("which semantic information influences the prediction?", "is the match explainable?") against two matched datasets identical in record count and link density but divergent only in per-record provenance completeness; if HNDL-staged archives are scored by standard ER precision/recall, they should look *as clean as* well-provenanced ones — i.e., no degradation — proving the detection vector is orthogonal to match accuracy. Experiment: add a provenance-completeness penalty to the blocking+matching objective and measure whether HNDL-stage detectability rises while matching-accuracy degrades only slightly (the hybrid gate from prior work on implementation-vs-testability). Confound to control: a matcher that ignores metadata entirely would score equally well or better, so one must show provenance-checks add detection *without* destroying the primary ER utility.

## Actionable items
- Can we instrument our entity_resolution pipeline with a lightweight provenance-completeness field per record and log it without slowing blocking? raised by /a0/usr/workdir/workspace/field-reports/2026-08-18_data_aggregation_entity_resolution_llm_frontier.md (T-KAER transparency, OpenPlanter 753-line pipeline)
- Is an archive whose records all lack provenance distinguishable from a healthy archive by any current metric, or only after the fact at decrypt time? raised by /a0/usr/workdir/workspace/field-reports/2026-08-18_harvest_now_decrypt_later_economics.md (ECH metadata triage degradation)
- Does a provenance penalty on matching sacrifice enough accuracy to matter in practice, or is the loss within the noise of normal blocking? raised by /a0/usr/workdir/workspace/wiki/research/scada-ics-cybersecurity.md (provenance-vs-detection tension in anomaly scoring)
