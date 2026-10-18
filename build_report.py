"""Render self-contained HTML and Markdown directly from recorded simulation runs."""
import hashlib
import html
import json
from pathlib import Path
from statistics import mean
from reliability_lab import Policy, Scenario, simulate

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / 'results'


def summarize(rows):
    summaries = []
    for scenario in ('healthy', 'outage', 'overload'):
        for policy in ('baseline', 'bounded', 'breaker'):
            group = [r for r in rows if r['scenario'] == scenario and r['policy'] == policy]
            if not group:
                raise ValueError('Missing scenario/policy cell')
            summaries.append(dict(scenario=scenario, policy=policy, n=len(group),
                                  **{key: mean(r[key] for r in group) for key in
                                     ('availability', 'within_1s', 'attempts_per_request',
                                      'p95_success_s', 'p95_terminal_s', 'queue_overflows',
                                      'breaker_rejections', 'dependency_work_s')},
                                  availability_min=min(r['availability'] for r in group),
                                  availability_max=max(r['availability'] for r in group)))
    return summaries


def table(rows, markdown=False):
    headings = ['Scenario', 'Policy', 'Success %', 'Success ≤1s %', 'Attempts/request',
                'Success p95 s', 'Terminal p95 s', 'Queue overflows', 'Breaker rejects', 'Work s']
    formatted = [[r['scenario'], r['policy'], f"{100*r['availability']:.1f}",
                  f"{100*r['within_1s']:.1f}", f"{r['attempts_per_request']:.3f}",
                  f"{r['p95_success_s']:.3f}", f"{r['p95_terminal_s']:.3f}",
                  f"{r['queue_overflows']:.1f}", f"{r['breaker_rejections']:.1f}",
                  f"{r['dependency_work_s']:.1f}"] for r in rows]
    if markdown:
        return '\n'.join('| ' + ' | '.join(row) + ' |' for row in
                         [headings, ['---'] * len(headings), *formatted])
    return '<div class="scroll"><table><thead><tr>' + ''.join(
        f'<th scope="col">{html.escape(x)}</th>' for x in headings) + '</tr></thead><tbody>' + ''.join(
            '<tr>' + ''.join(f'<td>{html.escape(x)}</td>' for x in row) + '</tr>'
            for row in formatted) + '</tbody></table></div>'


def main():
    raw = (RESULTS / 'runs.json').read_bytes()
    rows = json.loads(raw)
    sensitivity = json.loads((RESULTS / 'sensitivity/runs.json').read_text())
    primary, extra = summarize(rows), summarize(sensitivity)
    if len(rows) != 27 or len(sensitivity) != 90:
        raise ValueError('Expected all 27 primary and 90 sensitivity runs')
    if {r['seed'] for r in rows} != {17, 29, 43} or {r['seed'] for r in sensitivity} != set(range(1, 11)):
        raise ValueError('Unexpected seed populations')
    digest = hashlib.sha256(raw).hexdigest()
    narrative = ('With a 24-slot waiting queue, outage success averages 75.4% for baseline, '
                 '74.1% for bounded retries and 70.0% for the breaker. The breaker reserves '
                 'less dependency work but rejects requests that the other policies can serve. '
                 'Under overload, baseline succeeds on 62.5% of arrivals; bounded retries '
                 'achieve 0.7% and the breaker 9.9%. None meets the illustrative 80% success target.')
    # Guard human-readable headline rounding against changes to the source evidence.
    assert [f"{100*r['availability']:.1f}" for r in primary[3:]] == ['75.4', '74.1', '70.0', '62.5', '0.7', '9.9']
    ranges = '\n'.join(f"| {r['scenario']} | {r['policy']} | {100*r['availability']:.1f}% | "
                       f"{100*r['availability_min']:.1f}–{100*r['availability_max']:.1f}% |"
                       for r in extra)
    summary = ('# Generated results summary\n\nSynthetic experiments; never production results.\n\n' + narrative +
               '\n\n## Primary seeds: 17, 29, 43\n\n' + table(primary, True) +
               '\n\nAll cells are arithmetic means of per-run metrics. Means of p95 values are not pooled p95.\n'
               '\n## Sensitivity seeds: 1–10 (all 90 runs)\n\n' + table(extra, True) +
               '\n\n| Scenario | Policy | Mean success | Per-seed min–max success |\n| --- | --- | --- | --- |\n' + ranges +
               '\n\nRanges describe these seeds; they are not confidence intervals.\n\nPrimary JSON SHA-256: `' + digest + '`\n')
    (RESULTS / 'summary.md').write_text(summary, encoding='utf-8', newline='\n')
    tiny = simulate(Policy('timing_fixture', 2, 0),
                    Scenario('hand_check', rate=0, duration=2, capacity=1, queue_limit=1),
                    arrivals=[0, .1, .2, .3], demands=[[.5]] * 4, trace=True)
    (RESULTS / 'trace-example.json').write_text(json.dumps(tiny, indent=2, allow_nan=False) + '\n',
                                                 encoding='utf-8', newline='\n')
    bars = ''
    for scenario in ('healthy', 'outage', 'overload'):
        bars += f'<section class="chart"><h3>{scenario.title()}</h3>'
        for r in primary:
            if r['scenario'] == scenario:
                bars += (f'<div class="barrow"><span>{r["policy"]}</span><div class="track">'
                         f'<div class="bar {r["policy"]}" style="width:{100*r["availability"]}%"></div>'
                         f'</div><b>{100*r["availability"]:.1f}%</b></div>')
        bars += '</section>'
    range_html = '<table><thead><tr><th>Scenario</th><th>Policy</th><th>Mean success</th><th>Seed min–max</th></tr></thead><tbody>' + ''.join(
        f'<tr><td>{r["scenario"]}</td><td>{r["policy"]}</td><td>{100*r["availability"]:.1f}%</td>'
        f'<td>{100*r["availability_min"]:.1f}–{100*r["availability_max"]:.1f}%</td></tr>' for r in extra) + '</tbody></table>'
    page = '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Service Reliability Lab | Christopher Infante</title>
