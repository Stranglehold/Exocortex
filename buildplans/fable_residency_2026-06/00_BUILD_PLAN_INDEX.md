# Exocortex Build Plans — Master Index

**Authored by Fable 5, 2026-06-12, from the five residency research reports.**
**Status: drafts for the team. Each plan is buildable; not every detail is pinned. Piece together as needed.**

---

## What this is

Five research reports produced during the June 9–12 residency established *what*
to build and *why*. These build plans translate those findings into *sequenced,
buildable workstreams* — the order, the interfaces, the acceptance gates, and
the hand-off points for Kestrel. They are deliberately written to survive the
author: every plan states its dependencies, its done-criteria, and the failure
modes that should halt it.

Read against the research reports, not instead of them. Where a plan says
"per Research III," the detail and citations live there.

## The meta-rules these plans obey

1. **Verify against running code, not architectural reasoning.** Every plan ends
   with an acceptance gate tested against the deployed system.
2. **Every capture system must have a consumption path.** No plan instruments
   something without naming who reads it.
3. **Instrument before optimizing.** Measurement plans precede optimization plans.
4. **Defense in depth for data quality.** Multi-layer validation where it counts.

## Dependency order

```
                    +-----------------------------------------+
                    |  BP-01  Attention Router  (do first)    |  <- unblocks everything;
                    |         the alarms must annunciate       |     cheapest high-value win
                    +-------------------+---------------------+
                                        |
        +-------------------------------+-------------------------------+
        |                               |                               |
+-------v--------+          +-----------v----------+         +----------v---------+
| BP-02          |          | BP-03                |         | BP-04              |
| Eval / Backtest|          | Calculator Drawer    |         | Agent Health       |
| Harness        |          | (specialist tools)   |         | (scheduler, audit, |
| (the gate)     |          |                      |         |  doc-sync)         |
+-------+--------+          +----------+-----------+         +--------------------+
        |                              |
        |   +--------------------------+
        |   |
+-------v---v----+          +----------------------+
| BP-05          |          | BP-06                |
| Deterministic  |--------->| Intelligence Pipeline|  (needs gate from BP-05
| Spine          |          | OSS/SWARMFISH/TAK    |   for gated writes)
| (Rust+Cedar)   |          | /Graph/Obsidian      |
+----------------+          +----------------------+
```

## The plans

| ID | Plan | Source report | Blocks on | First gate |
|----|------|---------------|-----------|------------|
| BP-01 | Attention Router | Field survey (EVT-006) | nothing | one digest, all agents, by severity, delivered |
| BP-02 | Evaluation & Backtest Harness | Research I, IV | BP-01 helpful | pass^k diverges visibly from pass@1 on a fixed set |
| BP-03 | The Calculator Drawer | Research V | BP-02 for validation | embedder upgrade beats MiniLM on local golden set |
| BP-04 | Agent Health & Lifecycle | Field survey | BP-01 | scheduler survives a container restart |
| BP-05 | The Deterministic Spine | Research III | nothing (parallel) | Cedar gate denies one real irreversible action, fail-closed |
| BP-06 | Intelligence Pipeline Maturation | Research IV | BP-02, BP-03, BP-05 | backtest harness scores SWARMFISH on held-out questions |

## Sequencing rationale

- **BP-01 first** because the field survey's core finding was that the consumption
  gap has moved up a layer to Jake. Every other workstream produces signals;
  none of them help if the signals land in an unread log. Annunciate first.
- **BP-02 before BP-03 and BP-06** because capability has outrun evaluation. You
  cannot tell whether a calculator-drawer swap or a SWARMFISH redesign helped
  without a scoring harness. Instrument before optimizing.
- **BP-05 can run in parallel** — it's a separate container constellation that
  touches nothing inside Agent Zero until BP-06 needs its gate.
- **BP-06 last** because it depends on the harness (to score it), the drawer
  (to cheapen it), and the spine (to gate its writes).

## A note on scope honesty

Not everything in the research was fully specified, and these plans don't pretend
otherwise. Where a design decision is genuinely open, the plan says **[OPEN]**
and states the question rather than inventing an answer. The team knows the
running system better than any document; these are scaffolds for your judgment,
not substitutes for it.

---

*The seven files (this index + BP-01 through BP-06) were authored together. If any
are missing from this directory, the full set is also in the residency outputs as
downloads. — Fable, 2026-06-12*
