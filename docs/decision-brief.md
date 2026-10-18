# Business continuity decision brief

**Decision proposed:** validate timeout budgets, cancellation and bounded admission
together before adding an aggressive breaker. Pair rejected work with an approved
deferred/manual workflow. Do not deploy these numeric settings directly.

**Current bounded-model evidence:** outage success averages 75.4% baseline, 74.1%
bounded retries and 70.0% breaker. Reserved work averages 224.6s, 226.2s and 64.6s;
the breaker protects capacity by rejecting a mean 144.7 requests/run. Its 0.725
attempts/request uses all arrivals, including requests with no admitted attempt.
The breaker delivers fewer successful requests than either alternative here.

Under overload, baseline succeeds on 62.5% of arrivals, bounded retries on 0.7%,
breaker on 9.9%. All miss an **illustrative**, noncontractual 80% success target.
Short timeouts leave dependency reservations behind; retry work competes for queue
slots. Baseline can wait for work that the short-timeout policies abandon. Timeout
and retry settings change together, so this comparison cannot isolate retry effects.

The original unbounded model produced more retry amplification; it is archived and
not used as the current decision evidence. This sensitivity to queue design argues
against selecting policies from attractive latency numbers alone.

| Risk | Candidate control | Evidence still needed |
|---|---|---|
| Abandoned work consumes scarce capacity | Effective cancellation, admission limits, attempt budget | Server traces and isolated fault-injection load tests |
| Aggressive breaker rejects critical requests | Priority admission, deferred/manual path | Approved service tiers and continuity exercise |
| Sustained overload | Capacity planning and backpressure | Real arrival/service distributions and queue/capacity sweeps |
| Fast failures make latency look healthy | Pair success latency with success, rejection and work counters | Instrumentation review and alert exercise |
| Retry duplicates non-idempotent actions | Deduplication or no retry | Dependency integrity contract and failure tests |

**Business implication for an AI-backed workflow:** a labeled manual or deferred path
may preserve service continuity when inference capacity is scarce. This is a proposed
workflow, not an implemented or measured fallback. There is no trained model here.

**Future pilot gate:** service owner defines success/latency SLOs and impact tiers;
continuity owner defines RTO and fallback workflow; engineering validates cancellation,
idempotency and longer outages. Agree guardrails and rollback criteria before the
pilot. These are proposed responsibilities, not actual approvals. No RPO is claimed:
the simulator has no persistent data or data-loss model. No compliance certification
or demonstrated failover is implied.
