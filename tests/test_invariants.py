"""Targeted behavioral checks, including hand-computable injected workloads."""
import json
import unittest
from reliability_lab import POLICIES, Policy, Scenario, percentile, simulate


def tiny(policy, arrivals, demands, **kwargs):
    return simulate(policy, Scenario('tiny', rate=0, duration=10, **kwargs),
                    arrivals=arrivals, demands=demands, trace=True)


class InvariantTests(unittest.TestCase):
    def test_conservation_no_duplicate_completions_and_deadlines_across_seeds(self):
        for seed in (17, 29, 43):
            for scenario in ('healthy', 'outage', 'overload'):
                for policy in POLICIES:
                    with self.subTest(seed=seed, scenario=scenario, policy=policy.name):
                        r = simulate(policy, scenario, seed, trace=True)
                        completions = [e for e in r['trace'] if e['kind'] == 'completion']
                        self.assertEqual(len(completions), r['requests'])
                        self.assertEqual({e['request'] for e in completions}, set(range(r['requests'])))
                        self.assertEqual(len(r['outcomes']), r['requests'])
                        self.assertEqual(sum(o['attempts'] for o in r['outcomes']), r['attempts'])
                        self.assertEqual(r['attempts'] - r['failed_attempts'], r['successes'])
                        self.assertLessEqual(r['max_queue_depth'], r['queue_limit'])
                        for outcome in r['outcomes']:
                            self.assertLessEqual(outcome['attempts'], 1 + policy.retries)
                            self.assertGreaterEqual(outcome['latency_s'], 0)
                            self.assertLessEqual(outcome['latency_s'], policy.request_budget + 1e-9)
                        self.assertEqual(sum(o['reason'].startswith('breaker_') for o in r['outcomes']),
                                         r['breaker_rejections'])
                        self.assertEqual(sum(o['reason'] == 'queue_overflow' for o in r['outcomes']),
                                         r['queue_overflows'])

    def test_hand_computable_fcfs_queue_and_terminal_overflow(self):
        r = tiny(Policy('p', 2, 0), [0, .1, .2, .3], [[.5]] * 4,
                 capacity=1, queue_limit=1)
        self.assertEqual([o['completed_at'] for o in r['outcomes']], [.5, 1., .2, .3])
        self.assertEqual([o['reason'] for o in r['outcomes']],
                         ['success', 'success', 'queue_overflow', 'queue_overflow'])
        self.assertEqual((r['attempts'], r['successes'], r['max_queue_depth']), (2, 2, 1))
        self.assertEqual(r['dependency_work_s'], 1.)
        self.assertEqual(r['p95_success_s'], .9)

    def test_zero_queue_and_exact_service_boundary(self):
        r = tiny(Policy('p', 2, 0), [0, .1, .5], [[.5]] * 3,
                 capacity=1, queue_limit=0)
        self.assertEqual([o['reason'] for o in r['outcomes']],
                         ['success', 'queue_overflow', 'success'])
        self.assertEqual(r['max_queue_depth'], 0)

    def test_timeouts_do_not_cancel_dependency_reservations(self):
        r = tiny(Policy('p', .1, 2), [0], [[1, 1, 1]], capacity=1, queue_limit=1)
        self.assertEqual(r['attempts'], 2)
        self.assertEqual(r['queue_overflows'], 1)
        self.assertEqual(r['dependency_work_s'], 2)
        self.assertEqual(r['last_reserved_completion_s'], 2)
        self.assertAlmostEqual(r['outcomes'][0]['completed_at'], .5)

    def test_deadline_clips_inflight_response(self):
        r = tiny(Policy('p', 2, 2, deadline=.3), [0], [[1, 1, 1]])
        self.assertEqual(r['outcomes'][0]['reason'], 'deadline')
        self.assertEqual(r['outcomes'][0]['completed_at'], .3)
        self.assertEqual(r['attempts'], 1)
        self.assertEqual(r['dependency_work_s'], 1)

    def test_deadline_during_backoff_terminates_without_new_attempt(self):
        r = tiny(Policy('p', .1, 2, deadline=.15), [0], [[1, 1, 1]])
        self.assertEqual(r['outcomes'][0]['reason'], 'deadline')
        self.assertEqual(r['outcomes'][0]['completed_at'], .15)
        self.assertEqual(r['attempts'], 1)

    def test_retry_budget_and_exact_backoff_times(self):
        r = tiny(Policy('p', .1, 2), [0], [[1, 1, 1]], capacity=3)
        admitted = [e for e in r['trace'] if e['kind'] == 'attempt_admitted']
        self.assertEqual([e['attempt'] for e in admitted], [0, 1, 2])
        for actual, expected in zip([e['time'] for e in admitted], [0, .2, .5]):
            self.assertAlmostEqual(actual, expected)
        self.assertAlmostEqual(r['outcomes'][0]['completed_at'], .6)

    def test_closed_open_half_open_closed_and_single_probe(self):
        p = Policy('p', .5, 0, True, failure_threshold=1, cooldown=1)
        r = tiny(p, [0, .2, 1.1, 1.15, 1.4], [[.2]] * 5,
                 outage=(0, 1), impaired_service=.1)
        transitions = [e for e in r['trace'] if e['kind'] == 'breaker_transition']
        self.assertEqual([(e['old'], e['new']) for e in transitions],
                         [('closed', 'open'), ('open', 'half_open'), ('half_open', 'closed')])
        self.assertEqual([o['reason'] for o in r['outcomes']],
                         ['attempts_exhausted', 'breaker_open', 'success', 'breaker_half_open', 'success'])
        self.assertEqual(sum(e.get('probe', False) for e in r['trace']
                             if e['kind'] == 'attempt_admitted'), 1)
        self.assertEqual(r['attempts_per_request'], .6)

    def test_failed_probe_reopens(self):
        p = Policy('p', .5, 0, True, failure_threshold=1, cooldown=1)
        r = tiny(p, [0, 1.11, 1.3], [[.2]] * 3,
                 outage=(0, 5), impaired_service=.1)
        transitions = [e for e in r['trace'] if e['kind'] == 'breaker_transition']
        self.assertEqual([e['new'] for e in transitions], ['open', 'half_open', 'open'])
        self.assertEqual(transitions[-1]['reason'], 'probe_failed')
        self.assertEqual(r['outcomes'][-1]['reason'], 'breaker_open')

    def test_stale_success_cannot_close_open_breaker(self):
        p = Policy('p', 1, 0, True, failure_threshold=1, cooldown=1)
        r = tiny(p, [0, .01, .5], [[.4], [.1], [.1]],
                 outage=(.01, .2), impaired_service=.05)
        self.assertEqual(r['outcomes'][0]['reason'], 'success')
        self.assertEqual(r['outcomes'][2]['reason'], 'breaker_open')
        responses = [e for e in r['trace'] if e['kind'] == 'attempt_response']
        self.assertTrue(next(e for e in responses if e['request'] == 0)['stale'])
        self.assertEqual([e['new'] for e in r['trace'] if e['kind'] == 'breaker_transition'], ['open'])

    def test_success_resets_consecutive_failure_streak(self):
        p = Policy('p', .5, 0, True, failure_threshold=2)
        r = tiny(p, [0, 2, 4], [[1], [.1], [1]])
        self.assertEqual(r['breaker_opens'], 0)
        self.assertEqual(r['successes'], 1)

    def test_threshold_requires_consecutive_failures(self):
        p = Policy('p', .5, 0, True, failure_threshold=2)
        r = tiny(p, [0, 1, 2], [[1]] * 3)
        transitions = [e for e in r['trace'] if e['kind'] == 'breaker_transition']
        self.assertEqual(len(transitions), 1)
        self.assertEqual(transitions[0]['time'], 1.5)
        self.assertEqual(r['outcomes'][2]['reason'], 'breaker_open')

    def test_probe_queue_overflow_reopens_without_admission(self):
        p = Policy('p', .1, 0, True, failure_threshold=1, cooldown=.1)
        r = tiny(p, [0, 0, .3], [[1]] * 3, capacity=1, queue_limit=1)
        transitions = [e for e in r['trace'] if e['kind'] == 'breaker_transition']
        self.assertEqual([e['new'] for e in transitions], ['open', 'half_open', 'open'])
        self.assertEqual(transitions[-1]['reason'], 'probe_queue_overflow')
        self.assertEqual(r['attempts'], 2)
        self.assertEqual(r['outcomes'][2]['reason'], 'queue_overflow')

    def test_equal_time_arrival_precedes_previously_unscheduled_response(self):
        p = Policy('p', .5, 0, True, failure_threshold=1)
        r = tiny(p, [0, .1], [[.1]] * 2, outage=(0, 1), impaired_service=.1)
        self.assertEqual(r['attempts'], 2)
        events = [e['kind'] for e in r['trace'] if e['time'] == .1]
        self.assertEqual(events[:3], ['attempt_requested', 'attempt_admitted', 'attempt_response'])

    def test_deterministic_complete_trace_and_seed_sensitivity(self):
        a = simulate(POLICIES[2], seed=17, trace=True)
        b = simulate(POLICIES[2], seed=17, trace=True)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        self.assertEqual([e['time'] for e in a['trace']], sorted(e['time'] for e in a['trace']))
        self.assertNotEqual(a['trace'], simulate(POLICIES[2], seed=29, trace=True)['trace'])

    def test_outage_evaluated_at_service_start_and_end_is_exclusive(self):
        r = tiny(Policy('p', 3, 0), [0, .5, 1.], [[.1]] * 3,
                 capacity=1, queue_limit=2, outage=(0, 1), impaired_service=.5)
        self.assertEqual([o['success'] for o in r['outcomes']], [False, False, True])


