"""Deterministic bounded-queue discrete-event reliability experiment."""
from __future__ import annotations
import argparse
import csv
import heapq
import json
import math
import random
from dataclasses import dataclass, replace
from pathlib import Path


def positive(value, name, zero=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0 or (not zero and value == 0)):
        raise ValueError(f'{name} must be finite and {"nonnegative" if zero else "positive"}')


def integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f'{name} must be an integer >= {minimum}')


@dataclass(frozen=True)
class Policy:
    name: str
    timeout: float
    retries: int
    breaker: bool = False
    deadline: float | None = None
    failure_threshold: int = 5
    cooldown: float = 5.0

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError('Policy name must be nonempty')
        positive(self.timeout, 'timeout')
        integer(self.retries, 'retries')
        if self.retries > 2:
            raise ValueError('Supported retry count is 0..2')
        if type(self.breaker) is not bool:
            raise ValueError('breaker must be boolean')
        if self.deadline is not None:
            positive(self.deadline, 'deadline')
        integer(self.failure_threshold, 'failure_threshold', 1)
        positive(self.cooldown, 'cooldown')
        positive(self.request_budget, 'derived request budget')

    @property
    def request_budget(self):
        return (self.deadline if self.deadline is not None else
                self.timeout * (1 + self.retries) + sum(.1 * 2 ** i for i in range(self.retries)))


@dataclass(frozen=True)
class Scenario:
    name: str
    rate: float = 4
    duration: float = 120
    capacity: int = 6
    queue_limit: int = 24
    outage: tuple[float, float] | None = None
    impaired_service: float = 2.0

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError('Scenario name must be nonempty')
        positive(self.rate, 'rate', True)
        positive(self.duration, 'duration')
        integer(self.capacity, 'capacity', 1)
        integer(self.queue_limit, 'queue_limit')
        positive(self.impaired_service, 'impaired_service')
        if self.outage is not None:
            if not isinstance(self.outage, (tuple, list)) or len(self.outage) != 2:
                raise ValueError('outage must be a (start, end) pair')
            positive(self.outage[0], 'outage start', True)
            positive(self.outage[1], 'outage end')
            if self.outage[1] <= self.outage[0]:
                raise ValueError('outage end must follow start')


POLICIES = (Policy('baseline', 3.0, 0), Policy('bounded', .45, 2),
            Policy('breaker', .45, 2, True))
SCENARIOS = {'healthy': Scenario('healthy'),
             'outage': Scenario('outage', outage=(40, 70)),
             'overload': Scenario('overload', rate=80)}


def percentile(values, fraction):
    """Nearest-rank percentile; null for an empty population."""
    positive(fraction, 'percentile fraction')
    if fraction > 1:
        raise ValueError('Percentile fraction must be in (0, 1]')
    return sorted(values)[math.ceil(len(values) * fraction) - 1] if values else None


