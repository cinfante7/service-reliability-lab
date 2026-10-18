# Archived first-version evidence

These 27 run records are from the original **unbounded queue** model at local
Git commit `1a4bc44` (one JSON and one CSV file, each with 27 rows/records).
They were preserved before bounded-queue hardening. Their schema lacks newer queue,
deadline and configuration metadata. They are **excluded** from the current report
and summary and must not be presented as current bounded-queue outcomes.

For source history, inspect `git show 1a4bc44:reliability_lab.py` without modifying the
current checkout. The legacy regression test uses queue_limit=100000 as an effectively
unbounded behavioral proxy; it does not assert byte equality to the old schema.

The original result was stronger retry amplification: outage mean success
76.0%/67.4%/70.0% for baseline/bounded/breaker, versus 75.4%/74.1%/70.0% in the current
bounded model. Keeping both exposes model sensitivity rather than hiding a changed
conclusion. All values are synthetic.
