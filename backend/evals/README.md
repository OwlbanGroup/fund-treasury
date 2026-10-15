# Eval harness (scorecard advisory)

Measures accuracy, latency, cost on the mock stack.

```powershell
cd backend
python -m evals.run_evals
python -m evals.run_evals --json eval-results.json
```

Cases: forecast math (14 rows balance), payment
lifecycle (pending->sent, double-send 409),
latency p50/p95 x3 endpoints, cost bytes/row.

Tune `budgets.json` per environment.
