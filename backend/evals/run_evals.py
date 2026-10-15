"""Eval harness for the Fund Treasury backend (scorecard advisory).

Accuracy, latency, and cost on the mock stack.
Run: python -m evals.run_evals [--json out.json]
"""
# pylint: disable=wrong-import-position,too-many-locals
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="ft-eval-"))
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TMP / 'eval.db'}")
os.environ.setdefault("BANK_FILE_OUTBOX", str(_TMP / "outbox"))
os.environ.setdefault("KYRIBA_MODE", "mock")
os.environ.setdefault("BANK_MODE", "mock")
from fastapi.testclient import TestClient  # noqa: E402

from app.database import SessionLocal, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed_demo_data  # noqa: E402


@dataclass
class EvalResult:
    name: str
    category: str
    passed: bool
    detail: str
    latency_ms: float | None = None
    extra: dict = field(default_factory=dict)
def _timed(fn, repeats=1):
    samples = []
    out = None
    for _ in range(repeats):
        s = time.perf_counter()
        out = fn()
        samples.append((time.perf_counter() - s) * 1000.0)
    return out, samples
def _balanced(row) -> bool:
    """One forecast row balances: closing == opening + in - out."""
    exp = float(row["opening_balance"]) + float(row["inflows"])
    exp -= float(row["outflows"])
    return abs(float(row["closing_balance"]) - exp) < 0.01


# Part 2: accuracy cases.
def eval_forecast_math(client):
    es = client.get("/entities").json()
    eid = next(e["id"] for e in es if e["code"] == "RW-CAP")
    pull = client.post(f"/entities/{eid}/forecast/pull")
    if pull.status_code != 200:
        return EvalResult("forecast.math", "ACC", False, pull.text[:200])
    rows = client.get(f"/entities/{eid}/forecast").json()
    if len(rows) != 14:
        return EvalResult("forecast.math", "ACC", False, f"rows={len(rows)}")
    bad = sum(1 for r in rows if not _balanced(r))
    ok = bad == 0
    return EvalResult("forecast.math", "ACC", ok, f"{len(rows)-bad}/14 ok")
def eval_payment_lifecycle(client):
    accs = client.get("/accounts").json()
    if not accs:
        return EvalResult("payment.lifecycle", "ACC", False, "no accounts")
    aid = accs[0]["id"]
    stamp = str(int(time.time() * 1000))
    payload = {
        "account_id": aid, "amount": "250.00",
        "counterparty": "Eval Vendor", "reference": f"EVAL-{stamp}",
    }
    crt = client.post("/payments", json=payload)
    if crt.status_code != 201:
        return EvalResult("payment.lifecycle", "ACC", False, crt.text[:200])
    pid = crt.json()["id"]
    snd = client.post(f"/payments/{pid}/send")
    if snd.status_code != 200 or snd.json()["payment"]["status"] != "sent":
        return EvalResult("payment.lifecycle", "ACC", False, snd.text[:200])
    agn = client.post(f"/payments/{pid}/send")
    if agn.status_code != 409:
        return EvalResult("payment.lifecycle", "ACC", False, "dbl-send")
    return EvalResult("payment.lifecycle", "ACC", True, "pending->sent,409")
# Part 3: latency + cost + runner.
def _p95(samples: list) -> tuple:
    ordered = sorted(samples)
    mid = statistics.median(ordered)
    top = ordered[int(0.95 * (len(ordered) - 1))]
    return mid, top


def eval_latency(client, budgets):
    es = client.get("/entities").json()
    eid = next(e["id"] for e in es if e["code"] == "RW-CAP")

    def _health():
        return client.get("/health")

    def _entities():
        return client.get("/entities")

    def _fp():
        return (
            client.post(f"/entities/{eid}/forecast/pull"),
            client.get(f"/entities/{eid}/forecast"),
        )

    tgts = {"GET /health": _health, "GET /entities": _entities}
    tgts["forecast pull+read"] = _fp
    out = []
    for name, fn in tgts.items():
        _, s = _timed(fn, repeats=11)
        p50, p95 = _p95(s)
        b = float(budgets.get("p95_ms", {}).get(name, 2000.0))
        msg = f"p50={p50:.1f} p95={p95:.1f} b={b:.0f}"
        xtra = {"p50_ms": round(p50, 2), "p95_ms": round(p95, 2)}
        item = EvalResult(f"latency.{name}", "LAT", p95 <= b, msg,
                          latency_ms=p95, extra=xtra)
        out.append(item)
    return out
def eval_cost(client):
    es = client.get("/entities").json()
    eid = next(e["id"] for e in es if e["code"] == "RW-CAP")
    rp = client.post(f"/entities/{eid}/forecast/pull")
    rows = client.get(f"/entities/{eid}/forecast").json()
    tb = len(rp.content) + len(json.dumps(rows).encode())
    pr = tb / max(len(rows), 1)
    msg = f"{len(rows)}r {tb}B {pr:.0f}B/r"
    xtra = {"rows": len(rows), "bytes_total": tb, "bytes_per_row": round(pr, 1)}
    return EvalResult("cost.forecast-row", "COST", True, msg, extra=xtra)
def main():
    ap = argparse.ArgumentParser(description="Fund Treasury evals")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    bp = Path(__file__).with_name("budgets.json")
    budgets = json.loads(bp.read_text(encoding="utf-8")) if bp.exists() else {}
    init_db()
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()
    res = []
    with TestClient(app) as client:
        res.append(eval_forecast_math(client))
        res.append(eval_payment_lifecycle(client))
        res.extend(eval_latency(client, budgets))
        res.append(eval_cost(client))
    bad = [r for r in res if not r.passed]
    print(f"eval: {len(res)-len(bad)}/{len(res)} passed")
    for r in res:
        mark = "PASS" if r.passed else "FAIL"
        print(f"  [{mark}] {r.category} {r.name}: {r.detail}")
    if a.json:
        payload = json.dumps([asdict(r) for r in res], indent=2)
        Path(a.json).write_text(payload, encoding="utf-8")
        print(f"wrote {a.json}")
    return 0 if not bad else 1
if __name__ == "__main__":
    sys.exit(main())
