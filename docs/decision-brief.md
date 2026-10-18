# Business continuity decision brief

**Decision proposed:** for an idempotent, latency-sensitive dependency without effective
cancellation, evaluate circuit breaking alongside a request budget, admission control
and an approved degraded workflow. Do not deploy these numeric settings directly.

**Evidence:** in the simulated outage, retries increase attempts/request by 66.7%
relative to baseline and reduce availability by 8.6 percentage points. The breaker
cuts admitted attempts below one per original request, but availability remains
6.0 points below baseline. Under continuous overload, all policies fail a hypothetical
80% success target; breaker success reaches only 9.9%. Short terminal latency is
partly fast rejection, and cannot substitute for service delivery.

**Business implication:** protecting a scarce dependency can preserve recovery capacity
while denying immediate work. For an AI inference workflow, an explicitly labeled
deferred/manual path may be preferable to repeated expensive inference attempts.
That fallback is a proposed operational design, not an implemented or measured result.
For non-idempotent writes, retrying without deduplication can add integrity risk.

| Risk | Candidate control | Evidence still required |
|---|---|---|
| Retry storm and stale queued work | Global attempt budget, cancellation, bounded queue | Fault-injection load test and server cancellation traces |
| Breaker rejects critical work | Priority admission, manual/deferred workflow | Stakeholder-approved service tiers and exercise results |
| Sustained overload | Capacity planning, rate limits, backpressure | Real arrival/service distributions and capacity sweep |
| Misleading latency dashboard | Pair successful-only latency with success rate, rejection and work counters | Instrumentation review and alert exercise |
| Incorrect recovery assumption | Recovery probes and supervised rollout | Dependency owner signoff and rollback drill |

**Acceptance gate for a future pilot:** service owner defines availability/latency SLOs
and impact tiers; continuity owner defines an RTO and fallback workflow; engineering
validates cancellation/idempotency and tests outages longer than cooldown. Capture
request, attempt, rejection, queue and recovery evidence under controlled load. Roll
back on agreed success-rate or load guardrail breaches. No RPO is claimed: this model
has no persistent data or data-loss behavior. Approval roles are proposed roles, not
actual signoffs. This demonstration supports risk reasoning, not audit certification.
