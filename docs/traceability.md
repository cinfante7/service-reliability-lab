# Requirements-to-test traceability

Run `python -m unittest discover -s tests -v`: **28 tests** at final hardening.
Method names below identify exact tests; no requirement is accepted solely by a
policy winning a benchmark. All test code is in `tests/test_invariants.py` (I) and
`tests/test_reliability.py` (R).

| ID | Requirement / acceptance criterion | Targeted evidence |
|---|---|---|
| R1 | Input conservation: each arrival has one unique terminal outcome; admitted successes + failed attempts = admissions | I: test_conservation_no_duplicate_completions_and_deadlines_across_seeds; runtime assertions |
| R2 | Per-request attempt count ≤ 1+retry limit; exact exponential backoff | I: test_retry_budget_and_exact_backoff_times; R1 test checks individual budgets |
| R3 | Total deadline clips in-flight response and backoff; no work admitted after deadline | I: test_deadline_clips_inflight_response; test_deadline_during_backoff_terminates_without_new_attempt |
| R4 | FCFS timing, finite queue bound, explicit terminal overflow, zero-slot admission | I: test_hand_computable_fcfs_queue_and_terminal_overflow; test_zero_queue_and_exact_service_boundary; R1 across all 27 runs |
| R5 | Timed-out reservations remain; no implicit cancellation | I: test_timeouts_do_not_cancel_dependency_reservations |
| R6 | Closed → open → half-open → closed; exactly one probe; half-open traffic rejected | I: test_closed_open_half_open_closed_and_single_probe |
| R7 | Failed probe / probe overflow reopens; stale success cannot close new generation | I: test_failed_probe_reopens; test_probe_queue_overflow_reopens_without_admission; test_stale_success_cannot_close_open_breaker |
| R8 | Threshold requires consecutive failures; success resets streak | I: test_threshold_requires_consecutive_failures; test_success_resets_consecutive_failure_streak |
| R9 | Equal-time event order deterministic; outage [start,end) applied at service start | I: test_equal_time_arrival_precedes_previously_unscheduled_response; test_outage_evaluated_at_service_start_and_end_is_exclusive |
| R10 | Reject malformed/negative/non-finite scenario, policy and injected workload inputs; reject derived overflow | I: all four ValidationTests methods (multiple subcases); R: test_empty_population_and_input_validation |
| R11 | Identical seeded full trace, different seeds change trace, all primary seed/scenario/policy combinations checked | I: test_deterministic_complete_trace_and_seed_sensitivity; R1; R: test_seed_reproducibility_and_common_arrivals |
| R12 | Healthy delivery and no extra attempts; explicit timeout failure; empty percentile null | R: test_healthy_requests_all_succeed_without_retries; test_explicit_timeout_failure_has_no_success_latency; test_empty_population_and_input_validation |
| R13 | Default bounded behavior and retained legacy amplification are kept distinct; overload still misses illustrative 80% target | R: test_bounded_default_does_not_assume_breaker_is_best; test_timeout_retry_amplification_and_breaker_shedding (explicit queue_limit=100000 legacy proxy); test_overload_breaker_is_not_capacity_solution |
| R14 | All artifact bytes reproduce and report reflects the complete populations | verify_reproduction.py; build_report.py population/headline checks; generated artifact hashes |

R1 checks **27 combinations**: three policies × three scenarios × seeds 17,29,43,
including each individual outcome and full completion trace. Sensitivity retains
all 90 runs for seeds 1–10. An independent read-only reviewer additionally executed
300 small-queue stress runs across 100 seeds and reported conservation, queue and
deadline checks passing. That review is supporting evidence, not an exhaustive proof.

The hand-computed FCFS case: one worker, one waiting slot, arrivals 0/.1/.2/.3,
service .5s, timeout2s. First finishes .5; second starts .5 and finishes1.0; third
and fourth overflow at arrival. Two successes, two terminal overflows, exactly 1s
reserved work, successful latencies .5/.9, nearest-rank successful p95=.9.
