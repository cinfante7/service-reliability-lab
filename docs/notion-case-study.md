# Service Reliability Lab — Christopher Infante

**Focus:** systems engineering, reproducible experiments, reliability controls and
business continuity decision support. Synthetic portfolio work only.

**Question:** can retries improve apparent responsiveness while reducing successful
delivery and consuming scarce dependency capacity?

**Built:** a standard-library Python discrete-event simulator with seeded arrivals,
six-worker capacity, a bounded 24-slot FIFO queue, terminal overflow, explicit request
deadlines, bounded backoff and a stateful single-probe circuit breaker. A static HTML
report is generated from 27 primary runs plus all 90 additional sensitivity runs.

**Measured outcome:** outage success averages 75.4% baseline, 74.1% bounded retries
and 70.0% breaker. The breaker reserves 64.6s of work versus 224.6s baseline but
rejects a mean 144.7 requests/run. Its 0.725 attempts/request includes all arrivals
in the denominator; some requests are rejected before any dependency admission.
Overload success is 62.5%, 0.7% and 9.9%, respectively. There is no universal winner.

**Engineering judgment:** timeout cancellation and queue admission matter as much as
retry count. Fast rejection can improve terminal latency while denying useful work.
The original unbounded model had stronger retry amplification; retaining it separately
shows how an explicit queue requirement changed the conclusion. Timeout and retry
settings vary together, so the comparison does not isolate retries alone.

**Validation:** 28 tests covering unique completion/conservation, retry and deadline
bounds, hand-computed timing, queue overflow, breaker transitions/generations,
malformed inputs, deterministic traces and multiple seeds. An independent native
reviewer stress-tested 300 additional small-queue runs and identified numeric overflow;
the issue was fixed with a regression test. Exact reproduction and browser visual
checks are recorded in docs/verification.md.

**AI/ML + GRC connection:** inference services are dependencies with capacity and
failure contracts. The lab demonstrates controls and evidence useful to continuity
decisions; it does not train a model or claim an audit certification.

**Integration sources:** results/report.html, results/summary.md, results/runs.csv,
results/sensitivity/runs.json, docs/metrics.md, docs/architecture.md,
docs/traceability.md and docs/decision-brief.md. Public repository, released with
Christopher Infante's approval: https://github.com/cinfante7/service-reliability-lab.
Notion integration is handled separately; this file is the source draft.