class ValidationTests(unittest.TestCase):
    def test_finite_inputs_cannot_emit_infinite_derived_metrics(self):
        with self.assertRaises(ValueError):
            Policy('huge', 1e308, 2)
        with self.assertRaises(ValueError):
            tiny(Policy('p', 1, 0), [0, 0, 0], [[1e308]] * 3, capacity=3)
        with self.assertRaises(ValueError):
            tiny(Policy('p', 1, 0), [0, 1], [[1e308]] * 2, capacity=1)
        with self.assertRaises(ValueError):
            simulate(Policy('huge', 9e307, 0), Scenario('large', duration=1e308),
                     arrivals=[9e307], demands=[[1]])
        with self.assertRaises(ValueError):
            simulate(POLICIES[0], Scenario('too_large', rate=1e308))

    def test_malformed_and_negative_scenario_inputs(self):
        cases = [dict(rate=-1), dict(rate=float('nan')), dict(rate=float('inf')),
                 dict(duration=0), dict(duration=-1), dict(duration='120'),
                 dict(capacity=0), dict(capacity=1.5), dict(capacity=True),
                 dict(queue_limit=-1), dict(queue_limit=2.5), dict(queue_limit=False),
                 dict(outage=(2, 1)), dict(outage=(-1, 2)), dict(outage=(1, 1)),
                 dict(outage='bad'), dict(outage=(0, float('nan'))),
                 dict(impaired_service=0), dict(impaired_service=float('inf'))]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Scenario('bad', **kwargs)
        self.assertEqual(simulate(POLICIES[0], Scenario('zero', rate=0))['requests'], 0)

    def test_malformed_policy_inputs(self):
        for kwargs in (dict(timeout=float('nan')), dict(timeout=float('inf')),
                       dict(timeout=True), dict(retries=True), dict(retries=1.0),
                       dict(retries=-1), dict(retries=3), dict(deadline=-1),
                       dict(breaker=1), dict(failure_threshold=0), dict(cooldown=0)):
            params = dict(name='p', timeout=1, retries=0)
            params.update(kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Policy(**params)

    def test_malformed_run_and_workload_inputs(self):
        cases = [dict(scenario='unknown'), dict(scenario=None), dict(seed=-1),
                 dict(seed=True), dict(duration=float('inf')), dict(trace=1),
                 dict(arrivals=[-1]), dict(arrivals=[2, 1]), dict(arrivals=[120]),
                 dict(arrivals=[float('nan')]), dict(arrivals='bad'),
                 dict(arrivals=[0], demands=[]), dict(arrivals=[0], demands=[[0]]),
                 dict(arrivals=[0], demands=[[float('nan')]]),
                 dict(arrivals=[0], demands=[[]])]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                simulate(POLICIES[0], **kwargs)
        with self.assertRaises(ValueError):
            percentile([1], 0)


if __name__ == '__main__':
    unittest.main()
