# BP-05 — The Deterministic Spine

**Source:** Research III (the deterministic spine architecture study)
**Blocks on:** nothing — runs in parallel; BP-06 needs its gate.
**Owner:** [assign — candidate for Kestrel given the Rust]
**Status:** draft — *[Deposited 2026-07-03. Not started per Opus's briefing.]*

---

## Problem

The safety-critical layers — irreversibility gates, provenance, audit — currently
live (where they exist at all) inside Agent Zero's Python runtime, entangled with
the probabilistic core. Research III's thesis: extract them into a constellation
of small, strongly-typed, independently-running services *beside* Agent Zero, so
the boring correct parts are isolated from the parts that improvise.

## Architecture (sibling containers, not plugins)

```
                 +-------------------------------------+
                 |   Agent Zero containers (Python)     |
                 |   v16 - v17 - nifty_panini           |
                 +--------------+----------------------+
                                | MCP (network call, like the llama.cpp server)
        +-----------------------+-----------------------+
        v                       v                       v
+---------------+     +------------------+     +-----------------+
| Gate service  |     | Provenance svc   |     | Audit log       |
| Rust + Cedar  |     | Rust (CaMeL-ish) |     | hash-chained    |
| MCP server    |     | MCP server       |     | SQLite -> immudb|
| FAIL-CLOSED   |     |                  |     |                 |
+-------+-------+     +--------+---------+     +--------^--------+
        |                      |                        |
        +----------------------+------------------------+
                         all decisions written to the audit log
                                        |
                              +---------v---------+
                              | NATS JetStream    |  (the bus, adopted not built)
                              +-------------------+
```

**Docker compatibility (confirmed):** these are sibling containers on the same
bridge network. Agent Zero reaches them as MCP endpoints, exactly like it reaches
the llama.cpp server. No Agent Zero code modification. When the gate container is
down, the network call fails -> **denial by absence**, which is the behavior you
want. `depends_on` + restart policies give supervision-tree-lite behavior.

## Milestone 1 — The irreversibility gate (build this first, it proves the pattern)

This single service is the smallest thing that proves the whole spine concept and
retires the never-built HASKELL_DECISION_SERVICE_EXPLORATION (answer: Rust + Cedar,
not Haskell).

### Spec
- A **Rust MCP server** exposing one tool:
  `authorize_action(principal, action, resource, context) -> {allow | deny | require_approval}`
- Backed by **AWS Cedar** embedded as the `cedar-policy` crate (formally verified,
  4–11µs in-process decisions — orders of magnitude inside the in-loop budget).
- **Fail-closed default**: unknown or un-evaluable -> deny for irreversible actions.
- Every decision written to a **hash-chained audit log** (start with SQLite +
  hash chain; immudb only if external verifiability is ever needed).
- Wired to **one real irreversible action class** to start — file deletion or
  outbound network calls are the natural first targets.

### Cedar policy (sketch)
- Define a schema for the first action class: principals (which agent), actions
  (delete, post, transfer), resources (paths, endpoints), context (reversibility tag).
- `forbid` rules for irreversible actions absent explicit approval; `permit` for
  reversible ones. Forbid-overrides-permit makes global guardrails trivial.
- **Cedar verifies the engine, not your policies** — write policy tests; use
  Cedar's write-time schema validation.

### Build steps
1. `cargo` project, `rmcp` (official Rust MCP SDK) + `cedar-policy` + `rusqlite`.
2. Implement the `authorize_action` tool over stdio/HTTP MCP.
3. Implement the hash-chained audit writer (each entry's hash includes the prior).
4. Write the Cedar schema + policies for the first action class + policy tests.
5. Containerize; add to the compose file on the Agent Zero network.
6. Configure one agent to route that action class through the gate via MCP.
7. **Write a TLA+ spec for the fail-closed protocol** before trusting it (design
   artifact, not implementation).

### Acceptance gate (Milestone 1)
The gate denies a real irreversible action in a live agent, logs it tamper-evidently,
and fails closed when the gate container is stopped (the action is denied, not
silently allowed). **Kestrel reviews the Rust against the actual action it guards
— Rule 1 applies to the gate's own code.**

## Milestone 2 — The bus (adopt, ~1 evening)

- Stand up **NATS JetStream** (single ~15MB Go binary, official Docker image).
- Define **Protobuf message contracts** for gate decisions and audit events.
- Route gate decisions and audit events over the bus with at-least-once + dead-letter.

### Gate
A second agent/daemon consumes gate decisions over the bus reliably.

## Milestone 3 — Provenance / context-integrity (the prompt-injection defense)

- Build a **Rust service, CaMeL-inspired**: tag every context block with provenance
  (verbatim history / lossy summary / retrieved memory / operator injection / tool
  output), content-address it, enforce data-flow policies on what may flow to which sink.
- This is also the runtime home for the **provenance-marking gap** from EVT-008 —
  the thing the visitor most wanted added to the discipline.
- Closes the **lethal-trifecta** paths (private data + untrusted content + external
  comms): ensure no single agent path combines all three unguarded.

### Gate
The system blocks a simulated lethal-trifecta exfiltration path (test with
AgentDojo/Promptfoo-style patterns).

## Language verdicts (Research III, solo-maintainer + AI-codegen weighted)

- **Rust** earns its keep at the two untrusted-input boundaries (gate, provenance)
  and the MCP surface.
- **Haskell** only at the eventual epistemic/claim-tracker service (deferred).
- **Go** arrives free with adopted infrastructure (NATS, immudb).
- **Python-with-discipline** stays for everything exploratory (the agent layer).
- **TLA+** for *specifying* fail-closed and delivery protocols, never for implementation.

Three languages, not six. Polyglot sprawl is the real risk.

## Acceptance gate (whole plan)

The spine exists as sibling containers: one real irreversible action class is gated
fail-closed with tamper-evident logging, decisions flow over the bus, and a
lethal-trifecta path is blocked — all without modifying Agent Zero's runtime.
