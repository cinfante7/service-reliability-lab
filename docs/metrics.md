# Complete metric dictionary

Grain: **one simulation run** per scenario × policy × seed. Time units are simulated
seconds from experiment start. All arrivals occur in [0,duration); responses drain
afterward. Reports use arithmetic means of per-run metrics with equal seed weights;
they do not pool requests across seeds. Rates below use **all original arrivals**,
including queue and breaker rejections. Synthetic success fractions are not uptime.

| Output field | Definition / unit |
|---|---|
| scenario, policy | Experiment preset names; custom Scenario/Policy names for injected runs |
| seed | Nonnegative integer passed to Python random.Random |
| arrival_rate_s | Configured mean Poisson arrivals/second (metadata; injected fixture arrivals override it) |
| duration_s | Arrival generation horizon; responses and reservations may extend beyond it |
| capacity | Number of parallel dependency workers |
| outage_start_s, outage_end_s | Half-open impairment interval at service start; null if absent |
| impaired_service_s | Reserved service duration for attempts starting within outage; they fail |
| timeout_s | Per-attempt client timeout including queue waiting |
| retry_limit | Maximum retries beyond the initial attempt, 0..2 |
| breaker_enabled | Boolean; whether the breaker gates admission |
| failure_threshold | Consecutive observed current-generation failures needed to open |
| cooldown_s | Open duration before the next attempt can become the half-open probe |
| requests | Count of original arrivals, including requests never admitted |
| completed_requests | Unique terminal outcomes; must equal requests |
| successes | Original requests ending with a successful dependency response before/equal to cutoff |
| availability | successes / requests; a finite experiment success fraction |
| within_1s | Original requests succeeding with terminal latency ≤1s / requests |
| p95_success_s | Nearest-rank p95 of successful original-request latencies only |
| p95_terminal_s | Nearest-rank p95 of all terminal latencies, including fast rejection/failure |
| attempts | Admitted dependency reservations, initial and retry; excludes rejected attempts |
| attempts_per_request | attempts / requests, including zero-admission rejected requests in denominator |
| failed_attempts | Admitted reservations whose observed response is timeout/deadline/dependency failure; attempts − failed_attempts = successes |
| breaker_rejections | Requests terminated by open or busy half-open breaker (may already have earlier attempts) |
| breaker_opens | Transitions to open from threshold/probe failure/probe queue overflow, including reopen |
| queue_overflows | Requests terminated by an attempted admission to a full waiting queue; never retried |
| max_queue_depth | Maximum admitted reservations with service start > admission time; excludes active workers |
| queue_limit | Waiting-slot bound; zero allows only immediately runnable work |
| request_deadline_s | Total per-original-request budget; derived timeout/backoff bound unless explicitly provided |
| dependency_work_s | Sum of reserved service durations, including abandoned and post-horizon work; not CPU utilization |
| last_reserved_completion_s | Latest worker reservation end timestamp; zero if no work admitted |
| successes_arriving_after_75s | Count of successes whose original arrival ≥75s; coarse recovery sanity check, not RTO or recovery time |

For zero arrivals, rates are defined as **0 by convention**, not evidence of service
failure or success. Both p95 values are null when their population is empty. For
nonempty values x, nearest-rank p95 is sorted(x)[ceil(.95×len(x))−1]. A mean of seed
p95 values is not a pooled p95. Min/max sensitivity ranges are not confidence intervals.

## Trace-only outputs

With `trace=True`, `outcomes` lists one item per request ID, sorted by ID: `request`,
`arrival`, `completed_at`, `latency_s`, `reason`, `success`, `attempts`.
Latency = completed_at − original arrival, so retry backoff and prior failed attempts
are included. `trace` contains ordered records with `time`, `kind` and event-specific
fields. Admissions include `start`, `end`, `response`, `impaired`, `probe`, `generation`,
`queued`; responses include `success`, `probe`, `stale`; breaker transitions include
`old`, `new`, `reason`. `attempt` is zero-based. A stale response still ends/retries
its request but cannot alter current breaker state.

Terminal reasons are mutually exclusive: `success`, `deadline`, `attempts_exhausted`,
`queue_overflow`, `breaker_open`, `breaker_half_open`. A queue or breaker rejection
terminates the original request, even if it occurs on a retry. A successful service
ending exactly at cutoff counts as success. A retry event exactly at deadline does
not admit work. No duplicate completion is permitted.

## Sources for Notion integration

Implementation: `reliability_lab.py`; evidence: `results/runs.json` and `runs.csv`;
sensitivity: `results/sensitivity/runs.json` and `runs.csv`; generated readable
summaries: `results/summary.md` and `results/report.html`; behavioral evidence:
`tests/test_invariants.py`, `tests/test_reliability.py`; reproducibility:
`verify_reproduction.py`, `docs/verification.md`; decision context:
`docs/decision-brief.md`. Archived legacy evidence is explicitly under
`results/legacy-unbounded/` and must not be mixed with current bounded metrics.