def simulate(policy, scenario='outage', seed=17, duration=None, capacity=None,
             queue_limit=None, *, arrivals=None, demands=None, trace=False):
    """Explicit arrivals/demands support hand-checkable experiments, never real traffic."""
    if not isinstance(policy, Policy):
        raise ValueError('policy must be a Policy')
    if isinstance(scenario, str):
        if scenario not in SCENARIOS:
            raise ValueError('Unknown scenario')
        config = SCENARIOS[scenario]
    elif isinstance(scenario, Scenario):
        config = scenario
    else:
        raise ValueError('scenario must be a name or Scenario')
    overrides = {k: v for k, v in dict(duration=duration, capacity=capacity,
                                      queue_limit=queue_limit).items() if v is not None}
    config = replace(config, **overrides)
    integer(seed, 'seed')
    if type(trace) is not bool:
        raise ValueError('trace must be boolean')
    rng = random.Random(seed)
    if arrivals is None:
        if config.rate * config.duration > 1_000_000:
            raise ValueError('Generated workload exceeds one million expected requests')
        arrivals = []
        t = 0.0
        while config.rate > 0:
            t += rng.expovariate(config.rate)
            if t >= config.duration:
                break
            arrivals.append(t)
            if len(arrivals) > 1_000_000:
                raise ValueError('Generated workload exceeds one million requests')
    else:
        if not isinstance(arrivals, (list, tuple)):
            raise ValueError('arrivals must be a sequence')
        arrivals = list(arrivals)
        for i, arrival in enumerate(arrivals):
            positive(arrival, 'arrival', True)
            if arrival >= config.duration or (i and arrival < arrivals[i - 1]):
                raise ValueError('arrivals must be ordered and within [0, duration)')
    if demands is None:
        # Common random numbers across policies; admission does not consume RNG.
        demands = [[rng.uniform(.08, .16) for _ in range(3)] for _ in arrivals]
    else:
        if not isinstance(demands, (list, tuple)) or len(demands) != len(arrivals):
            raise ValueError('One demand row is required per request')
        for row in demands:
            if not isinstance(row, (list, tuple)) or len(row) < 1 + policy.retries:
                raise ValueError('Each demand row must cover the policy attempt budget')
            for service in row:
                positive(service, 'service demand')

    servers = [0.0] * config.capacity
    heapq.heapify(servers)
    queued_starts, events, records = [], [], []
    sequence = 0

    def record(now, kind, **details):
        if trace:
            records.append(dict(time=now, kind=kind, **details))

    def schedule(time, kind, request, attempt, payload=None):
        nonlocal sequence
        positive(time, 'event time', True)
        sequence += 1
        heapq.heappush(events, (time, sequence, kind, request, attempt, payload))

    for request, arrival in enumerate(arrivals):
        schedule(arrival, 'attempt', request, 0)
    outcomes = {}
    per_request_attempts = [0] * len(arrivals)
    attempts = rejects = overflows = failures = opens = max_queue = 0
    work = 0.0
    failure_streak = 0
    open_until = 0.0
    state = 'closed'
    generation = 0

    def transition(now, new_state, reason):
        nonlocal state
        record(now, 'breaker_transition', old=state, new=new_state, reason=reason)
        state = new_state

    def finish(request, now, reason):
        if request in outcomes:
            raise AssertionError('Duplicate request completion')
        if now - arrivals[request] > policy.request_budget + 1e-9:
            raise AssertionError('Request deadline exceeded')
        outcome = dict(request=request, arrival=arrivals[request], completed_at=now,
                       latency_s=now - arrivals[request], reason=reason,
                       success=reason == 'success', attempts=per_request_attempts[request])
        outcomes[request] = outcome
        record(now, 'completion', **outcome)

    while events:
        now, _, kind, request, attempt, payload = heapq.heappop(events)
        deadline = arrivals[request] + policy.request_budget
        positive(deadline, 'absolute request deadline')
        if kind == 'attempt':
            record(now, 'attempt_requested', request=request, attempt=attempt)
            if now >= deadline:
                finish(request, now, 'deadline')
                continue
            probe = False
            if policy.breaker:
                if state == 'open' and now >= open_until:
                    transition(now, 'half_open', 'cooldown_elapsed')
                    probe = True
                elif state != 'closed':
                    rejects += 1
                    finish(request, now, 'breaker_' + state)
                    continue
            while queued_starts and queued_starts[0] <= now:
                heapq.heappop(queued_starts)
            if servers[0] > now and len(queued_starts) >= config.queue_limit:
                overflows += 1
                if probe:
                    open_until = now + policy.cooldown
                    positive(open_until, 'breaker reopen time')
                    generation += 1
                    opens += 1
                    transition(now, 'open', 'probe_queue_overflow')
                finish(request, now, 'queue_overflow')
                continue
            attempts += 1
            per_request_attempts[request] += 1
            available = heapq.heappop(servers)
            start = max(now, available)
            if start > now:
                heapq.heappush(queued_starts, start)
                max_queue = max(max_queue, len(queued_starts))
            impaired = config.outage is not None and config.outage[0] <= start < config.outage[1]
            service = config.impaired_service if impaired else demands[request][attempt]
            end = start + service
            positive(end, 'reservation completion time')
            heapq.heappush(servers, end)
            work += service
            positive(work, 'accumulated dependency work')
            cutoff = min(now + policy.timeout, deadline)
            success = not impaired and end <= cutoff
            response = min(end, cutoff)
            record(now, 'attempt_admitted', request=request, attempt=attempt, start=start,
                   end=end, response=response, impaired=impaired, probe=probe,
                   generation=generation, queued=len(queued_starts))
            schedule(response, 'response', request, attempt, (success, probe, generation))
        else:
            success, probe, request_generation = payload
            failures += not success
            record(now, 'attempt_response', request=request, attempt=attempt, success=success,
                   probe=probe, stale=request_generation != generation)
            if policy.breaker and request_generation == generation:
                failure_streak = 0 if success else failure_streak + 1
                if success and probe:
                    transition(now, 'closed', 'probe_succeeded')
                if not success and (probe or failure_streak >= policy.failure_threshold):
                    open_until = now + policy.cooldown
                    positive(open_until, 'breaker reopen time')
                    generation += 1
                    failure_streak = 0
                    opens += 1
                    transition(now, 'open', 'probe_failed' if probe else 'failure_threshold')
            if success:
                finish(request, now, 'success')
            elif now >= deadline:
                finish(request, now, 'deadline')
            elif attempt < policy.retries:
                schedule(min(now + .1 * 2 ** attempt, deadline), 'attempt', request, attempt + 1)
            else:
                finish(request, now, 'attempts_exhausted')

    if set(outcomes) != set(range(len(arrivals))):
        raise AssertionError('Request conservation failed')
    ordered = [outcomes[i] for i in range(len(arrivals))]
    successful = [o['latency_s'] for o in ordered if o['success']]
    latencies = [o['latency_s'] for o in ordered]
    count = len(arrivals)
    result = dict(scenario=config.name, seed=seed, policy=policy.name, requests=count,
                  arrival_rate_s=config.rate, duration_s=config.duration, capacity=config.capacity,
                  outage_start_s=config.outage[0] if config.outage else None,
                  outage_end_s=config.outage[1] if config.outage else None,
                  impaired_service_s=config.impaired_service, timeout_s=policy.timeout,
                  retry_limit=policy.retries, breaker_enabled=policy.breaker,
                  failure_threshold=policy.failure_threshold, cooldown_s=policy.cooldown,
                  successes=len(successful), availability=len(successful) / count if count else 0,
                  within_1s=sum(x <= 1 for x in successful) / count if count else 0,
                  p95_success_s=percentile(successful, .95),
                  p95_terminal_s=percentile(latencies, .95), attempts=attempts,
                  attempts_per_request=attempts / count if count else 0,
                  failed_attempts=failures, breaker_rejections=rejects, breaker_opens=opens,
                  queue_overflows=overflows, max_queue_depth=max_queue, queue_limit=config.queue_limit,
                  request_deadline_s=policy.request_budget, dependency_work_s=work,
                  last_reserved_completion_s=max(servers),
                  successes_arriving_after_75s=sum(o['success'] and o['arrival'] >= 75 for o in ordered),
                  completed_requests=len(ordered))
    if trace:
        result.update(trace=records, outcomes=ordered)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('results'))
    parser.add_argument('--seeds', type=int, nargs='+', default=[17, 29, 43])
    args = parser.parse_args()
    rows = [simulate(policy, scenario, seed) for scenario in SCENARIOS
            for seed in args.seeds for policy in POLICIES]
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'runs.json').write_text(json.dumps(rows, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')
    with (args.output / 'runs.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    print('scenario policy availability timely<=1s attempts/request p95-terminal')
    for scenario in SCENARIOS:
        for policy in POLICIES:
            group = [r for r in rows if r['scenario'] == scenario and r['policy'] == policy.name]
            mean = lambda key: sum(r[key] for r in group) / len(group)
            print(f'{scenario:8} {policy.name:8} {mean("availability"):.3f} '
                  f'{mean("within_1s"):.3f} {mean("attempts_per_request"):.3f} '
                  f'{mean("p95_terminal_s"):.3f}')


if __name__ == '__main__':
    main()