<style>
:root{color-scheme:light;--ink:#152d3b;--muted:#476071;--rule:#cfdae0;--bg:#f4f7f8}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,Segoe UI,sans-serif}
header{background:#102c3a;color:#fff;padding:54px max(24px,calc((100vw - 1160px)/2)) 44px}
header p{color:#c4dce5;margin:8px 0}h1{font-size:clamp(2rem,4vw,3.3rem);line-height:1.1;margin:16px 0}
.eyebrow{font-size:13px;letter-spacing:.13em;text-transform:uppercase}.badge{display:inline-block;border:1px solid #769ba9;border-radius:4px;padding:3px 9px;font-size:13px}
main{max-width:1208px;margin:auto;padding:30px 24px 60px}section{margin:0 0 34px}h2{font-size:25px;margin:0 0 12px}h3{font-size:18px;margin:0 0 18px}
p{max-width:90ch}.lead{font-size:19px}.charts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
.chart{padding:20px;background:white;border:1px solid var(--rule);border-radius:8px;margin:0}.barrow{display:grid;grid-template-columns:66px 1fr 54px;align-items:center;gap:7px;margin:12px 0;font-size:13px}.barrow b{text-align:right;font-variant-numeric:tabular-nums}
.track{height:16px;background:#e7edf0;border-radius:3px;overflow:hidden}.bar{height:100%;background:#246383}.bounded{background:#b46b20}.breaker{background:#58774b}
.caption,.note{color:var(--muted);font-size:14px}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;background:#fff;font-size:13px;font-variant-numeric:tabular-nums}th,td{padding:11px 10px;border-bottom:1px solid var(--rule);text-align:right;white-space:nowrap}th{background:#e6eef2;font-weight:650}th:first-child,td:first-child,th:nth-child(2),td:nth-child(2){text-align:left}
details{background:white;border:1px solid var(--rule);padding:16px 20px;border-radius:6px;margin:14px 0}summary{cursor:pointer;font-weight:650}code{font-size:13px;overflow-wrap:anywhere}a{color:#125d85}footer{font-size:13px;color:var(--muted);border-top:1px solid var(--rule);padding-top:16px}.flow{font:14px/2 ui-monospace,monospace;padding:16px;background:#e6eef2;border-radius:6px}
@media(max-width:800px){.charts{grid-template-columns:1fr}header{padding:34px 24px}main{padding:24px 16px}.lead{font-size:17px}}@media print{body{background:white}header{background:white;color:#152d3b;padding:16px 0}header p{color:#476071}main{padding:0}details{break-inside:avoid}.scroll{overflow:visible}table{font-size:9px}th,td{padding:5px}.badge{border-color:#476071}}
</style></head><body><header><div class="eyebrow">Christopher Infante · Engineering evidence</div><h1>Service Reliability Lab</h1>
<p>Protecting dependency capacity can cost successful delivery.</p><span class="badge">Synthetic portfolio demonstration · 2026-10-18</span></header><main>
<section><h2>Executive summary</h2><p class="lead">NARRATIVE</p><p>Queue admission changes the conclusion. The original unbounded model showed much greater retry amplification; those runs are preserved separately. This report uses the hardened bounded model, with no policy selected as a universal winner.</p></section>
<section><h2>Successful delivery across three scenarios</h2><div class="charts">BARS</div><p class="caption">Success / all original arrivals; 0–100% bar scale. Mean of seeds 17, 29 and 43. Fast failures count against success.</p></section>
<section><h2>Latency and dependency pressure tell different stories</h2>PRIMARY<p class="caption">Arithmetic means of three per-seed runs. Queue overflow and breaker rejection columns are mean counts per run. Work is reserved service seconds, including work surviving client timeout. Terminal p95 includes fast failure; success p95 excludes failure. Neither is a pooled percentile.</p>
<p>The outage breaker's 0.156s terminal p95 includes immediate rejections. Its 0.725 attempts/request uses every arrival in the denominator, including requests rejected without a dependency attempt. A value below one is load shedding, not a fractional attempt or proof of greater efficiency.</p></section>
<section><h2>Why retries can worsen successful delivery</h2><p>A client timeout leaves dependency work running or queued. Retried work consumes scarce admission slots; short 0.45s attempt timeouts can expire in the queue even when the baseline's 3s timeout would succeed. Overflow ends the request immediately without retry. This comparison changes both timeout and retry settings, so it does not isolate the effect of retries alone.</p><p>The overload baseline delivers 62.5% rather than building an unlimited backlog. The breaker rejects aggressively after local failures and delivers 9.9%. Capacity protection and successful request completion are distinct objectives.</p></section>
<section><h2>Seed sensitivity retains every run</h2><p>Ten additional seeds (1–10), all policies and all scenarios: 90 runs. These ranges are descriptive, not confidence intervals.</p><div class="scroll">RANGES</div><details><summary>Full sensitivity metrics</summary>SENSITIVITY</details></section>
<section><h2>Operational decision</h2><p>Validate timeout budgets, cancellation and bounded admission together before adding a breaker. Define business priority and an approved deferred/manual workflow for rejected requests. None of these numeric settings is a production recommendation, RTO commitment or compliance claim.</p></section>
<section><h2>Model and evidence</h2><div class="flow">Seeded arrivals → policy gate → six workers + 24 waiting slots → response / timeout → bounded backoff → one terminal outcome</div>
<details><summary>Scenario and policy contract</summary><p>120s of Poisson arrivals; response events drain afterward. Healthy/outage rate: 4/s; overload: 80/s. Healthy service: uniform 0.08–0.16s. Outage [40,70), evaluated at service start: 2s work then failure. Baseline: 3s timeout, zero retries. Bounded/breaker: 0.45s timeout, at most two retries, 0.1/0.2s backoff; total request budget 1.65s. Breaker: five consecutive observed failures, 5s cooldown, one half-open probe. Equal-time events use insertion order; initial arrivals are inserted before response events.</p><p>One shared breaker, fixed capacity, FIFO reservations and ineffective cancellation. No trained ML model, live dependency, autoscaling, jitter, distributed breaker, persistent data or measured failover. Synthetic success fractions are not uptime SLAs. Three primary and ten sensitivity seeds do not characterize every workload.</p></details>
<details><summary>Sources and reproducibility</summary><p>Primary: <a href="runs.json">runs.json</a> / <a href="runs.csv">runs.csv</a>; sensitivity: <a href="sensitivity/runs.json">all 90 runs</a>; legacy unbounded: <a href="legacy-unbounded/runs.json">archived 27 runs</a>.</p><p>Primary JSON SHA-256: <code>DIGEST</code>. This HTML embeds generated summaries and needs no remote assets or JavaScript.</p><p><code>python -m unittest discover -s tests -v</code><br><code>python reliability_lab.py</code><br><code>python reliability_lab.py --output results/sensitivity --seeds 1 2 3 4 5 6 7 8 9 10</code><br><code>python build_report.py</code></p><p>See <a href="../docs/metrics.md">full metric dictionary</a>, <a href="../docs/traceability.md">requirements traceability</a>, <a href="../docs/verification.md">verification record</a>, and <a href="../docs/decision-brief.md">continuity decision brief</a>. Markdown sources are repository documents; browser download/display depends on the viewer.</p></details></section>
<footer>Christopher Infante · Service Reliability Lab · Standard-library Python · Local artifact; no production or client results</footer></main></body></html>'''
    for token, content in [('NARRATIVE', narrative), ('BARS', bars), ('PRIMARY', table(primary)),
                           ('RANGES', range_html), ('SENSITIVITY', table(extra)), ('DIGEST', digest)]:
        page = page.replace(token, content)
    (RESULTS / 'report.html').write_text(page, encoding='utf-8', newline='\n')
    print('Generated results/report.html and results/summary.md from all 117 current runs')


if __name__ == '__main__':
    main()
