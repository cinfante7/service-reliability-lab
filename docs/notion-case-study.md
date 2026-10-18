# Service Reliability Lab — Christopher Infante

**Portfolio focus:** systems engineering, reproducible experimentation, reliability
controls and business continuity decision support.

**Problem:** retry policies can appear responsive while increasing pressure on a slow
dependency. How should engineers balance successful delivery, latency and recovery load?

**What I built:** a deterministic discrete-event simulator in Python's standard library,
with FCFS service capacity, seeded arrivals, a timed outage, bounded retries and a
stateful circuit breaker. It compares 27 scenario/policy/seed runs and produces raw
CSV/JSON evidence. Seven automated tests cover reproducibility, accounting, timeout
bounds, healthy behavior, outage amplification and overload failure.

**Measured finding:** across three seeds, the outage baseline achieved 76.0% success
with 1.000 attempts/request. Bounded retries achieved 67.4% with 1.667 attempts/request.
The breaker achieved 70.0% with 0.725 attempts/request. Its fast responses include
rejections. No policy solved sustained overload.

**Engineering judgment:** reducing dependency pressure can protect recovery without
maximizing immediate availability. Pair latency dashboards with success and rejection
rates; use retry budgets, cancellation and admission controls; validate actual traffic
before choosing settings. For AI-backed workflows, apply the same dependency discipline
to inference services. This project does not train or benchmark an ML model.

**Evidence:** link the repository README, results/runs.csv, docs/architecture.md,
docs/traceability.md and docs/decision-brief.md after publication is approved.

**Scope disclosure:** entirely synthetic; no client or production results, credentials,
personal data, paid APIs or compliance claims. Local repository prepared; publication
and Notion integration remain separate actions.
