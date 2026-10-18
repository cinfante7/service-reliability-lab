# Requirements-to-test traceability

Run `python -m unittest discover -s tests -v`. Tests use only `unittest`.

| ID | Requirement and acceptance criterion | Automated evidence in tests/test_reliability.py |
|---|---|---|
| R1 | Identical seed/policy produces identical complete metrics; common arrival counts across policies | test_seed_reproducibility_and_common_arrivals |
| R2 | Healthy low-rate traffic has 100% success, one attempt/request and no breaker opens | test_healthy_requests_all_succeed_without_retries |
| R3 | Every original request terminates exactly once; attempts ≤ requests × (1+retries); timely success ≤ success; terminal bounds hold | test_accounting_and_bounds_all_scenarios |
| R4 | Outage exposes retry amplification; breaker reduces reserved work and rejects traffic; successful post-recovery arrivals exist | test_timeout_retry_amplification_and_breaker_shedding |
| R5 | Breaker cannot meet 80% success under sustained overload | test_overload_breaker_is_not_capacity_solution |
| R6 | A timeout shorter than every service demand yields zero successes and null success latency | test_explicit_timeout_failure_has_no_success_latency |
| R7 | Empty samples have null percentile; nearest-rank p95 works; invalid capacity and policy bounds are rejected | test_empty_population_and_input_validation |
| R8 | Recorded artifacts match a second complete execution byte for byte | Commands and hashes in verification.md |

R4 and R5 are regression checks for the chosen synthetic scenarios, not universal
claims about policies. R3 checks all three scenarios and policies at seed 17; the
recorded comparison additionally exercises seeds 29 and 43. Tests do not establish
distributed-system correctness or cover all breaker event interleavings.
