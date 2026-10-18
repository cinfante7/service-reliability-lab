"""Seeded discrete-event reliability experiment; Python standard library only."""
from __future__ import annotations

import argparse
import csv
import heapq
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Policy:
    name: str
    timeout: float
    retries: int
    breaker: bool = False

    def __post_init__(self):
        if self.timeout <= 0 or self.retries not in (0, 1, 2):
            raise ValueError('Timeout must be positive; supported retry count is 0..2')


POLICIES = (Policy('baseline', 3.0, 0), Policy('bounded', .45, 2),
            Policy('breaker', .45, 2, True))
SCENARIOS = {'healthy': (4, None), 'outage': (4, (40, 70)),
             'overload': (80, None)}


def percentile(values, fraction):
    """Nearest-rank percentile; empty populations are explicitly null."""
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)] if values else None


def simulate(policy, scenario='outage', seed=17, duration=120, capacity=6):
    if scenario not in SCENARIOS or duration <= 0 or capacity < 1:
        raise ValueError('Unknown scenario or invalid duration/capacity')
    rate, outage = SCENARIOS[scenario]
    rng = random.Random(seed)
    arrivals = []
    t = 0.0
    while True:
        t += rng.expovariate(rate)
        if t >= duration:
            break
        arrivals.append(t)
    # Draw service demands per request/attempt before policies diverge.
    demands = [[rng.uniform(.08, .16) for _ in range(3)] for _ in arrivals]
    servers = [0.0] * capacity
    heapq.heapify(servers)
    events = []
    sequence = 0

    def schedule(time, kind, request, attempt, payload=None):
        nonlocal sequence
        sequence += 1
        heapq.heappush(events, (time, sequence, kind, request, attempt, payload))

    for request, arrival in enumerate(arrivals):
        schedule(arrival, 'attempt', request, 0)
    latencies, successful, completion_times = [], [], []
    attempts = rejects = failures = opens = 0
    work = 0.0
    failure_streak = 0
    open_until = 0.0
    probe_inflight = False
    generation = 0

    def finish(request, now, success):
        latency = now - arrivals[request]
        latencies.append(latency)
        if success:
            successful.append(latency)
            completion_times.append((arrivals[request], now))

    while events:
        now, _, kind, request, attempt, payload = heapq.heappop(events)
        if kind == 'attempt':
            probe = False
            if policy.breaker and (now < open_until or probe_inflight):
                rejects += 1
                finish(request, now, False)
                continue
            if policy.breaker and open_until > 0:
                probe = True
                probe_inflight = True
            attempts += 1
            available = heapq.heappop(servers)
            start = max(now, available)
            impaired = outage is not None and outage[0] <= start < outage[1]
            service = 2.0 if impaired else demands[request][attempt]
            end = start + service
            heapq.heappush(servers, end)
            work += service
            success = not impaired and end <= now + policy.timeout
            response = min(end, now + policy.timeout)
            schedule(response, 'response', request, attempt, (success, probe, generation))
        else:
            success, probe, request_generation = payload
            failures += not success
            if policy.breaker and request_generation == generation:
                if probe:
                    probe_inflight = False
                failure_streak = 0 if success else failure_streak + 1
                if success and probe:
                    open_until = 0.0
                if not success and (probe or failure_streak >= 5):
                    open_until = now + 5.0
                    generation += 1
                    probe_inflight = False
                    failure_streak = 0
                    opens += 1
            if success:
                finish(request, now, True)
            elif attempt < policy.retries:
                schedule(now + .1 * 2 ** attempt, 'attempt', request, attempt + 1)
            else:
                finish(request, now, False)
    count = len(arrivals)
    timely = sum(x <= 1.0 for x in successful)
    return dict(scenario=scenario, seed=seed, policy=policy.name, requests=count,
                successes=len(successful), availability=len(successful) / count if count else 0,
                within_1s=timely / count if count else 0,
                p95_success_s=percentile(successful, .95),
                p95_terminal_s=percentile(latencies, .95), attempts=attempts,
                attempts_per_request=attempts / count if count else 0,
                failed_attempts=failures, breaker_rejections=rejects, breaker_opens=opens,
                dependency_work_s=work, last_reserved_completion_s=max(servers),
                successes_arriving_after_75s=sum(a >= 75 for a, _ in completion_times),
                completed_requests=len(latencies))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('results'))
    parser.add_argument('--seeds', type=int, nargs='+', default=[17, 29, 43])
    args = parser.parse_args()
    rows = [simulate(policy, scenario, seed) for scenario in SCENARIOS
            for seed in args.seeds for policy in POLICIES]
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'runs.json').write_text(json.dumps(rows, indent=2) + '\n', encoding='utf-8')
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
