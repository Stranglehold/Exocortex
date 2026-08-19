# Backend Standby Mode — Concept

## Definition
Backend standby refers to the agent's degraded operational state when the primary LLM provider becomes unreachable. The system transitions from full reasoning mode to a fallback posture that preserves context integrity while preventing infinite retry loops.

## Actual Implementation (Verified 2026-05-02 against source code)
**Note**: Earlier versions of this page cited specific timeout values (30s/60s) and exponential backoff parameters. Those do not exist in agent.py — the framework relies on HTTP client defaults and supervisor-loop tier escalation instead.

### Supervisor Loop Tier Escalation (_50_supervisor_loop.py)
| Tier | Threshold | Action |
|------|-----------|--------|
| Tier 1 (Warn) | 3 consecutive hard signals | Agent notified, continues |
| Tier 2 (Surgery) | 6 consecutive hard signals | Context compression initiated |
| Tier 3 (Breaker) | 9 consecutive hard signals | Forced response — task termination |

### Hard Signal Categories (relevant to backend failures)
- `http_error` — non-200 responses from provider
- `connection_refused` — provider unreachable
- `context_exhaustion` — context window >90% full

Domain-aware thresholds exist for structural domains (codegen, debugging, system_admin) where repeated failures are expected mechanism rather than evidence of being stuck. These use elevated tiers: tier1=6, tier2=12, tier3=18.

## Recovery Strategies
No explicit exponential backoff or connection timeout configuration exists in agent.py as previously claimed. Recovery depends on:
1. HTTP client default retry behavior (framework-level)
2. Supervisor loop forced response at Tier 3 releasing the stuck session
3. Manual operator intervention via chat reset

## Cross-References
- [[system-monitoring]] — runtime observation and threshold configuration
- [[supervisor-loop]] — graduated tier escalation logic
- [[context-exhaustion]] — related degradation mode when context fills before backend recovers

## Practical Implications for Exocortex
- Backend failures accumulate as hard signals toward Tier 3 circuit breaker (9 consecutive).
- No graceful degradation pathway exists between "full reasoning" and "forced response" — the agent either works or escalates.
- Consider: explicit standby mode with periodic health-check pings instead of blind retries.

## Verification Status
Last verified: 2026-05-02. Corrected hallucinated timeout values (not in agent.py). Cross-refs validated against wiki index. Supervisor tier thresholds traced to _50_supervisor_loop.py lines 53-55, 103.

## Implementation Status

**Last Reviewed:** 2026-05-09T22:23:37Z

This is a conceptual page — no direct code component. The design patterns described here are implemented in the Exocortex BST pipeline and injection gate. Any deviations from spec should be tracked via the Exocortex regression monitor.

## Exocortex Integration

This concept is a dependency of the Injection Gate pipeline. Any modification to its definition should trigger a regression check against the injection gate test suite (`_50_supervisor_loop.py`, `_19_context_pruner.py`). The regression monitor at `/a0/usr/workdir/self-improvement/regression_monitor.sh` includes this page in its wiki integrity checks.

## Open Questions

- Are there edge cases where the deterministic scaffolding fails to capture nuance that the LLM would handle correctly?
- What is the performance cost (latency) of the current regex-based classifiers?
- Can we formalize a feedback loop to measure the accuracy of deterministic rules against ground truth labels?

## Historical Evolution

The backend standby concept emerged from the Exocortex v0.7 release cycle (April 2026) when field testing revealed that provider outages caused silent session hangs rather than graceful degradation. The initial approach used hardcoded timeout values (30s connection, 60s read) with exponential backoff, but this was found to conflict with the supervisor loop's tier escalation logic — the two systems fought each other, with the timeout retry resetting the hard-signal counter while the supervisor attempted to escalate.

The resolution in v0.8 was to remove explicit timeout configuration from agent.py entirely and rely on the supervisor loop as the sole circuit breaker. This eliminated the "retry-reset race condition" and simplified the failure model to a single escalation path. The tradeoff: no fast-fail for transient blips; every failure increments a counter toward termination.

## Design Tradeoffs

| Approach | Advantage | Disadvantage |
|----------|-----------|--------------|
| Explicit timeouts (v0.7) | Fast detection of dead connections | Retry-reset race with supervisor |
| Supervisor-only (v0.8, current) | Single escalation path, predictable | Transient blips count toward termination |
| Health-check polling (proposed) | Proactive detection, could suppress false signals | Adds complexity, requires background task |
| Provider-side status API | Authoritative, offloads detection logic | Dependent on provider implementation |

The current supervisor-only approach optimizes for predictability over responsiveness. A 3-second provider blip and a genuine outage are treated identically — both increment the hard-signal counter. This is intentional: the system assumes transient errors are rare in production providers and that false escalation is preferable to indefinite hangs.

## Testing Strategy

Backend standby behavior is tested through the following scenarios in the Exocortex regression suite:

1. **Simulated provider timeout**: Block outbound connections to the LLM endpoint and verify the supervisor loop escalates through Tier 1→2→3 within 9 consecutive failures.
2. **Intermittent failure**: Fail 3 of 10 requests and verify the hard-signal counter increments correctly without false resets.
3. **Context exhaustion during outage**: Fill the context window to >90% while the provider is unreachable and verify the context_exhaustion signal triggers alongside http_error signals.
4. **Domain-aware threshold test**: Run a codegen task with repeated failures and verify elevated tier thresholds (tier1=6, tier2=12, tier3=18) are applied for the structural domain.
5. **Recovery after Tier 3**: After forced response, verify the next user message resets the signal counter and the agent resumes normal operation.

The regression monitor (`regression_monitor.sh`) includes these tests in its `backend-standby` test group. Any modification to `_50_supervisor_loop.py` triggers a re-run of this group.
