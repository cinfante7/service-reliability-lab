# Verification record

Executed locally on 2026-10-18 with Python 3.13.7 and Git 2.53.0.windows.2.
No packages or software were installed. No credentials or external datasets were used.

```console
python -m unittest discover -s tests -v
```

Result: **7 tests passed**. The suite exercises all nine policy/scenario combinations
for outcome accounting and bounds, as well as controlled failure and empty cases.

```console
python reliability_lab.py
python reliability_lab.py --output results-verify
```

Both executions produced the same 27 runs. SHA-256 checks of each artifact pair:

| File | SHA-256 (both executions) |
|---|---|
| runs.json | 8F2FA2531E9F7CB1941E0C8AB231DF6520A7994BD5A00DDE81D0E7A089FED75F |
| runs.csv | 5CC456C06692A6068AF894EB928C8553697AA861542BD057F2FAC6239F118BF7 |

The README table was transcribed from the CLI's arithmetic means of per-seed metrics.
Raw numerical precision remains available in the CSV and JSON. The verification copy
is ignored by Git. These checks establish local deterministic reproduction, not model
validation against a real dependency.

During development, the overload regression test failed because 40 requests/s was
below the modeled healthy capacity of approximately 50 attempts/s. The workload was
corrected to 80 requests/s and the full suite and both sample executions were rerun.
This is an experiment-design correction; no failed outcome was concealed by weakening
the test's 80% success threshold.
