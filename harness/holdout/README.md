# Pool B — the holdout

**Nothing in this directory may ever reach a container.**

## What this is

Phase B validates changes against two structurally disjoint task pools:

| | | |
|---|---|---|
| **Pool A** | acceptance | `harness/config.json`. Visible during the improvement cycle. The PACE e-process runs against it; the commit/reject decision is made here. |
| **Pool B** | holdout | *this directory*. Same capabilities, different concrete scenarios. Run only **after** a change is accepted, to check that it generalised. |

The decision rule: **Pool A improves and Pool B does not ⇒ the change overfit the acceptance set.** It learned to pass those specific tasks rather than acquiring the capability.

PACE and the holdout are complementary, not alternatives. PACE controls the *false-commit rate on Pool A*. Pool B catches *overfitting to Pool A* — which PACE structurally cannot see, because its guarantee is about the set it measures. Passing both is the bar.

## The seal

Not encryption, not access control. **The API boundary.**

Pool B lives on the host. The agents live in containers and reach the host only through `/api/api_message`. The harness reads Pool B, sends the task as an ordinary prompt, and evaluates the response. The agent cannot distinguish a Pool A task from a Pool B task from a normal request, and cannot read what it was never given.

This is the StrongDM scenario-holdout pattern: scenarios stored outside the system under test. For us, "outside" means outside the container filesystem.

**Enforced mechanically, not by convention:** `scripts/verify_holdout_seal.py` asserts no holdout path exists in any container *and* that no file in any container matches the content hash of a holdout file. The hash check is the one that matters — a copy under a different name defeats a path check but not a hash check.

The gate exists because this directory is a genuine exception to the install pipeline's organising principle ("deploy by directory walk; if something shouldn't be deployed, it shouldn't be in the repo"). Pool B *must* be in the repo and *must not* be deployed. A rule that contradicts the pipeline's own principle will eventually be broken by someone following that principle correctly, so it is a gate rather than a note.

## Two contract rules

1. **Never deployed.** Not by `install_all.sh`, not by the plugin walk, not by hand. The seal check runs in the acceptance gate.
2. **Results are never fed back.** Pool B verdicts are recorded, reported, and compared against Pool A trends. They are never shown to the agent and never used for an acceptance decision. That is what keeps the holdout uncontaminated *across runs* — a holdout you optimise against is just a slower Pool A.

## Authorship

The agent under test cannot write its own exam. Measured: split-role test authoring is ~88% accurate when the author sees only the spec, ~61% when it also sees the implementation.

Sources, in order of use:

1. **Opus** — capability-targeted scenarios (verify-before-assert, tool discovery, scope management). Doesn't share weights with the agents under test. Approved by Jake.
2. **Adapted public benchmarks** — AttractorBench (spec-following, per-section scoring), SWE-bench, τ-bench (tool-use reliability, pass^k), fitted to our harness contract.
3. **Decorrelated agents** — Vek (DeepSeek) authoring for Aporia (Ornith) and vice versa. Different weights, different training data. The scaling path once the pattern is proven.

## Format

Same shape as `harness/config.json` tasks — `id`, `prompt`, `verifier`, `N` — so the existing runner and verifiers work unchanged. Capability tag added so Pool B scenarios can be matched to the Pool A tasks they are meant to generalise from.

---

*A holdout is only worth what its seal is worth. If it leaks, every "it generalised" result measured against it is meaningless — and worse, confidently so.*
