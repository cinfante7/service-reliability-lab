# Generated results summary

Synthetic experiments; never production results.

With a 24-slot waiting queue, outage success averages 75.4% for baseline, 74.1% for bounded retries and 70.0% for the breaker. The breaker reserves less dependency work but rejects requests that the other policies can serve. Under overload, baseline succeeds on 62.5% of arrivals; bounded retries achieve 0.7% and the breaker 9.9%. None meets the illustrative 80% success target.

## Primary seeds: 17, 29, 43

| Scenario | Policy | Success % | Success ≤1s % | Attempts/request | Success p95 s | Terminal p95 s | Queue overflows | Breaker rejects | Work s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| healthy | baseline | 100.0 | 100.0 | 1.000 | 0.156 | 0.156 | 0.0 | 0.0 | 58.0 |
| healthy | bounded | 100.0 | 100.0 | 1.000 | 0.156 | 0.156 | 0.0 | 0.0 | 58.0 |
| healthy | breaker | 100.0 | 100.0 | 1.000 | 0.156 | 0.156 | 0.0 | 0.0 | 58.0 |
| outage | baseline | 75.4 | 74.0 | 0.976 | 0.158 | 3.000 | 11.7 | 0.0 | 224.6 |
| outage | bounded | 74.1 | 74.0 | 0.980 | 0.157 | 1.200 | 109.3 | 0.0 | 226.2 |
| outage | breaker | 70.0 | 70.0 | 0.725 | 0.156 | 0.156 | 0.0 | 144.7 | 64.6 |
| overload | baseline | 62.5 | 62.5 | 0.625 | 0.639 | 0.631 | 3612.0 | 0.0 | 722.8 |
| overload | bounded | 0.7 | 0.6 | 0.629 | 1.550 | 1.650 | 8933.3 | 0.0 | 727.4 |
| overload | breaker | 9.9 | 9.9 | 0.164 | 0.432 | 0.550 | 213.3 | 8468.3 | 189.6 |

All cells are arithmetic means of per-run metrics. Means of p95 values are not pooled p95.

## Sensitivity seeds: 1–10 (all 90 runs)

| Scenario | Policy | Success % | Success ≤1s % | Attempts/request | Success p95 s | Terminal p95 s | Queue overflows | Breaker rejects | Work s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| healthy | baseline | 100.0 | 100.0 | 1.000 | 0.156 | 0.156 | 0.0 | 0.0 | 56.7 |
| healthy | bounded | 100.0 | 100.0 | 1.000 | 0.156 | 0.156 | 0.0 | 0.0 | 56.7 |
| healthy | breaker | 100.0 | 100.0 | 1.000 | 0.156 | 0.156 | 0.0 | 0.0 | 56.7 |
| outage | baseline | 76.6 | 75.0 | 0.988 | 0.158 | 3.000 | 5.9 | 0.0 | 223.5 |
| outage | bounded | 75.1 | 75.0 | 0.997 | 0.157 | 1.229 | 102.0 | 0.0 | 225.7 |
| outage | breaker | 71.9 | 71.9 | 0.747 | 0.156 | 0.157 | 0.0 | 132.5 | 67.1 |
| overload | baseline | 62.5 | 62.5 | 0.625 | 0.639 | 0.630 | 3614.3 | 0.0 | 722.9 |
| overload | bounded | 0.7 | 0.6 | 0.630 | 1.576 | 1.650 | 8939.7 | 0.0 | 727.7 |
| overload | breaker | 10.1 | 10.1 | 0.166 | 0.431 | 0.550 | 230.4 | 8433.9 | 191.3 |

| Scenario | Policy | Mean success | Per-seed min–max success |
| --- | --- | --- | --- |
| healthy | baseline | 100.0% | 100.0–100.0% |
| healthy | bounded | 100.0% | 100.0–100.0% |
| healthy | breaker | 100.0% | 100.0–100.0% |
| outage | baseline | 76.6% | 74.5–79.4% |
| outage | bounded | 75.1% | 72.7–78.4% |
| outage | breaker | 71.9% | 69.6–76.3% |
| overload | baseline | 62.5% | 61.6–63.0% |
| overload | bounded | 0.7% | 0.5–1.1% |
| overload | breaker | 10.1% | 9.4–10.5% |

Ranges describe these seeds; they are not confidence intervals.

Primary JSON SHA-256: `6062f2b3bb635225671e1f99a21bd9066e8cc9bf3be54a6810c21aacca583ce2`
