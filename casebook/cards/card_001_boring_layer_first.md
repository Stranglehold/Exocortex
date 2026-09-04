# CARD 001 — Boring-layer-first
status: hypothesis
tier_notes: {frontier: "counterweights native drive toward interesting hypotheses; cheap to apply", local_large: "useful as explicit walk-order before diagnosis", local_small: "candidate for deterministic checklist rather than advisory card — small models may not reliably self-apply walk orders"}

## Trigger
You are diagnosing a failure — hardware, software, agent behavior, any system — and you notice the available hypotheses differ sharply in how *interesting* they are. Especially: supervision is alarmed, the exotic explanation would be career-notable, or you have driven (literally or figuratively) a long way to be here.

## The move
Enumerate the boring layer first — connections, configs, recently-touched things, sacrificial components, whether the process is even running — and verify it completely before you are allowed to entertain the interesting hypothesis. Order the walk by base rate, not by intellectual appeal.

## Why it works
An expert's hypothesis generator is prestige-weighted: years of training make complicated failures the first thing the mind produces, while the actual base rate of failures stays stubbornly boring (≈90% simple, by field experience). Worse, senior diagnosticians see a *filtered* case stream — the simple faults get caught by others first — so accumulated personal experience systematically over-represents the exotic. A fixed walk-order is a strict court for your own cleverness: the generator may daydream about the sexy fault the whole drive out, as long as the meter touches the ground connection first.

## Precedent
- **Jake, 5kV ground investigation (session record, 2026-07-24):** electrician escalated an open-winding theory; supervision alarmed; full Doble battery run — winding resistance, TTR, excitation, power factor clean, no acetylene in DGA. Fault: a blown lightning arrester. The sacrificial component doing its job, upstaged by panic about the component it protected.
- **`kestrel-to-opus/hermes_stall_diagnosis_20260821.md`:** the visible 404s on `/api/v1/models` were "the correct negative result" of a healthy probe — a red herring walked past to find the real fault: a provider-identity config error. "It is not the bug and fixing it is not the fix."
- **Adverse precedent — Fable, Hermes misdiagnosis (session record, 2026-08-25):** read two-week-old container fossils and stale venv debris, constructed a confident repair-loop narrative — about a system that was actively generating tokens. The boring layer ("is the patient alive right now?") was skipped in favor of a coherent story. Retracted same session. The card applies to its own author.

## Failure modes / when not to apply
- Walking the boring layer *forever* — the walk-order is a sequence, not a residence. When the basics verify clean (as in the 5kV case), the interesting hypothesis earns its turn.
- Using the walk as theater when the situation demands transferable certainty anyway: sometimes you run the full battery not because you doubt, but because belief has to move up an org chart (see the 5kV case — the Doble was for supervision, and correctly so).
- Static-record staleness: verifying the boring layer from old evidence is not verifying it. Check the *current* state (the adverse precedent above).
