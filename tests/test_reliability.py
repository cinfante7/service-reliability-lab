import unittest
from reliability_lab import POLICIES, Policy, Scenario, percentile, simulate


class ReliabilityTests(unittest.TestCase):
    def test_seed_reproducibility_and_common_arrivals(self):
        rows = [simulate(p) for p in POLICIES]
        self.assertEqual(rows[0], simulate(POLICIES[0]))
        self.assertEqual(len({r['requests'] for r in rows}), 1)

    def test_healthy_requests_all_succeed_without_retries(self):
        for policy in POLICIES:
            r = simulate(policy, 'healthy')
            self.assertEqual(r['availability'], 1)
            self.assertEqual(r['attempts'], r['requests'])
            self.assertEqual(r['breaker_opens'], 0)

    def test_accounting_and_bounds_all_scenarios(self):
        for scenario in ('healthy', 'outage', 'overload'):
            for policy in POLICIES:
                r = simulate(policy, scenario)
                self.assertEqual(r['completed_requests'], r['requests'])
                self.assertLessEqual(r['attempts'], r['requests'] * (1 + policy.retries))
                self.assertLessEqual(r['within_1s'], r['availability'])
                self.assertLessEqual(r['p95_terminal_s'],
                                     policy.timeout * (1 + policy.retries) + .3 + 1e-9)
                self.assertGreaterEqual(r['dependency_work_s'], 0)

    def test_timeout_retry_amplification_and_breaker_shedding(self):
        # Explicit legacy, effectively unbounded queue: retained comparison, not
        # an acceptance goal for the now-bounded default experiment.
        baseline, bounded, breaker = [simulate(p, queue_limit=100000) for p in POLICIES]
        self.assertGreater(bounded['attempts'], baseline['attempts'])
        self.assertGreater(breaker['breaker_rejections'], 0)
        self.assertLess(breaker['dependency_work_s'], bounded['dependency_work_s'])
        self.assertGreater(breaker['availability'], bounded['availability'])
        self.assertGreater(breaker['successes_arriving_after_75s'], 0)

    def test_bounded_default_does_not_assume_breaker_is_best(self):
        baseline, bounded, breaker = [simulate(p) for p in POLICIES]
        self.assertLess(breaker['dependency_work_s'], bounded['dependency_work_s'])
        self.assertLess(breaker['availability'], baseline['availability'])
        self.assertGreater(bounded['queue_overflows'], 0)

    def test_overload_breaker_is_not_capacity_solution(self):
        r = simulate(POLICIES[2], 'overload')
        self.assertLess(r['availability'], .8)

    def test_explicit_timeout_failure_has_no_success_latency(self):
        r = simulate(Policy('short', .01, 0), 'healthy')
        self.assertEqual(r['successes'], 0)
        self.assertIsNone(r['p95_success_s'])
        self.assertAlmostEqual(r['p95_terminal_s'], .01)

    def test_empty_population_and_input_validation(self):
        self.assertIsNone(percentile([], .95))
        self.assertEqual(percentile([1, 2, 3, 4], .95), 4)
        self.assertEqual(simulate(POLICIES[0], duration=1e-12)['requests'], 0)
        with self.assertRaises(ValueError):
            simulate(POLICIES[0], capacity=0)
        with self.assertRaises(ValueError):
            Policy('invalid', 0, 0)
        with self.assertRaises(ValueError):
            Policy('invalid', 1, 3)


if __name__ == '__main__':
    unittest.main()
