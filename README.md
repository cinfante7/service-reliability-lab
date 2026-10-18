# Service Reliability Lab

**Christopher Infante | Systems engineering · reliability analysis · continuity risk**

A reproducible Python experiment examining a practical question: **when a dependency
slows down, do retries help users or prolong failure?** Entirely synthetic; never a
client engagement or production result. It complements AI/ML and GRC work through
dependency reliability and evidence-backed continuity decisions. No trained model,
real inference traffic, or compliance certification is claimed.

**Bounded queue admission changes the policy comparison.** With a 24-slot waiting
queue, outage success averages **75.4% baseline, 74.1% bounded retries, and 70.0%
breaker**. The breaker reserves less work while rejecting more requests. Under
sustained overload, success is **62.5%, 0.7%, and 9.9%**, respectively. Protecting
capacity and delivering requests are distinct objectives.

Open the [static evidence report](results/report.html) in a browser, or read its
[generated tables](results/summary.md). All 27 primary runs and 90 additional seed
sensitivity runs are retained. [Original unbounded runs](results/legacy-unbounded/runs.json)
are archived separately; their stronger retry amplification is not the default
bounded model's finding. The queue requirement changed the model, not a desired winner.

## Reproduce

Python 3.10+; validated on Python **3.13.7**, Windows. Standard library only: no
installation, dependencies, credentials, external datasets, networking or paid APIs
are needed to run experiments or build the report.

```console
python -m unittest discover -s tests -v
python reliability_lab.py
python reliability_lab.py --output results/sensitivity --seeds 1 2 3 4 5 6 7 8 9 10
python build_report.py
python verify_reproduction.py
```

The final command regenerates both populations into temporary directories and checks
JSON/CSV bytes against recorded results. It also checks deterministic report rebuilds.
The 28-test suite includes targeted timing fixtures and full-trace invariants across
all 27 primary scenario/policy/seed combinations.

The HTML opens directly from disk and has no JavaScript, remote assets or fonts.
For an optional local preview:

```console
python -m http.server 8764 --bind 127.0.0.1
```

Open `http://127.0.0.1:8764/results/report.html`; stop with Ctrl+C.
Experiment CLI supports other seeds/output folders, e.g.
`python reliability_lab.py --seeds 5 11 19 --output custom-results`.
Report generation intentionally uses the documented primary and sensitivity populations.

## What the outputs mean

Availability is successful responses / **all original arrivals**, including queue and
breaker rejections. Attempts/request can be below one because rejected requests may
consume no dependency attempt. No degraded fallback counts as success. These finite
experiment success fractions are not uptime SLAs.

Timeouts do not cancel dependency reservations. Retries can consume scarce queue
slots after the client has stopped waiting. The 0.45s attempt timeout may expire in
the queue when the baseline's 3s timeout would succeed. This comparison changes
timeouts and retries together; it does not isolate retries alone. Queue overflow
terminates the request without retry and limits amplification.

Terminal latency includes fast failures. Read it alongside successful-only latency,
success rate, breaker rejection, overflow and reserved work. Summary tables average
per-run metrics; means of p95 values are not pooled percentiles. Seed ranges are
descriptive, not confidence intervals. No universal policy improvement is promised.

## Inspect the engineering evidence

- [Architecture and contracts](docs/architecture.md): event flow, bounded queue, deadlines and breaker state.
- [Requirements-to-test traceability](docs/traceability.md): acceptance criteria and targeted tests.
- [Full metric dictionary](docs/metrics.md): every field, denominator, unit and terminal reason.
- [Continuity decision brief](docs/decision-brief.md): implications and validation gates.
- [Verification record](docs/verification.md): exact commands, independent review and browser QA.
- [Notion case-study draft](docs/notion-case-study.md): prepared for later integration.
- [Raw primary CSV](results/runs.csv) / [JSON](results/runs.json); [all sensitivity runs](results/sensitivity/runs.json).

Suggested repository: **service-reliability-lab**. Local Git only; no remote repository
or upload has been created.
