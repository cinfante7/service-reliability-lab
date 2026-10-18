# Final hardening verification — 2026-10-18

Environment: Windows, **Python 3.13.7**, Git 2.53.0.windows.2. No packages or software
were installed. All experiment inputs are synthetic; no credentials or unrelated
personal records were accessed. Nothing was uploaded.

## Executed commands and outcomes

```console
python --version
python -m unittest discover -s tests -v
python reliability_lab.py
python reliability_lab.py --output results/sensitivity --seeds 1 2 3 4 5 6 7 8 9 10
python build_report.py
python verify_reproduction.py
```

- **28/28 tests passed.** Full requirement mapping is in traceability.md. Individual
  outcome conservation, uniqueness, deadlines, queue bounds and attempt budgets are
  checked across all 27 primary combinations, not only aggregate counts.
- Primary: **27 runs**, seeds 17/29/43. Sensitivity: **90 runs**, seeds 1–10, all
  policies/scenarios retained. No seed was removed because of its outcome.
- Reproduction: four raw JSON/CSV files matched fresh complete executions byte for
  byte. Report HTML, generated summary and injected timing trace matched rebuilds.
- [results/manifest.json](../results/manifest.json) records Python version, seed sets
  and all seven SHA-256 hashes. Primary JSON SHA-256:
  `6062f2b3bb635225671e1f99a21bd9066e8cc9bf3be54a6810c21aacca583ce2`.
- JSON/HTML/Markdown generation explicitly writes LF; CSV uses csv.writer CRLF and
  is marked binary in .gitattributes so Windows checkouts preserve artifact bytes.

## Independent native review

A separate native reviewer read the code without editing it or sharing externally.
It ran **300 stress cases**: 100 seeds × three policies, capacity two, queue bounds
zero through three, injected outage. It checked unique/conserved outcomes, queue
bounds and individual deadlines, and a controlled breaker recovery fixture.

It found finite input values could overflow derived arithmetic and produce Infinity
in JSON. Derived budgets, reservation completions, accumulated work, absolute
deadlines and cooldown ends now reject non-finite results; a targeted regression
test covers budget/end/work overflow and extreme workload generation. JSON writing
also forbids NaN/Infinity. Reviewer notes on equal-time ordering and terminal overflow
are now explicit in architecture.md and tested. No other blocking correctness defect
was found in that review. This is supporting review evidence, not exhaustive proof.

After the documentation and report stabilized, the independent reviewer reran the
full **28/28** suite and `python verify_reproduction.py` (all seven checks passed).
It read the README, architecture, metric dictionary, traceability, decision brief,
Notion draft and report and confirmed current bounded outcomes and denominators
were consistent. Final disposition: **no blocking issues found**.

## Browser visual check

Started a loopback-only server:

```console
python -m http.server 8764 --bind 127.0.0.1
```

Opened `http://127.0.0.1:8764/results/report.html` through the supported Chrome
browser tool. Visually inspected the title, executive summary, three comparison
charts and the wide primary metrics table. Text, headings, bars and table cells
were readable without clipping at the desktop viewport. The source disclosure
expanded through its accessible control. Accessibility output exposed all nine
primary rows, the sensitivity ranges and source links. The final report was reloaded
after LF/hash normalization; headline/table values remained aligned with generated
results. Mobile and print layout are implemented but not visually exercised.

The in-app browser was unavailable; the first sandboxed loopback server timed out
and a socket probe returned Windows permission error 10013. An explicitly approved
escalated **loopback-only** server resolved preview access; no firewall, browser
security or external hosting settings were changed. One locator click timed out;
the accessible source disclosure control succeeded and was verified afterward.

## Corrections and model version boundary

The first version had seven tests and an unbounded queue. Hardening added a bounded
24-slot waiting queue, terminal overflow and explicit total deadlines. This materially
changed default results and invalidated the old amplification regression. That test
now explicitly selects the legacy effectively-unbounded case; separate tests check
bounded behavior without requiring the breaker to win. Current README, report and
decision brief use bounded results. The original 27 runs are preserved under
results/legacy-unbounded/ and are excluded from current summaries.

The original overload rate of 40/s was below modeled healthy capacity; development
corrected it to 80/s before the first committed results. No policies, thresholds or
seeds were subsequently tuned to obtain a preferred winner. These corrections are
experiment design changes, not production findings. Known assumptions and next
validation steps remain explicit in architecture.md and decision-brief.md.
