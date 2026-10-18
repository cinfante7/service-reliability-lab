# Service Reliability Lab

**Christopher Infante | Systems engineering · reliability analysis · continuity risk**

A reproducible, standard-library Python experiment examining a practical question:
**when a dependency slows down, do retries help users or prolong the failure?**
This is a synthetic portfolio demonstration, never a client engagement or production result.
It complements AI/ML and GRC work by examining the reliability of a dependency that could
serve model inference, and translating engineering evidence into a continuity decision.
There is no trained model, real inference traffic, or compliance certification here.

The strongest finding: during a seeded 30-second dependency outage, bounded retries
increased attempts per request from **1.000 to 1.667** and reduced successful responses
from **76.0% to 67.4%**. A circuit breaker reduced attempts to **0.725** and recovered
some availability (**70.0%**), while intentionally rejecting requests. It did **not**
beat the baseline's availability. Faster terminal responses alone are a misleading win.

## Run in under a minute

Python 3.10+; no dependencies, installations, credentials, network access, or paid APIs.
Validated locally with Python 3.13.7 on Windows.

```powershell
python -m unittest discover -s tests -v
python reliability_lab.py
python reliability_lab.py --output results-verify
Get-FileHash results/runs.json,results-verify/runs.json -Algorithm SHA256
```

Portable equivalent for the final check:
```console
python -c "from pathlib import Path; assert Path('results/runs.json').read_bytes() == Path('results-verify/runs.json').read_bytes(); print('Identical JSON')"
```

Committed [CSV](results/runs.csv) and [JSON](results/runs.json) contain all 27 runs:
three scenarios × three policies × seeds 17, 29, 43. Each policy receives identical
arrivals and per-request service draws within a scenario/seed. Change seeds with
`python reliability_lab.py --seeds 5 11 19 --output custom-results`.

## Actual results

Arithmetic mean of per-run metrics across the three seeds, rounded here only.
Availability means successful application responses / original requests. No fallback
response is counted as success. These are finite-horizon experiment metrics, not SLA estimates.

| Scenario | Policy | Availability | Success ≤1s | Attempts / request | Terminal latency p95 (s) |
|---|---|---:|---:|---:|---:|
| Healthy | Baseline | 100.0% | 100.0% | 1.000 | 0.156 |
| Healthy | Bounded | 100.0% | 100.0% | 1.000 | 0.156 |
| Healthy | Breaker | 100.0% | 100.0% | 1.000 | 0.156 |
| Outage | Baseline | 76.0% | 73.9% | 1.000 | 3.000 |
| Outage | Bounded | 67.4% | 66.8% | 1.667 | 1.650 |
| Outage | Breaker | 70.0% | 70.0% | 0.725 | 0.156 |
| Overload | Baseline | 4.0% | 1.5% | 1.000 | 3.000 |
| Overload | Bounded | 0.6% | 0.6% | 2.989 | 1.650 |
| Overload | Breaker | 9.9% | 9.9% | 0.186 | 0.550 |

Terminal latency includes fast failures and breaker rejections. Successful-only p95,
breaker rejection/open counts, failed attempts, dependency work seconds, and the final
reserved dependency completion time are in the raw files. Means of p95 values are
**not** pooled population percentiles. Three seeds are illustrative, not confidence intervals.

## Engineering evidence

- [Architecture and model contracts](docs/architecture.md): event flow, queue semantics, policy state and limitations.
- [Requirements-to-test traceability](docs/traceability.md): explicit acceptance criteria and automated evidence.
- [Business continuity decision brief](docs/decision-brief.md): risk, tradeoffs and staged validation.
- [Notion case-study draft](docs/notion-case-study.md): ready for integration after review.
- [Verification record](docs/verification.md): commands and reproducibility evidence.

No public repository or remote upload is created by this project. Suggested repository:
`service-reliability-lab`.
