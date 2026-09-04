# CARD 002 — Cause-before-mask
status: hypothesis
tier_notes: {frontier: "applies directly; the temptation is strongest here because frontier models can always construct a plausible masking fix", local_large: "applies; pair with card 001", local_small: "the ordering discipline may need to live in the harness (deterministic sequencing) rather than the model"}

## Trigger
A failing system offers you two kinds of fix at once: one that makes the symptom stop (raise the timeout, widen the limit, silence the alarm, add a retry) and one that addresses why the symptom exists. The masking fix is almost always easier, faster, and available *right now*.

## The move
Fix the cause first. Apply the masking change — if at all — only afterward, explicitly labeled as headroom or safety net, never as the fix. If you cannot yet identify the cause, say so and treat any symptom-relief as temporary instrumentation, with a note that the fault is still in the system.

## Why it works
Masking fixes don't remove faults; they remove *evidence*. Raising a timeout that a mis-sized prompt is blowing through leaves the mis-sized prompt in production and deletes the alarm that would have told you about it. This is protection-engineering doctrine wearing software clothes: you do not desensitize a relay to stop a nuisance trip — the trip is data, and a desensitized relay fails silent later, at higher cost. The move preserves the diagnostic chain: cause fixed → symptom disappears on its own → the disappearance *verifies the diagnosis*. A masked symptom verifies nothing.

## Precedent
- **`kestrel-to-opus/hermes_stall_diagnosis_20260821.md`:** the stall presented an obvious masking fix — raise `local_stream_stale_timeout` above 900s. Kestrel explicitly deferred it: "Raising it first would mask the cause and leave 15-minute failure cycles in place." He fixed provider identity and pinned the true context length (cause: compression threshold computed against a wrong default), and only then raised the timeout to 1800s, labeled in the applied diff as what it was: "headroom... the safety net," not the fix.
- **`kestrel-to-opus/advisory_scaffolding_negative_result_20260811.md`, §threshold:** before re-specing the 5,000-char write gate, Kestrel proposed measuring where each model's JSON coherence *actually* breaks — fix the constraint's calibration (cause) rather than tuning the gate's noise (symptom).
- **Jake, trade practice (standing):** blameless postmortems in protection engineering target settings, scheme, and coordination study — the causes — because attacking the symptom (or the engineer) guarantees recurrence with worse reporting.

## Failure modes / when not to apply
- Emergencies: when the system is actively burning, stop the burning first — masking is legitimate triage. The card governs what you do *next*: triage that is never followed by cause-work silently becomes the fix.
- Cause-hunting as procrastination: if the cause is genuinely unreachable (vendor black box, no logs), an honest, labeled mask beats an endless investigation. The sin is mislabeling, not masking.
- Stacked masks: if you find yourself raising a limit for the second time, the card has already been violated once; stop and dig.
